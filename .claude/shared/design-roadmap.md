# Solarflower Design Roadmap

**Related:** `.claude/shared/design-guidelines.md` — full design system reference

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Earth & dusk color palette | Complete (v1.1) |
| Phase 2 | Paper / canvas textures | Complete (v1.1) |
| Phase 3 | Organic border radii | Complete (v1.1) |
| Phase 4 | Biophilic animations (bloom, breathe, grow) | Complete (v1.1) |
| Overhaul | Organic buttons, canvas card textures, floating seeds, vine nav, storytelling layouts | Complete (v1.2) |
| Phase 5 | Typography: Lora serif + Caveat handwritten | Complete (v1.3) |
| Phase 6 | Clay mark icon system, arc panel design, nav pills, vine border, texture overhaul | **Complete (v1.4)** |
| Phase 7 | Organic data visualization (flower sun path, root energy flow, tree rings) | In Progress |
| Phase 8 | Article page design system application | In Progress |
| Phase 9 | Cross-page consistency (solar-advisor.html, resources.html) | Planned |

---

## ✅ Phase 6: Clay Mark Icon System + Arc Panel Design (Complete v1.4)

**Chosen approach:** Single-path closed forms with SVG clay filter (not illustrated, not outline-stroke) — each icon is one continuous filled shape pressed like a clay stamp.

**Delivered:**
- Clay filter (`sf-clay`) with fractalNoise displacement + grain multiply
- 5 icons: `sf-notebook`, `sf-advisor`, `sf-compass`, `sf-sun`, `sf-location`
- Arc panel design: three tilted sectors (soil/moss/gold), two-color per panel, full-panel link
- Navigation redesigned as component pills (icon + label, colored per component)
- SVG vine border on hero philosophy text, extending to wave divider
- Panel textures strengthened 3× (soil 0.38, moss 0.32, gold 0.28)

**Files changed:** `website/index.html`, `website/styles.css`, `website/assets/icons.svg`

See `design-guidelines.md` §9 Phase 6 for full implementation detail.

---

## Phase 7: Organic Data Visualization

Transform charts from standard to nature-inspired representations.

### 7.1 Sun Path as Flower Petal Diagram
- Polar plot — each season = filled petal
- Colors: dawn pink → amber noon → dusk purple
- Replace line chart in Solar Advisor sun-path tab

```python
fig.add_trace(go.Scatterpolar(
    r=altitudes, theta=azimuths, fill='toself',
    fillcolor='rgba(245, 166, 35, 0.2)', line_color='#F5A623'
))
```

### 7.2 Energy Flow as Root / Sap System
- Main trunk = gross potential (amber)
- Loss branches = each loss category (terracotta), thickness ∝ magnitude
- Final leaves at bottom = net yield (green)
- Replaces or supplements loss waterfall chart

### 7.3 Monthly Yield as Tree Rings
- Each ring = one month; ring thickness ∝ yield
- Seasonal color: bare brown (Jan) → peak green (May/Jun) → autumn terracotta (Oct)

### 7.4 Organic Heatmap (Orientation Grid)
- Smooth contours instead of rigid grid squares
- Colorscale: green-pale → amber-light → amber
- Optionally replace square heatmap cells with hexagons

**Files:** `solar-app/ui/charts.py` (new chart functions), `solar-app/app.py` (toggle), `notebook/solar_panel_power.ipynb`.

---

---

## 🚧 Phase 8: Article Page Design System

Apply the v1.4 design system to `article.html` / `article.css`.

**Changes:**
- [x] Nav: replace text links with component pills + icon sprite (same as `index.html`)
- [x] Add inline SVG sprite to article.html
- [x] Add organic wave divider at bottom of article-hero
- [x] Replace emoji icons in "Explore Further" cards with clay mark SVG icons
- [x] Add canvas texture to article-hero background
- [ ] Review callout and equation styling for organic feel

**Files:** `website/article.html`, `website/article.css`

---

## 🚧 Phase 9: Cross-Page Consistency

Apply design system to remaining pages.

**solar-advisor.html:**
- [ ] Nav: component pills (same structure)
- [ ] Add icon sprite
- [ ] Consistent header/hero styling

**resources.html (new page):**
- [ ] Create resources landing page with consistent design
- [ ] Nav: component pills
- [ ] Apply clay aesthetic to resource cards

**Files:** `website/solar-advisor.html`, `website/resources.html`

---

## Detailed Implementation Notes

Full implementation detail (CSS snippets, HTML templates, Python code):
- `.claude/agents/00_design-plan-phases5-8.md` — phases 5–8 implementation plan
- `.claude/agents/00_design-improvements.md` — original improvement proposals (phases 1–8)

---

## File Change Summary (Phases 6–9)

| File | Changes |
|------|---------|
| `website/assets/icons.svg` | Clay mark icons (5 symbols + clay filter) |
| `website/styles.css` | Arc panels, nav pills, vine border, texture overhaul |
| `website/index.html` | Inline sprite, arc panels, component nav |
| `website/article.html` | Component nav, inline sprite, wave divider, SVG icons |
| `website/article.css` | Canvas texture, wave divider, icon sizing |
| `website/solar-advisor.html` | Component nav, inline sprite (Phase 9) |
| `website/resources.html` | New page (Phase 9) |
| `solar-app/ui/charts.py` | `plot_sun_path_flower()`, `plot_energy_roots()`, `plot_monthly_tree_rings()` (Phase 7) |
| `solar-app/app.py` | Chart-style toggle (Phase 7) |

---

## Design Conventions (Critical)

- **Azimuth:** 0° = North, 90° = East, 180° = South, 270° = West — all components
- **Tilt:** 0° = horizontal, 90° = vertical — all components
- **No emojis in production UI** — use SVG icons only
