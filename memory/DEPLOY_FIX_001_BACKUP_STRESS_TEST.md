# DEPLOY-FIX-001 · Backup Stress Test Report

**Date:** 2026-06-09  
**Methodology:** sandbox `/tmp/backup_stress_sandbox`; `BACKUPS_DIR` patched at runtime; builder function mocked to exercise the three failure modes deterministically.

---

## D1 · Successful Backup

| Step | Action                                                | Result                                               |
|------|--------------------------------------------------------|------------------------------------------------------|
| 1    | Mock `_build_backup_zip_to_path` returns `(17, "ok")` | OK                                                   |
| 2    | Call `exports_full_backup(_=True)`                    | completed                                            |
| 3    | Scan sandbox                                          | **final `.zip` count = 1, `.tmp.<hash>` count = 0**  |

PASS — atomic rename works; no temp file left after success.

---

## D2 · Failed Upload (RuntimeError mid-build)

| Step | Action                                                                          | Result                                                  |
|------|----------------------------------------------------------------------------------|---------------------------------------------------------|
| 1    | Mock `_build_backup_zip_to_path` writes 480 B then raises `RuntimeError`        | mock invoked                                            |
| 2    | Call `exports_full_backup(_=True)` — expects RuntimeError to propagate          | RuntimeError raised ✅                                  |
| 3    | Scan sandbox                                                                    | **final `.zip` count = 0, `.tmp.<hash>` count = 0**     |
| 4    | Log captured                                                                    | `WARNING [backup-cleanup] failure path · removing orphan tmp …` |

PASS — A2 cleanup verified.

---

## D3 · Gateway Timeout (CancelledError)

| Step | Action                                                                          | Result                                                  |
|------|----------------------------------------------------------------------------------|---------------------------------------------------------|
| 1    | Mock builder writes 480 B then raises `asyncio.CancelledError`                  | mock invoked                                            |
| 2    | Call `exports_full_backup(_=True)` — expects CancelledError to propagate        | CancelledError raised ✅                                |
| 3    | Scan sandbox                                                                    | **final `.zip` count = 0, `.tmp.<hash>` count = 0**     |

PASS — A3 cleanup verified (covered by the same `BaseException` arm as A2).

---

## D4 · Startup Recovery

| Step | Action                                                              | Result                                                  |
|------|---------------------------------------------------------------------|---------------------------------------------------------|
| 1    | Create `MASCI_full_backup_old.zip.tmp.deadbeef` aged 700 s          | file present                                            |
| 2    | Create `MASCI_full_backup_active.zip.tmp.cafebabe` aged 60 s        | file present                                            |
| 3    | Run `_emergency_prune_backups("D4-pytest")`                         | pruned = 1                                              |
| 4    | Verify old gone, fresh kept                                         | **old_gone=True · fresh_kept=True**                     |
| 5    | Log captured                                                        | `WARNING [backup-cleanup] orphan-sweep (D4-pytest) · file=MASCI_full_backup_old.zip.tmp.deadbeef age=700s reason=orphan_tmp_over_600s` |

PASS — A4 + A5 verified.

Live evidence from current backend boot:

```
2026-06-09 15:29:50,884 - server - WARNING - [scheduled-backup] disk at 85% on boot — running emergency prune
2026-06-09 15:29:52,386 - server - INFO    - [backup-cleanup] startup-sweep · no orphan tmp files found
```

The new `_deploy_fix_001_backup_orphan_sweep` runs on every backend boot.

---

## D5 · Disk Health

| Step | Action                              | Result                              |
|------|--------------------------------------|-------------------------------------|
| 1    | Call `_disk_pct_used()`             | returned `85` (int, 0 ≤ x ≤ 100)    |
| 2    | Threshold semantics                 | helper available for B1 gate        |

PASS — gate input is correct.

---

## Summary

| Test | Result |
|------|--------|
| D1   | ✅ PASS |
| D2   | ✅ PASS |
| D3   | ✅ PASS |
| D4   | ✅ PASS |
| D5   | ✅ PASS |

**All five backup stress scenarios PASS.** Backup pipeline now safe under:
- normal completion
- upstream errors
- gateway-triggered cancellation
- previously-abandoned orphans on next boot
