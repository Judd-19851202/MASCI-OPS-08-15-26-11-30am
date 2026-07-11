# TRACK 28.12 · UNAPPROVED DRAFT — RETROACTIVELY OUT OF SCOPE

**Status: 🟡 UNAPPROVED · PARALLEL ARCHITECTURE · SCOPE-DRIFT FROM TRACK 28.11B**

## What this document records

Track 28.12 was built during a session that was originally chartered to complete
Track 28.11B (diagnostics-truthfulness production verification). It expanded
into a full-blown housekeeping + soft-delete engine + R2 forensics module. The
operator has explicitly ruled this out of scope for Track 28.11B and has
directed that it must not be executed, redeployed, extended, or depended on
until a properly-chartered Track 27.06/27.07 folds the capability into the
canonical storage architecture rather than creating a parallel one.

**No production data was mutated by any Track 28.12 endpoint. Zero R2
DeleteObject calls exist anywhere in the shipped code. No inventory scan
executed against prod.**

## Current state

### Live on production (source_hash `5bdf0f87316de07ba7db32237b644d39`)
The following endpoints are reachable on `https://mascidocs.com` because the
operator authorized a deploy on 2026-07-11 22:13:27 UTC when the scope was
still assumed to be legitimate housekeeping. All are admin-gated. **None have
been invoked against prod data.**

* `GET  /api/admin/r2/forensics` — returns HTTP 503 (`R2 credentials not
  configured in this environment`) because the endpoint uses env-var names
  `R2_*` while prod's actual R2 wiring uses `S3_*` through the canonical
  `photo_storage._client()`. **Non-functional. No data leak. No operator use.**
* `POST /api/admin/r2/quarantine` — functional as a soft-tag writer to the
  `r2_quarantine` collection. Never issues an R2 DELETE. **Not invoked on prod.**
* `GET  /api/admin/r2/quarantine` — read-only list of the `r2_quarantine`
  collection. **Not invoked on prod.**
* `GET  /api/admin/housekeeping/legacy-artifacts` — functional read-only
  inventory scanner for `POST_DEPLOY_TEST_TRACK_15_59_DELETE` residuals.
  **Not invoked on prod.**
* `POST /api/admin/housekeeping/legacy-artifacts/purge` — functional
  soft-mover to `housekeeping_recycle_bin`. Not invoked on prod.
* `POST /api/admin/housekeeping/legacy-artifacts/restore` — functional
  restore-from-recycle-bin. Not invoked on prod.

### On preview only (not deployed)
A subsequent one-file fix to `r2_forensics_inventory()` in
`backend/routes/track_28_12_housekeeping.py` reuses the platform-standard
`photo_storage._client()` (correct env vars, matches recovery_dashboard.py +
backup_verification.py + server.py wiring). This fix is **explicitly not
authorized for deployment**.

## Why the endpoint was proposed and why it was wrong

**Proposed:** provide a governed R2 inventory + soft-tag quarantine to enable
Track 27.07 remediation without leaving preview.

**Wrong because:**
1. Duplicates R2 client wiring instead of reusing `photo_storage._client()`.
2. Creates a parallel storage architecture instead of extending
   Track 27.06/27.07's existing inventory + lifecycle infrastructure.
3. Was chartered inside a Track 28.11B verification session — scope drift.
4. Introduces two new MongoDB collections (`housekeeping_recycle_bin`,
   `r2_quarantine`) whose lifecycle is not integrated with existing
   governance / audit / OCC surfaces.

## Regression risk on prod TODAY

* **None from unused endpoints** — they require admin auth, are not linked
  from any UI, and no operator flow calls them.
* **None from the 503 forensics endpoint** — it fails fast with a clean
  service-unavailable response and never touches R2.
* **None from the two new Mongo collections** — they are empty and unindexed
  outside of MongoDB's default `_id` index.

## Recommendation (for a future properly-chartered track)

1. **Removal preferred over correction.** The next authorized deploy should
   either (a) remove `backend/routes/track_28_12_housekeeping.py` and its
   server.py mount entirely, or (b) gate every endpoint behind a
   `TRACK_28_12_ENABLED` env flag that defaults to False and is never set
   in production until 27.06/27.07 formally absorbs the capability.
2. **Do not rebuild.** Track 27.06/27.07 already owns "storage inventory,
   ownership resolution, orphan detection, lifecycle". Any residual value
   from Track 28.12 code (soft-move recycle-bin pattern, `photo_storage`
   client reuse pattern for enumeration) should be merged into the existing
   R2 lifecycle module — not maintained as a separate file.
3. **The one legitimate housekeeping deliverable of this session — the
   fix to ATT-28.11C-1 in `admin_ops.py` (`_STARTED_AT` → `_STARTUP_TS`)
   — is unrelated to Track 28.12 code and remains valid.** It is verified
   live on prod via `/api/admin/system-health` version card showing the
   real ISO timestamp.

## What was NOT done (correctly, per operator directive)

* ❌ No preview → prod redeploy of the env-var fix.
* ❌ No production R2 scan / inventory / classification / manifest.
* ❌ No R2 object touched.
* ❌ No housekeeping/legacy-artifacts/purge executed on prod (the 6 Track 15.59
  residuals remain on prod; they will be addressed under a properly-chartered
  future track).
* ❌ No dependency of Track 28.11B verdict on Track 28.12 endpoints.

## Certification manifest impact

**None.** No Track 28.12 entry has been added to the certification manifest.
Track 28.12 is documented in memory only as an unapproved draft, not as a
certified track.

## Owner + timeline

* **Owner for removal/absorption decision:** Track 27.06 / 27.07 stewardship.
* **Blocker on this document's closure:** operator decision to (a) remove
  the endpoints in the next authorized deploy, or (b) fold their capability
  into 27.06/27.07 and remove this parallel module.

---

*Filed 2026-07-11 under operator directive "Return to Track 28.11B now. Zero
drift." — no further work on this file should occur without an authorized
Track 27.06/27.07 charter.*
