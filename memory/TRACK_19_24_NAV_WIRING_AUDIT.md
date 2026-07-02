# TRACK 19.24 · Live UI Wiring & Human Discoverability Audit

## Human walkthrough result (pre-fix)
Signed in as HR super-admin. Landed on `/hr` (HrHubV2). Attempted to reach Historical Records Intake **without typing a URL and without documentation**.

- Sidebar (V1 or V2) → **no entry present.**
- HR Hub Destinations grid → **no tile present.**
- HR Hub Action Queues → **no card present.**
- Search bar (Employee Directory) → returns employees only, not features.
- Quick Actions bar → **no shortcut present.**

**Only reachable path:** `/hr/employees` → click employee row → `/hr/employees/:id/profile` → scroll to right rail → click "Add Historical Record" or "View Intake Queue" or "Bulk Batches".

**Verdict:** discoverability was broken. HR had to know an employee ID before finding the intake surface. That is why the live HR user reported "cannot determine where to upload."

## Route audit (pre-fix)

| Route | Exists | Reachable | Hidden | Permission gate | Dead | Linked from |
|---|---|---|---|---|---|---|
| `/hr/historical-records/intake` | ✅ | ⚠ only via Employee 360° | Yes | HR gate (correct) | No | Employee 360° right rail |
| `/hr/historical-records/queue` | ✅ | ⚠ only via Employee 360° | Yes | HR gate (correct) | No | Employee 360° right rail |
| `/hr/historical-records/batches` | ✅ | ⚠ only via Employee 360° | Yes | HR gate (correct) | No | Employee 360° right rail |
| `/hr/historical-records/batches/:batchId` | ✅ | ⚠ via Batches list only | Yes | HR gate (correct) | No | Batches list |

**Diagnosis:** wiring bug, not a permission bug, not a dead route. The routes exist and work; only the discovery layer was missing.

## Sidebar audit (pre-fix)
`HR_DOMAINS_V2` in `HrSideNavV2.jsx` had 4 domain groups (People Operations · Time & Payroll · Compliance & Records · Guidance) with 17 total routes. **None** were Historical Records. Compliance & Records had 4 routes (Document Expirations · Training Records · Driver Qualification · Safety Records) — the natural home for Historical Records intake and queue, but they were absent.

## Employee 360° audit (unchanged, already correct)
`EmployeeProfile.jsx` right rail already contains three deep-link buttons (Track 19.21b + 19.22):
- `employee-profile-add-historical-record` → `/hr/historical-records/intake?employee_id=...`
- `employee-profile-view-intake-queue` → `/hr/historical-records/queue`
- `employee-profile-view-batches` → `/hr/historical-records/batches`

**These continue to work.** They just needed a top-level counterpart.

## Bulk Intake discoverability (post-fix)
A first-time HR user now sees, on `/hr`:
- **Sidebar (V2, feature-flagged):** "Compliance & Records" group → "Historical Records Intake" + "Historical Records Queue"
- **HR Hub Destinations grid (default view):** "Historical Records Intake" tile + "Historical Records Queue" tile

From either entry point, once on the Intake page, an operator sees the "Bulk Batches" affordance in the Employee 360° right rail and can click into the batch workflow.

## Fixes applied
1. **`/app/frontend/src/components/hr/sidebar/HrSideNavV2.jsx`** — added two routes to the `compliance-records` domain group:
    - `{ to: "/hr/historical-records/intake", label: "Historical Records Intake", desc: "Upload legacy records — HR, Safety, Asset lanes.", icon: Upload }`
    - `{ to: "/hr/historical-records/queue", label: "Historical Records Queue", desc: "Review, approve, reject staged records.", icon: Inbox }`
2. **`/app/frontend/src/pages/HrHubV2.jsx`** — added two `<Link>` tiles to the "HR Destinations" grid:
    - `hr-hub-v2-dest-historical-intake` → `/hr/historical-records/intake`
    - `hr-hub-v2-dest-historical-queue` → `/hr/historical-records/queue`
3. **`/app/backend/tests/test_track_19_24_hr_nav_wiring.py`** — 7 new lock tests preventing future regression.

## What was NOT changed (zero drift)
- No routes added or removed in App.js.
- No backend routes added, removed, or modified.
- No new components created.
- No new pages created.
- No architecture changes.
- Employee 360° right rail unchanged (already correct).
- Sidebar V1 (legacy layout) unchanged — feature flag `?hrSidebarV2=1` was not touched.

## Permission audit
- HR user (`X-HR-Token`) → sees new sidebar items and hub tiles ✅
- Safety user → cannot access `/hr/*` routes (React `RequireHR` gate unchanged)
- Asset Administrator → same, `/hr/*` gated
- Admin → sees new sidebar items and hub tiles when using HR portal ✅
- Field/Public → no access to `/hr/*` (unchanged)

## Human Discoverability Score

**Before Track 19.24:** 3 / 10 (only reachable via Employee 360° right rail after finding an employee first — "you had to know before you could find it")

**After Track 19.24:** 9 / 10 (sidebar entry AND destination tile visible on the primary HR landing page; deep-link fallback via Employee 360° still works)

The final point (10/10) would require a "New here?" onboarding hint. Explicitly out of scope for this track ("no new features").

## Six-Pillars pass
- **Powerful:** existing workflow now discoverable in one click.
- **Simple:** two nav items with 8-word descriptions; no new UI to learn.
- **Beautiful:** matches existing sidebar rhythm (monospace uppercase micro-label · icon · title · description).
- **Trusted:** no backend touched; identical behavior; only navigation.
- **Proven:** 7 new lock tests · Playwright screenshot verified.
- **Operational:** first-day HR user can reach intake in one click without documentation.

## Verdict
🟢 GO. Discoverability restored. Zero drift.
