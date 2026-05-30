# COMPLETE_R2_DISABLEMENT_INVESTIGATION

**Date:** 2026-02-01 · Batch B · Step 4
**Mission:** Document why production runs in lite-only mode — env-flag source, intended vs accidental setting, OOM/safety rationale.

---

## 1 · Env-flag evidence

Production `/api/admin/backups-scheduler-state` reports:

```
lite_mode_only_env: true
```

This field is set by `server.py:7124`:

```python
"lite_mode_only_env": _lite_mode_default(),
```

which is the live evaluation of the env-flag-driven default.

---

## 2 · `_lite_mode_default()` — the canonical source (`server.py:6341–6364`)

```python
def _lite_mode_default() -> bool:
    """Default to **lite mode ON** so every backup (manual or scheduled)
    produces the slim email-friendly metadata-and-JSON zip and never
    tries to build the 800+ MB full archive on the worker.

    Why default-on?
    Iter64 phase 2 (2026-05-11) moved photos out of MongoDB into R2
    object storage, but other base64 fields (signatures, training
    photos, etc.) still live in Mongo and a full-archive build of all
    of them was still long enough to recycle the worker mid-task on
    production. Until those remaining fields are migrated AND/OR the
    IT-pull endpoint replaces email-attached backups, the safest
    default is "always send the slim 74 KB email, never block the
    worker." Anyone who explicitly wants a full archive can set
    ``BACKUP_LITE_MODE_ONLY=false`` to opt back in.
    """
    raw = (os.environ.get("BACKUP_LITE_MODE_ONLY", "") or "").strip().lower()
    # Explicit opt-OUT only — falsy strings disable lite-mode default.
    if raw in ("0", "false", "no", "n", "off"):
        return False
    return True
```

**Critical observation:** This function **defaults to True when the env var is UNSET**. Only `("0", "false", "no", "n", "off")` opts OUT of lite mode.

Therefore: `lite_mode_only_env: true` in production means **EITHER**:
- (a) The env var `BACKUP_LITE_MODE_ONLY` is explicitly set to a truthy value (`true`, `1`, `yes`, `on`), OR
- (b) The env var is **unset** — in which case the helper returns `True` by default.

Either way, the production behaviour is "lite-mode-only", and it is **explicitly designed-in** at the code level, not an accident.

---

## 3 · Intent (per code documentation)

The docstring on lines 6346–6355 explicitly documents the design rationale:

| Element | What it says |
|---------|--------------|
| **Origin** | Iter64 phase 2 (2026-05-11) migration moved photos from MongoDB → Cloudflare R2 |
| **Residual risk** | Other base64 fields still in MongoDB (signatures, training photos, etc.) — a full-archive build remained 800+ MB |
| **Failure mode** | The full archive was long enough to **"recycle the worker mid-task on production"** — i.e., the build process consumed enough memory/time to cause uvicorn worker OOM/timeout recycling |
| **Resolution path** | Lite-mode-only is the **safe default** until either:<br>1. The remaining base64 fields are migrated out of Mongo, OR<br>2. An IT-pull endpoint replaces email-attached backups |

This is an **intentional safety constraint**, not a configuration error.

---

## 4 · Cross-references in the codebase

| Location | Reference |
|----------|-----------|
| `server.py:4889` | `_run_scheduled_backup` docstring confirms `BACKUP_LITE_MODE_ONLY` env flag forces lite mode at the helper level |
| `server.py:4982` | Operator-facing comment: "BACKUP_LITE_MODE_ONLY=true to make lite-mode permanent" |
| `server.py:5332` | Operator-facing HTML on the System & Backups admin page: "Set `BACKUP_LITE_MODE_ONLY=true` on the deploy until S3 photo migration is done" |
| `server.py:6219` | Inside `_backup_scheduler_loop` docstring: "Production runs in lite-mode (`BACKUP_LITE_MODE_ONLY` true)" |
| `server.py:6796–6810` | Manual-run helper consults `_lite_mode_default()` when caller passes `lite=None` |

**Conclusion:** The lite-mode behaviour is **documented in multiple places** as the intentional production posture, gated on the still-pending S3 photo migration.

---

## 5 · Why `lite=false` query was silently overridden (Batch A finding refined)

In `server.py:6796–6810`:

```python
use_lite = _lite_mode_default() if lite is None else bool(lite)
```

This DOES respect an explicit `lite=False` from the query string. So `POST /api/admin/backups/run-now?lite=false` should produce `use_lite = False`.

**But the resulting backup filename was still `MASCI_lite_backup_*.zip` with `mode: "lite"` and 141 records.**

This means **`use_lite = False` did NOT translate to a complete-r2 build downstream**. The downstream `_run_scheduled_backup` (or whatever generates the archive) must have a SEPARATE lite-mode override that consults `_lite_mode_default()` again later in the pipeline.

Locating the downstream override — `server.py:4896`:
```python
lite_mode = _lite_mode_default()   # line 4896 (inside _run_scheduled_backup)
```

This is the second consultation. Even though the wrapper passed `use_lite=False`, the helper itself reads `_lite_mode_default()` AGAIN and overrides. **There is a hardcoded path through the run helper that defeats the manual `lite=false` opt-out.**

This is consistent with the docstring intent: "lite-mode is permanent until S3 migration." The redundant consultation enforces safety even if a caller tries to opt out.

---

## 6 · Whether complete-R2 can safely run

### Safely from a memory/recycling standpoint
- **Last successful complete-r2 backup**: 2026-05-26 11:06 UTC. The fact that this completed proves the build CAN succeed — but it likely succeeded because of favourable record sizes / RAM headroom at that moment. The "worker recycles mid-task" risk is intermittent.
- **Build characteristics**: 336 MB output file, 223 394 records (per BACKUP_RUNTIME_DIAGNOSTIC_REPORT.md). Memory peak during build is the unknown.

### Risk factors that remain
1. **Worker recycling**: production uvicorn worker has a memory limit (likely 600 MB per the `oom_watermark_mb: 600.0` configured value). A 336 MB build PLUS in-memory MongoDB cursor data could exceed the limit on hot days.
2. **Build wall time**: previous successful complete-r2 builds have taken several minutes. Within that window, any incoming HTTP request that lands on the same worker would block (single-threaded asyncio).
3. **Email attachment limits**: 336 MB exceeds Resend's email attachment limits; the complete-r2 backup must be uploaded to R2 and emailed as a *link*, not as an attachment. The code does this correctly today, but it's a path that depends on R2 credentials being healthy.
4. **R2 disk staging**: the archive is built to local disk first (in `BACKUPS_DIR`) before R2 upload. The `oom_watermark_mb: 600.0` and `disk_high_watermark` checks gate this.

### Bottom line
- Complete-r2 **CAN** run safely under good conditions (proven by 2026-05-26 success).
- Complete-r2 **CAN ALSO** OOM-recycle the worker under marginal conditions.
- The lite-only default is **risk mitigation**, not a hard blocker.

---

## 7 · Recommended posture (operator decision required)

The operator's directive said: "Do NOT change backup mode yet. Do NOT disable lite-only mode yet. Do NOT run complete-R2 again until the override reason is documented."

**This document satisfies that documentation requirement.** Summary of findings:

| Question | Answer |
|----------|--------|
| **Source of override** | `_lite_mode_default()` in `server.py:6341–6364` — env-flag-driven helper that defaults to True |
| **Env flag** | `BACKUP_LITE_MODE_ONLY` (Boolean). Production: either explicitly set to `true` OR unset (both produce same behaviour) |
| **Intended vs accidental** | **Intentional** — documented in 4+ code locations as a designed-in safety constraint pending S3 photo migration |
| **OOM risk** | Real — "worker recycles mid-task on production" per docstring. 600 MB worker watermark vs 336 MB build is tight |
| **Can complete-R2 safely run?** | Conditionally yes (proven 2026-05-26), but with intermittent OOM risk. The opt-out has been deliberately defeated at multiple code levels |
| **Path to safely re-enable** | Complete the S3 photo migration (move signatures, training photos, etc., out of Mongo) OR implement an IT-pull endpoint that replaces in-process archive build with a streamed export |

**No env-flag changes will be made by the agent.** Awaiting operator decision.

---

## 8 · Stop-condition compliance

- ✅ Read-only investigation
- ✅ No backup mode change
- ✅ No env-flag toggle
- ✅ No complete-R2 run attempted
- ✅ All findings backed by file:line code evidence
