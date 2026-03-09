# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for core.economics — NPV, IRR, LCOE, payback calculations."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose

from core.economics import EconResult, _irr, compute_economics


# ── _irr (Newton-Raphson internal rate of return) ────────────────────────────


class TestIRR:
    def test_known_irr(self):
        """Project: invest 10 000, receive 3 000/yr for 5 years → IRR ≈ 15.2%."""
        capex = 10_000
        cashflows = np.full(5, 3000.0)
        irr = _irr(capex, cashflows)
        # Verify: NPV at computed rate should be ~0
        years = np.arange(1, 6)
        npv = np.sum(cashflows / (1 + irr) ** years) - capex
        assert abs(npv) < 0.01

    def test_irr_positive(self):
        """When total cashflows > capex, IRR should be positive."""
        irr = _irr(10_000, np.full(10, 2000.0))
        assert irr > 0

    def test_irr_breakeven(self):
        """When total undiscounted cashflows ≈ capex, IRR ≈ 0."""
        irr = _irr(10_000, np.full(10, 1000.0))
        assert abs(irr) < 0.02

    def test_irr_nan_on_impossible(self):
        """Zero cashflows → NaN."""
        irr = _irr(10_000, np.zeros(5))
        assert math.isnan(irr)


# ── compute_economics ────────────────────────────────────────────────────────


class TestComputeEconomics:
    @pytest.fixture()
    def base_result(self) -> EconResult:
        """Standard scenario: 8 kWp, 10000 kWh/yr, 0.30 €/kWh, 100% self-consumption."""
        return compute_economics(
            annual_yield_kwh=10_000,
            peak_power_kw=8.0,
            cost_per_wp=1.20,
            elec_price=0.30,
            escalation=0.02,
            discount=0.04,
            degradation=0.005,
            lifetime_yr=25,
            feed_in_frac=0.0,
            feed_in_tariff=0.0,
        )

    def test_capex(self, base_result):
        """CAPEX = 8 kWp × 1000 W/kW × 1.20 €/Wp = 9600 €."""
        assert_allclose(base_result.capex_eur, 9600.0)

    def test_year1_savings(self, base_result):
        """Year-1 savings = 10 000 kWh × 0.30 €/kWh = 3 000 €."""
        assert_allclose(base_result.annual_savings_yr1, 3000.0)

    def test_simple_payback(self, base_result):
        """Simple payback = 9600 / 3000 = 3.2 years."""
        assert_allclose(base_result.simple_payback_yr, 9600 / 3000, rtol=1e-10)

    def test_npv_positive(self, base_result):
        """With 10 000 kWh/yr at 0.30 €/kWh and 9600 € CAPEX, NPV should be positive."""
        assert base_result.npv_eur > 0

    def test_irr_reasonable(self, base_result):
        """IRR should be in a reasonable range [5%, 40%]."""
        assert 5 < base_result.irr_pct < 40

    def test_lcoe_below_grid_price(self, base_result):
        """LCOE should be below grid price for this economic scenario."""
        assert base_result.lcoe_eur_kwh < 0.30

    def test_lcoe_positive(self, base_result):
        assert base_result.lcoe_eur_kwh > 0

    def test_annual_yield_array_shape(self, base_result):
        assert base_result.annual_yield_arr.shape == (25,)

    def test_annual_yield_degrades(self, base_result):
        """Yield should decrease year-over-year."""
        assert all(np.diff(base_result.annual_yield_arr) <= 0)

    def test_cumulative_cf_crosses_zero(self, base_result):
        """Cumulative cash flow should become positive (profitable project)."""
        assert base_result.cumulative_cf_arr[-1] > 0

    def test_discounted_payback_finite(self, base_result):
        assert base_result.discounted_payback_yr < 25

    def test_feed_in_tariff(self):
        """With 50% export at 0.08 €/kWh: year-1 savings = 5000*0.30 + 5000*0.08."""
        r = compute_economics(
            annual_yield_kwh=10_000,
            peak_power_kw=8.0,
            cost_per_wp=1.20,
            elec_price=0.30,
            escalation=0.0,
            discount=0.04,
            degradation=0.0,
            lifetime_yr=25,
            feed_in_frac=0.5,
            feed_in_tariff=0.08,
        )
        expected = 5000 * 0.30 + 5000 * 0.08
        assert_allclose(r.annual_savings_yr1, expected, rtol=1e-10)

    def test_zero_yield(self):
        r = compute_economics(
            annual_yield_kwh=0.0,
            peak_power_kw=8.0,
            cost_per_wp=1.20,
            elec_price=0.30,
            escalation=0.02,
            discount=0.04,
            degradation=0.005,
            lifetime_yr=25,
            feed_in_frac=0.0,
            feed_in_tariff=0.0,
        )
        assert r.simple_payback_yr == float("inf")
        assert r.lcoe_eur_kwh == float("inf")
