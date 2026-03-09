# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for core.climate — TMY fetch, clear-sky fallback, reindex helper."""

import pandas as pd
import pytest
from unittest.mock import patch
from numpy.testing import assert_allclose

from core.climate import _clear_sky_fallback, _reindex_tmy, fetch_tmy


# ── _reindex_tmy ─────────────────────────────────────────────────────────────


class TestReindexTMY:
    def test_output_length(self):
        idx_in = pd.date_range("2020-01-01", periods=8760, freq="1h", tz="UTC")
        result = _reindex_tmy(idx_in)
        assert len(result) == 8760

    def test_output_year(self):
        idx_in = pd.date_range("2018-01-01", periods=8760, freq="1h", tz="UTC")
        result = _reindex_tmy(idx_in)
        assert result[0].year == 2023

    def test_output_utc(self):
        idx_in = pd.date_range("2023-01-01", periods=8760, freq="1h", tz="UTC")
        result = _reindex_tmy(idx_in)
        assert str(result.tz) == "UTC"


# ── _clear_sky_fallback ─────────────────────────────────────────────────────


class TestClearSkyFallback:
    def test_shape(self):
        df = _clear_sky_fallback(52.5, 13.4)
        assert len(df) == 8760
        assert set(df.columns) >= {"ghi", "dni", "dhi", "temp_air", "wind_speed"}

    def test_ghi_daytime(self):
        """At Berlin mid-summer, noon GHI should be substantial."""
        df = _clear_sky_fallback(52.5, 13.4)
        # June 21 ≈ day 172 → hour 4344 onwards
        summer_noon = df.iloc[172 * 24 + 12]
        assert summer_noon["ghi"] > 200, f"Summer noon GHI = {summer_noon['ghi']}"

    def test_ghi_nighttime(self):
        """Berlin midnight GHI should be 0."""
        df = _clear_sky_fallback(52.5, 13.4)
        winter_midnight = df.iloc[0]  # Jan 1, 00:00 UTC
        assert_allclose(winter_midnight["ghi"], 0.0, atol=1.0)

    def test_equator(self):
        """Equatorial location should have higher total GHI than Berlin."""
        df_equator = _clear_sky_fallback(0.0, 0.0)
        df_berlin = _clear_sky_fallback(52.5, 13.4)
        assert df_equator["ghi"].sum() > df_berlin["ghi"].sum()


# ── fetch_tmy fallback chain ────────────────────────────────────────────────


class TestFetchTMYFallback:
    @patch("core.climate._fetch_pvgis_tmy", side_effect=Exception("API down"))
    @patch("core.climate._fetch_openmeteo_year", side_effect=Exception("API down"))
    def test_falls_back_to_clear_sky(self, mock_om, mock_pvgis):
        """When both APIs fail, fetch_tmy returns clear-sky fallback."""
        df, source = fetch_tmy(52.5, 13.4)
        assert len(df) == 8760
        assert "Clear-sky" in source or "clear" in source.lower()

    @patch("core.climate._fetch_pvgis_tmy", side_effect=Exception("API down"))
    @patch("core.climate._fetch_openmeteo_year")
    def test_falls_back_to_openmeteo(self, mock_om, mock_pvgis):
        """When PVGIS fails, fetch_tmy tries Open-Meteo."""
        times = pd.date_range("2023-01-01", periods=8760, freq="1h", tz="UTC")
        mock_df = pd.DataFrame(
            {
                "ghi": [500.0] * 8760,
                "dni": [300.0] * 8760,
                "dhi": [200.0] * 8760,
                "temp_air": [15.0] * 8760,
                "wind_speed": [3.0] * 8760,
                "pressure": [101325.0] * 8760,
            },
            index=times,
        )
        mock_om.return_value = (mock_df, "Open-Meteo 2023")
        df, source = fetch_tmy(52.5, 13.4)
        assert "Open-Meteo" in source
        mock_om.assert_called_once()
