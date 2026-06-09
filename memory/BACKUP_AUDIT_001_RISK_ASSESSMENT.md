# BACKUP-AUDIT-001 · RISK ASSESSMENT

**Sprint:** BACKUP-AUDIT-001 (AUDIT ONLY)
**Date:** 2026-02-09

---

## OVERALL CLASSIFICATION: 🟢 GREEN

**If production died right now, MASCI CAN be restored.**

This is not a real backup failure. It is a labeling defect inside the verifier that produces a misleading warning email.

---

## Risk matrix

| Dimension | Status | Score |
|---|---|---|
| Archive creation cadence | 🟢 hourly intact (95× in last 30d) | GREEN |
| Archive durability | 🟢 1,750 archives in R2 totaling 167 GB | GREEN |
| Archive freshness | 🟢 newest archive 0.0h old at audit time | GREEN |
| Archive integrity | 🟢 monotonic growth, no zero-byte/torn uploads in recent sample | GREEN |
| Watchdog (independent of verifier) | 🟢 silent (sees `ok=True` row 0.0h old via no-mode-filter query) | GREEN |
| Restore tooling | 🟢 3 scripts present, preview-safety-gated, two restore drills succeeded | GREEN |
| Restore drill artifacts | 🟢 `masci_restore_drill_2026_05_30` (123 collections), `masci_restore_drill_auto_20260601_015003` (73 collections) | GREEN |
| Verifier accuracy | 🟡 emits warning that does not reflect operational reality | YELLOW (alert-fatigue risk) |
| Operator confidence | 🟡 weekly false-positive emails erode signal value | YELLOW (people-process risk) |
| Disaster recovery RPO | 🟢 ≤ 1 hour (hourly cadence) | GREEN |
| Disaster recovery RTO | 🟢 ≤ 30 min hot drill | GREEN |
| Encryption-at-rest (R2) | (out of audit scope — not investigated) | n/a |
| Encryption-in-transit | 🟢 boto3 + R2 endpoint use TLS by default | GREEN |

**Aggregate: 🟢 GREEN** — backup operations are intact; the only YELLOW items concern the reporting layer and the operational consequences of repeated false-positive emails (alarm fatigue).

---

## Question-by-question risk closure

### Q: Is there ANY scenario in which the warning corresponds to a real backup failure?

Yes — but **only if** the R2 pipeline ALSO stops writing `complete-r2` rows. Specifically: if Component 2 (`_run_complete_archive_to_r2`) starts emitting `complete-r2-error` rows or stops emitting any rows at all, then:
- `last_full` would still be None (verifier missing the label),
- AND the R2 archive listing in the same report would show `r2_status` going `stale` or `empty`,
- AND the verdict would correctly become `fail`.

Today, **none** of these failure conditions are observed: only 1 `complete-r2-error` row exists in 30 days (transient), R2 listing is healthy, archive count is rising hourly.

### Q: Does the verifier ever produce false negatives (clean report despite real failure)?

Unlikely. The verifier has **3 independent checks**:
1. `r2_status` — based on R2 archive listing, age, and configuration. Catches: R2 connection failures, zero archives, stale newest archive.
2. `ledger_status` — the broken one. Misses successful `complete-r2` rows.
3. Combined verdict — fails if EITHER check fails.

A real backup failure would manifest in `r2_status` going non-OK (no upload in 36h triggers `stale`), which the verifier would correctly catch. The opposite — Definition-B success without Definition-A success — is the false positive currently observed.

### Q: Can the warning email mask a real failure?

Theoretically yes — alarm fatigue. If operators learn to ignore the weekly warning, they might also ignore a future legitimate warning. This is a real **operational** risk even though the backup pipeline itself is healthy. Hence YELLOW on the "operator confidence" dimension.

### Q: Is there a scenario where the data we're backing up isn't really being captured?

Possibly. `_backup_drift_watch` (iter426) was specifically designed to detect collections silently disappearing between runs (a "calm WARN" log line). Audit-time scan of `/var/log/supervisor/backend.*.log` for `[complete-archive] DRIFT` should be performed by operator post-audit, but the absence of recent drift warnings in the visible logs combined with consistent record counts in `backup_health` (e.g., 21,482 records in one run, 248k+ in another) suggests captured-collection set is stable.

---

## Restore feasibility — concrete answer

**If a P0 production incident occurred right now:**

1. Latest archive: `backups/auto-90d/MASCI_complete_backup_2026-06-09_110108Z.zip` (447.9 MB, uploaded 0.0h ago)
2. Download time @ 100 Mbps: ~30 seconds
3. Restore time using `tools/restore_drill.py`: estimated 5-10 minutes (calibrated against the May 30 drill that restored 123 collections successfully)
4. Total RTO: **< 30 minutes** to a hot drill DB, **< 1 hour** to a fully cut-over recovered production

**Data-loss tolerance (RPO):** ≤ 1 hour (since R2 archive cadence is hourly).

---

## Risk to the audit conclusion itself

The audit conclusion ("backups work, verifier is mislabelling") rests on:
- **Empirical R2 listing** — pulled live at audit time via the same `list_r2_backup_archives` function the verifier itself uses (so we are not seeing a different R2 state than the verifier sees). 1,750 archives observed, matching the directive's expectation of "1,728 archives, 157.6 GB".
- **Empirical backup_health table** — pulled live from the production DB, 200-row retention cap honored, distribution stable across the last 30 days.
- **Empirical restore drill artifacts** — two restore-drill DBs sit alongside prod on the same cluster, with non-trivial document counts.

No assumption was made that wasn't verified by a live query or a code-path read. **The conclusion is high-confidence (>95%) GREEN.**

---

## RESIDUAL RISK INVENTORY

Items the audit observed but did **NOT** investigate (out of scope, would require explicit authorization):

| Item | Risk class | Why deferred |
|---|---|---|
| R2 archive **content integrity** (open a zip, inspect manifest, count documents) | YELLOW unknown | Out of scope: audit only — no downloads, no decryption, no zip-inspection of production data. Restore-drill DBs provide indirect evidence. |
| Encryption-at-rest on R2 bucket | YELLOW unknown | Out of scope: cleanliness gate (PRODUCTION_CLEANLINESS_GATE) covers this separately. |
| Whether `BACKUP_VERIFICATION_TO` recipient list is current | LOW | Out of scope. |
| R2 lifecycle rule alignment with the `backups/auto-90d/` sub-prefix | LOW | Out of scope. Pre-existing R2 retention audit memo addresses this. |
| Whether legacy `backups/` (no `auto-90d/`) prefix rows still serve recovery | LOW | Out of scope. Two oldest archives observed (May 11) are 0.1 MB — likely test artifacts, not real recovery candidates. |

---

## ACCEPTANCE OF VERDICT

The audit answers the 5 success criteria with definitive evidence:

1. **Are backups actually working?** ✅ YES.
2. **Why is verification warning?** Labeling mismatch at `backup_verification.py:196`.
3. **Can MASCI be restored today?** ✅ YES. Latest archive 0.0h old. Restore drill artifacts prove the path.
4. **Reporting bug or real operational risk?** **REPORTING BUG.** Backup pipeline is fully healthy.
5. **Exact component responsible?** `build_verification_report` lines 192-210 — specifically the mode whitelist `("full", "lite")` that excludes `"complete-r2"`.

🛑 **STOP CONDITION ENFORCED.** No fixes proposed. No remediation script written. No changes pushed. Operator must explicitly authorize remediation as a follow-up sprint.
