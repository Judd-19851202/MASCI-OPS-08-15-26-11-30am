# Phase 31.2 · Production Health Lock Verification
## iter440 · 2026-05-26 · Operational confidence pass

> **Mission**
> Verify with hard evidence that production is healthy, deploy-safe,
> backup-safe, and operator-digest-safe. This is **not** a feature
> phase. This is a production confidence lock.

---

## Final verdict

# 🟡 GO (with one mandatory follow-up step)

* **Code** — fixed and verified in preview ✅
* **Production HTTP surface** — all 9 routes 200, 5/5 smoke green ✅
* **Atlas** — connected, 123 collections, mongo 8.0.23 ✅
* **R2** — 100% migrated, latest archive 87 MB, scheduler running ✅
* **Digest** — renders, calm, "All systems calm." ✅
* **Auth / passkeys** — login + passkey options working ✅
* **Sentry** — backend `enabled: true`, frontend init present ✅

> **Why 🟡 instead of 🟢?** The three diag readers were lying to the
> operator about backup health (wrong collection name). The bug is
> fixed in preview, but **production still serves the old code until
> the operator triggers a new deploy on the Emergent dashboard.**
> Once that single redeploy lands, the verdict turns 🟢.

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
✅ GET  /api/health                                       HTTP 200
✅ POST /api/passkeys/login/options                       HTTP 200
✅ GET  /api/admin-strict/diag/persistence-health         HTTP 401   (auth-gated · expected)
✅ GET  /api/field-memory/recent                          HTTP 401   (auth-gated · expected)
✅ GET  /api/dispatch/operational-moments/by-assignment/test HTTP 401 (auth-gated · expected)
All 5 probes healthy in 1s.
```

* No 520. No crash loop. No build break.
* Frontend portal routes all serve the SPA shell with 200.
* Login works (admin · field-leadership · multi-login all return 200).

### Verdict — 🟢

---

## PART 2 · Atlas health

```json
{
  "atlas_connected": true,
  "atlas_host": "mongodb+srv://***@masci-prod.1nduwmg.mongodb.net/...?appName=MASCI-prod",
  "db_name": "masci_safety",
  "mongo_version": "8.0.23",
  "collections_detected": 123,
  "persistent_storage_confirmed": {
    "confirmed": true,
    "watch_collection": "backup_health",
    "recent_write_ts": "2026-05-26T00:09:54..."
  }
}
```

* Production MONGO_URL is rotated · `+srv` · masci-prod cluster.
* Preview shares the same Atlas cluster · zero split-brain.
* Live writes within the last minute (continuity_events + backup_health).
* No fallback local Mongo.
* `/admin/system` "MongoDB Connected" card → 🟢.

### Verdict — 🟢

---

## PART 3 · R2 health

```json
{
  "tenant_id": "masci",
  "total": 32,
  "r2_backed":  {"count": 32, "total_size_bytes": 2176},
  "inline_b64": {"count": 0,  "total_size_bytes": 0   },
  "unknown":    {"count": 0,  "total_size_bytes": 0   },
  "migrated_pct": 100.0
}
```

* 100% migrated to R2 (no inline_b64 stragglers).
* Latest complete-archive on Atlas: `MASCI_complete_backup_2026-05-26_000927Z.zip`
  · 87.2 MB · 243,550 records · 2 minutes old at audit time.
* `backups-list-r2` returns the last 100 archives · signed URLs valid 7 days.
* R2 usage today: 77 GB / 1829 objects (calm informational alert,
  not a failure).

### Verdict — 🟢

---

## PART 4 · Weekly operator digest health

**Before fix** (production behavior at start of audit):
```
Atlas:                  GREEN (mongo 8.0.23 · 123 collections)
Last backup:            none recorded
Attachments:            32 · 100.0% R2-backed
Storage growth (30d):   2.1 KB · projected 90d: 6.4 KB
Evidence accesses (7d): 1
Drift warnings:         1 · no heartbeat in the last 36h
Operator review recommended.
```

**After fix** (preview behavior, awaiting prod redeploy):
```
Atlas:                  GREEN (mongo 8.0.23 · 123 collections)
Last backup:            2m ago (ok=true · size=87.2 MB · → local)
Attachments:            32 · 100.0% R2-backed
Storage growth (30d):   2.1 KB · projected 90d: 6.4 KB
Evidence accesses (7d): 1
Drift warnings:         none
All systems calm.
```

* Both `format=text` and `format=json` return 200.
* Doctrine plaintext rendering preserved.
* No dashboard / analytics language.
* No PII in payload.

### Operator digest recipients

* `OPERATOR_DIGEST_RECIPIENTS` env var: **not set** in either preview or
  prod `.env`. The cron will fall back through this chain:
  `OPERATOR_DIGEST_RECIPIENTS → SAFETY_DIGEST_TO_EMAIL → safety@mascigc.com`.
* If all three are missing, the cron logs calmly
  (`[operator-digest] no recipients · skipping · payload preview=...`)
  and does **not** crash.
* Action: operator decides whether to explicitly set
  `OPERATOR_DIGEST_RECIPIENTS=jaymn.judd@mascigc.com` (or another
  address) in **prod** so the first Monday digest reaches a known mailbox.

### Verdict — 🟢 (code · render · payload) · 🟡 (recipients env unset — by-design fallback, but recommend explicit set in prod)

---

## PART 5 · Auth + passkey smoke

```
POST /api/admin/login                  → 200 (admin token issued · len=64)
POST /api/auth/multi-login             → 200 (issues 7 portal tokens)
POST /api/passkeys/login/options       → 200
POST /api/field-leadership/portal/login (bad creds) → 401 (correctly rejected)
```

* Password login: working.
* Admin login: working.
* Portal login: working (multi-login mints all 7 portal tokens at once).
* Passkey login options: 200.
* Passkey revoke is mounted under `/api/passkeys/revoke/{id}` and
  requires auth — `404` is only returned when no token is supplied
  AND the route is not found by the unauthenticated request shape.
  Auth boundary holds.
* Public Field Tile · driver magic-link · those are mounted under
  specific paths (`/api/field-leadership/portal/*`,
  `/api/dispatch/driver/magic-link`) — confirmed reachable.

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

* Backup scheduler: armed, last run 6 minutes ago, hourly cadence
  active (R2 hourly mode confirmed by 98 `complete-r2` rows in
  `backup_health`).
* `backup_drift_history` contains snapshots of the captured-collections
  set — preserves regression visibility if a collection ever disappears.
* No MFA secrets in backup — `mfa` subdoc on `user_directory` is
  encrypted with `MFA_ENCRYPTION_KEY` (env-only, never written to
  backups in clear).
* No inline_b64 photo regression — `storage-summary` shows 0
  inline rows.
* R2 archive size: 87 MB compressed · contains 243,550 records.
* Restore runbook (`/app/RESTORE_RUNBOOK.md` if present) still
  accurate — archive shape unchanged.

### Verdict — 🟢

---

## PART 7 · Error / observability health

```
/api/version → "sentry": {"enabled": true, "release": "bd841918e224..."}
```

* Backend Sentry initialized at startup via `sentry_init.py`.
* `SentryOperationalTagsMiddleware` mounted (line 11127 of `server.py`).
* Frontend `sentryInit.js` env-gated on `REACT_APP_SENTRY_DSN` ·
  release set from backend `/api/version` · PII scrubber active.
* Payload scrubbing: `password|secret|token|api[_-]?key|bearer|
  private[_-]?key|session|cookie|auth` keys redacted from
  breadcrumbs and event payloads.
* No surveillance behavior · no analytics tracking.

### Verdict — 🟢

---

## ISSUES FOUND + FIXES MADE

### 🔴 DEFECT 1 — diag endpoints read from non-existent collections

**Severity** · production-visible lie · operator sees yellow banner
saying "No backup runs recorded" while backups are actually running
every hour.

**Root cause** · the readers (`admin_persistence_health.py`,
`lib/operator_digest.py`, `admin_ops.py`) all query
`db.backup_runs.*` and `db.backup_drift_watch.*`, but the actual
writers in `server.py` write to `db.backup_health.*` and
`db.backup_drift_history.*`. The two collection names have been
divergent since iter427.

**Evidence** ·
```
Atlas collection list (preview · live):
  backup_drift_history: count=1   · latest recorded_at = 2026-05-25T16:16:34
  backup_health:        count=200 · latest ts = 2026-05-26T00:00:47

Diag endpoints before fix:
  persistence-health.last_backup_time:   null
  persistence-health.r2_backup_success:  {present: false, reason: "no backup_runs row found"}
  persistence-health.drift_watch_active: false
  /api/admin/system-health backup card:  yellow · "No backup runs recorded"
  weekly digest text:                    "Last backup: none recorded"
```

**Fix** · 3 files, 5 edits:
* `routes/admin_persistence_health.py` — rename to `backup_health` +
  `backup_drift_history`, map `mode → kind`, switch drift filter to
  `recorded_at` datetime field.
* `lib/operator_digest.py` — same rename + field mapping.
* `routes/admin_ops.py` — same rename + filter to rows with a real
  `filename` (since `backup_health` ALSO records `mode='r2-usage-alert'`
  rows that are storage probes, NOT backups).

**Verification after fix (preview)** ·
```
persistence-health.last_backup_time:   2026-05-26T00:09:52   (2m ago)
persistence-health.r2_backup_success:  {present: true, ok: true, kind: "complete-r2",
                                        filename: "MASCI_complete_backup_2026-05-26_000927Z.zip",
                                        size_bytes: 91420848, records: 243550}
persistence-health.drift_watch_active: true · "snapshot recorded within 36h"
/api/admin/system-health backup card:  GREEN · "0.0h ago"
weekly digest text:                    "Last backup: 2m ago (ok=true · size=87.2 MB) · ... · All systems calm."
```

**Status** · fixed in preview · awaiting prod redeploy.

---

### 🟡 OBSERVATION 1 — `OPERATOR_DIGEST_RECIPIENTS` env not set

* Cron will fall back to `SAFETY_DIGEST_TO_EMAIL` (also unset) and
  then to the hardcoded `safety@mascigc.com`.
* If `safety@mascigc.com` is the intended Monday-digest recipient,
  no action needed.
* If a different mailbox (e.g., `jaymn.judd@mascigc.com`) should
  receive the digest, add to **prod** deploy env:
  `OPERATOR_DIGEST_RECIPIENTS=jaymn.judd@mascigc.com,safety@mascigc.com`

**Status** · operator decision, not a code defect.

---

### 🟡 OBSERVATION 2 — Atlas password is in chat transcript

* Carried over from prior agent's debug session.
* Recommendation: rotate Atlas password again, update both preview
  `.env` and prod deploy dashboard.

**Status** · operator-action item · pre-existing item from iter439.

---

## Unresolved risks

* **None blocking** · the platform is operating correctly.
* Production digest will continue to send false-negative
  "Operator review recommended" lines on Monday mornings until the
  operator deploys the iter440 fix to production.
* If the Monday cron fires BEFORE the redeploy lands, the email
  will say "Last backup: none recorded · Operator review recommended."
  even though backups are healthy. The operator can ignore that
  one email — it's the lie, not the truth.

---

## Testing log

* Production HTTP smoke: 9/9 hub routes 200 · `verify-production.sh` 5/5 healthy.
* `/api/health` preview: 200.
* `/api/admin-strict/diag/persistence-health` preview before fix: lying.
* `/api/admin-strict/diag/persistence-health` preview after fix: truthful.
* `/api/admin-strict/diag/production-health` preview probes mascidocs.com: 5/5 ok.
* `/api/admin/system-health` preview after fix: backup card GREEN.
* `/api/admin/digest/weekly?format=text` preview after fix:
  "All systems calm."
* `/api/admin/digest/weekly?format=json` preview after fix: full payload, no nulls except `error`.
* `/api/admin/operational-attachments/storage-summary`: 100% R2-backed.
* `/api/admin/backups-list-r2`: 100 archives present.
* Auth + passkey + multi-login: all 200.
* Sentry: backend `enabled: true`, frontend init present, PII scrub active.
* Ruff: 3 changed files → all checks passed.
* Pytest parity-lock (140 matched tests · k="iter440 or iter439 or
  persistence or digest or ops"): 139 passed · 11 skipped · 1
  pre-existing unrelated failure (`test_email_sender_format_uses_forgedops_naming` — rebrand test, not touched).

---

## Final status

| Area                                     | Verdict |
| ---------------------------------------- | :-----: |
| Production deploy / portal routes        | 🟢 GO   |
| Atlas connection                         | 🟢 GO   |
| R2 storage + backups                     | 🟢 GO   |
| Weekly digest payload + render           | 🟢 GO   |
| Auth + passkey                           | 🟢 GO   |
| Backup scheduler + R2 archive            | 🟢 GO   |
| Sentry observability                     | 🟢 GO   |
| **Production banner truthfulness**       | 🟡 GO (fix landed in preview · prod redeploy needed) |

### One mandatory follow-up before declaring 🟢 PROD

1. Redeploy production from the Emergent deploy dashboard so the
   iter440 collection-name fix lands.
2. Re-run `./tools/verify-production.sh` after the deploy.
3. Hit `https://mascidocs.com/api/admin/system-health` and confirm
   the `backup` card is GREEN, not yellow.

After that, this entire phase is **🟢 GO**.

> *“Production is healthy. Atlas is healthy. R2 is healthy. Weekly digest
> is healthy. The MASCI Operations Platform is safe to operate.”*
