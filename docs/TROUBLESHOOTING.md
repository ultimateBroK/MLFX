# Troubleshooting Guide

Occasionally, you might encounter issues due to environment setup or memory limits. If you see red errors in your terminal, check this guide for a quick fix.

---

### 🚨 Error 1: `pixi: command not found`
*   **Symptom**: The terminal throws an error when you try to run any `pixi` command.
*   **Cause**: Pixi is not installed, or your terminal hasn't been restarted since installation.
*   **Fix**: 
    1. Follow the installation steps closely in the [Usage Guide](USAGE_GUIDE.md).
    2. Close your Terminal or VSCode completely and open it again.

### 🚨 Error 2: Missing Package (`ModuleNotFoundError`)
*   **Symptom**: You see errors like `ModuleNotFoundError: No module named 'xgboost'`.
*   **Cause**: Your environment hasn't installed all necessary project libraries.
*   **Fix**: Run this command to sync your environment:
    ```bash
    pixi install
    ```

### 🚨 Error 3: File Not Found Errors (`SystemExit: No feature files found`)
*   **Symptom**: You trigger a labeling or training script, and it complains about missing files or empty DataFrames.
*   **Cause**: You skipped a step. For example, you tried to generate labels without first generating features.
*   **Fix**: Follow the pipeline steps in strict order as defined in the [Usage Guide](USAGE_GUIDE.md): Download Data -> Resample Candles -> Generate Features -> Label.

### 🚨 Error 4: Out Of Memory (OOM) / Crashes
*   **Symptom**: Your computer runs out of RAM and kills the script.
*   **Cause**: You might be trying to load all 10+ years of raw `.parquet` tick data into memory at once, which can exceed 20GB.
*   **Fix**: Always use Polars' `scan_parquet()` (Lazy Evaluation) to process data in chunks without overloading RAM, rather than `read_parquet()`.

### 🚨 Error 5: Download randomly freezes or network drops
*   **Symptom**: `download_data.py` stops running halfway through downloading historical data.
*   **Fix**: The script automatically tracks progress in `completed_months.json`. Simply rerun `pixi run python pipeline/download_data.py`, and it will resume exactly from where it left off.

---

### 💡 Quick Tip: Performing a Clean Reset
If you accidentally modified pipeline scripts and generated corrupted data files, you can easily delete your generated caches and start fresh without losing the original raw tick data.

```bash
# This cleans all generated candles, features, and labels.
# It safely keeps raw TICK data intact so you don't have to download it again.
rm -rf data/ohlcv/* data/features/* data/labels/*

# Afterwards, safely re-run the Resampling, Features, and Labeling scripts.
```
