# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for core.system — parametric module, inverter, search, mapping."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from core.system import (
    parametric_module,
    pvwatts_inverter,
    search_inverters,
    search_modules,
)


# ── parametric_module ────────────────────────────────────────────────────────


class TestParametricModule:
    @pytest.fixture()
    def mod(self) -> pd.Series:
        return parametric_module(
            pdc0=400.0,
            v_mp=34.0,
            i_mp=11.76,
            v_oc=41.0,
            i_sc=12.5,
            temp_coeff_pmax=-0.004,
            cells_in_series=66,
        )

    def test_pdc0(self, mod):
        assert_allclose(mod["pdc0"], 400.0)

    def test_stc_voltages(self, mod):
        assert_allclose(mod["V_mp_ref"], 34.0)
        assert_allclose(mod["V_oc_ref"], 41.0)

    def test_stc_currents(self, mod):
        assert_allclose(mod["I_mp_ref"], 11.76)
        assert_allclose(mod["I_sc_ref"], 12.5)

    def test_gamma_r_stored_as_pct_per_degC(self, mod):
        """gamma_r should be stored as %/°C: -0.004 * 100 = -0.4."""
        assert_allclose(mod["gamma_r"], -0.4)

    def test_cells_in_series(self, mod):
        assert mod["cells_in_series"] == 66

    def test_il_ref_is_none_or_nan(self, mod):
        """parametric_module sets IL_ref=None; pd.Series stores it as NaN (Bug 1)."""
        assert mod["IL_ref"] is None or pd.isna(mod["IL_ref"])

    def test_i0_ref_is_none_or_nan(self, mod):
        assert mod["I0_ref"] is None or pd.isna(mod["I0_ref"])

    def test_required_keys_present(self, mod):
        required = [
            "pdc0",
            "V_mp_ref",
            "I_mp_ref",
            "V_oc_ref",
            "I_sc_ref",
            "alpha_sc",
            "beta_oc",
            "gamma_r",
            "cells_in_series",
            "R_s",
            "R_sh_ref",
            "R_sh_0",
            "a_ref",
            "EgRef",
            "dEgdT",
            "adjust",
            "IL_ref",
            "I0_ref",
        ]
        for k in required:
            assert k in mod.index, f"Missing key: {k}"

    def test_r_s_positive(self, mod):
        assert mod["R_s"] > 0

    def test_r_sh_ref_positive(self, mod):
        assert mod["R_sh_ref"] > 0


# ── pvwatts_inverter ─────────────────────────────────────────────────────────


class TestPvwattsInverter:
    def test_pdc0(self):
        inv = pvwatts_inverter(pdc0_kw=5.0, eff_pct=96.0)
        assert_allclose(inv["pdc0"], 5000.0)

    def test_eta_inv_nom(self):
        inv = pvwatts_inverter(pdc0_kw=5.0, eff_pct=96.0)
        assert_allclose(inv["eta_inv_nom"], 0.96)

    def test_eta_inv_ref(self):
        inv = pvwatts_inverter(pdc0_kw=5.0, eff_pct=96.0)
        assert "eta_inv_ref" in inv.index

    def test_different_sizes(self):
        inv_small = pvwatts_inverter(pdc0_kw=3.0, eff_pct=95.0)
        inv_large = pvwatts_inverter(pdc0_kw=10.0, eff_pct=97.5)
        assert_allclose(inv_small["pdc0"], 3000.0)
        assert_allclose(inv_large["pdc0"], 10000.0)
        assert_allclose(inv_large["eta_inv_nom"], 0.975)


# ── search functions ─────────────────────────────────────────────────────────


class TestSearch:
    @pytest.fixture()
    def mini_module_db(self):
        data = {
            "Canadian_Solar_CS6K-300MS": pd.Series({"pdc0": 300}),
            "Canadian_Solar_CS6K-400MS": pd.Series({"pdc0": 400}),
            "SunPower_SPR-X21-345": pd.Series({"pdc0": 345}),
            "LG_NeON2_370": pd.Series({"pdc0": 370}),
        }
        return pd.DataFrame(data)

    def test_search_modules_match(self, mini_module_db):
        results = search_modules("Canadian", mini_module_db, n=10)
        assert len(results) == 2
        assert all("Canadian" in r for r in results)

    def test_search_modules_case_insensitive(self, mini_module_db):
        results = search_modules("sunpower", mini_module_db, n=10)
        assert len(results) == 1

    def test_search_modules_no_match(self, mini_module_db):
        results = search_modules("nonexistent", mini_module_db, n=10)
        assert len(results) == 0

    def test_search_modules_limit(self, mini_module_db):
        results = search_modules("Solar", mini_module_db, n=1)
        assert len(results) == 1

    def test_search_inverters(self):
        data = {
            "ABB__MICRO_0_25_I_OUTD_US_208__208V_": pd.Series({"Paco": 250}),
            "SMA__SB3000US__240V_": pd.Series({"Paco": 3000}),
        }
        db = pd.DataFrame(data)
        results = search_inverters("SMA", db, n=10)
        assert len(results) == 1
        assert "SMA" in results[0]
