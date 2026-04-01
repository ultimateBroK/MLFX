# Kiến Thức Cơ Bản ML cho MLOps: Hướng Dẫn Thực Tế
## Lấp Đầy Khoảng Trống Kiến Thức cho Phát Triển AI Agent

---

## Mục Lục
1. [Khái Niệm Cốt Lõi về ML](#1-khái-niệm-cốt-lõi-về-ml)
2. [Cơ Bản về Data Pipeline](#2-cơ-bản-về-data-pipeline)
3. [Vòng Đời Phát Triển Model](#3-vòng-đời-phát-triển-model)
4. [Chiến Lược Triển Khai Model](#4-chiến-lược-triển-khai-model)
5. [Giám Sát & Bảo Trì](#5-giám-sát--bảo-trì)
6. [Khái Niệm ML dành riêng cho AI Agent](#6-khái-niệm-ml-dành-riêng-cho-ai-agent)
7. [Best Practices cho MLOps](#7-best-practices-cho-mlops)
8. [Bảng Thuật Ngữ Quan Trọng](#8-bảng-thuật-ngữ-quan-trọng)
9. [Bảng Tham Khảo Nhanh](#9-bảng-tham-khảo-nhanh)

---

## 1. Khái Niệm Cốt Lõi về ML

### 1.1 Các Loại Học Máy (Machine Learning)

| Loại | Mô Tả | Khi Nào Sử Dụng | Ví Dụ |
|------|-------|-----------------|-------|
| **Supervised Learning (Học có giám sát)** | Học từ dữ liệu đã gán nhãn | Khi có cặp input-output | Phát hiện spam, dự đoán giá |
| **Unsupervised Learning (Học không giám sát)** | Tìm pattern trong dữ liệu không nhãn | Khi muốn khám phá cấu trúc ẩn | Phân khúc khách hàng, phát hiện bất thường |
| **Reinforcement Learning (Học tăng cường)** | Học qua thử và sai | Khi quyết định ảnh hưởng kết quả tương lai | AI chơi game, điều khiển robot, hành vi agent |
| **Self-Supervised Learning (Học tự giám sát)** | Tự tạo nhãn từ dữ liệu | Khi có nhiều dữ liệu không nhãn | Mô hình ngôn ngữ, nhận dạng ảnh |

### 1.2 Các Loại Model Phổ Biến (Giải thích đơn giản)

#### Classification Models (Mô hình phân loại)
```
Mục đích: Phân loại vật vào các danh mục
Đầu vào: Các đặc điểm của vật
Đầu ra: Nhãn danh mục

Ví dụ: Email này có phải spam không?
- Đầu vào: Nội dung email, người gửi, tiêu đề
- Đầu ra: "Spam" hoặc "Không Spam"
```

#### Regression Models (Mô hình hồi quy)
```
Mục đích: Dự đoán một con số
Đầu vào: Các đặc điểm của tình huống
Đầu ra: Một giá trị liên tục

Ví dụ: Giá nhà sẽ là bao nhiêu?
- Đầu vào: Diện tích, vị trí, số phòng ngủ
- Đầu ra: 4.5 tỷ VNĐ
```

#### Clustering Models (Mô hình phân cụm)
```
Mục đích: Gom nhóm các vật tương tự
Đầu vào: Các đặc điểm của vật
Đầu ra: Phân bổ nhóm

Ví dụ: Phân khúc khách hàng
- Đầu vào: Lịch sử mua hàng, nhân khẩu học
- Đầu ra: "Khách bình dân", "Khách cao cấp", v.v.
```

#### Sequence Models (Mô hình chuỗi)
```
Mục đích: Hiểu dữ liệu có thứ tự (văn bản, chuỗi thời gian)
Đầu vào: Một chuỗi giá trị
Đầu ra: Giá trị tiếp theo hoặc phân loại

Ví dụ: Dự đoán từ tiếp theo trong câu
- Đầu vào: "Con mèo nhanh nhẹn..."
- Đầu ra: "chạy"
```

### 1.3 Tham Khảo Nhanh Các Thuật Toán Quan Trọng

| Thuật Toán | Tốt Nhất Cho | Độ Phức Tạp | Lưu Ý Khi Production |
|-----------|--------------|-------------|---------------------|
| **Linear/Logistic Regression** | Quan hệ đơn giản | Thấp | Inference nhanh, dễ giải thích |
| **Decision Trees** | Quyết định dựa trên quy tắc | Thấp | Dễ giải thích, dễ overfit |
| **Random Forest** | Pattern phức tạp | Trung bình | Mạnh mẽ, xử lý được missing data |
| **Gradient Boosting (XGBoost, LightGBM)** | Dữ liệu bảng trong competition | Trung bình | Thường thắng Kaggle, cần tuning |
| **Neural Networks** | Ảnh, văn bản, pattern phức tạp | Cao | Cần nhiều data, GPU |
| **Transformers** | Ngôn ngữ, chuỗi | Rất Cao | State-of-art cho NLP, tốn kém |

### 1.4 Training vs. Inference (Huấn luyện vs. Suy luận)

```
┌─────────────────────────────────────────────────────────┐
│                    GIAI ĐOẠN TRAINING                    │
│  Dữ liệu → Model Học → Model Đã Được Train               │
│  (Xảy ra offline, tốn nhiều tài nguyên)                  │
└─────────────────────────────────────────────────────────┘
                          ↓
                    Lưu Model
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   GIAI ĐOẠN INFERENCE                    │
│  Input Mới → Model Đã Train → Dự Đoán                    │
│  (Xảy ra online, cần phải nhanh)                         │
└─────────────────────────────────────────────────────────┘
```

**Điểm then chốt:** Training giống như ôn thi. Inference giống như đi thi. Bạn train một lần (hoặc định kỳ), nhưng inference xảy ra liên tục trong production.

---

## 2. Cơ Bản về Data Pipeline

### 2.1 Hành Trình Của Dữ Liệu

```
Dữ Liệu Gốc (Raw Data)
    ↓ [Thu thập - Collection]
    ↓ [Kiểm tra - Validation]
    ↓ [Làm sạch - Cleaning]
    ↓ [Biến đổi - Transformation]
    ↓ [Feature Engineering]
    ↓ [Chia nhỏ - Splitting]
Sẵn Sàng Training
```

### 2.2 Chiến Lược Chia Dữ Liệu

```
┌──────────────────────────────────────────────────────┐
│                    DỮ LIỆU CỦA BẠN                    │
├──────────────┬──────────────┬────────────────────────┤
│    TRAIN     │  VALIDATION  │        TEST            │
│    70-80%    │    10-15%    │       10-15%           │
│              │              │                        │
│ Dùng để      │ Dùng để      │ Chỉ dùng MỘT lần       │
│ dạy model    │ điều chỉnh    │ để đánh giá            │
│              │ tham số       │ hiệu suất cuối cùng    │
└──────────────┴──────────────┴────────────────────────┘
```

**Quy tắc quan trọng:** KHÔNG BAO GIỜ để model nhìn thấy test data trong lúc training. Giống như đưa đề thi cho học sinh trước khi thi.

### 2.3 Feature Engineering Cơ Bản

| Kỹ Thuật | Mô Tả | Khi Nào Sử Dụng |
|----------|-------|-----------------|
| **Normalization** | Chuyển giá trị về khoảng 0-1 | Khi features có scales khác nhau |
| **One-Hot Encoding** | Chuyển categories thành số | Cho biến phân loại |
| **Embedding** | Biểu diễn dày đặc của categories | Khi có nhiều categories |
| **Feature Crossing** | Kết hợp features | Khi tương tác giữa features quan trọng |
| **Binning** | Chuyển liên tục thành rời rạc | Để giảm nhiễu |

### 2.4 Feature Stores (Thiết yếu cho MLOps)

```
┌─────────────────────────────────────────────────────────┐
│                   FEATURE STORE                          │
├─────────────────────────────────────────────────────────┤
│  Mục đích: Quản lý feature tập trung                     │
│                                                          │
│  Lợi ích:                                               │
│  • Tái sử dụng features qua nhiều models                 │
│  • Tính toán feature nhất quán                           │
│  • Đúng thời điểm trong quá khứ                          │
│  • Serve features theo thời gian thực                    │
│                                                          │
│  Công cụ phổ biến: Feast, Tecton, AWS Feature Store      │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Vòng Đời Phát Triển Model

### 3.1 Vòng Lặp Phát Triển ML

```
         ┌──────────────────┐
         │ Định Nghĩa Vấn Đề│
         └────────┬─────────┘
                  ↓
         ┌──────────────────┐
         │   Thu Thập Data  │
         └────────┬─────────┘
                  ↓
         ┌──────────────────┐
         │   Chuẩn Bị Data  │
         └────────┬─────────┘
                  ↓
    ┌─────────────────────────┐
    │                         │
    ↓                         │
┌───────────┐                 │
│   Train   │                 │
│   Model   │←────────────────┤
└─────┬─────┘                 │
      ↓                       │
┌───────────┐                 │
│  Đánh Giá │──Chưa Tốt───────┘
│   Model   │
└─────┬─────┘
      │ Đủ Tốt
      ↓
┌───────────┐
│  Triển Khai│
└───────────┘
```

### 3.2 Experiment Tracking Thiết Yếu

**Tại sao cần theo dõi experiment?**
- Tái tạo kết quả
- So sánh các cách tiếp cận
- Debug khi thất bại
- Tuân thủ quy định

**Những gì cần theo dõi:**
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

**Công cụ:** MLflow, Weights & Biases, Neptune, ClearML

### 3.3 Hyperparameter Tuning (Điều chỉnh siêu tham số)

```
Hyperparameters = Cài đặt BẠN chọn trước khi training
Parameters = Giá trị MODEL học trong lúc training

Ví dụ Hyperparameters:
- Learning rate: Model học nhanh như thế nào
- Batch size: Bao nhiêu examples xử lý cùng lúc
- Number of layers: Độ sâu của neural network
- Regularization: Bao nhiêu để ngăn overfitting
```

**Chiến lược Tuning:**
| Chiến Lược | Khi Nào Sử Dụng | Pros/Cons |
|----------|-----------------|-----------|
| Grid Search | Ít parameters | Kỹ lưỡng nhưng chậm |
| Random Search | Nhiều parameters | Thường tốt hơn grid |
| Bayesian Optimization | Training tốn kém | Hiệu quả, tìm kiếm thông minh |
| Hyperband | Ngân sách compute lớn | Early stopping các runs tồi |

### 3.4 Các Metric Đánh Giá Model

**Classification Metrics:**
```
Accuracy  = (Dự đoán đúng) / (Tổng dự đoán)
Precision = (True Positives) / (Predicted Positives)  -- "Trong các positive dự đoán, bao nhiêu đúng?"
Recall    = (True Positives) / (Actual Positives)     -- "Trong các positive thực tế, tìm được bao nhiêu?"
F1 Score  = 2 × (Precision × Recall) / (Precision + Recall)  -- Cân bằng cả hai
```

**Regression Metrics:**
```
MAE  = Mean Absolute Error         -- Sai số tuyệt đối trung bình
MSE  = Mean Squared Error          -- Phạt lỗi lớn hơn
RMSE = Root Mean Squared Error     -- Cùng đơn vị với target
R²   = Hệ số xác định -- Giải thích được bao nhiêu variance
```

---

## 4. Chiến Lược Triển Khai Model

### 4.1 Các Pattern Triển Khai

```
┌─────────────────────────────────────────────────────────────┐
│                    BATCH INFERENCE                          │
│  • Xử lý dữ liệu theo batch lớn                             │
│  • Chạy theo lịch (hàng giờ, hàng ngày)                     │
│  • Ví dụ: Cập nhật gợi ý hàng đêm                          │
│  • Công cụ: Spark, AWS Batch, SageMaker Batch Transform     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  REAL-TIME INFERENCE                        │
│  • Xử lý request riêng lẻ ngay lập tức                      │
│  • Cần độ trễ thấp (thường < 100ms)                         │
│  • Ví dụ: Phát hiện gian lận giao dịch                      │
│  • Công cụ: FastAPI, TensorFlow Serving, TorchServe         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    EDGE INFERENCE                           │
│  • Chạy trên thiết bị (điện thoại, IoT, edge server)        │
│  • Không phụ thuộc mạng                                     │
│  • Ví dụ: Nhận dạng khuôn mặt trên điện thoại               │
│  • Công cụ: TensorFlow Lite, ONNX Runtime, Core ML          │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Kiến Trúc Model Serving

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

### 4.3 So Sánh Chiến Lược Triển Khai

| Chiến Lược | Mô Tả | Rủi Ro | Rollback |
|----------|-------------|------|----------|
| **Blue-Green** | Hai môi trường giống hệt, chuyển traffic | Thấp | Ngay lập tức |
| **Canary** | Điều hướng % nhỏ traffic đến model mới | Thấp | Nhanh |
| **A/B Testing** | So sánh models trên nhóm user khác nhau | Trung bình | Trung bình |
| **Shadow Mode** | Model mới chạy song song, không serve | Rất Thấp | N/A |
| **Rolling Update** | Thay thế dần dần các instances | Trung bình | Trung bình |

### 4.4 Best Practices cho Model Registry

```yaml
# Ví dụ Model Registry Entry
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

## 5. Giám Sát & Bảo Trì

### 5.1 Những Gì Cần Giám Sát

```
┌─────────────────────────────────────────────────────────────┐
│                  ML MONITORING STACK                        │
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
│     • Prediction accuracy theo thời gian                    │
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

### 5.2 Phát Hiện Drift (Trôi dạt)

**Data Drift:** Dữ liệu đầu vào thay đổi theo thời gian
```
Training data: 30% premium users
Current data:  60% premium users
→ Model có thể hoạt động kém hơn
```

**Concept Drift:** Mối quan hệ giữa input và output thay đổi
```
Trước: Price = f(size, location)
Sau:  Price = f(size, location, interest_rates)  // Yếu tố mới quan trọng
→ Model cần retraining
```

**Phương pháp phát hiện:**

| Phương Pháp | Cách Hoạt Động | Công Cụ |
|--------|--------------|-------|
| Statistical tests | So sánh distributions (KS, Chi-squared) | Evidently, WhyLabs |
| Distance metrics | Đo khoảng cách giữa distributions | Custom + MLflow |
| Performance tracking | Giám sát prediction accuracy | Prometheus + Grafana |
| PCA-based | Phát hiện thay đổi trong feature space | Scikit-learn |

### 5.3 Các Trigger cho Retraining

```python
# Logic Quyết Định Retraining
def should_retrain(model_metrics, data_metrics, schedule):
    triggers = []

    # Dựa trên hiệu suất
    if model_metrics.accuracy < THRESHOLD:
        triggers.append("accuracy_drop")

    # Dựa trên data drift
    if data_metrics.drift_score > DRIFT_THRESHOLD:
        triggers.append("significant_drift")

    # Dựa trên thời gian
    if schedule.days_since_last_train > RETRAIN_INTERVAL:
        triggers.append("scheduled")

    # Dựa trên khối lượng dữ liệu
    if data_metrics.new_samples > MIN_NEW_SAMPLES:
        triggers.append("new_data_available")

    return len(triggers) > 0, triggers
```

### 5.4 Retraining Pipeline

```
┌─────────────────┐
│ Phát Hiện Trigger│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Thu Thập Data Mới│
└────────┬────────┘
         ↓
┌─────────────────┐
│  Validate Data  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Train Model Mới │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Đánh Giá Model │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
  Tốt Hơn   Tệ Hơn
    │         │
    ↓         ↓
┌───────┐ ┌───────────┐
│Deploy │ │Giữ Model  │
│Model  │ │Cũ & Điều  │
│Mới    │ │Tra        │
└───────┘ └───────────┘
```

---

## 6. Khái Niệm ML dành riêng cho AI Agent

### 6.1 Reinforcement Learning cho Agents

```
┌─────────────────────────────────────────────────────────────┐
│              REINFORCEMENT LEARNING CƠ BẢN                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ┌──────────┐      Action       ┌──────────┐            │
│     │  AGENT   │ ─────────────────→│ENVIRONMENT│            │
│     └────┬─────┘                   └─────┬────┘            │
│          │                               │                  │
│          │←──────────────────────────────│                  │
│          │        State + Reward         │                  │
│                                                             │
│  Khái niệm chính:                                           │
│  • State: Tình huống/quan sát hiện tại                      │
│  • Action: Những gì agent có thể làm                        │
│  • Reward: Tín hiệu phản hồi (tốt/xấu)                      │
│  • Policy: Chiến lược chọn actions                          │
│  • Value: Phần thưởng kỳ vọng dài hạn                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Các thuật toán RL phổ biến cho AI Agents:**

| Thuật Toán | Loại | Tốt Nhất Cho |
|-----------|------|----------|
| Q-Learning | Value-based | Actions đơn giản, rời rạc |
| DQN | Deep RL | States phức tạp (ảnh, văn bản) |
| PPO | Policy gradient | Mục đích chung, ổn định |
| A3C | Actor-Critic | Training song song |
| SAC | Off-policy | Actions liên tục |

### 6.2 Multi-Agent Systems (Hệ thống đa agent)

```
┌─────────────────────────────────────────────────────────────┐
│              KIẾN TRÚC MULTI-AGENT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Patterns:                                                  │
│                                                             │
│  1. HIERARCHICAL (Phân cấp)                                │
│     ┌──────────┐                                            │
│     │ Manager  │                                            │
│     └────┬─────┘                                            │
│      ┌───┼───┐                                              │
│      ↓   ↓   ↓                                              │
│    ┌───┐┌───┐┌───┐                                         │
│    │W1││W2││W3│  Agent workers                             │
│    └───┘└───┘└───┘                                         │
│                                                             │
│  2. COOPERATIVE (Hợp tác)                                  │
│    ┌───┐ ←──→ ┌───┐ ←──→ ┌───┐                             │
│    │A1 │ ←──→ │A2 │ ←──→ │A3 │  Mục tiêu chung             │
│    └───┘     └───┘     └───┘                               │
│                                                             │
│  3. COMPETITIVE (Cạnh tranh)                               │
│    ┌───┐                   ┌───┐                            │
│    │A1 │ ←─── đối đầu ────→│A2 │                            │
│    └───┘                   └───┘                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Tool Use & Function Calling (Sử dụng công cụ)

```python
# Định nghĩa Tool mang tính khái niệm
tools = {
    "search_web": {
        "description": "Tìm kiếm thông tin trên internet",
        "parameters": {
            "query": {"type": "string", "description": "Truy vấn tìm kiếm"},
            "limit": {"type": "integer", "default": 10}
        }
    },
    "execute_code": {
        "description": "Chạy code Python",
        "parameters": {
            "code": {"type": "string"},
            "timeout": {"type": "integer", "default": 30}
        }
    }
}

# Quy trình quyết định của Agent
def agent_act(observation, tools):
    # 1. Hiểu task
    task = parse_task(observation)

    # 2. Quyết định có cần tools không
    if needs_tools(task):
        # 3. Chọn tool phù hợp
        tool = select_tool(task, tools)
        # 4. Sinh parameters
        params = generate_params(task, tool)
        # 5. Thực thi và quan sát kết quả
        result = execute_tool(tool, params)

    # 6. Sinh phản hồi
    return generate_response(task, result)
```

### 6.4 Agent Memory Systems (Hệ thống bộ nhớ agent)

```
┌─────────────────────────────────────────────────────────────┐
│                  CÁC LOẠI BỘ NHỚ AGENT                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SHORT-TERM MEMORY (Context Window)                         │
│  ├── Cuộc hội thoại hiện tại                                │
│  ├── Các actions gần đây                                    │
│  └── Tính toán tạm thời                                     │
│      Kích thước: Giới hạn (e.g., 4K-128K tokens)            │
│                                                             │
│  LONG-TERM MEMORY (Persistent Storage)                      │
│  ├── Vector Database (semantic search)                      │
│  │   Công cụ: Pinecone, Weaviate, Chroma                    │
│  ├── Knowledge Graph (quan hệ có cấu trúc)                  │
│  │   Công cụ: Neo4j, NetworkX                               │
│  └── Document Store (facts, documents)                      │
│      Công cụ: MongoDB, Elasticsearch                        │
│                                                             │
│  EPISODIC MEMORY (Trải nghiệm quá khứ)                      │
│  └── Actions thành công/thất bại và kết quả                 │
│      Mục đích: Học từ sai lầm, cải thiện quyết định         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 Planning & Reasoning Patterns (Pattern lập kế hoạch và suy luận)

```
┌─────────────────────────────────────────────────────────────┐
│                  CÁC PATTERN AGENT PHỔ BIẾN                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. REACT (Reason + Act)                                    │
│     Thought → Action → Observation → Thought → ...          │
│                                                             │
│  2. CHAIN-OF-THOUGHT (CoT)                                  │
│     Bước 1 → Bước 2 → Bước 3 → Câu trả lời                  │
│                                                             │
│  3. TREE-OF-THOUGHT (ToT)                                   │
│          ┌─── Option A ───┐                                 │
│     Problem ─┼─── Option B ─┼── Tốt nhất ─→ Solution        │
│          └─── Option C ───┘                                 │
│                                                             │
│  4. REFLEXION                                               │
│     Thử → Phản biện → Cải thiện → Thử lại                  │
│                                                             │
│  5. PLANNING-BASED                                          │
│     Mục tiêu → Phân rã → Lập kế hoạch → Thực thi → Kiểm tra│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Best Practices cho MLOps

### 7.1 Mô Hình Trưởng Thành MLOps

```
Level 0: Quy trình thủ công
├── Training ad-hoc
├── Deploy thủ công
└── Không monitoring

Level 1: Tự động ML Pipeline
├── Tự động training pipeline
├── Deploy thủ công
└── Monitoring cơ bản

Level 2: Tự động CI/CD Pipeline
├── Tự động training
├── Tự động testing
├── Tự động deployment
└── Monitoring toàn diện

Level 3: MLOps hoàn toàn tự động
├── Tự động retraining
├── A/B testing
├── Phát hiện drift
├── Pipeline tự chữa lành
└── Governance đầy đủ
```

### 7.2 Version Mọi Thứ

```
Checklist Version Control:
├── Code (Git)
├── Data (DVC, lakeFS)
├── Models (MLflow Model Registry)
├── Configurations (Git + YAML)
├── Experiments (MLflow/W&B)
├── Infrastructure (Terraform)
└── Documentation (Git)
```

### 7.3 Chiến Lược Testing cho ML

```
┌─────────────────────────────────────────────────────────────┐
│                    ML TESTING PYRAMID                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────┐                              │
│                    │  E2E    │  Integration full pipeline   │
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

### 7.4 Chiến Lược Tối Ưu Chi Phí

| Chiến Lược | Mô Tả | Tiết Kiệm |
|----------|-------------|-----------|
| Spot/Preemptible VMs | Sử dụng instances có thể ngắt rẻ hơn | 60-90% |
| Auto-scaling | Scale về 0 khi không sử dụng | 40-70% |
| Model Compression | Quantization, pruning, distillation | 50-80% inference |
| Batch Processing | Batch inference vs real-time | 30-50% |
| Right-sizing | Khớp instance với workload | 20-40% |
| Caching | Cache predictions cho inputs phổ biến | 10-30% |

### 7.5 Checklist Bảo Mật

```
ML Security Checklist:
├── Bảo Mật Dữ Liệu
│   ├── Mã hóa khi nghỉ và khi truyền
│   ├── Kiểm soát truy cập (RBAC)
│   └── Ẩn danh/anonymization dữ liệu
│
├── Bảo Mật Model
│   ├── Ký và xác minh model
│   ├── Lưu trữ model an toàn
│   └── Logging truy cập
│
├── Bảo Mật Infrastructure
│   ├── Cô lập mạng (VPC)
│   ├── Quản lý secrets
│   ├── Quét container
│   └── Patch thường xuyên
│
└── Bảo Mật Inference
    ├── Validation input
    ├── Rate limiting
    ├── Lọc output
    └── Audit logging
```

---

## 8. Bảng Thuật Ngữ Quan Trọng

| Thuật Ngữ | Định Nghĩa Đơn Giản |
|------|-------------------------|
| **Artifact** | Bất kỳ file nào được tạo ra trong ML (model, data, logs) |
| **Batch Size** | Số examples xử lý cùng lúc trong training |
| **Bias** | Lỗi từ giả định sai (underfitting) hoặc sự thiếu công bằng |
| **Checkpoint** | Trạng thái model đã lưu trong training |
| **Class Imbalance** | Khi một số classes có nhiều examples hơn các classes khác |
| **Confusion Matrix** | Bảng hiển thị counts dự đoán vs thực tế |
| **Data Lineage** | Lịch sử dữ liệu đến từ đâu và thay đổi như thế nào |
| **Epoch** | Một lần đi qua toàn bộ training data |
| **Feature** | Một biến đầu vào dùng để dự đoán |
| **Feature Store** | Kho tập trung cho ML features |
| **Gradient** | Hướng để điều chỉnh weights nhằm giảm lỗi |
| **Ground Truth** | Câu trả lời đúng (từ labeled data) |
| **Hyperparameter** | Cài đặt bạn chọn trước training |
| **Inference** | Sử dụng model đã train để dự đoán |
| **Label** | Output đúng (cho supervised learning) |
| **Learning Rate** | Bước lớn như thế nào trong tối ưu hóa |
| **Loss Function** | Đo lường dự đoán sai như thế nào |
| **Model Registry** | Lưu trữ tập trung cho models đã version |
| **Overfitting** | Model ghi nhớ training data, thất bại trên data mới |
| **Pipeline** | Chuỗi các bước ML tự động |
| **Precision** | Độ chính xác của positive predictions |
| **Recall** | Khả năng tìm tất cả positive cases |
| **Regularization** | Kỹ thuật ngăn overfitting |
| **Serving** | Làm model khả dụng cho predictions |
| **Tensor** | Mảng đa chiều (ma trận tổng quát) |
| **Training** | Dạy model từ dữ liệu |
| **Underfitting** | Model quá đơn giản để nắm bắt patterns |
| **Validation Set** | Dữ liệu dùng để tune model trong development |
| **Variance** | Lỗi từ độ nhạy với training data (overfitting) |
| **Weight** | Tham số có thể học trong neural network |

---

## 9. Bảng Tham Khảo Nhanh

### Cây Quyết Định

**Chọn Loại Model:**
```
Có labeled data? ──Có──→ Supervised Learning
       │                      │
       Không                  ├── Dự đoán category? → Classification
       ↓                      └── Dự đoán number? → Regression
Có unlabeled data? ──Có──→ Unsupervised
       │                      │
       Không                  └── Tìm groups? → Clustering
       ↓
Ra quyết định tuần tự? → Reinforcement Learning
```

**Chọn Chiến Lược Deployment:**
```
Cần real-time response? ──Có──→ Real-time Serving
       │
       Không
       ↓
Xử lý theo lịch? ──Có──→ Batch Processing
       │
       Không
       ↓
Cần offline/low latency? ──Có──→ Edge Deployment
```

### Các Lệnh Phổ Biến

```bash
# MLflow tracking
mlflow ui --port 5000

# Serve model với MLflow
mlflow models serve -m "models:/my_model/Production" -p 5001

# DVC data versioning
dvc add data/dataset.csv
dvc push

# Docker build cho ML
docker build -t my-model:latest .
docker run -p 8080:8080 my-model:latest
```

### Benchmark Các Metric Quan Trọng

| Metric | Tốt | Chấp Nhận Được | Kém |
|--------|------|------------|------|
| Inference Latency (p99) | < 50ms | < 200ms | > 500ms |
| Model Accuracy Drop | < 1% | < 5% | > 10% |
| Data Drift Score | < 0.1 | < 0.3 | > 0.5 |
| Pipeline Success Rate | > 99% | > 95% | < 90% |
| Model Training Time | < 1hr | < 6hr | > 24hr |

---

## Phụ Lục: Tài Nguyên Học Tập

### Để Học Nhanh
- **Fast.ai** - Deep learning thực tế cho coders
- **Google ML Crash Course** - Cơ bản miễn phí, toàn diện
- **Kaggle Learn** - Micro-courses thực hành

### Dành Riêng Cho MLOps
- **Made With ML** - Tutorials tập trung MLOps
- **Full Stack Deep Learning** - Khóa production ML
- **MLOps.community** - Tài nguyên và talks từ cộng đồng

### Tài Liệu Cần Bookmark
- MLflow Documentation
- Kubernetes for ML
- AWS SageMaker / Azure ML / Vertex AI docs

---

*Cập nhật lần cuối: 2024*
*Phiên bản: 1.0*
*Mục đích: Lấp đầy khoảng trống kiến thức ML cho phát triển AI Agent MLOps*
