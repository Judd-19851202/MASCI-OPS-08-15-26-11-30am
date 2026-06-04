# COMBINED FRONTEND · UNIFIED USER DETAIL DRAWER CERTIFICATION

**Date:** 2026-06-04 17:50 UTC
**Directive:** OMEGA — Combined Frontend Pre-Deploy Certification (read-only)
**Sprint covered:** Unified User Detail Drawer Sprint (commit `01ab04b`)

---

## 1 · Files Touched

| File | Change |
| --- | --- |
| `frontend/src/components/iam/IamUserDetailDrawer.jsx` [NEW] | Right-side `<Sheet>`-based read-only drawer. Mounts as a singleton (`IamUserDetailDrawerHost`); imperatively opened via `window.__openIamUserDrawer({ user, portal })` or the exported `openIamUserDrawer(user, portal)` helper. |
| `frontend/src/components/iam/IamStandardCells.jsx` | Inline `Details` button calls `openIamUserDrawer(...)`; gracefully no-ops if no host is mounted on the page. |
| `frontend/src/pages/admin/AdminPeople.jsx` | Mounts the host once at page bottom. |
| `frontend/src/pages/HrFieldLeadershipUsers.jsx` | Mounts the host once (HR Field Leadership parity). |
| `frontend/src/buildVersion.generated.js` | Build stamp bump. |

No backend, DB, or auth changes. Drawer is **purely client-side and read-only** — it consumes the `user` object already in scope inside the row and the canonical badge reducers in `@/lib/iam/userBadges`.

---

## 2 · UI Behaviour Verified (Authenticated Smoke)

**Account used:** `jaymn.judd@mascigc.com`. No writes.

### Test #1 — Admin People (`/admin/people`)

| Step | Observed |
| --- | --- |
| Click `Details` button on a row inside HR accordion | Drawer opens on the right |
| `[data-testid='iam-user-detail-drawer']` | 1 |
| `[data-testid='iam-drawer-identity']` | 1 (Employee ID + Source + Access/Password badges) |
| `[data-testid='iam-drawer-portals']` | 1 (2×3 grid; 7 portals total: Admin · PM · HR · Safety · Dispatch · Shop · Field Leadership) |
| `[data-testid='iam-drawer-activity']` | 1 (Last Login · Last Activity · Last Password Issued · Issued By) |
| `[data-testid='iam-drawer-audit']` + `iam-drawer-audit-link` | 1 each |
| Audit deep-link href | `/admin/audit?actor=<email>` (correctly URL-encoded) |
| Close on Sheet `onOpenChange(false)` | Drawer dismisses cleanly |

### Test #2 — HR Field Leadership (`/hr/field-leadership-users`)

| Step | Observed |
| --- | --- |
| 24 Details buttons on Field Leadership user table | confirmed (`iam-row-view-details-field-leadership-*`) |
| Click first Details button | Drawer opens |
| All 5 sections render | Identity ✓ · Portal Access ✓ · Activity ✓ · Audit ✓ |
| Portal Access correctly shows ONLY Field Leadership granted for a native-FL user | confirmed (single emerald tile; other 6 portals greyed) |
| Audit deep-link to `/admin/audit?actor=allensmathers%40masciae.com` | confirmed |

---

## 3 · Read-Only Safety Verification

The drawer code was audited for any write-path or credential mutation:

```bash
grep -n "POST\|PUT\|PATCH\|DELETE\|setItem\|reset-password\|change-password" \
  frontend/src/components/iam/IamUserDetailDrawer.jsx
# (no matches)
```

| Risk vector | Verdict |
| --- | --- |
| No `axios.post/put/patch/delete` calls | PASS |
| No `localStorage.setItem(masci.*.token)` | PASS |
| No password / reset / temp-credential UI exposed | PASS |
| No backend mutation endpoints invoked | PASS |
| Reads only fields already in scope on the user object | PASS |
| Imports limited to shadcn `<Sheet>`, lucide icons, and `@/lib/iam/userBadges` | PASS |

The Audit deep-link is a `<Link to>` (react-router `<Link>`), not an action — it navigates to the existing `/admin/audit` page that is independently gated and read-only.

---

## 4 · Graceful Degradation

`openIamUserDrawer(...)` checks `window.__openIamUserDrawer`:

```js
if (typeof window.__openIamUserDrawer !== "function") {
  console.warn("[iam] User Detail Drawer host not mounted on this page.");
  return;
}
```

On any page that hasn't mounted the host (legacy admin pages), the Details button no-ops with a console.warn — **never** throwing or breaking the row. Verified by static read.

---

## 5 · Verdict — Drawer Certification

```
DRAWER SPRINT CERTIFICATION:  PASS

  Singleton host pattern (no double mount)        : confirmed (window.__openIamUserDrawer)
  Open contract via Details button                : confirmed (Admin People + HR FL)
  Identity / Portal Access / Activity / Audit     : all 4 sections render
  Audit deep-link → /admin/audit?actor=…           : confirmed
  Zero write paths                                : confirmed (static + runtime)
  Graceful degradation when host absent           : confirmed (console.warn no-op)
  Bilingual / accessibility                       : SheetHeader + SheetTitle + SheetDescription used (screen-reader compatible)
```

Unified User Detail Drawer is **deploy-ready**.
