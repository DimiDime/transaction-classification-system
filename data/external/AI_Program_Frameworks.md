# Accenture AI Program — Frameworks Reference

Source: Accenture S&C × Halfspace AI Program, 05.05.2026
Modules covered: Problem Solving + Storytelling (Module 3) + Industry Context + AI Case Studies

---

## 1. Jury & Audience Profile

The panel evaluating the final presentation consists of **C-level stakeholders from NordikBank**. Key characteristics:

- **Domain-knowledgeable** — they understand banking, AML, and compliance deeply
- **Mixed technical literacy** — not all have deep technical backgrounds; technical depth must be right-sized
- **Results-oriented** — they want business impact, not methodology walkthroughs
- **Holistic view** — they expect a full client case, as close to the real world as possible

**Presentation stance:**
- The team is the centre of attention — slides support, they do not lead
- Every element must be meaningful; nothing decorative
- Align on the storyline as a team before building slides
- The goal: make the panel feel the work is real, production-grade, and business-relevant

---

## 2. About the Client Organisation

Understanding the organisational context helps frame the business problem correctly.

**Core business lines:**
- Technology Transformation / Systems Integration
- Operations (outsourcing from client companies)
- Reinvention Services (knowledge-based production)

**Project type:** Long-cycle transformations (2–8 years). This is not a quick-fix engagement — the panel expects a roadmap, not a one-shot result.

**Technology posture:** Technology-agnostic ecosystem. The firm works across:
- Partners: major cloud, AI, and data platform vendors (including LLM providers, MLOps platforms, and defence/analytics platforms)
- Strategic acquisitions in the AI/data space

**Operating model summary:**
- **Work** — the delivery itself
- **Workforce** — talent pipeline and capability building
- **Workbench** — internal and external tooling

This context matters for framing recommendations: suggest operationally realistic next steps, not academic experiments.

---

## 3. Issue-Based Problem Solving

**Problem** = distance between As-is (current state) and To-be (desired state).

Three stages:

| Stage | Action |
|---|---|
| DEFINE | Frame the problem |
| SOLVE | Decompose and analyse |
| COMMUNICATE | Present the answer |

---

## 4. Framing the Problem: S-C-Q

| Element | Definition | Rule |
|---|---|---|
| **Situation** | Simply stated facts no one can dispute | Sets the scene |
| **Complication** | The source of difficulty for the client | The "burning platform" |
| **Question** | The most critical question for project success | Must address the complication |

**Key rule:** Do not take the client's diagnosis of their problem at face value. Dig to the real problem. The question must be simple (not compound), clearly phrased, focused on the most important issue, and addressed to the need to change.

**Common pitfalls when formulating the key question:**
1. Not relevant to the client's situation
2. Does not address the complication
3. Too vague, narrow, or broad
4. Assumption-driven
5. Several questions in one
6. Agreed by client but not validated with all stakeholders

**NordikBank SCQ (this project):**
- **Situation:** NordikBank processes ~5M transactions/month; 45 analysts monitor for AML.
- **Complication:** Rule-based TMS generates 15,000 alerts/month with 97% false positive rate — analysts have capacity for ~50 deep investigations; FSA review is Q3 2025.
- **Question:** How can NordikBank reduce false positives while maintaining regulatory explainability?

---

## 5. Decomposing the Key Question: The Issue Tree

**Why use it:**
- Breaks the key question into smaller, workable sub-problems
- Forces MECE structure (no overlap, no gaps)
- Easy to assign sub-problems to team members without duplication
- Enables identification of root causes, not just symptoms

**How to build:**
1. Start with the key question on the left
2. Break into first-level sub-issues (high-level "why?" answers)
3. Continue decomposing into second-level minor issues
4. Verify MECE at every level

**Two types:**
- **Problem-driven:** Start with the problem, decompose into causes → arrive at solution
- **Solution-driven:** Start with a hypothesis, decompose into reasons/actions → validate or disprove

**MECE check:**
- Mutually Exclusive = no overlap between branches
- Collectively Exhaustive = all branches together cover the full problem space

---

## 6. Communicating the Answer: The Pyramid Principle (Minto)

The mind naturally sorts information into pyramidal groupings. Presenting ideas pre-sorted this way reduces cognitive load.

**Three-part structure:**

| Part | Tool | Purpose |
|---|---|---|
| **Introduction** | S-C-Q | Set the scene, create alignment |
| **Conclusion** | Key message (Answer) | State it up front — inductive preferred |
| **Main Body** | Supporting arguments | Specific evidence, MECE grouped |

**Two pyramid rules:**
- **Rule 1 — Vertical grouping:** Every node must summarise the ideas below it
- **Rule 2 — Horizontal grouping:** Siblings must belong to the same argument and be sequenced logically (chronology / structure / importance)

**Inductive vs. Deductive:**
- **Inductive (preferred):** Lead with the conclusion, support with parallel reasons. Major points are easy to remember; if one point falls, the rest still hold. Risk: can feel direct/assertive for some audiences.
- **Deductive:** Present a chain of logic (A → B → therefore C). Strong single line of argument. Risk: one broken link invalidates the whole argument; audience must hold the whole chain in memory.

---

## 7. Building Individual Pages (Slides)

**Taglines must state the conclusion, not the topic:**

| Bad | Good |
|---|---|
| Market size | The market is big enough for client X to prosper |
| System requirements | The main system requirement is interoperability with SAP |
| Model performance | Engineered features deliver a 21% AUC lift over pre-computed baselines |

**Slide construction principles:**
- **One clear message per slide** — the tagline carries it; the visual proves it
- **Business relevance first** — every slide must answer "so what?" for a C-level audience
- **Simple, action-oriented titles** — not topic labels, not questions
- **Evidence on the slide, implications in the narration**
- **Topic relevance filter** — if a slide does not advance the recommendation, cut it or move it to the appendix
- **Understand your audience** — calibrate depth to the least technical person in the room who still needs to be convinced

**Storyboard approach:** Map the pyramid to slides — one major idea per slide. Use the Slide Sorter view to verify the story flows before building out content.

**What consultants do (vs. what students do):**

| Students often | Consultants do |
|---|---|
| Focus on features without business context | Start with the problem, ensure audience alignment |
| Explain every detail (causing exhaustion) | Guide the audience logically — help them follow |
| Present what was built, forgetting why | Show why the answer matters — enable a decision |

> "Strong solutions create little value if the story is unclear. Storytelling is not decoration — it is how good work becomes understandable, credible, and decision-ready."

---

## 8. Delivery: Telling the Story

**The 4 Ps of vocal delivery:**
- **Projection** — volume and clarity
- **Pitch** — vary tone to signal importance
- **Pace** — slow down at key numbers; let the headline metric land before moving on
- **Pause** — silence after a key point is more powerful than rushing to the next

**Physical presence:**
- Eye contact — hold it; scan the room deliberately
- Hands and arms — use them to signal structure and emphasis
- Placement and movement — own the space; don't retreat behind the screen

**Attention techniques:**
- **Injection** — refer to something physically present in the room to re-engage attention
- **Bridges** — explicitly connect different fields or modules ("this is where our feature engineering connects to the regulatory requirement")
- **Contrast** — introduce an unexpected angle or counterintuitive fact to reset attention before a key point

**Mindset for delivery:**
- Take personal ownership — present as if this were your real client engagement
- Show pride in the work — the panel wants to see capability and confidence
- You want to show off what you can do well — the presentation is the product

---

## 9. AI Case Studies — Patterns to Replicate

Two real delivery examples shown during the session. Extract these patterns for the NordikBank presentation.

### Case A: Fragmented Data → Unified AI Platform

**Problem framed as:** Fragmented data with no common view, manual processes, gut-feel decisions rather than data-driven ones.

**Solution:** Unified real-time data platform with AI-driven planning and built-in decision support.

**Demo structure:** Goal → Functions → Advantages. The demo showed an LLM querying the platform and generating automatic notifications — officer makes the final call.

**Presentation pattern to steal:**
- Lead with the fragmented/broken state (As-is pain)
- Show the unified state (To-be capability)
- Demo: let the tool speak; narrate the decision flow, not the technical stack

### Case B: Automated Audit Workflow (12-week Agentic/GenAI build)

**Client:** Major logistics company (invoice auditing at scale)

**Business value framing:**
- Time savings quantified (30–40% reduction)
- Logistics spend reduction
- EDA metrics and Pareto analysis shown to executives — not model internals

**Triage output used as the demo hook:**
- Red = manual intervention required
- Yellow = awaiting information
- Green = completed automatically

**Technical stack mentioned (for reference only — not the centre of the story):** Python orchestration, Azure, OCR layer, OpenAI model with guard rails, prompt tuning.

**Presentation pattern to steal:**
- Show the current process pain visually (steps, handoffs, bottlenecks)
- Quantify the business value in executive terms (time, cost, headcount)
- Demo the triage output — let the colour-coded result carry the message
- EDA/performance analytics go in the body, not the intro; Pareto framing works well for C-suite

---

## 10. Applied to This Project

**Pyramid for NordikBank:**
```
Answer: ML reduces analyst false-positive burden by X% while satisfying FSA auditability
    ├── 1. Behavioural features reveal patterns the rule engine cannot see
    ├── 2. Gradient boosting ranks customers with AUC-ROC 0.85 vs. 0.71 baseline
    └── 3. Analyst workbench makes risk scores actionable and auditable
```

**Issue tree for solving the key question:**
```
How can NordikBank cut false positives while maintaining explainability?
    ├── Can we build better features from transaction behaviour?
    │       ├── Structuring signals (below 15,000 DKK threshold)
    │       ├── Velocity and dormancy patterns
    │       └── Geographic spread and counterparty diversity
    ├── Can we rank customers more accurately than the rule engine?
    │       ├── Which model architecture? (LR vs. GB)
    │       └── What metric? (AUC-ROC primary; PR-AUC secondary)
    └── Can we make scores usable and auditable for analysts?
            ├── SHAP explanations per customer
            └── Prioritised alert queue with threshold calibrated to 50 investigations/month
```

**Submission format reminder:** `predictions.csv` — columns `customer_id, predicted_probability` (float 0.0–1.0). Panel scores AUC-ROC against true labels. No threshold needed in the file.

**Self-check before presenting:**
- Is the problem clear from slide 1 — without needing explanation?
- Is the solution directly and explicitly linked back to the complication?
- Is every slide tagline a conclusion, not a topic label?
- Are the three main pillars MECE — no overlap, nothing missing?
- Is the technical depth right-sized for a mixed-literacy C-level audience?
- Is value creation (analyst time saved, FSA readiness) stated in business terms, not model metrics?
- Has the demo been rehearsed end-to-end, including the flagged customer walkthrough?
- Does the team feel good about what they are showing — presenting from ownership, not apology?
