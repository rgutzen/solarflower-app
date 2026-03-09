# Completed Tasks

---

## Session: Initial project build (2026-03-06)

### [agent:01] Educational notebook
- [x] Derive solar position equations from first principles
- [x] Implement clear-sky irradiance model (Meinel 1976 DNI)
- [x] Implement Liu-Jordan isotropic diffuse + ground-reflected
- [x] Implement POA irradiance calculation
- [x] Implement annual energy grid (tilt × azimuth sweep)
- [x] Implement monthly energy breakdown
- [x] Orientation heatmap visualization

### [agent:03] Web-App (Solar Advisor)
- [x] Design full architecture (core + ui)
- [x] `core/climate.py` — PVGIS TMY + Open-Meteo + clear-sky fallback
- [x] `core/system.py` — CEC DB + PVsyst .pan/.ond import + parametric_module()
- [x] `core/losses.py` — LossBudget dataclass, IAM, DC/AC loss chain, waterfall builder
- [x] `core/energy.py` — run_simulation(), compute_orientation_grid(), SimResult
- [x] `ui/sidebar.py` — all input controls
- [x] `ui/charts.py` — waterfall, monthly, heatmap, daily, sun path (Plotly)
- [x] `app.py` — 5-tab Streamlit layout with persistent metrics bar
- [x] `requirements.txt`
- [x] Fix: pd.Series(None)→NaN, use pd.notna() (annual yield was 0)
- [x] Fix: pvwatts_dc positional args (deprecated keyword)
- [x] Fix: PR uses POA not GHI (was giving PR > 100%)
- [x] Fix: gamma_r unit convention documented and applied correctly
- [x] SPDX headers on all 7 Python source files

### [infra] Project setup
- [x] `.gitignore` created (Python, Jupyter, Streamlit, PVsyst files, secrets)
- [x] `LICENSE` — AGPL-3.0-or-later
- [x] `COMMERCIAL_LICENSE.md` — dual licensing terms + contact info
- [x] `solar-app/README.md` — quick start, physics stack, project structure
- [x] Initial git commit and push to `git@github.com:rgutzen/solarflower-app.git`

## Session: Streamlit Cloud deployment prep (2026-03-07)

### [agent:03] Streamlit Cloud preparation
- [x] Fixed `.gitignore` — tracks `config.toml`, ignores `secrets.toml` and `credentials.toml`
- [x] Created `solar-app/.streamlit/config.toml` — brand theme + iframe CORS disabled
- [x] Created `solar-app/docs/deployment.md` — full step-by-step guide
- [x] Updated `website/solar-advisor.html` — cloud-aware embed script with timeout handling

---

## Session: Web-app export + Solar Advisor website page (2026-03-07)

### [agent:03] Web-App — CSV/JSON export
- [x] Added "Download Results" expander to Tab 1 (Annual Summary)
- [x] `Download Monthly CSV` button — month, avg daily yield, PR
- [x] `Download Full Summary JSON` — location, orientation, system, results, monthly, loss waterfall

### [agent:02] Website — Solar Advisor dedicated page
- [x] Created `website/solar-advisor.html` — feature showcase + physics table + iframe embed
- [x] Updated `website/index.html` — Solar Advisor card now links to `solar-advisor.html`

---

## Session: Multi-agent coordination setup (2026-03-06)

### [infra] Agent coordination infrastructure
- [x] Agent base prompts for all 4 agents
- [x] Shared conventions, interfaces, status board
- [x] Per-agent memory files (all four)
- [x] Task queue (backlog, active, done)
- [x] Rewrote `.claude/memory/MEMORY.md` as orchestration hub

---

## Session: Economics, degradation, vectorized sweep (2026-03-07/08)

### [agent:03] Web-App — major feature additions
- [x] `core/economics.py` — compute_economics(): NPV, IRR, LCOE, simple payback, EconResult dataclass
- [x] `core/degradation.py` — lifetime_yield(): linear degradation projection (default 0.5%/yr)
- [x] `app.py` — added Tab 6 (Economics): 5 KPI metrics, cashflow chart, yield degradation chart
- [x] `app.py` — added lifetime projection expander in Annual Summary tab
- [x] Vectorized `compute_orientation_grid()` — numpy broadcasting, ~5 s for 15°×10° grid (was minutes)
- [x] `ui/charts.py` — cashflow_chart(), yield_degradation_chart(), lifetime_yield_chart()
- [x] `ui/charts.py` — orientation_contour() (smooth contour, replaces heatmap)
- [x] `ui/charts.py` — yield_vs_tilt() cross-section chart
- [x] `ui/sidebar.py` — Economics config section (CAPEX, tariff, discount rate, etc.)

---

## Session: Website design + article + Panel Compass PWA (2026-03-07/08)

### [agent:02] Website — design v1.4 + science article
- [x] Applied Phase 5 typography (Lora serif titles)
- [x] Applied Phase 6 clay mark icon system + arc panel design + nav pills + vine border
- [x] Created `website/assets/icons.svg` — 5 clay-mark icons + clay SVG filter
- [x] Created `website/article.html` — "From Sunlight to Watts" first-principles article
- [x] Created `website/article.css` — canvas texture, wave dividers, callout/equation styling
- [x] Created `website/article.js` — 10+ interactive Plotly charts
- [x] Applied Phase 8/9 design to `article.html` and `solar-advisor.html`
- [x] Fixed article.js: bold titles, margin.b 50→80, font sizes increased (2026-03-08)
- [x] Activated Panel Compass nav link (removed `pointer-events: none` CSS)

### [agent:04] Mobile-App — Panel Compass PWA (complete build)
- [x] `mobile-app/index.html` — single-page app shell, organic design
- [x] `mobile-app/app.js` — GPS → sensors → yield → UI orchestrator (60fps)
- [x] `mobile-app/solar.js` — optimal tilt formula, PVWatts-style yield model
- [x] `mobile-app/compass.js` — device sensor abstraction, exponential smoothing
- [x] `mobile-app/styles.css` — mobile-first Solarflower design system
- [x] `mobile-app/manifest.json` + `sw.js` — installable PWA, offline cache
- [x] Live compass + tilt meter + yield gauge + directional arrows
- [x] iOS 13+ DeviceOrientation permission pattern
- [x] `website/mobile-app` symlink → `../mobile-app`
- [x] `mobile-app/README.md` — how it works, quick start

---

## Session: Solar Advisor design overhaul (2026-03-08)

### [agent:03] Web-App — organic design system
- [x] `solar-app/.streamlit/config.toml` — switched to **light theme** (`#F8FAF5` bg, `#2D3B2D` text)
  - Root cause fix: dark theme was making all transparent-background charts appear dark
- [x] `solar-app/ui/charts.py` — complete organic design overhaul:
  - LAYOUT_BASE pattern + _layout() / _title() / _polar_style() helpers
  - Organic colour palette (SUN `#E8920E`, EARTH `#4A7A58`, TERRACOTTA `#C75B39`)
  - Removed all `template="plotly_dark"` instances
  - GREY_COLOR #AAAAAA → #6A7F72 (warm readable grey)
  - Seasonal bar colors in monthly_summary
  - energy_roots() Sankey + monthly_rose() polar charts as main Annual Summary visuals
- [x] `solar-app/ui/styles.css` — complete CSS overhaul with design tokens, metric card fixes
  - Metric cards: gradient+border+shadow (visible on light background)
  - Font sizes reduced for 7-column metric row (prevent "1,728 ..." truncation)
  - Organic asymmetric border-radius on expanders, chart containers, buttons
- [x] `solar-app/app.py` — all `st.plotly_chart` use `width="stretch"` (Streamlit 1.55+)

---

## Session: README + memory file updates (2026-03-09)

### [infra]
- [x] Updated root `README.md` — all 5 components documented with features and run instructions
- [x] Updated `.claude/memory/MEMORY.md` — correct repo URL, component statuses, design notes
- [x] Updated `.claude/shared/status.md` — full current state of all 4 components
- [x] Updated `.claude/shared/design-roadmap.md` — Phase 7/8/9 completion statuses
- [x] Updated all 4 agent MEMORY.md files — current state, decisions, paths

---

## Session: PNG favicon + mobile API integration (2026-03-10)

### [agent:02] Website
- [x] Added PNG favicon fallback (`<link rel="icon" href="assets/logo.png" type="image/png">`) to all 5 HTML pages (index, article, solar-advisor, resources, orientation-analysis)

### [agent:04] Mobile-App
- [x] `app.js` — added `API_BASE` constant (null = disabled; set to deployed URL to activate)
- [x] `app.js` — added `fetchApiEstimate()`: async POST to `/api/estimate`, 15 s timeout, returns null on any failure
- [x] `app.js` — added `applyApiResult()`: updates optimal orientation + `yieldScaleFactor` from API response
- [x] `app.js` — `setLocation()` fires API call in background after local estimate; guards against stale responses
- [x] `app.js` — live sensor frames apply `yieldScaleFactor` to keep `currentYield / optimalYield` consistent
