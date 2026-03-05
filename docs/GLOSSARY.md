# Glossary

A beginner-friendly guide to Trading and Machine Learning terms used in ML_FX.

---

## 1. Trading Terminology

*   **Tick Data**: The smallest unit of market data. Every time the price fluctuates even by a small fraction (a tick), the broker records it. Because there can be dozens of ticks per second, this data is incredibly dense.
*   **OHLCV**: Stands for Open, High, Low, Close, Volume. This represents the Open price, Highest price, Lowest price, Close price, and trading Volume of an asset during a specific time interval (e.g., 1 Hour candle).
*   **Timeframe (TF)**: The time duration of a single candlestick. Commonly `1m` (1 minute), `5m` (5 minutes), `1H` (1 hour).
*   **S/R (Support/Resistance)**: Support (price levels where a downtrend tends to pause) and Resistance zones (price levels where an uptrend tends to pause).
*   **Killzone**: Specific time windows that carry the highest trading volumes. In this project, we target 3 Killzones: Asian, London, and New York. ICT strategies heavily rely on trading during these highly liquid zones.
*   **ATR (Average True Range)**: An indicator that measures market volatility. Higher ATR means larger price swings. We use ATR to dynamically calculate safe Take Profit and Stop Loss targets instead of using rigid Pip increments.
*   **LONG / SHORT**: 
    *   **LONG (+1)**: Buying an asset, expecting its price to rise.
    *   **SHORT (-1)**: Selling an asset you don't own, expecting its price to drop.
*   **NEUTRAL (0)**: A lack of clear market trend. The best action is to stay out and observe.
*   **R-multiple (R)**: R stands for Risk. If you risk $100 per trade, 1R = $100. If you win and gain $150, your profit is 1.5R. Everything in this project is calculated in "R" rather than explicit cash amounts.

---

## 2. Data & Machine Learning Terminology

*   **Parquet (`.parquet`)**: A columnar data file format far superior to Excel or CSV for big data. It heavily compresses sizes while allowing extremely fast read speeds.
*   **Data Pipeline**: The step-by-step process of cleaning data: Extracting raw Tick Data -> Resampling into Candles (OHLCV) -> Calculating indicators (Features) -> Preparing targets (Labels) for the AI.
*   **Features**: The specific data points you feed to the AI. To predict prices, we give the AI context like the current RSI value or distance to resistance. ML_FX uses over 133 distinct features.
*   **Labels**: The historical "answers" (whether the future price went up or down) used to train the model. During Training, the AI looks at Features to predict the Label.
*   **KNN / XGBoost / LightGBM / LSTM**: Different Machine Learning models. KNN is a simple baseline. XGBoost and LightGBM are powerful decision-tree models excellent for financial data. LSTM is a Neural Network designed for sequential time-series patterns.
*   **Optuna**: An automated hyperparameter tuning framework. It dynamically searches for the optimal mathematical configurations for the AI models so you don't have to guess them manually.

---

## 3. Tool Terminology

*   **Pixi**: A modern project management and execution tool. It automatically downloads the correct Python version and fetches all isolated dependencies (like Polars or XGBoost) without messing up your global system environment.
*   **Polars**: A next-generation data manipulation library written in Rust. It is much faster than Pandas, allowing standard computers to process 10+ years of tick data (half a billion rows) very efficiently.
