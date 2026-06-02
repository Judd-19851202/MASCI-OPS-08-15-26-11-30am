# ITER500 · DEAD-END REGISTER

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY

A "dead-end" is a workflow where the user can START but cannot FINISH without operator assistance (Jaymn) or a re-deploy.

---

## Tier 1 — Confirmed dead-ends (workflow not buildable from UI alone)

| # | Workflow | Where it dies | Owner-side impact |
|---:|---|---|:-:|
| 1 | **OC-005 JHP Acknowledgement Ledger** — operator-stipulated build; UI not yet wired | Roadmap item · iter454 awaiting authorization | 🔴 |
| 2 | **Undo a status change** — once HR clicks Save and writes status_history, there is no in-app undo path other than a NEW status change with reverse direction | All lifecycle workflows | 🔴 (recovery gap) |
| 3 | **Withdraw an FL termination request** | FL portal · Termination Form intake | 🔴 (design choice per Phase Alpha G-5; documented but a UX surprise to FL users) |
| 4 | **Unlock a locked Daily Report** | DR detail page · only HR/Admin can unlock | 🟡 (intended but no operator-side UI cue) |
| 5 | **Bulk re-assign a closed incident** | Incidents admin | 🟡 |
| 6 | **Operator self-service `RESEND_WEBHOOK_SECRET` rotation** | Emergent env panel · no in-app affordance | 🟡 (documented in `RESEND_WEBHOOK_SECRET_REMEDIATION_REPORT.md`) |

## Tier 2 — Partial dead-ends (user can finish but feedback is opaque)

| # | Workflow | Issue |
|---:|---|---|
| 7 | Payroll time-off approval | Checkbox-toggle in table with no success toast |
| 8 | Asset-transfer "receive" acknowledgement | Subtle checkbox; no OLD→NEW transition message |
| 9 | PO request reject | Reason field not required; rejected items disappear without confirmation banner |
| 10 | Dispatch board crew assignment | Drag-drop without explicit OLD→NEW assignment toast |
| 11 | FleetDVIR post-submit | Confirmation page shows minimal text; no "edit" or "amend" path |
| 12 | Sub/Vendor archive | Add-new exists; no archive/disable workflow visible |
| 13 | Notifications digest config | Admin page wires settings but no "saved" banner on field blur |
| 14 | Daily Report share-email | Toast fires but doesn't show recipients on success |
| 15 | Constraint resolution close | Reopen exists but closure-action contract less prominent than QA/QC equivalent |

## Tier 3 — Path-exists-but-discoverability-gap

| # | Workflow | Issue |
|---:|---|---|
| 16 | Reactivate (Rehire) flow has TWO paths | Reactivate Dialog (preferred) vs Status tab Inactive→Active (works but loses rehire_date metadata) — user must know which to pick |
| 17 | HR Queue approve creates employee → user can't tell which row in the roster is the newly-created one | Queue approval succeeds but doesn't pin/highlight the new roster row |
| 18 | Admin audit log filter UI | Filters apply silently; no "filter active" chip-stack |
| 19 | Field-Leadership records detail | Some kinds of records (e.g., termination addendum) render as flat read-only without verbs |
| 20 | Operator Daily Reports digest opt-in | Buried in admin/digest-config; no inline preview |
| 21 | Equipment-inspection re-inspection chain | Closure-action "re-inspection" creates a new inspection but the link from parent to child is via a row tooltip |
| 22 | JHA submission → poster generation | "Print poster" flow exists but the toast for "poster sent to print queue" auto-dismisses too fast |
| 23 | Time-verification dispute path | Exists in code but the "raise dispute" verb is labeled "Flag for review" — terminology drift |
| 24 | Driver qualification expiration warning | Email digest fires but in-app dashboard doesn't visually flag the row with a red border |
| 25 | Backend dead-letter escalation (Ownership Doctrine O-4) | Operator notification fires via Resend; no in-app "Dead-letter queue" dashboard |

---

## STOP
