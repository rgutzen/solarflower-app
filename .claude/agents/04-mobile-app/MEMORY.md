# Agent 04 — Mobile-App (Panel Compass): Persistent Memory

_Update this file after every working session._
_Last updated: 2026-03-10_

## Scope
- **Directory:** `/home/rgutzen/01_PROJECTS/solarflower-app/mobile-app/`
- **Base prompt:** `.claude/agents/04-mobile-app/04_mobile-app.md`
- **Do NOT modify:** any file outside `mobile-app/`

## Current State

**Complete.** Full PWA built and functional.

### Files
```
mobile-app/
├── index.html       Single-page app shell, Solarflower organic design
├── app.js           Main orchestrator: GPS → sensors → yield → UI (60fps loop)
├── solar.js         Pure JS solar calculations (optimal tilt, PVWatts yield model)
├── compass.js       Device sensor abstraction (heading + tilt + smoothing)
├── styles.css       Mobile-first design system (organic, matches website v1.4)
├── manifest.json    PWA manifest (installable, icons, theme)
├── sw.js            Service worker: cache-first offline support
├── README.md        How it works, quick start
└── icons/           App icons (SVG + PNG fallbacks)
```

## Decisions Made

- **Tech stack:** PWA — vanilla JS + HTML5 + CSS (no framework, no bundler)
  - Rationale: no app store, works iOS + Android, DeviceOrientation API, offline via SW
- **Sensor for compass:** `deviceorientationabsolute` (absolute heading, 0=North)
  - iOS fallback: `deviceorientation` (iOS reports absolute heading natively)
  - Android: must use `deviceorientationabsolute` for true North heading
- **Sensor for tilt:** `DeviceOrientationEvent.beta` (front-to-back tilt)
  - Phone flat on panel → beta≈0, panel tilt = 90° − |beta|

## Key Technical Notes

### iOS Permission Pattern
```javascript
if (typeof DeviceOrientationEvent.requestPermission === 'function') {
    DeviceOrientationEvent.requestPermission()
        .then(perm => { if (perm === 'granted') startSensors(); });
} else {
    startSensors();  // Android, older iOS
}
```

### Heading Derivation
- `deviceorientationabsolute.alpha` = compass heading, 0=North, clockwise
- Matches azimuth convention directly (see `shared/conventions.md`)
- No magnetic declination correction needed (OS handles it)

### Tilt Derivation
- Phone lying flat on panel surface: `beta` ≈ 0°
- Panel at 30° tilt: `beta` ≈ 90° − 30° = 60°
- Landscape vs portrait handled via `gamma` roll check

## Optimal Tilt Formula (from `shared/interfaces.md`)
```javascript
const optimalTilt = 0.9 * Math.abs(lat) + 3.1;  // degrees
const optimalAz = lat >= 0 ? 180 : 0;             // South for N, North for S
```

## On-Target Thresholds
- Within ±3°: on target (green)
- Within ±10°: close (amber)
- Beyond ±10°: off target (red / directional guidance arrows shown)

## Exponential Smoothing
- Compass heading + tilt smoothed with α=0.12 (slow, stable for mounting)
- Prevents jitter on physical hardware

## Website Integration
- Website `website/mobile-app/` is a symlink to `../mobile-app`
- All `href="mobile-app/"` links in the website are correct
- Nav link in website was previously disabled (CSS `pointer-events: none`) — fixed 2026-03-08

## REST API Integration (2026-03-10)

`app.js` now integrates with the Solarflower REST API (`api/main.py`).

**How it works:**
1. `setLocation()` fires `fetchApiEstimate(lat, lon, tilt, azimuth)` async in background
2. Local JS model gives immediate result (no spinner, no blocking)
3. When API responds, `applyApiResult()` updates:
   - `state.optimalTilt` / `state.optimalAzimuth` (refined from API coarse sweep)
   - `state.yieldScaleFactor` = `apiYield / localOptimal` (calibrates live sensor frames)
   - `state.optimalYield`, yield display refreshed
4. Live sensor frames: `currentYield = estimateYieldKwhPerKwp(...) * yieldScaleFactor`
5. Stale responses (user changed location) silently ignored via location guard

**To activate:**
```javascript
// app.js line ~40
const API_BASE = 'https://your-api.railway.app';  // currently null (disabled)
```
Request: `{ lat, lon, tilt_deg, azimuth_deg, peak_power_kwp: 1.0, system_loss_pct: 14.0 }`
Response fields used: `specific_yield_kwh_kwp`, `optimal_tilt_deg`, `optimal_azimuth_deg`

## Pending
- Deploy to HTTPS host (GitHub Pages or custom) — DeviceOrientation + GPS require HTTPS
- Set `API_BASE` in `app.js` once API service is deployed
