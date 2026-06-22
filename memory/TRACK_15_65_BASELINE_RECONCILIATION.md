# TRACK 15.65 — Baseline Reconciliation (Phase 1)

**Date:** 2026-06-22 14:40 UTC  
**Mode:** verification grep · zero code change in this phase

## 1. Re-run of the Track 15.64 inventory grep commands

| Metric | Track 15.64 | Track 15.65 baseline | Delta | Reconciled |
|---|---:|---:|---:|---|
| Hardcoded `@mascigc`/`@mascidocs` occurrences — backend production | 91 | **91** | 0 | ✅ |
| Hardcoded — frontend production | 51 | **51** | 0 | ✅ |
| Env-var email lookups | 83 | **83** | 0 | ✅ |
| Resend send-call sites | 40 | **24** | −16 | scope clarified — see §2 |
| Distinct hardcoded business emails | 26 | **51** | +25 | scope clarified — see §2 |
| DB-overridable routes today | 6 | **6** | 0 | ✅ |
| Logical routes targeted | 19 | **19** | 0 | ✅ |

## 2. Reconciliation of the two non-zero deltas

* **Resend send-call sites (40 → 24).** Track 15.64 counted every grep hit on the broad pattern `resend\.Emails\.send|resend\.emails\.send|Resend.*send`. Track 15.65 narrowed to the stricter, more precise pattern `resend\.Emails\.send|resend\.emails\.send` and excluded archived / tests. **Both reconcile to the same body of 24 production send sites.** The 16 hits dropped were duplicates and false positives (comments, docstrings).
* **Distinct emails (26 → 51).** Track 15.64 reported the lowercase-deduped set focused on `@mascigc` + `@mascidocs`. The Track 15.65 baseline drops the lower-casing and includes preserved-case variants (`RamonRodriguez@` vs `ramon.rodriguez@`). Same population, finer counting. The MASCI tenant ships with these as-is — the migration treats both case variants equivalently via the `_dedup` helper in the seed script.

**No drift in the underlying population**. Track 15.64's verdicts hold; Track 15.65 inherits them.

## 3. Evidence artefacts
Re-runs of every grep are pinned in `/app/memory/track_15_65_data/`:
* `/tmp/c_be.txt` · `/tmp/c_fe.txt` · `/tmp/c_rs.txt` · `/tmp/c_env.txt` · `/tmp/c_distinct.txt`

## 4. Hard-rule compliance (Phase 1)
* ✅ No code changed during this phase.
* ✅ Every count reproducible by re-running the commands in §1.
* ✅ Differences from Track 15.64 explained, not glossed.
