# MLFX — Tham chiếu Feature

Tài liệu này liệt kê mọi cột do `mlfx pipeline` tạo ra, ý nghĩa của từng cột, và các tham số cấu hình ảnh hưởng đến chúng.

---

## 1. Cột OHLCV Gốc

Các cột này đến từ tick data thô sau khi resample và luôn có mặt trong output.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `timestamp` | Datetime (UTC) | Thời điểm mở cây nến |
| `open` | Float | Giá mở cửa |
| `high` | Float | Giá cao nhất |
| `low` | Float | Giá thấp nhất |
| `close` | Float | Giá đóng cửa |
| `volume` | Float | Volume tick của cây nến |

> **Lưu ý**: OHLCV được tính từ **giá mid** (`(bid + ask) / 2`), không phải bid hoặc ask riêng lẻ.

---

## 2. Chỉ báo Động lượng

Được kiểm soát bởi `[features]` trong `config.toml`.

| Cột | Khóa config | Mặc định | Mô tả |
|---|---|---|---|
| `rsi_{period}` | `rsi_period` | `14` | Chỉ số sức mạnh tương đối (RSI) |
| `macd` | `macd_fast`, `macd_slow` | `12`, `26` | Đường MACD |
| `macd_signal` | `macd_signal` | `9` | Đường signal của MACD |
| `macd_hist` | — | — | Histogram MACD (`macd - macd_signal`) |

---

## 3. Chỉ báo Biến động

| Cột | Khóa config | Mặc định | Mô tả |
|---|---|---|---|
| `atr_{period}` | `atr_period` | `14` | Average True Range (biên độ thực trung bình) |

---

## 4. Đường Trung bình Động (EMA)

| Cột | Khóa config | Mặc định | Mô tả |
|---|---|---|---|
| `ema_20` | `ema_periods` | `[20, 50, 200]` | EMA 20 cây nến |
| `ema_50` | `ema_periods` | `[20, 50, 200]` | EMA 50 cây nến |
| `ema_200` | `ema_periods` | `[20, 50, 200]` | EMA 200 cây nến |

Có thể thêm các EMA khác bằng cách chỉnh `ema_periods` trong config.

---

## 5. Pivot Points (Điểm Hỗ trợ/Kháng cự)

Được thêm bởi `add_sr_pp_features()`. Phương pháp tính được chọn qua `--pivot` / `pivot_type`.

**Phương pháp hỗ trợ**: `traditional`, `fibonacci`, `woodie`, `camarilla`, `demark`

| Mẫu cột | Mô tả |
|---|---|
| `pp` | Điểm pivot trung tâm |
| `r1`, `r2`, `r3`, `r4` | Các mức kháng cự (r4 không có ở mọi phương pháp) |
| `s1`, `s2`, `s3`, `s4` | Các mức hỗ trợ (s4 không có ở mọi phương pháp) |
| `pp_dist_{level}` | Khoảng cách giá thô từ close đến từng mức pivot |
| `pp_dist_{level}_atr` | Khoảng cách được chuẩn hóa theo ATR (`pp_dist_{level} / atr_14`) |

Chu kỳ neo (`daily`, `weekly`, `monthly`) được chọn qua `--anchor` / `pivot_anchor`.

---

## 6. ICT Killzones (Vùng Giờ Giao dịch)

Tất cả timestamp được chuyển sang **Giờ Đông Bộ Mỹ (ET / America/New_York)** trước khi tính session flag.

### 6.1 Cờ Phiên Giao dịch

| Cột | Khung giờ ET | Mô tả |
|---|---|---|
| `in_asia` | 20:00 trở đi | Phiên Á (đầu phiên tối New York) |
| `in_london` | 02:00 – 05:00 | Killzone mở cửa London |
| `in_nyam` | 09:30 – 11:00 | Killzone buổi sáng New York |
| `in_nylunch` | 12:00 – 13:00 | Giờ nghỉ trưa New York |
| `in_nypm` | 13:30 – 16:00 | Killzone buổi chiều New York |

### 6.2 Cột Phái sinh theo Phiên

Với mỗi tên phiên `{kz}` trong `[asia, london, nyam, nylunch, nypm]`:

| Cột | Mô tả |
|---|---|
| `kz_{kz}_session_id` | Số nguyên đếm từng lần xuất hiện liên tiếp của phiên |
| `kz_{kz}_high` | Giá cao chạy của phiên (cumulative max trong phiên) |
| `kz_{kz}_low` | Giá thấp chạy của phiên (cumulative min trong phiên) |
| `kz_{kz}_mid` | Điểm giữa phiên `(kz_high + kz_low) / 2` |
| `kz_{kz}_range` | Biên độ phiên `kz_high - kz_low` |
| `kz_{kz}_avg_range` | Trung bình biên độ `avg_range_n` phiên gần nhất |
| `dist_to_{kz}_high` | `close - kz_high` |
| `dist_to_{kz}_low` | `close - kz_low` |
| `dist_to_{kz}_high_atr` | `dist_to_{kz}_high` chuẩn hóa theo ATR |
| `dist_to_{kz}_low_atr` | `dist_to_{kz}_low` chuẩn hóa theo ATR |

`avg_range_n` được kiểm soát bởi khóa `avg_range_n` trong `[features]` (mặc định: `5` phiên).

### 6.3 Mức Giá Ngày / Tuần / Tháng

| Cột | Mô tả |
|---|---|
| `d_open` | Giá mở cửa ngày hôm nay (theo lịch ET) |
| `d_high` | Giá cao nhất ngày hôm nay (chạy) |
| `d_low` | Giá thấp nhất ngày hôm nay (chạy) |
| `w_open` | Giá mở cửa tuần này |
| `w_high` | Giá cao nhất tuần này (chạy) |
| `w_low` | Giá thấp nhất tuần này (chạy) |
| `m_open` | Giá mở cửa tháng này |
| `m_high` | Giá cao nhất tháng này (chạy) |
| `m_low` | Giá thấp nhất tháng này (chạy) |
| `pd_high` | Giá cao ngày hôm qua |
| `pd_low` | Giá thấp ngày hôm qua |
| `pw_high` | Giá cao tuần trước |
| `pw_low` | Giá thấp tuần trước |
| `pm_high` | Giá cao tháng trước |
| `pm_low` | Giá thấp tháng trước |

---

## 7. Order Block (ICT)

Order block xác định các cây nến tổ chức xuất hiện ngay trước một cú chuyển động mạnh.

**Logic phát hiện**:
1. Tính trung bình thân nến 5 cây gần nhất (`avg_body`)
2. Một cây nến là "nến lớn" khi `body > avg_body × 1.5`
3. **Order Block tăng**: cây nến giảm ngay tiếp theo là cây nến tăng "lớn"
4. **Order Block giảm**: cây nến tăng ngay tiếp theo là cây nến giảm "lớn"

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ob_bullish` | Boolean | Cây nến này là OB tăng |
| `ob_bearish` | Boolean | Cây nến này là OB giảm |
| `ob_bull_high` | Float | High của OB tăng gần nhất (forward-fill) |
| `ob_bull_low` | Float | Low của OB tăng gần nhất (forward-fill) |
| `ob_bear_high` | Float | High của OB giảm gần nhất (forward-fill) |
| `ob_bear_low` | Float | Low của OB giảm gần nhất (forward-fill) |
| `price_in_bull_ob` | Boolean | Close nằm trong vùng OB tăng |
| `price_in_bear_ob` | Boolean | Close nằm trong vùng OB giảm |

---

## 8. Fair Value Gap — FVG (Vùng Mất Cân Bằng)

FVG là vùng mất cân bằng giá được xác định bằng mẫu 3 cây nến.

**Logic phát hiện**:
- **FVG tăng**: `low` của cây hiện tại cao hơn `high` của cây 2 phiên trước (gap lên)
- **FVG giảm**: `high` của cây hiện tại thấp hơn `low` của cây 2 phiên trước (gap xuống)

| Cột | Kiểu | Mô tả |
|---|---|---|
| `fvg_bullish` | Boolean | Cây nến này tạo ra một FVG tăng |
| `fvg_bearish` | Boolean | Cây nến này tạo ra một FVG giảm |
| `fvg_bull_top` | Float | Đỉnh FVG tăng gần nhất (forward-fill) |
| `fvg_bull_bot` | Float | Đáy FVG tăng gần nhất (forward-fill) |
| `fvg_bear_top` | Float | Đỉnh FVG giảm gần nhất (forward-fill) |
| `fvg_bear_bot` | Float | Đáy FVG giảm gần nhất (forward-fill) |
| `price_in_bull_fvg` | Boolean | Close nằm trong vùng FVG tăng |
| `price_in_bear_fvg` | Boolean | Close nằm trong vùng FVG giảm |

---

## 9. Cột Nhãn (Label)

Nhãn được thêm vào bởi bước gắn nhãn (stage `pipeline` bao gồm nhãn trừ khi dùng `--skip-labels`).

**Các horizon**: `5`, `10`, `20` cây nến phía trước.

**Ngưỡng**: `atr_mult × atr_14` (mặc định `atr_mult=0.5`, tức ngưỡng = `0.5 × ATR_14`)

| Giá trị nhãn | Ý nghĩa |
|---|---|
| `2` | Close sau `horizon` cây vượt hơn `2 × ngưỡng` phía trên (tăng mạnh) |
| `1` | Close sau `horizon` cây nằm trong khoảng `ngưỡng` đến `2 × ngưỡng` phía trên (tăng nhẹ) |
| `0` | Close sau `horizon` cây nằm trong `±ngưỡng` (trung lập / không giao dịch) |
| `-1` | Close sau `horizon` cây nằm trong khoảng `ngưỡng` đến `2 × ngưỡng` phía dưới (giảm nhẹ) |
| `-2` | Close sau `horizon` cây vượt hơn `2 × ngưỡng` phía dưới (giảm mạnh) |
| `null` | Cây nến tương lai không tồn tại (các cây cuối của mỗi file) |

| Cột | Horizon | Mô tả |
|---|---|---|
| `label_5` | 5 cây nến | Nhãn định hướng ngắn hạn |
| `label_10` | 10 cây nến | Nhãn định hướng trung hạn (mặc định được khuyến nghị) |
| `label_20` | 20 cây nến | Nhãn định hướng dài hạn |

`atr_mult` được kiểm soát bởi `--atr-mult` trên CLI và `atr_mult` trong `[pipeline]` config.

---

## 10. Tổng kết: Số lượng Cột

Một run với cài đặt mặc định tạo ra khoảng **90+ cột** mỗi cây nến, bao gồm:

- 6 cột OHLCV gốc
- 4 cột động lượng (rsi, macd ×3)
- 1 cột ATR
- 3 cột EMA
- ~15 cột pivot (tùy phương pháp)
- 5 cờ phiên + 10×5 cột phái sinh theo phiên
- 9 cột mức giá DWM
- 8 cột Order Block
- 8 cột FVG
- 3 cột nhãn (thêm sau cùng)

Số lượng cột chính xác phụ thuộc vào phương pháp pivot và cài đặt `ema_periods`.
