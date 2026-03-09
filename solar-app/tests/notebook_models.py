# SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
First-principles solar physics models ported from the educational notebook.

These are independent implementations (numpy only, zero pvlib dependency) that
serve as an oracle for cross-validating the web-app's pvlib-backed calculations.

Source: notebook/solar_panel_power.ipynb
Models: Spencer 1971 (orbital), Meinel 1976 (clear-sky), Liu-Jordan (POA).
"""

from __future__ import annotations

import numpy as np

# Solar constant [W/m²]
S0 = 1361.0


def day_angle(doy: np.ndarray | float) -> np.ndarray | float:
    """Day angle B [radians].  doy = day of year (1–365)."""
    return 2 * np.pi * (doy - 1) / 365.25


def eccentricity_correction(doy: np.ndarray | float) -> np.ndarray | float:
    """Ratio (d₀/d)²: accounts for Earth's elliptical orbit (Spencer 1971)."""
    B = day_angle(doy)
    return (
        1.000110
        + 0.034221 * np.cos(B)
        + 0.001280 * np.sin(B)
        + 0.000719 * np.cos(2 * B)
        + 0.000077 * np.sin(2 * B)
    )


def solar_declination(doy: np.ndarray | float) -> np.ndarray | float:
    """Solar declination δ [radians] (Spencer 1971)."""
    B = day_angle(doy)
    return (
        0.006918
        - 0.399912 * np.cos(B)
        + 0.070257 * np.sin(B)
        - 0.006758 * np.cos(2 * B)
        + 0.000907 * np.sin(2 * B)
        - 0.002697 * np.cos(3 * B)
        + 0.001480 * np.sin(3 * B)
    )


def equation_of_time(doy: np.ndarray | float) -> np.ndarray | float:
    """Equation of time ET [minutes] — converts clock time to solar time."""
    B = day_angle(doy)
    return 229.18 * (
        0.000075
        + 0.001868 * np.cos(B)
        - 0.032077 * np.sin(B)
        - 0.014615 * np.cos(2 * B)
        - 0.04089 * np.sin(2 * B)
    )


def solar_altitude_azimuth(
    doy: np.ndarray | float,
    hour_utc: np.ndarray | float,
    lat_deg: float,
    lon_deg: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Solar altitude α [rad] and azimuth Az [rad, from North clockwise].
    Accepts scalars and numpy arrays.
    """
    delta = solar_declination(doy)
    phi = np.radians(lat_deg)

    # Apparent solar time
    ET = equation_of_time(doy)
    LSM = np.round(lon_deg / 15.0) * 15.0
    t_solar = hour_utc + ET / 60.0 + (lon_deg - LSM) / 15.0

    # Hour angle (0 at solar noon)
    omega = np.radians(15.0 * (t_solar - 12.0))

    # Altitude
    sin_alt = np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.cos(omega)
    altitude = np.arcsin(np.clip(sin_alt, -1.0, 1.0))

    # Azimuth via atan2
    cos_alt = np.cos(altitude) + 1e-12
    sin_az = np.cos(delta) * np.sin(omega) / cos_alt
    cos_az = (
        np.sin(delta) * np.cos(phi) - np.cos(delta) * np.sin(phi) * np.cos(omega)
    ) / cos_alt
    azimuth = np.arctan2(sin_az, cos_az) % (2 * np.pi)

    return altitude, azimuth


def air_mass(
    altitude_rad: np.ndarray | float, elevation_m: float = 0.0
) -> np.ndarray | float:
    """Kasten-Young air mass, corrected for site elevation."""
    alt_deg = np.degrees(altitude_rad)
    denom = np.sin(altitude_rad) + 0.50572 * np.maximum(alt_deg + 6.07995, 0.01) ** (
        -1.6364
    )
    AM_sl = np.where(alt_deg > 0.0, 1.0 / denom, np.inf)
    return AM_sl * np.exp(-elevation_m / 8435.0)


def clear_sky(
    G_ext: np.ndarray | float,
    altitude_rad: np.ndarray | float,
    elevation_m: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Clear-sky irradiance components [W/m²] — Meinel 1976 DNI model.
    Returns: (DNI, DHI, GHI).
    """
    daytime = altitude_rad > 0.0
    AM = air_mass(altitude_rad, elevation_m)
    AM_clip = np.minimum(AM, 38.0)

    DNI = np.where(daytime, G_ext * 0.7 ** (AM_clip**0.678), 0.0)
    DHI = np.where(daytime, 0.1 * G_ext * np.sin(altitude_rad), 0.0)
    GHI = DNI * np.where(daytime, np.sin(altitude_rad), 0.0) + DHI
    return DNI, DHI, GHI


def panel_irradiance(
    DNI: np.ndarray | float,
    DHI: np.ndarray | float,
    GHI: np.ndarray | float,
    altitude_rad: np.ndarray | float,
    azimuth_rad: np.ndarray | float,
    tilt_deg: float,
    panel_az_deg: float,
    albedo: float = 0.20,
) -> np.ndarray | float:
    """
    Total in-plane irradiance [W/m²] (isotropic sky / Liu-Jordan model).
    """
    beta = np.radians(tilt_deg)
    gamma = np.radians(panel_az_deg)

    cos_theta = np.sin(altitude_rad) * np.cos(beta) + np.cos(altitude_rad) * np.sin(
        beta
    ) * np.cos(azimuth_rad - gamma)
    cos_theta = np.where(altitude_rad > 0.0, np.clip(cos_theta, 0.0, 1.0), 0.0)

    G_direct = DNI * cos_theta
    G_sky = DHI * (1.0 + np.cos(beta)) / 2.0
    G_ground = GHI * albedo * (1.0 - np.cos(beta)) / 2.0
    return G_direct + G_sky + G_ground


def compute_annual_energy(
    lat_deg: float,
    lon_deg: float,
    elevation_m: float,
    tilt_deg: float,
    panel_az_deg: float,
    area_m2: float = 1.0,
    efficiency: float = 0.20,
    albedo: float = 0.20,
    dt: float = 1.0,
) -> float:
    """
    Annual energy [kWh] for a single orientation using clear-sky model.
    Uses Riemann integration over all daylight hours.
    """
    hours = np.arange(dt / 2, 24.0, dt)
    days = np.arange(1, 366)
    DOY, HOUR = np.meshgrid(days, hours, indexing="ij")

    G_ext = S0 * eccentricity_correction(DOY)
    alt, az = solar_altitude_azimuth(DOY, HOUR, lat_deg, lon_deg)
    DNI, DHI, GHI = clear_sky(G_ext, alt, elevation_m)
    G_T = panel_irradiance(DNI, DHI, GHI, alt, az, tilt_deg, panel_az_deg, albedo)

    return float(np.sum(area_m2 * efficiency * G_T) * dt / 1000)
