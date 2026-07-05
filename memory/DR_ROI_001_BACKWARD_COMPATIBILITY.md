# DR-ROI-001 · Backward Compatibility

**Non-negotiable:** every existing consumer keeps working across all 7 subtracks (A–G).

## Contract matrix

| Contract | Guarantee | Verified by |
|---|---|---|
| Legacy V1 POST succeeds | `model_config = ConfigDict(extra="allow")` on `DailyReportCreate` | Existing `test_daily_reports.py` |
| Legacy V1 GET returns full doc | V2 fields default null / empty | Existing tests |
| V2 POST with legacy fields only succeeds | Same schema, same defaults | New lock test (this session) |
| V2 POST with V2 fields succeeds today | Extra keys land as-is in Mongo | New lock test |
| HR crew-time reads unchanged | `masci_crews[]` shape untouched | HR portal tests |
| Safety escalation gate unchanged | 8 safety fields untouched | Safety portal tests |
| Excavation/JHA/JHP gate unchanged | 422 still fires when yes+no-links | `test_daily_reports.py` |
| Photo min 6 unchanged | Enforcement preserved | Existing tests |
| Signature required unchanged | `prepared_by_signature` + `superintendent_signature` unchanged | Existing tests |
| Job Photos mirror unchanged | Only new `photo_ai_tags[]` added later (Track D) | Job Photos tests |
| Audit trail unchanged | Trust-spine events keep firing on existing verbs | Track 15.13h tests |
| CSV export unchanged | V2 fields excluded until opt-in | Existing CSV test |
| PDF unchanged | Track F cutover only | PDF regression |
| Email delivery unchanged | No new workflow POSTs · `EMAIL_SAFETY_MODE=strict` remains | Track 22.1H tests |
| Existing dashboards unchanged | V2 dashboards mount at new routes | Playwright smoke |

## Feature flag

**Flag name:** `DR_V2_ENABLED_FOR_USER(user, project)`
**Default:** `false` (V1 is production default)
**Storage:** frontend `localStorage` opt-in for pilot users; backend `env`-driven kill switch (`DR_V2_ENABLED=false` in prod until Track G certifies)

## Rollback profile

Every V2 change is drop-column safe. Rolling back:
1. Remove V2 route from `AppRoutes.jsx` (1-line change).
2. Delete V2 folder (`frontend/src/pages/daily-report-v2/`).
3. Optional: drop `daily_report_kpis` collection (Track E only).

**No data migration ever required.** Original reports remain readable.

*Details in `DR_ROI_001_CONSOLIDATED_PLANS.md § 5`.*
