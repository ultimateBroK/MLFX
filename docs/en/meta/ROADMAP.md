# MLFX – Roadmap & Development Plan

> **Plan version:** 2026.02.08-v2
>
> Internal planning document.  
> Reference: [TODO.md](TODO.md) (detailed sprint task list), [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) (system architecture).

---

## I. MARKET ANALYSIS & COMPETITIVE ADVANTAGE

Why is MLFX worth building and continuing to expand? The project is positioned as a **local-first, research-oriented MLOps pipeline for market prediction**, focused on control, extensibility, and reproducibility rather than cloud lock-in or black-box automation.

| Capability | Hosted AI/AutoML Platforms | General Quant Frameworks | MLFX |
| ---------- | -------------------------- | ------------------------ | ---- |
| **Control over data** | **Medium.** Convenient, but data and experiment flow are often tied to vendor tooling. | **High.** You control execution and storage. | **Highest.** Local-first workflow, filesystem-based artifacts, optional tracking, and no mandatory hosted dependency. |
| **Reproducibility** | **Medium.** Depends on platform defaults and managed runtimes. | **High.** Reproducible if disciplined. | **High.** Config-driven workflows, local artifacts, deterministic pipeline stages, and structured outputs. |
| **Extensibility** | **Medium.** Usually limited by platform boundaries. | **High.** Flexible but often fragmented. | **High.** Modular ingestion, pipeline, training, evaluation, serving, and future adapters. |
| **Operational simplicity** | **High.** Managed services reduce setup overhead. | **Medium.** Powerful but can require manual glue code. | **Medium to High.** Pixi-based workflow simplifies local operation while preserving engineering flexibility. |
| **Research workflow** | **Medium.** Often optimized for production-first or dashboard-first usage. | **High.** Good for experimentation. | **High.** Built around iterative research: ingest → QA → pipeline → train → evaluate → benchmark → serve. |
| **Backend experimentation** | **Medium.** Often tied to supported runtimes. | **High.** Strong if you build the plumbing yourself. | **High.** Multiple trainable backends already exist, with room for standardized comparison and future expansion. |
| **Privacy / ownership** | **Low to Medium.** Vendor-managed services can expose operational metadata. | **High.** Usually self-managed. | **High.** Local execution and self-managed artifacts by default. |

**Conclusion:** MLFX does not try to be a generic hosted ML platform. It is strongest as a **local, modular, developer-controlled market prediction research stack**. Its advantage is the combination of reproducible workflows, flexible backend experimentation, and a practical MLOps structure that remains understandable and hackable.

---

## II. DEVELOPMENT ROADMAP

**Sprint dependency chain:** Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4 → Sprint 5. Each sprint builds on the outputs of the previous one.

**Cross-cutting operating loop:**

```text
Observe -> Validate -> Transform -> Train -> Evaluate -> Serve -> Monitor -> Improve
```

### SPRINT 1: FOUNDATION ✅

- **Goal:** Establish the local-first project foundation and baseline workflow.
- **Dependencies:** None.
- **Estimated duration:** 1–2 weeks.
- **Technology:** Python, Pixi, Parquet, project CLI, basic Docker setup.
- **Tasks:**
  1. Initialize the Python project with `pixi`.
  2. Define the main project structure for `mlfx`, `tests`, `data`, `outputs`, and `docs`.
  3. Add `pyproject.toml`, `.gitignore`, and base configuration.
  4. Create the unified CLI entrypoint.
  5. Establish the bilingual documentation structure.
  6. Add basic container and local environment support.
- **DoD:** The repository can run as a coherent local project with a documented developer workflow.
- **Acceptance criteria:** `pixi`-based commands run successfully, repository structure is stable, and contributors can understand where each subsystem lives.
- **Technical risks:** Keeping the initial layout simple enough for fast iteration while still leaving room for future serving and production concerns.
- **Status:** ✅ Completed.

### SPRINT 2: DATA INGESTION & PROCESSING ✅

- **Goal:** Build a reliable path from raw market data to training-ready datasets.
- **Dependencies:** Sprint 1.
- **Estimated duration:** 1–2 weeks.
- **Technology:** Dukascopy ingestion, Parquet storage, pipeline processing, QA, resampling.
- **Tasks:**
  1. Build the downloader in `mlfx.ingestion`.
  2. Support monthly raw tick downloads from Dukascopy.
  3. Persist raw data to Parquet.
  4. Track ingestion progress with state files.
  5. Implement data QA and anomaly checks.
  6. Resample tick data into OHLCV timeframes.
  7. Add feature engineering and labeling flow.
  8. Write processed outputs into stable dataset layouts.
- **DoD:** Raw market data can be ingested, validated, transformed, and saved in a reusable structure.
- **Acceptance criteria:** A full raw-to-processed run succeeds end-to-end and produces training-ready outputs without manual intervention.
- **Technical risks:** Data gaps, malformed source data, and keeping time handling consistent across ingestion and resampling stages.
- **Status:** ✅ Completed.

### SPRINT 3: TRAINING SYSTEM & MODEL BASELINES ✅

- **Goal:** Train multiple forecasting backends through a unified workflow.
- **Dependencies:** Sprint 2.
- **Estimated duration:** 1–2 weeks.
- **Technology:** `mlfx.training`, configurable backends, artifact persistence, optional MLflow.
- **Tasks:**
  1. Implement the training module and backend abstraction.
  2. Add baseline backends: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`.
  3. Build a unified CLI training flow.
  4. Enforce time-series-safe splitting.
  5. Save artifacts and training outputs under `outputs/`.
  6. Record run metadata and summary metrics.
  7. Support optional MLflow tracking.
- **DoD:** At least one backend can be trained end-to-end through the standard CLI, with reproducible artifacts and metrics.
- **Acceptance criteria:** Backend selection works via CLI, artifacts are saved consistently, and time-series data leakage is avoided.
- **Technical risks:** Divergent backend interfaces, inconsistent metrics, and accidental leakage in split logic.
- **Status:** ✅ Completed.

### SPRINT 4: EVALUATION, REPORTING & BENCHMARKING ✅

- **Goal:** Make model quality measurable, comparable, and reviewable.
- **Dependencies:** Sprint 3.
- **Estimated duration:** 1–2 weeks.
- **Technology:** `mlfx.evaluation`, backtesting, report generation, benchmark flow.
- **Tasks:**
  1. Implement evaluation workflows in `mlfx.evaluation`.
  2. Add backtesting support for prediction-driven analysis.
  3. Generate summary metrics and structured outputs.
  4. Persist evaluation reports under `outputs/`.
  5. Add a unified benchmark command.
  6. Improve result comparison across backends.
  7. Add end-to-end train/evaluate test coverage.
- **DoD:** Models can be trained, evaluated, benchmarked, and compared through a repeatable workflow.
- **Acceptance criteria:** Evaluation outputs are reproducible, benchmark runs complete successfully, and summary metrics are exportable.
- **Technical risks:** Metric inconsistency across backends, report sprawl, and fragile end-to-end test coverage.
- **Status:** ✅ Completed.

### SPRINT 5: SERVING, RELIABILITY & PRODUCTION READINESS

- **Goal:** Turn the research stack into a more operationally reliable serving system.
- **Dependencies:** Sprint 4.
- **Estimated duration:** 1–2 weeks.
- **Technology:** FastAPI serving layer, runtime packaging, drift workflow, logging, retry logic.
- **Tasks:**
  1. Harden the serving layer and define clearer inference contracts.
  2. Improve runtime packaging for deployment use cases.
  3. Expand health checks and observability.
  4. Add retry logic for unstable operations.
  5. Add circuit-breaker-style protection where external calls may fail repeatedly.
  6. Standardize CLI/API error handling.
  7. Improve runtime logs for diagnosis and incident review.
  8. Refine drift monitoring workflow.
- **DoD:** The system can serve predictions more safely and is easier to operate in a production-like environment.
- **Acceptance criteria:** Serving behavior is documented, health endpoints are dependable, logs are actionable, and failure recovery is more predictable.
- **Technical risks:** Overcomplicating a research-first codebase, unclear deployment boundaries, and insufficient runtime protection for long-lived services.
- **Status:** In progress / next major focus.

---

## III. ADDITIONAL INFORMATION

### Current completed milestones

- Unified CLI `mlfx`
- Dukascopy ingestion in `mlfx.ingestion`
- QA, resampling, feature engineering, and labeling in `mlfx.pipeline`
- Multiple trainable backends in `mlfx.training`
- Backtesting and reporting in `mlfx.evaluation`
- Runtime packaging and workflow commands
- Pixi-based operator and developer flow
- Unified benchmark flow
- End-to-end train/evaluate coverage
- Summary metrics export via `metrics_log.jsonl`

### Technical risks overview

- **Data source instability:** External market data providers may change behavior, throttle requests, or return incomplete data.
- **Time-series correctness:** Even small mistakes in split logic, resampling, or labeling can invalidate evaluation results.
- **Backend drift:** Supporting multiple modeling backends can lead to inconsistent metrics, input contracts, and artifact expectations.
- **Serving complexity:** A serving layer can accumulate production concerns faster than the rest of the stack if boundaries are not kept clean.
- **Documentation drift:** As the project grows, English and Vietnamese docs can diverge unless maintained together.

### Cost and best practices

- **Baseline cost:** Near-zero for local development beyond compute and storage.
- Prefer local, reproducible runs before adding deployment complexity.
- Keep configs explicit and version-controlled where safe.
- Use smaller fixture datasets to improve test speed and reliability.
- Expand serving safeguards before treating the project as production-ready.

### Why not rely only on hosted MLOps or generic quant frameworks?

Hosted platforms reduce setup effort but often trade away control, transparency, and flexibility. Generic frameworks are powerful but may require more glue code to shape a coherent market-prediction workflow. MLFX sits in the middle: opinionated enough to be productive, modular enough to remain extensible.

### Representative project workflow

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

This flow is the practical backbone of the project and should remain stable even as individual modules evolve.

---

## IV. FUTURE PLAN

- **Phase 1 – Stronger model comparison**
  - Standardize cross-backend metrics more rigorously.
  - Improve benchmark summaries for apples-to-apples comparisons.
  - Add more compact fixture datasets for repeatable validation.

- **Phase 2 – Broader experimentation**
  - Add new backend architectures, especially more attention-based variants.
  - Introduce additional live-data adapters beyond Dukascopy.
  - Expand configurable experiment templates.

- **Phase 3 – More production-grade operation**
  - Refactor the serving layer into cleaner operational boundaries.
  - Add stronger retry, fallback, and failure-isolation behavior.
  - Improve deployment guidance, runtime packaging, and health monitoring.

- **Phase 4 – Better research UX**
  - Add richer experiment dashboards and artifact comparison tools.
  - Improve CLI ergonomics and configuration discovery.
  - Add clearer contributor guidance for extending pipelines and backends.

---

## Documents

| Document | Description |
| -------- | ----------- |
| [README.md](../README.md) | English documentation hub |
| [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | System architecture and design |
| [TODO.md](TODO.md) | Sprint-based task list |
| [ROADMAP.md](ROADMAP.md) | Roadmap and development plan |
| [Vietnamese README](../../vi/README.md) | Vietnamese documentation hub |
| [Vietnamese TODO](../../vi/meta/TODO.md) | Vietnamese sprint task list |
| [Vietnamese ROADMAP](../../vi/meta/ROADMAP.md) | Vietnamese version of this roadmap |
