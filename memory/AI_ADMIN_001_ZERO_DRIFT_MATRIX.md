# AI-ADMIN-001 · Zero-Drift Matrix

**Claim:** AI-ADMIN-001 is purely additive. No existing route, page,
collection, workflow, or contract changed behaviour.

**Method:** Every user-facing surface was inventoried against the diff.
Row = surface. `Δ?` = whether behaviour changed.

| Surface                                      | Δ? | Evidence                                                                     |
| -------------------------------------------- | :-: | ---------------------------------------------------------------------------- |
| `POST /api/daily-reports` (V1 field submit)  | ❌  | No changes; regression lock `test_daily_report_submit_route_does_not_import_ai_admin_config`. |
| `POST /api/daily-reports` → ODS ingestion    | ❌  | No changes; regression lock `test_ai_off_still_lets_ods_ingestion_run`.       |
| `/daily/submit` field UI                     | ❌  | `NewDailyReport.jsx` untouched — grep shows no import of `AdminAIConfiguration.jsx`. |
| `/api/dr-v2/*` V2 back-office routes         | ❌  | Not touched by this track.                                                    |
| PM dashboards, briefs, KPI snapshots         | ❌  | No route/service under `services/ods_spine/*` or PM route module modified.    |
| Admin V1 daily report listing (`/api/daily-reports/approved`) | ❌ | Untouched.                                                    |
| Admin PDF (`/api/daily-reports/{id}/pdf`)    | ❌  | Untouched.                                                                    |
| Field Leadership portal                      | ❌  | Untouched.                                                                    |
| HR portal                                    | ❌  | Untouched.                                                                    |
| Safety portal                                | ❌  | Untouched.                                                                    |
| Shop portal                                  | ❌  | Untouched.                                                                    |
| Dispatch portal                              | ❌  | Untouched.                                                                    |
| Admin backups / restore / recovery           | ❌  | Untouched.                                                                    |
| Existing `GET /api/ai/gateway/status`        | ❌  | Kept intact for backward compatibility; the new `/api/admin/ai/config/status` returns the same envelope shape via the strict admin gate. |
| `.env.example`                               | ❌  | Untouched by AI-ADMIN-001 (AI-CONFIG-001 already fixed this).                 |
| `backend/.env` env keys                      | ❌  | No new env vars required.                                                     |
| Frontend router                              | ✅  | ADDITIVE: one new route `/admin/ai-configuration`.                            |
| Admin sidebar                                | ✅  | ADDITIVE: one new nav entry in `System & Governance`.                         |
| Field/PM/Shop/HR/Safety navs                 | ❌  | Zero touch.                                                                   |
| Mongo collections                            | ✅  | ADDITIVE: `tenant_ai_capabilities`, `tenant_ai_capability_audit` — created on first write only. Neither existed before AI-CONFIG-001 (which referenced the first). |

## Explicit non-changes

- No provider adapter modified (`anthropic_adapter.py`, `openai_adapter.py`,
  `google_adapter.py` — untouched).
- No resolver signature changed. `resolve_ai_capabilities(db, tenant_id, module)`
  is the same async function AI-CONFIG-001 shipped.
- `MODULE_ENV_MAP` and `PROVIDER_KEY_MAP` unchanged.
- `gateway_status_snapshot()` unchanged — new admin endpoint reuses it.

## Regression tests (must stay green)

- `backend/tests/test_ai_config_001_capabilities.py` — 17/17.
- `backend/tests/test_ai_admin_001_config.py` — 17/17 (new).

All 34 pass on this session. See `AI_ADMIN_001_TEST_REPORT.md`.

## Deployment risk

- **Config:** none required.
- **Data:** collections auto-created on first write.
- **Downtime:** none — additive router mounted at import time.
- **Rollback:** delete the two files + remove three lines from
  `server.py` / `AppRoutes.jsx` / `domainMap.js` / `AdminShell.jsx`.
  The two Mongo collections can be dropped safely if unused.
