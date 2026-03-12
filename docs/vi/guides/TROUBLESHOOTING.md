# MLFX - Khắc phục sự cố

Tài liệu này gom các lỗi thường gặp khi cài môi trường hoặc chạy workflow `mlfx`.

## 1. Checklist chẩn đoán nhanh

Khi một bước thất bại, hãy kiểm tra theo thứ tự:
1. `pixi install` đã chạy chưa
2. Đang chạy lệnh bằng `pixi run` hay không
3. Dữ liệu đầu vào của bước hiện tại có tồn tại không
4. Output của bước trước có sinh ra đúng thư mục không
5. Workspace có đang bị nhiễu bởi cache hoặc artifact cũ không

## 2. `pixi: command not found`

Nguyên nhân thường gặp:
- Chưa cài Pixi
- Đã cài nhưng terminal hoặc IDE chưa được mở lại

Cách xử lý:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

## 3. Thiếu package hoặc import lỗi

Ví dụ:

```text
ModuleNotFoundError: No module named 'xgboost'
```

Cách xử lý:

```bash
pixi install
```

Nếu vẫn lỗi:
- Kiểm tra bạn có chạy bằng `pixi run ...` hay không
- Thử `pixi run python -c "import polars"` để xác nhận environment

## 4. Thiếu file ở bước pipeline hoặc train

Nếu thiếu dữ liệu trong `data/ohlcv/`, `data/features/`, hoặc `data/labels/`, thường là do chạy sai thứ tự.

Thứ tự đúng:

```text
download -> qa -> pipeline -> train -> evaluate
```

Kiểm tra lần lượt:
- `data/raw/{symbol}/`
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

## 5. Download bị dừng giữa chừng

Downloader dùng `completed_months.json` để resume.

Chạy lại:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx
```

Nếu muốn kiểm tra lại toàn bộ:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --force
```

Nếu chất lượng dữ liệu đáng ngờ sau download:

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

## 6. Train báo backend không hợp lệ

CLI hiện hỗ trợ:
- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

Kiểm tra nhanh:

```bash
pixi run mlfx train --help
```

## 7. Hết RAM hoặc process bị kill

Gợi ý:
- Bắt đầu với timeframe lớn hơn như `1H`
- Xử lý từng symbol một
- Giảm scope kiểm thử xuống một khoảng thời gian ngắn hơn
- Với script tự viết, ưu tiên `scan_parquet()` cho dữ liệu lớn

## 8. Muốn dọn cache và output cũ

Dùng task chuẩn:

```bash
pixi run clean-generated
```

Task này dọn các phần có thể tái sinh an toàn như:
- `.cache/`
- `.pixi-cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `lightning_logs/`
- nội dung trong `outputs/models/{symbol}/{tf}/`
- nội dung trong `outputs/reports/{symbol}/{tf}/`

Task này không xóa `data/raw/`.

## 9. Muốn tạo lại dữ liệu trung gian nhưng giữ raw data

Nếu cần rebuild hoàn toàn phần trung gian:

```bash
rm -rf data/ohlcv/* data/features/* data/labels/*
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --pivot traditional --anchor daily --atr-mult 0.5
```

Chỉ dùng khi bạn chắc chắn muốn sinh lại toàn bộ parquet trung gian.

## 10. Backtest không tạo báo cáo

Kiểm tra:
- Thư mục `data/labels/{symbol}/{tf}/` có parquet không
- Cột tín hiệu truyền qua `--label` có tồn tại không
- Cột `atr_14` có tồn tại không
- Thư mục `outputs/reports/{symbol}/{tf}/` có ghi được không

Lệnh mẫu hợp lệ:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Lưu ý:
- CLI hiện không có tham số `--outdir`
- Report mặc định được ghi vào `outputs/reports/{symbol}/{tf}/`

## 11. Cần kiểm tra repo có còn sạch không

Chạy:

```bash
pixi run verify
```

Lệnh này phù hợp khi bạn vừa:
- Đổi cấu hình Pixi
- Chỉnh docs/entrypoints
- Dọn cache/output và muốn chắc workflow chính vẫn ổn

## 12. Drift liên tục báo cảnh báo nhưng không muốn thay đổi model

Nếu drift normally xuất hiện ở mức thấp và không đủ nguy hiểm, có thể nới lỏng ngưỡng:

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.2 --threshold-psi 0.3
```

Ngưỡng mặc định: `--threshold-ks 0.1` và `--threshold-psi 0.2`.

## 13. Muốn chạy nhiều timeframe cùng lúc

Lệnh `pipeline` hỗ trợ nhiều `--tf` trong một lần chạy:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

Các timeframe được xử lý lần lượt trong cùng một lời gọi.

## 14. Benchmark lưu báo cáo ở đâu

Sau khi chạy `benchmark`, kết quả JSON được lưu tự động vào:

```text
outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json
```

Ví dụ: `outputs/reports/XAUUSD/1H/benchmark_20260101_120000.json`
