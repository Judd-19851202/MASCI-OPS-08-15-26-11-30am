# RBAC BOUNDARY CERTIFICATION

_Phase V-Prelude · Deployment Readiness · Track 5 · 2026-05-29T00:22Z_

Human-readable permission matrix across all live roles. Source-traced
from `backend/server.py` route dependencies, per-route module
`require_*` shims, and the Phase K (iter172–180) hardening that gave
each portal a dedicated bcrypt-bound token type with strict
namespace lockdown.

---

## 1 · Live token types (8 total)

| # | Token header | Role | Auth file | Storage (frontend) |
|---|---|---|---|---|
| 1 | `X-Admin-Token` | Admin (single-tenant) | `auth.py` · `mfa.py` · `admin_hardening.py` | `localStorage.masci.admin.token` |
| 2 | `X-Directory-Token` | Super-admin namespace (MFA / passkeys / directory mutations) | `auth.py` · `passkey_session_mint.py` | mint-on-demand · short-lived |
| 3 | `X-PM-Token` | Project Manager (per-user) | `routes/pm_routes.py` · `routes/pm_admin.py` | `localStorage.masci.pm.token` |
| 4 | `X-HR-Token` | HR (per-user) | `routes/hr_portal.py` · `hr_users.py` | `localStorage.masci.hr.token` |
| 5 | `X-Safety-Token` | Safety (per-user) | `routes/safety_portal/auth_users.py` · `routes/safety_portal/*` | `localStorage.masci.safety.token` |
| 6 | `X-Dispatch-Token` | Dispatch (per-user) | `routes/dispatch_portal_auth.py` · `routes/dispatch_*` | `localStorage.masci.dispatch.token` |
| 7 | `X-FL-Token` | Field Leadership (per-user, bounded ops visibility) | `routes/field_leadership_portal.py` | `localStorage.masci.fl.token` |
| 8 | `X-Shop-Token` | Shop portal | `routes/shop_portal_deps.py` · `routes/shop_parts.py` | `localStorage.masci.shop.token` |

Token-stripped public surfaces (intentional, gated by anti-CSRF + rate-
limiters):

- `/api/auth/login` (every portal has its own `…/login`)
- `/api/draft-telemetry/*` (TF-018 visibility-of-visibility — admin-token-only on writes; public health endpoint)
- `/api/version` · `/api/health/*` (telemetry)
- `/api/auth/mfa/verify-login` (public, single-use TOTP verify)

---

## 2 · Capability matrix (read access)

Legend: ✅ full · 🔒 own-scope · 🔍 read-only · — denied · 🌐 anonymous OK

| Capability domain | Admin | PM | HR | Safety | Dispatch | FieldLead | Driver¹ |
|---|---|---|---|---|---|---|---|
| Admin console (`/api/admin/*`) | ✅ | — | — | — | — | — | — |
| User directory read | ✅ | — | 🔒 own | — | — | — | — |
| User directory mutate | ✅ (super-admin) | — | 🔒 own | — | — | — | — |
| PM projects | ✅ | ✅ | 🔍 | 🔍 | 🔍 | 🔍 own-crew | — |
| PM constraints (Wave 1) | ✅ | ✅ | — | 🔍 | 🔍 | 🔍 | — |
| PM links (Wave 1) | ✅ | ✅ | — | 🔍 | 🔍 | 🔍 | — |
| PM timeline (Wave 1.1 sidecar) | ✅ | ✅ | 🔍 | 🔍 | 🔍 | 🔍 | — |
| PM photo governance (Wave 1) | ✅ | ✅ | — | 🔍 | — | 🔍 own | — |
| HR employees | ✅ | 🔍 own-crew | ✅ | 🔍 | 🔍 driver-quals | 🔍 own-crew | — |
| HR time-off | ✅ | — | ✅ | — | — | 🔒 own | — |
| HR driver-qualification | ✅ | — | ✅ | — | 🔍 | 🔍 own-crew | 🔒 own |
| HR payroll variance | ✅ | — | ✅ | — | — | — | — |
| Safety incidents | ✅ | 🔍 own-projects | 🔍 | ✅ | 🔍 | 🔍 own-crew | — |
| Safety CAPAs | ✅ | 🔍 own | — | ✅ | — | 🔍 own | — |
| Safety forms | ✅ | 🔍 own | — | ✅ | — | 🔍 own | — |
| Dispatch board | ✅ | — | — | — | ✅ | 🔍 today/tomorrow | — |
| Dispatch driver assignments | ✅ | — | — | — | ✅ | 🔍 | 🔒 own |
| Daily Reports | ✅ | 🔍 own-projects | 🔍 | 🔍 | 🔍 | ✅ author | — |
| JHAs / Pre-Ops / DVIRs | ✅ | 🔍 | 🔍 | 🔍 | 🔍 | ✅ author | 🔒 own |
| Field Memory (read) | ✅ | ✅ | 🔍 | 🔍 | 🔍 | 🔍 | — |
| Governance probes / health | ✅ | — | — | — | — | — | — |
| Trust surfaces / self-protection page | ✅ | — | — | — | — | — | — |
| Observation Ledger | ✅ (operator file) | — | — | — | — | — | — |
| Backup / restore drill | ✅ (super-admin) | — | — | — | — | — | — |

¹ "Driver" is a Driver-Sessions token via magic-link auth (`driver_sessions.py`), not a full portal token. It only authorizes a narrow set of own-record reads + signature/return actions.

---

## 3 · Boundary enforcement gates (live in CI)

| Gate | Probe / test | Status |
|---|---|---|
| Admin namespace lockdown | `test_iter179_admin_access_control_gate.py` (35 tests) | ✅ |
| PM-token must not call `/api/admin/*` | `test_iter180_pm_token_admin_namespace_lockdown.py` (37 tests) | ✅ |
| Portal-token routing audit (no `/api/admin/*` from any non-admin) | `tests/pw_suite/test_portal_token_routing.py` (Playwright) | ✅ |
| Phase K1 — identity mirror | `test_iter172_phase_k1_identity_mirror.py` | ✅ |
| Phase K2 — RBAC service | `test_iter174_phase_k2_rbac_service.py` | ✅ |
| Phase K3 — role templates | `test_iter175_phase_k3_role_templates.py` | ✅ |
| Phase K4a — directory read | `test_iter176_phase_k4a_directory_read.py` | ✅ |
| Phase K4b — directory mutations | `test_iter177_phase_k4b_directory_mutations.py` | ✅ |
| Authority mismatch probe (frontend rendering coexistence) | `authority_mismatch_probe.py --gate` | ✅ 0 new viol |
| Magic-link hardening (iter437) | `test_iter437_magic_link_hardening.py` | ✅ |
| Sigma-III regression contract | `tests/regression/test_critical_flows.py` (53 tests) | ✅ |

All gates green in today's stability sweep.

---

## 4 · Exposure risks

| Risk class | Status | Mitigation |
|---|---|---|
| Token leakage from non-admin portal to `/api/admin/*` | 🟢 ZERO | iter179 + iter180 + Playwright `test_portal_token_routing.py` |
| Portal token reuse across portals (e.g., PM ⇌ HR) | 🟢 ZERO | Each token is bcrypt-bound to a per-user record; cross-portal tokens are rejected by `require_*` shims |
| Anonymous access to operator surfaces | 🟢 ZERO | Every `/api/<portal>/*` non-login route declares `Depends(require_<portal>_token)` |
| Super-admin MFA bypass | 🟢 ZERO | `MFA_ENCRYPTION_KEY` required at startup; `auth/mfa/verify-login` returns `X-Directory-Token` only after TOTP |
| Driver-session escalation | 🟢 ZERO | Driver sessions cannot satisfy any `require_*` shim except their own bounded read endpoints |
| Field-Leadership token satisfying HR/Admin/payroll | 🟢 ZERO | iter314: FL token strictly rejected by HR / Admin / payroll / system gates |
| Cross-tenant leakage | n/a — single-tenant deployment | n/a |

---

## 5 · Ambiguity / undocumented access

After this sweep, **no undocumented access paths were found.**
Every route in `backend/routes/` declares its `require_*` dependency
explicitly. Every login-token mint goes through `auth.py` or a
per-portal `*_auth.py` shim.

One **clarifying note** worth recording (not a finding):

- `/api/auth/mfa/verify-login` is intentionally **public** (no token
  required). It returns a short-lived `X-Directory-Token` only after
  a successful TOTP verification of an already-authenticated admin
  session. The endpoint cannot be used as an unauthenticated escalation
  path because it requires a one-time TOTP code generated from a
  Fernet-encrypted secret bound to a known super-admin row.

---

## 6 · Session timeout matrix (defense-in-depth)

| Tier | Roles | Idle min | Absolute h |
|---|---|---|---|
| `ADMIN_HR` | Admin · HR | 15 | 4 |
| `OPERATIONS` | PM · Safety · Dispatch · Shop | 30 | 8 |
| `FIELD` | Field-Leadership · Driver | 60 | 12 |

Enforced by `test_iter186b_session_timeout_middleware.py`. ✅

---

## 7 · Verdict

**RBAC BOUNDARY: ✅ PASS.**

- 8 token types, 7 RBAC tiers, 0 cross-tier leak paths.
- 11 CI gates green (35 + 37 + Playwright + 5 Phase K suites + auth
  probes + magic-link hardening + Sigma-III regression).
- Authority mismatch probe reports 0 new violations.
- Session timeout middleware enforced and tested.
- No undocumented access surface remains.

Track 5 of 8 · ✅ pass.
