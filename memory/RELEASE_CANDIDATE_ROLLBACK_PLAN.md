# RELEASE CANDIDATE · ROLLBACK PLAN

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · Baseline and HEAD

```
Baseline (last good pre-bundle production commit) : 88541da
Current HEAD (release candidate)                   : 8019740
```

## 2 · Preferred rollback (Emergent rollback feature)

| Step | Detail |
| --- | --- |
| 1. Operator opens Emergent rollback UI | available from the Emergent control plane |
| 2. Selects checkpoint `88541da` | the certified pre-bundle baseline |
| 3. Confirms rollback | rollback engine resets the live deployment to that commit |
| Expected time | **< 60 seconds** |
| Operator effort | one click in the Emergent UI |

## 3 · Manual rollback (only if Emergent rollback UI is unavailable)

```bash
cd /app
git revert --no-commit 8019740..88541da    # generate inverse patch
git commit -m "Revert: release candidate 8019740 → 88541da"
git push origin main
# Emergent platform re-runs build + deploy hooks
```

| Detail | Value |
| --- | --- |
| Expected time | ≈ 2–3 minutes (build + deploy via supervisor hot-reload) |
| Operator effort | three commands |

## 4 · Per-sprint surgical rollback

Each of the seven release-bundle items is implemented in additive, independent commits and can be reverted individually if a specific issue is found:

| Sprint item | Anchor commit(s) | Independently revertable? |
| --- | --- | --- |
| Dispatch Production Readiness | `17fa1fd` family | YES — UI-only |
| Admin IAM screen completion | `cb8cf74` family | YES — UI-only |
| Unified User Detail Drawer | `01ab04b` family | YES — UI-only, host degrades gracefully if absent |
| Employee public endpoint hardening | precedes baseline · already in production | (already deployed; no rollback required) |
| MaintainX read-first backend | iter508 commit family | YES — new module, new routes, additive |
| MaintainX Admin Integration Center | iter509 commit family | YES — new tab, additive |
| MaintainX Defect Source Coverage | iter511 commit family | YES — new section + new endpoints, additive |

## 5 · Files that would change on rollback

Files affected (frontend operational): 15
Files affected (backend operational): 6
Files affected (env): 1 (`backend/.env` — would lose the 4 MaintainX kill-switch keys; both default behaviours map to `false` already, so this is harmless)
Files affected (memory/docs): 53 (no runtime impact)

Total: **75 files** — same as the forward diff.

## 6 · Database rollback

**NONE REQUIRED.**

- No schema change to undo.
- No migration to run.
- No new collection holds data (the only new collection is `db.maintainx_dryrun_reports`, currently empty in preview; even if production picks up rows after deploy, those rows are an isolated audit collection that can be safely retained or dropped without affecting any operational system).
- No existing collection schema was modified.
- No existing row was migrated.

## 7 · Environment rollback

**NONE REQUIRED.**

The 4 new env keys default to empty / `false` — removing them on rollback merely returns the system to its pre-bundle state. No additional cleanup needed.

If operators have populated `MAINTAINX_API_KEY` after the deploy and then rollback, the key may be left in the env vault — it will be inert (no client code in the older revision references it). A separate manual cleanup of the env vault is optional.

## 8 · Forward-compatibility note

The bundle is **forward-compatible**: a browser holding the new frontend bundle can still talk to the rolled-back backend (no API contract was removed; the new MaintainX endpoints simply 404 after rollback, which the UI handles gracefully — both the P0 tab and Coverage section fail-soft to error toasts and continue rendering).

A browser holding the **old** frontend bundle can also talk to the new backend (no required new endpoint; admin can still operate without the new tabs and the new tiles).

## 9 · Recommended rollback decision tree

| Symptom after deploy | Recommended action |
| --- | --- |
| Anything looks wrong on Dispatch Hub | Per-sprint revert of `17fa1fd` |
| `/admin/people` broken | Per-sprint revert of `cb8cf74` |
| User Detail Drawer misbehaves | Per-sprint revert of `01ab04b` |
| MaintainX endpoints failing somehow | Per-sprint revert of MaintainX commits (iter508/509/511) |
| Multiple regressions / unknown root cause | Full Emergent rollback to `88541da` |

## 10 · Verdict — Rollback Readiness

```
ROLLBACK READINESS  :  GREEN

  Preferred rollback             : Emergent UI checkpoint to 88541da (< 60s)
  Manual rollback                : 3 commands · 2-3 minutes
  Per-sprint surgical rollback   : YES (7 independent commit families)
  DB rollback required           : NO
  Migration rollback required    : NO
  Env rollback required          : NO
  Operational complexity         : LOW
```
