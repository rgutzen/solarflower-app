// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * api.js — Optional REST API client for PVGIS TMY-backed yield refinement.
 *
 * The API base URL is read from localStorage at call time, making it
 * configurable at runtime without editing source code:
 *
 *   localStorage.setItem('api-base', 'https://your-api-host.com')
 *
 * When no API base is set (default), all calls return null immediately
 * and the app uses the local JS model in solar.js.
 *
 * API Contract:
 *   POST /api/estimate
 *   Body: { lat, lon, tilt_deg, azimuth_deg, peak_power_kwp, system_loss_pct }
 *   Response: { specific_yield_kwh_kwp, optimal_tilt_deg?, optimal_azimuth_deg? }
 */

const REQUEST_TIMEOUT_MS = 15000;

function getApiBase() {
  try { return localStorage.getItem('api-base') ?? null; } catch (_) { return null; }
}

/**
 * POST /api/estimate — Fetch PVGIS TMY yield estimate from the Solarflower API.
 * Returns parsed response object, or null if API is disabled or the call fails.
 * Never throws; all errors are swallowed and return null.
 *
 * @param {number} lat
 * @param {number} lon
 * @param {number} tilt    — panel tilt in degrees (0 = horizontal, 90 = vertical)
 * @param {number} azimuth — panel azimuth in degrees (0 = N, 180 = S)
 * @returns {Promise<object|null>}
 */
export async function fetchEstimate(lat, lon, tilt, azimuth) {
  const base = getApiBase();
  if (!base) return null;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${base}/api/estimate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lat,
        lon,
        tilt_deg: tilt,
        azimuth_deg: azimuth,
        peak_power_kwp: 1.0,     // normalise to 1 kWp → response is kWh/kWp
        system_loss_pct: 14.0,
      }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    clearTimeout(timer);
    return null;
  }
}
