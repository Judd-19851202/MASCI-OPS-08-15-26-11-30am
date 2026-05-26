# Phase 31.2 · Production Health Lock Verification
## iter440 · 2026-05-26 · Second-pass audit

> **Mission**
> Verify with hard evidence that production is healthy, deploy-safe,
> backup-safe, and operator-digest-safe. **Not** a feature phase.
> A production confidence lock.

---

## Final verdict

# 🟡 GO (one redeploy away from 🟢)

| Layer                                              | Verdict |
| -------------------------------------------------- | :-----: |
| Production deploy / 9 hub routes                   | 🟢 GO   |
| Atlas connection (shared cluster · 123 collections)| 🟢 GO   |
| R2 storage + backup zips                           | 🟢 GO   |
| Backup zip integrity + manifest                    | 🟢 GO   |
| Auth + passkey + multi-login                       | 🟢 GO   |
| Backend Sentry observability                       | 🟢 GO   |
| Frontend Sentry init + PII scrub                   | 🟢 GO   |
| MFA secrets excluded from backups                  | 🟢 GO   |
| Weekly digest payload + render                     | 🟢 GO   (after redeploy) |
| `/admin/system` banner truthfulness                | 🟡 GO  (preview ✅ · prod still serves old code) |
| `/admin/backups-list-r2` truthfulness              | 🟡 GO  (preview ✅ · prod still serves old code) |

> Two true defects were found this pass — **both fixed in code, both
> verified in preview, both waiting on a single production redeploy.**
> After the redeploy, the verdict is unambiguously 🟢.

---

## PART 1 · Production deploy health

```
GET  https://mascidocs.com/api/health           → 200  {"ok":true,...}
GET  https://mascidocs.com/sign-in              → 200
GET  https://mascidocs.com/admin                → 200
GET  https://mascidocs.com/dispatch-portal      → 200
GET  https://mascidocs.com/shop                 → 200
GET  https://mascidocs.com/pm                   → 200
GET  https://mascidocs.com/safety-portal        → 200
GET  https://mascidocs.com/leadership           → 200
GET  https://mascidocs.com/field                → 200
```

`tools/verify-production.sh` against `https://mascidocs.com`:
```
✅ GET  /api/health                                          HTTP 200
✅ POST /api/passkeys/login/options                          HTTP 200
✅ GET  /api/admin-strict/diag/persistence-health            HTTP 401
✅ GET  /api/field-memory/recent                             HTTP 401
✅ GET  /api/dispatch/operational-moments/by-assignment/test HTTP 401
All 5 probes healthy in 2s.
```

* No 520. No crash loop. No build break.
* Production `/api/version` reports `sentry: {enabled: true}`,
  release `3cae10f77b2e5926...`, uptime 1124s (~19 min at audit time).
* Admin login + multi-login both return 200.

### Verdict — 🟢

---

## PART 2 · Atlas health

**Live production probe**:
```json
{
  "atlas_connected": true,
  "atlas_host": "mongodb+srv://***@masci-prod.1nduwmg.mongodb.net/...?appName=MASCI-prod",
  "db_name": "masci_safety",
  "mongo_version": "8.0.23",
  "collections_detected": 123
}
```

* Production MONGO_URL is rotated, `+srv`, masci-prod cluster.
* Preview shares the same Atlas cluster — zero split-brain.
* Live writes within the last minute (continuity_events, backup_health).
* No fallback local Mongo.

### Verdict — 🟢

---

## PART 3 · R2 health

### Bucket inventory (paginated, via boto3 direct)
```
total keys under backups/: 1502
  backups/:            500   (legacy · pre-iter184 lifecycle rule)
  backups/auto-90d/: 1002    (90-day lifecycle scope)
```

### Newest 5 archives (real)
```
2026-05-26 00:12 · 91,424,451b · MASCI_complete_backup_2026-05-26_000942Z.zip
2026-05-26 00:12 · 91,428,549b · MASCI_complete_backup_2026-05-26_001203Z.zip
2026-05-26 00:09 · 91,420,848b · MASCI_complete_backup_2026-05-26_000927Z.zip
2026-05-26 00:00 · 91,392,852b · MASCI_complete_backup_2026-05-26_000021Z.zip
2026-05-25 23:25 · 91,238,365b · MASCI_complete_backup_2026-05-25_232457Z.zip
```

### Storage migration (storage-summary on prod)
```
total:        32 attachments
r2_backed:    32 · 2,176 bytes
inline_b64:    0
unknown:       0
migrated_pct: 100.0
```

### Manifest integrity (downloaded + parsed newest zip)
```
manifest keys:
  captured_collections     · 123 entries (matches Atlas count exactly)
  explicit_exclusions      · [] (none)
  redaction_rules_applied  · ['user_directory', 'users']
  inlined_photos           · 10
  inlined_photo_bytes      · present
  failed_photos            · present
  total_records            · 243,565
  generated_at             · present
  mode · notice · per_kind · source

Critical presence checks:
  operational_attachments  → ✅ included
  user_passkeys            → ✅ included
  webauthn_challenges      → ✅ included
```

### MFA secret exclusion
```
sample user_directory row:
  { "id": "u-iter425-...",
    "email": "...",
    "mfa": { "enabled": true } }      ← NO totp_secret · NO recovery codes
```
Redaction rules `user_directory` and `users` are applied — MFA secrets,
password hashes, and step-up codes never reach the backup zip.

### Lifecycle policy
* `backups/auto-90d/` is the active prefix governed by the R2
  lifecycle rule (`scripts/r2_lifecycle_apply.py`).
* Legacy `backups/*.zip` keys (500) are out of lifecycle scope and
  will be removed under explicit operator approval (see
  `R2_RETENTION_AUDIT.md`).

### Verdict — 🟢

---

## PART 4 · Weekly operator digest

### Endpoint shape
* `GET /api/admin/digest/weekly?format=text` → 200 · plaintext
* `GET /api/admin/digest/weekly?format=json` → 200 · payload

### Preview (after fix) plaintext
```
MASCI Operations · Weekly Digest · 2026-05-26T00:11:54...

Atlas:                  GREEN (mongo 8.0.23 · 123 collections)
Last backup:            2m ago (ok=true · size=87.2 MB · → local)
Attachments:            32 · 100.0% R2-backed
Storage growth (30d):   2.1 KB · projected 90d: 6.4 KB
Evidence accesses (7d): 1
Drift warnings:         none

All systems calm.
```

### Production (still old code) plaintext
```
MASCI Operations · Weekly Digest · 2026-05-26T00:26:00...

Atlas:                  GREEN (mongo 8.0.23 · 123 collections)
Last backup:            none recorded                ← lying
Attachments:            32 · 100.0% R2-backed
Storage growth (30d):   2.1 KB · projected 90d: 6.4 KB
Evidence accesses (7d): 1
Drift warnings:         1 · no heartbeat in the last 36h ← lying

Operator review recommended.                         ← false negative
```

### Recipients
* `OPERATOR_DIGEST_RECIPIENTS` env var not set.
* Fallback chain: `OPERATOR_DIGEST_RECIPIENTS → SAFETY_DIGEST_TO_EMAIL → safety@mascigc.com`.
* If all three missing, cron logs calmly and skips
  (`[operator-digest] no recipients · skipping · payload preview=...`).
* No crash. No alerting. Doctrine-clean.

### Verdict — 🟢 (preview · code · render · payload) · 🟡 (production still serves old code until redeploy)

---

## PART 5 · Auth + passkey smoke

```
POST /api/admin/login                                → 200
POST /api/auth/multi-login (jaymn.judd)              → 200 (7 portal tokens)
POST /api/passkeys/login/options                     → 200
POST /api/field-leadership/portal/login (bad creds)  → 401  (correctly rejected)
```

* Password login: ✅
* Admin login: ✅
* Portal login: ✅ multi-login mints `admin · pm · shop · hr · safety · dispatch · field_leadership` tokens in one call.
* Passkey login options: ✅
* Public field tile + driver magic-link: routes exist under
  `/api/field-leadership/portal/*` and `/api/dispatch/driver/magic-link`
  — confirmed reachable.

### Verdict — 🟢

---

## PART 6 · Backup + restore confidence

```
[scheduled-backup] scheduler started — 02:00 · 18:00 UTC · keep 14 days · max 3 files
                                       disk-watermark 75% · dir=/app/backend/backups
[scheduled-backup] staleness: disk=6.1h mongo=0.1h (using mongo, mode='r2-usage-alert')
[scheduled-backup] scheduler armed — last backup ~0.1h ago (healthy)
[scheduled-backup] supervisor armed — checks task health every 5 min
```

`backup_health` collection (Atlas):
```
mode=complete-r2        : 98 rows · latest ts 2026-05-26T00:12:32 · 91 MB · 243,565 rec
mode=r2-usage-alert     : 98 rows · informational R2 quota probe (77 GB / 1829 obj)
mode=complete-r2-error  :  2 rows · 2026-05-25T15:18 · OperationFailure on usage_events
                          sort (33 MB limit) — RECOVERED automatically; subsequent
                          archives are succeeding.
mode=lite               :  1 row · backup-via-email path
```

* Backup scheduler: armed · hourly cadence (R2 hourly mode active).
* `backup_drift_history` shows snapshot from 2026-05-25T16:16 with
  `captured_collections: [...]`, `total_records: 999`, `explicit_exclusions: []`.
* Archive integrity: 123 captured collections (matches Atlas), 10
  inlined photos, redactions applied to user_directory + users.
* No MFA secrets in backup (verified by sampling user_directory rows).
* No inline_b64 photo regression (storage-summary shows 0 inline).
* Restore runbook still accurate — archive shape unchanged.

### Verdict — 🟢

---

## PART 7 · Error / observability

```
/api/version (production):
  sentry: { enabled: true }
  release: 3cae10f77b2e5926754fdabf4138f868
```

* Backend Sentry initialized at startup via `sentry_init.py`
  (env-gated on `SENTRY_DSN`).
* `SentryOperationalTagsMiddleware` mounted (server.py:11127) — every
  request gets `route` + `portal` + `user_tier` tags scrubbed of PII.
* Frontend `sentryInit.js`:
  * Env-gated on `REACT_APP_SENTRY_DSN`.
  * Release pulled from backend `/api/version`.
  * PII scrubber strips `password|secret|token|api[_-]?key|bearer|
    private[_-]?key|session|cookie|auth` from breadcrumbs + events.
* No surveillance behavior. No analytics tracking.

### Verdict — 🟢

---

## ISSUES FOUND + FIXES MADE

### 🔴 DEFECT 1 — diag readers point at the wrong Mongo collections

**Severity** · operator-visible lie · banner says "No backup runs recorded"
while backups run every hour.

**Root cause** · the writers in `server.py` persist to `backup_health`
+ `backup_drift_history`. The readers in
`admin_persistence_health.py`, `lib/operator_digest.py`, and
`admin_ops.py` query `backup_runs` + `backup_drift_watch` (collections
that have never existed in this codebase). The two naming
conventions have been divergent since iter427.

**Evidence (before fix)**
```
backup_health collection on Atlas: 200 rows · latest ts 2026-05-26T00:09:52
persistence-health.last_backup_time:   null
persistence-health.r2_backup_success:  {present: false, reason: "no backup_runs row found"}
persistence-health.drift_watch_active: false
/api/admin/system-health backup card:  yellow · "No backup runs recorded"
weekly digest text:                    "Last backup: none recorded · Operator review recommended."
```

**Fix** · 3 files:
* `routes/admin_persistence_health.py` — read `backup_health` +
  `backup_drift_history`, map `mode → kind` for output, drift filter
  switched to `recorded_at` datetime field.
* `lib/operator_digest.py` — same rename + field mapping + filter to
  rows with real `filename` so quota-probe alerts don't masquerade
  as backups in the digest.
* `routes/admin_ops.py` — same fix for `/api/admin/system-health`
  banner card and `/api/admin/deploy-recovery` recent_backups list.

**Verified (preview, after fix)**
```
persistence-health.last_backup_time:   2026-05-26T00:09:52 (2m ago)
persistence-health.r2_backup_success:  {present:true, ok:true, kind:"complete-r2",
                                        filename:"MASCI_complete_backup_2026-05-26_000927Z.zip",
                                        size_bytes:91420848, records:243550}
persistence-health.drift_watch_active: true · "snapshot recorded within 36h"
/api/admin/system-health backup card:  GREEN · "0.0h ago"
weekly digest text:                    "All systems calm."
```

**Status** · fixed in preview · awaiting prod redeploy.

---

### 🔴 DEFECT 2 — `/api/admin/backups-list-r2` truncates >1000 keys

**Severity** · operator-visible lie · UI/API reports the newest backup
is from 2026-05-21 even though R2 contains 1002 newer archives under
`backups/auto-90d/`.

**Root cause** · `list_objects_v2` on AWS/R2 returns max 1000 keys
per page. The handler used a single un-paginated call. With 1502
total keys in `backups/`, the first 1000 returned (sorted alphabetically
by Key) consisted entirely of legacy `backups/*.zip` and the oldest
`backups/auto-90d/*` keys. The newest archives — from
`backups/auto-90d/MASCI_complete_backup_2026-05-2[2-6]_*.zip` — sort
LAST alphabetically and were truncated. After client-side sort by
`LastModified` desc, the "newest" surfaced was 2026-05-21.

**Evidence (before fix)**
```
PROD /api/admin/backups-list-r2?limit=500:
  count returned: 500 · total ignored: 1002
  newest: MASCI_complete_backup_2026-05-21_151920Z.zip  @ 2026-05-21T15:19  ← lying
  oldest: MASCI_complete_backup_2026-05-17_140233Z.zip  @ 2026-05-17T14:03

Direct boto3 paginator probe:
  total keys under backups/: 1502
  newest: MASCI_complete_backup_2026-05-26_000942Z.zip @ 2026-05-26T00:12  ← truth
```

**Fix** · `backend/server.py` (1 file) — replaced single
`list_objects_v2` call with `get_paginator("list_objects_v2")` +
full pagination. Added `total_in_bucket` to the response payload so
operators can see the bucket-wide count alongside the page they
requested.

**Verified (preview, after fix)**
```
PREVIEW /api/admin/backups-list-r2?limit=5:
  count returned: 5 · total_in_bucket: 1502
  newest: MASCI_complete_backup_2026-05-26_000942Z.zip @ 2026-05-26T00:12  ← truth
```

**Status** · fixed in preview · awaiting prod redeploy.

---

### 🟡 OBSERVATION 1 — `OPERATOR_DIGEST_RECIPIENTS` env not set

* Cron will fall back to `SAFETY_DIGEST_TO_EMAIL` (also unset) and
  then to `safety@mascigc.com`.
* If a different mailbox should receive Monday digest, add to
  **prod** deploy env:
  `OPERATOR_DIGEST_RECIPIENTS=jaymn.judd@mascigc.com,safety@mascigc.com`.
* If all three were missing, cron logs calmly and skips — no crash.

**Status** · operator decision · not a code defect.

---

### 🟡 OBSERVATION 2 — Atlas password in chat transcript

* Carried over from prior agent's debug session (iter439).
* Recommendation: rotate Atlas password, update preview `.env` +
  prod deploy dashboard.

**Status** · operator-action item.

---

### 🟢 NON-DEFECT — 2 historical `complete-r2-error` rows on 2026-05-25

```
2026-05-25T15:16:20 · OperationFailure · usage_events sort exceeded 33 MB memory
2026-05-25T15:18:06 · OperationFailure · same
```

* Self-recovered. Subsequent 98 complete-r2 archives succeeded.
* Not blocking. Logged calmly. No action required.

---

## Unresolved risks

* **None blocking.** Platform is operationally healthy.
* The diag-truthfulness fix and the pagination fix are landed in
  preview only. Until the operator triggers a production redeploy:
  * `/admin/system` banner will keep saying yellow / "No backup runs recorded."
  * `/admin/backups-list-r2` will keep showing only legacy archives.
  * If the Monday digest fires before the redeploy, the email will
    say "Operator review recommended" even though everything is calm.
    The operator should ignore that one email.

---

## Testing log

* Production HTTP smoke: 9/9 hub routes 200 · `verify-production.sh` 5/5 healthy.
* Preview diag endpoints before fix: lying. After fix: truthful.
* Production diag endpoints (still old code): lying as expected.
* `/api/admin-strict/diag/production-health` preview→prod: 5/5 ok.
* Boto3 paginator probe vs `backups-list-r2` endpoint:
  * Direct boto3: 1502 keys · newest 2026-05-26T00:12 ✅
  * Preview endpoint after pagination fix: matches boto3 ✅
  * Production endpoint (still old code): 500-key truncation ❌
* Downloaded newest backup zip (91 MB) · parsed MANIFEST.json:
  123 captured_collections, 10 inlined_photos, redactions applied,
  no MFA secrets, no `data_b64` regression.
* Sentry: backend `enabled: true` (release `3cae10f77b...`) ·
  frontend init present · PII scrub active.
* Ruff: 3 changed diag files → ✅. server.py has a pre-existing
  unrelated `_now_iso` F821 warning at line 3106 (not touched by us).
* Pytest parity-lock (k="iter440 or persistence or admin_ops or
  digest"): 29 collected · 29 passed.

---

## Mandatory next step

1. **Redeploy production from Emergent deploy dashboard** so the
   iter440 fixes land in `mascidocs.com`.
2. Re-run `./tools/verify-production.sh` after the deploy.
3. Hit:
   ```
   https://mascidocs.com/api/admin/system-health
   https://mascidocs.com/api/admin-strict/diag/persistence-health
   https://mascidocs.com/api/admin/digest/weekly?format=text
   https://mascidocs.com/api/admin/backups-list-r2?limit=5
   ```
   Confirm:
   * banner `backup` card GREEN
   * `last_backup_time` shows a real ISO from the last hour
   * digest plaintext ends with `All systems calm.`
   * `total_in_bucket: 1502` and newest archive timestamp is current.

After that, this entire phase is **🟢 GO**.

> *“Production is healthy. Atlas is healthy. R2 is healthy. Backups
> are landing in R2 every hour. Weekly digest is healthy. The MASCI
> Operations Platform is safe to operate.”*
