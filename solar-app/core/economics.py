# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Economic analysis for a grid-connected PV system.

Computes standard investment metrics: simple and discounted payback, NPV, IRR, LCOE.
No new package dependencies — uses only numpy (already required by pvlib).
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class EconResult:
    capex_eur:             float        # total installed cost [€]
    annual_savings_yr1:    float        # Year 1 total savings [€/yr]
    simple_payback_yr:     float        # capex / yr-1 savings (undiscounted)
    discounted_payback_yr: float        # years until cumulative NPV crosses zero
    npv_eur:               float        # net present value over lifetime [€]
    irr_pct:               float        # internal rate of return [%]
    lcoe_eur_kwh:          float        # levelised cost of energy [€/kWh]
    annual_yield_arr:      np.ndarray   # yield each year [kWh], shape (lifetime_yr,)
    annual_savings_arr:    np.ndarray   # savings each year [€], shape (lifetime_yr,)
    cumulative_cf_arr:     np.ndarray   # undiscounted cumulative cash flow [€]


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
    """
    Compute economic indicators for a PV system over its lifetime.

    Parameters
    ----------
    annual_yield_kwh  : first-year simulated yield [kWh]
    peak_power_kw     : array DC peak power [kW]
    cost_per_wp       : all-in installed cost [€/Wp]
    elec_price        : grid electricity price Year 1 [€/kWh]
    escalation        : annual electricity price increase [fraction, e.g. 0.02]
    discount          : opportunity cost of capital / WACC [fraction, e.g. 0.04]
    degradation       : annual module yield loss [fraction, e.g. 0.005]
    lifetime_yr       : project horizon [years]
    feed_in_frac      : fraction of production exported to grid [0–1]
    feed_in_tariff    : payment per kWh exported [€/kWh]
    """
    capex = peak_power_kw * 1000.0 * cost_per_wp   # € (kW → W, then × €/Wp)
    years = np.arange(1, lifetime_yr + 1)

    # Yield degrades year-over-year; degradation is already in year 1 (LID in sim)
    yield_arr = annual_yield_kwh * (1.0 - degradation) ** (years - 1)

    # Electricity price escalates
    price_arr = elec_price * (1.0 + escalation) ** (years - 1)

    # Self-consumed (displaces grid purchase) vs exported (receives feed-in tariff)
    self_consumed = yield_arr * (1.0 - feed_in_frac)
    exported      = yield_arr * feed_in_frac
    savings_arr   = self_consumed * price_arr + exported * feed_in_tariff

    # Simple payback (undiscounted)
    simple_pb = capex / savings_arr[0] if savings_arr[0] > 0 else float("inf")

    # Discounted cash flows, NPV
    discount_factors = 1.0 / (1.0 + discount) ** years
    dcf              = savings_arr * discount_factors
    cumulative_dcf   = np.cumsum(dcf) - capex
    npv              = float(cumulative_dcf[-1])

    # Discounted payback: first year where cumulative NPV ≥ 0
    disc_pb = float("inf")
    for i, cf in enumerate(cumulative_dcf):
        if cf >= 0:
            disc_pb = float(years[i])
            break

    # IRR via Newton-Raphson
    irr = _irr(capex, savings_arr)

    # LCOE = capex / discounted lifetime yield
    discounted_yield = float(np.sum(yield_arr * discount_factors))
    lcoe = capex / discounted_yield if discounted_yield > 0 else float("inf")

    # Undiscounted cumulative cash flow (for payback chart)
    cumulative_cf = np.cumsum(savings_arr) - capex

    return EconResult(
        capex_eur=capex,
        annual_savings_yr1=float(savings_arr[0]),
        simple_payback_yr=simple_pb,
        discounted_payback_yr=disc_pb,
        npv_eur=npv,
        irr_pct=irr * 100.0,
        lcoe_eur_kwh=lcoe,
        annual_yield_arr=yield_arr,
        annual_savings_arr=savings_arr,
        cumulative_cf_arr=cumulative_cf,
    )


def _irr(capex: float, cashflows: np.ndarray, max_iter: int = 200) -> float:
    """Compute IRR via Newton-Raphson. Returns NaN if convergence fails."""
    years = np.arange(1, len(cashflows) + 1)
    r = 0.10   # initial guess: 10%
    for _ in range(max_iter):
        pv   = np.sum(cashflows / (1.0 + r) ** years)
        dpv  = -np.sum(years * cashflows / (1.0 + r) ** (years + 1))
        npv_ = pv - capex
        if abs(dpv) < 1e-12:
            return float("nan")
        r_new = r - npv_ / dpv
        if abs(r_new - r) < 1e-7:
            return max(float(r_new), -1.0)   # clamp at -100%
        r = r_new
    return float("nan")
