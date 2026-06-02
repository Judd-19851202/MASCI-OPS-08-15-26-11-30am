# OMEGA · OPERATIONAL REALITY · PRIORITIZED ROADMAP

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates · zero authorization
**Purpose:** Prioritize the 48 gaps by operational impact (NOT by ease) per the Constitutional posture (Rule 9 Operator First).

---

## §0 · Prioritization framework

Each gap is scored on three dimensions:

| Dimension | Scale |
|---|---|
| **Operational Impact** (Rule 9) | High · Med · Low — does it block a real operational outcome? |
| **Constitutional Cleanliness** (10 Rules + Amendment 001) | High · Med · Low — can it be built Constitution-compliant? |
| **Existing-primitive Reuse** | High · Med · Low — does it consume existing primitives or require new collections? |

Within each priority bucket, ordering is by **Operational Impact first**, then by Constitutional Cleanliness, then by Existing-primitive Reuse.

---

## §1 · Priority 0 · Operationally critical (12 items)

These items block day-to-day operations or have already-live Constitutional violations.

| Rank | Item | Type | Source | Notes |
|---:|---|---|---|---|
| P0-1 | **Resolve OC-005 JHP Ack family (P0 + Rule 11)** | Constitutional re-scope | CV-1 / Amendment 001 | Eliminate or re-scope to Tier 3 identity capture · zero new collections |
| P0-2 | **Eliminate iter445 "Has crew reviewed JHP?" Yes/No field (FAIL-1)** | Constitutional remediation | Amendment 001 FAIL | Code change · separate authorization |
| P0-3 | **Decommission vestigial JHA system (FAIL-2)** | Constitutional remediation | Amendment 001 FAIL | Code change · separate authorization |
| P0-4 | **Resolve three-parallel-CA-systems pathology (Ownership P0-4)** | Constitutional re-scope | Ownership Audit | Canonical CA source; downstream others as consumers |
| P0-5 | **Layer A · ownership primitive on lifecycle records (with no-manual-assign UI guardrail)** | New capability | Ownership Audit §7 + Compliance Sweep HR-1 | Foundation for Rule 3 · auto-derived per Rule 7 |
| P0-6 | **Layer B · auto-task projection from state machine (strong Constitutional alignment per O-2)** | New capability | Ownership Audit §7 | Closes G0-11 (0/736 user-level assignment) |
| P0-7 | **Resend bounce webhook (iter452.5.2 P1 · pre-authorized)** | New capability | Pre-authorized · Rule 7 strong | Day-to-day delivery reliability |
| P0-8 | **iter453 OC-003 QA/QC follow-up with closure-action contract** | Existing-primitive completion | OPER-COMP-REG OC-003 + Amendment 001 REPLACE | Closure requires CA record OR re-inspection · not a click |
| P0-9 | **iter453 OC-004 Site Inspection follow-up with closure-action contract** | Existing-primitive completion | OC-004 + Amendment 001 REPLACE | Same pattern as P0-8 |
| P0-10 | **Field clock-in/out per employee (B-8)** | Greenfield | Reality Audit | Closes G0-7 · enables production tracking |
| P0-11 | **Subcontractor management (B-14)** | Greenfield | Reality Audit | Closes G0-9 |
| P0-12 | **Master schedule integration (EX-3) OR scheduling-consumer surface** | Integration | Reality Audit | Closes G0-2 |

---

## §2 · Priority 1 · Scalability / Executive visibility (14 items)

These items limit the company's ability to scale or expose executive-grade information.

| Rank | Item | Type |
|---:|---|---|
| P1-1 | **Executive role + login portal (B-11)** | Greenfield |
| P1-2 | **Portfolio rollup (B-11)** | Greenfield |
| P1-3 | **Per-PM accountability scorecard (B-12)** | Greenfield consumer of accountability_projection |
| P1-4 | **OSHA 300/301/300A generator (B-15)** | Greenfield consumer of incidents + safety_training_records |
| P1-5 | **Layer C · Action Console + Rule 8 escalation (with single-recipient guardrails per HR-2)** | New capability |
| P1-6 | **Accounting integration (EX-1) — dominant external dependency** | Integration |
| P1-7 | **Submittal workflow (B-1)** | Greenfield |
| P1-8 | **RFI workflow (B-2)** | Greenfield |
| P1-9 | **Change-order workflow (B-3)** | Greenfield |
| P1-10 | **Pay-application workflow (B-4)** | Greenfield |
| P1-11 | **DQ-file workflow (B-23)** | Greenfield |
| P1-12 | **DOT compliance dashboard (B-24)** | Greenfield Action Console |
| P1-13 | **`manager_employee_id` field on employees + FL users (B-20)** | Schema |
| P1-14 | **Performance review workflow (B-18)** | Greenfield |

---

## §3 · Priority 2 · Adoption / Operational clarity (15 items)

| Rank | Item | Type |
|---:|---|---|
| P2-1 | **OC-013 Onboarding multi-step re-scope to data capture per step** | Constitutional re-scope |
| P2-2 | **OC-014 Offboarding multi-step re-scope to data capture per step** | Constitutional re-scope |
| P2-3 | **PPE Return workflow (OC-008 / B-16)** | Greenfield |
| P2-4 | **Stop-work authority structured workflow (B-17)** | Greenfield |
| P2-5 | **Discipline tracking (B-19)** | Greenfield |
| P2-6 | **Production tracking by activity (B-9)** | Greenfield |
| P2-7 | **Material delivery confirmation (B-10)** | Greenfield extension of PO workflow |
| P2-8 | **Maintenance work-order system (B-21)** | Greenfield |
| P2-9 | **Equipment utilization-by-job (B-22)** | Greenfield consumer |
| P2-10 | **Lien-waiver tracking (B-5)** | Greenfield |
| P2-11 | **Meeting-minutes capture (B-6)** | Greenfield |
| P2-12 | **Project budgeting + forecast-to-complete (B-7)** | Greenfield |
| P2-13 | **Backlog / bid-pipeline tracker (B-13)** | Greenfield |
| P2-14 | **iter452.5.1 P2 Accountability Chain Projection (iter455.1 · already authorized for bundle)** | Existing-primitive completion |
| P2-15 | **Audit-trail uplift for 11 flag-only workflows (OC-018) — only items with operational consumer** | Constitutional re-scope |

---

## §4 · Priority 3 · Cosmetic / convenience (7 items)

| Rank | Item | Type |
|---:|---|---|
| P3-1 | OC-006 Safety Meeting amend | Existing completion |
| P3-2 | OC-016 Continuity Events edit/close | Existing completion |
| P3-3 | OC-017 Safety digest fire relocation (Rule 9 aligned) | Surface relocation |
| P3-4 | OC-019 Casing normalization | Cosmetic |
| P3-5 | OC-022 Reopen actions across 14 workflows | Existing completion |
| P3-6 | OC-009 Photo Janitor | Greenfield Rule 6/7 strong |
| P3-7 | Status vocabulary canonicalization (OC-010) — net-negative discipline | Existing completion |

---

## §5 · Priority Architectural · Multi-tenancy (5 items · SEPARATE TRACK)

These items are architectural and run in parallel · they do NOT improve MASCI's operational reality. They unblock Customer #2 / White-Label / Operations Center.

| Rank | Item | Type |
|---:|---|---|
| Arch-1 | `tenant_id` propagation across 141 collections | Architectural |
| Arch-2 | Multi-tenant auth + SSO/SAML/OIDC | Architectural |
| Arch-3 | Tenant onboarding wizard | Architectural |
| Arch-4 | Brand-config layer (logo + colors + brand-name + domain + PDF + email) | Architectural |
| Arch-5 | Operations Center MVP (Constitution-led from inception) | Greenfield |

---

## §6 · Roadmap shape (informational sequencing observation · NOT authorized)

Per the Constitution (Rule 9 Operator First) and Amendment 001 (Evidence Over Acknowledgement) and the Reality Audit's 35/100 verdict, the sequencing observation is:

> **Wave 1 (P0 · operationally critical):** Resolve Constitutional violations + Ownership v1 Layers A + B + close Phase 1A friction. Brings platform to ~50/100.
>
> **Wave 2 (P1 · executive + PM + integration):** Build Executive role + PM workflows + accounting integration + DQ/DOT compliance. Brings platform to ~70/100.
>
> **Wave 3 (P2 · adoption + ops completion):** Close remaining lifecycle gaps + maintenance + production tracking + lien waivers. Brings platform to ~85/100.
>
> **Wave 4 (Arch · multi-tenancy):** Tenant rebuild + brand-config + Operations Center MVP. Unblocks Customer #2 (~90/100 with multi-tenant operability).
>
> **Wave 5 (P3 · polish):** Cosmetic / convenience items.

This is sequencing observation. **No wave is authorized.** Operator selects pace and prioritization.

---

## §7 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| Zero estimates produced | ✅ |
| Zero implementation plans | ✅ |
| Zero authorization implied | ✅ |
| 48 gaps prioritized across 4 priority buckets + 1 architectural track | ✅ |
| Operational Impact framing per Rule 9 applied | ✅ |
| Constitutional re-scopes called out where applicable | ✅ |
| Sequencing observation (Waves 1–5) rendered as informational only | ✅ |

🛑 **STOPPED.** Roadmap delivered. Await operator direction.
