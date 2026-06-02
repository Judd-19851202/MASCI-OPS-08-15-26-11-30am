# ITER501 · TOP 10 NEXT SPRINTS

**Date**: 2026-06-02T21:12 UTC
**Mode**: READ-ONLY recommendation
**Authority**: OMEGA ITER501

Ranked by composite of value × impact × user experience × Customer #2 readiness × risk × effort. Each sprint is sized to fit in **1 calendar week** of focused single-developer work unless noted.

---

## Sprint 1 · 🟢 RANK #2 — Reopen out of kebab + Constraint LifecyclePanel
**Effort**: ≤ 1 week · **Risk**: low · **LOC**: ≤ 150 total
**What**: Promote `Reopen` to a top-level button on Incident detail · QA/QC detail · Site Inspection detail · Constraint detail. Reuse the existing `LifecyclePanel` substrate already on QA/QC.
**Why first**: 4 of the Top 25 closed in one cohesive design pass · pattern proven on QA/QC · zero backend changes · zero schema · no auth · single-file-each profile · highest ROI per developer-hour available.
**Closes**: Top 25 issues #3, plus discoverability gains on 3 lifecycle modules · plus Rank #2 + Rank #22 from the recommendation order.

---

## Sprint 2 · 🟢 RANK #3 — Approve / Reject out of dropdowns
**Effort**: ≤ 1 week · **Risk**: low–medium · **LOC**: ≤ 250 total
**What**: Promote `Approve` / `Reject` from row-action dropdowns to top-level buttons on Dispatch · PO Requests · Time-off. Add required `reason` field on PO Reject. Replace Time-off checkbox with explicit Approve / Reject buttons + toast.
**Why next**: 8 of the Top 25 discoverability failures resolved in one pass · PM / Dispatch / Payroll happiness · zero backend changes · payment-adjacent module (PO) gets the auditability fix.
**Closes**: Top 25 issues #2, #15, #18.

---

## Sprint 3 · 🟢 Quick-Wins Sweep
**Effort**: ≤ 1 week · **Risk**: low · **LOC**: ≤ 400 across 8–10 files
**What**: Bundle all ITER501 Quick-Wins < 4 hours each:
* Dispatch drag-drop toast
* JHA poster toast duration
* Disabled-button tooltips
* Driver-qual expiring-soon badge
* Notifications digest save banner
* Asset-transfer Receive verb
* PM Crew Compliance promoted in PmHub
* Audit-log filter chip-stack
**Why next**: Highest absolute frequency of user-pain reduction per LOC · 8 separate ROI≥7 wins · zero risk · psychological "platform got tighter" effect.
**Closes**: Top 25 issues #14, #16, #17, #19, #21, #24, plus 4–5 secondary friction items.

---

## Sprint 4 · 🟢 Hub Re-Grouping + AdminHub Re-Grouping
**Effort**: ≤ 1 week · **Risk**: low · **LOC**: ≤ 300 total
**What**: Group `Hub.jsx` (587 lines) by role-relevance (Daily / Compliance / People / Equipment / Procurement). Group `AdminHub.jsx` (133 lines · alphabetical) by category (Governance · Imports · Notifications · Webhooks · Audit). Promote PM Crew Compliance.
**Why next**: Daily-touch surface for every user. Hub.jsx is the platform's front door — re-grouping changes every user's perception of the product in one PR.
**Closes**: Top 25 issue #20, #21.

---

## Sprint 5 · 🟢 Reactivate/Rehire merged dialog + 5-statuses cleanup
**Effort**: ≤ 1 week · **Risk**: medium (HR doctrine sensitive) · **LOC**: ≤ 150 + doctrine note
**What**: Single dialog with explicit "Rehire (resets dates · creates new employment record)" vs "Reactivate (preserves dates · resumes existing employment)" radio. Audit the 5 "not currently working" statuses (Inactive / Suspended / LoA / Terminated / Resigned) and either merge or write clear in-app guide.
**Why next**: HR pain · governance-sensitive · doctrine update needed alongside code change.
**Closes**: Top 25 issues #5, #8, plus FRICTION #4, #2, #3.

---

## Sprint 6 · 🟢 Verb Harmonization Pass
**Effort**: ≤ 1 week · **Risk**: low (string-only) · **LOC**: ~ 300 across many files
**What**: Platform-wide string sweep. Adopt doctrine:
* **Submit** = transactional one-shot (Daily Report, Incident, Inspection)
* **Save** = ongoing edit (HR Lifecycle, Profile, Settings)
* **Create** = new record from scratch (rare; usually replaced by Submit or Save)
* **File** = (deprecated; replace with Submit)
* **Send** = transmission-explicit (Email Digest, Notify)
**Why next**: Closes the #1 friction item · cosmetic but high-frequency · zero schema impact.
**Closes**: Top 25 issue #6, plus FRICTION #1 · cross-platform polish.

---

## Sprint 7 · 🟢 Sub/Vendor archive workflow
**Effort**: ≤ 1 week · **Risk**: low–medium (backend mutation) · **LOC**: ≤ 200 (FE) + small BE handler
**What**: Add `Archive Sub/Vendor` button on Sub/Vendor detail. Backend handler sets `is_archived` + `archived_at` + `archived_by`. List page gets Active / Archived filter chip. Restore action on archived detail.
**Why next**: Closes one of the most-reported missing workflows · cleans up procurement governance · simple backend write.
**Closes**: Top 25 issue #23.

---

## Sprint 8 · 🟢 Universal Undo / Status Reversal Verb
**Effort**: 2 weeks · **Risk**: medium–high (cross-module data model decisions) · **LOC**: ~ 400 + audit-log integration
**What**: Add an `Undo Last Status Change` verb (and a 30-day TTL) to every lifecycle-bearing record. Backend writes a "reverse" status_history entry; UI exposes "Undo" only when actor + record allow. Audit-log captures the undo.
**Why next**: Closes the #4 Top 25 issue + frustration-driver "I made a mistake, now what?" · meaningful trust-builder.
**Closes**: Top 25 issue #4, plus eliminates a class of "backend ticket required" support calls.

---

## Sprint 9 · 🟡 OC-005 JHP Acknowledgement Ledger build (iter454)
**Effort**: 2–3 weeks · **Risk**: medium (new module, backend + schema + UI) · **LOC**: ~ 800
**What**: Ship the iter454 backlog item. New collection `jhp_acknowledgements`, signature capture, audit-log integration, expiration / re-acknowledge cadence, HR queue integration, Reopen path.
**Why now**: It's the #1 Tier-1 dead-end on the ITER500 register · Safety asks for it · compliance value · big visible build.
**Closes**: Top 25 issue #1.

---

## Sprint 10 · 🟡 Customer #2 Readiness Phase A — Brand Parameterization
**Effort**: 2 weeks · **Risk**: medium · **LOC**: ~ 400 + env / config
**What**: Parameterize the customer's brand throughout the UI: logo, page titles, email templates, PDF templates, MFA issuer, browser title, favicon, SEO meta. Introduce a `tenant_brand` config (single-tenant for now; multi-tenant later). Document what is still hard-coded.
**Why now**: Last sprint of the recommended 10-sprint arc — this is the bridge to the Customer #2 / White Label conversation. After Sprint 10 the operator can credibly demo a "your-brand-here" preview to a prospect.
**Closes**: 4 of the ~10 Customer #2 hard blockers · 4 of the ~15 White Label hard blockers.

---

## Composite arc

| Sprint | Theme | Top 25 closed (cumulative) |
|--:|---|---:|
| 1 | Rank #2 (Reopen + Constraint LifecyclePanel) | 4 |
| 2 | Rank #3 (Approve/Reject promotion) | 7 |
| 3 | Quick-Wins Sweep | 12 |
| 4 | Hub re-grouping | 14 |
| 5 | Reactivate/Rehire + statuses | 17 |
| 6 | Verb harmonization | 18 |
| 7 | Sub/Vendor archive | 19 |
| 8 | Universal undo | 20 |
| 9 | OC-005 JHP build | 21 |
| 10 | Customer #2 brand parameterization | 21 (closes 4 readiness blockers) |

After 10 weeks: **~ 84 % of Top 25 retired**, platform polish at production grade, Customer #2 demo-able.

---

## Sequencing principles applied

1. **Pattern reuse first**: Sprints 1–3 reuse the iter453.7 sticky / LifecyclePanel / verb-button pattern proven by Rank #1.
2. **Frequency-weighted**: high-touch surfaces (Hub, Dispatch, PO, Reopen) before low-touch (OC-005, undo).
3. **Risk-ascending**: low-LOC zero-backend sprints first; backend / data-model sprints later; new-module last.
4. **Strategic check-in at Sprint 10**: by then the operator has visible polish + Customer #2 demo capability and can make an informed decision about whether to continue UX work, pivot to multi-tenancy, or both.

---

## What is NOT in the Top 10 (deliberately deferred)

* **Multi-tenancy infrastructure** (~ 9 weeks alone · not a single sprint · belongs to its own program)
* **Full White Label** (~ 16 weeks total · belongs to its own program · do not start before Customer #2 multi-tenancy lands)
* **Accountability Chain Phase 1B** (waiting on user feedback from current Accountability Alpha)
* **ForgedOps Operations Center** (separate authorization · larger build)
* **PWA / native mobile shell** (out of current scope)
* **S3 storage migration** (P2 from existing roadmap)

---

End of Top 10 Next Sprints.
