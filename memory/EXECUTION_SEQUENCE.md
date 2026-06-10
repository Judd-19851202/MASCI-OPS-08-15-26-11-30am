# EXECUTION SEQUENCE — Dispatch Command Center V1
**FORGEDOPS · 2026-02-10 · Architecture-Only · Approval Required Before Build**

> Phased, testable slices. Each phase ships independently and is
> regression-tested before the next phase begins. Pillars: Powerful ·
> Simple · Beautiful · Trusted · Proven.

---

## Pre-flight (zero new code, ~30 min)

- ✅ Architecture documents 1–8 generated (this sprint).
- ✅ Asset Spine P0.1–P0.7 already shipped and certified.
- ✅ Dispatch lifecycle state machine, magic-link SMS, driver session,
     fleet defect lifecycle, Shop recovery sub-state — all in production.
- ⚪ **OPERATOR ACTION REQUIRED:** Review + approve the 8 architecture
     documents.

---

## Phase 1 — Backend Aggregation Foundation (1 sprint, ~150 LOC)

**Goal:** Stand up the 4 dispatch command boards + shop command feed +
broadcast SMS endpoints. NO UI yet.

**Deliverables:**
- `backend/routes/dispatch_command_center.py` (new file)
  - `GET /api/dispatch/command/fleet`
  - `GET /api/dispatch/command/drivers`
  - `GET /api/dispatch/command/jobs`
  - `GET /api/dispatch/command/haul`
  - `POST /api/dispatch/broadcast-sms`
- `backend/routes/shop_command_feed.py` (new file)
  - `GET /api/shop/command-feed`
- New collection: `dispatch_broadcasts` (audit log)
- One-line `equipment_master.current_project_*` population in
  `routes/dispatch_lifecycle.py:create_assignment` (when
  `body.equipment_id` provided)
- Wire into `server.py` startup

**Tests:**
- `backend/tests/test_dispatch_command_center.py` — 5 pytest cases (one
  per endpoint).
- `backend/tests/test_shop_command_feed.py` — 2 cases.
- `backend/tests/test_dispatch_broadcast_sms.py` — 3 cases (happy, no
  credentials, rate-limited).

**Acceptance:**
- All 5 dispatch + 1 shop endpoint return 200 with the shapes in
  `DISPATCH_COMMAND_CENTER_ARCHITECTURE.md` §2.
- `testing_agent_v3_fork` backend-only run passes.

---

## Phase 2 — Dispatch Command Center UI Shell + Live Fleet Board (1 sprint, ~250 LOC)

**Goal:** Operator can navigate to `/dispatch-portal/command` and see
Live Fleet Board live-polling.

**Deliverables:**
- `frontend/src/pages/DispatchCommandCenter.jsx` — shell with top tile
  strip + tab nav.
- `frontend/src/components/dispatch/command/LiveFleetBoard.jsx` —
  consumes `/api/dispatch/command/fleet`, polls 30 s, tone-keyed status
  chips.
- `frontend/src/components/dispatch/command/CommandTileStrip.jsx` —
  the 7-tile header.
- Add lazy route to `App.js`:
  `<Route path="/dispatch-portal/command" element={…} />`
- `data-testid` on every row, button, chip.

**Smoke test:** screenshot via `mcp_screenshot_tool` on
`/dispatch-portal/command`.

---

## Phase 3 — Live Driver Board + Live Job Board + Live Haul Board (1 sprint, ~300 LOC)

**Deliverables:**
- `LiveDriverBoard.jsx`
- `LiveJobBoard.jsx`
- `LiveHaulBoard.jsx`
- Tab navigation inside `DispatchCommandCenter.jsx`.
- Deep links from each row to existing surfaces (`AssignmentDrawer`,
  `AssetProfile`, project pages).

**Tests:**
- `testing_agent_v3_fork` frontend run on all 4 board tabs.

---

## Phase 4 — Driver Comms (Broadcast SMS) Tile (1 sprint, ~120 LOC)

**Deliverables:**
- `frontend/src/components/dispatch/command/BroadcastSmsDrawer.jsx`
- Audience picker (all_active / project / driver-multi-select)
- 280-char message form with character counter
- Per-driver outcome rows after send
- Rate-limit visual feedback

**Tests:**
- Mock Twilio credentials in test env; assert `dispatch_broadcasts` rows
  + per-driver `delivery_log` rows.
- `testing_agent_v3_fork` covers the happy path + missing-creds path.

---

## Phase 5 — Cross-Portal Integrations (1 sprint, ~250 LOC)

**Deliverables:**
- Shop Command Feed surfaced on `ShopHub.jsx` (new section above existing).
- Shop Feed tile on `DispatchCommandCenter.jsx`.
- AssignmentCreateDrawer enhanced to show OOS warning chip (no block).
- DVIR / Weekly Lead / Safety Equipment defect badges on
  `LiveFleetBoard.jsx` rows.

**Tests:**
- `testing_agent_v3_fork` flow: Shop acknowledges defect → Dispatch
  sees status change live within 30 s poll.

---

## Phase 6 — PM Command Center (1 sprint, ~250 LOC backend + ~200 LOC frontend)

**Deliverables:**
- `backend/routes/pm_command_center.py` (6 endpoints per
  `PM_VISIBILITY_ARCHITECTURE.md` §4)
- `frontend/src/pages/PmCommandCenter.jsx` (one-page view)
- Lazy route `/pm/command-center` in `App.js`
- Top-level entry from `PmHub.jsx`

**Tests:**
- Backend: pytest scope test (PM cannot see another PM's project).
- Frontend: `testing_agent_v3_fork` happy + scope-denied path.

---

## Phase 7 — Operations Center Cross-Job View (1 sprint, ~200 LOC)

**Deliverables:**
- Extend `routes/operations_center.py` with 4 new endpoints
  (`live-fleet`, `live-drivers`, `live-jobs`, `live-haul`).
- Extend `ROLE_VISIBILITY` map with new card keys.
- Promote `OperationsCenter.jsx` route to `/operations-center` (admin /
  executive / operations role).
- Add Cross-Job Board table + Cross-Driver Attention table.

**Tests:**
- pytest + testing agent + screenshot.

---

## Phase 8 — Regression & Certification (1/2 sprint)

- Full `testing_agent_v3_fork` end-to-end flow (dispatcher creates
  assignment → driver acks → state transitions → haul completes →
  PM sees rollup → Shop sees DVIR fail → Operations Center sees
  attention).
- Performance audit (each board < 1.5 s p95).
- Audit-log spot-check (every write produces 3 rows).
- Generate `FORGEDOPS_DISPATCH_COMMAND_CENTER_V1_CERTIFICATION.md`.
- Update `PRD.md`, `CHANGELOG.md`, `ROADMAP.md`.

---

## Total estimated effort

| Phase | Sprints | LOC | Risk |
|---|---|---|---|
| 1 | 1 | 150 backend | Low — composition only |
| 2 | 1 | 250 frontend | Low |
| 3 | 1 | 300 frontend | Low |
| 4 | 1 | 120 frontend + 50 backend | Med — SMS rate-limit + audience targeting |
| 5 | 1 | 250 cross-portal | Med — touches 3 portals |
| 6 | 1 | 450 (250 BE + 200 FE) | Med — PM scope correctness |
| 7 | 1 | 200 | Low — extension only |
| 8 | 0.5 | — | Low |

**Total: ~8 sprints · ~1750 LOC.**

---

## Off-Ramps (where we explicitly STOP)

| Idea | V1? | Notes |
|---|---|---|
| Live map / GPS overlay | NO | violates "validate-don't-surveil" |
| Driver chat / inbound SMS | NO | V2 backlog |
| Predictive analytics / scoring | NO | doctrine forbids |
| FleetWatcher activation | NO | P1 separate sprint |
| MaintainX activation | NO | stub remains until API live |
| Multi-tenant routing claim parsing | NO | V2 |
| Per-asset utilization % | NO | V2 |
| Charts / graphs | NO | doctrine forbids |
| Driver mobile UI redesign | NO | V2 |

---

## Approval Gates

Each phase requires:
1. Author's screenshot or testing agent pass.
2. Update to `PRD.md` + `CHANGELOG.md`.
3. Operator approval before Phase N+1 starts (single message
   acknowledgement sufficient).

Phase 1 cannot start until the 9 architecture documents are
operator-approved.

---

## Files Touched (cumulative final state)

**Backend new files (4):**
- `routes/dispatch_command_center.py`
- `routes/shop_command_feed.py`
- `routes/pm_command_center.py`
- `tests/test_dispatch_command_center.py`
- `tests/test_shop_command_feed.py`
- `tests/test_pm_command_center.py`
- `tests/test_dispatch_broadcast_sms.py`

**Backend edits (3):**
- `routes/dispatch_lifecycle.py` (5-line `equipment_master` mirror on
  assignment create)
- `routes/operations_center.py` (extend with 4 endpoints + visibility
  map)
- `server.py` (3-line wiring)

**Frontend new files (~10):**
- `pages/DispatchCommandCenter.jsx`
- `pages/PmCommandCenter.jsx`
- `components/dispatch/command/CommandTileStrip.jsx`
- `components/dispatch/command/LiveFleetBoard.jsx`
- `components/dispatch/command/LiveDriverBoard.jsx`
- `components/dispatch/command/LiveJobBoard.jsx`
- `components/dispatch/command/LiveHaulBoard.jsx`
- `components/dispatch/command/BroadcastSmsDrawer.jsx`
- `components/shop/ShopCommandFeed.jsx`
- `components/pm/PmCommandCenterShell.jsx`

**Frontend edits (3):**
- `App.js` — add lazy routes
- `pages/ShopHub.jsx` — surface Shop Command Feed at top
- `pages/PmHub.jsx` — top-level entry to PM Command Center
- `components/dispatch/AssignmentCreateDrawer.jsx` — OOS warning chip

**Memory files updated each phase:**
- `PRD.md`, `CHANGELOG.md`, `ROADMAP.md`, `test_credentials.md`
- One per-phase certification doc

---

**Verdict:** Architecture is complete. Build sequence is testable in
slices. Awaiting operator approval to proceed with Phase 1.
