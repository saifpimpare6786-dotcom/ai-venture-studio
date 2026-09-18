# AI Venture Studio — Design System & Craft Standards (`DESIGN.md`)

This document defines the visual design system, token hierarchy, and accessibility rules for the **AI Venture Studio** platform.

---

## 🎨 1. Color System & Contrast Standards

AI Venture Studio employs a **High-Contrast Institutional Dark Theme** designed for executive dashboards, dense analytical tables, and interactive financial models.

### A. Core Surfaces & Backgrounds
* **Canvas Background**: `#0A0D14` (Deep Obsidian / Midnight Blue)
* **Glass Card Surface (Level 1)**: `rgba(17, 24, 39, 0.7)` with `backdrop-filter: blur(12px)` and `border: 1px solid rgba(255, 255, 255, 0.08)`
* **Elevated Surface (Level 2 - Modals/Flyouts)**: `rgba(31, 41, 55, 0.75)` with `backdrop-filter: blur(16px)` and `border: 1px solid rgba(255, 255, 255, 0.12)`
* **Input Background**: `rgba(15, 23, 42, 0.6)` with `border: 1px solid rgba(255, 255, 255, 0.1)`

### B. Typography & Text Contrast Hierarchy (WCAG AAA Compliant)
* **Primary / Hero Numbers**: `#FFFFFF` (100% pure white) — Contrast Ratio: **19.5:1**
* **Headings & Body Titles**: `#F8FAFC` (`text-slate-100`) — Contrast Ratio: **18.2:1**
* **Standard Body & Table Data**: `#E2E8F0` (`text-slate-200`) — Contrast Ratio: **14.1:1**
* **Secondary Descriptions**: `#CBD5E1` (`text-slate-300`) — Contrast Ratio: **10.8:1**
* **Muted Metadata & Labels**: `#94A3B8` (`text-slate-400`) — Contrast Ratio: **5.7:1** (Meets WCAG AA)
* *Anti-Pattern Prohibition*: Never use `text-slate-600` or darker on dark glass surfaces for readable content.

### C. Semantic Domain Accents
* **Primary / Technology Anchor**: Electric Indigo (`#6366F1` / `rgba(99, 102, 241, ...)`)
* **Financial Health & Positive Traction**: Venture Emerald (`#10B981` / `rgba(16, 185, 129, ...)`)
* **Risk Warnings & Strategic Alerts**: Sovereign Amber (`#F59E0B` / `rgba(245, 158, 11, ...)`)
* **Competitive Whitespace & Moats**: Cyan Wave (`#06B6D4` / `rgba(6, 182, 212, ...)`)
* **Adversarial Critique & Capital Drawdown**: Crimson Rose (`#F43F5E` / `rgba(244, 63, 94, ...)`)

---

## 📐 2. Modular Typographic Scale

| Level | Size | Weight | Line Height | Tailwind Class | Semantic Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero Metric** | 48px / 3rem | 900 (Black) | 1.1 | `text-5xl font-black` | Overall Readiness Score (e.g. 82/100) |
| **H1 Title** | 24px / 1.5rem | 800 (Extrabold)| 1.25 | `text-2xl font-bold` | Venture Header, Project Name |
| **H2 Section** | 18px / 1.125rem| 700 (Bold) | 1.35 | `text-lg font-bold` | Report Titles, Simulator Header |
| **H3 Card** | 14px / 0.875rem| 700 (Bold) | 1.4 | `text-sm font-bold` | Module Subheadings, Card Titles |
| **Body Standard**| 13px / 0.8125rem| 400 (Normal) | 1.6 | `text-xs leading-relaxed`| Descriptions, Analysis Paragraphs |
| **Caption / Label**| 11px / 0.6875rem| 600 (Semibold)| 1.4 | `text-[11px] font-semibold uppercase` | Category Badges, Table Headers |
| **Mono Metric** | 12px / 0.75rem | 700 (Bold) | 1.2 | `text-xs font-mono font-bold` | Currency amounts, CAC, MRR, Steps |

### Line-Length Readability Guardrail:
* Paragraph blocks must be capped at `max-w-prose` (65ch) or `max-w-3xl` to avoid wide-screen reading fatigue.

---

## 🔲 3. Spatial System, Borders & Radiuses

* **Grid Base**: 4px / 8px incremental scale (`gap-3`, `gap-4`, `gap-6`, `p-4`, `p-6`, `p-8`).
* **Border Radiuses**:
  * Root Card Container: `rounded-2xl` (16px)
  * Inner Section / Sub-card: `rounded-xl` (12px)
  * Button / Input: `rounded-xl` (12px)
  * Badge / Tag: `rounded-full` (9999px)
* **Elevation Hierarchy**:
  * Default: `border-white/10` with subtle ambient glass reflection.
  * Hover: `border-primary-500/40` with `translateY(-2px)` spring lift.
  * Active / Focus: `box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25)`.

---

## ⚡ 4. Motion & Transition Rules (`emil-design-eng` Alignment)

* **Spring Deceleration Curve**: `--ease-spring: cubic-bezier(0.16, 1, 0.3, 1)`.
* **Button Snap Feedback**: `--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1)` with `active:scale-96`.
* **Stagger Timing**: 20ms staggered entrance per item for streaming lists (Deliberation Log, 13 Report Tabs).

---

## 🎛️ 5. Aesthetic Personality Dials & Taste Calibration Matrix (`taste-skill`)

To prevent generic AI output and ensure each module serves its user intent, AI Venture Studio enforces calibrated visual dials:

| Module / Screen | `VISUAL_DENSITY` (1–10) | `MOTION_INTENSITY` (1–10) | `DESIGN_VARIANCE` (1–10) | Archetype / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Financial Simulator** (`VentureSimulator.jsx`) | **8 / 10** | **4 / 10** | **3 / 10** | **High-Density Bloomberg/Linear Cockpit**: Compact sliders, immediate calculation feedback, multi-KPI metrics. |
| **Executive Dashboard & Tabs** (`Dashboard.jsx`) | **7 / 10** | **5 / 10** | **4 / 10** | **Institutional Executive Overview**: Glassmorphism cards, radial readiness score gauges, 13-tab bar. |
| **Boardroom Deliberation Log** (`DeliberationStream.jsx`) | **7 / 10** | **5 / 10** | **4 / 10** | **Live Autonomous Stream**: Fluid SSE log stream with active speaker glowing pulses and staggered card ingress. |
| **Intake Wizard** (`BusinessIdeaWizard.jsx`) | **6 / 10** | **5 / 10** | **4 / 10** | **Focused Intake Funnel**: Clean step progression, responsive file drag-and-drop, clear input grouping. |
| **Pitch Presentation Slide Deck** (`SlideCard`) | **5 / 10** | **6 / 10** | **5 / 10** | **Spacious Narrative Deck**: 16:9 proportion, bold slide titles, high-contrast bullet takeaways, presentation-ready. |

