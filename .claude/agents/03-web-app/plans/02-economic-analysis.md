# Plan 02 — Economic Analysis Tab

**Priority:** High
**Effort:** Medium (1 day)
**New tab:** Tab 6 "Economics" in `app.py`
**New module:** `core/economics.py`

---

## Motivation

The app currently shows yield (kWh) but not value. For a real user deciding whether to install panels,
the key questions are: "How long until it pays back?" and "What is my return on investment?"
This tab answers those with industry-standard metrics.

---

## New Sidebar Inputs

Add a collapsible "Economics" section to `ui/sidebar.py`, below the existing Loss Budget section.

```python
with st.sidebar.expander("Economics", expanded=False):
    system_cost_per_wp = st.number_input(
        "System cost [€/Wp]", min_value=0.1, max_value=5.0, value=1.10, step=0.05,
        help="All-in installed cost per watt-peak DC. EU residential: ~0.9–1.3 €/Wp (2024)."
    )
    electricity_price = st.number_input(
        "Electricity price [€/kWh]", min_value=0.01, max_value=1.0, value=0.30, step=0.01,
        help="Grid electricity price you displace (or feed-in tariff if all exported)."
    )
    price_escalation_pct = st.number_input(
        "Annual price escalation [%/yr]", min_value=0.0, max_value=10.0, value=2.0, step=0.5,
        help="Expected annual increase in electricity price."
    )
    discount_rate_pct = st.number_input(
        "Discount rate [%/yr]", min_value=0.0, max_value=15.0, value=4.0, step=0.5,
        help="Opportunity cost of capital / WACC. Use ~4% for homeowner, ~8% for commercial."
    )
    degradation_rate_pct = st.number_input(
        "Module degradation [%/yr]", min_value=0.0, max_value=2.0, value=0.5, step=0.1,
        help="Annual yield reduction from module aging. Typical: 0.4–0.7%/yr."
    )
    project_lifetime_yr = st.slider(
        "Project lifetime [years]", min_value=10, max_value=30, value=25, step=1
    )
    feed_in_fraction = st.slider(
        "Feed-in fraction [%]", min_value=0, max_value=100, value=30, step=5,
        help="Fraction of production exported to grid (remainder is self-consumed)."
    )
    feed_in_tariff = st.number_input(
        "Feed-in tariff [€/kWh]", min_value=0.0, max_value=0.5, value=0.08, step=0.01,
        help="Payment per kWh exported. Set equal to electricity price if net-metering."
    )
```

Add these keys to the `cfg` dict returned by `render_sidebar()`:
```python
cfg["econ"] = {
    "cost_per_wp": system_cost_per_wp,
    "elec_price":  electricity_price,
    "escalation":  price_escalation_pct / 100,
    "discount":    discount_rate_pct / 100,
    "degradation": degradation_rate_pct / 100,
    "lifetime_yr": project_lifetime_yr,
    "feed_in_frac": feed_in_fraction / 100,
    "feed_in_tariff": feed_in_tariff,
}
```

---

## New Module: `core/economics.py`

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class EconResult:
    capex_eur:           float   # total installed cost
    annual_savings_yr1:  float   # Year 1 total savings (self-consume + export)
    simple_payback_yr:   float   # capex / avg annual savings (undiscounted)
    discounted_payback_yr: float # years until cumulative NPV > 0
    npv_eur:             float   # net present value over lifetime
    irr_pct:             float   # internal rate of return [%]
    lcoe_eur_kwh:        float   # levelised cost of energy
    annual_yield_arr:    np.ndarray  # yield [kWh] each year (shape: lifetime_yr)
    annual_savings_arr:  np.ndarray  # savings [€] each year
    cumulative_cf_arr:   np.ndarray  # cumulative cash flow [€] each year


def compute_economics(
    annual_yield_kwh: float,
    peak_power_kw: float,
    cost_per_wp: float,
    elec_price: float,
    escalation: float,
    discount: float,
    degradation: float,
    lifetime_yr: int,
    feed_in_frac: float,
    feed_in_tariff: float,
) -> EconResult:
    capex = peak_power_kw * 1000 * cost_per_wp   # € (pdc0 in W * €/Wp)

    years = np.arange(1, lifetime_yr + 1)

    # Yield degrades year over year
    yield_arr = annual_yield_kwh * (1 - degradation) ** (years - 1)

    # Electricity price escalates
    price_arr = elec_price * (1 + escalation) ** (years - 1)

    # Self-consumed and exported fractions
    self_consumed = yield_arr * (1 - feed_in_frac)
    exported      = yield_arr * feed_in_frac

    # Annual savings (€)
    savings_arr = self_consumed * price_arr + exported * feed_in_tariff

    # Simple payback
    simple_pb = capex / savings_arr[0] if savings_arr[0] > 0 else float("inf")

    # Discounted cash flows and NPV
    discount_factors = 1 / (1 + discount) ** years
    dcf = savings_arr * discount_factors
    cumulative_dcf = np.cumsum(dcf) - capex
    npv = float(cumulative_dcf[-1])

    # Discounted payback
    disc_pb = float("inf")
    for i, cf in enumerate(cumulative_dcf):
        if cf >= 0:
            disc_pb = float(years[i])
            break

    # IRR: find r such that sum(savings / (1+r)^t) = capex
    # Newton's method starting from a rough guess
    irr = _irr(capex, savings_arr)

    # LCOE = capex / sum(yield_t / (1+d)^t)
    discounted_yield = float(np.sum(yield_arr * discount_factors))
    lcoe = capex / discounted_yield if discounted_yield > 0 else float("inf")

    # Cumulative cash flow (undiscounted, for payback chart)
    cumulative_cf = np.cumsum(savings_arr) - capex

    return EconResult(
        capex_eur=capex,
        annual_savings_yr1=float(savings_arr[0]),
        simple_payback_yr=simple_pb,
        discounted_payback_yr=disc_pb,
        npv_eur=npv,
        irr_pct=irr * 100,
        lcoe_eur_kwh=lcoe,
        annual_yield_arr=yield_arr,
        annual_savings_arr=savings_arr,
        cumulative_cf_arr=cumulative_cf,
    )


def _irr(capex: float, cashflows: np.ndarray, max_iter: int = 100) -> float:
    """Compute IRR via Newton-Raphson. Returns NaN if not found."""
    r = 0.10  # initial guess
    years = np.arange(1, len(cashflows) + 1)
    for _ in range(max_iter):
        pv   = np.sum(cashflows / (1 + r) ** years)
        dpv  = -np.sum(years * cashflows / (1 + r) ** (years + 1))
        npv_ = pv - capex
        if abs(dpv) < 1e-12:
            return float("nan")
        r_new = r - npv_ / dpv
        if abs(r_new - r) < 1e-6:
            return float(r_new)
        r = r_new
    return float("nan")
```

---

## New Charts: `ui/charts.py` additions

### `cashflow_chart(econ: EconResult) -> go.Figure`

Grouped bar chart: year on x-axis, bars for annual savings (€), line for cumulative cash flow.
Color: green above zero (profit), amber below zero (payback period).

```python
def cashflow_chart(econ: EconResult) -> go.Figure:
    years = list(range(1, len(econ.annual_savings_arr) + 1))
    colors = ["#28C840" if cf >= 0 else "#F5A623"
              for cf in econ.cumulative_cf_arr]

    fig = go.Figure()
    fig.add_bar(
        x=years, y=econ.annual_savings_arr,
        name="Annual savings (€)", marker_color="#F5A623", opacity=0.8,
    )
    fig.add_scatter(
        x=years, y=econ.cumulative_cf_arr,
        name="Cumulative cash flow (€)",
        line=dict(color="#2D7DD2", width=2.5),
        mode="lines+markers",
    )
    # Breakeven line
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        title="Cash Flow Over Project Lifetime",
        xaxis_title="Year", yaxis_title="€",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
```

### `yield_degradation_chart(econ: EconResult) -> go.Figure`

Line chart showing annual yield decay over the project lifetime.

---

## Tab 6 in `app.py`

```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Annual Summary", "Orientation Optimizer", "Monthly Breakdown",
    "Daily Irradiance", "Sun Path", "Economics",
])

with tab6:
    from core.economics import compute_economics
    econ = compute_economics(
        annual_yield_kwh=result.annual_yield_kwh,
        peak_power_kw=result.peak_power_kw,
        **cfg["econ"],
    )

    # KPI row
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("System cost",    f"€{econ.capex_eur:,.0f}")
    kpi_cols[1].metric("Yr 1 savings",   f"€{econ.annual_savings_yr1:,.0f}/yr")
    kpi_cols[2].metric("Simple payback", f"{econ.simple_payback_yr:.1f} yr"
                        if econ.simple_payback_yr < 50 else "> 50 yr")
    kpi_cols[3].metric("NPV",            f"€{econ.npv_eur:,.0f}",
                        delta=f"IRR {econ.irr_pct:.1f}%")
    kpi_cols[4].metric("LCOE",           f"€{econ.lcoe_eur_kwh:.3f}/kWh")

    # Cash flow chart
    st.plotly_chart(charts.cashflow_chart(econ), use_container_width=True)

    # Yield degradation
    with st.expander("Annual yield over lifetime"):
        st.plotly_chart(charts.yield_degradation_chart(econ), use_container_width=True)

    # Assumptions summary table
    with st.expander("Assumptions"):
        st.dataframe(pd.DataFrame({
            "Parameter": ["System cost", "Electricity price (yr 1)", "Price escalation",
                          "Discount rate", "Module degradation", "Feed-in fraction",
                          "Feed-in tariff", "Project lifetime"],
            "Value": [
                f"€{cfg['econ']['cost_per_wp']:.2f}/Wp",
                f"€{cfg['econ']['elec_price']:.2f}/kWh",
                f"{cfg['econ']['escalation']*100:.1f}%/yr",
                f"{cfg['econ']['discount']*100:.1f}%/yr",
                f"{cfg['econ']['degradation']*100:.1f}%/yr",
                f"{cfg['econ']['feed_in_frac']*100:.0f}%",
                f"€{cfg['econ']['feed_in_tariff']:.2f}/kWh",
                f"{cfg['econ']['lifetime_yr']} years",
            ],
        }), use_container_width=True, hide_index=True)
```

---

## Notes

- No new package dependencies: uses only `numpy` and `plotly` (already in requirements).
- `compute_economics()` is pure Python/numpy — no need for `@st.cache_data` (runs instantly).
- Default values reflect 2024 EU residential market: 1.10 €/Wp, 0.30 €/kWh electricity price.
- IRR may return `nan` for bad inputs (very low yield or very high cost) — handle gracefully in UI.
- The LCOE formula uses the project discount rate (not a separate financial rate).
