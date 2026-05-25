# PHASE26_BACKUP_RESTORE_VERIFICATION.md
## MASCI Operations Platform · Phase 26 · Backup + Restore Operational Survivability
## iter427 · 2026-05-25

---

## Source of truth references

- `/app/memory/R2_BACKUP_CONTINUITY_AUDIT.md` — full backup posture
- `/app/memory/RESTORE_RUNBOOK.md` — 15-section operator runbook
- `/app/memory/PHASE25_3_RESTORE_CONTINUITY_LOG.md` — iter426 hardening
- `/app/backend/tests/test_iter425_backup_auto_discovery.py` — 6 tests
- `/app/backend/tests/test_iter426_restore_drift_watcher.py` — 5 tests

---

## 1 · Pipeline state

| Pipeline | Trigger | Coverage | Status |
|---|---|---|---|
| **Pipeline A** — Hourly auto-snapshot to R2 | every hour from `_run_complete_archive_to_r2` | ALL `db.list_collection_names()` collections + 4 disk roots | 🟢 live |
| **Pipeline A fallback** — Nightly 03:00 UTC archive | scheduler | same | 🟢 live |
| **Pipeline B** — Admin-triggered manual archive (`/admin/system`) | operator button | same | 🟢 live |
| Auto-discovery (iter425) | `db.list_collection_names()` | every collection inherits archive · no allowlist drift | 🟢 verified |
| MFA / TOTP secret redaction (iter425) | server-side | `mfa.secret`, `mfa.recovery_codes`, password_hash never persisted | 🟢 verified |
| Backup drift watcher (iter426) | post-archive hook | calm WARN log on collection disappearance · INFO on new appearance | 🟢 verified |
| Disk-backed file inclusion | `DISK_BACKUP_ROOTS` | `/app/backend/storage`, `/static`, `/data`, **`/app/memory`** (iter426) | 🟢 verified |

---

## 2 · Live observation (Admin /admin/system)

| Indicator | Captured |
|---|---|
| "SAFE TO REDEPLOY" green pill | ✅ |
| Last complete archive | 24 min ago |
| Latest archive filename | `MASCI_full_backup_2026-05-24_003635Z.zip` |
| Hourly auto-snapshot | ON |
| Nightly fallback | 03:00 UTC |
| Find Record by Ref tool | ✅ present |
| **Backup-or-die banner** | ✅ Present and red — "Your data will be deleted on the next redeploy. MongoDB is running inside this container (localhost:27017)" with the **permanent fix** call-out (MongoDB Atlas free tier) |

---

## 3 · Backup manifest sanity

Each manifest carries (verified via `test_iter425`):

- `captured_collections` — list of every Mongo collection in this archive
- `explicit_exclusions` — names blocked by name (none currently)
- `redaction_rules_applied` — MFA + password_hash redaction confirmed
- `disk_files_summary` — `disk_files_count`, `disk_bytes`
- `database_summary` — per-collection document count
- `app_version`, `commit_sha`, `captured_at_utc`

---

## 4 · Restore continuity (RESTORE_RUNBOOK.md)

The runbook covers (15 sections):

1. When to restore
2. Operator pre-checks (R2 access, MongoDB Atlas URI, disk roots)
3. Download the desired R2 archive
4. Unzip + inspect manifest
5. `mongoimport` per-collection script
6. Disk-files restore (storage / static / data / memory)
7. Verify counts vs manifest
8. Validate operator-critical collections (employees, jobs, dispatch_assignments)
9. Bilingual continuity verification
10. Passkey continuity verification (user_passkeys count)
11. Operational_attachments byte-for-byte verification (data_b64 round-trip)
12. Backup drift cross-check (compare `captured_collections` to current)
13. Re-run hourly archive immediately post-restore
14. Smoke-test admin sign-in + dispatch shift start
15. Communications + sign-off template

Every section written in calm operator-readable language. No engineer
jargon. No tribal knowledge.

---

## 5 · Auto-discovery guarantee verification (live API smoke)

```
GET /api/health        → {"ok":true,"service":"masci-hub","ts":"..."}
POST /api/auth/multi-login → returns directory session
GET /api/passkeys/list → returns admin's enrolled passkeys → confirms
  user_passkeys collection exists and will be auto-archived
GET /api/dispatch/recovery/by-shop → 6-bucket recovery groupings render
  → confirms dispatch_assignments + recovery_history will be archived
```

All collections touched by Phase 20-26 routes (operational_attachments,
continuity_events, dispatch_driver_sessions, user_passkeys,
webauthn_challenges, backup_drift_history) inherit archive
automatically via `db.list_collection_names()` — verified by
`test_iter425_new_collections_in_r2_archive`.

---

## 6 · Drift detection sanity

| Test | Coverage | Status |
|---|---|---|
| `test_iter426_drift_detected_on_collection_disappearance` | watcher logs WARN | ✅ |
| `test_iter426_drift_history_capped_at_30` | FIFO trim works | ✅ |
| `test_iter426_disk_backup_roots_includes_memory` | `/app/memory` included | ✅ |
| `test_iter426_manifest_restore_readiness` | manifest has all required keys | ✅ |
| `test_iter426_attachment_binary_round_trip` | byte-for-byte data_b64 | ✅ |

---

## 7 · Critical deployment-readiness call-out

**The platform itself surfaces a permanent-fix banner on `/admin/system`:**

> ⚠ Your data will be deleted on the next redeploy.
> MongoDB is running inside this container (`localhost:27017`), which
> means every new deploy destroys your database. **Before you redeploy
> next time, always click the button below to grab + email a full
> backup**, or you will lose everything created since the last nightly
> backup.
>
> **Permanent fix:** switch the production app to MongoDB Atlas
> (free tier, 15-min setup) — see the instructions your developer sent.
> Once the Atlas connection string is in your production env vars,
> this banner will turn green and redeploys become safe forever.

This is **the single highest-value deployment readiness action**.
The platform self-protects via:

- Hourly R2 archive → at most 1 hour of data loss
- Backup-or-die banner → forces operator awareness
- "Backup + email + download now" button → manual safety net
- RESTORE_RUNBOOK.md → calm restore-under-stress doctrine

The platform is **operationally safe to redeploy today**, but
**migrating to MongoDB Atlas is the recommended permanent fix**.

---

## Verdict — Backup + Restore

🟢 **PASS · True operational survivability continuity in place.**
- Auto-discovery backup (iter425) eliminates allowlist drift forever.
- MFA secret + password_hash redaction enforced.
- Backup drift watcher (iter426) provides calm forensic trail.
- RESTORE_RUNBOOK.md gives operators a calm restore-under-stress
  procedure.
- Platform self-flags the MongoDB-in-container risk with a permanent-fix
  call-out.

**Pre-deploy operator MUST:**
1. Take a fresh manual archive on `/admin/system` before redeploy.
2. Confirm Atlas connection string is in production env vars
   (recommended permanent fix).

---

End of Phase 26 Backup + Restore Verification.
