# Shared Conventions — All Agents Must Follow

## Coordinate System

| Variable | Convention | Notes |
|----------|------------|-------|
| **Azimuth** | 0°=North, 90°=East, 180°=South, 270°=West | Clockwise from above; matches pvlib |
| **Tilt** | 0°=horizontal, 90°=vertical | Angle from ground plane |
| **Latitude** | Positive=North, Negative=South | Decimal degrees |
| **Longitude** | Positive=East, Negative=West | Decimal degrees |

**Optimal orientation:**
- Northern hemisphere (lat > 0): South-facing (~180°), tilt ≈ |lat| × 0.9 + 3°
- Southern hemisphere (lat < 0): North-facing (~0°), same tilt formula
- Near equator (|lat| < 5°): either direction, low tilt

**CRITICAL:** The mobile-app uses `DeviceOrientationEvent.alpha` which is 0=North
clockwise — this matches our azimuth convention directly. No conversion needed.

## Physical Units

| Quantity | Unit | Notes |
|----------|------|-------|
| Irradiance | W/m² | Instantaneous |
| Irradiation | kWh/m²/yr | Cumulative |
| Power | W or kW | System output |
| Energy | kWh or MWh | Annual yield |
| Temperature | °C | Cell and ambient |
| Temp coefficient | %/°C or 1/°C | See gamma_r convention below |
| Pressure | Pa | SI; Open-Meteo returns hPa — multiply ×100 |
| Wind speed | m/s | |

**gamma_r unit convention (critical for web-app):**
- Stored in module params as **%/°C** (e.g., −0.40 for −0.40%/°C)
- pvwatts_dc expects **1/°C** (e.g., −0.004)
- Conversion: `if abs(gamma) > 0.1: gamma /= 100`
- This conversion lives in `solar-app/core/energy.py:_electrical_model`

## Performance Ratio Definition

IEC 61724 standard — always use **POA** (in-plane) irradiance, not GHI:
```
PR = E_AC [kWh] / (H_poa [kWh/m²] × P_peak [kWp])
```
Using GHI causes PR > 100% for optimally tilted panels (POA > GHI). This is wrong.

## License & Copyright

Every source file must carry an SPDX header:

**Python / JavaScript:**
```python
# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
```

**HTML:**
```html
<!-- SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com> -->
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
```

**CSS:**
```css
/* SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com> */
/* SPDX-License-Identifier: AGPL-3.0-or-later */
```

Empty `__init__.py` files do not need a header.

## Brand Identity

| Token | Value | Used in |
|-------|-------|---------|
| Accent color | `#F5A623` (amber/orange) | web-app metric boxes, mobile on-target, website CTAs |
| Success green | `#22c55e` | on-target state in mobile |
| Warning amber | `#F5A623` | close-but-not-target in mobile |
| Error red | `#ef4444` | far-off in mobile |
| Background (dark) | `#1e1e2e` | web-app metric box background |
| Border (dark) | `#333` | web-app metric box border |
| Label text | `#aaa` | web-app metric labels |

**Project name:** Solarflower
**Web-app name:** Solar Advisor
**Mobile-app name:** Panel Compass (working title)

## Git Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <short description>

[optional body]
```
Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`
Scopes: `notebook`, `web-app`, `website`, `mobile`, `infra`

Examples:
```
feat(web-app): add CSV export for simulation results
fix(web-app): use pd.notna() to detect NaN IL_ref in parametric modules
docs(notebook): add interactive widget for solar path animation
feat(website): initial landing page with four component cards
```

**When to commit:** After each working milestone. Never commit broken code.

## Python Environment

```bash
# Run any Python command in the app-dev environment:
/home/rgutzen/miniforge3/envs/app-dev/bin/python <script>

# Run the web-app:
/home/rgutzen/miniforge3/envs/app-dev/bin/streamlit run app.py

# Install new packages:
/home/rgutzen/miniforge3/envs/app-dev/bin/pip install <package>
```

Packages: Python 3.12, pvlib 0.15.0, streamlit 1.55.0, numpy 2.4.2,
pandas 2.x, plotly 5.x, scipy, requests, ipywidgets, matplotlib

## pvlib-Specific Gotchas

1. **`pvwatts_dc` keyword renamed** (pvlib 0.13+): `g_poa_effective` →
   `effective_irradiance`. Use positional args to be version-safe:
   `pvlib.pvsystem.pvwatts_dc(poa, temp_cell, pdc0, gamma)`

2. **`pd.Series(None)` becomes NaN**: `None` stored in a pd.Series is `NaN`.
   `nan is not None` is `True`. Always use `pd.notna()` to check for real values.

3. **PVGIS TMY variable names**: PVGIS returns non-standard column names.
   Always pass `map_variables=True` to `get_pvgis_tmy()`. Have a rename fallback.

4. **TMY index**: PVGIS returns a non-standard DatetimeIndex. Always normalize to
   a standard UTC year (`_reindex_tmy()` in `core/climate.py`).

5. **Perez model needs DNI extra + airmass**: Don't forget `dni_extra` and
   `airmass` params when calling `get_total_irradiance(model='perez')`.
