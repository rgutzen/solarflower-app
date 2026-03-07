# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Solar Advisor REST API — quick PV yield estimates for the Solarflower mobile app.

Endpoints:
  GET  /health           — liveness check
  POST /api/estimate     — PV yield estimate for a given location + orientation

Deploy on Render / Railway / Hugging Face Spaces:
  pip install -r requirements.txt
  uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import pvlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.climate import fetch_tmy

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


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class EstimateRequest(BaseModel):
    lat:             float = Field(..., ge=-90, le=90, description="Latitude [°]")
    lon:             float = Field(..., ge=-180, le=180, description="Longitude [°]")
    elevation_m:     float = Field(0.0, ge=0, le=5000, description="Site elevation [m]")
    tilt_deg:        float = Field(30.0, ge=0, le=90, description="Panel tilt [°]")
    azimuth_deg:     float = Field(180.0, ge=0, le=360, description="Panel azimuth [°] (180=South)")
    peak_power_kwp:  float = Field(6.0, ge=0.1, le=1000, description="Array DC peak power [kWp]")
    system_loss_pct: float = Field(14.0, ge=0, le=50, description="Total system loss [%]")


class EstimateResponse(BaseModel):
    annual_yield_kwh:       float
    specific_yield_kwh_kwp: float
    performance_ratio_pct:  float
    avg_daily_yield_kwh:    float
    monthly_yield_kwh_day:  dict[str, float]
    data_source:            str
    optimal_tilt_deg:       float
    optimal_azimuth_deg:    float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest):
    try:
        tmy_df, source = fetch_tmy(req.lat, req.lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Climate data unavailable: {e}")

    result = _pvwatts_quick(
        tmy_df=tmy_df,
        lat=req.lat, lon=req.lon, elevation_m=req.elevation_m,
        tilt_deg=req.tilt_deg, azimuth_deg=req.azimuth_deg,
        peak_power_kwp=req.peak_power_kwp,
        system_loss_frac=req.system_loss_pct / 100.0,
    )

    opt_tilt, opt_az = _find_optimal(tmy_df, req.lat, req.lon, req.elevation_m)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return EstimateResponse(
        annual_yield_kwh=round(result["annual_kwh"], 1),
        specific_yield_kwh_kwp=round(result["annual_kwh"] / req.peak_power_kwp, 1),
        performance_ratio_pct=round(result["pr_pct"], 1),
        avg_daily_yield_kwh=round(result["annual_kwh"] / 365.0, 2),
        monthly_yield_kwh_day={m: round(v, 2) for m, v in zip(months, result["monthly"])},
        data_source=source,
        optimal_tilt_deg=float(opt_tilt),
        optimal_azimuth_deg=float(opt_az),
    )


# ---------------------------------------------------------------------------
# Physics helpers
# ---------------------------------------------------------------------------

def _pvwatts_quick(
    tmy_df: pd.DataFrame,
    lat: float, lon: float, elevation_m: float,
    tilt_deg: float, azimuth_deg: float,
    peak_power_kwp: float, system_loss_frac: float,
) -> dict:
    """PVWatts 6 simplified chain — responds in < 0.5 s."""
    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    sp  = loc.get_solarposition(tmy_df.index)
    poa = pvlib.irradiance.get_total_irradiance(
        tilt_deg, azimuth_deg,
        sp["apparent_zenith"], sp["azimuth"],
        tmy_df["dni"], tmy_df["ghi"], tmy_df["dhi"],
        dni_extra=pvlib.irradiance.get_extra_radiation(tmy_df.index),
        airmass=loc.get_airmass(solar_position=sp)["airmass_relative"],
        model="isotropic",
    )["poa_global"].fillna(0.0).clip(lower=0.0)

    gamma  = -0.004  # generic temperature coefficient [1/°C]
    t_cell = tmy_df["temp_air"] + poa / (25.0 + 6.84 * tmy_df["wind_speed"])
    p_dc   = pvlib.pvsystem.pvwatts_dc(poa, t_cell, peak_power_kwp * 1000.0, gamma).clip(lower=0.0)
    p_ac   = (p_dc * (1.0 - system_loss_frac)).clip(lower=0.0)

    annual_kwh = float(p_ac.sum() / 1000.0)
    poa_kwh    = float(poa.sum() / 1000.0)
    pr_pct     = annual_kwh / (poa_kwh * peak_power_kwp) * 100.0 if poa_kwh > 0 else 0.0

    monthly_kwh = (p_ac / 1000.0).resample("ME").sum()
    monthly_avg = (monthly_kwh.values / monthly_kwh.index.days_in_month.values).tolist()

    return {"annual_kwh": annual_kwh, "pr_pct": pr_pct, "monthly": monthly_avg}


def _find_optimal(
    tmy_df: pd.DataFrame,
    lat: float, lon: float, elevation_m: float,
) -> tuple[float, float]:
    """
    Find optimal (tilt, azimuth) via vectorized 10°/10° coarse sweep.
    Uses Hay-Davies sky model — O(N × T × A) with NumPy broadcast.
    """
    tilt_arr = np.arange(0, 91, 10, dtype=np.float32)
    az_arr   = np.arange(90, 271, 10, dtype=np.float32)  # South-facing hemisphere

    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    sp  = loc.get_solarposition(tmy_df.index)
    dni_extra = pvlib.irradiance.get_extra_radiation(tmy_df.index).values

    zen_r    = np.radians(sp["apparent_zenith"].values)
    az_sun_r = np.radians(sp["azimuth"].values)
    cos_z    = np.cos(zen_r).astype(np.float32)
    sin_z    = np.sin(zen_r).astype(np.float32)
    ghi      = tmy_df["ghi"].values.astype(np.float32)
    dni      = tmy_df["dni"].values.astype(np.float32)
    dhi      = tmy_df["dhi"].values.astype(np.float32)
    t_air    = tmy_df["temp_air"].values.astype(np.float32)
    ws       = tmy_df["wind_speed"].values.astype(np.float32)

    with np.errstate(divide="ignore", invalid="ignore"):
        F = np.where(dni_extra > 0, dni / dni_extra.astype(np.float32), 0.0).clip(0.0, 1.0)

    tilt_r = np.radians(tilt_arr)
    az_r   = np.radians(az_arr)

    cos_z_  = cos_z[:, None, None]
    sin_z_  = sin_z[:, None, None]
    az_sun_ = az_sun_r[:, None, None].astype(np.float32)
    cos_t   = np.cos(tilt_r)[None, :, None]
    sin_t   = np.sin(tilt_r)[None, :, None]
    az_p    = az_r[None, None, :]

    cos_aoi    = (cos_z_ * cos_t + sin_z_ * sin_t * np.cos(az_sun_ - az_p)).clip(0.0)
    cos_z_safe = np.where(cos_z_ > 0.087, cos_z_, 0.087)
    F_         = F[:, None, None]
    poa_direct = dni[:, None, None] * cos_aoi
    poa_sky    = dhi[:, None, None] * (F_ * cos_aoi / cos_z_safe + (1.0 - F_) * (1.0 + cos_t) / 2.0)
    poa_ground = ghi[:, None, None] * 0.20 * (1.0 - cos_t) / 2.0
    poa_eff    = (poa_direct + poa_sky + poa_ground).clip(0.0)

    gamma    = -0.004
    temp_c   = t_air[:, None, None] + poa_eff / (25.0 + 6.84 * ws[:, None, None])
    p_dc     = (6.0 * 1000.0 * poa_eff / 1000.0 * (1.0 + gamma * (temp_c - 25.0))).clip(0.0)
    p_ac_net = (p_dc * 0.86).clip(0.0)  # 14% system loss

    energy_grid = p_ac_net.sum(axis=0) / 1000.0
    i, j = np.unravel_index(energy_grid.argmax(), energy_grid.shape)
    return float(tilt_arr[i]), float(az_arr[j])
