# MLFX Documentation

Welcome to the MLFX documentation.

`MLFX` is an MLOps-style research pipeline for market data. The project covers the full Workflow from raw tick ingestion to feature engineering, model training, evaluation, and serving.

This page is the main English entrypoint for the documentation.

---

## Documentation Structure

The English docs are organized by purpose:

- **Getting Started** — for first-time readers and quick setup
- **Guides** — for operating the CLI and understanding Workflows
- **Reference** — for looking up fields, config keys, APIs, and terminology
- **Architecture** — for system design and backend-level technical structure
- **Meta** — for roadmap and project-status style documents

```text
docs/en/
├── README.md
├── getting-started/
│   ├── QUICKSTART.md
│   └── NOOB_GUIDE.md
├── guides/
│   ├── USAGE_GUIDE.md
│   ├── EVALUATION_GUIDE.md
│   └── TROUBLESHOOTING.md
├── reference/
│   ├── FEATURE_REFERENCE.md
│   ├── CONFIG_REFERENCE.md
│   ├── API_REFERENCE.md
│   └── GLOSSARY.md
├── architecture/
│   ├── ARCHITECTURE.md
│   └── BACKEND_COMPARISON.md
└── meta/
    └── ROADMAP.md
```

---

## Start Here

### If you are new to the repository
- [Quickstart](getting-started/QUICKSTART.md) — the shortest path to run the standard Workflow
- [Beginner Guide](getting-started/NOOB_GUIDE.md) — explains what the project does and why stage order matters

### If you want to operate the CLI
- [Usage Guide](guides/USAGE_GUIDE.md) — command-by-command operation guide
- [Evaluation Guide](guides/EVALUATION_GUIDE.md) — how to run evaluation and interpret reports
- [Troubleshooting](guides/TROUBLESHOOTING.md) — common setup, data, and runtime issues

### If you need technical reference
- [Feature Reference](reference/FEATURE_REFERENCE.md) — generated columns and feature meanings
- [Configuration Reference](reference/CONFIG_REFERENCE.md) — `config.toml` keys and CLI mappings
- [API Reference](reference/API_REFERENCE.md) — FastAPI serving endpoints
- [Glossary](reference/GLOSSARY.md) — common project and trading terms

### If you need system design details
- [Architecture](architecture/ARCHITECTURE.md) — data flow, module boundaries, training/evaluation/serving structure
- [Backend Comparison](architecture/BACKEND_COMPARISON.md) — backend trade-offs and selection guidance

### If you want roadmap / planning context
- [Roadmap](meta/ROADMAP.md)

---

## Recommended Reading Paths

### Path 1 — First-time setup
1. [Quickstart](getting-started/QUICKSTART.md)
2. [Beginner Guide](getting-started/NOOB_GUIDE.md)
3. [Usage Guide](guides/USAGE_GUIDE.md)

### Path 2 — Train and evaluate models
1. [Usage Guide](guides/USAGE_GUIDE.md)
2. [Feature Reference](reference/FEATURE_REFERENCE.md)
3. [Evaluation Guide](guides/EVALUATION_GUIDE.md)

### Path 3 — Understand the internals
1. [Architecture](architecture/ARCHITECTURE.md)
2. [Configuration Reference](reference/CONFIG_REFERENCE.md)
3. [API Reference](reference/API_REFERENCE.md)
4. [Backend Comparison](architecture/BACKEND_COMPARISON.md)

---

## Standard Workflow

The usual MLFX operating Workflow is:

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> serve / batch-predict
  -> drift
```

What each stage does:

- `download` — fetch raw tick data
- `qa` — audit raw data for gaps and anomalies
- `pipeline` — build OHLCV, features, and labels
- `train` — fit the selected backend and register artifacts
- `evaluate` — backtest signals and generate reports
- `benchmark` — compare multiple backends
- `serve` — start the inference API
- `batch-predict` — run offline prediction exports
- `drift` — compare recent distributions against reference data
- `drift-retrain` — drift detection with automatic retraining
- `profiles` — list workflow profiles
- `run-profile` — train + evaluate from a profile
- `run-all` — full end-to-end pipeline in one command
- `mlflow` — manage MLflow tracking server and migrate artifacts

For runnable commands, see [Quickstart](getting-started/QUICKSTART.md) and [Usage Guide](guides/USAGE_GUIDE.md).

---

## Environment Notes

- The repository is operated in a **Pixi-first** way
- Day-to-day commands should be run through `pixi run`
- Python and dependencies are managed through the project configuration
- The supported workflow does not require a separate `uv` or `venv` setup

Typical environment setup:

```bash
pixi install
```

Common entrypoints:

- `pixi run mlfx`
- `pixi run test`
- `pixi run verify`
- `pixi run clean-generated`

---

## Related Documentation

- Top-level docs index: [../README.md](../README.md)
- Vietnamese docs: [../vi/README.md](../vi/README.md)

---

## Conventions Used in This Docs Tree

- `README.md` files are navigation hubs, not full manuals
- `QUICKSTART.md` is the canonical fast-start document
- `NOOB_GUIDE.md` focuses on understanding the Workflow
- `USAGE_GUIDE.md` focuses on command usage and artifacts
- `REFERENCE` docs are the canonical source for fields, config keys, and APIs
- `ARCHITECTURE` docs explain internal design rather than day-to-day operation

---

## See Also

- [Quickstart](getting-started/QUICKSTART.md)
- [Usage Guide](guides/USAGE_GUIDE.md)
- [Architecture](architecture/ARCHITECTURE.md)
- [Troubleshooting](guides/TROUBLESHOOTING.md)
