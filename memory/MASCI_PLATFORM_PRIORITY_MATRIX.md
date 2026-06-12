# MASCI Platform — Priority Matrix (Track 13.4B · Phase 3)

**Mode:** Discovery + classification only. Tiered prioritisation; no recommendations, no implementation plan.  
**Source:** `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`.  
**Generated:** 2026-02.

---

## A. Scoring rubric (per finding)

Each finding receives a 0/1/2/3 score on every axis below. **0 = none, 1 = low, 2 = medium, 3 = critical.**

| Axis | Meaning |
|---|---|
| Ops Risk | Risk to live operational truth (Dispatch trust, status accuracy, count accuracy). |
| User Impact | How many operator interactions are affected per day. |
| Trust Impact | Operator confidence in platform truth. |
| Five-Pillar Impact | Strongest pillar violation (Powerful / Simple / Beautiful / Trusted / Proven). |
| WL Impact | White-label / multi-tenant readiness impact. |
| Cust #2 Impact | Risk to onboarding Customer #2. |
| Safety Impact | Risk to safety-critical flows (JHA · Incident · Trench · CAPAs). |
| Field Impact | Field operator (Spanish-speaking crew, foreman) usability impact. |
| Complexity | Engineering complexity to remediate (NOT yet planning — descriptive only). |
| Effort | Rough person-week scale (0 = hours, 1 = days, 2 = weeks, 3 = months). |
| Dep Risk | Risk that addressing this finding breaks another. |

---

## B. Scored matrix

### B.1 EXISTENTIAL findings (Tier 1 candidates)

| Finding | Ops | User | Trust | 5P | WL | Cust#2 | Safety | Field | Complex | Effort | Dep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W-01 No tenant model | 1 | 0 | 1 | 3 | 3 | 3 | 0 | 0 | 3 | 3 | 3 |
| W-02 No tenant scoping in routes | 1 | 0 | 1 | 3 | 3 | 3 | 0 | 0 | 3 | 3 | 3 |
| W-09 Hardcoded MASCI legal text (EN+ES) | 0 | 0 | 2 | 3 | 3 | 3 | 1 | 1 | 1 | 1 | 1 |
| W-12 No tenant onboarding surface | 0 | 0 | 0 | 3 | 3 | 3 | 0 | 0 | 3 | 3 | 2 |
| D-01 Production Motive webhook unverified | 3 | 2 | 3 | 3 | 0 | 0 | 2 | 2 | 1 | 1 | 1 |
| D-03 100/190 assets no GPS | 3 | 2 | 3 | 3 | 0 | 0 | 1 | 2 | 2 | 2 | 1 |
| D-04 157 assets stale | 3 | 2 | 3 | 3 | 0 | 0 | 1 | 2 | 2 | 2 | 1 |
| T-01 Safety-Critical UI Spanish gap | 1 | 2 | 2 | 3 | 0 | 0 | **3** | **3** | 1 | 2 | 0 |
| T-08 Outbound emails English-only | 0 | 2 | 2 | 2 | 1 | 1 | 2 | **3** | 2 | 2 | 1 |
| T-09 Server-rendered PDFs English-only | 0 | 2 | 2 | 2 | 1 | 1 | 2 | **3** | 2 | 2 | 1 |

### B.2 MAJOR DRIFT (Tier 2 candidates)

| Finding | Ops | User | Trust | 5P | WL | Cust#2 | Safety | Field | Complex | Effort | Dep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V-04 `tokens.css` unwired | 0 | 1 | 1 | 2 | 3 | 2 | 0 | 0 | 2 | 2 | 1 |
| V-11 Status verb overload | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
| V-12 Closure verb drift | 1 | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 2 | 1 |
| V-14 Public surface chrome drift | 0 | 1 | 1 | 2 | 3 | 2 | 0 | 0 | 2 | 2 | 1 |
| W-03 497 files reference "MASCI" | 0 | 0 | 1 | 2 | 3 | 2 | 0 | 0 | 2 | 2 | 1 |
| W-04 52 files reference `mascigc.com` | 0 | 0 | 1 | 2 | 3 | 2 | 0 | 0 | 1 | 1 | 1 |
| W-08 Hardcoded recipient emails | 0 | 1 | 1 | 2 | 3 | 3 | 1 | 1 | 1 | 1 | 1 |
| W-10 PDFs / outage alerts brand-leak | 0 | 1 | 1 | 2 | 3 | 2 | 0 | 0 | 1 | 1 | 1 |
| W-13 Per-workflow status engines hardcoded | 0 | 0 | 1 | 2 | 3 | 2 | 0 | 0 | 3 | 3 | 2 |
| W-15 Public surfaces single brand chrome | 0 | 0 | 1 | 2 | 3 | 2 | 0 | 0 | 2 | 2 | 1 |
| W-19 No per-tenant overlay model | 0 | 0 | 1 | 2 | 3 | 2 | 0 | 0 | 3 | 3 | 2 |
| W-20 Email templates Python-coded | 0 | 0 | 1 | 2 | 3 | 2 | 0 | 0 | 2 | 2 | 1 |
| T-02 Field-Critical Spanish gap (82.5%) | 1 | 2 | 2 | 2 | 0 | 0 | 2 | 3 | 1 | 2 | 0 |
| T-03 Workflow-Critical Spanish gap (82.5%) | 1 | 2 | 2 | 2 | 0 | 0 | 2 | 2 | 1 | 2 | 0 |
| T-04 Public-Facing Spanish gap (73.6%) | 0 | 1 | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 0 |
| T-12 Status verb translation = 0% | 1 | 2 | 2 | 2 | 0 | 0 | 1 | 2 | 1 | 2 | 1 |
| R-02 Daily/Inspect/Incident overlap | 0 | 2 | 1 | 2 | 0 | 0 | 1 | 2 | 2 | 2 | 1 |
| R-06 OA-1 still on 6 portals | 0 | 1 | 1 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| D-06 67 circle geofences render 0 | 1 | 1 | 2 | 2 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| V-05 Hub size variance 4.6× | 0 | 0 | 0 | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 1 |
| V-06 Header pattern variance | 0 | 0 | 0 | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 1 |
| V-07 Status-chip sprawl (15 components) | 0 | 1 | 1 | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 1 |
| V-09 Command-center sprawl (8 pages) | 0 | 1 | 1 | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 1 |
| V-13 Mobile evidence gap | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 2 | 0 | 1 | 0 |
| V-15 Driver portal landing missing | 0 | 1 | 1 | 2 | 0 | 0 | 1 | 2 | 1 | 1 | 0 |
| R-01 8 auth-flow variations | 0 | 1 | 1 | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 1 |
| R-10 Backend emails/PDFs/Excel English-only | (= T-08/T-09/T-10) | | | | | | | | | | |

### B.3 OPTIMISATION (Tier 3 candidates)

| Finding | Ops | User | Trust | 5P | WL | Cust#2 | Safety | Field | Complex | Effort | Dep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V-01 Shop header amber vs orange | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| V-02 PM tile-CTA amber vs indigo | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| V-03 FL red-700 overlaps Admin | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| V-08 OA-1 leakage (= R-06) | — | | | | | | | | | | |
| V-10 Status case drift | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| W-05 73 files reference "ForgedOps" | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| W-11 Excel filenames `MASCI_` | 0 | 0 | 1 | 1 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| W-14 8 auth flows × 0 tenant scope (= R-01) | — | | | | | | | | | | |
| W-16 `forgedops-logo.png` unused | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| W-17 Training catalog partial-positive | (positive) | | | | | | | | | | |
| W-18 Digest cadence partial-positive | (positive) | | | | | | | | | | |
| R-03 8 command-center pages (= V-09) | — | | | | | | | | | | |
| R-04 4 admin health pages overlap | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| R-05 `AdminCompliance` + `AdminComplianceFindings` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R-07 Notification duplication (PO digest) | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| R-09 1,146 dead Spanish keys | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R-11 Status verbs not in `t()` (= T-12) | — | | | | | | | | | | |
| R-14 Public form chrome drift (= V-14) | — | | | | | | | | | | |
| R-15 `guidance_search_misses` invisible | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D-02 Preview no live webhooks | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| D-05 33 attention-required | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| D-07 marker_kind heuristic | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| D-08 operational_summary unverified | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| D-09 cross-portal consistency | (positive) | | | | | | | | | | |
| T-05 Admin Spanish gap (74.0%) | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| T-06 Technical Spanish gap (68.8%) | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T-07 Unclassified Spanish gap (79.3%) | 0 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 2 | 0 |

---

## C. Tier assignment

### Tier 1 — Existential threats (12 findings)

| Tier-1 ID | Description |
|---|---|
| **W-01** | No tenant model exists |
| **W-02** | No tenant scoping in production routes |
| **W-09** | Hardcoded MASCI legal text in form acknowledgements (EN + ES) — legal exposure |
| **W-12** | No tenant onboarding surface |
| **D-01** | Production Motive webhook activity unverified |
| **D-03** | 100 of 190 motive-mapped assets lack GPS coords |
| **D-04** | 157 assets are no-recent / stale |
| **T-01** | Safety-Critical UI Spanish readiness only 75.8 % |
| **T-08** | Outbound emails 0 % Spanish |
| **T-09** | Server-rendered PDFs 0 % Spanish |
| **V-04** | `tokens.css` declared "PROPOSAL — NOT YET WIRED" (blocks all retheming) |
| **W-13** | Per-workflow status engines hardcoded (blocks workflow tenant config) |

### Tier 2 — Major platform drift (24 findings)

V-05 · V-06 · V-07 · V-09 · V-11 · V-12 · V-13 · V-14 · V-15 · R-01 · R-02 · R-06 · W-03 · W-04 · W-08 · W-10 · W-15 · W-19 · W-20 · T-02 · T-03 · T-04 · T-12 · D-06

### Tier 3 — Optimisation opportunities (30+ findings)

V-01 · V-02 · V-03 · V-10 · W-05 · W-11 · W-16 · R-04 · R-05 · R-07 · R-09 · R-15 · D-02 · D-05 · D-07 · D-08 · T-05 · T-06 · T-07 · plus all `(positive)` rows that are partial-positives (W-17 · W-18 · D-09) — not threats but documented for completeness.

### Positives (record but never remediate)

- W-17 Training catalog partially tenant-ready.
- W-18 Digest cadence partially tenant-ready.
- D-09 Dispatch & `/operations-map` consume same hook (cross-portal consistent).

---

## D. Risk ordering — top 12 by composite score

Composite = `Ops + User + Trust + 5P + WL + Cust#2 + Safety + Field` (sum of impact axes only, excluding effort/complexity).

| Rank | Finding | Composite |
|---|---|---|
| 1 | T-01 Safety-Critical UI Spanish gap | 14 |
| 2 | D-01 Production Motive webhook unverified | 13 |
| 3 | D-03 100 of 190 assets no GPS | 12 |
| 4 | D-04 157 assets stale | 12 |
| 5 | T-08 Outbound emails English-only | 13 |
| 6 | T-09 Server-rendered PDFs English-only | 13 |
| 7 | W-01 No tenant model | 11 |
| 8 | W-02 No tenant scoping in routes | 11 |
| 9 | W-09 Hardcoded MASCI legal text | 13 |
| 10 | W-12 No tenant onboarding | 9 |
| 11 | T-02 Field-Critical Spanish gap | 12 |
| 12 | T-03 Workflow-Critical Spanish gap | 11 |

(Order is informational. No remediation sequence is proposed.)

---

## E. What this matrix did NOT do
- Did not propose a remediation plan.
- Did not propose a Design System V1.
- Did not estimate calendar time.
- Did not propose a tenant model schema.
- Did not propose a translation strategy.
- Did not estimate cost.
- Did not propose a rollout sequence.

All deferred to Track 13.4C / 13.4D / Phase 4+ post-operator-authorization.
