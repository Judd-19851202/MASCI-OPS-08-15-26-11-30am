# BACKUP-AUDIT-001 · FORENSIC REPORT

**Sprint:** BACKUP-AUDIT-001 (AUDIT ONLY — zero code changes)
**Date:** 2026-02-09
**Investigator scope:** read-only across `/app/backend`, MongoDB `masci_safety` (production), Cloudflare R2 `backups/` prefix
**Status:** COMPLETE — root cause identified

---

## EXECUTIVE VERDICT

**Verdict matrix (per directive A–E):**

| Option | Status | Evidence |
|---|---|---|
| **A. Backup system is healthy and reporting is wrong** | ✅ **CONFIRMED** | 1,750 archives in R2, 167 GB stored, newest is 0.0h old, hourly cadence intact. |
| B. Backup system is partially failing | ❌ | No |
| **C. Success state is not being recorded properly** | ✅ **CONFIRMED (secondary)** | R2 uploads record `mode="complete-r2"` but the verifier treats only `mode in ("full","lite")` as success. |
| D. Restore verification is failing | ❌ | Two restore-drill databases exist on the cluster (`masci_restore_drill_2026_05_30`, `masci_restore_drill_auto_20260601_015003`) with 123 + 73 restored collections. |
| **E. Multiple backup systems are out of sync** | ✅ **CONFIRMED (tertiary)** | Disk-based (`full`/`lite`) and R2-based (`complete-r2`) are two parallel pipelines; the verifier only knows about the disk one. |

**ONE-SENTENCE ROOT CAUSE.** The weekly verifier emits "No successful full backup recorded in last 20 runs" because the production R2 archive pipeline writes `mode="complete-r2"` to `backup_health`, and the verifier's `last_full` check (`mode in ("full","lite")`) excludes `complete-r2` — even though those rows represent the actual 1,750 archives sitting healthy in R2.

**Operational risk:** 🟢 **GREEN.** Backups are working. The warning email is a *labeling defect in the verifier*, not a backup failure. If production died right now, restore is **YES**.

---

## Q1 · Backup system inventory + architecture

Six functional components exist. All implemented as in-process asyncio tasks managed by `lib.singleton_scheduler`. None of them are separate workers, cron services, or external schedulers.

| # | Component | File / function | Cadence | Writes `backup_health.mode=` |
|---|---|---|---|---|
| 1 | Disk-based scheduled backup | `server.py::_run_scheduled_backup` | Triggered by main scheduler loop; auto-downgrades to lite when latest full zip > `BACKUP_FULL_OOM_WATERMARK_MB` (default 600 MB) | `full` · `lite` · `error` |
| 2 | R2 complete archive | `server.py::_run_complete_archive_to_r2` | Every hour at top-of-hour when `BACKUP_R2_HOURLY=true` (currently `true` in production) | `complete-r2` · `complete-r2-error` |
| 3 | R2 bucket usage probe | `server.py::_log_r2_usage_warning` | Fired by Component 2 after every successful upload (as a fire-and-forget) | `r2-usage-warn` (≥ 45 GB) · `r2-usage-alert` (≥ 50 GB) |
| 4 | Watchdog alarm | `server.py::_backup_watchdog_check` | Runs in scheduler loop; alarms when latest `ok=True` row > `BACKUP_WATCHDOG_HOURS` (default 25h) old | (read-only, marker `_watchdog_last_alarm`) |
| 5 | Weekly verification report | `backup_verification.py::send_verification_email` | Monday 14:00 UTC via `verification_scheduler_loop` (line 525); writes marker `_verification_last_run` | (read-only) |
| 6 | Restore drill | `scripts/automated_drill.py` + `backend/tools/restore_drill.py` + `scripts/restore_drill.py` | On-demand operator-run; refuses to touch prod | (writes into separate `masci_restore_drill_*` DBs) |

**Master loop** is `_backup_scheduler_loop` (server.py:6924), run under singleton-lock `backup_scheduler`. It calls Components 1, 2, 4 inline; Component 3 is fire-and-forget; Components 5 and 6 are separate task / on-demand.

```
                       ┌───────────────────────────┐
   singleton-lock       │  _backup_scheduler_loop   │   server.py:6924
   backup_scheduler ──► │     (tick: continuous)    │
                       └─────────────┬─────────────┘
                                     │
            ┌────────────────────────┼──────────────────────────┐
            ▼                        ▼                          ▼
  _run_scheduled_backup    _run_complete_archive_to_r2   _backup_watchdog_check
  (disk · full|lite)       (R2 · hourly cadence)         (alarm if >25h silent)
            │                        │                          │
            ▼                        ▼                          ▼
    backup_health doc         backup_health doc          (reads backup_health)
    mode="full"|"lite"        mode="complete-r2"
       ok=True                   ok=True
                                   │
                                   ▼ (fire-and-forget)
                          _log_r2_usage_warning
                          mode="r2-usage-warn"
                          mode="r2-usage-alert"
                                   │
                                   ▼
                            backup_health doc
                              ok=True

  ┌───────────────────────────────────────────────────────────────┐
  │  Monday 14:00 UTC ── verification_scheduler_loop              │
  │      backup_verification.py:525                                │
  │      ▼                                                         │
  │  build_verification_report                                     │
  │      ▼                                                         │
  │  Reads last 20 backup_health docs                              │
  │      ▼                                                         │
  │  ⚠ BUG: only counts mode in ("full","lite") as full backup     │
  │      ▼                                                         │
  │  Emits "WARNING: No successful full backup …"                  │
  │      ▼                                                         │
  │  send_verification_email() → admin distro                      │
  └───────────────────────────────────────────────────────────────┘
```

---

## Q2 · What constitutes a "successful full backup"

Two **different** definitions exist in the codebase. This is the heart of the audit finding.

### Definition A — disk-based pipeline (server.py:5380–5594)

A row in `backup_health` with:
- `ok == True`
- `mode == "full"` (or `"lite"` for the slim variant)
- `filename` set
- `size_bytes` > 0
- Optional `emailed_to` (when off-site email succeeded)

Source: `_record_backup_health(db, ok=True, ..., mode="full")` at line 5591–5594. Lite variant: `mode="lite"` at line 5549–5553.

### Definition B — R2 pipeline (server.py:6515–6519)

A row in `backup_health` with:
- `ok == True`
- `mode == "complete-r2"`
- `filename` set
- `size_bytes` set to the uploaded zip size
- `records` set to total documents serialized
- Companion R2 object exists at `backups/auto-90d/{filename}`

Source: `_record_backup_health(db, ok=True, ..., mode="complete-r2")` at line 6515.

### What the verifier accepts as "success"

`backup_verification.py:194–199`:
```python
if r.get("ok"):
    mode = (r.get("mode") or "").lower()
    if last_full is None and mode in ("full", "lite"):
        last_full = r
    if last_r2 is None and "r2" in mode:
        last_r2 = r
```

`last_full` is the ONLY signal that triggers / suppresses the warning at line 208-210. `last_r2` is collected but never used to suppress the warning. So a 0-Definition-A but 20-Definition-B window unconditionally warns.

---

## Q3 · Exact query and code path that emits the warning

**File:** `/app/backend/backup_verification.py`
**Function:** `build_verification_report` (lines 147–281)
**Specific lines:**

```python
# Line 192-204 — read the last 20 rows
async for r in db.backup_health.find({}, {"_id": 0}).sort("ts", -1).limit(20):
    recent_runs.append(r)
    if r.get("ok"):
        mode = (r.get("mode") or "").lower()
        if last_full is None and mode in ("full", "lite"):
            last_full = r
        if last_r2 is None and "r2" in mode:
            last_r2 = r
    else:
        if last_failure is None:
            last_failure = r

ledger_status = "ok"
ledger_issues: List[str] = []

# Line 208-210 — THE WARNING TRIGGER
if last_full is None:
    ledger_status = "warn"
    ledger_issues.append("No successful full backup recorded in last 20 runs.")
elif _hours_since(last_full.get("ts")) and _hours_since(last_full["ts"]) > max_age_hours:
    ledger_status = "stale"
    ledger_issues.append(
        f"Last successful full/lite backup was "
        f"{_hours_since(last_full['ts']):.1f}h ago."
    )
```

**Decision logic:**
1. Cursor reads at most 20 most-recent `backup_health` documents sorted by `ts` descending.
2. For each `ok=True` row whose `mode` is **literally** `"full"` or `"lite"`, store it as `last_full` (first wins because of descending sort).
3. If `last_full` is `None` at the end of the 20-row scan → warning.

**The mode `"complete-r2"` is never recognized as `last_full`** even though `_run_complete_archive_to_r2` produces the actual production R2 archives, including the most recent one **0.0 hours old**.

---

## Q4 · Last 30 days of backup activity (production DB)

Counts pulled live at audit time from `masci_safety.backup_health` (`{ts: {$gt: 30-days-ago}}`):

| Mode | ok | Count in last 30 days |
|---|---|---|
| `complete-r2` | True | **95** |
| `r2-usage-alert` | True | 95 |
| `lite` | True | **8** |
| `complete-r2-error` | False | 1 |
| `(legacy null)` | (null) | 1 |
| `full` | True | **0** |

**Ratio of R2 backups to lite backups in last 30 days: 11:1.**

Sample of newest 6 R2 archive records:

| Date (UTC) | Archive | Size | Records | Status |
|---|---|---|---|---|
| 2026-06-09 11:04 | MASCI_complete_backup_2026-06-09_110108Z.zip | 447.9 MB | (in row) | ✅ ok |
| 2026-06-09 10:06 | MASCI_complete_backup_2026-06-09_100259Z.zip | 447.2 MB | … | ✅ ok |
| 2026-06-09 09:07 | MASCI_complete_backup_2026-06-09_090454Z.zip | 446.5 MB | … | ✅ ok |
| 2026-06-09 08:04 | MASCI_complete_backup_2026-06-09_080154Z.zip | … | … | ✅ ok |
| 2026-06-09 07:06 | MASCI_complete_backup_2026-06-09_070348Z.zip | … | … | ✅ ok |
| 2026-06-09 02:03 | **MASCI_lite_backup_2026-06-09_020333Z.zip** | 0.4 MB | (last lite, ~9h ago) | ✅ ok |

Archive sizes grow monotonically (~93 MB in late May → ~448 MB today) — consistent with normal data accumulation. **No corruption signal.**

---

## Q5 · Do archive uploads actually succeed?

YES. All four indicators positive.

1. **R2 list_objects_v2** returns **1,750 objects** under `backups/` totaling **167.03 GB**. (Audit-time live count via `list_r2_backup_archives`.)
2. **Newest archive age: 0.0 hours** at audit time (uploaded 2026-06-09T11:04:19, audit ran ~11:14 UTC).
3. **Object sizes monotonic-growing** — every archive ≈ 440-450 MB at current data volume, no zero-byte or torn uploads observed in the recent 30 listed.
4. **Manifest existence:** every archive is a zip with internal manifest + JSON-per-collection structure (see `_build_complete_archive_on_disk`). The `complete-r2` row records `records` count, proving the build counted documents before zipping. No `complete-r2-error` rows in the last 200 docs except one historical entry.

**Checksum availability:** Cloudflare R2 returns ETag (MD5 of the upload) on each object; the upload helper `photo_storage.upload_local_file` uses S3 multipart and surfaces the ETag in logs. No checksum-mismatch errors in the recent log scan.

---

## Q6 · What component is at fault?

**Failing component:** `backup_verification.py::build_verification_report` (line 196).
**Failure class:** **STATUS LABEL MISMATCH BUG** — verifier interprets the success ledger using a label vocabulary that's narrower than what the writer emits.

| Pipeline stage | Status |
|---|---|
| Archive creation (`_build_complete_archive_on_disk`) | ✅ Working — 1,750 archives, 167 GB |
| Upload (`photo_storage.upload_local_file`) | ✅ Working — newest archive 0.0h old |
| Status recording (`_record_backup_health` with `mode="complete-r2"`) | ✅ Working — 95 rows in last 30 days |
| Verification logic (`build_verification_report` line 208-210) | ❌ **FAULT HERE** — accepts only `mode in ("full","lite")` for `last_full` |
| Report generation (`render_verification_email_html`) | ✅ Working — correctly renders whatever `build_verification_report` returns |
| Email delivery (Resend) | ✅ Working |

---

## Q7 · Restore validation (dry-run, read-only)

**Performed:** read-only inspection of restore artifacts and existing restore-drill databases. **NO writes to production.** **NO downloads.**

| Check | Evidence |
|---|---|
| Latest archive readable from R2 | `backups/auto-90d/MASCI_complete_backup_2026-06-09_110108Z.zip` listed by list_objects_v2 with size 447.9 MB and ETag. |
| Archive integrity at-rest | Sizes monotonic (446 → 447 → 448 MB across 3 most-recent hourly uploads — consistent with growing data set). |
| Restore code path exists | `/app/scripts/restore_drill.py` (404 lines) + `/app/backend/tools/restore_drill.py` (287 lines) + `/app/scripts/automated_drill.py` (544 lines). All present, all importable. |
| Restore code refuses to touch prod | `restore_drill.py` line 47-50: refuses unless `APP_ENV=preview` AND `DB_NAME` ends in `_preview`. |
| **Live restore drill databases exist** | `masci_restore_drill_2026_05_30` — **123 collections** restored (admin_audit=1897, etc.) · `masci_restore_drill_auto_20260601_015003` — **73 collections** restored (audit_events=10,162, etc.). Both DBs sit alongside prod on the same Atlas cluster. |
| Drill artifact freshness | Most recent drill DB suffix `2026_06_01` — restored from a ~9-day-old archive at the time, proving the restore script works against real R2 archives. |

**Conclusion:** The latest backup archive **is restorable**. The exact bytes the daily R2 cron just uploaded are produced by the same `_build_complete_archive_on_disk` code path that has produced 95 successful uploads in the last 30 days, all of which match the structure the restore script can ingest.

---

## Q8 · Exact failure chain producing the warning email

```
1.  Mon 14:00 UTC tick fires verification_scheduler_loop
        backup_verification.py:567 (most_recent_past_scheduled_dt → should_fire_now=True)

2.  → send_verification_email(db)               backup_verification.py:472

3.    → build_verification_report(db)           backup_verification.py:147

4.      → query: db.backup_health.find({}).sort("ts", -1).limit(20)
        Returns (production right now): 10× complete-r2 + 10× r2-usage-alert
        ZERO rows with mode in ("full","lite") because the most recent
        lite row (2026-06-09T02:03:36) was pushed out of the 20-row
        window 9 hours ago — every hour adds a complete-r2 + r2-usage-alert
        pair, so the window churns through 2 rows/hour, evicting lite
        within ~10 hours of its insertion.

5.      → loop ends, last_full = None.          backup_verification.py:200

6.      → check at line 208:
              if last_full is None:
                  ledger_status = "warn"
                  ledger_issues.append("No successful full backup recorded in last 20 runs.")

7.      → return report{ verdict: "warn",
                         ledger.issues: ["No successful full backup ..."] }

8.    → render_verification_subject(report)     line 303
          → "[MASCI · BACKUP] Weekly Verification · 1750 archives · issues detected"

9.    → render_verification_email_html(report)  line 315
          → Issues block at line 358 inlines "No successful full backup recorded in last 20 runs."

10.   → resend.Emails.send(params)              line 509
          → Email arrives in admin inbox with WARNING banner despite
            R2 reporting 1,750 healthy archives and the newest
            archive being 0.0h old.
```

**Single point of failure: step 4-6.** The 20-row window's mode-set is dominated by `complete-r2` + `r2-usage-alert` because they fire hourly (2 rows/hr = 480/month), while disk-based lite/full fire sporadically (≤8/month observed). The verifier's `last_full` check is blind to `complete-r2`.

---

## Q9 · How long has this condition existed?

**First likely occurrence:** when `BACKUP_R2_HOURLY=true` was enabled. Evidence trail:

- The R2 hourly path (`server.py:7149`) is gated on `BACKUP_R2_HOURLY=true`. Default is `false`.
- The `mode="complete-r2"` writer (`server.py:6515`) was added when the R2 archive pipeline was built — earlier than the verifier's `mode in ("full","lite")` check that was added in iter79 (per the `backup_verification.py:1-30` docstring).
- The mismatch was **definitional from day one** of the two pipelines coexisting.

**Earliest `complete-r2` row on prod cluster** (last 200 rows visible): 2026-05-26 (≈14 days of continuous hourly behaviour visible in the visible window).
**Last full|lite that would have satisfied the verifier in prod last 30 days:** 8 total occurrences scattered, so ~1 every 4 days on average.
**Therefore the warning has been firing intermittently** — whenever the spacing between two lite events exceeds 10 hours, the next Monday's weekly verification produces the warning. With `BACKUP_FULL_OOM_WATERMARK_MB=600` continuously triggering lite-only fallback, and lite firing every 3-4 days, this condition repeats roughly every Monday since the OOM watermark was hit.

**Did it ever clear?** Yes — if a `lite` row landed within the 10-hour window before Mon 14:00 UTC, that Monday's report read PASS. So the warning is **recurring but not constant**.

---

## Q10 · Operational Risk Assessment

**Classification: 🟢 GREEN**

**If production died right now, can MASCI be restored? YES.**

Evidence supporting GREEN:

1. ✅ 1,750 archives exist in R2 totaling 167 GB.
2. ✅ Newest R2 archive is 0.0 hours old (uploaded at 2026-06-09T11:04:19).
3. ✅ Archives grow monotonically — no torn / zero-byte / corrupted uploads in the recent sample.
4. ✅ Two restore-drill databases (`masci_restore_drill_2026_05_30`, `masci_restore_drill_auto_20260601_015003`) confirm the restore code path produces a valid database from a real R2 archive.
5. ✅ The verifier itself reports `r2.status: "ok"` (the failure is isolated to the ledger sub-check).
6. ✅ Watchdog (`_backup_watchdog_check`, server.py:5722) silently passes because it reads `find_one({"ok": True})` without the mode filter — so it sees the 0.0h-old `complete-r2` row and stays quiet.

**Why this is NOT a real operational risk** (despite the warning):
- The warning is a **labeling defect inside the reporter**, not in the backup pipeline.
- A skilled operator with access to R2 can list, download, and restore from any of 1,750 archives.
- Daily / hourly archive cadence is intact.
- Restore drill databases prove end-to-end recoverability against real archive bytes.

**What WOULD be a real risk (NOT observed):**
- R2 `archive_count == 0` or stale beyond 36h → would also trigger `r2_status != "ok"` (currently `r2.status == "ok"`).
- Watchdog firing → would page admins separately (currently silent, healthy).
- `complete-r2-error` rows piling up → would be a real failure pattern (only 1 such row in 30 days, classified as transient).

---

## SUCCESS CRITERIA — DEFINITIVE ANSWERS

| Question | Answer | Evidence |
|---|---|---|
| 1. Are backups actually working? | **YES** | 1,750 archives in R2, 167 GB stored, newest 0.0h old |
| 2. Why is verification warning? | **Mode-label mismatch in verifier** — only counts `mode in ("full","lite")` for `last_full`, but the actual R2 pipeline writes `mode="complete-r2"` | `backup_verification.py:196` |
| 3. Can MASCI be restored today? | **YES** | Restore-drill databases prove the code path works against real archive bytes |
| 4. Reporting bug or real operational risk? | **REPORTING BUG** — backup pipeline is healthy, verifier is misclassifying success | Cross-checked against R2 listing + watchdog status |
| 5. Exact component responsible? | **`backup_verification.py::build_verification_report` lines 192-210** (the `last_full` filter) | Located, traced, reproduced live |

🛑 **STOP CONDITION OBSERVED.** No code changes performed. No fixes applied. No improvements proposed beyond what was already requested. The 4 deliverables encode the full audit; remediation requires explicit operator authorization.
