# MLFX — Tham chiếu đặc trưng

Tài liệu này liệt kê các cột do `mlfx pipeline` tạo ra, giải thích ý nghĩa của từng cột, và nêu rõ những tham số cấu hình có ảnh hưởng đến chúng.

---

## 1. Các cột OHLCV gốc

Các cột này được tạo ra từ dữ liệu tick thô sau bước chuyển đổi sang nến và luôn có mặt trong đầu ra.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `timestamp` | Datetime (UTC) | Thời điểm mở cây nến |
| `open` | Float | Giá mở cửa |
| `high` | Float | Giá cao nhất |
| `low` | Float | Giá thấp nhất |
| `close` | Float | Giá đóng cửa |
| `volume` | Float | Khối lượng tick của cây nến |

> **Lưu ý:** OHLCV được tính từ **giá trung bình** (`(bid + ask) / 2`), không phải chỉ từ `bid` hoặc `ask`.

---

## 2. Nhóm chỉ báo động lượng

Nhóm này được điều khiển bởi phần `[features]` trong `config.toml`.

| Cột | Khóa cấu hình | Mặc định | Mô tả |
|---|---|---|---|
| `rsi_{period}` | `rsi_period` | `14` | Chỉ số sức mạnh tương đối (RSI) |
| `macd` | `macd_fast`, `macd_slow` | `12`, `26` | Đường MACD |
| `macd_signal` | `macd_signal` | `9` | Đường tín hiệu của MACD |
| `macd_hist` | — | — | Phần chênh giữa `macd` và `macd_signal` |

---

## 3. Nhóm chỉ báo biến động

| Cột | Khóa cấu hình | Mặc định | Mô tả |
|---|---|---|---|
| `atr_{period}` | `atr_period` | `14` | Biên độ thực trung bình (ATR) |

---

## 4. Đường trung bình động hàm mũ (EMA)

| Cột | Khóa cấu hình | Mặc định | Mô tả |
|---|---|---|---|
| `ema_20` | `ema_periods` | `[20, 50, 200]` | EMA của 20 cây nến |
| `ema_50` | `ema_periods` | `[20, 50, 200]` | EMA của 50 cây nến |
| `ema_200` | `ema_periods` | `[20, 50, 200]` | EMA của 200 cây nến |

Bạn có thể thêm các EMA khác bằng cách chỉnh `ema_periods` trong tệp cấu hình.

---

## 5. Các mức điểm xoay và hỗ trợ / kháng cự

Các cột này được thêm bởi `add_sr_pp_features()`. Phương pháp tính được chọn qua `--pivot` hoặc `pivot_type`.

**Các phương pháp hỗ trợ:** `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`

| Mẫu cột | Mô tả |
|---|---|
| `pp` | Điểm xoay trung tâm |
| `r1`, `r2`, `r3`, `r4` | Các mức kháng cự |
| `s1`, `s2`, `s3`, `s4` | Các mức hỗ trợ |
| `pp_dist_{level}` | Khoảng cách giá thô từ `close` đến từng mức |
| `pp_dist_{level}_atr` | Khoảng cách đã chuẩn hóa theo ATR |

Chu kỳ neo được chọn qua `--anchor` hoặc `pivot_anchor`, với các giá trị thường dùng:

- `daily`
- `weekly`
- `monthly`

---

## 6. Khung giờ trọng điểm theo ICT và các phiên giao dịch

Tất cả dấu thời gian được chuyển sang **giờ miền Đông Hoa Kỳ** (`America/New_York`) trước khi tính các cờ phiên.

### 6.1. Cờ phiên giao dịch

| Cột | Khung giờ ET | Mô tả |
|---|---|---|
| `in_asia` | từ 20:00 trở đi | Phiên Á |
| `in_london` | 02:00 – 05:00 | Khung giờ trọng điểm London |
| `in_nyam` | 09:30 – 11:00 | Khung giờ trọng điểm sáng New York |
| `in_nylunch` | 12:00 – 13:00 | Giờ trưa New York |
| `in_nypm` | 13:30 – 16:00 | Khung giờ trọng điểm chiều New York |

### 6.2. Các cột dẫn xuất theo phiên

Với mỗi phiên `{kz}` trong `[asia, london, nyam, nylunch, nypm]`, hệ thống tạo thêm các cột sau:

| Cột | Mô tả |
|---|---|
| `kz_{kz}_session_id` | Số nguyên đếm từng phiên liên tiếp |
| `kz_{kz}_high` | Giá cao nhất đang chạy trong phiên |
| `kz_{kz}_low` | Giá thấp nhất đang chạy trong phiên |
| `kz_{kz}_mid` | Điểm giữa của phiên |
| `kz_{kz}_range` | Biên độ giá của phiên |
| `kz_{kz}_avg_range` | Trung bình biên độ của `avg_range_n` phiên gần nhất |
| `dist_to_{kz}_high` | Khoảng cách từ `close` đến đỉnh phiên |
| `dist_to_{kz}_low` | Khoảng cách từ `close` đến đáy phiên |
| `dist_to_{kz}_high_atr` | Khoảng cách đến đỉnh phiên đã chuẩn hóa theo ATR |
| `dist_to_{kz}_low_atr` | Khoảng cách đến đáy phiên đã chuẩn hóa theo ATR |

Khóa `avg_range_n` trong `[features]` điều khiển số phiên dùng để tính trung bình biên độ. Mặc định là `5`.

### 6.3. Các mức giá theo ngày / tuần / tháng

| Cột | Mô tả |
|---|---|
| `d_open` | Giá mở cửa của ngày hiện tại |
| `d_high` | Giá cao nhất đang chạy của ngày hiện tại |
| `d_low` | Giá thấp nhất đang chạy của ngày hiện tại |
| `w_open` | Giá mở cửa của tuần hiện tại |
| `w_high` | Giá cao nhất đang chạy của tuần hiện tại |
| `w_low` | Giá thấp nhất đang chạy của tuần hiện tại |
| `m_open` | Giá mở cửa của tháng hiện tại |
| `m_high` | Giá cao nhất đang chạy của tháng hiện tại |
| `m_low` | Giá thấp nhất đang chạy của tháng hiện tại |
| `pd_high` | Giá cao nhất của ngày hôm trước |
| `pd_low` | Giá thấp nhất của ngày hôm trước |
| `pw_high` | Giá cao nhất của tuần trước |
| `pw_low` | Giá thấp nhất của tuần trước |
| `pm_high` | Giá cao nhất của tháng trước |
| `pm_low` | Giá thấp nhất của tháng trước |

---

## 7. Khối lệnh (Order Block) theo ICT

Khối lệnh được dùng để xác định các vùng giá mang tính cấu trúc, thường xuất hiện ngay trước một chuyển động mạnh.

### Logic phát hiện

1. Tính trung bình thân nến của 5 cây gần nhất (`avg_body`)
2. Một cây nến được coi là “nến lớn” nếu `body > avg_body × 1.5`
3. **Khối lệnh tăng**: cây nến giảm ngay trước một cây nến tăng lớn
4. **Khối lệnh giảm**: cây nến tăng ngay trước một cây nến giảm lớn

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ob_bullish` | Boolean | Cây nến này là khối lệnh tăng |
| `ob_bearish` | Boolean | Cây nến này là khối lệnh giảm |
| `ob_bull_high` | Float | Giá cao của khối lệnh tăng gần nhất |
| `ob_bull_low` | Float | Giá thấp của khối lệnh tăng gần nhất |
| `ob_bear_high` | Float | Giá cao của khối lệnh giảm gần nhất |
| `ob_bear_low` | Float | Giá thấp của khối lệnh giảm gần nhất |
| `price_in_bull_ob` | Boolean | `close` nằm trong vùng khối lệnh tăng |
| `price_in_bear_ob` | Boolean | `close` nằm trong vùng khối lệnh giảm |

---

## 8. Vùng mất cân bằng giá trị hợp lý (Fair Value Gap — FVG)

FVG là vùng mất cân bằng giá được xác định theo mẫu 3 cây nến.

### Logic phát hiện

- **FVG tăng**: `low` của cây hiện tại cao hơn `high` của cây cách đó 2 phiên
- **FVG giảm**: `high` của cây hiện tại thấp hơn `low` của cây cách đó 2 phiên

| Cột | Kiểu | Mô tả |
|---|---|---|
| `fvg_bullish` | Boolean | Cây nến này tạo ra một FVG tăng |
| `fvg_bearish` | Boolean | Cây nến này tạo ra một FVG giảm |
| `fvg_bull_top` | Float | Đỉnh của FVG tăng gần nhất |
| `fvg_bull_bot` | Float | Đáy của FVG tăng gần nhất |
| `fvg_bear_top` | Float | Đỉnh của FVG giảm gần nhất |
| `fvg_bear_bot` | Float | Đáy của FVG giảm gần nhất |
| `price_in_bull_fvg` | Boolean | `close` nằm trong vùng FVG tăng |
| `price_in_bear_fvg` | Boolean | `close` nằm trong vùng FVG giảm |

---

## 9. Các cột nhãn

Các nhãn được thêm bởi bước gắn nhãn trong quy trình xử lý, trừ khi dùng `--skip-labels`.

### Các chân trời dự báo

- `5`
- `10`
- `20`

### Ngưỡng gắn nhãn

Ngưỡng được tính theo công thức:

- `atr_mult × atr_14`

Mặc định `atr_mult = 0.5`, nghĩa là ngưỡng = `0.5 × ATR_14`.

| Giá trị nhãn | Ý nghĩa |
|---|---|
| `2` | Giá đóng cửa sau `horizon` cây nến vượt quá `2 × ngưỡng` theo hướng tăng |
| `1` | Giá đóng cửa sau `horizon` cây nến tăng trong khoảng từ `ngưỡng` đến `2 × ngưỡng` |
| `0` | Giá đóng cửa sau `horizon` cây nến nằm trong khoảng `±ngưỡng` |
| `-1` | Giá đóng cửa sau `horizon` cây nến giảm trong khoảng từ `ngưỡng` đến `2 × ngưỡng` |
| `-2` | Giá đóng cửa sau `horizon` cây nến vượt quá `2 × ngưỡng` theo hướng giảm |
| `null` | Không đủ dữ liệu tương lai để gắn nhãn |

| Cột | Chân trời dự báo | Mô tả |
|---|---|---|
| `label_5` | 5 cây nến | Nhãn định hướng ngắn hạn |
| `label_10` | 10 cây nến | Nhãn định hướng trung hạn |
| `label_20` | 20 cây nến | Nhãn định hướng dài hạn |

Khóa `atr_mult` được điều khiển bởi `--atr-mult` trên dòng lệnh và `atr_mult` trong phần `[pipeline]` của cấu hình.

---

## 10. Tổng kết về số lượng cột

Một lần chạy với cấu hình mặc định thường tạo ra khoảng **90 cột trở lên** cho mỗi cây nến, bao gồm:

- 6 cột OHLCV gốc
- 4 cột chỉ báo động lượng
- 1 cột ATR
- 3 cột EMA
- khoảng 15 cột điểm xoay (tùy phương pháp)
- 5 cờ phiên và nhiều cột dẫn xuất theo phiên
- 9 cột mức giá ngày / tuần / tháng
- 8 cột khối lệnh
- 8 cột FVG
- 3 cột nhãn

Số lượng cột chính xác sẽ phụ thuộc vào:

- Phương pháp điểm xoay được chọn
- Danh sách `ema_periods`
- Các nhóm đặc trưng đang bật trong bước xử lý

---

## 11. Cách đọc tài liệu này

Bạn nên dùng tài liệu này khi cần trả lời các câu hỏi như:

- Cột này được tạo ra ở bước nào?
- Cột này có ý nghĩa gì?
- Khóa cấu hình nào ảnh hưởng đến cột này?
- Nếu muốn thay đổi cách tạo cột, tôi phải chỉnh ở đâu?

Nếu bạn muốn biết thêm:

- Cách chạy lệnh pipeline: xem `USAGE_GUIDE.md`
- Kiến trúc hệ thống: xem `ARCHITECTURE.md`
- Ý nghĩa thuật ngữ: xem `GLOSSARY.md`
- Cách đánh giá mô hình: xem `EVALUATION_GUIDE.md`
