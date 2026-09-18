---
name: market-mapping
description: Institutional-grade market landscape mapping, TAM/SAM/SOM triangulation, 2x2 competitive positioning matrix, and whitespace opportunity identification for AI venture strategy.
---

# Market Mapping & Competitive Intelligence Skill

This skill provides a standardized, consulting-grade framework to map markets, calculate defensible market sizes, construct 2×2 positioning matrices, and identify strategic "where-to-play" whitespace opportunities.

---

## 🎯 Core Analytical Frameworks

### 1. Triangulated Market Sizing (TAM / SAM / SOM)

Do not rely solely on top-down macroeconomic reports. Triangulate using both methodologies:

#### A. Top-Down Approach
$$\text{TAM}_{\text{Top-Down}} = \text{Total Industry Size} \times \text{Addressable Sub-Segment Percentage}$$

#### B. Bottom-Up Approach
$$\text{TAM}_{\text{Bottom-Up}} = \text{Total Qualified Buyer Organizations/Individuals} \times \text{Annual Contract Value (ACV) / ARPU}$$

#### C. Triangulation & Discrepancy Gate
* **SAM (Serviceable Available Market)**: The proportion of TAM reachable with the current business model, geography, and regulatory constraints.
* **SOM (Serviceable Obtainable Market)**: The realistic market share captured within 3–5 years given sales velocity and capital runway (typically 1–5% of SAM in early stages).
* **Sanity Hierarchy**: Strictly enforce $\text{SOM} \le \text{SAM} \le \text{TAM}$.
* **Variance Alert**: If $\text{TAM}_{\text{Top-Down}}$ and $\text{TAM}_{\text{Bottom-Up}}$ diverge by $>30\%$, explicitly reconcile the discrepancy by evaluating pricing elasticity or segmentation boundaries.

---

### 2. 2×2 Competitive Whitespace Matrix

Position the venture against incumbents across two polarizing, high-impact axes:

1. **Axis Selection**:
   * **Axis X (Execution / Architecture)**: e.g., *Self-Serve / Modular* vs. *Full-Stack / Custom Enterprise*, or *Lightweight AI Co-pilot* vs. *Autonomous System of Record*.
   * **Axis Y (Value Proposition / Focus)**: e.g., *Horizontal Generalist* vs. *Vertical Domain-Specialized*, or *Cost Leadership* vs. *High-Compliance / Security-First*.
2. **Quadrant Mapping**:
   * **Incumbents**: Plot legacy players and direct rivals in existing crowded quadrants.
   * **Venture Wedge (Whitespace)**: Highlight the underserved quadrant with high willingness-to-pay and low incumbent agility.

---

### 3. Value-Chain & Ecosystem Mapping

Map structural industry relationships:
* **Upstream**: Critical suppliers, data providers, foundational model vendors, or raw material providers.
* **Core Value Addition**: The proprietary transformation, automated orchestration, or regulatory moat built by the venture.
* **Downstream**: Distribution channels, system integrators, resellers, and end customers.
* **Gatekeepers & Regulators**: Compliance bodies, certification hurdles, and platform gatekeepers (e.g., Apple App Store, HIPAA/GDPR auditors).

---

### 4. Output Deliverable Schema

When executing a market mapping assessment, structure the result in structured JSON or clean Markdown:

```json
{
  "market_sizing": {
    "top_down_tam": "$14.2B Global Market (CAGR 18.4%)",
    "bottom_up_tam": "$11.8B (120k target enterprises × $98k ACV)",
    "sam": "$2.4B (North America & UK enterprise tier)",
    "som_3yr": "$120M (5% market share of core SAM by Year 3)",
    "triangulation_notes": "Variance within 17% tolerance; validated against peer enterprise SaaS pricing benchmarks."
  },
  "positioning_matrix": {
    "x_axis": "Integration Complexity (Turnkey vs Custom Heavy)",
    "y_axis": "Compliance & Security (Generalist vs Regulated Grade)",
    "whitespace_quadrant": "Top-Right: Turnkey deployment with institutional-grade regulatory compliance",
    "competitor_positions": [
      {"name": "Legacy Incumbent A", "quadrant": "Custom Heavy / Regulated Grade"},
      {"name": "Point Solution B", "quadrant": "Turnkey / Low Compliance"}
    ]
  },
  "where_to_play_wedge": "Initial entry wedge focuses on mid-market regulated entities seeking automated compliance without 6-month consulting implementations."
}
```
