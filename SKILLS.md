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
