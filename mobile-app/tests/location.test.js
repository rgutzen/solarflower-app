// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

// @vitest-environment jsdom

/**
 * Tests for location.js: coordinate validation, localStorage persistence,
 * URL param parsing, and coordinate formatting.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  validateCoords,
  formatCoords,
  saveLocation,
  loadSavedLocation,
} from '../location.js';


// ── validateCoords ───────────────────────────────────────────────────────────

describe('validateCoords', () => {
  it('valid coords → {valid: true}', () => {
    expect(validateCoords(52.5, 13.4).valid).toBe(true);
    expect(validateCoords(0, 0).valid).toBe(true);
  });

  it('latitude edge cases: ±90 are valid', () => {
    expect(validateCoords(90, 0).valid).toBe(true);
    expect(validateCoords(-90, 0).valid).toBe(true);
  });

  it('longitude edge cases: ±180 are valid', () => {
    expect(validateCoords(0, 180).valid).toBe(true);
    expect(validateCoords(0, -180).valid).toBe(true);
  });

  it('lat out of range → {valid: false, field: lat}', () => {
    const r = validateCoords(91, 0);
    expect(r.valid).toBe(false);
    expect(r.field).toBe('lat');
  });

  it('lat below range → {valid: false, field: lat}', () => {
    const r = validateCoords(-91, 0);
    expect(r.valid).toBe(false);
    expect(r.field).toBe('lat');
  });

  it('lon out of range → {valid: false, field: lon}', () => {
    const r = validateCoords(0, 181);
    expect(r.valid).toBe(false);
    expect(r.field).toBe('lon');
  });

  it('NaN lat → {valid: false, field: lat}', () => {
    const r = validateCoords(NaN, 13);
    expect(r.valid).toBe(false);
    expect(r.field).toBe('lat');
  });

  it('NaN lon → {valid: false, field: lon}', () => {
    const r = validateCoords(52, NaN);
    expect(r.valid).toBe(false);
    expect(r.field).toBe('lon');
  });
});


// ── formatCoords ─────────────────────────────────────────────────────────────

describe('formatCoords', () => {
  it('Northern hemisphere, Eastern longitude', () => {
    expect(formatCoords(52.5, 13.4)).toBe('52.5°N, 13.4°E');
  });

  it('Southern hemisphere, Western longitude', () => {
    expect(formatCoords(-33.9, -70.7)).toBe('33.9°S, 70.7°W');
  });

  it('Equator, prime meridian', () => {
    expect(formatCoords(0, 0)).toBe('0.0°N, 0.0°E');
  });
});


// ── saveLocation / loadSavedLocation ─────────────────────────────────────────

describe('location persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('loadSavedLocation returns null when nothing saved', () => {
    expect(loadSavedLocation()).toBeNull();
  });

  it('saveLocation + loadSavedLocation round-trip', () => {
    saveLocation(52.5, 13.4, 'Berlin, DE');
    const result = loadSavedLocation();
    expect(result).not.toBeNull();
    expect(result.lat).toBe(52.5);
    expect(result.lon).toBe(13.4);
    expect(result.name).toBe('Berlin, DE');
  });

  it('loadSavedLocation returns null when saved data has invalid coords', () => {
    localStorage.setItem('panel-compass-location', JSON.stringify({ lat: 999, lon: 0, name: 'Bad' }));
    expect(loadSavedLocation()).toBeNull();
  });

  it('loadSavedLocation returns null when saved data is malformed JSON', () => {
    localStorage.setItem('panel-compass-location', 'not-json');
    expect(loadSavedLocation()).toBeNull();
  });

  it('overwrites previous saved location', () => {
    saveLocation(52.5, 13.4, 'Berlin, DE');
    saveLocation(-33.9, 18.4, 'Cape Town, ZA');
    const result = loadSavedLocation();
    expect(result.lat).toBe(-33.9);
    expect(result.name).toBe('Cape Town, ZA');
  });

  it('handles missing name field gracefully', () => {
    localStorage.setItem('panel-compass-location', JSON.stringify({ lat: 52.5, lon: 13.4 }));
    const result = loadSavedLocation();
    expect(result).not.toBeNull();
    expect(result.lat).toBe(52.5);
    expect(result.name).toBeNull();
  });
});
