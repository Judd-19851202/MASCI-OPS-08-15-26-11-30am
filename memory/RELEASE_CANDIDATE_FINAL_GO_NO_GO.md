# RELEASE CANDIDATE · FINAL GO / NO-GO

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification
**Decision:** Operator authorisation gate before production deployment

---

## 1 · Release composition

The release candidate bundles seven independently-built items:

| # | Item | Commit family | Phase Verdict |
| --- | --- | --- | --- |
| 1 | Dispatch Portal cleanup / production readiness | `17fa1fd` | PASS (Phase 5) |
| 2 | Admin IAM screen completion | `cb8cf74` | PASS (Phase 4) |
| 3 | Unified User Detail Drawer | `01ab04b` | PASS (Phase 4) |
| 4 | Employee public endpoint projection hardening | already in baseline | PASS (Phase 6) |
| 5 | MaintainX read-first backend foundation (P0-A/P0-B) | iter508 | PASS (Phase 7) |
| 6 | MaintainX Admin Integration Center | iter509 | PASS (Phase 7) |
| 7 | MaintainX Defect Source Coverage Command Center | iter511 | PASS (Phase 4 / 7) |

---

## 2 · Baseline & HEAD

```
Baseline (last good production commit) : 88541da
Current HEAD (release candidate)        : 8019740
```

---

## 3 · Changed-files summary

| Type | Count | Notes |
| --- | --- | --- |
| `.md` (documentation) | 53 | No runtime impact |
| `.jsx` | 14 | 8 NEW · 6 MOD |
| `.py` | 6 | 4 NEW · 2 MOD |
| `.js` | 1 | `buildVersion.generated.js` |
| **Total** | **74** | 21 code · 53 docs |

**Auth / password / identity-mirror diffs: 0.**
**DB schema / migration diffs: 0.**
**MaintainX write code diffs: 0.**

Full file list and per-file risk classification in `RELEASE_CANDIDATE_DIFF_CERTIFICATION.md`.

---

## 4 · Tests run

| Suite | Result |
| --- | --- |
| `tests/test_maintainx_p0_read_first.py` | 13 / 13 PASS (0.16s) |
| `yarn build` (production CRA build) | PASS (33.13s, deployable bundle, 0 NEW warnings introduced by this release) |
| ESLint per-file on 14 changed frontend files | 0 blocking · 0 advisory |
| Ruff lint per-file on changed backend files | 0 / 0 |
| Live `/api/employees` projection probe | 7/7 allow-list · 0/12 forbidden leaks · 330 employees |
| Live `POST /api/auth/multi-login` | OK · all 7 portal tokens minted |
| Live `GET /api/admin/maintainx/p0/config` | OK · `api_key_present=false`, `write_enabled=false` |
| Live `POST /api/admin/maintainx/p0/dryrun` | OK · `writes_performed.*` all 0 |
| Live `GET /api/admin/maintainx/defect-coverage` | OK · 138 open · `writes_performed.*` all 0 |
| Authenticated route smoke | 5/5 PASS |
| Public form smoke | 4/4 PASS |

---

## 5 · Phase results

| Phase | Cert file | Verdict |
| --- | --- | --- |
| 1 · Diff / Footprint | `RELEASE_CANDIDATE_DIFF_CERTIFICATION.md` | **PASS** |
| 2 · Build / Test | `RELEASE_CANDIDATE_BUILD_TEST_CERTIFICATION.md` | **PASS** |
| 3 · Login / IAM Safety | `RELEASE_CANDIDATE_LOGIN_IAM_CERTIFICATION.md` | **PASS** (required sentence signed) |
| 4 · Admin IAM UI | `RELEASE_CANDIDATE_ADMIN_IAM_CERTIFICATION.md` | **PASS** |
| 5 · Dispatch | `RELEASE_CANDIDATE_DISPATCH_CERTIFICATION.md` | **PASS** |
| 6 · Employee Endpoint Hardening | `RELEASE_CANDIDATE_EMPLOYEE_ENDPOINT_CERTIFICATION.md` | **PASS** |
| 7 · MaintainX Safety | `RELEASE_CANDIDATE_MAINTAINX_CERTIFICATION.md` | **PASS** (zero MX writes possible) |
| 8 · Role Route Smoke | `RELEASE_CANDIDATE_ROLE_SMOKE_CERTIFICATION.md` | **PASS** |
| 9 · Data Safety | `RELEASE_CANDIDATE_DATA_SAFETY_CERTIFICATION.md` | **PASS** |
| 10 · Rollback Readiness | `RELEASE_CANDIDATE_ROLLBACK_PLAN.md` | **GREEN** |

---

## 6 · Single-sentence safety attestation

> **No existing user, password, temp password, credential, login history, audit history, role assignment, or portal assignment was modified, deleted, recreated, invalidated, or migrated during this release or its certification.**

---

## 7 · Known limitations (none are blockers)

| Limitation | Impact | Mitigation |
| --- | --- | --- |
| `MAINTAINX_API_KEY` is unset in preview | MaintainX dry-run pulls 0 assets; defect coverage shows "Ready=2 · Mapped=0" | Operator may provision a real key any time after deploy; no code change required |
| 134 defects are BLOCKED in the live coverage view | Data-quality signal — these defects can't yet resolve to live `equipment_master` rows | This IS the intended pre-write intelligence; operator triages before turning on writes |
| Production CI-strict `yarn build` would fail | Pre-existing baseline warnings on files outside this release | No new warnings introduced; production deploy uses the default `yarn build` (which succeeds in 33.13s) |

---

## 8 · Rollback path

| Option | Steps | Time |
| --- | --- | --- |
| Preferred | Emergent rollback UI → checkpoint `88541da` | < 60s |
| Manual | `git revert` + push | 2-3 min |
| Per-sprint surgical | Revert any of 7 commit families independently | < 2 min each |

DB rollback: not required. Migration rollback: not required. Env rollback: not required.

Full plan in `RELEASE_CANDIDATE_ROLLBACK_PLAN.md`.

---

## 9 · Deployment recommendation

```
================================================================
  RELEASE CANDIDATE PRE-DEPLOY CERTIFICATION
================================================================
  Baseline                    : 88541da
  HEAD                        : 8019740
  Files changed (code)         : 21  (8 new JSX + 4 new PY + 9 mod)
  Files changed (docs)         : 53
  Auth surface mutations       : 0
  DB schema mutations          : 0
  Migration runs               : 0
  MaintainX writes possible    : 0
  MaintainX writes performed   : 0
  Defect / equipment mutations : 0
  Backend tests                : 13 / 13 PASS
  Frontend build               : PASS · 33.13s · deployable
  Authenticated routes smoked  : 5 / 5
  Public forms smoked          : 4 / 4
  Critical errors              : 0
  Rollback readiness            : TRIVIAL (frontend/backend code only)
================================================================
                         DECISION
                  🟢 GO — SAFE TO DEPLOY
================================================================
```

### What this verdict means
- The release candidate is **safe to promote** to production.
- All seven bundled sprint items are additive, read-only at the data layer, and fully reversible via the Emergent rollback feature in under a minute.
- Login / IAM / password / portal-assignment / audit / login-history integrity is intact and verified.
- MaintainX cannot write to anything until operator separately authorises Stage 6 (per the master plan).

### What this verdict does NOT authorise
- Flipping `MAINTAINX_WRITE_ENABLED=true` in production.
- Flipping `MAINTAINX_SYNC_ENABLED=true` in production without separate operator authorisation.
- Building canonical defect payload code (Stage 2 of master plan).
- Pushing any MaintainX work order.
- Modifying any defect, DVIR, RTS, Pre-Op, Shop, or Dispatch lifecycle code.
- Any further code change without a new operator directive.

— End of Release Candidate Final GO/NO-GO —
