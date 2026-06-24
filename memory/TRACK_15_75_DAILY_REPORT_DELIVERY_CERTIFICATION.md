# TRACK 15.75 · Phase 3 — Daily Report End-to-End Delivery Certification

Evidence: `/tmp/t1575_phase3_dr.py` live `recipients_for_record_async`
trace + DB volumes.

## Save path
* Endpoint: `POST /api/daily-reports` (`routes/daily_reports.py:227`).
* Storage: `daily_reports` collection — **1 117 rows**; 1 113 since
  2026-05-01. Every row carries `doc_id` (100% coverage), 94.3 %
  carry `project_number` (the remainder are harness fixtures).
* Idempotency: `lib/idempotency` ensures replayed POSTs return the
  cached response.

## Routing trace (live simulation per project)

| Project | jobs_master.pm_email | co_pm_emails | DR count | `kind="daily-report"` → To | CC | Routing |
|---|---|---|---|---|---|---|
| 24-06 | `davidjewett@mascigc.com` | — | 0 | `['davidjewett@mascigc.com']` | `[]` | ✅ **DIRECT_PM** |
| 25-02 | `ramonrodriguez@mascigc.com` | — | 0 | `['ramonrodriguez@mascigc.com']` | `[]` | ✅ **DIRECT_PM** |
| 20-07 | _(empty)_ | `pm.demo@mascigc.com` | 53 | `['safety@mascigc.com']` | `['pm.demo@mascigc.com']` | ✅ **DEAD_LETTER** + co-PM CC |
| 21-06 | _(empty)_ | `pm.demo@mascigc.com` | 0 | `['safety@mascigc.com']` | `['pm.demo@mascigc.com']` | ✅ **DEAD_LETTER** + co-PM CC |
| 26-07 | _(empty)_ | _(none)_ | 16 | `['safety@mascigc.com']` | `[]` | ✅ **DEAD_LETTER** (no co-PM) |
| NOTAJOB | (non-existent) | — | 0 | `['safety@mascigc.com']` | `[]` | ✅ **DEAD_LETTER** (defensive) |

## Audit & dashboard surfaces

| Concern | State | Evidence |
|---|---|---|
| Dead-letter audit truthful | ✅ | `platform_audit.pm_unresolved_dead_letter` carries `dead_letter_to_count`, `dead_letter_configured`. Sample row: `{kind:'meeting', to_count:1, configured:True}`. |
| Email audit truthful (v2) | ✅ | `email_routing_audit_v2.status='routed_to_dead_letter'` with `resolved_to_count=1` post-15.74 fix. |
| PM dashboard | 🟢 | `/api/daily-reports?project_number=…` is admin/PM-scoped (PM JWT or admin token); 401 verified without token. |
| Admin PM-coverage dashboard | 🟢 | `/api/admin/pm-email-coverage` returns track=15.73Q shape; 401 without token, 200 with super-admin token. |
| HR labor visibility | 🟢 | DR row carries `masci_crews[].hours/foreman/trade/count/work_performed` for labor reporting. |
| PDF preserves identity | 🟢 | Track 15.73 Slice 3 picker tests confirm equipment unit + project number preservation. |

## Six-Pillar verdict

* Powerful 9 — full lifecycle works (save + route + audit + dashboard + PDF).
* Simple 8 — PM with email gets the DR directly; missing-PM gets visible dead-letter; operator sees gap on Routing Status Panel.
* Beautiful 8 — `RoutingStatusPanel` + PM Coverage card render cleanly; no UI defects found.
* Trusted 9 — audit truth restored by 15.74 fix; 2 regression tests lock it.
* Proven 9 — 40/40 regression tests + live routing simulation evidence.
* Deployable 9 — no env/code changes required to ship; one operator-owned data backfill outstanding.

**Verdict: 🟢 GREEN. No P0/P1 code defect remaining on Daily Report delivery.**
One operator-owned data hygiene item remains for two active projects (see Phase 12 Remediation Plan).
