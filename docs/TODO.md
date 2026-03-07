# ML_FX - Trạng thái hiện tại và hướng tiếp theo

Tài liệu này tóm tắt những capability chính hiện có và các hạng mục nên làm tiếp theo.

Chú giải:
- `[x]` đã sẵn sàng để dùng
- `[ ]` là hạng mục nên cân nhắc hoặc triển khai tiếp

## 1. Năng lực hiện tại

- [x] CLI hợp nhất `mlfx`
- [x] TUI `mlfx-tui`
- [x] downloader dữ liệu trong `mlfx.ingestion`
- [x] QA, resample, feature engineering, labeling trong `mlfx.pipeline`
- [x] train backend trong `mlfx.training`
- [x] backtest và reporting trong `mlfx.evaluation`
- [x] package runtime đóng gói qua `mlfx`
- [x] workflow phát triển và vận hành chuẩn qua Pixi

## 2. Backend hiện có

- [x] `mlf`
- [x] `lstm`
- [x] `transformer`
- [x] `cnn_lstm`
- [x] `sgd`
- [x] `stats`
- [x] `neuralforecast`
- [x] `bilstm` implementation có trong codebase nhưng chưa expose ở CLI/TUI

## 3. Hướng ưu tiên hợp lý tiếp theo

- [ ] quyết định có expose `bilstm` trong CLI/TUI hay không
- [ ] bổ sung benchmark thống nhất để so sánh backend trên cùng dataset
- [ ] mở rộng test end-to-end cho train và evaluate trên fixture dataset nhỏ hơn nữa
- [ ] cân nhắc thêm workflow export metrics hoặc report summary phục vụ monitoring

## 4. Gợi ý khi chọn việc tiếp theo

- nếu mục tiêu là so sánh mô hình: ưu tiên benchmark thống nhất
- nếu mục tiêu là ổn định vận hành: ưu tiên test end-to-end và export summary metrics
- nếu mục tiêu là mở rộng khả năng thử nghiệm: cân nhắc expose `bilstm`
