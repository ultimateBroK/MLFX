# MLFX - Glossary

This document collects the most common terms used across the MLFX project.  
Its goal is to help you read the documentation, use the CLI, and interpret outputs without mixing up technical concepts.

---

## 1. Market data

- `Tick data`: Data at the smallest observed price-change level, usually recorded on each market update.
- `OHLCV`: Short for `Open`, `High`, `Low`, `Close`, `Volume`; the standard candlestick representation.
- `Timeframe` or `TF`: The duration of a single candle, for example `1m`, `5m`, `15m`, `1H`, `4H`, `1D`.
- `Bid price`: The buy-side price in the market.
- `Ask price`: The sell-side price in the market.
- `Spread`: The difference between bid and ask.
- `Mid price`: The midpoint price, usually computed as `(bid + ask) / 2`.
- `Timestamp`: The time marker attached to each row of data or each candle.
- `Parquet`: A columnar file format commonly used for analytical datasets with good performance.
- `Data gap`: A time range where expected data is missing.
- `Raw data`: Data that has not been processed yet, usually stored under `data/raw/`.
- `Processed data`: Data that has gone through transformation, feature engineering, or labeling.

---

## 2. Trading concepts

- `Support`: A price zone where buying pressure often becomes stronger, causing price to pause or bounce.
- `Resistance`: A price zone where selling pressure often becomes stronger, causing price to pause or reverse.
- `Pivot Point`: A reference price level computed from prior-session data and used as a support / resistance guide.
- `Killzone`: High-liquidity time windows in the ICT framework, such as London or New York session windows.
- `LONG`: A signal expecting price to rise.
- `SHORT`: A signal expecting price to fall.
- `NEUTRAL`: No strong enough signal to take a trade.
- `Take-profit` (`TP`): A target profit level or exit price for closing a winning trade.
- `Stop-loss` (`SL`): A maximum accepted loss level or exit price for closing a losing trade.
- `Entry`: The moment a position is opened.
- `Exit`: The moment a position is closed.
- `Backtest`: A simulation of trading on historical data to evaluate a strategy or model.
- `Trade simulator`: The component that converts signals into simulated trades and computes outcomes.
- `R-multiple` or `R`: A normalized profit / risk unit based on the initial risk of a trade.
- `Commission`: Transaction cost deducted from simulated results.
- `Slippage`: The difference between the expected price and the simulated execution price.
- `Equity curve`: A chart showing capital growth or decline over time.
- `Drawdown`: The drop from an equity peak to a subsequent trough over a period.

---

## 3. Feature engineering

- `Feature`: An input variable used for training or inference.
- `Feature engineering`: The process of creating additional useful columns from raw price data.
- `Normalization`: Transforming values so they become easier to compare or share a more consistent scale.
- `RSI`: Relative Strength Index, a momentum indicator.
- `MACD`: Moving Average Convergence Divergence.
- `EMA`: Exponential Moving Average.
- `ATR`: Average True Range, used to measure volatility.
- `Order Block`: A structure-based price zone often interpreted as evidence of larger market participation.
- `Fair Value Gap` (`FVG`): A price imbalance gap between candles, often used as contextual structure.
- `Session feature`: A column that reflects trading sessions or market time windows.
- `Context-aware feature`: A column that reflects not only price itself, but also market structure or state.

---

## 4. Labels and training

- `Label`: The target column learned by the model, for example `label_5`, `label_10`, `label_20`.
- `Ordinal label`: A label with multiple ordered levels, such as `-2`, `-1`, `0`, `1`, `2`.
- `Look-ahead horizon`: The number of future bars used to create a label.
- `ATR multiplier`: The ATR-based factor used to avoid overly noisy labels.
- `Backend`: A specific model type or training pipeline.
- `Training`: The process of teaching a model from labeled data.
- `Training set`: The part of the data used to fit the model.
- `Validation set`: The part of the data used to tune the model during training.
- `Test set`: The part of the data used for final evaluation.
- `Data leakage`: A situation where future information accidentally enters training, producing unrealistically good results.
- `TimeSeriesSplit`: A time-aware splitting strategy for time-series problems.
- `Cross-validation`: Repeatedly splitting and evaluating a model to obtain more stable estimates.
- `Hyperparameter tuning`: Trying multiple model configurations to find a better setup.
- `Optuna`: A library for automated hyperparameter optimization.
- `Model artifact`: Output files from training, such as a saved model, configuration, and metrics.
- `Model registry`: The place where information about trained models is stored.
- `Experiment tracking`: The process of recording parameters, metrics, and outputs for each training run.

---

## 5. Evaluation and reporting

- `Win Rate`: The percentage of trades that are profitable.
- `Profit Factor`: Total gross profit divided by total gross loss.
- `Net Profit`: Final profit after subtracting costs and losses.
- `Sharpe Ratio`: A measure of return relative to overall volatility.
- `Sortino Ratio`: Similar to Sharpe, but focused only on downside volatility.
- `Calmar Ratio`: Return relative to maximum drawdown.
- `Heatmap`: A chart that shows performance by hour or by weekday.
- `Candlestick HTML report`: A visual report showing price, signals, and selected indicators on a candlestick chart.
- `Baseline`: An initial reference result used to compare stronger or more complex models against.
- `Out-of-sample evaluation`: Evaluation on data the model did not see during training.

---

## 6. Current backends

- `mlf`: `MLForecast + LightGBM` pipeline, usually the most practical default choice.
- `lstm`: LSTM model implemented with PyTorch.
- `sgd`: Very lightweight baseline based on `SGDClassifier`.
- `stats`: Statistical baseline models.

---

## 7. Main repository outputs

- `data/raw/`: Downloaded raw tick data.
- `data/ohlcv/`: Candle data resampled from raw tick data.
- `data/features/`: Feature-enriched datasets.
- `data/labels/`: Labeled datasets.
- `outputs/models/{symbol}/{tf}/{label}/`: Model artifacts, metrics, and training metadata for a specific label.
- `outputs/reports/{symbol}/{tf}/{label}/{mode}/{run}/`: Backtest reports and related charts grouped by label, evaluation mode, and run bucket such as `R15`.
- `outputs/predictions/{symbol}/{tf}/{label}/`: Batch prediction outputs for a specific label.
- `outputs/monitoring/{symbol}/{tf}/`: Outputs for monitoring and drift detection.
- `outputs/runs/{symbol}/{tf}/`: Run logs when using the file-based tracking path.

---

## 8. Monitoring and operations

- `Serving`: The process of exposing a trained model so it can accept inputs and return predictions.
- `Inference`: The process of using a trained model to generate new predictions.
- `Batch inference`: Running predictions over a larger dataset and saving them to disk.
- `Real-time inference`: Receiving requests via API and returning predictions immediately.
- `FastAPI`: The web framework used to build the serving layer.
- `Health check`: A simple endpoint or mechanism to confirm that the service is still operating correctly.
- `Data drift` / `Feature drift`: A situation where new data has a significantly different distribution from training data.
- `PSI`: Population Stability Index, a measure used for distribution drift.
- `KS test`: Kolmogorov–Smirnov test, used to compare distributions.
- `Structured logging`: Writing logs in a machine-readable format, usually JSON lines.

---

## 9. Short summary

If you are new to the repository, the main concept chain to remember is:

- tick data → OHLCV → features → labels → training → evaluation → reports → serving → monitoring

That is the backbone of the entire MLFX system.
