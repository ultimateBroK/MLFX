# MLFX Documentation

This directory contains the documentation for the `MLFX` market-data research pipeline.

The docs are organized by:

1. **language**
2. **document type**
3. **topic**

This structure is intended to make the documentation easier to navigate, easier to maintain, and easier to expand over time.

---

## Choose a language

- **English** → [docs/en/README.md](en/README.md)
- **Tiếng Việt** → [docs/vi/README.md](vi/README.md)

---

## Recommended reading paths

### If you are new to the project
- English: [Getting Started / Noob Guide](en/getting-started/NOOB_GUIDE.md)
- Tiếng Việt: [Getting Started / Noob Guide](vi/getting-started/NOOB_GUIDE.md)

### If you want the fastest working flow
- English: [Quick Start](en/getting-started/QUICKSTART.md)
- Tiếng Việt: [Bắt đầu nhanh](vi/getting-started/QUICKSTART.md)

### If you want command usage and operational details
- English: [Usage Guide](en/guides/USAGE_GUIDE.md)
- Tiếng Việt: [Usage Guide](vi/guides/USAGE_GUIDE.md)

### If you want to understand system design
- English: [Architecture](en/architecture/ARCHITECTURE.md)
- Tiếng Việt: [Architecture](vi/architecture/ARCHITECTURE.md)

### If you want technical reference docs
- English:
  - [Feature Reference](en/reference/FEATURE_REFERENCE.md)
  - [Config Reference](en/reference/CONFIG_REFERENCE.md)
  - [API Reference](en/reference/API_REFERENCE.md)
  - [Glossary](en/reference/GLOSSARY.md)
- Tiếng Việt:
  - [Feature Reference](vi/reference/FEATURE_REFERENCE.md)
  - [Config Reference](vi/reference/CONFIG_REFERENCE.md)
  - [API Reference](vi/reference/API_REFERENCE.md)
  - [Glossary](vi/reference/GLOSSARY.md)

### If you are debugging problems
- English: [Troubleshooting](en/guides/TROUBLESHOOTING.md)
- Tiếng Việt: [Troubleshooting](vi/guides/TROUBLESHOOTING.md)

---

## Documentation structure

```text
docs/
├── README.md
├── en/
│   ├── README.md
│   ├── getting-started/
│   │   ├── NOOB_GUIDE.md
│   │   └── QUICKSTART.md
│   ├── guides/
│   │   ├── USAGE_GUIDE.md
│   │   ├── EVALUATION_GUIDE.md
│   │   └── TROUBLESHOOTING.md
│   ├── reference/
│   │   ├── FEATURE_REFERENCE.md
│   │   ├── CONFIG_REFERENCE.md
│   │   ├── API_REFERENCE.md
│   │   └── GLOSSARY.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   └── BACKEND_COMPARISON.md
│   └── meta/
│       └── ROADMAP.md
├── vi/
│   ├── README.md
│   ├── getting-started/
│   │   ├── NOOB_GUIDE.md
│   │   └── QUICKSTART.md
│   ├── guides/
│   │   ├── USAGE_GUIDE.md
│   │   ├── EVALUATION_GUIDE.md
│   │   └── TROUBLESHOOTING.md
│   ├── reference/
│   │   ├── FEATURE_REFERENCE.md
│   │   ├── CONFIG_REFERENCE.md
│   │   ├── API_REFERENCE.md
│   │   └── GLOSSARY.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   └── BACKEND_COMPARISON.md
│   └── meta/
│       └── ROADMAP.md
```

---

## Standard Workflow

The typical workflow in `MLFX` is:

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> serve / batch-predict
  -> drift
```

### Short explanation
- `download`: fetch raw tick data
- `qa`: inspect raw data quality
- `pipeline`: build OHLCV, features, and labels
- `train`: train a model backend
- `evaluate`: run backtests and generate reports
- `serve`: start inference API
- `batch-predict`: run offline predictions
- `drift`: compare current data distribution against reference behavior

---

## Quick command example

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

For the canonical Quick Start, use:
- [English Quick Start](en/getting-started/QUICKSTART.md)
- [Vietnamese Quick Start](vi/getting-started/QUICKSTART.md)

---

## Main documentation categories

### Getting Started
Use this section when you need:
- Onboarding
- First-run guidance
- The shortest path to a working result

### Guides
Use this section when you need:
- Operational instructions
- Command usage
- Evaluation flow
- Troubleshooting steps

### Reference
Use this section when you need:
- Exact meanings of columns, flags, config keys, and API contracts
- Glossary definitions
- Lookup-style documentation

### Architecture
Use this section when you need:
- System design
- Data flow
- Backend design
- Engineering decisions

### Meta
Use this section when you need:
- Roadmap
- Planning
- Project/documentation direction



---

## Notes for contributors

When adding or updating docs:

- Place files in the correct **language** and **category**
- Avoid duplicating the same Quick Start in multiple files
- Keep `README.md` files focused on navigation
- Keep `NOOB_GUIDE.md` focused on orientation and “why”
- Keep `USAGE_GUIDE.md` focused on commands and usage
- Keep reference files canonical and concise
- Update both language trees when the content is meant to stay symmetric

---

## See also

- Project root overview: [../README.md](../README.md)
- Project roadmap: [../ROADMAP.md](../ROADMAP.md)
