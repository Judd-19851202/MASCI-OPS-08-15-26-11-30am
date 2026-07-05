# DR-UNIFY-004 · Production Readiness Checklist

Every clause required for Monday-morning deployment.

## Environment

- [x] `backend/.env` protected keys intact: `MONGO_URL`, `DB_NAME`.
- [x] `frontend/.env` protected key intact: `REACT_APP_BACKEND_URL`.
- [x] AI-CONFIG-001 placeholder keys present in `backend/.env`
      (17 keys — provider APIs, gateway/module/tenant flags).
- [x] All values are placeholders / safe defaults in the git tree.
- [x] `load_dotenv(override=True)` NOT set.
- [x] Supervisor status: backend RUNNING, frontend RUNNING.

## Services

- [x] Backend binds `0.0.0.0:8001` under supervisor.
- [x] Frontend serves on `:3000` under supervisor.
- [x] All backend routes prefixed with `/api`.
- [x] Health check: `GET /api/health` → 200.
- [x] Frontend redirects `/daily-report/v2` → `/daily/submit`.

## Data

- [x] `daily_reports` schema unchanged (additive optional fields only).
- [x] `operational_facts` schema unchanged (additive
      `intelligence_fact` type only).
- [x] Legacy `dr_v2_*` collections intact (~69 docs on preview).
- [x] Historical 1,329-record backfill queryable.
- [x] Migration script dry-run reports 0 collisions.
- [x] Live migration deliberately deferred to DR-UNIFY-005.

## Workflows

- [x] `POST /api/daily-reports` accepts new V1 submissions.
- [x] V1 → ODS ingest hook fires post-submit.
- [x] HR crew data (`masci_crews[]`) preserved verbatim.
- [x] Email auto-schedule callsite unchanged.
- [x] PDF endpoints (canonical + deprecated alias) both respond.
- [x] Approved list endpoints (canonical + deprecated alias) both
      respond.
- [x] PM/Admin OI dashboards render.
- [x] DR-CUTOVER-002 summary section mounted before sign-off band.
- [x] AI-optional disabled path returns 200 (not 5xx).

## AI

- [x] Resolver `resolve_ai_capabilities` is the single gate.
- [x] AI is disabled by default per tenant (`TENANT_AI_ENABLED=false`).
- [x] Admin AI Configuration page renders with all six modules +
      audit log + provider status.
- [x] No raw API key values in any response or rendered HTML.
- [x] Provider probe returns readiness booleans only.

## Security

- [x] Admin endpoints gated by `require_admin_strict`.
- [x] Field submit endpoint public + rate-limited.
- [x] No hardcoded secrets in the repo.
- [x] No provider / model / prompt leakage.
- [x] CORS configured.

## Frontend

- [x] `/daily/submit` renders `NewDailyReport` with summary section.
- [x] `/admin/ai-configuration` renders full admin page.
- [x] EN/ES toggle functional.
- [x] No V1 / V2 / next-generation / AI-agent vocabulary on any user
      surface.
- [x] Playwright HTML scan for banned strings → zero hits.

## Testing

- [x] AI-CONFIG-001 lock envelope: 17/17.
- [x] AI-ADMIN-001 lock envelope: 17/17.
- [x] DR-CUTOVER-002 lock envelope: 22/22.
- [x] DR-UNIFY-003 lock envelope: 19/19.
- [x] ODS-001 spine + PDF sweep + EN/ES lock + platform consistency
      lock: all green.
- [x] Testing agent iteration_532 role-by-role: 12/12 CERT items.

## Deployment audit

- [x] Deployment agent: PASS · zero blockers.

## Rollback

- [x] Rollback plan documented in
      `DR_UNIFY_004_ROLLBACK_PLAN.md`.
- [x] Disaster recovery verification documented in
      `DR_UNIFY_004_DISASTER_RECOVERY_VERIFICATION.md`.

## Documentation

- [x] Every track's executive summary + zero-drift matrix present in
      `/app/memory/`.
- [x] `PRD.md`, `CHANGELOG.md`, `TECHNICAL_DEBT_REGISTER.md`,
      `PLATFORM_MANIFEST.json` all up to date.
- [x] `test_credentials.md` current.

**Overall status: ✅ READY FOR PRODUCTION DEPLOYMENT.**
