---
name: emil-design-eng
description: Institutional design engineering, UI motion principles, spring-physics animations, and micro-interaction craft standards based on Emil Kowalski's design philosophy.
---

# Emil Kowalski Design Engineering & UI Motion Skill

This skill provides a standardized framework for building and auditing high-craft user interfaces, fluid animations, and polished micro-interactions.

---

## 🎨 Core Design Engineering Philosophy

1. **Intentionality Over Noise**:
   * Motion must serve a functional purpose: communicating hierarchy, spatial relationship, status change, or user intent.
   * If an animation does not make the interface easier to understand or more satisfying to interact with, remove it.

2. **Spring Physics Over Linear Easing**:
   * Avoid linear transitions and generic `ease-in-out` which feel robotic and artificial.
   * Use spring curves with high initial velocity and smooth deceleration (`cubic-bezier(0.16, 1, 0.3, 1)` or spring parameters with $\text{damping} \approx 20\text{--}30$, $\text{stiffness} \approx 200\text{--}300$).

3. **Composite-Only Property Animation**:
   * **Always Animate**: `transform` (`translate`, `scale`, `rotate`), `opacity`, and `filter`.
   * **Never Animate**: `width`, `height`, `top`, `left`, `margin`, or `padding` directly (causes layout recalculation, paint thrashing, and dropped frames).

4. **Spatial Continuity & Layout Stability**:
   * Elements should appear from where they originated or slide in along logical spatial axes (e.g. wizard step progression, modal expansion from trigger).
   * Avoid layout shifts (CLS) by reserving dimensions or using `transform: scale()` for expanding elements.

---

## ⚡ Curated Easing Curves & Timing Tokens

```css
:root {
  /* Fast Deceleration (Fluid Enter): 0.16, 1, 0.3, 1 */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
  
  /* Natural Spring Snap (Micro-interactions / Buttons): 0.34, 1.56, 0.64, 1 */
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* Gentle Exit (Smooth Dismissal): 0.7, 0, 0.84, 0 */
  --ease-out-smooth: cubic-bezier(0.25, 0.1, 0.25, 1);
  
  /* Micro Durations */
  --duration-micro: 150ms;
  --duration-enter: 280ms;
  --duration-layout: 400ms;
}
```

---

## 🛠️ Key Micro-Interaction Patterns

### 1. Staggered Stream / List Ingress
When elements stream in (e.g., live logs, discussion messages), stagger opacity and vertical translation to avoid sudden visual pops:
```css
@keyframes stagger-in {
  0% {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

### 2. Active Pulse & Glowing Rings
For active AI agents or speaking state indicators:
```css
@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(99, 102, 241, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(99, 102, 241, 0);
  }
}
```

### 3. Step & Tab Transitions
Animate active tab indicators with spring sliding effects, and form wizard transitions with subtle directional slide-in.

---

## 🔍 Code Review Checklist for UI Animation

* [ ] Are all animated properties GPU-accelerated (`transform` / `opacity`)?
* [ ] Are durations appropriate (typically $150\text{--}350\text{ms}$ for micro-interactions, never $>500\text{ms}$)?
* [ ] Does interactive feedback trigger immediately on `:active` / `pointerdown`?
* [ ] Is `prefers-reduced-motion` respected for accessibility?
* [ ] Are layout elements visually grounded with subtle borders and shadows?
