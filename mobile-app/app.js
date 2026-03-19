// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * app.js — Slim orchestrator for Panel Compass PWA.
 *
 * Coordinates four modules:
 *   location.js  — GPS, reverse geocoding, localStorage persistence
 *   solar.js     — optimal orientation + yield calculations
 *   compass.js   — device sensor abstraction (heading + tilt)
 *   ui.js        — all DOM manipulation
 *   api.js       — optional PVGIS TMY yield refinement via REST
 *
 * This file owns: application state, event binding, RAF update loop,
 * haptic feedback, and the window.__app_debug__ interface.
 */

import {
  computeOptimalOrientation,
  estimateYieldKwhPerKwp,
  angleDelta,
  azimuthToCardinal,
} from './solar.js';

import * as compass from './compass.js';
import { fetchEstimate } from './api.js';

import {
  validateCoords,
  saveLocation,
  loadSavedLocation,
  readURLParams,
  reverseGeocode,
  formatCoords,
  requestGeolocation,
} from './location.js';

import * as ui from './ui.js';

// ===========================================================================
// State
// ===========================================================================

const state = {
  lat: null,
  lon: null,
  locationName: null,
  optimalTilt: null,
  optimalAzimuth: null,
  optimalYield: null,
  yieldScaleFactor: 1.0,   // ratio of API yield to local model (applied to sensor frames)
  currentHeading: null,
  currentTilt: null,
  currentAccuracy: null,
  currentLowAccuracy: false,
  currentYield: null,
  currentPct: null,
  sensorsActive: false,
};

const THRESHOLDS = { onTarget: 3, close: 10 };

// Haptic state — only fire on threshold crossings, not every frame
const haptic = {
  wasAzOnTarget: false,
  wasTiltOnTarget: false,
  wasAzClose: false,
  wasTiltClose: false,
};

// ===========================================================================
// Initialization
// ===========================================================================

document.addEventListener('DOMContentLoaded', init);

function init() {
  ui.initUI();
  bindEvents();
  tryLockPortrait();

  // Priority: saved location → URL params → GPS
  const saved = loadSavedLocation();
  if (saved) {
    setLocation(saved.lat, saved.lon, saved.name || formatCoords(saved.lat, saved.lon));
    return;
  }

  const urlParams = readURLParams();
  if (urlParams) {
    ui.showSpinner(true);
    reverseGeocode(urlParams.lat, urlParams.lon).then(name => {
      ui.showSpinner(false);
      setLocation(urlParams.lat, urlParams.lon, name);
    });
    return;
  }

  ui.showSpinner(true);
  requestGeolocation(
    (lat, lon) => {
      reverseGeocode(lat, lon).then(name => {
        ui.showSpinner(false);
        setLocation(lat, lon, name);
      });
    },
    () => {
      ui.showSpinner(false);
      ui.showManualEntry('Location unavailable — enter manually');
    }
  );
}

function tryLockPortrait() {
  try { screen.orientation?.lock?.('portrait').catch(() => {}); } catch (_) {}
}

// ===========================================================================
// Event Binding
// ===========================================================================

function bindEvents() {
  const $ = (id) => document.getElementById(id);

  // Toggle manual location entry panel
  const locationBtn = $('location-btn');
  const locationManual = $('location-manual');
  if (locationBtn && locationManual) {
    locationBtn.addEventListener('click', () => {
      const isHidden = locationManual.hidden;
      locationManual.hidden = !isHidden;
      if (isHidden) {
        if (state.lat !== null) {
          const latInput = $('manual-lat');
          const lonInput = $('manual-lon');
          if (latInput) latInput.value = state.lat.toFixed(1);
          if (lonInput) lonInput.value = state.lon.toFixed(1);
        }
        $('manual-lat')?.focus();
      }
    });
  }

  // Manual location submit with validation
  const manualSubmit = $('manual-submit');
  if (manualSubmit) {
    manualSubmit.addEventListener('click', () => {
      const latInput = $('manual-lat');
      const lonInput = $('manual-lon');
      const latError = $('lat-error');
      const lonError = $('lon-error');
      const lat = parseFloat(latInput?.value);
      const lon = parseFloat(lonInput?.value);
      const result = validateCoords(lat, lon);

      // Always clear both first, then set errors
      ui.clearFieldError(latInput, latError);
      ui.clearFieldError(lonInput, lonError);

      if (!result.valid && result.field === 'lat') {
        ui.setFieldError(latInput, latError, 'Enter latitude (−90 to 90)');
        return;
      }
      if (isNaN(lon) || lon < -180 || lon > 180) {
        ui.setFieldError(lonInput, lonError, 'Enter longitude (−180 to 180)');
        return;
      }

      if (locationManual) locationManual.hidden = true;
      setLocation(lat, lon, formatCoords(lat, lon));
    });
  }

  // Clear validation errors on input
  ['manual-lat', 'manual-lon'].forEach(id => {
    const input = $(id);
    const errorId = id === 'manual-lat' ? 'lat-error' : 'lon-error';
    if (input) input.addEventListener('input', () => ui.clearFieldError(input, $(errorId)));
  });

  // Sensor permission button
  const permissionBtn = $('permission-btn');
  if (permissionBtn) {
    permissionBtn.addEventListener('click', async () => {
      const result = await compass.requestPermission();
      if (result === 'granted' || result === 'not-needed') {
        startSensors();
      } else {
        permissionBtn.textContent = 'Permission Denied — check browser settings';
        permissionBtn.disabled = true;
        permissionBtn.style.opacity = '0.5';
        ui.showNoSensorFallback(state.optimalYield);
      }
    });
  }

  // High-contrast mode is CSS-only via #contrast-toggle checkbox + :has()
  // No JS needed — toggling the checkbox triggers body:has(#contrast-toggle:checked) rules.
}

// ===========================================================================
// Location → Compute Optimal
// ===========================================================================

function setLocation(lat, lon, displayName) {
  state.lat = lat;
  state.lon = lon;
  state.locationName = displayName;

  // Persist for next session
  saveLocation(lat, lon, displayName);

  // Compute optimal orientation from latitude
  const { tilt, azimuth } = computeOptimalOrientation(lat);
  state.optimalTilt = tilt;
  state.optimalAzimuth = azimuth;
  state.optimalYield = estimateYieldKwhPerKwp(lat, tilt, azimuth);
  state.yieldScaleFactor = 1.0;

  // Update location + optimal displays
  ui.updateLocation(lat, lon, displayName);
  ui.updateOptimal(state.optimalTilt, state.optimalAzimuth, state.optimalYield);

  // Kick off background API refinement (improves accuracy when it returns)
  const localOptimal = state.optimalYield;
  const lockedLat = lat, lockedLon = lon;
  fetchEstimate(lat, lon, tilt, azimuth).then(result => {
    // Guard: ignore if user changed location since this request was made
    if (result && state.lat === lockedLat && state.lon === lockedLon) {
      applyApiResult(result, localOptimal);
    }
  });

  // Start sensors or show fallback
  if (compass.isSupported()) {
    if (compass.needsPermission()) {
      ui.showPermissionSection(true);
    } else {
      startSensors();
    }
  } else {
    ui.showNoSensorFallback(state.optimalYield);
  }
}

/**
 * Apply a successful API response: refine optimal orientation and yield scale.
 */
function applyApiResult(result, localOptimal) {
  const apiYield = result.specific_yield_kwh_kwp;
  if (!apiYield || apiYield <= 0) return;

  if (result.optimal_tilt_deg !== undefined)    state.optimalTilt    = result.optimal_tilt_deg;
  if (result.optimal_azimuth_deg !== undefined) state.optimalAzimuth = result.optimal_azimuth_deg;

  state.yieldScaleFactor = localOptimal > 0 ? apiYield / localOptimal : 1.0;
  state.optimalYield = apiYield;

  // Re-render optimal display with refined values
  ui.updateOptimal(state.optimalTilt, state.optimalAzimuth, state.optimalYield);
}

// ===========================================================================
// Sensors
// ===========================================================================

function startSensors() {
  ui.showPermissionSection(false);
  ui.showSensorSections(true);
  document.body.classList.add('sensors-active');
  compass.start(onSensorUpdate, onSensorError);
  state.sensorsActive = true;
}

function onSensorError(type) {
  ui.showSensorError(type);
}

// ===========================================================================
// Sensor Update Loop (requestAnimationFrame throttled)
// ===========================================================================

let _rafId = null;

function onSensorUpdate({ heading, tilt, accuracy, lowAccuracy }) {
  state.currentHeading     = heading;
  state.currentTilt        = tilt;
  state.currentAccuracy    = accuracy;
  state.currentLowAccuracy = lowAccuracy;

  // Throttle DOM updates to animation frames — skip if one is already queued
  if (_rafId) return;
  _rafId = requestAnimationFrame(() => {
    _rafId = null;
    renderFrame();
  });
}

function renderFrame() {
  const { currentHeading, currentTilt, optimalTilt, optimalAzimuth, lat, optimalYield } = state;
  if (currentHeading === null || lat === null) return;

  // Compute live yield from sensor readings (apply PVGIS scale factor if API responded)
  const useTilt = currentTilt !== null ? currentTilt : optimalTilt;
  state.currentYield = Math.round(
    estimateYieldKwhPerKwp(lat, useTilt, currentHeading) * state.yieldScaleFactor
  );
  state.currentPct = optimalYield > 0
    ? Math.round((state.currentYield / optimalYield) * 100)
    : 0;

  // Update all visual sections
  ui.updateCompass(currentHeading, optimalAzimuth, THRESHOLDS, {
    accuracy: state.currentAccuracy,
    lowAccuracy: state.currentLowAccuracy,
  });

  if (currentTilt !== null) {
    ui.updateTilt(currentTilt, optimalTilt, THRESHOLDS);
  }

  ui.updateYield(state.currentYield, state.optimalYield, state.currentPct);

  const alignmentState = ui.updateStatus(
    currentHeading, currentTilt, optimalAzimuth, optimalTilt,
    state.currentPct, state.currentYield, THRESHOLDS
  );

  // Haptic feedback on threshold crossings (fires once per transition)
  updateHaptics(currentHeading, currentTilt, optimalAzimuth, optimalTilt);
}

// ===========================================================================
// Haptic Feedback — fires only on threshold crossings
// ===========================================================================

function updateHaptics(heading, tilt, optAz, optTilt) {
  const azDelta  = Math.abs(angleDelta(heading, optAz));
  const tiltDelta = tilt !== null ? Math.abs(tilt - optTilt) : 999;

  const azOnTarget   = azDelta   <= THRESHOLDS.onTarget;
  const tiltOnTarget = tiltDelta <= THRESHOLDS.onTarget;
  const azClose      = azDelta   <= THRESHOLDS.close;
  const tiltClose    = tiltDelta <= THRESHOLDS.close;

  const v = (ms) => { try { navigator.vibrate?.(ms); } catch (_) {} };

  if (azOnTarget && tiltOnTarget && !(haptic.wasAzOnTarget && haptic.wasTiltOnTarget)) {
    v([15, 50, 15]); // Celebration pattern for full alignment
  } else if (azOnTarget   && !haptic.wasAzOnTarget)   v(15);
  else if (tiltOnTarget   && !haptic.wasTiltOnTarget)  v(15);
  else if (azClose   && !haptic.wasAzClose   && !azOnTarget)   v(10);
  else if (tiltClose && !haptic.wasTiltClose && !tiltOnTarget) v(10);

  haptic.wasAzOnTarget   = azOnTarget;
  haptic.wasTiltOnTarget = tiltOnTarget;
  haptic.wasAzClose      = azClose;
  haptic.wasTiltClose    = tiltClose;
}

// ===========================================================================
// Debug Interface
// ===========================================================================

/**
 * window.__app_debug__ — Test hooks for E2E automation and manual testing.
 *
 * In browser console:
 *   __app_debug__.getState()              → current app state snapshot
 *   __app_debug__.setLocation(52.5, 13.4) → bypass GPS, set Berlin
 *   __app_debug__.simulateSensor(180, 35) → inject heading=180°, tilt=35°
 *   __app_debug__.setApiBase('http://..') → enable API refinement at runtime
 */
window.__app_debug__ = {
  getState: () => ({ ...state }),
  setLocation: (lat, lon) => setLocation(lat, lon, formatCoords(lat, lon)),
  simulateSensor: (heading, tilt) => onSensorUpdate({
    heading, tilt, accuracy: null, lowAccuracy: false,
  }),
  getApiBase: () => { try { return localStorage.getItem('api-base'); } catch (_) { return null; } },
  setApiBase: (url) => { try { localStorage.setItem('api-base', url); } catch (_) {} },
};
