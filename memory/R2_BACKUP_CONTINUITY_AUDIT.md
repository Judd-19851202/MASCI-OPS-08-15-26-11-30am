# R2_BACKUP_CONTINUITY_AUDIT.md
## Phase 25.2 · MASCI Platform Backup Coverage Audit
## Date: 2026-05-25 · iter425 audit + remediation

---

## ✅ REMEDIATION LANDED · 2026-05-25 (iter425)

Both **P0** (R2 auto-discovery) and **P1** (MFA secret redaction) fixes are now live.
The disaster-recovery gap identified in Section 11 is **CLOSED**.

### Fixes shipped

| # | Fix | File / location | Status |
|---|-----|-----------------|--------|
| 1 | R2 complete-archive switched from `EXPORTABLE_KINDS` allowlist → `db.list_collection_names()` auto-discovery | `server.py:_build_complete_archive_on_disk` (~line 5550-5680) | 🟢 LIVE |
| 2 | `mfa.secret` + `mfa.recovery_codes` redacted on `user_directory` in BOTH pipelines | `server.py:BACKUP_SENSITIVE_FIELD_REDACTION` (line 4080-4100) | 🟢 LIVE |
| 3 | Explicit exclusion logging via `logger.info("[complete-archive] explicit exclusions ...")` + `MANIFEST.explicit_exclusions` | `server.py:_build_complete_archive_on_disk` | 🟢 LIVE |
| 4 | New manifest fields: `captured_collections` · `explicit_exclusions` · `redaction_rules_applied` | every R2 archive zip's MANIFEST.json | 🟢 LIVE |

### Verification

- **`test_iter425_backup_auto_discovery.py` · 6 / 6 PASS**:
  - ✅ R2 archive now contains: `dispatch_assignments`, `dispatch_continuity_events`, `operational_attachments`, `user_passkeys`, `user_directory`
  - ✅ MFA secrets + recovery_codes are STRIPPED from `user_directory` records in the archive
  - ✅ `password_hash` regression guard on `users` still passes
  - ✅ Operational attachment `data_b64` binary preserved end-to-end (restore-readiness round-trip)
  - ✅ Legacy `EXPORTABLE_KINDS` six kinds still covered under their friendly names
  - ✅ MANIFEST.json contains the new audit fields
- **Full parity-lock**: 245 / 245 PASS (no regressions)
- **Ruff**: clean on all changed files
- Smoke verified manually by building one archive against the live preview DB.

### Before / After behavior

| Surface                              | Before iter425             | After iter425                                |
|--------------------------------------|----------------------------|----------------------------------------------|
| Collection discovery in R2 archive   | Hard-coded 6-entry allowlist | `db.list_collection_names()` auto-discovery |
| Phase 12-25 collections in R2        | 🔴 MISSED                  | 🟢 INCLUDED automatically                    |
| MFA TOTP secrets in any backup       | 🔴 PRESENT (plaintext)     | 🟢 REDACTED before write                     |
| Excluded collections in audit trail  | 🔴 Silent                  | 🟢 Logged + listed in MANIFEST.json          |
| Future new collections               | 🔴 Required manual allowlist update | 🟢 Inherit coverage automatically   |

### Manifest schema (new fields)

```json
{
  "generated_at": "2026-05-25T04:30:00Z",
  "mode": "complete",
  "source": "mascidocs.com",
  "total_records": 38241,
  "per_kind": { "dispatch_assignments": 1247, ... },
  "captured_collections": ["dispatch_assignments", "dispatch_continuity_events", ... ],
  "explicit_exclusions": [],
  "redaction_rules_applied": ["user_directory", "users"],
  "inlined_photos": 412,
  "inlined_photo_bytes": 18421502,
  "failed_photos": 0,
  "notice": "Complete standalone backup. ... MFA secrets, password hashes, and recovery codes are redacted."
}
```

### Updated Go / No-Go

| Scenario | Before iter425 | After iter425 |
|----------|----------------|---------------|
| Daily ops · email backup live | 🟢 GO | 🟢 GO |
| Container disaster · restore from local zip | 🟢 GO | 🟢 GO |
| Disaster recovery from **R2 only** | 🔴 NO-GO | 🟢 **GO** |
| Live customer rollout depending on R2 as off-site copy | 🟠 CONDITIONAL | 🟢 **GO** |

---

## 1. Executive Verdict (PRE-REMEDIATION — preserved for record)

**Mixed: partially safe · one real gap that must be closed before depending on R2 alone for disaster recovery.**

| Backup path                          | Verdict      | Detail                                              |
|--------------------------------------|--------------|-----------------------------------------------------|
| Local nightly slim/full zip (email)  | 🟢 SAFE      | Auto-discovers every Mongo collection at runtime    |
| Local disk-files in zip              | 🟢 SAFE      | `/app/backend/storage`, `static`, `data` covered    |
| Operational-attachment binaries      | 🟢 SAFE      | Stored inline as `data_b64` in `operational_attachments` collection → flows through auto-discovery |
| **R2 nightly complete archive**      | 🔴 **GAP**   | **Allowlist-only (`EXPORTABLE_KINDS`) · MISSES every new Phase 12-25 collection** |
| /app/memory doctrine/PRD docs        | 🟠 partial   | Tracked in git but NOT in backup zip — relies on repo as backup |
| Passkey credential metadata          | 🟢 SAFE      | Captured by local-zip auto-discovery · NO biometric data present (verified) |
| TTL `webauthn_challenges`            | 🟢 ok-to-skip | Captured by auto-discovery but stale rows expire in 5 min · documented exclude candidate |

**Headline number**: The local nightly zip emailed to operators IS a complete disaster-recovery archive. The R2 cloud copy is NOT.

---

## 2. Backup Mechanism Summary

The platform runs **TWO independent backup pipelines** from the same in-process scheduler (`_backup_scheduler_loop` in `server.py:6153`):

### Pipeline A · Local nightly zip + email  (PRIMARY · auto-discovery)
- Function: `_build_backup_zip_to_path` (`server.py:4375`)
- Schedule: configured by `BACKUP_HOUR_UTC` (default 02:00 UTC)
- Modes:
  - `full`  → `MASCI_full_backup_<TS>.zip` (every record · base64 photos inlined)
  - `lite`  → `MASCI_lite_backup_<TS>.zip` (slim · base64-stripped) — fallback when disk-pressure detected
- **Collection discovery: `await db.list_collection_names()` at line 4504** — auto-includes any new collection going forward.
- Output: written to `/app/backend/backups/`, emailed to `BACKUP_EMAIL_TO` via `_email_backup_zip_from_path`.
- Disk artifacts in the zip:
  - `/app/backend/storage` → `disk_files/storage/...`
  - `/app/backend/static`  → `disk_files/static/...`
  - `/app/backend/data`    → `disk_files/data/...`
- Manifest: `backup_manifest.json` lists `captured_collections` + `all_db_collections_at_backup_time` (audit trail of what was in the DB at backup time).

### Pipeline B · R2 cloud archive  (SECONDARY · ALLOWLIST · ⚠️ GAP)
- Function: `_build_complete_archive_on_disk` (`server.py:5545`)
- Driver: `_run_complete_archive_to_r2` (`server.py:5759`)
- Schedule: `BACKUP_R2_FULL_HOUR_UTC` (default 03:00 UTC) — runs once per day after local-zip completes.
- Upload key pattern: `r2://<S3_BUCKET>/backups/auto-90d/MASCI_complete_backup_<TS>.zip`
- Lifecycle: 90-day retention under the `auto-90d/` prefix (see `R2_RETENTION_AUDIT.md`)
- **Collection discovery: hard-coded `EXPORTABLE_KINDS` allowlist** (`server.py:4070`):
  ```python
  EXPORTABLE_KINDS = {
    "inspections": "inspections",
    "meetings": "meetings",
    "jhas": "jhas",
    "incidents": "incidents",
    "daily-reports": "daily_reports",
    "equipment-inspections": "equipment_inspections",
  }
  ```
  Only those six collections are dumped + only photo refs inside those documents are inlined as bytes.

### Health tracking
- `backup_health` collection records every backup attempt (`ok / mode / filename / size_bytes / records / ts`).
- Diagnostic endpoint `/api/admin-strict/diag/backup-health` (read-only) shows the last successful row.
- Scheduler liveness ping: 1-hour staleness alarm via `_record_backup_health` rows.

---

## 3. Collection Coverage Table  (live DB · `await db.list_collection_names()`)

| Collection                          | Phase added | Pipeline A (local/email) | Pipeline B (R2 archive) | Notes |
|-------------------------------------|-------------|--------------------------|-------------------------|-------|
| inspections                         | pre-12      | 🟢 yes                   | 🟢 yes (allowlist)      | Phase 11 safety |
| meetings                            | pre-12      | 🟢 yes                   | 🟢 yes                  |       |
| jhas                                | pre-12      | 🟢 yes                   | 🟢 yes                  |       |
| incidents                           | pre-12      | 🟢 yes                   | 🟢 yes                  |       |
| daily_reports                       | pre-12      | 🟢 yes                   | 🟢 yes                  |       |
| equipment_inspections               | pre-12      | 🟢 yes                   | 🟢 yes                  |       |
| **dispatch_assignments**            | Phase 12    | 🟢 yes (auto)            | 🔴 **MISSED**           | Includes `recovery_history[]` + `recovery_state` (iter420) |
| **dispatch_state_events**           | Phase 12    | 🟢 yes (auto)            | 🔴 **MISSED**           | Lifecycle audit trail (append-only) |
| **haul_cycles**                     | Phase 13    | 🟢 yes (auto)            | 🔴 **MISSED**           |       |
| **dispatch_continuity_events**      | iter419     | 🟢 yes (auto)            | 🔴 **MISSED**           | Operational narrative · 5 canonical kinds |
| **operational_attachments**         | iter417     | 🟢 yes (auto · w/ data_b64) | 🔴 **MISSED · INCLUDES PHOTO BYTES** | breakdown_photo · load_photo · damage_photo etc. |
| **dispatch_driver_sessions**        | iter393     | 🟢 yes (auto)            | 🔴 **MISSED**           | Short-lived but useful for forensics |
| **user_passkeys**                   | iter422     | 🟢 yes (auto)            | 🔴 **MISSED**           | Public-key credential metadata only · NO biometric data |
| **webauthn_challenges**             | iter422     | 🟢 yes (auto · TTL stale OK) | 🔴 **MISSED**       | TTL 5 min · candidate for explicit exclude both pipelines |
| backup_health                       | misc        | 🟢 yes (auto)            | 🔴 missed (low value)   | Self-referential — restore doesn't need history |
| equipment_master / equipment_parts  | pre-12      | 🟢 yes (auto)            | 🔴 missed               | Master data — should be in R2 too |
| user_directory · users · …          | mixed       | 🟢 yes (auto · pw redacted) | 🔴 missed             | password_hash redacted in BOTH pipelines |

**Total NEW collections excluded from R2 nightly cloud archive: 8+** (highlighted in red).

---

## 4. Operational Attachment Binary Coverage

Attachments (Phase 20 / iter417 onward) include `breakdown_photo`, `load_photo`, `damage_photo`, `inspection_photo`, `delivery_proof`, `operational_note_photo`.

**Storage model**: inline base64 inside the document (`routes/operational_attachments.py:212`):
```python
"data_b64": base64.b64encode(raw).decode("ascii")
```

Implications:
- Pipeline A (local zip): the binary travels INSIDE the JSON dump as a base64 string → fully restorable.
- Pipeline B (R2): the entire `operational_attachments` collection is OUT of `EXPORTABLE_KINDS` → not in the R2 archive at all.

The R2 archive's `_iter_photo_refs` helper looks for `photo://<bucket>/<key>` URL refs — but operational attachments don't use that pattern. They're inline blobs. So even if `operational_attachments` were added to `EXPORTABLE_KINDS`, the binary inlining loop wouldn't fetch anything (the bytes are already in the JSON). That's actually fine — JSON dump = full restore.

**Verdict**: Attachments are SAFE in pipeline A. UNSAFE in pipeline B (entire collection missing).

---

## 5. Filesystem / Memory Doc Coverage

`DISK_BACKUP_ROOTS` (`server.py:4557`) covers:
- `/app/backend/storage`  — uploaded FDOT plans / project docs
- `/app/backend/static`   — training videos, safety cards, branding
- `/app/backend/data`     — equipment_master seed JSON, employee seed

**NOT covered:**
- `/app/memory/*.md` (PRD.md, doctrine, debrief docs, phase audits)
- `/app/backend/guidance/*.py` (guidance content + ES translations)
- `/app/frontend/src/lib/i18n.js`

These ARE in git. So if the repo is the source of truth (which it is), they survive any container loss. Document this dependency explicitly — losing the repo + the R2 archive would lose those docs.

---

## 6. R2 Key Structure (verified from code)

```
r2://<S3_BUCKET>/
  backups/auto-90d/MASCI_complete_backup_<UTC-stamp>.zip     ← Pipeline B nightly
  photos/<assignment_id>/<uuid>.jpg                           ← legacy R2 photo storage (Phase 11)
  ... other ad-hoc R2 keys per `photo_storage.py`
```

- Bucket env: `S3_BUCKET`
- Endpoint:  `S3_ENDPOINT_URL`
- Region:    `S3_REGION` (default `auto`)
- Keys:      `S3_ACCESS_KEY` · `S3_SECRET_KEY`
- Lifecycle rule (configured separately by `scripts/r2_lifecycle_apply.py`): only deletes under `auto-90d/` prefix · legacy zips uploaded before iter184 are preserved indefinitely.
- Usage probe: `_log_r2_usage_warning` warns at 45 GB · alerts at 50 GB. Quiet on success.

---

## 7. Restore Readiness

### Local-zip restore
A consumer of `MASCI_full_backup_<TS>.zip` can:
1. Read `backup_manifest.json` → confirm `all_db_collections_at_backup_time` matches expectations
2. For each `collections/<name>.json` → `mongoimport`-equivalent (each file is a JSON array of `_id`-stripped docs)
3. For each `disk_files/<archive_prefix>/<rel>` → write back into `/app/backend/<archive_prefix>/...`
4. Operational attachments restore automatically because `data_b64` carries the binary

### R2-archive restore
Same shape but only the six allowlisted kinds (`<kind>/json/<id>.json`) and the photo bytes under `photos/<key>`. **A pure R2 restore today would NOT restore dispatch, recovery, attachments, passkeys, or continuity events.**

### Documented restore instructions
- Local zip: implicit from manifest structure · no operator-facing runbook
- R2 archive: `R2_RETENTION_AUDIT.md` referenced in code but a step-by-step restore RUNBOOK does not appear to exist as a doc file

**Gap**: No formal restore runbook. Should be added but is OUTSIDE this audit's surgical-fix budget.

---

## 8. Data Sensitivity Review

| Surface           | What it stores                  | Sensitive? | Backup contains? |
|-------------------|---------------------------------|------------|-------------------|
| user_passkeys     | credential_id (b64url), public_key, sign_count, friendly_name, rp_id, timestamps | Public-key cryptography — safe to back up | yes (no biometric data ever stored) |
| webauthn_challenges | short-TTL random challenges | Low value · TTL expires | yes but worthless after 5 min |
| user_directory    | email, password_hash (bcrypt), mfa.secret, mfa.recovery_codes | Hash is salted bcrypt; MFA secrets ARE sensitive | yes — Pipeline A redacts `password_hash` (line 4501) but NOT `mfa.secret` |
| users             | password_hash | bcrypt | yes — explicitly redacted via `SENSITIVE_FIELD_REDACTION` |
| operational_attachments.data_b64 | image bytes | Field-operational photos | yes |

**Finding**: `user_directory.mfa.secret` is NOT in the `SENSITIVE_FIELD_REDACTION` map. The bcrypt password_hash IS redacted on the `users` collection but the directory-row hash is NOT (the directory uses a different field path). Surface this for separate review.

Biometric data: confirmed NEVER stored. iter422 audit holds.

---

## 9. Explicit Excluded Collections (intentional)

| Collection            | Excluded by                | Reason (must be documented) |
|-----------------------|----------------------------|------------------------------|
| `system.*`            | both pipelines             | Mongo internal · not customer data |
| Pipeline A: explicit exports | line 4492-4497 (EXCLUDE_FROM_AUTO_BACKUP — uses EXPORTABLE_KINDS to avoid double-counting) | the same data is already exported in dedicated CSV/PDF paths · auto-discovery skips to prevent duplicates |
| `webauthn_challenges` | NOT currently excluded     | candidate for explicit exclude — TTL makes content worthless within minutes |
| `dispatch_driver_sessions` | NOT currently excluded | candidate for explicit exclude — sessions expire on backend restart anyway, restore is meaningless |

---

## 10. Risks  (ranked by impact)

| # | Risk                                                                                          | Likelihood | Impact | Severity |
|---|-----------------------------------------------------------------------------------------------|------------|--------|----------|
| 1 | R2-only disaster recovery would lose ALL Phase 12-25 trucking, attachments, passkeys          | LOW (we still have local zip + email) | HIGH     | 🔴 P0 |
| 2 | Local backup zip email fails for >26 h → no fresh off-site copy of DLS/trucking data         | LOW (heartbeat watchdog alerts) | HIGH | 🟠 P1 |
| 3 | `/app/memory/PRD.md` lost in repo-loss + R2-only restore scenario                             | VERY LOW | LOW | 🔵 P3 |
| 4 | `webauthn_challenges` bloats every nightly zip with stale TTL'd rows                          | LOW | LOW | 🔵 P3 |
| 5 | `user_directory.mfa.secret` not redacted in backup dumps                                      | MEDIUM | MEDIUM (TOTP secrets in backup) | 🟠 P1 |

---

## 11. Required Fixes

### P0 · MUST fix before depending on R2 as a disaster-recovery surface
**Fix 1**: Switch `_build_complete_archive_on_disk` to auto-discovery (mirroring Pipeline A).
- Either iterate `db.list_collection_names()` with the same EXCLUDE rules, OR
- Extend `EXPORTABLE_KINDS` with the new collections (less ideal — still an allowlist).

Recommendation: convert to auto-discovery. Then NEW collections automatically inherit R2 coverage going forward (zero maintenance · same doctrine as Pipeline A).

### P1 · should fix soon
**Fix 2**: Add `mfa.secret` and `mfa.recovery_codes` to `SENSITIVE_FIELD_REDACTION` on `user_directory`.

### P3 · nice to have (defer · documented)
**Fix 3**: Add explicit `EXCLUDE_FROM_BACKUP` set including `webauthn_challenges` and `dispatch_driver_sessions` (transient).
**Fix 4**: Add `/app/memory/*.md` to `DISK_BACKUP_ROOTS` (small · cheap insurance against repo loss).
**Fix 5**: Author a formal restore runbook (`RESTORE_RUNBOOK.md`).

---

## 12. Go / No-Go Verdict

| Scenario | Go? |
|----------|-----|
| Day-to-day operations · platform live · daily email backup arriving | 🟢 **GO** |
| Container redeploy / disk loss · restore from latest local zip | 🟢 **GO** (auto-discovery captures everything) |
| Disaster recovery from R2 only (no local zip, no email archive) | 🔴 **NO-GO** until Fix 1 lands |
| Live customer rollout · DLS/trucking data depended on for proof | 🟠 **CONDITIONAL GO** — safe IF email backups arrive AND local zip retention >7 days · NOT safe assuming R2 is the only off-site copy |

**Bottom line**: Email zip is the trustworthy off-site copy today. R2 is a secondary archive with an allowlist gap. Fix 1 is small and surgical.

---

## Audit Methodology

- Read-only inspection of `server.py` (lines 4070-5860), `routes/operational_attachments.py`, `routes/passkeys.py`, `routes/dispatch_continuity.py`
- Verified `list_collection_names()` auto-discovery path in `_build_backup_zip_to_path`
- Verified `EXPORTABLE_KINDS` allowlist in `_build_complete_archive_on_disk`
- Verified `data_b64` inline storage in `routes/operational_attachments.py:212`
- Verified `DISK_BACKUP_ROOTS` triplet at `server.py:4557`
- Verified R2 key pattern + lifecycle in `_run_complete_archive_to_r2`
- Inspected `backup_health` collection role
- NO writes performed during this audit

End of audit.
