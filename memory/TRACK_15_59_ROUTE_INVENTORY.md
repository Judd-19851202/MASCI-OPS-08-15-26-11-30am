# TRACK 15.59 — Route Inventory (Phase 2)

Browser-driven enumeration of every public login/landing route on production.
Each row was hit by headless Chromium, screenshot taken, HTTP code recorded,
and the rendered DOM scanned for the presence of email + password inputs.

**Source data:** `/app/test_reports/track_15_59_live_prod_verify.json` → `phases.2_routes`

| # | Route | HTTP | Title | Email input | Password input | Login hint text | Screenshot |
|---|-------|------|-------|-------------|----------------|-----------------|------------|
| 1 | `/` | 200 | MASCI Operations Platform | 0 | 0 | yes (home hub) | `phase2_home.png` |
| 2 | `/sign-in` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_sign-in.png` |
| 3 | `/admin/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_admin_login.png` |
| 4 | `/pm/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_pm_login.png` |
| 5 | `/shop/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_shop_login.png` |
| 6 | `/hr/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_hr_login.png` |
| 7 | `/safety-portal/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_safety-portal_login.png` |
| 8 | `/dispatch-portal/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_dispatch-portal_login.png` |
| 9 | `/field-leadership/portal/login` | 200 | MASCI Operations Platform | 1 | 1 | yes | `phase2_field-leadership_portal_login.png` |
| 10 | `/leadership` | 200 | MASCI Operations Platform | 0 | 1 | yes (password gate) | `phase2_leadership.png` |
| 11 | `/safety/forms/login` | 200 | MASCI Operations Platform | 0 | 1 | yes (password gate) | `phase2_safety_forms_login.png` |
| 12 | `/dev/login` | 200 | MASCI Operations Platform | 0 | 1 | yes (password gate) | `phase2_dev_login.png` |

## Interpretation

- **Per-user portals (rows 2–9)** all render the email-+-password form expected by `/api/auth/multi-login` / per-portal `POST /login`. No console errors, no 4xx, no 5xx.
- **Shared-password portals (rows 10–12)** render a single-input password gate. This is by design: `/leadership` uses `LEADERSHIP_PASSWORD`, `/safety/forms/login` uses `SAFETY_FORMS_PASSWORD`, `/dev/login` uses `DEV_PASSWORD`. No email field is expected — proof that the SPA is correctly routing to the legacy gate, not a regressed shared-state component.
- **Home (`/`)** correctly renders the hub tile grid (no login required) and the page contains the words "Sign in" / "Login" in headers/footer copy (`login_hint=true`).

**Result:** 12 / 12 routes return HTTP 200 with the expected login affordance. Phase 2 PASS.
