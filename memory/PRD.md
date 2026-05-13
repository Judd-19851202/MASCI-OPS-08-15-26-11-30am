# MASCI Safety Hub — PRD

## 2026-05-13 — Iter75: Signature → Cloudflare R2 Migration

### User ask
"What exactly will the R2 work do? What's the issue & what will it fix?"
After explanation: "Do it."

### What shipped
- **Backend migration router** (`/app/backend/routes/signature_migration.py`):
  - `GET /api/admin/signatures/status` — per-collection scan of 11
    form collections; returns counts of records with signatures,
    base64 (still in DB) vs cloud (already R2), bytes recoverable.
  - `POST /api/admin/signatures/migrate?dry_run=true|false&limit=N&collection=name`
    — dry-run mode counts only; commit mode uploads each base64
    blob to R2 via `photo_storage.upload_data_url()`, replaces the
    field with the returned `photo://` ref atomically per record.
  - Padding-repair patch on `upload_data_url` — older Mongo records
    can have base64 padding stripped during JSON round-trips. The
    helper now pads to a multiple of 4 with `=` before decoding.
    Caught 2 stub records during preview migration that would have
    otherwise failed.

- **Read-side compatibility shim** — every renderer that previously
  inlined `<img src="data:...">` now resolves `photo://` refs at
  print/render time:
  - `pdf_render._signature()` (cover signatures + 1-pager footer
    signatures)
  - `pdf_render._render_subcontractor_inspection_html()` (Sign-Off
    block)
  - `pdf_render` attendees/witnesses signature list rows
  - `field_leadership_pdf._resolve_sig()` + `_signatures_block()`
  - Frontend `ViewEquipmentInspection`, `ViewMeeting`,
    `FieldLeadershipView` — all 5 `<img>` sites now wrap the src
    with `resolvePhotoSrc()` (identical to how job photos already
    resolve `photo://` refs to `/api/photo-bytes?ref=…`).

- **Admin panel** (`/app/frontend/src/components/AdminSignatureMigrationPanel.jsx`):
  - Mounted in `/admin` directly below the Cloud Archives panel.
  - R2 health badge (green when configured, amber when not).
  - 4-stat summary (records w/ signatures · cloud · base64 in DB · DB bytes recoverable).
  - Per-collection table.
  - "Dry Run" + "Migrate Now" buttons; both auto-disabled when
    `base64 === 0` with a green "All signatures live in R2" badge.
  - Last-run result panel with per-collection breakdown.

### Verified
- **Preview migration ran successfully**: 14 base64 signatures → R2
  (14/14, 0 failed). Status endpoint now reports `grand_total.base64=0`,
  `cloud=14`.
- **PDF compatibility verified**: a daily-report and an inspection
  with migrated `photo://` signatures rendered 1 MB+ PDFs with the
  signature images inlined correctly.
- **Testing agent iter75**: 8/8 backend pytest pass, 3 env-skipped,
  100% frontend assertions pass.
- **Build-breaker caught by testing agent**: duplicate
  `import { resolvePhotoSrc }` in ViewMeeting.jsx + FieldLeadershipView.jsx
  (added by an earlier automated edit). Testing agent removed the
  duplicates → lint clean, webpack compiles, View pages load.

### Files added
- `/app/backend/routes/signature_migration.py`
- `/app/backend/scripts/scan_signatures.py` (one-shot diagnostic script)
- `/app/frontend/src/components/AdminSignatureMigrationPanel.jsx`
- `/app/backend/tests/test_signature_migration_iter75.py`

### Files modified
- `/app/backend/server.py` (migration router mount)
- `/app/backend/photo_storage.py` (padding-repair in `upload_data_url`)
- `/app/backend/pdf_render.py` (3 read-side resolve sites)
- `/app/backend/field_leadership_pdf.py` (`_resolve_sig` + `_signatures_block`)
- `/app/frontend/src/pages/ViewEquipmentInspection.jsx`,
  `ViewMeeting.jsx`, `FieldLeadershipView.jsx` (all 5 sig `<img>`
  sites wrapped with `resolvePhotoSrc`)
- `/app/frontend/src/pages/AdminHub.jsx` (mount panel)

### Operational notes
- The migration is **idempotent** — re-runs return `migrated=0,
  failed=0` when no base64 signatures remain.
- The 30-day rollback fallback mentioned in the plan is not strictly
  necessary because the migration is atomic per record and the
  original base64 is only overwritten AFTER a successful R2 upload.
  If a future need arises, write a reverse script that downloads each
  `photo://` ref and writes back a `data:` URL.

---

## 2026-05-13 — Iter74: ForgedOps™ Standardization

PDF renderers + posters + dev portal UI flipped to `ForgedOps™`. LLC
retained only in legal pages, ownership disclosure, ops manual.

## 2026-05-13 — Iter73: Public Hub Redesign (Phase C + D)

4 grouped sections, welcome-back hero, hybrid verbiage scrub, EnforcePortalScope fix.

## 2026-05-13 — Iter72: HR Payroll Variance + Training Updates

## 2026-05-12 — Iter71: HR Portal full stack

(see git history)

---

## Prioritized backlog

### P1
- **Backup verification cron** — weekly check that the previous 7
  nightly R2 archives exist + are openable; alarm email if not.
- **IT server-dump endpoints** — `GET /api/admin/server-dump/list`
  + `/latest`. Now meaningful since signatures are no longer
  bloating the DB.
- **Employee Login Gate** — bulk import + termination + usage.
- **Photo-First Daily Report** — AI-drafted from gallery photos.
- **Motive (Fleet) integration** — Pre-Op autofill + GPS verification.
- **Add `eslint --rule no-duplicate-imports:error`** to catch the
  class of build-breaker the testing agent fixed this iter.

### P2
- Auto-cron for signature migration on a schedule (currently manual).
- "Restore from R2" admin button (manual archive pick).
- "Forward to IT" share button on backup rows.

---

## Test credentials
See `/app/memory/test_credentials.md`. Quick refs:
- Admin: `MASCI1982!`
- HR Manager: `hrmanager@mascigc.com` / `HRPortal2026!`
- Shop: `testmech@mascigc.com` / `ResetWorks2026!`
- Field Leadership: `MASCIGC`
- PM (Chris Wright): `chriswright@mascigc.com` / `ChrisRocksThis2026`
