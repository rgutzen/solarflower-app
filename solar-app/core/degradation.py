# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Module degradation projection over project lifetime.

Standard two-stage model (IEC 61853 convention):
  Year 1:  yield_1 = Y0 * (1 - LID)   — LID already in Y0 from run_simulation
  Year t:  yield_t = Y0 * (1 - r_deg)^(t-1)

Since run_simulation() already incorporates LID in the DC loss chain, we build
the projection directly from the first-year simulated yield.
"""

from __future__ import annotations
import numpy as np


def compute_lifetime_yield(
    annual_yield_kwh: float,
    degradation_rate: float,
    lifetime_yr: int = 25,
) -> np.ndarray:
    """
    Annual yield for each year of the project lifetime [kWh], shape (lifetime_yr,).

    Parameters
    ----------
    annual_yield_kwh  : first-year yield (already includes LID) from run_simulation()
    degradation_rate  : linear annual degradation fraction (e.g. 0.005 for 0.5%/yr)
    lifetime_yr       : number of years to project (default 25)
    """
    years = np.arange(lifetime_yr)
    return annual_yield_kwh * (1.0 - degradation_rate) ** years
