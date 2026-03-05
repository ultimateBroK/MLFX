# System Anatomy: A Guide for Beginners 🧠

Welcome! Instead of confusing you with dense code immediately, this document explains **how the bot works behind the scenes**. By understanding the big picture, you'll have an easier time navigating the project.

Think of building an AI trading bot like refining raw coffee beans into a perfect espresso. It requires a structured 4-step Data Pipeline.

---

## 🔧 The 4 Core Stages

### 1️⃣ Raw Data Extraction (Ticks to Candles)
The market records data using "Ticks" (every single price change). Computers can't easily learn from raw ticks because there's too much noise.
The `resample.py` script compacts millions of these raw ticks into structured Candlesticks (like 1 Hour, 5 Minute, or 15 Minute charts).

### 2️⃣ Feature Engineering (Giving the AI context)
If you just give an AI a bunch of green and red candles, it doesn't know where the tops or bottoms are.
The `features.py` script calculates and attaches over 133 technical indicators to these candles. 
*   **Example:** A specific candle might now have a tag that says "RSI is 30 (oversold)" or "Price is 5 pips away from last week's support." This gives the AI the context it needs to see the market properly.

### 3️⃣ Labeling (Grading the Exam)
To train an AI, you have to give it a historical test where the "answers" are already filled in. 
The `labels.py` script peeks into the future. If it sees that Gold's price shot up over the next 10 candles, it marks the current candle with a `"LONG"` label. It repeats this process across billions of candles over a 10-year history.

### 4️⃣ Machine Learning (Finding the Patterns)
Now the magic happens. We feed all this data (Features + Labels) into a Machine Learning model like XGBoost or an LSTM network.
The AI scans the data and figures out the underlying rules:
> *"Aha! I've noticed that whenever MACD crosses up AND RSI touches 30 AND we are in the London session... the chance of a successful LONG trade is 70%!"*

### 5️⃣ Backtesting (The Practice Run)
You never deploy a brand new AI directly to live trading. 
We use the `backtest.py` simulation engine to force the AI to trade historical data blindly, observing strict Risk Management rules (e.g., risking $100 to make $150). 
When the simulation finishes, it provides a full report showing its Win Rate and an Equity Curve (a chart showing wealth progression). 

Check out [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) to learn how to read these backtest reports.

---

## 🎯 Essential Mindsets for ML_FX

If you're just getting started, here are a few things to keep in mind:

1. **The Bot is NOT a Crystal Ball:** The AI doesn't predict the future flawlessly. It strictly operates on probability. It finds historical patterns with high win rates and relies on strict Stop Losses and Take Profits to handle the inevitable losing trades.
2. **Follow the Exact Sequence:** The pipeline must be run in order: **Data -> Candles -> Features -> Labels -> Train**. Trying to train the AI before calculating its features will result in immediate "File Missing" errors. Check [USAGE_GUIDE.md](USAGE_GUIDE.md) for the exact run order.
3. **Use the Glossary:** If you see a term you don't know (like *Tick*, *Parquet*, *OHLCV*, *Optuna*), check [GLOSSARY.md](GLOSSARY.md) for a simple definition.
4. **Don't Panic on Errors:** If your terminal shows errors, take a breath and open [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Over 99% of common issues (like missing files or memory limits) are documented there with quick fixes.

---

You're fully prepared! Head over to the [Usage Guide](USAGE_GUIDE.md) and start running some commands!
