# Kế hoạch: Streamlit UI thay thế TUI

> Áp dụng **ml-pipeline-workflow**: Progressive Disclosure, observability tại mỗi stage, Model Validation (so sánh baseline). Streamlit khắc phục hạn chế TUI: không xem biểu đồ inline, chỉ text log, terminal-only.

## Hạn chế TUI hiện tại

| Hạn chế | TUI (Textual) | Streamlit |
|---------|---------------|-----------|
| Xem biểu đồ backtest | Chỉ đường dẫn file, phải mở thủ công | Embed Plotly/HTML inline |
| Metrics | Text log | `st.metric()`, bảng trực quan |
| Môi trường | Terminal | Browser, dễ chia sẻ |
| Progressive Disclosure | Tất cả form cùng lúc | `st.expander` cho "Nâng cao" |
| Progress feedback | Text "Step 1/3..." | `st.progress`, spinner |
| So sánh model vs labels | Text 1 dòng | Metric cards, bảng side-by-side |

## Chuẩn ml-pipeline-workflow áp dụng

| Nguyên tắc | Áp dụng Streamlit |
|------------|-------------------|
| Data → Train → Validation → Deploy | 4 trang/section: Tải dữ liệu, Chuẩn bị, Train, Xem kết quả |
| Observability | `st.metric()` mỗi stage; bảng kết quả rõ ràng |
| Model Validation | So sánh model vs labels bằng metric cards |
| Progressive Disclosure | Level 1: 4 bước chính; Level 3+: QA, drift, batch-predict trong expander |
| Modularity | Dùng lại `run_*` từ mlfx (không duplicate logic) |

---

## Kiến trúc đề xuất

```
┌─────────────────────────────────────────────────────────────────┐
│  Streamlit App                                                   │
│  ┌─────────────┐  ┌──────────────────────────────────────────┐ │
│  │ Sidebar     │  │ Main                                      │ │
│  │ - config    │  │ 1. Tải dữ liệu  → run_download_job       │ │
│  │ - symbol/tf │  │ 2. Chuẩn bị     → resample+features+labels│ │
│  │ - Nâng cao  │  │ 3. Train       → run_training            │ │
│  └─────────────┘  │ 4. Xem kết quả  → run_model_backtest      │ │
│                   │    + metrics + biểu đồ inline             │ │
│                   └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Kế hoạch triển khai

### Phase 1: Thêm dependency và entrypoint

- Thêm `streamlit` vào `[project.optional-dependencies]` (vd: `ui = ["streamlit>=1.40,<2"]`)
- Thêm task Pixi: `mlfx-ui = "streamlit run mlfx.app.streamlit_app:main"`
- Tạo `mlfx/app/streamlit_app.py` với `main()` là entrypoint
- Script: `mlfx-streamlit` hoặc `mlfx-ui` trong `[project.scripts]` (optional)

### Phase 2: Cấu trúc app cơ bản

- **Sidebar**: Load `config.toml`, hiển thị symbol/tf mặc định; expander "Nâng cao" (qa, drift)
- **Main**: 4 section theo thứ tự workflow (st.expander hoặc st.tabs)
- **Shared state**: `st.session_state` cho symbol, tf, label_col (dùng chung giữa các bước)
- Dùng lại `load_config()` từ `mlfx.config.settings`

### Phase 3: 4 trang/section tương ứng TUI

| Section | Tương đương TUI | Thành phần Streamlit |
|---------|------------------|----------------------|
| 1. Tải dữ liệu | DownloadTab | Form (symbol, asset_class, start_year, ...), `st.button` → `run_download_job`, `st.spinner` |
| 2. Chuẩn bị | PipelineTab | Form (symbol, tf, pivot, ...), checkboxes resample/features/labels, `run_feature_pipeline` |
| 3. Train | TrainTab | Form (backend, n_trials, n_splits), `run_training`, hiển thị `best_cv_f1_macro` bằng `st.metric` |
| 4. Xem kết quả | BacktestTab | Form (tp, sl, capital, ...), `run_model_backtest`/`run_full_eval`, **metrics + biểu đồ inline** |

### Phase 4: Visualization backtest (ưu tiên cao)

- **Metrics**: `st.metric()` cho Total Trades, Win Rate, Net Profit (R), Sharpe, ...
- **So sánh baseline**: 2 cột `st.columns` — Model vs Labels; hoặc 1 dòng "Model tốt hơn +X.XR"
- **Biểu đồ inline**:
  - Đọc HTML candlestick từ `outputs/reports/` → `st.components.v1.html(html_str, height=700)`
  - Hoặc gọi trực tiếp `plot_interactive_candlestick` → trả về `go.Figure` → `st.plotly_chart(fig)`
  - Equity curve: `plot_equity_curve` lưu PNG → `st.image(path)` hoặc render Plotly nếu có API trả về fig
- **Heatmap**: `st.image(heatmap_path)` sau khi backtest xong
- Hiển thị đường dẫn reports: `st.info("Biểu đồ: outputs/reports/{symbol}/{tf}/")`

### Phase 5: Progressive Disclosure và UX

- **Level 1**: 4 section chính, mỗi section có form + nút chạy + kết quả
- **Level 3+**: Sidebar expander "Nâng cao" với link/ghi chú về qa, drift, batch-predict (có thể chỉ mô tả, chưa implement)
- **Long-running**: `st.spinner` hoặc `st.status` khi chạy download/pipeline/train/backtest
- **Error handling**: `st.error()` thay vì chỉ log
- **Tiếng Việt**: Labels, placeholder, tiêu đề section giống TUI

### Phase 6: Tích hợp và docs

- README: Thêm mục "Streamlit UI" với lệnh `pixi run mlfx-ui`
- USAGE_GUIDE: Ghi rõ có 2 cách chạy: CLI, TUI, **Streamlit** (khuyến nghị cho người mới)
- Giữ TUI: Không xóa, để người dùng chọn (CLI / TUI / Streamlit)

---

## File cần tạo/sửa

| File | Thay đổi |
|------|----------|
| `pyproject.toml` | Thêm `streamlit` vào optional-dependencies, task `mlfx-ui` |
| `mlfx/app/streamlit_app.py` | **Mới** — app Streamlit chính |
| `mlfx/evaluation/reporting.py` | (Tùy chọn) Thêm hàm trả về `go.Figure` thay vì chỉ ghi file, để Streamlit dùng |
| `README.md` | Thêm mục Streamlit UI |
| `docs/USAGE_GUIDE.md` | Cập nhật entrypoint, thêm Streamlit |

---

## Thứ tự thực hiện

1. **Phase 1**: Dependency + entrypoint + file `streamlit_app.py` rỗng chạy được
2. **Phase 2**: Sidebar + 4 section skeleton
3. **Phase 3**: Implement 4 section (form + gọi runner)
4. **Phase 4**: Backtest visualization (metrics + embed chart)
5. **Phase 5**: Progressive Disclosure, spinner, error handling
6. **Phase 6**: Docs

---

## Lưu ý kỹ thuật

- **Plotly**: Đã có trong deps; `plot_interactive_candlestick` ghi HTML. Có thể thêm hàm `get_candlestick_figure()` trả về `go.Figure` để `st.plotly_chart()` dùng trực tiếp.
- **Threading**: Streamlit chạy sync; job dài (train, download) sẽ block. Dùng `st.spinner` hoặc `st.status`; nếu cần async sau có thể dùng `streamlit-extras` hoặc custom.
- **Config**: Dùng `DEFAULT_PATHS.config_file`, `load_config()` từ settings.

---

## Design System (đã triển khai)

### Glassmorphism Emerald AMOLED

| Token | Giá trị | Mục đích |
|-------|---------|----------|
| `--bg-amoled` | `#000000` | Nền chính (OLED black) |
| `--glass-bg` | `rgba(10, 26, 22, 0.4)` | Glass card (emerald tint) |
| `--glass-border` | `rgba(16, 185, 129, 0.15)` | Viền glass |
| `--emerald-500` | `#10B981` | Primary, accent |
| `--emerald-400` | `#34D399` | Success, highlight |

File: `mlfx/app/streamlit_ui/assets/glass_emerald.css`  
Theme base: `.streamlit/config.toml`
