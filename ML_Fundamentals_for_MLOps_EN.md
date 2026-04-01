# ML Fundamentals for MLOps: A Practical Guide
## Bridging Knowledge Gaps for AI Agent Development

---

## Table of Contents
1. [Core ML Concepts](#1-core-ml-concepts)
2. [Data Pipeline Fundamentals](#2-data-pipeline-fundamentals)
3. [Model Development Lifecycle](#3-model-development-lifecycle)
4. [Model Deployment Strategies](#4-model-deployment-strategies)
5. [Monitoring & Maintenance](#5-monitoring--maintenance)
6. [AI Agent-Specific ML Concepts](#6-ai-agent-specific-ml-concepts)
7. [MLOps Best Practices](#7-mlops-best-practices)
8. [Key Terminology Glossary](#8-key-terminology-glossary)
9. [Quick Reference Cheat Sheet](#9-quick-reference-cheat-sheet)

---

## 1. Core ML Concepts

### 1.1 Types of Machine Learning

| Type | What It Does | When to Use | Example |
|------|--------------|-------------|---------|
| **Supervised Learning** | Learns from labeled data | When you have input-output pairs | Spam detection, price prediction |
| **Unsupervised Learning** | Finds patterns in unlabeled data | When you want to discover hidden structures | Customer segmentation, anomaly detection |
| **Reinforcement Learning** | Learns through trial and error | When decisions affect future outcomes | Game AI, robot control, agent behavior |
| **Self-Supervised Learning** | Creates labels from data itself | When you have lots of unlabeled data | Language models, image recognition |

### 1.2 Common Model Types (Plain English)

#### Classification Models
```
Purpose: Sort things into categories
Input: Features about an item
Output: A category label

Example: Is this email spam or not?
- Input: Email content, sender, subject
- Output: "Spam" or "Not Spam"
```

#### Regression Models
```
Purpose: Predict a number
Input: Features about a situation
Output: A continuous value

Example: What will the house price be?
- Input: Square footage, location, bedrooms
- Output: $450,000
```

#### Clustering Models
```
Purpose: Group similar items together
Input: Features about items
Output: Group assignments

Example: Customer segmentation
- Input: Purchase history, demographics
- Output: "Budget shoppers", "Premium buyers", etc.
```

#### Sequence Models
```
Purpose: Understand ordered data (text, time series)
Input: A sequence of values
Output: Next value or classification

Example: Predict next word in a sentence
- Input: "The quick brown..."
- Output: "fox"
```

### 1.3 Key Algorithms Quick Reference

| Algorithm | Best For | Complexity | Production Notes |
|-----------|----------|------------|------------------|
| **Linear/Logistic Regression** | Simple relationships | Low | Fast inference, interpretable |
| **Decision Trees** | Rule-based decisions | Low | Easy to explain, can overfit |
| **Random Forest** | Complex patterns | Medium | Robust, handles missing data |
| **Gradient Boosting (XGBoost, LightGBM)** | Tabular data competitions | Medium | Often wins Kaggle, needs tuning |
| **Neural Networks** | Images, text, complex patterns | High | Needs lots of data, GPU |
| **Transformers** | Language, sequences | Very High | State-of-art for NLP, expensive |

### 1.4 Training vs. Inference

```
┌─────────────────────────────────────────────────────────┐
│                    TRAINING PHASE                        │
│  Data → Model Learning → Trained Model                   │
│  (Happens offline, resource-intensive)                   │
└─────────────────────────────────────────────────────────┘
                          ↓
                    Save Model
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   INFERENCE PHASE                        │
│  New Input → Trained Model → Prediction                  │
│  (Happens online, needs to be fast)                      │
└─────────────────────────────────────────────────────────┘
```

**Key Insight:** Training is like studying for an exam. Inference is like taking the exam. You train once (or periodically), but inference happens constantly in production.

---

## 2. Data Pipeline Fundamentals

### 2.1 The Data Journey

```
Raw Data
    ↓ [Collection]
    ↓ [Validation]
    ↓ [Cleaning]
    ↓ [Transformation]
    ↓ [Feature Engineering]
    ↓ [Splitting]
Ready for Training
```

### 2.2 Data Splitting Strategy

```
┌──────────────────────────────────────────────────────┐
│                    YOUR DATA                          │
├──────────────┬──────────────┬────────────────────────┤
│   TRAIN      │  VALIDATION  │      TEST              │
│    70-80%    │    10-15%    │      10-15%            │
│              │              │                        │
│ Used to      │ Used to      │ Used ONLY once         │
│ teach the    │ tune         │ to evaluate            │
│ model        │ parameters   │ final performance      │
└──────────────┴──────────────┴────────────────────────┘
```

**Critical Rule:** NEVER let your model see test data during training. It's like giving students the exam questions beforehand.

### 2.3 Feature Engineering Basics

| Technique | What It Does | When to Use |
|-----------|--------------|-------------|
| **Normalization** | Scale values to 0-1 range | When features have different scales |
| **One-Hot Encoding** | Convert categories to numbers | For categorical variables |
| **Embedding** | Dense representation of categories | When you have many categories |
| **Feature Crossing** | Combine features | When feature interactions matter |
| **Binning** | Convert continuous to discrete | To reduce noise |

### 2.4 Feature Stores (MLOps Essential)

```
┌─────────────────────────────────────────────────────────┐
│                   FEATURE STORE                          │
├─────────────────────────────────────────────────────────┤
│  Purpose: Centralized feature management                 │
│                                                          │
│  Benefits:                                               │
│  • Reuse features across models                          │
│  • Consistent feature computation                        │
│  • Point-in-time correctness                             │
│  • Serve features in real-time                           │
│                                                          │
│  Popular Tools: Feast, Tecton, AWS Feature Store         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Model Development Lifecycle

### 3.1 The ML Development Loop

```
         ┌──────────────────┐
         │  Define Problem  │
         └────────┬─────────┘
                  ↓
         ┌──────────────────┐
         │  Collect Data    │
         └────────┬─────────┘
                  ↓
         ┌──────────────────┐
         │  Prepare Data    │
         └────────┬─────────┘
                  ↓
    ┌─────────────────────────┐
    │                         │
    ↓                         │
┌───────────┐                 │
│  Train    │←────────────────┤
│  Model    │                 │
└─────┬─────┘                 │
      ↓                       │
┌───────────┐                 │
│ Evaluate  │──Not Good───────┘
│  Model    │
└─────┬─────┘
      │ Good Enough
      ↓
┌───────────┐
│   Deploy  │
└───────────┘
```

### 3.2 Experiment Tracking Essentials

**Why Track Experiments?**
- Reproduce results
- Compare approaches
- Debug failures
- Comply with regulations

**What to Track:**
```yaml
experiment:
  id: exp_001
  timestamp: 2024-01-15T10:30:00Z
  parameters:
    learning_rate: 0.001
    batch_size: 32
    epochs: 100
    model_architecture: "resnet50"
  metrics:
    accuracy: 0.94
    precision: 0.92
    recall: 0.89
    f1_score: 0.905
  artifacts:
    model_path: "s3://models/exp_001/model.pkl"
    config_path: "s3://models/exp_001/config.yaml"
  data:
    dataset_version: "v2.3"
    train_samples: 50000
    val_samples: 10000
```

**Tools:** MLflow, Weights & Biases, Neptune, ClearML

### 3.3 Hyperparameter Tuning

```
Hyperparameters = Settings YOU choose before training
Parameters = Values the MODEL learns during training

Examples of Hyperparameters:
- Learning rate: How fast the model learns
- Batch size: How many examples processed at once
- Number of layers: Depth of neural network
- Regularization: How much to prevent overfitting
```

**Tuning Strategies:**
| Strategy | When to Use | Pros/Cons |
|----------|-------------|-----------|
| Grid Search | Few parameters | Thorough but slow |
| Random Search | Many parameters | Often better than grid |
| Bayesian Optimization | Expensive training | Efficient, smart search |
| Hyperband | Large compute budget | Early stopping of bad runs |

### 3.4 Model Evaluation Metrics

**Classification Metrics:**
```
Accuracy  = (Correct Predictions) / (Total Predictions)
Precision = (True Positives) / (Predicted Positives)  -- "Of all positives predicted, how many were right?"
Recall    = (True Positives) / (Actual Positives)     -- "Of all actual positives, how many did we find?"
F1 Score  = 2 × (Precision × Recall) / (Precision + Recall)  -- Balance of both
```

**Regression Metrics:**
```
MAE  = Mean Absolute Error         -- Average absolute difference
MSE  = Mean Squared Error          -- Penalizes large errors more
RMSE = Root Mean Squared Error     -- In same units as target
R²   = Coefficient of Determination -- How much variance is explained
```

---

## 4. Model Deployment Strategies

### 4.1 Deployment Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    BATCH INFERENCE                          │
│  • Process data in large batches                           │
│  • Run on schedule (hourly, daily)                         │
│  • Example: Nightly recommendation updates                 │
│  • Tools: Spark, AWS Batch, SageMaker Batch Transform      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  REAL-TIME INFERENCE                        │
│  • Process individual requests immediately                  │
│  • Low latency required (< 100ms typically)                │
│  • Example: Fraud detection on transactions                 │
│  • Tools: FastAPI, TensorFlow Serving, TorchServe          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    EDGE INFERENCE                           │
│  • Run on device (phone, IoT, edge server)                 │
│  • No network dependency                                    │
│  • Example: Face recognition on phone                       │
│  • Tools: TensorFlow Lite, ONNX Runtime, Core ML           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Model Serving Architecture

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                           ↓
                    ┌─────────────┐
                    │  Load       │
                    │  Balancer   │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
     ┌───────────┐  ┌───────────┐  ┌───────────┐
     │  Model    │  │  Model    │  │  Model    │
     │  Server 1 │  │  Server 2 │  │  Server 3 │
     └───────────┘  └───────────┘  └───────────┘
            │              │              │
            └──────────────┼──────────────┘
                           ↓
                    ┌─────────────┐
                    │   Model     │
                    │   Registry  │
                    └─────────────┘
```

### 4.3 Deployment Strategies Comparison

| Strategy | Description | Risk | Rollback |
|----------|-------------|------|----------|
| **Blue-Green** | Two identical environments, switch traffic | Low | Instant |
| **Canary** | Route small % traffic to new model | Low | Quick |
| **A/B Testing** | Compare models on different user groups | Medium | Medium |
| **Shadow Mode** | New model runs alongside, doesn't serve | Very Low | N/A |
| **Rolling Update** | Gradually replace instances | Medium | Medium |

### 4.4 Model Registry Best Practices

```yaml
# Model Registry Entry Example
model:
  name: fraud_detection_v2
  version: 2.3.1
  stage: Production  # Staging, Production, Archived

  metadata:
    training_date: 2024-01-15
    training_duration: 4h 32m
    dataset_version: v3.2

  performance:
    accuracy: 0.967
    precision: 0.945
    recall: 0.923
    latency_p99: 45ms

  lineage:
    experiment_id: exp_0892
    data_source: s3://data/transactions/v3.2
    code_version: git@sha256:abc123

  artifacts:
    model_binary: s3://models/fraud_detection_v2/2.3.1/model.pkl
    config: s3://models/fraud_detection_v2/2.3.1/config.yaml
    requirements: s3://models/fraud_detection_v2/2.3.1/requirements.txt
```

---

## 5. Monitoring & Maintenance

### 5.1 What to Monitor

```
┌─────────────────────────────────────────────────────────────┐
│                 ML MONITORING STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SYSTEM METRICS (Infrastructure)                         │
│     • CPU/GPU utilization                                   │
│     • Memory usage                                          │
│     • Latency (p50, p95, p99)                               │
│     • Throughput (requests/second)                          │
│     • Error rates                                           │
│                                                             │
│  2. MODEL METRICS (Performance)                             │
│     • Prediction accuracy over time                         │
│     • Prediction distribution                               │
│     • Confidence scores                                     │
│     • Feature importance drift                              │
│                                                             │
│  3. DATA METRICS (Input Quality)                            │
│     • Input data distribution                               │
│     • Missing values rate                                   │
│     • Feature drift                                         │
│     • Schema changes                                        │
│                                                             │
│  4. BUSINESS METRICS (Impact)                               │
│     • Revenue impact                                        │
│     • User engagement                                       │
│     • Conversion rates                                      │
│     • Customer satisfaction                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Detecting Drift

**Data Drift:** Input data changes over time
```
Training data: 30% premium users
Current data:  60% premium users
→ Model might perform worse
```

**Concept Drift:** The relationship between input and output changes
```
Before: Price = f(size, location)
After:  Price = f(size, location, interest_rates)  // New factor matters
→ Model needs retraining
```

**Detection Methods:**
| Method | How It Works | Tools |
|--------|--------------|-------|
| Statistical tests | Compare distributions (KS, Chi-squared) | Evidently, WhyLabs |
| Distance metrics | Measure distance between distributions | Custom + MLflow |
| Performance tracking | Monitor prediction accuracy | Prometheus + Grafana |
| PCA-based | Detect changes in feature space | Scikit-learn |

### 5.3 Retraining Triggers

```python
# Retraining Decision Logic
def should_retrain(model_metrics, data_metrics, schedule):
    triggers = []

    # Performance-based
    if model_metrics.accuracy < THRESHOLD:
        triggers.append("accuracy_drop")

    # Data drift-based
    if data_metrics.drift_score > DRIFT_THRESHOLD:
        triggers.append("significant_drift")

    # Time-based
    if schedule.days_since_last_train > RETRAIN_INTERVAL:
        triggers.append("scheduled")

    # Data volume-based
    if data_metrics.new_samples > MIN_NEW_SAMPLES:
        triggers.append("new_data_available")

    return len(triggers) > 0, triggers
```

### 5.4 The Retraining Pipeline

```
┌─────────────────┐
│  Detect Trigger │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Collect New Data│
└────────┬────────┘
         ↓
┌─────────────────┐
│   Validate Data │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Train New Model│
└────────┬────────┘
         ↓
┌─────────────────┐
│  Evaluate Model │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
 Better    Worse
    │         │
    ↓         ↓
┌───────┐ ┌───────────┐
│Deploy │ │Keep Old   │
│New    │ │Investigate│
└───────┘ └───────────┘
```

---

## 6. AI Agent-Specific ML Concepts

### 6.1 Reinforcement Learning for Agents

```
┌─────────────────────────────────────────────────────────────┐
│              REINFORCEMENT LEARNING BASICS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ┌──────────┐      Action       ┌──────────┐            │
│     │  AGENT   │ ─────────────────→│ENVIRONMENT│            │
│     └────┬─────┘                   └─────┬────┘            │
│          │                               │                  │
│          │←──────────────────────────────│                  │
│          │        State + Reward         │                  │
│                                                             │
│  Key Concepts:                                              │
│  • State: Current situation/observation                     │
│  • Action: What the agent can do                            │
│  • Reward: Feedback signal (good/bad)                       │
│  • Policy: Strategy for choosing actions                    │
│  • Value: Expected long-term reward                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Common RL Algorithms for AI Agents:**
| Algorithm | Type | Best For |
|-----------|------|----------|
| Q-Learning | Value-based | Simple, discrete actions |
| DQN | Deep RL | Complex states (images, text) |
| PPO | Policy gradient | General purpose, stable |
| A3C | Actor-Critic | Parallel training |
| SAC | Off-policy | Continuous actions |

### 6.2 Multi-Agent Systems

```
┌─────────────────────────────────────────────────────────────┐
│                  MULTI-AGENT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Patterns:                                                  │
│                                                             │
│  1. HIERARCHICAL                                            │
│     ┌──────────┐                                            │
│     │ Manager  │                                            │
│     └────┬─────┘                                            │
│      ┌───┼───┐                                              │
│      ↓   ↓   ↓                                              │
│    ┌───┐┌───┐┌───┐                                         │
│    │W1││W2││W3│  Worker agents                              │
│    └───┘└───┘└───┘                                         │
│                                                             │
│  2. COOPERATIVE                                             │
│    ┌───┐ ←──→ ┌───┐ ←──→ ┌───┐                             │
│    │A1 │ ←──→ │A2 │ ←──→ │A3 │  Shared goal                │
│    └───┘     └───┘     └───┘                               │
│                                                             │
│  3. COMPETITIVE                                             │
│    ┌───┐                   ┌───┐                            │
│    │A1 │ ←─── adversarial ──→│A2 │                         │
│    └───┘                   └───┘                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Tool Use & Function Calling

```python
# Conceptual Tool Definition
tools = {
    "search_web": {
        "description": "Search the internet for information",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "default": 10}
        }
    },
    "execute_code": {
        "description": "Run Python code",
        "parameters": {
            "code": {"type": "string"},
            "timeout": {"type": "integer", "default": 30}
        }
    }
}

# Agent Decision Process
def agent_act(observation, tools):
    # 1. Understand the task
    task = parse_task(observation)

    # 2. Decide if tools are needed
    if needs_tools(task):
        # 3. Choose appropriate tool
        tool = select_tool(task, tools)
        # 4. Generate parameters
        params = generate_params(task, tool)
        # 5. Execute and observe result
        result = execute_tool(tool, params)

    # 6. Generate response
    return generate_response(task, result)
```

### 6.4 Agent Memory Systems

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT MEMORY TYPES                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SHORT-TERM MEMORY (Context Window)                         │
│  ├── Current conversation                                   │
│  ├── Recent actions                                         │
│  └── Temporary calculations                                 │
│      Size: Limited (e.g., 4K-128K tokens)                   │
│                                                             │
│  LONG-TERM MEMORY (Persistent Storage)                      │
│  ├── Vector Database (semantic search)                      │
│  │   Tools: Pinecone, Weaviate, Chroma                      │
│  ├── Knowledge Graph (structured relationships)             │
│  │   Tools: Neo4j, NetworkX                                 │
│  └── Document Store (facts, documents)                      │
│      Tools: MongoDB, Elasticsearch                          │
│                                                             │
│  EPISODIC MEMORY (Past Experiences)                         │
│  └── Successful/failed actions and outcomes                 │
│      Used for: Learning from mistakes, improving decisions   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 Planning & Reasoning Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                  COMMON AGENT PATTERNS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. REACT (Reason + Act)                                    │
│     Thought → Action → Observation → Thought → ...          │
│                                                             │
│  2. CHAIN-OF-THOUGHT (CoT)                                  │
│     Step 1 → Step 2 → Step 3 → Answer                       │
│                                                             │
│  3. TREE-OF-THOUGHT (ToT)                                   │
│          ┌─── Option A ───┐                                 │
│     Problem ─┼─── Option B ─┼── Best ─→ Solution            │
│          └─── Option C ───┘                                 │
│                                                             │
│  4. REFLEXION                                               │
│     Attempt → Critique → Improve → Retry                    │
│                                                             │
│  5. PLANNING-BASED                                          │
│     Goal → Decompose → Plan → Execute → Verify              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. MLOps Best Practices

### 7.1 The MLOps Maturity Model

```
Level 0: Manual Process
├── Ad-hoc training
├── Manual deployment
└── No monitoring

Level 1: ML Pipeline Automation
├── Automated training pipeline
├── Manual deployment
└── Basic monitoring

Level 2: CI/CD Pipeline Automation
├── Automated training
├── Automated testing
├── Automated deployment
└── Comprehensive monitoring

Level 3: Fully Automated MLOps
├── Automated retraining
├── A/B testing
├── Drift detection
├── Self-healing pipelines
└── Full governance
```

### 7.2 Version Everything

```
Version Control Checklist:
├── Code (Git)
├── Data (DVC, lakeFS)
├── Models (MLflow Model Registry)
├── Configurations (Git + YAML)
├── Experiments (MLflow/W&B)
├── Infrastructure (Terraform)
└── Documentation (Git)
```

### 7.3 Testing Strategy for ML

```
┌─────────────────────────────────────────────────────────────┐
│                     ML TESTING PYRAMID                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────┐                              │
│                    │  E2E    │  Full pipeline integration   │
│                   ┌┴─────────┴┐                             │
│                   │  Model    │  Performance, bias,         │
│                   │  Quality  │  fairness tests             │
│                  ┌┴───────────┴┐                            │
│                  │ Integration │  Data + model + API        │
│                 ┌┴─────────────┴┐                           │
│                 │   Unit Tests  │  Functions, transforms    │
│                ┌┴───────────────┴┐                          │
│                │  Data Validation │  Schema, distributions  │
│                └─────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Cost Optimization Strategies

| Strategy | Description | Savings |
|----------|-------------|---------|
| Spot/Preemptible VMs | Use cheaper interruptible instances | 60-90% |
| Auto-scaling | Scale to zero when not in use | 40-70% |
| Model Compression | Quantization, pruning, distillation | 50-80% inference |
| Batch Processing | Batch inference vs real-time | 30-50% |
| Right-sizing | Match instance to workload | 20-40% |
| Caching | Cache predictions for common inputs | 10-30% |

### 7.5 Security Checklist

```
ML Security Checklist:
├── Data Security
│   ├── Encryption at rest and in transit
│   ├── Access controls (RBAC)
│   └── Data anonymization/anonymization
│
├── Model Security
│   ├── Model signing and verification
│   ├── Secure model storage
│   └── Access logging
│
├── Infrastructure Security
│   ├── Network isolation (VPC)
│   ├── Secrets management
│   ├── Container scanning
│   └── Regular patching
│
└── Inference Security
    ├── Input validation
    ├── Rate limiting
    ├── Output filtering
    └── Audit logging
```

---

## 8. Key Terminology Glossary

| Term | Plain English Definition |
|------|-------------------------|
| **Artifact** | Any file produced during ML (model, data, logs) |
| **Batch Size** | Number of examples processed at once during training |
| **Bias** | Error from wrong assumptions (underfitting) or unfairness |
| **Checkpoint** | Saved model state during training |
| **Class Imbalance** | When some classes have many more examples than others |
| **Confusion Matrix** | Table showing prediction vs actual counts |
| **Data Lineage** | History of where data came from and how it changed |
| **Epoch** | One complete pass through training data |
| **Feature** | An input variable used for prediction |
| **Feature Store** | Centralized repository for ML features |
| **Gradient** | Direction to adjust weights to reduce error |
| **Ground Truth** | The correct answer (from labeled data) |
| **Hyperparameter** | Setting you choose before training |
| **Inference** | Using a trained model to make predictions |
| **Label** | The correct output (for supervised learning) |
| **Learning Rate** | How big steps to take during optimization |
| **Loss Function** | Measures how wrong predictions are |
| **Model Registry** | Centralized storage for versioned models |
| **Overfitting** | Model memorizes training data, fails on new data |
| **Pipeline** | Sequence of automated ML steps |
| **Precision** | Accuracy of positive predictions |
| **Recall** | Ability to find all positive cases |
| **Regularization** | Techniques to prevent overfitting |
| **Serving** | Making model available for predictions |
| **Tensor** | Multi-dimensional array (generalized matrix) |
| **Training** | Teaching a model from data |
| **Underfitting** | Model too simple to capture patterns |
| **Validation Set** | Data used to tune model during development |
| **Variance** | Error from sensitivity to training data (overfitting) |
| **Weight** | Learnable parameter in a neural network |

---

## 9. Quick Reference Cheat Sheet

### Decision Trees

**Choosing a Model Type:**
```
Have labeled data? ──Yes──→ Supervised Learning
       │                      │
       No                     ├── Predicting category? → Classification
       ↓                      └── Predicting number? → Regression
Have unlabeled data? ──Yes──→ Unsupervised
       │                      │
       No                     └── Find groups? → Clustering
       ↓
Making sequential decisions? → Reinforcement Learning
```

**Choosing a Deployment Strategy:**
```
Need real-time response? ──Yes──→ Real-time Serving
       │
       No
       ↓
Process on schedule? ──Yes──→ Batch Processing
       │
       No
       ↓
Need offline/low latency? ──Yes──→ Edge Deployment
```

### Common Commands

```bash
# MLflow tracking
mlflow ui --port 5000

# Serve model with MLflow
mlflow models serve -m "models:/my_model/Production" -p 5001

# DVC data versioning
dvc add data/dataset.csv
dvc push

# Docker build for ML
docker build -t my-model:latest .
docker run -p 8080:8080 my-model:latest
```

### Key Metrics Benchmarks

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Inference Latency (p99) | < 50ms | < 200ms | > 500ms |
| Model Accuracy Drop | < 1% | < 5% | > 10% |
| Data Drift Score | < 0.1 | < 0.3 | > 0.5 |
| Pipeline Success Rate | > 99% | > 95% | < 90% |
| Model Training Time | < 1hr | < 6hr | > 24hr |

---

## Appendix: Learning Resources

### For Quick Learning
- **Fast.ai** - Practical deep learning for coders
- **Google ML Crash Course** - Free, comprehensive basics
- **Kaggle Learn** - Hands-on micro-courses

### For MLOps Specifically
- **Made With ML** - MLOps focused tutorials
- **Full Stack Deep Learning** - Production ML course
- **MLOps.community** - Community resources and talks

### Documentation to Bookmark
- MLflow Documentation
- Kubernetes for ML
- AWS SageMaker / Azure ML / Vertex AI docs

---

*Last Updated: 2024*
*Version: 1.0*
*Purpose: Bridge ML knowledge gaps for AI Agent MLOps development*
