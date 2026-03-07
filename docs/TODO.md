# ML_FX - Trạng thái và việc còn lại

Tài liệu này tóm tắt trạng thái hiện tại của repo dựa trên code đang có, không phải theo các bản kế hoạch cũ.

Chú giải:
- `[x]` đã có trong repo
- `[/]` đang làm dở hoặc đã có khung nhưng chưa hoàn chỉnh
- `[ ]` chưa triển khai

## 1. Thu thập và kiểm tra dữ liệu

- [x] [pipeline/download_data.py](../pipeline/download_data.py)
  - [x] tải dữ liệu tick từ Dukascopy
  - [x] hỗ trợ `fx` và `crypto`
  - [x] lưu state trong `completed_months.json`
  - [x] có cơ chế resume và repair
- [x] [pipeline/qa_data.py](../pipeline/qa_data.py)
  - [x] kiểm tra gap dữ liệu
  - [x] rà lỗi giá trị bất thường
  - [x] xuất báo cáo QA dạng Markdown

## 2. Pipeline dữ liệu

- [x] [pipeline/resample.py](../pipeline/resample.py)
  - [x] chuyển tick sang OHLCV
  - [x] hỗ trợ `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- [x] [pipeline/features.py](../pipeline/features.py)
  - [x] feature từ `ICT Killzone`
  - [x] feature từ `Support/Resistance`
  - [x] feature từ `Pivot Points`
  - [x] feature TA phổ biến
- [x] [pipeline/labels.py](../pipeline/labels.py)
  - [x] sinh `label_5`, `label_10`, `label_20`
  - [x] dùng ATR multiplier để giảm nhiễu

## 3. Backend huấn luyện hiện có

- [x] [models/ml_models.py](../models/ml_models.py)
- [x] [models/lstm.py](../models/lstm.py)
- [x] [models/transformer.py](../models/transformer.py)
- [x] [models/cnn_lstm.py](../models/cnn_lstm.py)
- [x] [models/online_sgd.py](../models/online_sgd.py)
- [x] [models/stats_baseline.py](../models/stats_baseline.py)
- [x] [models/neural_forecast.py](../models/neural_forecast.py)
- [x] [models/bilstm.py](../models/bilstm.py)

Ghi chú:
- TUI hiện expose các backend: `mlf`, `lstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`
- [models/bilstm.py](../models/bilstm.py) có trong repo nhưng hiện chưa nằm trong danh sách backend của TUI

## 4. Đánh giá và báo cáo

- [x] [eval/backtest.py](../eval/backtest.py)
- [x] [eval/run_eval.py](../eval/run_eval.py)
- [x] [viz/charts.py](../viz/charts.py)
  - [x] candlestick HTML
  - [x] equity curve PNG
  - [x] heatmap PNG

Đầu ra mặc định:
- `outputs/models/`
- `outputs/reports/`

## 5. Giao diện vận hành

- [x] [main.py](../main.py)
  - [x] tab `Download Data`
  - [x] tab `Pipeline`
  - [x] tab `Train Model`
  - [x] tab `Backtest`
- [x] [config.toml](../config.toml)
  - [x] điền sẵn giá trị mặc định cho TUI

## 6. Agent

- `agent/` hiện là khu vực dành cho giai đoạn sau
- [pyproject.toml](../pyproject.toml) vẫn đóng gói package `agent`
- trạng thái thực tế hiện tại là:
  - [/] thư mục đã tồn tại
  - [ ] chưa có implementation vận hành hoàn chỉnh để dùng như tính năng chính

## 7. Việc còn lại hợp lý

- [ ] đồng bộ `config.toml` comments với backend thật đang dùng trong TUI
- [ ] quyết định có đưa `bilstm.py` vào TUI hay không
- [ ] xác định rõ chiến lược đánh giá giữa dữ liệu gắn nhãn và dữ liệu dự báo thực
- [ ] nếu tiếp tục làm `agent/`, cần tài liệu hóa rõ trạng thái và phạm vi trước khi mở rộng README
- [ ] bổ sung tài liệu hoặc script benchmark để so sánh các backend trên cùng dataset
