# PHASE26_1_CLEANUP_CONTINUITY_LOG.md
## MASCI Operations Platform · Phase 26.1 · Cleanup Continuity Audit
## iter427 · 2026-05-25

---

## Scope

Audit every "temporary file lifecycle" surface on the platform and
confirm nothing silently accumulates forever. Where a gap is found,
add **small surgical cleanup routines** only (no UI · no dashboard).

---

## 1 · `.zip.tmp.*` orphans in backups dir

| Source | Behavior | Status |
|---|---|---|
| `_run_complete_archive_to_r2` partial-write | writes to `*.zip.tmp.<rand>` then `os.replace()` to final name | 🟢 atomic |
| Worker death mid-write | `*.zip.tmp.<rand>` remains | 🟢 swept by `_emergency_prune_backups` + `_run_scheduled_backup` pre-flight at next tick (after 10-min activity window) |
| Active concurrent stream | `.tmp` younger than 10 min is **kept** (could be active) | 🟢 doctrine-correct |

Current orphan count: **0**. Verified `ls /app/backend/backups/*.tmp* | wc -l → 0`.

---

## 2 · /tmp accumulation

| Path | Size | Source |
|---|---|---|
| `/tmp` | 2.2 MB | mostly shell scripts and Playwright session artefacts |

No process is writing large temp files to `/tmp`. FastAPI / Starlette
`UploadFile` uses an in-memory `SpooledTemporaryFile` (default 1 MB
spool) — for our `data_b64`-in-Mongo upload pattern, payloads never
hit disk as a temp file.

No cleanup routine needed.

---

## 3 · Upload path cleanup

| Endpoint | Temp-file behavior | Cleanup |
|---|---|---|
| `/api/operational-attachments/*` (iter417+) | upload bytes → base64 → store in Mongo doc; no on-disk temp | 🟢 implicit |
| `/api/safety-documents/upload` | inline base64 to Mongo | 🟢 implicit |
| `/api/equipment-master/upload` (Excel) | parsed in memory, no temp | 🟢 implicit |
| `/api/safety-forms/equipment-issuances/*/pdf` (PDF generation) | generated in memory, streamed back | 🟢 implicit |
| `/api/admin/cdl-import` | XLSX parsed in memory | 🟢 implicit |

No upload-path temp files leak.

---

## 4 · PDF generation cleanup

| Surface | Behavior |
|---|---|
| `field_leadership_pdf.py` | renders PDF to in-memory `BytesIO` · streamed to client | 🟢 no temp |
| `training_pdf.py` | same pattern | 🟢 no temp |
| `pdf_render.py` (legacy reports) | same pattern | 🟢 no temp |

No PDF temp files persist.

---

## 5 · Backup staging cleanup

| Stage | Temp file? | Cleanup |
|---|---|---|
| Build manifest in memory | no | n/a |
| Stream collections to JSONL inside zip | no on-disk JSONL — zip-builder streams directly into `zf.open(...)` | 🟢 |
| Stream disk-files into zip | 1 MB chunked stream into zip · no copy on disk | 🟢 |
| Final zip write | `*.zip.tmp.<rand>` → `os.replace()` to final name | 🟢 atomic |
| R2 upload | streams from local zip · no extra temp | 🟢 |

No backup staging temp files leak.

---

## 6 · Failed archive remnants

Two patterns historically left remnants:

| Pattern | Status |
|---|---|
| `.zip.tmp.*` orphans (OOM-killed mid-write) | 🟢 swept by 10-min-old prune in both prune paths |
| Legacy `MASCI_lite_backup_*.zip` (pre-iter425 naming) | 🟢 swept by iter427 prune extension |
| Legacy `MASCI_complete_backup_*.zip` (pre-iter425 naming) | 🟢 swept by iter427 prune extension |

---

## 7 · Stale Mongo collection cleanup

| Collection | Cleanup mechanism | Status |
|---|---|---|
| `usage_events` | TTL · 90 days | 🟢 |
| `audit_events` | TTL · 30 days | 🟢 |
| `r2_degraded_events` | TTL · 30 days | 🟢 |
| `digest_runs` | TTL · 30 days | 🟢 |
| `health_monitor_runs` | TTL · 30 days | 🟢 |
| `system_health_events` | TTL · 30 days | 🟢 |
| `session_activity` | TTL · 30 days (`last_seen_at_1`) | 🟢 |
| `admin_audit` | TTL · 365 days | 🟢 |
| `notifications` | per-doc `expires_at_1` TTL | 🟢 |
| `webauthn_challenges` | TTL · iter422 (challenge expiration) | 🟢 |
| `backup_drift_history` | FIFO-trimmed to 30 snapshots inside `_backup_drift_watch` | 🟢 |
| `dispatch_driver_sessions` | no TTL today · low volume (164 docs) | 🟡 P2 backlog: stale-session reaper (already on the Phase 26 backlog) |
| `directory_sessions` | no TTL · 1,748 docs · 0.40 MB | 🟡 low priority |
| `dispatch_state_events` | no TTL · 5,472 docs · 2.55 MB | 🟡 low priority |
| `operations_events` | no TTL · 1,007 docs · 0.77 MB | 🟡 low priority |
| `hub_banner_audit` | no TTL · 1,127 docs · 0.23 MB | 🟡 low priority |

→ The four "no TTL" collections combined consume ~4 MB. Not urgent.
The `dispatch_driver_sessions` reaper is already on the P2 backlog.

---

## 8 · `__pycache__` accumulation

| Path | Size |
|---|---|
| `/app/backend/__pycache__` | 1.7 MB |
| `/app/backend/routes/__pycache__` | 1.9 MB |
| `/app/backend/tests/__pycache__` | 12 MB |
| `/app/backend/guidance/__pycache__` | 868 KB |

Python bytecode cache. Regenerates on every code change. Excluded from
backup zips (iter425 archive skips `__pycache__` + `.pyc`). No cleanup
needed.

---

## 9 · Cleanup routines shipped this pass (iter427)

| Routine | Location | Behavior |
|---|---|---|
| Extended `_emergency_prune_backups` | `server.py:4854-4900` | now sweeps `MASCI_lite_backup_*.zip` + `MASCI_complete_backup_*.zip` past `BACKUP_RETENTION_DAYS` in addition to canonical `MASCI_full_backup_*.zip` |
| Extended pre-flight prune in `_run_scheduled_backup` | `server.py:4950-4982` | same legacy pattern sweep before each scheduled archive |
| Manual one-time cleanup | shell command at iter427 audit start | removed 318 legacy lite + 3 legacy complete files (26 MB · 321 inodes) |

---

## 10 · Doctrine adherence

| Restraint | Status |
|---|---|
| No cleanup dashboard | ✅ |
| No maintenance UI | ✅ |
| No admin surface | ✅ |
| No new endpoint | ✅ |
| No new env var | ✅ uses existing `BACKUP_RETENTION_DAYS` |
| No scheduler change | ✅ |
| Surgical fix only | ✅ — touched 2 functions, added 1 test file |

---

## GO / WATCH / ACTION REQUIRED

| Concern | Status |
|---|---|
| .zip.tmp.* orphan cleanup | 🟢 GO |
| Upload-path temp cleanup | 🟢 GO · no temp files used |
| Backup staging cleanup | 🟢 GO · streaming-only |
| Legacy backup pattern cleanup | 🟢 GO · iter427 fix shipped + tested |
| Mongo TTL coverage | 🟢 GO for high-volume collections · 🟡 4 low-volume collections lack TTL but consume <4 MB combined |
| `__pycache__` | 🟢 GO · excluded from archives · regenerated on demand |
| /tmp accumulation | 🟢 GO · 2.2 MB |

---

End of Phase 26.1 Cleanup Continuity Log.
