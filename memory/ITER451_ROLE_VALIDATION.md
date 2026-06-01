# OMEGA · iter451 · Role Validation Report

**Sprint:** iter451 · OC-001 Incident Lifecycle
**Mode:** Real-user role simulation against the preview build
**Date:** 2026-06-01
**Verdict:** 🟢 **PERMISSIONS ENFORCE CORRECTLY**

---

## 1 · Role mapping (preview build)

| Operator-mandated role | Platform token / surface | Real test identity |
|---|---|---|
| **Safety Manager** | `X-Safety-Token` (Safety Portal · `safety_users.role="Safety Manager"`) | `jaymn.judd@mascigc.com` Safety multi-login token |
| **Superintendent** | Superintendents historically file incidents from the field and review on the **PM portal** (`X-PM-Token`) — the platform does not currently expose a Superintendent-only portal; PM is the closest analog, and it is also the surface used to read incident detail in the field PM workflow. | `jaymn.judd@mascigc.com` PM multi-login token |
| **Super Admin** | `X-Admin-Token` — admin portal token. `is_super_admin(actor)` returns True for admin-portal tokens, and the state-machine normalizer maps Admin → `super_admin` role. | `jaymn.judd@mascigc.com` Admin multi-login token |

**Caveat:** the operator's directive lists "Superintendent" as a distinct role; the current platform's auth tokens are organized by portal (Admin / Safety / PM / HR / Shop / Dispatch / Field-Leadership). Per the iter450 design package and the iter451 directive ("Only Safety Manager, Operations Director, Super Admin may move PENDING_CLOSURE → CLOSED"), **Superintendents are intentionally read-only on incident closure** — they participate by filing the incident (public `POST /api/incidents`) and reviewing the lifecycle state on the detail page. The PM-token simulation in this report exercises the Superintendent's effective permission surface today.

If the operator wants a dedicated Superintendent role with bespoke transition rights, that is a Phase 1B request (role-template extension) and out of iter451 scope.

---

## 2 · Permission matrix — observed vs. expected

Each row is a (from_state, to_state, role) tuple. Result column is the live HTTP response captured during certification.

| # | Role | from_state → to_state | Expected | Observed | Pass |
|---|---|---|---|---|---|
| 1 | Anonymous (no token) | OPEN → UNDER_INVESTIGATION | 401 | 401 `Safety, Admin, or PM login required` | ✅ |
| 2 | Field-Leadership token | OPEN → UNDER_INVESTIGATION | 401 (gate doesn't accept FL token) | 401 | ✅ |
| 3 | **Superintendent (PM token)** | OPEN → UNDER_INVESTIGATION | 403 read-gate accepts, state-machine rejects | 403 `role_not_authorized` | ✅ |
| 4 | **Superintendent (PM token)** | CLOSED → UNDER_INVESTIGATION (reopen) | 403 | 403 `role_not_authorized` | ✅ |
| 5 | **Safety Manager** | OPEN → UNDER_INVESTIGATION | 200 | 200 | ✅ |
| 6 | **Safety Manager** | UNDER_INVESTIGATION → CORRECTIVE_ACTION_REQUIRED | 200 | 200 | ✅ |
| 7 | **Safety Manager** | CORRECTIVE_ACTION_REQUIRED → PENDING_CLOSURE | 200 | 200 | ✅ |
| 8 | **Safety Manager** | PENDING_CLOSURE → CLOSED (3-flag attestation) | 200 | 200 | ✅ |
| 9 | **Safety Manager** | CLOSED → UNDER_INVESTIGATION (reopen with valid reason) | 200 | 200 | ✅ |
| 10 | **Safety Manager** | RECLOSE — PENDING_CLOSURE → CLOSED | 200 | 200 | ✅ |
| 11 | **Super Admin** | OPEN → UNDER_INVESTIGATION (OSHA incident) | 200 | 200 | ✅ |
| 12 | **Super Admin** | PENDING_CLOSURE → CLOSED · without `osha_recordable_ack` | 422 | 422 `closure_attestation_missing:osha_recordable_ack` | ✅ |
| 13 | **Super Admin** | PENDING_CLOSURE → CLOSED · with full OSHA ack | 200 | 200 | ✅ |
| 14 | **Super Admin** | CLOSED → UNDER_INVESTIGATION (OSHA reopen with reason) | 200 | 200 | ✅ |
| 15 | **Super Admin** | RECLOSE OSHA path (PENDING_CLOSURE → CLOSED w/ OSHA ack) | 200 | 200 | ✅ |
| 16 | **Super Admin** | UNDER_INVESTIGATION → CLOSED (illegal skip) | 422 | 422 `transition_not_allowed` | ✅ |

**16 / 16 expectations met.**

---

## 3 · Closure-specific role gate

The closure transition (`PENDING_CLOSURE → CLOSED`) has a tighter role gate than other transitions per the operator directive:

> Only Safety Manager, Operations Director, Super Admin may move PENDING_CLOSURE → CLOSED.

Mapped to today's platform:

| Operator role | Platform role (state-machine normalizer) | Closure allowed? |
|---|---|---|
| Safety Manager | `safety` | ✅ |
| Operations Director | (no dedicated portal today; folded into `super_admin` via Super Admin login or directory `is_super_admin=true`) | ✅ when actor resolves to `super_admin` |
| Super Admin | `super_admin` | ✅ |
| Superintendent | `pm` | ❌ (`closure_role_not_authorized` would fire, but PM is already blocked on the broader `role_not_authorized` check upstream) |
| PM | `pm` | ❌ |
| HR | (no `X-HR-Token` accepted by the read gate) | ❌ at the 401 layer |
| Anonymous / Field reporter | `unknown` | ❌ at the 401 layer |

State-machine reference: `backend/lib/workflow_state_machine.py · INCIDENT_ALLOWED_ROLES`.

---

## 4 · Audit-trail attribution

Every persisted audit row identifies the actor:

* `actor_role` — one of `safety` / `admin` / `super_admin` for the certification run
* `actor_name` — `"Super Admin"` for the Safety multi-login token, `"Admin"` for the Admin token
* `actor_id` — populated when the actor dict carries an email/uuid (Safety user); intentionally empty for Admin-by-password (matches the existing platform pattern in `audit_events` for `incident_deleted`)
* `ip` + `user_agent` — captured on every row

A future enhancement (iter455 or beyond) could enrich the Admin actor_id by attaching the directory-user email after Admin password verification. Today, the `X-Admin-Token` is an HMAC over the shared password and does not carry the operator identity at the route layer.

---

## 5 · Defence-in-depth posture

The role gate is enforced at **three layers**:

1. **HTTP transport gate** — `make_require_safety_admin_or_pm` rejects requests with no recognised token (401).
2. **State-machine validator** — `validate_incident_transition` rejects transitions where the normalized actor role is not in `INCIDENT_ALLOWED_ROLES[(from, to)]` (403).
3. **UI gate** — `IncidentLifecyclePanel.jsx` calls `GET /api/incidents/:id/lifecycle` which returns `legal_next_states[].allowed_for_actor`; buttons are rendered only for `true` entries.

A motivated actor bypassing layer 3 still hits layers 2 and 1.

---

## 6 · Verdict

🟢 **Permissions enforce correctly across all 3 mandated role simulations.**

* Safety Manager — can drive the full lifecycle including reopen and reclose. ✅
* Superintendent (PM) — appropriately read-only on transitions per the iter451 directive. ✅
* Super Admin (Admin) — can drive the full lifecycle including OSHA-recordable closures and break-glass reopen. ✅

No privilege escalation surfaces detected. No role exceeded its authorized transitions.
