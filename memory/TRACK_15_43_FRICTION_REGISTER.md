# TRACK 15.43 · Friction Register

**Date:** 2026-06-19
**Scope:** Documented friction observed across the 7 persona audits. NOT a backlog; NOT a build plan. Pure evidence capture.

| ID | Persona | Description | Clicks | Impact |
|---|---|---|---|---|
| FR-001 | Executive | No single screen composing "jobs at risk" across DR cadence + safety + crew + holds | 4-6 (drill-down each domain) | **HIGH** |
| FR-002 | Executive | No org-wide "Overdue (N)" tile broken down by category (DRs, FL records, training renewals) | 3-5 | **HIGH** |
| FR-003 | PM | Notification action label vague on multi-record events ("Updated" doesn't say what) — Track 15.40 source-module chip helps but verbiage could be more specific | 1 | MEDIUM |
| FR-004 | Shop | Shop-to-PM handoff timing (when does a PM see a PM Work Order is being scheduled?) — relies on existing notification fanout; no dedicated "handoff" surface | 2 | MEDIUM |
| FR-005 | HR | HR-incident attachment naming convention not enforced; relies on file-upload original name | 1 | LOW |
| FR-006 | Dispatch | Driver-qualification expiration UI surface (cadence of "expires in 7d / 14d / 30d" warnings) configurable only via env vars | n/a | LOW |
| FR-007 | Safety | Safety-meeting attendee bulk-add: today user must add row-by-row or paste a comma list — no employee-multiselect from `employees` collection | 5-10 | MEDIUM |
| FR-008 | Field Lead | JHA crew acknowledgement on mobile — signature pad UX known to be smaller than desktop | n/a | LOW |
| FR-009 | Superintendent | DR delay-cause taxonomy maintenance UI — admin-only and not obvious how to add a new cause | 4 | LOW |
| FR-010 | HR | HR safety-records gating clarity — non-HR scope sees 403 with a generic message in some flows | n/a | LOW |
| FR-011 | Executive | Staffing-issues callout (projects missing a Foreman/PM) — possible via Team Assignment data but not surfaced as a leadership tile | n/a | MEDIUM |
| FR-012 | All | "Unknown person" directory orphans — RESOLVED in Track 15.40 for assignment surfaces; need a periodic sweep job to catch new orphans (employees not in user_directory who get assigned) | n/a | LOW (monitored) |

## Rank summary
* **HIGH (2):** FR-001, FR-002 — exec composite visibility.
* **MEDIUM (4):** FR-003 (notification clarity), FR-004 (shop→PM), FR-007 (bulk attendee), FR-011 (staffing callout).
* **LOW (6):** FR-005, FR-006, FR-008, FR-009, FR-010, FR-012.

## Track-15.43 directive compliance
The directive says: "Do NOT build solutions. Document them." This register documents friction with click counts and impact ranks. No code was changed in this track.

🟡 **Register live · 12 items captured · 2 HIGH · 4 MEDIUM · 6 LOW.**
