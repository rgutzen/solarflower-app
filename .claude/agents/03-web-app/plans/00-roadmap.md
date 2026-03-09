# Web-App Improvement Roadmap

Plans are ordered by impact-to-effort ratio. Each has a dedicated file with full implementation spec.

## Plan Index

| # | Plan | Priority | Effort | Blocks |
|---|------|----------|--------|--------|
| [01](./01-vectorize-orientation-grid.md) | Vectorize orientation grid sweep | H | S | — |
| [02](./02-economic-analysis.md) | Economic analysis tab | H | M | — |
| [03](./03-rest-api.md) | REST API for mobile integration | H | M | mobile-app |
| [04](./04-shading-model.md) | Horizon shading input | M | M | — |
| [05](./05-degradation-projection.md) | 20-year degradation projection | M | S | — |

**Effort key:** S = small (½–1 day), M = medium (1–2 days)

---

## Current App State (as of 2026-03)

Five tabs: Annual Summary, Orientation Optimizer, Monthly Breakdown, Daily Irradiance, Sun Path.

Core modules:
- `core/climate.py` — PVGIS TMY fetch with Open-Meteo + clear-sky fallback
- `core/system.py` — CEC/Sandia DB, PVsyst .pan/.ond parser, parametric module builder
- `core/energy.py` — full PVsyst-equivalent hourly simulation; nested-loop orientation grid
- `core/losses.py` — LossBudget dataclass, IAM, DC/AC loss chain, waterfall builder
- `ui/sidebar.py` — system configuration sidebar
- `ui/charts.py` — Plotly charts (waterfall, monthly, heatmap, sun path, daily irradiance)

Known issues / gaps addressed by these plans:
1. Orientation grid sweep takes ~10 min (nested Python loop) — **Plan 01**
2. No economic output (only yield, no cost/payback) — **Plan 02**
3. No machine-readable API for mobile integration — **Plan 03**
4. No near-shading / horizon input — **Plan 04**
5. No multi-year yield projection — **Plan 05**

---

## Shared Conventions

- All new physics: `core/` module, `@st.cache_data` on simulation functions
- All new UI: new tab in `app.py` or expander inside existing tab
- New sidebar inputs: add to `ui/sidebar.py`, key in `cfg` dict returned by `render_sidebar()`
- License header on every new file: `# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>`
- No new top-level dependencies without a requirements.txt update
