# DR-UNIFY-004 · Remaining Technical Debt

## Production blockers

**ZERO.**

Every item on the deployment gate is satisfied. No known defect,
regression, security issue, performance issue, or data risk blocks
Monday-morning deployment.

## P1 non-blockers (post-deploy scheduling)

- **DR-UNIFY-005 · Live migration + legacy cleanup.** Execute
  `--live` against production (with Atlas snapshot) once
  DR-UNIFY-004 telemetry confirms zero `/api/dr-v2/*` external
  callers for 30 days. Then drop the legacy collections and rename
  backend module filenames.
- **Background task queue for ODS ingestion.** V1 submit currently
  ingests synchronously. Move to a Redis/RQ-style queue before wide
  AI enablement causes tail latency.

## P2 non-blockers

- **Include Daily Operational Summary in PDF renderer.** Requires
  a golden-file diff test. Data is already stored on the doc; only
  renderer wiring remains.
- **Include summary in the auto-email body.** Same; data on the doc
  ready to render.
- **Live-LLM polish over the deterministic composer.** A future
  middleware wrapper can hand composed text to Anthropic/OpenAI for
  a style pass — with a hard "never introduce a new fact" cross-check
  against the composer's evidence_refs.
- **Live provider probe endpoint on Admin AI Configuration.** Today
  reports readiness (flag + key present). A follow-up can issue a
  cheap real LLM call with a bounded timeout so operators can verify
  keys work.
- **Tenant-admin scoped role.** When multi-tenant expands beyond
  MASCI, add `require_tenant_admin` gate scoped to a single tenant
  so tenant owners can self-serve.
- **Byte-comparison test between canonical and deprecated PDF
  variants.** DR-UNIFY-005 will add this alongside the alias removal
  decision.

## P3 non-blockers

- **Compound index on `tenant_ai_capability_audit.{tenant_id, timestamp}`**
  when volume exceeds ~1k entries per tenant.
- **Purge `dr_v2_optin` localStorage key** on any device that still
  carries it (harmless dead entry after redirect).
- **Sweep dead frontend files** (`ExecutiveOperationalIntelligence.jsx`,
  `pages/daily-report-v2/**`, `lib/dailyReportV2*.js`) once no tests
  reference them.
- **pytest-asyncio cross-test event-loop artefact.** One legacy
  `test_ods_001_spine.py` test intermittently fails when scheduled
  next to specific other test files; passes standalone in every
  order. Investigate `asyncio_default_test_loop_scope`.

## Zero-drift monitoring recommendations (post-deploy)

- Log `/api/dr-v2/*` vs `/api/daily-reports/*` request counts for 30
  days to inform the DR-UNIFY-005 alias-removal decision.
- Track `tenant_ai_capability_audit` insertions per week to catch any
  unexpected AI configuration churn.
- Track `operational_facts` write latency to catch ODS regression
  before it becomes user-visible.

**All items above are follow-ups, not blockers. Deployment is
approved.**
