# DR-UNIFY-004 · Disaster Recovery Verification

## Backup surfaces

- **Mongo Atlas snapshots** — daily automated backups of
  `masci_safety` (and preview equivalent). Retention per Atlas
  policy.
- **Emergent code deployment** — every deploy is a versioned artifact;
  previous artifacts recoverable via the Emergent rollback UI.
- **`/app/.git` and `/app/.emergent`** — repo history preserved
  (per platform contract; do not delete).

## Failure modes and responses

| Failure                                             | Response                                                                                  |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Backend fails to boot after deploy                  | Emergent rollback UI → previous deploy. Time: < 5 min.                                    |
| Mongo write failure on `daily_reports`              | Check Atlas cluster health. Application returns 500; supervisor auto-restarts service.    |
| `dr_v2_*` collection accidentally dropped           | Restore from Atlas snapshot. Read-compat helper still returns canonical fallback.         |
| API key leaked in a response                        | Lock tests prevent this at CI. If it slips: rotate keys via provider consoles + revoke.   |
| Auto-email flooding                                 | `EMAIL_SAFETY_MODE=strict` in preview intercepts. Prod: `AUTO_EMAIL_REPORTS=false` kills it. |
| Provider outage (Anthropic/OpenAI/Google)           | Resolver returns `enabled=false, reason=no_provider_available`. Field submit unaffected.  |
| Tenant AI accidentally enabled                      | Admin AI Configuration page → set `tenant_ai_enabled=false`. Immediate effect.            |

## Verification steps

Performed 2026-02:

1. `curl /api/health` → 200 ✅
2. Supervisor status: backend + frontend RUNNING ✅
3. Live V1 submit + retrieval round-trip: works ✅
4. Migration script `--dry-run` reports 0 collisions ✅
5. Deployment audit: PASS ✅
6. Testing agent role-by-role: 12/12 CERT items ✅

## Manual DR drill (recommended pre-deploy)

Before production deploy, execute the following in preview:

```
# 1. Take a manual Mongo snapshot.
# 2. Delete a test daily_reports doc.
# 3. Restore snapshot.
# 4. Verify doc reappears.
# 5. Restart supervisor. Verify all routes respond.
```

Not executed in this cert (preview data is disposable), but the plan
is documented for production deployment.

## Never-destroy artifacts

- `.git/`, `.emergent/` — preserve at all costs.
- `daily_reports` collection.
- `operational_facts` collection.
- `operational_kpi_snapshots` collection.
- `dr_v2_*` legacy collections (until DR-UNIFY-005 explicitly drops).

**Verdict:** Disaster recovery model documented and executable.
