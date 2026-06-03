# FORGEDOPS IAM SPRINT · 1 · GAP ANALYSIS
## OMEGA P0 · Read-only audit · No implementation

**Date**: 2026-06-03
**Scope**: All 7 portal-user management surfaces + their backend endpoints + their underlying collections.
**Posture**: Read-only. Zero writes. Zero auth changes. Zero data modifications.

---

## 1 · Inventory · what exists today

### 1.1 · Frontend panels (7)

| Panel | File | LOC |
|---|---|---:|
| Access Control Center | `frontend/src/components/AdminAccessControlPanel.jsx` | 578 |
| Unified Directory | `frontend/src/components/AdminUnifiedDirectoryPanel.jsx` | 395 |
| HR Users | `frontend/src/components/AdminHRUsersPanel.jsx` | 404 |
| Safety Users | `frontend/src/components/AdminSafetyUsersPanel.jsx` | 400 |
| Dispatch Users | `frontend/src/components/AdminDispatchUsersPanel.jsx` | 342 |
| Shop Users | `frontend/src/components/AdminShopUsersPanel.jsx` | 447 |
| Field Leadership Users | `frontend/src/components/AdminFieldLeadershipUsersPanel.jsx` | 434 |

**Total**: 7 panels · 3 000 LOC · 6 portals + 1 admin "Access Control" surface.

PM Users panel: **DOES NOT EXIST**. PM users live in `users` collection (admin layer) or as roles on other tables.

### 1.2 · Backend endpoint families (22 endpoints across 6 portals)

| Portal | List | Create | Update | Reset password | Delete | Email welcome | Disable | Source |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| **HR** | GET `/admin/hr-users` | POST | PATCH | POST `/{id}/reset-password` | DELETE | ❌ | (via PATCH `disabled`) | `routes/hr_portal.py:1445+` |
| **Safety** | GET `/admin/safety-users` | POST | PATCH | POST `/{id}/reset-password` | DELETE | ❌ | (via PATCH `disabled`) | `routes/safety_portal/auth_users.py:236+` |
| **Dispatch** | GET `/admin/dispatch-users` | POST | PATCH | POST `/{id}/reset-password` | DELETE | ❌ | (via PATCH `disabled`) | `routes/dispatch_portal_auth.py:251+` |
| **Shop** | GET `/admin/shop-users` | POST | PATCH | POST `/{id}/set-password` | DELETE | ✅ POST `/{id}/email-welcome` | ✅ POST `/{id}/disable` | `server.py:2941+` |
| **Field Leadership** | GET `/admin/field-leadership-users` | POST | PATCH | POST `/{id}/reset-password` | DELETE | ✅ POST `/{id}/resend-welcome` | (via PATCH `disabled`) | `routes/field_leadership_portal.py:781+` |
| **Admin (core)** | GET `/admin/users` | POST | PUT | POST `/{id}/reset-password` | DELETE | ❌ | (via `is_active`) | `auth.py:285+` |
| **PM** | — | — | — | — | — | — | — | **DOES NOT EXIST AS DEDICATED SURFACE** |

### 1.3 · Database collections

Direct count (read-only) against the Atlas cluster:

| Collection | Production (`masci_safety`) | Preview (`masci_safety_preview`) | Drives which panel? |
|---|---:|---:|---|
| `users` (admin) | 3 | 5 | Access Control + Admin core |
| `hr_users` | 3 | 42 | HR Users panel |
| `safety_users` | 2 | 2 | Safety Users panel |
| `dispatch_users` | 3 | 2 | Dispatch Users panel |
| `shop_users` | 2 | 3 | Shop Users panel |
| `field_leadership_users` | 27 | 24 | Field Leadership Users panel |
| `pm_users` | 0 | 0 | (none — collection does not exist) |
| `portal_users` | 0 | 0 | (none — naming convention not used) |
| `passkey_credentials` | 0 | 0 | n/a |

**Total production identities under management: 40 portal users + 3 admin users = 43.**

---

## 2 · Field-surface gaps · what each panel shows vs the directive's canonical set

The directive specifies a single canonical IDENTITY / ACCESS STATUS / PASSWORD STATUS / ACTIVITY / ACTIONS layout. Today each panel implements a different subset.

### 2.1 · IDENTITY

| Required field | HR | Safety | Dispatch | Shop | FL | Access Control |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Name | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Email | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Phone | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Employee ID** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Role | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

🟡 **Employee ID is missing from ALL panels.** Directive requires it everywhere.

### 2.2 · ACCESS STATUS

| Required state | Today's representation | Inconsistency |
|---|---|---|
| Active | `disabled: false` on hr/safety/dispatch/fl/AccessControl; `is_active: true` on shop/admin | 🟡 **Two flag names** for the same concept |
| Pending Activation | `must_change_password: true` proxy (only visible as a label on shop panel; hidden on others) | 🔴 **No explicit "Pending Activation" state** in any panel |
| Disabled | `disabled: true` on most; `is_active: false` on shop/admin | 🟡 **Two flag names** |

### 2.3 · PASSWORD STATUS

| Required state | Today's representation | Gap |
|---|---|---|
| Never Issued | Not surfaced anywhere | 🔴 missing |
| Temporary Password Active | `must_change_password: true` shown only on shop panel | 🔴 inconsistent surfacing |
| Password Set | Not surfaced | 🔴 missing |
| Expired | Not surfaced (no expiration policy implemented) | 🔴 missing |

### 2.4 · ACTIVITY

| Required field | Today's representation | Gap |
|---|---|---|
| Last Login | `last_login_at` shown only on AccessControl + UnifiedDirectory | 🔴 missing from 5 portal panels |
| Last Activity | Not surfaced anywhere | 🔴 missing |
| Last Password Issued | Not stored; not surfaced | 🔴 missing |
| Issued By | Not stored; not surfaced | 🔴 missing |

### 2.5 · ACTIONS

| Required action | HR | Safety | Dispatch | Shop | FL | Access Control |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Edit User | ✅ inline | ✅ inline | ✅ inline | ✅ inline | ✅ inline | ✅ (route-level) |
| Issue Temporary Password | ✅ (reset-password endpoint) | ✅ | ✅ | ✅ (set-password) | ✅ | ❌ (n/a at AC) |
| Resend Welcome Email | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Disable User | ✅ (PATCH `disabled`) | ✅ | ✅ | ✅ (POST `/disable`) | ✅ | ✅ |
| View Audit History | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

🔴 **Resend Welcome Email** is missing on 4 of 6 portals (HR, Safety, Dispatch, Admin core).
🔴 **View Audit History** is missing everywhere — no panel exposes the per-user audit trail.

---

## 3 · Functional & UX gaps

| Gap | Severity | Where | Cost to standardize |
|---|---|---|---|
| Status flag name varies between `disabled` (5 portals) and `is_active` (shop/admin) | HIGH | `routes/server.py:2941+` (shop), `routes/auth.py` (admin) | Display-layer abstraction only — no DB rename. Read both flags; show canonical badge. |
| Employee ID not in any panel's add-form or row | HIGH | All 6 portal panels | Add optional input + column. Existing rows: render "—". |
| Test-ids copy-pasted across panels (dispatch panel uses `admin-safety-add-*`; FL panel uses `admin-hr-add-*`) | MEDIUM | `AdminDispatchUsersPanel.jsx:202-211`, `AdminFieldLeadershipUsersPanel.jsx:242-251` | Pure cosmetic refactor in JSX. |
| "Resend Welcome Email" missing on 4 of 6 portals | MEDIUM | HR, Safety, Dispatch, Admin core | UI-only IF backend endpoints can be added; OR document as future work. **Directive forbids new APIs in this sprint**, so the gap stays open until a later sprint. |
| No "View Audit History" action anywhere | MEDIUM | All 7 panels | Audit data is already collected (`audit_log`, `dispatch_state_events`, `workflow_state_events`). Pure UI work — link out to existing audit view. |
| Last Password Issued / Issued By not tracked | MEDIUM | DB schema | DB write required to track. **Out of scope** for this sprint per directive. Can be standardized in the UI as "—" until backend persists. |
| 7 different panel layouts with subtly different colors (purple/cyan/orange/orange-cyan) | LOW | All panels | Cosmetic alignment. |
| Add-form button color drift (`bg-purple-700` HR/FL · `bg-cyan-700` Safety · `bg-orange-700 hover:bg-cyan-800` Dispatch — bug · `bg-orange-600` Shop) | LOW | All panels | Cosmetic alignment. |
| Dispatch add button has a hover color bug: `bg-orange-700 hover:bg-cyan-800` (orange→cyan flash) | LOW | `AdminDispatchUsersPanel.jsx:211` | Trivial CSS fix. |

---

## 4 · Schema-impact assessment

**No DB schema changes required by this sprint.** The standardization is presentation-layer:

| Concept | Existing field(s) | Standardize as display label | Schema change? |
|---|---|---|:-:|
| Active vs Disabled | `disabled` (5 portals) **OR** `is_active` (shop, admin) | "Active" / "Disabled" badge derived from BOTH | NO |
| Pending Activation | `must_change_password` true + ever logged in | "Pending Activation" badge | NO |
| Temporary Password Active | `must_change_password` true | "Temporary password active" sub-badge | NO |
| Password Set | `must_change_password` false **AND** `last_login_at` not null | "Password set" badge | NO |
| Last Login | `last_login_at` (already stored where supported) | column | NO |
| Last Activity | Derived from `last_activity` collections per portal (out of scope to wire up) | render "—" | NO |
| Employee ID | Optional new field; existing rows have no value | render "—"; add to add-form as optional | NO (additive, optional, nullable) |

🟢 **Conclusion**: The IAM standardization can be implemented as a **read-only presentation contract** over the existing data. No schema migrations. No data rewrites. No password resets. No user re-creation.

---

## 5 · Risk surface · what could go wrong if implemented carelessly

| Risk | Mitigation |
|---|---|
| Toggling between `disabled` and `is_active` could double-flip the row | Build a single `userIsDisabled(u)` accessor in a shared lib — read both flags, write back to whichever the row already uses |
| Changing the add-form's payload key (e.g. sending `is_active` where backend expects `disabled`) could break create flow | Keep per-portal write paths; standardize only the *display* |
| Removing test-ids would break Playwright tests | Add new canonical test-ids alongside legacy ones; do not remove |
| Adding `employee_id` to the create-form payload could trigger backend 422 if not whitelisted | Make it optional client-side and omit from payload if blank |

---

## 6 · Implementation cost · if/when authorized

| Phase | Work | LOC estimate |
|---|---|---:|
| Phase 1 — shared abstraction layer (`frontend/src/lib/iam/` — userStatus, passwordStatus, last-login badges) | New file ~200 LOC | +200 |
| Phase 2 — consolidate 7 panels into a `<PortalUsersPanel portalKey>` shared component | New file ~600 LOC; per-portal stubs ~40 LOC each | -2 400 (-80%) |
| Phase 3 — UX polish (status badges, Employee ID column, View Audit link) | +30 LOC per panel surface | +200 |
| **Net delta** | | **-2 000 LOC across the frontend** |

**No backend changes**, **no schema changes**, **no data changes** required.

---

## 7 · Stop-rule compliance for this audit

| Rule | Status |
|---|:-:|
| Did NOT delete users | 🟢 |
| Did NOT recreate users | 🟢 |
| Did NOT reset passwords | 🟢 |
| Did NOT change user IDs | 🟢 |
| Did NOT modify credentials | 🟢 |
| Did NOT modify login history | 🟢 |
| Did NOT modify audit history | 🟢 |
| Did NOT perform data migrations | 🟢 |
| Did NOT implement (audit only) | 🟢 |

---

## 8 · Companion deliverables

1. `IAM_STANDARD_SPECIFICATION.md` — the canonical row/badge/column contract
2. `IAM_USER_LIFECYCLE_MAPPING.md` — 8-state lifecycle mapped to today's fields
3. `IAM_DATA_PRESERVATION_VALIDATION.md` — proof that no existing identity data will be altered
4. `IAM_NO_MIGRATION_CERTIFICATION.md` — final sign-off that implementation is pure presentation
