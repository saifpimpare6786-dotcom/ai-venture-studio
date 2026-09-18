---
name: impeccable
description: Institutional design auditing, anti-pattern detection (59+ visual rules), typography scaling, and design system governance for AI web applications.
---

# Impeccable Design Quality & Anti-Pattern Detection Skill

This skill provides a comprehensive design engineering framework to audit, polish, and govern the visual quality of web interfaces, preventing generic "AI slop" and enforcing institutional-grade craftsmanship.

---

## 🎯 Core Principles of Impeccable Design

1. **Hierarchy Before Decoration**:
   * Visual weight must directly map to semantic importance. Primary data points (e.g. Overall Score, MRR, TAM) dominate; secondary metadata recedes with intentional opacity and font size.
   * Avoid decorative elements (e.g., redundant background blobs or rainbow gradients) that compete with critical information.

2. **Strict Typographic Scale & Contrast**:
   * Maintain a proportional modular scale ($10\text{px} \to 12\text{px} \to 14\text{px} \to 16\text{px} \to 20\text{px} \to 24\text{px} \to 32\text{px} \to 48\text{px}$).
   * All text must meet WCAG AA/AAA contrast ratios against dark surfaces (minimum $4.5:1$ for body text, $3.0:1$ for large headings). Never use muted text darker than `text-slate-400` on dark backgrounds.
   * Constrain line lengths to $45\text{--}75$ characters (`max-w-prose` / `max-w-3xl`) for readable paragraph blocks.

3. **Consistent Spatial & Radius Token Systems**:
   * Use an 8pt / 4pt grid system for padding and margins (`p-3`, `p-4`, `p-6`, `p-8`).
   * Nesting radius rule: Inner child radius should be smaller than parent container radius ($\text{Radius}_{\text{child}} = \text{Radius}_{\text{parent}} - \text{Padding}$).

4. **Micro-States & Interactive Affordance**:
   * Every interactive element must define 4 distinct visual states: **Default**, **Hover**, **Active/Pressed**, and **Focus-Visible**.

---

## 🔍 The 59 Deterministic Anti-Pattern Detectors (Summary)

| Category | High-Priority Anti-Patterns Flagged |
| :--- | :--- |
| **Typography** | • Unconstrained body text width ($>80\text{ch}$ causing reading fatigue)<br>• Text contrast $<4.5:1$ against surface background<br>• Mixing more than 2 distinct font families<br>• Arbitrary font sizes bypassing the design scale |
| **Color & Glass** | • Clashing saturated neon accents without a neutral grounding palette<br>• Overuse of multi-color rainbow gradients<br>• Low opacity borders that disappear on low-brightness displays |
| **Layout & Grid** | • Inconsistent card heights causing ragged row alignment<br>• Hardcoded pixel widths breaking responsive viewports ($<375\text{px}$ or $>1440\text{px}$)<br>• Touch targets smaller than $36\times 36\text{px}$ on interactive controls |
| **State & Motion** | • Missing `:focus-visible` outline rings for keyboard accessibility<br>• Animating layout-triggering properties (`width`, `height`, `margin`) instead of `transform`/`opacity`<br>• Abrupt layout pops on async data loading without placeholder skeletons |

---

## 🛠️ Impeccable Workflow Commands

* **`/impeccable audit`**: Conducts a full pass across typography, contrast, spacing, and micro-states.
* **`/impeccable polish`**: Refines specific components with subtle borders, elevation shadows, and micro-interactions.
* **`/impeccable typeset`**: Enforces strict line heights, character limits, and modular scale on all text elements.
* **`/impeccable bolder` / `/impeccable quieter`**: Adjusts the visual prominence and intensity of a section while preserving brand harmony.
