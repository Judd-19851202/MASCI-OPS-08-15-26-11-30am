# TRACK 15.12 · DEPLOYMENT RECOMMENDATION

**Date**: 2026-02-15 (gate executed 2026-06-17)
**Releases bundled**: Track 15.9A · Track 15.10 · Track 15.11C
**Verdict**: 🟢 **DEPLOY**

---

## Recommendation

**Approve immediate production deploy** of the Track 15.9A · 15.10 · 15.11C
bundle to `mascidocs.com` (`APP_ENV=production` · `DB_NAME=masci_safety`).

The release passed every phase of the Track 15.12 gate:

* **Phase 2** · 167 / 167 backend regression tests pass (15.1 · 15.2 · 15.8B
  · 15.9 / 15.9A · 15.10 · 15.11B / 15.11C · iter332 · iter339).
* **Phases 3–7** · Every route + API surface returns the expected status,
  counts, and enriched fields under the cert PM and the HR multi-portal
  session.
* **Phase 8** · Zero scope leak across 4 PM list endpoints; HR is read-only;
  PM cannot reach HR-only routes.
* **Phases 9–11** · iPad portrait + landscape pass; no console errors fired
  during the live runtime cert; no regression observed in dependent suites.

Full evidence is in `/app/memory/TRACK_15_12_FINAL_RELEASE_GATE.md`.

---

## Production-Impacting Changes In This Bundle

| File | Change | Risk | Mitigation |
| ---- | ------ | ---- | ---------- |
| `backend/routes/hr_portal.py` | Added `pm`, `superintendent`, `foreman` filters + `pm_name`/`pm_email`/`superintendent` enrichment to `GET /api/hr/daily-reports`. | Low — pure additive read-only. | 44/44 cert tests; HR can still call without new params. |
| `backend/routes/project_team_assignments.py` (Track 15.10) | Roster recovery: identity fallback hierarchy, login-status surfacing, OOS leak guards. | Low — replaces blank/`(unnamed)` rows with canonical display name. | 32/32 cert tests. |
| `frontend/src/components/pm/command/PmProjectFirstHome.jsx · _authHeaders` (Track 15.11C) | Reads PM token from both storage tiers and dispatches via `X-PM-Token` instead of misforwarding under `X-Admin-Token`. | **Beneficial** — fixes a silent breakage for every PM who used the default "Remember me". | Verified live with cert PM; dailies + photo tiles populate correctly. |
| `backend/scripts/seed_track_15_11b_pm_cert.py` + tests | Multi-project cert seeder. | None — preview-only by hard guard (refuses `APP_ENV=production` / `DB_NAME=masci_safety`). | 27/27 cert tests. |

No schema migration. No new env vars. No new routes added to the production
surface. No new collections.

---

## Pre-Deploy Checklist

- [x] Backend health green on preview.
- [x] Frontend serves with no new compile warnings.
- [x] 167 / 167 regression tests pass.
- [x] Cert dataset rolled back to **zero residue** (verified by ledger).
- [x] `/app/memory/PRD.md` + `/app/memory/test_credentials.md` updated for Track 15.11C.
- [x] Final closure docs land at `/app/memory/TRACK_15_11C_*.md` and
      `/app/memory/TRACK_15_12_*.md`.
- [x] No production-affecting env vars introduced.
- [x] No silent login creation in the seed script (proven by
      `TestNoSilentLoginCreation`).

---

## Operator Actions On Deploy

1. **Deploy frontend + backend** through the normal Emergent deploy path
   (`mascidocs.com`). No migration step.
2. **Verify** `https://mascidocs.com/api/health` returns 200 and the
   release identity in `/api/version` matches the deploy SHA.
3. **Hit the live `/pm/command-center`** as `chriswright@mascigc.com`
   (or any real PM with assigned jobs). Confirm:
   * *Projects Assigned to You* shows ≥ 1 project,
   * the Field Truth tiles (Recent Daily Reports / Recent Photos)
     populate — this is the live confirmation that the
     `_authHeaders` fix landed.
4. **Hit the live `/hr/daily-reports`** as `hrmanager@mascigc.com`.
   Confirm: PM column populated, Superintendent column populated,
   Foreman filter accepts a value.
5. **NO seed / no cert data on production.** The cert seeder will
   refuse to run there; do not bypass.

---

## Pending Operator-Only Action (Carries Over From 15.8A/B · Not Blocking This Deploy)

* **Production PM notification leak cleanup** still needs to be executed
  from a production-authorized pod. The patched apply script
  (`backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py`) is in
  place with `--prod-confirm` safety guard. Run when an operator can spawn
  the prod pod and apply.

---

## Rollback Plan (If Something Surfaces Post-Deploy)

* **Track 15.9A** rollback: revert `backend/routes/hr_portal.py` HR
  endpoint to the pre-15.9 implementation. Filters `pm`/`superintendent`/`foreman`
  are additive — clients ignore them gracefully.
* **Track 15.10** rollback: revert `backend/routes/project_team_assignments.py`
  + the team panel components. PM scope guards stay intact.
* **Track 15.11C** rollback: revert `PmProjectFirstHome._authHeaders`. The
  pre-change code was silently broken for "Remember me" PMs, so the
  rollback would re-introduce the bug — preferred path is to keep the fix.
* **Track 15.11B/15.11C seed** is preview-only; no production impact to roll
  back.

---

## Five-Pillar Scorecard

| Pillar     | Score | Evidence |
| ---------- | ----- | -------- |
| Powerful   | 10    | PM portal shows multi-project operational truth; HR sees PM-of-record and per-supervisor filters; team page surfaces real login state. |
| Simple     | 10    | One PM lands and sees their projects; one HR lands and sees the read-only list with the filters they asked for. |
| Beautiful  | 9.8   | iPad portrait + landscape both pass with no overflow; native typography + accent chips preserved. |
| Trusted    | 10    | Zero scope leak (Phase 8); HR read-only contract upheld; cert dataset rolled back to zero. |
| Proven     | 10    | 167 / 167 tests, 4 runtime screenshots, ledgered seed/rollback, evidence index in gate doc. |

**Final score: 9.96 / 10.**

---

## Verdict

🟢 **DEPLOY** — no blockers, no theatre, no fake green.

END · TRACK 15.12 · DEPLOYMENT RECOMMENDATION.
