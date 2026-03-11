# MLFX - Trạng thái hiện tại và hướng tiếp theo

Tài liệu này tóm tắt những capability chính hiện có và các hạng mục nên làm tiếp theo.

Chú giải:
- `[x]` đã sẵn sàng để dùng
- `[ ]` là hạng mục nên cân nhắc hoặc triển khai tiếp

## 1. Năng lực hiện tại

- [x] CLI hợp nhất `mlfx`
- [x] downloader dữ liệu trong `mlfx.ingestion`
- [x] QA, resample, feature engineering, labeling trong `mlfx.pipeline`
- [x] train backend trong `mlfx.training`
- [x] backtest và reporting trong `mlfx.evaluation`
- [x] package runtime đóng gói qua `mlfx`
- [x] workflow phát triển và vận hành chuẩn qua Pixi

## 2. Backend hiện có

- [x] `mlf`
- [x] `lstm`
- [x] `bilstm`
- [x] `transformer`
- [x] `cnn_lstm`
- [x] `sgd`
- [x] `stats`
- [x] `neuralforecast`

## 3. Hướng ưu tiên hợp lý tiếp theo

- [x] expose `bilstm` trong CLI (đã có qua `--backend bilstm`)
- [x] bổ sung benchmark thống nhất để so sánh backend trên cùng dataset (đã có `mlfx benchmark`)
- [x] mở rộng test end-to-end cho train và evaluate trên fixture dataset nhỏ (đã có `test_training_e2e.py`)
- [x] thêm workflow export metrics phục vụ monitoring (đã có `metrics_log.jsonl`)

## 4. Gợi ý khi chọn việc tiếp theo

- nếu mục tiêu là so sánh mô hình: dùng `mlfx benchmark --backends mlf bilstm lstm`; cân nhắc chuẩn hóa metrics cross-backend
- nếu mục tiêu là ổn định vận hành: mở rộng test coverage, thêm fixture dataset nhỏ hơn
- nếu mục tiêu là mở rộng thử nghiệm: thêm backend mới (e.g., attention-based), thêm live data adapter
- nếu mục tiêu là production: refactor serving layer, thêm retry logic và circuit breaker
