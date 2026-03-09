# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for core.energy — pure helpers + integration tests for run_simulation.

Pure helpers (no pvlib / no mocking):
  peak_power_kw, _interpolate_horizon, _compute_shading_mask,
  _monthly_yield, _monthly_pr

Integration tests (require pvlib + synthetic TMY):
  run_simulation, _electrical_model (PVWatts path)
"""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from core.energy import (
    SimResult,
    _compute_shading_mask,
    _interpolate_horizon,
    _monthly_pr,
    _monthly_yield,
    peak_power_kw,
    run_simulation,
)
from core.losses import LossBudget


# ── peak_power_kw ────────────────────────────────────────────────────────────


class TestPeakPowerKw:
    def test_from_pdc0(self):
        mp = pd.Series({"pdc0": 400.0})
        assert_allclose(peak_power_kw(mp, n_modules=20), 8.0)

    def test_from_vmp_imp(self):
        """Fallback: pdc0 = V_mp_ref × I_mp_ref."""
        mp = pd.Series({"V_mp_ref": 34.0, "I_mp_ref": 11.76})
        expected = 34.0 * 11.76 * 10 / 1000.0
        assert_allclose(peak_power_kw(mp, n_modules=10), expected, rtol=1e-6)

    def test_single_module(self):
        mp = pd.Series({"pdc0": 350.0})
        assert_allclose(peak_power_kw(mp, n_modules=1), 0.35)


# ── _interpolate_horizon ─────────────────────────────────────────────────────


class TestInterpolateHorizon:
    def test_exact_points(self):
        """Query at exact input azimuths → returns exact values."""
        az = (0, 90, 180, 270)
        el = (5, 10, 0, 15)
        result = _interpolate_horizon(az, el, np.array([0, 90, 180, 270], dtype=float))
        assert_allclose(result, [5, 10, 0, 15])

    def test_midpoint_interpolation(self):
        az = (0, 180)
        el = (0, 10)
        result = _interpolate_horizon(az, el, np.array([90.0]))
        assert_allclose(result, [5.0])

    def test_wrap_around(self):
        """Azimuth wraps: 350° should interpolate between 270° and 360°(=0°)."""
        az = (0, 90, 180, 270)
        el = (10, 5, 0, 5)
        result = _interpolate_horizon(az, el, np.array([350.0]))
        # Between 270° (el=5) and 360° (el=10): 350 is at fraction (350-270)/(360-270)=80/90
        expected = 5 + (10 - 5) * (80 / 90)
        assert_allclose(result, [expected], atol=0.5)

    def test_flat_horizon(self):
        az = (0, 90, 180, 270)
        el = (0, 0, 0, 0)
        result = _interpolate_horizon(az, el, np.array([45.0, 135.0, 225.0, 315.0]))
        assert_allclose(result, [0, 0, 0, 0])


# ── _compute_shading_mask ────────────────────────────────────────────────────


class TestComputeShadingMask:
    def test_sun_above_horizon(self):
        """Sun far above horizon → shading factor ≈ 1."""
        solar_pos = pd.DataFrame(
            {
                "azimuth": [180.0],
                "apparent_zenith": [30.0],  # alt = 60°
            }
        )
        result = _compute_shading_mask(solar_pos, (0, 90, 180, 270), (0, 0, 0, 0))
        assert result[0] > 0.99

    def test_sun_below_horizon(self):
        """Sun below horizon profile → shading factor ≈ 0."""
        solar_pos = pd.DataFrame(
            {
                "azimuth": [180.0],
                "apparent_zenith": [85.0],  # alt = 5°
            }
        )
        # Horizon at 20° all around
        result = _compute_shading_mask(solar_pos, (0, 90, 180, 270), (20, 20, 20, 20))
        assert result[0] < 0.01

    def test_sigmoid_transition(self):
        """At the horizon boundary, shading factor ≈ 0.5."""
        solar_pos = pd.DataFrame(
            {
                "azimuth": [180.0],
                "apparent_zenith": [80.0],  # alt = 10°
            }
        )
        result = _compute_shading_mask(solar_pos, (0, 90, 180, 270), (10, 10, 10, 10))
        assert 0.3 < result[0] < 0.7


# ── _monthly_yield ───────────────────────────────────────────────────────────


class TestMonthlyYield:
    def test_shape(self):
        times = pd.date_range("2023-01-01", periods=8760, freq="1h", tz="UTC")
        p = pd.Series(np.ones(8760) * 1000.0, index=times)  # 1 kW constant
        result = _monthly_yield(p)
        assert len(result) == 12
        assert list(result.index) == list(range(1, 13))

    def test_constant_power(self):
        """1000 W constant → each month ≈ 24 kWh/day."""
        times = pd.date_range("2023-01-01", periods=8760, freq="1h", tz="UTC")
        p = pd.Series(np.ones(8760) * 1000.0, index=times)
        result = _monthly_yield(p)
        assert_allclose(result.values, np.full(12, 24.0), atol=0.1)


# ── _monthly_pr ──────────────────────────────────────────────────────────────


class TestMonthlyPR:
    def test_perfect_system(self):
        """If AC output equals POA×P_peak, PR = 1.0."""
        times = pd.date_range("2023-01-01", periods=8760, freq="1h", tz="UTC")
        poa = pd.Series(np.ones(8760) * 500.0, index=times)  # 500 W/m²
        pk_kw = 1.0
        # Perfect system: P_ac = POA [W/m²] * P_peak [kW] = 500 W
        p_ac = poa * pk_kw
        result = _monthly_pr(p_ac, poa, pk_kw)
        assert len(result) == 12
        assert_allclose(result.values, np.ones(12), atol=0.01)


# ── run_simulation (integration) ─────────────────────────────────────────────


class TestRunSimulation:
    def test_basic_output(
        self, synthetic_tmy, default_module_params, default_inverter_params
    ):
        """Simulation should return a SimResult with physically plausible values."""
        result = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
            albedo=0.20,
            data_source="synthetic",
        )
        assert isinstance(result, SimResult)
        assert result.annual_yield_kwh > 0
        assert result.peak_power_kw > 0

    def test_pr_below_one(
        self, synthetic_tmy, default_module_params, default_inverter_params
    ):
        """PR should not exceed 1.0 (Bug 3 regression)."""
        result = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
        )
        assert (
            0 < result.performance_ratio <= 1.0
        ), f"PR = {result.performance_ratio} — should be in (0, 1]"

    def test_parametric_module_nonzero_yield(
        self, synthetic_tmy, default_inverter_params
    ):
        """Bug 1 regression: parametric module (IL_ref=None) must produce yield > 0."""
        from core.system import parametric_module

        mod = parametric_module(400, 34.0, 11.76, 41.0, 12.5, -0.004, 66)
        # Confirm this is the PVWatts path (IL_ref=None → stored as NaN in Series)
        assert mod["IL_ref"] is None or pd.isna(mod["IL_ref"])
        result = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=mod,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
        )
        assert (
            result.annual_yield_kwh > 100
        ), f"Annual yield = {result.annual_yield_kwh} — parametric module should produce > 100 kWh"

    def test_monthly_yield_shape(
        self, synthetic_tmy, default_module_params, default_inverter_params
    ):
        result = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
        )
        assert len(result.monthly_yield_kwh_day) == 12
        assert all(result.monthly_yield_kwh_day >= 0)

    def test_capacity_factor_range(
        self, synthetic_tmy, default_module_params, default_inverter_params
    ):
        result = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
        )
        assert (
            0 < result.capacity_factor < 0.5
        ), f"CF = {result.capacity_factor} — should be in (0, 0.5)"

    def test_loss_waterfall_present(
        self, synthetic_tmy, default_module_params, default_inverter_params
    ):
        result = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
        )
        assert isinstance(result.loss_waterfall, dict)
        assert len(result.loss_waterfall) > 0

    def test_horizon_shading(
        self, synthetic_tmy, default_module_params, default_inverter_params
    ):
        """With heavy horizon shading, yield should decrease vs unshaded."""
        baseline = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
        )
        shaded = run_simulation(
            tmy_df=synthetic_tmy,
            lat=52.5,
            lon=13.4,
            elevation_m=100,
            tilt_deg=35,
            panel_az_deg=180,
            module_params=default_module_params,
            inverter_params=default_inverter_params,
            inverter_type="pvwatts",
            n_modules=20,
            strings_per_inverter=10,
            n_inverters=2,
            loss_budget=LossBudget(),
            horizon_azimuths=(0, 90, 180, 270),
            horizon_elevations=(30, 30, 30, 30),  # heavy shading
        )
        assert shaded.annual_yield_kwh < baseline.annual_yield_kwh
