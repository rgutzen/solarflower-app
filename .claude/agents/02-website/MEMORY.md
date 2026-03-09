# Agent 02 — Website: Persistent Memory

_Update this file after every working session._
_Last updated: 2026-03-09_

## Scope
- **Directory:** `/home/rgutzen/01_PROJECTS/solarflower-app/website/`
- **Base prompt:** `.claude/agents/02-website/02_website.md`
- **Do NOT modify:** any file outside `website/`

## Current State

**Complete — design v1.4.** Three pages + science article, all with organic solarpunk design system.

### Files
```
website/
├── index.html        Landing page — arc panels, component nav pills, clay-mark icons, vine border
├── styles.css        Full responsive design system v1.4 (organic, WCAG AA)
├── main.js           Scroll reveal, nav state
├── article.html      "From Sunlight to Watts" science article (interactive charts)
├── article.css       Canvas texture, wave dividers, callout/equation styling
├── article.js        10+ interactive Plotly charts (bold titles, readable fonts)
├── solar-advisor.html Solar Advisor page: feature cards, physics table, iframe embed
└── assets/
    ├── icons.svg     Clay-mark SVG icon system (5 symbols: notebook, advisor, compass, sun, location)
    ├── logo.svg      Sunflower/solar-panel hybrid icon
    └── hero-illustration.svg  Animated sun + panel scene
```

Note: `mobile-app/` is a **symlink** → `../mobile-app` (Panel Compass PWA lives there)

## Decisions Made

- [x] **Tech stack:** Plain HTML/CSS/JS — zero build step, zero dependencies
- [x] **Typography:** Lora serif for headings/titles, system sans-serif for body
- [x] **Color palette (v1.4):** Amber `#E8920E` primary, Earth `#4A7A58` secondary, Ink `#2D3B2D` text
- [x] **Icons:** Clay-mark SVG system (not emoji, not outline) — continuous filled shapes
- [x] **Layout:** CSS Grid cards, responsive breakpoints at 960px / 480px
- [x] **Animations:** IntersectionObserver reveal-on-scroll, CSS hover transitions, SVG sun pulse
- [x] **Panel Compass nav link:** Active (was disabled 2026-03-07; enabled 2026-03-08)
- [ ] Deployment target: TBD (GitHub Pages, Netlify)
- [ ] Domain name: TBD

## Design System v1.4 (solarpunk / soilpunk)

Key CSS variables:
```css
--amber: #E8920E;  --earth: #4A7A58;  --terracotta: #C75B39;
--ink: #2D3B2D;    --ink-light: #4A6050;  --warm-white: #FFFBF3;
```

Key elements:
- **Arc panels:** Three tilted sectors (soil/moss/gold) on landing hero
- **Nav pills:** Component-colored icon+label pills (one per component)
- **Clay filter:** SVG `<filter id="sf-clay">` — fractalNoise displacement + grain multiply
- **Vine border:** SVG vine/leaf motif around hero philosophy text
- **Organic borders:** Asymmetric `border-radius` throughout (e.g. `12px 18px 14px 10px / 10px 14px 18px 12px`)

## Article Charts (article.js)

All charts share `LAYOUT_BASE` with:
- `font.size: 15`, `margin.b: 80` (prevents x-label clipping), `margin.t: 55`
- All titles wrapped in `<b>...</b>` for bold rendering
- Annotation/label fonts: 12px minimum
- Lora serif titles, INK_LIGHT `#4A6050` body text

Charts implemented:
1. Inverse-Square Law (irradiance vs distance)
2. Atmospheric attenuation (altitude → DNI)
3. Tilt sweep (yield vs tilt angle)
4. Sun path annual (polar, 4 seasons)
5. Monthly energy profile (bar chart)
6. Interactive sun path explorer (slider for day-of-year)
7. Interactive tilt optimizer (slider for tilt angle)
8. (and more energy/yield charts)

## Accessibility (all PASS WCAG AA)
- Ink on warm-white: > 15:1
- Dark text on amber btn: > 8:1
- Focus-visible outlines: 2px amber
- Keyboard navigable: all links + buttons

## Live URLs (deployed)
- Website: `https://robingutzen.com/solarflower/`
- Web-App: `https://solarflower.streamlit.app`
- Mobile: `https://robingutzen.com/solarflower/mobile-app/`
- Notebook: `https://github.com/rgutzen/solarflower-app/blob/main/notebook/solar_panel_power.ipynb`
- GitHub: `https://github.com/rgutzen/solarflower-app`

## TODO / Next Iteration
- [ ] Deploy to GitHub Pages or Netlify
- [ ] Update Web-App iframe URL once deployed to Streamlit Cloud
- [ ] Add favicon PNG fallback
- [ ] Create `resources.html` page (Phase 9)
- [ ] Add OG image for social sharing
- [ ] Test on real mobile devices
