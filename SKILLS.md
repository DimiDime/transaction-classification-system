# Project Skills & Collaboration Guidelines

## Context
AML transaction classification system. The goal is to improve a rule-based flagging system
using ML over Danish banking data (~1,200 customers, ~77,000 transactions). The unit of
prediction is the customer (`suspicious_activity_confirmed` in customers.csv), not individual
transactions. Class imbalance is approximately 5% suspicious.

---

## How to Approach This Work

### Critical Thinking
- Challenge assumptions and point out inconsistencies or weak reasoning.
- If something is unclear or potentially incorrect, explain why and suggest a better approach.
- Do not accept a feature, metric, or model choice without connecting it to a business or regulatory justification.

### Explanations
- Prioritize clear, structured, and practical explanations over generic theory.
- When discussing machine learning, explain both intuition and implementation.
- Provide concrete examples where possible: specific features, model choices, risk signals.
- Help translate technical work into clear narratives suitable for a non-technical compliance audience.

### Business & AML Grounding
- Always connect technical decisions (features, models, metrics) to business impact in an AML context.
- Explainability is a compliance requirement, not just a trade-off. Regulators expect reasoning.
  SHAP values, decision rules, or audit trails are non-negotiable, not optional extras.
- Distinguish between a high-recall system (catch everything, high analyst load) and a
  high-precision system (fewer alerts, higher confidence). The right balance depends on
  the institution's SAR filing obligations and analyst capacity.

---

## Data-Specific Considerations

### Unit of Analysis
- The train/val/test split lives in `customers.csv`. Prediction is at the **customer level**.
- Transactions must be aggregated up to the customer before modeling. Never split on transactions.

### Label Leakage
- `suspicious_activity_confirmed` is the target label.
- `alert_history.csv` contains analyst decisions (SAR_filed, escalated, cleared) — these are
  downstream of the label and must not be used as features without careful temporal gating.
- Features must only use information that would be available at the time of scoring.

### Baselines vs. Behavior
- `baselines.csv` contains 6-month behavioral aggregates per customer.
- Features built from `transactions.csv` should be framed as **deviations from baseline**,
  not raw values. A single large transaction means something different for CUST_0000
  (avg monthly volume: 3.5M DKK) than for CUST_0002 (avg: 61K DKK).

### Class Imbalance
- ~5% suspicious cases. Accuracy is a meaningless metric here — do not report it.
- Use Precision-Recall AUC as the primary evaluation metric.
- Use F-beta (beta > 1, recall-weighted) when a single threshold metric is needed.
- Calibrate the classification threshold based on the cost of a missed SAR vs. a false escalation,
  not the default 0.5.

---

## Grounding in Source Documents

Every feature choice, model decision, and design trade-off must be traceable to either the
Case Brief or the Data Dictionary. Do not justify decisions by intuition alone.

### Case Brief: Objectives & Evaluation Criteria

The panel evaluates work across four dimensions — decisions should map to at least one:

1. **Feature Engineering** — transform raw transactions into customer-level behavioural profiles
   (spending patterns, counterparty networks, geographic spread, cash intensity, income consistency)
2. **Model Performance** — primary metric is **AUC-ROC** on 500 held-out test customers.
   A higher score means truly suspicious customers rank closer to the top of the list.
3. **Application** — prioritised alert queue, customer investigation views, risk score explanations,
   investigation workflow
4. **Presentation** — translate technical work into clear narratives; a live demo of a flagged
   customer walkthrough is explicitly valued over methodology slides

Submission format: `predictions.csv` — 500 rows, columns `customer_id, predicted_probability` (0.0–1.0).
No threshold required; the panel computes AUC-ROC against true labels.

### Data Dictionary: Known Constraints & Gotchas

- **Nulls by design:** `age`, `declared_annual_income`, `occupation_category` are null for corporate
  customers — use `declared_annual_turnover` and `industry_code` instead
- **counterparty_bank_country** is null for ~97% of transactions (international wires only)
- **merchant_category_code** is only present for card_payment transactions
- **Declined transactions** (~2%) show attempted amount — no funds moved; treat separately from approved
- **Stale income declarations** — some customers' declared income may not reflect current reality;
  do not treat it as ground truth for income consistency checks
- **Structuring threshold** — NordikBank's internal TMS flags cash above 15,000 DKK; structuring
  patterns cluster just below this amount. This is a bank-specific threshold, not the regulatory limit.
- **alert_history** — 19,192 rows of TMS rule triggers with analyst decisions. These reflect the
  *old* rule-based system, not the ground-truth labels. Use with caution (see Label Leakage above).
- **Data relationships:** customers ↔ transactions (1:N), customers ↔ accounts (1:N),
  customers ↔ baselines (1:1), customers ↔ alert_history (1:N),
  customers.nationality → country_risk, transactions.counterparty_bank_country → country_risk

---

## Feature Engineering Priorities
- Emphasize customer-level aggregation and deviation from behavioral baselines.
- Key signal categories: transaction velocity, counterparty diversity, geographic spread,
  cash usage patterns, dormancy-then-activation, structuring indicators (amounts just below thresholds).
- Encode contextual risk: PEP status, sanctions flags, country risk scores, KYC rating.
- Time-based features: entropy of transaction timing, burst patterns, dormancy periods.

---

## Modeling Guidelines
- Always highlight precision/recall trade-offs and connect threshold choices to analyst workload.
- Prefer interpretable models (logistic regression, gradient boosting with SHAP) over black boxes
  unless a clear performance gain justifies the explainability cost.
- Document why each model was chosen, not just how it performed.
- Validate on the customer-level split in `customers.csv` (train/val/test columns).

---

## Presentation Guidelines (10-Minute Storyline)

The presentation follows the **Minto Pyramid Principle** as taught in the Accenture AI Program
(Module 3: Storytelling). Every slide must carry a conclusion-first action title — not a topic label.

### Structure: S-C-Q → Pyramid → Story

**Introduction (Situation → Complication → Question)** — ~1 min
- **Situation**: NordikBank processes ~5M transactions/month; 45 analysts monitor for AML.
- **Complication**: The rule-based TMS generates 15,000 alerts/month with a 97% false positive rate —
  analysts have capacity for only ~50 deep investigations; the FSA review is Q3 2025.
- **Question**: How can NordikBank cut false positives while maintaining regulatory explainability?

**Conclusion / Key Message** — state it up front, before the evidence:
> "Our ML system reduces the false positive burden by X% while surfacing the highest-risk customers
> first — with SHAP-based explanations that satisfy FSA auditability requirements."

**Main Body** — three MECE pillars that each answer "why does the solution work?":
1. Behavioural feature engineering reveals patterns the rule engine cannot see
2. The gradient boosting model ranks customers with AUC-ROC 0.85 vs. 0.71 baseline
3. The analyst workbench makes risk scores actionable and auditable

### Slide Layout (Accenture Style)

The deck uses the same design system as the NordikBank Case Brief HTML. Replicate it exactly.

**Colour palette**
- `#460073` — dark purple (headers, h2, h3, card titles, table headers) — used as `--pdk`
- `#7500C0` — medium purple (section labels, code text) — used as `--pd`
- `#A100FF` — accent purple (rule underlines, highlight bar, numbered circles) — used as `--pc`
- `#E6DCFF` — light purple tint (card backgrounds, highlight fill, pill backgrounds) — used as `--plk`
- `#fff` — slide background
- `#1a1a1a` — body text

**Cover slide** (dark background, centred text block)
- Background: `#460073` (dark purple)
- Logo top-left; title 48px semibold white; subtitle 24px light purple below; metadata block bottom-left
- Full-width 4px `#A100FF` bar at the very bottom

**Content slides** (all other slides share this structure top-to-bottom)
1. **Header strip** — logo right-aligned + section label left-aligned (10px uppercase, spaced, `#7500C0`);
   separated from body by a 3px solid `#A100FF` bottom border
2. **h2 action title** — 28px semibold `#460073`; this is the slide tagline (conclusion, not topic)
3. **Body** — flex column filling remaining height; uses one of three layout patterns:
   - **Single column** — prose / bullet list / table
   - **Two-column grid** — `grid-template-columns: 1fr 1fr; gap: 28px` for two equal panels
   - **Three-column grid** — `grid-template-columns: 1fr 1fr 1fr; gap: 22px` for three cards
4. **Cards** — light purple tint (`#f9f7fc`) background, 1px `#E6DCFF` border, 3px radius;
   numbered circle badges use `#A100FF` fill, white text (26×26px, circular)
5. **Highlight callout** — `#E6DCFF` background, 4px left border in `#A100FF`; for key takeaways
6. **Footer note** — 10px grey text, 1px top border, absolute-positioned 20px from bottom

**Typography**
- Font: Graphik → Inter → Helvetica Neue → Arial (system fallback)
- h2: 28px / 600 weight / `#460073`
- h3: 17px / 600 weight / `#460073`
- h4: 15px / 600 weight / `#333` (card sub-headers)
- Body / bullets: 15px / 1.6 line-height
- Tables: 14px; header row `#460073` background, white text, uppercase, 0.5px letter-spacing;
  alternating row tint `#faf8fd`; cell border `#e8e3f0`
- Code: Consolas/monospace, 13px, `#f0ecf5` background, `#7500C0` text

**Layout rules from the Storytelling module**
- One main message per slide — the h2 action title states the conclusion, not the topic
- Never reuse the same layout pattern for different concepts (graphical memory is strong)
- Align everything — use grid/flex alignment tools, never eyeball spacing
- Simple boxes over complex visuals — communicate with structure, not decoration
- Spell-check before any submission

### 10-Minute Slide Budget (~1 min per slide)

| # | Action Title | Content |
|---|---|---|
| 1 | NordikBank's TMS creates more noise than signal | S-C-Q opener; 97% FP rate, analyst capacity |
| 2 | Our system re-ranks customers by true behavioural risk | Key message + AUC headline number |
| 3 | Structuring, velocity, and geographic spread are the real signals | Feature engineering: top 5 features, AML rationale |
| 4 | The model lifts AUC from 0.71 to 0.85 — a 21% gain over baseline | ROC / PR curves, baseline vs. engineered comparison |
| 5 | The analyst workbench turns scores into investigations | Live demo: alert queue, customer drill-down, SHAP explanation |
| 6 | SHAP makes every flag explainable to the FSA | SHAP waterfall for a flagged customer; regulatory link |
| 7 | Flagged customer walkthrough: [CUST_XXXX] | Live demo: the panel explicitly values a single customer story |
| 8 | Threshold calibration aligns with analyst capacity | Precision-recall trade-off at 50 investigations/month cap |
| 9 | Next steps: operationalise, monitor drift, expand to corporate | Deployment roadmap; ongoing monitoring |
| 10 | Appendix: methodology, full feature list, hyperparameters | For questions; not presented unless asked |

### Audience & Delivery Notes

- **Audience type**: Panel is analytical + results-oriented (Driver/Analytical quadrant). They want
  evidence and business impact — not methodology slides. Lead with numbers.
- **Technical depth**: Right-size explanations. Compliance stakeholders need intuition, not equations.
  Frame SHAP as "the model's receipt for every decision."
- **Vocal**: Vary pace; pause after the key metric (AUC 0.85) to let it land.
- **Demo over slides**: The live demo of a flagged customer walkthrough is explicitly called out as
  valued by the panel — allocate time for it, rehearse it.
- **Self-assessment checklist before presenting**:
  - Is the problem clear from the first slide?
  - Is the solution linked directly to the problem?
  - Is the technical explanation at the right level for a compliance audience?
  - Is the value creation (analyst time saved, FSA readiness) explicit?
  - Are next steps realistic and scoped?
