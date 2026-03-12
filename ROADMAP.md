# MLFX - Trạng thái hiện tại và hướng tiếp theo

Tài liệu này tóm tắt những capability chính hiện có và các hạng mục nên làm tiếp theo.

Chú giải:
- `[x]` Đã sẵn sàng để dùng.
- `[ ]` Là hạng mục nên cân nhắc hoặc triển khai tiếp.

## 1. Năng lực hiện tại

- [x] CLI hợp nhất `mlfx`.
- [x] Downloader dữ liệu trong `mlfx.ingestion`.
- [x] QA, resample, feature engineering, labeling trong `mlfx.pipeline`.
- [x] Train backend trong `mlfx.training`.
- [x] Backtest và reporting trong `mlfx.evaluation`.
- [x] Package runtime đóng gói qua `mlfx`.
- [x] Luồng vận hành và phát triển chuẩn qua Pixi.

## 2. Backend hiện có

- [x] `mlf`.
- [x] `lstm`.
- [x] `bilstm`.
- [x] `transformer`.
- [x] `cnn_lstm`.
- [x] `sgd`.
- [x] `stats`.
- [x] `neuralforecast`.

## 3. Hướng ưu tiên hợp lý tiếp theo

- [x] Expose `bilstm` trong CLI (đã có qua `--backend bilstm`).
- [x] Bổ sung benchmark thống nhất để so sánh backend trên cùng dataset (đã có `mlfx benchmark`).
- [x] Mở rộng test end-to-end cho train và evaluate trên fixture dataset nhỏ (đã có `test_training_e2e.py`).
- [x] Thêm xuất metrics phục vụ monitoring vào luồng vận hành (đã có `metrics_log.jsonl`).

## 4. Gợi ý khi chọn việc tiếp theo

- Nếu mục tiêu là so sánh mô hình: dùng `mlfx benchmark --backends mlf bilstm lstm`; cân nhắc chuẩn hóa metrics cross-backend.
- Nếu mục tiêu là ổn định vận hành: mở rộng test coverage, thêm fixture dataset nhỏ hơn.
- Nếu mục tiêu là mở rộng thử nghiệm: thêm backend mới (e.g., attention-based), thêm live data adapter.
- Nếu mục tiêu là production: refactor serving layer, thêm retry logic và circuit breaker.
