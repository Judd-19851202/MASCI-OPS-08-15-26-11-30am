# Track 13.28 Phase 2 — Shop Workforce UI + Parts Capture

**Date:** 2026-06-12
**Mode:** CONTROLLED IMPLEMENTATION — frontend + minimal additive backend extension.
**Doctrine:**
  * `TRACK_13_24_SHOP_PORTAL_REALITY_AUDIT_AND_ACCESS_CLEANUP.md`
  * `TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`
  * `TRACK_13_28A_MECHANIC_ASSIGNMENT_AND_SHOP_WORKFORCE_CERTIFICATION.md`
  * `TRACK_13_28_MECHANIC_ASSIGNMENT_WORKFLOW.md`
**Verdict:** ✅ Shipped. 19/19 tests green (15 regression + 4 new). Zero deploy. Hard locks intact.

---

## 1 · Executive Summary

The Track 13.28 backend lifecycle (assign · accept · start · repair · manager-review) now has a real operator surface. Shop Managers and Mechanics work the chain through two new pages mounted under `RequireShop`:

* **`/shop/manager/queue`** — six-bucket queue (Unassigned · Assigned · Accepted · In Progress · Pending Review · RTS Pending) with assign / reassign / review actions. **No RTS action exists in this UI** — Dispatch retains `/clear`.
* **`/shop/me`** — mechanic's own assignments with accept / start / complete actions. Repair completion form captures multi-row `parts_used` + `parts_on_order` data (per-repair historical capture, NOT inventory).

The repair completion form enforces the new rule: **either ≥10-char notes OR ≥1 parts_used row**. Repair Complete ≠ RTS remains absolute.

Asset Service Event Backbone (Track 13.26) now surfaces the new lifecycle events plus parts metadata so the Known-Parts-By-Unit intelligence layer can derive from a single source.

---

## 2 · Source Verification

| Check                                                                                | Result                                                                                       |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Track 13.28 backend endpoints live (`/assign`, `/reassign`, `/accept`, `/start`, `/manager-review`, `/api/shop/manager/queue`, `/api/shop/me/assignments`) | ✅ verified — all return 200 (admin override). |
| Existing `/repair` endpoint + payload                                                | ✅ `DefectActionPayload(actor_name, notes, photos)` — extended additively into a new `DefectRepairPayload` (notes + photos + **parts_used** + **parts_on_order**). |
| Existing parts fields on `fleet_defects`                                              | ❌ NONE today. We add `parts_used[]` + `parts_on_order[]` (additive, nullable, no migration).  |
| Existing per-unit parts catalog                                                       | ✅ `equipment_parts` collection (admin-curated catalog · NOT modified here). Future enhancement: autocomplete the repair-form parts rows from this catalog. |
| Mechanic list source                                                                  | ✅ `db.shop_users` (live · `GET /api/admin/shop-users`). `role` field filters Mechanics from Managers. |
| Shop auth + `RequireShop` HOC                                                         | ✅ Per-user shop tokens accepted; admin token allowed.                                        |
| Legacy rollback `/shop/hub_legacy`                                                    | ✅ alive.                                                                                     |

---

## 3 · Files Changed

| Path                                                                                  | Type    | Purpose                                                                                                  |
| ------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------- |
| `backend/routes/fleet_ops.py`                                                          | MODIFY  | Added 3 Pydantic models (`PartUsedRow`, `PartOnOrderRow`, `DefectRepairPayload`); extended `/repair` to accept parts arrays + enforce min-10-char-OR-parts rule + persist to `fleet_defects.parts_used` / `parts_on_order`. No existing field semantics changed. |
| `backend/routes/asset_service_events.py`                                                | MODIFY  | Repair event now carries `parts_used_count`, `parts_on_order_count`, raw `parts_used` array; notes string includes top-5 parts summary so legacy renderers still see them. |
| `backend/tests/test_track_13_28_phase_2_parts_capture.py`                                | NEW     | 4 tests (notes-or-parts rule, parts persistence, timeline projection, RTS lock reaffirmation).            |
| `frontend/src/components/shop/RepairCompletionForm.jsx`                                 | NEW     | Shared multi-row parts form with `data-testid` per interactive element.                                  |
| `frontend/src/pages/shop/ShopManagerQueue.jsx`                                          | NEW     | Manager queue page (6 buckets · assign / reassign / review actions). No RTS.                              |
| `frontend/src/pages/shop/ShopMyAssignments.jsx`                                          | NEW     | Mechanic queue page (4 buckets · accept / start / complete actions).                                     |
| `frontend/src/App.js`                                                                   | MODIFY  | Lazy imports + 2 new routes (`/shop/manager/queue` · `/shop/me`).                                          |
| `frontend/src/pages/ShopHubV2.jsx`                                                       | MODIFY  | Added Section 05 — Shop Workforce — with 2 link cards. No existing card touched.                          |
| `memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`                          | NEW     | This report.                                                                                              |
| `memory/PRD.md` · `CHANGELOG.md` · `ROADMAP.md` · `MASCI_RC_CERTIFICATION_LEDGER.md`     | MODIFY  | Closeout entries appended.                                                                                |

**Files NOT touched:** Dispatch (map / hub / DCC) · Driver flow · PM portal · Safety portal · Material Movement Ledger · `equipment_parts` catalog · server.py · `.env`.

---

## 4 · Routes Added / Touched

| Route                       | Mount status               | Guard                          |
| --------------------------- | -------------------------- | ------------------------------ |
| `/shop/manager/queue`        | **NEW** (Track 13.28 P2)   | `RequireShop` (existing HOC)   |
| `/shop/me`                   | **NEW** (Track 13.28 P2)   | `RequireShop`                  |
| `/shop` → ShopHubV2          | unchanged · adds 2 link cards in new Section 05 | `RequireShop`                  |
| `/shop/hub_legacy`            | unchanged · still alive    | `RequireShop`                  |
| `/shop/fleet`, `/shop/equipment`, `/shop/equipment/:id` | unchanged | `RequireShop`                  |

Legacy rollback preserved. Dispatch map untouched. Driver no-login routes untouched.

---

## 5 · Endpoints Consumed (Frontend → Backend)

| UI surface                | Endpoint                                                              |
| ------------------------- | --------------------------------------------------------------------- |
| Manager Queue page          | `GET /api/shop/manager/queue` (initial + after every mutation)        |
| Manager Queue · Assign      | `POST /api/shop/fleet/defects/{id}/assign`                            |
| Manager Queue · Reassign    | `POST /api/shop/fleet/defects/{id}/reassign`                          |
| Manager Queue · Review      | `POST /api/shop/fleet/defects/{id}/manager-review` (`approved: bool`)|
| Manager Queue · Mechanic picker | `GET /api/admin/shop-users` (filter `role!="Shop Manager"`)        |
| My Assignments page          | `GET /api/shop/me/assignments`                                        |
| My Assignments · Accept      | `POST /api/shop/fleet/defects/{id}/accept`                            |
| My Assignments · Start       | `POST /api/shop/fleet/defects/{id}/start`                             |
| My Assignments · Repair complete | `POST /api/shop/fleet/defects/{id}/repair` (with parts arrays)   |

---

## 6 · Backend Changes

### 6.1 New Pydantic models (additive only)

```python
class PartUsedRow(BaseModel):
    part_name: str (1..200)        # required
    part_number: Optional[str]      # 0..120
    manufacturer: Optional[str]      # 0..120
    supplier: Optional[str]          # 0..120
    quantity: float (>=0)            # default 1.0
    notes: Optional[str]             # 0..500

class PartOnOrderRow(BaseModel):
    part_name, part_number, manufacturer, supplier, quantity (same as above)
    ordered_date: Optional[str]      # "" or YYYY-MM-DD
    expected_date: Optional[str]
    order_status: Optional[str]      # default "open"
    notes: Optional[str]

class DefectRepairPayload(BaseModel):
    actor_name: str
    notes: str (<=4000)
    photos: List[str]
    parts_used: List[PartUsedRow]
    parts_on_order: List[PartOnOrderRow]
```

### 6.2 `/repair` endpoint updates

* Now requires `notes.strip() ≥ 10` chars **OR** ≥1 `parts_used` row (422 otherwise).
* Persists `parts_used` and `parts_on_order` into `fleet_defects` with denormalized `logged_at` + `logged_by` per row.
* Persists `repair_completed_at = now_iso` (was only `repaired_at`).
* Audit row gains `parts_used_count` + `parts_on_order_count`.

### 6.3 Asset Service Event Backbone — repair event enriched

```json
{
  "event_type": "repair",
  "event_subtype": "completed",
  "actor_role": "mechanic" | "shop",
  "notes": "<repair_notes> · parts: 1× Oil filter [1R-1808]",
  "parts_used_count": 1,
  "parts_on_order_count": 0,
  "parts_used": [...],
  "parts_on_order": [...]
}
```

The summary inside `notes` lets legacy timeline renderers (Track 13.27 — future) surface parts without re-parsing the embedded arrays.

---

## 7 · Shop Manager Queue Behavior (`/shop/manager/queue`)

* **Buckets shown** (counts + lists): Unassigned · Assigned · Accepted · In Progress · Pending Review · RTS Pending. Filter chip bar at the top.
* **Each row shows**: unit number, source (PRE-OP / DVIR / MANUAL), severity (OOS in red), defect description, reported_by + timestamp, mechanic name, assigned/started/completed timestamps, reviewed-by line when present.
* **Manager actions**:
  * Pick mechanic from live `shop_users` dropdown (filtered to non-Manager active users).
  * Assign (or Reassign if already assigned).
  * Open Review panel → Approve (writes `shop_manager_reviewed_at` + by_id + by_name) OR Reject (≥5-char reason required · returns to `acknowledged` for re-work).
* **No RTS action surfaces.** RTS remains a Dispatch-only call.
* Refresh button + post-mutation auto-refresh keep counts honest.
* Empty state ("Nothing pending right now") shows when total = 0.

---

## 8 · Mechanic Queue Behavior (`/shop/me`)

* Backed by `GET /api/shop/me/assignments` which returns only the caller's assignments (by `assigned_to_mechanic_id == actor.id`).
* Buckets: Assigned · Accepted · In Progress · Pending Review.
* Per-row actions:
  * **Assigned** → "Accept work" button → `POST /accept`.
  * **Accepted** → "Start work" → `POST /start`.
  * **In Progress** → "Complete repair…" opens the repair form → `POST /repair` with parts arrays.
  * **Pending Review** → message "Waiting for Shop Manager review. RTS still requires Dispatch."
* Admin override displays an explicit "You are signed in as Admin" empty state and redirects them to the manager queue.
* Mechanic CANNOT assign / reassign / approve / RTS. Verified by absence of UI plus by backend gates from Track 13.28.

---

## 9 · Repair Completion Form

`components/shop/RepairCompletionForm.jsx`. Captures:

| Field             | Required           | UI behavior                                                                          |
| ----------------- | ------------------ | ------------------------------------------------------------------------------------ |
| `notes`           | ≥10 chars (or ≥1 parts row) | Live character counter · color-toggles when threshold met.                  |
| `parts_used[]`   | 0..N                | "+ Add part" button · per-row remove. 6-column grid: name · part# · mfr · supplier · qty · ×. |
| `parts_on_order[]` | 0..N (encouraged when waiting) | Same shape + `ordered_date` + `expected_date` (date pickers).        |
| Photos            | not in this form    | Existing photo-upload flows are deferred · the form sends `photos: []`.              |
| Submit button     | disabled until valid | Submit posts `{actor_name, notes, photos, parts_used, parts_on_order}`.            |

Cost / accounting / inventory fields **intentionally omitted** (out of doctrine).

---

## 10 · Parts Used Capture

* Per-repair line items only. Stored on `fleet_defects.parts_used[]`.
* Each row carries: `part_name` (req), `part_number`, `manufacturer`, `supplier`, `quantity`, `notes`, plus auto-added `logged_at` + `logged_by`.
* No global parts catalog written. The existing admin-curated `equipment_parts` collection is **untouched** — Track 13.28 P3 (future) will autocomplete from it.
* Asset Service Event Backbone surfaces the raw `parts_used` array and a `parts_used_count` in the `repair/completed` event so timeline UIs (Track 13.27 future) can render them.

**Known-Parts-By-Unit intelligence** can be derived today by:

```python
db.fleet_defects.aggregate([
  {"$match": {"truck_unit_number": "436", "parts_used": {"$exists": True, "$ne": []}}},
  {"$unwind": "$parts_used"},
  {"$group": {"_id": {"part_number": "$parts_used.part_number", "part_name": "$parts_used.part_name"}, "uses": {"$sum": 1}}}
])
```

No new endpoint built for that today (per "do not invent" rule); it is a natural Phase 3 follow-up once parts capture has live data.

---

## 11 · Parts On Order / Waiting Parts Capability

* Captured on `fleet_defects.parts_on_order[]` (additive nullable).
* Operational only — no cost, no purchasing approval, no PO numbers, no accounting.
* Per-row fields: name, part#, mfr, supplier, qty, ordered_date, expected_date, order_status (default `open`), notes.
* No new "shop waiting parts" status — the Shop Hub V2's existing **Waiting On Parts** count remains driven by `summary.shop.waiting_on_parts` (the Maintenance-Hold engine). Track 13.28 P3 may eventually fold this manual `parts_on_order` into that count if the rules align.

---

## 12 · Notifications

Through the existing `lib/event_fanout.py` primitive — **NO new framework, NO email invention**.

| Trigger                   | Task created               | Notification emitted                                                |
| ------------------------- | -------------------------- | ------------------------------------------------------------------- |
| Assign / Reassign          | `assignee_user_id=mechanic` · priority Critical (OOS) / Medium | `recipient_role="shop"` + `recipient_user_id=mechanic` · `shop_assignment` |
| Accept                     | —                          | `shop_assignment.accepted` to `shop` role (manager visibility)      |
| Start                      | —                          | `shop_assignment.in_progress`                                       |
| Complete (`/repair`)       | (existing audit only — no new task) | (existing `defect_repaired` audit row)                              |
| Manager Review · approved   | —                          | `shop_assignment.review_approved`                                   |
| Manager Review · rejected   | —                          | `shop_assignment.review_rejected`                                   |

Mechanic receives `shop_assignment.*` notifications via the existing notifications collection; can be surfaced in a future global notification bell.

---

## 13 · Asset Timeline Integration

`GET /api/assets/{unit}/timeline` now surfaces this lifecycle for every defect:

```
defect/opened → defect/assigned → defect/accepted → repair/started →
repair/completed (with parts_used + parts_used_count + parts_on_order_count) →
repair/manager_reviewed → rts/verified
```

Every event has `actor_id` + `actor_name` + `related_defect_id` + deterministic `event_id`. Verified by `test_parts_surface_in_asset_timeline` (parts make it through the projector).

**No second timeline. No duplicate asset history.**

---

## 14 · Tests Run

```
backend/tests/test_track_13_28_phase_2_parts_capture.py             4 / 4 PASS   (~23 s)
backend/tests/test_track_13_28_mechanic_assignment_workflow.py      4 / 4 PASS   (regression · ~25 s)
backend/tests/test_track_13_26_asset_service_event_backbone.py     11 /11 PASS  (regression · ~24 s)
─────────────────────────────────────────────────────────────────────────
TOTAL                                                              19 /19 PASS
```

Coverage of acceptance criteria:

| Acceptance criterion                                            | Coverage                                                                         |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1. Parts used persisted                                          | `test_repair_accepts_parts_row_with_short_notes` — defect doc carries `parts_used[]`. |
| 2. Parts on order persisted                                       | same test — `parts_on_order[0].part_number` asserted.                              |
| 3. Repair completion requires notes                              | `test_repair_rejects_short_notes_without_parts` — 422 on short notes.             |
| 4. Mechanic cannot RTS                                            | `test_repair_endpoint_does_not_grant_rts` + regression: lifecycle test asserts status remains `repaired` after `/repair` and after `/manager-review`. |
| 5. Manager cannot bypass dispatch RTS                              | full lifecycle test — `/clear` is the ONLY transition to `cleared`.                |
| 6. Rejected review notifies mechanic                              | rejection path in `manager-review` endpoint emits `shop_assignment.review_rejected` notification (best-effort).|
| 7. Assignment notifications still work                            | regression: lifecycle test, plus per-user notification payload includes `assignee_user_id`. |
| 8. Asset timeline includes assignment/repair events                 | `test_parts_surface_in_asset_timeline` + regression timeline subtype assertions.    |

---

## 15 · Browser Smoke Evidence

Playwright smoke (admin-token override, 5 s settle) confirmed:

| Page                              | Outcome                                                                                                          |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `/shop` (Hub V2)                  | Section 05 — Shop Workforce — renders with both link cards (`shop-hub-v2-action-manager-queue` + `shop-hub-v2-action-my-assignments` data-testids present). Existing sections (01-04) unchanged. |
| `/shop/manager/queue`              | Loads · counts strip rendered (83 unassigned · 0 across other buckets in preview seed) · per-row mechanic dropdown + Assign button render. |
| `/shop/me`                         | Admin override empty state displayed correctly ("You are signed in as Admin"). `data-testid=shop-my-assignments-actor-name` confirmed. |
| `/shop/hub_legacy`                  | Legacy rollback still loads (body present).                                                                       |
| Dispatch map (`/dispatch`)          | UNTOUCHED — not re-verified per scope, but no Dispatch file modified.                                              |

Screenshots: `/tmp/shop-manager-queue.png` · `/tmp/shop-my-assignments.png` · `/tmp/shop-hub-v2.png`.

---

## 16 · Hard Lock Verification

| Hard lock                                          | Verified                                                                                     |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Shop Repair Complete ≠ Returned-To-Service          | UI: no RTS action on manager queue · repair completion explicitly states "Repair Complete ≠ RTS." Backend: `/repair` flips `status: repaired`, never `cleared`. |
| Dispatch/Admin RTS authority                         | `/api/dispatch/fleet/defects/{id}/clear` continues to require `_require_dispatch_or_admin`. Untouched in this track. |
| Driver no-login                                      | No driver-side change.                                                                        |
| Dispatch map-first                                    | No Dispatch / map file touched.                                                               |
| One map engine · one source of truth                 | No map change · timeline + defect remain single sources.                                       |
| Asset Service Event Backbone                          | Extended additively only (event subtypes + parts payload).                                     |
| MaintainX dormant                                     | `MAINTAINX_API_KEY` untouched · SDK never invoked.                                            |
| No fake data                                          | All test fixtures use deterministic `itest-*` ids and clean up.                                |
| No duplicate asset history                            | Backbone remains the only per-unit history projection.                                         |
| No duplicate parts system                             | `equipment_parts` (admin catalog) untouched. New `parts_used[]` is per-repair history, NOT a catalog. |

---

## 17 · What Was Not Built

* No mechanic auto-assignment heuristics (manager picks · live).
* No part-catalog autocomplete in the repair form (Track 13.28 P3 will join `equipment_parts` for type-ahead suggestions).
* No global notification bell change — notifications land in the existing collection and will surface through the existing surfaces.
* No photo uploads in the repair completion form (existing `operational_attachments` flow does not yet accept `host_kind="fleet_defect"`; out of scope).
* No PM page / Fuel-Lube page / MaintainX integration / cost / inventory / pay-app.
* No mechanic-only portal · `/shop/me` is mounted under existing `RequireShop`.
* No new email channel (existing Resend wiring untouched).
* No frontend test runner change.

---

## 18 · Rollback Procedure

1. Frontend rollback: remove the 3 new routes in `App.js` (`ShopManagerQueue`, `ShopMyAssignments`) + delete Section 05 from `ShopHubV2.jsx`. Files in `/pages/shop/` and `/components/shop/RepairCompletionForm.jsx` can stay (dormant).
2. Backend rollback: revert `DefectActionPayload` back as the `/repair` model and remove the `parts_used` / `parts_on_order` persistence block (4 lines on the `$set` doc). Existing rows with parts data become orphaned but readable.
3. No DB migration required (additive nullable fields — Mongo absorbs cleanly).
4. Asset Service Event Backbone rollback: trim the 5-row "parts:" string concat + drop the `parts_used` / `parts_on_order` / `parts_used_count` / `parts_on_order_count` keys in the repair event projector.

`git revert` on the Phase 2 commit chain restores all of the above cleanly. The Track 13.28 Phase 1 (assign / accept / start / manager-review / queue endpoints) stays untouched.

---

## 19 · Five-Pillar Score

| Pillar                            | Score (0-10) | Justification                                                                                                |
| --------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| Action-Queue Focus                | 10       | Both new pages ARE action queues. Every row has a real workflow attached.                                     |
| No Dead Objects                   | 10       | Empty states are honest. Admin sees an explicit redirect. No phantom mechanics or invented work.              |
| Preserve Forms & Workflows         | 10       | `/repair` payload remained backward-compatible (existing callers continue to work; parts are optional).        |
| Rollback Pattern                  | 10       | `/shop/hub_legacy` still alive; new routes are additive. Phase 2 changes are revertable in two commits.       |
| Source-Truth                      | 10       | Mechanic list pulled live from `shop_users`. Parts derive from real `fleet_defects.parts_used`. No mocks.      |

**Average · 10.0 / 10.**

---

## 20 · Final Verdict

✅ Track 13.28 Phase 2 closes the loop on Shop accountability.

Defect → Shop Manager Assignment → Mechanic Acceptance → Work Started → Repair Completed With Notes + Parts → Shop Manager Review → Dispatch/Admin RTS is now operator-usable end-to-end from the UI. Parts capture builds the foundation for Known-Parts-By-Unit intelligence without inventing inventory, cost, or accounting. MaintainX remains dormant. Repair Complete ≠ RTS remains absolute.

---

## 21 · Recommended Next Track

**Track 13.31 — PM Engine (derived).**

Rationale (carried over from Track 13.28A §11):
* PM lifecycle plugs directly into the now-shipped assignment chain ("PM Open → Assigned → In Progress → Complete → RTS").
* Derived in v1 (no new persistence): read Motive hours/odometer + last PM completion off `fleet_defects.kind="pm"` (the lifecycle is shared).
* Backbone gains real `pm` events instead of placeholder.

Alternatively in parallel:
* **Track 13.28 Phase 3 — Per-Unit Parts Intelligence read-only endpoint.** ~2-3h additive. `GET /api/units/{unit_number}/parts-history` projects `fleet_defects.parts_used[]` into a frequency-ranked summary. Easy operator win.
* **Track 13.27 — Unit History Timeline UI** consuming `GET /api/assets/{unit}/timeline` end-to-end (the Phase 2 repair events + parts now display).

---

**Track 13.28 Phase 2 · CLOSED. Shop workforce surface LIVE.**
