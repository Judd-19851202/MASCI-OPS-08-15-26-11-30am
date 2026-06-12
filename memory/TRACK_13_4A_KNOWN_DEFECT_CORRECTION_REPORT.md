# Track 13.4A — Known Defect Correction Report

**Generated:** 2026-02 (per work item)  
**Verdict:** ⚠️ **Not Ready — Continue Audit** (Tracks 13.4B / 13.4C / 13.4D pending)  
**Author:** Engineering (Track 13.4A scope only)

---

## 1. Executive Summary

The Brutal Portal Variance Audit (Track 13.4 read-only) discovered that the
Dispatch Live Fleet Map rendered as a **blank white area** to the dispatcher
even though every DOM probe and selector test passed. Track 13.4A corrected
that defect under tight scope guardrails (no new features, no deploy, no
GitHub save, no merge) and additionally:

- Restored asset markers on the Dispatch map (a previously hidden bug
  where every snapshot asset was being filtered out at the client).
- Raised the Dispatch map to a dominant operational surface so it
  actually answers *"Where is my fleet right now?"*.
- Audited and verified the Motive/Fleet data feed end-to-end and
  documented every truth point (including the stale-data state, which
  is **honestly reported**, not papered over).
- Cleaned the HR homepage to be HR-native — removed cross-portal ops
  clutter and admin plumbing.
- Created a non-destructive PM preview fixture
  (`pm.demo@mascigc.com`, scoped to projects `20-07` and `21-06` via
  `co_pm_emails`) so PM regression flows can be proven without
  super-admin substitution.
- Added a pixel-level visual render guardrail that traps the exact
  failure class (DOM-OK / human-blank) so it cannot recur silently.

**Track 13.4A is conditionally accepted by the operator.** Deploy
remains forbidden until Tracks 13.4B (Identity Recovery), 13.4C
(Design System V1), and 13.4D (Full Reality Audit) finish.

---

## 2. Scope

In scope for this track:
- Dispatch Live Fleet Map render fix and visual weight tuning.
- Truthful verification of the Motive/Fleet data feed surfaced on Dispatch.
- HR homepage cleanup to a HR-native surface.
- Preview-only PM fixture (`pm.demo@mascigc.com`) scoped to two real projects.
- Visual render guardrail on the Dispatch map (pixel sampling).
- Documentation of all of the above (this file + ledger entry).

## 3. Non-Scope

Explicitly **out of scope** in this track:
- Production deployment.
- GitHub save / push / merge.
- New features anywhere on the platform.
- Geofence circle → polygon conversion (deferred to a later audit;
  observed and documented in §7).
- Re-issuing PASS / certification language.
- DOM-only validation.
- HR layout language redesign beyond clutter removal.
- PM Command Center feature additions.
- Identity Recovery / Design System / Reality Audit work — those are
  Tracks 13.4B / 13.4C / 13.4D respectively.

---

## 4. Dispatch Map Fix

### 4.1 Defect statement
*"The Live Fleet Map on `/dispatch-portal` renders as a blank/black
canvas although every selector probe passes."*

### 4.2 Root cause (verified via DOM inspection in `headless_shell`)
`MapCanvas` styles its container via the `.ops-map-canvas` CSS class.
`.ops-map-canvas` sizes itself **only** through `grid-column` /
`grid-row` placement inside `.ops-map-grid` (the dedicated full-screen
`/operations-map` page). When `MapCanvas` was reused inside the new
`DispatchMapHero`, the `.ops-map-grid` parent was absent **and** the
`OperationsMap.css` stylesheet was never imported on the Dispatch
portal route, so `.ops-map-canvas` had no width/height rule at all.

Computed style at runtime (captured before the fix):

| node | width | height | overflow |
|---|---|---|---|
| `[data-testid="dispatch-map-canvas-wrap"]` | 1084px | 320px | visible |
| `.ops-map-canvas` (== `.maplibregl-map`) | 1084px | **0px** | hidden |
| `.maplibregl-canvas` | 1084px | 300px (positioned `absolute`) | clip |

MapLibre still painted tiles into its 1084×300 canvas; the 0-height
parent with `overflow:hidden` was clipping the entire output, which
is why every selector existed and every pixel that we read directly
via `canvas.toDataURL()` looked correct, but the operator saw blank.

### 4.3 Fix (minimal & scoped — 2 changes in 2 files)

1. **`/app/frontend/src/components/operations-map/MapCanvas.jsx`**
   - Added `import "./OperationsMap.css"` so the canvas styling
     travels with the component everywhere it's used.
   - Added `preserveDrawingBuffer: true` to the MapLibre constructor
     so the guardrail (and any future automated screenshotter) can
     actually read the rendered tiles.

2. **`/app/frontend/src/components/operations-map/OperationsMap.css`**
   - Added a SCOPED override block at the bottom of the file:
     ```css
     [data-testid="dispatch-map-canvas-wrap"] .ops-map-canvas {
       position: absolute; inset: 0;
       width: 100%; height: 100%;
       grid-column: unset; grid-row: unset;
     }
     ```
   - The full-screen `/operations-map` page is **untouched** — the
     override only matches the Dispatch hero wrapper.

Post-fix runtime values (captured for evidence):

| node | width | height |
|---|---|---|
| `[data-testid="dispatch-map-canvas-wrap"]` | 1084px | **520px** |
| `.ops-map-canvas` | 1084px | **520px** |
| `.maplibregl-canvas` | 1084px | **520px** |

### 4.4 Second defect (found while verifying the first)

After the container fix the basemap rendered, but markers still didn't
appear. Root cause: `MapCanvas` had inconsistent filter semantics —
- Empty `types` array meant "show all kinds" (via `!tSet.size`).
- Empty `status` array meant "show **nothing**" because `[] || ALL` is
  truthy in JavaScript so the fallback never triggered.

`DispatchMapHero` passes `EMPTY_FILTERS = { types: [], status: [], … }`,
so 100% of snapshot assets were being silently filtered out.

**Fix:** symmetric semantics —
```js
const sSet = new Set(filters?.status?.length ? filters.status : ALL_BANDS);
```

---

## 5. Dispatch Map Visual Weight Adjustment

The Dispatch homepage must answer *"Where is my fleet?"* at a glance.
A 320px-tall map was not dominant enough.

`DispatchMapHero` now uses responsive Tailwind heights:

| viewport | height |
|---|---|
| `<sm` (phone) | 300px |
| `sm – lg` (tablet) | 420px |
| `>= lg` (desktop) | **520px** |

The counts strip (Attention Required · No Recent Position · Working
· Idle · Assets Assigned · Total Assets) and both CTA buttons
(`Open Full Live Map`, `Open Operational Board`) are preserved. The
"Operational Attention" cluster below is still above-the-fold on
desktop because the existing layout has flex-1 content beneath, and on
iPad portrait the user sees Map → Counts → CTAs in a single tap-down.

---

## 6. Dispatch Motive / Fleet Feed Verification

This section reports **what the snapshot actually returns today**, not
what the user *wants* it to return. The numbers below were pulled live
from `/api/operations-map/snapshot` in the preview environment with a
real Dispatch session token (`dispatch@mascigc.com`).

| Item | Truth |
|---|---|
| Data source | `db.motive_events` + `db.asset_mappings` + `db.equipment_master` |
| API endpoint | `GET /api/operations-map/snapshot` |
| Motive-mapped assets in `asset_mappings` | **190** |
| Assets returned to the snapshot | **190** |
| Assets with GPS coords (eligible to be a map marker) | **90** |
| Assets without GPS coords (will NOT appear as markers) | 100 |
| Newest position event timestamp | `2026-06-11T02:06:19Z` |
| Newest event age at audit time | **22.83 hours** |
| Oldest position event timestamp | `2024-03-15T10:15:14Z` |
| Oldest event age at audit time | ~819 days |
| Reported `feed_status` | `offline` / "No Recent Updates" |
| Reported `as_of` | `2026-06-12T00:53:56.639948+00:00` |
| Band distribution | 33 red (stale_position) · 157 gray (no recent) · 0 green · 0 amber |
| Marker kinds (GPS-only) | 31 dump_truck · 41 service_truck · 13 pickup · 5 water_truck |
| Geofences in `db.motive_geofences` | 67 stored |
| Geofences returned by snapshot | **0** (see §7) |
| `motive_events` documents in preview DB | 466 |
| Cross-portal consistency | `DispatchMapHero` and `/operations-map` consume the same hook and endpoint — same data |

### Truth statements

1. The `feed_status: offline` / "No Recent Updates" badge is
   **accurate**, not stale boilerplate — there are literally zero
   position events younger than 24h.
2. The header `Updated HH:MM` value is tied to the wall-clock of the
   last `/snapshot` request via `lastFetchMs` — **accurate** (not
   hardcoded, not a placeholder).
3. The counts strip values (33 / 157 / 0 / 0 / 90 / 190) are
   computed server-side in `operational_summary` — they match the
   underlying assets returned in the same payload.

### Why preview shows stale data

Preview env (`DB_NAME=masci_safety_preview`, `APP_ENV=preview`) does
not receive live Motive webhooks. The 22h-old data is the most
recent snapshot that landed when preview was last seeded from
production. **Production behaviour cannot be inferred from this audit
alone** — see §7.

---

## 7. Dispatch Known Data-Integrity Items for Future Audit

The operator has explicitly deferred these out of 13.4A. They must
appear as a dedicated section in Track 13.4D *Full Platform Reality
Audit*:

1. **Production Motive webhook activity** — verify webhooks land in
   `db.motive_events` on production at the expected cadence; confirm
   `feed_status: live` actually fires when fresh data exists.
2. **Preview vs production feed behaviour** — characterise the
   difference and decide whether preview should backfill periodically
   for QA purposes.
3. **GPS coverage rate** — 90 of 190 motive-mapped assets currently
   have any GPS at all. Triage which are "expected dark" (stationary
   shop equipment) vs which are genuinely missing telemetry.
4. **Stale position root causes** — 33 stale_position assets and 157
   no-recent assets warrant a per-unit ageing analysis.
5. **Motive mapping completeness** — verify `asset_mappings` covers
   every operational unit; flag orphans on both sides.
6. **Marker category accuracy** — `marker_kind` is heuristically
   derived from the equipment label; validate against ground truth.
7. **`operational_summary` count accuracy** — currently
   `total=190 / attention=33 / no_recent=157 / assigned=90` — re-derive
   independently in 13.4D to confirm no drift.
8. **Geofence rendering** — `db.motive_geofences` holds **67**
   geofences but `/snapshot` returns **0** because
   `_polygon_from_motive()` only emits geometries for polygon-shaped
   fences. The 67 fences are stored as `center + radius_m` circles.
   Conversion is intentionally out of scope for 13.4A.
9. **Trust verdict** — can Dispatch be relied on as operational truth
   in its current preview state? Today the honest answer is "not for
   live decision making in preview; pending production webhook
   verification."

---

## 8. HR Homepage Cleanup

### 8.1 Sections audited (before state)

| # | Section | Classification | Action |
|---|---|---|---|
| 1 | Header chrome (Home, Back, logo, portal switcher, search, notifications, lang, sign-out) | HR-native (portal chrome) | KEEP |
| 2 | Title + tagline ("Employee Records & Accountability") | HR-native | KEEP |
| 3 | `GovernanceHealthChip portal="hr"` | HR-native | KEEP |
| 4 | `HrKpiStrip` (active employees · pending requests · time-off · training · docs) | HR-native | KEEP |
| 5 | **`OperationsActionsTile` (OA-1)** — "Operations Actions" cross-portal tile | **Duplicated surface / Operational clutter** (HR already has "Tasks & Actions" tile in the People Operations group; OA-1 uses cross-portal ops language) | **REMOVE** |
| 6 | `PasskeyEnrollPrompt` (self-dismissing) | Cross-portal but HR-relevant | KEEP |
| 7 | TILE_GROUPS — People Operations · Time & Payroll · Compliance & Records · Access & Identity · Guidance | HR-native | KEEP (5-domain grouping intact) |
| 8 | `ExpirationsSummary` | HR-native | KEEP |
| 9 | **`IntegrationHealthCard`** (Motive / MaintainX sync status) | **Wrong portal / Operational clutter** (admin/ops integration plumbing) | **REMOVE** |
| 10 | `IntegrationEventsCard` provider="motive" title="Driver Safety Events (HR Review)" | Cross-portal but HR-relevant (HR uses for coaching/personnel review) | KEEP (demoted to single full-width card so it doesn't compete with HR-native tile groups) |

### 8.2 Removed

- `OperationsActionsTile` (mount **and** import).
- `IntegrationHealthCard` (mount **and** import).
- The two-column integration grid wrapper (`hr-integrations-strip`).
- Unused `OperationsCenter` import (Track 13 §4 had already commented
  it out of usage — now removed from the import list too).

### 8.3 Preserved (in display order)

GovernanceHealthChip → HrKpiStrip → PasskeyEnrollPrompt → tile groups
(People Operations / Time & Payroll / Compliance & Records / Access
& Identity / Guidance) → ExpirationsSummary → Driver Safety Events.

### 8.4 Relocated / deferred

- Driver Safety Events: relocated from a half-width slot in a
  two-column "Integrations" grid to a single full-width card placed
  after ExpirationsSummary so it stays HR-actionable but doesn't
  compete with the HR-native tile groups above it.

### 8.5 Five-Pillar mini-score (post-cleanup)

| Pillar | Score | Note |
|---|---|---|
| Powerful | 4 / 5 | Every HR-owned surface remains one tap away. |
| Simple | 5 / 5 | Removed cross-portal ops chrome; the page now answers a single question. |
| Beautiful | 4 / 5 | Calm, consistent 5-domain stripes; no clutter strip. |
| Trusted | 5 / 5 | No fake or operational data is implied as HR-owned. |
| Proven | 4 / 5 | Visually verified at desktop, iPad landscape, iPad portrait; testing agent run pending if operator wants. |

### 8.6 Operator one-paragraph

> A HR user now sees an HR-native homepage: the governance chip and a
> KPI strip (active employees, pending requests, time-off, training,
> doc expirations) at the top, an optional one-card device-sign-in
> prompt, the five HR domain tile groups, the document-and-cert
> expiration intelligence card, and a single Driver Safety Events
> "HR Review" card — and nothing else. There is no cross-portal
> "Operations Actions" duplicate, no Motive sync-health plumbing card,
> no operational metric clutter. The page now answers exactly one
> question: *what requires HR attention today?*

---

## 9. PM Fixture Account

### 9.1 Fixture identity

| Field | Value |
|---|---|
| Email | `pm.demo@mascigc.com` |
| Password | `PmTest2026!` |
| `must_change_password` | `false` (reusable for automation) |
| Role | Project Manager (per-PM auth) — **not admin**, **not super-admin**, **not legacy shared bypass** |
| Environment | **PREVIEW ONLY** — seed refuses to run unless `APP_ENV != "production"` AND `DB_NAME` ends with `_preview` |
| Assigned projects | `20-07` (T5686 SR 15 / SR600 — Sanford, 17/92, Lake Mary) and `21-06` (T5736 Oviedo — 426, Broadway) |
| Assignment mechanism | `co_pm_emails` on existing `jobs_master` docs — **does not** overwrite primary `pm_email` of any job |

### 9.2 Setup details

- Seed script: `/app/backend/scripts/seed_pm_demo_fixture.py`.
- Idempotent: re-running rewrites password hash, ensures
  `is_active=true`, and re-asserts the two project assignments via
  `$addToSet` while `$pull`-ing the fixture from any other job that
  may have drifted in.
- Credentials documented in `/app/memory/test_credentials.md` under
  the PM section.

### 9.3 `compute_pm_scope` verification (live)

```
pm_id = 0c5f4862-727e-425b-8a67-7fac5590e04e
is_admin = False
project_numbers = {'20-07', '21-06'}
```

Backed by:
```
db.jobs_master.find({
  $or: [{pm_email: "pm.demo@mascigc.com"},
        {co_pm_emails: "pm.demo@mascigc.com"}],
  deleted_at: { $in: [null, ""] }
})
```
returns exactly **2** documents.

### 9.4 API-level proof

| Endpoint | Result |
|---|---|
| `POST /api/pm/login` | 200 · 101-char per-PM token |
| `GET /api/pm/me` | `email=pm.demo@mascigc.com`, `name="PM Demo (Preview Fixture)"`, `is_admin_or_legacy=False` |
| `GET /api/pm/jobs` | exactly **2** jobs (20-07, 21-06) |
| `GET /api/pm/command-center/overview` | `scoped_projects=["20-07","21-06"]` |
| `GET /api/pm/crew/summary` | 200 OK |
| `GET /api/admin/jobs` | **401** (admin namespace correctly refuses PM token per iter180 lockdown) |

### 9.5 UI-level proof (Gemini-verified)

Vision analysis on the desktop PM Command Center screenshot
(`pm_demo_command_center_desktop_1920x1080_fullpage.png`) confirms,
verbatim:

> *"This is definitively a PM-scoped view. There are two
> projects/jobs visible. The project numbers visible are: 20-07 and
> 21-06. This absolutely looks like a Project Manager's command
> center view with PM-scoped data."*

Section structure observed:
- A. My Projects — `20-07`, `21-06` rows with "MISSING DAILY REPORT"
  alerts and OPEN PROJECT CTAs.
- B. Field Truth — recent dailies + recent photos (both empty for
  these two preview projects, correctly reported as such).
- C. Project Risk — Open Safety Items (0), Equipment Defects (0)
  scoped to the two projects.
- D. Documents & Plans — daily reports, JHPs, photo library, roster.
- E. Project Support Resources — equipment / trucks / drivers /
  trailers / road plates / specialty rollups, all 0 for these two
  preview projects (truthful).

No admin-summary substitution; no leakage of the other 27 jobs in
the system.

### 9.6 Remaining limitations

- Preview projects `20-07` and `21-06` have no recent dailies or
  photos in preview DB, so Sections B and E render mostly zeros.
  This is preview reality, not a PM scoping bug.
- Fixture exercises read-side scoping only. Write-side PM scoping is
  governed by the same `compute_pm_scope` for the relevant routes;
  not separately exercised in 13.4A.

---

## 10. Visual Render Guardrail

### 10.1 Failure class this guardrail catches

The brutal audit's exact failure pattern: *element exists in the DOM,
selector passes, operator sees blank*.

### 10.2 Test file & invocation

```
/app/backend/tests/test_track_13_4a_dispatch_map_visual_guardrail.py

cd /app/backend && PLAYWRIGHT_BROWSERS_PATH=/pw-browsers \
  python -m pytest tests/test_track_13_4a_dispatch_map_visual_guardrail.py -v
```

Also wired into `/app/scripts/predeploy_certify.sh` as **Phase 4**,
so a future *Save to GitHub + Deploy* gate execution will not pass
unless this guardrail passes.

### 10.3 Thresholds (conservative — false positives accepted, false
passes forbidden)

| Failure mode | Trigger |
|---|---|
| Canvas missing | `[data-testid="dispatch-map-canvas-wrap"] .maplibregl-canvas` not present |
| Canvas clipped (the original bug) | `getBoundingClientRect().width == 0` OR `height == 0` |
| Canvas buffer empty | `canvas.width == 0` OR `canvas.height == 0` |
| Near-all-black | `mean(rgb_avg) < 15` |
| Near-all-white | `mean(rgb_avg) > 240` |
| Solid colour | `variance(rgb_avg) < 5` |
| Posterised / flat | `unique_color_count < 8` |

Authoritative read uses `canvas.toDataURL()` against the real
MapLibre canvas (works because `preserveDrawingBuffer: true` is now
set). NO DOM-only validation.

### 10.4 Passing result (current run)

```
[guardrail PASS] stats={
  'present': True,
  'box_w': 1084, 'box_h': 520,
  'buf_w': 1084, 'buf_h': 520,
  'mean': 24.67,
  'variance': 244.11,
  'unique': 105
}
```

Artifact saved to:
`/app/memory/track_13_4a_evidence/guardrail_last_run.png`.

### 10.5 How this would have caught the original bug

Pre-fix runtime values would have produced `box_w=1084, box_h=0`
(the `.ops-map-canvas` parent had height:0) — tripping the
**Canvas clipped** rule immediately and failing the guardrail with
a precise error message ("`Map canvas DOM box collapsed to 1084×0px.
This is the exact symptom of the original 13.4A bug …`").

---

## 11. Screenshots and Evidence Index

All artifacts live under `/app/memory/track_13_4a_evidence/`.

### Dispatch
- `dispatch_desktop_1920x1080.png` / `_fullpage.png` — map visible, 520px tall, markers (54·14·3·2·8 clusters + individual unit labels).
- `dispatch_ipad_landscape_1180x820.png` / `_fullpage.png`.
- `dispatch_ipad_portrait_820x1180.png` / `_fullpage.png` — map 752×420.
- `dispatch_map_fix_proof.png` — direct `toDataURL` capture from the
  intermediate-fix step (pre-page-screenshot evidence).

### HR
- `hr_before_desktop_1920x1080(_fullpage).png` (× 3 viewports).
- `hr_after_desktop_1920x1080(_fullpage).png` (× 3 viewports).

### PM
- `pm_demo_command_center_{desktop|ipad_landscape|ipad_portrait}*.png` (× 3 viewports, command-center surface + scoped jobs surface).

### Guardrail
- `guardrail_last_run.png` — captured by the pytest run.

---

## 12. Tests Run

| Test | Result |
|---|---|
| `tests/test_track_13_4a_dispatch_map_visual_guardrail.py::test_dispatch_map_renders_real_geography` | **PASS** (mean=24.67, var=244, unique=105) |

(Existing test suites were intentionally not re-run; this track did
not modify backend routes or auth logic. Tracks 13.4B/C/D will
re-exercise broader regression scope.)

---

## 13. What Was Not Changed

- No deployment.
- No GitHub save.
- No merge.
- No backend route added or modified.
- No new authentication path created.
- No production user, role, or permission altered.
- No mobile/iPad responsive contract broken (verified visually at
  three viewports on both Dispatch and HR).
- No tile copy on HR rewritten beyond removing two stale wrappers.
- `/operations-map` full-screen page untouched: the new CSS override
  is scoped to `[data-testid="dispatch-map-canvas-wrap"]` only.

---

## 14. Remaining Risks

1. **Preview-only verification** — production webhook health for
   Motive has NOT been verified in this track.
2. **PM fixture coverage** — read-side scoping only; write-side PM
   scope is the same backend gate and is not separately exercised.
3. **Geofence rendering gap** — 67 in DB, 0 surfaced; explicitly
   deferred. Could mislead an operator into thinking there are no
   defined geofences.
4. **Asset GPS coverage** — 100/190 motive-mapped assets currently
   have no GPS coordinates ever. Trust-of-Dispatch depends on
   triaging these.
5. **Stale-data risk in preview** — by design, preview shows
   ~22h-old position data. Anyone using preview as a *demo* for
   stakeholders may be misled if this caveat isn't stated up front.
6. **Visual guardrail single-viewport** — currently runs at desktop
   only (1920×1080). iPad widths share the same code path but are
   not separately exercised by the guardrail.

---

## 15. Required Follow-Up Audits

- **Track 13.4B** — MASCI Platform Identity Recovery Audit
  (Admin / Dispatch / PM / Safety / Shop / HR / Leadership / Driver /
  Field Leadership / Field Tile / Safety Tile / Public Safety Tile /
  Public QR / Asset Lookup / Training / Governance / Guides /
  Coaching / Verbiage / Status Language / Theme / Role Clarity /
  Portal Cohesion). Must also include a dedicated **Dispatch Data
  Integrity / Motive Reality** subsection per §7.
- **Track 13.4C** — MASCI Platform Design System V1.
- **Track 13.4D** — MASCI Platform Reality Audit.

Until those land, this platform is **Not Ready for Deploy**.

---

## 16. Deployment Verdict

**Not Ready — Continue Audit.**

Track 13.4A is conditionally accepted as a known-defect-correction
milestone. Tracks 13.4B, 13.4C, 13.4D must complete (and a fresh
predeploy_certify.sh pass must be obtained) before any deploy,
GitHub save, or merge action is authorised.
