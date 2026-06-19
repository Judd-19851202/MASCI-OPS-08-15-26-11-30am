# TRACK 15.36 · Restore Runbook

**Track:** 15.36 · READ-ONLY architecture certification
**Date:** 2026-02
**Scope:** Document every restore path. NOT a destructive test — this is the operational map.

For each scenario, the runbook below answers: what data comes back, who can run it, how long it takes, what credentials are needed, what can go wrong, whether it's been tested.

---

## Scenario 1 · Single collection accidentally deleted (Mongo drop)

**What this restores:** the entire dropped collection
**Restore path:** pull most-recent R2 zip → extract `{kind}/json/*.json` → bulk insert via `POST /api/exports/restore` (with `merge=true` if other collections must stay intact)

| Step | Detail |
|---|---|
| Credentials | Admin token (`X-Admin-Token` from `/api/auth/multi-login`) |
| Services needed | Backend up · Mongo up · R2 reachable for archive pull |
| Time | 5–15 min (download ~600 MB · extract · upload via `/api/exports/restore`) |
| Data recovered | Records as of newest hourly backup — up to **1 hour** lost since last archive |
| Risk | The 500 MB upload ceiling means a full backup cannot be re-uploaded as-is. Operator must extract just the affected collection from the zip and re-package <500 MB. |
| Tested | Manifest-validated via `Track 14.0-I1` audit · merge mode exists in code; specific drop-restore drill has not been recorded in CHANGELOG. |

---

## Scenario 2 · Single document accidentally deleted (hard delete)

**What this restores:** one row by id
**Restore path:** download most-recent R2 archive → `unzip` → find `{kind}/json/{id}.json` → manually `db.<coll>.insertOne(<doc>)` via Mongo shell or repack a minimal restore zip

| Step | Detail |
|---|---|
| Credentials | Admin token + Mongo direct access (or recompose a minimal restore zip and call `POST /api/exports/restore` with `merge=true`) |
| Time | 5–10 min if Mongo shell access available |
| Data recovered | The record's last-archived state — up to **1 hour** lost |
| Risk | Foreign-key drift if other collections changed since the archive |
| Tested | No automated drill |

---

## Scenario 3 · Daily report accidentally deleted

**Path A · Soft-deleted (most common):** No dedicated `/admin/daily-reports/{id}/restore` endpoint exists. The four documented soft-delete restore endpoints (employees · jobs · equipment-master · suppliers) **do not cover daily_reports**.

**Path B · Hard-deleted or soft-delete-restore-missing:** follow Scenario 2 (pull from R2 archive).

| Credentials | Admin token |
|---|---|
| Time | 5–10 min |
| Data recovered | Last archived state — up to 1h lost |
| Gap | **No portal-level "undelete daily report" UI; restore is operator-only via R2 zip extraction.** |

---

## Scenario 4 · User account accidentally deleted

**What this restores:** user_directory row · per-portal user collection row (pm/hr/safety/shop/dispatch/field-leadership)

**Critical caveat:** `BACKUP_SENSITIVE_FIELD_REDACTION` strips `password_hash`, `mfa.secret`, `mfa.recovery_codes` from `user_directory` and `users` collections. **A restored user cannot log in until the operator re-enrolls password + MFA.**

| Credentials | Admin token |
|---|---|
| Time | 5 min restore + 5 min operator password reset = ~10 min |
| Data recovered | All non-credential fields |
| Gap | Restored user has no working credentials — must re-onboard auth |

---

## Scenario 5 · Project team assignment accidentally deleted

**Path:** pull most-recent R2 archive → extract `project_team_assignments/json/{id}.json` → repack + `POST /api/exports/restore` with `merge=true`

The audit trail in `project_team_assignment_audit` collection is also backed up — so the soft-delete `action=remove` event is preserved across restore.

| Credentials | Admin token |
|---|---|
| Time | 5–10 min |
| Data recovered | Both the assignment row + its audit history |

---

## Scenario 6 · Entire Mongo database corrupted

**Path A · Atlas Continuous Backup (if enabled):** restore via Atlas dashboard to a chosen PITR time.

**Path B · R2 archive bulk restore:** spin up a fresh Mongo instance · for each `{kind}/json/*.json` in the most-recent R2 zip, bulk insert into the new DB · point production at the new DB.

| Credentials | Atlas admin (Path A) · Atlas + R2 credentials (Path B) |
|---|---|
| Time | Path A: ~15 min (Atlas restore) · Path B: 1–4 hours (bulk import 138k records + 163 collections) |
| Data recovered | Path A: PITR time (≤24h lost) · Path B: last R2 archive (≤1h lost) |
| Risk | Path A requires Atlas backup tier — **OPERATOR REQUIRED** to verify. Path B: photos re-inlined from archive are at last-archive state. |
| Tested | No automated drill |

---

## Scenario 7 · Entire R2 bucket corrupted

**Atlas alone covers DB recovery.** Loss scope: photos and inlined PDFs that exist only in R2.

The latest R2 backup archive itself is also lost. If Atlas has snapshots, full restore proceeds via Atlas; photos are unrecoverable unless:
* Cloudflare R2 bucket versioning was enabled (must verify — **OPERATOR REQUIRED**)
* OR an out-of-band backup was made by Cloudflare retention policy

| Credentials | Atlas admin |
|---|---|
| Time | 15–30 min (DB restore from Atlas) + days/weeks of photo unavailability |
| Data recovered | All Mongo data via Atlas; **NO photos** unless R2 versioning was on |
| Risk | Photo loss is catastrophic for compliance evidence (incident photos, JHA documentation) |

---

## Scenario 8 · Emergent pod destroyed

**Path:** code is in GitHub (Save-to-GitHub) · Mongo data is in Atlas (live · already off-pod) · R2 backups are in Cloudflare (off-pod) · Photos are in R2 (off-pod).

Recovery: spin up new Emergent project · point at same Atlas + R2 via env vars · deploy from GitHub.

| Credentials | Atlas + R2 + Emergent platform admin |
|---|---|
| Time | 30 min – 2 hours |
| Data recovered | 100% — all state lives off-pod |
| Risk | Time to discover env-var divergence between old and new pod |
| Documented | `ops_manual.py:196` describes the disaster scenario explicitly |

---

## Scenario 9 · Bad deployment shipped (production code regression)

**Path:** "Save to GitHub" preserves every commit. Operator uses Emergent rollback feature OR reverts the GitHub commit and redeploys.

| Credentials | Emergent platform access · GitHub write |
|---|---|
| Time | 5–15 min |
| Data recovered | No data change — this is code-only rollback |
| Risk | A schema-changing migration may have run; rolling back code without rolling back data leaves the DB in a forward state |

---

## Scenario 10 · Operator accidentally deletes a backup object

**Recovery depends on R2 versioning status (**OPERATOR REQUIRED** to verify):**

| R2 versioning state | Recovery |
|---|---|
| **Enabled** | Restore prior version via Cloudflare API/dashboard — original key recoverable |
| **Disabled** | **DELETION IS PERMANENT.** If the deleted backup was the most recent, fall back to the previous hourly archive (max 1h additional data loss). |

| Time | ~5 min if versioning · forever if not |
| Data recovered | Versioning: 100% · No versioning: previous hourly = 1h gap |

---

## Scenario 11 · Atlas outage

**Path:** Atlas is the live Mongo. During outage, the application cannot read or write. Backup R2 archives remain accessible (Cloudflare is independent).

Recovery options:
1. **Wait** — Atlas typically restores within minutes; SLA-backed
2. **Failover to fresh Mongo** — spin up Docker Mongo · import latest R2 archive · point app at new MONGO_URL · accept ≤1h of data loss

| Credentials | R2 credentials + new Mongo provisioning |
|---|---|
| Time | Wait: 5 min – 4 hours (Atlas SLA) · Failover: 1–2 hours |
| Risk | When Atlas comes back, the operator must reconcile any data written during the failover window |

---

## Scenario 12 · Cloudflare R2 outage

**Effect:**
* Live photos (read from R2) return 502/timeout — degraded UX
* New hourly backup writes fail — gap in backup history
* Atlas Mongo stays live — application can read/write all non-photo data

**Recovery:** Cloudflare typically restores within minutes. R2 backups resume on next scheduler tick.

| Risk | Photo evidence temporarily unavailable; safety-form submissions captured in Mongo but new photos pending re-upload |
| Time | Outage-dependent (Cloudflare SLA) |

---

## Cross-scenario gaps

| Gap | Risk |
|---|---|
| **500 MB upload ceiling on `/api/exports/restore`** vs 600 MB current backup size — full-archive restore via the documented endpoint is **broken** for current-size archives. Operator must extract+repack. | 🔴 Documented but unaddressed |
| **No portal-level undelete UI for daily_reports, meetings, incidents, JHAs, corrective_actions, notifications** — only employees/jobs/equipment/suppliers have soft-delete restore endpoints | 🟡 Operator-only restore path for most safety-form data |
| **Password hashes & MFA stripped from backups** — restored users cannot log in until re-onboarded | 🟡 Documented (`BACKUP_SENSITIVE_FIELD_REDACTION`); expected behavior |
| **No automated restore drill ever recorded in CHANGELOG** — every restore path above is theoretical | 🔴 Untested in anger |
| **Atlas backup tier UNKNOWN from pod** — without it, Scenario 6 Path A is theoretical | 🔴 OPERATOR REQUIRED |
| **R2 versioning UNKNOWN from pod** — without it, Scenario 10 default is "permanent loss" | 🔴 OPERATOR REQUIRED |
| **Drift watcher dormant** — silent collection drops not auto-alerted | 🟡 Logs only |

---

## Who can run what

| Restore path | Required role |
|---|---|
| Soft-delete undo (employees/jobs/equipment/suppliers) | Admin (`X-Admin-Token`) |
| Full-archive `/api/exports/restore` | Admin |
| Atlas PITR | Atlas project admin (external to platform) |
| R2 object-version restore | Cloudflare R2 admin (external) |
| GitHub commit revert | Repository write access |
| Emergent pod re-spin | Emergent platform admin |

---

## Recommended runbook order on a real incident

1. **Stop the bleed.** Determine what was lost · when · how.
2. **Atlas first.** If Atlas Continuous Backup is enabled, PITR is the lowest-RPO option (≤24h depending on tier).
3. **R2 second.** Use the most recent hourly archive for the affected scope.
4. **Document.** Every restore writes an `audit_events` row via `_record_audit`.
5. **Re-verify.** Run `/api/admin-strict/diag/persistence-health` + the v15.34B production health probe.

---

🛑 This runbook is informational. NO destructive restore drill was performed during Track 15.36.
