# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for pure helper functions in ui.sidebar."""

import pytest

# Import helpers — they are module-level functions (no Streamlit dependency)
from ui.sidebar import _az_label, _optimal_tilt_guess, _size_label


class TestOptimalTiltGuess:
    def test_berlin(self):
        """Berlin 52.5°N → int(52.5 * 0.76 + 3.1) = 43."""
        assert _optimal_tilt_guess(52.5) == 43

    def test_equator(self):
        """Equator → int(0 * 0.76 + 3.1) = 3."""
        assert _optimal_tilt_guess(0.0) == 3

    def test_southern_hemisphere(self):
        """Cape Town -33.9° → int(33.9 * 0.76 + 3.1) = 28."""
        assert _optimal_tilt_guess(-33.9) == 28

    def test_high_latitude(self):
        """Tromsø 69.6°N → int(69.6 * 0.76 + 3.1) = int(55.996) = 55."""
        assert _optimal_tilt_guess(69.6) == int(69.6 * 0.76 + 3.1)


class TestAzLabel:
    def test_north(self):
        assert _az_label(0) == "North"

    def test_south(self):
        assert _az_label(180) == "South"

    def test_east(self):
        assert _az_label(90) == "East"

    def test_west(self):
        assert _az_label(270) == "West"

    def test_northeast(self):
        assert _az_label(45) == "North-East"

    def test_wrap_360(self):
        """360° should be the same as 0° → North."""
        assert _az_label(360) == "North"


class TestSizeLabel:
    def test_very_small(self):
        label = _size_label(1.0)
        assert "very small" in label or "off-grid" in label

    def test_small_residential(self):
        label = _size_label(4.0)
        assert "small" in label.lower()

    def test_residential(self):
        label = _size_label(10.0)
        assert "residential" in label.lower()

    def test_commercial(self):
        label = _size_label(100.0)
        assert "commercial" in label.lower() or "utility" in label.lower()
