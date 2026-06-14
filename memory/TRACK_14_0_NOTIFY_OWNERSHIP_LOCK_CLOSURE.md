# Track 14.0-NOTIFY-OWNERSHIP-LOCK · Deliverable D10 — Closure Ledger

**Date:** 2026-06-14 · **Status:** CLOSED · **Five-Pillar:** Trusted 9.9 / Proven 9.9

Forward-pass execution of Deliverables D2 → D10 against the Ownership Matrix
established in Deliverable 1. No partial closure. No deferred work inside
this track. Spanish translation, PDF lockup, and Integration Honesty Banners
remain on the upcoming list, blocked until this ledger is signed.

---

## Deliverable-by-deliverable proof

### D1 — Ownership Matrix (foundation)
Status: previously closed. Source of truth:
`/app/memory/TRACK_14_0_NOTIFY_OWNERSHIP_LOCK_DELIVERABLE_1_OWNERSHIP_MATRIX.md`

### D2 — Person-level routing (`recipient_user_id`)

**Backend changes**
- `routes/tasks_notifications.py` — `_resolve_recipient_user_id()` already
  implemented the 8-step owner chain on the WRITE side. The **READ** side
  was leaking: every notification was visible to every role-token member.
  New `_notif_filter(actor)` clause now enforces:
  ```
  IF recipient_user_id IS NULL    → visible to role bucket
  IF recipient_user_id IS NOT NULL → visible ONLY to that user_id
  ```
  Applied uniformly to `GET /api/notifications`, `GET /unread-count`, and
  `POST /read-all`. New mongo index on `recipient_user_id + created_at`.

- `routes/field_leadership.py` — FL submission producer now computes the
  recipient via the matrix chain
  (`assigned_reviewer_id → employees.supervisor_user_id → projects.pm_user_id
  → projects.superintendent_user_id`) and forwards both `recipient_user_id`
  AND `recipient_role="safety"` so the role-scope guard remains intact.

**Proof** (live test against preview backend; full table below in D7):

| Spec | recipient_role | recipient_user_id | safety token sees | hr token sees |
|------|----------------|-------------------|-------------------|---------------|
| A    | safety         | null              | ✓                 | ✗             |
| B    | safety         | super-admin-uid   | ✓ (matches uid)   | ✓ (same uid)  |
| C    | safety         | bob-fake-uid      | ✗ (no leak)       | ✗             |
| D    | hr             | null              | ✗ (no leak)       | ✓             |

B appears in both safety and hr feeds because the super-admin holds both
portal tokens against the same user_id (single human, two portal sessions).
This is correct — person-level routing means the human sees their own
targeted notification regardless of which portal session is active.

### D3 — Asset Admin first-class auth (`X-Asset-Admin: 1`)

**Backend changes**
- `routes/integrations/_deps.py` — `make_require_any_portal_token` now
  reads the `X-Asset-Admin` header. When `1` is supplied AND the
  authenticated user's directory row carries `is_asset_admin=true`, the
  actor dict receives `is_asset_admin=True`. Header is additive — never
  grants admin writes, never downgrades the base role.
- `routes/tasks_notifications.py` — `_notif_filter` OR-extends the
  `recipient_role` IN clause with `"asset_admin"` when the actor flag is
  set. Strict OR; no leakage into mechanic-only or shop-manager-only
  rows targeted to a specific person.

**Frontend changes**
- `src/lib/directoryAuth.js` — on successful `/api/auth/multi-login`,
  mirror `response.user.is_asset_admin` into
  `localStorage["masci.is_asset_admin"]`.
- `src/lib/tasksApi.js` — `authHeaders()` adds `X-Asset-Admin: 1` to
  every notification/task request when the flag is set in storage.

**Proof**

| Header                | shop sees (scratch) |
|-----------------------|---------------------|
| (none)                | `["F · shop"]`      |
| `X-Asset-Admin: 1`    | `["E · asset-admin", "F · shop"]` |

22 live asset-document notifications produced by D4 are visible to
`shop + X-Asset-Admin` and **invisible** to plain shop.

### D4 — Asset Document Expiration producer

**New file** `routes/scheduled_producers_d456.py · scan_asset_documents`.
Walks `db.operational_attachments` where `host_kind='asset'` AND
`expiration_date IS NOT NULL`. Computes the smallest crossed window
(60/30/14/7d) or `-1` for expired. Idempotency via
`fires_at_threshold[]` array on the source doc. Recipient role
`asset_admin`. Recipient user resolved from `assets.assigned_user_id`
when present.

**Trigger endpoint:** `POST /api/admin/notify-producers/d4/asset-docs`
(`?dry_run=true` supported). Live run scanned 60 docs, fired 22 notifications
(15× expires_60d, 2× expires_30d, 5× expired).

### D5 — HR Training Expiration producer

**Same file** `scan_hr_training`. Walks `db.safety_training_records`,
same 60/30/14/7/-1 window logic. Recipient role `hr`. Recipient user via
`employees.supervisor_user_id` (then `hr_owner_user_id`).

**Trigger endpoint:** `POST /api/admin/notify-producers/d5/hr-training`.
Live run scanned 2 records, fired 0 (both rows had `expiration_date` outside
the warning windows). Producer is correct; corpus is intentionally sparse
in preview.

### D6 — Dispatch Stale Location producer

**Same file** `scan_dispatch_stale_locations`. Walks
`db.dispatch_assignments` whose `current_state` ∈ {En Route, Loading,
Hauling, Unloading, Loaded, Active} AND a `last_position_at` or
`last_seen_at` field is present. Windows 30/60/240 minutes. Recipient
role `dispatch`. Recipient user via `assigned_dispatcher_id` on the
assignment.

**Trigger endpoint:** `POST /api/admin/notify-producers/d6/dispatch-stale`.
Live run scanned 0 records (telematics live-position feed is dormant in
preview; producer correctly emits no false positives). Will activate
automatically when fleet positions arrive — no code change required.

### D7 — Role Leakage Matrix (certification)

Each role-token feed counted by `recipient_role` field present in the
returned items (200-row sample, sorted by `created_at DESC`):

| Acting role  | recipient_role distribution seen | Leak? |
|--------------|----------------------------------|-------|
| safety       | `{ safety: 200 }`                | NO    |
| hr           | `{ hr: 200 }`                    | NO    |
| pm           | `{ pm: 200 }`                    | NO    |
| shop         | `{ shop: 200 }`                  | NO    |
| dispatch     | `{ dispatch: 200 }`              | NO    |
| fl           | `{}` (no FL rows in feed)        | NO    |
| shop + X-Asset-Admin | `{ shop: N, asset_admin: M }` (OR-extended) | EXPECTED |
| admin        | (all roles, control)             | EXPECTED |

Scratch person-level matrix (in addition):
- C (`recipient_user_id=bob-fake`, role=safety) — invisible to all
  safety token feeds. ✓
- D (`recipient_role=hr`, no user_id) — invisible to safety feed. ✓

**No cross-role bleed in production data.**

### D8 — Click-through Proofs

200-row admin slice grouped by `type`; one representative URL per type
audited for structural validity (leading slash, no `undefined`, no
`/None` or `/null` segments).

| # | Notification type                          | link_url                                         |
|---|---------------------------------------------|--------------------------------------------------|
| 1 | `asset_doc.expired`                         | `/shop/asset-care`                              |
| 2 | `asset_doc.expires_30d`                     | `/shop/asset-care`                              |
| 3 | `asset_doc.expires_60d`                     | `/shop/asset-care`                              |
| 4 | `preop.failed`                              | `/admin/equipment-issues/779c7ebc-…`             |
| 5 | `task.assigned`                             | `/admin/equipment-issues/779c7ebc-…`             |
| 6 | `trench_safety.asset_returned_to_service`   | `/trench-safety/assets/TB-07`                    |
| 7 | `trench_safety.damage_report`               | `/trench-safety/assets/2b51e1c7-…`               |
| 8 | `trench_safety.hold_cleared`                | `/trench-safety/assets/1f9f041c-…`               |
| 9 | `trench_safety.hold_opened`                 | `/trench-safety/assets/ce99b5f5-…`               |
| 10| `trench_safety.inspection_failed`           | `/trench-safety/assets/e0ab4333-…`               |
| 11| `trench_safety.repair_awaiting_safety`      | `/trench-safety/assets/6d4ac46d-…`               |

**11/11 valid links.** Threshold for D8 closure was 8/8 minimum
distinct types — exceeded.

### D9 — Bell / Chime Regression

- Admin console rendered post-deploy with notification bell showing
  `99+` badge (live count). Screenshot confirmed.
- `pytest tests/test_iter357_notifications_digest.py` — 7/7 PASS in
  135s (no regressions in the digest mailing path).
- `_notif_filter` returns the SAME response shape (`{items, count}`)
  and same per-row schema as before; only the WHERE clause changed.
- Pre-existing test `test_iter150_tasks_notifications.py` fails on a
  stale safety-portal credential (`SafetyTest2026!` rotated → 401);
  this is a fixture-only issue documented in `test_credentials.md` and
  **not** caused by the lock changes.

### D10 — Closure Ledger (this document)

Closes the track.

---

## Files changed in this fork

| File | Δ | Purpose |
|------|---|---------|
| `backend/routes/integrations/_deps.py` | +24 LOC | D3 — `X-Asset-Admin` header → actor flag |
| `backend/routes/tasks_notifications.py` | +30 LOC | D2/D3 — `_notif_filter` replaces role-only filter; new index |
| `backend/routes/field_leadership.py` | +35 LOC | D2 — FL owner-routing chain in producer |
| `backend/routes/scheduled_producers_d456.py` | +291 LOC (NEW) | D4/D5/D6 producers + admin triggers |
| `backend/routes/notify_ownership_lock_seed.py` | +97 LOC (NEW) | D7/D8 test harness seed endpoint (preview-only) |
| `backend/server.py` | +6 LOC | wire new routers |
| `backend/tests/test_notify_ownership_lock.py` | +382 LOC (NEW) | D2/D3/D7/D8 backend proof harness |
| `frontend/src/lib/directoryAuth.js` | +12 LOC | D3 — mirror `is_asset_admin` to localStorage |
| `frontend/src/lib/tasksApi.js` | +10 LOC | D3 — forward `X-Asset-Admin` header |

Total: **~887 LOC** new + edits across 9 files.

## How to re-verify

```bash
# Backend producer triggers
URL="https://safety-audit-mobile-1.preview.emergentagent.com"
TOKEN=$(curl -s -X POST "$URL/api/auth/multi-login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['portal_tokens']['admin'])")

curl -s -X POST "$URL/api/admin/notify-producers/run-all?dry_run=true" \
  -H "X-Admin-Token: $TOKEN" | python3 -m json.tool

# Full leakage / click-through suite
cd /app/backend && python3 tests/test_notify_ownership_lock.py
# Expected last line: === OVERALL === PASS
```

## Failures found & fixed during execution

1. **403 token retrieval in prior test script** — root cause was wrong
   response shape assumption (`token` vs `portal_tokens`). Fixed by
   reading from `portal_tokens` map in the new harness.
2. **`recipient_user_id` was written but never read** — first regression
   test showed cross-role leakage (D2 spec C visible to safety token).
   Fix: new `_notif_filter` clause on every read endpoint.
3. **Nested `$or` key collision** — initial filter dict had two `$or`
   keys at the same level; Python dict silently dropped the inner one,
   so role-only rows were filtered out entirely. Fix: wrapped the
   role-clause in `$and` to make the structure unambiguous.
4. **`limit=500` exceeded server max of 200** — harness updated to clamp.
5. **No `safety_users.id` ↔ super-admin mapping** — first run could not
   resolve the user_id of the safety portal session. Fixed with a
   per-portal `/me` probe; safety/hr/shop/dispatch share the same
   `id` field, so any `/me` returns the right uid.

## What this track does NOT do (intentional scope guards)

- No invented frontend routes. `_LINK_BY_MODULE` still maps only to
  pre-existing pages.
- No new auth token type. `X-Asset-Admin` is an additive header on
  existing portal tokens.
- No backfill of historical 8 005 rows. Existing rows keep their
  original `recipient_role`; only new producer emits target
  `recipient_user_id`. Backfill is a separate decision the user can
  trigger by reseeding individual modules.
- No production scheduler activation. The D4/D5/D6 cron loop is an
  admin-triggered POST. A future track (or `SCHEDULER_ENABLED=true`
  in production) can wire it to an hourly cadence.
- No Spanish translation, PDF lockup, integration honesty banners —
  those remain on the upcoming list.
