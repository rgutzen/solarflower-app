# Plan 05 — 20-Year Degradation Projection

**Priority:** Medium
**Effort:** Small (½ day)
**Location:** New expander inside Tab 1 "Annual Summary" in `app.py`
**Dependencies:** Plan 02 economics is a natural companion (uses same year array)

---

## Motivation

PV modules lose approximately 0.4–0.7% yield per year (linear degradation after LID).
A 25-year projection chart lets users see the full lifetime yield curve, total lifetime energy,
and understand why panels are typically warranted for 25–30 years.

This also sets up the data structure needed by the Economics tab (Plan 02), which uses
`annual_yield_arr` for the NPV calculation.

---

## Physics Model

Standard two-stage degradation model (IEC 61853, module datasheet convention):

```
Year 1:  yield_1 = Y0 * (1 - LID)
Year t:  yield_t = Y0 * (1 - LID) * (1 - r_deg)^(t-1)   for t ≥ 2
```

Where:
- `Y0` = first-year yield before LID (= `result.annual_yield_kwh` as computed)
- `LID` = light-induced degradation, first-year one-off loss (default 1.5%, already in LossBudget)
- `r_deg` = annual linear degradation rate (new input, default 0.5%/yr)

Since `result.annual_yield_kwh` already incorporates LID (it's part of the DC loss chain),
the projection builds from that result:

```
yield_t = result.annual_yield_kwh * (1 - r_deg)^(t-1)   for t = 1, 2, ..., N
```

This is conservative (assumes LID already happened in Year 1).

---

## New Sidebar Input

Add a single slider inside the existing "Loss Budget" expander in `ui/sidebar.py`:

```python
degradation_rate_pct = st.slider(
    "Annual degradation [%/yr]", min_value=0.0, max_value=2.0,
    value=0.50, step=0.05,
    help="Linear module yield loss per year after LID. Typical: 0.4–0.7%/yr. "
         "Premium modules: ~0.3%/yr. Budget: ~0.8%/yr."
)
cfg["degradation_rate"] = degradation_rate_pct / 100
```

If Plan 02 (Economics) is also implemented, this value is shared with the economics
calculation — define it once and pass to both.

---

## Computation

Pure numpy, no new simulation needed. Runs instantly:

```python
def compute_lifetime_yield(
    annual_yield_kwh: float,
    degradation_rate: float,
    lifetime_yr: int = 25,
) -> np.ndarray:
    """Annual yield for each year of the project lifetime [kWh]."""
    years = np.arange(lifetime_yr)
    return annual_yield_kwh * (1 - degradation_rate) ** years
```

Derived quantities:
```python
lifetime_yield = compute_lifetime_yield(result.annual_yield_kwh, cfg["degradation_rate"])

cumulative_yield = np.cumsum(lifetime_yield)          # kWh
year25_yield     = lifetime_yield[-1]                 # kWh in final year
year25_pct       = year25_yield / lifetime_yield[0] * 100  # % of year-1 yield
total_lifetime   = cumulative_yield[-1]               # total kWh over 25 yr
```

---

## New Charts: `ui/charts.py`

### `lifetime_yield_chart(lifetime_yield: np.ndarray) -> go.Figure`

```python
def lifetime_yield_chart(lifetime_yield: np.ndarray) -> go.Figure:
    years = list(range(1, len(lifetime_yield) + 1))

    fig = go.Figure()

    # Bar chart: annual yield
    fig.add_bar(
        x=years, y=lifetime_yield,
        name="Annual yield (kWh)",
        marker_color=[
            "#F5A623" if y == 1 else "#2D7DD2"
            for y in years
        ],
        opacity=0.85,
    )

    # Line: cumulative yield on secondary axis
    cumulative = np.cumsum(lifetime_yield)
    fig.add_scatter(
        x=years, y=cumulative,
        name="Cumulative yield (MWh)",
        yaxis="y2",
        line=dict(color="#66BB6A", width=2.5),
        mode="lines",
    )

    # Annotation: warranty thresholds (80% @ 25 yr typical)
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
            tickformat=".0f",
            ticksuffix=" MWh",
            showgrid=False,
        ),
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
```

---

## Tab 1 Integration in `app.py`

Add a new expander below the existing "Download Results" expander:

```python
with st.expander("Lifetime Yield Projection"):
    from core.degradation import compute_lifetime_yield  # or inline

    lifetime_yr = st.slider("Projection horizon [years]", 10, 30, 25, step=1,
                             key="lt_years")
    deg_rate = cfg.get("degradation_rate", 0.005)
    lifetime_yield = compute_lifetime_yield(
        result.annual_yield_kwh, deg_rate, lifetime_yr
    )
    cumulative = float(np.cumsum(lifetime_yield)[-1])
    yr25_pct   = lifetime_yield[-1] / lifetime_yield[0] * 100

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total lifetime yield",
                f"{cumulative/1000:,.1f} MWh",
                f"over {lifetime_yr} years")
    kpi2.metric(f"Year {lifetime_yr} yield",
                f"{lifetime_yield[-1]:,.0f} kWh",
                f"{yr25_pct:.1f}% of Year 1")
    kpi3.metric("Avg annual yield",
                f"{cumulative/lifetime_yr:,.0f} kWh/yr")

    st.plotly_chart(charts.lifetime_yield_chart(lifetime_yield), use_container_width=True)
```

---

## Optional: `core/degradation.py`

If shared with the Economics tab, extract into its own module:

```python
# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

def compute_lifetime_yield(
    annual_yield_kwh: float,
    degradation_rate: float,
    lifetime_yr: int = 25,
) -> np.ndarray:
    """Annual yield for each year [kWh], shape (lifetime_yr,)."""
    return annual_yield_kwh * (1 - degradation_rate) ** np.arange(lifetime_yr)
```

Otherwise inline both `compute_lifetime_yield` calls (in Tab 1 and Plan 02 economics) directly.

---

## Validation

For a 10 kWp system in Germany (~9,000 kWh/yr) at 0.5%/yr degradation:
- Year 1: ~9,000 kWh
- Year 25: 9,000 × 0.995^24 ≈ 7,960 kWh (88.4% of Year 1)
- 25-year total: ~206 MWh
- Matches typical industry figures (200–220 MWh per 10 kWp over 25 yr in central Europe)
