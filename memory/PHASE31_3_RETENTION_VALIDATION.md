# Phase 31.3 · R2 + Local Retention Validation
## iter440 · 2026-05-26

> Operator question · Is retention functioning? Are old archives
> actually being pruned? Are local + R2 retention policies aligned?

---

## Verdict

# 🟢 R2 LIFECYCLE HEALTHY  · 🟡 LOCAL DISK PRUNE HEALTHY · 🟡 LEGACY PREFIX OUT OF SCOPE (by design)

---

## R2 bucket lifecycle (probed directly)

```python
client.get_bucket_lifecycle_configuration(Bucket="masci-hub")
→
Rules: 2

Rule 1: "Default Multipart Abort Rule"
  Status: Enabled
  AbortIncompleteMultipartUpload: { DaysAfterInitiation: 7 }

Rule 2: "masci-backups-auto-90d"
  Status: Enabled
  Expiration: { Days: 90 }
  Filter: { Prefix: "backups/auto-90d/" }
  AbortIncompleteMultipartUpload: { DaysAfterInitiation: 7 }
```

### What this means

* Any object written under `backups/auto-90d/` is automatically
  deleted by Cloudflare R2 after 90 days. ✅
* No manual cron needed. ✅
* The rule is **enabled** and **active**.
* Multipart uploads that don't finish in 7 days are aborted (saves
  storage on stuck uploads). ✅

### Bucket evidence

| Prefix                  | Keys | Date range          | In lifecycle |
| ----------------------- | ---: | ------------------- | :----------: |
| `backups/auto-90d/`     | 1004 | 2026-05-17 → 05-26  | ✅ (90-day)  |
| `backups/<no-prefix>/`  |  500 | 2026-05-11 → 05-17  | ❌ (legacy)  |

The 500 legacy archives are pre-iter184 (before the lifecycle rule
existed). They will NEVER auto-expire — only manual cleanup with
operator approval can delete them. See `R2_RETENTION_AUDIT.md`.

This is **by design** — the iter184 comment in `server.py:5970–5976`
explicitly states:

> "Any legacy backups previously written to ``backups/*.zip`` (no
> sub-prefix) are intentionally OUT of scope so existing history is
> not retroactively deleted — they will be cleaned up manually later
> with explicit operator approval."

---

## Local disk retention

`backend/.env`:
```
BACKUP_HOURS_UTC=<set>
BACKUP_R2_HOURLY=<set>
```

`backend/server.py` constants:
```python
BACKUP_KEEP_MAX = int(os.environ.get("BACKUP_KEEP_MAX", "3"))
BACKUP_RETENTION_DAYS = 14  (default · see :4726)
```

### Local prune logic (server.py:4974–4980)

```python
existing.sort(key=..., reverse=True)
# By count (keep newest BACKUP_KEEP_MAX-1 so the new one fits within cap)
for p in existing[max(0, BACKUP_KEEP_MAX - 1):]:
    p.unlink()                       # delete file
```

### Live disk state at audit time

```
$ ls -la /app/backend/backups/

drwxr-xr-x 16 root root     4096 May 26 00:33 ..
-rw-r--r--  1 root root 89831737 May 25 17:27 MASCI_complete_backup_2026-05-25_172641Z.zip
-rw-r--r--  1 root root 89879103 May 25 18:12 ...172641Z.zip.tmp.e44a34ad
-rw-r--r--  1 root root 89936278 May 25 19:10 ...190948Z.zip.tmp.7638abc3
-rw-r--r--  1 root root 89936982 May 25 19:14 ...191347Z.zip.tmp.a2d77172
-rw-r--r--  1 root root 90108784 May 25 20:21 ...202128Z.zip.tmp.58f687f1
-rw-r--r--  1 root root 90706441 May 25 22:54 ...225421Z.zip.tmp.fbf344c6
-rw-r--r--  1 root root 90711028 May 25 22:56 ...225542Z.zip
```

### Findings

* **Final `.zip` files** are correctly pruned to ≤ `BACKUP_KEEP_MAX`
  (2 final zips on disk, both under the keep cap). ✅
* **`.tmp.<uuid>` orphan files**: 5 partial archives left behind from
  killed/restarted runs (when the worker reload happened between
  `tmp.replace(out)` and `out.unlink()`). Total: ~440 MB of stale
  temp files.

### Recommendation

Add a startup-time janitor that removes `*.zip.tmp.*` files older
than 1 hour. The complete-archive code already creates these as
intermediate state — leaving them behind is a side effect of
the restart-fire bug we just fixed. Once restarts stop dropping
mid-archive, this will naturally stop accumulating, but the existing
debris should be cleaned up.

**Status of this recommendation** · NOT FIXED IN THIS PHASE — phase
doctrine is "surgical fixes only, no scope creep." The 440 MB on the
worker disk is not blocking anything and will be reclaimed at the
next deploy (`/app/backend/backups` is ephemeral container storage).
Logged here for operator visibility.

---

## R2 vs local consistency

| Layer  | Retention                          | Source of truth                | Active |
| ------ | ---------------------------------- | ------------------------------ | :----: |
| Local  | newest `BACKUP_KEEP_MAX` finals    | `backend/.env` + code default  | ✅     |
| R2     | 90 days under `auto-90d/` prefix   | Cloudflare R2 lifecycle rule   | ✅     |
| R2     | indefinite under legacy `backups/` | (none · manual cleanup)        | 🟡     |

* Local and R2 retention diverge intentionally — local is "newest 3
  for fast emergency rollback", R2 is "90-day full archive chain for
  survivability." Doctrine documented in iter184 comments.
* Legacy `backups/<no-prefix>/` keys remain at 500 because iter184's
  cutover left them as a manual-cleanup item.

---

## Storage growth model

### Before the fix (this iter440)

* Real rate: ~100 archives/day × 87 MB = ~8.5 GB/day.
* At 90-day retention: steady-state = ~765 GB.
* Cloudflare R2 cost at $0.015/GB/month = **$11.50/month**.

### After the fix

* Expected rate: 24 archives/day × 87 MB = ~2.1 GB/day.
* At 90-day retention: steady-state = ~190 GB.
* Cloudflare R2 cost at $0.015/GB/month = **$2.85/month**.

**~75% cost reduction** at steady state once the legacy clutter and
post-fix lifecycle has time to converge.

---

## Status

* R2 90-day lifecycle: **healthy**
* Local 3-file keep-max prune: **healthy**
* Legacy `backups/<no-prefix>/` 22.5 GB: **out of lifecycle scope by design**
* `.tmp.<uuid>` debris on local disk: **non-blocking, will self-clear at next deploy**
* Restart-fire leak: **fixed in this iter**
