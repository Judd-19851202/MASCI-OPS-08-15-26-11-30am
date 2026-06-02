# OMEGA · OPERATIONAL REALITY · CONSTITUTIONAL VIOLATION REGISTER

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design
**Purpose:** Identify recommendations that have surfaced during prior Phase 1A work or that emerge from the Reality Audit's gap analysis that — if built as commonly imagined for a construction-operations platform — would violate the Constitution. This is the **forward-looking guardrail register.**

---

## §0 · Method

For each candidate capability identified in `BUILD_FROM_SCRATCH_REGISTER.md` and the broader Reality Audit, ask:

> **"Is there a likely industry-standard implementation pattern for this capability that would violate the Constitution?"**

If yes, document the Constitutional violation, the Rule(s) impacted, and the Constitutional-compliant alternative framing (per Amendment 001 Tier-evidence hierarchy).

This register does NOT duplicate `CONSTITUTIONAL_CONFLICT_REGISTER.md` (which covers existing recommendations already in scope). It identifies **new violation risks** that would emerge if the Reality Audit gaps were addressed using construction-industry-standard patterns.

---

## §1 · Forward-violation register · 14 entries

### V-1 · Submittal "Acknowledge Receipt" pattern

* **Capability:** Submittal workflow (B-1)
* **Industry-standard violation:** Architect/owner-side "Click Acknowledge Receipt" affordance before review starts
* **Rules impacted:** Rule 1 (Work Over Clicks) · Rule 11 (Evidence Over Acknowledgement)
* **Constitutional alternative:** Submittal receipt is captured automatically on transmittal record creation (Tier 1 work-performed); review starts when reviewer assigns themselves OR system auto-assigns per Rule 7

### V-2 · RFI "Acknowledged" status step

* **Capability:** RFI workflow (B-2)
* **Industry-standard violation:** "Acknowledged" intermediate status between Submitted and Answered
* **Rules impacted:** Rule 1 · Rule 11 · Rule 2 (Information Is Not A Task)
* **Constitutional alternative:** RFI lifecycle is Submitted → Answered → Closed. The answer IS Tier 1 work. The "acknowledged" status adds no operational value.

### V-3 · Change-order multi-step approval ack chain

* **Capability:** Change-order workflow (B-3)
* **Industry-standard violation:** Each approver (PM → owner-rep → owner) clicks Acknowledge before the next can act
* **Rules impacted:** Rule 1 · Rule 8 (Reduce Operational Noise) · Rule 3 (One Owner)
* **Constitutional alternative:** Approval IS Tier 1 work (Rule 6 explicit exception); one owner at each stage; notification on stage advance only; rejection requires text reason (operational decision content)

### V-4 · Pay-application "Owner Acknowledged Receipt"

* **Capability:** Pay-application workflow (B-4)
* **Industry-standard violation:** "Owner Acknowledged Receipt" status before review
* **Rules impacted:** Rule 1 · Rule 11
* **Constitutional alternative:** Receipt captured automatically on submission; review starts when reviewer takes action; payment status is Tier 1 financial-system feedback

### V-5 · Meeting-minutes "Read and Acknowledged"

* **Capability:** Meeting-minutes capture (B-6)
* **Industry-standard violation:** Attendees click "Read and Acknowledged" after minutes distributed
* **Rules impacted:** Rule 1 · Rule 11 · Amendment 001 worked example pattern
* **Constitutional alternative:** Tier 2 attendance roster captured at meeting; action items become Tier 1 work assignments; no post-meeting ack required

### V-6 · Field clock-in "I am at the correct jobsite"

* **Capability:** Field clock-in (B-8)
* **Industry-standard violation:** Self-attestation checkbox at clock-in
* **Rules impacted:** Rule 1 · Rule 11
* **Constitutional alternative:** GPS coordinates + device + timestamp at clock-in ARE Tier 1 work-performed evidence; no self-attestation required

### V-7 · OSHA 300 log "I attest these records are accurate"

* **Capability:** OSHA 300 generator (B-15)
* **Industry-standard violation:** Annual 300A submission with company-officer "I attest" ack
* **Rules impacted:** Rule 1 (mitigated · legally required) · Rule 11
* **Constitutional alternative:** OSHA 300A IS legally required to bear a corporate-officer signature — this is the explicit Tier 4 ride-along on Tier 1 work that Amendment 001 permits. **CONSTITUTIONAL** but the ack is constrained to the legally required artifact, not to every incident record.

### V-8 · Performance review "Employee acknowledges review"

* **Capability:** Performance review workflow (B-18)
* **Industry-standard violation:** Employee clicks "I acknowledge I received my review"
* **Rules impacted:** Rule 1 · Rule 11
* **Constitutional alternative:** Review delivery captured automatically (Tier 3 access); employee response if any is Tier 1 content (text); no ack click

### V-9 · Discipline "Employee acknowledges disciplinary action"

* **Capability:** Discipline tracking (B-19)
* **Industry-standard violation:** Acknowledgement checkbox on discipline form
* **Rules impacted:** Rule 1 (mitigated · sometimes legally required) · Rule 11
* **Constitutional alternative:** Employee response if required is Tier 1 content (text statement); union/legal contexts may require signature — that signature would be the explicit Tier 4 ride-along on Tier 1 work (per Amendment 001) — operator-decision territory

### V-10 · DOT compliance "Driver acknowledges policy"

* **Capability:** DOT Compliance Dashboard (B-24)
* **Industry-standard violation:** Annual "I acknowledge driver handbook" click
* **Rules impacted:** Rule 1 · Rule 11
* **Constitutional alternative:** Drug-test result + MVR clean + DQ-file complete + DVIR submission history ARE Tier 1+2+3 evidence of compliance; no separate ack required

### V-11 · Maintenance work-order "Mechanic acknowledges assignment"

* **Capability:** Maintenance work-order system (B-21)
* **Industry-standard violation:** Mechanic clicks "I acknowledge assignment" before work begins
* **Rules impacted:** Rule 1 · Rule 7 (Accountability Must Be Automatic)
* **Constitutional alternative:** Work-order assigned by system per Rule 7; work-order completion IS Tier 1 evidence; no acknowledge-of-assignment step required

### V-12 · Subcontractor "Acknowledge scope of work"

* **Capability:** Subcontractor management (B-14)
* **Industry-standard violation:** Sub clicks "I acknowledge scope" before scope is bound
* **Rules impacted:** Rule 1 · Rule 11
* **Constitutional alternative:** Contract execution (signature on agreement) IS Tier 4 ride-along on Tier 1 contract work; no separate acknowledgement workflow

### V-13 · Executive portfolio "Acknowledge weekly KPIs"

* **Capability:** Executive portfolio view (B-11)
* **Industry-standard violation:** Executive clicks "I have reviewed this week's KPIs"
* **Rules impacted:** Rule 1 · Rule 2 (Information Is Not A Task) · anti-checklist clause
* **Constitutional alternative:** Executive surfaces are Action Consoles; consumption is Tier 3 access evidence; no separate ack required

### V-14 · "Acknowledge update to handbook" pattern

* **Capability:** Cross-cutting HR / Safety policy updates
* **Industry-standard violation:** Annual "I acknowledge handbook update" employee-wide
* **Rules impacted:** Rule 1 · Rule 11 · Amendment 001 worked Safety example
* **Constitutional alternative:** Handbook delivery captured as Tier 3 access · Tier 2 attendance at policy roll-out meeting · NO separate per-employee acknowledgement workflow

---

## §2 · Patterns observed in §1

| Pattern cluster | Items | Constitutional answer |
|---|---|---|
| **"Acknowledge receipt" before review** | V-1, V-2, V-4 | Receipt is auto-captured; review begins on action |
| **"Acknowledge assignment"** | V-11 | Assignment is per Rule 7; no separate ack |
| **"Acknowledge policy / handbook / KPIs"** | V-5, V-13, V-14 | Tier 3 access + Tier 2 attendance sufficient |
| **"Self-attestation at start of work"** | V-6 | Tier 1 evidence dominates |
| **"Multi-step approval acks"** | V-3 | Approvals are Tier 1 (Rule 6 exception); no intermediate acks |
| **"Employee acknowledges receipt of discipline/review"** | V-8, V-9 | Tier 1 content sufficient; legal-required acks ride on Tier 1 |
| **Legally-required acks (OSHA 300A, etc.)** | V-7 | Permitted Tier-4 ride-along on Tier 1 |
| **Contract execution ack** | V-12 | Permitted Tier-4 ride-along on Tier 1 |

---

## §3 · Patterns that would be Constitutionally permitted

For clarity, the following ack patterns ARE Constitutionally permitted and should not be confused with the violations above:

| Permitted pattern | Why |
|---|---|
| OSHA 300A corporate-officer signature (legally required) | Tier 4 ride-along on Tier 1 |
| Contract execution signature | Tier 4 ride-along on Tier 1 contract work |
| FSI consent text version stamping on public-gate submissions | Legally appropriate; rides on Tier 1 submission |
| Incident closure attestation modal with operational notes | Closure IS Tier 1 work · notes are Tier 1 content |
| Reopen-with-reason modal | Reason is Tier 1 operational decision content |
| Approval / rejection decisions on PO · Time Off · Pay-App | Rule 6 explicit exception · Tier 1 work-performed |

---

## §4 · Forward-binding effect

Every greenfield item in `BUILD_FROM_SCRATCH_REGISTER.md` and every external integration in `EXTERNAL_DEPENDENCY_REGISTER.md` must pass the Constitutional Test ("What operational problem is solved by requiring this acknowledgement?") before any associated ack workflow can be authorized.

The 14 violations enumerated above are the most likely places a Constitutional Test would return **NONE** during future scoping conversations.

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| Forward-looking only (does not re-rank existing conflicts) | ✅ |
| 14 forward violations catalogued with Rule citations | ✅ |
| Constitutional alternative provided per violation | ✅ |
| 8 permitted-pattern examples surfaced for clarity | ✅ |

🛑 **STOPPED.**
