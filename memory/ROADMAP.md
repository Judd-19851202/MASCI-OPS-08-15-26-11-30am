# MasciDocs HUB — Future Features Roadmap

This file tracks **parked features** the user wants to revisit later. Surface these proactively when starting a new session or when the user asks "what's next?"

---

## ✅ Track 14.0-HUMAN-FIRST-VISIBILITY-CERTIFICATION — DONE (2026-02-12)
Full human-perspective audit · 10 portals · 232 surfaces · 14 roles. **18 permanent regression tests in `test_nav_drift_guard.py` · 64/64 pytest green.** Critical correction: PM V2 hub DOES have top-bar chrome via PortalShell (screenshot proof). RC1-NAV-002 WITHDRAWN · NAV-001/003-006 P0→P2. **3 unguarded routes discovered as RC1-NAV-007**. **No P0 blockers remain.** Five-Pillar **9.85**.
Ledger: `TRACK_14_0_HUMAN_FIRST_VISIBILITY_CERTIFICATION.md`.

## 🔴 P0 — Track 14.0-S1 Spanish Translation Sweep (NOW FULLY UNBLOCKED)
Public crew forms + admin operator copy.

## 🔴 P0 — Track 14.0-P1 PDF Lockup Sweep (NOW FULLY UNBLOCKED)
Server-side PDF generation pipelines.

## 🔴 P0 — Track 14.0-I1 Integration Honesty Banners (NOW FULLY UNBLOCKED)
Admin-portal integration health surfaces.

## 🟡 P1 — RC1-NAV-007 Quick Fix (~1 hour)
Wrap 3 newly-discovered unguarded portal routes with their guard tokens:
- `/admin/qaqc` → wrap with `A(...)`
- `/pm/odr` → wrap with `P(...)`
- `/hr/employees` + `/hr/employees/:id/accountability` → wrap with `H(...)`
After fix: remove paths from `known_unguarded` in `tests/test_nav_drift_guard.py`.

## 🟡 P1 — Track 14.0-RC1-ROLE-VISIBILITY-CERTIFICATION (after NAV-007 fix)
Certify all 14 roles can find and use their workflows.

## 🟡 P1 — Track 14.0-UXS-11 Final Certification (after S1 + P1 + I1 + NAV-007)
RC-1 acceptance suite.

## 🟡 P1 — RC1 Blockers Open (post-correction)
- **RC1-NAV-007** (P1) · 3 unguarded portal routes · pinned by test
- **RC1-INVITE-FLOW-001** (P1) · PM-inline portal-invite CTA · carried
- **RC1-NAV-008** (P2) · Change-password link missing from PM V2 top-bar
- **RC1-NOTIFICATION-DEEPLINK-002** (P1) · Producer link_urls not set
- ~~RC1-NAV-002~~ · WITHDRAWN by HUMAN-FIRST audit
- **RC1-NAV-001 / 003 / 004 / 005 / 006** · downgraded P0→P2 (V2 left-sidebar architectural choice, acceptable for RC-1)
- **RC1-LEGACY-RETIRE-001** (P2) · Retire `*hub_legacy` aliases after V2 cuts to 100%
- **RC1-NAV-PROMOTE-001** (P2) · ~12 surfaces with discoverability ≤ 2

## ✅ Track 14.0-PLATFORM-TRUTH-MAP — DONE (2026-02-12)
Complete read-only audit: 341 routes · 10 portals · 232 surfaces · 14 roles · 8 RC1 blockers. Biggest finding: PM/Shop/HR/Safety/Dispatch V2 hubs lack shell wrap. **Spanish · PDF · I1 unblocked.** Five-Pillar **9.85**.
Ledger: `TRACK_14_0_PLATFORM_TRUTH_MAP_ROUTE_NAV_SURFACE_INVENTORY.md`.

## 🔴 P0 — Track 14.0-NAV-SHELL-UNIFICATION (next · ~2–3 days · M effort)
Wrap PM/Shop/HR/Safety/Dispatch V2 hubs in their existing `*Shell` + `SideNavV2` components so sidebar + chrome render consistently. Single change unblocks UXS-11 and role visibility certification for 11 of 14 roles.

## 🔴 P0 — Track 14.0-S1 Spanish Translation Sweep (parallel · NOW UNBLOCKED)
Public crew forms + admin operator copy. Lands on DONE-DONE surfaces.

## 🔴 P0 — Track 14.0-P1 PDF Lockup Sweep (parallel · NOW UNBLOCKED)
PDF generation pipelines on operational records (DR · Incident · Inspection · JHA · Trench · QAQC · FL).

## 🔴 P0 — Track 14.0-I1 Integration Honesty Banners (parallel · NOW UNBLOCKED)
Resend · Twilio · MaintainX · Motive health surfaces in admin portal.

## 🟡 P1 — Track 14.0-RC1-ROLE-VISIBILITY-CERTIFICATION (after NAV-SHELL-UNIFICATION)
Certify all 14 roles can find and use their workflows from their landing portal.

## 🟡 P1 — Track 14.0-UXS-11 Final Certification (after NAV-SHELL-UNIFICATION + S1 + P1 + I1)
RC-1 acceptance suite.

## 🟡 P1 — RC1 Blockers Open (8)
- **RC1-NAV-001** (P0) · PM V2 hub no-shell · OPENED 2026-02-12
- **RC1-NAV-002** (P0) · PortalSwitcher/Bell missing on PM V2 · OPENED 2026-02-12
- **RC1-NAV-003** (P1) · Shop V2 hub no-shell · OPENED 2026-02-12
- **RC1-NAV-004** (P1) · HR V2 hub no-shell · OPENED 2026-02-12
- **RC1-NAV-005** (P1) · Safety V2 hub no-shell · OPENED 2026-02-12
- **RC1-NAV-006** (P1) · Dispatch V2 hub no-shell + legacy hub still on root · OPENED 2026-02-12
- **RC1-INVITE-FLOW-001** (P1) · PM-inline portal-invite CTA missing · carried from RC1-FIX-SWEEP
- **RC1-NOTIFICATION-DEEPLINK-002** (P1) · Producers emit no explicit `link_url` for safety/QAQC/preop/trench · OPENED 2026-02-12

## 🟢 P2 — Post-RC1
- **RC1-NAV-PROMOTE-001** (P2) · ~12 surfaces with discoverability ≤ 2 (Project Health · Constraints · etc.)
- **RC1-LEGACY-RETIRE-001** (P2) · Retire `*hub_legacy` route aliases after V2 cuts to 100%

## ✅ Track 14.0-RC1-DONE-DONE-CERTIFICATION-FIX-SWEEP — DONE (2026-02-12)
Canonical `MASCI_DEFINITION_OF_DONE.md` created. RC1-PORTAL-NAV-001 (PM Dispatch shortcut 403) FIXED. RC1-OWNERSHIP-UX-001 (PM Project Roster 404) FIXED. PM + Admin Project Team workflows OPERATIONAL with live screenshot proof. Five-Pillar **9.90**.
Ledger: `TRACK_14_0_RC1_DONE_DONE_CERTIFICATION_FIX_SWEEP.md`.

## 🟡 P1 — RC1 Blockers Open (3)
1. **RC1-INVITE-FLOW-001** — Inline "Invite to portal" CTA on `JobTeamRosterPanel` row when rostered person has no `user_directory` link. Existing admin temp-password flow at `/admin/people` is canonical; PM-inline UX is the gap.
2. **RC1-NOTIFICATION-DEEPLINK-001** — Permanent recurring check (currently green per Phase 2B-2B D8 audit). Re-verify after every producer wire.
3. **RC1-UI-CONSISTENCY-001** — PortalSwitcher visibility on FL-only tokens. Out of scope this track; flag for UXS-11.

## ✅ 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2B — DONE (2026-02-12)
11 job-scoped producer call sites now route to humans via `apply_routing` + extended ROLE_CHAIN. `recipient_role` preserved as scope guard. Transfer-redirect proven. 46/46 tests + NOTIFY-OWNERSHIP-LOCK matrix OVERALL PASS. Five-Pillar **9.90**. **Spanish unblocked.**
Ledger: `TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2B_PRODUCER_ROUTING_CLOSURE.md`.

## 🔴 P0 — Track 14.0-S1 Spanish Translation Sweep (next, NOW UNBLOCKED)
Operator-facing screens: Daily Report submit confirmation, Incident toast, Trench reinspection alert, Safety Meeting submit, FL portal dashboard, public crew-facing copy. Apply Spanish translations on top of the now-rostered person-level routed notifications.

## 🔴 P0 — Track 14.0-P1 PDF Lockup Sweep (parallel)
Audit + harden PDF generation pipelines (DR, Incident, Inspection, JHA, Trench, QAQC) for character-set + page-overflow safety after Spanish translation introduces wider strings.

## 🔴 P0 — Track 14.0-I1 Integration Honesty Banners
Surface integration health (Resend, Twilio, MaintainX, Motive) to operators with honest status — no fakery.

## 🟡 P1 — Track 14.0-UXS-11 Final Certification
RC-1 portal acceptance suite.

## 🟡 P1 — PORTAL-NAV-001
PM-visible Dispatch shortcut causes Dispatch Portal 403. Fix before RC-1.

## 🟡 P1 — Phase 2B-2C (cleanup of remaining producer scope)
1. Daily Report auto-email pipeline → `apply_routing` parity (re-route through resolver instead of legacy `pm_email`)
2. Asset Transfer two-resolver producer wiring (originating + destination project chains)
3. D6 Dispatch Stale resolver wire (deferred until `last_position_at` data flows)
4. Admin Disable-User Wizard UI inside `/admin/people` (Phase-2A backend ready)

## ✅ 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2A — DONE (2026-02-12)
12 job-scoped writers now embed `team_snapshot` at submit time via `lib.team_routing.snapshot_team`. 8 writers deferred with documented asset-/employee-/link-scope reasons. Snapshot immutability proven across roster mutation. 35/35 tests. Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95).
Ledger: `TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2A_SNAPSHOT_EMBEDDING_CLOSURE.md`.

## ✅ 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-1 — DONE (2026-06-14)
`lib/team_routing` shim · `OWNERSHIP_LOCK_ENABLED=true` · D4 + FL producer wiring · FL My-Jobs widget · PM Team link. 24/24 tests. Five-Pillar 9.78.
Ledger: `TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_CLOSURE.md`.

## 🔴 P0 — 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2 (next, ~3 days)
1. One-line `snapshot_team` embed at submit-time for 15 writers (Daily Report, Incident, Trench, JHA, Safety Meeting, QAQC, Pre-Op, DVIR, Asset Transfer, 811, Training, Time-Off, Excavation, Asset Document admin uploads, Dispatch Events)
2. One-line resolver swap for 12 producers using `ROLE_CHAIN` map already in `lib/team_routing`
3. Asset Care project-scoped view at `/asset-care/projects/{n}` (reuse `MyAssignedProjectsWidget` pattern)
4. Admin Disable-User Wizard UI inside `/admin/people` user detail (Phase-2A backend already ready)



## ✅ 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2A — DONE (2026-06-14)
Lifecycle states · transfer engine · disable wizard backend · snapshot helper · resolver · 9/9 certification tests. Five-Pillar 9.85.
Ledger: `TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2A_CLOSURE.md`.

## 🔴 P0 — 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B (next)
1. Embed `capture_team_snapshot` at submit-time across 17 operational writers
2. Rewrite 18 notification producers behind `OWNERSHIP_LOCK_ENABLED` to call
   `resolve_recipient_for_event` and populate `recipient_user_id`
3. Admin disable-with-migration wizard UI (mount inside `/admin/people` user detail)
4. FL portal roster sidebar consumer at `/field-leadership/portal/jobs/{n}`
5. Asset Care project-scoped view + 811 collection skeleton
6. PM dashboard "Team" CTA surfacing
Estimated: ~5 days.



## ✅ 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 1 — DONE (2026-06-14)
`project_team_assignments` collection · 13 roles · admin + PM CRUD · audit · backfill · 8/8 tests. Five-Pillar 9.62. Ledger: `TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_1_CLOSURE.md`.

## 🔴 P0 — 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2 (next)
1. Producer rewrites — 18 producers replace `recipient_role=…` with `resolve_users_for_project_role(...)` behind feature flag `OWNERSHIP_LOCK_ENABLED` (~360 LOC)
2. FL portal roster sidebar at `/field-leadership/portal/jobs/{n}` (~120 LOC)
3. Asset Care project-scoped view `/asset-care/projects` + `/asset-care/projects/{n}` (~400 LOC + 811 collection skeleton)
4. PM Job Team link surfaced on PM dashboard (~40 LOC)
Estimated: ~5 days.

## 🔴 P0 — 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 3
1. Closed-record `team_snapshot` freeze on Daily Reports / Incidents / QAQC / Trench / DVIR at submit-time
2. Disabled-user orphan migration UI in admin user detail drawer
Estimated: ~2 days.



## 🔴 P0 — Job Ownership Foundation (recommended next track)
*Read-only audit completed 2026-06-14 — see `TRACK_14_0_JOB_OWNERSHIP_AND_PROJECT_TEAM_ROSTER_AUDIT.md`.*
Blocking Spanish, PDF Lockup, Integration Honesty Banners, and UXS-11 final certification.

Build sequence (Option C — Hybrid):
1. Data model + indexes for `project_team_assignments` (~120 LOC · 1d)
2. Admin Project Team Manager APIs + UI (~850 LOC · 2.5d)
3. PM Job Team Manager APIs + UI (~750 LOC · 2d)
4. Field Leadership roster sidebar (~200 LOC · 1d)
5. Backfill scripts — Phases 1-3 (PM / Co-PM / Asset Admin) (~150 LOC · 0.5d)
6. Producer rewrite sweep — 18 producers behind feature flag (~360 LOC · 2d)
7. Asset Care project-scoped view + 811 locate collection skeleton (~600 LOC · 1.5d)
8. Permission helper + audit mirror + tests (~430 LOC · 1.5d)

Total: ~3 260 LOC / ~12 days.

## 🟠 P0 — Existing Block-list (unchanged)
- Spanish Translation Sweep (BLOCKED on Job Ownership Foundation)
- PDF Lockup Sweep (BLOCKED on Job Ownership Foundation)
- Integration Honesty Banners (BLOCKED on Job Ownership Foundation)
- UXS-11 Final Certification (BLOCKED on Job Ownership Foundation)

## 🟢 P2 — Backlog
- UXS-5D D3 PM Command status chip wording bleed
- LR2 Button variant long-tail retirement
- Executive Oversight read-only portal (no users today)
- Project Engineer dedicated screen (currently reuses PM portal)
- Crews-as-a-collection migration (free-text `employees.crew` is low-volume)

## ⚪ Dormant
- MaintainX integration (Track 13.32) — `MAINTAINX_SYNC_ENABLED=false`
- FleetWatcher integration — `NOT_CONNECTED`
- Scheduler activation for D4 / D5 / D6 producers — currently admin-trigger only


## 🔴 Track 14.0 Fix Tracks — pre-deploy hard gate (Certification 2026-06-13)

Source: `/app/memory/TRACK_14_0_PLATFORM_READINESS_CERTIFICATION.md` · Verdict CONDITIONAL PASS · Five-Pillar avg 9.62/10.

**Three blockers must close before redeploy. No GitHub save · no merge · no production push until 14.0 re-runs green.**

| Track     | Priority | Scope                                                                                                  | Est | Status |
|-----------|----------|--------------------------------------------------------------------------------------------------------|-----|--------|
| **14.0-S1** | P0 · blocker | Spanish translation sweep — ~222 strings across `AddAssetDialog` · `RequiredDocsEditor` · `AssetDocumentsTab` · `ShopAssetCare` · `AdminAssetAdmin` · canonical Pre-Op/DVIR section copy · document upload dialog · renewal alert copy. Wire to existing `lib/i18n.js` dictionary. | 8h | PENDING |
| **14.0-P1** | P0 · blocker | PDF lockup sweep — verify Pre-Op · DVIR · Incident · Excavation PDFs all carry the unified `safety_forms._BASE_CSS` MASCI header/footer/page-numbering/ForgedOps provider mark. Align where drift found. | 5h | PENDING |
| **14.0-I1** | P0 · blocker | Integration honesty banners — AssetProfile MaintainX tab gets "Awaiting integration · MAINTAINX_API_KEY required" notice. FleetWatcher gate label where surfaced. Resend renewal-cadence label. | 2h | PENDING |
| **14.0-M1** | P1 | Mobile/iPad re-screenshot pass — every D3–D33ABC surface at 768 px + 390 px. Asset Care home gets mobile sticky header if found missing. | 4h | PENDING |
| **14.0-F1** | P1 | Legacy form style alignment — Daily Report · Safety · Trench audit. **DONE 2026-06-13.** Honest source-inspection found legacy forms already well-aligned at shell/header/typography level; only real drift was a 33-line local `Section` shim in `PublicExcavationForm.jsx`. Additively enhanced canonical `@/components/Section` with `accent` + `dense` + `highlight` + `highlightLabel` + `testId` props; migrated PublicExcavationForm onto canonical with `accent="cyan"` + `dense`. 93/93 pytests green. 5-Pillar 9.81/10 · Beautiful 9.82/10. Form-style gate now closed. | 2h | ✅ **DONE** |
| **14.0-C1** | P2 · polish | Document-type 1-line descriptors in upload dialog + inline coaching on doc list. | 3h | PENDING |
| **14.0-N1** | P2 · v1-optional | In-app notification center delivery for the 25 asset events documented in 13.33ABC notification matrix. Email cadence (Resend). | 12h | PENDING |

### New fix tracks surfaced by Track 14.0-A0 Platform Coverage Inventory

| Track     | Priority | Scope                                                                                                  | Est | Status |
|-----------|----------|--------------------------------------------------------------------------------------------------------|-----|--------|
| **14.0-A0-B** | P0 · housekeeping | Backend `routes/*.py` housekeeping — classify the 24 zero-endpoint files. **DONE 2026-06-13 via Track 14.0-A1.** A0 finding was a grep regex limitation. 18 of 24 are legitimate endpoint modules using `register_{name}_routes(api_router, db, ...)` pattern (88 additional endpoints surfaced) · 5 are genuine FastAPI Depends providers (`*_deps.py` + `passkey_session_mint.py` + `trench_transport_bridge.py`) · 1 is `__init__.py`. Corrected platform total: 643 → ≈ 731 endpoints. ZERO file misplaced. | 1h | ✅ **DONE** |
| **14.0-A0-I** | P0 · audit | `/_internal/*` + `/dev/*` route audit. **DONE 2026-06-13 via Track 14.0-A1.** 5 `/_internal/*` routes were shipping public-by-obscurity with zero guard. Wrapped each in existing `RequireDev` helper. `/dev/login`+`/dev` already properly gated. 6 `*_hub_legacy` routes properly portal-gated. `/cheatsheet` intentionally public. | 1h | ✅ **DONE** |
| **14.0-R1 (partial)** | P1 · audit | Role-journey live-walk for 9 missing roles. **CODE-VERIFIED 2026-06-13 via Track 14.0-A1.** All 14 role landings verified via `landingFor()` inspection. Live-verified 5/14 via multi-login portal_tokens fan-out. 9 remain code-only verified (no screenshot evidence yet for Shop Manager · Mechanic · Dispatcher · PM · Superintendent · Driver · Safety · HR roles). | 6h | 🟡 **PARTIAL** (code-verified; 14.0-R1+ remains for screenshot pass) |
| **14.0-FL1 (new)** | P3 · minor | Add `field_leadership: "/leadership"` to `landingFor()` lines 120–127 — theoretical edge case where single-portal FL user lands at hub instead of leadership dashboard. Current MASCI roster has all FL users as multi-portal. | 5min | PENDING |
| **14.0-LR1 (new)** | P2 · post-RC-1 | Legacy `*_hub_legacy` retirement track (PM · Shop · HR · Safety · Dispatch). All currently gated; defer to post-deployment cleanup. | 2h | PENDING |
| **14.0-CONV1 (new)** | P3 · docs | Author `BACKEND_ROUTE_CONVENTIONS.md` documenting the `register_*_routes()` pattern, the `*_deps.py` naming convention, and the difference from module-level `router = APIRouter()` style. | 1h | PENDING |
| **14.0-B1** | P1 · audit · pre-Spanish | Button audit — 1 385 instances · 14 variants. **DONE 2026-06-13 via Track 14.0-BT.** `BUTTONS_DICT.md` published (12 roles · 34 approved labels · variant rules · 36 P0/P1 Spanish keys ≈99% of button text). Long-tail retirement deferred to 14.0-LR2. | 4h | ✅ **DONE** |
| **14.0-Mod1** | P1 · audit · pre-Spanish | Modal audit — 64 dialog/sheet/alert-dialog files. **CERTIFICATION DONE 2026-06-13 via Track 14.0-MC** (inventory · scoring · defect catalog). **EXEC PASS (per-modal Spanish/a11y/mobile + `<ModalFooter>` shared primitive) still pending** as 14.0-Mod1-EXEC. | 4h | 🟡 **CERT DONE · EXEC PENDING** |
| **14.0-H1** | P2 · feature · post-Spanish | Knowledge-base / training-content search. **A0/A2 correction**: data-search IS platform-wide (`GlobalSearch` wired on 8 portal hubs: HrHub · DispatchHub · ShopHub · FieldLeadershipHub · Tasks · DocumentExpirations · PoRequests · HrEmployees). What's actually missing is search across the 12 training routes + cheat-sheets + admin guide. | 8h | PENDING |
| **14.0-T1** | P3 · audit · pre-Spanish | Toast / terminology audit — 1 243 emissions. **DONE 2026-06-13 via Track 14.0-BT.** `TOAST_DICTIONARY.md` + `TERMINOLOGY.md` published · 5 operator-visible engineering leaks fixed (ViewIncident · HrEmployeeRequestsQueue · DispatchBoard) · ≈50 toast keys + 44 terminology keys catalogued for Spanish. Lint-rule deferred to 14.0-LR2. | 6h | ✅ **DONE** |
| **14.0-A2B** | P2 · audit · pre-Spanish | Admin/PM/HR coaching density audit. **A2 finding**: critical operator surfaces well-coached; admin power-user deeper-routes sparse but intentional. Confirm sparse is appropriate or polish needed. Translate stabilized coaching, not draft. | 6h | PENDING |

**Total estimated to close all named 14.0 blockers (existing + A0-surfaced): ~63 hours (~8 working days).**

---

**Proposed deployment-gate sequence:** close S1 → P1 → I1 → spot-check M1 → re-run Track 14.0 → if green, redeploy.

---

## 🟡 Track 13.18 — Material Movement Ledger · phased plan (architecture certified 2026-06-12)

Architecture report: `/app/memory/TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md`

| Track     | Phase | Scope                                                                                                | Files                                                          | Est | Status                                  |
| --------- | ----- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | --- | --------------------------------------- |
| **13.19** | A     | Proof-join (`operational_attachments` scale_ticket family) + virtual `verification_status` + rollup counters on existing `/api/material-movement/daily/{p}/{d}`. No new collection. No UI change. | `backend/routes/material_movement.py` (single file)            | 3h  | ✅ **DONE 2026-06-12** · 9/9 pytest pass |
| 13.20     | B     | Read-only Material Movement panel on `PmProjectDetail.jsx` (project-scoped). Consumes Phase A.       | `frontend/src/pages/PmProjectDetail.jsx`                       | 2h  | ✅ **DONE 2026-06-12** · ESLint clean · live browser smoke confirmed |
| 13.21     | C     | Dispatch Companion Haul Ledger page + `/api/dispatch/haul-ledger` filter endpoint. Outside MapLibre. | new dispatch page + `backend/routes/dispatch_lifecycle.py` ext | 6h  | ✅ **DONE 2026-06-12** · endpoint + page + sidebar live · map-first hard-lock intact |
| 13.22     | D     | Admin Material Data-Quality page + CSV export + Admin Hub V2 card.                                   | new admin page + new endpoint                                  | 5h  | ✅ **DONE 2026-06-12** · CSV stream + admin page + hub card live · map-first hard-lock intact |
| —         | E     | FleetWatcher ingestion: `fleetwatcher_tickets` collection + reconciliation job + Admin unmatched queue. | new ingestion service                                          | 12h | **BLOCKED on `FLEETWATCHER_API_KEY` + service credentials** |

**Material Movement Ledger phased plan (Phases A–D) is now COMPLETE.** All four phases shipped with hard locks intact (Dispatch Map-First · Driver no-login · no new collection · FleetWatcher honestly NOT_CONNECTED · no cost/accounting/pay-app/ERP fields).

**Immediate Build Queue (Track 13.9 §8) is now EMPTY** as of Track 13.23 (2026-06-12). All 8 IBQ items shipped.

**Track 13.25 (2026-06-12) · Asset Care & Service Architecture Certification** authored the future Asset Service Event Backbone + 8-track phased plan. NO implementation. Recommended next: **A · Track 13.26 · Asset Service Event Backbone** (derived virtual timeline · single backend file · NO new collection).

### Asset Care 8-track phased plan (Track 13.25 architecture)

| # | Track | Goal | Risk | Verdict |
|---|-------|------|------|---------|
| 1 | 13.26 | Asset Service Event Backbone (derived) | LOW | ✅ **DONE 2026-06-12** (11/11 pytest pass) |
| 2 | 13.27 | Unit History Timeline (page + endpoint) | LOW | ✅ **DONE 2026-06-12** (browser smoke confirmed) |
| 3 | 13.28 | Shop Mechanic Assignment + Repair Notes | MED | ✅ **DONE 2026-06-12** (backend 4/4 + Phase 2 UI 4/4 pass) |
| 4 | 13.29 | Fuel/Lube Job Visit Form | MED-HIGH | ✅ **DONE 2026-06-12** (backend + submission form + records list + detail UI · 24/24 backend pass) |
| 5 | 13.30 | Fuel/Lube Daily Reconciliation | MED | ✅ **DONE 2026-06-12** (backend 12/12 + 3 frontend pages · 36/36 backend pass · doc `TRACK_13_30_SERVICE_TRUCK_DAILY_RECONCILIATION.md`) |
| 5a | 13.30A | Shop Command Center UX + Role Workflow Audit | LOW | ✅ **DONE 2026-06-12** (read-only · doc only) |
| 5b | 13.30B | Shop Command Center Restructure + HubBackLink fix | LOW | ✅ **DONE 2026-06-12** |
| 5c | 13.30C | Shop Command Center Intelligence + Visual Hierarchy + Global Unit Search | MED | ✅ **DONE 2026-06-12** |
| 5d | 13.30D | Shop Command Center 10/10 Experience · Parts + Workload + audit closeout | MED | ✅ **DONE 2026-06-13** (24/24 pytest pass · 2 bugs caught + fixed in pre-closeout audit · doc `TRACK_13_30D_SHOP_COMMAND_CENTER_10_10_EXPERIENCE_PARTS_WORKLOAD.md`) |
| 6 | 13.31 | PM Engine (derived first) | LOW-MED | ✅ **DONE 2026-06-13** (15/15 pytest pass · 39/39 with regression · Five-Pillar 9.6/10 · 8 PM tiles in ShopHub · 4 new operator pages · PM completion ≠ RTS preserved · doc `TRACK_13_31_PM_ENGINE.md`) |
| 6a | 13.31A | Asset Administrator Certification & Source-of-Truth Audit (READ-ONLY) | LOW | ✅ **DONE 2026-06-13** (no code change · 31-field ownership matrix · 18 missing administrative fields documented · 5-Pillar 6.6/10 · doc `TRACK_13_31A_ASSET_ADMINISTRATOR_CERTIFICATION.md`) |
| 6aa | 13.31AA | Employee Lifecycle + Asset Issuance Architecture Certification (READ-ONLY) | LOW | ✅ **DONE 2026-06-13** (no code change · discovered mature live systems for employee lifecycle/custody/PPE issuance/returns/transfers · hard-rejected 6+ duplicates · revised 13.31B scope ~60% smaller · 5-Pillar 8.4/10 for current Employee+Issuance state · doc `TRACK_13_31AA_EMPLOYEE_LIFECYCLE_ASSET_ISSUANCE_CERTIFICATION.md`) |
| 6ab | 13.31AB | Asset Administration Spine Construction Audit (READ-ONLY · final blueprint) | LOW | ✅ **DONE 2026-06-13** (no code change · corrected 13.31AA's duplicate-spine note · asset_spine.py + equipment_master ARE the canonical spine · 19 of 31 fields already in pydantic · op_attachments R2-backed · 3 PDF renderers reusable · 5-Pillar 9.8/10 for proposed blueprint · doc `TRACK_13_31AB_ASSET_ADMINISTRATION_SPINE_CONSTRUCTION_AUDIT.md`) |
| 6ac | 13.31AC | Platform Asset Taxonomy, Classification & Source-of-Truth Certification (READ-ONLY) | LOW | ✅ **DONE 2026-06-13** (no code change · discovered 10 incompatible classification systems · canonical 11-class Level-1 + ~60-type Level-2 taxonomy proposed · 29 of 30 existing categories map cleanly · current 5-Pillar 4.2/10 · proposed future 9.8/10 · doc `TRACK_13_31AC_PLATFORM_ASSET_TAXONOMY_CLASSIFICATION_SOURCE_OF_TRUTH_CERTIFICATION.md`) |
| 6b | 13.31B-D0D1 | Taxonomy + Asset Admin Spine Foundation (Days 0+1 slice) | LOW-MED | ✅ **DONE 2026-06-13** (53/53 pytest pass · canonical 13-class/92-type taxonomy + behavior matrix + legacy crosswalk · AssetCreate/AssetUpdate extended with 17 fields · 4 new `/api/asset-spine/taxonomy/*` endpoints · 91/200 sample rows cleanly verified, 109 review-needed · 5-Pillar 9.78/10 · doc `TRACK_13_31B_D0D1_TAXONOMY_ASSET_ADMIN_SPINE_FOUNDATION.md`) |
| 6b-d2 | 13.31B-D2 | **Asset Admin UI + AssetProfile extension** | MED | ✅ **DONE 2026-06-13** (60/60 pytest pass · `/admin/asset-admin` page + AssetProfile Admin tab + 7 new D2 tests · 5-Pillar 9.72/10 · doc `TRACK_13_31B_D2_ASSET_ADMIN_UI.md`) |
| 6b-d5 | 13.31B-D5 | **Platform-wide Asset Taxonomy Consumer Reconciliation** | MED | ✅ **DONE 2026-06-13** (72/72 pytest pass · single read-side resolver · PM Engine hard-gated · Unit Search + Transfers + Offboarding enriched · 5-Pillar ≥9.5 on every consumer · doc `TRACK_13_31B_D5_PLATFORM_TAXONOMY_CONSUMER_RECONCILIATION.md`) |
| 6b-d5.1-cert | 13.31B-D5.1 | **Platform Asset Coverage / Pre-Op / Classification / Lifecycle Certification (READ-ONLY)** | LOW | ✅ **DONE 2026-06-13** (zero-code audit · 700 assets · 81 % unverified · PM 0 templates · Pre-Op 5-value dropdown · 5-Pillar 7.4 current → 9.7 future · authorized D5.1 build, D5.2, D3, D4, D6, 13.33-A/B · doc `TRACK_13_31B_D5_1_PLATFORM_ASSET_COVERAGE_PREOP_CLASSIFICATION_LIFECYCLE_CERTIFICATION.md`) |
| 6b-d5.1 | 13.31B-D5.1-BUILD | **Pre-Op canonical write stamp + canonical-driven equipment_type dropdown** | MED | ✅ **DONE 2026-06-13** (83/83 pytest pass · NEW `services/inspection_classification.py` + `<SmartUnitClassificationChip>` · Pre-Op + DVIR both stamp canonical class/type · per-trailer snapshots · `template_status="missing_template"` powers D5.2 backlog · 5-Pillar 9.83 · doc `TRACK_13_31B_D5_1_BUILD_SMART_PREOP_DVIR_CANONICAL_WRITE_STAMP.md`) |
| 6b-d5.2 | 13.31B-D5.2 | **Canonical Pre-Op + DVIR Inspection Template Expansion** | MED | ✅ **DONE 2026-06-13** (117/117 pytest pass · NEW `services/inspection_templates.py` w/ 45 canonical templates · NEW endpoints `/inspection-templates*` + missing-backlog · every directive-named type stamps `available` · Service Truck stays Service Truck · 5-Pillar 9.87 · doc `TRACK_13_31B_D5_2_CANONICAL_PREOP_DVIR_INSPECTION_TEMPLATE_EXPANSION.md`) |
| 6b-d5.3 | 13.31B-D5.3 | **Frontend render of canonical inspection sections + Asset Admin Missing-Template Backlog panel** | LOW-MED | ✅ **DONE 2026-06-13** (78/78 backend pytest pass · NEW `CanonicalInspectionSections` rendered on Pre-Op + DVIR · NEW "Missing Templates" tab on `/admin/asset-admin` · 5-Pillar 9.76 · doc `TRACK_13_31B_D5_3_FRONTEND_SMART_PREOP_DVIR_TEMPLATE_RENDERING.md`) |
| 6b-d5.4 | 13.31B-D5.4 | Wire canonical sections into submit payload (per-section pass/fail capture) · remove legacy 5-value dropdown · render trailer-specific sections inside DVIR per-trailer panel | LOW-MED | **NEXT (P0)** after operator verification of D5.3 |
| 6b-d3 | 13.31B-D3 | Document Vault (operational_attachments.host_kind="asset") | LOW-MED | after D5.2 |
| 6b-d4 | 13.31B-D4 | CSV / Print / PDF for Asset Admin | LOW | after D3 |
| 6b-d5 | 13.31B-D5 | Platform-wide consumer updates + final 5-Pillar audit | MED | after D4 |
| 7 | 13.32 | MaintainX Integration | HIGH | **BLOCKED on `MAINTAINX_API_KEY` credentials** |
| 8 | 13.33 | Asset Care Command Center | LOW | BUILD after lower tracks |

### Track 13.30A · Shop Command Center UX + Role Workflow Architecture Audit (DONE 2026-06-12 · READ-ONLY)
- 18-section audit completed · no implementation. **Verdict:** stop adding features to ShopHubV2 until **Track 13.30B** ships (Command Center restructure + HubBackLink Shop-aware fix · 2 d · LOW · frontend-only · ZERO new backend). Then **13.30C** (Global Unit Search · 1 d · 1 new endpoint), **13.30D** (Parts-On-Order + Mechanic Workload aggregators · 2 d), **13.31** (PM Engine), **13.33** (Asset Care Command Center). MaintainX 13.32 remains BLOCKED on `MAINTAINX_API_KEY`.
- HIGH-severity defects identified: HubBackLink Shop-blindness (3 routes); no global unit search; overlapping defect counters; track-graveyard copy in operator surfaces; buried high-value cards.
- Report: `/app/memory/TRACK_13_30A_SHOP_COMMAND_CENTER_UX_ROLE_WORKFLOW_ARCHITECTURE_AUDIT.md`.

### Track 13.30B · Shop Command Center Restructure + HubBackLink Fix (DONE 2026-06-12 · LIVE)
- Frontend-only · 2 files modified · zero backend · zero new endpoint · zero new collection.
- `HubBackLink` Shop-aware (`shop = !admin && !pm && (isShop() || pathname.startsWith("/shop"))`); `useHubHome()` extended.
- ShopHubV2 reorganized by workflow: Header → Your Queue strip → 01 Attention required → 02 Active work → 03 Parts + waiting → 04 Fuel and service → 05 Unit intelligence → 06 Records → 07 Recovery Map.
- Engineering copy scrubbed: preview banner removed · all `Track 13.x` and `Source: /api/...` mentions gone (verified at runtime · zero operator-visible occurrences).
- Honest dashed *"coming next"* slots for Global Unit Search and Parts-on-order — no fake buttons.
- ESLint clean. 21/21 browser smoke checks pass. Backend suite preserved at **36/36 pass**. All hard locks intact.
- Five-Pillar **7.0 → 9.0** / 10.
- Report: `/app/memory/TRACK_13_30B_SHOP_COMMAND_CENTER_RESTRUCTURE.md`.

### Track 13.30C (DONE 2026-06-12 · LIVE)
- Shop Command Center Intelligence + Visual Hierarchy + Global Unit Search.
- Backend: `GET /api/shop/units/search` + `GET /api/shop/me/summary` (read-only · composes from 4 existing collections · zero new collection).
- Frontend: `UnitSearch.jsx` mounted in header + Section 05 · `YourQueueStrip.jsx` role-aware tiles · Section 01 PriorityMetric upgrade · Recovery Map per-row "Open History →" link.
- 6 new pytest + 36 regression = **42/42 backend pass**. ESLint clean. Live counts visible (83 unassigned · 71 OOS · 83 open defects · 6 variance review).
- Recovery Map preserved AND improved (non-negotiable directive honored).
- Five-Pillar 9.0 → 9.8 / 10.
- Report: `/app/memory/TRACK_13_30C_SHOP_COMMAND_CENTER_INTELLIGENCE_VISUAL_HIERARCHY.md`.

### Track 13.30C-fix (DONE 2026-06-12 · LIVE · correction pass)
- Runtime crash fixed (`FocusBanner` import in `FleetVisibility.jsx`).
- 2 new read-only endpoints (`/api/shop/projects/list`, `/api/shop/units/list`) for source-truth Shop dropdowns.
- 2 new shared frontend components (`BackToShopLink`, kind-aware `ShopSelector`).
- "Back to Shop" mounted on all 10 PortalShell-driven Shop subpages.
- Fuel/Lube + Service Truck forms upgraded to source-truth selectors with honest manual fallback.
- Operator-copy scrub on all Fuel/Lube, STR, Manager Queue, My Assignments, Unit History pages.
- 12 smoke routes pass · backend regression preserved at 42/42 · `/shop/hub_legacy` rollback alive.
- Report: `/app/memory/TRACK_13_30C_FIX_SHOP_FORM_NAV_UX_CORRECTION.md`.

### Track 13.30D (next P0)
- Parts-On-Order + Mechanic Workload aggregators. 2 derived endpoints + 2 new hub cards. ~2 days.

**Hard locks reaffirmed:** Dispatch Map-First · Driver no-login · Shop Repair Complete ≠ RTS · one map engine · no fake MaintainX · no fake FleetWatcher · no accounting / ERP / pay-app / cost / contract / RFI / submittal / change-order / doc-control · no fake users / mechanics / PM / fuel totals.

| # | Gap                                                | Severity | Effort |
| - | -------------------------------------------------- | -------- | ------ |
| 1 | Equipment Pre-Op CSV/PDF export                    | MED      | ~5h    |
| 2 | DVIR CSV/PDF export                                | MED      | ~5h    |
| 3 | Date-range + project + unit search filters         | HIGH     | ~12h   |
| 4 | Per-unit unified history endpoint + page           | HIGH     | ~8h    |
| 5 | Print stylesheets for inspection / defect detail   | LOW      | ~2h    |
| 6 | Active reminder / overdue alert dispatch           | MED      | ~4h    |
| 7 | Per-mechanic assignment field on `fleet_defects`   | LOW      | needs operator decision |
| 8 | Auto-link Shop Parts orders to source defect       | LOW      | ~3h    |

**Hard locks enforced across all phases:** Map-First Dispatch · No-login Driver · PM scope = assigned projects · No new physical material ledger collection · No accounting / ERP / pay-app / cost / contract · No FleetWatcher fake data.



## ✅ RESOLVED — Atlas Tier Capacity (iter437 · 2026-05-26)

**Outcome:** Cluster upgraded M0 → M10. Restore drill completed end-to-end. Currently at **8.9% utilization** (911 MB / 10 240 MB). Operational runway ≈ 12 months at observed +25 MB/day growth.

**What's in place:**
- ✅ Cluster-capacity probe (`/api/cluster/capacity`) + frontend banner (`<ClusterCapacityBanner />`) · threshold logic VERIFIED across all 3 severities
- ✅ Atlas alerts runbook: `/app/memory/ATLAS_ALERTS_RUNBOOK.md`
- ✅ Restore-drill script proven: `/app/backend/tools/restore_drill.py` · 110s wall-clock · 26/26 collections parity
- ✅ Phase R certification: `/app/memory/PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md` (PASS)
- ✅ Phase Sigma · Operational Trust Hardening (iter437 · this session)
   - Playwright foundation: `/app/backend/tests/pw_suite/` · 15/15 green on desktop/ipad/mobile
   - Role Access Certification: `/app/memory/ROLE_ACCESS_CERTIFICATION.md` · 338 cells · 0 unexpected
   - Performance Forensics: `/app/memory/PERFORMANCE_FORENSICS.md` · `idempotency_keys` root cause identified
   - Operational Runbooks: `/app/memory/OPERATIONAL_RUNBOOKS.md` · 10 procedures with proof gates
   - Regression Strategy: `/app/memory/REGRESSION_STRATEGY.md` · 3-gate deploy doctrine

**Open items (queued, not yet implemented, all REVIEW-ONLY per directive):**
- 🟡 Configure Atlas alerts (operator-side, requires Atlas admin login) per `ATLAS_ALERTS_RUNBOOK.md`
- 🟡 Legacy base64 photo migration (300+ MB reclaim) — defer to dedicated migration phase
- 🟡 Re-seed `testmech@mascigc.com` shop test user (wiped by restore — shop direct-login gap)
- 🟡 Playwright flows 8 (crew), 9 (dispatch board), 10b (driver shift), 11b (payroll), 12 (MFA/passkey browser), 13 (public form), 15 (env isolation under WRITE load)
- 🟡 Per-FL-subrole direct logins (Superintendent, Foreman, Truck Boss, Working Supervisor) — needs credentials
- 🟡 `dispatch_driver` testing with real driver (preview lacks `is_driver=true` employees)
- 🟡 Magic-link issuance: validate `driver_id` against employees collection (~5 LoC; LOW severity)
- 🟡 Storage observability widget (data plumbing live — UI deferred)
- ⚪ Atlas alert smoke-test (operator-side · requires Atlas admin login)

**Phase Sigma-II completed (this session, all CERTIFIED PASS):**
- ✅ `IDEMPOTENCY_PATCH_CERTIFICATION.md` — strip patch + 99.2% rewrite reclaim
- ✅ `DISPATCH_COLDSTART_FORENSICS.md` — cannot reproduce; documented; no patch shipped
- ✅ `ROLE_ACCESS_CERTIFICATION.md` (2nd pass) — Leadership + driver session scope verified
- ✅ `STORAGE_OBSERVABILITY.md` — capacity history collection + endpoint live
- ✅ `PLAYWRIGHT_CERTIFICATION_PHASE2.md` — 4 new flows operational
- ✅ `DEPLOYMENT_CERTIFICATION_CHECKLIST.md` — 11 gates + preflight script
- ✅ `LIFECYCLE_GOVERNANCE.md` — 6-class doctrine; no destructive action

---

## 🅿️ PARKED — Awaiting User Green Light

### 🔐 Site-Wide Employee Login Gate
- **Status**: PARKED by user on 2026-05-07 — *"we will do this soon just not today"*
- **Priority when unparked**: P1 (security + audit trail + usage analytics)
- **Why parked**: Other priorities first. User wants this in the very near future.
- **Reminder trigger**: Surface during any conversation about user audit trail, security hardening, employee accountability, or "what should we tackle next?"

**Spec Summary (already mapped out in detail — ready to execute on user's go):**

The gate: every visitor to mascidocs.com hits a login screen first. Only after entering their employee credentials do they see any HUB content. PM/Shop/Admin/Safety-Forms portals stay as their own gates inside.

**Eight components to build (~14 hours / 1.5–2 days total):**
1. Bulk employee import from spreadsheet (name, email/ID, password, active flag) — ~1 hr
2. Site-wide login gate component wrapping the whole app — ~3 hr
3. `/api/field/login` endpoint (issues 30-day signed cookie token) — ~1 hr
4. Usage tracking: every page view + form submission stamps who/when/what — ~3 hr
5. Termination toggle: admin button → revokes all tokens instantly + blocks future logins — ~1 hr
6. Self-service password reset via Resend — ~2 hr
7. (Optional) First-time forced password change — ~1 hr
8. Per-employee record stamping: every form auto-tags `submitted_by_employee_id` — ~2 hr

**Smart additions I'd build alongside (free since we're in there):**
- Multi-device tracking (flag password sharing — same login from 3+ IPs in a week)
- "Stay logged in 30 days" on mobile (so crews don't type passwords at 6am)
- Biometric unlock prompt on iOS (Face ID via passkeys)
- Admin "Recent Activity" live stream
- Per-employee productivity stats (reports filed per month)
- Auto-flag accounts inactive for 90+ days

**Recommended phased rollout:**
- 🥇 Phase 1 (Day 1): Hard gate + employee import + admin termination toggle — ~6–10 hrs
- 🥈 Phase 2: Usage tracking + per-record stamping + admin activity dashboard — ~½ day
- 🥉 Phase 3: Self-service password reset + 30-day mobile sessions — ~½ day
- 🎖️ Phase 4: Productivity dashboard + multi-device alerts — ~½ day, optional

**Open decisions when unparked:**
- a) Identifier: email / employee ID / **either (recommended)**
- b) Force password change on first MASCI HUB login: yes / no / optional
- c) Pages staying public (no login): `/legal/terms`, `/legal/privacy`, `/company-info`?
- d) Subcontractor share-links: keep one-time signed URLs or also gate behind login?
- e) Phase 1 scope: just gate / gate + record stamping / full Phase 1+2
- f) Build a hardcoded "super-owner" backdoor login (strongly recommend yes — prevents lockout if deploy goes sideways)

**Tech approach:**
- Reuses existing JWT/signed-token pattern from PM/Admin/Shop auth (no new dependencies)
- New collection: `field_user_sessions` for active tokens
- New collection: `audit_log` for per-employee activity (or extend existing `activity_log`)
- Uses existing Resend integration for password reset emails
- Uses existing brute-force protection / rate limiting (already in production)

**Key gotchas to flag at build time:**
- Bootstrap risk: very first deploy with login required → user could lock self out → MUST ship super-owner backdoor first
- Existing 8-char paystub passwords are weak → recommend forced upgrade to 10+ chars on first MASCI HUB login
- Password sharing is real in construction → audit trail matters more than prevention
- Foremen at 6am with cold hands: 30-day sessions + Face ID is non-negotiable for adoption

**Call `integration_playbook_expert_v2` BEFORE writing any auth code** (per system policy — auth is always an integration).

---

### 🚛 Motive Fleet Watcher Integration
- **Status**: PARKED by user on 2026-02 — *"keep it on the list of things to add in the future"*
- **Priority when unparked**: P1 (huge ROI — Motive already knows almost everything crews currently type by hand)
- **Why parked**: User wants other priorities first; Motive can wait.
- **Reminder trigger**: Surface during any conversation about reducing Pre-Op friction, fleet visibility, incident documentation, or "what should we add next?"

**Spec Summary (already mapped out — ready to scope on user's go):**

Top 5 integrations ranked by MASCI impact:
1. 🥇 **Equipment Pre-Op auto-fill** — odometer, engine hours, last DVIR, fault codes (DTCs), last 24-hr driver auto-pulled from Motive when operator picks unit. Cuts Pre-Op time from ~8 min → ~3 min.
2. 🥈 **Equipment Master auto-sync** — nightly pull of Motive vehicle list into MASCI's `equipment_master`. New units appear in dropdowns automatically. Decommissioned units auto-flagged inactive. Ends manual roster maintenance forever.
3. 🥉 **GPS verification on Daily Reports + Site Inspections** — cross-reference MASCI form GPS with Motive trip log. Auto-fill arrival/departure/hours-on-site. Flag phantom reports where unit was in yard but report claims work was done. Audit gold.
4. 🏅 **Dashcam clips auto-attached to Incident Reports** — when an incident is filed for a unit, auto-pull the 60-sec dashcam clip from Motive bracketing the incident time. Embed in PDF. Insurance/legal killer feature.
5. 🎖️ **Live fleet map on Admin Dashboard** — every unit pinned with status (active/idle/off/OOS). Click pin → today's daily report status, open Pre-Op fails, current driver, today's job site.

Mid-tier opportunities:
- 6. Fault code → Shop ticket (webhook-driven check-engine alerts auto-create Needs-Attention queue items)
- 7. HOS clock on Pre-Op (CDL drivers see remaining drive time)
- 8. Trip log → Daily Report pre-fill (miles driven, hours run, idle time)
- 9. Geofence arrival → auto-Slack/email PM
- 10. Per-driver safety scoring (harsh braking, speeding events)
- 11. Monthly fuel/idle abuse reports

**Tech approach (already designed):**
- Base URL: `api.gomotive.com` (formerly KeepTruckin/api.keeptruckin.com)
- Auth: API key from Motive dashboard → Settings → Integrations → API → Generate Key (free with existing Motive subscription)
- Rate limit: 1000 req/min — plenty
- Webhooks supported (real-time safety events / DVIR submissions)
- New module: `/app/backend/integrations/motive.py`
- Mongo cache collections: `motive_vehicles`, `motive_drivers`, `motive_trips`, `motive_events`
- Single env var: `MOTIVE_API_KEY`
- Nightly background job + on-demand calls + webhook receiver

**Phase options when unparked:**
- 🐢 **Phase 1a (1 day)**: Equipment master sync only
- 🚙 **Phase 1b (2–3 days)**: Sync + Pre-Op auto-fill
- 🚀 **Phase 1c (~1 week)**: Sync + Pre-Op + GPS verification + live fleet map
- 🛡️ **Phase 2**: Dashcam clips on incidents (killer for insurance/legal)
- 🔔 **Phase 3**: Webhook-driven fault codes, geofence alerts, safety scoring

**Open questions when unparked:**
- Top 3 features to ship in Phase 1
- Approximate fleet size (informs polling vs webhook strategy)
- Phase 1 scope choice

---

### 📷 Photo-First Daily Report (Gallery Upload + AI Draft)
- **Status**: PARKED by user on 2026-02 — *"Keep this for later rollout after crews learn the system... Will wait, remind me later."*
- **Priority when unparked**: P1 (high ROI, ~2–3 hour build)
- **Why parked**: User wants crews to fully adopt current system before adding AI-driven workflows.
- **Reminder trigger**: Bring up after crews show solid adoption of Daily Reports / Safety Forms (~1–3 months post-deploy), or whenever user asks for new feature ideas.

**Spec Summary (already discussed and approved in concept):**
1. Super takes 8–15 photos throughout the day on phone camera (existing habit).
2. End-of-day, opens Daily Report → "📷 Upload Photos from Gallery" button.
3. Multi-select photos from camera roll.
4. AI (Gemini 3 Vision) analyzes ALL photos and generates:
   - **Top of report**: Synthesized narrative (work performed, crew, equipment, conditions).
   - **Bottom of report**: Per-photo captions as photo log appendix.
   - Photos embedded inline in the PDF.
5. Super edits, adds hours/quantities, signs, submits.

**Smart features approved in concept:**
- Auto-sort photos by EXIF timestamp (chronological narrative).
- GPS verification (flag photos taken outside project geo-fence).
- Date filter (default to "today's photos only" in picker).
- Photo dedup (AI mentions multi-angle shots once).
- Per-photo annotation field (super can tag a photo before AI runs).
- Bilingual draft (Spanish-first if super's UI language is ES, auto-translate to EN on submit using existing `translateUserInput` pipeline).
- Cost: ~$0.03 per report (~$45/mo at 50 reports/day).

**Open decisions when unparked:**
- Output style: per-photo / synthesized / both (recommended: both).
- Source: gallery only vs gallery + in-app camera (recommended: both).
- Required vs optional on daily reports.
- Where it lives: integrated into existing Daily Report form vs separate "📷 Photo Report" entry point.

---

## 🚀 OTHER BRAINSTORMED FEATURES (Feb 2026 ideation session)

Not parked, just queued for user prioritization later:

### Crew Quality-of-Life
- **QR Code Equipment Tagging** — Scan QR sticker to auto-fill Issuance/Return forms with item + serial #. (~1-day build, very high crew adoption)
- **Voice-to-Text on Notes Fields** — Mic button on every notes field; Spanish supported via existing translation pipe.

### Alerts / Compliance
- **PPE Expiration & Inspection Reminders** — Auto-pings 30 days before harness/extinguisher/fall-protection expirations. Prevents OSHA fines.
- **Training Renewal Auto-Reminders** — 30/60/90 day countdown; weekly Monday digest to Safety Officer.
- **Weather-Triggered Alerts** — NWS forecast by project GPS; heat index >95°F or lightning <10mi triggers stop-work alert to foreman.

### Admin / Office
- **Equipment Cost Dashboard** — "We charged back $X this quarter for lost gear, 60% hard hats."
- **PM Weekly Digest Email** *(P2 from PRD)* — Monday 7am rollup of QA/QC, Daily Reports, Equipment fails by PM.
- **Crew Roster Sync / Termination Auto-Charge** — Flag unreturned gear on termination, route to HR for final-paycheck deduction.

### Bigger Bets
- **Job Site Map View** — Map pins for all active projects → click for daily status snapshot.
- **Crew Self-Service Portal** — Phone-friendly login showing each employee's PPE, training, renewals, signed forms.
- **Subcontractor Compliance Vault** — Sub uploads COI/W-9/safety plan once; auto-blocks expired subs from new jobs.

---

## ✅ EXISTING ROADMAP (from PRD)

- **P1 · Platform Quality Infrastructure** · **Multi-Viewport Pre-Deploy Validation Gate (Phase 1C)** — APPROVED BACKLOG (2026-02-01). 10 viewport classes × 11 core targets wired into `scripts/pre_deploy_check.sh`. Spec: `/app/memory/PHASE_1C_VIEWPORT_VALIDATION_GATE_SPEC.md`. Binding deployment policy: no `SAFE TO DEPLOY` without a completed viewport report. Implement AFTER (a) production validation of current Phase V.5 fixes lands clean and (b) Backup Scheduler Hardening (P0 GAP-7) completes. ~7 dev-hour estimate.
- **P1**: Auto-suggest parts on Pre-Op FAIL (blocked on parts upload spreadsheet)
- **P2**: New Hire Onboarding flow (currently "Coming Soon" on Training Hub)
- **P2**: S3 Object Storage Migration (move local disk files/videos to S3)
- **P2**: PM Weekly Digest Email
- **P3**: Admin Bulk PDF Export (zip download for monthly archiving)

---

*Last updated: Feb 2026*

## Next up (after Track 13.4A · Feb 2026)

### P0 — Audit sequence (no new features, no deploy)
- **Track 13.4B — MASCI Platform Identity Recovery Audit** — handoff brief in `/app/memory/TRACK_13_4B_HANDOFF_BRIEF.md`. Includes dedicated *Dispatch Data Integrity / Motive Reality* appendix.
- **Track 13.4C — MASCI Platform Design System V1**.
- **Track 13.4D — MASCI Platform Full Reality Audit**.

### P1 — Carried defects (documented in 13.4A §7)
- Circle-geofence conversion (67 stored, 0 rendered).
- Production Motive webhook verification.
- 100/190 motive-mapped assets without any GPS coords — triage expected-dark vs missing-telemetry.
- Stale-position root causes per unit.

### Blocked
- Production deploy + Save to GitHub — explicitly forbidden by operator until 13.4B/C/D complete and operator visually approves.

---

## 2026-06-12 update · post Track 13.6N closure

### Completed
- ✅ Track 13.6N — Operational Polish & Signoff Readiness · CLOSED.

### Next (gated)
- **OPERATOR SIGNOFF (P0)** — operator walks the Section 5 checklist in `/app/memory/TRACK_13_6N_OPERATIONAL_POLISH_AND_SIGNOFF_READINESS.md` for PM · HR · Safety · Shop · Dispatch (map) · Driver (public flow) · Admin & Leadership companion lanes · legacy rollbacks.
- **Track 13.6O — Legacy Route Retirement (P1 · gated)** — fires ONLY after all five criteria are satisfied: 30-day window · zero regressions · zero rollback invocations · zero V2-specific incidents · explicit operator approval.

### Forbidden / blocked (unchanged)
- No new portals · no new APIs · no new auth · no new route swaps · no mock data · no Dispatch map alteration · no Driver auth · no deploy / GitHub push / merge.
- **New permanent doctrine**: "No workflow changes without workflow discovery."

---

## 2026-06-12 update · post Track 13.7A discovery

### Completed
- ✅ Track 13.7A — Operational Map Engine Discovery & Role-Based View Architecture · CLOSED (discovery only · no code).

### Pending operator decisions (gated · no code yet)
- **REVIEW**: read `/app/memory/TRACK_13_7A_OPERATIONAL_MAP_DISCOVERY.md` and decide whether Option B is authorized.
- **IF AUTHORIZED — first warranted lens (P1, gated)**: Shop awareness panel inside `ShopHubV2.jsx` answering "where are my OOS / open-defect units physically?" — small embed of `MapCanvas` filtered to `attention_reason∈{maintenance,inspection}`. Zero new backend work. No swap. Secondary to the recovery queue.
- **IF AUTHORIZED — second lens (P2, gated)**: PM awareness panel inside `PmHubV2.jsx` answering "are the right assets on my project sites today?" — filtered to PM's `/api/pm/jobs` project list. Doctrine flag: high risk of duplicating PmHubV2 queues; only build if operator explicitly asks.

### Permanent exclusions (this report formalised them)
- **Safety**: NO MAP. Decisions are list-driven & time-driven.
- **Leadership**: NO MAP. Decisions are aggregate counts & trends.
- **Mechanic**: NO MAP. Reuse Asset Card deep link if ever needed.
- **Admin** (operationally): full `/operations-map` already in place; no role-specific lens.

### Three permanent hard locks
1. Dispatch map dominance · MapLibre canvas must remain dominant at `/dispatch-portal`.
2. One map engine · one source of truth · no second map library or pipeline.
3. No map without workflow discovery.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No new map systems · no new GPS / telematics providers · no UI modernization · no mockups · no new portals · no new APIs · no new auth.

---

## 2026-06-12 update · post Track 13.7B implementation

### Completed
- ✅ Track 13.7B — Shop Operational Map Lens · Implementation · CLOSED.

### Pending operator decisions
- **OPERATOR VALIDATION (P0)**: Run a real `/shop` shift with Section 3 in view. Confirm queues stay primary, map is useful but not dominant, copy is truthful.
- **Track 13.6N OPERATOR SIGNOFF (P0)**: Still pending — RC-1 swapped portal signoff window not yet started.

### Deferred (gated)
- **PM lens (P2 · only if explicitly requested)**: Awareness panel inside `PmHubV2.jsx`. High duplication risk; do NOT build unless operator explicitly asks.
- **Shop lens deep-link to asset card (P3 · gated)**: If operator finds the lens useful and asks for deep-link to a full asset card, the cheapest path is to enable Shop tokens on the frontend `/operations-map` guard (backend already accepts them). Requires its own workflow-discovery track per the permanent doctrine.

### Permanent exclusions (unchanged)
- Safety · Leadership · Mechanic — NO MAP. Permanently excluded by Track 13.7A.

### Three permanent hard locks (unchanged · verified intact post-13.7B)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No new map systems · no new GPS / telematics providers · no new portals · no new APIs · no new auth · no route swaps · no UI modernization beyond what is explicitly approved.

---

## 2026-06-12 update · post Track 13.7B-VERIFY

### Completed
- ✅ Track 13.7B-VERIFY — Shop Recovery Map zero-marker source truth check · CLOSED (discovery only).

### Open decision (operator gate)
- **Decision A** · Accept Shop lens behaviour as truthful-but-thin until production Motive GPS proves it. No track required.
- **Decision B (gated)** · Authorize separate track to loosen `attention_reason` gate in `operations_map_v1.py` so `maintenance` / `inspection` are set regardless of band. Must verify against Dispatch hard lock first.
- **Decision C (preview only · safe)** · Preview-data reseed: backfill a handful of `fleet_defects` rows with truck_unit_numbers that DO match `asset_mappings.masci_unit_number`, and populate `equipment_inspections.equipment_id` for some open rows, so the lens can be visually exercised in preview without changing production architecture.

### Permanent hard locks (unchanged · verified intact)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No filter widening / no architecture change to `attention_reason` without operator authorization of a new track.

---

## 2026-06-12 update · post Track 13.7C

### Completed
- ✅ Track 13.7C — Shop Map Lens Preview Data Proof · CLOSED.

### Status of decisions from 13.7B-VERIFY
- Decision **C (preview-only seed)** has been EXECUTED — proved the lens renders correctly with valid data.
- Decision **A (accept lens-thin until production GPS)** remains a valid posture for production.
- Decision **B (loosen attention_reason gate)** is still deferred — requires its own workflow-discovery track if operator wants Shop lens to show units regardless of band.

### Open operator decisions
- Should the preview seed remain in place for ongoing demo/screenshots, or be rolled back after evidence capture?
- Should Decision B be authorized as Track 13.7D? (Loosen `band==red` gate so `maintenance` / `inspection` reasons fire regardless of GPS freshness. High blast radius: would also change Dispatch attention_breakdown and project_rollups.)

### Permanent hard locks (unchanged)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No production data writes.
- No new map systems · no new GPS / telematics providers · no new portals · no new APIs · no new auth · no route swaps.

---

## 2026-06-12 update · post Track 13.8A

### Completed
- ✅ Track 13.8A — Operational Workflow Gap Discovery · CLOSED (discovery only · no code).

### Operator decisions pending
- Authorise one operator-interview cycle (10 questions in §12 of the 13.8A report)?
- If only one build is authorised, the source-tailwind candidate is **Haul/Scale ticket structured entry** — still operator-interview gated.

### Permanent DO-NOT-BUILD list (reaffirmed)
- RFIs · Submittals · Change Orders (formal) · Pay Applications · Cost Management · Contract Management · Formal Document Control · Plan Revision Management · vendor location overlay · driver hub / driver auth · mechanic portal · Safety map lens · Leadership map lens · parallel map engine · cost/margin dashboards · sub-side login · AI auto-rewrite of Daily Reports.

### Permanent hard locks
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No new portals / APIs / auth / map systems / route swaps without explicit operator authorisation tied to a discovery-then-build track.

---

## 2026-06-12 update · post Track 13.8B

### Completed
- ✅ Track 13.8B — Hidden Systems Audit & Recovery Discovery · CLOSED.

### Operator-interview-gated recovery candidates (in priority order)
1. **PO Requests surfacing** (PM Hub V2 + Field Leadership V2) — 95% complete · zero new backend.
2. **Operational Events project-day panel** (PM project-detail) — 90% complete · zero new backend.
3. **Operational Locations reconciliation surfacing** (Admin Hub V2) — 100% complete · link-only · zero new backend.
4. **MaterialMovementTile in PM Hub V2 daily-report context** — 100% (read-view) · zero new backend.
5. **Scale-ticket structured entry** (Track 13.8A §7.2 reaffirmed) — 30% (schema-slot only) · operator-interview gated.

### Background activation candidates (also operator-gated)
- MaintainX credential activation (~70% built · medium recovery cost).
- FleetWatcher (~10% built · high recovery cost · no operator pain proof).

### Permanent retain
- Legacy `*_legacy` PM/HR/Safety/Shop/Dispatch routes until Track 13.6O after 30-day signoff window.

### Permanent do-not-revive
- Driver V2 · Field Leadership V2 (Track 13.6L doctrine).

### Five permanent hard locks (unchanged)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No new portals / APIs / auth / map systems / route swaps without explicit operator authorisation tied to a discovery-then-build track.

---

## 2026-06-12 update · post Track 13.8C halt

### Track 13.8C status
- **HALTED · DELIVERABLE COMPLETE** — operator runbook written; awaiting production read-only execution.
- Closes when an operator with prod read credentials executes §4 of the report and appends results to `TRACK_13_8C_LIVE_RESULTS.md`.

### Pre-deploy gate (P0)
- Cannot make an informed deploy/promote decision without §4 results.
- Recommend authorising a single read-only `mongosh` session against prod, ~30–60 min, by a person/role that already has production access (platform engineer / DBA / authorised admin).

### Pending operator decisions
- Authorise §4 runbook execution against production (who runs it · when · where results are written).
- Track 13.6N RC-1 operator signoff still pending.
- Track 13.7C preview seed still in place (rollback via `python3 /app/scripts/preview_seed_13_7c.py rollback` when ready).

### Hard locks reaffirmed in source (no production probe needed)
- Dispatch map dominance · Driver no-login · Shop Repair ≠ RTS · One map engine · One source of truth · MaintainX stub · FleetWatcher absent.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No code · no UI · no APIs · no auth · no routes.
- No production touches · no preview writes.

---

## 2026-06-12 update · post Track 13.8D

### Completed
- ✅ Track 13.8D — Hidden System Recovery & Certification · CLOSED.

### Single doctrine-pure SURFACE candidate (no operator interview required)
- **Operational Locations reconciliation queue link in Admin Hub V2** — link only · admin-only · zero new backend · zero new permission · improves operations-map `assignment.name` quality indirectly.

### Operator-interview-gated recovery candidates
1. PO Requests action-queue cards in PM Hub V2 + Field Leadership Hub.
2. Operational Events project-day panel on PM project-detail.
3. MaterialMovementTile in PM Hub V2 daily-report context.
4. `scale_ticket` structured-entry extension on driver attach.
5. Field Memory · Field Revision finishing (needs interview before any work).

### Background activation (operator-gated)
- MaintainX credentials + UI surface decision.

### Permanent retain (until 30-day signoff window completes)
- `*_legacy` PM/HR/Safety/Shop/Dispatch routes (Track 13.6O handles retirement).

### Permanent do-not-build / do-not-revive (Section 17 of 13.8D report)
- RFIs · Submittals · Change Orders (formal) · Pay Applications · Cost Management · Contract Management · Formal Document Control · Plan Revision Management · Vendor Map Overlay · Driver Hub · Driver Login · Mechanic Portal · Safety Map Lens · Leadership Map Lens · Parallel Map Engine · FleetWatcher full activation (no operator pain proof).

### Five permanent hard locks (verified intact)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No new portals / APIs / auth / map systems / route swaps without explicit operator authorisation tied to a discovery-then-build track.

---

## 2026-06-12 update · post Track 13.8E

### Completed
- ✅ Track 13.8E — Operational Locations Recovery Surfacing · CLOSED. Single doctrine-pure SURFACE executed without operator interview.

### Remaining operator-interview-gated recovery candidates
1. PO Requests action-queue cards in PM Hub V2 + Field Leadership Hub.
2. Operational Events project-day panel on PM project-detail.
3. MaterialMovementTile in PM Hub V2 daily-report context.
4. `scale_ticket` structured-entry extension on driver attach.
5. Field Memory · Field Revision finishing.
6. Notifications cadence + recipient quality tuning (combined with Track 13.8C runbook).
7. Operational Records / Operational Timeline use case validation.

### Pending operator decisions
- Track 13.6N RC-1 operator signoff still pending.
- Track 13.7C preview seed still in place (rollback via `python3 /app/scripts/preview_seed_13_7c.py rollback` when ready).
- Track 13.8C runbook execution against production read-only (whoever holds prod credentials).

### Permanent do-not-build (unchanged · reaffirmed)
RFIs · Submittals · formal Change Orders · Pay Applications · Cost / Contract / Document Control / Plan Revision Management · Vendor map overlay · Driver hub / Driver login · Mechanic portal · Safety map lens · Leadership map lens · Parallel map engine.

### Five permanent hard locks (verified intact post-13.8E)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
No deploy · no Save to GitHub · no merge · no new portals / APIs / auth / map systems / route swaps without explicit operator authorisation tied to a discovery-then-build track.

---

## 2026-06-12 update · post Track 13.8F

### Completed
- ✅ Track 13.8F — PO Requests Certification & Surfacing Plan · CLOSED.

### Single ready-to-execute spec
- **PO Requests action-queue card** spec is locked at §12 of `TRACK_13_8F_PO_REQUESTS_CERTIFICATION.md`. Awaiting one operator-interview cycle (PM + FL · ~20 min total) to choose destination (PM Hub V2 vs Field Leadership Hub vs both) before implementation track is authorised.

### Operator-interview-gated surfacing candidates (priority order)
1. **PO Requests card** (spec locked · interview chooses destination).
2. Operational Events project-day panel on PM project-detail.
3. MaterialMovementTile in PM Hub V2 daily-report context.
4. `scale_ticket` structured-entry extension on driver attach.
5. Field Memory · Field Revision finishing.
6. Notifications cadence + recipient tuning (combined with Track 13.8C runbook).
7. Operational Records / Operational Timeline use-case validation.

### Pending operator decisions
- Track 13.6N RC-1 operator signoff.
- Track 13.7C preview seed rollback decision.
- Track 13.8C runbook execution against production read-only.
- Operator interview cycle for Tracks 13.8F / 13.8A / 13.8B / 13.8D candidates.

### Permanent hard locks (unchanged · verified intact)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No code · no UI · no route changes without explicit operator authorisation.

---

## 2026-06-12 update · post Track 13.8G

### Completed
- ✅ Track 13.8G — Combined Operator Interview Crib Sheet · CLOSED. Printable packet ready.

### Critical-path next step
- **Conduct the interviews offline** using `/app/memory/TRACK_13_8G_OPERATOR_INTERVIEW_CRIB_SHEET.md`. ~45 min combined per role. 11 roles in priority order: PM · Field Leadership · Shop Manager · Superintendent · Dispatcher · Admin · HR · Safety · Foreman · Leadership · Driver.
- After interviews complete, a new synthesis track converts the packet into authorisations for: PO Requests card destination · Material Movement future · scale_ticket structured entry · Operational Events project-day panel · Notifications cadence tuning · Field Memory / Field Revision finishing · plus the broader 13.8A workflow gap candidates.

### Pending operator decisions (unchanged)
- Track 13.6N RC-1 operator signoff.
- Track 13.7C preview seed rollback decision.
- Track 13.8C runbook execution against production read-only.

### Five permanent hard locks (unchanged · verified intact)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No code · no UI · no route changes without explicit operator authorisation.

## 2026-06-12 update · post Tracks 13.9 / 13.9.1 / 13.10–13.12

### Completed this wave
- ✅ Track 13.9 — Final Disposition Certification · CLOSED (173-row matrix · 8-item Immediate Build Queue).
- ✅ Track 13.9.1 — ODR Certification Report · CLOSED (Track 13.10 authorised by source-truth).
- ✅ Track 13.10 — ODR Sidebar Surfacing in PM + Admin + Safety sidebars + FL Hub tile · DONE.
- ✅ Track 13.11 — PO Requests Action Card on PM Hub V2 · DONE (live counts: 252 / 13 / 23 in preview).
- ✅ Track 13.12 — Operations Actions surfacing in Admin Sidebar V2 · DONE (50 OPEN · 18 ASSIGNED · 9 CLOSED).

### Critical-path next step (Build Queue #4)
- **Track 13.13 — Operational Events Project-Day Panel on `PmProjectDetail.jsx`** (4–6h · Op-Value 65 · LOW risk).
  - Read-only panel embedding the existing `GET /api/operational-events/project-day/{project_number}/{date}` endpoint.
  - Honest empty state when day has no events.
  - Single file edit · zero backend touch · zero new permission.

### Remaining Build Queue items (5–8)
- Scale Ticket 4-field extension on `operational_attachments.scale_ticket` (8h · combined FINISH + IMPROVE).
- PO missing-receipts → tasks_notifications wire-up (5h).
- MaterialMovementTile embed in PM Hub V2 daily-rollup (1.5h).
- ODR PM-Hub pending-drafts pill (2.5h) — only meaningful AFTER Track 13.10 lands.

### Pending operator decisions (unchanged)
- Track 13.6N RC-1 operator signoff (30-day window).
- Track 13.6O — `*_legacy` route retirement after signoff window.
- Track 13.7C preview seed rollback decision.

### Five permanent hard locks (unchanged · verified intact this wave)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

### Forbidden / blocked (unchanged)
- No deploy · no Save to GitHub · no merge.
- No new portals · no new auth · no new RFI/Submittal/Pay-App/Doc-Control/Plan-Revision/Cost/Contract/Vendor-Map/Mechanic-Portal/Safety-Map/Leadership-Map/Driver-Auth.

## 2026-06-12 update · post Track 13.13

### Completed
- ✅ Track 13.13 — Operational Events Project-Day Panel surfaced on `PmProjectDetail.jsx` · honest empty/error states · DONE.

### Critical-path next step (Build Queue #5)
- **Track 13.14 — Scale Ticket 4-Field Extension** (~8h · Op-Value 75 · LOW risk).
  - Extend existing `operational_attachments.scale_ticket` slot with `weight_gross_lbs / weight_tare_lbs / weight_net_lbs / material_code`.
  - Accept on existing driver-attach POST. Render on PM `ViewDailyReport.jsx` Material Movement tile + dispatch detail attachment list.
  - Schema slot already exists in `operational_attachments.py`; this is the only backend-touching item in the queue.

### Remaining Build Queue items (6–8)
- PO missing-receipts → tasks_notifications wire-up (5h · pure additive · uses existing `admin/scan-missing-receipts` endpoint).
- MaterialMovementTile embed in PM Hub V2 daily-rollup (1.5h).
- ODR PM-Hub pending-drafts pill (2.5h).

### Hard locks (unchanged · verified intact this track)
1. Dispatch map dominance.
2. One map engine · one source of truth.
3. No map without workflow discovery.
4. Driver no-login.
5. Shop Repair ≠ Returned-To-Service.

## 2026-06-12 update · post Track 13.14

### Completed
- ✅ Track 13.14 — Scale Ticket 4-field extension on `operational_attachments.scale_ticket` · 8/8 pytest pass · DONE.

### Critical-path next step (Build Queue #6)
- **Track 13.15 — PO Missing-Receipts → tasks_notifications wire-up** (~5h · Op-Value 60 · LOW risk).
  - Bind `POST /api/admin/po-requests/scan-missing-receipts` output into per-assignee `tasks_notifications` rows.
  - Closes the receipt-loss operational loop and reinforces the PO Requests action card from Track 13.11.

### Remaining Build Queue items (7–8)
- MaterialMovementTile embed in PM Hub V2 daily-rollup (1.5h · Op-Value 45).
- ODR PM-Hub pending-drafts pill (2.5h · Op-Value 40 · only meaningful AFTER Track 13.10 sidebar lands — which it did).

After 13.15 + 13.16 + 13.17 land, the full 34-hour Immediate Build Queue from Track 13.9 §8 is closed. The platform's "collection of dashboards → operational heavy-civil OS" transition is complete.

## 2026-06-12 update · post Track 13.15

### Completed
- ✅ Track 13.15 — Live Portal Trust Copy Cleanup · DONE (copy alignment to App.js route truth · 8 files · zero workflow change).

### Critical-path next step (Build Queue #6 — unchanged)
- **Track 13.16 — PO Missing-Receipts → tasks_notifications wire-up** (~5h · Op-Value 60 · LOW risk).

### Remaining Build Queue items (7–8)
- MaterialMovementTile embed in PM Hub V2 daily-rollup (~1.5h).
- ODR PM-Hub pending-drafts pill (~2.5h).

### Hard locks intact post-13.15
- Dispatch map-first · Driver no-login · Shop Repair Complete ≠ Returned-To-Service · One map engine · One source of truth.
- DriverHubV2 retirement: `/driver/hub_v2` returns 404 by route-table absence (verified this track).

## 2026-06-12 · Post Track 13.16
- ✅ Track 13.16 — Dispatch sidebar dead-link cleanup · DONE.
- 🟢 Deployment readiness now GREEN.

### Critical-path next step
- **Track 13.17 — Build Queue #6 — PO Missing-Receipts → tasks_notifications wire-up** (~5h · Op-Value 60 · LOW risk).
  Bind existing `POST /api/admin/po-requests/scan-missing-receipts` output into per-assignee `tasks_notifications` rows.

### Remaining Build Queue items
- BQ #7 — MaterialMovementTile embed in PM Hub V2 daily-rollup (~1.5h · Op-Value 45).
- BQ #8 — ODR PM-Hub pending-drafts pill (~2.5h · Op-Value 40).

After 13.17 + 13.18 + 13.19 land, the entire 34-hour Immediate Build Queue from Track 13.9 §8 is closed. Then Track 13.6N opens the 30-day operator signoff window → Track 13.6O legacy retirement.

## 2026-06-12 · Post Track 13.26
- ✅ Track 13.26A + 13.26 — Asset Service Event Backbone (derived) · DONE.
- 🟢 Deployment readiness remains GREEN.

### Critical-path next step (operator-gated)
- **Track 13.27 — Unit History Timeline (frontend page)** (~4h · LOW risk · no backend change).
  Consume `GET /api/assets/{unit}/timeline` from a new `/shop/equipment/{unit}/history` page. Reuse Shop Hub V2 patterns. Operator-visible value: "Show me everything that happened to Unit 152" answered from one page.

### Future tracks (per Track 13.25 §13 build sequence)
- **Track 13.28** — Shop Mechanic Assignment + Repair Notes (operator decision gate on mechanic login).
- **Track 13.29** — Fuel/Lube Job Visit Form (new collection · multi-equipment lines · Motive geofence suggestion).
- **Track 13.30** — Fuel/Lube Daily Service-Truck Reconciliation (depends on 13.29).
- **Track 13.31** — PM Engine (derived first · reads Motive hours/odometer + last PM completion).
- **Track 13.32** — MaintainX Integration (BLOCKED on `MAINTAINX_API_KEY` + active service credentials).
- **Track 13.33** — Asset Care Command Center (Shop Hub V2 Section 05 or dedicated page · depends on 13.26–13.31).

After Track 13.27 lands, the Asset Service Event Backbone becomes operator-visible. Subsequent fuel/lube/PM/mechanic systems consume the SAME endpoint shape — no duplicate history surfaces.

## 2026-06-12 · Post Track 13.28A (READ-ONLY cert · no implementation)
- ✅ Source-truth certification CLOSED · readiness score 7.0/10 · LOW-RISK go-ahead for Track 13.28.
- 🟢 Deployment readiness remains GREEN.

### Recommended build order (rework-minimized · per Track 13.28A §11)
1. **Track 13.28** — Mechanic Assignment Workflow (LOW-MED risk · additive-only schema)
   - Add nullable assignment + identity fields on `fleet_defects` (assigned_to_mechanic_id, assigned_at, repair_started_at, shop_manager_reviewed_by_id + companions).
   - Add 4 endpoints: `assign` · `reassign` · `start` · `manager-review`.
   - Wire per-user fan-out (`tasks_notifications.assignee_user_id`).
   - Optional: `/shop/me` mechanic-only queue UI + assign dropdown.
   - Ship identity capture FIRST. Defer K6 per-action enforcement to follow-up Track 13.28b after 30 days of telemetry.
2. **Track 13.31** — PM Engine (LOW risk · derived first · reuses 13.28 lifecycle)
3. **Track 13.29** — Fuel/Lube Job Visit Form (MED risk · operator decision gate)
4. **Track 13.30** — Fuel/Lube Daily Service-Truck Reconciliation (depends on 13.29)
5. **Track 13.33** — Asset Care Command Center (LOW risk · pure read aggregation)
6. **Track 13.32** — MaintainX Integration (HIGH risk · BLOCKED on `MAINTAINX_API_KEY` + sync/write env flags)

### Decision gates pending operator approval
- (a) Authorize Track 13.28 implementation kickoff.
- (b) Confirm K6 (per-action RBAC enforcement) defers to Track 13.28b after telemetry.
- (c) Confirm Track 13.29 introduces "Fuel/Lube Operator" role + `fuel_service_visits` collection scope.
- (d) MaintainX credentials still embargoed pending vendor + IT.

## 2026-06-12 · Post Track 13.28 (BACKEND LIVE)
- ✅ Mechanic Assignment Workflow shipped backend-only. Architectural prerequisite for 13.29/13.31/13.33 unlocked.
- 🟢 Deployment readiness remains GREEN.

### Critical-path next step (operator-gated)
- **Track 13.31 — PM Engine (derived)** (~6h · LOW risk · reuses 13.28 lifecycle · ZERO new persistence in v1)
  Read Motive hours/odometer + last PM completion from `fleet_defects` (kind=pm once defect lifecycle is extended). Validates the new assignment chain under heavier load before 13.29 introduces a brand-new collection.
  Backbone gains real `pm` event_type instead of placeholder.

### Or in parallel
- **Track 13.28 Phase 2 — Shop Hub V2 assignment UI** (~4h · frontend only · no backend change). Adds manager assign-dropdown on `/shop/fleet/defects/{id}` + mechanic queue at `/shop/me` + manager queue at `/shop/manager`.

### Future tracks (per 13.28A §11)
- **Track 13.29** — Fuel/Lube Job Visit Form (MED risk · operator decision gate on new role + collection).
- **Track 13.30** — Service-Truck Daily Reconciliation (depends on 13.29).
- **Track 13.33** — Asset Care Command Center (LOW risk · pure read aggregation over 13.26/13.28/13.31).
- **Track 13.32** — MaintainX Integration (HIGH risk · LAST · BLOCKED on `MAINTAINX_API_KEY`).
- **Track 13.28b** — K6 per-action RBAC enforcement (deferred 30 days for telemetry).

## 2026-06-12 · Post Track 13.28 Phase 2 (UI + Parts Capture LIVE)
- ✅ Shop accountability now usable from the UI: Shop Manager assigns, mechanic accepts/starts/completes with parts + notes, manager reviews. Dispatch retains RTS.
- 🟢 Deployment readiness remains GREEN.

### Critical-path next step (operator-gated)
- **Track 13.31 — PM Engine (derived)** (~6h · LOW risk · reuses 13.28 lifecycle). PM events plug into the now-shipped assignment chain. Zero new persistence in v1.

### Or in parallel
- **Track 13.28 Phase 3 — Per-Unit Parts Intelligence read-only endpoint** (~2-3h additive). `GET /api/units/{unit_number}/parts-history` projects `fleet_defects.parts_used[]` into a frequency-ranked summary. Operator win once parts data accrues.
- **Track 13.27 — Unit History Timeline UI** consuming `GET /api/assets/{unit}/timeline` end-to-end (~4h · frontend only).

### Future tracks (per 13.28A §11)
- Track 13.29 — Fuel/Lube Job Visit Form (MED risk · operator decision gate).
- Track 13.30 — Service-Truck Daily Reconciliation (depends on 13.29).
- Track 13.33 — Asset Care Command Center (LOW risk · aggregation over 13.26/13.28/13.31).
- Track 13.32 — MaintainX Integration (HIGH risk · LAST · BLOCKED on `MAINTAINX_API_KEY`).
- Track 13.28b — K6 per-action RBAC enforcement (deferred 30 days for telemetry).

## 2026-06-12 · Post Track 13.27 (Unit History UI LIVE)
- ✅ Unit History Timeline shipped. Asset Service Event Backbone (Track 13.26) is now operator-visible end-to-end.
- 🟢 Deployment readiness remains GREEN.

### Critical-path next step (operator-gated)
- **Track 13.31 — PM Engine (derived)** (~6h · LOW risk · reuses 13.28 lifecycle). PM events plug into the now-shipped assignment chain AND immediately render on the Unit History timeline with zero code change. Best ROI in the backlog.

### Or in parallel
- **Track 13.28 Phase 3 — Known-Parts-By-Unit endpoint** (~2-3h additive). `GET /api/units/{unit_number}/parts-history` aggregates `fleet_defects.parts_used[]` into a frequency-ranked summary. Becomes a panel on the Unit History page.
- **Track 13.29 — Fuel/Lube Job Visit Form** (MED risk · operator decision gate · closes next-largest placeholder on the Unit History page).

### Future tracks (per 13.28A §11)
- Track 13.30 — Service-Truck Daily Reconciliation (depends on 13.29).
- Track 13.33 — Asset Care Command Center (LOW risk · aggregation over 13.26/13.27/13.28/13.31).
- Track 13.32 — MaintainX Integration (HIGH risk · LAST · BLOCKED on `MAINTAINX_API_KEY`).
- Track 13.28b — K6 per-action RBAC enforcement (deferred 30 days for telemetry).
- Track 13.27 P2 polish — equipment-list / fleet-row inline "View History" action + dedicated timeline rail aesthetic + print-friendly layout.

## 2026-06-12 · Post Track 13.29 (Fuel/Lube Visit Record LIVE)
- ✅ Fuel/Lube Visit Record shipped. Asset Service Event Backbone now carries real `fuel · fluid · service · meter` events. Only `pm` and `maintainx` remain as placeholders.
- 🟢 Deployment readiness remains GREEN.

### Critical-path next step (operator-gated)
- **Track 13.31 — PM Engine (derived)** — closes the second-to-last placeholder; reuses 13.28 lifecycle.

### Or in parallel
- **Track 13.30 — Service-Truck Daily Reconciliation** — rolls up the fuel data now flowing in. Depends on 13.29 (✓ shipped).
- **Track 13.29 Phase 2 — Fuel/Lube list + detail UI** (~3h frontend · backend ready).
- **Track 13.33 — Asset Care Command Center** — aggregation over 13.26/13.27/13.28/13.29.
- **Track 13.32 — MaintainX Integration** — HIGH risk · LAST · BLOCKED on `MAINTAINX_API_KEY`.
- **Track 13.28b — K6 per-action RBAC enforcement** — 30-day telemetry deferral.
