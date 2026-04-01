# MLFX – Roadmap & Development Plan

> **Plan version:** 2026.02.08-v2
>
> Internal planning document.  
> Reference: [TODO.md](TODO.md) (detailed task list), [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) (system architecture explanation).

---

## I. MARKET LANDSCAPE & COMPETITIVE ADVANTAGE

Why is MLFX worth continuing to invest in and expand? This project sits at the intersection of quantitative research tooling, machine learning pipelines, and MLOps thinking for market data.

| Criteria | Fragmented Research Scripts | Trading Frameworks / Open-Source Bots | MLFX |
| -------- | --------------------------- | ------------------------------------- | ---- |
| **System organization** | **Low.** Code is often fragmented and hard to reuse. | **Medium to High.** Structured, but often focused more on execution logic. | **High.** Clear flow from data ingestion → validation → processing → training → evaluation → serving. |
| **Reproducibility** | **Low.** Hard to standardize environment and execution flow. | **Medium.** Somewhat stable, but often tightly coupled to framework conventions. | **High.** Uses `pixi`, centralized configuration, and a unified CLI. |
| **ML / MLOps depth** | **Low to Medium.** Often stops at notebooks or lightweight backtests. | **Medium.** Strong on rule-based systems or bots, but not always strong on ML pipelines. | **High.** Focused on data, feature engineering, training, model comparison, evaluation, drift detection, and serving. |
| **Backend extensibility** | **Low.** Adding a new model often requires edits in many places. | **Medium.** Depends heavily on framework design. | **High.** Includes multiple backends: `mlf`, `lstm`, `sgd`, `stats`. |
| **Evaluation capability** | **Medium.** May include backtests, but often without strong standardization. | **High.** Many frameworks include solid backtesting support. | **High.** Includes evaluation, reporting, multi-backend comparison, and summary metric logging. |
| **Operational readiness** | **Low.** Scripts are hard to deploy reliably. | **Medium.** Often strong in execution, but not always strong in ML-serving concerns. | **Medium to High.** Already has `serve`, `batch-predict`, and `drift`, but still needs stronger serving reliability, retry logic, circuit breaking, and logging. |
| **Long-term research fit** | **Low.** Structure tends to collapse as the project grows. | **Medium.** Can become limited by framework philosophy. | **High.** Well-suited for model research, backend comparison, data-adapter expansion, and gradual movement toward more stable operation. |

**Conclusion:** MLFX does not try to become a “does everything” trading bot from day one. Its strength is as an **MLOps-style market-data research pipeline**, where you can download data, normalize it, train multiple backends, compare models, evaluate them, and serve predictions in one coherent system.

---

## II. DEVELOPMENT ROADMAP

**Sprint dependency chain:** Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4 → Sprint 5.  
These should not be implemented in parallel; each sprint depends on the outputs and stability of the previous one.

**System-wide lifecycle loop:**

```text
Observe → Validate → Transform → Train → Evaluate → Serve → Monitor → Improve
```

### SPRINT 1: FOUNDATION

- **Goal:** Lay the groundwork so the project can run end-to-end at a basic level.
- **Dependencies:** None.
- **Estimated duration:** 1–2 weeks.
- **Core technology:** Python, Pixi, Parquet, CLI structure, basic documentation.
- **Tasks:**
  1. Initialize the Python project with `pixi`.
  2. Establish the main project structure for `mlfx`, `tests`, `data`, `outputs`, and `docs`.
  3. Create `pyproject.toml`, `config.toml`, `.gitignore`, and `README.md`.
  4. Standardize the unified `mlfx` CLI.
  5. Add basic `Dockerfile` and `docker-compose.yml`.
  6. Set up the bilingual documentation framework.
- **Definition of done:** The repository can run a basic CLI-driven workflow, the project structure is stable, and the development environment is reproducible.
- **Acceptance criteria:** A new contributor can clone the repository, install the environment, and run basic commands with `pixi run`.
- **Technical risks:** If the initial structure is unclear, later sprints will accumulate tight coupling and technical debt.

### SPRINT 2: DATA INGESTION & PROCESSING

- **Goal:** Turn raw market data into normalized data usable for training and evaluation.
- **Dependencies:** Sprint 1.
- **Estimated duration:** 1–2 weeks.
- **Core technology:** `mlfx.ingestion`, `mlfx.pipeline`, Parquet, timeframe conversion, labeling.
- **Tasks:**
  1. Build the downloader in `mlfx.ingestion`.
  2. Download tick data from Dukascopy.
  3. Store raw data by month.
  4. Track download state with state files.
  5. Validate data quality and detect gaps and anomalies.
  6. Convert tick data into OHLCV across timeframes.
  7. Build feature engineering and labeling stages.
  8. Standardize processed outputs for training and evaluation.
- **Definition of done:** Raw data can be turned into OHLCV, features, labels, and stable processed outputs in a consistent workflow.
- **Acceptance criteria:** Data validation, timeframe conversion, feature generation, and labeling run successfully in one unified flow.
- **Technical risks:** Financial data is highly sensitive to gaps, timestamp drift, and inconsistent formats; weak handling here will propagate errors into training.

### SPRINT 3: TRAINING & BACKEND STANDARDIZATION ✅

- **Goal:** Train multiple backends and standardize the training workflow for fairer model comparison.
- **Dependencies:** Sprint 2.
- **Estimated duration:** 1–2 weeks.
- **Core technology:** `mlfx.training`, optional MLflow, CLI-driven training configuration.
- **Tasks:**
  1. Build the shared training module.
  2. Integrate backends: `mlf`, `lstm`, `sgd`, `stats`.
  3. Standardize train / validation / test splitting for time-series data.
  4. Avoid data leakage.
  5. Store training artifacts and metrics under `outputs/`.
  6. Integrate MLflow as an optional path.
  7. Standardize run metadata for each training job.
- **Definition of done:** At least one backend can be trained end-to-end; artifacts and metrics are stored consistently; multiple backends can be compared within the same system.
- **Status:** ✅ Completed.

### SPRINT 4: EVALUATION, BACKTESTING & MODEL COMPARISON ✅

- **Goal:** Evaluate model quality reproducibly and establish a solid basis for backend comparison.
- **Dependencies:** Sprint 3.
- **Estimated duration:** 1–2 weeks.
- **Core technology:** `mlfx.evaluation`, reporting, comparison workflow.
- **Tasks:**
  1. Build the evaluation module.
  2. Add backtesting support.
  3. Compute basic and out-of-sample evaluation metrics.
  4. Store evaluation outputs under `outputs/`.
  5. Generate reports and summary metrics.
  6. Add a unified comparison flow via `mlfx benchmark`.
  7. Add `metrics_log.jsonl`.
  8. Increase end-to-end test coverage for training and evaluation.
- **Definition of done:** Trained models can be evaluated and backtested; multi-backend comparison works; results are stored and reviewable.
- **Status:** ✅ Completed.
- **Acceptance criteria:** The same workflow can be used to compare multiple backends on the same data and metric set.

### SPRINT 5: SERVING, MONITORING & RELIABILITY HARDENING

- **Goal:** Move the system toward more stable operation for inference, batch prediction, and monitoring.
- **Dependencies:** Sprint 4.
- **Estimated duration:** 1–2 weeks.
- **Core technology:** FastAPI, serving layer, drift-detection workflow, logging, retry / circuit-breaker behavior.
- **Tasks:**
  1. Harden the serving path for `serve` and `batch-predict`.
  2. Standardize inference input / output contracts.
  3. Improve health checks and runtime diagnostics.
  4. Refine the `drift` workflow.
  5. Add retry logic for unstable operations.
  6. Add circuit breaker protection for fragile integrations.
  7. Improve runtime logging and error handling.
  8. Write clearer deployment documentation for production-like operation.
- **Definition of done:** The system can serve predictions via API or batch mode, detect feature drift, and reach a basic level of operational readiness.
- **Acceptance criteria:** Runtime failures are surfaced clearly, API health checks are dependable, and operators can follow the docs successfully.
- **Technical risks:** If the serving layer is not hardened properly, it becomes the weakest point when moving from research to operation.

---

## III. CURRENT STATUS & NEXT PRIORITIES

### What already exists

- Unified CLI `mlfx`
- Dukascopy ingestion in `mlfx.ingestion`
- QA, timeframe conversion, feature engineering, and labeling in `mlfx.pipeline`
- Multiple training backends in `mlfx.training`
- Evaluation, backtesting, and reporting in `mlfx.evaluation`
- Runtime packaging through `mlfx`
- Unified benchmark workflow
- End-to-end training and evaluation test coverage
- Summary metric export via `metrics_log.jsonl`
- `serve`, `batch-predict`, and `drift` commands

### Next priorities

1. Standardize metrics across backends for fairer comparison.
2. Expand test coverage with smaller fixture datasets for faster, more stable test runs.
3. Reorganize the serving layer for easier maintenance.
4. Add retry and circuit-breaker behavior.
5. Add real-time data adapters beyond Dukascopy.
6. Expand backend coverage, especially more attention-based variants.

### Prioritization logic

- If the goal is **model comparison**: prioritize benchmark flow, metric consistency, and reporting quality.
- If the goal is **operational reliability**: prioritize testing, retries, circuit breakers, and logging.
- If the goal is **research expansion**: prioritize new backends and real-time data adapters.
- If the goal is **earlier operational deployment**: prioritize serving-layer reorganization and inference-contract standardization.

---

## IV. ADDITIONAL INFORMATION

### General technical risks

- **Market data:** Data gaps, timestamp drift, or source-format changes can break the pipeline if validation is too weak.
- **ML / DL backends:** Some deep-learning backends require large compute budgets or long training times; comparison must be standardized to avoid unfair conclusions.
- **Serving layer:** If input / output contracts are unstable, external integrations become hard to maintain.
- **Drift monitoring:** If reference data is not managed clearly, drift alerts become noisy and difficult to interpret.
- **External dependencies:** Data providers or real-time adapters may change APIs, impose rate limits, or alter access policies.

### Cost and best practices

- **Initial cost:** Low; mostly local-machine or modest research-server cost.
- Use `pixi` to keep the environment reproducible.
- Keep raw data and processed data clearly separated.
- Do not mix research logic with serving logic in the same layer.
- Prefer repeatable comparisons over fast experiments that are hard to validate.
- Every new backend should come with documentation, a minimum metric set, and appropriate tests.

### Why not just use notebooks or loose scripts?

Notebooks are excellent for rapid prototyping, but they become hard to maintain as projects grow. MLFX offers a more coherent structure for long-term research, model comparison, and gradual movement toward practical MLOps discipline.

### How to think about the system

MLFX should be viewed as a continuous improvement loop:

```text
New data → Validate quality → Transform → Train → Evaluate → Serve → Monitor drift → Adjust
```

---

## V. FUTURE PLAN

- **Phase 1 – Broader model research**
  - Add more attention-based backends and sequence-model variants.
  - Expand automated tuning or hyperparameter-search workflows.
  - Standardize comparison more deeply across statistical and deep-learning models.

- **Phase 2 – Data and operational expansion**
  - Support more real-time data adapters beyond Dukascopy.
  - Increase large-scale data handling capability.
  - Refine runtime contracts and the serving layer for more production-like operation.

- **Phase 3 – Observability and user experience**
  - Add richer dashboards for training, evaluation, and serving.
  - Improve logging, health checks, diagnostics, and drift observability.
  - Improve CLI ergonomics and operational documentation.

---

## Documents

| Document | Description |
| -------- | ----------- |
| [../README.md](../README.md) | English documentation hub |
| [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | System architecture explanation |
| [TODO.md](TODO.md) | Sprint-based task list |
| [ROADMAP.md](ROADMAP.md) | Roadmap and development plan |
| [../../vi/README.md](../../vi/README.md) | Vietnamese documentation hub |
| [../../vi/meta/TODO.md](../../vi/meta/TODO.md) | Vietnamese sprint task list |
| [../../vi/meta/ROADMAP.md](../../vi/meta/ROADMAP.md) | Vietnamese version of this roadmap |

---
