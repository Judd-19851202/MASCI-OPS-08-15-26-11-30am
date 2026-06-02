# ITER500 · ROLE-BASED FRICTION REPORT

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY

For each of the 12 personas, the top 3 friction points.

---

## Employee (field worker)

* No employee-self-service portal — employees cannot view their own status_history, training records, or pending time-off.
* Daily-report participation is via foreman entry; employee doesn't see their own attendance reflected anywhere.
* Time-off requests must be entered by foreman or HR, not by employee directly.

## Foreman

* Daily Report "Submit" vs "Save Draft" — primary action unclear.
* Crew assignment changes have to go through dispatch portal, not the foreman's own daily flow.
* JHA generation feels redundant when the same crew worked the same task yesterday — no "copy last" button.

## Supervisor / Superintendent

* Project Health page is read-only; cannot drill into specific incident or QA/QC item from the dashboard.
* Constraints list mixes own-team and other-team items; no team filter.
* No supervisor-level approval for Daily Report sign-off (gap between foreman submit and PM approve).

## PM

* PM Hub has 499 lines worth of tiles; primary daily action unclear.
* "Projects" vs "Jobs" vs "Project Number" — three names for one entity.
* PO-request approval batch flow: must click into each item individually; no bulk approve.

## Safety

* Incident lifecycle reopen requires reason but the reason textarea is below the fold on common viewports (same defect class as iter453.7 was for HR).
* JHA poster regeneration has no preview before sending to print queue.
* Training records list does NOT auto-flag the rows about to expire in the next 30 days (visual cue missing).

## HR

* iter453.7 + iter453.9 cleared the major HR Lifecycle frictions (this fork).
* HR Queue: approve creates an employee but cannot identify the newly-created row in the roster afterward.
* Bulk-upload (CSV) confirmation page does not show per-row error preview before commit.

## Payroll

* Time-off approval is a table toggle, not a verb — feels accidental rather than deliberate.
* Variance report has no drill-down to a single employee's time records.
* Pay-period close has no explicit "lock" CTA; lock happens silently on schedule.

## Dispatcher

* Dispatch Board drag-drop has no toast confirmation per assignment.
* "Driver qualification expired" appears on dashboard but no jump-to-fix link.
* Fleet visibility page is read-only; cannot initiate a re-routing from this page.

## Fleet

* DVIR submission confirmation is bare-minimum (no echo of submitted state).
* Weekly emergency/lead inspection forms are separate routes — operator may forget which to use when.
* No fleet-wide compliance dashboard summarizing DVIR completion rates by driver.

## Executive

* Command Center dashboard is the right concept but lacks period-over-period deltas (no MoM or WoW arrows).
* Operations Center is admin-only by design; exec view doesn't carve out a "C-level" subset.
* P&L page wires data but the chart legend overlaps narrow viewports.

## Admin

* AdminHub: 35+ admin pages without grouped sections (alphabetical sprawl).
* Audit log filters apply without a visible "Filter active" chip.
* Database admin page (`/admin/database`) exists; no read-only safeguard for destructive operations.

## Public / Field-form submitter (anonymous)

* The public Daily Report submit form requires JOB number — no autocomplete from past 90 days.
* Incident report from public link has no progress-saving (refresh = lost work).
* JHA submit confirmation: shows ID but doesn't email a copy to the submitter.

---

## STOP
