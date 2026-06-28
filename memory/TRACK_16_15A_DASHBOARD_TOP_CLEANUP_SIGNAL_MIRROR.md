# TRACK 16.15A · Dashboard Top Cleanup Signal Mirror

**Date:** 2026-02-10  
**Status:** ✅ GO  
**Type:** Pure UX bridge (frontend-only) · zero new backend logic

---

## Mission

Surface the **top cleanup signal** directly on the Transportation
Dashboard's *Attention Required* area, giving leadership a 5-second
read on the single most actionable cleanup opportunity — without
forcing them to navigate into the Cleanup Companion tab.

Strict additive constraint: **no new endpoints, no new scoring, no
new collections, no duplicate signal logic**. The widget consumes
the existing Track 16.15 endpoint and renders its `signals[0]`.

---

## Verdict

✅ **GO** — 12/12 new regression tests · 52/52 combined Track 16.15
+ 16.15A tests · live dashboard verified on preview (signal:
"Carrier packet needs correction" · 91 affected · severity
`action_required` · CTA routes to the existing Cleanup Companion
tab). Zero backend mutations.

---

## What shipped

* **`/app/frontend/src/pages/transportation/_views.jsx`** — new
  `TopCleanupOpportunityCard` component (≈110 LOC) mounted inside
  `TransportationDashboard` directly below the existing HR Health
  Widget. Reuses the dashboard's `txGet` admin helper.
* **`/app/backend/tests/test_track_16_15a_dashboard_cleanup_signal_mirror.py`**
  — 12 regression tests locking the contract (no new endpoint, no
  new lib, no scoring, testid coverage, severity inheritance,
  admin-only RBAC, deployment-gate wiring).
* **`/app/scripts/deployment_gate.py`** — wired in as the 22nd
  transport-track regression file.

---

## Backend (read-only, unchanged)

Reuses `GET /api/admin/transportation/intelligence/cleanup-signals`
(Track 16.15 · admin-only · returns `{ok, schema_version,
generated_at, range, signals[], note}`). Signals are already
server-sorted: `action_required` first, then by `affected_count`
desc — so `signals[0]` is canonically the top opportunity.

**No new routes. No new library. No new collections. No new
scoring. No backend changes whatsoever.**

---

## Frontend (dashboard widget)

```jsx
// Mounted inside TransportationDashboard, below <HrHealthWidget />.
<TopCleanupOpportunityCard />
```

States:
* **Loading** → `data-testid="tx-dashboard-top-cleanup-loading"`
* **Error** → `data-testid="tx-dashboard-top-cleanup-error"` (calm
  "Cleanup signals unavailable." copy; never punitive)
* **Empty** → `data-testid="tx-dashboard-top-cleanup-empty"` —
  emerald banner: *"No cleanup signals detected. Transportation
  data is currently in a healthy state."*
* **Top signal** → `data-testid="tx-dashboard-top-cleanup"` with
  six nested testids (title, severity, count, description,
  recommended, link).

CTA: **"View in Cleanup Companion →"** routes to
`/admin/transportation/intelligence/cleanup` (the existing
Track 16.15 panel — no new tab introduced).

---

## Hard guarantees (locked in regression)

1. **No new backend cleanup endpoint** — forbidden markers
   (`dashboard-cleanup`, `top-cleanup`, `cleanup-mirror`, etc.)
   absent from `routes/transportation_intelligence.py`.
2. **No new lib module / no new scoring function** — markers
   like `def compute_dashboard_top_signal` absent from
   `lib/transport_cleanup_companion.py`; no
   `transport_*dashboard_top_cleanup*.py` module exists.
3. **Reuses existing txGet helper** — no parallel fetch wrapper,
   no hardcoded URL bypass.
4. **Admin-only inheritance** — underlying endpoint still wired
   via `require_admin_dep`; dispatch users still cannot see the
   card.
5. **Empty-state copy mirrors Cleanup Companion** verbatim
   ("No cleanup signals detected. Transportation data is
   currently in a healthy state.").
6. **CTA points to existing Cleanup Companion tab** —
   `/admin/transportation/intelligence/cleanup` route is
   confirmed mounted in `_intelligence.jsx`.
7. **Top semantics inherit from `build_cleanup_signals`** —
   regression seeds a fixture and asserts `signals[0]` carries
   the canonical surface the widget binds to
   (`signal_key`, `title`, `description`, `severity`,
   `affected_count`, `recommended_action`).
8. **Deployment gate wired** —
   `test_track_16_15a_dashboard_cleanup_signal_mirror.py`
   included in `/app/scripts/deployment_gate.py`.

---

## Live verification

| Check | Evidence |
|---|---|
| Backend endpoint admin-only | `curl …/cleanup-signals?days=30` without token → 401 |
| Endpoint returns signals | With admin token → `ok=True · count=4` |
| Dashboard renders top card | Preview screenshot — "Carrier packet needs correction · 91 affected · action required" |
| CTA href | `/admin/transportation/intelligence/cleanup` |
| 12/12 new tests | `pytest tests/test_track_16_15a_dashboard_cleanup_signal_mirror.py` → 12 passed |
| 52/52 combined 16.15 + 16.15A tests | same suite — 52 passed in 0.11s |

---

## Files changed

| File | Change |
|---|---|
| `/app/frontend/src/pages/transportation/_views.jsx` | +1 component (`TopCleanupOpportunityCard`) + 1 JSX mount inside `TransportationDashboard` |
| `/app/backend/tests/test_track_16_15a_dashboard_cleanup_signal_mirror.py` | NEW · 12 regression tests |
| `/app/scripts/deployment_gate.py` | +1 line (regression file added) |

No backend route, library, or collection touched.

---

## Deferrals (out of scope)

* Per-record click-through from the dashboard card (Cleanup
  Companion tab already provides the Affected Records drawer).
* Multi-signal carousel on the dashboard (single-card discipline
  preserves the *"top opportunity"* read).
* Email digest of dashboard signals (separate Track 16.10A
  Command Digest already exists for that need).

---

## Next recommended track

Wire dashboard testids into the continuous browser smoke gate
(Track 15.86) so future regressions on the cleanup mirror are
caught at deploy time. Optional; the static regression already
locks the surface.
