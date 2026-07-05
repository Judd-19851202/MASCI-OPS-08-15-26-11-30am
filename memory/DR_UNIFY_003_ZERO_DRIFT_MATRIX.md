# DR-UNIFY-003 · Zero-Drift Matrix

**Claim:** DR-UNIFY-003 is a cleanup track. Nothing users depend on
changed. Every downstream contract preserved.

| Surface                                                | Δ? | Evidence                                                                     |
| ------------------------------------------------------ | :-: | ---------------------------------------------------------------------------- |
| `/daily/submit` field workflow                         | ❌  | `NewDailyReport.jsx` untouched (locked by DR-CUTOVER-002 mount test).        |
| `POST /api/daily-reports` submit path                  | ❌  | `routes/daily_reports.py` untouched.                                          |
| DR-CUTOVER-002 summary section                         | ❌  | Still mounted; regression `test_daily_submit_form_still_mounts_the_summary_section`. |
| Daily Operational Summary endpoints                    | ❌  | Under canonical `/api/daily-reports/*` — same as before.                     |
| HR crew time (`masci_crews[]`)                         | ❌  | Not touched by this track.                                                    |
| Auto-email pipeline                                    | ❌  | Not touched.                                                                  |
| PDF renderer                                           | ❌  | Not touched — canonical + alias routes still declared side-by-side.          |
| ODS V1 ingest                                          | ❌  | Untouched.                                                                    |
| PM / Admin OI dashboards                               | ❌  | Untouched.                                                                    |
| Approved reports list                                  | ❌  | Both canonical + deprecated variants still served.                            |
| AI-CONFIG-001 resolver + env contract                  | ❌  | Untouched.                                                                    |
| AI-ADMIN-001 admin page + endpoints                    | ❌  | Untouched.                                                                    |
| `.env` files                                           | ❌  | Untouched.                                                                    |
| Frontend nav / sidebar / shells                        | ❌  | Untouched.                                                                    |
| `/daily-report/v2` route                               | ✅  | ADDITIVE-BEHAVIOURAL: now a redirect to `/daily/submit`. No product exposed. |
| `AppRoutes.jsx` `DailyReportV2` import                 | ✅  | REMOVED (dead import). Component file remains on disk for tests.             |
| `lib/daily_report_collections.py`                      | ✅  | NEW helper.                                                                   |
| `scripts/migrate_dr_v2_collections_to_daily_report.py` | ✅  | NEW script (dry-run only; no live writes in this track).                     |
| Mongo `dr_v2_*` collections                            | ❌  | Not touched. All 56 docs remain intact.                                       |
| Mongo `daily_report_*` collections                     | ❌  | Empty pre-migration (as expected).                                            |
| `dr_v2_optin` localStorage key                         | ❌  | Left alone (harmless dead entry after redirect).                             |

## Explicit non-changes

- No env var added or removed.
- No dependency added or upgraded.
- No provider adapter modified.
- No auth path modified.
- No user-facing string added or removed on the field form.
- No PM/Admin dashboard column added or removed.
- No collection dropped, renamed, or index rebuilt.

## Deployment risk

- **Config:** none.
- **Data:** none — no writes.
- **Behaviour:** `/daily-report/v2` now instantly redirects to
  `/daily/submit` (previously rendered a hidden shell).
- **Rollback:** revert 3 lines in `AppRoutes.jsx`; delete 2 new
  backend files. Immediate; zero data impact.

## Follow-ups (P1/P2)

- **DR-UNIFY-004 (P1):** run `--live` migration against preview,
  then production. Byte-compare canonical vs. deprecated PDF variants.
- **DR-UNIFY-004 (P1):** move service reads
  (`dr_ai/cache.py`, `photo_intelligence/store.py`,
  `ods_spine/ingest.py`) onto `resolve_read_collection_name`.
- **DR-UNIFY-005 (P2):** drop legacy `dr_v2_*` collections and rename
  backend module filenames.
- **DR-UNIFY-005 (P2):** delete `ExecutiveOperationalIntelligence.jsx`,
  `pages/daily-report-v2/**`, and `lib/dailyReportV2*.js` once no test
  references them.
