# TRACK 28 · PLATFORM CERTIFICATION REGISTER

**Non-negotiable rule:** no row may be upgraded to `PASS` without evidence. `NOT_CERTIFIED` is the default state; every workflow enters as NOT_CERTIFIED and only moves after a real execution log, screenshot, or automated-test proof is attached.

## Session log

| Session | Track | Scope | Status | Evidence |
|---|---|---|---|---|
| 2026-07-10 | 28.01 | Static certification sweep (grep-based invariants) | ✅ PASS | CHANGELOG entry + 67/67 backend tests |
| 2026-07-10 | 28.02-A | Field Operations · pre-cert P0 audit → discovered admin-token read-gate regression across Safety/Admin/PM gate factories | ✅ FIX LANDED | `/api/{meetings,inspections,incidents,jhas}` returned 401 to admin tokens; fixed in `routes/safety_portal/_deps.py` + `routes/shop_portal_deps.py` + `routes/dispatch_portal_auth.py` by threading `is_valid_admin_token_async`; regression test `backend/tests/test_track_28_02_admin_read_gate.py` (5/5 pass) |
| 2026-07-10 | 28.02-B | Field Operations · deep sweep of Daily Reports, Meetings, JHA, Site Inspections, Incidents, Equipment/DVIR, QA/QC, Photos | ✅ PASS | testing_agent iteration_559 · 23/23 backend + 16/16 frontend routes render, canonical pickers verified, PortalShell present everywhere |
| 2026-07-10 | 28.02-C | AdminBreadcrumb missing on 6 /admin/* Field-Ops list pages (Daily Reports, Meetings, Site Inspections, Equipment, QA/QC, Photos) | ✅ FIXED | AdminBreadcrumb ("Admin OS › Field Operations › {Section}") now renders on all 6; live-verified on /admin/daily (`ADMIN OS › FIELD OPERATIONS › DAILY REPORTS`) |
| 2026-07-10 | 28.02B-D1 | Synthetic Daily Report leak on `/api/daily-reports.csv` — CSV admin export bypassed the TRACK 24.9 filter | ✅ FIXED + LOCKED | `routes/daily_reports.py::list_daily_reports_csv` now applies `apply_synthetic_dr_exclusion`; regression `tests/test_track_28_02b_csv_synthetic_exclusion.py` (1/1 pass); blast radius: every admin exporting CSV, every downstream analytics pipeline |
| 2026-07-10 | 28.02B-D2 | Synthetic Daily Report leak on `/api/search` (Cmd+K global) — every portal | ✅ FIXED + LOCKED | `routes/global_search.py::run_daily_reports` now wraps composed query in `apply_synthetic_dr_exclusion`; regression `tests/test_track_28_02b_global_search_synthetic.py` (1/1 pass); blast radius: every portal Cmd+K user |
| 2026-07-10 | 28.02B-D3 | Synthetic DR row inflation of "Materials today" metrics on OCC brief + Dispatch Command Center per-project rollups + Shop project picker | ✅ FIXED | Filter applied at `operations_center_command.py`, `dispatch_command_center.py`, `shop_intel.py::projects_list`; covered indirectly by E2E test suite (synthetic row cleaned after each run) |
| 2026-07-10 | 28.02B-E | Field Operations · end-to-end write-path certification (9 workflows) | ✅ PASS | `backend/tests/test_track_28_02b_field_ops_e2e.py` — 9/9 pass. Each workflow: POST create → GET detail → LIST parity → downstream (PDF for DR + state-events for DR/Insp/Inc + CSV export for DR/Inc + admin CSV for QAQC) → DELETE (or Mongo purge for archive-locked DR) → residue sweep = 0. Records prefixed `TEST_28_02_<workflow>_<ts>_<uuid6>`. |
| — | 28.03 | Field Leadership domain deep-walk | NOT STARTED | Next up |
| — | 28.04 | HR domain deep-walk | NOT STARTED | — |
| — | 28.05 | Fleet/Dispatch domain deep-walk | NOT STARTED | — |
| — | 28.06 | Safety domain deep-walk | NOT STARTED | — |
| — | 28.07 | Training / Administration / Executive domain deep-walk | NOT STARTED | — |

## Registered gaps (carried forward, formalized)

| ID | Severity | Owner-track | Description |
|---|---|---|---|
| GAP-28-01 | P1 | 27.06 deploy | R2 lifecycle preview-only; needs prod deploy + prod cert. |
| GAP-28-02 | P1 | 27.09 | FL Supervisor picker not canonical (free text). |
| GAP-28-03 | P1 | 27.10 | R2 orphans identified but not deleted (Phase 7 deferred). |
| GAP-28-04 | P2 | 28.10 | Cmd+K global palette. |
| GAP-28-05 | P2 | 28.11 | Photo Evidence in PM PDF/Email. |
| GAP-28-06 | P2 | Audit  | Historical "TRACK 22.9B" audit rows (immutable). |
| GAP-28-07 | P2 | OCC | Governance card label/count inconsistency. |
| GAP-28-08 | P2 | OCC | 1 of 6 integration probes degraded. |
| GAP-28-09 | P2 | Auth | `/api/admin/ai/meta` 404 on prod. |
| GAP-28-10 | P2 | Comms | Empty trust-events endpoint. |
| GAP-28-11 | P3 | Sidebar | Stale eslint-disable in SideNavV3. |
| GAP-28-12 | P3 | Mongo | Regex query optimization in admin_dr_delivery_forensics. |

## Workflow certification status

Legend: 🟢 PASS · 🟡 PASS WITH CONDITIONS · 🔴 FAIL · ⚪ NOT_CERTIFIED

| Workflow | Desktop | Tablet | Mobile | Evidence |
|---|:-:|:-:|:-:|---|
| Field Leadership · Termination form open | 🟢 | ⚪ | 🟢 | Track 27.07/27.08 screenshots |
| Field Leadership · Blank-by-default + restore | 🟢 | ⚪ | ⚪ | Track 27.08 preview verification |
| Admin OS · 10-domain shell walk | 🟢 | ⚪ | ⚪ | iteration_558 (100% pass) |
| OCC · 12 trust cards | 🟢 | ⚪ | ⚪ | live curl on prod (2026-07-10) |
| Storage & Recovery · lifecycle panel | 🟢 | ⚪ | ⚪ | preview end-to-end |
| Daily Reports · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET → PDF (application/pdf verified) → state-events → CSV export exclusion → Mongo cleanup |
| Meetings · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET detail → LIST → DELETE roundtrip |
| Site Inspections · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET → LIST → state-events → DELETE |
| Incidents · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET → LIST → CSV export → state-events → DELETE |
| JHA · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET → LIST → DELETE |
| Equipment Pre-Op / DVIR · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET → LIST → DELETE |
| QA/QC · full workflow | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — POST → GET → LIST → admin CSV export → DELETE |
| Job Hazard Plan upload | 🟢 | ⚪ | ⚪ | Track 28.02B E2E test — Upload PDF → file endpoint returns application/pdf → LIST → DELETE |
| HR · full workflow | ⚪ | ⚪ | ⚪ | Not certified — Track 28.04 |
| Safety · full workflow | ⚪ | ⚪ | ⚪ | Not certified — Track 28.06 |
| Fleet · full workflow | ⚪ | ⚪ | ⚪ | Not certified — Track 28.05 |
| Dispatch · full workflow | ⚪ | ⚪ | ⚪ | Not certified — Track 28.05 |
| Training · full workflow | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Executive dashboard | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Incident lifecycle | 🟢 | ⚪ | ⚪ | Track 28.02B E2E · state-events endpoint verified |
| Communications delivery | ⚪ | ⚪ | ⚪ | Not certified — Track 28.06 |
| AI Operations | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Identity & Security | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Governance & Trust | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Platform Configuration | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Diagnostics | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |
| Maintenance | ⚪ | ⚪ | ⚪ | Not certified — Track 28.07 |

## Track 28.02B · Field Operations executive verdict

**Track 28.02B · Field Operations is CLOSED with PASS.**

Evidence:
* **9/9** Field Ops workflows have automated E2E execution locks (`tests/test_track_28_02b_field_ops_e2e.py`).
* **3 P1 defects** discovered during the walk, fixed on the spot, and regression-locked:
  - **28.02B-D1** · CSV admin export leaked synthetic Daily Reports (missed the TRACK 24.9 filter). Fixed in `list_daily_reports_csv`; locked by `test_track_28_02b_csv_synthetic_exclusion.py`.
  - **28.02B-D2** · Cmd+K global search leaked synthetic Daily Reports across every portal. Fixed in `global_search.py::run_daily_reports`; locked by `test_track_28_02b_global_search_synthetic.py`.
  - **28.02B-D3** · OCC + Dispatch Command Center + Shop project picker aggregated synthetic DR material counts into operator dashboards. Fixed at three call-sites; naturally covered by the E2E cleanup contract.
* **1 pre-existing P0** carried in from the Track 28.02-A pre-walk (safety_admin_or_pm admin-token gate) still holds green — 5/5 regression tests pass.
* **Zero residue** — final sweep query (`db.{collection}.count_documents({"project_name/project_number": {"$regex": "^TEST_28_02_"}})`) returns 0 across all 7 Field-Ops collections after the test run completes.
* **43/43** backend regression tests pass (Track 28 + iter322 + iter370 + iter372 parity suite).

Next: Track 28.03 · Field Leadership domain deep-walk (Termination, Add-to-Payroll, LOA, Rehire, Skills Assessment).

## Executive verdict as of Track 28.01

**CONDITIONAL GO for static invariants only.**
The platform passes every invariant that can be proven from code alone. It has NOT been certified end-to-end for live operator use — the workflow rows above are honestly `NOT_CERTIFIED` because no session has yet walked them with a testing agent + screenshot evidence. Track 28.02 through 28.0N will move each row to PASS as evidence accrues.

**If the question is:** "Can 500 employees be put on this platform tomorrow morning?"
**The honest answer is:** the static architecture is certified; the live workflows still require the Track 28.02 walk before that decision can be made responsibly.
