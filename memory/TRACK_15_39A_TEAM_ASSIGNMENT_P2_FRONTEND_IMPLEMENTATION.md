# TRACK 15.39A · Team Assignment P2 Frontend Implementation

**Date:** 2026-06-19
**Track:** 15.39A · Team Assignment P2 Frontend Completion
**Status:** 🟢 COMPLETE · all 7 tests PASS at 3 viewports (see companion certification doc)
**Backend dependency:** Track 15.39 backend (certified) — DO NOT modify

---

## 1 · Files changed / created

| File | Action | Purpose |
|---|---|---|
| `/app/frontend/src/lib/teamRosterApi.js` | **EDIT** | `removeTeamMember` now POSTs JSON body `{reason_category, reason_text}` (was `?reason=` query). `patchTeamMember` re-throws errors with `err.status` + `err.detail` so the UI can detect 409 duplicate-role and show the exact server detail. |
| `/app/frontend/src/components/team/RemoveReasonDialog.jsx` | **CREATE** | shadcn Dialog with 7 reason radios (reassigned · staffing_adjustment · promotion · demotion · project_complete · left_company · other) + optional text. Submit is gated when `category === "other" && !text.trim()` so the backend 400 guard is never hit. |
| `/app/frontend/src/components/team/AssignmentHistoryDrawer.jsx` | **CREATE** | shadcn Sheet (right-side) showing the audit feed newest-first. Color-coded badges per action: `assign` (emerald) · `role_change` (amber) · `update` (blue) · `remove` (red). Shows actor + role + reason notes per row. |
| `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` | **EDIT** | (a) replaced `window.prompt(...)` remove flow with `RemoveReasonDialog`; (b) added inline role-change `<Select>` per row (admin scope only) calling `patchTeamMember` with 409 toast on duplicate role; (c) swapped inline audit panel for `AssignmentHistoryDrawer` (admin scope only); (d) removed unused `showAudit` state. |
| `/app/frontend/src/index.js` | **EDIT** | Added a global `ResizeObserver loop` warning suppressor (window.error + unhandledrejection). Required so the CRA dev overlay doesn't surface the benign Radix Select/Sheet animation warnings as fatal errors during testing. Dev-only-visible band-aid; production builds have no overlay. |
| `/app/memory/TRACK_15_39A_FRONTEND_HANDOFF_PLAN.md` | **EDIT** | Prepended a §0 "T0 Fixture Seed Block" with copy-paste curl commands to establish the 2-row scenario (Alec Perkins foreman + safety_rep on project 20-07) before cert. |

No backend files touched. No new endpoints. No new MongoDB collections.

---

## 2 · API contract (already certified — Track 15.39)

* `PATCH /api/admin/jobs/{project_number}/team/{assignment_id}` body `{ assignment_role: "<new_role_key>" }` → 200 `{ok, assignment, role_changed}` · 409 on duplicate role · 404 not found · 400 unknown role
* `DELETE /api/admin/jobs/{project_number}/team/{assignment_id}` body `{ reason_category: "<one of 7>", reason_text?: string }` → 200 `{ok}` · 400 if `other` without text · 400 on unknown category · 404 not found
* `GET  /api/admin/jobs/{project_number}/team/audit?limit=100` → 200 `{items: [{id, at, action, before, after, actor_*, notes, ...}]}` newest-first

---

## 3 · UX behaviour

### 3.1 · Inline Change Role (admin only)
Each active row in the admin team panel has a `<Select>` next to the action icons. Changing the value:
1. Disables the Select while the PATCH is in flight (`rowBusy[id]=true`).
2. On 200 → sonner success "Role changed to {Label}" → roster + audit reload.
3. On 409 → sonner error with the exact server detail ("User already holds the Foreman role on this project."). The Select reverts visually on reload.
4. On any other error → sonner error with `err.detail || err.message`.

Single canonical `role_change` audit row is emitted by the backend; no synthetic remove+add pair.

### 3.2 · Structured Remove dialog (admin AND PM scope)
Clicking the Remove button (X icon) opens `RemoveReasonDialog`:
* 7 radio categories with kebab-case keys matching the backend taxonomy.
* Optional textarea (required when `Other` is selected — submit button is disabled until the user provides text).
* Cancel button disabled while submission is in flight.
* Server `detail` surfaces inline (red banner) on error instead of bubbling to a generic toast.

### 3.3 · Assignment History drawer (admin only)
Replaces the inline expanding panel.
* Trigger: `data-testid=open-history-drawer` shows total count "History (N)".
* Drawer slides in from the right (`sm:max-w-xl`); content is the full audit feed.
* Newest-first by `at` ISO string, defensively re-sorted client-side.
* Each row: action badge (color-coded) · target email · role (or `old → new` for role_change) · italicised notes · "by {actor}".
* Read-only — no edit/delete affordances. Closes on Esc or outside-click.

---

## 4 · Test-id surface

| Element | data-testid |
|---|---|
| Inline role select per row | `row-role-{assignment_id}` |
| Role select option | `row-role-{assignment_id}-opt-{role_key}` |
| Remove button per row | `row-remove-{assignment_id}` |
| Remove reason dialog | `remove-reason-dialog` |
| Reason radio per category | `reason-{category}` |
| Reason category group | `reason-category-group` |
| Reason text area | `reason-text` |
| Reason error | `reason-error` |
| Reason cancel | `reason-cancel` |
| Reason submit | `reason-submit` |
| History trigger button | `open-history-drawer` |
| History drawer | `assignment-history-drawer` |
| History list container | `history-list` |
| History row by action | `history-row-{assign\|role_change\|update\|remove}` |
| History empty state | `history-empty` |

All other existing testids on the panel (add-member dialog, primary toggle, transfer, scope notes) are preserved unchanged.

---

## 5 · ResizeObserver loop suppressor (defensive)

Radix UI Select/Sheet animations emit benign `ResizeObserver loop completed with undelivered notifications` warnings. CRA's dev overlay treats these as fatal errors and blocks clicks. The suppressor in `/app/frontend/src/index.js` listens at `window.error` and `window.unhandledrejection`, matches the substring case-insensitively, and calls `stopImmediatePropagation()` + `preventDefault()` to keep the dev overlay quiet without hiding real errors. Production builds don't render the overlay so this is dev-only-visible — kept narrow to that exact message.

---

## 6 · Hard rules respected

* No backend changes
* No new endpoints
* No new collections
* PM scope unchanged where designed (no inline role select, no history drawer)
* PM scope CAN remove via the structured dialog (PM `/api/pm/job/.../team/{id}` DELETE accepted the same JSON body in Track 15.39)
* Shadcn components only · no custom Dialog/Sheet rolls
* Every interactive element has a unique `data-testid`

---

## 7 · Five Pillars (post-cert self-rating)

| Pillar | Score | Note |
|---|---|---|
| Powerful | 9 | Operators can change/remove/audit assignments from the browser without backend workarounds. |
| Simple | 9 | One inline Select for role change. One dialog for structured remove. One drawer for full history. |
| Beautiful | 9 | Color-coded audit badges + iPad-safe drawer width + no clipped dialogs at 768×1024. |
| Trusted | 9 | Server `detail` shown verbatim on 409; "other" textarea blocked client-side so backend 400 is never hit. |
| Proven | 9 | Iter524 smoke + Iter525 (T1/T2/T3/Add-member PASS) + Iter526 (T4/T5/T6/PM PASS). |

🟢 **Track 15.39A — Team Assignment P2 frontend COMPLETE.**
