# MLFX – Task List

> **Version:** aligned with [ROADMAP.md](ROADMAP.md).  
> Sprint-based task list; see [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) to understand the system design.

## SPRINT 1: FOUNDATION

> **Goal:** Establish the foundation so the MLFX pipeline can download data, process data, and run end-to-end on a local machine.
>
> **Dependencies:** None.
>
> **Estimated duration:** 1–2 weeks.

### Environment setup

- [x] Initialize the Python project with `pixi`
- [x] Set up the main directory structure: `mlfx/`, `tests/`, `data/`, `outputs/`, `docs/`
- [x] Create and configure `pyproject.toml`
- [x] Configure `.gitignore`
- [x] Write the main project README
- [x] Create the default `config.toml`

### Development infrastructure

- [x] Create the unified `mlfx` CLI
- [x] Standardize entrypoints for the main workflows
- [x] Add basic logging for the CLI and pipeline
- [x] Create a basic `Dockerfile`
- [x] Create `docker-compose.yml` for the development environment
- [x] Add the bilingual documentation structure under `docs/en` and `docs/vi`

### Input data

- [x] Build the downloader in `mlfx.ingestion`
- [x] Support tick-data downloads from Dukascopy
- [x] Save raw monthly data into `data/raw/`
- [x] Track download state with `completed_months.json`
- [x] Support decompression of the `bi5` format

### Sprint 1 completion criteria

- [x] The first raw-data download workflow can run successfully
- [x] The CLI works locally through `pixi run`
- [x] The project structure is ready for later sprints

---

## SPRINT 2: DATA PROCESSING & PIPELINE

> **Goal:** Turn raw data into datasets that can be used for model training and evaluation.
>
> **Dependencies:** Sprint 1.
>
> **Estimated duration:** 1–2 weeks.

### Data quality

- [x] Build the data-quality check stage in `mlfx.pipeline`
- [x] Detect time-based data gaps
- [x] Detect abnormal data or structural errors
- [x] Generate a basic quality-check report

### Data transformation and feature engineering

- [x] Convert tick data into OHLCV by timeframe
- [x] Support multiple timeframe conversions
- [x] Build the basic feature-engineering stage
- [x] Support label generation for forecasting or signal tasks
- [x] Standardize output data for training and evaluation

### Processed data storage

- [x] Write pipeline outputs into `data/processed/`
- [x] Standardize storage format as `parquet`
- [x] Organize data by symbol, timeframe, and split set

### Sprint 2 completion criteria

- [x] Raw data can be turned into OHLCV and features
- [x] Quality checking, transformation, and labeling run in one unified workflow
- [x] Output data is ready for model training

---

## SPRINT 3: MODEL TRAINING

> **Goal:** Train forecasting backends and standardize the training workflow.
>
> **Dependencies:** Sprint 2.
>
> **Estimated duration:** 1–2 weeks.

### Training backends

- [x] Build the `mlfx.training` module
- [x] Support the `mlf` backend
- [x] Support the `lstm` backend
- [x] Support the `bilstm` backend
- [x] Support the `transformer` backend
- [x] Support the `cnn_lstm` backend
- [x] Support the `sgd` backend
- [x] Support the `stats` backend
- [x] Support the `neuralforecast` backend

### Training workflow

- [x] Standardize the shared training program
- [x] Support train / validation / test splits for time series
- [x] Prevent data leakage during splitting
- [x] Save training artifacts into `outputs/`
- [x] Record training metrics

### Experiment tracking

- [x] Integrate optional MLflow support
- [x] Save metric logs as `metrics_log.jsonl`
- [x] Standardize metadata for each training run

### Sprint 3 completion criteria

- [x] At least one backend can be trained end-to-end
- [x] Artifacts and metrics are saved consistently
- [x] Multiple backends can be compared within the same workflow

---

## SPRINT 4: EVALUATION & BACKTESTING

> **Goal:**
> Measure model quality and practical usefulness in forecasting or trading contexts.
>
> **Dependencies:** Sprint 3.
>
> **Estimated duration:** 1–2 weeks.

### Model evaluation

- [x] Build the `mlfx.evaluation` module
- [x] Compute core evaluation metrics
- [x] Support evaluation on out-of-sample datasets
- [x] Export evaluation reports

### Backtesting

- [x] Create a backtest workflow based on prediction signals
- [x] Compute core performance metrics
- [x] Save backtest outputs to `outputs/`
- [x] Generate summary reports for each evaluation run

### Multi-backend comparison

- [x] Add the `mlfx benchmark` command
- [x] Compare multiple backends in one workflow
- [x] Standardize benchmark outputs for easier comparison

### Sprint 4 completion criteria

- [x] Models can be evaluated and backtested after training
- [x] Multi-backend comparison works reliably
- [x] Reports clearly support backend-quality comparison

---

## SPRINT 5: MODEL SERVING & OPERATIONS

> **Goal:** Bring the system to a state where it can serve predictions and operate as a more complete research-oriented MLOps system.
>
> **Dependencies:** Sprint 4.
>
> **Estimated duration:** 1–2 weeks.

### Model serving

- [x] Package the runtime layer through `mlfx`
- [x] Support the `serve` command
- [x] Support the `batch-predict` command
- [x] Build a basic FastAPI serving layer
- [x] Add a basic health-check endpoint

### Monitoring

- [x] Support the `drift` workflow
- [x] Compare recent data distributions against reference data
- [x] Generate outputs for model-drift inspection

### Operational reliability

- [ ] Add retry logic for the serving layer
- [ ] Add circuit-breaker behavior for fragile integrations
- [ ] Standardize error handling across the CLI and API
- [ ] Increase runtime logging detail
- [ ] Add clearer deployment configuration for real environments

### Sprint 5 completion criteria

- [x] Predictions can be served via API or batch mode
- [x] A data-drift detection workflow exists
- [ ] The system reaches a basic operational-readiness level

---

## RECOMMENDED NEXT WORK

> This section is aligned with [ROADMAP.md](ROADMAP.md) and reflects the most sensible next steps based on the current state of the project.

### High priority

- [x] Expose `bilstm` through the CLI via `--backend bilstm`
- [x] Add a unified benchmarking workflow (`mlfx benchmark`)
- [x] Add end-to-end coverage for training and evaluation (`test_training_e2e.py`)
- [x] Add summary metric export (`metrics_log.jsonl`)

### Next priorities

- [ ] Standardize metrics across backends for fairer comparison
- [ ] Expand test coverage with smaller fixture datasets for faster, more stable runs
- [ ] Refactor the serving layer for easier maintenance
- [ ] Add retry logic and circuit-breaker behavior to improve operational readiness
- [ ] Add live data adapters beyond Dukascopy
- [ ] Expand the set of backend architectures, especially attention-based ones

---

## CROSS-CUTTING IMPROVEMENTS

### Service layer and internal architecture

- [ ] Separate service layers more clearly for ingestion / pipeline / training / evaluation / serving
- [ ] Reduce tight coupling between the CLI and business logic
- [ ] Standardize interfaces between backends
- [ ] Improve backend replaceability without major orchestration changes

### Logging and observability

- [ ] Standardize logging levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- [ ] Write logs to separate files per workflow
- [ ] Add execution summaries for each run
- [ ] Improve health checks for the realtime runtime and serving layers

### Testing

- [ ] Expand unit tests for ingestion
- [ ] Expand unit tests for the pipeline
- [ ] Expand unit tests for evaluation
- [ ] Add API tests for the serving layer
- [ ] Add test coverage reports
- [ ] Reduce total test-suite runtime

### DevOps & deployment

- [ ] Improve container packaging for the full system
- [ ] Create clearer deployment guidance for real environments
- [ ] Add CI/CD workflows on GitHub Actions
- [ ] Add automated build, test, and lint checks
- [ ] Standardize environment configuration for development / testing / operations

### Documentation

- [ ] Synchronize the English `TODO.md` with the Vietnamese version
- [ ] Continue improving fully symmetric bilingual docs
- [ ] Add consistent breadcrumbs and cross-links between documentation files
- [ ] Update docs whenever a new backend or workflow is added
- [ ] Add contributor guidance

---

## FUTURE DIRECTIONS

> The items below are outside the short-term scope, but useful for the long-term direction of MLFX.

### Data and pipeline

- [ ] Support more market-data sources
- [ ] Add near-realtime streaming pipelines
- [ ] Increase large-scale data processing capacity
- [ ] Optimize large-batch feature generation

### Modeling

- [ ] Experiment with more attention-based architectures
- [ ] Add automatic model selection
- [ ] Add automated hyperparameter tuning
- [ ] Deepen comparisons between statistical and deep-learning models

### Serving and monitoring

- [ ] Improve serving-layer scalability
- [ ] Add API authentication
- [ ] Add monitoring dashboards
- [ ] Improve model-drift and data-drift alerting quality

### User experience

- [ ] Build visual dashboards for training / evaluation / serving
- [ ] Improve CLI ergonomics
- [ ] Export more readable visual reports
- [ ] Increase configurability without requiring source-code edits

---

## Related Documents

| Document | Description |
| -------- | ----------- |
| [../../README.md](../../README.md) | Overview of the documentation system |
| [../README.md](../README.md) | Main entrypoint for the English docs |
| [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | Explanation of system architecture |
| [ROADMAP.md](ROADMAP.md) | Current status and next steps |

---
