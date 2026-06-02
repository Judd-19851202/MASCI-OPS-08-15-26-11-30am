# ITER500 · USER CONFUSION REGISTER

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY

---

## Top 25 user-confusion areas (synthesized from this fork's findings + code-path scan)

| # | Confusion area | Affected roles | Severity |
|---:|---|---|:-:|
| 1 | "Save" vs "Submit" vs "Create" inconsistent verbs across forms | All | 🟡 |
| 2 | "Inactive" vs "Suspended" vs "Leave of Absence" — three statuses for "not currently working" | HR · Foreman | 🟡 |
| 3 | "Resigned" vs "Terminated · separation_type=voluntary" — overlapping semantics | HR | 🟡 |
| 4 | "Reactivate" (Inactive→Active) vs "Rehire" (Resigned/Terminated→Active) — same button label may apply to either | HR | 🟡 |
| 5 | Daily Report "Submit" → status becomes "Submitted" but UI says "Open" until shop confirms | Foreman · PM | 🟡 |
| 6 | QA/QC Closure-action contract: three options (re-inspection / corrective_action / exception) but their semantics tribal | PM · QC | 🟡 |
| 7 | Constraint "Resolve" vs "Close" — both verbs appear on detail page | PM | 🟡 |
| 8 | Incident "lifecycle_state" vs "is_closed" — two fields for one concept | Safety · HR | 🟡 |
| 9 | FleetDVIR "pass / pass-with-defects / fail" — defects without fail seems incongruous | Driver | 🟡 |
| 10 | Time-off "approved" but pay-period not yet aligned — user thinks request is in limbo | Foreman · HR | 🟡 |
| 11 | Equipment inspection "expires_at" date — is it the next-inspection due date or this-inspection valid-until? | Shop · Field | 🟡 |
| 12 | JHA "applies-to" job vs "issued-for" job — two job-references on one record | Safety · PM | 🟡 |
| 13 | Asset transfer "shipped" vs "in-transit" vs "received" — three terms · only 2 user actions | Shop | 🟡 |
| 14 | Dispatch crew assignment vs ad-hoc reassignment — two different flows | Dispatch | 🟡 |
| 15 | PO request "approved" but vendor not yet notified — opaque status gap | PM | 🟡 |
| 16 | Sub/Vendor "active" vs "approved" vs "preferred" — three flags · usage unclear | PM | 🟡 |
| 17 | HR Queue "pending" vs "needs_review" — when does an item move? | HR | 🟡 |
| 18 | Field Leadership Portal "Records" tab — mixes Type=Termination · Type=Hire · Type=Equipment · with type-icon only | Foreman | 🟡 |
| 19 | PM "Projects" vs "Jobs" — interchangeable in code, separate in UI | PM | 🟡 |
| 20 | Training records "completed" vs "valid_until" — completed implies valid; user must compute expiry | HR · Safety | 🟡 |
| 21 | Driver qualification "expiration" vs "review_due" — overlapping fields | HR · Dispatch | 🟡 |
| 22 | Photo Viewer "tagged employees" — implies attribution; actually just metadata index | Field · PM | 🟡 |
| 23 | Admin audit log "actor" vs "submitter" vs "by" — three names for the same role across pages | Admin | 🟡 |
| 24 | Scheduler digest opt-in is per-user but configured per-org by admin — split mental model | All | 🟡 |
| 25 | "Closed" lifecycle state means different things across QA/QC vs Inspection vs Incident vs Constraint | All | 🟡 |

---

## STOP
