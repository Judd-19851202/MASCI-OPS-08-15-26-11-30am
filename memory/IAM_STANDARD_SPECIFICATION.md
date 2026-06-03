# FORGEDOPS IAM SPRINT · 2 · STANDARD SPECIFICATION
## OMEGA P0 · Canonical presentation contract

**Date**: 2026-06-03
**Companion**: `IAM_GAP_ANALYSIS.md`, `IAM_USER_LIFECYCLE_MAPPING.md`

---

## 1 · Canonical user row · single contract for every portal panel

Every portal-user panel (HR, Safety, Dispatch, Shop, Field Leadership, Admin core, and any future PM panel) renders the same row shape. The data values come from each portal's existing collection unchanged.

| Section | Column | Source field(s) | Display rule |
|---|---|---|---|
| **IDENTITY** | Name | `name` | Plain text |
| | Email | `email` | Mono small caps; mailto link |
| | Phone | `phone` | "—" when null |
| | Employee ID | `employee_id` (additive, optional) | "—" when null |
| | Role | `role` | Badge |
| **ACCESS STATUS** | Status badge | `disabled` (HR/Safety/Dispatch/FL) **OR** `is_active`/`disabled` (Shop) **OR** `is_active` (Admin) | Display rule §2 |
| **PASSWORD STATUS** | Password badge | `must_change_password`, `last_login_at`, `password_set_at` (if present) | Display rule §3 |
| **ACTIVITY** | Last login | `last_login_at` | Relative ("2h ago"); "—" if null |
| | Last activity | derived from per-portal activity event store (future) | "—" today |
| | Last password issued | not stored today | "—" today |
| | Issued by | not stored today | "—" today |
| **ACTIONS** | Edit | inline drawer | per panel |
| | Issue Temp Password | POST `/{portal}-users/{id}/reset-password` (Shop uses `/set-password`) | per panel |
| | Resend Welcome | POST `/{portal}-users/{id}/resend-welcome` (only Shop/FL today) | hide button if portal lacks endpoint |
| | Disable / Re-enable | PATCH `{disabled}` or POST `/disable` (Shop) | per panel |
| | View Audit History | nav to `/admin/audit?actor=<email>` | new link only |

---

## 2 · ACCESS STATUS badge derivation (canonical reducer)

```
function deriveAccessStatus(u) {
  // Read both flags. NEVER write back to the wrong flag.
  const isDisabled = u.disabled === true || u.is_active === false;
  const pending = !isDisabled && u.must_change_password === true && !u.last_login_at;
  if (isDisabled) return "DISABLED";
  if (pending)    return "PENDING_ACTIVATION";
  return "ACTIVE";
}
```

| State | Badge color | Badge text |
|---|---|---|
| ACTIVE | emerald-100 / emerald-800 | "Active" |
| PENDING_ACTIVATION | amber-100 / amber-800 | "Pending activation" |
| DISABLED | rose-100 / rose-700 | "Disabled" |

---

## 3 · PASSWORD STATUS badge derivation

```
function derivePasswordStatus(u) {
  if (!u.password_set_at && !u.last_login_at && !u.must_change_password) return "NEVER_ISSUED";
  if (u.must_change_password === true)  return "TEMP_PASSWORD_ACTIVE";
  if (u.last_login_at && !u.must_change_password) return "PASSWORD_SET";
  // Expiration policy not implemented; never returns "EXPIRED" today.
  return "PASSWORD_SET";
}
```

| State | Badge color | Badge text |
|---|---|---|
| NEVER_ISSUED | slate-100 / slate-700 | "Never issued" |
| TEMP_PASSWORD_ACTIVE | amber-100 / amber-800 | "Temp password active" |
| PASSWORD_SET | slate-100 / slate-600 | "Password set" |
| EXPIRED (reserved) | rose-100 / rose-700 | "Expired" |

---

## 4 · Add-form contract

Single 5-input layout used by all portal panels:

```
[Name        ] [Email       ] [Phone (opt) ] [Employee ID (opt)] [Role ▾] [+ Add]
```

| Field | Required | Sent to backend if blank? |
|---|:-:|:-:|
| Name | ✅ | n/a |
| Email | ✅ | n/a |
| Phone | optional | omit |
| Employee ID | optional | omit |
| Role | ✅ | n/a |

Button color standardized to `bg-slate-900 hover:bg-slate-800 text-white` to remove the portal-specific drift. (The portal palette stripe remains on the panel card.)

---

## 5 · Test-id contract

Standardize on `iam-user-row-{portal}-{email}` for rows and `iam-{portal}-add-{field}` for inputs. **Existing test-ids are preserved** (the new contract is additive — old test-ids stay alongside new ones to avoid breaking any Playwright suite).

| Element | New test-id | Legacy preserved |
|---|---|---|
| Panel root | `iam-{portal}-panel` | `admin-{portal}-users-panel` |
| Add Name | `iam-{portal}-add-name` | `admin-{portal}-add-name` |
| Add Email | `iam-{portal}-add-email` | `admin-{portal}-add-email` |
| Add Phone | `iam-{portal}-add-phone` | `admin-{portal}-add-phone` |
| Add Employee ID | `iam-{portal}-add-employee-id` | — (new) |
| Add Role | `iam-{portal}-add-role` | `admin-{portal}-add-role` |
| Add Submit | `iam-{portal}-add-submit` | `admin-{portal}-add-submit` |
| Row | `iam-row-{portal}-{email}` | `admin-{portal}-row-{email}` |
| Status badge | `iam-row-status-{portal}-{email}` | — (new) |
| Password badge | `iam-row-pwstatus-{portal}-{email}` | — (new) |
| Action: edit | `iam-row-edit-{portal}-{email}` | per-panel legacy |
| Action: issue temp pw | `iam-row-issue-pw-{portal}-{email}` | per-panel legacy |
| Action: resend welcome | `iam-row-resend-welcome-{portal}-{email}` | per-panel legacy (where exists) |
| Action: toggle disable | `iam-row-toggle-disable-{portal}-{email}` | per-panel legacy |
| Action: view audit | `iam-row-view-audit-{portal}-{email}` | — (new) |

Existing Playwright tests are not broken because legacy test-ids stay.

---

## 6 · Implementation strategy (when authorized)

| Phase | What | Risk |
|---|---|---|
| Phase A — shared lib `frontend/src/lib/iam/userBadges.js` | Pure functions `deriveAccessStatus`, `derivePasswordStatus`, `formatLastLogin`. No JSX, no fetch. | NONE |
| Phase B — shared component `<IamRow user={u} portal="hr" />` returns standard row JSX | New component; existing panels can opt in row-by-row | LOW |
| Phase C — replace 7 panel row markups with `<IamRow>` | Wholesale UI swap; backend unchanged | LOW |
| Phase D — add Employee ID column + add-form input (optional) | Optional field; existing rows show "—" | NONE |
| Phase E — add "View Audit History" link to row actions | New link; opens existing admin audit page filtered by email | NONE |
| Phase F — cosmetic alignment (button colors, panel headers) | Pure CSS | NONE |

**No phase touches the backend.** **No phase touches the database.** **No phase modifies an existing user.**

---

## 7 · What stays unchanged

| Concern | Status |
|---|:-:|
| Backend endpoints (22) | 🟢 untouched |
| Database collections (6 portal-user collections + admin `users`) | 🟢 untouched |
| Password hashes | 🟢 untouched |
| `last_login_at`, `must_change_password`, `disabled`, `is_active` field semantics | 🟢 untouched |
| `passkey_credentials` | 🟢 untouched |
| `audit_log`, `dispatch_state_events`, `workflow_state_events` | 🟢 untouched (read-only) |
| User IDs | 🟢 untouched |
| Email addresses | 🟢 untouched |
| Login history | 🟢 untouched |
| Existing test-ids | 🟢 preserved (new ones are additive) |

---

## 8 · Acceptance criteria for the implementation (once authorized)

1. Every panel renders the same 11-column row contract.
2. Status / Password badges derive from existing fields via §2 / §3 reducers.
3. Add-form is identical across all panels (Name + Email + Phone + Employee ID + Role).
4. Disable / re-enable continues to call whichever endpoint that portal exposes today (no API surface change).
5. "View Audit History" link routes to `/admin/audit?actor=<email>` and that page already exists.
6. Production verification: counts unchanged before/after deploy (43 portal users in production).
7. Playwright legacy test-ids still resolve.
