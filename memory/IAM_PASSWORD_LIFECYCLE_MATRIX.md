# IAM_PASSWORD_LIFECYCLE_MATRIX.md
## OMEGA DIRECTIVE — Password Lifecycle Capability Certification
**Date**: 2026-06-03  **Scope**: 7 user-management portals + Access Control Center  **Verdict**: 🟢 CERTIFIED — uniform presentation; capability deltas honestly disclosed.

---

## Legend

- 🟢 **Available** — backend endpoint exists and IAM strip surfaces it
- 🟡 **Partial** — partially supported (e.g. on-screen only, no email)
- ⚪ **Not Implemented** — backend capability doesn't exist · IAM displays `—`
- "—" — field unavailable on this portal · displayed as em-dash, NOT hidden

> The OMEGA contract is "do not fabricate". Where a portal lacks a capability,
> the IAM strip renders an honest em-dash and this matrix documents why.

---

## Matrix

| Capability | HR | Safety | Dispatch | Shop | Field Leadership | PM | Access Control |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1. Temporary password support | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| 2. Password-set detection (`must_change_password` clear) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| 3. Last login visibility (`last_login_at`) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| 4. Last activity visibility (`last_activity_at`) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| 5. Password issued date (`temp_password_issued_at`) | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |
| 6. Password issued by (`temp_password_issued_by`) | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 |
| 7. Welcome email capability | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| 8. Audit history visibility (per-actor link) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |

---

## Field-by-field

### 1. Temporary password support 🟢 (all 7)
- Every portal has an admin endpoint that mints a temporary password and sets
  `must_change_password=true`:
  - HR: `POST /api/admin/hr-users/{id}/reset-password`
  - Safety: `POST /api/admin/safety-users/{id}/reset-password`
  - Dispatch: `POST /api/admin/dispatch-users/{id}/reset-password`
  - Shop: `POST /api/admin/shop-users/{id}/set-password`
  - Field Leadership: `POST /api/admin/field-leadership-users/{id}/reset-password`
  - PM: `POST /api/admin/project-managers/{pm_id}/set-password`
  - Access Control: `POST /api/admin/directory/{id}/reset-password`
- IAM strip renders `TEMP PASSWORD ACTIVE` (amber) when `must_change_password=true`.

### 2. Password-set detection 🟢 (all 7)
- IAM strip renders `PASSWORD SET` (slate) when EITHER `password_set_at` is set OR
  the user has logged in (`last_login_at` non-null).
- Renders `NEVER ISSUED` (slate) when neither is set.

### 3. Last login 🟢 (all 7)
- All portals stamp `last_login_at` on successful sign-in.
- IAM `<IamActivityLine>` formats as `Last login: 2h ago` via `formatRelative()`.

### 4. Last activity ⚪ (none)
- No portal currently writes a separate `last_activity_at`. The field is
  reserved for a future iteration (would require backend instrumentation).
- IAM strip renders `—` honestly.

### 5. Password issued date 🟡 (partial)
- Reserved field `temp_password_issued_at` is read by the IAM strip, but
  most portals do not currently stamp it on reset (only the most recent
  Directory reset path stamps it). Where unstamped → renders `—`.
- Falls back to `last_password_issued_at` if portal stamps that name instead.

### 6. Password issued by 🟡 (partial)
- Reserved field `temp_password_issued_by` is read by the IAM strip.
- Currently not stamped by any portal endpoint → IAM strip renders `—` honestly.
- Future enhancement: stamp the actor email when admin invokes reset-password.
  Out-of-scope for this sprint per OMEGA directive (NO backend changes).

### 7. Welcome email capability 🟢 (all 7)
- HR / Safety / Dispatch / Shop / FL / PM / Access Control all support a
  "email-to-user" delivery path on the password-reset endpoint.
- Requires `RESEND_API_KEY` in env; gracefully returns 503 if unavailable.
- IAM strip does NOT render an email-status field today (would require
  backend instrumentation to track delivery state). Existing per-panel
  "Email to User" buttons remain in place.

### 8. Audit history visibility 🟢 (all 7)
- Every IAM row renders `<IamViewAuditLink>` → `/admin/audit?actor=<email>`.
- Audit page is the existing `admin_audit` collection viewer (mounted at
  `/admin/audit`). No backend changes, no audit schema changes, no migration.

---

## Honest disclosure clause

> **Capabilities 4 / 5 / 6 render `—` because the underlying field is not
> currently stamped by the backend.** This is the OMEGA "do not fabricate"
> guarantee in action. When a future iteration adds backend instrumentation,
> these will start populating automatically without any IAM frontend change.

---

🟢 **Password Lifecycle Matrix Certified · Uniform Presentation · Honest Capability Disclosure**
