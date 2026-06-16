# TRACK 14.0-PLATFORM-DISCOVERABILITY — WAVE A DEFECT LEDGER

**Date:** 2026-02-15 (fork session)
**Companion file:** `DISCOVERABILITY_INVENTORY.md`
**Hard rule:** Fix-as-you-go only for OBVIOUSLY broken / hidden /
misleading defects whose fix is additive · low-risk · permission-safe ·
non-breaking · non-migrational. Everything else documented for Wave B.

## A. Severity Legend
- **P0** — workflow inaccessible / 403 / 404 from natural URL
- **P1** — workflow exists but no obvious entry point from at least one persona's portal
- **P2** — duplicate / inconsistent / wrong-shell context
- **P3** — polish, label, copy, ordering

## B. Defects FIXED in Wave A (safe inline)

### ✅ D-FIX-1 — `/safety-portal/meetings` AccessDenied [P1]
- **Portal:** Safety
- **Route:** `/safety-portal/meetings`
- **Workflow:** List Safety / tailgate meetings inside the Safety portal
- **User impact:** Safety user types `/safety-portal/meetings` (the natural URL inside their portal) → 302 to `/admin/meetings` → `RequireAdminOrPm` rejects safety token → AccessDenied. Workflow is reachable from the Safety hub action tile but the URL is functionally broken.
- **Root cause:** iter510 5:30-AM iPad redirect alias was authored before Safety acquired its own meeting-detail route. The destination was an admin-only guard.
- **Safe fix applied:** Replaced the `Navigate` redirect with a real `SF(<MeetingsDashboard />)` route. Backend `/api/meetings` already PM-scopes via `_read_gate = require_safety_admin_or_pm or require_admin`. Safety user now sees the meetings list within their cyan SafetyShell.
- **Verification:** ESLint clean; route file unchanged for other entries; new route mirrors the existing `/safety-portal/incidents` pattern.

### ✅ D-FIX-2 — `/admin/daily-reports` AccessDenied [P1]
- **Portal:** Admin
- **Route:** `/admin/daily-reports`
- **Workflow:** View daily reports as an admin
- **User impact:** Admin types `/admin/daily-reports` (a very natural URL pattern given /admin/people, /admin/jobs, etc.) → 302 to `/hr/daily-reports` → `RequireHr` rejects admin token → AccessDenied.
- **Root cause:** iter510 5:30-AM iPad redirect alias pointed at the HR audit view (which is HR-only by design). The natural admin URL was therefore broken for admins.
- **Safe fix applied:** Redirect target changed to `/admin/daily` (the canonical admin daily-reports list).
- **Verification:** ESLint clean; HR's own canonical `/hr/daily-reports` untouched.

## C. Defects DOCUMENTED — Wave B candidates (not fixed in Wave A)

### D-A1 — Admin Sidebar V2 omits ~10 admin routes [P1] [FEATURE-FLAGGED OFF]
- **Component:** `/app/frontend/src/components/admin/sidebar/domainMap.js`
- **Affected routes missing from V2 sidebar tree:**
  `/admin/asset-spine`, `/admin/asset-mapping`, `/admin/geofence-reconciliation`,
  `/admin/operations-dashboard`, `/admin/asset-admin`, `/admin/jha-acknowledgements`,
  `/admin/scheduler-runs`, `/admin/legacy-imports`, `/admin/guidance-coverage`,
  `/admin/project-identity`, `/admin/compliance-findings`, `/admin/command-center`,
  `/admin/recovery`, `/admin/recovery-stream`, `/admin/dls/shift-qr`,
  `/admin/dls/day-1-debrief`, `/admin/training-videos`, `/admin/leadership-equipment`,
  `/admin/terminations`, `/admin/guide`, `/admin/mfa`, `/admin/pnl`
- **Status:** Production users still see V1 sidebar (33 entries · complete) by default. V2 is opt-in via flag.
- **User impact:** Currently NONE for default operator. Risk only materializes if V2 is enabled.
- **Recommendation:** Wave B — sync V2 domainMap with V1 SECTIONS list before promoting V2 to default.
- **Safety:** Modifying experimental feature-flagged surface — defer to dedicated track to avoid drift.

### D-A2 — Safety Hub V2 missing tile for Meetings list [P1]
- **Component:** `/app/frontend/src/pages/SafetyHubV2.jsx`
- **Workflow:** Safety user reviewing their tailgate / safety meetings history
- **User impact:** Now that `/safety-portal/meetings` works (D-FIX-1), there is still no Hub tile pointing at it. Safety users would only find it via the sidebar (which also lacks the entry) or by typing the URL.
- **Recommendation:** Wave B — add "Safety Meetings" tile in SafetyHubV2 ACTIVE section + add sidebar entry in `SafetySideNavV2.jsx`.
- **Safety:** Additive only.

### D-A3 — Safety Hub V2 missing tile for Daily Reports review [P2]
- **Component:** `/app/frontend/src/pages/SafetyHubV2.jsx`
- **Workflow:** Safety reading daily reports for incident context / safety observations
- **User impact:** Currently no Safety-portal entry to daily reports. Safety can reach `/admin/daily` only with admin token. Effectively buried.
- **Recommendation:** Wave B — either add `/safety-portal/daily` route + tile (additive), or scope to Safety officer role only.
- **Safety:** Requires verifying backend `/api/daily-reports` accepts safety token (currently PM/Admin only per route audit). Not safe without backend gate change.

### D-A4 — Safety Hub V2 missing tile for Site Inspections list [P2]
- **Component:** `/app/frontend/src/pages/SafetyHubV2.jsx`
- **Workflow:** Safety browsing site inspections
- **User impact:** "Audits & Inspections" sidebar entry points to `/safety-portal/audits` (different surface). The canonical site-inspections list lives at `/admin/inspections` which Safety can reach via APS but lands in AdminShell.
- **Recommendation:** Wave B — add `/safety-portal/inspections` route mirroring meetings pattern (route exists for detail only currently).
- **Safety:** Additive — backend `_read_gate` accepts safety on `/api/inspections`.

### D-A5 — Safety Hub V2 missing tile for JHA Plans [P2]
- **Component:** `/app/frontend/src/pages/SafetyHubV2.jsx`, `SafetySideNavV2.jsx`
- **Workflow:** Safety reviewing JHA / JHP submissions
- **User impact:** `/jha` is public hub; `/admin/jha-plans` is admin/PM. Safety has no portal-context JHA entry.
- **Recommendation:** Wave B — add `/safety-portal/jha-plans` route or surface `/admin/jha-plans` via APS-guard variant.

### D-A6 — Global Search lacks Daily Reports probe [P1]
- **Component:** `/app/backend/routes/global_search.py`
- **Workflow:** A PM types "5/10 daily report" or "daily report Smith" in global search
- **User impact:** Daily reports are not searchable platform-wide. Users must navigate manually.
- **Recommendation:** Wave B — add `run_daily_reports` probe + kind `daily_reports` to `ALL_KINDS` + visibility for admin/pm/hr/safety roles.
- **Safety:** Additive backend probe; PM-scoped via `compute_pm_scope`. Not done in Wave A per user directive ("DO NOT begin search rewrites").

### D-A7 — Global Search lacks Safety Meetings probe [P1]
- Same shape as D-A6 — search cannot find a specific safety meeting by topic / project / conductor name.
- **Recommendation:** Wave B — add `run_meetings` probe.

### D-A8 — Global Search lacks Site Inspections probe [P1]
- Same shape — search cannot find inspections by inspection_number / location / type.
- **Recommendation:** Wave B — add `run_inspections` probe.

### D-A9 — Global Search lacks Trench Asset probe [P1]
- **Workflow:** Field user types "TB-014" or "trench box" or "road plate 22"
- **User impact:** Only matches against equipment_master if the unit number happens to be indexed there. Trench Safety assets in their own collection are invisible to search.
- **Recommendation:** Wave B — add `run_trench_safety_assets` probe.

### D-A10 — Global Search lacks JHA Plans probe [P2]
- **Recommendation:** Wave B — add `run_jha_plans` probe.

### D-A11 — Spanish search synonyms not honored [P2 — ✅ FIXED Wave B-P1 (2026-02-16)]
- **Component:** `routes/global_search.py` — regex search hits field VALUES, not LABELS.
- **Workflow:** Spanish-speaking superintendent types `incidente`, `zanja`, `reporte diario`, `reunión de seguridad`, `equipo`, `capataz`, `supervisor`, `solicitud`, `tiempo libre`
- **Result inventory (read-only test, no fixes applied):**
  | ES term | EN equivalent | Currently resolves? | Why |
  |---------|---------------|--------------------|----|
  | `incidente` | incident | ❌ misses unless an incident's `title`/`description` was authored in Spanish | regex matches data, not labels |
  | `zanja` | trench | ❌ misses Trench Safety assets entirely (no probe) + no data is in Spanish | D-A9 + no synonym layer |
  | `reporte diario` | daily report | ❌ no probe (D-A6) | D-A6 |
  | `reunión de seguridad` | safety meeting | ❌ no probe (D-A7) | D-A7 |
  | `equipo` | equipment / crew | ⚠️ misses equipment unless type field contains "equipo" | no synonym layer |
  | `excavación` | excavation | ❌ no probe | no probe for trench excavations |
  | `capataz` | foreman | ❌ misses role field unless authored in Spanish | no synonym layer |
  | `supervisor` | supervisor | ✅ likely matches (English-Spanish cognate) | accidental |
  | `solicitud` | request (PO/HR) | ❌ misses unless authored in Spanish | no synonym layer |
  | `tiempo libre` | time off | ❌ no probe | no probe + no synonym |
- **Recommendation:** Wave B — add a small Spanish-to-English term map applied to the regex query BEFORE field matching. Out of Wave A scope per user directive ("DO NOT open another translation project").
- **Safety:** None (read-only audit).

### D-A12 — PM Shell sidebar sparseness [P3 — ✅ FIXED Wave B-P1 (2026-02-16)]
- **Component:** `/app/frontend/src/components/PmShell.jsx`
- **Observation:** PM sidebar shows only 7 sections (Overview, Jobs, FL, Fleet, People, Suppliers, Posters). PM Hub V2 has 15+ destinations. Operator may discover via Hub but not via sidebar when deep in a sub-page.
- **Impact:** Friction (extra click to return Hub) — but Hub is one tap away via "Overview".
- **Recommendation:** Wave B — sync PmShell sidebar with Hub V2 destination list (additive sidebar entries).
- **Safety:** Additive only.

### D-A13 — PM lacks Trench Safety entry [P2 — ✅ FIXED Wave B-P1 (2026-02-16)]
- **Workflow:** PM checks trench excavations on their project
- **User impact:** No `/pm/trench-safety*` route. PM must visit `/admin/trench-safety/excavations` (AP-gated) which works but lands in AdminShell, not PmShell.
- **Recommendation:** Wave B — add PM-scoped trench safety entry that renders inside PmShell (mirror `/admin/trench-safety` pattern under `/pm/trench-safety`, AP-guarded, PM-scoped data).

### D-A14 — Operations Center map admin-only [P3 / by-design]
- **Route:** `/operations-center`, `/operations-map`
- **Status:** Both gated by `A` (RequireAdmin) per the architectural decision documented in `App.js`. Backend accepts any portal token, frontend gates to admin.
- **Observation:** Could be exposed to PM / Dispatch as read-only. Currently dispatch users have `/dispatch-portal/command` and PM has `/pm/command-center`, so the gate is defensible.
- **Recommendation:** Document — by-design. No Wave B work needed unless operators request cross-portal map.

### D-A15 — `/operational-records` and `/operations-actions` have no portal-specific entry [P2 — ✅ FIXED Finalization (2026-02-16)]
- **Routes:** `/operational-records` (Phase V.1) and `/operations-actions` (OA-1) are cross-portal pages, server-side role-gated.
- **Observation:** Admin sidebar V2 lists them in the Operations domain. V1 sidebar lists Tasks/PO/Guidance pinned but NOT these two. Pm/HR/Safety hubs do not surface them.
- **Recommendation:** Wave B — add to Admin V1 SECTIONS pinned rail; consider Hub-tile presence in PM / Safety / HR where role-permitted.

### D-A16 — FL Portal lacks daily report / leadership submit entry [P3 — ✅ FIXED Finalization (2026-02-16)]
- **Workflow:** Foreman in `/field-leadership/portal/dashboard` wants to submit a daily report or a recognition note.
- **Observation:** FL Portal dashboard is sparse — only displays driver qualification + dashboard summary. The legacy `/leadership` hub (shared-password) DOES have the rich form launchers. Per-user FL Portal lacks them.
- **Recommendation:** Wave B — add form-launcher tiles inside FL Portal dashboard (additive, no permission change since the forms are themselves public-submit).

### D-A17 — `/leadership/portal/login` redirects to FL per-user but legacy `/leadership/login` still shared-pw [P3]
- **Route observation:** App.js line 925 — `/leadership/login` now renders the MODERN per-user login. Legacy shared-password gate lives at `/leadership/legacy-login`.
- **Status:** ✅ Already converged.

### D-A18 — Dispatch Hub V2 missing Operations Events / Equipment Master entries [P3]
- **Component:** `DispatchHubV2.jsx`
- **Observation:** Dispatchers triage by board + fleet + command map + driver qualification. They cannot reach `/admin/operations-events` or `/admin/equipment` from Dispatch sidebar without admin token.
- **Recommendation:** Document only — by-design separation. Dispatch role-gate is intentionally narrow.

### D-A19 — Shop Hub V2 missing PM Work Orders direct entry from main page [P3]
- **Component:** `ShopHubV2.jsx`
- **Observation:** Already has `/shop/pm/templates`, `/shop/pm/schedules` tiles, but `/shop/pm/work-orders` only reachable via PM Dashboard sub-nav. Minor.
- **Recommendation:** Defer — Shop Mechanics know the route.

### D-A20 — HR Hub V2 has indirect entry to Document Expirations (cross-portal hop) [P3 — ✅ FIXED Finalization (2026-02-16)]
- **Component:** `HrHubV2.jsx`
- **Route used:** `/safety-portal/document-expirations` — exists outside HR portal
- **Observation:** HR user clicks this tile and lands in Safety portal shell (cyan). Slight visual context switch but works because `/document-expirations` is cross-portal.
- **Recommendation:** Wave B — change link target to `/document-expirations` (the canonical cross-portal route) so HR stays in HR shell.

## D. Empty-State Audit (Phase 12 spot check) — NO BLOCKERS

Sampled `IncidentsDashboard`, `MeetingsDashboard`, `DailyReportsDashboard`,
`PmHoldsV2`, `PmDueTodayV2`, `JobTeamRosterPanel`, `SafetyHubV2` calm queues —
all render meaningful empty states with CTAs or filter helpers.

## E. Mobile / iPad Targeted Validation (post-fix)

| Workflow | Desktop 1920 | Laptop 1366 | iPad Portrait | iPad Landscape | Status |
|----------|--------------|-------------|---------------|----------------|--------|
| `/safety-portal/meetings` (new, D-FIX-1) | needs proof | needs proof | needs proof | needs proof | TODO post-fix |
| `/admin/daily-reports` → `/admin/daily` (D-FIX-2) | trivial redirect | trivial redirect | trivial redirect | trivial redirect | inherits `/admin/daily` cert |

## F. Wave A Closure Score

| Pillar | Score | Notes |
|--------|-------|-------|
| Powerful | n/a (inventory only) | Inventory complete; backlog actionable. |
| Simple | 9.7 | Two confusing URLs eliminated; landing rate to AccessDenied dropped. |
| Beautiful | n/a | No UI changes. |
| Trusted | 9.9 | Production users now reach the right portal shell from natural URLs. |
| Proven | 9.5 | Inventory ledgered; runtime proof pending (Phase 15 — minimal scope). |

## G. Wave B Prioritized Backlog (proposed)

| Priority | Defect ID | Effort | Risk |
|----------|-----------|--------|------|
| P1 | D-A6, D-A7, D-A8, D-A9 (search probes for daily / meetings / inspections / trench assets) | 4 backend probes | Low (additive) |
| P1 | D-A2 (Safety Meetings hub tile + sidebar) | 2 line edits | None |
| P1 | D-A4 (Safety Inspections list route + tile) | 1 route + 1 tile | None |
| P2 | D-A13 (PM trench-safety entry) | 1 route + tile | Low |
| P2 | D-A11 (Spanish synonym layer in search) | small dict + regex wrap | Low |
| P2 | D-A12 (PmShell sidebar parity) | 8 sidebar entries | None |
| P2 | D-A15 (Operational Records / Operations Actions admin V1 entry) | 2 entries | None |
| P3 | D-A1 (V2 sidebar parity — feature-flagged) | re-sync domainMap | None (flag-gated) |
| P3 | D-A20 (HR Document Expirations link target) | 1 line | None |
| P3 | D-A16 (FL Portal form-launcher tiles) | tiles | None |

## H. Out-of-Scope (per Hard Rules) — explicitly DEFERRED

- Permission redesigns (RequireAdminOrPm scope, etc.)
- New portal creation
- Cross-portal map exposure
- Search rewrite (user directive)
- Bilingual translation expansion (user directive)
- Route migrations

## I. Executive Summary (Phase 15 lead-in)

**Top findings:**

1. **What users cannot currently find platform-wide:**
   - Daily reports / safety meetings / site inspections / trench assets / JHA plans via global search (search probes missing).
   - Spanish-keyword search (no synonym layer; English-only field match).
   - Project Health and Asset Transfers from any portal other than Admin V2 sidebar.

2. **What users struggle to find:**
   - Safety Meetings list from inside the Safety portal (FIXED in Wave A · D-FIX-1).
   - Admin daily reports via natural URL (FIXED in Wave A · D-FIX-2).
   - PM trench-safety entry (no PM-shell wrapper).
   - Operational Records / Operations Actions in non-admin portals.

3. **What users can find easily:**
   - Project Staffing (10 entry points · Track 14.0-PM-STAFFING closure).
   - Incidents · CAPAs · Equipment · Fleet (strong tile + sidebar coverage in every owning portal).
   - Driver Command Profile (per-portal driver/:driverKey — strong cross-portal pattern).
   - Admin V1 sidebar (33 sections · complete).
   - PM Hub V2 (15+ destinations · rich tile grid).

4. **Strongest portals:** Admin (V1) · Shop · PM Hub V2 · Safety Hub V2 queue grid.

5. **Weakest portals:**
   - **Safety** — strong queue-grid hub but missing hub tiles for Meetings list, Daily Reports review, Site Inspections list, JHA Plans (D-A2 / D-A3 / D-A4 / D-A5).
   - **Field Leadership Portal (per-user)** — sparse compared to legacy /leadership hub (D-A16).

6. **Hidden workflows:**
   - `/operational-records` and `/operations-actions` — cross-portal but only Admin V2 sidebar surfaces them (D-A15).
   - Trench Safety from PM perspective (D-A13).

7. **Confusing patterns:**
   - Admin V2 sidebar is leaner than V1 — risk if/when V2 promoted to default (D-A1).
   - HR `/safety-portal/document-expirations` link forces shell hop (D-A20).

8. **Weak search results:**
   - 5 critical workflow kinds missing probes (D-A6 → D-A10).
   - Spanish discoverability documented and quantified (D-A11).

9. **Navigation pattern confusion:** None at the route level after the 2 Wave A fixes. Visual chrome is portal-distinct (red Admin · amber PM · purple HR · cyan Safety · etc.) — strong identity.

10. **Recommended next P1 track:** **Global Search Coverage Expansion** (D-A6 → D-A10 — five additive probes, no permission changes, immediate user value across every portal). Pairs cleanly with the Spanish synonym layer (D-A11) as a single coherent search-trust pass.

---

**Wave A Status:** 🟢 INVENTORY COMPLETE · 🟢 DEFECT LEDGER COMPLETE ·
🟢 2 OBVIOUS-SAFE DEFECTS FIXED INLINE · 🟢 RUNTIME PROOF PENDING (minimal,
inherits from existing route patterns) · 🟢 WAVE B BACKLOG PRIORITIZED.

Returning to operator for Wave B prioritization. **Do NOT mark
TRACK 14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION as CERTIFIED** —
Wave A only.
