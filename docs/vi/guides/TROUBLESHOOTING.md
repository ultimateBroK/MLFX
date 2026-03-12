# MLFX - Khắc phục sự cố

Tài liệu này tổng hợp những lỗi thường gặp khi cài môi trường hoặc chạy các bước trong quy trình `mlfx`.

Nếu một bước gặp lỗi, đừng sửa ngẫu nhiên từng phần. Hãy kiểm tra theo đúng thứ tự: môi trường → dữ liệu đầu vào → kết quả của bước trước → vùng nhớ đệm / đầu ra cũ.

---

## 1. Danh sách kiểm tra nhanh

Khi một bước thất bại, hãy kiểm tra lần lượt:

1. Bạn đã chạy `pixi install` chưa
2. Bạn có đang chạy lệnh qua `pixi run` hay không
3. Dữ liệu đầu vào của bước hiện tại có tồn tại không
4. Kết quả của bước trước có được sinh ra đúng thư mục không
5. Không gian làm việc có đang bị nhiễu bởi vùng nhớ đệm hoặc đầu ra cũ không

Đây là cách nhanh nhất để loại trừ các nguyên nhân phổ biến.

---

## 2. `pixi: command not found`

### Nguyên nhân thường gặp

- Bạn chưa cài `Pixi`
- Bạn đã cài nhưng cửa sổ dòng lệnh hoặc IDE chưa được mở lại
- Biến môi trường của shell chưa được nạp lại

### Cách xử lý

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

Nếu vẫn chưa dùng được:

- Đóng và mở lại terminal
- Mở lại IDE
- Kiểm tra xem shell hiện tại đã nạp cấu hình mới chưa

---

## 3. Thiếu gói hoặc lỗi import

Ví dụ lỗi:

```text
ModuleNotFoundError: No module named 'xgboost'
```

### Nguyên nhân thường gặp

- Môi trường chưa được cài đầy đủ
- Bạn đang chạy Python hệ thống thay vì môi trường do dự án quản lý
- Bạn chạy lệnh trực tiếp mà không đi qua `pixi run`

### Cách xử lý

```bash
pixi install
```

Sau đó kiểm tra lại bằng một lệnh nhỏ:

```bash
pixi run python -c "import polars; print('ok')"
```

Nếu lệnh này chạy được, môi trường cơ bản đã ổn.

---

## 4. Thiếu tệp ở bước `pipeline` hoặc `train`

Nếu thiếu dữ liệu trong các thư mục như:

- `data/ohlcv/`
- `data/features/`
- `data/labels/`

thì nguyên nhân phổ biến nhất là **bạn đang chạy sai thứ tự**.

### Thứ tự đúng

```text
download -> qa -> pipeline -> train -> evaluate
```

### Cần kiểm tra gì

Kiểm tra lần lượt các thư mục sau:

- `data/raw/{symbol}/`
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

Nếu một mắt xích chưa có dữ liệu, bước sau thường sẽ lỗi theo.

---

## 5. Tải dữ liệu bị dừng giữa chừng

Bộ tải dữ liệu dùng tệp `completed_months.json` để tiếp tục từ chỗ còn dở.

### Chạy lại bình thường

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx
```

### Muốn tải lại toàn bộ

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --force
```

### Nếu nghi dữ liệu tải về có vấn đề

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

Bước này giúp phát hiện khoảng trống dữ liệu, tháng lỗi hoặc dữ liệu bất thường.

---

## 6. Huấn luyện báo bộ máy không hợp lệ

### Các bộ máy hiện đang hỗ trợ

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Cách kiểm tra nhanh

```bash
pixi run mlfx train --help
```

Nếu tên bộ máy bạn nhập không nằm trong danh sách hỗ trợ, dòng lệnh sẽ không chạy được.

---

## 7. Hết RAM hoặc tiến trình bị dừng

### Dấu hiệu thường gặp

- Tiến trình tự dừng giữa chừng
- Hệ điều hành báo thiếu bộ nhớ
- Bước huấn luyện hoặc pipeline bị kết thúc đột ngột

### Cách giảm tải

- Bắt đầu với khung thời gian lớn hơn như `1H`
- Chỉ xử lý một mã mỗi lần
- Rút ngắn giai đoạn dữ liệu để thử nghiệm trước
- Với mã tự viết thêm, ưu tiên `scan_parquet()` khi dữ liệu lớn
- Tránh chạy nhiều bước nặng cùng lúc trên máy yếu

### Gợi ý thực tế

Nếu bạn chỉ đang thử nhanh lần đầu, hãy dùng:

- `symbol = XAUUSD`
- `tf = 1H`
- `backend = mlf`

Đây thường là tổ hợp nhẹ và ổn định hơn so với các bộ máy học sâu.

---

## 8. Muốn dọn vùng nhớ đệm và đầu ra cũ

Dùng tác vụ chuẩn:

```bash
pixi run clean-generated
```

### Tác vụ này dọn những gì

Các thành phần có thể tạo lại an toàn, ví dụ:

- `.cache/`
- `.pixi-cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `lightning_logs/`
- Nội dung trong `outputs/models/{symbol}/{tf}/{label}/`
- Nội dung trong `outputs/reports/{symbol}/{tf}/{label}/`

### Tác vụ này không xóa

- `data/raw/`

Điều này rất quan trọng, vì dữ liệu thô thường là phần tốn thời gian nhất để tải lại.

---

## 9. Muốn tạo lại dữ liệu trung gian nhưng giữ dữ liệu thô

Nếu bạn cần tạo lại toàn bộ các lớp dữ liệu trung gian mà vẫn giữ `data/raw/`, có thể làm như sau:

```bash
rm -rf data/ohlcv/* data/features/* data/labels/*
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --pivot traditional --anchor daily --atr-mult 0.5
```

### Khi nào nên dùng

Chỉ nên dùng khi bạn chắc chắn muốn tạo lại toàn bộ:

- OHLCV
- Đặc trưng
- Nhãn

### Khi nào không nên dùng

Không nên dùng nếu bạn chỉ muốn kiểm tra một lỗi nhỏ mà chưa rõ nguyên nhân, vì việc xóa dữ liệu trung gian có thể làm mất dấu vết giúp bạn chẩn đoán lỗi.

---

## 10. Backtest không tạo báo cáo

### Cần kiểm tra

- Thư mục `data/labels/{symbol}/{tf}/` có parquet hay không
- Cột tín hiệu truyền qua `--label` có tồn tại hay không
- Cột `atr_14` có tồn tại hay không
- Thư mục `outputs/reports/{symbol}/{tf}/{label}/` có ghi được hay không

### Lệnh mẫu hợp lệ

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### Lưu ý quan trọng

- CLI hiện **không có** tham số `--outdir`
- Báo cáo mặc định được ghi vào:
  - baseline labels: `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/`
  - model backtests: `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/`

Nếu lệnh chạy xong mà không có tệp mới, hãy kiểm tra lại dữ liệu nhãn và cột tín hiệu trước tiên.

---

## 11. Cần kiểm tra kho mã còn ở trạng thái ổn định hay không

Chạy:

```bash
pixi run verify
```

Lệnh này hữu ích khi bạn vừa:

- Đổi cấu hình Pixi
- Sửa tài liệu hoặc điểm vào dòng lệnh
- Dọn vùng nhớ đệm hoặc đầu ra cũ
- Muốn chắc rằng luồng chính vẫn hoạt động

---

## 12. Drift liên tục báo cảnh báo nhưng chưa muốn thay đổi mô hình

Nếu cảnh báo độ lệch xuất hiện ở mức thấp và chưa thực sự đáng lo, bạn có thể nới ngưỡng kiểm tra:

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.2 --threshold-psi 0.3
```

### Ngưỡng mặc định

- `--threshold-ks 0.1`
- `--threshold-psi 0.2`

### Khi nào nên nới ngưỡng

- Khi bạn chỉ muốn giảm nhiễu cảnh báo
- Khi dữ liệu có dao động tự nhiên nhưng chưa ảnh hưởng rõ đến chất lượng
- Khi bạn đang theo dõi thử nghiệm, chưa phải môi trường vận hành thật

Không nên nới ngưỡng chỉ để “làm cho cảnh báo biến mất” nếu bạn chưa hiểu bản chất của độ lệch.

---

## 13. Muốn chạy nhiều khung thời gian cùng lúc

Lệnh `pipeline` hỗ trợ nhiều giá trị `--tf` trong một lần gọi:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

Các khung thời gian sẽ được xử lý lần lượt trong cùng một lệnh.

### Khi nào nên dùng

- Khi bạn muốn tạo nhiều bộ dữ liệu cùng lúc
- Khi bạn đang chuẩn bị cho lần so sánh chuẩn theo nhiều khung thời gian

### Khi nào không nên dùng

- Khi máy yếu
- Khi bạn vẫn đang gỡ lỗi pipeline ở một khung thời gian duy nhất

Trong lúc xử lý sự cố, chạy từng khung thời gian riêng lẻ thường dễ theo dõi hơn.

---

## 14. So sánh chuẩn lưu báo cáo ở đâu

Sau khi chạy `benchmark`, kết quả JSON sẽ được lưu tự động vào:

```text
outputs/reports/{symbol}/{tf}/{label}/benchmark/benchmark_{timestamp}.json
```

Ví dụ:

```text
outputs/reports/XAUUSD/1H/label_10/benchmark/benchmark_20260101_120000.json
```

Nếu bạn không thấy tệp này, hãy kiểm tra:

- Bước so sánh chuẩn có thực sự chạy xong không
- Thư mục `outputs/reports/{symbol}/{tf}/{label}/benchmark/` có tồn tại không
- Có lỗi ghi tệp hoặc lỗi quyền truy cập hay không

---

## 15. Khi nào nên nghi lỗi nằm ở dữ liệu, không phải ở mã?

Hãy nghi nguyên nhân nằm ở dữ liệu nếu bạn thấy một trong các dấu hiệu sau:

- Dữ liệu thô có tháng bị thiếu
- Số lượng lệnh sau backtest bằng `0`
- Cột nhãn tồn tại nhưng không tạo ra tín hiệu vào lệnh
- Báo cáo được sinh ra nhưng kết quả rất bất thường
- Nhiều bước chạy thành công nhưng chỉ số đầu ra “vô lý”

Trong những trường hợp này, hãy quay lại kiểm tra:

1. `download`
2. `qa`
3. `pipeline`

Đừng vội kết luận lỗi nằm ở mô hình.

---

## 16. Khi nào nên nghi lỗi nằm ở cấu hình?

Hãy nghi do cấu hình nếu:

- Lệnh vẫn chạy nhưng kết quả không như mong đợi
- Sai `label`
- Sai `tf`
- Sai `symbol`
- Chọn bộ máy không phù hợp
- Ngưỡng `tp` / `sl` quá bất thường
- Cấu hình trong `config.toml` khác với thứ bạn tưởng đang dùng

Cách an toàn nhất là truyền rõ các tham số quan trọng ngay trên dòng lệnh trong lúc gỡ lỗi.

---

## 17. Cách gỡ lỗi an toàn nhất cho người mới

Nếu bạn chưa rõ lỗi nằm ở đâu, hãy quay về luồng đơn giản nhất:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0
```

Vì sao cách này an toàn?

- Chưa phụ thuộc vào bước huấn luyện
- Dễ tách lỗi dữ liệu khỏi lỗi mô hình
- Còn cho bạn một kết quả đầu tiên để quan sát

Sau khi luồng này ổn, mới thêm bước `train`.

---

## 18. Đọc tiếp gì?

- [../getting-started/QUICKSTART.md](../getting-started/QUICKSTART.md) — lộ trình bắt đầu nhanh nhất
- [../getting-started/NOOB_GUIDE.md](../getting-started/NOOB_GUIDE.md) — hiểu tổng thể quy trình
- [USAGE_GUIDE.md](USAGE_GUIDE.md) — cách dùng từng lệnh
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) — cách đọc kết quả đánh giá
- [../reference/CONFIG_REFERENCE.md](../reference/CONFIG_REFERENCE.md) — tra cứu cấu hình
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) — hiểu kiến trúc hệ thống
