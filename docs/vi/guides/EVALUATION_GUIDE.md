# MLFX - Hướng dẫn đánh giá

Tài liệu này giải thích cách chạy `mlfx evaluate`, cách đọc các chỉ số đánh giá và cách hiểu các tệp đầu ra được tạo ra sau mỗi lần chạy.

## Tài liệu liên quan

- [Cổng tài liệu tiếng Việt](../README.md)
- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](USAGE_GUIDE.md)
- [Tham chiếu đặc trưng](../reference/FEATURE_REFERENCE.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)

---

## 1. Dữ liệu đầu vào

Bước đánh giá đọc toàn bộ dữ liệu đã gắn nhãn trong:

```text
data/labels/{symbol}/{tf}/*.parquet
```

Tập dữ liệu đầu vào tối thiểu cần có:

- Cột `timestamp`
- Các cột giá như `open`, `high`, `low`, `close`
- Cột ATR, mặc định là `atr_14`
- Cột tín hiệu được truyền qua `--label`

Các cột tín hiệu thường dùng:

- `label_5`
- `label_10`
- `label_20`

---

## 2. Cách chạy kiểm định

```bash
pixi run mlfx evaluate \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --capital 10000 \
  --risk 1.0 \
  --commission 0.1 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0
```

### 2.1. Quy tắc khớp lệnh

Với mỗi cây nến có tín hiệu, bộ mô phỏng sẽ:

1. Mở vị thế tại **giá mở cửa của cây nến kế tiếp**
2. Kiểm tra các cây nến phía sau xem có chạm mức chốt lời hoặc dừng lỗ hay không
3. Nếu sau **10 cây nến** (`horizon_limit`) vẫn chưa chạm chốt lời hoặc dừng lỗ, lệnh sẽ bị đóng bắt buộc ở cây nến thứ 10

Mức chốt lời và dừng lỗ được biểu diễn theo đơn vị **R** — tức là bội số của khoảng rủi ro ban đầu, được suy ra từ `atr_14`.

### 2.2. Ánh xạ từ nhãn sang tín hiệu giao dịch

Các giá trị nhãn thứ bậc được ánh xạ sang tín hiệu như sau:

| Nhãn | Tín hiệu | Ý nghĩa |
|---|---|---|
| `2` | LONG | Tăng mạnh |
| `1` | LONG | Tăng |
| `0` | Bỏ qua | Không vào lệnh |
| `-1` | SHORT | Giảm |
| `-2` | SHORT | Giảm mạnh |

> **Lưu ý:** Nhãn `1` và `2` hiện đều tạo ra cùng một loại lệnh LONG. Mức độ mạnh hay yếu (`±2` so với `±1`) hiện chưa làm thay đổi quy mô vị thế trong phần cài đặt hiện tại.

### 2.3. Ý nghĩa các tham số

- `--symbol`: Mã công cụ tài chính
- `--tf`: Khung thời gian cần đánh giá
- `--label`: Cột tín hiệu dùng để vào lệnh
- `--capital`: Vốn ban đầu, dùng để quy đổi từ `R` sang tiền
- `--risk`: Phần trăm vốn chấp nhận rủi ro cho mỗi lệnh
- `--commission`: Chi phí hoa hồng cho mỗi lệnh
- `--tp`: Mức chốt lời theo đơn vị `R`
- `--sl`: Mức dừng lỗ theo đơn vị `R`
- `--slippage`: Mức trượt giá giả lập
- `--use-labels`: Chỉ kiểm định trực tiếp trên nhãn, bỏ qua dự đoán của mô hình

---

## 3. Hai chế độ đánh giá: mô hình và nhãn

### 3.1. Chế độ mặc định

Theo mặc định, `mlfx evaluate` sẽ dùng **mô hình tốt nhất đã đăng ký** để sinh dự đoán, sau đó kiểm định trên các dự đoán đó.

Nếu chưa có mô hình phù hợp, quy trình sẽ quay về dùng **nhãn** như một mốc tham chiếu.

### 3.2. Kiểm định trực tiếp trên nhãn

Nếu bạn muốn đánh giá trực tiếp nhãn gốc, hãy thêm `--use-labels`:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0
```

### 3.3. Kiểm định trên mô hình

Nếu không truyền `--use-labels`, hệ thống sẽ cố gắng:

1. Đọc `outputs/models/registry.json`
2. Chọn mô hình tốt nhất dựa trên chỉ số đã đăng ký
3. Chạy suy luận trên toàn bộ tập dữ liệu
4. Kiểm định trên dự đoán của mô hình đó

Ví dụ:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 3.4. Luồng so sánh mốc nền

Một cách hợp lý để kiểm tra giá trị thực sự của mô hình là:

```bash
# Bước 1: Mốc nền — đánh giá trực tiếp trên nhãn
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0

# Bước 2: Huấn luyện mô hình
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf

# Bước 3: Đánh giá mô hình
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Khi đó bạn có thể so sánh:

- Đường vốn
- Hệ số lợi nhuận
- Tỷ lệ Sharpe
- Lợi nhuận ròng theo đơn vị `R`
- Độ ổn định của kết quả

---

## 4. Quy ước đặt tên báo cáo

Bộ chạy sẽ tạo `out_name` theo công thức:

```text
{label}_R{int(tp_r * 10)}
```

Sau đó mô-đun báo cáo tạo tiền tố đầy đủ:

```text
{symbol}_{tf}_{out_name}
```

Ví dụ với:

- `symbol = XAUUSD`
- `tf = 1H`
- `label = label_10`
- `tp = 1.5`

thì tiền tố sẽ là:

```text
XAUUSD_1H_label_10_R15
```

---

## 5. Các tệp đầu ra được tạo ra

Mỗi lần chạy thường sinh ra 4 đầu ra trong thư mục báo cáo theo từng nhãn:

- `{prefix}_candlestick.html`
- `{prefix}_equity.png`
- `{prefix}_heatmap.png`
- `{prefix}_trades.parquet`

Vị trí mặc định:

- Chế độ nhãn nền: `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/`
- Chế độ backtest mô hình: `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/`

Ví dụ:

```text
outputs/reports/XAUUSD/1H/label_10/model/R15/model_label_10_R15_candlestick.html
outputs/reports/XAUUSD/1H/label_10/model/R15/model_label_10_R15_equity.png
outputs/reports/XAUUSD/1H/label_10/model/R15/model_label_10_R15_heatmap.png
outputs/reports/XAUUSD/1H/label_10/model/R15/model_label_10_R15_trades.parquet
```

---

## 6. Các chỉ số quan trọng

Phần tóm tắt đầu ra thường gồm:

- `Total Trades`
- `Win Rate (%)`
- `Profit Factor`
- `Net Profit (R)`
- `Net Profit ($)`
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Final Capital ($)`

### 6.1. Diễn giải nhanh

- `Total Trades`: Tổng số lệnh được mô phỏng
- `Win Rate (%)`: Tỷ lệ lệnh có lãi; không nên dùng riêng lẻ
- `Profit Factor`: Tổng lãi chia tổng lỗ; thường cần `> 1` mới có ý nghĩa tối thiểu
- `Net Profit (R)`: Lợi nhuận chuẩn hóa; rất hữu ích khi so sánh công bằng nhiều cấu hình
- `Net Profit ($)`: Lợi nhuận quy đổi ra tiền theo `capital` và `risk`
- `Sharpe Ratio`: Lợi nhuận trung bình so với biến động tổng thể
- `Sortino Ratio`: Tương tự Sharpe nhưng chỉ phạt biến động theo hướng xấu
- `Calmar Ratio`: Lợi nhuận ròng chia cho mức sụt giảm tối đa
- `Final Capital ($)`: Số vốn cuối cùng sau khi áp tất cả chi phí và kết quả giao dịch

### 6.2. Lưu ý khi đọc chỉ số

- Đừng dùng `Win Rate` một mình để kết luận chiến lược tốt hay xấu
- `Profit Factor`, `Net Profit (R)` và `Sharpe / Sortino` thường hữu ích hơn khi so sánh cấu hình
- Số lượng lệnh quá ít có thể làm chỉ số rất đẹp nhưng thiếu ý nghĩa thống kê
- Nếu có thể, luôn so sánh mô hình với mốc nền là nhãn

---

## 7. Cách đọc từng loại báo cáo

### 7.1. Báo cáo nến dạng HTML

Hiển thị:

- Biến động giá
- Dấu đánh dấu điểm vào lệnh LONG / SHORT
- Khung RSI nếu tập dữ liệu có `rsi_14`

Phù hợp để:

- Kiểm tra xem điểm vào lệnh có hợp lý không
- Xem tín hiệu có bị dồn vào một đoạn ngắn bất thường không
- Xác nhận chiến lược có vào lệnh đúng thời điểm hay không

### 7.2. Biểu đồ đường vốn dạng PNG

Hiển thị:

- Lãi/lỗ tích lũy theo đơn vị `R`
- Mức sụt giảm vốn ở khung bên dưới

Phù hợp để:

- Nhìn nhịp tăng trưởng vốn
- So sánh độ “mượt” giữa nhiều cấu hình
- Đánh giá xem lợi nhuận đến từ cả chuỗi lệnh ổn định hay chỉ từ vài lệnh may mắn

### 7.3. Bản đồ nhiệt dạng PNG

Hiển thị hiệu suất trung bình theo:

- Giờ UTC
- Ngày trong tuần

Phù hợp để:

- Xác định xem có nên thêm bộ lọc thời gian hoặc bộ lọc phiên giao dịch hay không
- Nhận diện khung giờ có hiệu suất tốt hoặc kém một cách bất thường

---

## 8. Những kiểu lỗi thường gặp

Bước đánh giá thường lỗi hoặc cho kết quả rỗng khi:

- Không có tệp parquet trong `data/labels/{symbol}/{tf}/`
- Cột được truyền qua `--label` không tồn tại
- Cột `atr_14` không tồn tại
- Dữ liệu quá ít nên gần như không có lệnh nào
- Cột tín hiệu không bao giờ phát ra LONG hoặc SHORT có ý nghĩa

### 8.1. Dấu hiệu lỗi phổ biến

- Dòng lệnh không in ra bảng chỉ số tổng hợp
- Không có tệp mới trong `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/` hoặc `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/`
- Số lượng lệnh quá thấp hoặc bằng `0`
- Tên tệp sinh ra không đúng tiền tố mong đợi

---

## 9. Danh sách kiểm tra sau khi chạy đánh giá

Sau khi chạy xong, bạn nên kiểm tra:

- Dòng lệnh có in ra các chỉ số tổng hợp hay không
- `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/` hoặc `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/` có các đầu ra mới hay không
- Tên tệp có đúng tiền tố kỳ vọng hay không
- Số lượng lệnh có đủ lớn để kết luận hay chỉ là một mẫu quá nhỏ
- Nếu đang đánh giá mô hình, mô hình đó có thực sự tồn tại trong registry không

---

## 10. Ví dụ Python tối thiểu

```python
from pathlib import Path

import polars as pl

from mlfx.evaluation.backtest import compute_metrics, simulate_trades
from mlfx.evaluation.reporting import generate_full_report

df = pl.read_parquet("data/labels/XAUUSD/1H/2024-01.parquet")

trades = simulate_trades(
    df,
    signal_col="label_10",
    tp_r=1.5,
    sl_r=1.0,
    commission=0.1,
    slippage=0.0,
)

metrics = compute_metrics(
    trades,
    initial_capital=10000.0,
    risk_pct=1.0,
)

print(metrics)

generate_full_report(
    "XAUUSD",
    "1H",
    df,
    trades,
    "label_10_R15",
    Path("outputs/reports/XAUUSD/1H"),
)
```

---

## 11. Gợi ý thứ tự đọc kết quả

Nếu bạn mới bắt đầu, hãy đọc kết quả theo thứ tự:

1. `Total Trades`
2. `Profit Factor`
3. `Net Profit (R)`
4. `Sharpe Ratio`
5. Đường vốn
6. Bản đồ nhiệt
7. Báo cáo nến dạng HTML

Lý do:

- Các chỉ số tổng quan cho biết cấu hình có đáng xem tiếp hay không
- Đường vốn cho biết chất lượng diễn biến vốn
- Bản đồ nhiệt gợi ý cải tiến chiến lược theo thời gian
- Báo cáo nến giúp kiểm tra trực quan điểm vào lệnh

---

## 12. Xem thêm

- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](USAGE_GUIDE.md)
- [Tham chiếu đặc trưng](../reference/FEATURE_REFERENCE.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)
