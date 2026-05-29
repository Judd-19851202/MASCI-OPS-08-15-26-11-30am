# Dashboard Destination Certification

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:42 UTC._

> Verifies that every operational record lands on at least one human-
> reachable dashboard surface. Records with no dashboard destination
> are classified as ORPHANS. Read-only audit, no fixes.

## 1 · Definition

> A **dashboard destination** is any portal surface where a record:
> 1. Appears in a list/table by default (without requiring direct URL)
> 2. Is summarized in a stat card or count badge
> 3. Triggers a bell-feed entry the user sees on login

A record can have ONE or MANY destinations. The minimum acceptable
state for non-archival workflows is **at least ONE proactive surface**
(stat card or task / bell — not just "you can search for it").

## 2 · Per-workflow certification

| Workflow | Proactive surface(s) | Search-only surface(s) | Certified |
|---|---|---|---|
| Daily Report | PM Hub project tile · Admin DR list · HR Daily Reports filter · Safety Operations (Incidents/Injuries when flagged) | none | ✅ |
| Equipment Pre-Op PASS | Admin Equipment Dashboard · PM Equipment list · Shop Equipment list | n/a | ✅ |
| Equipment Pre-Op FAIL | Admin "Open Items" panel · Shop "Equipment Needing Attention" tile · Shop bell · Shop task | n/a | ✅ |
| Shop Recovery | ShopHub Active Recovery section · Shop Asset Transfers list · Shop bell · Shop task | n/a | ✅ |
| PO Request (open) | PendingApprovalQueue widget · PO Requests filter · admin nightly cron · Approval bell · Approval task | n/a | ✅ |
| PO Approve / Reject / Clarify | requester bell · audit log · admin PO Requests | n/a | ✅ |
| PO Receipt upload | requester bell · admin PO Requests | n/a | ✅ |
| Incident Report | Safety Operations Dashboard · Admin Incidents · HR Safety Records | n/a | ✅ |
| Safety Meeting | Safety Operations Dashboard · Admin Meetings | n/a | ✅ |
| Safety Inspection | Safety Operations Dashboard · Admin Inspections | n/a | ✅ |
| QA/QC (all types) | Safety Operations Dashboard · Admin QA/QC list · PM QA/QC list | n/a | ✅ |
| Corrective Action | Safety CA list · Safety Hub Open CAs card | n/a | ✅ |
| Fire Extinguisher | Safety Fire Extinguishers list · Safety bell | n/a | ✅ |
| Dispatch Request | DispatchHub board · Dispatch bell · Dispatch task | n/a | ✅ |
| Time Verification (query) | HR Time Verification page (the page IS the surface) | n/a | ✅ |
| Payroll Variance | HR Payroll Variance page · weekly cron email | n/a | ✅ (page IS surface) |
| Training Record (assigned) | Training Center · HR/Safety Training Records · Employee bell · Employee task | (supervisor needs to navigate to find) | ⚠ partial (GAP-4) |
| Visitor Log | Daily Report detail (parent) | n/a | ✅ (sub-record) |
| Document Expirations | HR Hub Docs Expired card · HR bell · HR task | n/a | ✅ |
| Backup success row | Admin Backup Health panel | n/a | ✅ |
| Backup failure / staleness | Admin Backup Health panel · email alarm (when scheduler alive) | n/a | ⚠ depends on scheduler (P0) |
| **JHA** | Admin JHA list (search only — no card on Safety Hub) | required navigation | ❌ **GAP-3** |
| **Safety Forms (Equip Issuance/Training/Return)** | Admin Safety Forms list · Safety Hub "Open Safety Forms" card (currently shows count but no actionable surface per record) | required navigation | ❌ **GAP-2** |
| **Field Leadership 10 forms** | FL Portal forms list · Admin FL forms list · NO Safety Hub surface | required navigation | ❌ **GAP-1** |
| **Fleet DVIR** | (no confirmed surface) | (none) | ❌ **GAP-6** |

## 3 · Net-state summary

| Workflow class | ✅ Certified | ⚠ Partial | ❌ Orphan |
|---|---|---|---|
| Operational/safety records | 14 | 1 | 4 |
| HR records | 4 | 0 | 0 |
| Shop records | 3 | 0 | 0 |
| Admin/system records | 2 | 1 | 0 |

## 4 · Recommended dashboard additions (NOT IMPLEMENTED — audit only)

| Gap | Suggested surface |
|---|---|
| GAP-1 (FL 10 forms) | Add "Open FL Forms" stat card + actionable list to FL Portal Hub AND to Safety Operations Dashboard (FL forms are mostly safety/compliance) |
| GAP-2 (Safety Forms) | Make Safety Hub "Open Safety Forms" card actionable — clicking opens a filterable list of recent issuance/training/return forms |
| GAP-3 (JHA) | Add JHA stat card to Safety Operations Dashboard's Primary Operations section (parallel to Inspections / Meetings) |
| GAP-4 (Training supervisor) | When a Training Record is assigned, also create a low-priority bell entry for the assignee's `linked_supervisor` (best-effort lookup) |
| GAP-6 (Fleet DVIR) | Confirm with operator whether DVIR was intended to notify Dispatch + Shop. If yes: add `schedule_auto_email` and `emit_task_and_notification` to DVIR submit endpoint; surface on Shop Hub and Dispatch Hub. |

## 5 · Verdict

The platform has a strong dashboard surface for **safety operations**, **PO requests**, **equipment pre-op fails**, and **shop recovery**. Three workflow families lack adequate proactive surfaces (FL forms · safety forms · JHA) and one (Fleet DVIR) appears wholly orphaned. These are the operator-described "trust-killing black holes" — they are recorded reliably but lack the "what happens next?" pathway.

---

_End of DASHBOARD_DESTINATION_CERTIFICATION.md._
