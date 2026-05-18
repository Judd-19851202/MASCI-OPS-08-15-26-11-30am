# Pre-Deploy Verification Gate — Operational Policy

> **Maturity-phase policy.** As of iter229, every production deployment to
> `mascidocs.com` MUST pass this formal verification gate before the Emergent
> Deploy button is clicked. "Looks good in preview" is no longer sufficient
> deployment discipline.
>
> **What we're protecting:** operational continuity · HR workflows · Dispatch
> coordination · Safety records · onboarding continuity · audit integrity ·
> exports/backups · leadership communication · operational trust.
>
> **Tool:** `python3 /app/scripts/pre_deploy_verify.py`
> **Output:** `/app/deploy_reports/{timestamp}_deploy_summary.md`
> **Exit codes:** 0 = APPROVE · 1 = HOLD (operator review required) · 2 = BLOCK

---

## 0 · When this gate runs

- **MANDATORY** before every production push (the operator clicking Deploy)
- **RECOMMENDED** before merging any high-risk batch
- Re-runs of the gate are idempotent and cheap; running it twice is fine

The gate is preview-side. It does not touch production. It does not deploy
anything. It produces a verdict + a report — the operator still makes the
deploy decision.

---

## 1 · Five required check phases

### Phase 1 — Regression suite
Wraps the existing `pre_deploy_check.sh` baseline (backend syntax, ruff,
eslint, frontend build, auth/RBAC critical tests, full pytest).

PASS criteria:
- All compile/lint stages exit 0
- Auth + RBAC critical-path tests: 100% pass
- Full pytest backend suite: 100% pass (1 known skip OK)

Anti-drift sub-checks (regression suite includes them):
- `test_iter22*.py` anti-legal-drift firewall (all parametrized tone bans)
- `test_iter226*` motivational-fluff + KPI-poster banlists
- `test_iter226*` strategic-hold guard (mid-day-defect prescriptions blocked)
- Coaching registry integrity (canonical-4 per family, RBAC scope, bilingual,
  word budget)

### Phase 2 — Build verification
- Backend Python compile (no syntax errors)
- Backend lint (ruff — errors only, style warnings tolerated)
- Frontend lint (eslint — zero warnings)
- Frontend production build (`yarn build` clean)
- Dependency integrity (`backend/requirements.txt` parseable;
  `frontend/package.json` lockfile consistent)
- Env validation (required `.env` keys present and non-empty):
  - `frontend/.env`: `REACT_APP_BACKEND_URL`
  - `backend/.env`: `MONGO_URL`, `DB_NAME`

### Phase 3 — Core operational walkthrough validation
- **HR walkthrough** (`python -m walkthroughs.hr`) — must report 0 actionable
  findings (closed loop, iter225 invariant)
- **Dispatcher walkthrough** (`python -m walkthroughs.dispatcher`) — must
  report 0 actionable findings (closed loop, iter226 invariant)
- **Foreman walkthrough** (`python -m walkthroughs.foreman`) — known-finding
  baseline acceptance: actionable ≤ 6 (iter227 honest-discovery baseline
  documented; do not regress beyond this)

PASS criteria:
- HR: actionable count == 0
- Dispatcher: actionable count == 0
- Foreman: actionable count ≤ 6 AND positive-observation count ≥ 5

WARN criteria (not fail, but flag):
- Any walkthrough adds a NEW finding type not in the documented baseline
- Foreman positive-observation count drops below 5

`--fast` mode skips Phase 3 (operator must justify in deploy summary).

### Phase 4 — Production-safety checks
Live API smoke checks against the preview URL. Read-only. No mutations.

| Check | Method | PASS criterion |
|---|---|---|
| RBAC anon leakage | `GET /api/guidance/tips?form_key=employee-lifecycle` with no token | `count == 0` |
| RBAC anon leakage | `GET /api/guidance/tips?form_key=document-expirations` with no token | `count == 0` |
| RBAC anon leakage | `GET /api/guidance/tips?form_key=dispatch.handoff` with no token | `count == 0` |
| Health endpoint | `GET /api/health` (or equivalent) | HTTP 200 |
| Version endpoint | `GET /api/version` | HTTP 200 + `source_hash` present |
| Scheduler health | session lifecycle endpoint smoke | HTTP 200 if exists; skip if not |
| Backup/export smoke | `GET /api/exports/health` or equivalent | HTTP 200 or 401 (auth-gated is fine) |

Anti-drift sub-checks:
- **RBAC widening detection** — git diff scan for new `"public"` scope
  additions in `backend/guidance/tips.py`; any new public scope on a
  previously authenticated form_key = HOLD
- **Auth-surface detection** — git diff scan for changes to
  `backend/server.py` auth routes (`/api/auth/*`), `backend/auth.py`,
  `backend/sessions.py`; if touched = AUTH-SENSITIVE flag

### Phase 5 — Deployment classification
Computed from git diff against the deploy baseline (default: last deployed
commit per `/api/version`, fallback: `HEAD~1`).

**Operational risk level** — one of:
- **LOW** — coaching-only iter (tips.py + tips_es.py + tests + frontend
  HelpTipBlock wiring); no auth, no models, no migrations
- **MEDIUM** — UI changes affecting non-auth surfaces; new routes; new
  walkthrough scripts; documentation changes touching architecture
- **HIGH** — auth/RBAC modifications; backend model/schema changes;
  migration files; scheduler/lifecycle changes; session-handling changes;
  export/backup pipeline changes

**Three sensitivity flags**:
- **auth-sensitive** — any change to `backend/auth*.py`, `backend/sessions.py`,
  `backend/server.py` auth routes, or `frontend/src/contexts/Auth*`
- **data-sensitive** — any change to `backend/models/`, migration scripts,
  schema files, or seed/fixture changes
- **rollback-sensitive** — any change that alters data shape, deletes
  fields, or changes export/backup formats

---

## 2 · Deployment summary report

Every gate run writes a markdown report to `/app/deploy_reports/`.

### Required fields
- Header (timestamp · baseline ref · current ref · mode)
- Verdict: APPROVE / HOLD / BLOCK
- Phase results table
- Tests passed count (X / Y)
- Walkthrough status (HR / Dispatcher / Foreman)
- Changed operational surfaces (parsed from git diff)
- Affected portals (HR / Dispatch / Field Leadership / Safety / PM / Admin /
  Public)
- Migrations yes/no
- Auth touched yes/no
- Exports/backups touched yes/no
- Rollback considerations (free-text guidance based on classification)

### Verdict decision rules
- **APPROVE** — all phases PASS; risk LOW or MEDIUM with no sensitivity
  flags
- **HOLD** — risk HIGH OR any sensitivity flag set OR any walkthrough
  regression; requires operator review/sign-off before deploy
- **BLOCK** — any PASS-criterion failure; deploy must NOT proceed; fix
  required first

---

## 3 · Anti-drift guarantees this gate enforces

| Guarantee | Enforced by | Detection |
|---|---|---|
| Anti-legal-drift firewall holds | Phase 1 regression | Pytest fails |
| Anti-KPI-poster firewall holds | Phase 1 regression | iter226 banlist tests fail |
| Anti-motivational-fluff firewall holds | Phase 1 regression | iter224 banlist tests fail |
| Strategic-hold (mid-day-defect) preserved | Phase 1 regression | iter226 hold-guard test fails |
| Coaching registry RBAC scope intact | Phase 1 + Phase 4 | tests + live anon check |
| Reviewer-side voice discipline preserved | Phase 1 regression | iter226 reviewer-side test fails |
| HR walkthrough loop stays closed | Phase 3 | actionable count > 0 |
| Dispatcher walkthrough loop stays closed | Phase 3 | actionable count > 0 |
| Foreman known baseline doesn't regress | Phase 3 | actionable count > 6 |
| No public-scope additions sneak in | Phase 4 | git-diff scan |
| Production endpoints reachable | Phase 4 | live HTTP probes |

---

## 4 · Operating modes

| Mode | What runs | Use when |
|---|---|---|
| `python pre_deploy_verify.py` | All 5 phases | Standard pre-deploy (mandatory) |
| `python pre_deploy_verify.py --fast` | Phases 1, 2, 4, 5 (skip walkthroughs) | Rapid iteration during dev |
| `python pre_deploy_verify.py --auth-only` | Phases 1 (auth tests), 4 (RBAC smoke), 5 | Targeted auth-change verification |
| `python pre_deploy_verify.py --classify-only` | Phase 5 only | Quick risk read on a pending batch |
| `python pre_deploy_verify.py --baseline <ref>` | All phases, custom baseline | Verify against a known-good ref |

`--fast` and `--auth-only` must be explicitly justified in the deploy
summary. Default is the full gate.

---

## 5 · Cultural alignment with platform philosophy

This gate is **operational support, not bureaucracy**. It exists to:
- Catch operational regressions before they reach production
- Protect HR, Dispatch, and Safety operational continuity
- Surface auth/data sensitivity for human review
- Provide the operator with a structured report instead of a "looks good"

It does NOT exist to:
- Block every change with a checklist
- Replace operator judgment (verdict is HOLD/APPROVE/BLOCK; operator decides
  on HOLD)
- Manufacture audit trail (reports are operator-facing decision aids, not
  compliance artifacts)
- Slow iteration (typical full run: 60–180 seconds)

The gate is a **conversation with the operator**, not a barrier. When it
returns HOLD, it's saying "this batch touches sensitive surfaces — confirm
intentional." When it returns BLOCK, it's saying "something is broken; fix
first." When it returns APPROVE, it's saying "this batch is the kind of
change we've already proven safe."

---

## 6 · What this gate explicitly does NOT do

- It does not deploy. Operator still clicks Deploy.
- It does not push to git. Operator handles version control.
- It does not run production smoke tests (use `post_deploy_check.py` for that).
- It does not test from a real user browser. Walkthroughs use Playwright but
  they are scripted operational simulations, not full user testing.
- It does not enforce branch protection or merge gates. It's a local discipline
  tool that runs in the preview pod.

---

*Policy authored iter229 · part of the stabilization-phase maturity protocol.
The gate is preview-only. The verdict is operator-facing. The discipline is
operational protection.*
