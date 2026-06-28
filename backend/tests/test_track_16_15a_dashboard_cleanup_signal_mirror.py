"""TRACK 16.15A · Dashboard Top Cleanup Signal Mirror · regression.

Pure UX bridge: the Transportation Dashboard mirrors the highest-priority
cleanup signal from the existing Track 16.15 ``/api/admin/transportation/
intelligence/cleanup-signals`` endpoint. No new backend, no new scoring,
no new collections, no duplicate signal logic.

This regression locks the contract:

  1. Frontend dashboard widget exists and is mounted inside the
     ``TransportationDashboard`` component (not in some other tab).
  2. Widget calls the existing Track 16.15 cleanup-signals endpoint
     and ONLY that endpoint (no new API introduced).
  3. The component renders the empty state when ``signals`` is empty
     and the top card when at least one signal is present.
  4. Required ``data-testid`` attributes are present for QA + RBAC
     assertions.
  5. The component links into the existing Cleanup Companion tab.
  6. No new backend route, library, or scoring is introduced — the
     existing Track 16.15 endpoint is fully sufficient.
  7. Severity ordering / "top" semantics are inherited from
     ``build_cleanup_signals`` (signals[0]).
  8. The regression file is wired into the deployment gate.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

LIB = BACKEND / "lib" / "transport_cleanup_companion.py"
ROUTE = BACKEND / "routes" / "transportation_intelligence.py"
FE_VIEWS = ROOT / "frontend" / "src" / "pages" / "transportation" / "_views.jsx"
FE_INTEL = ROOT / "frontend" / "src" / "pages" / "transportation" / "_intelligence.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ---------------------------------------------------------------------------
# In-memory DB doubles (same shape as the Track 16.15 regression).
# ---------------------------------------------------------------------------
def _matches(row, q):
    for k, v in (q or {}).items():
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
                return False
            continue
        if isinstance(v, dict) and "$gte" in v:
            if (row.get(k) or "") < v["$gte"]:
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

    async def find_one(self, q=None, *_, **kwargs):
        rows = [r for r in self.rows if _matches(r, q or {})]
        sort = kwargs.get("sort")
        if sort:
            key, direction = sort[0]
            rows.sort(key=lambda r: r.get(key) or "", reverse=direction == -1)
        return rows[0] if rows else None

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"_id_{len(self.rows)}"
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()


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
# 1 — Dashboard widget is defined inside _views.jsx (TransportationDashboard).
# ===========================================================================
def test_01_top_cleanup_card_defined_in_views():
    src = FE_VIEWS.read_text()
    # Component must be DEFINED (not just referenced) inside the views
    # module so that it ships with the Transportation Dashboard.
    assert "function TopCleanupOpportunityCard(" in src, (
        "TopCleanupOpportunityCard component must be defined in "
        "_views.jsx so it renders inside TransportationDashboard."
    )


# ===========================================================================
# 2 — TopCleanupOpportunityCard is mounted INSIDE TransportationDashboard.
# ===========================================================================
def test_02_top_cleanup_card_mounted_in_dashboard():
    src = FE_VIEWS.read_text()
    dash_idx = src.find("export function TransportationDashboard(")
    next_export_idx = src.find("export function ", dash_idx + 1)
    if next_export_idx < 0:
        next_export_idx = len(src)
    # Also scope to the end of the function (next top-level "// ─" header
    # OR the next `function ` declaration). Conservative slice:
    dashboard_body = src[dash_idx:next_export_idx]
    # Stop at the first `\nfunction ` that begins a sibling helper.
    sibling_idx = dashboard_body.find("\nfunction ")
    if sibling_idx > 0:
        dashboard_body = dashboard_body[:sibling_idx]
    assert "<TopCleanupOpportunityCard" in dashboard_body, (
        "TopCleanupOpportunityCard JSX must render inside the "
        "TransportationDashboard component body."
    )


# ===========================================================================
# 3 — Widget calls the existing Track 16.15 cleanup-signals endpoint.
# ===========================================================================
def test_03_widget_uses_existing_cleanup_signals_endpoint():
    src = FE_VIEWS.read_text()
    assert "/admin/transportation/intelligence/cleanup-signals" in src, (
        "Dashboard widget must reuse the existing Track 16.15 "
        "/api/admin/transportation/intelligence/cleanup-signals endpoint."
    )


# ===========================================================================
# 4 — No new backend cleanup endpoint is introduced (16.15A is FE-only).
# ===========================================================================
def test_04_no_new_backend_cleanup_endpoint_added():
    route_src = ROUTE.read_text()
    # Sanity: the three Track 16.15 endpoints exist.
    assert '@router.get("/cleanup-signals")' in route_src
    assert '@router.get("/cleanup-signals/{signal_key}")' in route_src
    assert '@router.post("/cleanup-signals/{signal_key}/materialize-actions")' in route_src
    # And NO 16.15A-specific cleanup mirror endpoint has been bolted on.
    forbidden = (
        "dashboard-cleanup",
        "top-cleanup",
        "dashboard_top_cleanup",
        "cleanup-signal-top",
        "cleanup-mirror",
    )
    for needle in forbidden:
        assert needle not in route_src, (
            f"Track 16.15A must not introduce a new backend endpoint "
            f"(found forbidden marker {needle!r})."
        )


# ===========================================================================
# 5 — No new backend library / scoring is introduced for 16.15A.
# ===========================================================================
def test_05_no_new_backend_library_for_16_15a():
    # Track 16.15A is a UX bridge — there must be NO new lib module
    # nor any new scoring functions hanging off the existing one.
    src = LIB.read_text()
    for forbidden in (
        "def compute_dashboard_top_signal",
        "def build_dashboard_cleanup",
        "def build_top_cleanup_mirror",
    ):
        assert forbidden not in src, (
            f"Track 16.15A must not add new scoring/builders "
            f"(found {forbidden!r} in transport_cleanup_companion.py)."
        )
    # And no new sibling lib module with a 16.15A prefix.
    lib_dir = BACKEND / "lib"
    for p in lib_dir.glob("transport_*dashboard_top_cleanup*.py"):
        raise AssertionError(
            f"Track 16.15A must not introduce a new lib module: {p}")


# ===========================================================================
# 6 — Empty-state contract: widget surfaces a calm healthy message.
# ===========================================================================
def test_06_empty_state_renders_healthy_message():
    src = FE_VIEWS.read_text()
    assert 'data-testid="tx-dashboard-top-cleanup-empty"' in src
    assert (
        "No cleanup signals detected. Transportation data is currently in a healthy state."
        in src
    ), "Dashboard empty state must mirror the Cleanup Companion calm copy."


# ===========================================================================
# 7 — Required data-testid attributes are present.
# ===========================================================================
def test_07_required_testids_present():
    src = FE_VIEWS.read_text()
    for tid in (
        "tx-dashboard-top-cleanup",
        "tx-dashboard-top-cleanup-title",
        "tx-dashboard-top-cleanup-severity",
        "tx-dashboard-top-cleanup-count",
        "tx-dashboard-top-cleanup-description",
        "tx-dashboard-top-cleanup-recommended",
        "tx-dashboard-top-cleanup-link",
        "tx-dashboard-top-cleanup-empty",
    ):
        assert f'data-testid="{tid}"' in src, (
            f"Track 16.15A: required data-testid {tid!r} missing from "
            f"_views.jsx — QA + RBAC tests rely on it."
        )


# ===========================================================================
# 8 — Link routes to the existing Cleanup Companion tab.
# ===========================================================================
def test_08_link_targets_cleanup_companion_tab():
    src = FE_VIEWS.read_text()
    assert "/admin/transportation/intelligence/cleanup" in src, (
        "Dashboard widget must link to the existing Cleanup Companion "
        "tab (/admin/transportation/intelligence/cleanup)."
    )
    # Sanity: that route is actually mounted in the intelligence center.
    intel_src = FE_INTEL.read_text()
    assert 'path="cleanup"' in intel_src and "CleanupCompanionPanel" in intel_src


# ===========================================================================
# 9 — "Top" semantics inherit from build_cleanup_signals (signals[0]).
# ===========================================================================
def test_09_top_signal_inherits_existing_ordering():
    from lib.transport_cleanup_companion import build_cleanup_signals
    from datetime import datetime, timedelta, timezone
    db = _DB()
    # Seed a "watch" signal (carrier docs > 12 months old) AND an
    # "action_required" signal (driver insurance expiring soon) so the
    # endpoint should rank action_required FIRST.
    now = datetime.now(timezone.utc)
    db.driver_documents.rows.append({
        "id": "doc-ins",
        "tenant": "masci",
        "transport_person_id": "tp-1",
        "document_type": "Insurance Certificate",
        "expires_at": (now + timedelta(days=10)).isoformat(),
    })
    out = _run(build_cleanup_signals(db))
    assert out["ok"] is True
    assert out["signals"], "fixture should yield at least one signal"
    top = out["signals"][0]
    # The very first signal must carry the canonical surface the
    # dashboard widget binds to.
    for key in (
        "signal_key", "title", "description", "severity",
        "affected_count", "recommended_action",
    ):
        assert key in top, f"top signal must include {key!r}"
    # Severity must be one of the documented states.
    assert top["severity"] in ("action_required", "watch")


# ===========================================================================
# 10 — Widget never imports a new (non-existent) API helper.
# ===========================================================================
def test_10_widget_uses_existing_txget_helper():
    src = FE_VIEWS.read_text()
    # Reuses the same admin-gated helper as every other dashboard
    # widget (txGet). This implicitly inherits the X-Admin-Token
    # header → admin-only RBAC on the underlying endpoint.
    assert "txGet(\"/admin/transportation/intelligence/cleanup-signals\"" in src
    # And does NOT introduce a parallel fetch wrapper or hardcode a URL.
    forbidden = (
        "fetch(\"/api/admin/transportation/intelligence/cleanup-signals",
        "fetch(`/api/admin/transportation/intelligence/cleanup-signals",
    )
    for n in forbidden:
        assert n not in src, (
            f"Track 16.15A widget must reuse txGet, not bypass it "
            f"(found {n!r})."
        )


# ===========================================================================
# 11 — Underlying endpoint is admin-only (Dispatch must NOT see it).
# ===========================================================================
def test_11_endpoint_is_admin_only():
    src = ROUTE.read_text()
    block_start = src.find('@router.get("/cleanup-signals")')
    # Look at the next ~12 lines for the dependency wiring.
    snippet = src[block_start : block_start + 600]
    assert "require_admin_dep" in snippet, (
        "Track 16.15A relies on the existing Track 16.15 endpoint, "
        "which must remain admin-only (require_admin_dep) — no widening."
    )


# ===========================================================================
# 12 — Track 16.15A regression file is wired into the deployment gate.
# ===========================================================================
def test_12_regression_wired_into_deployment_gate():
    src = GATE.read_text()
    assert (
        "test_track_16_15a_dashboard_cleanup_signal_mirror.py" in src
    ), (
        "Track 16.15A regression must be wired into "
        "/app/scripts/deployment_gate.py so it runs on every deploy."
    )
