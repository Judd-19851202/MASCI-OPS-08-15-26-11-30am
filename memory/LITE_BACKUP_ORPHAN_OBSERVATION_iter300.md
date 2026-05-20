# Lite-Backup Orphan Observation · iter300 follow-on

**Date:** 2026-05-20
**Scope:** observation-only per operator direction "DO NOT implement autonomous cleanup yet · inspect age · verify orphan status · understand why May testing generated ~300 files · confirm no retention purpose exists"

## Inventory

| Metric | Value |
| --- | --- |
| Total `MASCI_lite_backup_*.zip` files | 300 |
| Combined size | **20.4 MB** (avg 69.6 KB · range 47.5 KB → 170.4 KB) |
| Date range | 2026-05-11 → 2026-05-20 (10 days) |
| Heaviest days | May 15 (111) · May 13 (61) · May 14 (42) · May 16 (36) |

## Age verification

- Oldest: `MASCI_lite_backup_2026-05-11_095124Z.zip` · 9.4 days ago
- Newest: `MASCI_lite_backup_2026-05-20_170834Z.zip` · 3.4 hours ago

The newest one matches the operational backup schedule (UTC mid-afternoon slot). The platform is still producing lite files as expected.

## Source · why ~300 files in May testing?

The accumulation pattern (heaviest May 13–16) correlates with the **iter182 era** ("backup email storm fix"). Test file evidence: `/app/backend/tests/test_iter182_backup_email_storm_fix.py`. The lite backup mode was used heavily during that hardening period because the OOM watermark (`BACKUP_FULL_OOM_WATERMARK_MB`) auto-downgrades full backups to lite when the latest full archive crosses ~600 MB. That auto-downgrade fired repeatedly during the regression cycle.

The auto-downgrade is **working as designed** — lite-mode is the OOM escape hatch. The accumulation is a symptom of the hatch firing, not a malfunction.

## Retention purpose

**Confirmed: lite backups DO have an operational purpose** beyond their immediate write.

`server.py:6825-6836` (inside `_backup_watchdog_check`'s on-disk-staleness fallback):
> *"...the staleness check returned None → ...files.extend(BACKUPS_DIR.glob('MASCI_lite_backup_*.zip'))"*

When the watchdog tries to verify "is the backup pipeline alive?" and finds no full-backup rows in `backup_health`, it falls back to checking the **newest lite backup on disk** as a liveness signal. This prevents false-alarm emails when the system is intentionally running lite-only.

**But only the NEWEST 1–2 lite files are actually consulted.** The other 298 serve no operational purpose.

## Disk-pressure contribution

The lite cluster contributes **20.4 MB of 2,290 MB total backup footprint = 0.9%**. The real disk pressure (currently 88%) is dominated by:

| File class | Count | Approx. size |
| ---: | ---: | ---: |
| `MASCI_full_backup_*.zip` | 2 | ~1.5 GB |
| `MASCI_complete_backup_*.zip` | 2 | ~300 MB |
| `MASCI_lite_backup_*.zip` | 300 | ~20 MB |
| **Total backups** | 304 | ~1.82 GB |

The platform's existing `BACKUP_KEEP_MAX=3` prune logic correctly maintains the full-backup cap at 2-3 newest. The disk-pressure question is whether 3 × 750 MB full backups is the right ceiling for a 9.8 GB container — that's an operator policy decision, NOT a lite-cleanup decision.

## Recommended posture (DEFERRED to operator)

The lite cluster is **operationally inert and small**. Three viable postures, all defensible:

| Option | Description | Trade-off |
| --- | --- | --- |
| **a** | Leave as-is | Costs 20 MB. Easiest. Watchdog fallback uses the newest one transparently. |
| **b** | One-shot manual cleanup (`find . -name 'MASCI_lite_backup_*.zip' -mtime +1 -delete`) | Frees 20 MB. Preserves only the freshest lite for watchdog fallback. NOT autonomous. |
| **c** | Add a lite-cap (e.g., `BACKUP_LITE_KEEP_MAX=5`) inside `_emergency_prune_backups()` | Permanent fix. Tiny code addition. Requires operator approval since iter299 was explicitly visibility-only. |

The audit explicitly DOES NOT recommend autonomous execution of any of these. The operator's direction was "observation first, cleanup later if justified" — these are the inputs for that decision.

## What this observation does NOT propose

- 🚫 Autonomous deletion of any file.
- 🚫 New env var without operator approval.
- 🚫 Changing `_emergency_prune_backups` behavior.
- 🚫 Raising `BACKUP_KEEP_MAX` for full backups (that's a different conversation about RTO/RPO).
- 🚫 Removing the lite-backup-fallback liveness check in `_backup_watchdog_check`.

## Linked artifacts

- iter299 visibility log line that surfaced this: `[ops-hygiene] startup · disk=88% · backups: total=304 (2290.5 MB) · full=2 lite=300 complete=2 · ...`
- The lite-backup auto-downgrade itself: `server.py:5585-5608` (DEFENSE LAYER 4.5 — OOM watermark preflight).
- Watchdog fallback that gives lite backups their purpose: `server.py:6825-6836`.
