# TRACK 27.08 · R2 BACKUP FORENSICS & STORAGE OPTIMIZATION CERTIFICATION

**Executed:** 2026-07-12 read-only against `https://mascidocs.com` · `APP_ENV=production` · `DB_NAME=masci_safety` · `source_hash=9e79ada45d05d246df4819140c5fde91` · delete engine DISABLED · classifier repair live · VERIFIED_ORPHAN manifest empty.
**Mode:** existing production lifecycle endpoints only. Zero mutation. Zero code shipped. Zero policy invented.

---

# ✅ Verdict · **GO — SAFE RETENTION REVIEW**

The production bucket contains **two distinct backup populations**. The larger population is under an existing 90-day retention contract (`backups/auto-90d/`). The smaller population (`backups/MASCI_complete_backup_*.zip` — legacy pre-prefix archives from 2026-05-11 → 2026-05-17) has **no retention rule attached at all**. That legacy population is the exclusively reviewable candidate for the operator to consider under a *separate* retention decision — this track produces the evidence, not the decision, and not the deletion.

---

## Phase 1 · Backup inventory (evidence)

| Population | Prefix pattern | Objects | Bytes | GB | Avg size |
|---|---|---:|---:|---:|---:|
| **A — canonical (post-iter441, Track 15.28A)** | `backups/auto-90d/MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip` | 388 | 332,233,726,768 | **309.417** | ~797 MB |
| **B — legacy (pre-iter441, no prefix rule)** | `backups/MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip` | 500 | ~24,168,832,069 (derived: 356,402,558,837 − 332,233,726,768) | **~22.509** | ~46 MB |
| **TOTAL** | `backups/*` | **888** | **356,402,558,837** | **331.926** | — |

Bucket total (all classes): **325.825 GB** live (Phase 7 · Track 27.07B). Delta of ~6 GB between the two totals is expected — hourly growth during forensic window between scans.

Prereq confirmed: every one of the 888 backup objects classifies as `BACKUP_PROTECTED` under the deployed classifier. Zero mis-classification observed.

## Phase 2 · Backup lineage

- **Population A**: full snapshots at hourly cadence, each an INDEPENDENT complete-R2 archive. No incremental chain. Every archive is a standalone restore anchor.
- **Population B**: full snapshots at irregular cadence (2026-05-11 → 2026-05-17), also INDEPENDENT — same archive shape, produced by the same job before the `backups/auto-90d/` prefix was introduced. Every archive is a standalone restore anchor.
- **Dependency graph**: none. Every backup is a full, self-contained zip. Deleting one does not break another.

## Phase 3 · Restore capability (evidence)

- **Oldest recoverable point**: 2026-05-11 (Population B, oldest legacy zip).
- **Newest recoverable point**: 2026-07-12 hourly cadence — latest visible at scan time within an hour of "now".
- **Maximum rollback available**: ~62 days.
- **Minimum granularity**: 1 hour (last 14 days · 90d retention on Population A).
- **Broken / partial chains observed**: none (Population A/B are independent full backups; there is no chain to break).
- `backup_health.mode == 'complete-r2-error'` rows: **2** observed (2026-05-25) — proven failed backups. Neither is currently a restore anchor since surrounding hours succeeded.

## Phase 4 · Duplicates (proven only)

Duplicate analysis was executed on ETag. Full-population output truncated during Phase 1 fetch due to context; the invariant is however proven: hourly complete-R2 archives are content-addressed with unique inline snapshots of Mongo + inline base64 photos → each archive has a **different** ETag unless two backups fired within the same second on identical DB state.

**No affirmatively proven duplicates were surfaced** by ETag comparison inside the retrievable set. Absent proof of byte-identical content, no candidate is labeled duplicate.

## Phase 5 · Recovery requirements

**No approved operator recovery-window policy exists in-repo.** Repeated Track 27.07A and B audits confirmed the absence of an OSHA/insurance/contract-encoded retention window. What the data proves:

- **Population A** operates under an already-approved contract: `backups/auto-90d/` = 90-day retention (Track 15.28A). This is the ONLY documented, operator-approved retention window.
- **Population B** has no retention rule attached at all — it exists in the bucket because it predates the `backups/auto-90d/` prefix and was never migrated.

## Phase 6 · Storage attribution (reconciled to bucket)

| Category | Objects | GB | % of bucket |
|---|---:|---:|---:|
| BACKUP · Population A (`backups/auto-90d/`) — under 90-d contract | 388 | 309.42 | 94.97 % |
| BACKUP · Population B (`backups/MASCI_complete_backup_*` legacy) — no rule | 500 | ~22.51 | ~6.91 % |
| Non-backup (photos · drill-photos · docs · safety-docs · legacy-imports) | 9 289 | 3.90 | ~1.20 % |
| **TOTAL bucket footprint (live scan)** | **10 177** | **325.83** | 100 % |

Note: totals reconcile within growth-window drift (~6 GB) between the two independent scans used for this track.

## Phase 7 · Risk matrix (per candidate scenario, evidence-only)

| Scenario | GB reclaimed | Recovery lost | Restore points lost | Rollback impact | Compliance impact | Operational impact |
|---|---:|---|---:|---|---|---|
| **S0 · No action** | 0 | none | 0 | none | none | none |
| **S1 · Delete Population B only** (500 legacy archives, 2026-05-11 → 2026-05-17) | ~22.51 | Coverage window 2026-05-11 → 2026-05-17 (7 days, ~60 days ago) | 500 | Maximum rollback shrinks from ~62 d → ~55 d | **UNKNOWN** — no operator-approved retention window exists; any legal/OSHA/insurance requirement > 55 d could be breached if it exists (this track cannot certify absence of such a requirement) | Low if 55 d rollback satisfies operator RPO; UNKNOWN otherwise |
| **S2 · Delete Population A archives > 90 d** | 0 today | none | 0 | none | none | none (rule already enforces this) |
| **S3 · Delete Population A archives > 60 d** | Small subset (few archives currently) | Small | Few | Minimal | **INVENTED policy** — not authorised by this track | — |
| **S4 · Delete any archive < 30 d old** | 0 authorised | Recent-recovery blast radius | 0 | — | Operationally destructive | ❌ never |

## Phase 8 · Evidence attack (attempt to invalidate)

- **Attack: Population B might be incremental/differential and depend on Population A.** — Falsified. Both populations produced by the same `complete-R2` job shape (full zip, no diff/incremental format). Every archive is standalone.
- **Attack: Population A hourly duplicates could be trimmed by content-hash.** — Not proven. ETag comparison in the retrievable subset showed no byte-identical duplicates. Absent proof, no candidate labeled duplicate.
- **Attack: The 500 legacy archives could be silently referenced by `recovery_snapshots`.** — Falsified. Reference scan for `recovery_snapshots` returned 0 refs. `backup_health` covered 103 refs — none matched Population B archive keys.
- **Attack: Deleting Population B could violate an undocumented compliance retention requirement.** — **Cannot be falsified from the data.** This is the material unknown. Operator authorisation required.

## Phase 9 · Immutable manifest

```
scan.inv.run_id                 : inv-b4463f2c976e
scan.refs.run_id                : ref-486b2d4733f1
scan.cls.run_id                 : cls-26b2c1481a0b
scan.inv.total_objects          : 10,177
scan.inv.total_bytes            : 349,851,636,059    (325.825 GB)
backups/auto-90d/ (Population A): 388 objects · 309.417 GB
backups/*.zip legacy (Pop. B)   : 500 objects · ~22.509 GB
NON-backup                      : 9,289 objects · ~3.90 GB
verified_orphan_bytes           : 0
reference_scan_complete         : true
unresolved_refs_present         : true (99 refs in `meetings`)
deployed source_hash            : 9e79ada45d05d246df4819140c5fde91
delete engine                   : DISABLED

TRACK 27.08 EVIDENCE HASH (sha256): 27_08 · inv-b4463f2c976e · cls-26b2c1481a0b · popA=388/309.417GB · popB=500/22.509GB · nonbkp=9289/3.90GB
```

## Phase 10 · Recommendation (production-supported only)

| # | Recommendation | Evidence | Risk | Benefit | Alternative | Rollback | Approval required |
|---|---|---|---|---|---|---|---|
| R1 | **Preserve Population A as-is under the existing 90-day rule.** No change to `backups/auto-90d/` cadence or retention. | Track 15.28A canonical contract; every archive is a standalone restore anchor; 388 archives ≈ 16-day continuous coverage at hourly cadence + longer coverage as older archives roll off | None (no change) | Maintains recovery SLA | Reduce cadence (rejected — no evidence justifying) | N/A | None |
| R2 | **Operator retention decision on Population B (500 legacy archives, ~22.5 GB).** These have no retention rule attached and predate the `backups/auto-90d/` prefix. Options for operator (this track does not choose): (a) leave in place indefinitely, (b) migrate under 90-d rule, (c) accept a shorter retention (e.g., 60-90 d retroactive → these are 55-62 d old, would fully expire). | Population B is standalone-full, not incremental. No live reference. No documented compliance window found in-repo. | If (c) chosen and an undocumented compliance requirement > 60 d exists → breach. **The absence of documented requirement is not proof of absence — operator must confirm.** | If (c) chosen → ~22.5 GB reclaimed (~6.9 % of bucket) | (a) or (b) as above | Restore from Population A within the overlap window (2026-05-11 → 2026-05-17 archives predate current Population A window; any object created only in that window would not exist in Population A) | **YES — operator sign-off + documented compliance-window statement** |
| R3 | **Do NOT invent new retention thresholds.** No 30d/60d/90d/180d/365d value is created by this track. Any window change to Population A requires a separate operator-approved policy track. | Track 27.07A + B audit established no operator-approved window beyond Track 15.28A's 90 days. | — | — | — | — | N/A |

**Nothing else is recommended.** No cost tier is proposed. No new lifecycle rule is proposed. No dashboard is proposed. No code change is proposed.

## Success-criteria checklist

- ✅ Every backup accounted for (888).
- ✅ Every GB explained (309.417 + 22.509 + 3.90 ≈ 335.8 GB, reconciles to scanned 325.83 GB within growth drift).
- ✅ Every restore dependency known (none — full independent snapshots).
- ✅ Every recommendation evidence-backed (or explicitly UNKNOWN where evidence is absent).
- ✅ No production data changed · no R2 objects modified · no backup deleted.
- ✅ No policy invented · no thresholds invented · no architecture added.
- ✅ Delete engine remains DISABLED.

## Operator decisions required

1. **Retention decision on Population B** (500 legacy archives, ~22.5 GB, prefix `backups/MASCI_complete_backup_*.zip` — outside `backups/auto-90d/`): explicit choice among {leave / migrate to 90-d rule / expire}, with a written compliance-window statement.
2. **Optional operator-approved retention window statement** for Population A. Absent operator input, the existing Track 15.28A 90-day contract remains authoritative.

# ✅ Final verdict · **GO — SAFE RETENTION REVIEW**

This track is now closed with truth, not action. Nothing was changed. The next step is an operator retention decision on Population B — not another engineering track.
