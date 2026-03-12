# MLFX – Task List

> **Version:** aligned with [ROADMAP.md](ROADMAP.md).  
> Sprint-based task list; see [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) to understand the system design.

## SPRINT 1: FOUNDATION

> **Goal:** Build a reliable end-to-end baseline workflow for data ingestion, preprocessing, training, and evaluation.
>
> **Dependencies:** None.
>
> **Estimated duration:** 1–2 weeks.

### Project setup

- [x] Initialize the Python project with `pixi`
- [x] Create `README.md` and the initial documentation structure
- [x] Configure `.gitignore`
- [x] Define the base project layout for `mlfx`, `tests`, `data`, and `outputs`
- [x] Add `pyproject.toml` and core development dependencies

### Market data ingestion

- [x] Build the Dukascopy downloader in `mlfx.ingestion`
- [x] Support monthly raw tick downloads
- [x] Persist raw data as Parquet files
- [x] Track completed downloads with download state files
- [x] Add retry and recovery behavior for ingestion failures

### Data quality and preprocessing

- [x] Implement raw data QA checks
- [x] Detect gaps and anomalies in tick data
- [x] Build OHLCV resampling logic
- [x] Normalize time handling for pipeline stages
- [x] Organize processed outputs under stable directory conventions

### Core pipeline

- [x] Implement feature engineering pipeline in `mlfx.pipeline`
- [x] Add labeling pipeline for prediction targets
- [x] Support configurable workflow through `config.toml`
- [x] Produce reusable training-ready datasets
- [x] Establish a standard CLI workflow for pipeline execution

### DoD Sprint 1

- [x] Raw market data can be downloaded successfully
- [x] OHLCV and derived datasets can be generated end-to-end
- [x] The project can run through a baseline CLI workflow

---

## SPRINT 2: MODEL TRAINING BASELINE

> **Goal:** Train initial forecasting models and standardize experiment execution.
>
> **Dependencies:** Sprint 1.
>
> **Estimated duration:** 1–2 weeks.

### Training backends

- [x] Implement trainable backend structure in `mlfx.training`
- [x] Add `mlf` backend
- [x] Add `lstm` backend
- [x] Add `bilstm` backend
- [x] Add `transformer` backend
- [x] Add `cnn_lstm` backend
- [x] Add `sgd` backend
- [x] Add `stats` backend
- [x] Add `neuralforecast` backend

### Training workflow

- [x] Build unified training entrypoints through CLI
- [x] Add backend selection with `--backend`
- [x] Implement time-series-safe train/validation/test workflow
- [x] Save model artifacts to `outputs/`
- [x] Export training metrics and summaries

### Benchmarking and comparison

- [x] Add unified benchmark flow with `mlfx benchmark`
- [x] Support multi-backend comparison in one workflow
- [x] Standardize output metrics for model comparison
- [x] Improve experiment reproducibility through config-driven runs

### DoD Sprint 2

- [x] Multiple backends can be trained from the CLI
- [x] Benchmark runs compare backends consistently
- [x] Artifacts and metrics are saved for later evaluation

---

## SPRINT 3: EVALUATION AND REPORTING

> **Goal:** Evaluate model behavior in a reproducible way and generate useful reports for research.
>
> **Dependencies:** Sprint 2.
>
> **Estimated duration:** 1–2 weeks.

### Evaluation pipeline

- [x] Implement evaluation flow in `mlfx.evaluation`
- [x] Add backtesting support
- [x] Generate summary metrics from evaluation runs
- [x] Persist evaluation outputs to structured directories
- [x] Support CLI-driven evaluation execution

### Reporting

- [x] Export metrics to `metrics_log.jsonl`
- [x] Generate machine-readable result summaries
- [x] Document evaluation workflow in the docs
- [x] Provide guidance for interpreting reports

### Test coverage

- [x] Add end-to-end train/evaluate coverage
- [x] Add `test_training_e2e.py`
- [x] Expand regression protection around training and evaluation workflow

### DoD Sprint 3

- [x] Models can be evaluated end-to-end after training
- [x] Evaluation results are reproducible and persisted
- [x] Researchers can compare outcomes across runs

---

## SPRINT 4: SERVING AND OPERATIONS

> **Goal:** Improve operational readiness of the inference and runtime layer.
>
> **Dependencies:** Sprint 3.
>
> **Estimated duration:** 1–2 weeks.

### Serving layer

- [ ] Refactor the serving layer for clearer separation of concerns
- [ ] Add stronger runtime packaging and deployment boundaries
- [ ] Define stable inference input/output contracts
- [ ] Improve error handling in serving endpoints
- [ ] Add health-check behavior for runtime services

### Reliability

- [ ] Add retry logic where external or unstable operations may fail
- [ ] Add circuit breaker patterns for fragile runtime integrations
- [ ] Improve failure visibility with clearer logs and runtime diagnostics
- [ ] Define recovery behavior for partial pipeline failures

### Operational workflows

- [ ] Document production-style execution patterns
- [ ] Standardize operational commands for training, evaluation, and serving
- [ ] Improve environment notes and deployment guidance

### DoD Sprint 4

- [ ] The serving layer is easier to operate and reason about
- [ ] Runtime failures are surfaced clearly and handled more safely
- [ ] Operators can run the project with documented procedures

---

## SPRINT 5: HARDENING AND EXPERIMENTATION SCALE

> **Goal:** Increase reliability, speed of experimentation, and confidence in future extensions.
>
> **Dependencies:** Sprint 4.
>
> **Estimated duration:** 1–2 weeks.

### Testing and quality

- [ ] Expand test coverage with smaller fixture datasets
- [ ] Add more integration tests for CLI workflows
- [ ] Add tests for failure and recovery scenarios
- [ ] Improve confidence around configuration edge cases

### Experimentation breadth

- [ ] Add new backend architectures beyond the current set
- [ ] Explore more attention-based or sequence-model variants
- [ ] Add a live data adapter for more realistic operating scenarios
- [ ] Improve cross-backend metric consistency for research comparisons

### Performance and maintainability

- [ ] Identify slow stages in ingestion, pipeline, and training
- [ ] Reduce duplicated logic between backends where possible
- [ ] Improve internal module boundaries and service responsibilities
- [ ] Add clearer developer guidance for extending the system

### DoD Sprint 5

- [ ] The codebase is easier to extend safely
- [ ] Tests cover the most important operational paths
- [ ] Researchers can iterate faster across backends and datasets

---

## CROSS-CUTTING IMPROVEMENTS

### Documentation

- [ ] Keep English and Vietnamese docs structurally aligned
- [ ] Add missing cross-links between roadmap, architecture, and reference docs
- [ ] Standardize terminology across guides and reference pages
- [ ] Add contributor guidance for future documentation updates

### Logging and observability

- [ ] Replace ad-hoc output with a more consistent logging strategy
- [ ] Add log levels for debugging and runtime monitoring
- [ ] Improve tracing of long-running pipeline stages
- [ ] Make failure causes easier to diagnose from logs alone

### Configuration and UX

- [ ] Simplify configuration discovery for new users
- [ ] Improve defaults for common workflows
- [ ] Validate critical configuration earlier in command execution
- [ ] Make CLI help and error messages more actionable

### Packaging and deployment

- [ ] Review `Dockerfile` for reproducible builds
- [ ] Review `docker-compose.yml` for local development usability
- [ ] Define a more explicit deployment story for serving mode
- [ ] Add graceful shutdown behavior where needed

---

## FUTURE IDEAS

> These items are outside the current core roadmap and should be considered after the main workflow is stable.

### Advanced modeling

- [ ] Add richer ensemble workflows
- [ ] Add probabilistic forecasting options
- [ ] Add model explainability support for research analysis
- [ ] Add automated hyperparameter search workflows

### Data and market coverage

- [ ] Support more symbols and broader dataset management workflows
- [ ] Add more robust live-data ingestion adapters
- [ ] Add richer data validation and provenance tracking

### Research tooling

- [ ] Add experiment dashboards
- [ ] Add richer artifact comparison tools
- [ ] Add workflow templates for common research scenarios

---

## Documents

| Document | Description |
| -------- | ----------- |
| [README.md](../README.md) | English documentation hub |
| [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | System architecture and design |
| [TODO.md](TODO.md) | Sprint-based task list |
| [ROADMAP.md](ROADMAP.md) | Current status and next work |
| [Vietnamese README](../../vi/README.md) | Vietnamese documentation hub |
| [Vietnamese TODO](../../vi/meta/TODO.md) | Vietnamese version of this task list |

---
