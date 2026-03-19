// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

// @vitest-environment jsdom

/**
 * Tests for api.js: fetchEstimate behaviour with and without API base configured.
 * Uses vi.stubGlobal to mock fetch and localStorage.
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { fetchEstimate } from '../api.js';


// ── helpers ──────────────────────────────────────────────────────────────────

function mockFetch(response, { ok = true, delay = 0 } = {}) {
  return vi.stubGlobal('fetch', vi.fn(() =>
    new Promise((resolve, reject) => {
      const handler = () => {
        if (response instanceof Error) {
          reject(response);
        } else {
          resolve({
            ok,
            json: () => Promise.resolve(response),
          });
        }
      };
      delay > 0 ? setTimeout(handler, delay) : handler();
    })
  ));
}


// ── fetchEstimate ─────────────────────────────────────────────────────────────

describe('fetchEstimate', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns null when no API base is configured', async () => {
    mockFetch({ specific_yield_kwh_kwp: 1200 });
    const result = await fetchEstimate(52.5, 13.4, 35, 180);
    expect(result).toBeNull();
    // fetch should NOT have been called
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
  });

  it('returns parsed JSON on successful API call', async () => {
    localStorage.setItem('api-base', 'http://localhost:8501');
    const payload = { specific_yield_kwh_kwp: 1234, optimal_tilt_deg: 36 };
    mockFetch(payload);

    const result = await fetchEstimate(52.5, 13.4, 35, 180);

    expect(result).toEqual(payload);
    expect(vi.mocked(fetch)).toHaveBeenCalledOnce();
    const [url, opts] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe('http://localhost:8501/api/estimate');
    expect(JSON.parse(opts.body)).toMatchObject({ lat: 52.5, lon: 13.4, tilt_deg: 35, azimuth_deg: 180 });
  });

  it('returns null on HTTP error response', async () => {
    localStorage.setItem('api-base', 'http://localhost:8501');
    mockFetch({}, { ok: false });

    const result = await fetchEstimate(52.5, 13.4, 35, 180);

    expect(result).toBeNull();
  });

  it('returns null when fetch throws (network error)', async () => {
    localStorage.setItem('api-base', 'http://localhost:8501');
    mockFetch(new Error('Network error'));

    const result = await fetchEstimate(52.5, 13.4, 35, 180);

    expect(result).toBeNull();
  });

  it('returns null when the request is aborted (timeout)', async () => {
    vi.useFakeTimers();
    localStorage.setItem('api-base', 'http://localhost:8501');

    // Simulate a very slow server: response never comes
    vi.stubGlobal('fetch', vi.fn((_url, opts) =>
      new Promise((_resolve, reject) => {
        opts.signal.addEventListener('abort', () =>
          reject(new DOMException('Aborted', 'AbortError'))
        );
      })
    ));

    const promise = fetchEstimate(52.5, 13.4, 35, 180);
    vi.advanceTimersByTime(15001); // Past the 15s timeout

    const result = await promise;
    expect(result).toBeNull();

    vi.useRealTimers();
  });
});
