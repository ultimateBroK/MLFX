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

---

## 2. Available Backends

The CLI currently supports:

- `mlf`
- `lstm`
- `sgd`
- `stats`

---

## 3. Comparison Table

| Backend | Family | Strengths | Weaknesses | Data Requirement | Compute Cost | Interpretability | Best Use Case |
|---|---|---|---|---|---|---|---|
| `stats` | Statistical baseline | Fast, simple, cheap baseline | Limited nonlinear modeling | low | very low | high | sanity check, baseline comparison |
| `sgd` | Linear / online ML | Fast, lightweight, scalable | Weaker on complex feature interactions | Low to medium | Low | Medium | Large tabular feature sets, cheap experiments |
| `mlf` | Gradient boosting / tabular forecasting | Strong baseline, handles nonlinear patterns well | Less sequence-native than DL | Medium | Medium | Medium | Default production-style baseline |
| `lstm` | Deep learning sequence model | Models temporal dependencies directly | Slower, more tuning-sensitive | Medium to high | High | Low | Sequential patterns over rolling windows |

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
Choose:

- `lstm`

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

## 6. Practical Benchmarking Strategy

A sensible experiment ladder is:

### Stage 1 — Cheap baselines
- `stats`
- `sgd`

### Stage 2 — Strong default benchmark
- `mlf`

### Stage 3 — Sequence models
- `lstm`

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

---

## 8. Production Readiness Heuristic

This is a practical heuristic, not a strict rule.

| Backend | Operational Simplicity | Training Stability | Deployment Simplicity | Overall Production Friendliness |
|---|---|---|---|---|
| `stats` | High | high | high | high |
| `sgd` | High | High | High | High |
| `mlf` | High | High | Medium to High | High |
| `lstm` | Medium | Medium | Medium | Medium |

For most teams, `mlf` is the most realistic production-oriented starting point.

---

## 9. Recommended Default Workflow

If you are unsure, do this:

```text
1. Run `stats`
2. Run `sgd`
3. Run `mlf`
4. Compare evaluation metrics
5. Only then test `lstm`
```

This prevents over-investing in complex models before proving they are necessary.

---

## 10. Common Mistakes

- Starting with `lstm` before establishing a baseline
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
Start with `lstm`.

---

## 12. See Also

- [Architecture](ARCHITECTURE.md)
- [Usage Guide](../guides/USAGE_GUIDE.md)
- [Evaluation Guide](../guides/EVALUATION_GUIDE.md)
- [Config Reference](../reference/CONFIG_REFERENCE.md)
- [Glossary](../reference/GLOSSARY.md)
