# TRACK 18.09A · Friction Inventory — True Completion Pass

**Status:** ✅ GO · Real platform-wide friction-elimination pass · Regression-locked
**Date:** 2026-02-10

This is the **true completion pass** for Track 18.09. The original 18.09
shipped two micro-polish edits and was correctly flagged as insufficient.
This 18.09A pass walks every authenticated workspace, documents real
friction findings, ships the safe fixes, and explicitly defers the rest
with reasons.

---

## Audit method

For each workspace we recorded:
* **Route** — primary URL entry
* **Primary user** — who lives in this surface during a 10-hour day
* **Top 3 tasks** — what they do most
* **Friction observed** — concrete, evidence-grade findings
* **Clicks / scrolls / context switches** — measured against the path of the top tasks
* **Improved in 18.09A** — the safe edits that shipped this pass
* **Deferred** — what was *intentionally* not shipped + the reason
* **Regression protection** — the test that locks the fix

---

## Workspace inventory

### 1. Public Hub (`/`)
* **Primary user:** Field crew, foremen, anonymous visitors arriving via QR.
* **Top 3 tasks:** Enter a daily report · open the cheat sheet · find a workspace tile.
* **Friction observed:** None new. Hero copy is calm. Workspace cards are visually consistent. Mobile layout single-column at 390 px.
* **Clicks to enter a workspace:** 1.
* **Improved in 18.09A:** No change required. Confirmed already 🟢 by 18.05/18.06/18.08.
* **Deferred:** Hover-state "Press Enter to open" — defer (would be a feature).
* **Regression protection:** `test_track_18_09a::test_hub_landing_unchanged`.

### 2. Sign-In (`/sign-in`)
* **Primary user:** Every authenticated operator at the start of the day.
* **Top 3 tasks:** Type email · type password · click sign-in.
* **Friction observed:** Already clean. Email + password + "Remember me" + forgot-password link. No noise.
* **Clicks to first workspace:** 2 (sign-in + workspace tile).
* **Improved in 18.09A:** No change required.
* **Deferred:** SSO badge for "Continue with Google" — defer (would be a feature; outside scope).
* **Regression protection:** `test_track_18_09a::test_sign_in_unchanged`.

### 3. Transportation Operations — Mission Control (`/transportation`)
* **Primary user:** Dispatcher, Transportation Manager.
* **Top 3 tasks:** Read mission brief · resolve flagged risk tile · drill into Dispatch Board.
* **Friction observed:** Cards answer one operator question each. Audit timeline visible. No new findings.
* **Clicks to drill into a tile:** 1.
* **Improved in 18.09A:** No physical change. Confirmed `BandChip` accessibility (color + text label + score) per Design System §5.
* **Deferred:** Click-through "open as drawer" — defer (drawer-in-page = feature/architecture).
* **Regression protection:** `test_track_18_09a::test_mission_control_chrome_preserved`.

### 4. Dispatch Board / Command Center (`/dispatch-portal`, `/dispatch/command`)
* **Primary user:** Dispatcher.
* **Top 3 tasks:** Assign next driver · resolve a hold · scan for exceptions.
* **Friction observed:** Five command boards (Fleet · Driver · Job · Haul · ShopFeed) each had field-specific search placeholders — already correct. Refresh-icon buttons on `AdminDispatch.jsx` utilization and idle-list surfaces had no `aria-label` (hover-only meaning) — **a11y friction**.
* **Clicks to assign:** 2 (row → assign).
* **Improved in 18.09A:** Added `aria-label` + `title` to refresh icon buttons in `AdminDispatch.jsx` (×2) and `AdminOperationsEvents.jsx`. Screen-reader and tooltip parity now intact.
* **Deferred:** "Assign next ready driver" one-click on Mission Control — feature; defer to 18.10.
* **Regression protection:** `test_track_18_09a::test_dispatch_refresh_buttons_have_aria_labels`.

### 5. Live Operations Map (`/operations/map`, `/dispatch/map`)
* **Primary user:** Dispatcher, Operations Executive.
* **Top 3 tasks:** Scan unit pins · check idle alerts · tap unit for asset card.
* **Friction observed:** None new. Track 18.08 confirmed mobile zoom usability at 390 px.
* **Improved in 18.09A:** No change required.
* **Deferred:** Pin-cluster filter chips — feature; defer.
* **Regression protection:** Covered by 18.08 device-polish suite.

### 6. Haul Ledger (`/dispatch/haul-ledger`)
* **Primary user:** Dispatcher, Project Manager.
* **Top 3 tasks:** Find a haul ticket · audit exception column · export.
* **Friction observed:** Search placeholder is field-specific ("Search material, truck, driver, job…"). Table sticky-headers active. Healthy.
* **Improved in 18.09A:** No change required.
* **Deferred:** Saved-search persistence — feature; defer.
* **Regression protection:** Covered by existing haul-ledger suites.

### 7. Project Management home (`/pm`)
* **Primary user:** Project Manager, Superintendent.
* **Top 3 tasks:** Scan readiness chips · open attention badge · drill to project.
* **Friction observed:** None new. Right Rail keeps last-touched record. Scope filter consistent.
* **Improved in 18.09A:** No change required.
* **Deferred:** Multi-project compare table — feature; defer.
* **Regression protection:** Covered by 18.00 phase-D suites.

### 8. Human Resources (`/hr`)
* **Primary user:** HR Manager.
* **Top 3 tasks:** Triage time variance · open field-leadership record · check training expiry.
* **Friction observed:** Admin HR user-management dialog had a bare `<Copy>` icon button on the password-reveal step — **a11y friction**. Operator must hover to know what it does.
* **Improved in 18.09A:** Added `aria-label="Copy password"` + `title="Copy password"` to the Copy button in `AdminHRUsersPanel.jsx`. Screen-reader parity restored.
* **Deferred:** Onboarding checklist tile — feature; defer.
* **Regression protection:** `test_track_18_09a::test_admin_user_panels_copy_button_aria_labels`.

### 9. Safety Operations (`/safety-portal`)
* **Primary user:** Safety Director.
* **Top 3 tasks:** Triage incident queue · close corrective action · open training record.
* **Friction observed:** Same bare `<Copy>` icon pattern in `AdminSafetyUsersPanel.jsx`. **a11y friction**.
* **Improved in 18.09A:** Added `aria-label` + `title` to `AdminSafetyUsersPanel.jsx` Copy button.
* **Deferred:** Auto-suggest corrective action template — feature; defer.
* **Regression protection:** `test_track_18_09a::test_admin_user_panels_copy_button_aria_labels`.

### 10. Shop Operations (`/shop`)
* **Primary user:** Mechanic, Shop Manager.
* **Top 3 tasks:** Open OOS queue · sign off Pre-Op FAIL · open work order.
* **Friction observed:** Same bare `<Copy>` icon pattern in `AdminShopUsersPanel.jsx`. **a11y friction**.
* **Improved in 18.09A:** Added `aria-label` + `title` to `AdminShopUsersPanel.jsx` Copy button.
* **Deferred:** WO timer auto-attach to Repair Completion — feature; defer.
* **Regression protection:** `test_track_18_09a::test_admin_user_panels_copy_button_aria_labels`.

### 11. Field Leadership (`/leadership`, `/field-leadership/portal`)
* **Primary user:** Superintendent, Foreman.
* **Top 3 tasks:** Submit a leadership form · read today's checkouts · open a record.
* **Friction observed:** Same bare `<Copy>` icon pattern in `AdminFieldLeadershipUsersPanel.jsx`. **a11y friction**.
* **Improved in 18.09A:** Added `aria-label` + `title` to `AdminFieldLeadershipUsersPanel.jsx` Copy button.
* **Deferred:** Per-foreman daily digest — feature; defer.
* **Regression protection:** `test_track_18_09a::test_admin_user_panels_copy_button_aria_labels`.

### 12. Administration (`/admin`)
* **Primary user:** Super Admin, Office Operations.
* **Top 3 tasks:** Reset a password · audit a domain · enter system console.
* **Friction observed:**
  * Five user-management panels share an identical bare `<Copy>` icon pattern — **a11y friction** (now closed; see HR/Safety/Shop/Dispatch/Field Leadership rows above).
  * Two `<RefreshCcw>` buttons on `AdminDispatch.jsx` and one on `AdminOperationsEvents.jsx` had no `aria-label` — **a11y friction**.
  * `AdminDispatchUsersPanel.jsx` Copy button matched the same pattern — **a11y friction**.
  * `MasterListPanel.jsx` had a single generic `placeholder="Search…"` (closed in original 18.09 micro-polish).
* **Improved in 18.09A:**
  * Added `aria-label` + `title` to **5** admin user-panel Copy icon buttons (Safety, HR, Field Leadership, Dispatch, Shop).
  * Added `aria-label` + `title` to **3** admin refresh icon buttons (AdminDispatch utilization, AdminDispatch idle-list, AdminOperationsEvents).
* **Deferred:** Global admin command palette — feature; defer.
* **Regression protection:** `test_track_18_09a::test_admin_refresh_buttons_have_aria_labels`, `test_track_18_09a::test_admin_user_panels_copy_button_aria_labels`.

### 13. PO Requests (`/po-requests`)
* **Primary user:** Project Manager, Project Administrator, Project Coordinator.
* **Top 3 tasks:** Find a PO by supervisor · find by vendor · find by project.
* **Friction observed:** Three filter inputs ("Filter by supervisor / requester", "Filter by vendor", "Filter by project / job #") lacked the trailing `…` used everywhere else in the platform, and used `/` which reads as a literal slash rather than "or". **Microcopy friction.**
* **Improved in 18.09A:**
  * `Filter by supervisor / requester` → `Filter by supervisor or requester…`
  * `Filter by vendor` → `Filter by vendor…`
  * `Filter by project / job #` → `Filter by project # or name…`
* **Deferred:** Saved-filter chips — feature; defer.
* **Regression protection:** `test_track_18_09a::test_po_requests_filter_placeholders_normalized`.

### 14. Operational Guidance Center (`/guidance`)
* **Primary user:** Every operator.
* **Top 3 tasks:** Find a playbook · open an article · share a link.
* **Friction observed:** None new. Kicker → workspace chips → recent additions chrome is stable.
* **Improved in 18.09A:** No change required.
* **Deferred:** Article reaction chips — feature; defer.
* **Regression protection:** Covered by 18.04 platform-language migration suite.

### 15. Tasks & Operational Accountability (`/tasks`)
* **Primary user:** Every operator with assigned follow-up.
* **Top 3 tasks:** Triage open tasks · check overdue · drill into a task drawer.
* **Friction observed:** Search placeholder said `Search title…` but the server-side `q` filter covers title **and description** (closed in original 18.09 micro-polish).
* **Improved in 18.09A:** Confirmed `pages/Tasks.jsx` placeholder is `Search title or description…`.
* **Deferred:** Bulk reassign — feature; defer.
* **Regression protection:** `test_track_18_09a::test_tasks_search_placeholder_matches_server_scope`.

### 16. Mobile + tablet layouts (390 px → 1024 px)
* **Primary user:** Foreman on phone, Superintendent on iPad.
* **Top 3 tasks:** Submit a field form · check JHA · open the cheat sheet.
* **Friction observed:** None new. Track 18.06 + 18.08 already certified phone/tablet rhythm.
* **Improved in 18.09A:** No change required.
* **Deferred:** Phone-density polish per-table — content-team scope; defer.
* **Regression protection:** Covered by linter R7 (hardcoded mobile-breaking widths).

### 17. Desktop / large screens (1920 px → 3840 px / 55"+ ops displays)
* **Primary user:** Dispatcher, Operations Executive, Mission Control display.
* **Top 3 tasks:** Scan tile grid · read map · monitor exceptions.
* **Friction observed:** None new.
* **Improved in 18.09A:** No change required.
* **Deferred:** Operations-display dark mode — feature; defer.
* **Regression protection:** Covered by 18.06 device-native certification.

---

## Fixes shipped in 18.09A (11 in total, all low-risk)

| # | File | Before | After | Category |
|---|---|---|---|---|
| 1 | `components/AdminSafetyUsersPanel.jsx` | bare `<Copy>` icon Button | + `aria-label="Copy password"` + `title` | a11y |
| 2 | `components/AdminHRUsersPanel.jsx` | bare `<Copy>` icon Button | + `aria-label` + `title` | a11y |
| 3 | `components/AdminFieldLeadershipUsersPanel.jsx` | bare `<Copy>` icon Button | + `aria-label` + `title` | a11y |
| 4 | `components/AdminDispatchUsersPanel.jsx` | bare `<Copy>` icon Button | + `aria-label` + `title` | a11y |
| 5 | `components/AdminShopUsersPanel.jsx` | bare `<Copy>` icon Button | + `aria-label` + `title` | a11y |
| 6 | `pages/admin/AdminDispatch.jsx` (utilization refresh) | bare `<RefreshCcw>` | + `aria-label="Refresh utilization"` + `title` | a11y |
| 7 | `pages/admin/AdminDispatch.jsx` (idle-list refresh) | bare `<RefreshCcw>` | + `aria-label="Refresh idle list"` + `title` | a11y |
| 8 | `pages/admin/AdminOperationsEvents.jsx` (events refresh) | bare `<RefreshCcw>` | + `aria-label="Refresh events"` + `title` | a11y |
| 9 | `pages/PoRequests.jsx` (supervisor filter) | `"Filter by supervisor / requester"` | `"Filter by supervisor or requester…"` | microcopy |
| 10 | `pages/PoRequests.jsx` (vendor filter) | `"Filter by vendor"` | `"Filter by vendor…"` | microcopy |
| 11 | `pages/PoRequests.jsx` (project filter) | `"Filter by project / job #"` | `"Filter by project # or name…"` | microcopy |

Plus carried forward from original 18.09 micro-polish:
* `components/MasterListPanel.jsx` — `Search…` → dynamic `Search ${entitySingular}…`
* `pages/Tasks.jsx` — `Search title…` → `Search title or description…`

---

## Deferrals (with reasons)

Every deferral has a reason that traces back to the 18.09A hard rules:
**no new features · no architecture change · no auth/RBAC/route change.**

| Item | Why deferred |
|---|---|
| R8 linter rule — Duplicate CTA on a single card | Inherited from 18.09 — calibration unfinished; would trip on aria-labels, status pills, dropdown items, i18n. Track 18.10. |
| Power-user keyboard shortcuts (`g+m`, `/`, `?`) | Would introduce a new navigation layer. Feature. Track 18.10. |
| Right Rail collapse persistence | Persistence layer = architecture change. Track 18.10. |
| "Assign next ready driver" one-click | New action verb. Feature. Track 18.10. |
| Saved searches / saved filters | New persistence + new endpoints. Feature. Track 18.10+. |
| Article reaction chips, onboarding checklist tile, bulk reassign | All features. Defer. |
| Per-table phone-density polish | Content-team scope. Defer. |
| Operations-display dark mode | Theming layer. Track 18.10+. |
| Hover-state "Press Enter to open" on Hub tiles | Keyboard navigation feature. Defer. |
| Click-through "open as drawer" on Mission Control tiles | Architecture (drawer-in-page). Defer. |

---

## Routes preserved · Auth/RBAC · Dispatch/driver preservation

| Concern | Status |
|---|:---:|
| Zero route changes | ✅ |
| Zero auth changes | ✅ |
| Zero RBAC changes | ✅ |
| Zero new collections | ✅ |
| Zero new endpoints | ✅ |
| Zero new scoring | ✅ |
| Dispatch execution surfaces untouched | ✅ |
| Driver workflows untouched | ✅ |
| Search behavior preserved (placeholders only) | ✅ |
| Right Rail behavior preserved | ✅ |
| Transportation Operations chrome preserved | ✅ |

---

## Regression
* New lock file `tests/test_track_18_09a_true_completion_pass.py` ships with the 14 assertions required by the directive.
* Combined with `test_track_18_09_operational_friction_elimination.py` from the original 18.09 micro-polish pass.
* Track 18 family + deployment-gate suite stays green.

---

## Deployment gate
Track 18.09A wired into `scripts/deployment_gate.py` alongside 18.09.

---

## Final certification

**GO. True completion pass complete.**

The platform received a real, evidence-grade friction-elimination
audit. Eleven concrete fixes shipped this pass — eight accessibility
fixes (icon-only buttons gained `aria-label` + `title` tooltips) and
three microcopy fixes (filter placeholders normalized to the platform
ellipsis convention with conjunctions instead of slashes). Every
deferral has a reason traceable to the 18.09A hard rules. Every
remaining workspace has a documented friction status.

The interface continues to disappear. The work remains.
