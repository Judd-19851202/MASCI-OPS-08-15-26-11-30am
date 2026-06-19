# TRACK 15.39A · Team Assignment P2 Frontend Certification

**Date:** 2026-06-19
**Track:** 15.39A · Team Assignment P2 Frontend Completion
**Status:** 🟢 CERTIFIED — 7 of 7 tests PASS across 3 viewports
**Backend:** Track 15.39 (certified, not modified)

---

## 1 · Cert iterations summary

| Iteration | Scope | Result |
|---|---|---|
| `iteration_524.json` | Smoke — login, page load, all testids mounted | PASS (infra only) |
| `iteration_525.json` | T1 Change Role + revert · T2 409 duplicate guard · T3 structured Remove · Add-member regression | **4/4 PASS** (T4-T6 blocked by Radix ResizeObserver dev overlay) |
| `iteration_526.json` | T4 Other-requires-text · T5 History Drawer · T6 Viewport matrix · PM-scope regression | **4/4 PASS** after dev overlay suppressor merged |

---

## 2 · Detailed test evidence

### T1 — Inline Change Role
* **Source:** iter525
* Foreman row (`9a9bfc3d-c740-4ef8-9f58-9afad29b3e8c`) Select opened, picked `assistant_superintendent`. Sonner success toast `"Role changed to Assistant Superintendent"` confirmed.
* After hard reload, row appeared under Assistant Superintendent group; Select trigger value reflected new role.
* Audit feed showed exactly ONE `role_change` event for this assignment id — NOT a synthetic remove+add pair.
* Reverted back to `foreman` the same way; row id remained `9a9bfc3d-...` (no new assignment created).
* **Status: PASS**

### T2 — Duplicate role guard (409)
* **Source:** iter525
* While foreman row held `foreman`, opened safety_rep row Select (`61447c6f-8ae3-4544-a7e5-d18d5bd91616`) and chose `foreman`.
* Sonner error toast contained the exact server detail substring `"already holds the Foreman role on this project"`.
* After hard reload, safety_rep row Select still showed `Safety Representative` — no mutation persisted.
* **Status: PASS**

### T3 — Remove with structured reason
* **Source:** iter525
* Clicked `row-remove-61447c6f-...`, picked `reason-reassigned`, typed text, submitted.
* DELETE returned 200 with JSON body `{reason_category:"reassigned", reason_text:"<text>"}`.
* safety_rep row disappeared from active list on reload.
* New audit `remove` event appeared in history with reason text.
* **Status: PASS** (safety_rep was re-seeded by iter525 as `34b4aba2-...`, then by main agent as `453e5110-...` for subsequent T4-T6 runs)

### T4 — Other requires text
* **Source:** iter526
* Opened dialog on safety_rep row (`453e5110-2b6b-4a5c-aa33-130cce3b33fd`).
* Clicked `reason-other` → `reason-submit` confirmed **disabled**.
* Typed `"hi"` into `reason-text` → `reason-submit` confirmed **enabled**.
* Cleared textarea → `reason-submit` confirmed **disabled again**.
* Clicked `reason-cancel` → dialog closed, safety_rep row remained (no mutation).
* **Status: PASS**

### T5 — Assignment History Drawer
* **Source:** iter526
* Clicked `open-history-drawer` → drawer slid in from right.
* Counted: `history-row-assign = 8`, `history-row-role_change = 5`, `history-row-remove = 6` (all ≥ 1) · total 20 rows.
* Row[0] ASSIGNED `6/19/2026 1:10:25 PM`, Row[1] REMOVED `6/19/2026 1:07:11 PM` — newest-first ordering confirmed.
* Each row contained `by Admin` actor field substring.
* Escape key dismissed drawer cleanly (`assignment-history-drawer` count → 0).
* **Status: PASS**

### T6 — Viewport matrix
* **Source:** iter526
* Tested at Desktop 1920×800, iPad portrait 768×1024, iPad landscape 1024×768.
* Drawer rendered correctly at all three viewports.
* Remove dialog bbox stayed within viewport at every viewport:
  * Desktop: x=736, y=111, w=448, h=578
  * iPad-P: x=160, y=223, w=448, h=578
  * iPad-L: x=288, y=95, w=448, h=578
* No horizontal scroll on any viewport (`documentElement.scrollWidth ≤ window.innerWidth + 2`).
* **Status: PASS**

### Regression — Add Member
* **Source:** iter525
* `job-team-add-btn` opened `job-team-add-form` dialog with role + employee pickers.
* Cancel closed cleanly without mutation.
* **Status: PASS**

### Regression — PM scope
* **Source:** iter526
* Logged out admin (`masci.*` localStorage cleared), logged in as `pm.demo@mascigc.com / PmTest2026!` at `/pm/login`.
* Navigated to `/pm/job/20-07/team` (note: singular `job` in PM route).
* Asserted **admin-only surfaces are hidden** for PM:
  * `open-history-drawer` count = 0 ✓
  * `row-role-9a9bfc3d-...` count = 0 ✓ (no inline role Select for PM)
* Asserted **PM-allowed flow works**:
  * `row-remove-9a9bfc3d-...` count = 1 ✓
  * Clicking it opened `remove-reason-dialog` ✓
  * `reason-cancel` closed dialog cleanly ✓
* **Status: PASS**

---

## 3 · Outstanding notes (NOT failures)

* **Display name fallback** — Foreman & Safety Rep rows render `"Unknown person — Admin review required"` because the directory link for `c9d7ebc3-a292-4d7a-8765-0ce2739c6029` is broken. **Out of scope for Track 15.39A** per main agent's test brief. Tests target rows by `data-testid` assignment id, not by name.
* **PM login form** — `/pm/login` does not expose `data-testid` attributes (`pm-email-input` etc). Test fell back to generic `input[type=email]` selectors which worked. Filed as a minor testability improvement.
* **ResizeObserver loop suppressor** — `/app/frontend/src/index.js` adds a narrow listener to swallow the benign Radix Select/Sheet warning that the CRA dev overlay treats as fatal. Production builds have no overlay so this is dev-only-visible. Acceptable as-is.

---

## 4 · Five Pillars final score

| Pillar | Score | Evidence |
|---|---|---|
| Powerful  | **9** | Operators can change/remove/audit project team assignments from the browser without backend workarounds. |
| Simple    | **9** | One inline Select. One structured dialog. One read-only drawer. No hidden actions. |
| Beautiful | **9** | iPad-safe at 768×1024, color-coded audit badges, no clipped dialogs across 3 viewports. |
| Trusted   | **9** | Server 409 detail surfaces verbatim; "other" textarea client-side blocks the 400 path. |
| Proven    | **9** | iter524 + iter525 + iter526 → 7/7 PASS across 3 viewports + PM-scope regression PASS. |

---

## 5 · Final state of fixture (preserved)

Project `20-07` · Alec Perkins (`c9d7ebc3-a292-4d7a-8765-0ce2739c6029`):
* foreman → `9a9bfc3d-c740-4ef8-9f58-9afad29b3e8c` (stable from T0 seed)
* safety_rep → `453e5110-2b6b-4a5c-aa33-130cce3b33fd` (re-seeded after T3 by main agent)

Fixture left intact for operator inspection. Optional teardown is documented in §0.5 of the handoff plan.

🟢 **TRACK 15.39A · TEAM ASSIGNMENT P2 FRONTEND · COMPLETE & CERTIFIED.**

> "MASCI operators can now add, change, remove, and audit project team assignments from the browser without backend-only workarounds. The frontend uses certified backend endpoints exclusively, supports desktop + iPad portrait + iPad landscape, and emits a single canonical audit row per intent."
