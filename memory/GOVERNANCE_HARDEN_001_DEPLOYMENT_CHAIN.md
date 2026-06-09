# GOVERNANCE-HARDEN-001 · Workstream F · Deployment Chain

```
Environment    : both
Access Level   : static-analysis + preview-runtime + external-probe
Evidence Source: /app/backend/.env · /app/frontend/.env · `git log` · curl probes · platform behaviour observed in this session
Confidence     : VERIFIED for steps 1-7 (observable) · INFERRED for operator-side mechanics (cannot observe directly)
```

---

## §F.1 · End-to-end deployment chain (observed)

```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1 — PREVIEW BUILD (this fork pod)                            │
│  • Agent writes code in /app/backend, /app/frontend                  │
│  • Hot reload picks up changes within seconds                        │
│  • Supervisor manages backend (uvicorn) + frontend (craco dev)       │
│  • Sentry release tag                                                │
│    : source_hash = b1cfa3598c80665f606007f1e155a43c (today)          │
│  Who: E1 fork agent + tools (root in container)                      │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            │ (no automated gate; pure dev iteration)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2 — PREVIEW TEST                                              │
│  • jest (frontend)  — e.g., resiliencyQueue 7/7 today                │
│  • pytest (backend) — /app/backend/tests                             │
│  • Curl smoke against external preview URL                           │
│  • Screenshot smoke (optional)                                       │
│  Who: E1 fork agent invoking testing_agent_v3_fork OR direct        │
│       jest/pytest in preview pod                                     │
│  Required evidence: test report JSON in /app/test_reports/           │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3 — PREVIEW CERTIFICATION                                     │
│  • Markdown report under /app/memory/*_CERTIFICATION*.md             │
│  • MUST carry the four-field header (per Workstream E)               │
│  • Verdict: PASS / CONDITIONAL PASS / FAIL                           │
│  Who: E1 fork agent under OMEGA directive                            │
│  Required evidence: verbatim test output + explain plans + curl      │
│                     outputs · stored under /app/memory/<sprint>_     │
│                     evidence/                                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            │ Operator reviews; if approved →
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4 — PUSH TO GIT                                               │
│  • Operator clicks "Save to GitHub" in Emergent chat UI              │
│  • Git remote (operator-owned) receives commits                      │
│  Who: Operator only — fork has no Git push authority                 │
│  Required credentials: GitHub OAuth token (held by operator)         │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 5 — PRODUCTION DEPLOYMENT                                     │
│  • Operator clicks "Deploy" in Emergent chat UI                      │
│  • Emergent platform pulls latest commit, builds, restarts prod pod  │
│  • Prod pod boot runs ensure_indexes() blocks (idempotent)           │
│  • Sentry release tag                                                │
│    : source_hash = 7f68853f791fb19709cee3be9f7e70b8 (today, prod)    │
│  Who: Operator only                                                  │
│  Required credentials: Emergent platform deploy permission           │
│  Database changes: indexes only (idempotent); no schema migration    │
│                    unless explicitly authored in the migration code  │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 6 — PRODUCTION VALIDATION                                     │
│  • External probes against https://mascidocs.com                     │
│  • /api/version returns app_env=production, db_name=masci_safety     │
│  • Auth gate enforces 401 on protected routes                        │
│  • Webhook contracts verifiable: 401/503/200 paths                   │
│  • DB-backed signals readable via shared cluster Atlas user          │
│  • Operator-side: admin login + dashboard counts (auth-only flows)   │
│  Who: Operator + fork agent (read-only) cooperating                  │
│  Required evidence: PROD_STABILIZE / POST_DEPLOY-style reports       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 7 — ROLLBACK PATH                                             │
│  • Operator clicks "Rollback" in Emergent chat UI                    │
│  • Platform restores prior commit's build to prod pod                │
│  • Database: no automatic rollback — schema/data changes persist     │
│              unless a migration explicitly undoes them               │
│  Who: Operator only                                                  │
│  Required credentials: Emergent platform rollback permission         │
│  Limit: Code rollback only. Data rollback requires Atlas restore     │
│         from latest hourly backup (DEPLOY-FIX-001 verified).         │
└─────────────────────────────────────────────────────────────────────┘
```

## §F.2 · Authority matrix

| Action | Authority | Required credential |
|---|---|---|
| Author code in preview | E1 fork agent | Container root (provided by Emergent) |
| Restart preview supervisor | E1 fork agent | `sudo supervisorctl` (provided) |
| Run preview tests | E1 fork agent | none additional |
| Author certification markdown | E1 fork agent | none additional |
| Push to GitHub | **Operator only** | GitHub OAuth (operator-held) |
| Promote to production | **Operator only** | Emergent platform deploy permission |
| Modify prod pod `.env` | **Operator only** | Emergent secrets panel |
| Direct prod DB write | E1 fork agent (CAPABILITY) · Operator-authorized in practice | Shared cluster Atlas user (`admin_db_user`) |
| Atlas user / role / cluster ops | **Operator only** | Atlas Console login |
| Rollback prod | **Operator only** | Emergent platform rollback permission |
| Atlas point-in-time restore | **Operator only** | Atlas Console |

## §F.3 · Required evidence at each gate

| Stage | Mandatory evidence | Where stored |
|---|---|---|
| 2 — Preview Test | jest output OR pytest output OR `/app/test_reports/iteration_*.json` | `/app/test_reports/` |
| 3 — Preview Certification | Markdown report with four-field header + raw evidence captures | `/app/memory/<SPRINT>_*.md` + `/app/memory/<sprint>_evidence/` |
| 5 — Production Deployment | Operator-attested green light + reference to the certification | Chat history + commit message |
| 6 — Production Validation | External probes + operator-attested authenticated checks per `PROD_STABILIZE_001_CERTIFICATION.md` § 8 | `/app/memory/PROD_STABILIZE_001_*.md` and successor reports |
| 7 — Rollback | Operator rollback decision recorded in chat + post-rollback validation report | `/app/memory/` rollback report |

## §F.4 · Required approvals

| Gate | Required approver |
|---|---|
| Preview commit | E1 fork (self-approve allowed for non-production sprints) |
| Preview Certification → PASS | Operator review (per OMEGA: "STOP AT CERTIFICATION. WAIT FOR OPERATOR.") |
| Push to GitHub | Operator |
| Deploy to production | Operator (cannot be delegated to fork) |
| Rollback | Operator |
| Atlas Console action | Operator |

## §F.5 · Gaps observed in the current chain

1. **No automated pre-deploy lint/test gate on the operator path.** The operator clicks "Deploy" without an enforced check that preview tests are green. Recommendation: a Stage-3 → Stage-5 gate that requires the certification report to exist and have its header.
2. **No environment-isolation gate on Atlas credential.** Stage 5 runs against prod DB using the same Atlas user as preview. Recommendation per Workstream A § A.7.
3. **No automated certification-header check.** Workstream E doctrine relies on operator review until tooling is built.
4. **No `.env` diff visibility between preview and prod.** Operator cannot easily see whether the two pods' `.env` files have drifted. Recommendation: an operator-only command that compares key SHAs (not values) across the two pods.
5. **No deployment-evidence persistence outside `/app/memory/`.** Memory files live in the preview pod's filesystem. A pod rebuild without Git push would erase them. (Mitigated today by operator using "Save to GitHub" frequently.)

## §F.6 · Verdict — Workstream F

✅ **PASS as documentation.** ⚠️ **Five chain-of-custody gaps documented** (§F.5) for operator review and prioritization. No code or config changes attempted in this audit per directive.
