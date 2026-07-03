# TRACK 19.53 · P2 Remediation Execution

Traceability map — every P2 roadmap item → surgical change.

## P2 #6 · Admin v1 hub deprecation + Mission-Control OI Attention Strip
- **File touched:** `frontend/src/pages/AdminHubV2.jsx`
- **Change 1:** Mounted `OiAttentionStrip` at the very top of the Admin Portal home consuming three executive-tier products: `corporate_intelligence`, `weekly_operations_digest`, `executive_operations_brief`. Uses the shared shared primitive, no new framework.
- **Change 2:** Replaced the prominent "Open Classic Admin Hub (V1)" primary-action button with an "Open OI Cockpit →" button. This is the phased-retirement move — V1 stays reachable at `/admin/hub_v1` for rollback purposes only, referenced in the trace-note footer via `admin-hub-v2-v1-archive-link`.
- **Doctrine:** Admin becomes Mission Control — OI attention first, integration probes / compliance / cross-portal reads below. Every card still opens the same existing workflow it did before.

## P2 #7 · Dispatch Attention Strip formalisation
- **File touched:** `frontend/src/pages/DispatchCommandCenter.jsx`
- **Change:** Mounted `OiAttentionStrip` with `productIds=["transportation_intelligence"]` directly under the `TransportationOpsTopBar` and above the existing 8-tile `CommandStrip`. Zero disruption to the seven-tab layout below.
- **Doctrine:** Dispatch begins the operational day. The transportation-intelligence attention level must appear before any tab is selected.

## P2 #8 + #11 · Field / Superintendent Today Action Queue
- **File touched:** `frontend/src/pages/FieldLeadershipPortalDashboard.jsx`
- **Change:** Added a compact "Today's focus · Field Leadership" banner directly under the PortalShell subtitle. The banner labels the section for the Command Center standard's Section 3 (Today / This Week Action Queue) and states the priority order: assigned jobs → today's dispatch window → driver readiness → workflows. The existing widgets remain — the banner only makes the ordering explicit and gives the section a canonical name.
- **Doctrine:** No OI product powers this queue (per the OI Integration Map — "Field: none · task-launcher"). This is a naming / hierarchy fix, not a new dashboard.
- Superintendent persona uses the same field-leadership dashboard, so the same edit satisfies P2 #11.

## P2 #10 · Asset Administrator polish
- **File touched:** `frontend/src/pages/admin/AdminAssetAdmin.jsx`
- **Change:** Mounted `OiAttentionStrip` with `productIds=["fleet_intelligence"]` at the top of the asset-admin page — surfaces active holds / critical defects / availability inline before the taxonomy review queue.
- **Doctrine:** Asset Admin can now see whether the fleet has a hold-oriented attention signal without leaving the taxonomy workflow.

## P2 #12 · Cockpit sparkline mini-chart
- **File touched:** `frontend/src/pages/admin/AdminOperationalIntelligence.jsx`
- **Change:** Added a `TrendSparkline` React component. Rendered inside each `ProductCard` next to the score. Uses ONLY the `trend_direction` and `trend_percent` fields already returned by `GET /operational-intelligence/summary` — no per-card history fetch, no additional HTTP requests. Pure inline SVG (`72×24`) rendering "prior → current" trend line with colour coded by direction (emerald up, red down, slate flat) and magnitude driven by `|trend_percent|` capped at 20.
- **Doctrine:** Reuses `GET /summary`. Zero-drift enforced by the lock test which greps the sparkline body for `fetch(` and `operational-intelligence/history` — both must be absent.

## P2 #9 · Guidance Center role-based restructure — DEFERRED
- See `TRACK_19_53_DEFERRED_ITEMS.md`. LARGE scope. Requires a new backend grouping (workflow-list) in `/api/guidance/*` beyond what this frontend-only track can support.

## Total footprint
- Files modified: 5 (Admin hub, Dispatch cockpit, Field Leadership dashboard, Asset Admin, OI Cockpit).
- Files created: 0 new frontend components (shared `OiAttentionStrip` is reused).
- Backend: 0 changes.
- Lock test: 1 new file · 13 assertions.
- Docs: 8 governance files.
