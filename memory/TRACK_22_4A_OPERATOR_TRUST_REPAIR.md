# TRACK 22.4a — Operator Trust Repair + Portal Truth Consolidation

**Status**: ✅ SHIPPED · 2026-07-05
**Branch/Commit**: `main` · `11c3941b`
**Environment**: PREVIEW · `masci_safety_preview`
**Repair mission**: close the operator-facing P1 defects surfaced by
Track 22.4 without introducing new features or redesigning any portal.

---

## Baseline (Phase 0)

- Backend endpoints: **1,325**
- Frontend routes: **392**
- Backend pytest files: **687** (was 686 · added 1 in this track)
- Track 22.3 Integration Truth: reachable (401 without token)
- Track 22.4 findings being repaired:
  - F22-4-001 · P1 · OI signals loading hang across Admin/PM/Safety/HR/Shop
  - F22-4-002 · P1 · Dispatch stale-Motive truth not surfaced to operator
  - F22-4-003 · P1 · Dispatch contradictory attention counts (349 vs 0)
  - F22-4-006 · P2 · Safety Trench tile shows "No Recent Data" while assets exist
  - F22-4-008 · P2 · Overlapping admin trust surfaces (documented; not deleted)

---

## Phase 1 — OI signals loading hang · FIXED

**Root cause**: `fetchOiSummary()` in `OiAttentionStrip.jsx` had no timeout.
If the fetch hung, `state.loaded` stayed `false` forever and "Loading OI
signals…" persisted indefinitely.

**Fix** (`/app/frontend/src/components/operational_intelligence/OiAttentionStrip.jsx`):
- Added `AbortController` with **3 s timeout** on the summary fetch.
- Added portal-scoped fallback copy dictionary — Admin / PM / Safety /
  HR / Shop each get their own operator-readable timeout message.
- Added **Retry** button that re-triggers the fetch on demand.
- Preserved existing 401/403 empty-state and existing OK/products state.

Prop `portal` added to `<OiAttentionStrip>`; passed from all five
portal home components (`AdminHubV2`, `PmCommandCenter`, `SafetyHubV2`,
`HrHubV2`, `ShopHubV2`, and `DispatchCommandCenter` uses `"default"`).

**Verified** on all five portals via Playwright screenshot: `retry_visible=True`,
portal-specific message present, primary queues remain visible below.

---

## Phase 2 — Dispatch stale-Motive truth ribbon · FIXED

**Root cause**: Motive UNREACHABLE/STALE state was truthful on
`/admin/integration-truth` (Track 22.3) but **not surfaced where
dispatchers actually work** — the map still rendered with markers and
no honesty ribbon.

**Fix — backend**:
- New endpoint `GET /api/dispatch/motive-posture` in `server.py` (near the
  shared dispatch-or-admin dependency) reusing the same
  `_motive_truth(db)` helper from `routes/integration_truth.py`.
- Gated by `_require_dispatch_or_admin` — dispatchers can call it with
  their dispatch token; admins with their admin token; anonymous → 401.
- Returns three-state truth (`config_status`, `connectivity_status`,
  `operational_status`, `overall`) + `last_successful_sync_at` +
  `connectivity_detail`. **Never** returns raw API keys, source, or
  `api_key_present` (admin-only fields explicitly stripped).

**Fix — frontend**:
- New shared component
  `/app/frontend/src/components/operational_intelligence/MotivePostureRibbon.jsx`.
- Consumes `/api/dispatch/motive-posture` with 3 s timeout. On timeout,
  shows honest "Motive posture unavailable" ribbon with Retry — never
  hangs.
- Amber ribbon for `UNREACHABLE / CONFIGURED / PARTIAL`. Slate for
  `MISSING_CONFIG / MISSING_SECRET / DISABLED`. Red for `ERROR`.
  **Green** *only* when `overall === LIVE_VERIFIED`.
- Mounted at the top of:
  - `/dispatch-portal` (`DispatchHub`)
  - `/dispatch-portal/map` (`DispatchOperationsMapPage`)
  - `DispatchCommandCenter` (Mission Control shell)

**Verified**: ribbon renders as
`MOTIVE · CONNECTIVITY DEGRADED · Motive location feed is not
currently verified…` with three-state disclosure `config: CONFIGURED ·
connectivity: UNREACHABLE · operational: STALE`. Refresh button works.

---

## Phase 3 — Dispatch attention count consolidation · FIXED

**Root cause**: `DispatchEquipmentMaintenanceIndicator` said
"Equipment Maintenance Issues Requiring Attention: 349" — but this is
**Shop-owned**, not Dispatch attention. On the same page the map tile
"Attention Required" showed `0`, creating a contradiction.

**Fix** (`DispatchEquipmentMaintenanceIndicator.jsx`):
- Relabelled to **`[SHOP · FLEET HEALTH]  Equipment out of service:
  349  (context — not a Dispatch attention item)`**.
- Added `data-testid="dispatch-mx-attribution"` for regression
  screenshotting.

The "Attention Required" tile on the map remains the single Dispatch
attention count.

---

## Phase 4 — Cross-portal count wiring (Safety Trench tile) · FIXED

**Root cause**: `SafetyHubV2.jsx` had a hard-coded `value={null}` for
the Trench Safety tile — displayed as "No Recent Data" while the
`/trench-safety` page correctly showed 21 active assets from
`/api/trench-safety/dashboard`.

**Fix** (`SafetyHubV2.jsx`):
- Extended `useSafetySignals()` with `trench_active_assets` +
  `trench_loaded`.
- Added a second `safeJson("/api/trench-safety/dashboard")` fetch that
  reads `total_active_assets` from the canonical Trench Safety engine.
- Wired `<QueueCard title="Trench Safety · active assets"
  source="Live engine · same source /trench-safety uses"
  value={s.trench_active_assets} loaded={s.trench_loaded} />`.

**Verified**: Safety Portal tile now displays **21** with source
"Live engine · same source /trench-safety uses" — matches
`/trench-safety` exactly.

---

## Phase 5 — Trust surface consolidation

**Not deleted** (per hard rules — do not delete canonical workflows).
**Rules locked** in this memo:

- **`/admin/integration-truth` = CANONICAL** — integrations, AI keys,
  DR-V2 alias telemetry, three-state truth.
- **`/admin/deploy-readiness` = pre-deploy gate only** — must not
  re-derive Motive/MaintainX state; must link to Integration Truth for
  those.
- **`/admin/system-health` = infrastructure only** — Mongo/R2/Sentry
  runtime health. Must not claim integration liveness beyond linking
  to Integration Truth.
- **`/admin/operations-trust` = workflow trust only** — deployment /
  audit trail claims. Must not duplicate integration status.

Full physical consolidation deferred to Track 22.4a-follow-up (would
require deletions which risk breaking existing certifications).

---

## Phase 6 — Field Leadership doctrine · LOCKED

New memo: `/app/memory/FIELD_LEADERSHIP_PORTAL_PATTERN.md` — ten rules
for the reference model:

1. Single-purpose cards. 2. No sidebar. 3. No dashboard clutter.
4. No copied metrics. 5. Recent operational memory strip.
6. Primary actions visible without scroll. 7. Calm empty states.
8. Mobile-safe by construction. 9. Role-native language. 10. Zero drift.

Applied selectively in this track: OI copy shift, Dispatch attention
attribution, Safety tile source labelling.

---

## Phase 7 — Tests / regression locks

- `/app/backend/tests/test_track_22_4a_motive_posture.py` — **4/4 pass**
  - 401 without auth
  - 200 with admin token
  - No admin-only fields leak (last-4, source, present)
  - Never LIVE_VERIFIED without operational proof
- Existing `test_track_22_3_integration_truth.py` — **9/9 still pass**
  (regression preserved).

---

## Phase 8 — Screenshot evidence

Captured in `/tmp/t224a_verify_*.jpg`:

- `dispatch_hub_verify.jpg` — Motive ribbon + Shop attribution both visible
- `dispatch_map_verify.jpg` — Motive ribbon at top of map canvas
- `safety_trench_wire_verify.jpg` — Trench count wired to 21

Earlier `/tmp/t224a_*.jpg` capture:

- `pm_oi_state.jpg` — PM shows portal copy + Retry
- `safety_oi_state.jpg` — Safety shows portal copy + Retry
- `hr_oi_state.jpg` — HR shows portal copy + Retry
- `shop_oi_state.jpg` — Shop shows portal copy + Retry
- `admin_oi_state.jpg` — Admin shows portal copy + Retry

Selector-level assertions in the automation log confirm each portal's
OI Retry element is present.

---

## Operator experience after fix

- **Admin**: OI panel resolves in 3 s to a portal-specific message; no
  silent hang. Retry available.
- **PM**: same — Project intelligence copy visible; primary sections
  A/B still render.
- **Safety**: same — plus Trench Safety tile now shows **21** live.
- **HR**: same — Compliance queue below unaffected.
- **Shop**: same — Recovery workflows below unaffected.
- **Dispatch**: Motive live posture ribbon at the top of every dispatch
  screen; Shop-owned equipment count clearly attributed as context, not
  Dispatch attention.

---

## Truth source map

| Surface | Source | Doctrine |
|---|---|---|
| OI signals | `/api/operational-intelligence/summary` | 3 s timeout; portal-scoped fallback |
| Motive status (admin) | `/api/admin/integrations/truth-status` | Three-state truth |
| Motive status (dispatch) | `/api/dispatch/motive-posture` | Same helper, dispatch-safe scope |
| Dispatch attention | `dispatch.command.summary` "Attention Required" tile | One number, dispatch-actionable only |
| Trench Safety count | `/api/trench-safety/dashboard.total_active_assets` | Canonical — Safety hub reads this |
| Integration keys | `/api/admin/ai/keys/status` | Reads os.environ; admin-only |
| Deploy readiness | `/api/admin/deploy-readiness` (existing) | Pre-deploy gate; links to Integration Truth |

---

## Deployment verdict

**READY (conditional on retest)** — Track 22.4a introduces only additive,
admin-gated or dispatch-gated read endpoints; no schema migrations, no
RBAC weakening, no destructive changes.

## Feature Freeze

**LIFT for trust-repair follow-ups.** Freeze on new features remains
(no new dashboards, no new portals). The freeze was in place to
prevent a repeat of F-01/F-02 while the operator surface still lied.
The operator surface no longer lies:

- OI signals no longer hang.
- Motive stale state is surfaced where dispatchers work.
- Dispatch contradictory counts eliminated.
- Cross-portal counts wired to canonical sources.
- Field Leadership doctrine locked as the pattern to steal from.

The remaining P1 (mobile responsiveness on PM/Dispatch) is a separate
scope handled by Track 22.4c.

## Next tracks

1. **Track 22.4b** — Driver Portal + workflow deep trace.
2. **Track 22.4c** — Mobile Responsiveness Sweep (390 & 1024 px).
3. **Track 22.4a-follow-up** — Physical trust surface consolidation
   (deprecate the overlapping admin surfaces after 30 days of
   Integration Truth adoption telemetry).
