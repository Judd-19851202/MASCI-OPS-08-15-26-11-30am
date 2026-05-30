# AUTOMATED_RESTORE_DRILL_SPEC.md

**Batch:** OMEGA · Operational Perfection Track · Priority 4
**Date:** 2026-05-30 (UTC)
**Mode:** Design specification. **NO implementation in this batch.**
**Goal:** Convert today's manual `scripts/restore_drill.py` invocation (Batch G drill, 283K records, photo rehydration verified) into a recurring, isolated, evidence-producing automated drill that runs without operator presence.

---

## 0 · Why this matters

Today's restorability proof is a snapshot — Batch G ran one drill, generated `BATCH_G_EXECUTIVE_SUMMARY.md` + `PHOTO_REHYDRATION_RECOVERY_REPORT.md`, and stopped. No continuous evidence that **next week's** backup is still restorable. Operational Perfection demands the drill repeat automatically, in isolation, and report results so any regression is caught within one cycle.

**Acceptance criterion:** every authorized drill cycle produces a verifiable artifact (`drill_runs` row + `DRILL_<id>_REPORT.md`) that proves: archive downloadable from R2 · zip integrity passes · Mongo restore round-trips N business records · photo rehydration round-trips M unique R2 keys · cleanup leaves zero residue. Failure of any axis raises an Admin warning surfacing in `RECOVERY_DASHBOARD_SPEC.md`.

---

## 1 · Isolated restore environment

### 1.1 · Database isolation (already supported by `restore_drill.py`)

- Restore target DB **MUST** start with `masci_restore_drill_` (safety rail at `restore_drill.py` lines 30-32).
- Target DB **CANNOT** equal live `DB_NAME` (rail at lines 33-34).
- Lives on the same Atlas cluster (single-instance test) but a distinct database → zero risk of touching live data.

**Naming convention for automated drills:**
```
masci_restore_drill_auto_YYYYMMDD_HHMMSS
```

### 1.2 · R2 isolation

- The drill **only reads** the production archive (immutable in `backups/auto-90d/<key>`).
- `--restore-photos` writes rehydrated photos to a **separate isolated R2 prefix**: `r2://<bucket>/drill-photos/<drill_id>/...`.
- A lifecycle rule (NOT included in this batch's scope but proposed for the future): 7-day auto-expire on `drill-photos/*`. **Operator must authorize separately** before any R2 lifecycle change.

### 1.3 · Compute isolation

- Drill runs in a dedicated subprocess via `asyncio.create_subprocess_exec` from a new lightweight scheduler module — **NOT** in the live API worker process. This prevents drill memory pressure from coupling to live web traffic (the exact failure mode iter441 fixed for backups).
- Subprocess has its own Python interpreter, its own glibc heap, its own PyMongo client. Heap fragmentation cannot leak into the API worker.

---

## 2 · Drill workflow (logical steps)

```
[1] ENQUEUE        →  scheduler row in drill_runs (state="queued")
[2] PROVISION      →  pick latest healthy archive; mint isolated DB name
[3] DOWNLOAD       →  fetch archive from R2 to /tmp/drill_<id>.zip
[4] INTEGRITY      →  zipfile.testzip() · CRC every entry · parse MANIFEST.json
[5] MONGO RESTORE  →  insert_many per kind into masci_restore_drill_auto_<id>
[6] VALIDATE       →  per-collection row count vs MANIFEST · sample JSON parse
[7] PHOTO REHYDRATE → write photos/<key> from archive into drill-photos/<id>/<key> on R2
[8] PHOTO VERIFY   →  every photo:// ref in restored docs resolves to drill-photos/<id>/<key>
[9] REPORT         →  write DRILL_<id>_REPORT.md + drill_runs row update
[10] CLEANUP       →  drop drill DB · delete /tmp/drill_<id>.zip · (R2 photos expire via lifecycle)
[11] NOTIFY        →  if any axis failed, admin notification + recovery-dashboard warning
```

Each step idempotent. Failure at any step writes an error row and stops; subsequent automatic cleanup runs at next cycle.

---

## 3 · Verification workflow (per axis)

Each drill cycle asserts the following invariants. ALL must pass for an `ok=true` drill outcome.

| Axis | Assertion | Source |
|---|---|---|
| **A1 · Archive available** | R2 `head_object(key)` returns 200, `ContentLength > 0` | boto3 |
| **A2 · Archive integrity** | `zipfile.testzip() == None`, manifest parses, `failed_photos == 0` (from manifest) | zipfile stdlib |
| **A3 · Record count parity** | Per-collection count after restore == MANIFEST `per_kind[k]` for every k | restore_drill |
| **A4 · Sample parseability** | 100 random business JSON entries parse via `json.loads`, all return dict | restore_drill |
| **A5 · User directory restored** | `user_directory` count + `users` count both > 0 (auth survives) | restore_drill |
| **A6 · No `_id` leakage** | No restored doc contains a top-level MongoDB `_id` field (was stripped at archive build) | new check |
| **A7 · Photo refs reconcile** | Every `photo://` ref in restored docs ∈ archive `photos/` entries | new check |
| **A8 · Photo rehydration** | Every unique key in archive `photos/` → present in `drill-photos/<id>/` on R2 after `--restore-photos` | restore_drill |
| **A9 · Coverage gap stays zero** | `unique_refs == unique_inlined` (post-iter442; today this would fail by 63) | new check |
| **A10 · Build-vs-restore reconciliation** | `last(backup_health).records == manifest.total_records == sum(per_kind)` | new check |

Failing any axis → drill marked `failed`, error message captured, admin notification fires (using existing `emit_notification(admin)` from `lib/event_fanout.py`).

---

## 4 · Cleanup workflow

| Step | Action | Idempotent? |
|---|---|---|
| C1 | `sync_db[drill_target_db].drop()` (Atlas dropDatabase) | yes (no-op if already dropped) |
| C2 | `os.remove("/tmp/drill_<id>.zip")` | yes (no-op if absent) |
| C3 | (operator-authorized lifecycle) prune `drill-photos/<id>/*` after 7d | yes (lifecycle is idempotent by design) |
| C4 | Mark `drill_runs.cleanup_complete=true` with timestamp | atomic mongo update |

**Failure resilience:** if the drill crashes between steps, the next drill cycle's PROVISION phase first looks for any `drill_runs` row with `state` in `{queued, downloading, restoring, validating}` and age > 2h → runs cleanup before starting fresh.

---

## 5 · Reporting workflow

### 5.1 · Per-drill artifact: `/app/memory/DRILL_<drill_id>_REPORT.md`

Auto-generated markdown with this template (one report per cycle):

```markdown
# DRILL_<drill_id>_REPORT.md
**Cycle:** automatic · <ts>
**Archive tested:** <filename> · <r2_key> · <size_mb> MB · <records> records
**Outcome:** 🟢 PASS / 🔴 FAIL
**Duration:** <minutes> min

## Per-axis evidence
| Axis | Result | Detail |
|---|---|---|
| A1 Archive available | 🟢 | ETag, ContentLength |
| ...                  | ... | ...                |

## Per-collection record-count parity (top 20)
...

## Photo rehydration audit
- unique_refs_in_docs: <N>
- unique_archive_photo_entries: <M>
- unique_drill_r2_uploads: <M>
- delta: 0

## Cleanup
- target_db dropped: ✅ <ts>
- /tmp/drill_<id>.zip removed: ✅
- drill_runs row finalized: ✅

## Notes / anomalies
(empty unless failure)
```

### 5.2 · Aggregate trend

The recovery dashboard (`RECOVERY_DASHBOARD_SPEC.md` §3.3) reads the latest `drill_runs` row to render the "Last restore drill" card. Failures populate the "Warnings" card.

### 5.3 · No-fanout-for-success rule

Successful drills are silent (just a log line + `drill_runs` row + Memory doc). Only failures fan out to Admin notification — this prevents email-storm noise.

---

## 6 · Cadence design (operator decision — NOT chosen here)

The spec is **cadence-agnostic by design** (per OMEGA stop-list: no scheduler / cadence / frequency changes). The implementation entry points support three modes:

| Mode | How invoked | Use case |
|---|---|---|
| **Manual** (today) | `python3 /app/scripts/restore_drill.py --backup K --target-db ... --restore-photos` | What Batch G executed; no change |
| **CLI cron-friendly** | `python3 /app/scripts/automated_drill.py --auto` (idempotent; pulls latest archive automatically) | Operator can schedule externally without touching backend scheduler |
| **Backend-scheduler integrated** (future · requires operator authorization) | Same `singleton_scheduler.py` pattern that backups use, with a NEW lock key `drill_runner` | Only if/when operator lifts cadence-freeze |

**This batch ships ONLY the design.** No cron, no scheduler, no env-var enabled.

---

## 7 · Data persistence: `drill_runs` collection

| Field | Type | Source / write site |
|---|---|---|
| `id` | UUID4 str | generated at enqueue |
| `enqueued_at` | ISO ts | enqueue |
| `started_at` / `finished_at` | ISO ts | step boundaries |
| `archive_filename` | str | from PROVISION |
| `archive_r2_key` | str | from PROVISION |
| `archive_size_bytes` | int | head_object |
| `target_db` | str | mint at PROVISION |
| `state` | enum: `queued`, `downloading`, `restoring`, `validating`, `cleaning`, `done`, `failed` | step transitions |
| `axes` | dict of `{axis: {ok: bool, message: str}}` | per VALIDATE assertion |
| `records_restored` | int | VALIDATE step |
| `photos_rehydrated` | int | PHOTO REHYDRATE step |
| `duration_minutes` | float | finished_at - started_at |
| `outcome` | enum: `ok`, `failed` | terminal |
| `error` | str / null | terminal failure |
| `cleanup_complete` | bool | C4 |

Indexed by `{started_at: -1}` for the dashboard's "last drill" query. TTL not applied (history is small + valuable).

---

## 8 · Drift detection

The automated drill is also a **drift detector** for collection-set changes:

- The archive's `MANIFEST.captured_collections` is compared to the previous drill's value.
- If a collection silently disappears between drills (e.g. an accidental `drop_collection` in code review made it to production), the drill writes an `axis=drift_detected, ok=false` row.
- This is identical in spirit to the existing `_backup_drift_watch` (server.py:5838) but runs against restored data, catching the case where the ARCHIVE has the collection but the LIVE DB silently lost it (the opposite direction).

---

## 9 · Failure modes & recovery

| Failure | Detection | Recovery |
|---|---|---|
| R2 transient 5xx during archive download | A1 retry x3 with backoff | If still fails: mark `failed`, retry next cycle |
| Mongo timeout during restore | A3 records-count mismatch | Mark `failed`; cleanup drops partial DB |
| `--restore-photos` partial (some R2 PUTs fail) | A8 count mismatch | Mark `failed`; admin notif |
| Drill subprocess OOMs (unlikely — independent process) | parent process detects nonzero exit | Mark `failed`; capture stderr in `error` field |
| Two drills overlap | singleton lock on `drill_runner` (mirrors backup_scheduler pattern) | second drill skips |

---

## 10 · Build-effort estimate (for future implementation batch — NOT this batch)

| Component | LOC | Notes |
|---|---:|---|
| `/app/scripts/automated_drill.py` (CLI wrapper around existing restore_drill.py + the 4 new axes A6/A7/A9/A10) | ~250 | reuses 80 % of existing drill code |
| `/app/backend/lib/drill_scheduler.py` (deferred — only if operator lifts cadence freeze) | ~150 | mirror of `singleton_scheduler.py` |
| `drill_runs` collection writes | ~80 | reused from existing health-record pattern |
| Per-drill Memory report writer | ~120 | jinja-style markdown template |
| Dashboard integration (already in `RECOVERY_DASHBOARD_SPEC.md`) | 0 | already specced separately |
| Tests | ~150 | pytest fixture spins up a mini archive |
| **Total (CLI-only path)** | **~600 LOC** | One scoped batch |
| **Total (with scheduler integration)** | **~750 LOC** | Two scoped batches |

---

## 11 · What stays untouched (stop-condition affirmations)

- ⛔ `BACKUP_R2_HOURLY` — untouched
- ⛔ Scheduler cadence — untouched (drill cadence is intentionally deferred to operator decision)
- ⛔ Backup retention — untouched
- ⛔ Backup frequency — untouched
- ⛔ R2 backup lifecycle (`backups/auto-90d/`) — untouched
- ⛔ Notification fan-out (drill failures use the EXISTING `emit_notification(admin)` from `lib/event_fanout.py` — no new event kind, no new email path, no new escalation)
- ⛔ UI / DVIR / accountability / workflows — untouched

---

## 12 · Out of scope (explicit)

- ❌ Cross-region restore (DR to a second Atlas cluster)
- ❌ Schema migration testing as part of drill
- ❌ Performance benchmarking beyond duration capture
- ❌ User-facing drill trigger (Admin clicks "Run Drill Now") — viable later, not specced here
- ❌ Drill-driven RTO/RPO target adjustment — display only

---

## 13 · Stop-condition compliance

- ✅ NO implementation in this batch
- ✅ Design only — every component cites the existing code path it would extend (`scripts/restore_drill.py`, `lib/singleton_scheduler.py`, `lib/event_fanout.py`)
- ✅ Every claim cites code, runtime, or existing-drill evidence (Batch G)
- ✅ No drift / no side quests / no new unrelated features
- ✅ Operator authorization required before any code ships for either §10 path

---

_End of AUTOMATED_RESTORE_DRILL_SPEC.md_
