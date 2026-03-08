# Plan 04 — Horizon Shading Input

**Priority:** Medium
**Effort:** Medium (1 day)
**Files affected:** `core/losses.py`, `core/energy.py`, `ui/sidebar.py`, `app.py`

---

## Motivation

The current waterfall already reserves a slot "Horizon & far shading" but sets it to
`(GHI_total - POA_transposed)` — this is the transposition loss, not actual shading.
True horizon shading from nearby obstacles (rooftop parapets, trees, chimneys) can
reduce yield by 5–20%. This plan adds a simple 8-point horizon profile input that
masks the beam component when the sun is geometrically below the user-defined horizon.

---

## Inputs: Horizon Profile

Add a collapsible "Near Shading / Horizon" section to `ui/sidebar.py`:

```python
with st.sidebar.expander("Near Shading / Horizon", expanded=False):
    st.caption(
        "Enter the horizon elevation angle (° above horizontal) at 8 cardinal directions. "
        "Use 0° for an unobstructed horizon."
    )
    horizon_azimuths = [0, 45, 90, 135, 180, 225, 270, 315]
    labels = ["N (0°)", "NE (45°)", "E (90°)", "SE (135°)",
              "S (180°)", "SW (225°)", "W (270°)", "NW (315°)"]
    cols1, cols2 = st.columns(2), st.columns(2)  # 2x4 grid
    horizon_elevations = []
    for i, (az, label) in enumerate(zip(horizon_azimuths, labels)):
        col = [cols1, cols2][i // 4][i % 4]  # adjust layout as needed
        elev = col.number_input(label, min_value=0.0, max_value=60.0,
                                value=0.0, step=0.5, key=f"hz_{az}")
        horizon_elevations.append(elev)
    cfg["horizon_azimuths"] = horizon_azimuths
    cfg["horizon_elevations"] = horizon_elevations
```

Default is all zeros (no shading). The profile is interpolated to full azimuth resolution
at simulation time using linear interpolation with wrap-around at 0°/360°.

---

## Physics Implementation

### Step 1 — Interpolate horizon profile

In `core/energy.py`, before the main simulation loop:

```python
def _interpolate_horizon(
    horizon_azimuths: list[float],
    horizon_elevations: list[float],
    query_azimuths: np.ndarray,
) -> np.ndarray:
    """
    Interpolate the 8-point horizon profile to arbitrary azimuth values.
    Uses linear interpolation with periodic (wrap-around) boundary conditions.
    """
    az = np.array(horizon_azimuths + [horizon_azimuths[0] + 360])  # close the loop
    el = np.array(horizon_elevations + [horizon_elevations[0]])
    # Normalize query to [0, 360)
    q = np.mod(query_azimuths, 360.0)
    return np.interp(q, az, el)
```

### Step 2 — Compute sun elevation angle

Sun elevation = 90° - zenith angle. Already available from `solar_pos["apparent_elevation"]`
(or `90 - solar_pos["apparent_zenith"]`).

### Step 3 — Compute horizon elevation at each sun azimuth

```python
sun_az = solar_pos["azimuth"].values          # (N,) degrees
sun_el = solar_pos["apparent_elevation"].values  # (N,) degrees

# Horizon elevation at each timestep's sun azimuth
hz_at_sun = _interpolate_horizon(
    horizon_azimuths, horizon_elevations, sun_az
)  # (N,)
```

### Step 4 — Compute beam shading factor

```python
# Sun is shaded when its elevation is below the horizon profile
# Returns 1.0 (unshaded) or 0.0 (shaded) — binary mask
beam_unshaded = (sun_el > hz_at_sun).astype(float)  # (N,)
```

For a smoother result (avoids abrupt steps in energy charts), apply a sigmoid transition
over 1° above/below the horizon line instead of a binary mask:

```python
delta = sun_el - hz_at_sun            # positive = sun above horizon
beam_unshaded = 1 / (1 + np.exp(-4 * delta))  # smooth step, 50% at delta=0
```

### Step 5 — Apply to beam DNI component

In `run_simulation()`, modify the POA computation section:

```python
# Apply horizon shading to beam component before transposition
dni_shaded = tmy_df["dni"] * pd.Series(beam_unshaded, index=tmy_df.index)

poa = pvlib.irradiance.get_total_irradiance(
    ...
    dni=dni_shaded,    # ← shaded DNI
    ghi=tmy_df["ghi"],
    dhi=tmy_df["dhi"],
    ...
)
```

Note: GHI and DHI are not masked — horizon shading only blocks direct beam.
In reality, nearby obstacles also reduce diffuse sky view factor, but that requires
a more complex angular integration. The beam-only approach is a common simplification
used by PVsyst's "far shading" mode.

---

## Loss Waterfall Update

The waterfall currently computes horizon loss as `(GHI_total - POA_transposed)`.
With explicit horizon shading, replace this with:

```python
# Before shading:
poa_unshaded = get_total_irradiance(... dni=tmy_df["dni"] ...)["poa_global"].sum()
# After shading:
poa_shaded   = poa_global.sum()   # already computed with shaded DNI
shading_loss  = max(poa_unshaded - poa_shaded, 0) / 1000  # kWh
optical_loss  = max(ghi_total_kwh - poa_unshaded_kwh, 0)  # transposition
```

Update `build_loss_waterfall()` in `core/losses.py` to accept a `shading_loss_kwh` parameter
and split the "Horizon & far shading" entry into two rows:
- "Transposition" (diffuse/ground component of ETR → POA gap)
- "Near shading" (beam blocked by horizon profile)

---

## `run_simulation()` Signature Change

Add two new optional parameters:

```python
def run_simulation(
    ...,
    horizon_azimuths: list[float] | None = None,
    horizon_elevations: list[float] | None = None,
) -> SimResult:
    if horizon_azimuths and horizon_elevations:
        beam_unshaded = _compute_shading_mask(solar_pos, horizon_azimuths, horizon_elevations)
        dni_effective = tmy_df["dni"] * pd.Series(beam_unshaded, index=tmy_df.index)
    else:
        dni_effective = tmy_df["dni"]
```

The default `None` means no shading, preserving backwards compatibility.

---

## UI: Horizon Profile Visualizer

Add a polar chart to visualize the entered horizon profile alongside the annual sun path.
In `ui/charts.py`:

```python
def horizon_profile_chart(
    lat: float, lon: float, elevation_m: float,
    horizon_azimuths: list[float], horizon_elevations: list[float],
) -> go.Figure:
    """Polar chart: sun path overlay + user horizon profile."""
    # Draw horizon profile as shaded region
    # Overlay winter solstice / equinox / summer solstice sun paths
    ...
```

Display this in the sidebar expander or as an optional chart in Tab 5 (Sun Path).

---

## Validation

For a test with S-facing 30° tilt panel and a 15° obstacle at S (180°):
- The morning and evening hours are unaffected
- Midday hours with sun elevation < 15° are blocked (winter at high latitudes)
- Expected yield reduction: 5–15% at 52°N vs 1–3% at 35°N
