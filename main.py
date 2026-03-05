"""
main.py
=======
ML_FX — Interactive Terminal UI (TUI) built with Textual.

Usage:
    pixi run python main.py

Features:
    - 4 tabs: Download Data | Pipeline | Train Model | Backtest
    - Reads config.toml at startup to pre-fill all forms
    - Runs heavy tasks in background threads (non-blocking)
    - Streams real-time log output into a RichLog panel
    - Dark/light mode toggle with `d`, quit with `q`
"""

from __future__ import annotations

import io
import logging
import sys
import threading
import tomllib
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
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

# ── Config ─────────────────────────────────────────────────────────────────────

CONFIG_FILE = Path("config.toml")

_DEFAULT_CONFIG: dict[str, Any] = {
    "download": {
        "symbol": "XAUUSD",
        "asset_class": "fx",
        "start_year": 2015,
        "start_month": 1,
        "concurrency": 20,
    },
    "pipeline": {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "pivot_type": "traditional",
        "pivot_anchor": "daily",
    },
    "train": {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "label_col": "label_10",
        "backend": "xgb",
        "n_trials": 30,
        "n_splits": 5,
    },
    "backtest": {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "label_col": "label_10",
    },
}


def load_config() -> dict[str, Any]:
    """Load config.toml; fall back to built-in defaults if file missing."""
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("rb") as f:
                data = tomllib.load(f)
            merged: dict[str, Any] = {}
            for section, defaults in _DEFAULT_CONFIG.items():
                merged[section] = {**defaults, **data.get(section, {})}
            return merged
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Could not parse config.toml: {exc} — using defaults")
    return _DEFAULT_CONFIG


# ── Log helper ─────────────────────────────────────────────────────────────────


class _LogCapturer(io.StringIO):
    """StringIO subclass that forwards every write() call to a RichLog widget."""

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


# ── helpers ────────────────────────────────────────────────────────────────────


def _select_val(widget: Select, fallback: str) -> str:
    """Return Select value as str, or fallback if BLANK."""
    v = widget.value
    return fallback if v is Select.BLANK else str(v)


# ── Timeframe / option constants ───────────────────────────────────────────────

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
BACKEND_OPTIONS = [("XGBoost (xgb)", "xgb"), ("LightGBM (lgb)", "lgb")]
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


# ── Tab: Download Data ─────────────────────────────────────────────────────────


class DownloadTab(TabPane):
    """Tab for downloading Dukascopy tick data."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("📥 Download Data", id="tab-download")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        d = self._cfg["download"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Download Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(
                    value=d["symbol"], id="dl-symbol", placeholder="e.g. XAUUSD"
                )
                yield Label("Asset Class", classes="field-label")
                yield Select(
                    ASSET_CLASS_OPTIONS, value=d["asset_class"], id="dl-asset-class"
                )
                yield Label("Start Year", classes="field-label")
                yield Input(
                    value=str(d["start_year"]), id="dl-start-year", placeholder="2015"
                )
                yield Label("Start Month (1–12)", classes="field-label")
                yield Input(
                    value=str(d["start_month"]), id="dl-start-month", placeholder="1"
                )
                yield Label("Max Concurrent Downloads", classes="field-label")
                yield Input(
                    value=str(d["concurrency"]), id="dl-concurrency", placeholder="20"
                )
                yield Checkbox(
                    "Force re-verify existing months", id="dl-force", value=False
                )
                with Horizontal(classes="btn-row"):
                    yield Button(
                        "▶ Start Download", id="btn-download", variant="primary"
                    )
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-download":
            # Read all form values on the main thread BEFORE entering the worker
            symbol = self.query_one("#dl-symbol", Input).value.strip() or "XAUUSD"
            asset_class = _select_val(self.query_one("#dl-asset-class", Select), "fx")
            start_year = int(self.query_one("#dl-start-year", Input).value or "2015")
            start_month = int(self.query_one("#dl-start-month", Input).value or "1")
            concurrency = int(self.query_one("#dl-concurrency", Input).value or "20")
            force = self.query_one("#dl-force", Checkbox).value
            self._run_download(
                symbol, asset_class, start_year, start_month, concurrency, force
            )

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
        btn = self.query_one("#btn-download", Button)
        self.app.call_from_thread(setattr, btn, "disabled", True)
        self.app.call_from_thread(
            self._log.write, "[bold cyan]═══ Download started ═══[/]"
        )
        try:
            from pipeline import download_data as dd
            import datetime
            import os

            dd.CONFIG.update(
                {
                    "SYMBOL": symbol,
                    "START_YEAR": start_year,
                    "START_MONTH": start_month,
                    "ASSET_CLASS": asset_class,
                    "MAX_CONCURRENT": concurrency,
                    "FORCE": force,
                    "OUTPUT_DIR": f"data/raw/{symbol}",
                    "STATE_FILE": f"data/raw/{symbol}/completed_months.json",
                }
            )
            os.makedirs(dd.CONFIG["OUTPUT_DIR"], exist_ok=True)

            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                now = datetime.datetime.now()
                state = dd.migrate_old_markers(dd.load_state())
                for year in range(start_year, now.year + 1):
                    m_start = start_month if year == start_year else 1
                    m_end = now.month if year == now.year else 12
                    for month in range(m_start, m_end + 1):
                        key = f"{year}-{month:02d}"
                        file_path = f"{dd.CONFIG['OUTPUT_DIR']}/{key}.parquet"
                        is_past = not (year == now.year and month == now.month)
                        entry = state.get(key)
                        if (
                            is_past
                            and entry
                            and entry["missing_hours"] == 0
                            and os.path.exists(file_path)
                            and not force
                        ):
                            print(
                                f"Skip     {key}  rows={entry['rows']:>10,}  missing=0 ✓"
                            )
                            continue
                        if os.path.exists(file_path):
                            print(f"Checking {key}  ...")
                            rows, missing = dd.repair_month(year, month, file_path)
                            flag = (
                                "✓ full" if missing == 0 else f"⚠ {missing} hrs missing"
                            )
                            print(f"   {key}  rows={rows:>10,}  {flag}")
                            if is_past:
                                state[key] = {"rows": rows, "missing_hours": missing}
                                dd.save_state(state)
                            continue
                        print(f"Download {key} ...", end=" ", flush=True)
                        frames, timed_out = dd.fetch_hours(
                            dd.all_slots(year, month), month
                        )
                        if frames:
                            import polars as pl

                            df = dd.to_datetime_df(
                                pl.concat(frames).sort("timestamp_ms")
                            )
                            df.write_parquet(file_path)
                            print(f"Saved {len(df):,} rows.")
                        else:
                            print("No data found.")
                        if is_past:
                            rows = len(df) if frames else 0
                            state[key] = {"rows": rows, "missing_hours": timed_out}
                            dd.save_state(state)

            self.app.call_from_thread(
                self._log.write, "[bold green]═══ Download complete ═══[/]"
            )
        except Exception as exc:
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, btn, "disabled", False)


# ── Tab: Pipeline ──────────────────────────────────────────────────────────────


class PipelineTab(TabPane):
    """Tab for running the full ETL pipeline: resample → features → labels."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("🔄 Pipeline", id="tab-pipeline")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        p = self._cfg["pipeline"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Pipeline Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(
                    value=p["symbol"], id="pl-symbol", placeholder="e.g. XAUUSD"
                )
                yield Label("Timeframe", classes="field-label")
                yield Select(TF_OPTIONS, value=p["timeframe"], id="pl-timeframe")
                yield Label("Pivot Type", classes="field-label")
                yield Select(
                    PIVOT_TYPE_OPTIONS, value=p["pivot_type"], id="pl-pivot-type"
                )
                yield Label("Pivot Anchor", classes="field-label")
                yield Select(
                    PIVOT_ANCHOR_OPTIONS, value=p["pivot_anchor"], id="pl-pivot-anchor"
                )
                yield Checkbox(
                    "Force overwrite existing files", id="pl-force", value=False
                )
                yield Label("Steps to run:", classes="field-label")
                yield Checkbox(
                    "1. Resample (Tick → OHLCV)", id="pl-step-resample", value=True
                )
                yield Checkbox(
                    "2. Features  (OHLCV → feature matrix)",
                    id="pl-step-features",
                    value=True,
                )
                yield Checkbox(
                    "3. Labels    (ATR-based LONG/SHORT/NEUTRAL)",
                    id="pl-step-labels",
                    value=True,
                )
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Run Pipeline", id="btn-pipeline", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pipeline":
            symbol = self.query_one("#pl-symbol", Input).value.strip() or "XAUUSD"
            tf = _select_val(self.query_one("#pl-timeframe", Select), "1H")
            pivot_type = _select_val(
                self.query_one("#pl-pivot-type", Select), "traditional"
            )
            pivot_anchor = _select_val(
                self.query_one("#pl-pivot-anchor", Select), "daily"
            )
            force = self.query_one("#pl-force", Checkbox).value
            do_resample = self.query_one("#pl-step-resample", Checkbox).value
            do_features = self.query_one("#pl-step-features", Checkbox).value
            do_labels = self.query_one("#pl-step-labels", Checkbox).value
            self._run_pipeline(
                symbol,
                tf,
                pivot_type,
                pivot_anchor,
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
        force: bool,
        do_resample: bool,
        do_features: bool,
        do_labels: bool,
    ) -> None:
        btn = self.query_one("#btn-pipeline", Button)
        self.app.call_from_thread(setattr, btn, "disabled", True)
        self.app.call_from_thread(
            self._log.write, "[bold cyan]═══ Pipeline started ═══[/]"
        )
        try:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                if do_resample:
                    self.app.call_from_thread(
                        self._log.write, "[yellow]Step 1/3: Resampling tick data...[/]"
                    )
                    from pipeline.resample import resample_symbol_tf

                    stats = resample_symbol_tf(symbol=symbol, tf=tf, force=force)
                    self.app.call_from_thread(
                        self._log.write,
                        f"  ✓ Resample — processed={stats['processed']}  "
                        f"skipped={stats['skipped']}  bars={stats['total_bars']:,}",
                    )

                if do_features:
                    self.app.call_from_thread(
                        self._log.write,
                        "[yellow]Step 2/3: Building feature matrix...[/]",
                    )
                    from pipeline.features import run_feature_pipeline

                    stats = run_feature_pipeline(
                        symbol=symbol,
                        tf=tf,
                        pivot_type=pivot_type,
                        pivot_anchor=pivot_anchor,
                        force=force,
                    )
                    self.app.call_from_thread(
                        self._log.write,
                        f"  ✓ Features — processed={stats['processed']}  "
                        f"skipped={stats['skipped']}  bars={stats['total_bars']:,}  "
                        f"cols={stats['total_features']}",
                    )

                if do_labels:
                    self.app.call_from_thread(
                        self._log.write, "[yellow]Step 3/3: Generating labels...[/]"
                    )
                    from pipeline.labels import run_label_pipeline

                    stats = run_label_pipeline(symbol=symbol, tf=tf, force=force)
                    self.app.call_from_thread(
                        self._log.write,
                        f"  ✓ Labels  — processed={stats['processed']}  "
                        f"skipped={stats['skipped']}  bars={stats['total_bars']:,}",
                    )

            self.app.call_from_thread(
                self._log.write, "[bold green]═══ Pipeline complete ═══[/]"
            )
        except Exception as exc:
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, btn, "disabled", False)


# ── Tab: Train Model ───────────────────────────────────────────────────────────


class TrainTab(TabPane):
    """Tab for training ML models (XGBoost / LightGBM)."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("🧠 Train Model", id="tab-train")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        t = self._cfg["train"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Training Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(
                    value=t["symbol"], id="tr-symbol", placeholder="e.g. XAUUSD"
                )
                yield Label("Timeframe", classes="field-label")
                yield Select(TF_OPTIONS, value=t["timeframe"], id="tr-timeframe")
                yield Label("Label Column", classes="field-label")
                yield Select(LABEL_OPTIONS, value=t["label_col"], id="tr-label-col")
                yield Label("Model Backend", classes="field-label")
                yield Select(BACKEND_OPTIONS, value=t["backend"], id="tr-backend")
                yield Label("Optuna Trials", classes="field-label")
                yield Input(
                    value=str(t["n_trials"]), id="tr-n-trials", placeholder="30"
                )
                yield Label("CV Splits (TimeSeriesSplit)", classes="field-label")
                yield Input(value=str(t["n_splits"]), id="tr-n-splits", placeholder="5")
                yield Checkbox(
                    "Force retrain (overwrite saved model)", id="tr-force", value=False
                )
                yield Checkbox("Compute SHAP values", id="tr-shap", value=True)
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Train", id="btn-train", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-train":
            symbol = self.query_one("#tr-symbol", Input).value.strip() or "XAUUSD"
            tf = _select_val(self.query_one("#tr-timeframe", Select), "1H")
            label_col = _select_val(self.query_one("#tr-label-col", Select), "label_10")
            backend = _select_val(self.query_one("#tr-backend", Select), "xgb")
            n_trials = int(self.query_one("#tr-n-trials", Input).value or "30")
            n_splits = int(self.query_one("#tr-n-splits", Input).value or "5")
            force = self.query_one("#tr-force", Checkbox).value
            plot_shap = self.query_one("#tr-shap", Checkbox).value
            self._run_train(
                symbol, tf, label_col, backend, n_trials, n_splits, force, plot_shap
            )

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
        btn = self.query_one("#btn-train", Button)
        self.app.call_from_thread(setattr, btn, "disabled", True)
        self.app.call_from_thread(
            self._log.write, "[bold cyan]═══ Training started ═══[/]"
        )
        try:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                from models.gradient_boost import run_gradient_boost

                result = run_gradient_boost(
                    symbol=symbol,
                    tf=tf,
                    label_col=label_col,
                    backend=backend,
                    n_trials=n_trials,
                    n_splits=n_splits,
                    force=force,
                    plot_shap=plot_shap,
                )
            if result:
                self.app.call_from_thread(
                    self._log.write,
                    f"  ✓ Best CV F1 (macro): [bold]{result.get('best_cv_f1_macro', 0):.4f}[/]",
                )
                self.app.call_from_thread(
                    self._log.write,
                    f"  ✓ Train F1 (macro):   [bold]{result.get('f1_macro_train', 0):.4f}[/]",
                )
            self.app.call_from_thread(
                self._log.write, "[bold green]═══ Training complete ═══[/]"
            )
        except Exception as exc:
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, btn, "disabled", False)


# ── Tab: Backtest ──────────────────────────────────────────────────────────────


class BacktestTab(TabPane):
    """Tab for running the walk-forward backtest engine."""

    def __init__(self, cfg: dict, log: RichLog) -> None:
        super().__init__("📊 Backtest", id="tab-backtest")
        self._cfg = cfg
        self._log = log

    def compose(self) -> ComposeResult:
        b = self._cfg["backtest"]
        with Horizontal(classes="tab-body"):
            with Vertical(classes="form-panel"):
                yield Label("Backtest Settings", classes="form-title")
                yield Label("Symbol", classes="field-label")
                yield Input(
                    value=b["symbol"], id="bt-symbol", placeholder="e.g. XAUUSD"
                )
                yield Label("Timeframe", classes="field-label")
                yield Select(TF_OPTIONS, value=b["timeframe"], id="bt-timeframe")
                yield Label("Label Column", classes="field-label")
                yield Select(LABEL_OPTIONS, value=b["label_col"], id="bt-label-col")
                yield Label("Commission (pips)", classes="field-label")
                yield Input(value="0.1", id="bt-commission", placeholder="0.1")
                with Horizontal(classes="btn-row"):
                    yield Button("▶ Run Backtest", id="btn-backtest", variant="primary")
            yield self._log

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-backtest":
            symbol = self.query_one("#bt-symbol", Input).value.strip() or "XAUUSD"
            tf = _select_val(self.query_one("#bt-timeframe", Select), "1H")
            label_col = _select_val(self.query_one("#bt-label-col", Select), "label_10")
            commission = float(self.query_one("#bt-commission", Input).value or "0.1")
            self._run_backtest(symbol, tf, label_col, commission)

    @work(thread=True)
    def _run_backtest(
        self,
        symbol: str,
        tf: str,
        label_col: str,
        commission: float,
    ) -> None:
        btn = self.query_one("#btn-backtest", Button)
        self.app.call_from_thread(setattr, btn, "disabled", True)
        self.app.call_from_thread(
            self._log.write, "[bold cyan]═══ Backtest started ═══[/]"
        )
        try:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
            capturer = _LogCapturer(self._log, sys.stdout)
            with redirect_stdout(capturer), redirect_stderr(capturer):  # type: ignore[arg-type]
                from eval.run_eval import run_full_eval  # type: ignore[import]

                results = run_full_eval(
                    symbol=symbol, tf=tf, label_col=label_col, commission=commission
                )
            if results:
                for k, v in results.items():
                    self.app.call_from_thread(self._log.write, f"  {k}: {v}")
            self.app.call_from_thread(
                self._log.write, "[bold green]═══ Backtest complete ═══[/]"
            )
        except ImportError:
            self.app.call_from_thread(
                self._log.write,
                "[yellow]⚠ eval.run_eval not yet wired — run directly:\n"
                "  pixi run python eval/run_eval.py[/]",
            )
        except Exception as exc:
            self.app.call_from_thread(self._log.write, f"[bold red]Error: {exc}[/]")
        finally:
            self.app.call_from_thread(setattr, btn, "disabled", False)


# ── Main App ───────────────────────────────────────────────────────────────────


class MLFXApp(App):
    """ML_FX — ICT-Based Price Prediction System. Interactive TUI."""

    TITLE = "ML_FX — ICT Price Prediction"
    CSS_PATH = "main.tcss"

    # NOTE: `d` uses Textual's built-in `action_toggle_dark` — no override needed.
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Dark Mode"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._config = load_config()
        self._dl_log = RichLog(
            highlight=True, markup=True, wrap=True, id="log-download"
        )
        self._pl_log = RichLog(
            highlight=True, markup=True, wrap=True, id="log-pipeline"
        )
        self._tr_log = RichLog(highlight=True, markup=True, wrap=True, id="log-train")
        self._bt_log = RichLog(
            highlight=True, markup=True, wrap=True, id="log-backtest"
        )

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


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = MLFXApp()
    app.run()
