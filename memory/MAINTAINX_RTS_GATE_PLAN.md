# MAINTAINX · RTS GATE PLAN  (Phase 5)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes, no MaintainX traffic)

This document defines the Return-to-Service gate that closes the loop **after** a MaintainX Work Order is completed. ForgedOps RTS is the operational authority — MaintainX completion alone does NOT make the asset available again.

---

## 1 · Sequence (canonical)

```
                                                    +--------------------------+
   Defect originated                                |  ForgedOps source row    |
   ───────────────────                              |  (fleet_defects /        |
                                                    |  equipment_inspections / |
   1) Source writes defect row                      |  asset_holds)            |
   2) Canonical defect payload built                +-------------+------------+
   3) Push WO → MaintainX                                         |
   4) MaintainX returns wo.id                                     |
   5) external_refs stamped on source row ◀────────────────────────+
   6) Asset marked OOS in ForgedOps                                |
                                                                  ▼
                                            +─────────────────────────────────+
                                            │   MaintainX shop performs work  │
                                            +─────────────────────────────────+
                                                                  │
                                                                  │ (a) WO closed in MaintainX
                                                                  ▼
                                            +─────────────────────────────────+
                                            │   Webhook: workOrder.completed  │
                                            +─────────────────────────────────+
                                                                  │
                                                                  │ correlates by externalId / wo.id
                                                                  ▼
                                            +─────────────────────────────────+
                                            │  ForgedOps RTS Queue            │
                                            │  (mirror status: WO closed,     │
                                            │   awaiting RTS verification)    │
                                            +─────────────────────────────────+
                                                                  │
                                                                  │ Shop verification + Dispatch clear
                                                                  ▼
                                            +─────────────────────────────────+
                                            │  Asset returned to service       │
                                            │  ForgedOps clears OOS            │
                                            +─────────────────────────────────+
```

---

## 2 · Which sources require an RTS gate?

| Source | RTS gate? | Who closes the gate? |
| --- | --- | --- |
| Fleet DVIR OOS | **YES** | Dispatch (via `POST /api/dispatch/fleet/defects/{id}/clear`) **after** Shop signs the repair AND MaintainX WO is closed |
| Trailer DVIR OOS | **YES** | Dispatch |
| Service Truck / Pickup OOS | **YES** | Dispatch |
| Manual OOS flip (Shop or Dispatch) | **YES** | Dispatch (same `/clear` route) |
| Heavy Equipment Pre-Op OOS | **YES** | Admin / Shop (via `POST /api/admin/operations/holds/{id}/release`) |
| Manual maintenance request | **YES** | Admin / Shop (same hold-release route) |
| DVIR Monitor / Pre-Op monitor (non-OOS) | NO RTS gate | Defect auto-clears when shop closes the WO; ForgedOps reflects via webhook only |

---

## 3 · Approver / evidence matrix

| Gate | Approver role | Required evidence | Server-side check |
| --- | --- | --- | --- |
| Dispatch `/clear` for an OOS defect linked to a MaintainX WO | Dispatch (or Admin override) | MaintainX WO status ∈ {`Done`,`Completed`,`Cancelled`} | `GET /v1/work-orders/{id}` at clear-time; cache for 60s |
| Hold `release` for a heavy-equipment hold linked to a MaintainX WO | Admin / Shop (or Admin override) | Same | Same |
| Override path | Admin only | Operator name + free-text reason; logs an audit row `rts_override_pre_wo_close` | Required when WO status is not closed yet |

The `external_refs.maintainx_work_order_id` on the source row is the ONLY field consulted to decide whether the gate is "armed". If the field is empty (no WO was pushed — e.g. monitor severity), the gate is bypassed and standard RTS proceeds.

---

## 4 · State table for the link

| Source row state | MaintainX WO state | Allowed RTS action |
| --- | --- | --- |
| `open` | not yet pushed | none (defect must first be acknowledged + repaired internally) |
| `repaired` | not yet pushed | `clear` allowed (gate not armed) |
| `repaired` | `Open` / `In Progress` | `clear` BLOCKED — `409 Conflict` unless override |
| `repaired` | `On Hold` | `clear` BLOCKED — same |
| `repaired` | `Done` / `Completed` / `Cancelled` | `clear` ALLOWED |
| `cleared` (RTS done) | `Open` (still!) | This is a "MaintainX closed but ForgedOps RTS failed" inversion — see §5 |

---

## 5 · Edge cases

### 5.1 MaintainX closes but ForgedOps RTS fails (e.g. shop tech closed the WO without confirming repair)

- Webhook event arrives → ForgedOps writes an audit row `wo_completed_without_rts` on the source row.
- The source row remains in `repaired` (NOT `cleared`).
- Dispatch / Shop sees a banner on the row: "MaintainX WO closed — RTS still required".
- Dispatch must still issue a `/clear` to formally return the asset.
- This guards against: a tech mis-clicks "Done" in MaintainX; ForgedOps RTS does NOT auto-complete.

### 5.2 ForgedOps RTS clears before MaintainX WO closes (forbidden path)

- The gate logic in §3 BLOCKS this path on the server with `409 Conflict` and a structured error body:

  ```jsonc
  {
    "ok": false,
    "code": "maintainx_wo_still_open",
    "message": "MaintainX WO mx-12345 is still in status 'In Progress'. Wait for closure or use admin override.",
    "wo_id": "mx-12345",
    "wo_status": "In Progress",
    "override_required": true
  }
  ```

- If the admin chooses override, an audit row `rts_override_pre_wo_close` is written capturing `wo_id`, `wo_status_at_override`, `override_reason`, `override_actor`. The MaintainX WO is NOT mutated by ForgedOps.

### 5.3 WO push initially failed; defect is now repaired locally

- `external_refs.maintainx_work_order_id` is empty (the push went into `maintainx_sync_pending`).
- The gate is NOT armed (no WO id to check).
- Standard RTS proceeds — but a banner on the row tells the operator "MaintainX WO push was not successful — retry from Integration Center" with a deep link.

### 5.4 Webhook delivery missing (network drop)

- Status of `wo.id` is fetched lazily at RTS-time via `GET /v1/work-orders/{id}` (60s cache).
- This means even if the webhook was lost we will still surface the latest status at the moment a human pushes `/clear`.

---

## 6 · No auto-write to MaintainX from the RTS gate

The RTS gate ONLY reads MaintainX status. It MUST NOT, in this design:

- Close the MaintainX WO automatically on ForgedOps `/clear`.
- Cancel a MaintainX WO automatically.
- Modify any MaintainX-side data.

A future P1 sprint may add an OPTIONAL "Close WO on RTS" toggle behind explicit admin authorization, but that is **not** part of the canonical RTS gate.

---

## 7 · Per-source code touch list (planned · not built this sprint)

| File | Add |
| --- | --- |
| `backend/routes/fleet_ops.py` (defect `/clear` route around line 880) | Pre-call check: if `defect.external_refs.maintainx_work_order_id` is set → call `maintainx_client.get_work_order(...)` → enforce table §4. |
| `backend/routes/operations.py` (`release_hold(...)` around line 350) | Same pre-call check against the hold's linked WO id. |
| `backend/routes/integrations/webhooks.py` (`process_webhook`) | On `workOrder.statusUpdated` / `workOrder.completed` events, find the source row via `external_refs.*`, mirror status into a new field `external_refs.maintainx_wo_status` + `maintainx_wo_completed_at`. Never auto-clear. |
| `backend/services/maintainx_client.py` | Add `get_work_order(wo_id)` (still read-only; safe to ship now if operator authorizes Phase 6+). |

None of these are touched in this Phase-5 planning sprint.

---

## 8 · Verdict — Phase 5 RTS Gate Design

```
RTS GATE DESIGN  :  COMPLETE

  Sequence diagram                          : DEFINED
  Per-source gating table                   : DEFINED
  Approver + evidence matrix                : DEFINED
  Server-side enforcement points            : LISTED (not built)
  Edge cases (4)                            : DOCUMENTED
  No auto-write to MaintainX                 : INVARIANT
```

— End of Phase 5 RTS Gate Plan —
