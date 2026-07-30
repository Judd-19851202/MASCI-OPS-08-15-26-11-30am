# WP16 Wave 1 Inventory & Inspection Baseline

Date: 2026-07-30  
Status: Inspection complete. Evidence collected. No Wave 1 repairs started.

## Scope baseline
- Original Wave 1 register scope inspected: 30 items (`29` active routes + `1` unrouted page file).
- Additional active Wave 1 route discovered during inspection: `/hr/forgot` (redirect-only backstop route present in `AppRoutes.jsx` but missing from the certification register before this pass).
- Final Wave 1 baseline inventory after inspection: `31` items.
- Evidence sources used in this pass:
  - Code review of `AppRoutes.jsx`, Wave 1 page files, and shared auth shells/helpers.
  - Preview curl checks for `/api/auth/multi-login`, `/api/pm/login`, `/api/hr/login`, `/api/safety/login`, `/api/dispatch/login`, `/api/shop/login`, `/api/field-leadership/portal/login`, `/api/safety/forgot-password`, `/api/dispatch/forgot-password`, and `/api/dev/login`.
  - Preview Playwright smoke and focused auth checks on 2026-07-30.

## Route and page inventory

| Surface | Type | Source | Dialogs / primary workflow | Inspection outcome |
| --- | --- | --- | --- | --- |
| `/` | route_screen | `frontend/src/pages/Hub.jsx` | Public hub navigation + company information dialog | Inspected. No new Wave 1 defect opened. |
| `/sign-in` | route_screen | `frontend/src/pages/SignIn.jsx` | Multi-portal directory sign-in (`/api/auth/multi-login`) | Inspected. No new Wave 1 defect opened. |
| `/change-password` | route_screen | `frontend/src/pages/DirectoryChangePassword.jsx` | Shared directory password rotation workflow | **Defect open:** auth-shell visual / operational drift (`WP16-W1-001`). |
| `/access-denied` | route_screen | `frontend/src/pages/AccessDenied.jsx` | Recovery / route-back workflow | Inspected. No new Wave 1 defect opened. |
| `/legal/terms` | route_screen | `frontend/src/pages/legal/TermsOfService.jsx` | Public legal read-only workflow | Inspected. No new Wave 1 defect opened. |
| `/legal/privacy` | route_screen | `frontend/src/pages/legal/PrivacyPolicy.jsx` | Public legal read-only workflow | Inspected. No new Wave 1 defect opened. |
| `/admin/login` | route_screen | `frontend/src/pages/AdminLogin.jsx` | Admin sign-in workflow | **Defect open:** stale `/admin/hub` redirect target (`WP16-W1-008`). |
| `/pm/login` | route_screen | `frontend/src/pages/PmLogin.jsx` | PM sign-in + inline forgot-password dialog | Inspected. No new Wave 1 defect opened. |
| `/pm/reset/:token` | route_screen | `frontend/src/pages/PmResetPassword.jsx` | PM reset-password workflow | Form render inspected; no live token exercise in this pass. |
| `/pm/change-password` | route_screen | `frontend/src/pages/PmChangePassword.jsx` | PM authenticated password-change workflow | Inspected with authenticated preview token. No new defect opened. |
| `/hr/login` | route_screen | `frontend/src/pages/HrLogin.jsx` | HR sign-in + inline forgot-password dialog | Inspected. No new Wave 1 defect opened. |
| `/hr/forgot` | redirect_route | `frontend/src/pages/HrForgotPassword.jsx` | Legacy bookmark backstop redirect to `/hr/login` | **Register gap discovered:** route added to baseline; control defect `WP16-W1-009`. |
| `/hr/reset/:token` | route_screen | `frontend/src/pages/HrResetPassword.jsx` | HR reset-password workflow | Form render inspected; no live token exercise in this pass. |
| `/hr/change-password` | route_screen | `frontend/src/pages/HrChangePassword.jsx` | HR authenticated password-change workflow | Inspected with authenticated preview token. No new defect opened. |
| `/safety/forms/login` | route_screen | `frontend/src/pages/SafetyFormsLogin.jsx` | Legacy Safety Forms password gate | **Defect open:** remembered-session token cleared on mount (`WP16-W1-003`). |
| `/safety-portal/login` | route_screen | `frontend/src/pages/SafetyLogin.jsx` | Safety portal sign-in workflow | Inspected. No new Wave 1 defect opened. |
| `/safety-portal/forgot-password` | route_screen | `frontend/src/pages/SafetyForgotPassword.jsx` | Safety forgot-password workflow | **Defect open:** `token_for_dev` exposed in UI (`WP16-W1-004`). |
| `/safety-portal/reset/:token` | route_screen | `frontend/src/pages/SafetyResetPassword.jsx` | Safety reset-password workflow | Form render inspected; no live token exercise in this pass. |
| `/safety-portal/change-password` | route_screen | `frontend/src/pages/SafetyChangePassword.jsx` | Safety authenticated password-change workflow | Inspected with authenticated preview token. No new defect opened. |
| `/dispatch-portal/login` | route_screen | `frontend/src/pages/DispatchLogin.jsx` | Dispatch sign-in workflow | Inspected. No new Wave 1 defect opened. |
| `/dispatch-portal/forgot-password` | route_screen | `frontend/src/pages/DispatchForgotPassword.jsx` | Dispatch forgot-password workflow | **Defect open:** `token_for_dev` exposed in UI (`WP16-W1-005`). |
| `/dispatch-portal/reset/:token` | route_screen | `frontend/src/pages/DispatchResetPassword.jsx` | Dispatch reset-password workflow | Form render inspected; no live token exercise in this pass. |
| `/dispatch-portal/change-password` | route_screen | `frontend/src/pages/DispatchChangePassword.jsx` | Dispatch authenticated password-change workflow | Inspected with authenticated preview token. No new defect opened. |
| `/shop/login` | route_screen | `frontend/src/pages/ShopLogin.jsx` | Shop sign-in + inline forgot-password dialog | Inspected. No new Wave 1 defect opened. |
| `/shop/reset/:token` | route_screen | `frontend/src/pages/ShopResetPassword.jsx` | Shop reset-password workflow | Form render inspected; no live token exercise in this pass. |
| `/shop/change-password` | route_screen | `frontend/src/pages/ShopChangePassword.jsx` | Shop authenticated password-change workflow | Inspected with authenticated preview token. No new defect opened. |
| `/field-leadership/portal/login` | route_screen | `frontend/src/pages/FieldLeadershipPortalLogin.jsx` | Field Leadership portal sign-in + inline forgot-password dialog | **Defect open:** failed login attempt clears existing admin session (`WP16-W1-006`). |
| `/field-leadership/portal/change-password` | route_screen | `frontend/src/pages/FieldLeadershipPortalChangePassword.jsx` | Field Leadership authenticated password-change workflow | **Defect open:** auth-shell visual / operational drift (`WP16-W1-002`). |
| `/leadership/login` | route_screen | `frontend/src/pages/FieldLeadershipPortalLogin.jsx` | Canonical leadership sign-in route using shared FL login component | **Defect open:** failed login attempt clears existing admin session (`WP16-W1-006`). |
| `/dev/login` | route_screen | `frontend/src/pages/DevLogin.jsx` | Vendor / developer portal sign-in | **Defect open:** preview backend intentionally fail-closes endpoint; route not operationally certifiable (`WP16-W1-007`). |
| `frontend/src/pages/LeadershipLogin.jsx` | page_file_only | `frontend/src/pages/LeadershipLogin.jsx` | Legacy unrouted login page file | Inspected as legacy/unrouted file only. No runtime repair opened. |

## Dialog inventory inside Wave 1 surfaces

| Dialog / embedded recovery surface | Parent surface | Current role in workflow | Inspection note |
| --- | --- | --- | --- |
| `CompanyInfoDialog` | `/` (`Hub.jsx`) | Public company-information overlay | Inventoried. No defect opened during this pass. |
| PM forgot-password dialog | `/pm/login` | Inline recovery path replacing separate PM forgot route | Inventoried. No defect opened during this pass. |
| HR forgot-password dialog | `/hr/login` | Inline recovery path; `/hr/forgot` now acts only as legacy redirect backstop | Inventoried. Register gap logged because `/hr/forgot` was missing from the ledger. |
| Shop forgot-password dialog | `/shop/login` | Inline recovery path | Inventoried. No defect opened during this pass. |
| Field Leadership forgot-password dialog | `/field-leadership/portal/login` and `/leadership/login` | Inline recovery path | Inventoried. Parent page has open cross-session defect `WP16-W1-006`. |

## Primary workflow inventory

| Workflow | Surfaces involved | Inspection outcome |
| --- | --- | --- |
| Public hub navigation | `/`, `/legal/terms`, `/legal/privacy` | Completed. No new defect opened. |
| Directory multi-login | `/sign-in` → `/api/auth/multi-login` | Completed in preview. No new defect opened on the page itself. |
| Shared directory password rotation | `/change-password` | Defect open (`WP16-W1-001`). |
| Access-denied recovery | `/access-denied` | Completed. No new defect opened. |
| Admin login | `/admin/login` → `/api/auth/login` / existing-session redirect | Latent redirect defect open (`WP16-W1-008`). |
| PM auth lifecycle | `/pm/login`, inline PM forgot dialog, `/pm/reset/:token`, `/pm/change-password` | Login and authenticated change-password verified; reset route inspected at form-render level. |
| HR auth lifecycle | `/hr/login`, inline HR forgot dialog, `/hr/forgot`, `/hr/reset/:token`, `/hr/change-password` | Login and authenticated change-password verified; redirect backstop gap logged; reset route inspected at form-render level. |
| Safety Forms gate | `/safety/forms/login` | Defect open (`WP16-W1-003`). |
| Safety auth lifecycle | `/safety-portal/login`, `/safety-portal/forgot-password`, `/safety-portal/reset/:token`, `/safety-portal/change-password` | Login and authenticated change-password verified; forgot flow defect open; reset route inspected at form-render level. |
| Dispatch auth lifecycle | `/dispatch-portal/login`, `/dispatch-portal/forgot-password`, `/dispatch-portal/reset/:token`, `/dispatch-portal/change-password` | Login and authenticated change-password verified; forgot flow defect open; reset route inspected at form-render level. |
| Shop auth lifecycle | `/shop/login`, inline Shop forgot dialog, `/shop/reset/:token`, `/shop/change-password` | Login and authenticated change-password verified; reset route inspected at form-render level. |
| Field Leadership auth lifecycle | `/field-leadership/portal/login`, `/leadership/login`, inline FL forgot dialog, `/field-leadership/portal/change-password` | Login session-continuity defect open; change-password shell drift defect open. |
| Developer portal login | `/dev/login` → `/api/dev/login` | Preview route present, endpoint intentionally fail-closed; operational defect / certification blocker open. |

## Inspection conclusion
- Wave 1 inventory baseline is now complete enough for review.
- Wave 1 is **not certified**.
- No repairs were started in this pass.
- See `WP16_LIVE_PUNCH_LIST.md` for the authoritative open-defect ledger and `WP16_CERTIFICATION_REGISTER.csv` for per-surface current status.