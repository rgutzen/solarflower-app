# Task Backlog

Tasks are prioritized within each agent section. Pick from the top.
Format: `- [ ] [agent:0X] [priority:H/M/L] Description`

---

## Agent 02 — Website

- [ ] [agent:02] [priority:H] Deploy website to GitHub Pages
  - Enable GitHub Pages in repo settings (branch: main, folder: /website or root)
  - Verify all links work (mobile-app symlink, iframe embed)
- [ ] [agent:02] [priority:M] Create `resources.html` page (Phase 9)
  - Nav: component pills
  - Resource cards with clay aesthetic (links to pvlib docs, PVGIS, PVWatts, etc.)
- [ ] [agent:02] [priority:L] Add OG image for social sharing (meta og:image tag)
- [ ] [agent:02] [priority:L] Test on real mobile devices (iOS Safari + Android Chrome)

---

## Agent 04 — Mobile-App

- [ ] [agent:04] [priority:H] Deploy Panel Compass PWA (needs HTTPS for sensor APIs)
  - GitHub Pages serves HTTPS — link to `website/mobile-app/` path
  - Test DeviceOrientationEvent.requestPermission() on iOS 16+ Safari
- [ ] [agent:04] [priority:H] Set `API_BASE` in `mobile-app/app.js` once API is deployed
  - Update constant from `null` to deployed API URL (e.g. Railway/Render/Fly.io)
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

- [ ] [agent:03] [priority:M] Vectorize physics in `compute_orientation_grid()` further
  - Current: numpy-vectorized transposition, still loops over tilt/az (cached, ~5 s)
  - Future: full numpy broadcasting over tilt × az × time → single batch call
- [ ] [agent:03] [priority:L] Full horizon shading physics
  - Horizon profile UI already exists; wire up physics to block beam when sun below horizon
- [ ] [agent:03] [priority:L] Deploy Solar Advisor to Streamlit Community Cloud
  - See `solar-app/docs/deployment.md` for instructions

---

## Infrastructure / Cross-Component

- [ ] [all] [priority:H] Deploy REST API (`api/`) to hosting service (Railway / Render / Fly.io)
  - Then set `API_BASE` in `mobile-app/app.js`
  - CORS already configured for `robingutzen.com` and `solarflower.streamlit.app`
- [ ] [all] [priority:M] Write deployment checklist (GitHub Pages + Streamlit Cloud)
  - Verify HTTPS (needed for sensors + PVGIS API)
  - Verify iframe X-Frame-Options headers
  - Verify service worker cache on Panel Compass
