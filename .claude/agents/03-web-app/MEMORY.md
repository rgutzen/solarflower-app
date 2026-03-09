# Agent 03 — Web-App (Solar Advisor): Persistent Memory

_Update this file after every working session._
_Last updated: 2026-03-09_

## Scope
- **Directory:** `/home/rgutzen/01_PROJECTS/solarflower-app/solar-app/`
- **Base prompt:** `.claude/agents/03-web-app/03_web-app.md`
- **Do NOT modify:** any file outside `solar-app/`

## Architecture

```
solar-app/
├── app.py               Streamlit entry, 6 tabs + persistent metrics bar
├── requirements.txt
├── .streamlit/
│   └── config.toml      Light theme: #F8FAF5 bg, #2D3B2D text, #E8920E primary
├── core/
│   ├── __init__.py
│   ├── climate.py       fetch_tmy(): PVGIS TMY → Open-Meteo → clear-sky fallback
│   ├── system.py        CEC DB, PVsyst .pan/.ond import, parametric_module()
│   ├── losses.py        LossBudget dataclass, IAM, DC/AC loss chain, waterfall
│   ├── energy.py        run_simulation(), compute_orientation_grid(), SimResult
│   ├── economics.py     compute_economics(): NPV, IRR, LCOE, payback, EconResult
│   └── degradation.py   lifetime_yield(): linear degradation projection
└── ui/
    ├── __init__.py
    ├── sidebar.py        All Streamlit input controls → returns cfg dict
    └── charts.py         Plotly figure builders (organic LAYOUT_BASE design system)
```

## Physics Stack

| Stage | Model | Function |
|-------|-------|----------|
| Climate | PVGIS TMY (20+yr satellite) | `pvlib.iotools.get_pvgis_tmy()` |
| Solar position | Ephemeris | `location.get_solarposition()` |
| Sky diffuse | Perez anisotropic | `get_total_irradiance(model='perez')` |
| IAM | Physical (AR glass) | `pvlib.iam.physical()` |
| Thermal | Faiman (PVsyst default) | `pvlib.temperature.faiman()` |
| Electrical (SDM) | PVsyst one-diode | `calcparams_pvsyst()` + `singlediode()` |
| Electrical (fallback) | PVWatts | `pvwatts_dc(poa, Tcell, pdc0, gamma)` |
| Inverter | CEC Sandia / PVWatts | `pvlib.inverter.sandia/pvwatts()` |
| PR | IEC 61724 | E_AC / (H_poa × P_peak) |

## Critical Bugs (all fixed — DO NOT REGRESS)

### Bug 1: pd.Series(None) → NaN
- **File:** `core/energy.py:_electrical_model`
- **Symptom:** Annual yield = 0 for parametric modules
- **Fix:** `sdm_available = has_sdm and il_ref is not None and pd.notna(il_ref) and ...`

### Bug 2: pvwatts_dc keyword removed
- **File:** `core/energy.py:_electrical_model`
- **Fix:** `pvlib.pvsystem.pvwatts_dc(poa, temp_cell, pdc0, gamma)` (positional only)

### Bug 3: PR > 100% using GHI
- **File:** `core/energy.py:run_simulation`
- **Fix:** `pr = annual_yield / (poa_kwh * pk_kw)` (use POA per IEC 61724)

### Bug 4: gamma_r unit mismatch
- gamma_r stored as %/°C; pvwatts_dc needs 1/°C — conversion at use site

## Caching Strategy
- `@st.cache_resource`: `load_cec_modules()`, `load_cec_inverters()` (once per process)
- `@st.cache_data`: `run_simulation()`, `compute_orientation_grid()` (keyed on all args)
- `st.session_state["tmy_df"]`: TMY data (fetched on demand, survives reruns)
- `st.session_state["energy_grid"]`: Orientation sweep (behind "Run Sweep" button)

## Verification Baseline (do not break)
Berlin (52.5°N), 20 × 400W = 8 kWp CEC monocrystalline, S-facing 35°, Open-Meteo 2023:
- Annual yield: ~10,200 kWh
- Specific yield: ~1,275 kWh/kWp
- Performance Ratio: ~89.4%
- Capacity Factor: ~14.6%

## Key cfg Dict Keys (from render_sidebar)
`lat, lon, elevation_m, tilt_deg, panel_az_deg, albedo,`
`module_params (pd.Series), inverter_params (pd.Series), inverter_type (str),`
`n_modules, strings_per_inverter, n_inverters, loss_budget (LossBudget),`
`tilt_step, az_step, fetch_climate (bool), econ (dict | None)`

## Decisions Made
- Tabs: Annual Summary / Orientation Optimizer / Monthly Breakdown / Daily Irradiance / Sun Path / Economics
- Metric bar: DC Peak | Annual Yield | Specific Yield | PR | CF | Avg Daily | Data Source
- Annual tab: Sankey energy-flow diagram (`energy_roots`) + monthly polar rose (`monthly_rose`)
  (Earlier decision of "horizontal bar chart not Sankey" was reversed — Sankey now primary)
- Orientation sweep: vectorized (numpy broadcasting) — ~5 s for 15°×10° grid
- PR definition: IEC 61724 vs POA (not GHI) — this is non-negotiable

## Design System (charts.py)
```python
# Organic palette
SUN_COLOR = "#E8920E"    EARTH_COLOR = "#4A7A58"    TERRACOTTA = "#C75B39"
INK_COLOR = "#2D3B2D"    INK_LIGHT   = "#4A6050"    GREY_COLOR = "#6A7F72"

# Shared layout
LAYOUT_BASE = dict(font=..., paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,252,248,0.45)", ...)
def _layout(**overrides) → dict    # deep-copy + merge
def _title(text, size=15) → dict   # Lora serif title
def _polar_style() → dict          # shared polar axis config
```
- **Never** use `template="plotly_dark"` — conflicts with light page background
- `paper_bgcolor="rgba(0,0,0,0)"` renders correctly because `config.toml` bg is now light

## Streamlit API Notes
- `st.plotly_chart(..., width="stretch")` — replaces deprecated `use_container_width=True`
- `st.dataframe`, `st.button`, `st.download_button` still use `use_container_width=True` (valid)
