# RELEASE CANDIDATE · ADMIN IAM UI CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · `/admin/people` live verification

| Check | data-testid | Observed |
| --- | --- | --- |
| Access Control Center loads | `admin-access-control-panel` (existing) | renders inside `admin-people-stack` |
| Unified Directory loads | `admin-unified-directory-panel` (existing) | renders below ACC |
| Portal accordions load | `portal-accordion-hr` | 1 |
| | `portal-accordion-pm` | 1 |
| | `portal-accordion-field_leadership` | 1 |
| Accordions collapsed by default | `portal-accordion-toggle-{portal}` | initial state `aria-expanded=false` per `PortalUsersAccordion.jsx` |
| Counts display | `portal-accordion-count-hr` | "43" (live from `/admin/directory/k4/stats`) |
| IAM row strip displays cleanly | `IamStandardCells.jsx` row layout | 2-badge cap (Access + Password); activity pill replaces multi-line strip |
| Details drawer opens | `iam-user-detail-drawer` after clicking `iam-row-view-details-hr-*` | 1 |
| Audit link opens | `iam-drawer-audit-link` | `<Link to="/admin/audit?actor=…">` rendered with URL-encoded actor |
| Field Leadership no longer dominates | accordion order | FL is the LAST of six portal accordions, behind collapse-by-default state |
| No white screens | route render | page title `MASCI Operations Platform` resolved; full `<AdminShell>` rendered |
| No console-breaking errors | browser console captured | no uncaught exceptions during navigation |

## 2 · HR Field Leadership IAM parity

| Check | Observed |
| --- | --- |
| `/hr/field-leadership-users` page loads | YES (title `Field Leadership Users · HR`) |
| Details drawer opens | YES via `iam-row-view-details-field-leadership-*` → `iam-user-detail-drawer` |
| Same drawer component | YES — same `<IamUserDetailDrawerHost />` mounted in both pages |
| Same drawer behaviour | YES — Identity / Portal Access / Activity / Audit sections all present |
| Existing FL login data preserved | YES — 24 FL user rows enumerated (matches pre-bundle baseline); no row was deleted, disabled, or renamed by any code in this release |

## 3 · Source check — admin people / FL only added presentation surface

```
git diff --stat 88541da..HEAD -- frontend/src/pages/admin/AdminPeople.jsx
  +59 / -23   (accordion wrapping + drawer host mount + intro copy)

git diff --stat 88541da..HEAD -- frontend/src/pages/HrFieldLeadershipUsers.jsx
  +3        (one import + one drawer host placement)

git diff --stat 88541da..HEAD -- frontend/src/components/iam/IamStandardCells.jsx
  +71 / -23 (density pass · activity pill · Details button)

git diff --stat 88541da..HEAD -- frontend/src/components/iam/IamUserDetailDrawer.jsx
  +270 / -0  (new file)

git diff --stat 88541da..HEAD -- frontend/src/components/iam/PortalUsersAccordion.jsx
  +108 / -0  (new file)
```

All changes are presentational — no API mutation routes were added. The drawer reads only existing user objects already in scope on the parent row.

## 4 · Verdict — Admin IAM UI

```
ADMIN IAM UI CERTIFICATION  :  PASS

  /admin/people renders                  : YES (stack + 6 accordions + drawer host)
  Portal accordions collapsed by default  : YES
  Counts display                         : YES (HR=43 example, live K4)
  Drawer opens cleanly                   : YES (Identity / Portals / Activity / Audit)
  Audit deep-link intact                 : YES
  Field Leadership no longer dominates   : YES
  No white screens                       : YES
  No console-breaking errors             : YES
  HR Field Leadership IAM parity         : YES (same drawer component, 24 FL rows preserved)
```
