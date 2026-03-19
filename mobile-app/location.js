// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * location.js — Geolocation, reverse geocoding, and location persistence.
 *
 * Responsibilities:
 *   - GPS via navigator.geolocation
 *   - URL deep-link parsing (?lat=&lon=)
 *   - Reverse geocoding via Nominatim (best-effort, no API key)
 *   - localStorage persistence so location survives page reloads
 *   - Input validation for manual lat/lon entry
 */

const STORAGE_KEY = 'panel-compass-location';

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/**
 * Validate latitude and longitude values.
 *
 * @param {number} lat
 * @param {number} lon
 * @returns {{ valid: boolean, field?: 'lat'|'lon' }}
 */
export function validateCoords(lat, lon) {
  if (isNaN(lat) || lat < -90 || lat > 90) return { valid: false, field: 'lat' };
  if (isNaN(lon) || lon < -180 || lon > 180) return { valid: false, field: 'lon' };
  return { valid: true };
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

/**
 * Format lat/lon as a readable coordinate string (e.g. "52.5°N, 13.4°E").
 */
export function formatCoords(lat, lon) {
  return `${Math.abs(lat).toFixed(1)}°${lat >= 0 ? 'N' : 'S'}, ${Math.abs(lon).toFixed(1)}°${lon >= 0 ? 'E' : 'W'}`;
}

// ---------------------------------------------------------------------------
// localStorage persistence
// ---------------------------------------------------------------------------

/**
 * Save the current location to localStorage for session persistence.
 *
 * @param {number} lat
 * @param {number} lon
 * @param {string} name — display name (city, coords, etc.)
 */
export function saveLocation(lat, lon, name) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ lat, lon, name }));
  } catch (_) {
    // Silently fail if localStorage is unavailable (private browsing, storage full)
  }
}

/**
 * Load the previously saved location from localStorage.
 *
 * @returns {{ lat: number, lon: number, name: string }|null}
 */
export function loadSavedLocation() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const { lat, lon, name } = JSON.parse(raw);
    if (!validateCoords(lat, lon).valid) return null;
    return { lat, lon, name: name || null };
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// URL deep-link
// ---------------------------------------------------------------------------

/**
 * Parse lat/lon from URL query string: ?lat=52.5&lon=13.4
 *
 * @returns {{ lat: number, lon: number }|null}
 */
export function readURLParams() {
  try {
    const params = new URLSearchParams(window.location.search);
    const lat = parseFloat(params.get('lat'));
    const lon = parseFloat(params.get('lon'));
    if (validateCoords(lat, lon).valid) return { lat, lon };
  } catch (_) {}
  return null;
}

// ---------------------------------------------------------------------------
// Reverse geocoding
// ---------------------------------------------------------------------------

/**
 * Reverse geocode lat/lon to a human-readable location name using Nominatim.
 * Falls back to formatted coordinates on any failure.
 *
 * @param {number} lat
 * @param {number} lon
 * @returns {Promise<string>}
 */
export async function reverseGeocode(lat, lon) {
  try {
    const resp = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&zoom=10`,
      { headers: { 'Accept-Language': 'en' } }
    );
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    const addr = data.address || {};
    const city = addr.city || addr.town || addr.village || addr.county || '';
    const country = addr.country_code ? addr.country_code.toUpperCase() : '';
    if (city) return `${city}${country ? ', ' + country : ''}`;
  } catch (_) {
    // Network unavailable or Nominatim rate-limited — fall back to coords
  }
  return formatCoords(lat, lon);
}

// ---------------------------------------------------------------------------
// GPS
// ---------------------------------------------------------------------------

/**
 * Request the device's current GPS position.
 *
 * @param {function} onSuccess — (lat: number, lon: number) => void
 * @param {function} onError   — (reason: 'denied'|'unavailable', message?: string) => void
 */
export function requestGeolocation(onSuccess, onError) {
  if (!('geolocation' in navigator)) {
    onError('unavailable');
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => onSuccess(pos.coords.latitude, pos.coords.longitude),
    (err) => onError(err.code === 1 ? 'denied' : 'unavailable', err.message),
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}
