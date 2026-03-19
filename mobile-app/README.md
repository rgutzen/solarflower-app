# Panel Compass

Real-time solar panel orientation helper — a Progressive Web App (PWA) that
uses your phone's compass and tilt sensors to guide you toward the optimal
panel alignment for your location.

## Platform & Stack

- **Platform:** Progressive Web App (PWA) — works on iOS Safari 16+ and Android Chrome 120+
- **Framework:** Vanilla JavaScript ES modules (no bundler, no framework)
- **Sensors:** DeviceOrientationEvent / DeviceOrientationAbsoluteEvent
- **Testing:** Vitest 3.x (unit tests only; E2E requires a physical device or HTTPS)

## Setup & Running

```bash
# Serve locally (no build step needed)
cd mobile-app
python -m http.server 8081
# Open http://localhost:8081 in browser DevTools device emulation
# For sensor testing: serve over HTTPS or use a physical device
```

## Test Commands

```bash
cd mobile-app
npm install          # Install Vitest devDependency
npm test             # Run all tests once
npm run test:watch   # Run in watch mode
```

Tests cover four modules:

| Test file | Coverage |
|-----------|---------|
| `tests/solar.test.js` | Optimal orientation, yield estimation, geometry helpers (32 tests) |
| `tests/compass.test.js` | Smoothing math (circular + linear) and sensor watchdog (13 tests) |
| `tests/location.test.js` | Coordinate validation, localStorage persistence (11 tests) |
| `tests/api.test.js` | HTTP client fallback behaviour (5 tests) |

## Architecture

The app is split into five modules with clear single responsibilities:

- **`solar.js`** — Pure calculation library: optimal tilt/azimuth from latitude, yield
  estimation (PVWatts simplified model), orientation factor, and geometry helpers.
  No side effects, no DOM access, fully unit-tested.
- **`compass.js`** — Device sensor abstraction: wraps DeviceOrientationEvent,
  handles iOS permission flow, applies exponential smoothing (circular for angles,
  linear for tilt), and fires a 5-second watchdog if the sensor never responds.
- **`location.js`** — Geolocation, Nominatim reverse geocoding, URL deep-link parsing
  (`?lat=&lon=`), coordinate validation, and localStorage persistence so the last
  location survives page reloads.
- **`api.js`** — Optional HTTP client for `POST /api/estimate` yield refinement via
  the Solarflower PVGIS TMY API. Disabled by default (no API base configured).
  Configurable at runtime via `localStorage.setItem('api-base', 'https://…')`.
- **`ui.js`** — All DOM manipulation: compass SVG, tilt arc, yield gauge, status bar,
  zone arc geometry, tick mark generation. Pure update functions — no logic.
- **`app.js`** — Slim orchestrator (~200 lines): wires the modules together, owns
  application state, runs the `requestAnimationFrame` update loop, manages haptic
  feedback threshold crossings, and exposes `window.__app_debug__`.

## Debug Interface

Open browser DevTools console on any page load:

```javascript
__app_debug__.getState()                         // current app state snapshot
__app_debug__.setLocation(52.5, 13.4)            // bypass GPS → Berlin
__app_debug__.simulateSensor(180, 35)            // inject heading=180°, tilt=35°
__app_debug__.setApiBase('http://localhost:8501') // enable API refinement at runtime
__app_debug__.getApiBase()                       // check current API base
```

## Physics Model

| Parameter | Value |
|-----------|-------|
| Optimal tilt | `0.9 × |latitude| + 3.1°` (±2° vs PVGIS for lat 15°–65°) |
| Optimal azimuth | 180° (N hemisphere) / 0° (S hemisphere) |
| GHI reference | Latitude-band lookup table (15 bands, 0°–70°) |
| Performance ratio | 0.80 (fixed, typical PV+inverter losses) |
| Yield | `GHI × POA_boost × orientation_factor × PR` |

Thresholds: ±3° = on-target (green), ±10° = close (amber), >10° = off (red/grey).

## Deliberate Deviations from Idiomatic Patterns

1. **No bundler (Vite/webpack)** — ES modules load directly in the browser. The app
   has no build step, which means no tree-shaking or minification. This is intentional:
   the target audience installs this on-site, often on slow mobile networks where a
   first-load cache is more important than bundle optimization. After install the service
   worker serves all assets from cache.

2. **No framework (React/Vue/Svelte)** — Vanilla JS keeps the app under 50 KB total.
   The UI updates are imperative (direct DOM manipulation in `ui.js`) rather than
   reactive. This is appropriate for a sensor-driven app where every frame update
   involves the same fixed set of DOM elements.

3. **Vitest without browser environment for most tests** — `solar.js`, `compass.js`
   math, and `api.js` tests run in `jsdom`. Real sensor behaviour (DeviceOrientation
   accuracy, iOS permission UX) cannot be automated and must be tested on physical
   devices.

## Selector Contract

Key DOM IDs referenced by test automation and the debug interface:

| ID / Class | Element | Purpose |
|-----------|---------|---------|
| `#location-text` | span | Detected location name |
| `#manual-lat`, `#manual-lon` | inputs | Manual coordinate entry |
| `#optimal-tilt`, `#optimal-azimuth` | spans | Computed optimal values |
| `#heading-value`, `#tilt-value` | spans | Live sensor readings |
| `#heading-delta`, `#tilt-delta` | spans | Guidance text |
| `#status-section` | div | Alignment state bar |
| `#yield-current`, `#yield-optimal` | spans | Yield estimates |
| `#permission-btn` | button | Request sensor permission |
| `.status--on-target` / `--close` / `--off` | status-section states | Alignment CSS classes |
| `#compass-needle` | SVG element | Compass needle |

## License

AGPL-3.0 — see [LICENSE](../LICENSE).
Commercial licensing available — see [COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md).

## See Also

- [Solar Advisor](../solar-app/) — full-featured PV yield simulator
- [Solar Panel Power](../notebook/) — educational notebook with derivations
