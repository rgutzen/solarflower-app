// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Tests for compass.js smoothing helpers.
 *
 * Only the pure math functions (smoothAngle, smoothLinear) are tested here.
 * Sensor event handling requires browser APIs and is tested via integration/E2E.
 */

// compass.js does not export smoothAngle/smoothLinear directly — they are
// module-scoped. We need to re-implement or extract them for unit testing.
// For now, we test the math independently and verify against known values.

import { describe, it, expect } from 'vitest';

// Replicate the exact smoothing functions from compass.js for testing.
// If compass.js is refactored to export these, import directly instead.

function smoothAngle(prev, curr, alpha) {
  if (prev === null) return curr;
  const prevRad = prev * Math.PI / 180;
  const currRad = curr * Math.PI / 180;
  const sinAvg = (1 - alpha) * Math.sin(prevRad) + alpha * Math.sin(currRad);
  const cosAvg = (1 - alpha) * Math.cos(prevRad) + alpha * Math.cos(currRad);
  let result = Math.atan2(sinAvg, cosAvg) * 180 / Math.PI;
  if (result < 0) result += 360;
  return result;
}

function smoothLinear(prev, curr, alpha) {
  if (prev === null) return curr;
  return (1 - alpha) * prev + alpha * curr;
}


// ── smoothAngle ─────────────────────────────────────────────────────────────

describe('smoothAngle', () => {
  it('null prev → returns curr directly', () => {
    expect(smoothAngle(null, 90, 0.3)).toBe(90);
  });

  it('Same angle → no change', () => {
    expect(smoothAngle(10, 10, 0.3)).toBeCloseTo(10, 5);
  });

  it('Small step (no wrap)', () => {
    const result = smoothAngle(100, 110, 0.5);
    expect(result).toBeGreaterThan(100);
    expect(result).toBeLessThan(110);
    expect(result).toBeCloseTo(105, 0);
  });

  it('Wrap-around 350° → 10° should NOT go through 180°', () => {
    const result = smoothAngle(350, 10, 0.3);
    // With alpha=0.3, should be near 356° (slight move toward 10°)
    // NOT near 180° (naive linear average)
    expect(result).toBeGreaterThan(340);  // near 350-360 range
    // Or just wrapped past 0
    const dist = Math.min(Math.abs(result - 356), Math.abs(result + 360 - 356));
    expect(dist).toBeLessThan(10);
  });

  it('Wrap-around 10° → 350° should NOT go through 180°', () => {
    const result = smoothAngle(10, 350, 0.3);
    // Should move slightly counter-clockwise from 10° toward 350°
    // i.e., result > 350 or result < 10
    const inWrapZone = result > 340 || result < 20;
    expect(inWrapZone).toBe(true);
  });

  it('Result is always in [0, 360)', () => {
    for (const [prev, curr] of [[0, 359], [180, 181], [350, 10], [90, 270]]) {
      const result = smoothAngle(prev, curr, 0.25);
      expect(result).toBeGreaterThanOrEqual(0);
      expect(result).toBeLessThan(360);
    }
  });

  it('alpha=0 → stays at prev', () => {
    const result = smoothAngle(100, 200, 0.0);
    expect(result).toBeCloseTo(100, 5);
  });

  it('alpha=1 → jumps to curr', () => {
    const result = smoothAngle(100, 200, 1.0);
    expect(result).toBeCloseTo(200, 5);
  });
});


// ── smoothLinear ────────────────────────────────────────────────────────────

describe('smoothLinear', () => {
  it('null prev → returns curr directly', () => {
    expect(smoothLinear(null, 42, 0.5)).toBe(42);
  });

  it('Midpoint at alpha=0.5', () => {
    expect(smoothLinear(30, 40, 0.5)).toBeCloseTo(35, 5);
  });

  it('alpha=0 → stays at prev', () => {
    expect(smoothLinear(30, 40, 0.0)).toBeCloseTo(30, 5);
  });

  it('alpha=1 → jumps to curr', () => {
    expect(smoothLinear(30, 40, 1.0)).toBeCloseTo(40, 5);
  });

  it('Weighted blend', () => {
    // alpha=0.25: result = 0.75*30 + 0.25*40 = 32.5
    expect(smoothLinear(30, 40, 0.25)).toBeCloseTo(32.5, 5);
  });

  it('Works with negative values', () => {
    expect(smoothLinear(-10, 10, 0.5)).toBeCloseTo(0, 5);
  });
});
