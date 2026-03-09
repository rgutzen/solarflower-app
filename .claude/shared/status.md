# Project Status Board

_Update this file whenever a component's status changes._
_Last updated: 2026-03-10_

---

## Component Status

| # | Component | Status | Blockers | Next action |
|---|-----------|--------|----------|-------------|
| 1 | SciComm Notebook | Functional draft | — | Add ipywidgets, cell temperature section |
| 2 | Web-App (Solar Advisor) | **Complete — 6 tabs** | — | Vectorize orientation sweep further |
| 3 | Website | **Complete — index + article + solar-advisor** | — | Add resources.html |
| 4 | REST API | **Complete — deployed-ready** | Needs hosting | Deploy to Railway/Render; set API_BASE in app.js |
| 5 | Panel Compass PWA | **Complete + API-ready** | API not deployed | Set API_BASE once API is hosted |

---

## Component 1 — SciComm Notebook

**Status:** Functional draft
**File:** `notebook/solar_panel_power.ipynb`

### What works
- Solar position calculation (declination, hour angle, altitude, azimuth)
- Clear-sky irradiance (Meinel 1976 DNI + Liu-Jordan isotropic diffuse)
- Panel irradiance (POA: beam + diffuse + ground-reflected)
- Annual energy grid (tilt × azimuth sweep)
- Monthly energy breakdown
- Orientation heatmap visualization

### Known gaps
- No interactive widgets (ipywidgets) for live parameter exploration
- No section on cell temperature effects
- No section on real-world losses (soiling, LID, etc.)
- No comparison with PVGIS TMY vs clear-sky model
- No link/pointer to the Solar Advisor web-app

### Physics models used
- DNI: Meinel 1976 (simplified; educational only)
- Diffuse: Liu-Jordan isotropic (simpler than Perez used in web-app)
- Temperature: NOCT model (not Faiman)

---

## Component 2 — Web-App (Solar Advisor)

**Status:** Complete — 6 interactive tabs, economics, design overhaul
**Directory:** `solar-app/`

### What works
- PVGIS TMY data fetch with Open-Meteo + clear-sky fallback
- Full PVsyst-equivalent simulation pipeline (one-diode SDM + Perez sky + Faiman thermal)
- **6 interactive tabs:** Annual Summary, Orientation Optimizer, Monthly Breakdown, Daily Irradiance, Sun Path, Economics
- CEC database (15k modules, 3k inverters) + PVsyst .pan/.ond import + parametric
- Vectorized orientation grid sweep with contour heatmap (~5 s)
- Sankey energy-flow diagram + horizontal loss waterfall
- Monthly polar rose + bar+PR chart
- Sun path flower polar diagram + horizon profile overlay
- Lifetime yield projection (20–30 yr degradation model)
- Economics tab: CAPEX, payback, NPV, IRR, LCOE, cash-flow chart
- CSV and JSON export
- Organic light design system: warm off-white bg (`#F8FAF5`), earth tones, Lora serif

### Design config (2026-03-09 current state)
- `solar-app/.streamlit/config.toml`: **light theme** — `backgroundColor #F8FAF5`, `textColor #2D3B2D`
- `solar-app/ui/styles.css`: CSS custom properties, metric cards with gradient+border+shadow
- `solar-app/ui/charts.py`: LAYOUT_BASE pattern, organic palette, no dark templates
- `app.py`: all `st.plotly_chart` use `width="stretch"` (Streamlit 1.55+)

### Known gaps
- Orientation sweep not vectorized at physics level (cached; tolerable)
- No site shading input (horizon profile UI exists, physics not wired up fully)

### Verification baseline (Berlin, 8 kWp, S-facing 35°)
- Annual yield: ~10,200 kWh
- Specific yield: ~1,275 kWh/kWp
- Performance Ratio: ~89.4%
- Capacity Factor: ~14.6%

---

## Component 3 — Website

**Status:** Complete — landing page + science article + Solar Advisor page (design v1.4)
**Directory:** `website/`

### What works
- `index.html` — landing page, organic arc panels, component nav pills, clay-mark icons, vine border
- `styles.css` — full responsive design system v1.4 (solarpunk/soilpunk, WCAG AA)
- `main.js` — scroll reveal, nav state
- `article.html` — "From Sunlight to Watts" science article, design v1.4 applied
- `article.css` — canvas texture, wave dividers, callout boxes, equation styling
- `article.js` — 10+ interactive Plotly charts (bold titles, readable fonts/margins as of 2026-03-08)
- `solar-advisor.html` — Solar Advisor page: organic feature cards, physics table, iframe embed
- `assets/icons.svg` — clay-mark SVG icon system (5 symbols + clay filter)
- Panel Compass nav link **active** (was disabled via CSS; fixed 2026-03-08)
- `mobile-app/` symlink in `website/` pointing to `../mobile-app`

### Known gaps
- Not yet deployed (GitHub Pages / Netlify)
- `resources.html` not yet created

---

## Component 4 — Panel Compass PWA

**Status:** Complete
**Directory:** `mobile-app/`

### What works
- `index.html` — single-page app shell, organic Solarflower design
- `app.js` — main orchestrator: GPS → sensors → yield model → UI updates (60fps)
- `solar.js` — pure JS solar calculations (optimal tilt formula, PVWatts-style yield)
- `compass.js` — device sensor abstraction (heading + tilt + exponential smoothing)
- `styles.css` — mobile-first design system
- `manifest.json` + `sw.js` — installable PWA with offline cache-first service worker
- Live compass needle + target marker + zone arcs (±3° green, ±10° amber)
- Live tilt arc gauge + directional arrows
- Circular yield gauge (% of optimal output)
- GPS geolocation + reverse geocoding (Open-Meteo Geocoding API)
- iOS 13+ DeviceOrientationEvent.requestPermission() pattern
- Accessible from website via `website/mobile-app/` symlink

### Known gaps
- Not yet deployed (needs HTTPS for sensor APIs)
- `API_BASE` in `app.js` is `null` — set to deployed API URL to activate TMY-backed yields

---

## Component 4 — REST API

**Status:** Complete, ready to deploy
**Directory:** `api/`

### What works
- `GET /health` — liveness probe
- `POST /api/estimate` — PVGIS TMY + Perez + Faiman + PVWatts chain, returns:
  - `annual_yield_kwh`, `specific_yield_kwh_kwp`, `performance_ratio_pct`
  - `avg_daily_yield_kwh`, `monthly_yield_kwh_day`
  - `optimal_tilt_deg`, `optimal_azimuth_deg` (from vectorized 10° coarse sweep)
  - `data_source`
- CORS pre-configured for `robingutzen.com` and `solarflower.streamlit.app`
- `Procfile` for Heroku/Railway deploy; `requirements.txt` complete
- `api/core/` contains Streamlit-free copies of `climate.py` and `losses.py`

### Deploy
```bash
cd api && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Cross-Component Dependencies

```
website ──links to──→ web-app (URL contract, iframe embed in solar-advisor.html)
website ──links to──→ notebook (GitHub URL)
website ──symlink──→ mobile-app (website/mobile-app → ../mobile-app)
mobile-app ──optional API call──→ api/ (API_BASE=null until deployed; local JS fallback)
mobile-app ──implements──→ shared optimal_tilt formula
notebook ──references (prose only)──→ web-app (no runtime dependency)
```
