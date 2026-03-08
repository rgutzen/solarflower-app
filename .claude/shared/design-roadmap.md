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
| Phase 6 | Iconography: illustrated botanical / organic line icons | Planned |
| Phase 7 | Organic data visualization (flower sun path, root energy flow, tree rings) | Planned |

---

## Phase 6: Iconography Evolution

Replace geometric glyphs with illustrated botanical/solarpunk icons.

**Style options:**
- **Option A — Illustrated:** small drawings within each icon (sun with petal rays, panel cells as seeds)
- **Option B — Organic line:** wobbly lines with round end-caps, variable stroke width

**Key icons to redesign:**

| Icon | Solarpunk version |
|------|------------------|
| Sun | Flower with petal rays, warm glow |
| Panel | Rectangle with cell-seed pattern |
| Compass | Flower compass (N petal) |
| Location | House with growing garden |
| Settings | Gear with vine growing through |
| Chart | Root system branching |
| Download | Seed dropping into soil |
| Upload | Flower blooming upward |
| Menu | Three leaves |

**Implementation:** SVG sprite system at `website/assets/icons.svg`, referenced via `<use href="...#id">`.

```css
.icon {
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
  stroke-width: 1.8;
}
@keyframes wobble {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(2deg); }
  75% { transform: rotate(-2deg); }
}
.icon--living:hover { animation: wobble 2s ease-in-out infinite; }
```

**Files:** `website/assets/icons.svg` (new), `website/styles.css`, `website/index.html`.

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

## Detailed Implementation Notes

Full implementation detail (CSS snippets, HTML templates, Python code):
- `.claude/agents/00_design-plan-phases5-8.md` — phases 5–8 implementation plan
- `.claude/agents/00_design-improvements.md` — original improvement proposals (phases 1–8)

---

## File Change Summary (Phases 6–7)

| File | Changes |
|------|---------|
| `website/assets/icons.svg` | New — SVG icon sprite sheet |
| `website/styles.css` | Icon utility classes, wobble animation |
| `website/index.html` | Replace icons with new system |
| `solar-app/ui/charts.py` | Add `plot_sun_path_flower()`, `plot_energy_roots()`, `plot_monthly_tree_rings()` |
| `solar-app/app.py` | Chart-style toggle (standard / organic) |
| `notebook/solar_panel_power.ipynb` | Add organic visualizations |

---

## Design Conventions (Critical)

- **Azimuth:** 0° = North, 90° = East, 180° = South, 270° = West — all components
- **Tilt:** 0° = horizontal, 90° = vertical — all components
- **No emojis in production UI** — use SVG icons only
