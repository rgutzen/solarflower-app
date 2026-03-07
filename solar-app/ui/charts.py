# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Plotly figure builders for the Solar Advisor web app.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pvlib

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Brand colors (Phase 1)
SUN_COLOR    = "#F5A623"  # Amber - primary
BLUE_COLOR   = "#2D7DD2"  # Sky blue - secondary
GREY_COLOR   = "#AAAAAA"   # Neutral
RED_COLOR    = "#E63946"   # Semantic danger

# Extended palette: Earth & Dusk (Phase 1)
TERRACOTTA   = "#C75B39"  # Earth, clay, groundedness
OCHRE        = "#D4A03A"  # Golden earth, complementary accent
CLAY         = "#A67B5B"  # Ground, roots
DUSK         = "#6B5B95"  # Twilight, transition
DAWN         = "#E8B4B8"  # Morning, renewal
MIDNIGHT     = "#2D2D44"  # Night, rest
GREEN_COLOR  = "#4CAF50"  # Growth, nature


# ---------------------------------------------------------------------------
# Tab 1: Annual Summary — Loss Waterfall
# ---------------------------------------------------------------------------

_WATERFALL_LABELS = {
    "Horizon & far shading": "Orientation losses",
    "Transposition": "Orientation losses",
    "Near shading":  "Near shading (horizon)",
    "IAM (angle of incidence)": "Glass reflections",
    "Temperature derating": "Heat derating",
    "Soiling": "Soiling (dust & dirt)",
    "LID": "First-year aging (LID)",
    "Mismatch": "Panel mismatch",
    "DC wiring": "DC cable losses",
    "Inverter": "Inverter conversion",
    "Availability": "Downtime",
    "AC wiring": "AC cable losses",
    "Transformer": "Transformer",
}
GREEN_COLOR = "#28C840"


def loss_waterfall(waterfall: dict[str, float], net_kwh: float) -> go.Figure:
    """Horizontal waterfall chart showing the loss chain from gross ETR to net yield."""
    friendly = {_WATERFALL_LABELS.get(k, k): v for k, v in waterfall.items()}
    labels = list(friendly.keys()) + ["Net AC yield"]
    losses = list(friendly.values())
    values = [-v for v in losses] + [net_kwh]

    gross = net_kwh + sum(losses)
    running = gross

    bar_bases = []
    bar_values = []
    colors = []

    for v in losses:
        bar_bases.append(running - v)
        bar_values.append(-v)
        running -= v
        colors.append(RED_COLOR)

    bar_bases.append(0.0)
    bar_values.append(net_kwh)
    colors.append(SUN_COLOR)

    fig = go.Figure(go.Bar(
        y=labels,
        x=bar_values,
        base=bar_bases,
        orientation="h",
        marker_color=colors,
        text=[f"{abs(v):.0f} kWh" for v in bar_values],
        textposition="inside",
        insidetextanchor="middle",
    ))
    fig.add_vline(x=gross, line_dash="dash", line_color=GREY_COLOR,
                  annotation_text=f"Gross solar input {gross:.0f} kWh",
                  annotation_position="top")
    fig.update_layout(
        title="Where does the energy go? — Annual loss chain",
        xaxis_title="Energy [kWh/year]",
        yaxis=dict(autorange="reversed"),
        height=420,
        margin=dict(l=180, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig


def monthly_summary(
    monthly_yield: pd.Series,
    monthly_pr: pd.Series,
    monthly_yield_opt: pd.Series | None = None,
) -> go.Figure:
    """Monthly kWh/day bars + PR line, with optional optimal-orientation bars."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    x = list(range(12))

    if monthly_yield_opt is not None:
        fig.add_trace(go.Bar(
            x=x, y=monthly_yield_opt.values, name="Optimal orientation",
            marker_color=BLUE_COLOR, opacity=0.4, width=0.4,
            offset=-0.2,
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=x, y=monthly_yield.values, name="Selected orientation",
            marker_color=SUN_COLOR, opacity=0.9, width=0.4,
            offset=0.2,
        ), secondary_y=False)
    else:
        fig.add_trace(go.Bar(
            x=x, y=monthly_yield.values, name="Avg daily yield",
            marker_color=SUN_COLOR, opacity=0.9,
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=(monthly_pr * 100).values, name="PR [%]",
        mode="lines+markers", line=dict(color=GREY_COLOR, width=2),
        marker=dict(size=5),
    ), secondary_y=True)

    fig.update_layout(
        title="Monthly yield — average kWh generated per day",
        xaxis=dict(tickmode="array", tickvals=x, ticktext=MONTH_LABELS),
        height=350, margin=dict(l=60, r=60, t=50, b=40),
        legend=dict(orientation="h", y=1.1),
        barmode="overlay",
    )
    fig.update_yaxes(title_text="Avg daily yield [kWh/day]", secondary_y=False)
    fig.update_yaxes(title_text="Performance Ratio [%]", secondary_y=True,
                     range=[0, 120])
    return fig


# ---------------------------------------------------------------------------
# Tab 2: Orientation Optimizer
# ---------------------------------------------------------------------------

def orientation_heatmap(
    energy_grid: np.ndarray,
    tilt_arr: np.ndarray,
    az_arr: np.ndarray,
    selected_tilt: float,
    selected_az: float,
) -> go.Figure:
    """Heatmap of annual yield vs tilt × azimuth with optimal and selected markers."""
    opt_i, opt_j = np.unravel_index(np.argmax(energy_grid), energy_grid.shape)
    opt_tilt = tilt_arr[opt_i]
    opt_az   = az_arr[opt_j]
    opt_val  = energy_grid[opt_i, opt_j]

    fig = go.Figure(go.Heatmap(
        z=energy_grid,
        x=az_arr,
        y=tilt_arr,
        colorscale="YlOrRd",
        colorbar=dict(title="kWh/yr"),
        hovertemplate="Tilt: %{y}°<br>Azimuth: %{x}°<br>Yield: %{z:.0f} kWh<extra></extra>",
    ))

    # Optimal marker
    fig.add_trace(go.Scatter(
        x=[opt_az], y=[opt_tilt], mode="markers+text",
        marker=dict(symbol="star", size=16, color="white",
                    line=dict(color="black", width=1.5)),
        text=[f"Opt: {opt_val:.0f} kWh"],
        textposition="top center",
        name="Optimal",
    ))

    # Selected marker
    fig.add_trace(go.Scatter(
        x=[selected_az], y=[selected_tilt], mode="markers",
        marker=dict(symbol="cross", size=14, color=BLUE_COLOR,
                    line=dict(color="white", width=1.5)),
        name="Selected",
    ))

    fig.update_layout(
        title=f"Annual yield by orientation — best: tilt {opt_tilt}°, facing {opt_az}° → {opt_val:,.0f} kWh/yr",
        xaxis_title="Facing direction [°]  (0° = North · 90° = East · 180° = South · 270° = West)",
        yaxis_title="Tilt angle [°]  (0° = flat · 90° = vertical)",
        height=420,
        margin=dict(l=60, r=20, t=60, b=50),
        legend=dict(orientation="h", y=1.1),
    )
    return fig, float(opt_tilt), float(opt_az), float(opt_val)


def yield_vs_tilt(
    energy_grid: np.ndarray,
    tilt_arr: np.ndarray,
    az_arr: np.ndarray,
    selected_az: float,
    selected_tilt: float,
) -> go.Figure:
    """Yield vs tilt curves for south-facing and user-selected azimuth."""
    # South-facing index (az closest to 180°)
    south_j = int(np.argmin(np.abs(az_arr - 180)))
    sel_j   = int(np.argmin(np.abs(az_arr - selected_az)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tilt_arr, y=energy_grid[:, south_j],
        name="South-facing (180°)", line=dict(color=SUN_COLOR, width=2),
    ))
    if sel_j != south_j:
        fig.add_trace(go.Scatter(
            x=tilt_arr, y=energy_grid[:, sel_j],
            name=f"Selected ({selected_az}°)", line=dict(color=BLUE_COLOR, width=2, dash="dash"),
        ))

    # Mark selected point
    sel_i = int(np.argmin(np.abs(tilt_arr - selected_tilt)))
    fig.add_trace(go.Scatter(
        x=[selected_tilt], y=[energy_grid[sel_i, sel_j]],
        mode="markers", marker=dict(size=10, color=BLUE_COLOR),
        name="Current", showlegend=True,
    ))
    fig.update_layout(
        title="How tilt angle affects annual yield",
        xaxis_title="Tilt angle [°]  (0° = flat · 90° = vertical)",
        yaxis_title="Annual yield [kWh/yr]",
        height=300, margin=dict(l=60, r=20, t=50, b=50),
        legend=dict(orientation="h", y=1.1),
    )
    return fig


# ---------------------------------------------------------------------------
# Tab 3: Daily Irradiance
# ---------------------------------------------------------------------------

def daily_irradiance(
    tmy_df: pd.DataFrame,
    lat: float,
    lon: float,
    elevation_m: float,
    tilt_deg: float,
    panel_az_deg: float,
    albedo: float,
    doy: int,
) -> go.Figure:
    """Stacked area: POA components + solar altitude for a single day."""
    import pvlib

    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    # Select one day from TMY
    times = pd.date_range(f"2023-{_doy_to_mmdd(doy)}", periods=24, freq="1h", tz="UTC")
    day_mask = (tmy_df.index.month == times[0].month) & (tmy_df.index.day == times[0].day)
    day_df = tmy_df[day_mask].copy()
    if len(day_df) == 0:
        return go.Figure().update_layout(title="No data for this day")

    solar_pos = loc.get_solarposition(day_df.index)
    dni_extra = pvlib.irradiance.get_extra_radiation(day_df.index)
    airmass   = loc.get_airmass(solar_position=solar_pos)

    poa = pvlib.irradiance.get_total_irradiance(
        tilt_deg, panel_az_deg,
        solar_pos["apparent_zenith"], solar_pos["azimuth"],
        day_df["dni"], day_df["ghi"], day_df["dhi"],
        dni_extra=dni_extra,
        airmass=airmass["airmass_relative"],
        model="perez", albedo=albedo,
    )

    hours = day_df.index.hour + day_df.index.minute / 60
    altitude = 90 - solar_pos["apparent_zenith"].clip(upper=90)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=hours, y=poa["poa_direct"].clip(lower=0),
        name="Direct beam", stackgroup="poa",
        fillcolor="rgba(245,166,35,0.7)", line=dict(width=0),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hours, y=poa["poa_diffuse"].clip(lower=0),
        name="Sky diffuse", stackgroup="poa",
        fillcolor="rgba(135,206,250,0.6)", line=dict(width=0),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hours, y=poa["poa_ground_diffuse"].clip(lower=0),
        name="Ground reflected", stackgroup="poa",
        fillcolor="rgba(144,238,144,0.5)", line=dict(width=0),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hours, y=altitude, name="Solar altitude [°]",
        mode="lines", line=dict(color=GREY_COLOR, width=2, dash="dot"),
    ), secondary_y=True)

    import datetime
    date_str = (datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)).strftime("%B %d")
    fig.update_layout(
        title=f"Solar energy on your panel surface — {date_str}",
        xaxis_title="Hour of day (UTC)", height=360,
        margin=dict(l=60, r=60, t=50, b=50),
        legend=dict(orientation="h", y=1.12),
    )
    fig.update_yaxes(title_text="Solar power on panel [W/m²]", secondary_y=False)
    fig.update_yaxes(title_text="Sun height above horizon [°]", secondary_y=True, range=[0, 90])
    return fig


# ---------------------------------------------------------------------------
# Tab 4: Sun Path Diagram
# ---------------------------------------------------------------------------

def sun_path_polar(lat: float, lon: float, elevation_m: float, selected_doy: int) -> go.Figure:
    """Polar sun path diagram: elevation vs azimuth for solstices, equinox, and selected day."""
    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")

    special_days = {
        "Winter solstice (Dec 21)": 355,
        "Equinox (Mar 20)": 79,
        "Summer solstice (Jun 21)": 172,
        "Selected day": selected_doy,
    }
    colors = [BLUE_COLOR, GREY_COLOR, SUN_COLOR, RED_COLOR]
    dashes = ["solid", "dot", "solid", "dash"]

    fig = go.Figure()

    for (label, doy), color, dash in zip(special_days.items(), colors, dashes):
        import datetime
        date = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
        times = pd.date_range(
            datetime.datetime(2023, date.month, date.day, 0, 0),
            periods=145, freq="10min", tz="UTC",
        )
        sp = loc.get_solarposition(times)
        alt = (90 - sp["apparent_zenith"].clip(upper=90)).clip(lower=0)
        az  = sp["azimuth"]
        mask = alt > 0
        if mask.sum() < 2:
            continue
        # Polar: r = 90 - elevation (so zenith=0 is center, horizon=90 is edge)
        r = 90 - alt[mask]
        theta = az[mask]

        fig.add_trace(go.Scatterpolar(
            r=r, theta=theta,
            mode="lines",
            name=label,
            line=dict(color=color, width=2, dash=dash),
        ))

    fig.update_layout(
        title="Sun path across the sky — centre = directly overhead, edge = horizon",
        polar=dict(
            angularaxis=dict(
                tickmode="array",
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                direction="clockwise",
                rotation=90,
            ),
            radialaxis=dict(
                tickmode="array",
                tickvals=[0, 15, 30, 45, 60, 75, 90],
                ticktext=["90°", "75°", "60°", "45°", "30°", "15°", "0°"],
                range=[0, 90],
            ),
        ),
        height=420,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", y=-0.1),
    )
    return fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doy_to_mmdd(doy: int) -> str:
    import datetime
    d = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
    return d.strftime("%m-%d")


# ---------------------------------------------------------------------------
# Plan 05: Lifetime Yield Projection
# ---------------------------------------------------------------------------

def lifetime_yield_chart(lifetime_yield: np.ndarray) -> go.Figure:
    """Bar chart of annual yield decay + cumulative yield on secondary axis."""
    years      = list(range(1, len(lifetime_yield) + 1))
    cumulative = np.cumsum(lifetime_yield) / 1000.0   # MWh

    fig = go.Figure()
    fig.add_bar(
        x=years, y=lifetime_yield,
        name="Annual yield (kWh)",
        marker_color=[SUN_COLOR if y == 1 else BLUE_COLOR for y in years],
        opacity=0.85,
    )
    fig.add_scatter(
        x=years, y=cumulative,
        name="Cumulative yield (MWh)",
        yaxis="y2",
        line=dict(color=GREEN_COLOR, width=2.5),
        mode="lines",
    )
    # Typical 80% warranty threshold
    y1 = lifetime_yield[0]
    fig.add_hline(
        y=y1 * 0.80, line_dash="dot", line_color="rgba(255,165,0,0.5)",
        annotation_text="80% yr-1 (typical warranty)",
        annotation_position="top left",
    )
    fig.update_layout(
        title="Annual Yield Over Project Lifetime",
        xaxis_title="Year",
        yaxis_title="Annual yield (kWh)",
        yaxis2=dict(
            title="Cumulative yield (MWh)",
            overlaying="y", side="right",
            showgrid=False,
        ),
        template="plotly_dark",
        height=350,
        margin=dict(l=60, r=80, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ---------------------------------------------------------------------------
# Plan 02: Economic Analysis Charts
# ---------------------------------------------------------------------------

def cashflow_chart(econ) -> go.Figure:
    """
    Annual savings bars + cumulative cash-flow line.
    Green = profit region, amber = payback period.
    """
    years = list(range(1, len(econ.annual_savings_arr) + 1))

    fig = go.Figure()
    fig.add_bar(
        x=years, y=econ.annual_savings_arr,
        name="Annual savings (€)",
        marker_color=SUN_COLOR, opacity=0.8,
    )
    fig.add_scatter(
        x=years, y=econ.cumulative_cf_arr,
        name="Cumulative cash flow (€)",
        line=dict(color=BLUE_COLOR, width=2.5),
        mode="lines+markers",
        marker=dict(size=4),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        title="Cash Flow Over Project Lifetime",
        xaxis_title="Year",
        yaxis_title="€",
        template="plotly_dark",
        height=350,
        margin=dict(l=60, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def yield_degradation_chart(econ) -> go.Figure:
    """Line chart showing annual yield decay over project lifetime."""
    years = list(range(1, len(econ.annual_yield_arr) + 1))
    y1    = econ.annual_yield_arr[0]

    fig = go.Figure()
    fig.add_scatter(
        x=years, y=econ.annual_yield_arr,
        name="Annual yield (kWh)",
        line=dict(color=SUN_COLOR, width=2),
        fill="tozeroy", fillcolor="rgba(245,166,35,0.15)",
    )
    fig.add_hline(
        y=y1 * 0.80, line_dash="dot", line_color="rgba(255,165,0,0.5)",
        annotation_text="80% yr-1", annotation_position="top left",
    )
    fig.update_layout(
        title="Annual Yield Degradation",
        xaxis_title="Year",
        yaxis_title="Annual yield (kWh)",
        template="plotly_dark",
        height=280,
        margin=dict(l=60, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Plan 04: Horizon Profile Chart (shown in Sun Path tab)
# ---------------------------------------------------------------------------

def horizon_profile_chart(
    lat: float, lon: float, elevation_m: float,
    horizon_azimuths: tuple[float, ...],
    horizon_elevations: tuple[float, ...],
) -> go.Figure:
    """
    Polar chart: user horizon profile (shaded region) overlaid on the annual
    sun path for winter solstice, equinox, and summer solstice.
    """
    import datetime

    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")

    # --- Horizon profile: close the loop at 360° ---
    hz_az = list(horizon_azimuths) + [horizon_azimuths[0] + 360]
    hz_el = list(horizon_elevations) + [horizon_elevations[0]]
    # Interpolate to full 1° resolution for smooth shading
    az_full = np.arange(0, 361)
    el_full = np.interp(az_full, hz_az, hz_el)
    # Polar r: convert elevation to zenith distance (90° = horizon in polar)
    r_hz = 90 - el_full

    fig = go.Figure()

    # Shaded horizon obstruction zone
    fig.add_trace(go.Scatterpolar(
        r=np.concatenate([r_hz, [90, 90, r_hz[0]]]),
        theta=np.concatenate([az_full, [az_full[-1], az_full[0], az_full[0]]]),
        fill="toself",
        fillcolor="rgba(150,150,150,0.25)",
        line=dict(color=GREY_COLOR, width=2),
        name="Horizon profile",
        mode="lines",
    ))

    # Sun paths for special days
    special_days = [
        ("Winter solstice (Dec 21)", 355, BLUE_COLOR, "solid"),
        ("Equinox (Mar 20)",          79, GREY_COLOR, "dot"),
        ("Summer solstice (Jun 21)",  172, SUN_COLOR,  "solid"),
    ]
    for label, doy, color, dash in special_days:
        date = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
        times = pd.date_range(
            datetime.datetime(2023, date.month, date.day, 0, 0),
            periods=145, freq="10min", tz="UTC",
        )
        sp  = loc.get_solarposition(times)
        alt = (90 - sp["apparent_zenith"].clip(upper=90)).clip(lower=0)
        az  = sp["azimuth"]
        mask = alt > 0
        if mask.sum() < 2:
            continue
        r     = 90 - alt[mask]
        theta = az[mask]
        fig.add_trace(go.Scatterpolar(
            r=r, theta=theta, mode="lines",
            name=label, line=dict(color=color, width=2, dash=dash),
        ))

    fig.update_layout(
        title="Horizon Profile & Sun Path — shaded area = obstruction zone",
        polar=dict(
            angularaxis=dict(
                tickmode="array",
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                direction="clockwise",
                rotation=90,
            ),
            radialaxis=dict(
                tickmode="array",
                tickvals=[0, 15, 30, 45, 60, 75, 90],
                ticktext=["90°", "75°", "60°", "45°", "30°", "15°", "0°"],
                range=[0, 90],
            ),
        ),
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", y=-0.12),
    )
    return fig
