# RESTORE_RUNBOOK.md
## MASCI Operations Platform · Disaster Recovery Restore Runbook
## Phase 25.3 · iter426 · 2026-05-25

This runbook walks an operator (NOT only a software engineer) through restoring
the MASCI platform from a backup archive. It assumes the primary production
environment is gone or unrecoverable, and that you have a backup zip.

---

## 1. Recovery overview

The platform backs up to **two** independent archives:

1. **Local nightly zip + email** — `MASCI_full_backup_<UTC>.zip` (or `_lite_`) ·
   emailed to the operators on `BACKUP_EMAIL_TO`. Contains every Mongo
   collection (JSON), inline binaries, and disk artifacts.
2. **R2 cloud archive** — `MASCI_complete_backup_<UTC>.zip` · uploaded to
   `r2://<S3_BUCKET>/backups/auto-90d/` · 90-day retention. Auto-discovers
   every collection (iter425).

**Either archive is sufficient to restore.** Prefer the most recent.

The runbook restores in this calm order:

1. Stand up a fresh container
2. Configure environment variables
3. Restore Mongo (collections)
4. Restore disk artifacts (storage / static / data / memory)
5. Restart services
6. Walk the post-restore validation checklist

---

## 2. Restore prerequisites

You need:

| Item                                 | Where                                                                  |
|--------------------------------------|------------------------------------------------------------------------|
| The backup zip                       | Your operator email OR `r2://<bucket>/backups/auto-90d/<file>.zip`     |
| MongoDB instance                     | Fresh empty Mongo at `MONGO_URL`                                        |
| Backend container with `/app/backend` | Standard MASCI deployment (Emergent or self-host)                     |
| Environment file `/app/backend/.env` | See Section 3                                                          |
| `unzip` + `mongoimport` (or pymongo) | Standard Mongo CLI tools                                                |

---

## 3. Environment variables required

The restored backend MUST start with these env keys present in `/app/backend/.env`:

| Variable             | Purpose                                                            |
|----------------------|--------------------------------------------------------------------|
| `MONGO_URL`          | Where to write restored collections                                |
| `DB_NAME`            | Database name                                                      |
| `S3_BUCKET`          | R2 bucket name (for photo bytes still in R2 from older records)   |
| `S3_ENDPOINT_URL`    | R2 endpoint                                                        |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | R2 credentials                                          |
| `S3_REGION`          | typically `auto`                                                   |
| `BACKUP_EMAIL_TO`    | Restore future backups to the same address                         |
| `EMERGENT_LLM_KEY`   | If used by Phase 24 passkey / coaching · paste from operator vault |

**Do NOT copy env files from the lost container.** Re-create from secure storage.

---

## 4. Mongo restore sequence

### 4a. Unzip the backup

```bash
mkdir -p /tmp/masci-restore && cd /tmp/masci-restore
unzip /path/to/MASCI_full_backup_<UTC>.zip
ls
# expected: MANIFEST.json or backup_manifest.json, collections/, disk_files/, photos/ (R2 archive)
```

### 4b. Verify the manifest first (read · do not panic)

```bash
cat MANIFEST.json | python3 -m json.tool | head -40
```

Confirm:
- `mode` is `"complete"` (R2 archive) or `"full"` (local nightly)
- `captured_collections` lists at least the new Phase 12-25 names:
  `dispatch_assignments`, `dispatch_continuity_events`, `operational_attachments`,
  `user_passkeys`, `user_directory`, `users`
- `redaction_rules_applied` includes `user_directory` and `users`
- `explicit_exclusions` lists ONLY `system.indexes` style entries

If `captured_collections` does NOT include the DLS collections, the archive is
pre-iter425 and you should fall back to the most recent post-iter425 archive.

### 4c. Restore collections

The archive ships JSON files under `<kind>/json/<id>.json` (R2 archive shape)
or `collections/<name>.json` (local archive shape — single JSON array per file).

For the **R2 complete archive** layout:

```bash
# One collection at a time. Replace dispatch_assignments with each name.
for coll in $(jq -r '.captured_collections[]' MANIFEST.json); do
  echo "Restoring $coll ..."
  # R2 archive uses one JSON file per record
  find "$coll" -name "*.json" -path "*/json/*" | while read f; do
    mongoimport --uri "$MONGO_URL" --db "$DB_NAME" --collection "$coll" --file "$f"
  done
done
```

For the **local archive** layout (`collections/<name>.json` containing an array):

```bash
for f in collections/*.json; do
  coll=$(basename "$f" .json)
  echo "Restoring $coll ..."
  mongoimport --uri "$MONGO_URL" --db "$DB_NAME" --collection "$coll" --jsonArray --file "$f"
done
```

### 4d. Recreate indexes

Indexes are NOT in the backup (Mongo auto-creates them as schemas write). The
MASCI backend recreates every required index on startup via the
`@app.on_event("startup")` `ensure_*` calls. **Just start the backend.**

---

## 5. Attachment continuity restore

Operational attachments (Phase 20 / iter417) store image bytes **inline** as
`data_b64` inside each document in the `operational_attachments` collection.
**No additional restore step needed.** Once the Mongo collection is restored,
the AttachmentStrip in the AssignmentDrawer will fetch and display them
automatically via `GET /api/operational-attachments/{id}/bytes`.

**Legacy photos** stored under `photo://<bucket>/<key>` references (Phase 11
safety side: inspections / incidents / daily_reports / equipment_inspections /
jhas / meetings) are inlined under `photos/<key>` in the R2 complete archive.
If R2 itself is unreachable AND your archive came from R2, you can re-upload
those bytes back into R2 from the zip:

```bash
# Walk the photos/ tree in the unzipped archive
find photos/ -type f | while read f; do
  key=${f#photos/}
  # Re-upload to R2 using your favorite client (rclone, aws s3 cp, etc.)
  rclone copyto "$f" "r2:$S3_BUCKET/$key"
done
```

If the original R2 is still alive, **skip this step** — the photo refs work as-is.

---

## 6. Operational attachment validation (post-restore)

After services are up:

```bash
# Pick one breakdown photo from the restored data
EXAMPLE_AID=$(curl -s "https://<host>/api/dispatch/assignments?limit=1" \
  -H "X-Admin-Token: <token>" | jq -r '.assignments[0].id')

# Fetch the attachment list
curl -s "https://<host>/api/operational-attachments/list?host_kind=assignment&host_id=$EXAMPLE_AID" \
  -H "X-Admin-Token: <token>" | jq '.count'

# Fetch the binary bytes of an attachment — expect 200 with image/png or image/jpeg
ATT_ID=$(... | jq -r '.attachments[0].id')
curl -sI "https://<host>/api/operational-attachments/$ATT_ID/bytes" -H "X-Admin-Token: <token>"
```

If you see an image MIME and non-zero bytes, attachment continuity is intact.

---

## 7. DLS / trucking continuity validation

```bash
# 1. Assignments visible to Dispatch
curl -s "https://<host>/api/dispatch/assignments" -H "X-Admin-Token: <token>" | jq '.count // length'

# 2. Recovery sub-state grouping (iter423)
curl -s "https://<host>/api/dispatch/recovery/by-shop" -H "X-Admin-Token: <token>" | jq '.summary'

# 3. Continuity events chronology (iter419)
curl -s "https://<host>/api/dispatch/continuity-events/recent" -H "X-Admin-Token: <token>" | jq '.count'
```

All three should return non-empty data matching the production volume.

---

## 8. Passkey continuity notes

iter422 passkeys store ONLY public-key credential metadata (`credential_id`,
`public_key`, `sign_count`, `friendly_name`, `rp_id`). After restore:

- ✅ Users keep their enrolled passkeys (same device unlocks the same account).
- ✅ The `rp_id` in stored credentials MUST match the restored host's domain
  (e.g., `preview.emergentagent.com`). If you restore into a DIFFERENT domain,
  the browser will refuse to use the existing passkeys — users sign in with
  password and re-enroll new passkeys on the new domain. **This is expected
  WebAuthn security behavior, not a backup bug.**
- ✅ No biometric data is in the archive (verified by iter425 test).

---

## 9. TTL collection behavior (intentional)

| Collection                  | Restore behavior                                              |
|-----------------------------|---------------------------------------------------------------|
| `webauthn_challenges`       | TTL-expires within 5 minutes of restore · safe to restore     |
| `dispatch_driver_sessions`  | Restored but operationally near-useless · drivers re-sign in  |
| `backup_health`             | Self-referential · keep last few rows for forensics           |
| `backup_drift_history`      | iter426 · NOT critical for continuity · restore for trend     |

None of these are restore blockers.

---

## 10. Post-restore validation checklist

Walk these BEFORE declaring restore successful:

- [ ] Backend health endpoint returns 200: `curl -s https://<host>/api/health`
- [ ] Admin sign-in works (password fallback): `/sign-in` → land on `/admin`
- [ ] Multi-login response shape preserved (no MFA mid-flow surprise)
- [ ] Dispatch Portal loads: `/dispatch-portal/board` shows assignments
- [ ] Shop Portal loads: `/shop` shows 5 calm operational sections
  (Equipment Needing Attention / Active Recovery Work / Waiting / Returned /
  Continuity History)
- [ ] PM Portal loads: `/pm` shows haul-cycle visibility
- [ ] Field Leadership portal loads: `/fl`
- [ ] At least one Dispatch assignment shows: recovery_state visible · recovery_history populated
- [ ] At least one operational attachment renders in AssignmentDrawer
  (AttachmentStrip thumbnails fetch via `/operational-attachments/{id}/bytes`)
- [ ] Driver shift page loads via a magic link: `/d/<token>`
- [ ] Guidance/help search returns at least one article: `/guidance` → search "shop"
- [ ] Spanish language toggle preserves operational meaning: 🌐 → "Recuperación Operacional"
- [ ] Passkey login works (or password fallback works): `/sign-in` → use device sign-in
- [ ] Offline pending-sync indicator absent (no stale localStorage queue corruption)
- [ ] Backup scheduler emits a `backup_health` row within 26 hours (tomorrow's run)

---

## 11. Operational smoke-test checklist

Beyond technical checks, validate operational flow:

- [ ] Create a test dispatch assignment → it appears on the board
- [ ] Transition it through DLS lifecycle (assigned → en_route → ...) → state events recorded
- [ ] Create a recovery transition on the same assignment → recovery_state updated · history appended
- [ ] Upload a breakdown photo via the driver / shop attachment endpoint → byte fetch returns the same image
- [ ] Search for "active recovery work" in `/guidance` → article surfaces in EN + ES
- [ ] Create a continuity event (iter419) → it appears in `/api/dispatch/continuity-events/recent`

If any item fails, see Section 14 (rollback).

---

## 12. Known intentional exclusions

The `BACKUP_EXPLICIT_EXCLUSIONS` set in `server.py:4101` documents what is
DELIBERATELY left out of every backup. Currently:

| Collection         | Reason                                                  | Restore impact |
|--------------------|---------------------------------------------------------|----------------|
| `system.*`         | MongoDB internal · not customer data                     | None           |

**No silent exclusions exist.** If a collection is missing from the manifest,
either it never existed in the production DB at the time of backup OR a drift
event should be visible in the `backup_drift_history` collection (iter426).

---

## 13. R2 manifest interpretation

Every R2 archive ships a `MANIFEST.json` at the zip root. Key fields:

```json
{
  "generated_at": "<ISO timestamp>",
  "mode": "complete",
  "total_records": <int>,
  "per_kind": { "<collection>": <count>, ... },
  "captured_collections": [ ... ],         // iter425 audit trail
  "explicit_exclusions": [ ... ],          // iter425 audit trail
  "redaction_rules_applied": [ ... ],      // iter425 audit trail
  "inlined_photos": <int>,
  "inlined_photo_bytes": <int>,
  "failed_photos": <int>,
  "notice": "<human-readable description>"
}
```

If `failed_photos > 0`, photo bytes were partially missing during archive
generation. Check R2 directly for those specific keys.

If `redaction_rules_applied` does NOT include `user_directory`, the archive
predates iter425 and **may contain plaintext MFA secrets** — handle that
archive as sensitive material and restore-then-rotate every MFA secret.

---

## 14. Emergency rollback guidance

If the restored platform misbehaves and you have an earlier-known-good archive:

1. Drop the current database: **DO NOT** do this in production without
   confirming you have the earlier archive in hand.
2. `mongo <DB_NAME> --eval "db.dropDatabase()"` (or use MongoDB Compass)
3. Repeat Section 4 with the earlier zip.
4. Re-walk Section 10 + 11.

If the issue is software regression (not data), redeploy the earlier release
tag from git BEFORE rerunning the restore. The platform is data-agnostic to
release versions as long as schemas match (forward-compatible).

---

## 15. Disaster-recovery doctrine notes

- **The platform is one operational nervous system.** Restore is not a
  feature negotiation — every section above is part of the same continuity.
- **No surveillance, no biometric data, no plaintext MFA secrets** ever land
  in a backup. Verified by `test_iter425_backup_auto_discovery.py`.
- **Auto-discovery is the doctrine** — never re-introduce a backup allowlist.
  Future collections inherit coverage by construction.
- **No backup-management UI.** This runbook is the entire operator interface.
  If you ever feel pressured to build a "backup center," re-read iter425's
  `R2_BACKUP_CONTINUITY_AUDIT.md` Section 11 — the restraint is the design.

---

## Doctrine reaffirmed

This runbook is operational survivability continuity. NOT enterprise backup
software. Calm restoration · evidence-based validation · no panic recovery.
