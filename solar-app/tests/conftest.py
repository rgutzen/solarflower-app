# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Shared fixtures for solar-app unit tests.

Patches Streamlit caching decorators so core modules can be imported and tested
without a running Streamlit server.
"""

from __future__ import annotations

import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# Ensure solar-app/ root is on sys.path so `from core.xxx import ...` works
_SOLAR_APP_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
if _SOLAR_APP_ROOT not in sys.path:
    sys.path.insert(0, _SOLAR_APP_ROOT)


# ---------------------------------------------------------------------------
# 1.  Stub out Streamlit BEFORE importing any application code
# ---------------------------------------------------------------------------


def _cache_stub(*args, **kwargs):
    """
    Drop-in replacement for @st.cache_data / @st.cache_resource.

    Handles both usage patterns:
      @st.cache_resource          → called with fn as first positional arg
      @st.cache_data(show_spinner=False) → called with kwargs, returns decorator
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        # @st.cache_resource  (bare decorator, no parentheses)
        return args[0]

    # @st.cache_data(show_spinner=False)  (decorator factory)
    def wrapper(fn):
        return fn

    return wrapper


# Build a minimal Streamlit stub so `import streamlit as st` works in core/*
_st = MagicMock()
_st.cache_data = _cache_stub
_st.cache_resource = _cache_stub
sys.modules.setdefault("streamlit", _st)


# ---------------------------------------------------------------------------
# 2.  Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def default_loss_budget():
    """Default LossBudget with factory defaults."""
    from core.losses import LossBudget

    return LossBudget()


@pytest.fixture()
def synthetic_tmy():
    """
    Synthetic TMY-like DataFrame for Berlin (52.5°N, 13.4°E).

    Uses a simple sinusoidal clear-sky pattern — NOT physically accurate but
    gives non-zero irradiance during daytime and zero at night.
    8760 rows, columns: ghi, dni, dhi, temp_air, wind_speed, pressure.
    """
    times = pd.date_range("2023-01-01", periods=8760, freq="1h", tz="UTC")
    doy = times.dayofyear.values
    hour = times.hour.values

    # Rough day-length model for ~52°N
    sunrise = 6.0 - 2.5 * np.cos(2 * np.pi * (doy - 172) / 365)
    sunset = 18.0 + 2.5 * np.cos(2 * np.pi * (doy - 172) / 365)
    daytime = (hour >= sunrise) & (hour < sunset)

    # Simple parabolic GHI curve peaking at solar noon
    solar_noon = 12.0
    hour_angle = (hour - solar_noon) / ((sunset - sunrise) / 2 + 1e-6)
    ghi_peak = 600 + 300 * np.cos(2 * np.pi * (doy - 172) / 365)  # summer peak ~900
    ghi = np.where(daytime, ghi_peak * np.maximum(1 - hour_angle**2, 0), 0.0)

    # Split into DNI/DHI (approx): DNI≈70% of GHI/sin(α), DHI≈30% of GHI
    # Use a rough solar altitude for the split
    lat_r = np.radians(52.5)
    decl = np.radians(23.44) * np.sin(2 * np.pi * (doy - 81) / 365)
    omega = np.radians(15.0 * (hour - 12.0))
    sin_alt = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(
        omega
    )
    sin_alt = np.clip(sin_alt, 0.01, 1.0)

    dni = np.where(daytime, ghi * 0.7 / sin_alt, 0.0)
    dni = np.clip(dni, 0, 1200)
    dhi = np.where(daytime, ghi * 0.3, 0.0)

    # Temperature: seasonal + diurnal
    temp = (
        10
        + 8 * np.cos(2 * np.pi * (doy - 200) / 365)
        + 3 * np.sin(2 * np.pi * hour / 24)
    )

    df = pd.DataFrame(
        {
            "ghi": ghi,
            "dni": dni,
            "dhi": dhi,
            "temp_air": temp,
            "wind_speed": np.full(8760, 3.0),
            "pressure": np.full(8760, 101325.0),
        },
        index=times,
    )
    return df


@pytest.fixture()
def default_module_params():
    """Generic 400 W parametric module (same as sidebar default)."""
    from core.system import parametric_module

    return parametric_module(
        pdc0=400.0,
        v_mp=34.0,
        i_mp=11.76,
        v_oc=41.0,
        i_sc=12.5,
        temp_coeff_pmax=-0.004,
        cells_in_series=66,
    )


@pytest.fixture()
def default_inverter_params():
    """Generic 5 kW PVWatts inverter (same as sidebar default)."""
    from core.system import pvwatts_inverter

    return pvwatts_inverter(pdc0_kw=5.0, eff_pct=97.0)
