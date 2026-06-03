# IAM_FIELD_LEADERSHIP_HR_SURFACE_CERTIFICATION.md
## OMEGA DIRECTIVE — HR Field Leadership Surface · Phase D Certification
**Date**: 2026-06-03  **Verdict**: 🟢 IDENTICAL — zero special-case implementation.

---

## 1. What this certifies

That the Field Leadership user-management surface accessed from inside the HR
Dashboard (`/hr/field-leadership-users`) is **byte-for-byte identical** to the
Field Leadership user-management surface accessed from the Admin Dashboard
(`/admin/people` → "Field Leadership Users & Logins").

---

## 2. Architecture

Both surfaces mount the **same** React component:

```
frontend/src/components/AdminFieldLeadershipUsersPanel.jsx
```

### Mount points
| Portal | Page file | Mount |
|--------|-----------|-------|
| Admin | (composed inside `/admin/people`) | `<AdminFieldLeadershipUsersPanel />` |
| HR | `frontend/src/pages/HrFieldLeadershipUsers.jsx:66` | `<AdminFieldLeadershipUsersPanel />` |

### Backend authority
The backend routes that the panel calls (`/api/admin/field-leadership-users/*`)
accept **either** `X-Admin-Token` **or** `X-HR-Token`. The token used is
determined automatically by `@/lib/api`. The component itself is portal-agnostic.

---

## 3. Per-requirement attestation

| Requirement | Status | Evidence |
|---|:-:|---|
| Same layout | 🟢 | Same component file — one React tree. |
| Same row structure | 🟢 | Same `<table>` markup, same `<tr>`, same `<td>` order. |
| Same badge system | 🟢 | `<IamStandardCells portal="field-leadership"/>` rendered identically. |
| Same password lifecycle display | 🟢 | `IamPasswordStatusBadge` renders the same `NEVER_ISSUED / TEMP_ACTIVE / PASSWORD_SET` vocabulary. |
| Same activity display | 🟢 | `IamActivityLine` renders `Last login · Last pw issued · Issued by`. |
| Same audit visibility | 🟢 | `IamViewAuditLink → /admin/audit?actor=<email>` (same target). |
| Same action ordering | 🟢 | Same JSX order: `[Edit] [Reset password] [Disable] [Delete]`. |
| Same terminology | 🟢 | Strings drawn from the same component source. |

---

## 4. Implementation note

When Phase D was originally drafted, the assumption was that HR might have a
separate Field Leadership management implementation. After tracing the codebase:

```
/app/frontend/src/pages/HrFieldLeadershipUsers.jsx
  └─ imports AdminFieldLeadershipUsersPanel
        └─ contains <IamStandardCells portal="field-leadership"/>
```

The HR-facing surface has **always** delegated to the same component. Phase C's
patch of `AdminFieldLeadershipUsersPanel` therefore automatically standardized
both the Admin-side and HR-side views. Phase D was satisfied at Phase C close.

This is the "one source of truth" guarantee: there is no duplicate component to
keep in sync. There can NEVER be a presentation drift between the two surfaces.

---

## 5. What was NOT done (per OMEGA constraints)

- ❌ No new HR-specific component created
- ❌ No HR-specific badge / label / icon / vocabulary divergence introduced
- ❌ No field_leadership_users schema changes
- ❌ No backend route changes
- ❌ No audit log changes
- ❌ No user record changes
- ❌ No portal assignment changes

---

🟢 **Field Leadership HR Surface · Identical to Admin Surface · No Special Case**
