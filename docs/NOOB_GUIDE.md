# Giải Phẫu Hệ Thống: Cẩm nang cho Newbie 🧠

Chào bạn! Thay vì đập ngay vào mặt bạn hàng tá dòng code khó hiểu, tài liệu này được thiết kế để bạn hiểu được **Bản chất của con Bot này đang làm gì sau cánh gà**. Hiểu được nó, bạn mới làm chủ được nó.

Hãy tưởng tượng bạn đang xay hạt cafe để pha Espresso. Bot ML_FX cũng hoạt động y hệt như thế, với 4 giai đoạn chính (được gọi là Data Pipeline).

---

## 🔧 4 Giai Đoạn Vận Hành Chống "Ngáo"

### 1️⃣ Khai thác Sơ chế (Raw Data -> Nến 1 Giờ)
Thị trường hoạt động bằng các "Tick" (từng nhịp giật lên xuống rất nhỏ). Máy tính không thể học được từ Tick vì nó quá nhiễu. 
Do đó, chúng ta có một file tên là `resample.py`. Trách nhiệm của nó là nén hàng triệu nhịp đập đó thành Cây Nến (Candlestick) 1 Giờ (hoặc 5 Phút, 15 Phút tùy bạn chọn).

### 2️⃣ Thêm Chút Gia Vị (Gắn Features/Chỉ báo)
Giả sử bạn chỉ đưa cho AI bộ ảnh nến Xanh, nến Đỏ thì AI sẽ "bị mù", nó không thể biết đâu là Đỉnh/Đáy.
File `features.py` làm nhiệm vụ đi tính toán và đính kèm 133 "kính lúp" vào cây nến đó.
*   **Ví dụ:** Cây nến đang chỉ điểm chỉ số RSI là 30 (quá bán), cách mốc hỗ trợ của tuần cũ bao nhiêu giá. Nhờ đó, thuật toán AI mới có dữ kiện để "mở mắt" ra nhìn.

### 3️⃣ Chấm Điểm Bài Tập (Labeling)
Để dạy AI, bạn phải phát bài kiểm tra có sẵn ĐÁP ÁN. 
File `labels.py` có nhiệm vụ đi nhìn lén Tương Lai. Ví dụ, nó nhìn thấy 10 cây nến tiếp theo giá VÀNG (XAUUSD) thực sự tăng mạnh, nó sẽ quay ngược lại cây nến hiện tại và lấy bút Đỏ viết lên đó chữ `"LONG"`. 
Nó cứ làm như thế hàng tỷ nến trong 10 năm qua.

### 4️⃣ Đào Tạo Siêu Trí Tuệ (Khúc Machine Learning)
Đây là lúc phép màu xuất hiện. Bạn tung rổ dữ liệu (Features + Labels) cho XGBoost hoặc LSTM. Lúc này AI sẽ học một quy tắc ngầm định như sau:
> *"À! Tôi nhận ra cứ mỗi khi MACD cắt lên + RSI ở mốc 30 + Đang là phiên giao dịch London... thì tỉ lệ nến sau mang nhãn LONG là tới 70%!"*

---

## 🎯 Tư Duy Đúng Cần Nắm Rõ Khi Dùng Bot

Nếu bạn vừa mới bước vào làm quen, hãy xóa bỏ suy nghĩ **"Bot tiên tri giá"**.

1. **Bot không Đoán Chính Xác 100%:** Bot của chúng ta chỉ đang tính "Xác suất". Nó tìm lại lịch sử, đo lường các tín hiệu và chọn cửa có tỷ lệ thắng cao nhất theo số liệu. Nó vẫn sẽ có lệnh thua (Take Profit / Stop Loss).
2. **Trật Tự Tuyệt Đối:** Quy trình 4 bước ở trên (**Nến -> Feature -> Label -> Train**) giống như việc mặc Quần Trong rồi mới mặc Quần Ngoài. Bạn không thể nhảy cóc chạy Train AI khi chưa có Features. Mọi lỗi "Không tìm thấy file" đều bắt nguồn từ đây. Đọc ngay [USAGE_GUIDE.md](USAGE_GUIDE.md) để biết lệnh chạy.
3. **Từ Điển (Đừng để bị dắt Mũi)**: Ai chém gió với bạn mấy từ lạ lạ như *Tick*, *Parquet*, *OHLCV*, *Optuna*... Đừng hoảng! Hãy mở trang [GLOSSARY.md](GLOSSARY.md) (Từ Điển Thuật Ngữ) để tra cứu lại. Chẳng có gì cao siêu cả!
4. **Lỗi Đừng Khóc:** Bấm chạy mà nó văng màu Đỏ cả cái màn hình? Thở ra một hơi thật dài, mở phao cứu sinh [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (Sổ Tay Cấp Cứu) lên. Lỗi của bạn 99% nằm trong đó.

---
Bây giờ thì bạn sẵn sàng rồi đấy! Hãy qua quay trở lại trang [Sổ Tay Gõ Code Dành Cho Tay Mơ - USAGE GUIDE](USAGE_GUIDE.md) và gõ lệnh chạy thôi!
