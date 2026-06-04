# MAINTAINX · WO DUPLICATE PROTECTION PLAN  (Phase 8)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes)

This is the contract that the future WO push module MUST satisfy before any `POST /v1/work-orders` call to MaintainX is made. The rule is simple: **no double work orders, ever.** Repeated form submissions, retries, webhook replays, and admin re-imports must all converge on at most one WO per logical defect group.

---

## 1 · The seven duplicate-protection layers (in evaluation order)

Each push attempt MUST pass all seven checks. The first layer to flag a duplicate halts the push.

### Layer 1 — `external_refs.maintainx_work_order_id` already set on the source row
- Look up the originating row (`fleet_defects` / `equipment_inspections` / `asset_holds`) by `id`.
- If `external_refs.maintainx_work_order_id` is non-empty → **already pushed**; mark `sync_status="skipped_already_pushed"`, return the existing wo id.

### Layer 2 — `correlation_id` already stored on the source row
- Even before a WO id is captured, the canonical builder stamps `external_refs.correlation_id`.
- If a push attempt comes in for the same `(source_collection, source_record_id)` AND `external_refs.correlation_id` is set AND `sync_status` is `pending` → check Layer 3 (MaintainX side) before generating a fresh id; never re-roll the correlation_id.

### Layer 3 — MaintainX `externalId` lookup
- Before any POST, the push module issues:
  ```
  GET /v1/work-orders?externalId=<correlation_id>
  ```
- If a WO already exists with that `externalId` → adopt its `id` + `url`, stamp the source row, mark `sync_status="skipped_external_id_match"`. **No POST is issued.**

### Layer 4 — Same source-record-id + asset-id + open WO
- If Layer 3 returns nothing, perform a defensive secondary query against MaintainX:
  ```
  GET /v1/work-orders?assetId=<maintainx_asset_id>&status=Open,InProgress,OnHold
  ```
- Walk results; if any result's `customFields.forgedops_source_record_id` matches the canonical payload → adopt it (Layer 3 backstop). Mark `sync_status="skipped_source_record_match"`.

### Layer 5 — Same asset + same defect title within an `N`-day window
- If Layers 3 + 4 are silent and the canonical payload's `defect_title` and `assetId` match an existing OPEN WO whose `created_at` is within `MAINTAINX_DUPE_WINDOW_DAYS` (default `7`) → adopt it. Mark `sync_status="skipped_title_match_window"`.
- This protects against driver-DVIR + later operator-Pre-Op reporting the same brake issue twice.

### Layer 6 — Same `reported_at` minute-window from the same source
- Pure local check on `db.fleet_defects` / `db.equipment_inspections`: if another row in the same source collection has `unit_number == self.unit_number` AND `defect_title == self.defect_title` AND `reported_at` within `±2 minutes` AND has `external_refs.maintainx_work_order_id` set → adopt that row's wo id. Mark `sync_status="skipped_form_double_submit"`.
- This is the **double-click / form-resubmit guard** — pure ForgedOps-side, fastest check, runs before any network call in retry scenarios.

### Layer 7 — Persistent push attempt log
- `db.maintainx_wo_push_attempts` (NEW · audit) carries one row per attempted push. Before issuing a POST, the module checks for an attempt with the same `correlation_id` that has `status="pushed"`. If found → adopt.
- This protects against process restart between POST success and source-row write success.

---

## 2 · Idempotency key

The single canonical idempotency key across all layers is:

```
idempotency_key = correlation_id (UUID v4 per defect group)
```

`correlation_id` is generated **once per defect group**:

| Defect group key | Definition |
| --- | --- |
| For DVIR | `(inspection_id, equipment_id)` — one correlation_id per inspection per unit, even with multiple failed items |
| For Pre-Op | `(inspection_id, equipment_id)` |
| For Manual OOS | `(defect_id, equipment_id)` (single-row source) |
| For asset_holds | `(hold_id, equipment_id)` |

The first time the canonical payload is built for that key, the correlation_id is stamped on every involved row (`external_refs.correlation_id`). All future re-builds reuse the existing key.

---

## 3 · Per-asset rate cap (defence-in-depth)

Even if all 7 layers fail (network glitch, MaintainX 5xx, etc.), the push module is hard-capped:

```
MAINTAINX_PUSH_PER_ASSET_CAP   = 2 per 24h  (env var)
MAINTAINX_PUSH_DAILY_CAP       = 50         (env var)
MAINTAINX_PUSH_BURST_CAP       = 5 per 60s  (env var)
```

Exceeding ANY of the three causes the push to be enqueued into `db.maintainx_sync_pending` with status `rate_capped` and an admin alert. The default values are conservative; admins may relax once production is stable.

---

## 4 · Audit trail required

For every push attempt (whether skipped, succeeded, or failed), one row in `db.maintainx_wo_push_attempts`:

```jsonc
{
  "id":              "<uuid>",
  "attempted_at":    "<iso>",
  "correlation_id":  "<uuid>",
  "source_type":     "fleet_dvir | equipment_preop | ...",
  "source_record_id":"<id>",
  "equipment_id":    "<id>",
  "maintainx_asset_id":"<id or null>",
  "defect_title":    "...",
  "severity":        "...",
  "decision":        "pushed | skipped_already_pushed | skipped_external_id_match | skipped_source_record_match | skipped_title_match_window | skipped_form_double_submit | rate_capped | failed",
  "decision_layer":  1-7,
  "wo_id":           "<id or null>",
  "wo_url":          "<url or null>",
  "error":           { ...StructuredError or null },
  "duration_ms":     int
}
```

This is the canonical artefact for any retrospective duplicate audit.

---

## 5 · Inverse case — defect re-opens

If a defect is re-opened in ForgedOps after WO closure (a real situation when shop missed something):

| Scenario | Behaviour |
| --- | --- |
| Same `source_record_id` re-opened | Push a NEW WO with a **NEW** correlation_id (acknowledging this is a regression event); stamp the source row's `external_refs.maintainx_re_open_history[]` with the previous wo id for trace. |
| New `source_record_id` for the same unit + same item within N days of a recent close | Push a new WO; do NOT short-circuit to Layer 5 (we want shop visibility into the regression). |

Note: re-opens are NOT covered in the initial build. Stage 8 may introduce them after operator approval.

---

## 6 · Edge cases explicitly handled

| Scenario | Layer that catches it |
| --- | --- |
| User double-clicks "Submit" on a DVIR form (two near-simultaneous inserts) | Layer 6 (±2 min same source / same title) |
| Push retry fires twice (e.g. queue worker race) | Layer 7 (push_attempts log) |
| MaintainX-side admin had already manually created the WO | Layer 5 (asset + title window) |
| Process crash between WO POST and source-row write | Layer 3 (`externalId` round-trip) + Layer 7 |
| Webhook replay from MaintainX | Webhook handler matches by `wo.id` against `external_refs.maintainx_work_order_id` first; if no match, falls through to canonical correlation_id |
| Same unit two different defects on the same DVIR | Each `(inspection_id, equipment_id)` is ONE correlation_id; the WO description carries both items as bullets (consolidation rule from Phase 4 §3) |
| Mapping wizard re-runs creating a fresh `asset_mappings` row | Idempotency key is `correlation_id`, not `asset_mappings._id`; safe |

---

## 7 · Failure modes — what duplicates can still happen?

| Failure mode | Likelihood after this design | Mitigation |
| --- | --- | --- |
| MaintainX `externalId` query unsupported / silently broken in tenant version | LOW · medium impact | Layer 4 (assetId + source_record_id) is the backstop. Push module must REFUSE to start if `GET /v1/work-orders?externalId=` returns a non-empty body for an arbitrary uuid (sanity check) |
| Operator manually creates a WO between Layer 3 and the POST | VERY LOW · low impact (one extra WO; auditable; admin resolves) | Admin "duplicate detector" daily cron flags any two WOs sharing `customFields.forgedops_unit_number + forgedops_source_record_id` within 24h |
| Two ForgedOps preview environments both pushing to the same production MaintainX tenant | LOW · high impact (must never happen) | Hard env-var: `MAINTAINX_TENANT_GUARD=preview|production`; mismatched env vs `MAINTAINX_BASE_URL` host refuses to push |

---

## 8 · Required collections (planned · NOT BUILT this sprint)

| Collection | Purpose | Indexes |
| --- | --- | --- |
| `db.maintainx_wo_push_attempts` | Per-attempt audit | `correlation_id`, `decision`, `attempted_at` (DESC) |
| `db.maintainx_sync_pending` | Retry queue for rate-capped / failed pushes | `next_attempt_at` (ASC), `correlation_id` (unique) |

Neither collection is created in this Phase 8 planning sprint.

---

## 9 · Verdict — Phase 8 Duplicate Protection

```
DUPLICATE PROTECTION  :  DESIGN COMPLETE

  7-layer evaluation order                  : DEFINED
  Idempotency key (correlation_id)          : DEFINED
  Per-asset rate cap                        : DEFINED
  Audit trail collection (planned)          : DEFINED
  Edge cases enumerated                     : 7 / 7
  Failure mode mitigations                  : DEFINED
  Inverse case (re-open) handling           : DEFINED
```

— End of Phase 8 Duplicate Protection Plan —
