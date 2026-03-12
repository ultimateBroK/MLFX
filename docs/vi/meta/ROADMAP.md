# Lộ trình tài liệu MLFX

Tài liệu này tổng hợp định hướng cải tiến cho hệ thống tài liệu trong `docs/`, đóng vai trò như một **roadmap cấp chỉ mục** cho kế hoạch viết mới, tái cấu trúc, chuẩn hóa và bảo trì docs.

> Trạng thái hiện tại: roadmap này tập trung vào **tài liệu**, không phải roadmap tính năng của toàn bộ sản phẩm.

---

## Mục tiêu

Roadmap này giúp bạn:

- Theo dõi các hạng mục tài liệu đang có và còn thiếu
- Biết ưu tiên nên làm gì trước
- Phân biệt giữa:
  - Tài liệu cho người mới
  - Tài liệu hướng dẫn vận hành
  - Tài liệu tham chiếu
  - Tài liệu kiến trúc
  - Tài liệu meta / archive
- Giữ cấu trúc `docs/` ổn định khi repo tiếp tục phát triển

---

## Tài liệu liên quan

- [Kế hoạch tái cấu trúc docs](../../DOCS_RESTRUCTURE_PLAN.md)
- [README tiếng Việt](../README.md)
- [README gốc của docs](../../README.md)
- [Tracking thay đổi cũ](../../archive/DOCUMENTATION_IMPROVEMENT_TRACKING.md)

---

## Nguyên tắc ưu tiên

Ưu tiên được chia theo tác động:

### Ưu tiên cao
Các hạng mục ảnh hưởng trực tiếp đến khả năng đọc và điều hướng của người dùng:
- Cấu trúc thư mục rõ ràng
- Link điều hướng không bị gãy
- `README` dễ dùng
- Quickstart canonical
- Song ngữ đối xứng

### Ưu tiên trung bình
Các hạng mục giúp tài liệu đầy đủ và chuyên nghiệp hơn:
- Bổ sung tài liệu còn thiếu
- Tách nội dung bị trùng lặp
- Chuẩn hóa naming và breadcrumb
- Hoàn thiện cross-link giữa các file

### Ưu tiên thấp
Các hạng mục tối ưu hóa lâu dài:
- Archive tài liệu cũ
- Guideline đóng góp docs
- Checklist review docs
- Governance cho maintainers

---

## Trạng thái theo nhóm tài liệu

## 1. Entry points / điều hướng

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `docs/README.md` làm hub tổng | [ ] | Cần duy trì như cổng điều hướng song ngữ |
| `docs/vi/README.md` | [ ] | Nên là hub tiếng Việt riêng |
| `docs/en/README.md` | [~] | Có sẵn nhưng cần chuẩn hóa theo cấu trúc mới |
| Breadcrumb và link quay lại hub | [ ] | Cần thêm đồng bộ ở các file |

---

## 2. Getting started

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `QUICKSTART.md` tiếng Việt | [ ] | Nên là nguồn quickstart canonical |
| `QUICKSTART.md` tiếng Anh | [ ] | Nên song hành với bản tiếng Việt |
| `NOOB_GUIDE.md` tập trung vào “vì sao” | [~] | Nội dung tốt, nhưng cần giảm trùng với quickstart |
| Luồng đọc cho người mới | [ ] | Nên rõ: README → QUICKSTART → NOOB_GUIDE |

---

## 3. Guides

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `USAGE_GUIDE.md` tiếng Việt | [~] | Đầy đủ, nhưng còn lặp quickstart |
| `USAGE_GUIDE.md` tiếng Anh | [~] | Cần kiểm tra lại link và cấu trúc |
| `EVALUATION_GUIDE.md` | [x] | Đã có ở cả hai ngôn ngữ |
| `TROUBLESHOOTING.md` | [x] | Đã có ở cả hai ngôn ngữ |

---

## 4. Reference

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `FEATURE_REFERENCE.md` tiếng Việt | [x] | Đã có |
| `FEATURE_REFERENCE.md` tiếng Anh | [x] | Đã có |
| `CONFIG_REFERENCE.md` tiếng Việt | [ ] | Còn thiếu, cần bổ sung |
| `CONFIG_REFERENCE.md` tiếng Anh | [x] | Đã có |
| `API_REFERENCE.md` tiếng Việt | [ ] | Còn thiếu, cần bổ sung |
| `API_REFERENCE.md` tiếng Anh | [x] | Đã có |
| `GLOSSARY.md` tiếng Việt | [x] | Đã có |
| `GLOSSARY.md` tiếng Anh | [x] | Đã có |

---

## 5. Architecture

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `ARCHITECTURE.md` tiếng Việt | [x] | Đã có |
| `ARCHITECTURE.md` tiếng Anh | [x] | Đã có |
| `BACKEND_COMPARISON.md` tiếng Việt | [ ] | Nên tạo mới |
| `BACKEND_COMPARISON.md` tiếng Anh | [ ] | Nên tạo mới |

---

## 6. Meta / maintenance

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Roadmap docs tiếng Việt | [x] | File hiện tại |
| Roadmap docs tiếng Anh | [~] | Đã có file roadmap, nên chuẩn hóa vai trò |
| Tracking migration cũ | [x] | Đưa về `archive/` |
| Governance / contributing for docs | [ ] | Nên bổ sung sau khi cấu trúc ổn định |

---

## 7. Archive

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| `archive/` cho tài liệu lịch sử | [ ] | Nên là nơi chứa tracking và tài liệu cũ |
| `legacy/` cho file không còn active | [ ] | Chỉ dùng khi thực sự cần |
| Loại bỏ hoặc thay thế `storings/` | [ ] | Tên cũ không rõ nghĩa |

---

## Mốc triển khai đề xuất

## Phase 1 — Ổn định cấu trúc thư mục
Mục tiêu:
- hoàn tất mô hình `docs/{lang}/{category}/`
- đưa tài liệu tiếng Việt khỏi root `docs/`
- phân nhóm `getting-started`, `guides`, `reference`, `architecture`, `meta`, `archive`

Kết quả mong đợi:
- cấu trúc dễ hiểu hơn ngay lập tức
- giảm sự lẫn lộn giữa user docs và meta docs

---

## Phase 2 — Chuẩn hóa điều hướng
Mục tiêu:
- Viết lại `README` tổng
- Tạo `README` tiếng Việt rõ ràng
- Tạo `QUICKSTART.md` cho cả hai ngôn ngữ
- Thêm breadcrumb và “đọc tiếp / see also”

Kết quả mong đợi:
- Người mới vào repo biết bắt đầu từ đâu
- Giảm việc lặp quickstart trong nhiều file

---

## Phase 3 — Lấp tài liệu còn thiếu
Mục  tiêu:
- Tạo `CONFIG_REFERENCE.md` tiếng Việt
- Tạo `API_REFERENCE.md` tiếng Việt
- Tạo `BACKEND_COMPARISON.md` cho cả `vi` và `en`

Kết quả mong đợi:
- Reference docs đầy đủ hơn
- Hỗ trợ tốt hơn cho việc chọn backend và tích hợp API

---

## Phase 4 — Giảm trùng lặp nội dung
Mục tiêu:
- Rút quickstart khỏi `USAGE_GUIDE.md`
- Giữ `NOOB_GUIDE.md` đúng vai trò nhập môn
- Làm `README` gọn và chủ yếu là navigation

Kết quả mong đợi:
- Mỗi file có một nhiệm vụ rõ ràng
- Giảm chi phí bảo trì khi nội dung thay đổi

---

## Phase 5 — Governance và bảo trì dài hạn
Mục tiêu:
- Thêm quy ước viết docs
- Thêm checklist review docs
- Thêm nguyên tắc sync song ngữ
- Xác định quy trình archive

Kết quả mong đợi:
- Tránh tài liệu bị lệch cấu trúc trở lại
- Dễ maintain khi repo tiếp tục lớn lên

---

## Backlog đề xuất

### Backlog gần hạn
- [ ] Tạo `docs/vi/README.md`
- [ ] Tạo `docs/vi/getting-started/QUICKSTART.md`
- [ ] Tạo `docs/en/getting-started/QUICKSTART.md`
- [ ] Cập nhật link trong các file đã di chuyển
- [ ] Chuẩn hóa `docs/README.md`

### Backlog tiếp theo
- [ ] Viết `docs/vi/reference/CONFIG_REFERENCE.md`
- [ ] Viết `docs/vi/reference/API_REFERENCE.md`
- [ ] Viết `docs/vi/architecture/BACKEND_COMPARISON.md`
- [ ] Viết `docs/en/architecture/BACKEND_COMPARISON.md`

### Backlog dài hạn
- [ ] Tạo `docs/CONTRIBUTING.md`
- [ ] Thêm quy ước breadcrumb cho toàn bộ docs
- [ ] Thêm checklist kiểm tra link markdown
- [ ] Chuẩn hóa archive policy

---

## Tiêu chí hoàn thành roadmap giai đoạn này

Giai đoạn tái cấu trúc docs được xem là đạt khi:

- Toàn bộ docs được tổ chức nhất quán theo `ngôn ngữ → nhóm tài liệu`
- `README` tổng và README theo ngôn ngữ đều hoạt động như hub điều hướng
- Quickstart có một nguồn canonical duy nhất
- Các file reference quan trọng có đủ ở cả `vi` và `en`
- Architecture docs có cặp song ngữ rõ ràng
- Các file tracking cũ được chuyển khỏi khu user-facing docs
- Link nội bộ hoạt động ổn định

---

## Quy ước trạng thái

- `[x]` Hoàn thành
- `[~]` Đã có một phần / cần chuẩn hóa thêm
- `[ ]` Chưa làm

---

## Ghi chú bảo trì

- Nếu roadmap này không còn là nơi theo dõi active work, nên chuyển nó vào `archive/`.
- Nếu roadmap docs trở thành một phần của roadmap chung toàn repo, nên giữ file này như một **index chuyên cho tài liệu**, và link ra roadmap tổng ở project root.

---

*Cập nhật khi có thay đổi lớn về cấu trúc hoặc ưu tiên tài liệu.*
