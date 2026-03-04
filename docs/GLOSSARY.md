# Tự Điển Thuật Ngữ (Glossary)

Dành cho những người mới bắt đầu làm quen với Trading và Machine Learning.

---

## 1. Thuật ngữ Trading (Giao dịch)

*   **Tick Data**: Mức dữ liệu nhỏ nhất của thị trường. Mỗi khi giá thay đổi dù chỉ 1 chút (1 tick), sàn sẽ ghi lại. Nó rất nặng vì có hàng chục tick mỗi giây.
*   **OHLCV**: Viết tắt của Open, High, Low, Close, Volume. Nghĩa là Giá Mở cửa, Cao nhất, Thấp nhất, Đóng cửa và Khối lượng của một **Cây Nến** (Bar/Candle) trong một khoảng thời gian (ví dụ 1 Giờ).
*   **Timeframe (TF)**: Khung thời gian của một cây nến. Ví dụ: `1m` (1 phút), `5m` (5 phút), `1H` (1 giờ).
*   **S/R (Support/Resistance)**: Vùng Hỗ trợ (Support - giá khó rớt xuống thêm) và Kháng cự (Resistance - giá khó tăng vượt qua).
*   **Killzone**: Các khung giờ "vàng" có khối lượng giao dịch cực lớn. Trong dự án này ta quan tâm 3 Killzone: Asian (Châu Á), London, và New York. Chiến lược ICT rất thích đánh ở những khung giờ này.
*   **ATR (Average True Range)**: Một chỉ báo đo lường "Độ giật" (biến động) của thị trường. ATR càng cao, nến càng dài. Ta dùng ATR để quyết định mức chốt lời/cắt lỗ cho an toàn thay vì dùng số Pips cứng nhắc.
*   **LONG / SHORT**: 
    *   **LONG (+1)**: Mua vào, kỳ vọng giá tăng.
    *   **SHORT (-1)**: Bán khống, kỳ vọng giá giảm.
*   **NEUTRAL (0)**: Đứng ngoài quan sát, thị trường không rõ xu hướng.
*   **R-multiple (R)**: R là Risk (Rủi ro). Nếu bạn quy định 1 lệnh lỗ tối đa mất 100$ (tức là 1R = 100$). Khi thắng bạn được 150$, tức là bạn lãi 1.5R. Trong dự án này, hệ thống chấm điểm dựa trên "R" thay vì tiền USD thật.

---

## 2. Thuật ngữ Data & Machine Learning (AI)

*   **Parquet (`.parquet`)**: Định dạng file dữ liệu xịn hơn Excel hay CSV. Nó nén dung lượng xuống rất nhỏ và cho phép máy tính đọc cực kỳ nhanh. Toàn bộ dự án này xài Parquet.
*   **Data Pipeline (Đường ống dữ liệu)**: Quá trình hút dữ liệu thô (Tick) -> Nặn thành Nến (OHLCV) -> Đắp thêm chỉ báo (Features) -> Đóng gói để AI học.
*   **Features (Đặc trưng)**: Những "Gợi ý" mà bạn đưa cho AI. Để AI đoán được giá Vàng, bạn phải mớm cho nó các thông số như RSI đang là bao nhiêu, khoảng cách tới S/R là bao nhiêu. ML_FX có 133 features.
*   **Labels (Gán nhãn)**: Đáp án chuẩn (Tương lai là lên hay xuống) mà bạn đem giấu. Trong lúc Train, AI sẽ nhìn Features và ráng đoán Label. Đoán sai nó tự học cách sửa sai. Đoán đúng nó bám vào mẫu đó.
*   **XGBoost / LightGBM / KNN**: Tên của các loại bộ não AI (Thuật toán). XGBoost và LightGBM là dạng "Rừng cây quyết định" cực kỳ thông minh trong data tài chính. KNN thì là thuật toán bình dân hơn.
*   **Optuna**: Một công cụ tự động "vặn ốc vít" (Hyperparameter tuning) cho bộ não AI để tìm ra não thông minh nhất mà bạn không cần tự test bằng tay.

---

## 3. Thuật ngữ Công cụ (Tools)

*   **Pixi**: Là một công cụ quản lý dự án thần thánh. Nó sẽ tự động tải Python chuẩn, tải mọi thư viện (Polars, Xgboost..) về dự án mà không làm rác máy tính của bạn.
*   **Polars**: Thư viện xử lý dữ liệu đời mới, nhanh hơn Pandas hàng chục lần. Giúp máy tính cá nhân có thể xử lý 10 năm dữ liệu (nửa tỷ dòng) chỉ trong vài phút. 
