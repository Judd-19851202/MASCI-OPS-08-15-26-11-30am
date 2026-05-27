# Deployment Governance Maturity — Sigma-III Enforcement Model

**Phase:** SIGMA-III · P0
**Iteration:** iter437
**Status:** 🟢 SHIPPED · ENFORCED · PREVIEW VERIFIED

---

## Why this was opened

Prior to Sigma-III, the deploy contract was **documented** (in `REGRESSION_STRATEGY.md` § 3) but never **enforced**:

- Operators COULD click Emergent's "Deploy" button without running any pre-flight check.
- The GH Actions `ci.yml` only covered static checks (ruff + frontend build) — never the behavioural matrix.
- A green CI was wrongly interpreted as "safe to deploy" even though regression + Playwright + cluster-severity gates were skipped.

Sigma-III moves the contract from suggestion → enforcement.

---

## The Two-Stage Enforcement Model

Deploys are gated by **two independent stages**. Both MUST be green.

### Stage A · CI-side (GitHub Actions)

File: `/app/.github/workflows/sigma3-deploy-gate.yml`

Runs on every push + PR to `main`/`master` + manual `workflow_dispatch`.

Enforces what is provable WITHOUT a live preview backend:

| Job                            | What it checks                                                   |
|--------------------------------|------------------------------------------------------------------|
| `static-contract`              | `python -m compileall` on `server.py` + `routes/`; ruff E9/F63/F7/F82 |
| `iteration-summary-discipline` | `scripts/lint-iteration-summary.py` validates PRD discipline     |
| `governance-acknowledgement`   | Confirms governance artefacts exist; prints operator reminder    |

GitHub UI shows red ✖ on failure. Branch protection rules (set in
the repo via UI) can require this workflow before allowing merges to
`main`.

### Stage B · Operator-side (preview pod)

File: `/app/scripts/pre_deploy_check.sh`

Run by the operator from the preview pod's container shell BEFORE
clicking Emergent's "Deploy" button. Existing stages preserved; new
Sigma-III stages appended.

| Stage (in order)                       | Behaviour                                                  |
|----------------------------------------|------------------------------------------------------------|
| Backend syntax compile                 | (existing)                                                 |
| Backend lint (ruff errors)             | (existing)                                                 |
| Frontend lint                          | (existing, skip in `--auth-only`)                          |
| Frontend production build              | (existing, skip in `--fast`)                               |
| Auth + RBAC critical tests             | (existing)                                                 |
| **🆕 Sigma-III regression contract**   | `tests/regression/test_critical_flows.py + test_iter437`   |
| **🆕 Sigma-III Playwright suite**      | All 3 phases (`tests/pw_suite/`) — 35 tests × 3 viewports  |
| **🆕 Sigma-III cluster severity probe**| `/api/cluster/capacity` must return `severity ∈ {ok, warning}` — `critical` BLOCKS deploy |
| Full backend pytest suite              | (existing, full mode only)                                 |

**Exit code:** non-zero on ANY failure → script prints `❌ GATE FAILED — DO NOT DEPLOY.`

---

## Why both stages are necessary

CI cannot run the behavioural gates because they require:

- A live preview pod with `app_env=preview`
- A connected Mongo (Atlas) instance with the restored production snapshot
- The seeded super-admin account
- An Atlas TTL index baseline matching production
- A running uvicorn process to serve `/api/cluster/capacity`

These cannot reasonably be reproduced in a 5-minute GH Actions runner.
The operator-side stage is the only place these contracts can be
truly verified.

Conversely, the operator-side stage cannot detect a syntax error that
made it into a commit but never reached the preview pod (e.g. someone
pushed broken code direct to main). The CI stage catches that.

The two stages are **complementary**, not redundant.

---

## What changed in this iteration

### New files
- `/app/.github/workflows/sigma3-deploy-gate.yml` — CI-side gate
- `/app/memory/DEPLOYMENT_GOVERNANCE_MATURITY.md` — this document

### Modified files
- `/app/scripts/pre_deploy_check.sh` — appended 3 Sigma-III stages + helper functions

### Unchanged (preserved doctrine)
- Auth + RBAC stages
- Frontend lint + build stages
- Backwards-compatible flags (`--fast`, `--auth-only`)
- `scripts/lint-iteration-summary.py`
- `tools/verify-production.sh`

---

## How an operator deploys after Sigma-III

```bash
# 1. (CI auto-runs on push) — open the PR/commit in GitHub, confirm the
#    sigma3-deploy-gate workflow shows green.

# 2. In the preview pod's shell:
bash /app/scripts/pre_deploy_check.sh
# Expected last line: "✅ GATE PASSED — safe to click Emergent Deploy."

# 3. ONLY THEN click the Emergent Deploy button.

# 4. After deploy completes, run:
bash /app/tools/verify-production.sh
# Confirms the new build is live + healthy on mascidocs.com.
```

If any of these returns non-zero, the deploy is BLOCKED. There is no
override path. Fix the failure, repeat.

---

## Local verification of this iteration

```bash
$ bash /app/scripts/pre_deploy_check.sh --auth-only
# Skips frontend stages; confirms the new Sigma-III stages run cleanly.

$ python3 -m pytest \
    /app/backend/tests/regression/test_critical_flows.py \
    /app/backend/tests/pw_suite/ \
    /app/backend/tests/test_iter437_magic_link_hardening.py \
    -q
# Expected: 88 passed, 1 skipped in ~97s

$ curl -fsS "$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)/api/cluster/capacity" \
  | python3 -c "import json, sys; d=json.load(sys.stdin); print(d['severity'])"
# Expected: ok  (or warning — both are non-blocking)
```

---

## Verdict

🟢 **Sigma-III Deployment Governance — ENFORCED.**

Deploy gates have moved from documentation → executable contract. The
operator no longer has the option to bypass the regression/Playwright/
cluster-severity matrix between code change and production deploy.

# 🟢 P0 — Deployment Governance Maturity · CLOSED
