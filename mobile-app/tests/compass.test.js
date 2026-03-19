// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

// @vitest-environment jsdom

/**
 * Tests for compass.js: smoothing helpers and sensor watchdog.
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { smoothAngle, smoothLinear, start, stop } from '../compass.js';


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
    const dist = Math.min(Math.abs(result - 356), Math.abs(result + 360 - 356));
    expect(dist).toBeLessThan(10);
  });

  it('Wrap-around 10° → 350° should NOT go through 180°', () => {
    const result = smoothAngle(10, 350, 0.3);
    const inWrapZone = result > 340 || result < 20;
    expect(inWrapZone).toBe(true);
  });

  it('Wrap-around 1° → 359° stays near 0°', () => {
    const result = smoothAngle(1, 359, 0.5);
    const inWrapZone = result > 350 || result < 10;
    expect(inWrapZone).toBe(true);
  });

  it('Wrap-around 180° → 0°: result is a valid angle in [0, 360)', () => {
    // 180° and 0° are antipodal (180° apart): the circular mean is undefined.
    // atan2(≈0, 0) returns 90° due to floating-point noise in sin(π).
    // Just verify the output is a valid angle; the midpoint direction is arbitrary.
    const result = smoothAngle(180, 0, 0.5);
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThan(360);
  });

  it('Wrap-around 270° → 90°: result is a valid angle in [0, 360)', () => {
    // 270° and 90° are antipodal: same degenerate case as 180°/0°.
    // Output is arbitrary but must be a valid angle.
    const result = smoothAngle(270, 90, 0.5);
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThan(360);
  });

  it('Result is always in [0, 360)', () => {
    for (const [prev, curr] of [[0, 359], [180, 181], [350, 10], [90, 270]]) {
      const result = smoothAngle(prev, curr, 0.25);
      expect(result).toBeGreaterThanOrEqual(0);
      expect(result).toBeLessThan(360);
    }
  });

  it('alpha=0 → stays at prev', () => {
    expect(smoothAngle(100, 200, 0.0)).toBeCloseTo(100, 5);
  });

  it('alpha=1 → jumps to curr', () => {
    expect(smoothAngle(100, 200, 1.0)).toBeCloseTo(200, 5);
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


// ── Watchdog ─────────────────────────────────────────────────────────────────

describe('sensor watchdog', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    stop(); // Reset module state between tests
  });

  afterEach(() => {
    stop();
    vi.useRealTimers();
  });

  it('calls onError with sensor-timeout when no event fires within 5s', () => {
    const onError = vi.fn();
    start(() => {}, onError);

    vi.advanceTimersByTime(5001);

    expect(onError).toHaveBeenCalledOnce();
    expect(onError).toHaveBeenCalledWith('sensor-timeout');
  });

  it('does not call onError when a sensor event fires before timeout', () => {
    const onError = vi.fn();
    start(() => {}, onError);

    // Simulate a deviceorientation event arriving before the 5s watchdog
    vi.advanceTimersByTime(2000);
    window.dispatchEvent(new Event('deviceorientation'));

    // Now advance past the original watchdog deadline
    vi.advanceTimersByTime(4000);

    expect(onError).not.toHaveBeenCalled();
  });

  it('stop() prevents the watchdog from firing', () => {
    const onError = vi.fn();
    start(() => {}, onError);
    stop();

    vi.advanceTimersByTime(6000);

    expect(onError).not.toHaveBeenCalled();
  });
});
