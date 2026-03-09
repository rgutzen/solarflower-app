# Task Backlog

Tasks are prioritized within each agent section. Pick from the top.
Format: `- [ ] [agent:0X] [priority:H/M/L] Description`

---

## Agent 02 — Website

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

- [ ] [agent:01] [priority:H] Expand interactive dashboard (cell [19])
  - Add DOY slider (1–365) → daily sun path panel for chosen day
  - Add panel_tilt slider (0–90°) and panel_azimuth slider (0–360°) → manual orientation marker on heatmap
  - Reuses existing `compute_annual_grid()`, `solar_altitude_azimuth()`, `compute_monthly_energy()`
- [ ] [agent:01] [priority:M] Cape Town side-by-side heatmap
  - Compute optimal tilt/azimuth for Berlin (52.5°N) and Cape Town (33.9°S)
  - Show two heatmaps side-by-side with annotated optimal points
- [ ] [agent:01] [priority:L] Solar Advisor forward link (final markdown cell)
  - "For professional-grade calculations see Solar Advisor" with URL
  - Brief comparison table: notebook clear-sky model vs Solar Advisor PVGIS TMY

---

## Agent 03 — Web-App

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
