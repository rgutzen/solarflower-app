# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for core.losses — LossBudget, IAM, DC/AC loss chain, waterfall."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from core.losses import (
    LossBudget,
    apply_ac_losses,
    apply_dc_losses,
    build_loss_waterfall,
    compute_iam,
    performance_ratio,
)


# ── LossBudget dataclass ────────────────────────────────────────────────────


class TestLossBudget:
    def test_defaults(self):
        lb = LossBudget()
        assert lb.soiling == 0.02
        assert lb.lid == 0.015
        assert lb.mismatch == 0.01
        assert lb.dc_wiring == 0.015
        assert lb.availability == 0.01
        assert lb.ac_wiring == 0.005
        assert lb.transformer == 0.01

    def test_dc_factor(self):
        lb = LossBudget()
        expected = (1 - 0.02) * (1 - 0.015) * (1 - 0.01) * (1 - 0.015)
        assert_allclose(lb.dc_factor, expected, rtol=1e-10)

    def test_ac_factor(self):
        lb = LossBudget()
        expected = (1 - 0.01) * (1 - 0.005) * (1 - 0.01)
        assert_allclose(lb.ac_factor, expected, rtol=1e-10)

    def test_total_dc_loss(self):
        lb = LossBudget()
        assert_allclose(lb.total_dc_loss, 1 - lb.dc_factor, rtol=1e-10)

    def test_total_ac_loss(self):
        lb = LossBudget()
        assert_allclose(lb.total_ac_loss, 1 - lb.ac_factor, rtol=1e-10)

    def test_dc_factor_approximate_value(self):
        """DC factor ≈ 0.941 for defaults."""
        lb = LossBudget()
        assert 0.93 < lb.dc_factor < 0.95

    def test_ac_factor_approximate_value(self):
        """AC factor ≈ 0.975 for defaults."""
        lb = LossBudget()
        assert 0.97 < lb.ac_factor < 0.98

    def test_zero_losses(self):
        lb = LossBudget(
            soiling=0,
            lid=0,
            mismatch=0,
            dc_wiring=0,
            availability=0,
            ac_wiring=0,
            transformer=0,
        )
        assert_allclose(lb.dc_factor, 1.0)
        assert_allclose(lb.ac_factor, 1.0)

    def test_as_dict_keys(self):
        lb = LossBudget()
        d = lb.as_dict()
        expected_keys = {
            "Soiling",
            "LID",
            "Mismatch",
            "DC wiring",
            "Availability",
            "AC wiring",
            "Transformer",
        }
        assert set(d.keys()) == expected_keys


# ── compute_iam ──────────────────────────────────────────────────────────────


class TestComputeIAM:
    def test_normal_incidence_physical(self):
        """At AOI=0° (normal), IAM should be very close to 1."""
        aoi = pd.Series([0.0])
        result = compute_iam(aoi, model="physical")
        assert_allclose(result.values, [1.0], atol=0.01)

    def test_grazing_angle_physical(self):
        """At AOI=90° (grazing), IAM should be near 0."""
        aoi = pd.Series([90.0])
        result = compute_iam(aoi, model="physical")
        assert result.values[0] < 0.05

    def test_intermediate_angle_physical(self):
        """At AOI=60°, IAM should be in [0.85, 0.99]."""
        aoi = pd.Series([60.0])
        result = compute_iam(aoi, model="physical")
        assert 0.85 < result.values[0] < 0.99

    def test_iam_none_model(self):
        """Model 'none' returns all ones."""
        aoi = pd.Series([0.0, 30.0, 60.0, 90.0])
        result = compute_iam(aoi, model="none")
        assert_allclose(result.values, np.ones(4))

    def test_iam_ashrae_model(self):
        """ASHRAE model: AOI=0° → 1, AOI<90° → positive."""
        aoi = pd.Series([0.0, 30.0, 60.0])
        result = compute_iam(aoi, model="ashrae")
        assert_allclose(result.values[0], 1.0, atol=0.01)
        assert all(result.values > 0)

    def test_iam_preserves_index(self):
        idx = pd.date_range("2023-06-21", periods=3, freq="1h")
        aoi = pd.Series([0.0, 45.0, 90.0], index=idx)
        result = compute_iam(aoi, model="physical")
        assert result.index.equals(idx)


# ── apply_dc_losses / apply_ac_losses ────────────────────────────────────────


class TestApplyLosses:
    def test_dc_losses(self):
        lb = LossBudget()
        p = pd.Series([1000.0, 2000.0, 500.0])
        result = apply_dc_losses(p, lb)
        assert_allclose(result.values, p.values * lb.dc_factor)

    def test_ac_losses(self):
        lb = LossBudget()
        p = pd.Series([1000.0, 2000.0, 500.0])
        result = apply_ac_losses(p, lb)
        assert_allclose(result.values, p.values * lb.ac_factor)

    def test_zero_power(self):
        lb = LossBudget()
        p = pd.Series([0.0, 0.0])
        assert_allclose(apply_dc_losses(p, lb).values, [0.0, 0.0])
        assert_allclose(apply_ac_losses(p, lb).values, [0.0, 0.0])


# ── build_loss_waterfall ─────────────────────────────────────────────────────


class TestBuildLossWaterfall:
    def test_all_losses_non_negative(self):
        lb = LossBudget()
        wf = build_loss_waterfall(1000, 900, 880, 800, 750, 700, 650, lb)
        for label, val in wf.items():
            assert val >= 0, f"{label} = {val} is negative"

    def test_without_shading(self):
        lb = LossBudget()
        wf = build_loss_waterfall(1000, 900, 880, 800, 750, 700, 650, lb)
        assert "Horizon & far shading" in wf
        assert "Near shading" not in wf

    def test_with_shading(self):
        lb = LossBudget()
        wf = build_loss_waterfall(
            1000, 900, 880, 800, 750, 700, 650, lb, shading_loss_kwh=30.0
        )
        assert "Transposition" in wf
        assert "Near shading" in wf
        assert_allclose(wf["Near shading"], 30.0)

    def test_expected_keys(self):
        lb = LossBudget()
        wf = build_loss_waterfall(1000, 900, 880, 800, 750, 700, 650, lb)
        required = {
            "IAM (angle of incidence)",
            "Temperature derating",
            "Soiling",
            "LID",
            "Mismatch",
            "DC wiring",
            "Inverter",
            "Availability",
            "AC wiring",
            "Transformer",
        }
        assert required.issubset(set(wf.keys()))


# ── performance_ratio ────────────────────────────────────────────────────────


class TestPerformanceRatio:
    def test_known_values(self):
        pr = performance_ratio(net_yield_kwh=1000, ghi_kwh_m2=1200, peak_power_kw=1.0)
        assert_allclose(pr, 1000 / 1200, rtol=1e-10)

    def test_zero_reference(self):
        pr = performance_ratio(net_yield_kwh=100, ghi_kwh_m2=0, peak_power_kw=1.0)
        assert pr == 0.0

    def test_zero_peak_power(self):
        pr = performance_ratio(net_yield_kwh=100, ghi_kwh_m2=1000, peak_power_kw=0.0)
        assert pr == 0.0
