# Bảng Thuật Ngữ (Glossary)

Hướng dẫn thân thiện cho người mới bắt đầu về các thuật ngữ Giao dịch và Học Máy (Machine Learning) được sử dụng trong dự án ML_FX.

---

## 1. Thuật ngữ Giao dịch

*   **Tick Data (Dữ liệu Tick)**: Đơn vị dữ liệu thị trường nhỏ nhất. Lần nào giá dao động dù chỉ một phần nhỏ (một tick), sàn giao dịch đều ghi lại. Vì có thể có hàng chục tick mỗi giây, dữ liệu này cực kỳ dày đặc.
*   **OHLCV**: Viết tắt của Open (Mở cửa), High (Giá cao nhất), Low (Giá thấp nhất), Close (Đóng cửa), Volume (Khối lượng). Đại diện cho giá Mở cửa, Cao nhất, Thấp nhất, Đóng cửa và Khối lượng giao dịch của một tài sản trong một khoảng thời gian cụ thể (ví dụ: một cây nến 1 Giờ).
*   **Timeframe (TF - Khung thời gian)**: Thời lượng của một cây nến. Phổ biến là `1m` (1 phút), `5m` (5 phút), `1H` (1 giờ).
*   **S/R (Hỗ trợ/Kháng cự)**: Các vùng Hỗ trợ (các mức giá mà xu hướng giảm thường chững lại) và Kháng cự (các mức giá mà xu hướng tăng thường đảo chiều).
*   **Killzone (Vùng giao dịch trọng điểm)**: Các khung thời gian cụ thể mang khối lượng giao dịch cao nhất. Trong dự án này, chúng ta nhắm mục tiêu vào 3 Killzone: Châu Á (Asian), Luân Đôn (London), và New York. Chiến lược ICT phụ thuộc rất nhiều vào giao dịch trong những vùng có thanh khoản cao này.
*   **ATR (Average True Range - Vùng dao động thực tế trung bình)**: Một chỉ báo đo lường biên độ dao động của thị trường. ATR càng cao nghĩa là giá biến động càng mạnh. Chúng ta sử dụng ATR để tính toán linh hoạt mức Chốt Lời (Take Profit) và Dừng Lỗ (Stop Loss) an toàn thay vì sử dụng số Pip cứng nhắc.
*   **LONG / SHORT (Mua / Bán khống)**: 
    *   **LONG (+1)**: Mua một tài sản, kỳ vọng giá của nó sẽ tăng.
    *   **SHORT (-1)**: Bán một tài sản mà bạn không thực sự sở hữu, kỳ vọng giá của nó sẽ giảm.
*   **NEUTRAL (0)**: Không có xu hướng thị trường rõ ràng. Hành động tốt nhất là đứng ngoài quan sát.
*   **R-multiple (R)**: R viết tắt của Rủi ro (Risk). Nếu bạn mạo hiểm $100 mỗi giao dịch, 1R = $100. Nếu bạn thắng và lãi $150, lợi nhuận của bạn là 1.5R. Mọi thứ trong dự án này được tính toán bằng "R" thay vì số tiền cụ thể.

---

## 2. Thuật ngữ Dữ liệu & Học Máy (Machine Learning)

*   **Parquet (`.parquet`)**: Định dạng tệp dữ liệu lưu trữ cột, vượt trội hơn rất nhiều so với Excel hoặc CSV đối với Dữ liệu Lớn (Big Data). Nó nén kích thước mạnh mẽ trong khi cho phép tốc độ đọc cực nhanh.
*   **Data Pipeline (Đường ống dữ liệu)**: Quy trình từng bước làm sạch dữ liệu: Trích xuất Dữ liệu Tick thô -> Đồng bộ hóa thành Nến (OHLCV) -> Tính toán chỉ báo (Features) -> Chuẩn bị mục tiêu (Labels) cho AI.
*   **Features (Đặc trưng)**: Những điểm dữ liệu cụ thể bạn cung cấp cho AI. Để dự đoán giá, chúng tôi cung cấp cho AI bối cảnh như giá trị RSI hiện tại hoặc khoảng cách tới kháng cự. ML_FX sử dụng hơn 133 đặc trưng khác nhau.
*   **Labels (Nhãn)**: Những "câu trả lời" lịch sử (liệu giá tương lai đã tăng hay giảm) được sử dụng để huấn luyện mô hình. Trong quá trình Huấn luyện, AI phân tích các Đặc trưng để dự đoán Nhãn.
*   **KNN / XGBoost / LightGBM / LSTM**: Những mô hình Học máy khác nhau. KNN là đường cơ sở đơn giản. XGBoost và LightGBM là những mô hình cây quyết định mạnh mẽ tuyệt vời cho dữ liệu tài chính. LSTM là Mạng nơ-ron nhân tạo chuyên tìm các chuỗi mẫu trong chuỗi thời gian tuần tự.
*   **Optuna**: Một khuôn khổ tự động tối ưu hóa siêu tham số. Nó linh hoạt tìm kiếm cấu hình toán học tốt nhất cho các mô hình AI để bạn không cần đoán chúng một cách thủ công.

---

## 3. Thuật ngữ Công cụ

*   **Pixi**: Trình quản lý dự án hiện đại. Nó tự động tải xuống phiên bản Python chuẩn xác và tải toàn bộ các phần mềm độc lập (như Polars hoặc XGBoost) mà không gây nhầm lẫn môi trường hệ thống máy tính toàn cầu của bạn.
*   **Polars**: Một thư viện quản lý dữ liệu thế hệ mới được viết bằng Rust. Nó nhanh hơn nhiều so với Pandas, cho phép máy tính tiêu chuẩn xử lý hơn 10 năm dữ liệu tick (nửa tỷ hàng) rất hiệu quả.
