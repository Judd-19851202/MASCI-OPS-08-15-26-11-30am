"""
test_iter175_phase_k3_role_templates.py — Phase K3 verification.

Pure tests for the role-template system. K3 is **non-enforcing** — no
route reads these templates yet. We verify:

  1. Every seeded template validates against KNOWN_ACTIONS catalog
  2. Inheritance resolution flattens correctly
  3. Inheritance cycles are detected & their templates skipped at seed
  4. Self-inheritance rejected at validation time
  5. Unknown action references rejected at validation time
  6. Missing parents tolerated (template still seeded; resolver skips)
  7. Seed is idempotent (re-run does not create duplicates)
  8. Built-in (system=True) seed re-run refreshes definitions
  9. Custom (system=False) rows are NEVER touched by seed
 10. Field Leadership hierarchy: Foreman ⊆ Superintendent ⊆ Senior Sup
 11. PM hierarchy: PM Read Only ⊆ Coordinator ⊆ Engineer ⊆ Assistant ⊆ Manager
 12. Shop Manager unions Mechanic + Service Writer + Parts Coordinator
 13. System Admin template has empty actions (gates via is_super_admin)
 14. Every portal has at least one seeded template
 15. Indexes created
 16. Resolver returns empty for unknown template_id
 17. Resolver fails closed on malformed in-memory inputs
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, "/app/backend")


def _load_env(p: str) -> None:
    txt = Path(p).read_text()
    for line in txt.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env("/app/backend/.env")

from lib.role_templates import (  # noqa: E402
    SEED_TEMPLATES,
    TemplateValidationError,
    _detect_cycles,
    _resolve_in_memory,
    _validate_one,
    ensure_indexes,
    get_template,
    list_templates,
    resolve_actions,
    seed_role_templates,
)
from lib.rbac import KNOWN_ACTIONS, PORTALS  # noqa: E402


def _fresh_db():
    name = f"masci_test_iter175_{uuid.uuid4().hex[:10]}"
    return name


def _run(coro_factory):
    name = _fresh_db()

    async def body():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[name]
        try:
            return await coro_factory(db)
        finally:
            await client.drop_database(name)
            client.close()

    return asyncio.run(body())


# ────────────────────────────────────────────────────────────────
# 1. Catalog alignment
# ────────────────────────────────────────────────────────────────

def test_every_seed_action_is_in_known_actions():
    """Every action referenced by every seed template must already
    exist in rbac.KNOWN_ACTIONS. This keeps K2 + K3 in lock-step."""
    seen = set()
    for t in SEED_TEMPLATES:
        for a in t.get("actions") or []:
            seen.add((t["id"], a))
            assert a in KNOWN_ACTIONS, f"{t['id']} references unknown action {a}"
    assert len(seen) > 0


def test_every_portal_has_at_least_one_template():
    portals_with_seed = {t["portal"] for t in SEED_TEMPLATES}
    for p in PORTALS:
        assert p in portals_with_seed, f"portal {p} has no seed template"


def test_every_template_id_starts_with_rt_prefix():
    for t in SEED_TEMPLATES:
        assert t["id"].startswith("rt-"), f"bad id: {t['id']}"


def test_template_ids_are_unique():
    ids = [t["id"] for t in SEED_TEMPLATES]
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"


# ────────────────────────────────────────────────────────────────
# 2. Per-template validation
# ────────────────────────────────────────────────────────────────

def test_validate_rejects_unknown_portal():
    bad = {"id": "rt-bad-portal", "portal": "nope", "name": "Bad"}
    try:
        _validate_one(bad)
        assert False, "should have raised"
    except TemplateValidationError as e:
        assert "unknown portal" in str(e)


def test_validate_rejects_unknown_action():
    bad = {"id": "rt-bad-action", "portal": "shop", "name": "Bad",
           "actions": ["shop.work_orders.view", "fake.module.verb"]}
    try:
        _validate_one(bad)
        assert False, "should have raised"
    except TemplateValidationError as e:
        assert "unknown action" in str(e)


def test_validate_rejects_self_inheritance():
    bad = {"id": "rt-self", "portal": "shop", "name": "Self",
           "inherits_from": ["rt-self"]}
    try:
        _validate_one(bad)
        assert False, "should have raised"
    except TemplateValidationError as e:
        assert "self-inheritance" in str(e)


def test_validate_rejects_missing_id():
    bad = {"portal": "shop", "name": "No ID"}
    try:
        _validate_one(bad)
        assert False
    except TemplateValidationError:
        pass


def test_validate_rejects_bad_id_prefix():
    bad = {"id": "no-prefix", "portal": "shop", "name": "Bad"}
    try:
        _validate_one(bad)
        assert False
    except TemplateValidationError:
        pass


def test_validate_rejects_non_string_action():
    bad = {"id": "rt-bad", "portal": "shop", "name": "Bad",
           "actions": [None, 42]}
    try:
        _validate_one(bad)
        assert False
    except TemplateValidationError:
        pass


def test_validate_rejects_non_list_actions():
    bad = {"id": "rt-bad", "portal": "shop", "name": "Bad", "actions": "not a list"}
    try:
        _validate_one(bad)
        assert False
    except TemplateValidationError:
        pass


def test_validate_accepts_minimal_template():
    good = {"id": "rt-good", "portal": "shop", "name": "Good"}
    _validate_one(good)  # must not raise


def test_validate_accepts_full_template():
    good = {
        "id": "rt-good-full",
        "portal": "pm",
        "name": "Good Full",
        "description": "x",
        "inherits_from": [],
        "actions": ["pm.project.view"],
        "record_scope": {"pm.project": "assigned"},
        "hierarchy_level": 3,
    }
    _validate_one(good)


# ────────────────────────────────────────────────────────────────
# 3. Cycle detection
# ────────────────────────────────────────────────────────────────

def test_detect_no_cycles_in_seed():
    by_id = {t["id"]: t for t in SEED_TEMPLATES}
    assert _detect_cycles(by_id) == []


def test_detect_simple_two_node_cycle():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": ["rt-b"]}
    b = {"id": "rt-b", "portal": "pm", "name": "B", "inherits_from": ["rt-a"]}
    cyclic = _detect_cycles({"rt-a": a, "rt-b": b})
    assert set(cyclic) == {"rt-a", "rt-b"}


def test_detect_three_node_cycle():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": ["rt-b"]}
    b = {"id": "rt-b", "portal": "pm", "name": "B", "inherits_from": ["rt-c"]}
    c = {"id": "rt-c", "portal": "pm", "name": "C", "inherits_from": ["rt-a"]}
    cyclic = _detect_cycles({"rt-a": a, "rt-b": b, "rt-c": c})
    assert set(cyclic) == {"rt-a", "rt-b", "rt-c"}


def test_detect_ignores_dag():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": []}
    b = {"id": "rt-b", "portal": "pm", "name": "B", "inherits_from": ["rt-a"]}
    c = {"id": "rt-c", "portal": "pm", "name": "C", "inherits_from": ["rt-a", "rt-b"]}
    assert _detect_cycles({"rt-a": a, "rt-b": b, "rt-c": c}) == []


def test_detect_missing_parent_does_not_cycle():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": ["rt-nonexistent"]}
    assert _detect_cycles({"rt-a": a}) == []


# ────────────────────────────────────────────────────────────────
# 4. In-memory resolver
# ────────────────────────────────────────────────────────────────

def test_resolver_flattens_simple_inheritance():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": [],
         "actions": ["pm.project.view"]}
    b = {"id": "rt-b", "portal": "pm", "name": "B", "inherits_from": ["rt-a"],
         "actions": ["pm.po_requests.view"]}
    out = _resolve_in_memory("rt-b", {"rt-a": a, "rt-b": b})
    assert out == {"pm.project.view", "pm.po_requests.view"}


def test_resolver_handles_diamond_inheritance():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": [],
         "actions": ["pm.project.view"]}
    b = {"id": "rt-b", "portal": "pm", "name": "B", "inherits_from": ["rt-a"],
         "actions": ["pm.po_requests.view"]}
    c = {"id": "rt-c", "portal": "pm", "name": "C", "inherits_from": ["rt-a"],
         "actions": ["pm.daily_reports.view"]}
    d = {"id": "rt-d", "portal": "pm", "name": "D", "inherits_from": ["rt-b", "rt-c"],
         "actions": ["pm.incidents.view"]}
    out = _resolve_in_memory("rt-d", {"rt-a": a, "rt-b": b, "rt-c": c, "rt-d": d})
    assert out == {"pm.project.view", "pm.po_requests.view",
                   "pm.daily_reports.view", "pm.incidents.view"}


def test_resolver_skips_cyclic_templates():
    a = {"id": "rt-a", "portal": "pm", "name": "A", "inherits_from": ["rt-b"],
         "actions": ["pm.project.view"]}
    b = {"id": "rt-b", "portal": "pm", "name": "B", "inherits_from": ["rt-a"],
         "actions": ["pm.po_requests.view"]}
    # Cyclic templates resolve to empty (fail closed).
    assert _resolve_in_memory("rt-a", {"rt-a": a, "rt-b": b}) == set()


def test_resolver_unknown_id_returns_empty():
    assert _resolve_in_memory("rt-nonexistent", {}) == set()
    assert _resolve_in_memory("", {}) == set()


def test_resolver_filters_unknown_actions():
    # Even if a DB row sneaks in an unknown action, resolver drops it.
    a = {"id": "rt-bad", "portal": "pm", "name": "Bad", "inherits_from": [],
         "actions": ["pm.project.view", "fake.module.verb"]}
    out = _resolve_in_memory("rt-bad", {"rt-bad": a})
    assert out == {"pm.project.view"}
    assert "fake.module.verb" not in out


# ────────────────────────────────────────────────────────────────
# 5. Specific hierarchies (the real product semantics)
# ────────────────────────────────────────────────────────────────

def _seed_dict():
    """Build the SEED_TEMPLATES indexed by id for direct in-memory
    resolution (no DB needed)."""
    return {t["id"]: t for t in SEED_TEMPLATES}


def test_leadership_hierarchy_is_a_chain():
    seed = _seed_dict()
    foreman = _resolve_in_memory("rt-leadership-foreman", seed)
    sup = _resolve_in_memory("rt-leadership-superintendent", seed)
    senior = _resolve_in_memory("rt-leadership-senior-superintendent", seed)
    assert foreman <= sup
    assert sup <= senior
    assert len(foreman) > 0
    # leadership-specific actions present at the lowest tier
    assert "leadership.records.create" in foreman
    assert "leadership.po_requests.create" in foreman


def test_pm_chain_inheritance():
    seed = _seed_dict()
    ro = _resolve_in_memory("rt-pm-readonly", seed)
    coord = _resolve_in_memory("rt-pm-coordinator", seed)
    eng = _resolve_in_memory("rt-pm-engineer", seed)
    asst = _resolve_in_memory("rt-pm-assistant", seed)
    mgr = _resolve_in_memory("rt-pm-manager", seed)
    assert ro <= coord <= eng <= asst <= mgr
    assert "pm.po_requests.approve" in mgr
    assert "pm.po_requests.approve" not in ro
    assert "pm.project.view" in ro      # foundation
    assert "pm.po_requests.create" in coord
    assert "pm.project.edit" in eng
    assert "pm.po_requests.upload_receipt" in asst


def test_hr_inheritance_diamond():
    seed = _seed_dict()
    ro = _resolve_in_memory("rt-hr-readonly", seed)
    payroll = _resolve_in_memory("rt-hr-payroll", seed)
    coord = _resolve_in_memory("rt-hr-coordinator", seed)
    mgr = _resolve_in_memory("rt-hr-manager", seed)
    # Manager inherits from both Coordinator AND Payroll.
    assert ro <= coord <= mgr
    assert ro <= payroll <= mgr
    # Manager-only actions
    assert "hr.po_requests.approve" in mgr
    assert "pm.po_requests.approve" in mgr   # cross-portal grant
    assert "hr.po_requests.approve" not in coord
    # Coordinator has training/document/employee management
    assert "hr.training.assign" in coord
    assert "hr.employee.edit" in coord
    # Payroll Specialist sees payroll
    assert "hr.payroll.view" in payroll
    assert "hr.payroll.view" in mgr


def test_shop_manager_unions_subordinates():
    seed = _seed_dict()
    mechanic = _resolve_in_memory("rt-shop-mechanic", seed)
    sw = _resolve_in_memory("rt-shop-service-writer", seed)
    parts = _resolve_in_memory("rt-shop-parts-coordinator", seed)
    mgr = _resolve_in_memory("rt-shop-manager", seed)
    assert mechanic <= mgr
    assert sw <= mgr
    assert parts <= mgr
    # Manager-only
    assert "shop.users.manage" in mgr
    assert "shop.users.manage" not in mechanic
    # Cross-portal grant
    assert "dispatch.equipment.view" in mgr


def test_safety_director_includes_coordinator_and_readonly():
    seed = _seed_dict()
    ro = _resolve_in_memory("rt-safety-readonly", seed)
    coord = _resolve_in_memory("rt-safety-coordinator", seed)
    director = _resolve_in_memory("rt-safety-director", seed)
    assert ro <= coord <= director
    assert "safety.corrective_actions.close" in director
    assert "safety.corrective_actions.close" not in coord
    assert "safety.users.manage" in director


def test_dispatch_chain_inheritance():
    seed = _seed_dict()
    ro = _resolve_in_memory("rt-dispatch-readonly", seed)
    disp = _resolve_in_memory("rt-dispatch-dispatcher", seed)
    fc = _resolve_in_memory("rt-dispatch-fleet-coordinator", seed)
    mgr = _resolve_in_memory("rt-dispatch-manager", seed)
    assert ro <= disp <= fc <= mgr
    assert "dispatch.users.manage" in mgr
    assert "dispatch.equipment.transfer" in fc
    assert "dispatch.equipment.transfer" not in disp


def test_system_admin_template_has_empty_actions():
    """System Admin gates via is_super_admin() at the rbac layer.
    Its template intentionally contains no actions."""
    sa = next(t for t in SEED_TEMPLATES if t["id"] == "rt-admin-system")
    assert sa["actions"] == []


def test_executive_viewer_is_strict_subset_of_system_admin_via_rbac():
    """Executive Viewer = read-only audits/integrations/signals + platform."""
    seed = _seed_dict()
    ev = _resolve_in_memory("rt-admin-executive-viewer", seed)
    assert "admin.audit.view" in ev
    assert "admin.users.manage" not in ev
    assert "platform.operations_center.view" in ev


def test_other_templates_have_empty_actions():
    """The 'Other' templates are escape-hatches for users who don't
    fit any predefined role. They start with zero actions and rely on
    explicit overrides."""
    for other_id in (
        "rt-hr-other", "rt-pm-other", "rt-shop-other",
        "rt-safety-other", "rt-dispatch-other",
    ):
        seed = _seed_dict()
        assert seed[other_id]["actions"] == []
        assert _resolve_in_memory(other_id, seed) == set()


# ────────────────────────────────────────────────────────────────
# 6. DB-backed seed + idempotency
# ────────────────────────────────────────────────────────────────

def test_seed_creates_all_templates():
    async def body(db):
        stats = await seed_role_templates(db)
        count = await db.role_templates.count_documents({})
        return stats, count

    stats, count = _run(body)
    assert stats["inserted"] == len(SEED_TEMPLATES)
    assert stats["updated"] == 0
    assert stats["cyclic_skipped"] == 0
    assert count == len(SEED_TEMPLATES)


def test_seed_is_idempotent():
    async def body(db):
        s1 = await seed_role_templates(db)
        s2 = await seed_role_templates(db)
        s3 = await seed_role_templates(db)
        count = await db.role_templates.count_documents({})
        return s1, s2, s3, count

    s1, s2, s3, count = _run(body)
    assert s1["inserted"] == len(SEED_TEMPLATES)
    assert s2["inserted"] == 0
    assert s2["updated"] == len(SEED_TEMPLATES)
    assert s3["inserted"] == 0
    assert s3["updated"] == len(SEED_TEMPLATES)
    assert count == len(SEED_TEMPLATES)


def test_seed_does_not_touch_custom_rows():
    """A non-system template (e.g. an admin-defined custom role) must
    survive the seed pass unchanged."""
    custom = {
        "id": "rt-custom-special",
        "portal": "hr",
        "name": "Special Manager",
        "description": "Custom role",
        "inherits_from": [],
        "actions": ["hr.employee.view"],
        "record_scope": {},
        "hierarchy_level": 4,
        "system": False,    # ← important
        "active": True,
        "created_by": "tester",
        "updated_by": "tester",
        "created_at": "2026-05-16T00:00:00Z",
        "updated_at": "2026-05-16T00:00:00Z",
        "schema_version": 1,
    }

    async def body(db):
        await db.role_templates.insert_one(dict(custom))
        await seed_role_templates(db)
        return await db.role_templates.find_one({"id": "rt-custom-special"}, {"_id": 0})

    row = _run(body)
    assert row is not None
    assert row["system"] is False
    assert row["name"] == "Special Manager"
    assert row["actions"] == ["hr.employee.view"]
    assert row["created_by"] == "tester"


def test_seed_refreshes_system_rows_on_update():
    """If a system row exists with stale fields, the seed should refresh
    its name/description/actions/inherits_from/record_scope, while
    preserving created_at / created_by."""
    async def body(db):
        await seed_role_templates(db)
        # Corrupt one system row.
        await db.role_templates.update_one(
            {"id": "rt-pm-readonly"},
            {"$set": {"name": "WRONG NAME", "actions": ["pm.project.view"]}},
        )
        await seed_role_templates(db)
        return await db.role_templates.find_one({"id": "rt-pm-readonly"}, {"_id": 0})

    row = _run(body)
    assert row["name"] == "PM Read Only"
    # Original actions list restored
    assert "pm.po_requests.view" in row["actions"]


def test_indexes_created():
    async def body(db):
        await ensure_indexes(db)
        return await db.role_templates.index_information()

    info = _run(body)
    assert "id_unique" in info
    assert "portal_idx" in info
    assert "active_idx" in info


# ────────────────────────────────────────────────────────────────
# 7. Public read API
# ────────────────────────────────────────────────────────────────

def test_get_template_returns_seeded_row():
    async def body(db):
        await seed_role_templates(db)
        return await get_template(db, "rt-shop-mechanic")

    row = _run(body)
    assert row is not None
    assert row["name"] == "Mechanic"
    assert row["portal"] == "shop"
    assert "_id" not in row


def test_get_template_missing_returns_none():
    async def body(db):
        await seed_role_templates(db)
        return await get_template(db, "rt-nonexistent")

    assert _run(body) is None


def test_list_templates_filters_by_portal():
    async def body(db):
        await seed_role_templates(db)
        return await list_templates(db, portal="leadership")

    rows = _run(body)
    ids = sorted(r["id"] for r in rows)
    assert ids == [
        "rt-leadership-foreman",
        "rt-leadership-senior-superintendent",
        "rt-leadership-superintendent",
    ]


def test_list_templates_all_portals_when_unfiltered():
    async def body(db):
        await seed_role_templates(db)
        return await list_templates(db)

    rows = _run(body)
    assert len(rows) == len(SEED_TEMPLATES)
    portals_seen = {r["portal"] for r in rows}
    assert portals_seen == {"admin", "hr", "pm", "shop", "safety", "dispatch", "leadership"}


def test_resolve_actions_db_backed():
    async def body(db):
        await seed_role_templates(db)
        return await resolve_actions(db, "rt-pm-manager")

    actions = _run(body)
    # PM Manager union should include the full chain.
    assert "pm.project.view" in actions          # from PM Read Only
    assert "pm.po_requests.create" in actions    # from PM Coordinator
    assert "pm.project.edit" in actions          # from Project Engineer
    assert "pm.po_requests.upload_receipt" in actions  # from Assistant PM
    assert "pm.po_requests.approve" in actions   # own
    assert "safety.incidents.view" in actions    # own (cross-portal grant)
    assert "safety.corrective_actions.close" in actions


def test_resolve_actions_unknown_template_empty():
    async def body(db):
        await seed_role_templates(db)
        return await resolve_actions(db, "rt-nonexistent")

    assert _run(body) == set()
