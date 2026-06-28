"""TRACK 16.16 · Operations × Transportation Integration Layer · regression.

Thin read-only consumer endpoint + four operator-awareness components
that surface Transportation health inside Operations workflows
(PmProjectDetail · OperationsCenterCommand · PmCommandCenter).

This regression locks the contract:

  1. Backend route exists with the correct prefix.
  2. Cross-portal RBAC (any signed-in portal token can READ).
  3. Endpoint composes EXISTING engines — no new scoring, no new
     collections, no new audit kinds.
  4. Response envelope carries the keys the frontend binds to.
  5. Banner stays SILENT when no risks exist (no warning fatigue).
  6. All four frontend components defined + mounted in the right
     pages with the required data-testid coverage.
  7. Regression file wired into the deployment gate.
"""
from __future__ import annotations

import asyncio
import inspect
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ROUTE = BACKEND / "routes" / "operations_transportation_integration.py"
SERVER = BACKEND / "server.py"

FE_COMP = (
    ROOT / "frontend" / "src" / "components"
    / "operations_transportation_integration.jsx"
)
FE_PM_PROJECT = ROOT / "frontend" / "src" / "pages" / "PmProjectDetail.jsx"
FE_OC_CMD = ROOT / "frontend" / "src" / "pages" / "OperationsCenterCommand.jsx"
FE_PM_CMD = ROOT / "frontend" / "src" / "pages" / "PmCommandCenter.jsx"

GATE = ROOT / "scripts" / "deployment_gate.py"


# ---------------------------------------------------------------------------
# In-memory DB doubles. Identical shape to the Track 16.15 / 16.15A doubles.
# ---------------------------------------------------------------------------
def _matches(row, q):
    for k, v in (q or {}).items():
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
                return False
            continue
        if isinstance(v, dict) and ("$gte" in v or "$lt" in v or "$ne" in v):
            val = row.get(k) or ""
            if "$gte" in v and val < v["$gte"]:
                return False
            if "$lt" in v and val >= v["$lt"]:
                return False
            if "$ne" in v and row.get(k) == v["$ne"]:
                return False
            continue
        if row.get(k) != v:
            return False
    return True


class _Cur:
    def __init__(self, items): self._items = list(items)
    def sort(self, *_, **__): return self
    def limit(self, _): return self
    async def to_list(self, _=None): return list(self._items)


class _Coll:
    def __init__(self): self.rows: List[Dict[str, Any]] = []

    def find(self, q=None, *_, **__):
        return _Cur([r for r in self.rows if _matches(r, q or {})])

    async def count_documents(self, q=None):
        return sum(1 for r in self.rows if _matches(r, q or {}))

    async def find_one(self, q=None, *_, **kwargs):
        rows = [r for r in self.rows if _matches(r, q or {})]
        sort = kwargs.get("sort")
        if sort:
            key, direction = sort[0]
            rows.sort(key=lambda r: r.get(key) or "", reverse=direction == -1)
        return rows[0] if rows else None


class _DB:
    def __init__(self): self._c: Dict[str, _Coll] = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._c:
            self._c[name] = _Coll()
        return self._c[name]

    def __getitem__(self, k): return getattr(self, k)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ===========================================================================
# 1 — Backend module + route file exists with the right prefix.
# ===========================================================================
def test_01_route_file_exists():
    assert ROUTE.exists(), (
        "Track 16.16 must ship routes/operations_transportation_integration.py"
    )
    src = ROUTE.read_text()
    assert 'prefix="/api/operations"' in src
    assert '@router.get("/transportation/readiness")' in src


# ===========================================================================
# 2 — Registered in server.py with cross-portal RBAC.
# ===========================================================================
def test_02_route_registered_in_server():
    src = SERVER.read_text()
    assert "register_track_16_16_routes" in src
    assert "operations_transportation_integration" in src
    assert "make_require_any_portal_token" in src
    # Track 16.16 wiring must use the cross-portal helper, NOT
    # require_admin_strict, so PMs / Dispatch can see the integration.
    register_block = src[src.find("register_track_16_16_routes"):]
    register_block = register_block[: register_block.find("\n\n\n")]
    assert "require_any_portal_dep" in register_block


# ===========================================================================
# 3 — No new scoring functions introduced.
# ===========================================================================
def test_03_no_new_scoring_in_route():
    src = ROUTE.read_text()
    for forbidden in (
        "def compute_driver_intelligence",
        "def compute_carrier_intelligence",
        "def compute_truck_intelligence",
        "def composite(",
        "def derive_band(",
        "def grade(",
        "compute_score",
    ):
        assert forbidden not in src, (
            f"Track 16.16 must consume existing engines — found "
            f"forbidden scoring marker {forbidden!r}"
        )


# ===========================================================================
# 4 — Route composes EXISTING engines via inline imports.
# ===========================================================================
def test_04_composes_existing_engines():
    src = ROUTE.read_text()
    # Must reference each existing engine by canonical name. Track 16.16
    # deliberately consumes ONLY lightweight engines (cleanup signals +
    # HR sync + Phase-2 counters) and never invokes the heavyweight
    # Track 16.12 per-entity intelligence engine from this endpoint.
    for must in (
        "transportation_dashboard_hr_health",
        "transport_eligibility_state",
        "carrier_documents",
        "driver_documents",
        "transport_action_items",
    ):
        assert must in src, (
            f"Track 16.16 must reuse {must!r} — pure consumer pattern."
        )
    # And explicitly NOT call the heavyweight intelligence/cleanup
    # engines from this hot path (they live on dedicated surfaces).
    assert "build_operational_health" not in src, (
        "Track 16.16 must NOT call build_operational_health from "
        "this endpoint — performance discipline."
    )
    assert "build_executive_dashboard" not in src, (
        "Track 16.16 must NOT call build_executive_dashboard from "
        "this endpoint — performance discipline."
    )
    assert "build_cleanup_signals" not in src, (
        "Track 16.16 must NOT call build_cleanup_signals from this "
        "endpoint — that 7s scan already runs on the Transportation "
        "Dashboard / Cleanup Companion."
    )


# ===========================================================================
# 5 — No new collection created. No write call on the source records.
# ===========================================================================
def test_05_route_is_read_only():
    src = ROUTE.read_text()
    forbidden_writes = (
        ".insert_one(",
        ".insert_many(",
        ".update_one(",
        ".update_many(",
        ".delete_one(",
        ".delete_many(",
        ".replace_one(",
        ".find_one_and_update(",
    )
    for needle in forbidden_writes:
        assert needle not in src, (
            f"Track 16.16 must be read-only (found {needle!r} in route)."
        )


# ===========================================================================
# 6 — Endpoint envelope smoke test against an in-memory DB.
# ===========================================================================
def test_06_endpoint_envelope_shape():
    from routes.operations_transportation_integration import (
        register_track_16_16_routes,
    )
    db = _DB()

    # Fake FastAPI app so we can introspect the registered route.
    class _Body:  # minimal include_router stand-in
        def __init__(self): self.included = []
        def include_router(self, r): self.included.append(r)

    app = _Body()

    async def _allow(*_, **__):
        return {"actor": "test"}

    router = register_track_16_16_routes(app, db, require_any_portal_dep=_allow)
    # Find the route function on the router.
    handler = None
    for r in router.routes:
        if r.path.endswith("/transportation/readiness"):
            handler = r.endpoint
            break
    assert handler is not None, "readiness route missing on router"

    out = _run(handler())
    assert out["ok"] is True
    assert out["schema_version"] == "16.16.0"
    for key in (
        "overall_readiness", "driver_band", "truck_band", "carrier_band",
        "dispatch_readiness", "capacity", "snapshot", "cleanup", "hr_sync",
        "risks", "links",
    ):
        assert key in out, f"envelope missing {key}"
    assert "transportation_dashboard" in out["links"]
    assert "cleanup_companion" in out["links"]
    # snapshot must contain the documented operator-facing counters.
    for k in (
        "available_drivers", "available_trucks", "available_carriers",
        "pending_reviews", "blocked_dispatches", "open_action_items",
        "upcoming_expirations_30d", "documents_awaiting_review",
    ):
        assert k in out["snapshot"], f"snapshot missing {k}"


# ===========================================================================
# 7 — Risks builder stays SILENT when fleet is healthy (no fatigue).
# ===========================================================================
def test_07_risks_silent_when_healthy():
    from routes.operations_transportation_integration import _build_risks
    out = _build_risks(
        blocked_dispatches=0,
        top_cleanup=None,
        hr_health={"counts": {"sync_mismatches": 0}},
        upcoming_expirations=0,
    )
    assert out == [], "Risk banner must remain silent when fleet is healthy"


# ===========================================================================
# 8 — Risks builder surfaces blocked dispatches as action_required.
# ===========================================================================
def test_08_risks_surface_blocked_dispatches():
    from routes.operations_transportation_integration import _build_risks
    out = _build_risks(
        blocked_dispatches=5,
        top_cleanup=None,
        hr_health={},
        upcoming_expirations=0,
    )
    assert len(out) == 1
    assert out[0]["code"] == "blocked_dispatches"
    assert out[0]["severity"] == "action_required"


# ===========================================================================
# 9 — Band projection green ≥ 80 · yellow ≥ 50 · red otherwise.
# ===========================================================================
def test_09_band_projection_thresholds():
    from routes.operations_transportation_integration import _band_from_score
    assert _band_from_score(95)["label"] == "green"
    assert _band_from_score(80)["label"] == "green"
    assert _band_from_score(79.9)["label"] == "yellow"
    assert _band_from_score(50)["label"] == "yellow"
    assert _band_from_score(49.9)["label"] == "red"
    assert _band_from_score(0)["label"] == "red"


# ===========================================================================
# 10 — All four frontend components are defined.
# ===========================================================================
def test_10_frontend_components_defined():
    src = FE_COMP.read_text()
    for comp in (
        "TransportationReadinessCard",
        "TransportationRiskBanner",
        "OperationsTransportationHealthWidget",
        "TransportationCloseoutAwareness",
        "useTransportationReadiness",
    ):
        assert f"function {comp}(" in src or f"export function {comp}(" in src, (
            f"Track 16.16: frontend component {comp!r} missing."
        )


# ===========================================================================
# 11 — Required data-testid coverage on the integration surface.
# ===========================================================================
def test_11_required_testids_present():
    src = FE_COMP.read_text()
    # Section-level data-testid markers rendered directly in JSX.
    direct_markers = (
        # Readiness card
        "ops-tx-readiness-card",
        "ops-tx-readiness-title",
        "ops-tx-readiness-view-link",
        # Risk banner
        "ops-tx-risk-banner",
        "ops-tx-risk-banner-link",
        "ops-tx-risk-list",
        # Health widget
        "ops-tx-health-widget",
        "ops-tx-health-widget-link",
        # Closeout
        "ops-tx-closeout-complete",
        "ops-tx-closeout-unresolved",
        "ops-tx-closeout-link",
    )
    for tid in direct_markers:
        assert f'data-testid="{tid}"' in src, (
            f"Track 16.16: required data-testid {tid!r} missing."
        )

    # Helper-rendered testids (passed as a `testid` prop to BandChip
    # / Tile helpers, which interpolate them as data-testid).
    helper_markers = (
        # BandChip
        "ops-tx-readiness-overall",
        "ops-tx-health-widget-band",
        # Tile (readiness)
        "ops-tx-tile-drivers",
        "ops-tx-tile-trucks",
        "ops-tx-tile-carriers",
        "ops-tx-tile-risks",
        "ops-tx-tile-cleanup",
        "ops-tx-tile-dispatch",
        # Tile (health widget)
        "ops-tx-health-tile-blocked",
        "ops-tx-health-tile-pending",
        "ops-tx-health-tile-expiring",
        "ops-tx-health-tile-cleanup",
    )
    for tid in helper_markers:
        assert tid in src, (
            f"Track 16.16: required testid prop {tid!r} missing."
        )

    # Lock the helpers actually render data-testid={testid} so QA can
    # bind to those tiles.
    assert "data-testid={testid}" in src, (
        "Track 16.16: Tile/BandChip helpers must render data-testid={testid}."
    )


# ===========================================================================
# 12 — Frontend mounts the components in the right pages.
# ===========================================================================
def test_12_components_mounted_in_target_pages():
    pm_proj = FE_PM_PROJECT.read_text()
    assert "TransportationReadinessCard" in pm_proj
    assert "TransportationRiskBanner" in pm_proj
    assert "TransportationCloseoutAwareness" in pm_proj
    assert "pm-project-tx-integration" in pm_proj
    assert "pm-project-tx-closeout" in pm_proj

    oc = FE_OC_CMD.read_text()
    assert "OperationsTransportationHealthWidget" in oc
    # Must be rendered inside the page body, not just imported.
    assert "<OperationsTransportationHealthWidget" in oc

    pm_cmd = FE_PM_CMD.read_text()
    assert "OperationsTransportationHealthWidget" in pm_cmd
    assert "<OperationsTransportationHealthWidget" in pm_cmd


# ===========================================================================
# 13 — Endpoint URL the components consume MUST be the new route only.
# ===========================================================================
def test_13_frontend_consumes_correct_endpoint():
    src = FE_COMP.read_text()
    assert "/operations/transportation/readiness" in src
    # Components must NOT call the admin-only Transportation dashboard
    # directly (that would defeat cross-portal access).
    assert "/admin/transportation/dashboard" not in src
    # Components must NOT call the cleanup-signals endpoint directly —
    # we read it via the composer.
    assert "/admin/transportation/intelligence/cleanup-signals" not in src


# ===========================================================================
# 14 — Track 16.16 regression file is wired into the deployment gate.
# ===========================================================================
def test_14_regression_wired_into_deployment_gate():
    src = GATE.read_text()
    assert (
        "test_track_16_16_operations_transportation_integration.py" in src
    ), (
        "Track 16.16 regression must be wired into "
        "/app/scripts/deployment_gate.py."
    )


# ===========================================================================
# 15 — Risk banner stays silent when the readiness envelope reports no
#      risks. Lock the "no warning fatigue" guarantee in source.
# ===========================================================================
def test_15_banner_silent_when_no_risks():
    src = FE_COMP.read_text()
    banner_block_idx = src.find("function TransportationRiskBanner(")
    assert banner_block_idx >= 0, "RiskBanner component must exist"
    banner_block = src[banner_block_idx : banner_block_idx + 1200]
    # The banner MUST early-return null when risks.length === 0.
    assert re.search(
        r"risks\.length\s*===\s*0[\s\S]{0,200}return\s+null",
        banner_block,
    ), (
        "TransportationRiskBanner must return null when risks list is "
        "empty (no warning fatigue)."
    )
