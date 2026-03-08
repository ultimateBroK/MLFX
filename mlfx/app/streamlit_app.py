"""
MLFX Streamlit UI - Glassmorphism Emerald AMOLED.

Workflow: Data Preparation → Training → Validation (Backtest).
"""

from __future__ import annotations

import io
import logging
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import streamlit as st

from mlfx.config.paths import DEFAULT_PATHS
from mlfx.config.settings import load_config as shared_load_config
from mlfx.evaluation.runner import get_baseline_metrics, run_full_eval, run_model_backtest
from mlfx.ingestion.download import run_download_job
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.resampling import resample_symbol_tf
from mlfx.training.config import TrainingConfig
from mlfx.training.runner import run_training

CONFIG_FILE = DEFAULT_PATHS.config_file
ASSETS_DIR = Path(__file__).resolve().parent / "streamlit_ui" / "assets"

TF_OPTIONS = ["1m", "5m", "15m", "30m", "1H", "2H", "4H", "1D"]
ASSET_CLASS_OPTIONS = ["fx", "crypto"]
BACKEND_OPTIONS = [
    "mlf",
    "lstm",
    "transformer",
    "cnn_lstm",
    "sgd",
    "stats",
    "neuralforecast",
]
LABEL_OPTIONS = ["label_5", "label_10", "label_20"]
PIVOT_TYPE_OPTIONS = ["traditional", "fibonacci", "woodie", "classic", "demark", "camarilla"]
PIVOT_ANCHOR_OPTIONS = ["daily", "weekly", "monthly"]


def _inject_glass_css() -> None:
    """Inject Glassmorphism Emerald AMOLED CSS."""
    css_path = ASSETS_DIR / "glass_emerald.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text()}</style>",
            unsafe_allow_html=True,
        )


def _load_config() -> dict:
    """Load config.toml via shared config layer."""
    return shared_load_config(CONFIG_FILE)


def _run_with_capture(func, *args, **kwargs):
    """Run function capturing stdout/stderr, return (result, log_output)."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            result = func(*args, **kwargs)
        return result, buf.getvalue()
    except Exception as e:
        return None, buf.getvalue() + f"\nError: {e}"


def main() -> None:
    """Entrypoint for Streamlit UI."""
    st.set_page_config(
        page_title="MLFX — ICT Price Prediction",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_glass_css()

    cfg = _load_config()
    dl_cfg = cfg.get("download", {})
    pl_cfg = cfg.get("pipeline", {})
    tr_cfg = cfg.get("train", {})
    bt_cfg = cfg.get("backtest", {})

    # Sidebar - shared params
    with st.sidebar:
        st.title("MLFX")
        st.caption("ICT-Based Price Prediction")
        st.divider()

        symbol = st.text_input(
            "Symbol",
            value=pl_cfg.get("symbol", "XAUUSD"),
            key="sidebar_symbol",
            help="e.g. XAUUSD, EURUSD",
        )
        _tf = pl_cfg.get("timeframe", "1H")
        tf = st.selectbox(
            "Timeframe",
            options=TF_OPTIONS,
            index=TF_OPTIONS.index(_tf) if _tf in TF_OPTIONS else 4,
            key="sidebar_tf",
        )
        _label = tr_cfg.get("label_col", "label_10")
        label_col = st.selectbox(
            "Label Column",
            options=LABEL_OPTIONS,
            index=LABEL_OPTIONS.index(_label) if _label in LABEL_OPTIONS else 1,
            key="sidebar_label_col",
        )

        st.divider()
        with st.expander("Nâng cao"):
            st.caption("QA, drift monitoring, batch-predict (coming soon)")

    st.session_state["symbol"] = symbol
    st.session_state["tf"] = tf
    st.session_state["label_col"] = label_col

    # Main - 4 sections
    st.title("MLFX — ICT Price Prediction")
    st.caption("Data → Chuẩn bị → Train → Xem kết quả")

    # --- 1. Tải dữ liệu ---
    with st.expander("1. Tải dữ liệu", expanded=True):
        c1, c2 = st.columns([1, 1])
        with c1:
            dl_symbol = st.text_input("Symbol", value=symbol, key="dl_symbol")
            asset_class = st.selectbox(
                "Asset Class",
                options=ASSET_CLASS_OPTIONS,
                index=0 if dl_cfg.get("asset_class", "fx") == "fx" else 1,
                key="dl_asset_class",
            )
            start_year = st.number_input("Start Year", value=dl_cfg.get("start_year", 2015), min_value=2000, key="dl_start_year")
            start_month = st.number_input("Start Month", value=dl_cfg.get("start_month", 1), min_value=1, max_value=12, key="dl_start_month")
        with c2:
            concurrency = st.number_input("Concurrency", value=dl_cfg.get("concurrency", 20), min_value=1, key="dl_concurrency")
            force_dl = st.checkbox("Force re-verify", value=False, key="dl_force")

        if st.button("▶ Bắt đầu tải", key="btn_download", type="primary"):
            with st.spinner("Đang tải dữ liệu..."):
                logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                try:
                    _, log = _run_with_capture(
                        run_download_job,
                        symbol=dl_symbol or "XAUUSD",
                        asset_class=asset_class,
                        start_year=int(start_year),
                        start_month=int(start_month),
                        concurrency=int(concurrency),
                        force=force_dl,
                    )
                    if log:
                        st.code(log, language="text")
                    st.success("Tải xong.")
                except Exception as e:
                    st.error(str(e))

    # --- 2. Chuẩn bị ---
    with st.expander("2. Chuẩn bị"):
        c1, c2 = st.columns([1, 1])
        with c1:
            pl_symbol = st.text_input("Symbol", value=symbol, key="pl_symbol")
            pl_tf = st.selectbox("Timeframe", options=TF_OPTIONS, index=TF_OPTIONS.index(tf), key="pl_tf")
            pivot_type = st.selectbox(
                "Pivot Type",
                options=PIVOT_TYPE_OPTIONS,
                index=PIVOT_TYPE_OPTIONS.index(pl_cfg.get("pivot_type", "traditional")),
                key="pl_pivot_type",
            )
            pivot_anchor = st.selectbox(
                "Pivot Anchor",
                options=PIVOT_ANCHOR_OPTIONS,
                index=PIVOT_ANCHOR_OPTIONS.index(pl_cfg.get("pivot_anchor", "daily")),
                key="pl_pivot_anchor",
            )
        with c2:
            atr_period = st.number_input("ATR Period", value=pl_cfg.get("atr_period", 14), min_value=1, key="pl_atr_period")
            atr_mult = st.number_input("ATR Multiplier", value=float(pl_cfg.get("atr_multiplier", 0.5)), min_value=0.1, key="pl_atr_mult")
            force_pl = st.checkbox("Force overwrite", value=False, key="pl_force")
            do_resample = st.checkbox("1. Resample (Tick → OHLCV)", value=True, key="pl_resample")
            do_features = st.checkbox("2. Features (OHLCV → matrix)", value=True, key="pl_features")
            do_labels = st.checkbox("3. Labels (ATR-based)", value=True, key="pl_labels")

        if st.button("▶ Chạy Pipeline", key="btn_pipeline", type="primary"):
            with st.spinner("Đang chạy pipeline..."):
                logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                logs: list[str] = []
                try:
                    _buf = io.StringIO()
                    with redirect_stdout(_buf), redirect_stderr(_buf):
                        if do_resample:
                            stats = resample_symbol_tf(symbol=pl_symbol or "XAUUSD", tf=pl_tf, force=force_pl)
                            logs.append(f"Resample: processed={stats['processed']} skipped={stats['skipped']} bars={stats['total_bars']:,}")
                        if do_features:
                            stats = run_feature_pipeline(
                                symbol=pl_symbol or "XAUUSD",
                                tf=pl_tf,
                                pivot_type=pivot_type,
                                pivot_anchor=pivot_anchor,
                                force=force_pl,
                            )
                            logs.append(f"Features: processed={stats['processed']} bars={stats['total_bars']:,} cols={stats['total_features']}")
                        if do_labels:
                            stats = run_label_pipeline(
                                symbol=pl_symbol or "XAUUSD",
                                tf=pl_tf,
                                atr_period=int(atr_period),
                                atr_mult=atr_mult,
                                force=force_pl,
                            )
                            logs.append(f"Labels: processed={stats['processed']} bars={stats['total_bars']:,}")
                    for line in logs:
                        st.write(f"✓ {line}")
                    st.success("Pipeline xong.")
                except Exception as e:
                    st.error(str(e))

    # --- 3. Train ---
    with st.expander("3. Train"):
        c1, c2 = st.columns([1, 1])
        with c1:
            tr_symbol = st.text_input("Symbol", value=symbol, key="tr_symbol")
            tr_tf = st.selectbox("Timeframe", options=TF_OPTIONS, index=TF_OPTIONS.index(tf), key="tr_tf")
            tr_label = st.selectbox("Label Column", options=LABEL_OPTIONS, index=LABEL_OPTIONS.index(label_col), key="tr_label")
            _backend = tr_cfg.get("backend", "mlf")
            backend = st.selectbox(
                "Backend",
                options=BACKEND_OPTIONS,
                index=BACKEND_OPTIONS.index(_backend) if _backend in BACKEND_OPTIONS else 0,
                key="tr_backend",
            )
        with c2:
            n_trials = st.number_input("Optuna Trials", value=tr_cfg.get("n_trials", 30), min_value=1, key="tr_trials")
            n_splits = st.number_input("CV Splits", value=tr_cfg.get("n_splits", 5), min_value=2, key="tr_splits")
            force_tr = st.checkbox("Force retrain", value=False, key="tr_force")

        if st.button("▶ Train", key="btn_train", type="primary"):
            with st.spinner("Đang train..."):
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
                    result, log = _run_with_capture(run_training, cfg_train)
                    if log:
                        st.code(log, language="text")
                    if result:
                        st.metric("Best CV F1 (macro)", f"{result.get('best_cv_f1_macro', 0):.4f}")
                        st.metric("Train F1 (macro)", f"{result.get('f1_macro_train', 0):.4f}")
                    st.success("Train xong.")
                except Exception as e:
                    st.error(str(e))

    # --- 4. Xem kết quả ---
    with st.expander("4. Xem kết quả"):
        c1, c2 = st.columns([1, 1])
        with c1:
            bt_symbol = st.text_input("Symbol", value=symbol, key="bt_symbol")
            bt_tf = st.selectbox("Timeframe", options=TF_OPTIONS, index=TF_OPTIONS.index(tf), key="bt_tf")
            bt_label = st.selectbox("Label Column", options=LABEL_OPTIONS, index=LABEL_OPTIONS.index(label_col), key="bt_label")
            capital = st.number_input("Initial Capital ($)", value=float(bt_cfg.get("initial_capital", 10000)), min_value=100.0, key="bt_capital")
            risk = st.number_input("Risk per Trade (%)", value=float(bt_cfg.get("risk_per_trade_pct", 1.0)), min_value=0.1, key="bt_risk")
        with c2:
            commission = st.number_input("Commission (pips)", value=float(bt_cfg.get("commission_pips", 0.1)), min_value=0.0, key="bt_commission")
            tp_r = st.number_input("Take Profit (R)", value=float(bt_cfg.get("tp_r", 1.5)), min_value=0.1, key="bt_tp")
            sl_r = st.number_input("Stop Loss (R)", value=float(bt_cfg.get("sl_r", 1.0)), min_value=0.1, key="bt_sl")

        if st.button("▶ Chạy Backtest", key="btn_backtest", type="primary"):
            with st.spinner("Đang chạy backtest..."):
                logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                eval_kw = dict(
                    symbol=bt_symbol or "XAUUSD",
                    tf=bt_tf,
                    label_col=bt_label,
                    initial_capital=capital,
                    risk_pct=risk,
                    commission=commission,
                    tp_r=tp_r,
                    sl_r=sl_r,
                )
                try:
                    model_results = run_model_backtest(**eval_kw)
                    if model_results is None:
                        results = run_full_eval(**eval_kw)
                        st.info("Không có model — chạy backtest trên labels.")
                        out_name = f"{bt_label}_R{int(tp_r * 10)}"
                    else:
                        results = model_results
                        out_name = f"model_{bt_label}_R{int(tp_r * 10)}"
                    if results:
                        cols = st.columns(4)
                        items = list(results.items())
                        for i, (k, v) in enumerate(items):
                            cols[i % 4].metric(k, v)
                        baseline = get_baseline_metrics(**eval_kw)
                        if baseline is not None:
                            st.divider()
                            try:
                                model_r_str = results.get("Net Profit (R)", "0")
                                model_r = float(model_r_str.replace("R", "").replace(",", "").strip())
                                base_r = baseline["total_r"]
                                diff = model_r - base_r
                                c1, c2 = st.columns(2)
                                c1.metric("Model (Net R)", f"{model_r:+.2f}R")
                                c2.metric("Labels (Net R)", f"{base_r:+.2f}R")
                                if diff > 0:
                                    st.success(f"Model tốt hơn +{diff:.1f}R")
                                elif diff < 0:
                                    st.warning(f"Labels tốt hơn {-diff:.1f}R")
                                else:
                                    st.info("Bằng nhau")
                            except (ValueError, KeyError):
                                pass
                        reports_dir = DEFAULT_PATHS.reports_dir(bt_symbol or "XAUUSD", bt_tf)
                        candlestick_path = reports_dir / f"{out_name}_candlestick.html"
                        equity_path = reports_dir / f"{out_name}_equity.png"
                        heatmap_path = reports_dir / f"{out_name}_heatmap.png"
                        if candlestick_path.exists():
                            html_str = candlestick_path.read_text()
                            st.components.v1.html(html_str, height=700, scrolling=True)
                        if equity_path.exists():
                            st.image(str(equity_path), caption="Equity Curve")
                        if heatmap_path.exists():
                            st.image(str(heatmap_path), caption="Session Performance Heatmap")
                        st.info(f"Biểu đồ: `{reports_dir}`")
                    st.success("Backtest xong.")
                except Exception as e:
                    st.error(str(e))


if __name__ == "__main__":
    main()
