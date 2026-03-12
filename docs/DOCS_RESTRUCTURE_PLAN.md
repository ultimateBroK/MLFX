# Kế hoạch tái cấu trúc nội dung và cây thư mục `docs/`

## 1. Mục tiêu

Tái cấu trúc lại tài liệu trong `docs/` để:
- Dễ tìm hơn theo **ngôn ngữ → mục đích → chủ đề**
- Giảm trùng lặp nội dung giữa `README`, `NOOB_GUIDE`, `USAGE_GUIDE`
- Tách rõ **user docs**, **reference docs**, **developer/internal docs**, **archive**
- Đưa cấu trúc song ngữ về trạng thái **đối xứng và dễ bảo trì**
- Tạo nền cho việc mở rộng thêm tài liệu mới mà không làm thư mục gốc bị lộn xộn

---

## 2. Đánh giá hiện trạng

### 2.1 Cây thư mục hiện tại

```/dev/null/docs-current-tree.txt#L1-24
docs/
├── ARCHITECTURE.md
├── DOCUMENTATION_IMPROVEMENT_TRACKING.md
├── EVALUATION_GUIDE.md
├── FEATURE_REFERENCE.md
├── GLOSSARY.md
├── NOOB_GUIDE.md
├── README.md
├── TROUBLESHOOTING.md
├── USAGE_GUIDE.md
├── en/
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── CONFIG_REFERENCE.md
│   ├── EVALUATION_GUIDE.md
│   ├── FEATURE_REFERENCE.md
│   ├── GLOSSARY.md
│   ├── NOOB_GUIDE.md
│   ├── README.md
│   ├── ROADMAP.md
│   ├── TROUBLESHOOTING.md
│   └── USAGE_GUIDE.md
└── storings/
```

### 2.2 Vấn đề chính

1. **Thư mục gốc đang đóng vai trò như docs tiếng Việt**, nhưng lại không nằm trong `vi/`.
2. **Song ngữ chưa đối xứng**:
   - `docs/en/` có `API_REFERENCE.md`, `CONFIG_REFERENCE.md`, `ROADMAP.md`
   - Phía tiếng Việt chưa có cấu trúc tương ứng
3. **Tên file theo “guide/reference” ổn**, nhưng chưa được gom theo nhóm chủ đề.
4. **Nội dung bị chồng lấn**:
   - `README.md`
   - `NOOB_GUIDE.md`
   - `USAGE_GUIDE.md`
5. Có tài liệu mang tính **tracking / roadmap / internal maintenance** đang nằm chung với user-facing docs.
6. `storings/` đang để trống, tên thư mục cũng chưa rõ nghĩa bằng `archive/`.

---

## 3. Nguyên tắc tái cấu trúc

### 3.1 Nguyên tắc tổ chức

- Tổ chức theo thứ tự ưu tiên:
  1. **ngôn ngữ**
  2. **loại tài liệu**
  3. **chủ đề**
- Mỗi file nên có **một vai trò rõ ràng**.
- `README.md` chỉ làm nhiệm vụ **entrypoint / navigation / quick orientation**.
- Nội dung tham chiếu chi tiết phải nằm trong các file `reference` hoặc `guides` chuyên biệt.
- Tài liệu roadmap, tracking, audit cũ phải tách khỏi user docs.

### 3.2 Nguyên tắc nội dung

- **Không lặp lại quickstart đầy đủ ở 3 nơi**.
- `NOOB_GUIDE` trả lời câu hỏi: **“vì sao phải làm bước này?”**
- `USAGE_GUIDE` trả lời câu hỏi: **“chạy lệnh nào, tham số nào?”**
- `ARCHITECTURE` trả lời câu hỏi: **“hệ thống vận hành ra sao?”**
- `REFERENCE` trả lời câu hỏi: **“field/flag/api/config nghĩa là gì?”**
- `TROUBLESHOOTING` chỉ chứa lỗi, triệu chứng, nguyên nhân, cách xử lý.

---

## 4. Đề xuất cấu trúc cây thư mục mới

## Phương án khuyến nghị

```/dev/null/docs-target-tree.txt#L1-45
docs/
├── README.md
├── en/
│   ├── README.md
│   ├── getting-started/
│   │   ├── NOOB_GUIDE.md
│   │   └── QUICKSTART.md
│   ├── guides/
│   │   ├── USAGE_GUIDE.md
│   │   ├── EVALUATION_GUIDE.md
│   │   └── TROUBLESHOOTING.md
│   ├── reference/
│   │   ├── FEATURE_REFERENCE.md
│   │   ├── CONFIG_REFERENCE.md
│   │   ├── API_REFERENCE.md
│   │   └── GLOSSARY.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   └── BACKEND_COMPARISON.md
│   └── meta/
│       └── ROADMAP.md
├── vi/
│   ├── README.md
│   ├── getting-started/
│   │   ├── NOOB_GUIDE.md
│   │   └── QUICKSTART.md
│   ├── guides/
│   │   ├── USAGE_GUIDE.md
│   │   ├── EVALUATION_GUIDE.md
│   │   └── TROUBLESHOOTING.md
│   ├── reference/
│   │   ├── FEATURE_REFERENCE.md
│   │   ├── CONFIG_REFERENCE.md
│   │   ├── API_REFERENCE.md
│   │   └── GLOSSARY.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   └── BACKEND_COMPARISON.md
│   └── meta/
│       └── ROADMAP.md
└── archive/
    ├── DOCUMENTATION_IMPROVEMENT_TRACKING.md
    └── legacy/
```

### Vì sao chọn cấu trúc này

- Dễ scale khi thêm tài liệu mới.
- Song ngữ đối xứng hoàn toàn.
- Phân tách rõ:
  - `getting-started`: nhập môn
  - `guides`: hướng dẫn thao tác
  - `reference`: tra cứu
  - `architecture`: thiết kế hệ thống
  - `meta`: kế hoạch / trạng thái
  - `archive`: tài liệu lịch sử

---

## 5. Mapping từ hiện trạng sang cấu trúc mới

| Hiện tại | Đề xuất mới | Hành động |
|---|---|---|
| `docs/README.md` | `docs/README.md` | Giữ, viết lại thành cổng điều hướng song ngữ rõ hơn |
| `docs/NOOB_GUIDE.md` | `docs/vi/getting-started/NOOB_GUIDE.md` | Di chuyển + chỉnh nội dung |
| `docs/USAGE_GUIDE.md` | `docs/vi/guides/USAGE_GUIDE.md` | Di chuyển + giảm trùng lặp |
| `docs/EVALUATION_GUIDE.md` | `docs/vi/guides/EVALUATION_GUIDE.md` | Di chuyển |
| `docs/TROUBLESHOOTING.md` | `docs/vi/guides/TROUBLESHOOTING.md` | Di chuyển |
| `docs/FEATURE_REFERENCE.md` | `docs/vi/reference/FEATURE_REFERENCE.md` | Di chuyển |
| `docs/GLOSSARY.md` | `docs/vi/reference/GLOSSARY.md` | Di chuyển |
| `docs/ARCHITECTURE.md` | `docs/vi/architecture/ARCHITECTURE.md` | Di chuyển |
| `docs/DOCUMENTATION_IMPROVEMENT_TRACKING.md` | `docs/archive/DOCUMENTATION_IMPROVEMENT_TRACKING.md` | Lưu archive |
| `docs/en/README.md` | `docs/en/README.md` | Giữ, viết lại navigation theo cấu trúc mới |
| `docs/en/NOOB_GUIDE.md` | `docs/en/getting-started/NOOB_GUIDE.md` | Di chuyển |
| `docs/en/USAGE_GUIDE.md` | `docs/en/guides/USAGE_GUIDE.md` | Di chuyển |
| `docs/en/EVALUATION_GUIDE.md` | `docs/en/guides/EVALUATION_GUIDE.md` | Di chuyển |
| `docs/en/TROUBLESHOOTING.md` | `docs/en/guides/TROUBLESHOOTING.md` | Di chuyển |
| `docs/en/FEATURE_REFERENCE.md` | `docs/en/reference/FEATURE_REFERENCE.md` | Di chuyển |
| `docs/en/GLOSSARY.md` | `docs/en/reference/GLOSSARY.md` | Di chuyển |
| `docs/en/CONFIG_REFERENCE.md` | `docs/en/reference/CONFIG_REFERENCE.md` | Di chuyển |
| `docs/en/API_REFERENCE.md` | `docs/en/reference/API_REFERENCE.md` | Di chuyển |
| `docs/en/ARCHITECTURE.md` | `docs/en/architecture/ARCHITECTURE.md` | Di chuyển |
| `docs/en/ROADMAP.md` | `docs/en/meta/ROADMAP.md` | Di chuyển |
| `docs/storings/` | `docs/archive/legacy/` | Đổi tên hoặc loại bỏ |

---

## 6. Kế hoạch tái cấu trúc nội dung

## 6.1 `docs/README.md`

### Vai trò mới
- Landing page cho toàn bộ docs
- Chọn ngôn ngữ
- Chỉ tới các luồng đọc phổ biến

### Nội dung nên có
- Giới thiệu ngắn về MLFX docs
- Chọn `English` / `Tiếng Việt`
- 3 lối vào chính:
  - Mới bắt đầu
  - Vận hành CLI
  - Tra cứu kỹ thuật
- Sơ đồ cây docs ngắn gọn

### Không nên chứa
- Quickstart quá dài
- Giải thích chi tiết từng command

---

## 6.2 `QUICKSTART.md` mới ở cả `en` và `vi`

### Lý do thêm file này
Hiện Quickstart đang bị rải ở nhiều file. Nên gom về một nơi canonical.

### Nội dung
- 4 bước chuẩn:
  - `download`
  - `pipeline`
  - `train`
  - `evaluate`
- Kết quả mong đợi sau mỗi bước
- Link sang `NOOB_GUIDE` và `USAGE_GUIDE`

### Tác động
- `README` chỉ giữ bản rút gọn
- `NOOB_GUIDE` bỏ phần copy-paste command quá dài
- `USAGE_GUIDE` chỉ liên kết sang `QUICKSTART.md`

---

## 6.3 `NOOB_GUIDE.md`

### Vai trò mới
Tập trung vào tư duy và workflow cho người mới.

### Nên giữ
- Dự án này làm gì
- Vì sao workflow phải đi đúng thứ tự
- Dữ liệu chảy qua các tầng ra sao
- Sau mỗi bước sẽ thấy gì trong thư mục nào

### Nên bỏ / rút gọn
- Command reference chi tiết
- Listing dài các flag CLI

---

## 6.4 `USAGE_GUIDE.md`

### Vai trò mới
Manual vận hành CLI đầy đủ.

### Nên giữ
- Command-by-command usage
- Tham số chính
- Artifact sinh ra
- Ví dụ thực tế

### Nên bỏ / rút gọn
- Giải thích nhập môn dài dòng
- Lặp lại toàn bộ Quickstart nếu đã có `QUICKSTART.md`

---

## 6.5 `ARCHITECTURE.md`

### Vai trò mới
Tài liệu thiết kế kỹ thuật chuẩn.

### Nên giữ
- Data flow
- Training layer
- Experiment tracking
- Model registry
- Evaluation layer
- Serving layer

### Nên mở rộng thêm
- Config loading flow
- Inference path ở serving
- Dependency map dễ đọc hơn
- Boundaries giữa các package trong `mlfx/`

---

## 6.6 `REFERENCE` docs

### `FEATURE_REFERENCE.md`
- Tiếp tục là nơi canonical cho cột dữ liệu

### `CONFIG_REFERENCE.md`
- Cần có ở cả `en` và `vi`
- Tách hẳn khỏi `USAGE_GUIDE`

### `API_REFERENCE.md`
- Cần có ở cả `en` và `vi`
- Nếu API chưa ổn định, ghi rõ version/status

### `GLOSSARY.md`
- Gọn, dễ scan, thống nhất thuật ngữ song ngữ

---

## 6.7 `BACKEND_COMPARISON.md` mới

### Lý do nên thêm
Hiện backend được liệt kê ở nhiều nơi nhưng thiếu tài liệu giúp chọn backend.

### Nên có
- Bảng so sánh `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`
- Use case phù hợp
- Ưu/nhược điểm
- Chi phí tài nguyên
- Thời gian train tương đối
- Mức độ production-readiness

---

## 6.8 `meta/ROADMAP.md`

### Vai trò
- Dành cho kế hoạch docs hoặc project-facing roadmap
- Không để lẫn với user help docs

### Gợi ý
Nếu roadmap là tài liệu của toàn dự án chứ không chỉ docs, cân nhắc chuyển hẳn ra project root thay vì giữ trong `docs/`.

---

## 6.9 `archive/`

### Mục đích
- Lưu tài liệu mang tính lịch sử / migration notes / tracking cũ
- Tránh xóa mất ngữ cảnh thay đổi

### Nên đưa vào đây
- `DOCUMENTATION_IMPROVEMENT_TRACKING.md`
- Các file audit/report không còn là tài liệu vận hành chính
- Nội dung của `storings/` nếu sau này dùng lại

---

## 7. Khoảng trống nội dung cần bổ sung

Dựa trên hiện trạng, các file sau nên được tạo để hoàn thiện cấu trúc:

### Tiếng Việt còn thiếu
- `docs/vi/reference/CONFIG_REFERENCE.md`
- `docs/vi/reference/API_REFERENCE.md`
- `docs/vi/architecture/BACKEND_COMPARISON.md`
- `docs/vi/getting-started/QUICKSTART.md`
- `docs/vi/meta/ROADMAP.md` hoặc link tới roadmap chung

### Tiếng Anh còn nên chuẩn hóa
- `docs/en/getting-started/QUICKSTART.md`
- `docs/en/architecture/BACKEND_COMPARISON.md`
- Rà lại link trong `docs/en/README.md` vì hiện còn dấu vết `TODO.md`

---

## 8. Thứ tự triển khai đề xuất

## Phase 1 — Sửa cấu trúc mà ít đụng nội dung

1. Tạo các thư mục mới:
   - `docs/vi/`
   - `docs/en/getting-started/`
   - `docs/en/guides/`
   - `docs/en/reference/`
   - `docs/en/architecture/`
   - `docs/en/meta/`
   - `docs/vi/getting-started/`
   - `docs/vi/guides/`
   - `docs/vi/reference/`
   - `docs/vi/architecture/`
   - `docs/vi/meta/`
   - `docs/archive/`
2. Di chuyển file theo mapping.
3. Đổi `storings/` thành `archive/legacy/` hoặc bỏ nếu không dùng.
4. Cập nhật toàn bộ link tương đối.

### Kết quả mong đợi
- Cây thư mục sạch hơn ngay
- Chưa cần rewrite nhiều

---

## Phase 2 — Chuẩn hóa entrypoints nội dung

1. Viết lại `docs/README.md`
2. Viết `docs/en/README.md` và `docs/vi/README.md` theo cùng một format
3. Tạo `QUICKSTART.md` cho cả 2 ngôn ngữ
4. Rút phần Quickstart dư thừa khỏi:
   - `NOOB_GUIDE.md`
   - `USAGE_GUIDE.md`

### Kết quả mong đợi
- User vào docs sẽ biết bắt đầu từ đâu
- Giảm trùng lặp rõ rệt

---

## Phase 3 — Lấp khoảng trống tài liệu

1. Tạo bản tiếng Việt cho:
   - `CONFIG_REFERENCE.md`
   - `API_REFERENCE.md`
2. Tạo `BACKEND_COMPARISON.md` cho cả `en` và `vi`
3. Kiểm tra song ngữ đối xứng 1-1

### Kết quả mong đợi
- Tài liệu hai ngôn ngữ đồng đều hơn
- Phần reference hoàn chỉnh

---

## Phase 4 — Archive và governance

1. Chuyển các file tracking / migration notes vào `archive/`
2. Thêm quy ước đóng góp docs, ví dụ:
   - Mọi file mới phải đặt đúng nhóm
   - Mọi file `guide` phải link ngược về `README`
   - Nội dung song ngữ phải có mapping rõ ràng
3. Có thể thêm `docs/CONTRIBUTING.md` nếu tài liệu sẽ tiếp tục mở rộng mạnh

---

## 9. Quy ước đặt tên và điều hướng

### Quy ước tên file
- Giữ tên tiếng Anh đồng nhất cho cả hai ngôn ngữ để dễ mapping:
  - `NOOB_GUIDE.md`
  - `USAGE_GUIDE.md`
  - `FEATURE_REFERENCE.md`
- Không đổi tên file sang tiếng Việt có dấu.

### Quy ước breadcrumb điều hướng
Mỗi file nên có phần đầu ngắn:
- Ngôn ngữ
- Nhóm tài liệu
- Link quay lại `README`

Ví dụ:
- `Docs > Tiếng Việt > Guides > Usage Guide`
- `Docs > English > Reference > API Reference`

### Quy ước link chéo
Mỗi file nên có mục `Đọc tiếp / See also` ở cuối.

---

## 10. Rủi ro khi tái cấu trúc

### 10.1 Gãy link nội bộ
- Xảy ra khi move file mà không cập nhật relative links
- Cần grep toàn bộ markdown links sau khi move

### 10.2 Gãy link từ README root hoặc external references
- Nếu repo root đang trỏ trực tiếp tới `docs/NOOB_GUIDE.md` thì sẽ hỏng sau khi move sang `docs/vi/...`
- Cần rà toàn repo, không chỉ trong `docs/`

### 10.3 Song ngữ lệch dần theo thời gian
- Nếu không có quy ước maintain, `en` và `vi` sẽ lại diverge
- Nên thêm checklist review docs

### 10.4 Di chuyển quá mạnh trước khi chuẩn hóa nội dung
- Nếu move hết trước nhưng chưa có `README` và `QUICKSTART` mới, trải nghiệm đọc có thể tệ hơn tạm thời
- Vì vậy nên theo phase

---

## 11. Checklist nghiệm thu

## Về cấu trúc
- [ ] không còn docs tiếng Việt nằm trực tiếp ở `docs/` ngoại trừ `docs/README.md`
- [ ] `en/` và `vi/` có cấu trúc đối xứng
- [ ] `storings/` đã được đổi tên hoặc loại bỏ
- [ ] file tracking cũ đã chuyển sang `archive/`

## Về nội dung
- [ ] `README` không còn ôm quá nhiều nội dung chi tiết
- [ ] `QUICKSTART` là nguồn Quickstart canonical
- [ ] `NOOB_GUIDE` không còn thành command reference thứ hai
- [ ] `USAGE_GUIDE` không còn lặp lại giải thích nhập môn dài
- [ ] `CONFIG_REFERENCE` và `API_REFERENCE` có ở cả `en` và `vi`
- [ ] có `BACKEND_COMPARISON` cho quyết định chọn backend

## Về điều hướng
- [ ] tất cả markdown links hoạt động
- [ ] mỗi file có link quay lại hub gần nhất
- [ ] root `docs/README.md` đủ để dẫn user vào đúng nhánh đọc

---

## 12. Kết luận ngắn

Nếu chỉ chọn **một hướng tái cấu trúc tốt nhất**, tôi khuyến nghị:

1. Chuyển docs hiện tại sang mô hình **`docs/{lang}/{category}/file.md`**
2. Thêm `QUICKSTART.md` làm nguồn Quickstart duy nhất
3. Tách `reference`, `guides`, `architecture`, `meta`, `archive`
4. Đưa toàn bộ docs tiếng Việt từ root vào `docs/vi/`
5. Hoàn thiện các file còn thiếu ở tiếng Việt và file so sánh backend

Đây là hướng cân bằng tốt giữa:
- Khả năng đọc cho user
- Khả năng maintain cho bạn
- Khả năng mở rộng docs về sau

---

## 13. Đề xuất file đầu ra

File này phù hợp để lưu tại:
- `docs/DOCS_RESTRUCTURE_PLAN.md` nếu muốn đặt cùng khu docs hiện tại
- Hoặc `docs/archive/DOCS_RESTRUCTURE_PLAN.md` nếu chỉ dùng như tài liệu planning tạm thời

Khuyến nghị thực tế: lưu ở `docs/DOCS_RESTRUCTURE_PLAN.md` trong giai đoạn triển khai, sau đó chuyển vào `archive/` khi hoàn tất.
