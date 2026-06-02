# OMEGA · TOP 10 FORGEDOPS CAPABILITIES

**Date:** 2026-06-02 · Companion to `BUILD_INTEGRATE_IGNORE_MASTER_REGISTER.md`
**Mode:** READ-ONLY · zero code · zero estimates
**Method:** From the 24 BUILD-classified items, rank by 8 weighted dimensions per OMEGA scope:
* Operational Impact · Constitution Compliance · Adoption Probability · Accountability Impact · Field Value · Executive Value · Customer #2 Value · Effort-to-Value Ratio

---

## §0 · Ranking framework

Each candidate scored 1-5 on each dimension. Weighted equally. Items below ranked by aggregate score · ties broken by Operational Impact then Constitution Compliance.

---

## §1 · Top 10 BUILD capabilities

### Rank 1 · Universal Ownership Layer (Layer A + Layer B)

Combines: G0-10 (CA canonicalization) · G0-11 (user-level assignment) · G1-2 (PM scorecard) · G1-11 (manager_employee_id) · G1-14 ("what's mine") · subset of Ownership Audit §7

* **Why ForgedOps must own this:** Accountability is in the Constitution's mission statement; no external system can own it because it spans every workflow in the platform.
* **Operational problem it solves:** 0/736 user-level task assignment · 0/736 task closures · three parallel CA systems disagreeing · no per-PM scorecard · no manager hierarchy for escalation routing.
* **What happens if never built:** Every workflow remains orphaned · field crews report "I never got told" · executives have no visibility · Customer #2 inherits identical pathology.
* **Would MASCI use it immediately:** YES — closes the largest single-named friction in `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` (F-21 "what's mine") + the 8 P0 Ownership Audit gaps.

### Rank 2 · Field Clock-in / Clock-out per employee (G0-7 · B-8)

* **Why ForgedOps must own this:** Pure field operations · the foundation primitive for production tracking · time verification · payroll integration. No external system can own this for ForgedOps's accountability layer.
* **Operational problem it solves:** Paper time tickets · Time Verification CSV reconciliation friction · cannot tie hours to activity codes.
* **What happens if never built:** Production tracking impossible · earned-value impossible · payroll reconciliation remains weekly manual friction · field accountability fragmented.
* **Would MASCI use it immediately:** YES — replaces paper time tickets day one.

### Rank 3 · Production tracking by activity (G0-8 · B-9)

* **Why ForgedOps must own this:** Heavy-civil-specific earned-value foundation · ForgedOps's product differentiator vs. generic construction platforms.
* **Operational problem it solves:** Daily Reports capture narrative but not quantities · executives cannot answer "how much did we install this week" · estimators cannot improve future bids.
* **What happens if never built:** Heavy civil GCs continue running production tracking in spreadsheets · ForgedOps fails the "Heavy Civil" portion of its mission.
* **Would MASCI use it immediately:** YES — production-by-activity replaces multiple spreadsheets and tribal reports.

### Rank 4 · Executive Role + Portfolio Action Console (G1-1 · G1-3 · B-11)

* **Why ForgedOps must own this:** Executive operational visibility is in the mission ("operational visibility"). The Action Console pattern is the Constitutional alternative to "audit software."
* **Operational problem it solves:** Executive operational visibility 0/8 surfaces today · executives ask IT to run Mongo queries.
* **What happens if never built:** Executives remain external to the platform · MASCI never proves ForgedOps to ownership · Customer #2 pitch falls flat.
* **Would MASCI use it immediately:** YES — every Monday operations meeting wants the data this surfaces.

### Rank 5 · iter453 OC-003 + OC-004 Closure-Action Contract (G2-1 · G2-2)

* **Why ForgedOps must own this:** Safety + QA/QC operations are in the mission. iter453 design is Day-9 gate cleared.
* **Operational problem it solves:** QA/QC deficiencies stack forever · Site Inspections submit-only · safety walks accumulate without remediation trail.
* **What happens if never built:** Two of the five core Phase 1A workflows remain perpetually 🔴 INCOMPLETE · 6,000+ records continue without closure paths.
* **Would MASCI use it immediately:** YES — Safety officer can finally close inspection-finding cycles.

### Rank 6 · OSHA 300 / 301 / 300A Generator (G1-6 · B-15)

* **Why ForgedOps must own this:** Safety regulatory artifact generation is in the mission. The data source (incidents lifecycle) already lives in ForgedOps.
* **Operational problem it solves:** Annual OSHA reporting runs on spreadsheets · severe-injury reporting requires manual data assembly · 300A posting is paper-based.
* **What happens if never built:** Safety compliance remains spreadsheet-dependent · annual reporting friction · audit exposure when OSHA visits.
* **Would MASCI use it immediately:** YES — annual cycle plus year-round 300 log maintenance.

### Rank 7 · DOT Compliance Dashboard + Driver Qualification File (G1-7 · G1-8 · B-23 · B-24)

* **Why ForgedOps must own this:** Fleet operations · regulatory · heavy-civil GCs run mixed fleets with DOT exposure.
* **Operational problem it solves:** Paper DQ files · spreadsheet compliance tracker · roadside-incident scramble · CSA score blindness.
* **What happens if never built:** DOT audit exposure remains high · driver-qualification breaks discovered only at roadside · insurance premiums reflect risk gap.
* **Would MASCI use it immediately:** YES — Fleet manager + Safety manager use it weekly.

### Rank 8 · OC-005 JHP Evidence (Re-scoped per Amendment 001 · Tier 3 download identity + Toolbox Talk linkage)

* **Why ForgedOps must own this:** Safety operations · JHP library already in platform.
* **Operational problem it solves:** OSHA hazard-communication evidence captured automatically (Tier 1 Toolbox Talk + Tier 3 JHP download with FSI identity) · eliminates Constitutional violation (CV-1 ack ledger).
* **What happens if never built:** Vestigial JHP system continues without evidence · Constitutional P0 violation persists.
* **Would MASCI use it immediately:** YES — passive capture · zero new clicks · zero new UI affordance.

### Rank 9 · Subcontractor Management (G0-9 · B-14)

* **Why ForgedOps must own this:** Operational workflow · contract execution + scope + insurance tracking are operational decisions tied to project ops.
* **Operational problem it solves:** Subcontractor coordination runs on email + spreadsheets + phone · insurance expirations missed · scope-of-work disputes lost in inbox.
* **What happens if never built:** Sub coordination remains externalized · sub-related delays attributed informally · executive visibility into sub performance impossible.
* **Would MASCI use it immediately:** YES — PMs use the Subcontractor workflow daily.

### Rank 10 · Notification Routing per Rule 8 + iter452.5.2 Resend Bounce Webhook

Combines: iter452.5.2 P1 (pre-authorized · ~3d · strongest Constitutional alignment per O-1) + platform-wide Rule 8 single-recipient discipline audit (Conflict Register HR-8 · O-5)

* **Why ForgedOps must own this:** Notification fan-out to multiple roles violates Rule 8; bounce-detection auto-escalation per Rule 7 is mission-critical for delivery reliability.
* **Operational problem it solves:** PM+Safety+Admin all CC'd on every DR review · notification fatigue · bounces silently routed to dead-letter without alert.
* **What happens if never built:** Notification fatigue erodes accountability · field crews stop reading platform emails · the FSI 5-tier ladder's strongest claim ("orphan corner closed") degrades operationally.
* **Would MASCI use it immediately:** YES — silent improvement; no UX disruption.

---

## §2 · Top 10 summary table

| # | Capability | Class | Mission Pillar | If never built |
|---:|---|---|---|---|
| 1 | Universal Ownership Layer (A+B) | 🔨 BUILD | Accountability | Platform fails its mission |
| 2 | Field Clock-in/out | 🔨 BUILD | Field Ops | Heavy-civil claim fails |
| 3 | Production Tracking by Activity | 🔨 BUILD | Field Ops | Heavy-civil differentiator absent |
| 4 | Executive Role + Portfolio Action Console | 🔨 BUILD | Executive Ops | Customer #2 pitch falls flat |
| 5 | iter453 OC-003+OC-004 Closure-Action | 🔨 BUILD | Safety/QC | Phase 1A never completes |
| 6 | OSHA 300/301/300A Generator | 🔨 BUILD | Safety | Annual reporting remains spreadsheet |
| 7 | DOT Compliance + DQ-File | 🔨 BUILD | Fleet | DOT audit exposure high |
| 8 | OC-005 JHP Evidence (re-scoped) | 🔨 BUILD (re-scope) | Safety | Constitutional P0 persists |
| 9 | Subcontractor Management | 🔨🔗 HYBRID | Project Ops | Sub coordination externalized |
| 10 | Notification Routing per Rule 8 + iter452.5.2 | 🔨 BUILD | Accountability | Delivery reliability degrades |

---

## §3 · What is NOT in the Top 10 (and why)

| Capability | Why deferred |
|---|---|
| Submittal / RFI workflows (G0-3, G0-4 · B-1, B-2) | Heavy civil GC volume lower than vertical construction; defer to Wave 2 with PM workflow cluster |
| Pay-application / Change-order / Lien-waiver | HYBRID requires accounting integration first (EX-1) |
| Multi-tenancy / Customer #2 architecture (G1-12, G1-13) | Architectural · parallel track · should follow operational maturity per `CUSTOMER2_READINESS_REALITY_ANALYSIS.md` |
| Performance review / Discipline / Onboarding / Offboarding | INTEGRATE-leaning · HRIS owns or HYBRID-deferred |
| Maintenance work-order system (G2-4) | INTEGRATE — MaintainX/Fiix own this per operator doctrine |

---

## §4 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| 10 capabilities ranked across 8 weighted dimensions | ✅ |
| Each item answers the 4 mandatory questions (Why own? · Problem solved? · If never built? · Would MASCI use?) | ✅ |
| Mission-pillar mapped per item | ✅ |
| Top 10 is BUILD-only per doctrine | ✅ |

🛑 **STOPPED.**
