# WP16 Navigation Trace Register

Date: 2026-07-29

## Phase 3 status
- Phase 3 remained route-first and read-only.
- Real in-UI traces were added where authentication or nested launches mattered; the broader desktop sweep continued to rely on direct route openings for census breadth.

## Exact current totals
| Metric | Exact total | Note |
| --- | ---: | --- |
| Navigation elements traced from real in-UI launch points | 42 | Phase 1 + Phase 2 traces plus Phase 3 portal sign-in submits and select nested launches. |
| Direct URL evidence openings recorded | 341 | Used to expand desktop route coverage without modifying runtime code. |
| Dead-end screens documented | 18 | Includes blocked auth gates, missing-data placeholders, spent links, and dev/login dead ends. |
| Screens without clear return path documented | 12 | Includes tokenized states, reset screens, and dedicated poster/packet-like flows. |

## Phase 3 representative traces
| Trace ID | Visible label | Source screen | Destination | Result | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| NAV-P3-001 | HR login submit | `/hr/login` | `/hr` | Success into partially degraded HR home | `wp16_p3_hr_login_test.jpeg`, `wp16_p3_hr_auth_001_home.jpeg` | Real in-UI HR authentication trace. |
| NAV-P3-002 | Safety login submit | `/safety-portal/login` | `/safety-portal` / gated safety routes | Success, then secondary workflow auth gates documented | `wp16_p3_safety_006_cards.jpeg`, `wp16_p3_safety_003_forms_home.jpeg` | Distinguished ordinary safety auth from elevated workflow auth. |
| NAV-P3-003 | Shop login submit | `/shop/login` | `/shop` | Success | `wp16_p3_shop_003_home.jpeg` | Shop desktop route family authenticated successfully. |
| NAV-P3-004 | Dispatch login submit | `/dispatch-portal/login` | `/dispatch-portal` | Success into partially degraded home | `wp16_p3_dispatch_004_home_partial.jpeg` | Dispatch auth trace retained known MaintainX defect. |
| NAV-P3-005 | Admin login submit | `/admin/login` | `/admin` | Success | `wp16_p3_admin_001_home.jpeg` | Re-used to capture the admin desktop batch. |
| NAV-P3-006 | PM token-backed route launch | `/pm` family | `/pm/job/:projectNumber/team` | Success | `wp16_p3_pm_auth_007_job_team.jpeg` | Seeded project 24-06 used to verify a parameterized PM detail route. |
