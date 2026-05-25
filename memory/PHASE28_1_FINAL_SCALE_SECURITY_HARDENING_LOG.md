# PHASE 28.1 — Final Scale + Security Hardening Execution
## iter429.1 · 2026-05-25

---

## Mission
Close the remaining production-hardening loop opened by Phase 27/28:
credential rotation, R2 cold-storage convergence, calm verification
visibility, Week-1 live-ops feedback, and a refreshed `server.py`
modularization roadmap — all without expanding feature surface.

---

## What landed this phase

### Part 1 · Atlas password rotation (security hygiene) ✅
- Operator rotated the production Atlas DB user password in the Atlas
  dashboard (`Database Access` → edit user → new password).
- `/app/backend/.env` `MONGO_URL` updated in the preview environment.
- Backend restarted; full startup ran (~30 index ensures, identity
  mirror sync of 68 users, role-templates seed of 31 entries) →
  ALL succeeded against Atlas with the new credential.
- `/api/health` (internal + external URL) → `{"ok": true}` ✅
- **Old password no longer in use anywhere** in the preview env.
- **Operator action still required**: update the prod deploy
  dashboard `MONGO_URL` env var to the new password and redeploy.

### Part 2 · Live R2 attachment backfill ✅
- `scripts/migrate_attachments_to_r2.py` executed safely in stages:
  1. `--apply --limit 10`  → 10/10 OK · sha256 round-trips verified
  2. Random-sample R2 read-back via `photo_storage.read_photo_bytes`
     hashed identically to stored `sha256` (proves cold-storage truth).
  3. `--apply` (no limit)  → 60/60 OK · 0 failures
- **Final live Atlas state**: TOTAL=70 · R2-backed=70 · inline_b64=0
- No `data_b64` payload remained on any operational_attachments row.
- The migration script proved its safety contract: every row had its
  sha256 round-trip verified BEFORE `data_b64` was `$unset`.

### Part 3 · Admin-only storage summary endpoint ✅
- New route: `GET /api/admin/operational-attachments/storage-summary`
- Returns JSON only (no UI, no chart, no dashboard):
  ```
  {
    "tenant_id": "masci",
    "total": <int>,
    "r2_backed": {"count": <int>, "total_size_bytes": <int>},
    "inline_b64": {"count": <int>, "total_size_bytes": <int>},
    "unknown": {"count": <int>, "total_size_bytes": <int>},
    "migrated_pct": <float>,
    "captured_at": "<iso8601>"
  }
  ```
- One-pass `$facet` aggregation → single Atlas round-trip.
- Admin-gated via `require_admin` (new optional `require_admin_dep`
  parameter on the router factory).

### Part 4 · Week-1 Live Ops Debrief ✅
- Implemented as a calm extension of the existing Day-1 module, NOT a
  parallel duplicate. One backend module
  (`routes/dispatch_day1_debrief.py`), one frontend page
  (`pages/admin/AdminDlsDay1Debrief.jsx` with a `variant` prop).
- New endpoints (mirror surface of Day-1):
  - `GET  /api/admin/dls/week-1-debrief/questions` → 14 questions
  - `POST /api/admin/dls/week-1-debrief` → writes
    `/app/memory/DLS_WEEK1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md`
- New route: `/admin/dls/week-1-debrief` (same React component, variant
  prop = `"week-1"`).
- Existing Day-1 surface UNCHANGED — all old test IDs and URL paths
  preserved verbatim.
- Question set: the 14 Phase 28.1 "repeated pattern" questions
  (friction, hesitation, natural flow, confusion, dispatch trust,
  driver lifecycle taps, Shop recovery, PM haul awareness, attachment
  value, passkey friction, Spanish translation issues, what stays
  simple, what NOT to build, highest-value surgical improvement).

### Part 5 · `server.py` modularization roadmap refresh ✅
- Re-measured: `server.py` = 11,584 LOC, but only **11** `@app.{verb}`
  decorators remain inline — every other route is already mounted via
  `app.include_router()`. All 11 are under `/api/legacy-imports/*`.
- Roadmap (`SERVER_PY_MODULARIZATION_ROADMAP.md`) updated with the
  exact line ranges, route inventory, shared-symbol checklist, and
  zero-behavior-change contract for Phase 1 extraction.
- **No code changes** in this phase — planning only, per directive.

---

## Verification (parity-lock testing)
- `test_iter429_op_attachments_r2.py` · 4 tests · ✅ all pass
- `test_iter427_legacy_backup_prune.py` · 2 tests · ✅ all pass
- `test_iter429_1_storage_summary_and_week1.py` (new) · ✅ all pass
- Backend `/api/health` (internal + external URL) → 200 ✅
- Live Atlas counts confirm migration: 70/70 R2-backed, 0 inline_b64
- Frontend lint clean across all modified hub pages.

## What this phase did NOT do
- ❌ No dashboards · no charts · no analytics · no scoring
- ❌ No new portal · no identity center · no document management
- ❌ No `server.py` extraction code (planning only)
- ❌ No legacy-test-suite triage (still parity-lock subset only)

## User action remaining (operator-only)
1. Update **production** `MONGO_URL` env var to the new password in
   the deploy dashboard. Redeploy production.
2. Optional: once you've used the platform for a week, file the first
   Week-1 debrief at `/admin/dls/week-1-debrief`.
