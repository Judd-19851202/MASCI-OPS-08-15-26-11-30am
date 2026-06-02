# OMEGA · CUSTOMER #2 READINESS REALITY ANALYSIS

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design
**Companion to existing:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §5 Customer #2 Score (23/90) · `CUSTOMER2_BLOCKER_MATRIX.md`

---

## §0 · Framing change

Prior Customer #2 readiness analyses scored the platform's *architectural* readiness (tenant isolation · brand config · SSO · onboarding wizard). The current Reality Audit asks a different question: **"Could MASCI's operational reality even be replicated for a second customer if multi-tenancy were solved?"**

This document answers the broader question.

---

## §1 · Two-dimension assessment

### Dimension 1 · Architectural readiness (existing — unchanged from prior audits)

23 / 90 🔴 per `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §5. The blockers are:
* No `tenant_id` propagation across 141 collections
* No multi-tenant auth / SSO / SAML / OIDC
* No tenant-onboarding wizard
* Brand strings hard-coded
* PDF templates hard-coded
* Hard-coded MASCI domain references in QR posters / emails

Estimated 10 weeks of platform work to remediate (independent of this audit).

### Dimension 2 · Operational replicability (new — this audit)

Even if multi-tenancy were solved tomorrow, **Customer #2 inherits the same 65 % operational shortfall MASCI has today** (per `COMPANY_OPERABILITY_SCORECARD.md` 35/100 aggregate). The Reality Audit's evidence:

| Area | MASCI today | Customer #2 (post tenant-rebuild, if everything else stayed identical) |
|---|---|---|
| Executive | 🔴 12/100 | 🔴 12/100 — same gap |
| Operations | 🟠 40/100 | 🟠 40/100 — same gap |
| Project Management | 🟠 34/100 | 🟠 34/100 — same gap |
| Field Operations | 🟡 56/100 | 🟡 56/100 — same gap |
| Safety | 🟡 51/100 | 🟡 51/100 — same gap |
| HR | 🟠 36/100 | 🟠 36/100 — same gap |
| Equipment | 🟠 40/100 | 🟠 40/100 — same gap |
| Fleet | 🟠 36/100 | 🟠 36/100 — same gap |
| Financial Operations | 🔴 20/100 | 🔴 20/100 — same gap |

**Customer #2 cannot run their company entirely inside ForgedOps today for the same reason MASCI cannot.** The operational shortfall is not MASCI-specific.

---

## §2 · Customer #2 onboarding readiness — combined verdict

| Dimension | Score | Verdict |
|---|---:|---|
| Architectural (tenant + brand + SSO + wizard) | 23 / 90 | 🔴 NOT READY |
| Operational replicability (workflows + lifecycle + ownership + executive) | 35 / 100 | 🔴 NOT READY |
| Constitutional posture (Constitution + Amendment 001 cleanliness) | 67 / 100 | 🟡 PARTIAL READY |
| **AGGREGATE (weighted: 33 % arch · 50 % op · 17 % constitutional)** | **~36 / 100** | 🔴 **NOT READY** |

---

## §3 · Per-blocker tier analysis

### Tier 1 blockers (cannot ship Customer #2 without these)

| # | Blocker | Source |
|---:|---|---|
| T1-1 | `tenant_id` propagation across 141 collections | Architectural |
| T1-2 | Multi-tenant auth | Architectural |
| T1-3 | Tenant-onboarding wizard | Architectural |
| T1-4 | Brand-config layer (logo · color · brand-name · domain) | Architectural |
| T1-5 | PDF template registry per tenant | Architectural |
| T1-6 | Email subject + sender tokenization per tenant | Architectural |
| T1-7 | Resolution of OC-005 Constitutional violation BEFORE Customer #2 inherits it | Operational + Constitutional |

### Tier 2 blockers (Customer #2 will report the same operational complaints MASCI has)

| # | Blocker | Source |
|---:|---|---|
| T2-1 | No executive role / portfolio view | Operational |
| T2-2 | No PM workflows (Submittal/RFI/CO/Pay-App) | Operational |
| T2-3 | No job-cost integration | External dependency |
| T2-4 | Three parallel CA systems | Operational + Constitutional |
| T2-5 | 0/736 user-level task assignment | Operational + Constitutional |
| T2-6 | OC-014 / OC-013 multi-step lifecycle incomplete | Operational + Constitutional |
| T2-7 | OSHA 300/301 generator absent | Operational |

### Tier 3 blockers (Customer #2 can ship with workarounds)

| # | Blocker | Source |
|---:|---|---|
| T3-1 | DOT compliance dashboard absent | Operational |
| T3-2 | DQ-file workflow absent | Operational |
| T3-3 | Performance review / discipline / benefits workflows absent | Operational |
| T3-4 | Maintenance work-order system absent | Operational |
| T3-5 | Subcontractor management absent | Operational |

---

## §4 · Operator decision matrix

| Path | Customer #2 outcome |
|---|---|
| (A) **Ship Customer #2 as-is post-tenant-rebuild** (10 weeks) | Customer #2 inherits all 48 gaps from Reality Audit · same operational shortfall as MASCI · same Constitutional violations (OC-005 ack pattern · etc.) — high risk of customer churn within first 6 months |
| (B) **Close Phase 1A Constitutional issues + Ownership v1 BEFORE tenant rebuild** (~6 weeks platform + 10 weeks tenant) | Customer #2 inherits a stronger, Constitution-clean platform · 35→55 operability score; still missing PM workflows + executive surfaces |
| (C) **Close Phase 1A + Phase 1B + Executive role BEFORE tenant rebuild** (~14 weeks platform + 10 weeks tenant) | Customer #2 inherits 65+ operability score · still missing PM workflows + Financial integration |
| (D) **Close PM workflows + accounting integration BEFORE tenant rebuild** (~24 weeks total) | Customer #2 inherits 75+ operability score · ForgedOps becomes a marketable construction-ops platform |
| (E) **Defer Customer #2 indefinitely** · focus on MASCI operability | No platform pressure to compromise Constitutional posture for tenant readiness |

🛑 None authorized. Operator decision required.

---

## §5 · Sequencing observation

Per the Constitutional Compliance Sweep (67/100) and the Reality Audit (35/100), **launching Customer #2 on the current platform would replicate every Constitutional and operational liability across a second tenant**, multiplying remediation cost when both customers eventually demand fixes.

The Constitutionally and operationally disciplined sequence is:

> **(1) Fix MASCI → (2) Strengthen platform → (3) Add multi-tenancy → (4) Onboard Customer #2**

Reversing this sequence (multi-tenancy first) has the cost-multiplication property described above.

---

## §6 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Prior Customer #2 architecture score preserved verbatim (23/90) | ✅ |
| New operational replicability dimension added (not a re-score) | ✅ |
| Tier 1 / Tier 2 / Tier 3 blockers explicit | ✅ |
| 5 operator-decision paths rendered (none authorized) | ✅ |
| Sequencing observation derived from Constitution + Amendment 001 + Operational Reality | ✅ |

🛑 **STOPPED.**
