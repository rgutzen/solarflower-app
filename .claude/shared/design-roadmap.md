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
| Phase 7 | Organic data visualization (flower sun path, Sankey energy flow, polar rose, contour) | **Complete** |
| Phase 8 | Article page design system application | **Complete** |
| Phase 9 | Cross-page consistency (solar-advisor.html) | **Complete** |
| Phase 10 | Solar Advisor app organic light theme | **Complete (2026-03-08)** |

---

## ✅ Phase 6: Clay Mark Icon System + Arc Panel Design (Complete v1.4)

**Delivered:**
- Clay filter (`sf-clay`) with fractalNoise displacement + grain multiply
- 5 icons: `sf-notebook`, `sf-advisor`, `sf-compass`, `sf-sun`, `sf-location`
- Arc panel design: three tilted sectors (soil/moss/gold), full-panel links
- Navigation redesigned as component pills (icon + label, colored per component)
- SVG vine border on hero philosophy text + wave divider

**Files changed:** `website/index.html`, `website/styles.css`, `website/assets/icons.svg`

---

## ✅ Phase 7: Organic Data Visualization (Complete)

Implemented in `solar-app/ui/charts.py`:

### 7.1 Sun Path as Flower Petal Diagram ✅
- `sun_path_flower()` — polar plot, each day-of-year arc = season-colored petal
- Colors: winter blue → spring green → summer amber → autumn terracotta

### 7.2 Energy Flow as Sankey / Root System ✅
- `energy_roots()` — Sankey diagram, amber source → terracotta losses → green net yield
- Replaces horizontal loss waterfall as primary Annual Summary chart

### 7.3 Monthly Yield as Polar Rose ✅
- `monthly_rose()` — polar bar chart, each month = petal, radius = avg kWh/day
- Seasonal colors: clay (winter) → green (spring) → amber (summer) → terracotta (autumn)

### 7.4 Organic Orientation Heatmap ✅
- `orientation_contour()` — smooth Plotly contour chart, amber colorscale
- Replaces rigid heatmap grid squares

**Shared design system in charts.py:**
```python
LAYOUT_BASE = dict(font=..., paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,252,248,0.45)", ...)
def _layout(**overrides) → dict   # deep-copy + merge
def _title(text, size=15) → dict  # Lora serif title
def _polar_style() → dict         # shared polar axis config
```

---

## ✅ Phase 8: Article Page Design System (Complete)

**Delivered:**
- `website/article.html` — full v1.4 design: component nav pills, inline SVG sprite, wave divider, clay mark icons
- `website/article.css` — canvas texture, wave dividers, callout/equation styling
- `website/article.js` — 10+ interactive Plotly charts with:
  - Bold titles (`<b>Title</b>` in Plotly text fields)
  - Increased fonts (size 15 base, labels ≥ 12)
  - Increased margins (margin.b: 80 to prevent x-label clipping)
  - Sun path legend repositioned to avoid overlap

---

## ✅ Phase 9: Cross-Page Consistency (Complete)

**solar-advisor.html:**
- Component nav pills (same structure as index.html)
- Inline SVG icon sprite
- Organic feature cards, terracotta table header, clay mark icons
- Consistent header/hero styling

**resources.html:** Not yet created (backlog)

---

## ✅ Phase 10: Solar Advisor App Organic Light Theme (Complete 2026-03-08)

**Problem solved:** `config.toml` had dark Streamlit theme (`#0e1117` background). All chart
`paper_bgcolor="rgba(0,0,0,0)"` were inheriting the dark page background, making charts appear
as solid dark rectangles.

**Delivered:**
- `solar-app/.streamlit/config.toml` — light theme:
  `backgroundColor #F8FAF5`, `textColor #2D3B2D`, `primaryColor #E8920E`
- `solar-app/ui/styles.css` — complete organic CSS:
  - CSS custom properties (design tokens)
  - Metric cards: gradient + border + shadow + organic border-radius
  - Reduced metric font sizes to prevent value truncation in 7-column layout
  - `white-space: normal; overflow: visible` on metric values
  - Organic asymmetric borders on expanders, chart containers
  - Amber hover glow on metric cards
  - Sidebar section styling

---

## File Change Summary (All Phases)

| File | Changes |
|------|---------|
| `website/assets/icons.svg` | Clay mark icons (5 symbols + clay filter) |
| `website/styles.css` | Arc panels, nav pills, vine border, texture overhaul (v1.4) |
| `website/index.html` | Inline sprite, arc panels, component nav |
| `website/article.html` | Component nav, inline sprite, wave divider, SVG icons |
| `website/article.css` | Canvas texture, wave dividers, callout styling |
| `website/article.js` | 10+ interactive charts, bold titles, readable fonts/margins |
| `website/solar-advisor.html` | Component nav, inline sprite, organic feature cards |
| `solar-app/ui/charts.py` | LAYOUT_BASE pattern, all organic chart functions, no dark templates |
| `solar-app/ui/styles.css` | Design tokens, metric cards, organic shapes |
| `solar-app/.streamlit/config.toml` | Light theme (critical fix) |
| `solar-app/app.py` | width="stretch" on all plotly_chart calls |

---

## Design Conventions (Critical)

- **Azimuth:** 0° = North, 90° = East, 180° = South, 270° = West — all components
- **Tilt:** 0° = horizontal, 90° = vertical — all components
- **No emojis in production UI** — use SVG icons only
- **Streamlit charts:** `paper_bgcolor="rgba(0,0,0,0)"` works because config.toml background is light
- **Brand accent:** `#E8920E` (amber-dark) — updated from earlier `#F5A623`
