# MLFX Backend Comparison

This document compares the training backends currently exposed through the `mlfx train` CLI so you can choose the right one for your use case.

---

## 1. Quick Recommendation

If you want the shortest path to a strong baseline:

- Start with `mlf`
- Compare against `stats` and `sgd`
- Only move to deep learning backends if you have a clear reason such as:
  - Sequential pattern modeling
  - Longer training windows
  - Enough data volume
  - Enough compute budget

A practical order is:

1. `stats`
2. `sgd`
3. `mlf`
4. `lstm`
5. `bilstm`
6. `cnn_lstm`
7. `transformer`
8. `neuralforecast`

---

## 2. Available Backends

The CLI currently supports:

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

---

## 3. Comparison Table

| Backend | Family | Strengths | Weaknesses | Data Requirement | Compute Cost | Interpretability | Best Use Case |
|---|---|---|---|---|---|---|---|
| `stats` | Statistical baseline | fast, simple, cheap baseline | limited nonlinear modeling | low | very low | high | sanity check, baseline comparison |
| `sgd` | Linear / online ML | fast, lightweight, scalable | weaker on complex feature interactions | low to medium | low | medium | large tabular feature sets, cheap experiments |
| `mlf` | Gradient boosting / tabular forecasting | strong baseline, handles nonlinear patterns well | less sequence-native than DL | medium | medium | medium | default production-style baseline |
| `lstm` | Deep learning sequence model | models temporal dependencies directly | slower, more tuning-sensitive | medium to high | high | low | sequential patterns over rolling windows |
| `bilstm` | Bidirectional sequence model | richer context than plain LSTM | more expensive, may be less realistic for strict causal inference if misused in setup | high | high | low | offline experiments with richer sequence encoding |
| `cnn_lstm` | Hybrid DL | good at local pattern extraction + sequence modeling | more architecture complexity | high | high | low | candlestick-like local motifs plus temporal context |
| `transformer` | Attention-based DL | flexible long-range dependency modeling | compute-heavy, tuning-heavy, data-hungry | high | very high | low | large datasets, longer-range pattern modeling |
| `neuralforecast` | Forecasting DL ecosystem | strong for time-series experimentation | library complexity, tuning overhead | medium to high | high | low | advanced forecasting experiments |
| `mlf` | Boosted tabular forecasting | balanced performance and usability | not the best for all long-context sequence problems | medium | medium | medium | first serious model to train |

---

## 4. Backend-by-Backend Details

## 4.1 `stats`

### What it is
`stats` is the simplest statistical baseline. It is useful as a reference point before trying more advanced models.

### Strengths
- Fastest to run
- Lowest operational complexity
- Gives you a baseline that is easy to explain
- Useful for checking whether complex models add real value

### Weaknesses
- Limited ability to model nonlinear relationships
- Usually underperforms on richer feature sets
- May miss regime-dependent or interaction-heavy effects

### Use it when
- You need a sanity-check baseline
- You are benchmarking multiple backends
- You want to validate the pipeline end-to-end cheaply

### Avoid it when
- You expect complex nonlinear feature interactions
- You want top predictive performance

---

## 4.2 `sgd`

### What it is
`sgd` is a lightweight machine learning baseline based on stochastic gradient descent.

### Strengths
- Fast training
- Low memory use
- Suitable for iterative experimentation
- Often stronger than pure statistical baselines

### Weaknesses
- Still relatively simple compared with boosted trees or deep learning
- Performance depends more on feature quality and scaling
- May struggle when the decision surface is highly nonlinear

### Use it when
- You want a cheap ML baseline
- You have large tabular data
- You want fast feedback loops

### Avoid it when
- Your problem depends heavily on nonlinear relationships
- You already know sequence structure is critical

---

## 4.3 `mlf`

### What it is
`mlf` is the strongest default baseline for most MLFX users. It is the most practical starting point for serious experiments.

### Strengths
- Usually the best first model to try
- Strong on tabular engineered features
- Handles nonlinear relationships better than linear models
- Practical balance of performance, speed, and maintainability
- Often easier to operationalize than deep learning backends

### Weaknesses
- Not sequence-native in the same way as recurrent or attention models
- May plateau if predictive signal depends strongly on long temporal context
- Hyperparameter search can increase runtime

### Use it when
- You want the best default backend
- You are training on engineered feature tables
- You want a robust benchmark for all other backends

### Avoid it when
- You specifically need deep sequence modeling
- Your research question is about long-range temporal representation learning

---

## 4.4 `lstm`

### What it is
`lstm` is a recurrent neural network backend designed for sequence modeling.

### Strengths
- Directly models ordered temporal context
- Useful for rolling-window sequential learning
- Can capture patterns not obvious in independent tabular rows

### Weaknesses
- Slower to train
- More sensitive to window length and other hyperparameters
- Harder to debug than simpler ML models
- Can overfit if data volume is limited

### Use it when
- Temporal order matters strongly
- You have enough data for sequence learning
- You are willing to trade simplicity for modeling flexibility

### Avoid it when
- You need fast experiments
- You have a small dataset
- `mlf` already performs well enough

---

## 4.5 `bilstm`

### What it is
`bilstm` is a bidirectional LSTM variant that encodes sequence information in both directions within the training setup.

### Strengths
- Richer sequence representation than plain `lstm`
- May capture context more effectively in offline experiments
- Useful when local sequence context around each point matters

### Weaknesses
- More expensive than `lstm`
- Added complexity may not translate into meaningful gains
- Requires careful interpretation in time-series workflows

### Use it when
- You are doing offline modeling experiments
- You want to test whether richer sequence encoding helps
- You already established that sequence models are worthwhile

### Avoid it when
- You want the simplest deployable model
- You are still establishing your first strong baseline

---

## 4.6 `cnn_lstm`

### What it is
`cnn_lstm` combines convolutional feature extraction with recurrent sequence modeling.

### Strengths
- Can learn short-term local motifs before sequence aggregation
- Useful for repeated local price-pattern structures
- Often a good compromise between raw sequence modeling and hierarchical pattern extraction

### Weaknesses
- More complex than plain recurrent models
- Tuning is harder
- Training cost is still high
- Model behavior is less interpretable

### Use it when
- You suspect local window patterns matter
- You want to combine motif detection with temporal modeling
- Plain `lstm` is not expressive enough

### Avoid it when
- You need a simple experimental baseline
- Your compute budget is constrained

---

## 4.7 `transformer`

### What it is
`transformer` is an attention-based deep learning backend for sequence modeling.

### Strengths
- Flexible architecture for long-range dependencies
- Strong representation capacity
- Attractive for larger datasets and longer contexts

### Weaknesses
- Highest tuning burden among common choices
- Expensive in memory and compute
- Can underperform simpler backends on modest datasets
- Easy to use prematurely before strong baselines are established

### Use it when
- You have substantial data
- You want to model longer-range context
- You are explicitly researching attention-based sequence models

### Avoid it when
- You are early in the project
- You need quick training cycles
- You have not yet benchmarked `mlf` or `lstm`

---

## 4.8 `neuralforecast`

### What it is
`neuralforecast` is a forecasting-oriented deep learning backend built around a specialized ecosystem for time-series models.

### Strengths
- Good for advanced forecasting experiments
- Can provide access to architectures beyond a single custom model
- Useful when your workflow is close to forecasting research

### Weaknesses
- Added library and integration complexity
- Training and tuning overhead
- Not always the simplest fit for classification-style decision workflows

### Use it when
- You want to explore forecasting-native neural methods
- You are already comfortable with deeper experimentation
- Your problem benefits from a forecasting-centric setup

### Avoid it when
- You just need a practical first model
- Operational simplicity matters more than experimentation breadth

---

## 5. Selection Guide by Goal

## 5.1 I want the fastest useful baseline
Choose:

1. `stats`
2. `sgd`
3. `mlf`

Start with `stats`, then move to `sgd`, then `mlf`.

---

## 5.2 I want the best practical default
Choose:

- `mlf`

This should usually be your first serious benchmark.

---

## 5.3 I want to model temporal sequences directly
Choose from:

- `lstm`
- `bilstm`
- `cnn_lstm`
- `transformer`

Recommended order:

1. `lstm`
2. `bilstm`
3. `cnn_lstm`
4. `transformer`

---

## 5.4 I want the lowest compute cost
Choose:

- `stats`
- `sgd`

---

## 5.5 I want the easiest model to explain
Choose:

- `stats`
- `sgd`
- `mlf`

Deep learning backends are less transparent.

---

## 5.6 I want advanced experimentation breadth
Choose:

- `transformer`
- `neuralforecast`
- `cnn_lstm`

These are best once you already have solid simpler benchmarks.

---

## 6. Practical Benchmarking Strategy

A sensible experiment ladder is:

### Stage 1 — Cheap baselines
- `stats`
- `sgd`

### Stage 2 — Strong default benchmark
- `mlf`

### Stage 3 — Sequence models
- `lstm`
- `bilstm`

### Stage 4 — More complex deep learning
- `cnn_lstm`
- `transformer`
- `neuralforecast`

The point is not to train everything immediately. The point is to build confidence step by step.

---

## 7. Suggested Decision Matrix

| Situation | Recommended Backend |
|---|---|
| New repo user, first serious run | `mlf` |
| Need a sanity-check baseline | `stats` |
| Need a cheap ML baseline | `sgd` |
| Best balance of practicality and power | `mlf` |
| Strong sequential dependency suspected | `lstm` |
| Want richer sequence encoding | `bilstm` |
| Want local motif extraction + sequence modeling | `cnn_lstm` |
| Want long-range attention experiments | `transformer` |
| Want forecasting-oriented neural experimentation | `neuralforecast` |

---

## 8. Production Readiness Heuristic

This is a practical heuristic, not a strict rule.

| Backend | Operational Simplicity | Training Stability | Deployment Simplicity | Overall Production Friendliness |
|---|---|---|---|---|
| `stats` | high | high | high | high |
| `sgd` | high | high | high | high |
| `mlf` | high | high | medium to high | high |
| `lstm` | medium | medium | medium | medium |
| `bilstm` | medium | medium | medium | medium |
| `cnn_lstm` | low to medium | medium | medium | medium |
| `transformer` | low | low to medium | medium | low to medium |
| `neuralforecast` | medium | medium | medium | medium |

For most teams, `mlf` is the most realistic production-oriented starting point.

---

## 9. Recommended Default Workflow

If you are unsure, do this:

```text
1. Run `stats`
2. Run `sgd`
3. Run `mlf`
4. Compare evaluation metrics
5. Only then test `lstm` or other DL backends
```

This prevents over-investing in complex models before proving they are necessary.

---

## 10. Common Mistakes

- Starting with `transformer` before establishing a baseline
- Comparing deep learning results against nothing
- Using expensive backends with too little data
- Assuming complex models are automatically better
- Ignoring operational cost when choosing a backend
- Skipping `stats` or `sgd` and losing a useful sanity check
- Treating one strong backtest as enough evidence

---

## 11. Final Recommendations

### For most users
Use `mlf`.

### For baseline comparison
Use `stats` and `sgd`.

### For sequence research
Start with `lstm`, then try `bilstm`.

### For advanced deep learning exploration
Try `cnn_lstm`, `transformer`, or `neuralforecast` only after you already understand how your simpler baselines behave.

---

## 12. See Also

- [Architecture](ARCHITECTURE.md)
- [Usage Guide](../guides/USAGE_GUIDE.md)
- [Evaluation Guide](../guides/EVALUATION_GUIDE.md)
- [Config Reference](../reference/CONFIG_REFERENCE.md)
- [Glossary](../reference/GLOSSARY.md)
