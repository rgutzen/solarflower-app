# Agent 01 — SciComm Notebook: Persistent Memory

_Update this file after every working session._
_Last updated: 2026-03-09_

## Scope
- **File:** `/home/rgutzen/01_PROJECTS/solarflower-app/notebook/solar_panel_power.ipynb`
- **Base prompt:** `.claude/agents/01-notebook/01_scicomm-notebook.md`
- **Do NOT modify:** any file outside the notebook

## Current State

The notebook contains a working first-principles derivation. All functions are defined
and the core physics chain is implemented. The notebook runs end-to-end without errors.

### Sections confirmed present
1. Solar position (declination, hour angle, altitude, azimuth)
2. Extraterrestrial irradiance (solar constant, eccentricity correction)
3. Atmospheric attenuation → clear-sky DNI/DHI/GHI (Meinel 1976)
4. Panel irradiance (POA: beam + Liu-Jordan diffuse + ground-reflected)
5. Annual energy grid and orientation heatmap
6. Monthly energy breakdown

### Key functions
```python
solar_altitude_azimuth(doy, hour_utc, lat_deg, lon_deg) → (alt_rad, az_rad)
panel_irradiance(DNI, DHI, GHI, altitude_rad, azimuth_rad,
                 tilt_deg, panel_az_deg, albedo) → G_T [W/m²]
compute_annual_grid(lat, lon, elev, tilt_arr, az_arr, ...) → energy_grid [kWh]
compute_monthly_energy(...) → monthly avg kWh/day
```

### Physics models used (simpler than web-app — intentional for education)
- DNI attenuation: Meinel 1976 (`DNI = G_0 × 0.7^(AM^0.678)`)
- Diffuse: Liu-Jordan isotropic (`DHI × (1+cosβ)/2`)
- Temperature: NOCT model (not Faiman; simpler)
- Electrical: PVWatts-style (not full one-diode SDM)

## Confirmed Decisions

- **Coordinate system:** Azimuth 0°=N, 90°=E, 180°=S, 270°=W — matches `shared/conventions.md`
- **Audience:** General public, no PV engineering prerequisites
- **Format:** Computational article — prose + LaTeX equations + code + interactive figures
- **Dependencies:** numpy, pandas, matplotlib, plotly, ipywidgets (all in app-dev env)
- **Standalone:** No dependency on `solar-app/` at runtime

## Session 2 Changes (2026-03-09) — 23 cells total

- **Cell [19] expanded**: interactive dashboard now has 8 sliders:
  lat, elevation, area, efficiency, albedo (existing) + **DOY, panel_tilt, panel_azimuth** (new)
  4-panel layout: heatmap (⭐ optimal + ✕ your choice) / tilt sweep / monthly / **daily sun path polar**
- **Cell [20] new**: Cape Town (33.9°S) vs Berlin (52.5°N) side-by-side heatmaps — azimuth flip demo
- **Cell [22] new**: Solar Advisor forward link + notebook vs Solar Advisor model comparison table

## Remaining Gaps

- [ ] No quantitative comparison: clear-sky yield numbers vs PVGIS TMY (only a conceptual note)

## Sanity Check Values

Berlin (52.5°N), south-facing 35° tilt, 1 m² panel, η=20%:
- Expected annual clear-sky yield: ~175–200 kWh/m²/yr
- (Higher than reality; clear-sky overestimates vs TMY which accounts for clouds)

Tilt=0° (flat panel): yield should be azimuth-independent (symmetric)
Cape Town (33.9°S): optimal azimuth should be ~0° (North-facing)
