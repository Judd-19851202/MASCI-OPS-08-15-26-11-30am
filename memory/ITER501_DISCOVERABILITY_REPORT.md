# ITER501 · DISCOVERABILITY REPORT

**Date**: 2026-06-02T21:04 UTC
**Mode**: READ-ONLY synthesis
**Source**: ITER500_BUTTON_VISIBILITY_AUDIT + ITER500_DEAD_END_REGISTER + ITER500_USER_CONFUSION_REGISTER + ITER500_WORKFLOW_COMPLETENESS_MATRIX

This report synthesizes the six "Top 25" lists requested by the operator. Items already retired by Rank #1 (Save below fold on the 6 New X form pages) are excluded.

---

## A · Top 25 Discoverability Failures (residual after Rank #1)

| # | Failure | Surface |
|--:|---|---|
| 1 | Approve / Reject buried under row-action dropdown | Dispatch list |
| 2 | Approve / Reject buried under row-action dropdown | PO Requests list |
| 3 | Approve / Reject as table checkbox | Time-off approval |
| 4 | Receive as table checkbox | Asset Transfer |
| 5 | Reopen hidden in kebab | Incident detail |
| 6 | Reopen hidden in kebab | QA/QC detail |
| 7 | Reopen hidden in kebab | Site Inspection detail |
| 8 | Reactivate / Rehire dual button on Inactive employee detail | HR Employees |
| 9 | Constraint resolve / close verbs inline · no LifecyclePanel | Constraint detail |
| 10 | Sub / Vendor archive — workflow does not exist | Sub/Vendor list |
| 11 | Notifications digest opt-in buried 3 clicks deep | Admin → Notifications |
| 12 | Hub tile sprawl · 35+ tiles · alphabetical | Hub.jsx (587 lines) |
| 13 | AdminHub alphabetical · no groupings | AdminHub.jsx (133 lines) |
| 14 | PM Crew Compliance hidden inside PmHub | PmHub.jsx |
| 15 | Off-screen action on long admin pages | AdminGuide.jsx, AdminLegacyImports.jsx |
| 16 | Disabled buttons with no tooltip explanation | Admin governance |
| 17 | ~ 18 pages with no `data-testid` on primary action | platform-wide |
| 18 | Field-Leadership records type-mix without filter chips | FL Records |
| 19 | Daily Report "Submit" vs "Save Draft" — no primary CTA distinction | Daily Report new |
| 20 | Driver-qualification expiring-soon visual flag missing | Driver Qual dashboard |
| 21 | Equipment re-inspection chain hidden in tooltip | Equipment list |
| 22 | JHA poster print-queue toast auto-dismisses too fast | JHA poster |
| 23 | Backend dead-letter escalation queue has no in-app dashboard | Admin |
| 24 | Audit-log "filter active" chip-stack missing | Admin Audit Log |
| 25 | FleetDVIR post-submit edit / amend path not surfaced | FleetDVIR detail |

---

## B · Top 25 Usability Failures

| # | Failure |
|--:|---|
| 1 | Lifecycle verbs not promoted to primary CTAs anywhere |
| 2 | No universal undo / status reversal verb |
| 3 | Toast position inconsistent across modules |
| 4 | Some forms use modal · others drawer · others full page for the same kind of edit |
| 5 | Date-pickers behave differently across modules |
| 6 | Photo upload zone sizing varies (PhotoUpload.jsx vs inline) |
| 7 | Empty-state copy inconsistent ("No items" vs "Clean" vs "—") |
| 8 | Loading state varies (spinner · skeleton · dim) |
| 9 | Error toast formats vary in tone and length |
| 10 | Required-field markers (*) inconsistent (some red asterisks, some Required pill, some none) |
| 11 | Inline help-tips not present on every gnarly field |
| 12 | i18n coverage 95% — some pages still half-English in ES mode |
| 13 | Search UI inconsistent across list pages |
| 14 | Filter UI inconsistent (drawer vs inline chips vs select) |
| 15 | Pagination vs infinite-scroll mixed |
| 16 | Mobile-friendly grids on some pages, desktop-only tables on others |
| 17 | Mobile keyboard cover-up on a few tall pages |
| 18 | Sticky-header z-index occasionally collides with mobile keyboard |
| 19 | Tab order non-obvious on some multi-section forms |
| 20 | Multi-select chips inconsistent (some with X, some only via dropdown) |
| 21 | Cancel-button placement varies (left vs right) |
| 22 | Confirmation dialogs vary in copy tone |
| 23 | Long-running operations have no progress UI |
| 24 | Bulk action UX (where it exists) inconsistent |
| 25 | Detail-page action bars (where they exist) inconsistent |

---

## C · Top 25 Confusion Points

(See `ITER500_USER_CONFUSION_REGISTER.md` for the source list — replicated here for completeness)

| # | Confusion |
|--:|---|
| 1 | Save / Submit / Create / File / Send verb inconsistency |
| 2 | 5 statuses for "not currently working" |
| 3 | Resigned vs Terminated/voluntary overlap |
| 4 | Reactivate vs Rehire button confusion |
| 5 | Daily Report submit → "Open" until shop confirms |
| 6 | QA/QC closure-action contract requires training |
| 7 | Constraint Resolve vs Close |
| 8 | Incident `lifecycle_state` + `is_closed` dual field |
| 9 | FleetDVIR pass-with-defects without explicit fail |
| 10 | Time-off approved vs pay-period misalignment |
| 11 | Equipment `expires_at` ambiguity |
| 12 | JHA applies-to vs issued-for jobs |
| 13 | Asset transfer shipped / in-transit / received tri-state |
| 14 | Dispatch assignment vs ad-hoc reassignment dual flow |
| 15 | PO approved but vendor not yet notified |
| 16 | Sub/Vendor active vs approved vs preferred flags |
| 17 | HR Queue pending vs needs_review |
| 18 | FL Records mixed types · icon-only |
| 19 | PM Projects vs Jobs |
| 20 | Training completed vs valid_until |
| 21 | Driver-qualification expiration vs review_due |
| 22 | Photo Viewer "tagged" implies attribution |
| 23 | Audit-log actor / submitter / by terminology drift |
| 24 | Scheduler digest opt-in mental model split |
| 25 | "Closed" means different things across QA/QC vs Inspection vs Incident vs Constraint |

---

## D · Top 25 Workflow Friction Points

| # | Friction |
|--:|---|
| 1 | Approve / Reject hidden in dropdowns (multi-module) |
| 2 | Reopen hidden in kebab (lifecycle pages) |
| 3 | Universal undo missing |
| 4 | Reactivate vs Rehire mental model |
| 5 | DR "Open" status confusion |
| 6 | QA/QC closure contract training-dependent |
| 7 | Constraint Resolve vs Close |
| 8 | Incident dual-field |
| 9 | FleetDVIR pass-with-defects |
| 10 | Time-off / pay-period misalignment |
| 11 | Equipment expires_at |
| 12 | JHA applies-to vs issued-for |
| 13 | Asset transfer tri-state |
| 14 | Dispatch assignment vs reassignment |
| 15 | PO approved but vendor not notified |
| 16 | Sub/Vendor flag confusion |
| 17 | HR Queue dual-state |
| 18 | FL Records mixed types |
| 19 | PM Projects vs Jobs |
| 20 | Training completed vs valid_until |
| 21 | Driver-qual expiration vs review_due |
| 22 | Photo Viewer tag-attribution implication |
| 23 | Audit-log actor terminology |
| 24 | Scheduler digest opt-in mental split |
| 25 | "Closed" cross-module drift |

(Note: friction and confusion lists are the same content viewed through different lenses — by design.)

---

## E · Top 25 Completion Risks

| # | Risk |
|--:|---|
| 1 | OC-005 JHP build gap — operator cannot acknowledge JHP |
| 2 | Reopen kebab on 3 lifecycle pages — users believe closure is final |
| 3 | Approve/Reject dropdown — actions missed because they're "not there" |
| 4 | Daily Report "Open" — foremen re-submit thinking the first failed |
| 5 | Reactivate vs Rehire — wrong path taken, breaks original_hire_date logic |
| 6 | Time-off checkbox — approver thinks they approved when they didn't |
| 7 | Asset-transfer checkbox — receiver thinks the transfer is done when it isn't |
| 8 | Dispatch drag-drop silent — dispatcher reassigns same crew twice |
| 9 | Notifications digest no save banner — admin saves nothing |
| 10 | Sub/Vendor archive missing — sub still appears as "active" after offboard |
| 11 | PO reject without reason — auditor cannot trace decision |
| 12 | FleetDVIR fail/amend missing — defect not recorded correctly |
| 13 | Driver-qual expiring-soon flag missing — driver compliance lapses unnoticed |
| 14 | Equipment expires_at — inspection lapses noticed too late |
| 15 | Constraint Resolve vs Close — wrong status, wrong downstream signal |
| 16 | JHA applies-to vs issued-for — wrong job linkage |
| 17 | Training completed vs valid_until — re-trained too late |
| 18 | Photo Viewer tag — attribution implied, decision built on wrong assumption |
| 19 | Audit-log filter — investigator misses the right slice |
| 20 | "Closed" cross-module drift — escalation routes wrong |
| 21 | Incident dual-field — reports show inconsistent state |
| 22 | HR Queue dual-state — HR processes the wrong queue |
| 23 | PM Projects vs Jobs — wrong rollup |
| 24 | Notifications mental-model split — recipient surprised |
| 25 | i18n half-coverage — Spanish operator misreads English-only string |

---

## F · Top 25 "User Thinks System Is Broken" Risks

| # | Risk |
|--:|---|
| 1 | Daily Report "Open" status (foreman: "did it not save?") |
| 2 | Dispatch drag-drop with no toast |
| 3 | Approve/Reject hidden behind dropdown (manager: "where's the approve button?") |
| 4 | Reopen hidden in kebab (operator: "this is supposed to be reopenable") |
| 5 | Notifications digest save with no banner (admin: "did the toggle stick?") |
| 6 | Save-disabled with no tooltip on admin governance pages |
| 7 | Sub/Vendor archive missing (admin: "why can't I retire this sub?") |
| 8 | Reactivate vs Rehire wrong path (HR: "wait, this didn't reset the original date?") |
| 9 | Time-off checkbox silent (approver: "did this go to payroll?") |
| 10 | Asset-transfer checkbox silent |
| 11 | PO reject no reason path (vendor: "why was this rejected?") |
| 12 | FleetDVIR amend missing (mechanic: "I can't fix the typo") |
| 13 | Driver-qual flag missing (Safety: "I had no warning") |
| 14 | Audit-log filter chip-stack missing (admin: "what filters are even on?") |
| 15 | Off-screen Submit on long admin pages |
| 16 | JHA poster toast auto-dismisses too fast |
| 17 | Equipment re-inspection chain hidden in tooltip |
| 18 | Constraint Resolve vs Close ambiguity (operator: "I clicked Resolve but it shows Closed?") |
| 19 | i18n partial coverage (ES operator: "this page is mostly English now?") |
| 20 | HR Queue dual-state (HR: "what's the difference between pending and needs_review?") |
| 21 | Disabled buttons with no tooltip |
| 22 | Long-running ops with no progress (admin: "is the import frozen?") |
| 23 | Bulk action UX inconsistent (admin: "did all rows process?") |
| 24 | Multi-select chip inconsistencies |
| 25 | Mobile keyboard cover-up on tall forms |

---

## Cross-list synthesis

Items appearing on **3 or more** of the six lists (the "vortex" issues):

* Approve / Reject hidden in dropdowns
* Reopen hidden in kebab
* Daily Report "Open" status
* Dispatch drag-drop silent
* Sub/Vendor archive missing
* Notifications digest opt-in save
* Reactivate vs Rehire
* Verb / "Closed" semantic drift
* Hub re-grouping
* Driver-qual expiring-soon flag

These are the items where the most leverage exists: each lives in multiple categories, so one fix retires multiple findings.

---

End of discoverability report.
