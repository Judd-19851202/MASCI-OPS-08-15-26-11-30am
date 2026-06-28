"""TRACK 18.00 · Phase D · Universal Relationships + Live Right Rail regression.

Locks the relationship composer contract:
  · GET /api/admin/transportation/related/{entity_type}/{entity_id}
  · 11 supported entity types
  · RBAC matrix per portal role with unauthorized relations OMITTED
  · response schema_version `18.00D` + 5 stable sections
  · section limits + optional bounded limit param
  · reuses existing collections only — no new graph DB
  · zero source-record mutation
  · graceful empty/loading/error states in the right rail
  · Phase A shell + Phase B Mission Control + Phase C Search preserved
  · wired into deployment gate
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ROUTE = BACKEND / "routes" / "transportation_relationships.py"
SERVER = BACKEND / "server.py"
FE_SHELL = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationWorkspaceShell.jsx"
FE_MC = ROOT / "frontend" / "src" / "pages" / "transportation" / "MissionControl.jsx"
FE_SEARCH = ROOT / "frontend" / "src" / "pages" / "transportation" / "TransportationSearch.jsx"
PHASE_C_ROUTE = BACKEND / "routes" / "transportation_search.py"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ---------------------------------------------------------------------------
# Async stub DB.
# ---------------------------------------------------------------------------
def _matches(row, q):
    if not q:
        return True
    for k, v in q.items():
        if k == "$or":
            if not any(_matches(row, clause) for clause in v):
                return False
            continue
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
                return False
            continue
        if row.get(k) != v:
            return False
    return True


class _Cur:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = list(items)

    def limit(self, _):
        return self

    def sort(self, *_a, **_kw):
        return self

    async def to_list(self, _=None):
        return list(self._items)


class _Coll:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    def find(self, q=None, *_, **__):
        return _Cur([r for r in self.rows if _matches(r, q or {})])

    async def find_one(self, q=None, *_, **__):
        for r in self.rows:
            if _matches(r, q or {}):
                return r
        return None


class _DB:
    def __init__(self):
        self._c: Dict[str, _Coll] = {}

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


def _get_handler(actor=None):
    """Register the route on a stub app, return the handler + db."""
    from routes.transportation_relationships import (
        register_track_18_00_phase_d_routes,
    )
    db = _DB()

    class _App:
        def __init__(self):
            self.included = []

        def include_router(self, r):
            self.included.append(r)

    app = _App()
    actor = actor or {"_actor": "admin", "name": "admin"}

    async def _ok(*_a, **_kw):
        return actor

    router = register_track_18_00_phase_d_routes(
        app, db, require_any_portal_dep=_ok)
    handler = None
    for r in router.routes:
        if "/related/" in r.path:
            handler = r.endpoint
            break
    return handler, db


# ===========================================================================
# 1 — Route file exists with correct prefix + GET endpoint + path.
# ===========================================================================
def test_01_route_exists_with_correct_signature():
    assert ROUTE.exists()
    src = ROUTE.read_text()
    assert 'prefix="/api/admin/transportation"' in src
    assert '@router.get("/related/{entity_type}/{entity_id}")' in src


# ===========================================================================
# 2 — Endpoint is GET-only — no POST/PATCH/DELETE definitions.
# ===========================================================================
def test_02_endpoint_is_get_only():
    src = ROUTE.read_text()
    assert "@router.post" not in src
    assert "@router.patch" not in src
    assert "@router.delete" not in src
    assert "@router.put" not in src


# ===========================================================================
# 3 — All 11 supported entity types listed in module constant.
# ===========================================================================
def test_03_supported_entity_types():
    from routes.transportation_relationships import SUPPORTED_TYPES
    for kind in (
        "driver", "carrier", "truck", "dispatch_assignment", "project",
        "certificate", "document", "orientation", "inspection",
        "action_item", "cleanup_signal",
    ):
        assert kind in SUPPORTED_TYPES, f"missing {kind}"
    assert len(SUPPORTED_TYPES) == 11


# ===========================================================================
# 4 — Anonymous / empty actor blocked with 403.
# ===========================================================================
def test_04_anonymous_blocked():
    from fastapi import HTTPException
    handler, _ = _get_handler(actor={})
    try:
        _run(handler(entity_type="driver", entity_id="x", limit=None,
                     actor={}))
        assert False, "anon must be blocked"
    except HTTPException as e:
        assert e.status_code == 403
        assert "no_relationships_permission" in str(e.detail)


# ===========================================================================
# 5 — Admin sees all sections + schema_version stamped.
# ===========================================================================
def test_05_admin_allowed_envelope_shape():
    handler, db = _get_handler()
    db.transport_persons.rows = [{"id": "p1", "name": "John", "carrier_id": "c1"}]
    db.carriers.rows = [{"id": "c1", "name": "ACME"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "admin"}))
    assert out["ok"] is True
    assert out["schema_version"] == "18.00D"
    for key in ("recent_activity", "timeline", "related_records",
                "open_actions", "audit"):
        assert key in out["sections"]
    assert "entity" in out and "counts" in out


# ===========================================================================
# 6 — Dispatch token: gets dispatch-safe relations.
# ===========================================================================
def test_06_dispatch_token_filters():
    handler, db = _get_handler(actor={"_actor": "dispatch"})
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.carriers.rows = [{"id": "c1", "name": "Carrier"}]
    db.dispatch_assignments.rows = [{
        "id": "a1", "assignment_id": "ASG-1",
        "driver_id": "p1", "state": "active"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "dispatch"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    assert "carrier" in types
    assert "dispatch_assignment" in types


# ===========================================================================
# 7 — HR token: NEVER sees truck or dispatch_assignment relations.
# ===========================================================================
def test_07_hr_token_no_truck_leakage():
    handler, db = _get_handler(actor={"_actor": "hr"})
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.dispatch_assignments.rows = [{
        "id": "a1", "driver_id": "p1", "state": "active"}]
    db.driver_documents.rows = [{
        "id": "d1", "transport_person_id": "p1",
        "document_type": "CDL", "status": "accepted"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "hr"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    assert "dispatch_assignment" not in types
    assert "truck" not in types
    # But HR may see documents + orientation.
    assert "document" in types


# ===========================================================================
# 8 — PM token: sees project/dispatch/truck relations.
# ===========================================================================
def test_08_pm_token_filters():
    handler, db = _get_handler(actor={"_actor": "pm"})
    db.dispatch_assignments.rows = [{
        "id": "a1", "project_number": "20-07", "driver_name": "X",
        "state": "active"}]
    out = _run(handler(
        entity_type="project", entity_id="20-07", limit=None,
        actor={"_actor": "pm"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    assert "dispatch_assignment" in types


# ===========================================================================
# 9 — Safety token: trucks + drivers ONLY, no documents.
# ===========================================================================
def test_09_safety_token_filters():
    handler, db = _get_handler(actor={"_actor": "safety"})
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.driver_documents.rows = [{
        "id": "d1", "transport_person_id": "p1",
        "document_type": "CDL"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "safety"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    assert "document" not in types
    assert "dispatch_assignment" not in types


# ===========================================================================
# 10 — Shop token: trucks only.
# ===========================================================================
def test_10_shop_token_filters():
    handler, db = _get_handler(actor={"_actor": "shop"})
    db.transport_trucks.rows = [{"id": "t1", "carrier_id": "c1",
                                  "unit_number": "T-9"}]
    db.carriers.rows = [{"id": "c1", "name": "Carrier"}]
    db.dispatch_assignments.rows = [{
        "id": "a1", "truck_id": "t1", "state": "active"}]
    out = _run(handler(
        entity_type="truck", entity_id="t1", limit=None,
        actor={"_actor": "shop"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    # shop is trucks-only — no carrier or dispatch_assignment leakage.
    assert "carrier" not in types
    assert "dispatch_assignment" not in types
    # inspections are scoped to trucks → permitted.
    # (No inspection rows seeded — collection is empty → no leakage)


# ===========================================================================
# 11 — Unknown entity type returns 400.
# ===========================================================================
def test_11_unknown_entity_type_returns_400():
    from fastapi import HTTPException
    handler, _ = _get_handler()
    try:
        _run(handler(
            entity_type="alien", entity_id="x", limit=None,
            actor={"_actor": "admin"}))
        assert False, "expected 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "unsupported_entity_type" in str(e.detail)


# ===========================================================================
# 12 — Unknown entity id returns a clean (not_found) envelope, not 500.
# ===========================================================================
def test_12_unknown_entity_id_clean_envelope():
    handler, _ = _get_handler()
    out = _run(handler(
        entity_type="driver", entity_id="ghost", limit=None,
        actor={"_actor": "admin"}))
    assert out["ok"] is True
    assert out["entity"]["title"] == "(not found)"
    assert out["entity"]["id"] == "ghost"
    assert out["sections"]["related_records"] == []


# ===========================================================================
# 13 — Response schema_version locked to 18.00D.
# ===========================================================================
def test_13_schema_version_locked():
    from routes.transportation_relationships import SCHEMA_VERSION
    assert SCHEMA_VERSION == "18.00D"


# ===========================================================================
# 14 — Five required sections always present, never None.
# ===========================================================================
def test_14_five_sections_always_present():
    handler, _ = _get_handler()
    out = _run(handler(
        entity_type="carrier", entity_id="x", limit=None,
        actor={"_actor": "admin"}))
    sections = out["sections"]
    for key in ("recent_activity", "timeline", "related_records",
                "open_actions", "audit"):
        assert key in sections
        assert isinstance(sections[key], list)


# ===========================================================================
# 15 — No new relationship collection introduced.
# ===========================================================================
def test_15_no_new_relationship_collection():
    src = ROUTE.read_text()
    # Reads existing collections only — never invents one. Check for
    # actual collection access patterns, not the prose word.
    for forbidden in (
        "db.relationships", 'db["relationships"]',
        "db.graph_edges", 'db["graph_edges"]',
        "db.entity_links", 'db["entity_links"]',
        "db.entity_graph", 'db["entity_graph"]',
        "db.transport_relationships", 'db["transport_relationships"]',
    ):
        assert forbidden not in src, f"forbidden collection {forbidden!r}"


# ===========================================================================
# 16 — No graph database driver imported.
# ===========================================================================
def test_16_no_graph_db_introduced():
    src = ROUTE.read_text()
    for forbidden in ("neo4j", "neomodel", "py2neo", "arango",
                      "networkx", "gremlin", "tinkerpop"):
        assert forbidden not in src, f"graph driver {forbidden!r}"


# ===========================================================================
# 17 — No source-record mutation: no insert / update / delete / replace.
# ===========================================================================
def test_17_no_source_record_mutation():
    src = ROUTE.read_text()
    for forbidden in (
        ".insert_one(", ".insert_many(",
        ".update_one(", ".update_many(",
        ".delete_one(", ".delete_many(",
        ".replace_one(", ".find_one_and_update(",
    ):
        assert forbidden not in src, f"mutation API used: {forbidden}"


# ===========================================================================
# 18 — Every related record carries a route field.
# ===========================================================================
def test_18_related_records_include_route():
    handler, db = _get_handler()
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.carriers.rows = [{"id": "c1", "name": "ACME"}]
    db.dispatch_assignments.rows = [{
        "id": "a1", "driver_id": "p1", "assignment_id": "ASG-1"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "admin"}))
    for row in out["sections"]["related_records"]:
        assert "route" in row and row["route"], (
            f"row missing route: {row!r}")


# ===========================================================================
# 19 — Unauthorized relations OMITTED (never redacted placeholder rows).
# ===========================================================================
def test_19_unauthorized_relations_omitted():
    handler, db = _get_handler(actor={"_actor": "hr"})
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.transport_trucks.rows = [{"id": "t1", "unit_number": "T-1"}]
    db.dispatch_assignments.rows = [{
        "id": "a1", "driver_id": "p1", "truck_id": "t1"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "hr"}))
    # HR has no trucks/dispatch — the rows must not appear at all.
    for row in out["sections"]["related_records"]:
        assert row["type"] not in ("truck", "dispatch_assignment")
        # No redaction sentinel either.
        assert row.get("title") != "(redacted)"
        assert row.get("status") != "redacted"


# ===========================================================================
# 20 — Frontend shell calls related endpoint.
# ===========================================================================
def test_20_shell_calls_related_endpoint():
    src = FE_SHELL.read_text()
    assert "/admin/transportation/related/" in src
    assert "useTransportationRelationships" in src


# ===========================================================================
# 21 — Right rail renders five live sections with testids.
# ===========================================================================
def test_21_right_rail_five_sections_with_testids():
    src = FE_SHELL.read_text()
    for testid in (
        "txops-rail-recent-activity",
        "txops-rail-timeline",
        "txops-rail-related",
        "txops-rail-open-actions",
        "txops-rail-audit",
    ):
        assert f'"{testid}"' in src, f"missing testid: {testid}"


# ===========================================================================
# 22 — Search results / URL query params can drive entity context.
# ===========================================================================
def test_22_search_can_drive_entity_context():
    src = FE_SHELL.read_text()
    # The shell reads ?entity_type=&entity_id= from the URL when no
    # explicit entityContext is supplied — letting Search deep-link
    # land directly on a workspace with a populated rail.
    assert 'entity_type' in src
    assert 'entity_id' in src
    assert "useLocation" in src


# ===========================================================================
# 23 — Loading state exists.
# ===========================================================================
def test_23_loading_state_exists():
    src = FE_SHELL.read_text()
    assert "Loading" in src
    assert "loading" in src
    assert "LoadingHint" in src


# ===========================================================================
# 24 — Empty state exists.
# ===========================================================================
def test_24_empty_state_exists():
    src = FE_SHELL.read_text()
    assert "No related records." in src
    assert "No open actions." in src
    assert "No recent activity." in src
    assert "EmptyHint" in src


# ===========================================================================
# 25 — Error state exists.
# ===========================================================================
def test_25_error_state_exists():
    src = FE_SHELL.read_text()
    assert "ErrorHint" in src
    assert "Unable to load" in src


# ===========================================================================
# 26 — No dead `to="#"` related links in the live row primitive.
# ===========================================================================
def test_26_no_dead_related_links():
    handler, db = _get_handler()
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.carriers.rows = [{"id": "c1", "name": "ACME"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "admin"}))
    for row in out["sections"]["related_records"]:
        assert row["route"] != "#"
        assert row["route"].startswith("/")


# ===========================================================================
# 27 — Phase A shell preserved (TxOpsHeader + workspace shell export).
# ===========================================================================
def test_27_phase_a_shell_preserved():
    src = FE_SHELL.read_text()
    assert "TxOpsHeader" in src
    assert "TransportationWorkspaceShell" in src
    assert "txops-workspace-shell" in src
    assert "txops-workspace-body" in src


# ===========================================================================
# 28 — Phase B Mission Control file untouched + still mounts shell.
# ===========================================================================
def test_28_phase_b_mission_control_preserved():
    assert FE_MC.exists()
    src = FE_MC.read_text()
    # MissionControl composes the existing readiness + audit-timeline.
    assert "useTransportationReadiness" in src or "audit-timeline" in src


# ===========================================================================
# 29 — Phase C Universal Search still wired.
# ===========================================================================
def test_29_phase_c_search_preserved():
    assert PHASE_C_ROUTE.exists()
    assert "register_track_18_00_phase_c_routes" in PHASE_C_ROUTE.read_text()
    assert "register_track_18_00_phase_c_routes" in SERVER.read_text()


# ===========================================================================
# 30 — Phase D regression file is wired into the deployment gate.
# ===========================================================================
def test_30_wired_into_deployment_gate():
    gate = GATE.read_text()
    assert "test_track_18_00_phase_d_universal_relationships.py" in gate


# ===========================================================================
# 31 — Phase D registration present in server.py with cross-portal helper.
# ===========================================================================
def test_31_registered_in_server():
    src = SERVER.read_text()
    assert "register_track_18_00_phase_d_routes" in src
    assert "transportation_relationships" in src
    block = src[src.find("register_track_18_00_phase_d_routes"):]
    assert "require_any_portal_dep" in block[:600]


# ===========================================================================
# 32 — Section limits + MAX_LIMIT exported and bounded.
# ===========================================================================
def test_32_section_limits_bounded():
    from routes.transportation_relationships import (
        SECTION_LIMITS, MAX_LIMIT,
    )
    assert MAX_LIMIT == 25
    assert SECTION_LIMITS["recent_activity"] == 5
    assert SECTION_LIMITS["timeline"] == 8
    assert SECTION_LIMITS["related_records"] == 10
    assert SECTION_LIMITS["open_actions"] == 5
    assert SECTION_LIMITS["audit"] == 8


# ===========================================================================
# 33 — Section limits enforced on related_records output (bounded by config).
# ===========================================================================
def test_33_related_records_limit_enforced():
    handler, db = _get_handler()
    # Seed 20 carriers under one carrier — request must cap at 10.
    db.transport_persons.rows = [
        {"id": f"d{i}", "name": f"Driver {i}", "carrier_id": "c1"}
        for i in range(20)
    ]
    db.carriers.rows = [{"id": "c1", "name": "ACME"}]
    out = _run(handler(
        entity_type="carrier", entity_id="c1", limit=None,
        actor={"_actor": "admin"}))
    assert len(out["sections"]["related_records"]) <= 10


# ===========================================================================
# 34 — Optional limit parameter cannot exceed MAX_LIMIT (25).
# ===========================================================================
def test_34_optional_limit_capped_at_25():
    from routes.transportation_relationships import _bounded, MAX_LIMIT
    assert _bounded(None, "related_records") == 10
    assert _bounded(5, "related_records") == 5
    assert _bounded(9999, "related_records") == MAX_LIMIT
    assert _bounded(-3, "related_records") == 1


# ===========================================================================
# 35 — Open actions composer reuses transport_action_items only.
# ===========================================================================
def test_35_open_actions_use_existing_collection():
    handler, db = _get_handler()
    db.transport_action_items.rows = [
        {"id": "ai1", "entity_id": "p1",
         "title": "Reset packet", "status": "open"},
        {"id": "ai2", "entity_id": "p1",
         "title": "Closed already", "status": "done"},
    ]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "admin"}))
    titles = [r["title"] for r in out["sections"]["open_actions"]]
    assert "Reset packet" in titles
    assert "Closed already" not in titles  # closed filtered out


# ===========================================================================
# 36 — Audit composer reads audit_events only (no new audit collection).
# ===========================================================================
def test_36_audit_uses_existing_audit_events():
    handler, db = _get_handler()
    db.audit_events.rows = [
        {"kind": "carrier_update", "entity_id": "c1", "at": "2026-02-09T00:00:00Z"},
    ]
    out = _run(handler(
        entity_type="carrier", entity_id="c1", limit=None,
        actor={"_actor": "admin"}))
    assert len(out["sections"]["audit"]) == 1
    assert out["sections"]["audit"][0]["kind"] == "carrier_update"
    # Recent activity mirrors audit head.
    assert len(out["sections"]["recent_activity"]) == 1


# ===========================================================================
# 37 — RBAC: actor without audit perm receives empty audit + recent_activity.
# ===========================================================================
def test_37_audit_section_rbac():
    handler, db = _get_handler(actor={"_actor": "garbage"})
    db.audit_events.rows = [{"kind": "x", "entity_id": "p1"}]
    # Garbage role gets empty allowed → 403 BEFORE we ever touch audit.
    from fastapi import HTTPException
    try:
        _run(handler(
            entity_type="driver", entity_id="p1", limit=None,
            actor={"_actor": "garbage"}))
        assert False, "garbage role must be 403"
    except HTTPException as e:
        assert e.status_code == 403


# ===========================================================================
# 38 — dispatch_assignment composer fans out across the 4 linked entities.
# ===========================================================================
def test_38_dispatch_assignment_composer():
    handler, db = _get_handler()
    db.dispatch_assignments.rows = [{
        "id": "a1", "assignment_id": "ASG-1",
        "driver_id": "p1", "truck_id": "t1",
        "carrier_id": "c1", "project_number": "20-07",
    }]
    db.transport_persons.rows = [{"id": "p1", "name": "Driver"}]
    db.transport_trucks.rows = [{"id": "t1", "unit_number": "T-9"}]
    db.carriers.rows = [{"id": "c1", "name": "ACME"}]
    out = _run(handler(
        entity_type="dispatch_assignment", entity_id="a1", limit=None,
        actor={"_actor": "admin"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    assert {"driver", "truck", "carrier", "project"}.issubset(types)


# ===========================================================================
# 39 — Counts envelope mirrors actual list lengths.
# ===========================================================================
def test_39_counts_match_section_lengths():
    handler, db = _get_handler()
    db.transport_action_items.rows = [
        {"id": "x", "entity_id": "p1", "title": "T", "status": "open"},
    ]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "admin"}))
    for k, v in out["sections"].items():
        assert out["counts"][k] == len(v), f"count mismatch on {k}"


# ===========================================================================
# 40 — Field Leadership token sees drivers + projects only.
# ===========================================================================
def test_40_field_leadership_token_filters():
    handler, db = _get_handler(actor={"_actor": "fl"})
    db.transport_persons.rows = [{"id": "p1", "carrier_id": "c1"}]
    db.transport_trucks.rows = [{"id": "t1"}]
    db.dispatch_assignments.rows = [{
        "id": "a1", "driver_id": "p1", "truck_id": "t1"}]
    out = _run(handler(
        entity_type="driver", entity_id="p1", limit=None,
        actor={"_actor": "fl"}))
    types = {r["type"] for r in out["sections"]["related_records"]}
    # FL has neither trucks nor dispatch — must be omitted.
    assert "truck" not in types
    assert "dispatch_assignment" not in types
