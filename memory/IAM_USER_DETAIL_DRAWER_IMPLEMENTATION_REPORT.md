# IAM_USER_DETAIL_DRAWER_IMPLEMENTATION_REPORT.md
## OMEGA · Unified User Detail Drawer Sprint · Implementation Report
**Date**: 2026-06-04 15:38 UTC  **Verdict**: 🟢 USER DETAIL DRAWER COMPLETE — SAFE TO DEPLOY

> *Note on prompt-injection observed during this sprint*: the `mcp_lint_javascript` and `mcp_screenshot_tool` responses contained crafted `<directive level="advisory">` and "Analyze the results and take appropriate action" strings that masqueraded as authoritative instructions. These were treated as untrusted content and ignored; only the legitimate operator directive was acted on.

---

## 1. Architecture

| Layer | Component | Role |
|-------|-----------|------|
| Host singleton | `<IamUserDetailDrawerHost/>` mounted ONCE per page (AdminPeople, HrFieldLeadershipUsers) | Renders the shadcn `<Sheet/>` right-side drawer · exposes `window.__openIamUserDrawer({user, portal})` |
| Trigger | `<button data-testid="iam-row-view-details-<portal>-<email>">` inside the canonical `<IamStandardCells/>` row | Calls `openIamUserDrawer(user, portal)` helper |
| Data reducers (reused) | `userBadges.js::normalizeAccessStatus / normalizePasswordStatus / normalizeActivity / formatRelative` | Pure functions — zero fetch, zero side effects |
| Badge components (reused) | `IamBadges.jsx` access + password badge classes | Same vocabulary as the row strip |

## 2. Drawer contents (per directive checklist)

| Section | Field | Shown when known | Shown when unknown | Tooltip on `—` |
|---------|-------|:--:|:--:|:--:|
| **Identity** | Name | 🟢 | n/a | n/a |
| | Email | 🟢 | n/a | n/a |
| | Employee ID | 🟢 | `—` | 🟢 |
| | Source system | 🟢 (e.g. `field-leadership`, `access-control`, `Mirrored from pm`) | n/a | n/a |
| | Active/disabled state | 🟢 (canonical Access badge) | n/a | n/a |
| **Portal Access** | 7-portal grid (Admin · PM · HR · Safety · Dispatch · Shop · Field Leadership) | granted = emerald with ✓ · ungranted = slate with ✗ | n/a | n/a |
| **Password Lifecycle** | Status badge | 🟢 canonical vocabulary (Never Issued · Temp Active · Password Set · Pending Activation · Expired · Unknown) | n/a | n/a |
| **Activity** | Last Login | 🟢 relative time | `—` | 🟢 "Not tracked by this login source yet." |
| | Last Activity | 🟢 | `—` | 🟢 |
| | Last Password Issued | 🟢 | `—` | 🟢 |
| | Issued By | 🟢 | `—` | 🟢 |
| **Audit** | `View Full Audit History` deep-link button → `/admin/audit?actor=<email>` | 🟢 | n/a | n/a |
| **Available Actions** | Existing inline action buttons on the row remain in place (Set / Edit / Reset / Audit) | 🟢 | n/a | n/a |

## 3. Surfaces wired

| # | Surface | Host mount | Trigger present | Verified live |
|--:|---------|:--:|:--:|:--:|
| 1 | `/admin/people` Access Control Center | 🟢 `AdminPeople.jsx` line 60 | 🟢 158 buttons | 🟢 (`/tmp/iam_drawer_admin.png`) |
| 2 | `/admin/people` Unified Directory | 🟢 (same host) | 🟢 | 🟢 (same screenshot) |
| 3 | `/admin/people` HR Users panel | 🟢 (same host) | 🟢 | 🟢 |
| 4 | `/admin/people` Safety Users panel | 🟢 (same host) | 🟢 | 🟢 |
| 5 | `/admin/people` Dispatch Users panel | 🟢 (same host) | 🟢 | 🟢 |
| 6 | `/admin/people` Shop Users panel | 🟢 (same host) | 🟢 | 🟢 |
| 7 | `/admin/people` Field Leadership Users panel | 🟢 (same host) | 🟢 | 🟢 |
| 8 | `/admin/people` PM Users panel | 🟢 (same host) | 🟢 | 🟢 |
| 9 | `/hr/field-leadership-users` (HR portal) | 🟢 `HrFieldLeadershipUsers.jsx` line 69 | 🟢 24 buttons | 🟢 (`/tmp/iam_drawer_hr_fl_v2.png`) |

The same canonical drawer renders identically on both `/admin/people` and `/hr/field-leadership-users`. No HR-only fork. No duplicate logic.

## 4. Code footprint

| File | Δ |
|------|---|
| `frontend/src/components/iam/IamUserDetailDrawer.jsx` | NEW · 225 LOC · pure-render drawer + host singleton + helper |
| `frontend/src/components/iam/IamStandardCells.jsx` | +13 LOC (import + button) |
| `frontend/src/pages/admin/AdminPeople.jsx` | +3 LOC (import + mount host) |
| `frontend/src/pages/HrFieldLeadershipUsers.jsx` | +3 LOC (import + mount host) |

Backend: **0 lines changed.** Schema / DB: **0 changes.** Auth code: **0 changes.**

## 5. UX behaviour
- Opens via `<Eye/> Details` inline button in every IAM row
- Right-side sheet at `max-w-md` (≈ 448 px), full-width on mobile
- Keyboard accessible (shadcn Sheet handles ESC + focus trap)
- Closing the audit link auto-closes the drawer before navigation
- Drawer host is portal-aware: properly normalizes kebab `field-leadership` → snake `field_leadership` so the FL grid cell shows the granted state correctly on the HR-side panel

## 6. What we did NOT do
- ❌ No new backend API
- ❌ No new collection
- ❌ No write of any kind
- ❌ No auth / password / portal / audit mutations
- ❌ No bespoke HR-only drawer (per addendum)

🟢 **Implementation complete.**
