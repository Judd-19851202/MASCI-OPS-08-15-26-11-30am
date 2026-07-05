# DR-UNIFY-004 · Zero-Drift Certification

**Claim:** No user-visible change to any workflow from last week's production, except the two additive surfaces (Daily Operational Summary section + Admin AI Configuration page).

## Preserved surfaces (unchanged)

| Surface                                      | State  |
| -------------------------------------------- | :----: |
| `/daily/submit` (canonical field form)       | ✅ same |
| `POST /api/daily-reports` (V1 submit)        | ✅ same |
| `GET /api/daily-reports/approved`            | ✅ same |
| `GET /api/daily-reports/{id}/pdf`            | ✅ same |
| PM Operational Intelligence dashboard        | ✅ same |
| Admin Operational Intelligence dashboard     | ✅ same |
| HR crew-time export (`masci_crews[]` reads)  | ✅ same |
| Auto-email pipeline (`schedule_auto_email`)  | ✅ same |
| PDF renderer (`dr_v2_pdf.py`)                | ✅ same |
| ODS V1 ingest hook                           | ✅ same |
| ODS `operational_facts` schema               | ✅ same |
| Photo upload flow + min-6 rule               | ✅ same |
| Safety fields, incident/injury/JHA/JHP gates | ✅ same |
| Excavation gate                              | ✅ same |
| Equipment rows + operator hours              | ✅ same |
| Signature capture                            | ✅ same |
| Autosave / draft recovery                    | ✅ same |
| EN/ES language toggle                        | ✅ same |
| AI-CONFIG-001 resolver + env contract        | ✅ same |
| Deprecated `/api/dr-v2/*` route aliases      | ✅ still served (locked) |
| Frontend admin nav / sidebar                 | ✅ same + one entry |
| Field / PM / Shop / HR / Safety / Dispatch navs | ✅ same |
| Mongo `daily_reports` collection             | ✅ same schema (+ optional summary fields) |
| Mongo `operational_facts` collection         | ✅ same schema (+ optional intelligence_fact) |
| Legacy `dr_v2_*` collections                 | ✅ untouched (56/69 docs preserved) |

## Additive-only changes

- **`/admin/ai-configuration`** — new admin page. Not in any user nav.
- **Daily Operational Summary section** — inside the existing form,
  optional, non-blocking. Never shown differently from other sections.
- **Route aliases** locked (canonical + deprecated coexist).
- **`/daily-report/v2`** now redirects to `/daily/submit` (was a
  hidden shell before).

## Evidence

- `test_dr_unify_003_consolidation.py` — 19/19 locks pass.
- `test_dr_cutover_002_daily_summary.py` — 22/22 locks pass.
- Live smoke: every canonical route responds; every deprecated alias
  still responds; migration script dry-run reports 0 collisions.
- Testing agent iteration_532: 12/12 CERT items pass across roles.

**Verdict:** ZERO DRIFT.
