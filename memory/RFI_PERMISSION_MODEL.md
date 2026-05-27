# RFI Permission Model
## Phase V.0 · Architecture & Governance · 2026-05-27

> Authoritative role × operation matrix. Doctrine-locked before any code.
> Inherits the AUTHORIZATION_MATRIX baseline and the portal-scope rules.

---

## 1 · Scope

This document defines **who can do what** on RFI records, including
external tokenized actors. It does **not** prescribe storage format,
endpoint paths, or component layouts — those land in V.1.

---

## 2 · Roles in Scope

| Role | Token type | Provenance |
|---|---|---|
| Super Admin | `X-Admin-Token` (super flag) | `user_directory` |
| Admin | `X-Admin-Token` | `user_directory` |
| PM (per-PM) | `X-PM-Token` | `project_managers` |
| Superintendent / Foreman / Truck Boss / Field Supervisor | `X-FL-Token` | `field_leadership_users` |
| Safety Manager | `X-Safety-Token` | `safety_users` |
| Dispatch | `X-Dispatch-Token` | `dispatch_users` |
| HR | `X-HR-Token` | `hr_users` |
| Executive (read-only insight) | derived from admin or PM with executive flag | `user_directory` |
| **External CEI** | `X-RFI-Ext-Token` (NEW · tokenized) | `rfi_external_tokens` collection |
| **External Engineer / DOT / FAA / Owner / Utility** | `X-RFI-Ext-Token` (NEW · tokenized) | `rfi_external_tokens` collection |

External tokens are **NOT** portal tokens. They authorize a single RFI
or a single distribution group, expire, and audit every use.

---

## 3 · Operation × Role Matrix

Legend: ✅ allowed · ⚠ allowed within scope · ✖ denied · 🔒 dual-control required.

| Operation | Super Admin | Admin | PM | Superintendent | Safety | Dispatch | Executive | External CEI/Eng | External Owner |
|---|---|---|---|---|---|---|---|---|---|
| Create draft | ✅ | ✅ | ✅ (in scope) | ⚠ (own crew jobs only) | ✖ | ✖ | ✖ | ✖ | ✖ |
| Read draft | ✅ | ✅ | ⚠ (scope) | ⚠ (own) | ✖ | ✖ | ✖ | ✖ | ✖ |
| Read internal-review | ✅ | ✅ | ⚠ (scope) | ⚠ (own) | ⚠ (if safety flag) | ✖ | ⚠ (read-only) | ✖ | ✖ |
| Edit body before submit | ✅ | ⚠ (scope) | ✅ (scope) | ⚠ (own draft) | ✖ | ✖ | ✖ | ✖ | ✖ |
| Submit (lock + PDF) | ✅ | ⚠ (scope) | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Read submitted | ✅ | ✅ | ⚠ (scope) | ⚠ (own jobs) | ⚠ (if safety flag) | ⚠ (if MOT/access flag) | ⚠ (read-only) | ⚠ (assigned RFI only) | ⚠ (assigned RFI only) |
| Issue external token | ✅ | ✅ | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Revoke external token | ✅ | ✅ | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Request clarification | ✅ | ⚠ (scope) | ✅ | ✖ | ✖ | ✖ | ✖ | ✅ (assigned RFI) | ✅ (assigned RFI) |
| Submit response | ✅ | ⚠ (scope) | ✖ (PM accepts/rejects) | ✖ | ✖ | ✖ | ✖ | ✅ (assigned RFI) | ✅ (assigned RFI) |
| Accept response | ✅ | ⚠ (scope) | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Reject response | ✅ | ⚠ (scope) | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Convert to Change Condition | ✅ | ⚠ (scope) | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Log schedule impact | ✅ | ⚠ (scope) | ✅ (scope) | ⚠ (propose only) | ✖ | ✖ | ✖ | ✖ | ✖ |
| Close | ✅ | ⚠ (scope) | ✅ (scope) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Void | 🔒 (Admin + PM agree, with reason) | 🔒 | 🔒 | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| Read audit trail | ✅ | ✅ | ⚠ (scope) | ⚠ (own jobs) | ⚠ (if safety flag) | ⚠ (if MOT/access flag) | ⚠ (read-only) | ✖ | ✖ |
| Download PDF | ✅ | ✅ | ⚠ (scope) | ⚠ (own jobs) | ⚠ (if safety flag) | ⚠ (if MOT/access flag) | ⚠ (read-only) | ✅ (assigned RFI) | ✅ (assigned RFI) |
| Hard-delete | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |

> **Hard-delete is never allowed in any role.** Voiding preserves the
> snapshot. Backups preserve voided records. Legal defensibility.

---

## 4 · Scope Resolution

Scope follows the existing PM scope helper (`pm_auth.compute_pm_scope`)
extended to:

- **PM:** projects where they are primary or co-PM.
- **Superintendent / Foreman / Truck Boss:** projects where they are
  assigned in crew assignments (existing field-leadership scope).
- **Safety:** all projects, but body edits remain ✖. Safety can flag
  safety/compliance exposure on an RFI without editing it.
- **Dispatch:** RFIs flagged with MOT / phasing / haul / access impact
  only. Read-only.
- **Executive:** all projects, read-only.
- **External tokens:** strictly the RFI(s) the token was issued for.

---

## 5 · External-Token Authorization Envelope

| Field | Constraint |
|---|---|
| `rfi_id` (or `distribution_id`) | required · single record or single distribution group |
| `recipient_email` | recorded · audit |
| `recipient_role` | one of `cei`, `engineer`, `owner`, `dot`, `faa`, `utility` |
| `permissions` | enum subset of: `read`, `respond`, `request_clarification`, `download_pdf` |
| `expires_at` | required · default = response_due_date + 30 days |
| `max_uses` | optional · 0 = unlimited (default), N = limit |
| `issued_by` | PM or Admin user_id |
| `issued_at` | ts |
| `revoked_at` | nullable · admin/PM action |
| `last_used_at` | updated on every use |
| `use_count` | monotonic |

External tokens **cannot** escalate to portal tokens. They have no
write access outside the explicit `permissions` set.

---

## 6 · Dual-Control Operations

The only RFI operation requiring dual control is **void**. PM proposes
with `void_reason` (≥ 20 chars). Admin confirms with their own
`confirmation_note`. Both audit entries land. This prevents single-
actor mistakes from removing a submitted RFI from operational view.

---

## 7 · Cross-Portal Read Discipline

Mirroring the existing `make_require_any_portal_token` pattern, **read**
on submitted RFIs can be satisfied by any in-scope portal token. **Write**
is strictly the PM scope (and Admin) except for the external-respond
path. This matches the iter126 Dispatch precedent for operations.

---

## 8 · Implementation Note (V.1)

The permission engine should be expressed as a **declarative matrix**
that maps `(token_kind, operation, target_state)` → `allow|deny|scope_check`.
This makes the regression-test surface compact (one parametrized test
per matrix cell). Free-form `if role == "x"` checks scattered across
endpoints are **rejected by doctrine**.

---

## 9 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Matrix locks during V.1. Any change to allowed/denied cells requires a doctrine revision.
