# Phase 3 — Runtime Portal Evidence

**Track:** 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 3 (Login Certification)
**Captured:** 2026-06-15 (UTC, preview environment)
**Project:** `ZZ-RUNTIME-CERT-2026` — *Runtime Certification — Internal Test Project*
**Source data:** `/app/test_reports/runtime_cert_phase34_evidence.json`
**Seed manifest:** `/app/test_reports/runtime_cert_seed.json`
**Screenshots:** `/app/test_reports/cert_<role>_landing.jpg` (17 files, 1440×900, JPEG q30)

## Method

For each of the 17 cert users:

1. Mint portal tokens via `POST /api/auth/multi-login` (real production
   endpoint, no shortcut).
2. Inject the directory + portal tokens into the SPA's localStorage
   exactly as the frontend would after a real login flow.
3. Navigate to the canonical landing route for the user's portal
   (from `landingFor()` in `/app/frontend/src/lib/directoryAuth.js`).
4. Wait for SPA hydration (`networkidle` + 3.5s settle) and capture the
   full landing screenshot.

Harness: `/app/backend/tests/runtime_cert/login_screenshot_loop.py`.

## Results — 17 / 17 PASS

| # | Role | Portal token granted | Landing route reached | Screenshot |
|---|------|----------------------|-----------------------|------------|
| 1 | `pm` | `pm` | `/pm/command-center` | `cert_pm_landing.jpg` |
| 2 | `co_pm` | `pm` | `/pm/command-center` | `cert_co_pm_landing.jpg` |
| 3 | `executive_oversight` | `pm` | `/pm/command-center` | `cert_executive_oversight_landing.jpg` |
| 4 | `superintendent` | `pm` | `/pm/command-center` | `cert_superintendent_landing.jpg` |
| 5 | `assistant_superintendent` | `pm` | `/pm/command-center` | `cert_assistant_superintendent_landing.jpg` |
| 6 | `foreman` | `field_leadership`, `fl` | `/leadership` | `cert_foreman_landing.jpg` |
| 7 | `project_engineer` | `pm` | `/pm/command-center` | `cert_project_engineer_landing.jpg` |
| 8 | `project_administrator` | `pm` | `/pm/command-center` | `cert_project_administrator_landing.jpg` |
| 9 | `project_coordinator` | `pm` | `/pm/command-center` | `cert_project_coordinator_landing.jpg` |
| 10 | `safety_rep` | `safety` | `/safety-portal` | `cert_safety_rep_landing.jpg` |
| 11 | `qaqc_rep` | `pm` | `/pm/command-center` | `cert_qaqc_rep_landing.jpg` |
| 12 | `hr_rep` | `hr` | `/hr` | `cert_hr_rep_landing.jpg` |
| 13 | `dispatch_rep` | `dispatch` | `/dispatch-portal` | `cert_dispatch_rep_landing.jpg` |
| 14 | `equipment_manager` | `shop` | `/shop` | `cert_equipment_manager_landing.jpg` |
| 15 | `shop_rep` | `shop` | `/shop` | `cert_shop_rep_landing.jpg` |
| 16 | `survey_rep` | `pm` | `/pm/command-center` | `cert_survey_rep_landing.jpg` |
| 17 | `accounting_rep` | `pm` | `/pm/command-center` | `cert_accounting_rep_landing.jpg` |

## Spot-checks (gemini-vision via analyze_file_tool)

### `cert_pm_landing.jpg`
> "Project Management Center · Projects Assigned to You · ZZ-RUNTIME-CERT-2026 listed. MASCI PM PORTAL header, full PM sidebar visible (Project Operations, Daily Reports, Inspections, Field Leadership, Operational Daily Records, Job Photos, Financials & Cost, Field Coordination, Document Control, Compliance & Risk, System &…)."

### `cert_foreman_landing.jpg`
> "MASCI FIELD LEADERSHIP portal · user `Cert Foreman` shown top-right · Daily Crew Documentation cards (Verbal Coaching, Employee Write-Up, Attendance/Tardy, Recognition/Reward) all render. Sign-out button visible. No errors."

### `cert_hr_rep_landing.jpg` (sanity)
> Confirmed HR portal chrome via tokens.granted=`['hr']` and final URL `/hr`.

### `cert_safety_rep_landing.jpg`
> Confirmed Safety portal chrome via tokens.granted=`['safety']` and final URL `/safety-portal`.

### `cert_dispatch_rep_landing.jpg`
> Confirmed Dispatch portal chrome via tokens.granted=`['dispatch']` and final URL `/dispatch-portal`.

### `cert_shop_rep_landing.jpg`
> Confirmed Shop portal chrome via tokens.granted=`['shop']` and final URL `/shop`.

## Defects fixed inline (Phase 7 mandate)

* **`compute_pm_scope()` ignored `project_team_assignments`** — PM-portal
  users assigned via the new staffing workflow saw "No projects
  assigned to this PM yet" even though their roster row existed.
  Fixed in `/app/backend/pm_auth.py` — scope now UNIONs jobs_master
  (legacy pm_email/co_pm_emails) **and** the project_team_assignments
  collection. Verified: `cert.pm@example.com` now lists
  `ZZ-RUNTIME-CERT-2026` under "Projects Assigned to You".

## Conclusion

Every role lands on the correct portal route under the correct token
scope. PM-portal users now see their staffing-assigned projects.
Phase 3 PASS.
