# Executive Command Center — Data Source Map (Pillar 2)

**Classification:** OMEGA Pillar 2 · DESIGN / SPEC ONLY · No code · No DB changes · No endpoints · No UI · No notifications · No workflow changes
**Generated:** 2026-05-31 UTC
**Author:** E1
**Audience:** Operations Leadership · future implementation agent (when authorized)
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_AUDIT.md` · `EXECUTIVE_COMMAND_CENTER_SPEC.md` · `EXECUTIVE_HEATMAP_SPEC.md` · `EXECUTIVE_IMPLEMENTATION_ROADMAP.md`

---

## 1 · How to read this map

For every widget in `EXECUTIVE_COMMAND_CENTER_SPEC.md`, this document declares:

| Column | Meaning |
|---|---|
| Source collection | the **existing** MongoDB collection the data is read from |
| Source workflow | the existing submit handler / business workflow producing the data |
| Source owner | the role that owns that workflow (i.e., who is accountable for the data quality) |
| Existing data availability | ✅ already captured · 🟡 partial · ❌ missing |
| Missing data requirements | what (if anything) must be added to fill the gap |

**Operating rule:** the implementation batch must **NOT add new collections** for any widget marked ✅. Use what exists. Net-new collections are permitted **only** where this map flags ❌ — and only after operator authorization.

---

## 2 · Per-widget data source table

### 2.1 Pulse Strip (5-second)

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Overall RAG pill | derived from cards 1–9 (no own source) | — | — | ✅ | none — composition only |
| Headline counts | `tasks` · `corrective_actions` · `incidents` · `po_requests` (aggregations) | (cross-domain) | (cross-domain) | ✅ | none |
| `computed_at` | server time | — | — | ✅ | none |
| `release` / `app_env` | `/api/version` | system | system | ✅ | none — already exposed |

### 2.2 Priority Stack (60-second) — Top 5 items

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Recommender candidates | union of red+amber items across cards 1–9 | (cross-domain) | (cross-domain) | ✅ | composite scorer (logic, not data) — see `EXECUTIVE_HEATMAP_SPEC.md` §4.10 |
| Owner role/name | `user_directory` JOIN `tasks.assignee` / `incidents.routed_to` / `po_requests.approver` etc. | various | role-dependent | ✅ | normalize "owner role" enum across collections (logic, not data) |
| Action verb | inferred from item's collection + state | — | — | ✅ | small lookup table — not a collection (config doc OK) |
| ETA | `tasks.due_at` · `corrective_actions.due_date` · `po_requests.due_at` (when set) | original workflow | original owner | 🟡 | not every workflow sets a due_at — Phase B `escalation_clock` (see Pillar 4) |

### 2.3 Card 1 · Jobs Today

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Active job list | `jobs_master` | `/admin/jobs` create/edit | Admin · PM | ✅ | none |
| DR filed today per job | `daily_reports` filter by `project_number` + `created_at` | `POST /api/daily-reports` | Foreman → PM | ✅ | none |
| Open incidents per job | `incidents` filter by `project_number` + `status=open` | `POST /api/incidents` | Foreman/Safety → Safety/PM | ✅ | none |
| Orphaned project (no PM) | `jobs_master.assigned_pm_email IS NULL` | Admin assignment | Admin | ✅ | none |

### 2.4 Card 2 · Safety Today

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Open incidents | `incidents` | `routes/safety.py:579` | Safety + PM | ✅ | none |
| Open corrective actions | `corrective_actions` | `routes/safety.py` (corrective actions) | Safety | ✅ | none |
| Open compliance findings | (collection from `/api/admin/compliance/findings`) | `routes/admin_ops.py` / compliance scan | Safety + Admin | ✅ | none |
| Safety meeting gap | `meetings` aggregation by project_number / last_14d | `POST /api/meetings` | Foreman/Safety | ✅ | none |

### 2.5 Card 3 · Equipment Today

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| OOS pre-op | `equipment_inspections.out_of_service=yes` AND no shop signoff | `routes/equipment.py:234` (Pre-Op FAIL) | Operator → Shop | ✅ | none |
| Critical defects | `fleet_defects.status=open AND severity=critical` | `routes/fleet_ops.py` defect lifecycle | Operator → Shop · Dispatch | ✅ | none |
| Aging asset holds | `asset_holds.active=true` (compute age client/server) | `routes/operations.py` hold workflow | Dispatch · Admin | ✅ | none |
| DVIR defect-OOS w/o shop task | `fleet_defects` joined `tasks` filter `kind=dvir.defect.oos` | `routes/fleet_ops.py:412` + `tasks_notifications.py` | Driver → Shop · Dispatch | ✅ | **none — Batch L closeout already wired this fan-out (PRD line 14)** |

### 2.6 Card 4 · Accountability Overdue

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Open overdue tasks | `tasks.status=open AND due_at < now` | `routes/tasks_notifications.py` | per-task `assignee` | ✅ | none |
| Open overdue CAs | `corrective_actions.due_date < now` | Safety workflow | Safety | ✅ | none |
| Stale unack notifications | `notifications.acknowledged=false AND created_at < now-7d` (filtered to executive audience) | `routes/notifications.py` | each recipient | ✅ | none |

### 2.7 Card 5 · PM Load

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| PM roster | `project_managers` | Admin people CRUD | Admin | ✅ | none |
| Assigned-jobs count per PM | derived from `jobs_master.primary_pm` + `co_pms[]` | Admin assignment | Admin | ✅ | none |
| Open DRs awaiting PM review | `daily_reports` filter by PM scope AND `pm_review.status != "reviewed"` | foreman submit | PM | ✅ | none |
| Open incidents in PM scope | `incidents` filter by PM scope AND `status=open` | safety/foreman submit | Safety/PM | ✅ | none |
| Open POs in PM scope | `po_requests.requester_email IN pm_scope OR project_number IN pm_scope` | requester submit | approver | ✅ | none |
| `last_login_at` per PM | `project_managers.last_login_at` (stamped by `pm_auth.stamp_login`) | login | PM | ✅ | none |

### 2.8 Card 6 · Supervisor Load

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| FL user roster | `field_leadership_portal_users` (per `field_leadership_portal.py`) | Admin/HR CRUD | Admin · HR | ✅ | none |
| Daily reports signed by FL user | `daily_reports.supervisor_email` (or sub-field) | foreman submit | Supervisor signs | 🟡 | confirm field name in code at implementation time (`PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md` §1.1 row 1) |
| Open field-leadership records | `field_leadership_records.status` (kind ∈ write_up/coaching/...) | `routes/field_leadership.py` submit | FL | ✅ | none |
| Dispatch crew-day-count | `dispatch_assignments` aggregation by `supervisor_id` × week | dispatch lifecycle | Dispatch | ✅ | none |

### 2.9 Card 7 · Approvals Aging

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| PO list with status & age | `po_requests` | `routes/po_requests.py:206+220+242` | approver per routing | ✅ | none |
| Receipt-missing aging | `po_requests.receipt_required AND receipt_uploaded=false AND due_at < now` | PO receipt upload workflow | requester | ✅ | none — `po_digest_admin.py` already runs the watchdog cron |

### 2.10 Card 8 · Projects at Risk

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Per-project safety roll-up | `incidents` + `corrective_actions` + `compliance_findings` GROUP BY project_number | (multi-workflow) | Safety + PM | ✅ | none |
| Per-project equipment roll-up | `equipment_inspections` + `fleet_defects` + `asset_holds` joined to project | (multi-workflow) | Shop · Dispatch | ✅ | none |
| Per-project DR cadence | `daily_reports` aggregation per project_number | foreman submit | PM | ✅ | none |
| Per-project PO churn | `po_requests` group by project_number | requester submit | approver | ✅ | none |
| Per-project P&L variance | `projects.pnl` (if populated) | manual upload / cost system | Admin | 🟡 | optional — Phase B (rule OFF when missing) |

### 2.11 Card 9 · Operational Bottlenecks

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Stuck dispatch | `dispatch_assignments` aging in same `state` | dispatch lifecycle | Dispatch | ✅ | none |
| Unreviewed DRs | `daily_reports.pm_review.status != reviewed AND created_at < now-48h` | DR submit | PM | ✅ | none |
| Stuck POs | `po_requests` (also feeds APP-2 / APP-3) | PO workflow | approver | ✅ | none |
| OOS equipment w/o WO | `fleet_status.out_of_service=true AND tasks(kind=dvir.defect.oos).count==0` past 24h | DVIR + fan-out | Driver → Shop | ✅ | none — Batch L wiring |
| `operations_events.status=stuck` | `operations_events` | cross-portal emitter | various | 🟡 | confirm `status` enum at implementation time |

### 2.12 Card 10 · Recommender

| Element | Source collection | Source workflow | Owner | Avail | Missing |
|---|---|---|---|---|---|
| Source items | union of cards 1–9 | — | — | ✅ | scoring logic (formulas in `EXECUTIVE_HEATMAP_SPEC.md` §4.10) — code, not data |

---

## 3 · Net-new collection requirements

| Collection | Purpose | Phase | Replaces existing? | Authorized? |
|---|---|---|---|---|
| `command_center_thresholds` | Single config doc holding all RAG thresholds (one field per rule_id) | Phase A | no — supplements | 🚫 PENDING operator authorization in future batch |
| `command_center_snapshots` (OPTIONAL) | Cached snapshots if compute exceeds 60-sec freshness target | Phase B | no | 🚫 NOT REQUIRED in Phase A — compute on demand |

**Net-new collections beyond these two: zero.** Every widget reuses existing collections.

---

## 4 · Net-new endpoint requirements

| Endpoint | Method | Purpose | Auth | Phase | Authorized? |
|---|---|---|---|---|---|
| `/api/admin/command-center/snapshot` | GET | Single read endpoint returning the full snapshot JSON described in `EXECUTIVE_COMMAND_CENTER_SPEC.md` §6 | admin-strict | Phase A | 🚫 PENDING |
| `/api/admin/command-center/thresholds` | GET · PATCH | Read/update `command_center_thresholds` config doc | admin-strict + `X-Directory-Token` | Phase A | 🚫 PENDING |
| `/api/admin/command-center/snapshot.csv` | GET | CSV export of the snapshot for executive meetings / boards | admin-strict | Phase B | 🚫 PENDING |

**Net-new endpoints beyond these three: zero.** Every drill action reuses existing detail endpoints (see `EXECUTIVE_COMMAND_CENTER_SPEC.md` §6).

---

## 5 · Net-new frontend pages

| Page | Phase | Authorized? |
|---|---|---|
| `/admin/command-center` (single page · Pulse Strip + Priority Stack + 10 cards) | Phase A | 🚫 PENDING |
| `/admin/command-center/thresholds` (small admin form to tune rules) | Phase A | 🚫 PENDING |
| `/admin/command-center/recommender-detail` (Top-20 ranked list) | Phase B | 🚫 PENDING |

**Net-new pages beyond these three: zero.** No portal is duplicated; no existing dashboard is modified.

---

## 6 · Proposed `command_center_thresholds` config schema (Phase A · PENDING AUTHORIZATION)

```json
{
  "_id": "command_center_thresholds",
  "version": 1,
  "updated_at": "2026-MM-DDTHH:MM:SSZ",
  "updated_by": "<directory_user_id>",
  "rules": {
    "JOBS-1": { "amber": 2,  "red": 5  },
    "JOBS-2": { "amber": 1,  "red": 3  },
    "JOBS-3": { "amber": 1,  "red": 1  },
    "SAF-1":  { "amber": 1,  "red": 3  },
    "SAF-2":  { "amber": 1,  "red": 3  },
    "SAF-3":  { "amber": 1,  "red": 1  },
    "SAF-4":  { "amber": 2,  "red": 4  },
    "EQP-1":  { "amber": 1,  "red": 3  },
    "EQP-2":  { "amber": 1,  "red": 1  },
    "EQP-3":  { "amber": 1,  "red": 3  },
    "EQP-4":  { "amber": 1,  "red": 1  },
    "ACC-1":  { "amber": 5,  "red": 15 },
    "ACC-3":  { "amber": 5,  "red": 15 },
    "PML-1":  { "amber": 12, "red": 24 },
    "PML-2":  { "amber": 1,  "red": 1  },
    "SUP-1":  { "amber": 15, "red": 25 },
    "SUP-2":  { "amber": 1,  "red": 3  },
    "APP-1":  { "amber_days_min": 3,  "amber_days_max": 4 },
    "APP-2":  { "red_days_min": 5,   "red_days_max": 6 },
    "APP-3":  { "red_days_min": 7 },
    "APP-4":  { "amber": 1,  "red": 3  },
    "PRJ-1":  { "amber_days_no_dr": 3, "red_days_no_dr": 5 },
    "PRJ-2":  { "amber_variance_pct": 10, "red_variance_pct": 25 },
    "BNK-1":  { "amber": 1,  "red": 5  },
    "BNK-2":  { "amber": 3,  "red": 10 },
    "BNK-4":  { "amber": 1,  "red": 3  },
    "BNK-5":  { "amber": 1,  "red": 5  }
  }
}
```

The config doc is the **single source of truth** for tuning. No threshold may live in JSX or Python literals.

---

## 7 · Ownership table — who fixes the data when it's wrong

| Card | Data quality owner | Escalation path (Pillar 4 territory · for reference only) |
|---|---|---|
| Jobs Today | Admin (job master) + PM (assignment) | Admin Hub → PM Activity panel |
| Safety Today | Safety lead | Safety Hub → Admin Console |
| Equipment Today | Shop Manager | Shop Hub → Admin Equipment panel |
| Accountability Overdue | each task's assignee | individual portal notifications |
| PM Load | Operations Director | Admin PM panel |
| Supervisor Load | Operations Director + HR | Admin FL users panel |
| Approvals Aging | Approval-routing leadership (per `APPROVAL_PERMISSION_MATRIX.md`) | Admin PO panel |
| Projects at Risk | PM + Operations Director | Admin Job + PM panel |
| Operational Bottlenecks | Operations Director | per-domain detail page |
| Recommender | — (derived) | — |

When data is wrong on a card, leadership clicks through to the existing detail page; the existing owner is already wired to fix it. The Command Center never introduces a parallel ownership chain.

---

## 8 · Summary

- 9 of 10 cards: **0 new collections, 0 new workflows, 0 new endpoints** beyond the single snapshot synthesizer.
- 1 card (PRJ-2 cost variance, Phase B): optional — gated on existing `projects.pnl` data; rule disabled when data missing.
- The implementation footprint is **synthesis + scoring + presentation**, not new data plumbing.
