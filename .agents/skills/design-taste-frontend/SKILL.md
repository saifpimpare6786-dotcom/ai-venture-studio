---
name: design-taste-frontend
description: Frontend design taste curation, tunable aesthetic dials (VISUAL_DENSITY, MOTION_INTENSITY, DESIGN_VARIANCE), and archetype styling for AI web applications.
---

# Design Taste Frontend Skill (Taste-Skill)

This skill provides a structured framework for steering the aesthetic personality, visual density, and craft quality of AI-generated user interfaces.

---

## 🎛️ The Three Global Taste Dials (1–10 Scale)

```yaml
taste_configuration:
  VISUAL_DENSITY: 8      # 1 = Ultra-spacious/editorial -> 10 = High-density Bloomberg terminal
  MOTION_INTENSITY: 5    # 1 = Static/instant -> 10 = Expressive spring choreography
  DESIGN_VARIANCE: 4     # 1 = Rigid standard grid -> 10 = Experimental bespoke layout
```

### Dial Guidelines:
1. **`VISUAL_DENSITY` (1–10)**:
   * **1–3 (Editorial / Consumer Showcase)**: Generous whitespace ($32\text{--}64\text{px}$ padding), oversized typography, low data per viewport.
   * **4–6 (SaaS Landing / Presentation)**: Balanced padding ($20\text{--}32\text{px}$), card-based grids, presentation slide decks.
   * **7–10 (Executive Cockpit / Financial Dashboard)**: Compact padding ($12\text{--}16\text{px}$), mono-spaced numbers, multi-column analytics, zero wasted space.

2. **`MOTION_INTENSITY` (1–10)**:
   * **1–3 (Snappy / Enterprise)**: Instant state switches, micro-durations ($100\text{--}150\text{ms}$), subtle fade.
   * **4–6 (Polished Product)**: Spring deceleration, micro-interactions on click/hover, staggered list ingress ($200\text{--}300\text{ms}$).
   * **7–10 (Showcase / Expressive)**: Fluid morphing, multi-layer parallax, dynamic elastic springs.

3. **`DESIGN_VARIANCE` (1–10)**:
   * **1–3 (Conservative / Safe)**: Familiar 12-column layouts, standard navbar and card grids.
   * **4–7 (Intentional Craft)**: Asymmetrical accents, distinctive border treatments, customized badges and 2×2 matrices.
   * **8–10 (Avant-Garde / Bespoke)**: Experimental navigation, non-standard layout flows.

---

## 🏛️ Style Archetypes

### 1. Dark Executive Cockpit (Default for AI Venture Studio)
* **Visual Density**: `8/10`
* **Motion Intensity**: `5/10`
* **Design Variance**: `4/10`
* **Characteristics**: Midnight canvas (`#0A0D14`), subtle glassmorphism (`backdrop-filter: blur(12px)`), crisp mono metrics, high-contrast semantic borders (Indigo, Emerald, Amber, Cyan), zero decorative fluff.

### 2. Pitch Presentation Deck
* **Visual Density**: `5/10`
* **Motion Intensity**: `6/10`
* **Design Variance**: `5/10`
* **Characteristics**: 16:9 proportioned slide containers, bold slide headers, high-contrast bullet highlights, narrative-first structure.
