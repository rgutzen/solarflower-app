# Plan 01 — Vectorize Orientation Grid Sweep

**Priority:** High
**Effort:** Small (½ day)
**File:** `solar-app/core/energy.py` — `compute_orientation_grid()`

---

## Problem

`compute_orientation_grid()` runs a nested Python loop over `(T_tilt × A_az)` orientations,
calling `pvlib.irradiance.get_total_irradiance()` once per cell — 8760 timesteps each.

At the default 15°/10° step sizes: T=7, A=36 → **252 iterations × 8760 hours = 2.2M per-cell ops**.
Wall time: ~10 minutes on Streamlit Cloud (blocks the UI thread).

---

## Solution

Replace the nested loop with a single NumPy broadcast over the full `(8760, T, A)` tensor.

Key insight: the Perez sky parameters F1/F2 depend only on airmass and sky state (DHI/DNI/GHI),
not on surface orientation. So the only per-orientation computation is:
1. `cos(AOI)` — geometric, trivially vectorized
2. Diffuse view factors — `(1+cos(tilt))/2`, `sin(tilt)`, `(1-cos(tilt))/2` — vectorized over tilt only
3. The PVWatts DC model — linear in POA, trivially vectorized

For the sweep we use **Hay-Davies** sky diffuse (anisotropic, ~1–2% error vs Perez, zero per-orientation overhead)
and keep full Perez only for the selected-orientation main simulation (`run_simulation`).

---

## Implementation

### Step 1 — Precompute geometry (per time step, shared across all orientations)

```python
import numpy as np
import pvlib
import pandas as pd

# --- Pre-compute once ---
loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
times = tmy_df.index
solar_pos  = loc.get_solarposition(times)
dni_extra  = pvlib.irradiance.get_extra_radiation(times).values  # (N,)

zen_r   = np.radians(solar_pos["apparent_zenith"].values)        # (N,)
az_sun_r = np.radians(solar_pos["azimuth"].values)               # (N,)
cos_z   = np.cos(zen_r)                                           # (N,)
sin_z   = np.sin(zen_r)                                           # (N,)

ghi = tmy_df["ghi"].values   # (N,)
dni = tmy_df["dni"].values   # (N,)
dhi = tmy_df["dhi"].values   # (N,)
t_air = tmy_df["temp_air"].values    # (N,)
ws    = tmy_df["wind_speed"].values  # (N,)

# Hay-Davies anisotropy index (per timestep)
with np.errstate(divide="ignore", invalid="ignore"):
    F = np.where(dni_extra > 0, dni / dni_extra, 0.0).clip(0.0, 1.0)  # (N,)
```

### Step 2 — Broadcast cos(AOI) across the full (N, T, A) grid

```python
tilt_r = np.radians(tilt_arr)   # (T,)
az_r   = np.radians(az_arr)     # (A,)

# Expand dims for broadcasting: axes = [time, tilt, az]
cos_z_  = cos_z[:, None, None]       # (N, 1, 1)
sin_z_  = sin_z[:, None, None]       # (N, 1, 1)
az_sun_ = az_sun_r[:, None, None]    # (N, 1, 1)
cos_t   = np.cos(tilt_r)[None, :, None]  # (1, T, 1)
sin_t   = np.sin(tilt_r)[None, :, None]  # (1, T, 1)
az_p    = az_r[None, None, :]            # (1, 1, A)

cos_aoi = (cos_z_ * cos_t + sin_z_ * sin_t * np.cos(az_sun_ - az_p)).clip(0.0)
# shape: (N, T, A)
```

### Step 3 — Compute POA via Hay-Davies in one shot

```python
dni_  = dni[:, None, None]    # (N, 1, 1)
dhi_  = dhi[:, None, None]
ghi_  = ghi[:, None, None]
F_    = F[:, None, None]

# Guard against near-zero cos(zenith) in circumsolar term
cos_z_safe = np.where(cos_z_ > 0.087, cos_z_, 0.087)  # clip at 85° zenith

poa_direct  = dni_ * cos_aoi                                # (N, T, A)
poa_sky     = dhi_ * (F_ * cos_aoi / cos_z_safe            # circumsolar
                      + (1 - F_) * (1 + cos_t) / 2)        # isotropic diffuse
poa_ground  = ghi_ * albedo * (1 - cos_t) / 2

poa_eff = (poa_direct + poa_sky + poa_ground).clip(0.0)    # (N, T, A)
```

### Step 4 — IAM on beam component (vectorized ASHRAE approximation)

The full `pvlib.iam.physical()` is not vectorizable as-is. Use the ASHRAE approximation:

```python
# ASHRAE: IAM = 1 - b0 * (1/cos(aoi) - 1),  b0 = 0.05 for AR glass
# cos_aoi already computed; guard divide:
cos_aoi_safe = np.where(cos_aoi > 0.01, cos_aoi, 0.01)
iam = (1 - 0.05 * (1 / cos_aoi_safe - 1)).clip(0.0, 1.0)   # (N, T, A)

poa_eff_iam = (poa_direct * iam + poa_sky + poa_ground).clip(0.0)
```

### Step 5 — Cell temperature (vectorized Faiman)

Faiman model: `T_cell = T_air + POA / (U0 + U1 * WS)`, default U0=25, U1=6.84.

```python
t_air_ = t_air[:, None, None]
ws_    = ws[:, None, None]

temp_cell = t_air_ + poa_eff_iam / (25.0 + 6.84 * ws_)      # (N, T, A)
```

### Step 6 — PVWatts DC model (vectorized)

```python
pdc0  = float(module_params.get("pdc0",
    module_params.get("V_mp_ref", 30.0) * module_params.get("I_mp_ref", 8.0)))
gamma = float(module_params.get("gamma_r", -0.004))
if abs(gamma) > 0.1:
    gamma = gamma / 100.0

p_dc = (pdc0 * poa_eff_iam / 1000.0 * (1 + gamma * (temp_cell - 25.0))
        ).clip(0.0) * n_modules                               # (N, T, A)
```

### Step 7 — Loss chain and annual sum

```python
dc_factor = loss_budget.dc_factor
ac_factor = loss_budget.ac_factor
eta_inv   = float(inverter_params.get("eta_inv_nom", 0.96))

p_ac_net = (p_dc * dc_factor * eta_inv * ac_factor).clip(0.0)

# Sum over time axis (axis=0), convert W→kWh (hourly data: dt=1h)
energy_grid = p_ac_net.sum(axis=0) / 1000.0  # (T, A), float32 preferred
```

### Step 8 — Memory budget check

At default 15°/10° steps: N=8760, T=7, A=36 → 2.2M elements.
`float32` → 8.8 MB per array. We allocate ~6 such arrays simultaneously → ~53 MB peak.
At 10°/5° steps: T=10, A=72 → 6.3M elements → ~150 MB peak. Acceptable on Cloud.

For high-resolution sweeps (5°/5°) add a `chunk_tilt` loop to stay under 500 MB:

```python
# Optional chunking for very fine grids
CHUNK = 5  # process 5 tilt values at a time
energy_grid = np.zeros((len(tilt_arr), len(az_arr)), dtype=np.float32)
for i0 in range(0, len(tilt_arr), CHUNK):
    i1 = min(i0 + CHUNK, len(tilt_arr))
    # ... run Steps 2-7 with tilt_arr[i0:i1] ...
    energy_grid[i0:i1, :] = chunk_result
```

---

## Drop-in Replacement

The new `compute_orientation_grid()` keeps the same signature and return type (`np.ndarray` of shape `(T, A)`).
The `@st.cache_data` decorator stays — parameters haven't changed.

The only behavioral change: grid values will differ by ≤2% from the loop version due to Hay-Davies vs Perez
and ASHRAE vs physical IAM. The optimal orientation (argmax) is unaffected in practice.

---

## Validation

After implementing, run both versions on a test location (e.g., Berlin, 52.5°N) and compare:
- Max energy cell should agree within 1%
- Optimal (tilt, az) should match exactly (or by 1 step at most)
- Wall time target: < 5 seconds for 15°/10° grid on Cloud

```python
# Quick smoke test in a notebook or script:
import time
t0 = time.time()
grid_new = compute_orientation_grid_vectorized(...)
print(f"New: {time.time()-t0:.1f}s, max={grid_new.max():.0f} kWh")

t0 = time.time()
grid_old = compute_orientation_grid_loop(...)
print(f"Old: {time.time()-t0:.1f}s, max={grid_old.max():.0f} kWh")

print(f"Max diff: {abs(grid_new - grid_old).max():.0f} kWh")
print(f"Opt new: {np.unravel_index(grid_new.argmax(), grid_new.shape)}")
print(f"Opt old: {np.unravel_index(grid_old.argmax(), grid_old.shape)}")
```

---

## UX Improvement Alongside This

With sweep time dropping from ~10 min to ~5 sec, change the Orientation Optimizer tab behavior:
- Remove the explicit "Run Orientation Sweep" button
- Run sweep automatically whenever location/system changes (still cache via `@st.cache_data`)
- Add a progress bar or spinner that resolves quickly

This requires removing the `run_sweep = st.button(...)` guard in `app.py:225` and replacing it
with a direct call gated only on cache invalidation.
