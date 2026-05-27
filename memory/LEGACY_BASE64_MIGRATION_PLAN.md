# Legacy Base64 Media Migration — Planning Document

**Phase:** SIGMA-III · P1 (planning-only, no execution)
**Iteration:** iter437
**Status:** 🟡 PLAN COMPLETE · 🔴 EXECUTION DEFERRED (requires operator authorization)

---

## Context

Before iter319 (Job Photos library migration to R2), several
operational write paths stored photos and signatures as **inline
base64** strings on the parent document:

- `inspections.photos[]`              (now empty in preview)
- `meetings.photos[]`                  (legacy backfill still present)
- `meetings.conductor_signature`       (base64 PNG)
- `incidents.photos[]`, `witnesses[].signature`
- `daily_reports.photos[]`, `prepared_by_signature`, `superintendent_signature`
- `equipment_inspections.signatures[]`
- `jhas.attachments[]`, `crew_signatures[]`
- `safety_documents.inline_b64`

Inline base64 grew the documents 3-5× their true byte size, slowed
list endpoints (the iter440 Phase 31.4 HR Time Verification fix was
literally this root cause), and bloated R2 backup archives unnecessarily.

R2 migration is **complete for all NEW writes** since iter319. This
document plans the **back-migration** of legacy rows that still
carry inline base64 strings.

---

## Census (preview DB, 2026-02)

| Collection             | Rows | Inline base64 present? |
|------------------------|-----:|------------------------|
| `inspections`          |    0 | n/a (preview empty)    |
| `meetings`             |   19 | **YES** (legacy photos + signatures) |
| `incidents`            |    7 | no                     |
| `daily_reports`        |   71 | no                     |
| `equipment_inspections`|   18 | no                     |
| `jhas`                 |    0 | n/a                    |
| `safety_documents`     |    6 | no                     |
| `fire_extinguishers`   |    2 | no                     |

Production census MUST be re-run before execution (preview is a stale
snapshot). The expected production hit-list:

- ~19 meetings in production carry conductor_signature + photos
- ~67 daily_reports in production carry inline photos + signatures
- ~18 equipment_inspections carry inline signatures

Estimated total inline payload to migrate: **~80-150 MB** across
~104 documents. Negligible — but the perf win is non-trivial because
the list endpoints stop dragging the base64 over the wire.

---

## Migration strategy (when executed)

### Phase 1 · Preparation (no DB writes)

1. Cut a fresh **complete R2 archive** as a rollback safety net. Take note of the resulting `MASCI_complete_backup_<ts>.zip` key.
2. Confirm `R2_ENDPOINT_URL`, `R2_BUCKET`, `R2_ACCESS_KEY`, `R2_SECRET_KEY` are populated. (Same vars used for backups.)
3. Disable the scheduler (`SCHEDULER_ENABLED=false`) on the **production** environment for the migration window so no concurrent writes happen mid-walk.
4. **Re-run the census** against production using the same script as
   above. Replace the preview numbers with the real ones in this doc.

### Phase 2 · Walk + rewrite (idempotent)

For each affected collection:

1. Cursor through `{"<field>": {"$type": "string", "$regex": "^.{1000,}$"}}` (server-side regex picks rows with long inline strings).
2. For each row + each inline blob:
   - Compute `r2_key = f"legacy-migration/{collection}/{id}/{idx}.{ext}"`.
   - PUT to R2 with `Content-Type: image/jpeg` (or `image/png` based on magic bytes).
   - Replace the inline string with a structured reference:
     ```json
     {"r2_key": "<key>", "size_bytes": <n>, "content_type": "<mime>", "migrated_at": "<iso>"}
     ```
3. Mark the document with `_legacy_b64_migrated: true` so the walk is idempotent and resumable.
4. Batch size: 25 docs per commit · sleep 200ms between batches · stop on first 5xx and surface to operator.

### Phase 3 · Schema reader compatibility shims

Every read path that consumed inline base64 must now handle BOTH
shapes:

- Plain string → assume legacy fallback (still works post-migration
  because the writer leaves nothing inline)
- Dict with `r2_key` → fetch from R2 via the existing photo helper

Affected reader files (audit list — not exhaustive, must be re-verified at execution time):

- `routes/safety.py` — `list_meetings` / `get_meeting` / PDF render
- `routes/daily_reports.py` — `get_daily_report` / PDF render
- `routes/incidents.py` — incident PDF render
- `routes/equipment_inspections.py` — DVIR PDF render
- `routes/hr_portal.py` — `/api/hr/time-verification` projection (already excludes photos; no change)
- `routes/job_photos.py` — already R2-native; no change

### Phase 4 · Verification

1. Re-run the census. Expected `has_inline_base64 = false` everywhere.
2. Re-render 3 random PDFs from the migrated collections (one meeting, one daily report, one equipment inspection). Confirm photos + signatures render correctly.
3. Re-enable scheduler.
4. Cut a post-migration backup archive (regression rollback target).

### Phase 5 · Cleanup (optional · 14-day delay)

After 14 days of clean operation, run a single `update_many({}, {"$unset": {"_legacy_b64_migrated": ""}})` to drop the marker field. This is cosmetic — no behavioural impact.

---

## Risk matrix

| Risk                                                     | Severity | Mitigation                                                    |
|----------------------------------------------------------|----------|---------------------------------------------------------------|
| R2 PUT fails mid-walk → partial migration                | MED      | Idempotent marker (`_legacy_b64_migrated`) makes the walk resumable |
| Reader fails to handle dict shape → broken PDF render    | HIGH     | Phase 3 reader compat shims · Phase 4 verification of 3 PDFs   |
| Concurrent writes mid-migration (race vs scheduler)      | MED      | Disable scheduler for migration window                         |
| Rollback needed                                          | LOW      | Phase 1 backup archive + 14-day marker                         |
| Migrated R2 objects accidentally affected by lifecycle   | MED      | Use `legacy-migration/` prefix (NOT inside `backups/auto-90d/`) so the 90-day TTL never fires on these |

---

## Execution criteria

This migration MUST NOT execute until **all** of the following are true:

1. Operator authorises in writing (chat/email) — this is a write-path doctrine change.
2. Production census re-run with up-to-date numbers.
3. Phase 1 backup archive cut < 30 minutes before execution.
4. A dry-run executed against preview first with full reader-compatibility verification.
5. The migration script committed to the repo at `/app/scripts/migrate_legacy_b64_to_r2.py` (does NOT exist yet — intentionally not pre-written to avoid accidental invocation).

---

## What this iteration produced

- ✅ This planning document.
- ✅ A live preview census (above) that confirms only `meetings` carries legacy inline data in preview.
- ❌ No migration script written.
- ❌ No DB writes performed.
- ❌ No reader compat shims merged.

The user's directive was **"Document migration strategy, no execution"** — and we have done exactly that.

---

## Verdict

🟡 **Legacy Base64 Media Migration — PLAN COMPLETE · EXECUTION GATED ON OPERATOR APPROVAL.**

Once the operator gives the go-ahead, a focused iteration can build
the migration script, execute against preview, verify, then execute
against production. Until then, no code change is needed.

# 🟡 P1 — Legacy Base64 Migration Planning · DOCUMENTED · CLOSED
