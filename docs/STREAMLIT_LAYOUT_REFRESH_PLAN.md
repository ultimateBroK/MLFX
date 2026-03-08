# Kế hoạch làm mới giao diện Streamlit cho Trader

> Áp dụng **using-streamlit-layouts**: Sidebar chỉ navigation + global filters, Main content rõ ràng, containers có mục đích, Progressive Disclosure.

---

## 1. Phân tích hiện trạng

### 1.1 Cấu trúc hiện tại

| Thành phần | Hiện tại | Vấn đề |
|------------|----------|--------|
| **Sidebar** | Progress, Quick Nav, Global Settings, Danger Zone | Quá nhiều nội dung; Global Settings chưa phải filter thực sự |
| **Main** | 5 bước workflow (Data Loading → Export Reports) | Mỗi step có form dài, thiếu nhóm logic |
| **Navigation** | 5 cột `st.columns` + Previous/Next | 5 cột hơi chật (skill: max 4 columns) |
| **Steps** | Form + button trực tiếp | Thiếu `st.container(border=True)`, `st.expander` cho "Nâng cao" |

### 1.2 Đối tượng: Trader

- Cần **symbol, timeframe, label** luôn thấy rõ (global filters)
- Cần **metrics** nổi bật (KPI cards)
- Cần **biểu đồ** inline, không phải mở file
- Cần **Progressive Disclosure**: cơ bản trước, nâng cao ẩn trong expander

---

## 2. Nguyên tắc layout (theo using-streamlit-layouts)

| Nguyên tắc | Áp dụng |
|------------|---------|
| **Sidebar: navigation + global filters only** | Symbol, TF, Label, Date range; không đặt charts/tables |
| **Columns: max 4** | Giảm workflow bar từ 5 → 4 cột hoặc dùng horizontal container |
| **Horizontal containers** | Button groups (Cancel/Save/Submit) thay vì columns |
| **Bordered containers** | Nhóm form, KPI cards, chart sections |
| **Tabs** | Chart vs Data trong Visual Analysis; form sections |
| **Expander** | "Nâng cao" (concurrency, force re-verify, QA, drift) |
| **Popover** | Settings nhỏ (font size, dark mode) nếu cần |
| **Dialog** | Confirm reset workflow, confirm delete |
| **Spacing** | `st.space()`, `gap` trên containers |
| **Width/height** | `height="stretch"` cho chart containers cạnh nhau |

---

## 3. Kế hoạch chi tiết

### Phase 1: Sidebar tối ưu

**Mục tiêu**: Sidebar chỉ chứa navigation + global filters.

| Thay đổi | Chi tiết |
|----------|----------|
| **Global filters** | `symbol`, `tf`, `label_col` dùng `st.selectbox`/`st.text_input` — lưu vào `st.session_state` |
| **Date range** | `st.date_input` cho phạm vi dữ liệu (dùng chung các bước) |
| **Quick Navigation** | Giữ 5 nút bước, dùng `use_container_width=True` |
| **Nâng cao** | `st.expander("Nâng cao")` chứa: QA, drift, batch-predict (ghi chú/placeholder) |
| **App info** | `st.caption("App v1.x")` ở cuối sidebar |
| **Danger Zone** | Chuyển "Reset Workflow" vào `@st.dialog` confirm thay vì button trực tiếp |

**File**: `layout.py` — `render_sidebar()`

---

### Phase 2: Main content — cấu trúc từng step

#### 2.1 Data Loading

| Thành phần | Layout |
|------------|--------|
| Header | `navigation.render_step_header()` (giữ) |
| Mode | `st.radio` horizontal (giữ) |
| Form chính | `st.container(border=True)` — symbol, date range |
| Form phụ | `st.columns(2)` cho Start/End date vs Concurrency/Options |
| Nâng cao | `st.expander("Tùy chọn nâng cao")` — force re-verify, skip current month |
| Buttons | `st.container(horizontal=True, horizontal_alignment="center")` — "Start Data Loading" |

#### 2.2 Data Preparation

| Thành phần | Layout |
|------------|--------|
| Form | `st.container(border=True)` — symbol, tf, pivot, label |
| Checkboxes | `st.container(gap="small")` — resample, features, labels |
| Nâng cao | `st.expander("Pivot / Anchor nâng cao")` |
| Button | Horizontal container center |

#### 2.3 Model Training

| Thành phần | Layout |
|------------|--------|
| Form | `st.container(border=True)` — backend, n_trials, n_splits |
| KPI sau train | `st.columns(2)` hoặc `st.columns(4)` — best_cv_f1_macro, loss, ... (max 4) |
| Nâng cao | `st.expander("Hyperparameter nâng cao")` |

#### 2.4 Visual Analysis

| Thành phần | Layout |
|------------|--------|
| Tabs | `st.tabs(["Market Overview", "Trade Analysis", "Model Insights", "Risk"])` (giữ) |
| Mỗi tab | `st.container(border=True, height="stretch")` cho chart |
| Date range | Trong tab hoặc sidebar (global) |
| KPI cards | `st.columns(4)` — Win Rate, Sharpe, Net R, Total Trades |

#### 2.5 Export Reports

| Thành phần | Layout |
|------------|--------|
| Options | `st.container(border=True)` — format, path |
| Preview | `st.expander("Xem trước")` nếu có |
| Button | Horizontal container |

---

### Phase 3: Workflow navigation bar

**Vấn đề**: 5 cột quá chật (skill: max 4 columns).

**Giải pháp**:

- **Option A**: Gom 5 bước thành 4 (Visual Analysis + Export Reports → "Results & Export")
- **Option B**: Dùng `st.container(horizontal=True, horizontal_alignment="distribute")` cho 5 step pills, mỗi pill là 1 div nhỏ
- **Option C**: Giữ 5 cột nhưng dùng `st.columns(5, vertical_alignment="center")` và rút gọn text (chỉ icon + title ngắn)

**Đề xuất**: Option B — horizontal container với pills, responsive hơn.

---

### Phase 4: KPI & Metrics cho Trader

| Vị trí | Metrics |
|--------|---------|
| **Data Loading** | Số tháng đã tải, phạm vi date |
| **Data Preparation** | Số rows, số features, label distribution |
| **Model Training** | best_cv_f1_macro, best trial, thời gian train |
| **Visual Analysis** | Win Rate, Sharpe, Net R, Total Trades, Max DD |
| **Export** | Đường dẫn file, kích thước |

**Cách hiển thị**: `st.metric()` trong `st.columns(2)` hoặc `st.columns(4)` (max 4), bọc trong `st.container(border=True)`.

---

### Phase 5: Dialogs & Progressive Disclosure

| Tính năng | Cách làm |
|-----------|----------|
| Reset Workflow | `@st.dialog("Confirm reset")` — nội dung confirm, nút Delete |
| Nâng cao (mọi step) | `st.expander("Nâng cao")` cho options ít dùng |
| Settings nhỏ | `st.popover("Settings")` nếu cần (font, theme) |

---

### Phase 6: Spacing & Visual polish

| Áp dụng | Chi tiết |
|---------|----------|
| `st.space("medium")` | Giữa sections |
| `gap="small"` | Trong list checkboxes |
| `height="stretch"` | Chart containers cạnh nhau (2 cột) |
| `width="content"` | Container cho button group nhỏ |

---

## 4. Thứ tự triển khai

| # | Phase | Ưu tiên | Effort |
|---|-------|---------|--------|
| 1 | Sidebar: global filters + expander Nâng cao | Cao | 1–2h |
| 2 | Reset Workflow → Dialog | Cao | 0.5h |
| 3 | Data Loading: bordered container + expander | Cao | 1h |
| 4 | Data Preparation, Model Training: cùng pattern | Trung bình | 1–2h |
| 5 | Visual Analysis: KPI cards + container stretch | Cao | 1h |
| 6 | Workflow nav: horizontal container (5 pills) | Trung bình | 1h |
| 7 | Export Reports: bordered + expander | Thấp | 0.5h |
| 8 | Spacing, gap, polish | Thấp | 0.5h |

---

## 5. Checklist theo using-streamlit-layouts

- [ ] Sidebar chỉ có: global filters (symbol, tf, label, date), quick nav, app info, expander Nâng cao
- [ ] Không đặt chart/table/dataframe trong sidebar
- [ ] Columns tối đa 4; nếu cần 5 → dùng horizontal container
- [ ] Button groups dùng `st.container(horizontal=True)`
- [ ] Form sections bọc trong `st.container(border=True)`
- [ ] Options ít dùng trong `st.expander`
- [ ] Confirm actions dùng `@st.dialog`
- [ ] KPI dùng `st.metric()` trong bordered container
- [ ] Chart containers dùng `height="stretch"` khi 2 cột
- [ ] Spacing: `st.space()`, `gap` trên container

---

## 6. File cần sửa

| File | Thay đổi |
|------|----------|
| `layout.py` | `render_sidebar()`: global filters, expander, dialog reset |
| `navigation.py` | `render_navigation()`: horizontal container thay 5 columns |
| `steps/data_loading.py` | Bordered container, expander, horizontal button |
| `steps/data_preparation.py` | Bordered container, expander |
| `steps/model_training.py` | Bordered container, KPI columns, expander |
| `steps/visual_analysis.py` | KPI cards, container stretch cho charts |
| `steps/export_reports.py` | Bordered container, expander |
| `assets/workflow_styles.css` | (Tùy chọn) style cho pills, bordered sections |

---

## 7. Tham chiếu

- Skill: `using-streamlit-layouts`
- Plan gốc: `docs/STREAMLIT_UI_PLAN.md`
- Design system: Glassmorphism Emerald AMOLED (`assets/glass_emerald.css`)
