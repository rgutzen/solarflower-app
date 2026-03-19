// SPDX-FileCopyrightText: 2025 Robin Gutzen <robin.gutzen@outlook.com>
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * ui.js — All DOM manipulation for Panel Compass.
 *
 * Pure DOM update functions: accept data values as arguments, return nothing.
 * No business logic, no calculations, no state. Imported and called by app.js.
 *
 * Call initUI() once after DOMContentLoaded before any update functions.
 */

import { azimuthToCardinal, angleDelta } from './solar.js';

// ---------------------------------------------------------------------------
// Geometry constants (SVG layout)
// ---------------------------------------------------------------------------

const TILT_CX = 150, TILT_CY = 140, TILT_R = 120;
const GAUGE_RADIUS = 68;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;

// ---------------------------------------------------------------------------
// DOM cache (populated by initUI)
// ---------------------------------------------------------------------------

const dom = {};

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

/**
 * Cache DOM references and generate static SVG tick marks.
 * Must be called once after DOMContentLoaded.
 */
export function initUI() {
  const $ = (id) => document.getElementById(id);

  Object.assign(dom, {
    locationText:     $('location-text'),
    locationCoords:   $('location-coords'),
    locationManual:   $('location-manual'),
    locationSpinner:  $('location-spinner'),
    optimalSection:   $('optimal-section'),
    optimalTilt:      $('optimal-tilt'),
    optimalAzimuth:   $('optimal-azimuth'),
    permissionSection: $('permission-section'),
    compassSection:   $('compass-section'),
    compassTicks:     $('compass-ticks'),
    compassTarget:    $('compass-target'),
    compassNeedle:    $('compass-needle'),
    compassGuideArrow: $('compass-guide-arrow'),
    compassZoneAmber: $('compass-zone-amber'),
    compassZoneGreen: $('compass-zone-green'),
    headingValue:     $('heading-value'),
    headingCardinal:  $('heading-cardinal'),
    headingDelta:     $('heading-delta'),
    tiltSection:      $('tilt-section'),
    tiltTicks:        $('tilt-ticks'),
    tiltTarget:       $('tilt-target'),
    tiltIndicator:    $('tilt-indicator'),
    tiltGuideArrow:   $('tilt-guide-arrow'),
    tiltZoneAmber:    $('tilt-zone-amber'),
    tiltZoneGreen:    $('tilt-zone-green'),
    tiltValue:        $('tilt-value'),
    tiltDelta:        $('tilt-delta'),
    yieldSection:     $('yield-section'),
    yieldArc:         $('yield-arc'),
    yieldPct:         $('yield-pct'),
    yieldCurrent:     $('yield-current'),
    yieldOptimal:     $('yield-optimal'),
    yieldLoss:        $('yield-loss'),
    statusSection:    $('status-section'),
    statusIcon:       $('status-icon'),
    statusText:       $('status-text'),
    statusYield:      $('status-yield'),
    nosensorSection:  $('nosensor-section'),
    footer:           $('footer'),
    compassAccuracy:  $('compass-accuracy'),
    compassAccuracyText: $('compass-accuracy-text'),
  });

  generateCompassTicks();
  generateTiltTicks();
}

// ---------------------------------------------------------------------------
// Location display
// ---------------------------------------------------------------------------

export function updateLocation(lat, lon, name) {
  if (dom.locationText)  dom.locationText.textContent  = name;
  if (dom.locationCoords) dom.locationCoords.textContent = `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`;
}

export function showSpinner(visible) {
  if (dom.locationSpinner) {
    dom.locationSpinner.classList.toggle('spinner--hidden', !visible);
  }
}

export function showManualEntry(message) {
  if (dom.locationText)   dom.locationText.textContent = message || 'Enter your location';
  if (dom.locationManual) dom.locationManual.hidden = false;
}

// ---------------------------------------------------------------------------
// Form validation helpers (take element references — used by app.js in bindEvents)
// ---------------------------------------------------------------------------

export function setFieldError(inputEl, errorEl, message) {
  if (!inputEl) return;
  inputEl.style.borderColor = 'var(--red)';
  inputEl.setAttribute('aria-invalid', 'true');
  if (errorEl) errorEl.textContent = message;
}

export function clearFieldError(inputEl, errorEl) {
  if (!inputEl) return;
  inputEl.style.borderColor = '';
  inputEl.removeAttribute('aria-invalid');
  if (errorEl) errorEl.textContent = '';
}

// ---------------------------------------------------------------------------
// Optimal orientation display
// ---------------------------------------------------------------------------

/**
 * Show the optimal section and update all related SVG markers and zone arcs.
 *
 * @param {number} tilt    — optimal tilt degrees
 * @param {number} azimuth — optimal azimuth degrees
 * @param {number} yieldKwh — optimal annual yield kWh/kWp
 */
export function updateOptimal(tilt, azimuth, yieldKwh) {
  if (dom.optimalTilt)   dom.optimalTilt.textContent   = `${Math.round(tilt)}°`;
  if (dom.optimalAzimuth) dom.optimalAzimuth.textContent =
    `${Math.round(azimuth)}° (${azimuthToCardinal(azimuth)})`;
  if (dom.yieldOptimal)  dom.yieldOptimal.textContent  =
    `${Math.round(yieldKwh).toLocaleString()} kWh/kWp`;
  if (dom.optimalSection) dom.optimalSection.hidden = false;

  // Compass: position target marker and zone arcs
  if (dom.compassTarget) {
    dom.compassTarget.setAttribute('transform', `rotate(${azimuth} 150 150)`);
  }
  updateCompassZoneArcs(azimuth);

  // Tilt: position target marker and zone arcs
  positionTiltTarget(tilt);
  updateTiltZoneArcs(tilt);
}

// ---------------------------------------------------------------------------
// Section visibility
// ---------------------------------------------------------------------------

export function showPermissionSection(visible) {
  if (dom.permissionSection) dom.permissionSection.hidden = !visible;
}

/** Show or hide the live sensor panels (compass, tilt, yield, status, footer). */
export function showSensorSections(visible) {
  if (dom.compassSection)  dom.compassSection.hidden  = !visible;
  if (dom.tiltSection)     dom.tiltSection.hidden     = !visible;
  if (dom.yieldSection)    dom.yieldSection.hidden    = !visible;
  if (dom.statusSection)   dom.statusSection.hidden   = !visible;
  if (dom.footer)          dom.footer.hidden          = !visible;
  if (dom.nosensorSection) dom.nosensorSection.hidden = true;
}

/** Show the no-sensor fallback (show optimal values only). */
export function showNoSensorFallback(optimalYield) {
  if (dom.permissionSection) dom.permissionSection.hidden = true;
  if (dom.nosensorSection)   dom.nosensorSection.hidden   = false;
  if (dom.yieldSection)      dom.yieldSection.hidden      = false;
  if (dom.statusSection)     dom.statusSection.hidden     = false;

  if (dom.yieldCurrent)  dom.yieldCurrent.textContent  = '— kWh/kWp';
  if (dom.yieldOptimal)  dom.yieldOptimal.textContent  =
    optimalYield ? `${Math.round(optimalYield).toLocaleString()} kWh/kWp` : '—';
  if (dom.yieldLoss)     dom.yieldLoss.textContent     = 'Sensors needed';
  if (dom.yieldPct)      dom.yieldPct.textContent      = '—';
  if (dom.statusText)    dom.statusText.textContent    = 'Use values above to align panel';
  if (dom.statusYield)   dom.statusYield.textContent   =
    optimalYield ? `Optimal: ~${Math.round(optimalYield).toLocaleString()} kWh/kWp/yr` : '';
  if (dom.statusSection) dom.statusSection.className   = 'status';
}

/** Show a sensor error message (e.g., timeout, calibration needed). */
export function showSensorError(type) {
  const messages = {
    'sensor-timeout': 'Sensors not responding — check browser permissions',
  };
  const msg = messages[type] || 'Sensor error — try refreshing';
  showNoSensorFallback(null);
  if (dom.statusText) dom.statusText.textContent = msg;
}

// ---------------------------------------------------------------------------
// Live compass updates
// ---------------------------------------------------------------------------

/**
 * Update compass needle, delta text, guide arrow, and accuracy indicator.
 *
 * @param {number} heading       — current compass heading (0–360°)
 * @param {number} optAzimuth    — optimal azimuth (0–360°)
 * @param {{ onTarget: number, close: number }} thresholds
 * @param {{ accuracy: number|null, lowAccuracy: boolean }} [accuracyInfo]
 */
export function updateCompass(heading, optAzimuth, thresholds, accuracyInfo = {}) {
  const { onTarget, close } = thresholds;

  if (dom.compassNeedle) {
    dom.compassNeedle.setAttribute('transform', `rotate(${heading} 150 150)`);
  }
  if (dom.headingValue)   dom.headingValue.textContent   = Math.round(heading);
  if (dom.headingCardinal) dom.headingCardinal.textContent = azimuthToCardinal(heading);

  const azDelta = angleDelta(heading, optAzimuth);
  const absAzDelta = Math.abs(azDelta);

  if (dom.headingDelta) {
    if (absAzDelta <= onTarget) {
      dom.headingDelta.textContent = 'On target ✓';
      dom.headingDelta.className = 'compass__delta delta--on-target';
    } else {
      const dir = azDelta > 0 ? 'clockwise' : 'counter-clockwise';
      const arrow = azDelta > 0 ? '↻' : '↺';
      dom.headingDelta.textContent = `${arrow} Rotate ${Math.round(absAzDelta)}° ${dir}`;
      dom.headingDelta.className = absAzDelta <= close
        ? 'compass__delta delta--close'
        : 'compass__delta delta--off';
    }
  }

  if (dom.compassGuideArrow) {
    if (absAzDelta <= onTarget) {
      dom.compassGuideArrow.setAttribute('opacity', '0');
    } else {
      dom.compassGuideArrow.setAttribute('transform', `rotate(${optAzimuth} 150 150)`);
      dom.compassGuideArrow.setAttribute('opacity', absAzDelta <= close ? '0.5' : '0.7');
    }
  }

  updateAccuracyIndicator(accuracyInfo.accuracy, accuracyInfo.lowAccuracy);
}

// ---------------------------------------------------------------------------
// Live tilt updates
// ---------------------------------------------------------------------------

/**
 * Update tilt indicator, delta text, and guide arrow.
 *
 * @param {number} tilt       — current panel tilt (0–90°)
 * @param {number} optTilt    — optimal tilt
 * @param {{ onTarget: number, close: number }} thresholds
 */
export function updateTilt(tilt, optTilt, thresholds) {
  const { onTarget, close } = thresholds;
  const tiltAngle = Math.min(90, Math.max(0, tilt));

  positionTiltIndicator(tiltAngle);
  if (dom.tiltValue) dom.tiltValue.textContent = Math.round(tilt);

  const tiltDiff = tilt - optTilt;
  const absTiltDiff = Math.abs(tiltDiff);

  if (dom.tiltDelta) {
    if (absTiltDiff <= onTarget) {
      dom.tiltDelta.textContent = 'Perfect tilt ✓';
      dom.tiltDelta.className = 'tilt__delta delta--on-target';
    } else {
      const dir = tiltDiff > 0 ? 'down' : 'up';
      const arrow = tiltDiff > 0 ? '▽' : '△';
      dom.tiltDelta.textContent = `${arrow} Tilt ${dir} ${Math.round(absTiltDiff)}°`;
      dom.tiltDelta.className = absTiltDiff <= close
        ? 'tilt__delta delta--close'
        : 'tilt__delta delta--off';
    }
  }

  if (dom.tiltGuideArrow) {
    if (absTiltDiff <= onTarget) {
      dom.tiltGuideArrow.setAttribute('opacity', '0');
    } else {
      positionTiltGuideArrow(optTilt, tiltDiff);
      dom.tiltGuideArrow.setAttribute('opacity', absTiltDiff <= close ? '0.5' : '0.7');
    }
  }
}

// ---------------------------------------------------------------------------
// Live yield display
// ---------------------------------------------------------------------------

/**
 * Update the circular yield gauge and text values.
 *
 * @param {number} currentYield — kWh/kWp at current orientation
 * @param {number} optYield     — kWh/kWp at optimal orientation
 * @param {number} pct          — percentage of optimal (0–100+)
 */
export function updateYield(currentYield, optYield, pct) {
  if (dom.yieldPct) dom.yieldPct.textContent = `${pct}%`;

  // Circular gauge arc
  if (dom.yieldArc) {
    const pctClamped = Math.min(100, Math.max(0, pct));
    const offset = GAUGE_CIRCUMFERENCE * (1 - pctClamped / 100);
    dom.yieldArc.setAttribute('stroke-dashoffset', offset.toFixed(1));

    let gaugeColor, panelClass;
    if (pct >= 97) {
      gaugeColor = 'var(--success)';
      panelClass = 'yield yield--on-target';
    } else if (pct >= 85) {
      gaugeColor = 'var(--amber)';
      panelClass = 'yield yield--close';
    } else {
      gaugeColor = 'var(--red)';
      panelClass = 'yield yield--off';
    }
    dom.yieldArc.setAttribute('stroke', gaugeColor);
    if (dom.yieldSection) dom.yieldSection.className = panelClass;
  }

  if (dom.yieldCurrent) {
    dom.yieldCurrent.textContent = `${currentYield.toLocaleString()} kWh/kWp`;
  }
  if (dom.yieldOptimal) {
    dom.yieldOptimal.textContent = `${Math.round(optYield).toLocaleString()} kWh/kWp`;
  }

  const lossKwh = optYield - currentYield;
  if (dom.yieldLoss) {
    if (lossKwh <= 0) {
      dom.yieldLoss.textContent = 'None';
      dom.yieldLoss.style.color = 'var(--green-dark)';
    } else {
      dom.yieldLoss.textContent = `−${lossKwh.toLocaleString()} kWh/kWp`;
      dom.yieldLoss.style.color = '';
    }
  }
}

// ---------------------------------------------------------------------------
// Status bar
// ---------------------------------------------------------------------------

const CHECK_SVG = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
const TARGET_SVG = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>';
const SUN_SVG = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>';

/**
 * Update the status bar based on current alignment.
 *
 * @param {number} heading     — current heading
 * @param {number|null} tilt   — current tilt (null if unavailable)
 * @param {number} optAzimuth  — optimal azimuth
 * @param {number} optTilt     — optimal tilt
 * @param {number} pct         — yield percentage
 * @param {number} currentYield — current yield kWh/kWp
 * @param {{ onTarget: number, close: number }} thresholds
 * @returns {'on-target'|'close'|'off'} alignment state (for haptic use by caller)
 */
export function updateStatus(heading, tilt, optAzimuth, optTilt, pct, currentYield, thresholds) {
  const { onTarget, close } = thresholds;
  const azDelta  = Math.abs(angleDelta(heading, optAzimuth));
  const tiltDelta = tilt !== null ? Math.abs(tilt - optTilt) : 999;

  const azOnTarget   = azDelta   <= onTarget;
  const tiltOnTarget = tiltDelta <= onTarget;
  const azClose      = azDelta   <= close;
  const tiltClose    = tiltDelta <= close;

  if (!dom.statusSection) return 'off';

  if (azOnTarget && tiltOnTarget) {
    dom.statusSection.className = 'status status--on-target';
    if (dom.statusText) dom.statusText.textContent = 'Perfectly aligned!';
    if (dom.statusIcon) dom.statusIcon.innerHTML = CHECK_SVG;
    if (dom.statusYield) dom.statusYield.textContent =
      `Tilt: ${Math.round(tilt)}° · Azimuth: ${Math.round(heading)}° (${azimuthToCardinal(heading)})`;
    return 'on-target';
  } else if (azClose && tiltClose) {
    dom.statusSection.className = 'status status--close';
    if (dom.statusText) dom.statusText.textContent = 'Almost there…';
    if (dom.statusIcon) dom.statusIcon.innerHTML = TARGET_SVG;
    if (dom.statusYield) dom.statusYield.textContent =
      `${pct}% of maximum — adjust a few degrees`;
    return 'close';
  } else {
    dom.statusSection.className = 'status status--off';
    if (dom.statusText) dom.statusText.textContent = 'Aligning…';
    if (dom.statusIcon) dom.statusIcon.innerHTML = SUN_SVG;
    if (dom.statusYield) dom.statusYield.textContent =
      `${pct}% of maximum — follow the guidance above`;
    return 'off';
  }
}

// ---------------------------------------------------------------------------
// Accuracy indicator
// ---------------------------------------------------------------------------

/**
 * Show or hide the compass calibration warning.
 * Uses iOS accuracy (degrees) or generic lowAccuracy flag for Android.
 *
 * @param {number|null} accuracy  — iOS webkitCompassAccuracy (lower = better), or null
 * @param {boolean} lowAccuracy   — generic low-accuracy flag (from heading variance)
 */
function updateAccuracyIndicator(accuracy, lowAccuracy) {
  if (!dom.compassAccuracy || !dom.compassAccuracyText) return;

  if (lowAccuracy) {
    dom.compassAccuracy.hidden = false;
    dom.compassAccuracyText.textContent = accuracy !== null
      ? `Low compass accuracy (±${Math.round(accuracy)}°) — wave phone in a figure-8`
      : 'Compass may be inaccurate — wave phone in a figure-8 to calibrate';
  } else {
    dom.compassAccuracy.hidden = true;
  }
}

// ---------------------------------------------------------------------------
// SVG geometry helpers
// ---------------------------------------------------------------------------

/** Describe a circular arc path for the compass rose (0°=North, clockwise). */
function describeArc(cx, cy, r, startAngle, endAngle) {
  const s = (startAngle - 90) * Math.PI / 180;
  const e = (endAngle   - 90) * Math.PI / 180;
  const x1 = cx + r * Math.cos(s), y1 = cy + r * Math.sin(s);
  const x2 = cx + r * Math.cos(e), y2 = cy + r * Math.sin(e);
  const largeArc = (endAngle - startAngle) > 180 ? 1 : 0;
  return `M ${x1.toFixed(1)} ${y1.toFixed(1)} A ${r} ${r} 0 ${largeArc} 1 ${x2.toFixed(1)} ${y2.toFixed(1)}`;
}

/** Describe a tilt arc path (tilt 0°=left, 90°=right on the semicircle). */
function describeTiltArc(cx, cy, r, tiltLo, tiltHi) {
  const aStart = (180 - tiltHi) * Math.PI / 180;
  const aEnd   = (180 - tiltLo) * Math.PI / 180;
  const x1 = cx + r * Math.cos(aStart), y1 = cy - r * Math.sin(aStart);
  const x2 = cx + r * Math.cos(aEnd),   y2 = cy - r * Math.sin(aEnd);
  const sweep = (tiltHi - tiltLo) > 90 ? 1 : 0;
  return `M ${x1.toFixed(1)} ${y1.toFixed(1)} A ${r} ${r} 0 ${sweep} 0 ${x2.toFixed(1)} ${y2.toFixed(1)}`;
}

// ---------------------------------------------------------------------------
// Zone arcs
// ---------------------------------------------------------------------------

function updateCompassZoneArcs(targetAz) {
  const cx = 150, cy = 150, r = 135;
  const onTarget = 3, close = 10;
  if (dom.compassZoneAmber) {
    dom.compassZoneAmber.setAttribute('d',
      describeArc(cx, cy, r, targetAz - close, targetAz + close));
  }
  if (dom.compassZoneGreen) {
    dom.compassZoneGreen.setAttribute('d',
      describeArc(cx, cy, r, targetAz - onTarget, targetAz + onTarget));
  }
}

function updateTiltZoneArcs(targetTilt) {
  const onTarget = 3, close = 10;
  const amberLo = Math.max(0, targetTilt - close);
  const amberHi = Math.min(90, targetTilt + close);
  const greenLo = Math.max(0, targetTilt - onTarget);
  const greenHi = Math.min(90, targetTilt + onTarget);
  if (dom.tiltZoneAmber) {
    dom.tiltZoneAmber.setAttribute('d',
      describeTiltArc(TILT_CX, TILT_CY, TILT_R, amberLo, amberHi));
  }
  if (dom.tiltZoneGreen) {
    dom.tiltZoneGreen.setAttribute('d',
      describeTiltArc(TILT_CX, TILT_CY, TILT_R, greenLo, greenHi));
  }
}

// ---------------------------------------------------------------------------
// Tilt indicator (needle)
// ---------------------------------------------------------------------------

function positionTiltTarget(tiltDeg) {
  if (!dom.tiltTarget) return;
  const arcAngle = 180 - tiltDeg;
  const rad = arcAngle * Math.PI / 180;
  const x = TILT_CX + TILT_R * Math.cos(rad);
  const y = TILT_CY - TILT_R * Math.sin(rad);
  dom.tiltTarget.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
}

function positionTiltIndicator(tiltDeg) {
  if (!dom.tiltIndicator) return;
  const r = 110;
  const arcAngle = 180 - tiltDeg;
  const rad = arcAngle * Math.PI / 180;
  const x2 = TILT_CX + r * Math.cos(rad);
  const y2 = TILT_CY - r * Math.sin(rad);
  const line = dom.tiltIndicator.querySelector('line');
  if (line) {
    line.setAttribute('x2', x2.toFixed(1));
    line.setAttribute('y2', y2.toFixed(1));
  }
}

function positionTiltGuideArrow(targetTilt, tiltDiff) {
  if (!dom.tiltGuideArrow) return;
  const arcAngle = 180 - targetTilt;
  const rad = arcAngle * Math.PI / 180;
  const arrowR = TILT_R - 18;
  const x = TILT_CX + arrowR * Math.cos(rad);
  const y = TILT_CY - arrowR * Math.sin(rad);
  const arrowRotation = tiltDiff > 0 ? arcAngle + 90 : arcAngle - 90;
  dom.tiltGuideArrow.setAttribute('transform',
    `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${arrowRotation.toFixed(1)})`);
}

// ---------------------------------------------------------------------------
// SVG tick generators (called once during initUI)
// ---------------------------------------------------------------------------

function generateCompassTicks() {
  if (!dom.compassTicks) return;
  let html = '';
  for (let deg = 0; deg < 360; deg += 10) {
    const isMajor = deg % 30 === 0;
    const y1 = isMajor ? 18 : 22;
    const y2 = isMajor ? 38 : 32;
    const sw = isMajor ? 2 : 1;
    const op = isMajor ? 0.5 : 0.25;
    html += `<line x1="150" y1="${y1}" x2="150" y2="${y2}" `
         + `stroke="var(--ink)" stroke-width="${sw}" stroke-linecap="round" `
         + `opacity="${op}" transform="rotate(${deg} 150 150)"/>`;
  }
  dom.compassTicks.innerHTML = html;
}

function generateTiltTicks() {
  if (!dom.tiltTicks) return;
  let html = '';
  for (let deg = 0; deg <= 90; deg += 10) {
    const arcAngle = 180 - deg;
    const rad = arcAngle * Math.PI / 180;
    const isMajor = deg % 30 === 0;
    const outerR = TILT_R + (isMajor ? 10 : 5);
    const innerR = TILT_R - (isMajor ? 3 : 0);
    const x1 = TILT_CX + innerR * Math.cos(rad);
    const y1 = TILT_CY - innerR * Math.sin(rad);
    const x2 = TILT_CX + outerR * Math.cos(rad);
    const y2 = TILT_CY - outerR * Math.sin(rad);
    const sw = isMajor ? 1.5 : 0.8;
    const op = isMajor ? 0.4 : 0.2;
    html += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" `
         + `x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" `
         + `stroke="var(--ink)" stroke-width="${sw}" stroke-linecap="round" `
         + `opacity="${op}"/>`;
    if (isMajor && deg > 0 && deg < 90) {
      const labelR = TILT_R + 18;
      const lx = TILT_CX + labelR * Math.cos(rad);
      const ly = TILT_CY - labelR * Math.sin(rad);
      html += `<text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" `
           + `font-size="10" fill="var(--ink-light)" text-anchor="middle" `
           + `dominant-baseline="central" font-family="var(--font-sans)" opacity="0.5">`
           + `${deg}°</text>`;
    }
  }
  dom.tiltTicks.innerHTML = html;
}
