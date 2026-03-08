"""Step 3: Model Training."""

from __future__ import annotations

import logging
from datetime import datetime

import streamlit as st

from mlfx.app.streamlit.config import BACKEND_OPTIONS, LABEL_OPTIONS, TF_OPTIONS
from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.utils import load_config, run_with_capture
from mlfx.training.config import TrainingConfig
from mlfx.training.runner import run_training
from mlfx.registry.models import get_registry
from mlfx.evaluation.runner import get_baseline_metrics, run_model_backtest


def _render_backtest_params_form(cfg: dict) -> tuple[float, float, float, float, float]:
    """Render backtest params form and return (tp_r, sl_r, initial_capital, risk_pct, commission)."""
    bt_cfg = cfg.get("backtest", {})
    with st.expander("Backtest params (TP/SL, capital)"):
        c1, c2 = st.columns(2)
        with c1:
            tp_r = st.number_input(
                "Take Profit (R)",
                value=float(bt_cfg.get("tp_r", 1.5)),
                min_value=0.1,
                step=0.1,
                key="bt_tp_r",
            )
            sl_r = st.number_input(
                "Stop Loss (R)",
                value=float(bt_cfg.get("sl_r", 1.0)),
                min_value=0.1,
                step=0.1,
                key="bt_sl_r",
            )
        with c2:
            initial_capital = st.number_input(
                "Initial Capital ($)",
                value=float(bt_cfg.get("initial_capital", 10000.0)),
                min_value=100.0,
                step=1000.0,
                key="bt_capital",
            )
            risk_pct = st.number_input(
                "Risk (%)",
                value=float(bt_cfg.get("risk_pct", 1.0)),
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                key="bt_risk_pct",
            )
            commission = st.number_input(
                "Commission ($)",
                value=float(bt_cfg.get("commission", 0.1)),
                min_value=0.0,
                step=0.05,
                key="bt_commission",
            )
    return tp_r, sl_r, initial_capital, risk_pct, commission


def _format_baseline_metrics(raw: dict[str, float] | None) -> dict[str, str]:
    """Format raw baseline metrics for display (match run_model_backtest format)."""
    if raw is None:
        return {}
    return {
        "Total Trades": f"{int(raw.get('total_trades', 0))}",
        "Win Rate (%)": f"{raw.get('win_rate', 0):.2f}%",
        "Profit Factor": f"{raw.get('profit_factor', 0):.2f}",
        "Net Profit (R)": f"{raw.get('total_r', 0):.2f}R",
        "Net Profit ($)": f"${raw.get('net_profit_dollar', 0):.2f}",
        "Sharpe Ratio": f"{raw.get('sharpe_ratio', 0):.2f}",
        "Sortino Ratio": f"{raw.get('sortino_ratio', 0):.2f}",
        "Calmar Ratio": f"{raw.get('calmar_ratio', 0):.2f}",
        "Final Capital ($)": f"${raw.get('final_capital', 0):.2f}",
    }


def render_model_training_step() -> None:
    """Render Step 3: Model Training."""
    cfg = load_config()
    tr_cfg = cfg.get("train", {})

    navigation.render_step_header()
    st.space("medium")

    symbol = st.session_state.get("symbol", "XAUUSD")
    tf = st.session_state.get("tf", "1H")
    selected_model_idx = None

    st.markdown("### Model Configuration")
    action = st.radio("Model Source", ["Train New Model", "Use Existing Model"], horizontal=True, key="model_source")
    st.space("medium")

    with st.container(border=True):
        c1, c2 = st.columns([1, 1])
        with c1:
            tr_symbol = st.text_input("Symbol", value=symbol, key="tr_symbol")
            tr_tf = st.selectbox(
                "Timeframe",
                options=TF_OPTIONS,
                index=TF_OPTIONS.index(tf) if tf in TF_OPTIONS else 4,
                key="tr_tf",
            )
            tr_label = st.selectbox(
                "Label Column",
                options=LABEL_OPTIONS,
                index=LABEL_OPTIONS.index(tr_cfg.get("label_col", "label_10"))
                if tr_cfg.get("label_col", "label_10") in LABEL_OPTIONS
                else 1,
                key="tr_label",
            )
            _backend = tr_cfg.get("backend", "mlf")
            backend = st.selectbox(
                "Backend",
                options=BACKEND_OPTIONS,
                index=BACKEND_OPTIONS.index(_backend) if _backend in BACKEND_OPTIONS else 0,
                key="tr_backend",
            )

        if action == "Train New Model":
            with c2:
                n_trials = st.number_input(
                    "Optuna Trials",
                    value=tr_cfg.get("n_trials", 30),
                    min_value=1,
                    key="tr_trials",
                )
                n_splits = st.number_input(
                    "CV Splits",
                    value=tr_cfg.get("n_splits", 5),
                    min_value=2,
                    key="tr_splits",
                )
                with st.expander("Hyperparameter nâng cao"):
                    force_tr = st.checkbox("Force retrain", value=False, key="tr_force")
        else:
            with c2:
                registry = get_registry()
                models = registry.list_models(symbol=tr_symbol or "XAUUSD", tf=tr_tf, backend=backend)
                models = [m for m in models if m.get("label_col") == tr_label]
                if not models:
                    st.info(f"No existing models found for {tr_symbol} {tr_tf} {tr_label}")
                    selected_model_idx = None
                else:
                    def format_model(m):
                        dt = datetime.fromtimestamp(m.get("registered_at", 0)).strftime("%Y-%m-%d %H:%M")
                        f1 = m.get("metrics", {}).get("best_cv_f1_macro", 0.0)
                        return f"{dt} - F1: {f1:.4f} ({m.get('backend')})"
                    model_options = [format_model(m) for m in models]
                    selected_model_idx = st.selectbox(
                        "Select Model",
                        range(len(model_options)),
                        format_func=lambda i: model_options[i],
                        key="tr_model_select",
                    )

    tp_r, sl_r, initial_capital, risk_pct, commission = _render_backtest_params_form(cfg)

    st.space("medium")
    with st.container(horizontal=True, horizontal_alignment="center"):
        if action == "Train New Model":
            if st.button("▶ Train & Evaluate Model", key="btn_train", type="primary"):
                with st.status("Training model...", expanded=True) as status:
                    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                    try:
                        cfg_train = TrainingConfig(
                            symbol=tr_symbol or "XAUUSD",
                            tf=tr_tf,
                            label_col=tr_label,
                            backend=backend,
                            n_trials=int(n_trials),
                            n_splits=int(n_splits),
                            force=force_tr,
                        )
                        result, log = run_with_capture(run_training, cfg_train)

                        if result:
                            status.update(label="Running backtest evaluation...", state="running")

                            metrics = run_model_backtest(
                                symbol=tr_symbol,
                                tf=tr_tf,
                                label_col=tr_label,
                                tp_r=tp_r,
                                sl_r=sl_r,
                                initial_capital=initial_capital,
                                risk_pct=risk_pct,
                                commission=commission,
                            )

                            baseline_raw = get_baseline_metrics(
                                symbol=tr_symbol,
                                tf=tr_tf,
                                label_col=tr_label,
                                tp_r=tp_r,
                                sl_r=sl_r,
                                initial_capital=initial_capital,
                                risk_pct=risk_pct,
                                commission=commission,
                            )
                            baseline_metrics = _format_baseline_metrics(baseline_raw)

                            navigation.mark_step_completed(WorkflowStep.MODEL_TRAINING)
                            navigation.store_step_data(
                                WorkflowStep.MODEL_TRAINING,
                                {
                                    "symbol": tr_symbol,
                                    "timeframe": tr_tf,
                                    "label_col": tr_label,
                                    "backend": backend,
                                    "result": result,
                                    "metrics": metrics,
                                    "baseline_metrics": baseline_metrics,
                                    "baseline_raw": baseline_raw,
                                    "tp_r": tp_r,
                                    "sl_r": sl_r,
                                },
                            )
                            navigation.invalidate_subsequent_steps(WorkflowStep.MODEL_TRAINING)
                            st.session_state["label_col"] = tr_label

                            with st.container(border=True):
                                st.markdown("### Training Results")
                                kpi_cols = st.columns(4)
                                kpi_cols[0].metric("Best CV F1 (macro)", f"{result.get('best_cv_f1_macro', 0):.4f}")
                                kpi_cols[1].metric("Train F1 (macro)", f"{result.get('f1_macro_train', 0):.4f}")
                                if metrics:
                                    kpi_cols[2].metric("Win Rate", metrics.get("Win Rate (%)", "N/A"))
                                    kpi_cols[3].metric("Net Profit", metrics.get("Net Profit ($)", "N/A"))

                            if metrics and baseline_raw is not None:
                                model_r_str = str(metrics.get("Net Profit (R)", "0R"))
                                model_r_val = float(model_r_str.replace("R", "").strip() or 0)
                                baseline_r_val = baseline_raw.get("total_r", 0)
                                diff_r = model_r_val - baseline_r_val
                                st.markdown("#### Model vs Labels (baseline)")
                                col_model, col_labels = st.columns(2)
                                with col_model:
                                    st.markdown("**Model**")
                                    for k, v in list(metrics.items())[:6]:
                                        st.metric(k, v)
                                with col_labels:
                                    st.markdown("**Labels (baseline)**")
                                    for k, v in list(baseline_metrics.items())[:6]:
                                        st.metric(k, v)
                                if diff_r > 0:
                                    st.success(f"Model tốt hơn +{diff_r:.2f}R so với baseline")
                                elif diff_r < 0:
                                    st.warning(f"Model kém hơn {diff_r:.2f}R so với baseline")
                                else:
                                    st.info("Model và Labels có Net Profit (R) bằng nhau")

                            status.update(label="Model training and evaluation completed!", state="complete", expanded=False)
                            st.rerun()
                        else:
                            navigation.mark_step_error(WorkflowStep.MODEL_TRAINING, "Training failed")
                            status.update(label="Model training failed", state="error", expanded=True)

                        if log:
                            st.code(log, language="text")

                    except Exception as e:
                        navigation.mark_step_error(WorkflowStep.MODEL_TRAINING, str(e))
                        status.update(label=f"Error: {str(e)}", state="error", expanded=True)
        elif action == "Use Existing Model" and selected_model_idx is not None:
            if st.button("▶ Evaluate Selected Model", key="btn_eval", type="primary"):
                with st.status("Evaluating model...", expanded=True) as status:
                    try:
                        metrics = run_model_backtest(
                            symbol=tr_symbol,
                            tf=tr_tf,
                            label_col=tr_label,
                            tp_r=tp_r,
                            sl_r=sl_r,
                            initial_capital=initial_capital,
                            risk_pct=risk_pct,
                            commission=commission,
                        )

                        if metrics:
                            baseline_raw = get_baseline_metrics(
                                symbol=tr_symbol,
                                tf=tr_tf,
                                label_col=tr_label,
                                tp_r=tp_r,
                                sl_r=sl_r,
                                initial_capital=initial_capital,
                                risk_pct=risk_pct,
                                commission=commission,
                            )
                            baseline_metrics = _format_baseline_metrics(baseline_raw)

                            selected_model = models[selected_model_idx]
                            result = selected_model.get("metrics", {})

                            navigation.mark_step_completed(WorkflowStep.MODEL_TRAINING)
                            navigation.store_step_data(
                                WorkflowStep.MODEL_TRAINING,
                                {
                                    "symbol": tr_symbol,
                                    "timeframe": tr_tf,
                                    "label_col": tr_label,
                                    "backend": backend,
                                    "result": result,
                                    "metrics": metrics,
                                    "baseline_metrics": baseline_metrics,
                                    "baseline_raw": baseline_raw,
                                    "tp_r": tp_r,
                                    "sl_r": sl_r,
                                },
                            )
                            navigation.invalidate_subsequent_steps(WorkflowStep.MODEL_TRAINING)
                            st.session_state["label_col"] = tr_label

                            with st.container(border=True):
                                st.markdown("### Training Results")
                                kpi_cols = st.columns(4)
                                kpi_cols[0].metric("Best CV F1 (macro)", f"{result.get('best_cv_f1_macro', 0):.4f}")
                                kpi_cols[1].metric("Train F1 (macro)", f"{result.get('f1_macro_train', 0):.4f}")
                                kpi_cols[2].metric("Win Rate", metrics.get("Win Rate (%)", "N/A"))
                                kpi_cols[3].metric("Net Profit", metrics.get("Net Profit ($)", "N/A"))

                            if baseline_raw is not None:
                                model_r_str = str(metrics.get("Net Profit (R)", "0R"))
                                model_r_val = float(model_r_str.replace("R", "").strip() or 0)
                                baseline_r_val = baseline_raw.get("total_r", 0)
                                diff_r = model_r_val - baseline_r_val
                                st.markdown("#### Model vs Labels (baseline)")
                                col_model, col_labels = st.columns(2)
                                with col_model:
                                    st.markdown("**Model**")
                                    for k, v in list(metrics.items())[:6]:
                                        st.metric(k, v)
                                with col_labels:
                                    st.markdown("**Labels (baseline)**")
                                    for k, v in list(baseline_metrics.items())[:6]:
                                        st.metric(k, v)
                                if diff_r > 0:
                                    st.success(f"Model tốt hơn +{diff_r:.2f}R so với baseline")
                                elif diff_r < 0:
                                    st.warning(f"Model kém hơn {diff_r:.2f}R so với baseline")
                                else:
                                    st.info("Model và Labels có Net Profit (R) bằng nhau")

                            status.update(label="Model evaluation completed!", state="complete", expanded=False)
                            st.rerun()
                        else:
                            navigation.mark_step_error(WorkflowStep.MODEL_TRAINING, "Evaluation failed")
                            status.update(label="Model evaluation failed", state="error", expanded=True)
                            
                    except Exception as e:
                        navigation.mark_step_error(WorkflowStep.MODEL_TRAINING, str(e))
                        status.update(label=f"Error: {str(e)}", state="error", expanded=True)
