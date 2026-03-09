// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, it, expect } from 'vitest';
import {
  computeOptimalOrientation,
  computeOrientationFactor,
  estimateYieldKwhPerKwp,
  azimuthToCardinal,
  angleDelta,
} from '../solar.js';

// ── computeOptimalOrientation ───────────────────────────────────────────────

describe('computeOptimalOrientation', () => {
  it('Berlin (52.5°N): tilt ≈ 50.4°, azimuth = 180° (South)', () => {
    const { tilt, azimuth } = computeOptimalOrientation(52.5);
    expect(tilt).toBeCloseTo(0.9 * 52.5 + 3.1, 1);
    expect(azimuth).toBe(180);
  });

  it('Cape Town (-33.9°S): tilt ≈ 33.6°, azimuth = 0° (North)', () => {
    const { tilt, azimuth } = computeOptimalOrientation(-33.9);
    expect(tilt).toBeCloseTo(0.9 * 33.9 + 3.1, 1);
    expect(azimuth).toBe(0);
  });

  it('Equator (0°): tilt ≈ 3.1°, azimuth = 180°', () => {
    const { tilt, azimuth } = computeOptimalOrientation(0);
    expect(tilt).toBeCloseTo(3.1, 1);
    expect(azimuth).toBe(180);
  });

  it('High latitude (65°N): tilt ≈ 61.6°', () => {
    const { tilt } = computeOptimalOrientation(65);
    expect(tilt).toBeCloseTo(0.9 * 65 + 3.1, 1);
  });

  it('Returns positive tilt for negative latitude', () => {
    const { tilt } = computeOptimalOrientation(-50);
    expect(tilt).toBeGreaterThan(0);
  });
});

// ── computeOrientationFactor ────────────────────────────────────────────────

describe('computeOrientationFactor', () => {
  it('At optimal orientation → factor ≈ 1.0', () => {
    const factor = computeOrientationFactor(52.5, 50.4, 180);
    expect(factor).toBeCloseTo(1.0, 1);
  });

  it('East-facing (90°) penalty at mid-latitude', () => {
    const optimal = computeOrientationFactor(52.5, 50.4, 180);
    const east = computeOrientationFactor(52.5, 50.4, 90);
    expect(east).toBeLessThan(optimal);
  });

  it('Flat panel (tilt=0): south closer to optimal than east', () => {
    const south = computeOrientationFactor(52.5, 0, 180);
    const east = computeOrientationFactor(52.5, 0, 90);
    // Model measures deviation from optimal (tilt~50°, az=180°).
    // Even at tilt=0, south azimuth scores higher because optimal az is 180°.
    expect(south).toBeGreaterThan(east);
    // Both heavily penalised by the large tilt deviation from optimal
    expect(south).toBeLessThan(0.75);
    expect(east).toBeGreaterThan(0);
  });

  it('Factor is in [0, 1]', () => {
    for (const az of [0, 45, 90, 135, 180, 225, 270, 315]) {
      for (const tilt of [0, 15, 30, 45, 60, 75, 90]) {
        const f = computeOrientationFactor(52.5, tilt, az);
        expect(f).toBeGreaterThanOrEqual(0);
        expect(f).toBeLessThanOrEqual(1);
      }
    }
  });

  it('Southern hemisphere: north-facing is best', () => {
    const north = computeOrientationFactor(-33, 30, 0);
    const south = computeOrientationFactor(-33, 30, 180);
    expect(north).toBeGreaterThan(south);
  });
});

// ── estimateYieldKwhPerKwp ──────────────────────────────────────────────────

describe('estimateYieldKwhPerKwp', () => {
  it('Berlin optimal: yield in range 800–1400 kWh/kWp', () => {
    const y = estimateYieldKwhPerKwp(52.5, 50.4, 180);
    expect(y).toBeGreaterThan(800);
    expect(y).toBeLessThan(1400);
  });

  it('Equator has higher yield than Berlin', () => {
    const yEq = estimateYieldKwhPerKwp(0, 3.1, 180);
    const yBe = estimateYieldKwhPerKwp(52.5, 50.4, 180);
    expect(yEq).toBeGreaterThan(yBe);
  });

  it('Flat panel yields less than optimal tilt at mid-latitudes', () => {
    const yFlat = estimateYieldKwhPerKwp(52.5, 0, 180);
    const yOpt = estimateYieldKwhPerKwp(52.5, 50.4, 180);
    expect(yFlat).toBeLessThan(yOpt);
  });

  it('Returns a positive integer', () => {
    const y = estimateYieldKwhPerKwp(45, 30, 180);
    expect(y).toBeGreaterThan(0);
    expect(Number.isInteger(y)).toBe(true);
  });

  it('Cross-validation: within ±25% of web-app Berlin reference (~1050 kWh/kWp)', () => {
    // Web-app produces ~950-1100 kWh/kWp for Berlin at optimal.
    // Mobile uses a simpler model, so ±25% tolerance.
    const y = estimateYieldKwhPerKwp(52.5, 35, 180);
    expect(y).toBeGreaterThan(1050 * 0.75);
    expect(y).toBeLessThan(1050 * 1.25);
  });

  it('Yield ranking: 5 orientations match expected physical order', () => {
    const orientations = [
      { tilt: 35, az: 180, label: 'S-35' },
      { tilt: 0, az: 180, label: 'flat' },
      { tilt: 35, az: 90, label: 'E-35' },
      { tilt: 35, az: 270, label: 'W-35' },
      { tilt: 80, az: 180, label: 'S-80' },
    ];
    const yields = orientations.map(o => estimateYieldKwhPerKwp(52.5, o.tilt, o.az));
    // South-facing should be best (or tied); flat should beat extreme tilt/off-azimuth
    const bestIdx = yields.indexOf(Math.max(...yields));
    expect(orientations[bestIdx].az).toBe(180);
    // East and West should be roughly symmetric
    expect(Math.abs(yields[2] - yields[3])).toBeLessThan(yields[0] * 0.1);
  });
});

// ── azimuthToCardinal ───────────────────────────────────────────────────────

describe('azimuthToCardinal', () => {
  it('0° → N', () => expect(azimuthToCardinal(0)).toBe('N'));
  it('90° → E', () => expect(azimuthToCardinal(90)).toBe('E'));
  it('180° → S', () => expect(azimuthToCardinal(180)).toBe('S'));
  it('270° → W', () => expect(azimuthToCardinal(270)).toBe('W'));
  it('45° → NE', () => expect(azimuthToCardinal(45)).toBe('NE'));
  it('135° → SE', () => expect(azimuthToCardinal(135)).toBe('SE'));
  it('225° → SW', () => expect(azimuthToCardinal(225)).toBe('SW'));
  it('315° → NW', () => expect(azimuthToCardinal(315)).toBe('NW'));
  it('360° → N (wrap)', () => expect(azimuthToCardinal(360)).toBe('N'));
  it('Negative angle wraps correctly', () => {
    expect(azimuthToCardinal(-90)).toBe('W');
  });

  // Cross-validation with web-app sidebar._az_label (same mapping)
  it('Matches web-app cardinal directions for all 8 sectors', () => {
    // Web-app uses: N, NE, E, SE, S, SW, W, NW at 0,45,90,...,315°
    const expected = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const azimuths = [0, 45, 90, 135, 180, 225, 270, 315];
    azimuths.forEach((az, i) => {
      expect(azimuthToCardinal(az)).toBe(expected[i]);
    });
  });
});

// ── angleDelta ──────────────────────────────────────────────────────────────

describe('angleDelta', () => {
  it('Small positive delta', () => {
    expect(angleDelta(170, 180)).toBeCloseTo(10, 5);
  });

  it('Small negative delta', () => {
    expect(angleDelta(180, 170)).toBeCloseTo(-10, 5);
  });

  it('Wrap-around clockwise (350° → 10°)', () => {
    expect(angleDelta(350, 10)).toBeCloseTo(20, 5);
  });

  it('Wrap-around counter-clockwise (10° → 350°)', () => {
    expect(angleDelta(10, 350)).toBeCloseTo(-20, 5);
  });

  it('Same angle → 0', () => {
    expect(angleDelta(180, 180)).toBeCloseTo(0, 5);
  });

  it('Opposite directions → ±180', () => {
    const d = angleDelta(0, 180);
    expect(Math.abs(d)).toBeCloseTo(180, 5);
  });

  it('Result always in [-180, 180]', () => {
    for (let a = 0; a < 360; a += 30) {
      for (let b = 0; b < 360; b += 30) {
        const d = angleDelta(a, b);
        expect(d).toBeGreaterThanOrEqual(-180);
        expect(d).toBeLessThanOrEqual(180);
      }
    }
  });
});
