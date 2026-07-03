# TRACK 19.29 · PERMISSION / SECURITY CERTIFICATION

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Anchor:** `TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md`

Certifies that every role sees only what it should, cannot access what it shouldn't, and never sees raw 401/403 leakage. Public forms remain public where designed and do not leak private data.

---

## Role / permission matrix

| Role | Public routes | Portal home | Restricted access | Never sees |
|---|---|---|---|---|
| Public / anonymous | `/` · `/safety` · `/field` · `/qaqc` · `/daily/submit` · `/incidents/report` · `/near-miss` · `/meetings/submit` · `/equipment/submit` · `/fleet/dvir/submit` · `/inspections/submit` · `/jha` · `/trench-safety/*` · `/cheatsheet` · `/guidance` · `/transport-invite/:token` · `/transport-verify/:cnum` · `/field/calculators` | `/` (Hub landing) | `/sign-in` shows "Sign in to continue" | HR records · Employee 360 · Safety cases · Admin console · Employee PDFs |
| Field Laborer (public) | Same | Same | — | Same |
| Foreman | Public + `/field-leadership/portal/dashboard` | `/field-leadership` | Field Leadership records | HR PDFs · Admin config |
| Superintendent | + `/leadership/*` | `/leadership` | FL forms + records | HR PII beyond scope |
| PM | + `/pm/*` | `PmHubV2` | PM job dashboards · staffing · POs | HR admin · Safety cases (read-only tiles surface only) |
| Safety Manager | + `/safety-portal/*` · `/safety/*` | `SafetyHubV2` | Case Workspace · Investigation · Executive PDFs | HR admin · Employee salary/discipline unless approved |
| HR | + `/hr/*` | `HrHubV2` | Employee 360 · Historical Records · Compliance Brief · 6 Employee Packages | Safety case internals (read-only summary tiles only) |
| Shop / Mechanic | + `/shop/*` | `ShopHubV2` | Pre-Op · DVIR · Fleet · Fuel/Lube · Recovery · Asset Care | Asset Records section 09 (unless `is_asset_admin=true`) |
| Asset Administrator | Shop + `/hr/historical-records/*` | `ShopHubV2` w/ Section 09 visible | Historical Records intake/queue/batches | Safety cases · HR discipline PDFs |
| Fleet | Same as Shop | `/shop/fleet` | Fleet visibility · DVIR queue | — |
| Dispatch | + `/dispatch-portal/*` · `/transportation-operations/*` | `DispatchHubV2` | Command summary · Motive · Ops attention | HR discipline · Safety case internals |
| Transportation | Same as Dispatch | `TX` gate for `/transportation-operations` | Carrier invites · Certificate verify · Academy admin | — |
| Executive | + `/admin/executive-overview` · `/safety/executive-intelligence` · `/leadership/hub_v2` | Executive read-only surfaces | Cross-portal KPIs | Direct data edits |
| Administrator | + `/admin/*` | `AdminHubV2` (Track 19.28) | Everything (super-admin) | Nothing (with audit trail) |

## Auth token surfaces

| Token key (localStorage) | Owner | Setter |
|---|---|---|
| `masci.admin.token` | Admin | `AdminLogin.jsx` |
| `masci.pm.token` | PM | `PmLogin.jsx` |
| `masci.shop.token` | Shop | `ShopLogin.jsx` |
| `masci.dispatch.token` | Dispatch | `DispatchLogin.jsx` |
| `masci.hr.token` | HR | `HrLogin.jsx` |
| `masci.safety.token` | Safety | `SafetyLogin.jsx` |
| `masci.leadership.token` | Field Leadership | `FieldLeadershipHub` password gate |
| `masci.is_asset_admin` | Directory-mirrored flag | Mirrored by `directoryAuth.js:96-104` on login |
| `masci.tx.token` | Transportation | `TxLogin.jsx` (dispatch-safe TX gate) |

## Backend gate enforcement

- Every `/api/*` endpoint enforces role via header (`X-Admin-Token`, `X-Hr-Token`, `X-Safety-Token`, `X-Shop-Token`, `X-Dispatch-Token`, etc.).
- Multi-portal endpoints accept multiple tokens with capability-scoping (per `constraintCapabilities.js` and `TRACK_19_27_PERMISSION_SECURITY_AUDIT.md`).
- Directory mirror pattern for `is_asset_admin` — 4 auth paths verified in Track 15.13F (admin_token · directory_flag · legacy_shop_role · hr_user).

## Clean restricted-state UI

- No route ever renders a raw 401/403 JSON.
- Restricted portal tiles on `/` show a 🔒 icon + "Sign in to continue" neutral CTA — no telegraphing of internal structure to unauthorized viewers.
- Admin sub-routes wrapped in `A()` guard redirect unauthenticated users to `/admin/login`.
- Portal-specific guards (`P`, `S`, `H`, `SF`, `TX`) mirror the same pattern.
- `SessionStatusOverlay` catches API 401 mid-session · offers "Log Back In" · preserves draft.

## Public-form privacy audit

Public forms accept submissions without exposing internal data:
- ✅ `/daily/submit` — no employee list dropdown pre-populated with all HR data (freeform name entry).
- ✅ `/incidents/report` — no case-workspace preview to anonymous users.
- ✅ `/near-miss` — kiosk mode, no auth, no read-back of prior submissions.
- ✅ `/equipment/submit` — no equipment master pre-populated (asset ID entered by operator).
- ✅ `/meetings/submit` — no roster pre-populated (attendance filled by foreman).
- ✅ `/transport-invite/:token` — token-gated · single-use · does not leak carrier list.
- ✅ `/trench-safety` public dashboard — read-only summary · no PII.

## PDF permission gates

- HR-only PDFs (`/api/hr/employees/{id}/accountability/brief.pdf`, employee packages) — HR + Admin only.
- Safety Case executive PDFs — Safety + Admin only.
- Daily Report PDFs — PM + Safety + Admin + report author's crew supervisor chain.
- Equipment Pre-Op / DVIR PDFs — Shop + Fleet + Admin + submitting operator/driver.
- Field Leadership PDFs — FL-token + Admin.

Each PDF endpoint enforces the same header-gate as its parent HTML surface.

## Track 19.28 delta permission re-verification

- **Shop Hub V2 visibility polish:** Purely cosmetic frontend gate. Backend `is_asset_admin` gate on `/hr/historical-records/*` unchanged — clicking through (if section were shown) would still be backend-blocked. No permission drift.
- **Admin Hub V1 soft-retire:** `/admin` now renders V2 · `/admin/hub_v1` retains V1 · `A()` guard unchanged. No permission drift.
- **AdminSideNavV2 +3 routes:** Routes already existed with backend enforcement (`/admin/command-center`, `/operational-records`, `/admin/project-identity`) — sidebar visibility follows same guard. No permission drift.

## Findings

- No P0 permission defects.
- No P1 permission defects.
- No auth-path drift (verified against Track 15.13F 4-path certification: admin_token · directory_flag · legacy_shop_role · hr_user).

## Verdict

🟢 **GO for pilot rollout.** Permission model is verified end-to-end. Every role has a clean, gate-enforced surface with no raw 401/403 leakage and no cross-role data spillage.
