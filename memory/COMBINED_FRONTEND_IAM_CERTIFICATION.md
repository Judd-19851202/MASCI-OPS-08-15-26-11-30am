# COMBINED FRONTEND · ADMIN IAM CERTIFICATION

**Date:** 2026-06-04 17:50 UTC
**Directive:** OMEGA — Combined Frontend Pre-Deploy Certification (read-only)
**Sprint covered:** Admin IAM Screen Completion Sprint (commit `cb8cf74`)

---

## 1 · Files Touched

| File | Change |
| --- | --- |
| `frontend/src/pages/admin/AdminPeople.jsx` | Re-ordered into LEVEL 0/1/2/3 hierarchy; wrapped portal-specific panels in collapsible `<PortalUsersAccordion>` shells (HR / PM / Safety / Dispatch / Shop / Field Leadership); mounted `IamUserDetailDrawerHost` once on the page. |
| `frontend/src/components/iam/PortalUsersAccordion.jsx` [NEW] | Collapsible header (closed by default), 48-px row, count badge wired to read-only `GET /admin/directory/k4/stats`, shared singleton cache. |
| `frontend/src/components/iam/IamStandardCells.jsx` | Replaced multi-line activity strip with single `ActivityPill` token (`"6/3/26"` / `"Never logged in"` / `"—"` with tooltip); added inline "Details" button that opens the host drawer; reduced from 4-badge stack to **max 2 visible badges** (Access + Password). |

No backend, DB, or auth changes.

---

## 2 · UI Behaviour Verified (Authenticated Smoke)

**Account used:** `jaymn.judd@mascigc.com` (super admin via multi-login). No writes performed.

**Route:** `/admin/people`.

| Verification | data-testid | Observed |
| --- | --- | --- |
| Intro paragraph reflects new IAM hierarchy | `admin-people-intro` | 1 (text starts with "Access Control Center is the source of truth…") |
| Outer stack present | `admin-people-stack` | 1 |
| Accordion sections rendered | `portal-accordion-*` | 18 nodes (6 outer shells × 3 testid variants — toggle/count/section) |
| HR accordion shell | `portal-accordion-hr` | 1 |
| PM accordion shell | `portal-accordion-pm` | 1 |
| Field Leadership accordion shell | `portal-accordion-field_leadership` | 1 |
| HR accordion expands cleanly | `portal-accordion-body-hr` | 1 (after click) |
| Per-row Details buttons | `iam-row-view-details-hr-*` | 42 (one per HR row, matches list) |
| Count badge populated | `portal-accordion-count-hr` | "43" (from `/admin/directory/k4/stats` read) |

### LEVEL hierarchy verification (visual order in render)

1. LEVEL 0 — `AdminAccessStatsTile` (at-a-glance)
2. LEVEL 1 — `AdminAccessControlPanel` (multi-portal source of truth)
3. LEVEL 2 — `AdminUnifiedDirectoryPanel` (search index)
4. LEVEL 3 — Portal accordions (HR · PM · Safety · Dispatch · Shop · Field Leadership) — **collapsed by default**
5. Peripheral — `EmployeeMasterPanel`
6. Mounted once at page bottom — `IamUserDetailDrawerHost`

Matches the directive.

---

## 3 · Row Cleanup Verification

In `IamStandardCells.jsx`, row markup is one line:

```
[ACCESS-BADGE] [PASSWORD-BADGE] · activity-pill · [DETAILS] [AUDIT]
```

* 2 badges max — Access status + Password status. Activity is now a **pill, not a badge**.
* Activity pill shows: relative date (`"6/3/26"`), `"Never logged in"`, or `"—"` (with hover tooltip *"Not tracked by this login source yet."*).
* `IamActivityLine` (the legacy multi-line strip) has been removed from the row.
* `Details` button has its own `data-testid` (`iam-row-view-details-{portal}-{email|id}`) for QA.
* `IamViewAuditLink` retained for the audit deep-link.

---

## 4 · Non-Regression Checks

* All pre-existing portal panels (`AdminHRUsersPanel`, `AdminPMPanel`, `AdminShopUsersPanel`, `AdminSafetyUsersPanel`, `AdminDispatchUsersPanel`, `AdminFieldLeadershipUsersPanel`) **render identically** inside the accordion — no panel internals were modified by this sprint.
* `AdminAccessControlPanel` and `AdminUnifiedDirectoryPanel` untouched.
* No new routes, no new auth gates, no new MongoDB collections, no new write endpoints.
* Count fetch (`/admin/directory/k4/stats`) is a pre-existing GET-only K4 read endpoint; falls back to `null` (renders `·`) on error.

---

## 5 · Verdict — Admin IAM Certification

```
ADMIN IAM SPRINT CERTIFICATION:  PASS

  LEVEL 0/1/2/3 hierarchy in render order   : confirmed
  Accordion shells (6 portals, collapsed)    : confirmed
  K4 count badges                            : confirmed (HR=43 example)
  ActivityPill replaces strip                : confirmed
  Max 2 badges per row                       : confirmed
  Details button per row                     : confirmed (42 in HR)
  Drawer host mounted once                   : confirmed
  Zero backend / auth / DB touches           : confirmed
```

Admin IAM Screen Completion sprint is **deploy-ready**.
