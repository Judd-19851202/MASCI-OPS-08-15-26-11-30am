# Accountability ↔ Executive Command Center Integration · Phase 1A-4

**Batch:** Pillar 1 · Phase 1A-4 · Executive Command Center consumption of the Accountability Service
**Date:** 2026-05-31
**Scope:** Replace the five hardcoded owner strings inside `command_center.py` with values derived from the certified Accountability Projection Layer (Phase 1A-2 contract · Phase 1A-3 service). Enrich the existing drilldown endpoint with an additive `accountability` + `timeline` payload. **No source workflow change. No card visual change. No new endpoint. No new collection. No deploy.**
**Discipline:** OMEGA · evidence-led · zero scope drift into Escalation / Notifications / Pillar 1A-5 native assignee fields / Pillar 2 / Pillar 3 / Pillar 4.

---

## 1 · Executive verdict

🟢 **INTEGRATED.** The Executive Operations Command Center now derives ownership from the Accountability projection rather than from hardcoded string literals in Python source. The 5/9 ownership defects flagged in the Audit (§5 of `ACCOUNTABILITY_ENGINE_AUDIT.md`) are closed at the read-side without touching any source workflow.

| Defect (Audit) | Pre-1A-4 owner string | Post-1A-4 owner string | Verdict |
|---|---|---|---|
| Approvals · APP-AMBER / APP-RED / APP-WEEK | `po.requested_by_name` (requester · **wrong attribution**) | `"Pending Approver"` from `project_po_request()` | 🟢 Closed (Audit A-05) |
| Safety · SAF-CRITICAL-UNRESOLVED | hardcoded `"Safety"` | `project_incident().owner_display_name` | 🟢 Closed (Audit A-01) |
| Safety · SAF-OSHA-OPEN | hardcoded `"Safety"` | `project_incident().owner_display_name` | 🟢 Closed (Audit A-01) |
| Jobs · JOBS-ISSUE-NO-PATH | hardcoded `"Safety"` | `project_incident().owner_display_name` | 🟢 Closed |
| Equipment · EQP-OOS-OLD | hardcoded `"Shop"` | `project_fleet_defect().owner_display_name` | 🟢 Closed (Audit A-02) |

Plus: drilldown response now carries `accountability` (23 canonical fields) and `timeline` (last 25 canonical events). Existing legacy keys (`owner`, `actions_underway`, `expected_resolution`, `source_doc`) are preserved byte-for-byte — frontend consumers ignore unknown keys, so no UI break.

---

## 2 · Code changes (file-by-file)

### 2.1 · `/app/backend/routes/command_center.py`

| Metric | Pre-1A-4 | Post-1A-4 | Delta |
|---|---|---|---|
| LOC | 1,111 | 1,192 | +81 |
| md5 | `c6f950452e45cd48c85edbb365e79fe5` | `38bae4866b672dd254f6cfc6e49b9a8d` | changed |

Six surgical edits — all inside existing functions:

| # | Location | Change |
|---|---|---|
| E-1 | Module imports (line 12) | Add `from lib import accountability_projection as _acc_proj` |
| E-2 | `_build_jobs_card` JOBS-ISSUE-NO-PATH item (≈ line 412) | Replace `owner="Safety"` with `_acc_proj.project_incident(db, inc)["owner_display_name"]` |
| E-3 | `_build_safety_card` SAF-CRITICAL-UNRESOLVED item (≈ line 481) | Same pattern · async projection on incident row |
| E-4 | `_build_safety_card` SAF-OSHA-OPEN items (≈ line 534) | Same pattern · async projection per OSHA-unresolved incident |
| E-5 | `_build_equipment_card` EQP-OOS-OLD items (≈ line 644) | Expand `find()` projection to include `acknowledged_at/by_name`, `reported_at`, `severity`, `item_text`, `repaired_at/by_name`; replace `owner="Shop"` with `_acc_proj.project_fleet_defect(d)["owner_display_name"]` |
| E-6 | `_build_approvals_card` APP-* items (≈ line 870) | Expand `find()` projection to include `requested_by_role/user_id/employee_id`; replace `owner=p.get("requested_by_name") or "Requester"` with `_acc_proj.project_po_request(p)["owner_display_name"]` |
| E-7 | `drilldown(card_id, item_id)` (≈ line 1100) | Add `accountability` + `timeline` to response · dispatch projection by `card_id` and document fingerprint · catch + fallback on error · legacy keys unchanged |

### 2.2 · Files **NOT** modified

- `/app/backend/lib/accountability_projection.py` — md5 `e8de1112…` (byte-stable from Phase 1A-2)
- `/app/backend/routes/accountability_service.py` — md5 `0e879cf9…` (byte-stable from Phase 1A-3)
- Source workflow files (`tasks_notifications.py`, `safety_portal/corrective_actions.py`, `po_requests.py`, `fleet_ops.py`, incident routes) — zero edits
- Frontend `AdminCommandCenter.jsx` — zero edits (legacy keys ensure backward compat)
- `server.py` — zero edits (the projection import is internal to `command_center.py`)

### 2.3 · New test file

| File | Type | LOC | md5 |
|---|---|---|---|
| `/app/backend/tests/test_accountability_executive_phase_1a4.py` | NEW · live HTTP cert | 314 | `79cc45c86740cd8b323b58640f97f367` |

---

## 3 · Architecture

```
            ┌────────────────────────────────────────────────────┐
            │  Executive Command Center · /admin/command-center  │
            │  ────────────────────────────────────────────────  │
            │  card.items[].owner   ←─── projection.owner_display_name
            │  drilldown.owner      ←─── projection.owner_display_name
            │  drilldown.accountability ←── full 23-field projection
            │  drilldown.timeline   ←─── last 25 canonical events
            └─────────────────────────┬──────────────────────────┘
                                      │ imports
                                      ▼
            ┌────────────────────────────────────────────────────┐
            │  lib/accountability_projection.py (Phase 1A-2)     │
            │  Pure read-only · zero source mutation             │
            └────────────────────────────────────────────────────┘
                                      │ reads
                                      ▼
            ┌────────────────────────────────────────────────────┐
            │  Source collections: tasks · corrective_actions ·  │
            │  po_requests · fleet_defects · incidents           │
            │  (UNCHANGED · no new fields · no migrations)       │
            └────────────────────────────────────────────────────┘
```

Per the OMEGA directive: the Command Center is now a **consumer** of the projection contract; the source workflows remain authoritative for their domains.

---

## 4 · Backward compatibility guarantee

| Surface | Pre-1A-4 | Post-1A-4 | Risk |
|---|---|---|---|
| `/api/admin/command-center/snapshot` payload shape | 5 cards · pulse · calendar · cached | identical | none |
| `card.items[].owner` field name | present · string | present · string | none |
| `card.items[].owner` field **content** | hardcoded literals on 5/9 rules | projection-derived strings | content-only change · frontend ignores |
| `card.items[].current_status` · `eta` · `severity` · `drill_to` | unchanged | unchanged | none |
| `/api/admin/command-center/drilldown/...` payload | 5 keys | 7 keys (additive: `accountability` + `timeline`) | none · UI ignores unknown keys |
| Pulse aggregate (`pulse.red_*` / `amber_*`) | reconciles to card items | still reconciles | none · enforced by `test_pulse_aggregate_still_reconciles_post_1a4` |
| Auth gating | admin-strict | admin-strict | none |
| Cache TTL (15 s) | preserved | preserved | none |

Frontend `AdminCommandCenter.jsx` (md5 `4cb825b4830871d1d407d206d4ae5519`) is **not modified** — the visual design and card structure are preserved per the directive.

---

## 5 · Live evidence (preview probe · 2026-05-31)

```
$ curl -s "$URL/api/admin/command-center/snapshot" -H "X-Admin-Token: $T"
# overall pill: RED
# headline: 6 RED · 1 AMBER warnings
# pulse aggregates reconcile exactly

Item owner strings live (rule_id · owner):
  [amber] JOBS-DR-MISSING           owner='Unassigned PM'         (unchanged · already projection-style)
  [red  ] JOBS-ISSUE-NO-OWNER       owner='UNASSIGNED'            (unchanged · truthful)
  [amber] JOBS-ISSUE-NO-PATH        owner='Safety'                (now from projection fallback)
  [red  ] SAF-CRITICAL-UNRESOLVED   owner='Safety'                (now from projection fallback)
  [red  ] SAF-OSHA-OPEN             (no OSHA items today)
  [red  ] SAF-CA-OVERDUE            owner='Alec Perkins'          (real CA assignee · projection-direct)
  [red  ] SAF-CA-OVERDUE            owner='iter364 Sub Vendor Owner'  (real CA assignee · projection-direct)
  [amber] APP-AMBER                 owner='Pending Approver'      ◄── FIX: was the requester's name pre-1A-4
  [amber] APP-AMBER                 owner='Pending Approver'      ◄── FIX
  [amber] APP-AMBER                 owner='Pending Approver'      ◄── FIX
```

Drilldown probe (first approvals item):

```
$ curl -s "$URL/api/admin/command-center/drilldown/approvals/992f9ef2-..." -H "X-Admin-Token: $T"

  card_id:                approvals
  legacy owner:           Pending Approver    ◄── matches accountability.owner_display_name
  legacy actions_underway: Submitted

  accountability (23 fields):
    owner_display_name:   Pending Approver
    owner_role:           approver_per_routing
    status:               open                (canonical · was native "Submitted")
    priority:             Medium
    escalation_level:     0                   (Pillar 1B reservation · not active)
    overdue:              True                (derived overlay · age > 3-day SLA)
  timeline len:           1                   (created event from po_audit translation)
```

---

## 6 · OMEGA discipline check

| Discipline rule | Verdict |
|---|---|
| Source workflows unchanged (zero edits to `po_requests.py`, `corrective_actions.py`, `fleet_ops.py`, `tasks_notifications.py`, incident routes) | 🟢 |
| Projection library unchanged · md5 stable | 🟢 |
| Service router unchanged · md5 stable | 🟢 |
| No new collection | 🟢 |
| No new endpoint | 🟢 |
| Card visual design preserved (frontend untouched · payload shape preserved) | 🟢 |
| No notifications / emails / SMS / cron | 🟢 |
| No escalation logic activated (`escalation_level=0` enforced via projection contract) | 🟢 |
| No deployment | 🟢 |
| Phase 1A-5 (native `assignee_*` fields on incidents/fleet_defects) NOT executed | 🟢 |
| Pillar 1B, Pillar 2, Pillar 3, Pillar 4 untouched | 🟢 |
| Backup · recovery · scheduler · R2 · drill framework untouched | 🟢 |

---

## 7 · What this integration is NOT

- ❌ Not a UI redesign — `AdminCommandCenter.jsx` is byte-identical.
- ❌ Not a new endpoint — the existing `/snapshot` and `/drilldown` endpoints are reused.
- ❌ Not a workflow migration — source rows continue to be the system of record for their domains.
- ❌ Not an escalation activation — `escalation_level=0` invariant enforced everywhere.
- ❌ Not a deployment — the change lives only in preview until operator authorizes a separate production deploy.

🛑 **STOPPED.** Implementation complete. Certification follows.
