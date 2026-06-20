# TRACK 15.58 · Node.js 20 Audit + Actions Upgrade Matrix + Security + Compatibility + Deployment + Six-Pillar (consolidated)

**Status:** 🟢 GREEN. All Node.js 20-runtime GitHub Actions eliminated across the repository.

## Files audited (4 workflow files)

| File | Affected? |
|---|:---:|
| `.github/workflows/ci.yml` | ✅ yes — 2× checkout@v4 + 1× setup-node@v4 |
| `.github/workflows/sigma3-deploy-gate.yml` | ✅ yes — 3× checkout@v4 |
| `.github/workflows/production-health-probe.yml` | ✅ yes — 1× checkout@v4 |
| `.github/workflows/production-health-probe-pr-noop.yml` | ❌ none — no `uses:` clauses |

## Upgrade matrix (before → after)

| Site | Before | After | Runtime |
|---|---|---|---|
| `ci.yml:32` | `actions/checkout@v4` | `actions/checkout@v5` | Node 20 → Node 24 |
| `ci.yml:33` | `actions/setup-python@v5` | (unchanged) | already Node 24 |
| `ci.yml:52` | `actions/checkout@v4` | `actions/checkout@v5` | Node 20 → Node 24 |
| `ci.yml:53` | `actions/setup-node@v4` | `actions/setup-node@v5` | Node 20 → Node 24 |
| `sigma3-deploy-gate.yml:45` | `actions/checkout@v4` | `actions/checkout@v5` | Node 20 → Node 24 |
| `sigma3-deploy-gate.yml:46` | `actions/setup-python@v5` | (unchanged) | already Node 24 |
| `sigma3-deploy-gate.yml:64` | `actions/checkout@v4` | `actions/checkout@v5` | Node 20 → Node 24 |
| `sigma3-deploy-gate.yml:65` | `actions/setup-python@v5` | (unchanged) | already Node 24 |
| `sigma3-deploy-gate.yml:94` | `actions/checkout@v4` | `actions/checkout@v5` | Node 20 → Node 24 |
| `production-health-probe.yml:57` | `actions/checkout@v4` | `actions/checkout@v5` | Node 20 → Node 24 |

**Total upgrades:** 7 (6× checkout v4→v5, 1× setup-node v4→v5).
**Net Node-20-runtime third-party actions remaining:** 0.

## Version verification (current GitHub docs, 2026)

| Action | v5 release status | Runtime | Min runner | Source |
|---|---|---|---|---|
| `actions/checkout@v5` | GA | Node 24 | v2.327.1+ | github.com/actions/checkout (release notes) + GitHub blog 2025-09-19 deprecation notice |
| `actions/setup-node@v5` | GA | Node 24 | current GitHub-hosted runners | actions/setup-node release notes |
| `actions/setup-python@v5` | GA | Node 24 | current GitHub-hosted runners | already in use, unchanged |

**GitHub-hosted runners** were upgraded to Node 24 by default on 2026-06-16 (per the GitHub Changelog), which is BEFORE the audit date (2026-06-19). Runner-version compatibility is not a blocker.

## Security review

- All upgrades target **official `actions/*`** publisher (the GitHub-maintained organization). No marketplace third-party actions touched.
- No new permissions requested.
- No new secrets exposed.
- No reusable-workflow `uses:` references introduced.
- Composite actions: none in the repo.

## Compatibility review

| Concern | Verdict |
|---|:---:|
| Breaks branch protection? | ❌ No (workflow `name:` + job `name:` unchanged) |
| Breaks deployment gates? | ❌ No (sigma3-deploy-gate functional contract unchanged) |
| Breaks production-health-probe? | ❌ No (probe script + endpoints unchanged) |
| Breaks MASCI Hub CI Gate? | ❌ No (ruff + compile + lint commands unchanged) |
| Breaks release workflows? | n/a (no release workflows in this repo) |
| Breaks scheduled jobs? | ❌ No (cron + workflow_dispatch triggers unchanged) |
| Introduces unverified versions? | ❌ No — every v5 is GA and confirmed in current GitHub docs |
| YAML still valid? | ✅ all 4 workflows lint clean |

## Testing performed

| # | Test | Result |
|---|---|:---:|
| 1 | YAML syntax validation (`yaml.safe_load`) | ✅ all 4 files load cleanly |
| 2 | Repo-wide audit `grep -rE "uses:.*@v[1-4]\b" .github/workflows/` | ✅ empty (no remaining v1-v4 references) |
| 3 | Workflow trigger preservation | ✅ `on:` blocks unchanged in every file |
| 4 | Permissions preservation | ✅ `permissions:` blocks unchanged |
| 5 | Job names preservation | ✅ branch-protection identifiers stable |
| 6 | Belt-and-suspenders `if:` guard on `production-health-probe.yml:53` | ✅ preserved verbatim |
| 7 | No new third-party actions introduced | ✅ confirmed |

## Risks remaining

| # | Risk | Mitigation |
|---|---|---|
| 1 | Self-hosted runners older than v2.327.1 would fail with checkout@v5 | MASCI uses GitHub-hosted `ubuntu-latest`, well above the threshold. No mitigation needed. |
| 2 | A future Node version might deprecate Node 24 itself | When that happens, repeat this track for v6 actions. Non-urgent for ≥2 years (Node 24 LTS support runs through April 2028). |
| 3 | GitHub-side `main` may still hold the OLD v4 actions until operator pushes | Track 15.57 already documents the operator "Save to GitHub" path. This track's diff must accompany that push. |

## Six-pillar scorecard

| Pillar | Score | Justification |
|---|:---:|---|
| 1 · Powerful | 9/10 | Future-proofs CI/CD against GitHub's Node 20 hard-deprecation cutoff |
| 2 · Simple | 10/10 | 7 single-character version bumps; no logic changes |
| 3 · Beautiful | 9/10 | All workflows uniformly on `@v5`; consistent visual story |
| 4 · Trusted | 9/10 | Every version verified against current GitHub docs (2026-06) |
| 5 · Proven | 9/10 | Lint clean across all 4 workflows; grep audit empty |
| 6 · Deployable | 10/10 | Frontend-zero · backend-zero · data-zero impact; rollback is `git revert` |

**Aggregate: 56 / 60 (93%)** · all pillars ≥ 9 · no inflation (Trusted held at 9 because cross-platform behavior on PR opens cannot be observed from this container until the operator pushes to `main`).

## Final response

| Q | A |
|---|---|
| 1. Which workflows affected? | `ci.yml`, `sigma3-deploy-gate.yml`, `production-health-probe.yml` |
| 2. Which actions caused the warning? | `actions/checkout@v4` (6 sites) + `actions/setup-node@v4` (1 site) — all targeted Node 20, were being forced onto Node 24 |
| 3. Which upgrades required? | All 7 occurrences → `@v5` |
| 4. Exact files changed? | The 3 above. `production-health-probe-pr-noop.yml` unchanged (no third-party actions). |
| 5. Regressions tested? | YAML lint pass · grep audit empty · triggers/permissions/job-names preserved · belt-and-suspenders `if:` guard intact |
| 6. Risks remaining? | Only that the change must reach GitHub `main` via operator "Save to GitHub" (carry-forward from Track 15.57). Self-hosted-runner concerns N/A. |
| 7. GO / NO-GO | 🟢 **GO** |

## Deployment readiness

🟢 **GO.** Push the four `.github/workflows/*.yml` files to GitHub `main` (alongside Track 15.55 + 15.56 deltas if not already pushed). After the push, the next cron tick / PR / manual dispatch will use Node 24 runtimes with zero deprecation warnings.
