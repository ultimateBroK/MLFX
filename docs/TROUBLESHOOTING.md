# ML_FX - Khắc phục sự cố

Tài liệu này gom các lỗi thường gặp khi cài môi trường hoặc chạy pipeline.

## 1. `pixi: command not found`

Nguyên nhân thường gặp:
- chưa cài Pixi
- đã cài nhưng terminal chưa được mở lại

Cách xử lý:
1. cài Pixi theo `USAGE_GUIDE.md`
2. đóng terminal hoặc IDE rồi mở lại
3. chạy lại:

```bash
pixi install
```

## 2. Thiếu package

Ví dụ:

```text
ModuleNotFoundError: No module named 'xgboost'
```

Nguyên nhân:
- môi trường chưa được đồng bộ đủ dependency

Cách xử lý:

```bash
pixi install
```

## 3. Thiếu file ở bước feature, label, hoặc train

Ví dụ:
- không tìm thấy file trong `data/ohlcv/`
- không tìm thấy file trong `data/features/`
- không tìm thấy file trong `data/labels/`

Nguyên nhân:
- chạy sai thứ tự pipeline

Thứ tự đúng:

```text
download -> qa -> resample -> features -> labels -> train -> backtest
```

Nếu train lỗi, hãy kiểm tra lần lượt:
- `data/raw/{symbol}/`
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

## 4. Hết RAM hoặc process bị kill

Nguyên nhân:
- đang đọc quá nhiều dữ liệu tick cùng lúc

Cách xử lý:
- bắt đầu với timeframe lớn hơn như `1H`
- xử lý từng symbol một
- nếu cần tự viết thêm script phân tích, ưu tiên `scan_parquet()` thay vì `read_parquet()` cho dữ liệu lớn

## 5. Download bị dừng giữa chừng

`pipeline/download_data.py` có cơ chế resume dựa trên `completed_months.json`.

Thường chỉ cần chạy lại:

```bash
pixi run python pipeline/download_data.py --symbol XAUUSD --asset-class fx
```

Nếu muốn ép kiểm tra lại các tháng đã hoàn tất:

```bash
pixi run python pipeline/download_data.py --symbol XAUUSD --asset-class fx --force-repair
```

## 6. Muốn làm sạch dữ liệu trung gian

Nếu bạn muốn tạo lại OHLCV, features, hoặc labels từ đầu mà vẫn giữ dữ liệu raw:

```bash
rm -rf data/ohlcv/* data/features/* data/labels/*
```

Sau đó chạy lại:

```bash
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H
```

## 7. Backtest không tạo báo cáo

Kiểm tra:
- file truyền vào `--data` có tồn tại không
- cột truyền vào `--label` có nằm trong parquet không
- thư mục output có quyền ghi không

Lệnh mẫu:

```bash
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --outdir outputs/reports
```
