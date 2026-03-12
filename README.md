# MLFX

> Local-first, Pixi-first MLOps pipeline for market data research, feature engineering, forecasting, evaluation, and serving.

[![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)](#requirements)
[![Pixi](https://img.shields.io/badge/workflow-pixi-7A4DFF)](#quickstart)
[![Platform](https://img.shields.io/badge/platform-linux--64-1793D1?logo=linux&logoColor=white)](#requirements)
[![Docs](https://img.shields.io/badge/docs-bilingual-brightgreen)](docs/README.md)
[![License](https://img.shields.io/badge/license-open--source-blue)](#license)
[![Stars](https://img.shields.io/github/stars/ultimateBroK/MLFX?style=social)](https://github.com/ultimateBroK/MLFX/stargazers)

MLFX helps you build an end-to-end market prediction workflow on your own machine:

- 📥 download historical tick data
- 🧪 validate and resample it into OHLCV
- 🧩 engineer features and labels
- 🤖 train multiple forecasting backends
- 📊 benchmark and evaluate results
- 🚀 serve predictions and monitor drift

If you want a clean, hackable research stack instead of a pile of notebooks or a black-box hosted platform, MLFX is built for that.

> ⭐ If MLFX is useful to you, give the repo a star — it helps more builders discover the project.

---

## Why MLFX?

Most projects force you to choose between:

- **quick scripts** that are hard to maintain
- **trading frameworks** that are great at execution but less opinionated about ML workflows
- **hosted MLOps tools** that are convenient but reduce control

MLFX sits in the middle:

- 🏠 **Local-first** — your data, artifacts, and workflow stay under your control
- 🔁 **Reproducible** — config-driven, Pixi-managed, CLI-first operation
- 🧱 **Modular** — ingestion, pipeline, training, evaluation, serving, and monitoring are separated cleanly
- 🔬 **Research-friendly** — easy to compare backends, inspect artifacts, and iterate
- 🌍 **Open-source approachable** — readable project structure, documented workflows, bilingual docs

---

## What you can do with it

With MLFX, you can:

- 📈 ingest historical market data from Dukascopy
- ⏱️ resample raw ticks into multi-timeframe OHLCV datasets
- 🛠️ build technical and context-aware features
- 🏷️ generate labels for supervised learning
- ⚙️ train and compare multiple model families
- 🧾 run backtests and export reports
- 🌐 serve inference through an API
- 🚨 detect feature drift in production-like workflows

---

## Core workflow

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> benchmark
  -> serve / batch-predict
  -> drift
```

### What each step means

- `download` — fetch raw tick data from Dukascopy
- `qa` — inspect raw data for gaps and anomalies
- `pipeline` — build OHLCV, features, and labels
- `train` — train a selected backend and persist artifacts
- `evaluate` — backtest outputs and generate reports
- `benchmark` — compare multiple backends consistently
- `serve` — start the inference API
- `batch-predict` — export offline prediction results
- `drift` — compare recent feature distributions against a reference baseline

---

## Highlights

- ✨ Unified CLI: `mlfx`
- 🟣 Pixi-first developer workflow
- 📥 Historical tick ingestion
- 🧪 QA + resampling + labeling pipeline
- 🤖 Multiple training backends
- 📊 Evaluation + reporting + benchmark flow
- ⚡ FastAPI serving layer
- 👀 Drift monitoring workflow
- 🌐 Bilingual documentation: English + Vietnamese

---

## Available backends

| Backend | Description |
| --- | --- |
| `mlf` | MLForecast + LightGBM baseline |
| `lstm` | PyTorch LSTM |
| `bilstm` | Bidirectional LSTM |
| `transformer` | Transformer encoder |
| `cnn_lstm` | CNN + LSTM hybrid |
| `sgd` | Online `SGDClassifier` baseline |
| `stats` | Statistical forecasting baselines |
| `neuralforecast` | NeuralForecast family |

MLFX is designed so you can compare these approaches inside one consistent project structure instead of rebuilding the same plumbing every time.

---

## Quickstart

### Requirements

- Linux `x86_64` / `linux-64`
- [Pixi](https://pixi.sh/) installed
- no separate `venv` or `uv` setup needed for the standard workflow

### Install environment

```bash
pixi install
```

### Run a minimal end-to-end flow

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

After `evaluate`, MLFX prints summary metrics and points you to generated report artifacts.

For the full onboarding flow, read:

- English: [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
- Tiếng Việt: [docs/vi/getting-started/QUICKSTART.md](docs/vi/getting-started/QUICKSTART.md)

---

## Common commands

```bash
pixi run mlfx
pixi run test
pixi run verify
pixi run clean-generated
```

### Command reference

- `pixi run mlfx` — unified CLI entrypoint
- `pixi run test` — run the full test suite
- `pixi run verify` — run core smoke/contract checks
- `pixi run clean-generated` — safely remove common generated artifacts and caches

---

## Project structure

```text
MLFX/
├── mlfx/
│   ├── app/            # CLI entrypoints
│   ├── config/         # config loading and path policy
│   ├── ingestion/      # historical data download
│   ├── pipeline/       # qa, resampling, features, labels
│   ├── features/       # feature modules
│   ├── training/       # backend training system
│   ├── evaluation/     # backtesting and reports
│   ├── tracking/       # experiment tracking
│   ├── registry/       # model registry
│   ├── serving/        # FastAPI inference layer
│   └── monitoring/     # drift detection and monitoring
├── docs/               # bilingual documentation hub
├── data/               # raw and processed datasets
├── outputs/            # models, reports, predictions, monitoring outputs
├── tests/              # tests and integration coverage
├── Dockerfile
├── docker-compose.yml
├── config.toml
└── pyproject.toml
```

---

## Generated artifacts

MLFX keeps outputs organized so experiments stay inspectable:

- `data/raw/{symbol}/` — downloaded raw tick data
- `data/ohlcv/{symbol}/{tf}/` — resampled OHLCV parquet files
- `data/features/{symbol}/{tf}/` — feature datasets
- `data/labels/{symbol}/{tf}/` — labeled datasets
- `outputs/models/{symbol}/{tf}/` — trained model artifacts and metadata
- `outputs/reports/{symbol}/{tf}/` — evaluation reports
- `outputs/predictions/{symbol}/{tf}/` — batch prediction outputs
- `outputs/monitoring/{symbol}/{tf}/` — drift references and alerts

---

## Documentation

### Start here

- Docs hub: [docs/README.md](docs/README.md)
- English docs: [docs/en/README.md](docs/en/README.md)
- Vietnamese docs: [docs/vi/README.md](docs/vi/README.md)

### Recommended reading

**If you're new**
- [English Quickstart](docs/en/getting-started/QUICKSTART.md)
- [Vietnamese Quickstart](docs/vi/getting-started/QUICKSTART.md)
- [Beginner Guide (EN)](docs/en/getting-started/NOOB_GUIDE.md)
- [Beginner Guide (VI)](docs/vi/getting-started/NOOB_GUIDE.md)

**If you want to use the CLI**
- [Usage Guide (EN)](docs/en/guides/USAGE_GUIDE.md)
- [Usage Guide (VI)](docs/vi/guides/USAGE_GUIDE.md)

**If you want to understand evaluation**
- [Evaluation Guide (EN)](docs/en/guides/EVALUATION_GUIDE.md)
- [Evaluation Guide (VI)](docs/vi/guides/EVALUATION_GUIDE.md)

**If you want architecture details**
- [Architecture (EN)](docs/en/architecture/ARCHITECTURE.md)
- [Architecture (VI)](docs/vi/architecture/ARCHITECTURE.md)
- [Backend Comparison (EN)](docs/en/architecture/BACKEND_COMPARISON.md)
- [Backend Comparison (VI)](docs/vi/architecture/BACKEND_COMPARISON.md)

**Project planning**
- [Roadmap (EN)](docs/en/meta/ROADMAP.md)
- [Roadmap (VI)](docs/vi/meta/ROADMAP.md)
- [TODO (EN)](docs/en/meta/TODO.md)
- [TODO (VI)](docs/vi/meta/TODO.md)

---

## Who is this for?

MLFX is a good fit if you are:

- a solo quant or researcher who wants a structured local workflow
- an engineer tired of rewriting data/training/evaluation glue code
- someone comparing classical ML, deep learning, and forecasting backends
- an open-source user who values control, reproducibility, and inspectable artifacts

MLFX may be less ideal if you only want:
- a plug-and-play trading bot with zero setup
- a cloud-managed SaaS workflow
- an execution-only framework without ML experimentation needs

---

## Current direction

MLFX already covers the core research loop well.

The next major improvements are around:

- serving reliability
- cleaner inference contracts
- retry and failure isolation
- stronger observability
- broader backend experimentation
- improved benchmark consistency

See the roadmap for details:
- [English roadmap](docs/en/meta/ROADMAP.md)
- [Vietnamese roadmap](docs/vi/meta/ROADMAP.md)

---

## Contributing

Contributions are welcome.

If you like the direction of the project, a ⭐ on GitHub is one of the easiest ways to support it.

Good contribution areas include:

- new model backends
- feature engineering improvements
- live data adapters
- evaluation/reporting improvements
- serving hardening
- documentation polish
- tests and reproducibility improvements

If you're exploring the repo for the first time, start with:

- [docs/README.md](docs/README.md)
- [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
- [docs/en/architecture/ARCHITECTURE.md](docs/en/architecture/ARCHITECTURE.md)

---

## Author

**Hieu Nguyen**  
GitHub: [@ultimateBroK](https://github.com/ultimateBroK)

---

## License

Please add your project license here if it is not already defined in the repository metadata.
