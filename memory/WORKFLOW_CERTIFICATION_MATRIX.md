# Workflow Certification Matrix

**Track:** 14.0-RC1
**Date:** 2026-06-15

## Methodology

Each operational workflow is certified at the **code-contract** level
(its endpoints + collection writes + audit hooks are regression-test
locked) and at the **route-render** level (its portal pages render
under the correct sidebar with the correct role gates). Full UI
end-to-end Create→Edit→Approve→Revise→Close→PDF→Export proof for each
workflow is NOT re-executed in this audit window; that work was
previously certified across Track 13.6 RC1 sweeps (~7411 regression
tests) and Track 14.0-PM-STAFFING-RUNTIME-PROOF (17-role coverage).

## Matrix

| # | Workflow | Portal | Endpoints | Audit | Notifications | Status |
|---|----------|--------|-----------|:-----:|:-------------:|:------:|
| 1 | Daily Reports | PM · Field Leadership | `/api/daily-reports` (POST · GET · GET/{id}) · `/api/daily-reports/{id}.pdf` | ✅ | PM auto-email | ✅ contract |
| 2 | Incidents | Safety · HR · PM | `/api/incidents` | ✅ | Safety + HR + PM | ✅ contract |
| 3 | Safety Meetings | Safety · Field Leadership | `/api/meetings` | ✅ | Safety | ✅ contract |
| 4 | QA/QC Inspections | PM · QA/QC Rep | `/api/qaqc-inspections` | ✅ | PM | ✅ contract |
| 5 | Equipment Pre-Op / DVIR | Shop · Foreman | `/api/equipment-inspections` | ✅ | Shop auto-email on fail | ✅ contract |
| 6 | Asset Transfers | Shop · Dispatch · PM | `/api/asset-transfers` | ✅ | Shop + receiving PM | ✅ contract |
| 7 | HR Time Verification | HR | `/api/hr/time-verification[.csv]` | n/a | n/a | ✅ contract |
| 8 | HR Training Records | HR · Safety | `/api/hr/training-records` · `/api/safety-forms/equipment-trainings` | ✅ | Safety | ✅ contract |
| 9 | PM Staffing Roster | PM · Admin | `/api/admin/jobs/{pn}/team` · `/api/pm/job/{pn}/team` | ✅ | Bell to assignee (NEW this session) | 🟢 PROVEN (17 / 17 roles cert) |
| 10 | Safety Documents | Safety | `/api/safety-documents` | ✅ | Safety digest | ✅ contract |
| 11 | Fire Extinguisher Inspections | Safety | `/api/fire-extinguishers` | ✅ | Safety | ✅ contract |
| 12 | JHA (Job Hazard Analysis) | Safety · PM | `/api/jhas` | ✅ | Safety | ✅ contract |
| 13 | Trench Safety | Safety · Field Leadership · PM | `/api/trench-safety/*` | ✅ | Routed | ✅ contract |
| 14 | Road Plates | Dispatch · Field Leadership | `/api/road-plates` | ✅ | Dispatch | ✅ contract |
| 15 | Dispatch Board | Dispatch | `/api/dispatch/*` · `/api/operations/*` | ✅ | Dispatch | ✅ contract |
| 16 | Driver Qualification | Dispatch · HR | `/api/dispatch/driver-qualification` | ✅ | n/a | ✅ contract |
| 17 | Equipment Master | Shop · Admin | `/api/equipment-units` · `/api/admin/equipment-master/*` | ✅ | n/a | ✅ contract |
| 18 | Field Leadership Forms (10 kinds) | Field Leadership · HR | `/api/leadership/*` · `/api/field-leadership/*` | ✅ | PM + Safety + HR auto-email | ✅ contract |
| 19 | PM Command Center | PM | `/api/pm/command-center/*` | n/a | n/a | ✅ contract |
| 20 | Equipment Issuance + Training (Safety Forms) | Safety | `/api/safety-forms/*` | ✅ | Safety auto-email | ✅ contract |
| 21 | Corrective Actions | Safety · PM | `/api/corrective-actions` | ✅ | Safety + PM | ✅ contract |
| 22 | Project Health (snapshot) | PM | `/api/pm/projects/{pn}/health` | n/a | n/a | ✅ contract |
| 23 | Backups / Restore | Admin | `/api/admin/backup[s]` · `/api/admin/backup/{id}/restore` | ✅ | n/a | 🟡 isolation verified, manual drill recommended |

**23 workflows inventoried. All contracts certified. PM Staffing
workflow PROVEN end-to-end. Remaining 22 rely on previously-passing
regression suites + the deploy-readiness internal check.**
