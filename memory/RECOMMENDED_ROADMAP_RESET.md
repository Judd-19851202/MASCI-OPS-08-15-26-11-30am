# OMEGA · RECOMMENDED ROADMAP RESET

**Date:** 2026-06-02 · Replaces prior severity-ordered roadmap (`OPERATIONAL_REALITY_PRIORITIZED_ROADMAP.md`) as the canonical pre-build sequencing reference
**Mode:** READ-ONLY · zero code · zero design · zero estimates · zero authorization
**Method:** Re-organize the 48-gap roadmap by Build/Integrate/Ignore Doctrine alignment + Constitutional Review verdicts. Informational waves only. No timing commitments. No effort numbers. No batch numbers. Operator authorizes one wave at a time.

---

## §0 · Why a reset?

The prior `OPERATIONAL_REALITY_PRIORITIZED_ROADMAP.md` ordered the 48 gaps by severity (P0 / P1 / P2 / P3 / Architectural). Severity-ordered sequencing answers "what hurts most?" but the post-doctrine question is **"what should the platform actually build, in what order, given that 31 of 48 items belong outside ForgedOps?"**

The reset roadmap separates the 48 items into three lanes (BUILD · INTEGRATE · IGNORE) and orders each lane by:
1. Build/Integrate/Ignore Doctrine fit
2. Constitutional Review verdict (PASS items move first; REVIEW REQUIRED items move after operator scoping decisions)
3. Mission-pillar dependency (accountability primitives → field ops → office ops → executive ops → architectural)

The IGNORE lane has no wave structure — items on it are eliminated or never started.

---

## §1 · BUILD lane (24 items + 7 HYBRID build-side)

### Wave 1 · Accountability primitives + Constitutional re-scopes
*Foundation — every downstream wave presupposes this layer exists*

| Item | Source | Constitutional posture |
|---|---|---|
| Universal Ownership Layer A+B | G0-11 + G1-2 + G1-11 + G1-14 + Top 10 #1 | ✅ PASS · no manual-assign UI · auto-derive from state machine |
| `manager_employee_id` schema addition | G1-11 + B-20 | ✅ PASS · Rule 8 routing primitive |
| Notification Routing per Rule 8 + iter452.5.2 Resend Bounce Webhook | Top 10 #10 + Compliance Sweep O-5 | ✅ PASS · pre-authorized · strongest Constitutional alignment |
| Three-CA system canonicalization | G0-10 | ✅ PASS · Rule 3 + Rule 6 |
| iter445 "Has crew reviewed JHP?" Yes/No field elimination | G0-12 / FAIL-1 | (Counts as IGNORE-execution · paired with Wave 1 because it touches the same data path as ownership primitives) |
| Vestigial `db.jhas` form decommission | FAIL-2 | (Same as above) |
| OC-005 re-scope decision per Amendment 001 (CV-1 resolution) | Top 10 #8 | 🟡 REVIEW REQUIRED — operator selects among 8 options in `AMENDMENT001_EXECUTIVE_SUMMARY.md §5` |
| iter453 closure-action contract per Amendment 001 REPLACE-4/5 | Top 10 #5 / G2-1 / G2-2 | 🟡 REVIEW REQUIRED — Cluster B of `BUILD_INTEGRATE_IGNORE_CONSTITUTIONAL_REVIEW.md §7` |

### Wave 2 · Field operations foundation
*Heavy-civil differentiator stack — depends on Wave 1 ownership primitives*

| Item | Source | Constitutional posture |
|---|---|---|
| Field Clock-in/Clock-out per employee | G0-7 / B-8 / Top 10 #2 / Greenfield #1 | ✅ PASS · Tier 1 by construction · GPS replaces V-6 attestation |
| Production Tracking by Activity | G0-8 / B-9 / Top 10 #3 / Greenfield #2 | ✅ PASS · Tier 1 production data · heavy-civil differentiator |
| Equipment utilization-by-job | G2-5 / B-22 | ✅ PASS · consumes existing Tier 1 primitives |
| Material delivery confirmation | B-10 | ✅ PASS · extends PO workflow |
| Photo Janitor (OC-009) | G3-6 | ✅ PASS · Constitutional exemplar |
| OC-006 Safety Meeting amend | G3-1 | ✅ PASS · existing primitive completion |
| OC-016 Continuity Events edit/close | G3-2 | ✅ PASS · existing primitive completion |
| OC-017 Safety digest fire relocation | G3-3 | ✅ PASS · Rule 9 surface relocation |
| OC-022 Reopen actions across 14 workflows | G3-5 | ✅ PASS · Rule 4 extension |

### Wave 3 · Safety / Fleet regulatory surfaces
*Regulatory artifacts and compliance Action Consoles*

| Item | Source | Constitutional posture |
|---|---|---|
| OSHA 300 / 301 / 300A Generator | G1-6 / B-15 / Top 10 #6 / Greenfield #4 | ✅ PASS · 300A signature legally required Tier 4 ride-along |
| OC-005 re-scoped build (per Wave 1 decision) | Top 10 #8 | (depends on Wave 1 operator decision) |
| OC-008 PPE Return | G2-3 / B-16 | ✅ PASS · operational action |
| Stop-work authority structured workflow | B-17 | ✅ PASS · operational decision content |
| Driver Qualification File | G1-7 / B-23 / Top 10 #7 / Greenfield #5 | 🟡 REVIEW REQUIRED — exclude V-10 annual DOT-policy ack ritual |
| DOT Compliance Dashboard (Action Console) | G1-8 / B-24 / Top 10 #7 / Greenfield #5 | 🟡 REVIEW REQUIRED — Cluster A anti-checklist enforcement |

### Wave 4 · Office operations + Executive surfaces
*Office-side workflows + Executive visibility (depends on Wave 1 ownership + EX-1 accounting Wave per INTEGRATE lane)*

| Item | Source | Constitutional posture |
|---|---|---|
| Executive Role + Portfolio Action Console | G1-1 / G1-3 / B-11 / B-12 / Top 10 #4 / Greenfield #3 | 🟡 REVIEW REQUIRED — Cluster A anti-checklist enforcement |
| Per-PM accountability scorecard | G1-2 / B-12 / part of Top 10 #1 | ✅ PASS · Action Console consumer |
| Submittal workflow | G0-3 / B-1 | 🟡 REVIEW REQUIRED — Cluster D ack-ride-along exclusion (V-1) |
| RFI workflow | G0-4 / B-2 | 🟡 REVIEW REQUIRED — Cluster D ack-ride-along exclusion (V-2) |
| Subcontractor management | G0-9 / B-14 / Top 10 #9 | 🟡 REVIEW REQUIRED — Cluster D (V-12 sub-acknowledges-scope exclusion) |
| Meeting-minutes capture | G2-15 / B-6 | 🟡 REVIEW REQUIRED — Cluster A (V-5 minutes-as-ack exclusion) |
| Change-Order workflow (build-side) | G0-5 / B-3 | 🟡 REVIEW REQUIRED — Cluster D (V-3 approval-ack exclusion) + EX-1 dependency |
| Pay-Application workflow (build-side) | G0-6 / B-4 | 🟡 REVIEW REQUIRED — Cluster D + EX-1 dependency |
| Lien-Waiver tracking (build-side) | G2-14 / B-5 | ✅ PASS · document tracking is Tier 1 · EX-1 dependency for financial linkage |
| Project Budgeting / Forecast-to-Complete UI (build-side) | B-7 | ✅ PASS for UI side · EX-1 dependency for actuals |
| OC-013 Onboarding field-side build | G2-7 / partial | 🟡 REVIEW REQUIRED — Cluster C (Amendment 001 REPLACE-7) + HRIS HYBRID split |
| OC-014 Offboarding field-side build | G2-8 / partial | 🟡 REVIEW REQUIRED — Cluster C (Amendment 001 REPLACE-6) + HRIS HYBRID split |
| Discipline tracking (safety-incident-tied build) | G1-10 / B-19 / partial | 🟡 REVIEW REQUIRED — HR/Safety boundary decision |

### Wave 5 · Architectural multi-tenancy (parallel track)
*Customer #2 readiness — runs in parallel with Waves 2-4 once authorized*

| Item | Source | Constitutional posture |
|---|---|---|
| `tenant_id` propagation across 141 collections | G1-12 | ✅ PASS · architectural foundation |
| Multi-tenant auth / SSO / SAML / OIDC (build-side) | G1-13 | ✅ PASS · architectural · auth provider INTEGRATE side handled in INTEGRATE lane |
| Multi-tenant onboarding wizard | from `OPERATIONAL_REALITY_PRIORITIZED_ROADMAP.md` Arch-3 | ✅ PASS |
| Brand-config / White-Label layer | from prior roadmap Arch-4 | ✅ PASS |
| Operations Center MVP | from prior roadmap Arch-5 | 🟡 REVIEW REQUIRED — Constitution-led from inception per Compliance Sweep O-6 |

---

## §2 · INTEGRATE lane (15 INTEGRATE + 7 HYBRID integration-side)

### Wave 1 · Single largest unblock
| Item | Verdict |
|---|---|
| **EX-1 Accounting / ERP** | 🔗 INTEGRATE — BLOCKING · ranks ahead of most BUILD items per `EXTERNAL_DEPENDENCY_STRATEGY.md §6` |

### Wave 2 · Required integrations
| Item | Verdict |
|---|---|
| **EX-2 Payroll processor** | 🔗 INTEGRATE — REQUIRED · completes iter452 variance loop |
| **EX-4 ELD / Telematics (Motive)** | 🔗 INTEGRATE — REQUIRED · feeds DQ-file + DOT Dashboard |

### Wave 3 · Regulatory + recommended integrations
| Item | Verdict |
|---|---|
| **EX-8 OSHA portal** | 🔗 INTEGRATE — REGULATORY · pairs with B-15 OSHA Generator |
| **EX-6 Drug-test pool** | 🔗 INTEGRATE — RECOMMENDED · feeds DQ-file |
| **EX-11 MSDS / SDS library** | 🔗 INTEGRATE — RECOMMENDED · JHP context linkage |
| **EX-7 Workers comp carrier** | 🔗 INTEGRATE — RECOMMENDED · incident→claim ID linkage |
| **EX-3 Scheduling (P6 / HCSS HeavyJob)** | 🔗 INTEGRATE — RECOMMENDED · look-ahead view (may move earlier if MASCI uses HCSS) |

### Wave 4 · Optional integrations
| Item | Verdict |
|---|---|
| **EX-9 Benefits administration** | 🔗 INTEGRATE — OPTIONAL · employee-status push |
| **EX-10 ATS / recruiting** | 🔗 INTEGRATE — OPTIONAL · hire-event consumption |
| **EX-5 IFTA** | 🔗 INTEGRATE — OPTIONAL · ELD-bundled · likely zero-effort |

### Architectural integration (parallel track · Wave 5 of BUILD lane)
| Item | Verdict |
|---|---|
| **Auth provider (Auth0 / Okta)** | 🔗 INTEGRATE side of G1-13 multi-tenant SSO |

---

## §3 · IGNORE lane (48 items · no wave structure)

Items in this lane are **eliminated or never started**. No wave assignment. Cross-references:

| Category | Item count | Authoritative source |
|---|---:|---|
| Amendment 001 acknowledgement-as-work violations | 18 | `FORGEDOPS_IGNORE_LIST.md §1 + §3 (V-1..V-14 + ad-hoc)` |
| Mature-system replacement avoidance (Doctrine) | 22 | `FORGEDOPS_IGNORE_LIST.md §2` |
| Architectural / UX anti-patterns | 8 | `FORGEDOPS_IGNORE_LIST.md §3` |
| **TOTAL** | **48** | |

The IGNORE lane is the operational fence around ForgedOps's mission. Returning items from this lane to the BUILD lane requires explicit Constitutional reconsideration.

---

## §4 · Cross-lane dependencies

| Dependency | Source wave | Consumer wave |
|---|---|---|
| Ownership Layer A+B | BUILD Wave 1 | All BUILD waves 2–5 + Per-PM scorecard + Executive Action Console |
| `manager_employee_id` | BUILD Wave 1 | Notification Routing · Discipline tracking · all escalation surfaces |
| Field Clock-in/out | BUILD Wave 2 | Production Tracking · Utilization-by-job · payroll variance reconciliation |
| EX-1 Accounting | INTEGRATE Wave 1 | BUILD Wave 4 HYBRID items (CO · Pay-App · Lien-Waiver · Budgeting) + Executive financial column |
| EX-2 Payroll processor | INTEGRATE Wave 2 | iter452 variance loop closure · payroll reconciliation Action Console |
| EX-4 ELD / Motive | INTEGRATE Wave 2 | BUILD Wave 3 DQ-file + DOT Dashboard |
| EX-8 OSHA portal | INTEGRATE Wave 3 | BUILD Wave 3 OSHA Generator output submission |
| `tenant_id` propagation | BUILD Wave 5 | Multi-tenant SSO + Customer #2 onboarding wizard |
| Constitutional re-scope decisions (4 P0 CVs) | BUILD Wave 1 | iter453 build · OC-005 build · OC-013/014 build |

---

## §5 · Operational completeness ceiling per wave (informational projection only)

| State | Aggregate Operability Score (projected · not authorized) |
|---|---:|
| Today (`COMPANY_OPERABILITY_SCORECARD.md`) | 35/100 🔴 |
| After BUILD Wave 1 (Ownership + Constitutional re-scopes + Notification Routing) | ~50/100 🟡 |
| After BUILD Wave 2 (Field ops foundation) | ~60/100 🟡 |
| After INTEGRATE Wave 1 (EX-1 Accounting) | ~65/100 🟡 |
| After BUILD Wave 3 (Safety / Fleet regulatory) | ~70/100 🟢 |
| After BUILD Wave 4 (Office + Executive surfaces) + INTEGRATE Wave 2 | ~80/100 🟢 |
| After BUILD Wave 5 (Architectural multi-tenancy) + INTEGRATE Waves 3–4 | ~90/100 🟢 |
| After IGNORE lane discipline maintained throughout | (preserved) |

Projections are informational only. Actual completeness depends on operator-authorized scope per wave.

---

## §6 · What this roadmap is NOT

| Not a … | Because |
|---|---|
| Estimate | OMEGA scope forbids estimates |
| Authorization | OMEGA scope forbids unsolicited build authorizations |
| Implementation plan | OMEGA scope forbids implementation planning |
| Timing commitment | No calendar dates · no engineer-day budgets |
| Vendor selection | INTEGRATE items name market categories only |
| Severity ranking | Severity-ranked roadmap survives at `OPERATIONAL_REALITY_PRIORITIZED_ROADMAP.md` for cross-reference |
| Drop-in replacement for batch authorization | Each wave still requires explicit operator message before any work commences |

---

## §7 · How to use this document

1. **Operator reviews** the lanes and waves.
2. **Operator selects** one wave (or one slice of one wave) to authorize as the next batch.
3. **Operator authorizes** the batch in a new message with explicit scope.
4. **Agent executes** the authorized batch only · zero drift outside it.
5. **Agent stops · reports · updates _INDEX + PRD · awaits next operator message.**

Per OMEGA discipline, the agent will **never** assume authorization for a wave from this document alone. Adoption of the roadmap reset itself is also operator-authorized (Option H in `BUILD_INTEGRATE_IGNORE_EXECUTIVE_SUMMARY.md §6`).

---

## §8 · Doctrine cross-citations

| Doctrine | Reference |
|---|---|
| Constitution Parts I–IV | `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` |
| Constitutional Override | Constitution Part II |
| Amendment 001 (Rule 11 + Evidence Hierarchy) | Constitution Part IV |
| Build/Integrate/Ignore Doctrine | This batch (`BUILD_INTEGRATE_IGNORE_MASTER_REGISTER.md` §0) |
| 4 forward-binding REVIEW REQUIRED clusters | `BUILD_INTEGRATE_IGNORE_CONSTITUTIONAL_REVIEW.md §7` |
| 4 P0 Constitutional Violations awaiting operator decision | `CONSTITUTIONAL_CONFLICT_REGISTER.md` (CV-1..CV-4) |
| 8 Amendment 001 decision options | `AMENDMENT001_EXECUTIVE_SUMMARY.md §5` |
| 8 Build/Integrate/Ignore decision options | `BUILD_INTEGRATE_IGNORE_EXECUTIVE_SUMMARY.md §6` |

---

## §9 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero solutions designed | ✅ |
| Zero implementation plans | ✅ |
| Zero estimates | ✅ |
| Zero authorizations issued | ✅ |
| 3-lane structure (BUILD · INTEGRATE · IGNORE) | ✅ |
| 5 informational waves in BUILD lane | ✅ |
| 4 informational waves + parallel architectural track in INTEGRATE lane | ✅ |
| IGNORE lane no wave structure (eliminate or never start) | ✅ |
| Doctrine cross-citations rendered per wave | ✅ |
| Operator-authorization gate enforced at every wave | ✅ |

🛑 **STOPPED.**
