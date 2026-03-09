# Web-App Improvement Roadmap

Plans are ordered by impact-to-effort ratio. Each has a dedicated file with full implementation spec.

## Plan Index

| # | Plan | Status | Effort | Notes |
|---|------|--------|--------|-------|
| [01](./01-vectorize-orientation-grid.md) | Vectorize orientation grid sweep | ✅ Done | S | NumPy broadcast, ~5 s |
| [02](./02-economic-analysis.md) | Economic analysis tab | ✅ Done | M | IRR, NPV, LCOE, cashflow chart |
| [03](./03-rest-api.md) | REST API for mobile integration | 🔲 Pending | M | CORS configured; needs hosting |
| [04](./04-shading-model.md) | Horizon shading physics | ✅ Done | M | Sigmoid mask in run_simulation + orientation grid |
| [05](./05-degradation-projection.md) | 20-year degradation projection | ✅ Done | S | `core/degradation.py` + lifetime chart |
| [06](./06-sensitivity-and-shading.md) | Sensitivity tornado + shading in grid | ✅ Done | M | `compute_sensitivity()`, `sensitivity_tornado()`, horizon in grid |

**Effort key:** S = small (½–1 day), M = medium (1–2 days)

---

## Current App State (as of 2026-03, session 2)

**Six tabs:** Annual Summary · Orientation Optimizer · Monthly Breakdown · Daily Irradiance · Sun Path · Economics

**Core modules:**
- `core/climate.py` — PVGIS TMY → Open-Meteo → clear-sky fallback
- `core/system.py` — CEC/Sandia DB, PVsyst .pan/.ond parser, parametric module builder
- `core/energy.py` — full PVsyst-equivalent hourly sim; vectorized orientation grid; `compute_sensitivity()`
- `core/losses.py` — LossBudget dataclass, IAM, DC/AC loss chain, waterfall builder
- `core/economics.py` — NPV, IRR, LCOE, payback; `EconResult`
- `core/degradation.py` — linear degradation projection
- `ui/sidebar.py` — system configuration sidebar (includes horizon profile input)
- `ui/charts.py` — 15 Plotly chart builders (all using organic LAYOUT_BASE design system)

**Annual Summary tab expanders:**
1. Loss Budget Detail (table)
2. **Sensitivity Analysis** — What Moves Your Yield? (tornado chart — new)
3. Lifetime Yield Projection (bar + cumulative line)
4. Download Results (CSV + JSON)

**Horizon shading:** UI input → sigmoid mask in `run_simulation()` → also applied in `compute_orientation_grid()` ✅

---

## Next Priorities

| # | Task | Agent | Priority |
|---|------|-------|----------|
| REST API | Deploy `api/` to Railway/Render | 03+04 | H (unblocks mobile) |
| Deploy | Streamlit Community Cloud | 03 | L |

---

## Shared Conventions

- All new physics: `core/` module, `@st.cache_data` on simulation functions
- All new UI: new tab in `app.py` or expander inside existing tab
- New sidebar inputs: add to `ui/sidebar.py`, key in `cfg` dict returned by `render_sidebar()`
- License header on every new file: `# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>`
- No new top-level dependencies without a requirements.txt update
