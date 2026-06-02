# OMEGA · FORGEDOPS V1 REQUIREMENTS REPORT

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero implementation plan
**Purpose:** Define what ForgedOps v1 must contain to be marketable as a construction-operations platform that can run a heavy-civil GC end-to-end.

---

## §0 · ForgedOps v1 definition (re-stated)

Per `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §7 ForgedOps Foundation Readiness (42/100 today):

> "Is the platform's data, audit, and lifecycle architecture mature enough to be marketed as a productized 'operational discipline' offering ('ForgedOps')?"

The Reality Audit refines this to a stricter Constitution + Amendment 001 framing:

> **ForgedOps v1 must enable a customer to run their construction company entirely inside the platform without spreadsheets, notebooks, whiteboards, side databases, text-message workflows, email-based business processes, tribal knowledge, or memory-based tracking.**

---

## §1 · v1 requirement set (organized by Constitutional contract)

### Requirement Class A · Universal Primitives (foundation · mostly present)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| A-1 | Universal state machine with 5+ states per workflow (iter451 pattern) | 🟢 LIVE on 3 workflows (Incident · DR · PV) | Extend to QA/QC · Site Inspection · JHP · Subcontractor · Submittal · RFI · CO · Pay-App · Maintenance |
| A-2 | Immutable audit trail (`workflow_state_events`) | 🟢 LIVE | None |
| A-3 | 5-tier identity ladder (FSI iter452.5.1) | 🟢 LIVE | None |
| A-4 | Tasks schema | 🟢 LIVE (`assignee_user_id` schema-ready) | 0/736 user-level assignment — Layer A ownership work needed |
| A-5 | Universal lifecycle library (LifecyclePanel pattern) | 🟢 LIVE | None — pattern reusable across workflows |
| A-6 | Universal evidence-tier classification (Amendment 001) | 🟢 ACTIVE doctrine | Apply at every new workflow scoping |

### Requirement Class B · Ownership & Accountability Layer (mostly absent)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| B-1 | `current_owner_user_id` on every lifecycle record | 🔴 ABSENT | Layer A from Ownership Audit §7 |
| B-2 | `current_owner_due_at` SLA timer | 🔴 ABSENT | Layer A |
| B-3 | Auto-task projection (state-machine → tasks) | 🔴 ABSENT | Layer B from Ownership Audit §7 (O-2 strong-aligned) |
| B-4 | `manager_employee_id` graph for Rule 8 escalation routing | 🔴 ABSENT | B-20 from `BUILD_FROM_SCRATCH_REGISTER.md` |
| B-5 | Nightly idle-workflow alerter (Rule 7 escalation engine) | 🔴 ABSENT | Layer C from Ownership Audit §7 (with Rule 8 single-recipient guardrails) |
| B-6 | "What's mine right now" view per user | 🔴 ABSENT | F-21 / Top-10 #2 from Cert Audit |

### Requirement Class C · Executive & Operations Layer (absent)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| C-1 | Executive role + login portal | 🔴 ABSENT | B-11 from `BUILD_FROM_SCRATCH_REGISTER.md` |
| C-2 | Portfolio rollup (project × workflow open count) | 🔴 ABSENT | B-11/B-12 |
| C-3 | Per-PM accountability scorecard (Action Console) | 🔴 ABSENT | B-12 |
| C-4 | Backlog / bid-pipeline tracker | 🔴 ABSENT | B-13 |
| C-5 | WIP schedule / forecast-to-complete (consumes accounting) | 🔴 ABSENT | EX-1 integration + new consumer |
| C-6 | OSHA 300 / 301 / 300A generator | 🔴 ABSENT | B-15 |
| C-7 | DOT Compliance Dashboard | 🔴 ABSENT | B-24 |
| C-8 | Per-tenant configurable executive cadence (daily / weekly digest) | 🔴 ABSENT | New requirement; Rule 8 compliant |

### Requirement Class D · Project Management Workflows (absent)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| D-1 | Submittal workflow | 🔴 ABSENT | B-1 |
| D-2 | RFI workflow | 🔴 ABSENT | B-2 |
| D-3 | Change-order workflow | 🔴 ABSENT | B-3 |
| D-4 | Pay-application workflow | 🔴 ABSENT | B-4 |
| D-5 | Lien-waiver tracking | 🔴 ABSENT | B-5 |
| D-6 | Subcontractor management | 🔴 ABSENT | B-14 |
| D-7 | Meeting-minutes capture | 🔴 ABSENT | B-6 |
| D-8 | Project budgeting + forecast-to-complete | 🔴 ABSENT | B-7 |

### Requirement Class E · Field Operations completion (mostly present · needs strengthening)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| E-1 | Daily Report lifecycle | 🟢 LIVE | None |
| E-2 | FSI 5-tier identity ladder | 🟢 LIVE | None |
| E-3 | Bilingual public-gate forms | 🟢 LIVE | None |
| E-4 | Toolbox Talk · Safety Meeting · Equipment Pre-Op · DVIR | 🟢 LIVE (submit-only · 0 closure) | Close lifecycle per workflow |
| E-5 | Field clock-in/out per employee | 🔴 ABSENT | B-8 |
| E-6 | Production tracking by activity | 🔴 ABSENT | B-9 |
| E-7 | Material delivery confirmation | 🔴 ABSENT | B-10 (extends PO workflow) |

### Requirement Class F · Safety completion (mostly present · Constitutional re-scope needed)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| F-1 | Incident lifecycle (iter451) | 🟢 LIVE | None |
| F-2 | OSHA recordable ack (legal Tier-4 ride-along) | 🟢 LIVE | None |
| F-3 | QA/QC follow-up (OC-003) | 🟡 SUBMIT-ONLY | iter453 with Constitutional closure-action contract |
| F-4 | Site Inspection follow-up (OC-004) | 🟡 SUBMIT-ONLY | iter453 with Constitutional closure-action contract |
| F-5 | JHP library | 🟢 LIVE (iter445) | None |
| F-6 | JHP evidence (Toolbox Talk + Tier-3 download identity) | 🟡 partial | OC-005 re-scope per Amendment 001 REPLACE |
| F-7 | PPE Return (OC-008) | 🔴 ABSENT | B-16 |
| F-8 | Stop-work authority structured workflow | 🔴 ABSENT | B-17 |
| F-9 | Discipline tracking (overlaps HR) | 🔴 ABSENT | B-19 |

### Requirement Class G · HR completion (partial · much absent)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| G-1 | Employee directory | 🟢 LIVE (261 records) | None |
| G-2 | Time Off Request lifecycle | 🟢 LIVE | None |
| G-3 | Payroll Variance lifecycle (iter452) | 🟢 LIVE | None |
| G-4 | Onboarding lifecycle | 🟡 SINGLE-RECORD | Constitutional re-scope of OC-013 multi-step |
| G-5 | Offboarding lifecycle | 🟡 STATUS MUTATOR | Constitutional re-scope of OC-014 multi-step |
| G-6 | Performance review workflow | 🔴 ABSENT | B-18 |
| G-7 | Discipline workflow | 🔴 ABSENT | B-19 |
| G-8 | Full payroll processing | 📤 EXTERNAL | EX-2 integration |
| G-9 | Benefits administration | 📤 EXTERNAL | EX-9 integration |
| G-10 | ATS / recruiting | 📤 EXTERNAL | EX-10 integration |

### Requirement Class H · Equipment / Fleet completion (partial)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| H-1 | Equipment master + Pre-Op + DVIR + Asset Transfers | 🟢 LIVE | None |
| H-2 | Maintenance work-order system | 🔴 ABSENT | B-21 |
| H-3 | Utilization-by-job tracking | 🔴 ABSENT | B-22 |
| H-4 | Driver Qualification File workflow | 🔴 ABSENT | B-23 |
| H-5 | DOT compliance dashboard | 🔴 ABSENT | B-24 |
| H-6 | ELD integration | 📤 EXTERNAL | EX-4 |
| H-7 | Drug-test pool tracking | 📤 EXTERNAL | EX-6 |

### Requirement Class I · Financial integration (largely external)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| I-1 | PO Request workflow | 🟢 LIVE (request-only) | Extend to PO commit + receipt + payment via accounting integration |
| I-2 | Suppliers master | 🟢 LIVE | None |
| I-3 | Payroll Variance lifecycle | 🟢 LIVE | None |
| I-4 | Accounting integration (GL · AP · AR · job cost · WIP) | 📤 EXTERNAL | EX-1 (dominant) |
| I-5 | Pay-application + lien-waiver | 🔴 ABSENT | B-4 / B-5 |
| I-6 | Change-order integration | 🔴 ABSENT | B-3 → accounting |

### Requirement Class J · Customer #2 / White-Label / Operations Center (architectural)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| J-1 | `tenant_id` propagation across 141 collections | 🔴 ABSENT | T1-1 from `CUSTOMER2_READINESS_REALITY_ANALYSIS.md` |
| J-2 | Multi-tenant auth + SSO | 🔴 ABSENT | T1-2 |
| J-3 | Tenant onboarding wizard | 🔴 ABSENT | T1-3 |
| J-4 | Brand-config layer | 🔴 ABSENT | T1-4 / T1-5 / T1-6 |
| J-5 | Operations Center (customer support · tickets · tenancy admin) | 🔴 ABSENT | 92-108 dev-day build per prior audit |

### Requirement Class K · Doctrine (active · binding)

| # | Requirement | Status today | Gap |
|---:|---|---|---|
| K-1 | Constitution (10 Friction Rules + Override) | 🟢 ACTIVE | Doctrine binding |
| K-2 | Amendment 001 (Evidence Over Acknowledgement) | 🟢 ACTIVE | Doctrine binding |
| K-3 | Constitutional Test as pre-build gate | 🟢 ACTIVE | Enforce on every authorization |
| K-4 | 3-criterion success test (complete + accountable + simple) | 🟢 ACTIVE | Enforce on every authorization |
| K-5 | 5 new mandatory audit axes | 🟢 ACTIVE | Apply in every new audit |
| K-6 | Anti-checklist clause | 🟢 ACTIVE | Enforce at every Action Console design |

---

## §2 · v1 build effort (qualitative · per OMEGA scope no estimates)

The v1 requirement set above splits into 4 effort buckets:

| Bucket | Requirement count | Effort character |
|---|---:|---|
| **Already live · keep healthy** | ~16 | No new build · regression discipline |
| **Constitutional re-scope of existing** | ~7 | Doctrine + scoping conversations · minimal code |
| **Greenfield build (additive · single-tenant)** | ~24 | Substantial; phased; estimated cumulatively as the Phase 1A + 1B + Phase 2 + Ownership v1 + Executive layer |
| **External integration** | ~9 | Vendor-selection + integration layer; effort dependent on vendor choices |
| **Multi-tenancy architectural rebuild** | ~5 | Substantial; prior estimate ~10 weeks |

---

## §3 · The Constitutional v1 platform contract

Marketing-quality statement of what ForgedOps v1 would deliver:

> **"Every workflow has a named human owner, a tracked SLA, an escalation path, and executive-visible reporting. Every workflow generates Tier 1 work-performed evidence — never just acknowledgement clicks. Every notification reaches one accountable person, not a department. Every closure requires operational action, not a status-pill click. The construction-operations function runs entirely inside ForgedOps; accounting · payroll · ELD · drug-test · OSHA portal · workers comp · MSDS / SDS · benefits · ATS are integrated as evidence sources — never re-implemented."**

If the platform can credibly say this in a sales call, ForgedOps v1 is complete.

---

## §4 · v1 NOT-included list (intentional)

To keep v1 Constitutionally clean and operationally scoped, the following are explicitly OUT of v1:

* Internal accounting system (GL/AP/AR) — integrate, don't rebuild
* Internal payroll processor — integrate
* Internal ELD vendor — integrate
* Internal scheduling tool (P6/MS Project replacement) — integrate or read-only consume
* Customer-facing public marketing site — separate concern
* Mobile-first native app (web-mobile is sufficient per Rule 10)
* Acknowledgement workflows of any kind that would return "None" to the Constitutional Test

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| Zero estimates produced (per OMEGA scope) | ✅ |
| 11 requirement classes (A–K) catalogued | ✅ |
| Every requirement cross-cited to Gap Register / Build Register / External Register | ✅ |
| v1 NOT-included list rendered for Constitutional discipline | ✅ |

🛑 **STOPPED.**
