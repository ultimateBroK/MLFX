# ML_FX - Glossary

This file collects the most common terms used across the repository.

## 1. Market data

- `Tick data`: data at the smallest observed price-change level
- `OHLCV`: Open, High, Low, Close, Volume for a candlestick
- `Timeframe` or `TF`: the duration of one candle such as `1m`, `5m`, `1H`
- `Spread`: the difference between bid and ask

## 2. Trading concepts

- `Support/Resistance`: price zones where the market often reacts
- `Pivot Points`: reference price levels derived from previous-session data
- `Killzone`: high-liquidity trading windows in the ICT approach
- `LONG`: a signal expecting price to rise
- `SHORT`: a signal expecting price to fall
- `NEUTRAL`: no strong signal
- `R-multiple` or `R`: normalized risk and return unit per trade
- `Commission`: transaction cost applied to simulated trades
- `Slippage`: simulated execution price slippage on entry or exit

## 3. Feature engineering

- `Feature`: an input variable used by the model
- `ATR`: Average True Range, a volatility measure
- `RSI`: Relative Strength Index
- `MACD`: Moving Average Convergence Divergence
- `EMA`: Exponential Moving Average
- `Order Block`: a structure-based price zone used as a feature
- `Fair Value Gap` or `FVG`: a price imbalance gap between candles

## 4. Labels and training

- `Label`: the target column learned by the model, such as `label_5`, `label_10`, `label_20`
- `Look-ahead horizon`: the number of future bars used to build a label
- `ATR multiplier`: the ATR-based threshold used to avoid noisy labels
- `Backend`: the selected model or training pipeline
- `TimeSeriesSplit`: a time-aware split strategy for time-series evaluation
- `Optuna`: a hyperparameter optimization library

## 5. Evaluation and reporting

- `Profit Factor`: gross profit divided by gross loss
- `Sharpe Ratio`: mean return relative to overall volatility
- `Sortino Ratio`: mean return relative to downside volatility
- `Calmar Ratio`: total return relative to maximum drawdown
- `Heatmap`: a performance chart grouped by UTC hour and weekday

## 6. Current backends

- `mlf`: `MLForecast + LightGBM` pipeline
- `lstm`: LSTM model
- `transformer`: Transformer-based time-series model
- `cnn_lstm`: CNN + LSTM hybrid
- `sgd`: online SGD baseline
- `stats`: statistical baseline
- `neuralforecast`: NeuralForecast backend
- `bilstm`: backend present in the codebase but not currently exposed in the CLI/TUI

## 7. Repository outputs

- `data/raw/`: raw tick data
- `data/ohlcv/`: resampled candle data
- `data/features/`: feature datasets
- `data/labels/`: labeled datasets
- `outputs/models/`: saved models, metrics, and training metadata
- `outputs/reports/`: backtest reports and charts
