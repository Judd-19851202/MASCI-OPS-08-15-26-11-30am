# Track 13.19 — Material Movement Ledger · Phase A · Proof-Join + Verification Foundation

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION (single-file backend enrichment)
**Doctrine:** TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md
**Verdict:** ✅ **PASS** · all 9 targeted tests green · backward-compatible · zero new collection · zero UI change.

---

## 1 · Executive Summary

Phase A of the Material Movement Ledger is **complete**. The existing
`/api/material-movement/daily/{project_number}/{date}` endpoint is now an enriched derived
view that:

* Joins **scale-ticket proof** from `operational_attachments` (Track 13.14 family) onto dispatch row ids.
* Joins **derived haul cycles** from `haul_cycles` by `(project_number, completed_at)` day prefix.
* Surfaces virtual `verification_status` from a closed-set classifier.
* Surfaces `proof_summary{}`, `rollups{}`, and `source_breakdown{}` counters.
* Preserves every legacy response key verbatim — `MaterialMovementTile.jsx` and any other
  consumer continues to function untouched.
* Writes **nothing**. No new collection. No source mutation. No FleetWatcher fabrication.

**Single file changed:** `backend/routes/material_movement.py`.
**Tests added:** `backend/tests/test_track_13_19_material_movement_phase_a.py` (9 cases · all pass).

---

## 2 · Source Verification (Phase 0)

### 2.1 Backend baseline

| Item | Value |
| ---- | ----- |
| Endpoint file | `backend/routes/material_movement.py` |
| Route | `GET /api/material-movement/daily/{project_number}/{date}` |
| Auth | Public read (same posture as `/api/jobs`) |
| Legacy response keys | `project_number`, `date`, `dispatch{assignments,loads,trucks,by_haul_type,rows}`, `incoming[]`, `outgoing[]` |
| Existing sources read | `dispatch_assignments`, `daily_reports` (materials[], outbound_materials[]) |
| `production[]` posture | INTENTIONALLY EXCLUDED (MM-001B-F1) |
| Track 13.14 fields confirmed in `operational_attachments` | `weight_gross_lbs`, `weight_tare_lbs`, `weight_net_lbs`, `material_code` |
| Track 13.14 attachment types canonical | 12 types, of which 5 are proof-bearing (see §5) |
| `operational_attachments.host_kind` | walking-skeleton = `assignment` only |
| `haul_cycles` collection | exists, written by `dispatch_lifecycle._materialize_haul_cycle()` on COMPLETE |
| `odr.MaterialEvent` | exists; Phase A does NOT join (deferred per Track 13.18 §7) |
| FleetWatcher | NOT_CONNECTED (env key absent; `_fleetwatcher_template()` returns all None) |
| MaintainX | out of scope |

### 2.2 Frontend baseline

| Item | Value |
| ---- | ----- |
| Tile consumer | `frontend/src/components/MaterialMovementTile.jsx` |
| Tile mount | `frontend/src/pages/ViewDailyReport.jsx` |
| PM consumer | `frontend/src/pages/PmCommandCenter.jsx` (separate `/pm/command-center/materials` endpoint — not the rollup endpoint) |
| Dispatch consumer | `frontend/src/components/dispatch/AttachmentStrip.jsx` reads `/api/operational-attachments/list` directly — does NOT consume the rollup endpoint |
| Driver consumer | **NONE** — no driver-facing material UI exists today |

### 2.3 Driver flow verification

* `/shift`, `/d/:token`, `/driver` routes confirmed present in `frontend/src/App.js`.
* `frontend/src/pages/driver/` directory contains `DriverMagicLanding.jsx`, `DriverShift.jsx`, `ShiftStart.jsx`. **No attachment UI.**
* `backend/routes/dispatch_driver.py` does NOT import or call `operational_attachments`.
* `operational_attachments` upload endpoint requires `require_dispatch_or_admin_dep` — drivers cannot upload scale tickets today.
* **Conclusion:** Drivers do not contribute scale-ticket proof today. See §10.

---

## 3 · Existing Endpoint Baseline

```
GET /api/material-movement/daily/{project_number}/{date}
→ 200 {
    "project_number": "...",
    "date": "...",
    "dispatch": { "assignments": int, "loads": int, "trucks": int,
                  "by_haul_type": {...}, "rows": [...] },
    "incoming": [...],   // from daily_reports.materials[]
    "outgoing": [...]    // from daily_reports.outbound_materials[]
  }
```

422 on whitespace-only `project_number` or `date`.

---

## 4 · Enriched Response Shape

Six additive top-level keys. Every legacy key preserved verbatim.

```jsonc
{
  // ── Legacy (unchanged) ─────────────────────────────────────
  "project_number": "...",
  "date": "...",
  "dispatch": { "assignments": 0, "loads": 0, "trucks": 0,
                "by_haul_type": {}, "rows": [] },
  "incoming": [],
  "outgoing": [],

  // ── Phase A additive ───────────────────────────────────────
  "scale_ticket_proofs": [
    {
      "id": "...",                            // attachment id
      "type": "scale_ticket" | "asphalt_ticket" | "delivery_receipt" | "dump_receipt" | "tanker_BOL",
      "host_kind": "assignment",
      "host_id": "...",
      "dispatch_assignment_id": "...",        // mirror of host_id
      "truck_id": "..." | null,               // joined from dispatch row
      "driver_name": "..." | null,            // joined from dispatch row
      "material_code": "..." | null,
      "weight_gross_lbs": 0.0 | null,
      "weight_tare_lbs":  0.0 | null,
      "weight_net_lbs":   0.0 | null,
      "net_tons":         0.0 | null,         // derived = net_lbs / 2000
      "uploaded_by": "...",
      "uploaded_role": "...",
      "uploaded_at": "...",
      "operational_note": "...",
      "filename": "...",
      "content_type": "image/jpeg",
      "source": "scale_ticket"
    }
  ],
  "haul_cycles": [
    {
      "id": "...",
      "assignment_id": "...",
      "truck_id": "...",
      "driver_name": "...",
      "material": "...",
      "haul_type": "Material" | "Equipment" | ...,
      "source_location": "...",
      "destination": "...",
      "started_at": "...",
      "completed_at": "...",
      "total_seconds": 0,
      "wait_seconds": 0,
      "operating_seconds": 0,
      "transitions": 0
    }
  ],
  "proof_summary": {
    "scale_ticket_count": 0,
    "scale_ticket_net_lbs": null | float,
    "scale_ticket_net_tons": null | float,
    "missing_proof_count": 0,
    "matched_proof_count": 0,
    "partial_proof_count": 0
  },
  "rollups": {
    "inbound_count": 0,
    "outbound_count": 0,
    "haul_cycles_count": 0,
    "scale_ticket_count": 0,
    "loads_count": 0,
    "trucks_count": 0,
    "materials_count": 0,
    "net_lbs_from_tickets": null | float,
    "net_tons_from_tickets": null | float
  },
  "verification_status": "no_activity" | "verified" | "partial" | "missing_proof" | "needs_review",
  "source_breakdown": {
    "daily_reports": 0,
    "dispatch_assignments": 0,
    "haul_cycles": 0,
    "scale_tickets": 0,
    "odr_events": 0,
    "fleetwatcher": 0
  }
}
```

**Hard guarantees:**
* `proof_summary.scale_ticket_net_lbs` / `.scale_ticket_net_tons` and `rollups.net_lbs_from_tickets` / `.net_tons_from_tickets` are `null` when no structured net was found — **never a fabricated 0**.
* `source_breakdown.fleetwatcher` is **always 0** (no live FleetWatcher).
* `source_breakdown.odr_events` is **always 0** in Phase A (ODR join deferred).

---

## 5 · Proof-Join Logic (Phase 2)

### Join keys

* `operational_attachments.host_kind == "assignment"` (only host_kind today)
* `operational_attachments.host_id IN { dispatch_rows[*].id }`
* `operational_attachments.type IN { scale_ticket, asphalt_ticket, delivery_receipt, dump_receipt, tanker_BOL }`

### Why these 5 attachment types

These are the operational-attachment kinds that **materially evidence a haul/delivery**:

| Type              | Why it counts as proof                                                      |
| ----------------- | --------------------------------------------------------------------------- |
| scale_ticket      | Track 13.14 carries structured weight + material code                       |
| asphalt_ticket    | Mix ticket from asphalt plant — proves what was hauled in                   |
| delivery_receipt  | Vendor delivery confirmation — proves inbound                               |
| dump_receipt      | Landfill / soil recycling receipt — proves outbound                         |
| tanker_BOL        | Bill of Lading for liquid asphalt — proves liquid product haul              |

Excluded: `load_photo`, `damage_photo`, `breakdown_photo`, `inspection_photo`,
`transfer_document`, `fuel_receipt`, `operational_note_photo` — these are operational
context, not material movement proof.

### Enrichment fields on each proof row

* `truck_id` / `driver_name` — joined read-only from the source dispatch row when found.
* `net_tons` — derived `weight_net_lbs / 2000` (US short tons). `None` when net is absent.
* `source: "scale_ticket"` label (Phase A normalizes all 5 proof types under this label;
  the original `type` is preserved beside it).

### Hard rules followed

* No fuzzy matching. The join uses `host_id` only.
* No record mutation. Read-only projection.
* No new collection. No verification persistence.
* `weight_net_lbs` is **not fabricated** — only summed when at least one row carries it.

---

## 6 · Verification Status Logic (Phase 3)

| Condition                                                                                          | Status            |
| -------------------------------------------------------------------------------------------------- | ----------------- |
| No dispatch rows, no incoming, no outgoing, no haul cycles, no proof attachments                   | `no_activity`     |
| Daily-report-only day (incoming or outgoing present) with no dispatch and no proof                 | `needs_review`    |
| Dispatch rows present, every row has at least one proof attachment                                 | `verified`        |
| Dispatch rows present, some have proof, some do not                                                | `partial`         |
| Dispatch rows present, zero proof attachments                                                      | `missing_proof`   |
| Any other ambiguous combination (fallback)                                                         | `needs_review`    |

* `mismatch` is documented in the §4 closed set but **not emitted in Phase A** — quantity
  reconciliation between Daily Report totals and structured net-weight tickets requires
  unit-aware comparison + tolerance config that Phase D will own. Deliberate conservatism:
  better to under-claim verification than over-claim.
* No persistence. The label is recomputed on every read.

---

## 7 · Rollup Counter Logic (Phase 4)

| Counter                     | Source                                                            | Notes                                                                                                            |
| --------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `inbound_count`             | length of `incoming[]`                                            | Foreman-authored inbound rows.                                                                                   |
| `outbound_count`            | length of `outgoing[]`                                            | Foreman-authored outbound rows (K-MM-2).                                                                         |
| `haul_cycles_count`         | length of joined `haul_cycles[]`                                  | Dispatch completion truth.                                                                                       |
| `scale_ticket_count`        | length of `scale_ticket_proofs[]`                                 | Proof rows count.                                                                                                |
| `loads_count`               | Σ `dispatch_rows[*].load_count`                                   | Existing field; null/empty treated as 0.                                                                         |
| `trucks_count`              | unique `dispatch_rows[*].truck_id`                                | Existing computation.                                                                                            |
| `materials_count`           | unique lowercased material descriptions across all sources        | Best-effort dedup (free-text materials).                                                                         |
| `net_lbs_from_tickets`      | Σ `proofs[*].weight_net_lbs` when present                         | `null` when zero proofs carry net; **never** synthesizes a 0 to look complete.                                  |
| `net_tons_from_tickets`     | `net_lbs_from_tickets / 2000`                                     | `null` when net_lbs is null.                                                                                     |

No financial totals. No cost totals. No pay-quantity totals.

---

## 8 · Driver-Scoped Contribution Findings (Phase 5)

### Today

| Question                                                          | Answer | Evidence |
| ----------------------------------------------------------------- | ------ | -------- |
| Can driver see current assigned load?                             | YES (read) | `/d/:token` + `dispatch_driver.py` |
| Can driver see next assigned load?                                | NO | `dispatch_driver.py` returns current truck rotation only |
| Can driver confirm what they are hauling?                         | PARTIAL — via state transitions only | dispatch lifecycle state machine |
| Can driver attach scale ticket?                                   | **NO** | `operational_attachments/upload` requires `require_dispatch_or_admin_dep` |
| Can driver enter gross/tare/net/material_code (Track 13.14)?      | **NO** | Same gate as above |
| Can driver mark loaded/dumped/problem?                            | PARTIAL — via state transitions | dispatch lifecycle |
| Can driver report load issue?                                     | NO dedicated path | only via dispatch state |

### How Phase A consumes driver records today

* Driver state transitions write to `dispatch_assignments.state_history`.
* On `COMPLETE`, `_materialize_haul_cycle()` writes a row to `haul_cycles`.
* **Phase A reads these haul_cycles** and surfaces them under `haul_cycles[]`. This is the
  driver's indirect contribution to the ledger today.

### Future gap (NOT built in this track)

A future **Phase Driver-Scoped Load Confirmation** would let the driver upload a scale
ticket scoped to their current assignment without elevating to dispatch/admin. That work is
out of scope here per the Track 13.19 hard rules. The data path is ready — only the
auth-gate widening and a thin driver UI are missing.

**No driver UI / driver portal / driver login was created or modified in this track.**

---

## 9 · Files Changed

| File                                                                       | Change                                                                                                                                                                       |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/routes/material_movement.py`                                      | Replaced with enriched implementation. All legacy fields preserved; six additive fields added (`scale_ticket_proofs`, `haul_cycles`, `proof_summary`, `rollups`, `verification_status`, `source_breakdown`). Imports `Optional` from typing. Adds private `_PROOF_ATTACHMENT_TYPES` set + `_net_lbs_to_tons()` helper. No other module touched. |
| `backend/tests/test_track_13_19_material_movement_phase_a.py`              | NEW · 9-case live-preview test suite.                                                                                                                                       |

**No other backend file was modified.**
**No frontend file was modified.**

---

## 10 · Endpoints Touched

| Endpoint                                                       | Change                                                                                              |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `GET /api/material-movement/daily/{project_number}/{date}`     | Response enriched with 6 additive keys. Legacy keys preserved. Status codes unchanged. Auth unchanged. |

**No other endpoint touched.**

---

## 11 · Collections Touched

* **READ:** `dispatch_assignments`, `daily_reports`, `operational_attachments`, `haul_cycles`.
* **WRITE:** *(none)* — Phase A is pure read.
* **NEW:** *(none)* — no new collection.

---

## 12 · Tests Added / Run

`backend/tests/test_track_13_19_material_movement_phase_a.py` — 9 cases:

| # | Case                                                            | Result |
| - | --------------------------------------------------------------- | ------ |
| 1 | Legacy keys preserved on empty day                              | PASS   |
| 2 | Phase A additive keys present on empty day                      | PASS   |
| 3 | `proof_summary` shape on empty day                              | PASS   |
| 4 | `rollups` shape on empty day                                    | PASS   |
| 5 | `source_breakdown` shape + FleetWatcher hard-zero               | PASS   |
| 6 | `verification_status` in closed set                             | PASS   |
| 7 | Input validation preserved (whitespace-only project_number)     | PASS   |
| 8 | Idempotent · no side effects                                    | PASS   |
| 9 | Live-data response shape (best-effort)                          | PASS   |

```
============================== 9 passed in 2.29s ===============================
```

Track 13.14 scale-ticket pytest suite was **not re-run** in this track (no code path
touched in `operational_attachments.py`). Track 13.17 PO-lifecycle pathway untouched.

---

## 13 · Backward Compatibility Results

| Consumer                                                | Test                                                                                              | Result |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------ |
| `MaterialMovementTile.jsx`                              | Curl response carries `dispatch{assignments,loads,trucks,by_haul_type,rows}`, `incoming[]`, `outgoing[]` | ✅ Preserved verbatim |
| `ViewDailyReport.jsx` (tile mount)                      | Tile renders or hides identically — extra fields ignored                                          | ✅ Forward-compatible |
| PM Command Center `/pm/command-center/materials`        | Separate endpoint; not touched                                                                    | ✅ Unaffected |
| Dispatch `/api/operational-attachments/list`            | Separate endpoint; not touched                                                                    | ✅ Unaffected |
| Driver `/shift`, `/d/:token`, `/driver`                 | Not touched; no auth/gate change                                                                  | ✅ Unaffected |
| Track 13.17 PO lifecycle notifications                  | Separate router; not touched                                                                      | ✅ Unaffected |
| Track 13.14 scale-ticket fields                         | Read-only consumed; structure preserved on attachment side                                        | ✅ Unaffected |

---

## 14 · Hard-Lock Regression Results (Phase 8)

| Hard lock                                                  | Verified | Method |
| ---------------------------------------------------------- | -------- | ------ |
| Dispatch Map-First (MapLibre canvas)                       | ✅       | `DispatchSideNavV2.jsx`, `DispatchCommandCenter.jsx` not touched |
| Driver no-login (`/shift`, `/d/:token`, `/driver`)         | ✅       | No driver route added; no driver auth widened |
| No DriverHubV2 revival                                     | ✅       | `frontend/src/App.js` not touched |
| Shop Repair ≠ Returned-To-Service                          | ✅       | `shop_*` routes not touched |
| One map engine                                             | ✅       | No new map mount |
| Track 13.17 PO lifecycle notifications                     | ✅       | `po_requests.py` not touched |
| Track 13.14 scale-ticket extension                         | ✅       | `operational_attachments.py` not touched; fields read identically |
| Track 13.13 Operational Events project-day panel           | ✅       | `operational-events` endpoint smoke = 200 |
| ODR surfacing                                              | ✅       | ODR routes not touched |
| PM Hub, Admin Hub                                          | ✅       | No hub file touched |
| No new collection                                          | ✅       | Code search confirms read-only |
| FleetWatcher remains NOT_CONNECTED                         | ✅       | `source_breakdown.fleetwatcher == 0` enforced by test #5 |

---

## 15 · What Was NOT Built

* ❌ No new collection
* ❌ No new endpoint (existing endpoint enriched in-place)
* ❌ No new UI component
* ❌ No driver UI / no driver portal / no driver login
* ❌ No Dispatch ledger screen (Phase C)
* ❌ No PM project material panel (Phase B)
* ❌ No Admin data-quality screen (Phase D)
* ❌ No FleetWatcher integration (Phase E)
* ❌ No ODR `MaterialEvent` join (deferred per Track 13.18 §7)
* ❌ No verification persistence (virtual label only)
* ❌ No quantity-mismatch detection (Phase D will own this)
* ❌ No `mismatch` verification_status (deliberate conservatism)
* ❌ No accounting / cost / pay-app / ERP / RFI / Submittal / Change Order / Doc Control
* ❌ No `tons_in` / `tons_out` rollups in non-ticket units (avoids unit-mixing bugs)
* ❌ No new permission model

---

## 16 · Five-Pillar Evaluation

| Pillar    | Score | Justification                                                                                                          |
| --------- | ----- | ---------------------------------------------------------------------------------------------------------------------- |
| Powerful  | 7/10  | Adds proof-join, virtual verification, six new counters in a single endpoint. Foundation for B/C/D in one read.        |
| Simple    | 9/10  | One file. One endpoint. One in-process join. Zero new collection. Zero new permission model. Zero UI churn.            |
| Beautiful | 8/10  | Response shape is clean, additive-only, closed-set status, never fabricates zeros for absent data.                      |
| Trusted   | 10/10 | Hard rules honored: no mutation · no FleetWatcher fakes · null beats fabricated zero · ODR join deferred not faked.    |
| Proven    | 9/10  | 9/9 targeted tests pass against live preview. Existing tile + Track 13.13/13.14/13.17 surfaces verified intact.       |

---

## 17 · Rollback Procedure

If Phase A must be reverted:

1. `git checkout HEAD~1 -- backend/routes/material_movement.py`
2. Delete `backend/tests/test_track_13_19_material_movement_phase_a.py`
3. `sudo supervisorctl restart backend`

Zero schema delta · zero collection delta · zero index delta · zero API contract delta
(legacy keys are a strict subset of the enriched response).

---

## 18 · Final Verdict

**Track 13.19 · CLOSED · PASS.**

Phase A of the Material Movement Ledger is live. The data foundation is ready for Phase B
(PM project panel), Phase C (Dispatch companion ledger), and Phase D (Admin data-quality
+ export) to be built on top without further endpoint churn.

Deployment readiness remains 🟢 **GREEN**.

---

## 19 · Recommended Track 13.20

**Track 13.20 — Material Movement Ledger · Phase B · PM Project Material Panel.**

* Single frontend file: `frontend/src/pages/PmProjectDetail.jsx`.
* Add a read-only Material Movement panel using the same Operational Events panel pattern from Track 13.13.
* Consume `/api/material-movement/daily/{project_number}/{report_date_picked}`.
* Surface: `verification_status` chip · `proof_summary` counts · `scale_ticket_proofs[]` list (truck/material/net_tons/uploaded_by) · honest empty state when `verification_status == "no_activity"`.
* Zero backend touch · zero new endpoint · zero new collection.
* Estimated effort: ~2 hours.
* Hard rule: PM scope = assigned projects only (project route enforces this).

---

## 20 · Final Response (per Track 13.19 §10)

1. **Track status:** CLOSED · PASS.
2. **Implementation summary:** Single backend file enrichment of `/api/material-movement/daily/{p}/{d}`. Six additive top-level keys. Zero new collection. Zero UI change. Zero FleetWatcher activation.
3. **Files changed:** `backend/routes/material_movement.py` (rewritten additively) · `backend/tests/test_track_13_19_material_movement_phase_a.py` (new).
4. **Endpoint changed:** `GET /api/material-movement/daily/{project_number}/{date}` — additive response only.
5. **New response fields:** `scale_ticket_proofs[]`, `haul_cycles[]`, `proof_summary{}`, `rollups{}`, `verification_status`, `source_breakdown{}`.
6. **Driver contribution findings:** Drivers contribute **indirectly today** via dispatch state transitions → `haul_cycles` materialization (now surfaced). Drivers cannot upload scale tickets today (auth-gated to dispatch/admin). Future Phase Driver-Scoped Load Confirmation documented but **not built**.
7. **Tests passed:** 9 / 9.
8. **Hard locks verified:** Map-First Dispatch · Driver no-login · DriverHubV2 retired · Shop RTS · one map engine · Track 13.14 · Track 13.13 · Track 13.17 · FleetWatcher NOT_CONNECTED · MaintainX OOS · no new collection.
9. **Blockers:** None.
10. **Recommended next build:** **Track 13.20 · Phase B · PM Project Material Panel** (single frontend file · ~2h).
