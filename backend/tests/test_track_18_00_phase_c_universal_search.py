"""TRACK 18.00 · Phase C · RBAC-aware Universal Search regression.

Locks the search composer contract:
  · route exists, GET only, q required, anon blocked
  · per-portal RBAC (admin/dispatch/hr/pm/safety/shop/fl) result-type
    filtering
  · reuses existing collections only (no new search index)
  · no source-record mutation
  · safe escaped regex
  · stable response schema (18.00C)
  · frontend header search component + keyboard shortcut + debounce
  · grouped results + empty state + deep-link routes
  · Phase A shell + Phase B Mission Control preserved
  · wired into deployment gate
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ROUTE = BACKEND / "routes" / "transportation_search.py"
SERVER = BACKEND / "server.py"
FE_SEARCH = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationSearch.jsx"
FE_APP = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationApp.jsx"
FE_SHELL = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
FE_MC = ROOT / "frontend" / "src" / "pages" / "transportation" / "MissionControl.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


def _matches(row, q):
    for k, v in (q or {}).items():
        if isinstance(v, dict) and "$or" in v:
            continue
        if isinstance(v, dict) and "$regex" in v:
            import re
            if not re.search(v["$regex"], str(row.get(k) or ""), re.I):
                return False
            continue
        if row.get(k) != v:
            return False
    return True


class _Cur:
    def __init__(self, items):
        self._items = list(items)

    def limit(self, _):
        return self

    async def to_list(self, _=None):
        return list(self._items)


class _Coll:
    def __init__(self): self.rows = []

    def find(self, q=None, *_, **__):
        # Support $or queries used by the search route.
        if q and "$or" in q:
            ors = q["$or"]
            def match(r):
                import re
                for clause in ors:
                    for k, v in clause.items():
                        if isinstance(v, dict) and "$regex" in v:
                            if re.search(v["$regex"], str(r.get(k) or ""), re.I):
                                return True
                        elif r.get(k) == v:
                            return True
                return False
            return _Cur([r for r in self.rows if match(r)])
        return _Cur([r for r in self.rows if _matches(r, q or {})])

    async def insert_one(self, doc):
        self.rows.append(doc)
        return type("R", (), {"inserted_id": "_id"})()


class _DB:
    def __init__(self):
        self._c = {}

    def __getattr__(self, n):
        if n.startswith("_"):
            raise AttributeError(n)
        if n not in self._c:
            self._c[n] = _Coll()
        return self._c[n]

    def __getitem__(self, k):
        return getattr(self, k)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _get_handler():
    """Register the route on a stub app, return the search handler."""
    from routes.transportation_search import (
        register_track_18_00_phase_c_routes,
    )
    db = _DB()
    class _App:
        def __init__(self): self.included = []
        def include_router(self, r): self.included.append(r)
    app = _App()

    async def _ok(*_, **__):
        return {"_actor": "admin", "name": "admin"}

    router = register_track_18_00_phase_c_routes(
        app, db, require_any_portal_dep=_ok)
    handler = None
    for r in router.routes:
        if r.path.endswith("/search"):
            handler = r.endpoint
            break
    return handler, db


# ===========================================================================
# 1 — Route file exists with correct prefix + GET endpoint.
# ===========================================================================
def test_01_route_exists():
    assert ROUTE.exists()
    src = ROUTE.read_text()
    assert 'prefix="/api/admin/transportation"' in src
    assert '@router.get("/search")' in src


# ===========================================================================
# 2 — Route is registered in server.py with cross-portal helper.
# ===========================================================================
def test_02_registered_in_server():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_c_routes" in src
    assert "transportation_search" in src
    block_start = src.find("register_track_18_00_phase_c_routes")
    block = src[block_start:block_start + 600]
    assert "make_require_any_portal_token" in src
    assert "require_any_portal_dep" in block


# ===========================================================================
# 3 — Per-role allowlist filtering.
# ===========================================================================
def test_03_rbac_per_role_types():
    from routes.transportation_search import _types_for_role
    assert _types_for_role({"_actor": "admin"}) == set([
        "drivers","carriers","trucks","dispatch","projects",
        "documents","orientation","actions","intelligence","timeline",
    ])
    assert _types_for_role({"_actor": "dispatch"}) == {
        "trucks","drivers","carriers","dispatch","projects"}
    assert _types_for_role({"_actor": "hr"}) == {
        "drivers","documents","orientation"}
    assert _types_for_role({"_actor": "pm"}) == {
        "projects","dispatch","trucks"}
    assert _types_for_role({"_actor": "safety"}) == {
        "drivers","trucks"}
    assert _types_for_role({"_actor": "shop"}) == {"trucks"}
    assert _types_for_role({"_actor": "fl"}) == {"drivers","projects"}
    # Unknown / anon returns empty set.
    assert _types_for_role({}) == set()
    assert _types_for_role({"_actor": "garbage"}) == set()


# ===========================================================================
# 4 — Safe regex escapes user input.
# ===========================================================================
def test_04_safe_regex_escapes_input():
    from routes.transportation_search import _safe_regex
    # Special regex chars must be escaped, not interpreted.
    rx = _safe_regex("truck.*214")
    assert rx["$regex"] == r"truck\.\*214"
    assert rx["$options"] == "i"
    # Empty / whitespace returns empty projection.
    assert _safe_regex("") == {}
    assert _safe_regex("   ") == {}


# ===========================================================================
# 5 — Query bounded to MAX_QUERY chars.
# ===========================================================================
def test_05_query_bounded():
    from routes.transportation_search import _safe_regex, MAX_QUERY
    long_q = "x" * 500
    rx = _safe_regex(long_q)
    # The escaped regex string maps each x → x, so length should be
    # exactly MAX_QUERY after the [:MAX_QUERY] slice.
    assert len(rx["$regex"]) == MAX_QUERY


# ===========================================================================
# 6 — Admin sees results across all groups.
# ===========================================================================
def test_06_admin_envelope_shape():
    handler, db = _get_handler()
    db.transport_persons.rows = [{"id": "p1", "name": "John Truck"}]
    db.transport_trucks.rows = [{"id": "t1", "unit_number": "214", "vin": "1FUYZZZZZ"}]
    db.carriers.rows = [{"id": "c1", "name": "Sample Truck Lines"}]
    out = _run(handler(q="truck", limit=20, types=None, actor={"_actor": "admin"}))
    assert out["ok"] is True
    assert out["schema_version"] == "18.00C"
    assert out["query"] == "truck"
    assert "counts" in out and "results" in out
    # Every result MUST carry the documented contract.
    for r in out["results"]:
        for k in ("type", "title", "subtitle", "status", "source",
                  "route", "reason"):
            assert k in r, f"result missing {k}"


# ===========================================================================
# 7 — Dispatch token receives ONLY dispatch-safe groups.
# ===========================================================================
def test_07_dispatch_restricted():
    handler, db = _get_handler()
    db.transport_action_items.rows = [{"id": "a1", "title": "Truck cleanup"}]
    db.transport_trucks.rows = [{"id": "t1", "unit_number": "Truck-12"}]
    out = _run(handler(q="truck", limit=20, types=None, actor={"_actor": "dispatch"}))
    assert out["ok"] is True
    # Actions and documents and orientation MUST NOT appear.
    for r in out["results"]:
        assert r["group"] in {"trucks","drivers","carriers","dispatch","projects"}, (
            f"dispatch saw forbidden group {r['group']}"
        )


# ===========================================================================
# 8 — HR token blocked from trucks/dispatch/projects/actions.
# ===========================================================================
def test_08_hr_restricted():
    handler, db = _get_handler()
    db.transport_trucks.rows = [{"id": "t1", "unit_number": "T-99"}]
    db.transport_action_items.rows = [{"id": "a1", "title": "Truck cleanup"}]
    db.dispatch_assignments.rows = [{"assignment_id": "asg1", "driver_name": "Truck Lane"}]
    out = _run(handler(q="truck", limit=20, types=None, actor={"_actor": "hr"}))
    for r in out["results"]:
        assert r["group"] in {"drivers", "documents", "orientation"}, (
            f"HR saw forbidden group {r['group']}")


# ===========================================================================
# 9 — Unknown/anon role yields 403 no_search_permission.
# ===========================================================================
def test_09_unknown_role_rejected():
    from fastapi import HTTPException
    handler, _ = _get_handler()
    try:
        _run(handler(q="truck", limit=20, types=None, actor={"_actor": "anonymous"}))
    except HTTPException as exc:
        assert exc.status_code == 403
        assert "no_search_permission" in str(exc.detail)
        return
    raise AssertionError("Unknown role must be rejected with 403")


# ===========================================================================
# 10 — Route is read-only (NO writes other than the lightweight audit row).
# ===========================================================================
def test_10_no_source_record_mutation():
    src = ROUTE.read_text()
    # No update / delete / replace calls anywhere.
    for forbidden in (
        ".update_one(", ".update_many(", ".delete_one(",
        ".delete_many(", ".replace_one(", ".find_one_and_update(",
    ):
        assert forbidden not in src, (
            f"Search route must be read-only (found {forbidden})")
    # Only ONE insert is allowed (the audit row).
    insert_calls = src.count(".insert_one(")
    assert insert_calls == 1, (
        f"Search route must only emit ONE insert (the audit row); "
        f"found {insert_calls}")
    assert "transportation_search_performed" in src


# ===========================================================================
# 11 — No new search collection introduced.
# ===========================================================================
def test_11_no_new_search_collection():
    src = ROUTE.read_text()
    forbidden_collections = (
        "transportation_search_index",
        "transport_search_index",
        "search_index",
        "transportation_search_cache",
    )
    for c in forbidden_collections:
        assert c not in src, f"Phase C must not introduce {c!r}"


# ===========================================================================
# 12 — Composer reuses existing collections only.
# ===========================================================================
def test_12_uses_existing_collections():
    src = ROUTE.read_text()
    for coll in (
        "transport_persons", "carriers", "transport_trucks",
        "dispatch_assignments", "projects", "carrier_documents",
        "driver_documents", "transport_orientation_modules",
        "transport_orientation_certificates", "transport_action_items",
    ):
        assert coll in src, f"Search must compose from existing {coll}"


# ===========================================================================
# 13 — Audit row stores prefix, NOT the full query (PII safety).
# ===========================================================================
def test_13_audit_query_pii_safe():
    src = ROUTE.read_text()
    assert "query_prefix" in src
    assert "query_length" in src
    # Slice JUST the audit_events.insert_one(...) dict literal. The
    # full query must NOT be stored on the audit row.
    audit_start = src.find("db.audit_events.insert_one({")
    assert audit_start > 0, "audit insert block not found"
    audit_end = src.find("})", audit_start)
    audit_block = src[audit_start:audit_end]
    assert '"query": q' not in audit_block, (
        "Audit must not store the full search query (PII risk)")
    assert "kind" in audit_block
    assert "transportation_search_performed" in audit_block


# ===========================================================================
# 14 — Default limit 20 · max limit 50.
# ===========================================================================
def test_14_limit_bounds():
    from routes.transportation_search import DEFAULT_LIMIT, SAFE_MAX_LIMIT
    assert DEFAULT_LIMIT == 20
    assert SAFE_MAX_LIMIT == 50


# ===========================================================================
# 15 — Every result carries a deep-link route.
# ===========================================================================
def test_15_every_result_has_route():
    handler, db = _get_handler()
    db.transport_persons.rows = [{"id": "p1", "name": "Truck Tester"}]
    db.transport_trucks.rows = [{"id": "t1", "unit_number": "Truck-2"}]
    db.carriers.rows = [{"id": "c1", "name": "Truck Hauling"}]
    out = _run(handler(q="truck", limit=20, types=None, actor={"_actor": "admin"}))
    for r in out["results"]:
        assert r.get("route"), f"result missing route: {r!r}"


# ===========================================================================
# 16 — Frontend search component exists and uses the composer endpoint.
# ===========================================================================
def test_16_frontend_search_component():
    src = FE_SEARCH.read_text()
    assert "/admin/transportation/search" in src
    assert 'data-testid="txops-search"' in src
    assert 'data-testid="txops-search-input"' in src
    assert 'data-testid="txops-search-drawer"' in src
    assert 'data-testid="txops-search-empty"' in src
    assert 'data-testid="txops-search-clear"' in src


# ===========================================================================
# 17 — Keyboard shortcut and debounce wired.
# ===========================================================================
def test_17_shortcut_and_debounce_present():
    src = FE_SEARCH.read_text()
    assert 'data-testid="txops-search-shortcut-hint"' in src
    assert 'e.key === "/"' in src
    assert "DEBOUNCE_MS" in src
    assert "300" in src


# ===========================================================================
# 18 — Grouped result sections rendered.
# ===========================================================================
def test_18_grouped_results():
    src = FE_SEARCH.read_text()
    assert "txops-search-group-" in src
    assert "txops-search-result-action-" in src
    # Group labels for every documented group.
    for g in ("Drivers", "Carriers", "Trucks", "Dispatch",
              "Projects", "Documents", "Orientation", "Actions"):
        assert g in src, f"frontend missing group label {g!r}"


# ===========================================================================
# 19 — Search is mounted in the Transportation Operations shell.
# ===========================================================================
def test_19_search_mounted_in_shell():
    src = FE_APP.read_text()
    assert "TransportationSearch" in src
    assert "<TransportationSearch" in src
    assert 'data-testid="txops-search-rail"' in src


# ===========================================================================
# 20 — Phase A shell preserved.
# ===========================================================================
def test_20_phase_a_preserved():
    src = FE_SHELL.read_text()
    assert "TransportationWorkspaceShell" in src
    assert "txops-right-rail" in src


# ===========================================================================
# 21 — Phase B Mission Control preserved.
# ===========================================================================
def test_21_phase_b_preserved():
    src = FE_MC.read_text()
    assert "mc-mission-control" in src
    for c in (
        "mc-card-fleet","mc-card-drivers","mc-card-carriers","mc-card-dispatch",
        "mc-card-blocking","mc-card-recent","mc-card-attention","mc-card-next",
    ):
        assert c in src


# ===========================================================================
# 22 — Deployment gate wires the Phase C regression file.
# ===========================================================================
def test_22_deployment_gate_wired():
    src = GATE.read_text()
    assert "test_track_18_00_phase_c_universal_search.py" in src


# ===========================================================================
# 23 — Schema version locked to 18.00C.
# ===========================================================================
def test_23_schema_version():
    from routes.transportation_search import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00C"
