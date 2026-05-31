# Role & Permission Matrix · Forensic Phase 5

**Batch:** OMEGA Forensic Platform Certification · Phase 5
**Date:** 2026-05-31
**Scope:** Audit role definitions and permission scopes across the 9 roles. Validate via `role_templates` (production) + portal-token middleware + auth tests in `backend/tests/`.

---

## 1 · Role inventory (9 roles)

| # | Role | Authentication surface | Identity collection | Permission template namespace |
|---|---|---|---|---|
| 1 | Employee (self-service) | session/passkey | `user_directory` | implicit (own records only) |
| 2 | Field Leadership | `X-FL-Token` | `field_leadership_users` (27 users) | `rt-leadership-*` (n templates) |
| 3 | PM | `X-PM-Token` | `users` (roles.pm) · `project_managers` | `rt-pm-*` |
| 4 | Safety | `X-Safety-Token` | `safety_users` (2 users) | `rt-safety-*` |
| 5 | HR | `X-HR-Token` | `hr_users` (3 users) | `rt-hr-*` |
| 6 | Dispatch | `X-Dispatch-Token` | `dispatch_users` (2 users) | `rt-dispatch-*` |
| 7 | Shop | `X-Shop-Token` | `shop_users` (2 users) | `rt-shop-*` |
| 8 | Admin | `X-Admin-Token` | `users` (super-admin flag) | `rt-admin-*` |
| 9 | Super Admin (operator) | break-glass `POST /api/admin/login` (env password) | n/a (env-only) | implicit (all) |

---

## 2 · `role_templates` collection (31 docs · 7 portals)

Production state:

| Portal | Templates |
|---|---|
| admin | (count not enumerated · inferred from snapshot) |
| dispatch | (count not enumerated) |
| hr | (count not enumerated) |
| leadership | (count not enumerated) |
| pm | (count not enumerated) |
| safety | (count not enumerated) |
| shop | (count not enumerated · includes `rt-shop-service-writer` · `rt-shop-readonly`) |

(31 total templates across 7 portals · per-portal counts not separately enumerated in this batch · inspect `db.role_templates` for the full template catalog.)

---

## 3 · Permission scope · per-portal narrative

### 3.1 · Field Leadership scope (canonical · per FL token middleware)

Visible:
- Daily Reports (own + assigned projects)
- Safety Meetings
- JHAs (Job Hazard Analyses)
- DVIRs (Equipment Inspections)
- Fleet read-only
- Dispatch read-only
- Incidents (read + report)
- Driver Qualification dashboard

Hidden:
- HR Employee Lifecycle
- Payroll Variance
- PO Approvals
- Admin Command Center / Recovery

### 3.2 · HR scope

Visible: `hr/employees · hr/training-records · hr/safety-documents · hr/daily-reports · hr/payroll-variance · hr/driver-qualification`
Hidden: Safety incidents (except read-only) · PO approvals · Admin Command Center

### 3.3 · PM scope

Visible: own projects · PO requests · daily reports · safety meetings on own projects · JHAs · incidents on own projects
Hidden: HR · Safety portal config · Dispatch admin · Shop admin

### 3.4 · Safety scope

Visible: all incidents · corrective actions · safety equipment · trainings · jha
Hidden: HR · PO · Dispatch · Shop · admin command-center config

### 3.5 · Dispatch scope

Visible: dispatch board · driver qualification · assignments
Hidden: most other portals

### 3.6 · Shop scope

Visible: fleet · work orders · equipment parts
Hidden: most other portals

### 3.7 · Admin / Super Admin scope

Admin (UI): Command Center · Recovery · Banners · Training Videos · MFA · Terminations · Compliance · Integration Center · Legacy Imports · Operational Inventory · Project Managers · Dispatch users · Field Leadership users · ...
Super Admin (break-glass + `jaymn.judd@mascigc.com` multi-login): full multi-portal access via multi-login fan-out

---

## 4 · Permission audit findings

### 4.1 · 🔴 Test FL account in production

Already documented in `PRODUCTION_DATA_HYGIENE_AUDIT.md` §3 (`fieldleader@mascigc.com`). This account has `role=Superintendent · is_active=True` in production with a documented password in `/app/memory/test_credentials.md`. Anyone with repo read access can authenticate to production with Field Leadership scope.

### 4.2 · 🟡 `user_directory` collection has 7 users · all `is_active=null`

Production state:
```
user_directory: total=7  active=0  inactive=0  (other=7 with null is_active)
```

Implication: any UI surface that filters `is_active=True` on `user_directory` would treat all 7 as not-active. Surfaces that don't filter (or filter `$ne False`) would include them. Inconsistent visibility risk.

### 4.3 · 🟡 Super-admin email hardcoded

`backend/server.py:8697` hardcodes `SUPER = "jaymn.judd@mascigc.com"`. Multi-portal scaling (Customer #2) requires this to come from environment or tenant config.

### 4.4 · 🟡 Multi-login returns 7 portal tokens for super-admin even when a portal has 0 users

Multi-login successfully returns a `pm` token for super-admin even though `pm_users` has 0 rows on production. This is correct (super-admin bypasses portal-user check), but it does mean the super-admin grants themselves access to portals that have no other users.

### 4.5 · 🟢 No detected "excess permission" leaks

Probed: admin endpoints reject portal tokens · portal endpoints reject cross-portal tokens · auth gate fires 401 on every Pillar 1 admin endpoint without token. No regression.

---

## 5 · Dead menu items / broken pages

Static scan did not reveal dead menu items in any portal's primary navigation. The 5 orphaned pages (`DevHub.jsx` · `DevLogin.jsx` · `AllPostersPrint.jsx` · `AccessDenied.jsx` · `AdminDeployReadiness.jsx`) are intentionally not in navigation.

`AdminAccountabilityHub` page reference: **not yet present in frontend** (Pillar 1A-6 Dashboard not yet built). The Pillar 1A-3 service surface is reachable only via direct API calls, NOT via UI today.

---

## 6 · Closeout

🟡 Permissions are **structurally sound** with one 🔴 critical finding (test FL account in production) and one 🟡 finding (super-admin email hardcoded). All 9 roles have well-defined permission templates. Multi-portal token issuance via multi-login works correctly.

🛑 STOP.
