# Task Backlog

Tasks are prioritized within each agent section. Pick from the top.
Format: `- [ ] [agent:0X] [priority:H/M/L] Description`

---

## Agent 02 — Website

- [x] [agent:02] [priority:H] Build initial landing page `website/index.html` — DONE
- [x] [agent:02] [priority:H] Create `website/solar-advisor.html` — dedicated Solar Advisor page with iframe embed, feature grid, physics table — DONE
- [ ] [agent:02] [priority:M] Add favicon and PWA manifest to website
- [ ] [agent:02] [priority:L] Write deployment guide for GitHub Pages / Netlify

---

## Agent 04 — Mobile-App

- [ ] [agent:04] [priority:H] Bootstrap `mobile-app/` PWA scaffold
  - `index.html`, `app.js`, `styles.css`, `manifest.json`, `sw.js`
  - Request geolocation on load → compute optimal tilt/azimuth
- [ ] [agent:04] [priority:H] Implement compass widget using `DeviceOrientationAbsoluteEvent`
  - Visual compass rose, current vs target heading, delta label
  - iOS permission request pattern
- [ ] [agent:04] [priority:H] Implement tilt meter using `DeviceOrientationEvent.beta`
  - Visual level indicator, current vs target, delta label
- [ ] [agent:04] [priority:M] On-target detection (±3°) with green highlight feedback
- [ ] [agent:04] [priority:M] Offline support via service worker (cache core assets)
- [ ] [agent:04] [priority:L] Add yield estimate display (simplified PVWatts in `solar.js`)
- [ ] [agent:04] [priority:L] Test on iOS Safari 16+ and Android Chrome 120+

---

## Agent 01 — Notebook

- [ ] [agent:01] [priority:H] Add ipywidgets interactive controls for solar path
  - Sliders for lat/lon/doy → live sun path plot update
- [ ] [agent:01] [priority:H] Add section: Cell Temperature and its effect on yield
  - Derive NOCT model: T_cell = T_air + (NOCT − 20) × G_T/800
  - Show power loss curve vs temperature
- [ ] [agent:01] [priority:M] Add section: Real-World Losses (brief, conceptual)
  - Soiling, LID, mismatch, wiring, inverter — show loss chain
  - Note: for full loss budget see Solar Advisor web-app
- [ ] [agent:01] [priority:M] Add Southern hemisphere example
  - Cape Town (33.9°S) → show optimal azimuth flips to North (~0°)
- [ ] [agent:01] [priority:L] Add forward reference section at end
  - "For professional-grade calculations see Solar Advisor" with link
  - Brief comparison: clear-sky model vs PVGIS TMY

---

## Agent 03 — Web-App

- [ ] [agent:03] [priority:H] Add REST API endpoint (`/api/estimate`) for mobile integration
  - `POST /api/estimate` → returns quick yield estimate for a location + orientation
  - Can be a lightweight Streamlit custom component or a FastAPI side process
- [ ] [agent:03] [priority:M] Vectorize `compute_orientation_grid()` for speed
  - Currently nested loop (~10 min for 15°/10° steps)
  - Vectorize transposition over tilt/azimuth grid using numpy broadcasting
- [x] [agent:03] [priority:M] Add CSV/JSON export for simulation results — DONE
  - Monthly CSV + full summary JSON download buttons in Tab 1 "Download Results" expander
- [x] [agent:03] [priority:M] Write deployment guide for Streamlit Community Cloud — DONE
  - `solar-app/docs/deployment.md`: step-by-step, X-Frame-Options note, Python version, sleep warning
  - `solar-app/.streamlit/config.toml`: brand theme + iframe CORS config added
  - `.gitignore` updated to track config.toml but not secrets
- [ ] [agent:03] [priority:L] Add shading input
  - Simple: user specifies horizon profile as altitude angles at 8 azimuths
  - Block beam component when sun below horizon profile
- [ ] [agent:03] [priority:L] Add degradation/LID year-by-year projection
  - Show 20-year yield curve assuming linear degradation (default 0.5%/yr)

---

## Infrastructure / Cross-Component

- [ ] [all] [priority:M] Decide deployment strategy (GitHub Pages / Netlify / Streamlit Cloud)
  - Website + Mobile: static → GitHub Pages or Netlify
  - Web-App: Streamlit Community Cloud (free tier)
  - Update `shared/interfaces.md` URL contracts with real URLs once deployed
- [ ] [all] [priority:L] Write root-level `README.md` (currently empty)
  - Project overview, links to all components, license
