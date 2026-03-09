# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for core.degradation — lifetime yield projection."""

import numpy as np
from numpy.testing import assert_allclose

from core.degradation import compute_lifetime_yield


class TestComputeLifetimeYield:
    def test_no_degradation(self):
        result = compute_lifetime_yield(10000, degradation_rate=0.0, lifetime_yr=25)
        assert_allclose(result, np.full(25, 10000.0))

    def test_year1_equals_input(self):
        result = compute_lifetime_yield(10000, degradation_rate=0.005, lifetime_yr=25)
        assert_allclose(result[0], 10000.0)

    def test_year25_at_half_percent(self):
        """Year 25 at 0.5%/yr: yield_25 = 10000 * 0.995^24 ≈ 8869."""
        result = compute_lifetime_yield(10000, degradation_rate=0.005, lifetime_yr=25)
        expected = 10000 * 0.995**24
        assert_allclose(result[-1], expected, rtol=1e-10)

    def test_shape(self):
        result = compute_lifetime_yield(10000, degradation_rate=0.005, lifetime_yr=30)
        assert result.shape == (30,)

    def test_monotonically_decreasing(self):
        result = compute_lifetime_yield(10000, degradation_rate=0.005, lifetime_yr=25)
        assert all(np.diff(result) <= 0)

    def test_single_year(self):
        result = compute_lifetime_yield(5000, degradation_rate=0.01, lifetime_yr=1)
        assert result.shape == (1,)
        assert_allclose(result[0], 5000.0)

    def test_high_degradation(self):
        """At 5%/yr for 20 years: year 20 = 10000 * 0.95^19 ≈ 3774."""
        result = compute_lifetime_yield(10000, degradation_rate=0.05, lifetime_yr=20)
        assert_allclose(result[-1], 10000 * 0.95**19, rtol=1e-8)

    def test_cumulative_yield_reasonable(self):
        """Total 25-year yield at 0.5%/yr should be ~93% of 25 * year-1."""
        result = compute_lifetime_yield(10000, degradation_rate=0.005, lifetime_yr=25)
        total = result.sum()
        # Geometric series sum: Y * (1 - r^n) / (1 - r)  where r = 0.995
        expected = 10000 * (1 - 0.995**25) / (1 - 0.995)
        assert_allclose(total, expected, rtol=1e-8)
