# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Plotly figure builders for the Solar Advisor web app.

Organic / solarpunk design system:
  Lora serif for titles, warm neutral backgrounds, earth-toned palette.
"""

from __future__ import annotations
import copy
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pvlib

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------------------------------------------------------------------
# Organic colour palette (matches the website design system)
# ---------------------------------------------------------------------------
SUN_COLOR    = "#E8920E"   # amber-dark  — primary accent
AMBER_LIGHT  = "#F5A623"   # amber-mid   — fills / highlights
EARTH_COLOR  = "#4A7A58"   # sage green  — cumulative / positive
TERRACOTTA   = "#C75B39"   # terracotta  — losses / negative
WINTER_COLOR = "#5B8DC4"   # muted blue  — winter / comparison
CLAY         = "#A67B5B"   # clay brown  — winter months
DUSK         = "#6B5B95"   # twilight    — spare accent
INK_COLOR    = "#2D3B2D"   # dark ink    — title / strong text
INK_LIGHT    = "#4A6050"   # medium ink  — body text / labels
GREY_COLOR   = "#6A7F72"   # warm grey   — secondary lines
GREEN_COLOR  = "#3D9A6B"   # earthy green — net yield
BLUE_COLOR   = "#4A85C0"   # muted blue  — selected orientation
RED_COLOR    = "#C75B39"   # same as terracotta for semantic loss

_GRID    = "rgba(74,96,80,0.10)"   # warm green grid lines
_WARM_BG = "#FEFDF5"               # warm off-white for hover labels

# ---------------------------------------------------------------------------
# Shared layout base — applied to every figure
# ---------------------------------------------------------------------------
LAYOUT_BASE: dict = dict(
    font=dict(family='"Lora", Georgia, serif', size=13, color=INK_LIGHT),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,252,248,0.45)",
    hoverlabel=dict(
        bgcolor=_WARM_BG,
        bordercolor="rgba(76,175,80,0.2)",
        font=dict(family='"Inter", sans-serif', size=12, color=INK_COLOR),
    ),
)


def _layout(**overrides) -> dict:
    """Return LAYOUT_BASE merged with caller-supplied overrides (deep copy)."""
    out = copy.deepcopy(LAYOUT_BASE)
    out.update(overrides)
    return out


def _title(text: str, size: int = 15) -> dict:
    """Organic Lora serif title dict."""
    return dict(text=text, font=dict(family='"Lora", Georgia, serif', size=size, color=INK_COLOR))


def _xgrid(**extra) -> dict:
    return dict(gridcolor=_GRID, zerolinecolor=_GRID, zerolinewidth=1, **extra)


def _ygrid(**extra) -> dict:
    return dict(gridcolor=_GRID, zerolinecolor=_GRID, zerolinewidth=1, **extra)


# ---------------------------------------------------------------------------
# Waterfall label friendly names
# ---------------------------------------------------------------------------
_WATERFALL_LABELS = {
    "Horizon & far shading":       "Orientation losses",
    "Transposition":               "Orientation losses",
    "Near shading":                "Near shading (horizon)",
    "IAM (angle of incidence)":    "Glass reflections",
    "Temperature derating":        "Heat derating",
    "Soiling":                     "Soiling (dust & dirt)",
    "LID":                         "First-year aging (LID)",
    "Mismatch":                    "Panel mismatch",
    "DC wiring":                   "DC cable losses",
    "Inverter":                    "Inverter conversion",
    "Availability":                "Downtime",
    "AC wiring":                   "AC cable losses",
    "Transformer":                 "Transformer",
}


# ---------------------------------------------------------------------------
# Tab 1: Annual Summary
# ---------------------------------------------------------------------------

def loss_waterfall(waterfall: dict[str, float], net_kwh: float) -> go.Figure:
    """Horizontal waterfall chart showing the loss chain from gross ETR to net yield."""
    friendly = {_WATERFALL_LABELS.get(k, k): v for k, v in waterfall.items()}
    labels   = list(friendly.keys()) + ["Net AC yield"]
    losses   = list(friendly.values())

    gross = net_kwh + sum(losses)
    running = gross
    bar_bases, bar_values, colors = [], [], []

    for v in losses:
        bar_bases.append(running - v)
        bar_values.append(-v)
        running -= v
        colors.append(TERRACOTTA)

    bar_bases.append(0.0)
    bar_values.append(net_kwh)
    colors.append(SUN_COLOR)

    fig = go.Figure(go.Bar(
        y=labels, x=bar_values, base=bar_bases,
        orientation="h", marker_color=colors,
        text=[f"{abs(v):.0f} kWh" for v in bar_values],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color=_WARM_BG, size=12),
    ))
    fig.add_vline(
        x=gross, line_dash="dash", line_color=GREY_COLOR,
        annotation_text=f"Gross solar input {gross:.0f} kWh",
        annotation_font_color=INK_LIGHT, annotation_font_size=12,
        annotation_position="top",
    )
    fig.update_layout(**_layout(
        title=_title("Where does the energy go? — Annual loss chain"),
        xaxis=dict(title="Energy [kWh/year]", **_xgrid()),
        yaxis=dict(autorange="reversed"),
        height=420, margin=dict(l=195, r=20, t=55, b=50),
        showlegend=False,
    ))
    return fig


def monthly_summary(
    monthly_yield: pd.Series,
    monthly_pr: pd.Series,
    monthly_yield_opt: pd.Series | None = None,
) -> go.Figure:
    """Monthly kWh/day bars + PR line, with optional optimal-orientation bars."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    x = list(range(12))

    seasonal = [
        WINTER_COLOR, WINTER_COLOR,
        EARTH_COLOR,  EARTH_COLOR,  EARTH_COLOR,
        SUN_COLOR,    SUN_COLOR,    SUN_COLOR,
        TERRACOTTA,   TERRACOTTA,
        CLAY,         CLAY,
    ]

    if monthly_yield_opt is not None:
        fig.add_trace(go.Bar(
            x=x, y=monthly_yield_opt.values, name="Optimal orientation",
            marker_color=BLUE_COLOR, opacity=0.45, width=0.4, offset=-0.2,
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=x, y=monthly_yield.values, name="Selected orientation",
            marker_color=seasonal, opacity=0.9, width=0.4, offset=0.2,
        ), secondary_y=False)
    else:
        fig.add_trace(go.Bar(
            x=x, y=monthly_yield.values, name="Avg daily yield",
            marker_color=seasonal, opacity=0.9,
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=(monthly_pr * 100).values, name="PR [%]",
        mode="lines+markers", line=dict(color=GREY_COLOR, width=2),
        marker=dict(size=5),
    ), secondary_y=True)

    fig.update_layout(**_layout(
        title=_title("Monthly yield — average kWh generated per day"),
        xaxis=dict(tickmode="array", tickvals=x, ticktext=MONTH_LABELS, **_xgrid()),
        height=360, margin=dict(l=65, r=65, t=55, b=50),
        legend=dict(orientation="h", y=1.1, font=dict(size=12, color=INK_COLOR)),
        barmode="overlay",
    ))
    fig.update_yaxes(
        title_text="Avg daily yield [kWh/day]", secondary_y=False,
        gridcolor=_GRID, zerolinecolor=_GRID, color=INK_LIGHT,
    )
    fig.update_yaxes(
        title_text="Performance Ratio [%]", secondary_y=True,
        range=[0, 120], showgrid=False, color=GREY_COLOR,
    )
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
    opt_tilt = tilt_arr[opt_i]; opt_az = az_arr[opt_j]; opt_val = energy_grid[opt_i, opt_j]

    fig = go.Figure(go.Heatmap(
        z=energy_grid, x=az_arr, y=tilt_arr,
        colorscale=[
            [0.00, "#E8F5E9"], [0.35, "#FFF3DC"],
            [0.70, "#F5A623"], [1.00, "#9A6207"],
        ],
        colorbar=dict(title="kWh/yr", tickfont=dict(size=12, color=INK_LIGHT)),
        hovertemplate="Tilt: %{y}°<br>Azimuth: %{x}°<br>Yield: %{z:.0f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[opt_az], y=[opt_tilt], mode="markers+text",
        marker=dict(symbol="star", size=16, color=_WARM_BG,
                    line=dict(color=INK_COLOR, width=1.5)),
        text=[f"Opt: {opt_val:.0f} kWh"], textposition="top center",
        textfont=dict(color=INK_COLOR, size=12), name="Optimal",
    ))
    fig.add_trace(go.Scatter(
        x=[selected_az], y=[selected_tilt], mode="markers",
        marker=dict(symbol="cross", size=14, color=BLUE_COLOR,
                    line=dict(color=_WARM_BG, width=1.5)),
        name="Selected",
    ))
    fig.update_layout(**_layout(
        title=_title(f"Annual yield by orientation — best: tilt {opt_tilt}°, facing {opt_az}° → {opt_val:,.0f} kWh/yr"),
        xaxis=dict(title="Facing direction [°]  (0° = N · 90° = E · 180° = S · 270° = W)", **_xgrid()),
        yaxis=dict(title="Tilt angle [°]", **_ygrid()),
        height=420, margin=dict(l=65, r=20, t=65, b=55),
        legend=dict(orientation="h", y=1.1, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig, float(opt_tilt), float(opt_az), float(opt_val)


def yield_vs_tilt(
    energy_grid: np.ndarray,
    tilt_arr: np.ndarray,
    az_arr: np.ndarray,
    selected_az: float,
    selected_tilt: float,
) -> go.Figure:
    """Yield vs tilt curves for south-facing and user-selected azimuth."""
    south_j = int(np.argmin(np.abs(az_arr - 180)))
    sel_j   = int(np.argmin(np.abs(az_arr - selected_az)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tilt_arr, y=energy_grid[:, south_j],
        name="South-facing (180°)", line=dict(color=SUN_COLOR, width=2.5),
    ))
    if sel_j != south_j:
        fig.add_trace(go.Scatter(
            x=tilt_arr, y=energy_grid[:, sel_j],
            name=f"Selected ({selected_az}°)",
            line=dict(color=BLUE_COLOR, width=2, dash="dash"),
        ))
    sel_i = int(np.argmin(np.abs(tilt_arr - selected_tilt)))
    fig.add_trace(go.Scatter(
        x=[selected_tilt], y=[energy_grid[sel_i, sel_j]],
        mode="markers",
        marker=dict(size=12, color=BLUE_COLOR, line=dict(color=_WARM_BG, width=1.5)),
        name="Current", showlegend=True,
    ))
    fig.update_layout(**_layout(
        title=_title("How tilt angle affects annual yield"),
        xaxis=dict(title="Tilt angle [°]  (0° = flat · 90° = vertical)", **_xgrid()),
        yaxis=dict(title="Annual yield [kWh/yr]", **_ygrid()),
        height=300, margin=dict(l=65, r=20, t=55, b=55),
        legend=dict(orientation="h", y=1.1, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig


# ---------------------------------------------------------------------------
# Tab 3: Daily Irradiance
# ---------------------------------------------------------------------------

def daily_irradiance(
    tmy_df: pd.DataFrame,
    lat: float, lon: float, elevation_m: float,
    tilt_deg: float, panel_az_deg: float, albedo: float, doy: int,
) -> go.Figure:
    """Stacked area: POA components + solar altitude for a single day."""
    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    times    = pd.date_range(f"2023-{_doy_to_mmdd(doy)}", periods=24, freq="1h", tz="UTC")
    day_mask = (tmy_df.index.month == times[0].month) & (tmy_df.index.day == times[0].day)
    day_df   = tmy_df[day_mask].copy()
    if len(day_df) == 0:
        return go.Figure().update_layout(**_layout(title=_title("No data for this day")))

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

    hours    = day_df.index.hour + day_df.index.minute / 60
    altitude = 90 - solar_pos["apparent_zenith"].clip(upper=90)

    import datetime
    date_str = (datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)).strftime("%B %d")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=hours, y=poa["poa_direct"].clip(lower=0),
        name="Direct beam", stackgroup="poa",
        fillcolor="rgba(232,146,14,0.72)", line=dict(width=0),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hours, y=poa["poa_diffuse"].clip(lower=0),
        name="Sky diffuse", stackgroup="poa",
        fillcolor="rgba(74,133,192,0.55)", line=dict(width=0),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hours, y=poa["poa_ground_diffuse"].clip(lower=0),
        name="Ground reflected", stackgroup="poa",
        fillcolor="rgba(74,122,88,0.45)", line=dict(width=0),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=hours, y=altitude, name="Solar altitude [°]",
        mode="lines", line=dict(color=GREY_COLOR, width=2, dash="dot"),
    ), secondary_y=True)

    fig.update_layout(**_layout(
        title=_title(f"Solar energy on your panel surface — {date_str}"),
        xaxis=dict(title="Hour of day (UTC)", **_xgrid()),
        height=360, margin=dict(l=65, r=65, t=55, b=55),
        legend=dict(orientation="h", y=1.12, font=dict(size=12, color=INK_COLOR)),
    ))
    fig.update_yaxes(
        title_text="Solar power on panel [W/m²]", secondary_y=False,
        gridcolor=_GRID, zerolinecolor=_GRID, color=INK_LIGHT,
    )
    fig.update_yaxes(
        title_text="Sun height above horizon [°]", secondary_y=True,
        range=[0, 90], showgrid=False, color=GREY_COLOR,
    )
    return fig


# ---------------------------------------------------------------------------
# Tab 4: Sun Path Diagram
# ---------------------------------------------------------------------------

def sun_path_polar(lat: float, lon: float, elevation_m: float, selected_doy: int) -> go.Figure:
    """Polar sun path diagram: elevation vs azimuth for solstices, equinox, and selected day."""
    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    special_days = {
        "Winter solstice (Dec 21)": 355,
        "Equinox (Mar 20)":          79,
        "Summer solstice (Jun 21)": 172,
        "Selected day":         selected_doy,
    }
    colors = [WINTER_COLOR, GREY_COLOR, SUN_COLOR, TERRACOTTA]
    dashes = ["solid", "dot", "solid", "dash"]

    fig = go.Figure()
    for (label, doy), color, dash in zip(special_days.items(), colors, dashes):
        import datetime
        date  = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
        times = pd.date_range(
            datetime.datetime(2023, date.month, date.day, 0, 0),
            periods=145, freq="10min", tz="UTC",
        )
        sp   = loc.get_solarposition(times)
        alt  = (90 - sp["apparent_zenith"].clip(upper=90)).clip(lower=0)
        mask = alt > 0
        if mask.sum() < 2:
            continue
        fig.add_trace(go.Scatterpolar(
            r=(90 - alt[mask]).values, theta=sp["azimuth"][mask].values,
            mode="lines", name=label,
            line=dict(color=color, width=2, dash=dash),
        ))

    fig.update_layout(**_layout(
        title=_title("Sun path across the sky — centre = directly overhead, edge = horizon"),
        polar=_polar_style(),
        height=420, margin=dict(l=40, r=40, t=65, b=50),
        legend=dict(orientation="h", y=-0.12, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig


def sun_path_flower(lat: float, lon: float, elevation_m: float, selected_doy: int | None = None) -> go.Figure:
    """Sun path as filled flower petals — each season is a filled polar arc."""
    import datetime
    loc = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")

    petals = [
        ("Winter solstice (Dec 21)", 355, "rgba(91,141,196,0.22)",  WINTER_COLOR),
        ("Equinox (Mar 20)",          79, "rgba(74,122,88,0.28)",   EARTH_COLOR),
        ("Summer solstice (Jun 21)", 172, "rgba(232,146,14,0.28)",  SUN_COLOR),
    ]
    if selected_doy is not None:
        petals.append(("Selected day", selected_doy, "rgba(199,91,57,0.20)", TERRACOTTA))

    fig = go.Figure()
    for label, doy, fillcolor, linecolor in petals:
        date  = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
        times = pd.date_range(
            datetime.datetime(2023, date.month, date.day, 0, 0),
            periods=145, freq="10min", tz="UTC",
        )
        sp   = loc.get_solarposition(times)
        alt  = (90 - sp["apparent_zenith"].clip(upper=90)).clip(lower=0)
        mask = alt > 0
        if mask.sum() < 2:
            continue
        fig.add_trace(go.Scatterpolar(
            r=(90 - alt[mask]).values, theta=sp["azimuth"][mask].values,
            fill="toself", fillcolor=fillcolor,
            line=dict(color=linecolor, width=2),
            name=label, mode="lines",
        ))

    fig.update_layout(**_layout(
        title=_title("Sun's journey across the sky — each season is a petal"),
        polar=_polar_style(),
        height=450, margin=dict(l=40, r=40, t=65, b=65),
        legend=dict(orientation="h", y=-0.14, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig


def monthly_rose(monthly_yield: pd.Series) -> go.Figure:
    """Monthly yield as a polar rose — each month is a petal, radius = avg kWh/day."""
    month_colors = [
        CLAY,         CLAY,          # Jan, Feb  — winter
        EARTH_COLOR,  EARTH_COLOR,   # Mar, Apr  — spring
        SUN_COLOR,    SUN_COLOR,     # May, Jun  — early summer
        SUN_COLOR,    AMBER_LIGHT,   # Jul, Aug  — peak summer
        TERRACOTTA,   TERRACOTTA,    # Sep, Oct  — autumn
        CLAY,         CLAY,          # Nov, Dec  — winter
    ]

    fig = go.Figure()
    for i, (label, val, color) in enumerate(zip(MONTH_LABELS, monthly_yield.values, month_colors)):
        fig.add_trace(go.Barpolar(
            r=[float(val)], theta=[i * 30], width=[26],
            marker_color=color, marker_line_color=_WARM_BG,
            marker_line_width=1.5, opacity=0.88,
            name=label, showlegend=True,
        ))

    fig.update_layout(**_layout(
        title=_title("A year of sunlight — monthly average yield"),
        polar=dict(
            bgcolor="rgba(232,245,233,0.3)",
            angularaxis=dict(
                tickmode="array",
                tickvals=[i * 30 for i in range(12)],
                ticktext=MONTH_LABELS,
                direction="clockwise", rotation=90,
                tickfont=dict(size=13, color=INK_COLOR),
                gridcolor=_GRID,
            ),
            radialaxis=dict(
                title_text="kWh/day", showticklabels=True,
                tickfont=dict(size=11, color=INK_LIGHT),
                gridcolor=_GRID,
            ),
        ),
        showlegend=False,
        height=420, margin=dict(l=65, r=65, t=65, b=65),
    ))
    return fig


def energy_roots(waterfall: dict[str, float], net_kwh: float) -> go.Figure:
    """Energy flow as a root / sap Sankey diagram."""
    friendly    = {_WATERFALL_LABELS.get(k, k): v for k, v in waterfall.items()}
    loss_labels = list(friendly.keys())
    losses      = list(friendly.values())
    gross       = net_kwh + sum(losses)

    node_labels = ["Gross solar input"] + loss_labels + ["Net AC yield"]
    n = len(losses)
    node_colors = [SUN_COLOR] + [TERRACOTTA] * n + [GREEN_COLOR]
    link_colors = ["rgba(199,91,57,0.20)"] * n + ["rgba(61,154,107,0.30)"]

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=14, thickness=18,
            line=dict(color="rgba(0,0,0,0.10)", width=0.5),
            label=node_labels, color=node_colors,
        ),
        link=dict(
            source=[0] * (n + 1),
            target=list(range(1, n + 2)),
            value=losses + [net_kwh],
            color=link_colors,
        ),
    ))
    fig.update_layout(**_layout(
        title=_title(f"Energy flow — {gross:,.0f} kWh gross → {net_kwh:,.0f} kWh net"),
        height=455, margin=dict(l=20, r=20, t=65, b=20),
        font=dict(family='"Inter", sans-serif', size=13, color=INK_COLOR),
    ))
    return fig


def orientation_contour(
    energy_grid: np.ndarray,
    tilt_arr: np.ndarray,
    az_arr: np.ndarray,
    selected_tilt: float,
    selected_az: float,
) -> tuple[go.Figure, float, float, float]:
    """Smooth contour map of annual yield vs tilt × azimuth."""
    opt_i, opt_j = np.unravel_index(np.argmax(energy_grid), energy_grid.shape)
    opt_tilt = tilt_arr[opt_i]; opt_az = az_arr[opt_j]; opt_val = energy_grid[opt_i, opt_j]

    fig = go.Figure(go.Contour(
        z=energy_grid, x=az_arr, y=tilt_arr,
        colorscale=[
            [0.00, "#E8F5E9"], [0.40, "#FFF3DC"],
            [0.75, "#F5A623"], [1.00, "#9A6207"],
        ],
        contours=dict(
            coloring="heatmap",
            showlabels=True,
            labelfont=dict(size=12, color=INK_COLOR),
        ),
        colorbar=dict(title="kWh/yr", tickfont=dict(size=12, color=INK_LIGHT)),
        hovertemplate="Tilt: %{y}°<br>Azimuth: %{x}°<br>Yield: %{z:.0f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[opt_az], y=[opt_tilt], mode="markers+text",
        marker=dict(symbol="star", size=16, color=_WARM_BG,
                    line=dict(color=SUN_COLOR, width=2)),
        text=[f"Best: {opt_val:.0f} kWh"], textposition="top center",
        textfont=dict(color=INK_COLOR, size=12), name="Optimal",
    ))
    fig.add_trace(go.Scatter(
        x=[selected_az], y=[selected_tilt], mode="markers",
        marker=dict(symbol="cross", size=14, color=BLUE_COLOR,
                    line=dict(color=_WARM_BG, width=1.5)),
        name="Selected",
    ))
    fig.update_layout(**_layout(
        title=_title(
            f"Annual yield by orientation — best: tilt {opt_tilt}°, "
            f"facing {opt_az}° → {opt_val:,.0f} kWh/yr"
        ),
        xaxis=dict(title="Facing direction [°]  (0° = N · 90° = E · 180° = S · 270° = W)", **_xgrid()),
        yaxis=dict(title="Tilt angle [°]", **_ygrid()),
        height=420, margin=dict(l=65, r=20, t=65, b=55),
        legend=dict(orientation="h", y=1.1, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig, float(opt_tilt), float(opt_az), float(opt_val)


# ---------------------------------------------------------------------------
# Lifetime Yield Projection
# ---------------------------------------------------------------------------

def lifetime_yield_chart(lifetime_yield: np.ndarray) -> go.Figure:
    """Bar chart of annual yield decay + cumulative yield on secondary axis."""
    years      = list(range(1, len(lifetime_yield) + 1))
    cumulative = np.cumsum(lifetime_yield) / 1000.0  # MWh
    bar_colors = [SUN_COLOR if y == 1 else WINTER_COLOR for y in years]

    fig = go.Figure()
    fig.add_bar(
        x=years, y=lifetime_yield,
        name="Annual yield (kWh)",
        marker_color=bar_colors,
        marker_line_color="rgba(0,0,0,0.08)", marker_line_width=0.5,
        opacity=0.85,
    )
    fig.add_scatter(
        x=years, y=cumulative,
        name="Cumulative yield (MWh)",
        yaxis="y2",
        line=dict(color=EARTH_COLOR, width=2.5),
        mode="lines",
    )
    y1 = lifetime_yield[0]
    fig.add_hline(
        y=y1 * 0.80, line_dash="dot", line_color="rgba(199,91,57,0.5)",
        annotation_text="80% yr-1 (typical warranty)",
        annotation_font_color=TERRACOTTA, annotation_font_size=12,
        annotation_position="top left",
    )
    fig.update_layout(**_layout(
        title=_title("Annual Yield Over Project Lifetime"),
        xaxis=dict(title="Year", **_xgrid()),
        yaxis=dict(title="Annual yield (kWh)", **_ygrid()),
        yaxis2=dict(
            title="Cumulative yield (MWh)",
            overlaying="y", side="right",
            showgrid=False, color=EARTH_COLOR,
            title_font=dict(color=EARTH_COLOR),
            tickfont=dict(color=EARTH_COLOR),
        ),
        height=360, margin=dict(l=65, r=95, t=55, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig


# ---------------------------------------------------------------------------
# Economic Analysis Charts
# ---------------------------------------------------------------------------

def cashflow_chart(econ) -> go.Figure:
    """Annual savings bars + cumulative cash-flow line."""
    years      = list(range(1, len(econ.annual_savings_arr) + 1))
    cumcf      = list(econ.cumulative_cf_arr)
    bar_colors = [EARTH_COLOR if cf > 0 else TERRACOTTA for cf in cumcf]

    fig = go.Figure()
    fig.add_bar(
        x=years, y=econ.annual_savings_arr,
        name="Annual savings (€)",
        marker_color=bar_colors,
        marker_line_color="rgba(0,0,0,0.08)", marker_line_width=0.5,
        opacity=0.85,
    )
    fig.add_scatter(
        x=years, y=econ.cumulative_cf_arr,
        name="Cumulative cash flow (€)",
        line=dict(color=WINTER_COLOR, width=2.5),
        mode="lines+markers", marker=dict(size=4),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(74,96,80,0.35)")
    fig.update_layout(**_layout(
        title=_title("Cash Flow Over Project Lifetime"),
        xaxis=dict(title="Year", **_xgrid()),
        yaxis=dict(title="€", **_ygrid()),
        height=360, margin=dict(l=65, r=20, t=55, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig


def yield_degradation_chart(econ) -> go.Figure:
    """Line chart showing annual yield decay over project lifetime."""
    years = list(range(1, len(econ.annual_yield_arr) + 1))
    y1    = econ.annual_yield_arr[0]

    fig = go.Figure()
    fig.add_scatter(
        x=years, y=econ.annual_yield_arr,
        name="Annual yield (kWh)",
        line=dict(color=SUN_COLOR, width=2.5),
        fill="tozeroy", fillcolor="rgba(232,146,14,0.12)",
    )
    fig.add_hline(
        y=y1 * 0.80, line_dash="dot", line_color="rgba(199,91,57,0.5)",
        annotation_text="80% yr-1",
        annotation_font_color=TERRACOTTA, annotation_font_size=12,
        annotation_position="top left",
    )
    fig.update_layout(**_layout(
        title=_title("Annual Yield Degradation"),
        xaxis=dict(title="Year", **_xgrid()),
        yaxis=dict(title="Annual yield (kWh)", **_ygrid()),
        height=290, margin=dict(l=65, r=20, t=55, b=50),
        showlegend=False,
    ))
    return fig


# ---------------------------------------------------------------------------
# Horizon Profile Chart (Sun Path tab)
# ---------------------------------------------------------------------------

def horizon_profile_chart(
    lat: float, lon: float, elevation_m: float,
    horizon_azimuths: tuple[float, ...],
    horizon_elevations: tuple[float, ...],
) -> go.Figure:
    """Polar chart: user horizon profile (shaded) overlaid on annual sun path."""
    import datetime
    loc   = pvlib.location.Location(lat, lon, altitude=elevation_m, tz="UTC")
    hz_az = list(horizon_azimuths) + [horizon_azimuths[0] + 360]
    hz_el = list(horizon_elevations) + [horizon_elevations[0]]
    az_full = np.arange(0, 361)
    el_full = np.interp(az_full, hz_az, hz_el)
    r_hz    = 90 - el_full

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=np.concatenate([r_hz, [90, 90, r_hz[0]]]),
        theta=np.concatenate([az_full, [az_full[-1], az_full[0], az_full[0]]]),
        fill="toself", fillcolor="rgba(106,127,114,0.22)",
        line=dict(color=GREY_COLOR, width=2),
        name="Horizon profile", mode="lines",
    ))

    special_days = [
        ("Winter solstice (Dec 21)", 355, WINTER_COLOR, "solid"),
        ("Equinox (Mar 20)",          79, GREY_COLOR,   "dot"),
        ("Summer solstice (Jun 21)", 172, SUN_COLOR,    "solid"),
    ]
    for label, doy, color, dash in special_days:
        date  = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
        times = pd.date_range(
            datetime.datetime(2023, date.month, date.day, 0, 0),
            periods=145, freq="10min", tz="UTC",
        )
        sp   = loc.get_solarposition(times)
        alt  = (90 - sp["apparent_zenith"].clip(upper=90)).clip(lower=0)
        mask = alt > 0
        if mask.sum() < 2:
            continue
        fig.add_trace(go.Scatterpolar(
            r=(90 - alt[mask]).values, theta=sp["azimuth"][mask].values,
            mode="lines", name=label,
            line=dict(color=color, width=2, dash=dash),
        ))

    fig.update_layout(**_layout(
        title=_title("Horizon Profile & Sun Path — shaded area = obstruction zone"),
        polar=_polar_style(),
        height=460, margin=dict(l=40, r=40, t=65, b=50),
        legend=dict(orientation="h", y=-0.12, font=dict(size=12, color=INK_COLOR)),
    ))
    return fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doy_to_mmdd(doy: int) -> str:
    import datetime
    d = datetime.date(2023, 1, 1) + datetime.timedelta(days=doy - 1)
    return d.strftime("%m-%d")


def _polar_style() -> dict:
    """Shared organic polar axis style for sun path diagrams."""
    return dict(
        bgcolor="rgba(232,245,233,0.30)",
        angularaxis=dict(
            tickmode="array",
            tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
            ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
            direction="clockwise", rotation=90,
            tickfont=dict(size=13, color=INK_COLOR),
            gridcolor=_GRID,
        ),
        radialaxis=dict(
            tickmode="array",
            tickvals=[0, 15, 30, 45, 60, 75, 90],
            ticktext=["90°", "75°", "60°", "45°", "30°", "15°", "0°"],
            range=[0, 90],
            tickfont=dict(size=11, color=INK_LIGHT),
            gridcolor=_GRID,
        ),
    )
