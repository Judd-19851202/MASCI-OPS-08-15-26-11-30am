# SAFETY DAILY REPORTS — PERMISSION REVIEW (D-A3)

**Phase 17 deliverable (Track 15.0). Audit-only. No permission change without authorization.**

## Defect

**D-A3** — Safety Hub has no read-only entry for `/daily-reports`. Safety needs to cross-reference daily field activity (especially for incident investigations) but cannot access daily reports today.

## Current permission model

| Route | Allowed identities | Mechanism |
|-------|-------------------|-----------|
| `GET /api/daily-reports` | Admin · PM (scoped via `compute_pm_scope`) · Field Leadership (scoped to projects they're rostered on) | `_daily_reports_read_gate` in `routes/daily_reports.py` |
| `GET /safety-portal/daily-reports` | route does not exist | n/a |

Safety identity (`X-Safety-Token`) is **not** in the read gate.

## Why Safety wants read access

1. **Incident investigation** — when investigating an incident, Safety needs to see the daily report from that day to understand who was on site, what the crew was doing, weather, etc.
2. **Corrective-action follow-up** — Safety needs to see whether a documented hazard was acknowledged in the next day's report.
3. **Trench / excavation cross-reference** — daily reports often include the kind of work that triggers JHA review.

## Why exposing all daily reports to Safety is non-trivial

1. **Confidentiality** — daily reports include manpower, hours, production numbers, and notes that PMs consider commercially sensitive (subcontractor relationships, owner negotiations, change-order narrative).
2. **Scope mismatch** — Safety is a company-wide identity; PMs are project-scoped. Granting Safety company-wide daily-report read crosses a clean boundary that took two prior tracks to establish.
3. **Audit consequences** — every Safety view of a daily report becomes a precedent in any future litigation. PMs may not want Safety inside their commercial notes.

## Permission-shape options

| Option | Description | Risk | Recommendation |
|--------|-------------|------|----------------|
| **A. Open read to all daily reports** | Safety can read any daily report on any project. | High — crosses PM commercial boundary | ❌ NO. |
| **B. Open read scoped to projects flagged as safety-relevant** | Only reports tagged `requires_safety_review = true` (a new field) are visible. | Medium — requires schema change + migration + business-rule definition. | ❌ DEFER (out of scope per hard rules). |
| **C. Open read scoped to projects with an open incident OR open corrective action** | Safety sees daily reports only on projects where Safety already has an open thread. | Medium — requires join logic but no schema change. Audit trail is natural. | ✅ **RECOMMENDED for future track** — minimal commercial exposure; aligns "Safety reads what Safety is investigating." |
| **D. Open read scoped to safety-flagged DR sections only (incidents, hazards, near-misses)** | Safety reads the safety section, not the production / man-hour / commercial sections. | Medium — requires DR response payload to be sliced server-side; doable but non-trivial. | ✅ **RECOMMENDED alternative** — sharpest commercial boundary; safest for production. |
| **E. PM-grants-Safety-read on demand** | Safety requests read access; PM grants per-report or per-project. | Low security risk · high friction. | ❌ NO — too much friction; users will work around. |

## Engineering reality

Implementing Option C or D safely requires:
1. Backend: extend `_daily_reports_read_gate` with a Safety branch.
2. Backend: compute the Safety scope (`projects with open incident OR open CA OR open JHA review`) or implement the section-slicing.
3. Frontend: add a Safety entry in Safety Hub V2 + Safety SideNav to `/safety-portal/daily-reports`.
4. Tests: 6-10 regression tests proving scope boundary holds.
5. Doc: business-rule decision + audit policy.

**Estimated effort**: 1-2 days, must be its own track.

## Track-15 verdict

🟡 **DEFER D-A3 to a dedicated "Safety ↔ Daily Reports Permission" track.**

**Why deferred**: Hard rules for Track 15 forbid permission redesign, schema changes, and business-rule decisions. D-A3 hits all three. Casual exposure is not safe.

**What Track 15 does provide**:
- This permission review (Phase 17 deliverable).
- A clear path forward (Option C or D).
- An honest acknowledgment that Safety today must ask a PM to share the daily report (workaround) for incident investigations.

**Risk while deferred**: Safety must ask PM by email/chat for daily reports during incident investigations. Acceptable for now — Safety has been operating this way for 6+ months.

## Recommendation when track opens

1. Pick Option C (project-scoped via open incidents) OR Option D (safety-section slice) — preferably both. C is faster; D is cleaner.
2. Open a "Safety Cross-Portal Read · Track 16" with this doc as Phase 0.
3. Co-design the business rule with at least one PM stakeholder.
4. Ship behind a feature flag with audit log of every Safety read.

## Status

🟡 **DOCUMENT-ONLY AUDIT COMPLETE.** D-A3 deferred. No casual permission exposure.
