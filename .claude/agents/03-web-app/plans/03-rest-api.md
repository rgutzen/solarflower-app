# Plan 03 — REST API for Mobile Integration

**Priority:** High (blocks mobile-app development)
**Effort:** Medium (1–2 days)
**New service:** `api/` — standalone FastAPI app, deployed separately from Streamlit

---

## Architecture Decision

Streamlit Community Cloud only hosts Streamlit apps; it cannot expose arbitrary HTTP endpoints.
A separate lightweight FastAPI service is required. Recommended free hosting:
- **Render** (render.com) — free tier, auto-deploys from GitHub, 512 MB RAM, spins down after 15 min idle
- **Railway** (railway.app) — free $5/month credit, always-on option
- **Hugging Face Spaces** — supports FastAPI, generous free tier

The mobile-app (`mobile-app/`) will call this API at a URL defined in its config.

---

## Scope: `/api/estimate` Endpoint

A single `POST` endpoint that returns a quick PV yield estimate for a given location and orientation.
Uses PVWatts-style physics (no CEC DB lookup needed) so it responds in < 2 seconds.

### Request Body

```json
{
  "lat": 52.5,
  "lon": 13.4,
  "elevation_m": 50,
  "tilt_deg": 30,
  "azimuth_deg": 180,
  "peak_power_kwp": 6.0,
  "system_loss_pct": 14.0
}
```

### Response Body

```json
{
  "annual_yield_kwh": 5840.2,
  "specific_yield_kwh_kwp": 973.4,
  "performance_ratio_pct": 83.1,
  "avg_daily_yield_kwh": 16.0,
  "monthly_yield_kwh_day": {
    "Jan": 7.2, "Feb": 10.1, "Mar": 14.8, "Apr": 18.3,
    "May": 21.4, "Jun": 22.9, "Jul": 22.5, "Aug": 20.0,
    "Sep": 15.8, "Oct": 11.0, "Nov": 7.4, "Dec": 5.9
  },
  "data_source": "PVGIS TMY (2005–2023), satellite SARAH3/ERA5",
  "optimal_tilt_deg": 35,
  "optimal_azimuth_deg": 180
}
```

---

## Directory Structure

```
api/
├── main.py           ← FastAPI app
├── core/             ← symlink or copy of solar-app/core/ (or shared package)
│   ├── climate.py
│   ├── energy.py
│   └── losses.py
├── requirements.txt  ← fastapi, uvicorn, pvlib, numpy, pandas, scipy
├── Procfile          ← for Render: web: uvicorn main:app --host 0.0.0.0 --port $PORT
└── render.yaml       ← optional Render Blueprint config
```

Rather than copying `core/`, restructure `solar-app/core/` as an installable package
(add `__init__.py` if missing, extract Streamlit imports into optional deps).
Or simply copy and strip `@st.cache_data` decorators for the API version.

**Important:** `solar-app/core/energy.py` currently imports `streamlit` for `@st.cache_data`.
The API must not depend on Streamlit. Either:
- Remove the `@st.cache_data` decorator in the API copy (replace with simple memoization or none)
- Use `functools.lru_cache` on `fetch_tmy()` keyed on `(lat, lon)`

---

## `api/main.py` Skeleton

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np

# -- local imports (core/ without Streamlit) --
from core.climate import fetch_tmy
from core.losses import LossBudget
# energy.py stripped of @st.cache_data → import compute functions directly

app = FastAPI(
    title="Solar Advisor API",
    description="Quick PV yield estimates for the Solarflower mobile app.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to mobile-app origin in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class EstimateRequest(BaseModel):
    lat:             float = Field(..., ge=-90, le=90)
    lon:             float = Field(..., ge=-180, le=180)
    elevation_m:     float = Field(0.0, ge=0, le=5000)
    tilt_deg:        float = Field(30.0, ge=0, le=90)
    azimuth_deg:     float = Field(180.0, ge=0, le=360)
    peak_power_kwp:  float = Field(6.0, ge=0.1, le=1000)
    system_loss_pct: float = Field(14.0, ge=0, le=50)


class EstimateResponse(BaseModel):
    annual_yield_kwh:      float
    specific_yield_kwh_kwp: float
    performance_ratio_pct: float
    avg_daily_yield_kwh:   float
    monthly_yield_kwh_day: dict[str, float]
    data_source:           str
    optimal_tilt_deg:      float
    optimal_azimuth_deg:   float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest):
    try:
        tmy_df, source = fetch_tmy(req.lat, req.lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Climate data unavailable: {e}")

    # PVWatts-style quick simulation
    result = _pvwatts_quick(
        tmy_df=tmy_df,
        lat=req.lat, lon=req.lon, elevation_m=req.elevation_m,
        tilt_deg=req.tilt_deg, azimuth_deg=req.azimuth_deg,
        peak_power_kwp=req.peak_power_kwp,
        system_loss_frac=req.system_loss_pct / 100,
    )

    # Quick optimal orientation (coarse 10°/10° sweep)
    opt_tilt, opt_az = _find_optimal(tmy_df, req.lat, req.lon, req.elevation_m)

    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    return EstimateResponse(
        annual_yield_kwh=round(result["annual_kwh"], 1),
        specific_yield_kwh_kwp=round(result["annual_kwh"] / req.peak_power_kwp, 1),
        performance_ratio_pct=round(result["pr_pct"], 1),
        avg_daily_yield_kwh=round(result["annual_kwh"] / 365, 2),
        monthly_yield_kwh_day={m: round(v, 2) for m, v in zip(months, result["monthly"])},
        data_source=source,
        optimal_tilt_deg=float(opt_tilt),
        optimal_azimuth_deg=float(opt_az),
    )
```

---

## `_pvwatts_quick` Helper

PVWatts 6 simplified chain (< 0.5 s):

```python
import pvlib, numpy as np, pandas as pd

def _pvwatts_quick(tmy_df, lat, lon, elevation_m, tilt_deg, azimuth_deg,
                   peak_power_kwp, system_loss_frac):
    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    sp  = loc.get_solarposition(tmy_df.index)
    poa = pvlib.irradiance.get_total_irradiance(
        tilt_deg, azimuth_deg,
        sp["apparent_zenith"], sp["azimuth"],
        tmy_df["dni"], tmy_df["ghi"], tmy_df["dhi"],
        dni_extra=pvlib.irradiance.get_extra_radiation(tmy_df.index),
        airmass=loc.get_airmass(solar_position=sp)["airmass_relative"],
        model="isotropic",  # faster than Perez for quick estimate
    )["poa_global"].fillna(0).clip(0)

    gamma = -0.004  # generic temp coefficient
    t_cell = tmy_df["temp_air"] + poa / (25 + 6.84 * tmy_df["wind_speed"])
    p_dc = pvlib.pvsystem.pvwatts_dc(poa, t_cell, peak_power_kwp * 1000, gamma).clip(0)
    p_ac = (p_dc * (1 - system_loss_frac)).clip(0)

    annual_kwh = float(p_ac.sum() / 1000)
    poa_kwh    = float(poa.sum() / 1000)
    pr_pct     = annual_kwh / (poa_kwh * peak_power_kwp) * 100 if poa_kwh > 0 else 0

    monthly_kwh = (p_ac / 1000).resample("ME").sum()
    monthly_avg = monthly_kwh.values / monthly_kwh.index.days_in_month.values

    return {"annual_kwh": annual_kwh, "pr_pct": pr_pct, "monthly": monthly_avg}
```

---

## `_find_optimal` Helper

Coarse sweep (10°/10°) using the vectorized approach from Plan 01:

```python
def _find_optimal(tmy_df, lat, lon, elevation_m):
    tilt_arr = np.arange(0, 90, 10, dtype=float)
    az_arr   = np.arange(90, 270, 10, dtype=float)  # South-facing hemisphere only
    # ... vectorized POA as in Plan 01 ...
    i, j = np.unravel_index(energy_grid.argmax(), energy_grid.shape)
    return tilt_arr[i], az_arr[j]
```

---

## `api/requirements.txt`

```
fastapi>=0.110
uvicorn>=0.29
pvlib>=0.11
numpy>=2.0
pandas>=2.1
scipy>=1.13
requests>=2.31
```

## `api/Procfile`

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Deployment Steps

1. Create `api/` directory in repo root with the files above.
2. Push to GitHub — Streamlit Cloud ignores non-`solar-app/` code.
3. On Render: New Web Service → connect GitHub → root dir `api/` → build `pip install -r requirements.txt` → start `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set `API_BASE_URL` in `mobile-app/app.js` to the Render URL.
5. Update `shared/interfaces.md` with the live API URL.

---

## Mobile App Integration

In `mobile-app/app.js`:

```javascript
const API_BASE = 'https://solarflower-api.onrender.com';

async function getYieldEstimate(lat, lon, tiltDeg, azimuthDeg) {
  const resp = await fetch(`${API_BASE}/api/estimate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      lat, lon, elevation_m: 0,
      tilt_deg: tiltDeg, azimuth_deg: azimuthDeg,
      peak_power_kwp: 6.0, system_loss_pct: 14.0,
    }),
  });
  if (!resp.ok) throw new Error('API error');
  return resp.json();
}
```
