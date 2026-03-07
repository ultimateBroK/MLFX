"""
ML_FX Textual TUI implemented in the `mlfx.app` package.
"""

from __future__ import annotations

import io
import logging
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    TabbedContent,
    TabPane,
)

from mlfx.config.paths import DEFAULT_PATHS
from mlfx.config.settings import load_config as shared_load_config
from mlfx.evaluation.runner import run_full_eval
from mlfx.ingestion.download import run_download_job
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.resampling import resample_symbol_tf
from mlfx.training.config import TrainingConfig
from mlfx.training.runner import run_training

CONFIG_FILE = DEFAULT_PATHS.config_file


def load_config() -> dict[str, Any]:
    """Load config.toml via the shared config layer."""
    return shared_load_config(CONFIG_FILE)


class _LogCapturer(io.StringIO):
    """Forward stdout/stderr writes to a RichLog widget."""

    def __init__(self, log_widget: RichLog, original: Any) -> None:
        super().__init__()
        self._log = log_widget
        self._original = original
        self._lock = threading.Lock()

    def write(self, s: str) -> int:  # type: ignore[override]
        if s and s.strip():
            stripped = s.rstrip("\n")
            if stripped:
                self._log.app.call_from_thread(self._log.write, stripped)
        try:
            self._original.write(s)
        except Exception:
            pass
        return len(s)

    def flush(self) -> None:
        try:
            self._original.flush()
        except Exception:
            pass


def _select_val(widget: Select, fallback: str) -> str:
    """Return Select value as str, or fallback if BLANK."""
    value = widget.value
    return fallback if value is Select.BLANK else str(value)


TF_OPTIONS = [
    ("1m", "1m"),
    ("5m", "5m"),
    ("15m", "15m"),
    ("30m", "30m"),
    ("1H", "1H"),
    ("2H", "2H"),
    ("4H", "4H"),
    ("1D", "1D"),
]
ASSET_CLASS_OPTIONS = [("Forex / Commodities (fx)", "fx"), ("Crypto 24/7", "crypto")]
BACKEND_OPTIONS = [
    ("MLForecast (mlf)", "mlf"),
    ("LSTM (lstm)", "lstm"),
    ("Transformer (transformer)", "transformer"),
    ("CNN-LSTM (cnn_lstm)", "cnn_lstm"),
    ("Online SGD (sgd)", "sgd"),
    ("Statistical Baselines (stats)", "stats"),
    ("NeuralForecast N-HiTS/N-BEATS (neuralforecast)", "neuralforecast"),
]
LABEL_OPTIONS = [
    ("label_5  (5 bars)", "label_5"),
    ("label_10 (10 bars)", "label_10"),
    ("label_20 (20 bars)", "label_20"),
]
PIVOT_TYPE_OPTIONS = [
    ("Traditional", "traditional"),
    ("Fibonacci", "fibonacci"),
    ("Woodie", "woodie"),
    ("Classic", "classic"),
    ("DeMark", "demark"),
    ("Camarilla", "camarilla"),
]
PIVOT_ANCHOR_OPTIONS = [
    ("Daily", "daily"),
    ("Weekly", "weekly"),
    ("Monthly", "monthly"),
]


class DownloadTab(TabPane):
    """Tab for downloading Dukascopy tick data."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("📥 Download Data", id="tab-download")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        download_cfg = self._cfg["download"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Download Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(value=download_cfg["symbol"], id="dl-symbol", placeholder="e.g. XAUUSD")
                yield Label("Asset Class", classes="field-label")
                yield Select(ASSET_CLASS_OPTIONS, value=download_cfg["asset_class"], id="dl-asset-class")
                yield Label("Start Year", classes="field-label")
                yield Input(value=str(download_cfg["start_year"]), id="dl-start-year", placeholder="2015")
                yield Label("Start Month (1–12)", classes="field-label")
                yield Input(value=str(download_cfg["start_month"]), id="dl-start-month", placeholder="1")
                yield Label("Max Concurrent Downloads", classes="field-label")
                yield Input(value=str(download_cfg["concurrency"]), id="dl-concurrency", placeholder="20")
                yield Checkbox("Force re-verify existing months", id="dl-force", value=False)
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Start Download", id="btn-download", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-download":
            return
        symbol = self.query_one("#dl-symbol", Input).value.strip() or "XAUUSD"
        asset_class = _select_val(self.query_one("#dl-asset-class", Select), "fx")
        start_year = int(self.query_one("#dl-start-year", Input).value or "2015")
        start_month = int(self.query_one("#dl-start-month", Input).value or "1")
        concurrency = int(self.query_one("#dl-concurrency", Input).value or "20")
        force = self.query_one("#dl-force", Checkbox).value
        self._run_download(symbol, asset_class, start_year, start_month, concurrency, force)

    @work(thread=True)
    def _run_download(
        self,
        symbol: str,
        asset_class: str,
        start_year: int,
        start_month: int,
        concurrency: int,
        force: bool,
    ) -> None:
        button = self.query_one("#btn-download", Button)
        self.app.call_from_thread(setattr, button, "disabled", True)
        self.app.call_from_thread(self._log.write, "[bold cyan]═══ Download started ═══[/]")
        try:
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                run_download_job(
                    symbol=symbol,
                    asset_class=asset_class,
                    start_year=start_year,
                    start_month=start_month,
                    concurrency=concurrency,
                    force=force,
                )
            self.app.call_from_thread(self._log.write, "[bold green]═══ Download complete ═══[/]")
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, button, "disabled", False)


class PipelineTab(TabPane):
    """Tab for running the ETL pipeline: resample → features → labels."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("🔄 Pipeline", id="tab-pipeline")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        pipeline_cfg = self._cfg["pipeline"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Pipeline Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(value=pipeline_cfg["symbol"], id="pl-symbol", placeholder="e.g. XAUUSD")
                yield Label("Timeframe", classes="field-label")
                yield Select(TF_OPTIONS, value=pipeline_cfg["timeframe"], id="pl-timeframe")
                yield Label("Pivot Type", classes="field-label")
                yield Select(PIVOT_TYPE_OPTIONS, value=pipeline_cfg["pivot_type"], id="pl-pivot-type")
                yield Label("Pivot Anchor", classes="field-label")
                yield Select(PIVOT_ANCHOR_OPTIONS, value=pipeline_cfg["pivot_anchor"], id="pl-pivot-anchor")
                yield Label("ATR Period", classes="field-label")
                yield Input(value=str(pipeline_cfg.get("atr_period", 14)), id="pl-atr-period")
                yield Label("ATR Multiplier", classes="field-label")
                yield Input(value=str(pipeline_cfg.get("atr_multiplier", 0.5)), id="pl-atr-multiplier")
                yield Checkbox("Force overwrite existing files", id="pl-force", value=False)
                yield Label("Steps to run:", classes="field-label")
                yield Checkbox("1. Resample (Tick → OHLCV)", id="pl-step-resample", value=True)
                yield Checkbox("2. Features  (OHLCV → feature matrix)", id="pl-step-features", value=True)
                yield Checkbox("3. Labels    (ATR-based LONG/SHORT/NEUTRAL)", id="pl-step-labels", value=True)
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Run Pipeline", id="btn-pipeline", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-pipeline":
            return
        symbol = self.query_one("#pl-symbol", Input).value.strip() or "XAUUSD"
        tf = _select_val(self.query_one("#pl-timeframe", Select), "1H")
        pivot_type = _select_val(self.query_one("#pl-pivot-type", Select), "traditional")
        pivot_anchor = _select_val(self.query_one("#pl-pivot-anchor", Select), "daily")
        atr_period = int(self.query_one("#pl-atr-period", Input).value or "14")
        atr_mult = float(self.query_one("#pl-atr-multiplier", Input).value or "0.5")
        force = self.query_one("#pl-force", Checkbox).value
        do_resample = self.query_one("#pl-step-resample", Checkbox).value
        do_features = self.query_one("#pl-step-features", Checkbox).value
        do_labels = self.query_one("#pl-step-labels", Checkbox).value
        self._run_pipeline(
            symbol,
            tf,
            pivot_type,
            pivot_anchor,
            atr_period,
            atr_mult,
            force,
            do_resample,
            do_features,
            do_labels,
        )

    @work(thread=True)
    def _run_pipeline(
        self,
        symbol: str,
        tf: str,
        pivot_type: str,
        pivot_anchor: str,
        atr_period: int,
        atr_mult: float,
        force: bool,
        do_resample: bool,
        do_features: bool,
        do_labels: bool,
    ) -> None:
        button = self.query_one("#btn-pipeline", Button)
        self.app.call_from_thread(setattr, button, "disabled", True)
        self.app.call_from_thread(self._log.write, "[bold cyan]═══ Pipeline started ═══[/]")
        try:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                if do_resample:
                    self.app.call_from_thread(self._log.write, "[yellow]Step 1/3: Resampling tick data...[/]")
                    stats = resample_symbol_tf(symbol=symbol, tf=tf, force=force)
                    self.app.call_from_thread(
                        self._log.write,
                        f"  ✓ Resample — processed={stats['processed']}  skipped={stats['skipped']}  bars={stats['total_bars']:,}",
                    )

                if do_features:
                    self.app.call_from_thread(self._log.write, "[yellow]Step 2/3: Building feature matrix...[/]")
                    stats = run_feature_pipeline(
                        symbol=symbol,
                        tf=tf,
                        pivot_type=pivot_type,
                        pivot_anchor=pivot_anchor,
                        force=force,
                    )
                    self.app.call_from_thread(
                        self._log.write,
                        f"  ✓ Features — processed={stats['processed']}  skipped={stats['skipped']}  bars={stats['total_bars']:,}  cols={stats['total_features']}",
                    )

                if do_labels:
                    self.app.call_from_thread(self._log.write, "[yellow]Step 3/3: Generating labels...[/]")
                    stats = run_label_pipeline(
                        symbol=symbol,
                        tf=tf,
                        atr_period=atr_period,
                        atr_mult=atr_mult,
                        force=force,
                    )
                    self.app.call_from_thread(
                        self._log.write,
                        f"  ✓ Labels  — processed={stats['processed']}  skipped={stats['skipped']}  bars={stats['total_bars']:,}",
                    )
            self.app.call_from_thread(self._log.write, "[bold green]═══ Pipeline complete ═══[/]")
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, button, "disabled", False)


class TrainTab(TabPane):
    """Tab for training model backends."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("🧠 Train Model", id="tab-train")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        train_cfg = self._cfg["train"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Training Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(value=train_cfg["symbol"], id="tr-symbol", placeholder="e.g. XAUUSD")
                yield Label("Timeframe", classes="field-label")
                yield Select(TF_OPTIONS, value=train_cfg["timeframe"], id="tr-timeframe")
                yield Label("Label Column", classes="field-label")
                yield Select(LABEL_OPTIONS, value=train_cfg["label_col"], id="tr-label-col")
                yield Label("Model Backend", classes="field-label")
                yield Select(BACKEND_OPTIONS, value=train_cfg["backend"], id="tr-backend")
                yield Label("Optuna Trials", classes="field-label")
                yield Input(value=str(train_cfg["n_trials"]), id="tr-n-trials", placeholder="30")
                yield Label("CV Splits (TimeSeriesSplit)", classes="field-label")
                yield Input(value=str(train_cfg["n_splits"]), id="tr-n-splits", placeholder="5")
                yield Checkbox("Force retrain (overwrite saved model)", id="tr-force", value=False)
                yield Checkbox("Compute SHAP values", id="tr-shap", value=True)
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Train", id="btn-train", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-train":
            return
        symbol = self.query_one("#tr-symbol", Input).value.strip() or "XAUUSD"
        tf = _select_val(self.query_one("#tr-timeframe", Select), "1H")
        label_col = _select_val(self.query_one("#tr-label-col", Select), "label_10")
        backend = _select_val(self.query_one("#tr-backend", Select), "mlf")
        n_trials = int(self.query_one("#tr-n-trials", Input).value or "30")
        n_splits = int(self.query_one("#tr-n-splits", Input).value or "5")
        force = self.query_one("#tr-force", Checkbox).value
        plot_shap = self.query_one("#tr-shap", Checkbox).value
        self._run_train(symbol, tf, label_col, backend, n_trials, n_splits, force, plot_shap)

    @work(thread=True)
    def _run_train(
        self,
        symbol: str,
        tf: str,
        label_col: str,
        backend: str,
        n_trials: int,
        n_splits: int,
        force: bool,
        plot_shap: bool,
    ) -> None:
        button = self.query_one("#btn-train", Button)
        self.app.call_from_thread(setattr, button, "disabled", True)
        self.app.call_from_thread(self._log.write, "[bold cyan]═══ Training started ═══[/]")
        try:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                cfg = TrainingConfig(
                    symbol=symbol,
                    tf=tf,
                    label_col=label_col,
                    backend=backend,
                    n_trials=n_trials,
                    n_splits=n_splits,
                    force=force,
                )
                result = run_training(cfg)
            if result:
                self.app.call_from_thread(
                    self._log.write,
                    f"  ✓ Best CV F1 (macro): [bold]{result.get('best_cv_f1_macro', 0):.4f}[/]",
                )
                self.app.call_from_thread(
                    self._log.write,
                    f"  ✓ Train F1 (macro):   [bold]{result.get('f1_macro_train', 0):.4f}[/]",
                )
            self.app.call_from_thread(self._log.write, "[bold green]═══ Training complete ═══[/]")
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, button, "disabled", False)


class BacktestTab(TabPane):
    """Tab for running the walk-forward backtest engine."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("📊 Backtest", id="tab-backtest")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        backtest_cfg = self._cfg["backtest"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Backtest Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(value=backtest_cfg["symbol"], id="bt-symbol", placeholder="e.g. XAUUSD")
                yield Label("Timeframe", classes="field-label")
                yield Select(TF_OPTIONS, value=backtest_cfg["timeframe"], id="bt-timeframe")
                yield Label("Label Column", classes="field-label")
                yield Select(LABEL_OPTIONS, value=backtest_cfg["label_col"], id="bt-label-col")
                yield Label("Initial Capital ($)", classes="field-label")
                yield Input(value=str(backtest_cfg.get("initial_capital", 10000.0)), id="bt-capital")
                yield Label("Risk per Trade (%)", classes="field-label")
                yield Input(value=str(backtest_cfg.get("risk_per_trade_pct", 1.0)), id="bt-risk")
                yield Label("Commission (pips/trade)", classes="field-label")
                yield Input(value=str(backtest_cfg.get("commission_pips", 0.1)), id="bt-commission")
                yield Label("Take Profit (R)", classes="field-label")
                yield Input(value=str(backtest_cfg.get("tp_r", 1.5)), id="bt-tp")
                yield Label("Stop Loss (R)", classes="field-label")
                yield Input(value=str(backtest_cfg.get("sl_r", 1.0)), id="bt-sl")
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Run Backtest", id="btn-backtest", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-backtest":
            return
        symbol = self.query_one("#bt-symbol", Input).value.strip() or "XAUUSD"
        tf = _select_val(self.query_one("#bt-timeframe", Select), "1H")
        label_col = _select_val(self.query_one("#bt-label-col", Select), "label_10")
        capital = float(self.query_one("#bt-capital", Input).value or "10000.0")
        risk = float(self.query_one("#bt-risk", Input).value or "1.0")
        commission = float(self.query_one("#bt-commission", Input).value or "0.1")
        tp_r = float(self.query_one("#bt-tp", Input).value or "1.5")
        sl_r = float(self.query_one("#bt-sl", Input).value or "1.0")
        self._run_backtest(symbol, tf, label_col, capital, risk, commission, tp_r, sl_r)

    @work(thread=True)
    def _run_backtest(
        self,
        symbol: str,
        tf: str,
        label_col: str,
        capital: float,
        risk: float,
        commission: float,
        tp_r: float,
        sl_r: float,
    ) -> None:
        button = self.query_one("#btn-backtest", Button)
        self.app.call_from_thread(setattr, button, "disabled", True)
        self.app.call_from_thread(self._log.write, "[bold cyan]═══ Backtest started ═══[/]")
        try:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                results = run_full_eval(
                    symbol=symbol,
                    tf=tf,
                    label_col=label_col,
                    initial_capital=capital,
                    risk_pct=risk,
                    commission=commission,
                    tp_r=tp_r,
                    sl_r=sl_r,
                )
            if results:
                for key, value in results.items():
                    self.app.call_from_thread(self._log.write, f"  {key}: {value}")
            self.app.call_from_thread(self._log.write, "[bold green]═══ Backtest complete ═══[/]")
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, button, "disabled", False)


class MLFXApp(App):
    """ML_FX — ICT-Based Price Prediction System. Interactive TUI."""

    TITLE = "ML_FX — ICT Price Prediction"
    CSS_PATH = str(DEFAULT_PATHS.project_root / "main.tcss")
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Dark Mode"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._config = load_config()
        self._dl_log = RichLog(highlight=True, markup=True, wrap=True, id="log-download")
        self._pl_log = RichLog(highlight=True, markup=True, wrap=True, id="log-pipeline")
        self._tr_log = RichLog(highlight=True, markup=True, wrap=True, id="log-train")
        self._bt_log = RichLog(highlight=True, markup=True, wrap=True, id="log-backtest")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            yield DownloadTab(self._config, self._dl_log)
            yield PipelineTab(self._config, self._pl_log)
            yield TrainTab(self._config, self._tr_log)
            yield BacktestTab(self._config, self._bt_log)
        yield Footer()

    def on_mount(self) -> None:
        self._dl_log.write(
            "[bold]Welcome to [cyan]ML_FX[/] TUI[/]\n"
            "Config loaded from [italic]config.toml[/] — forms pre-filled.\n"
            "Select a tab above to get started.\n"
        )


def main() -> None:
    """Launch the package-native TUI."""
    MLFXApp().run()
