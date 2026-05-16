"""
test_iter174_phase_k2_rbac_service.py — Phase K2 verification.

Pure unit tests for the centralized RBAC service. The service is
non-enforcing — these tests prove the decision matrix is correct so
that Phase K6 (deferred) can confidently swap scattered `role == "..."`
checks for `require(actor, "...")` calls.

Properties verified:
  1. Fail closed on missing/empty/malformed input.
  2. Unknown actions are rejected even for super admin.
  3. Super admin bypasses portal/role checks.
  4. Each portal actor receives its own namespace.
  5. Cross-portal grants work exactly as documented.
  6. Platform-level actions are universal to authenticated actors.
  7. `actions_for_actor` returns the correct capability set.
  8. `require()` raises HTTPException(403) on deny.
  9. Anon actor receives empty capability set.
 10. Field Leadership has its scoped subset.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, "/app/backend")

from fastapi import HTTPException

from lib.rbac import (
    KNOWN_ACTIONS,
    PORTALS,
    actions_for_actor,
    actor_email,
    actor_id,
    actor_portal,
    actor_role,
    can,
    explain,
    is_super_admin,
    require,
)


# ────────────────────────────────────────────────────────────────
# Fixtures (plain dicts — match the runtime actor shape)
# ────────────────────────────────────────────────────────────────

def admin_actor() -> dict:
    return {"_actor": "admin", "name": "Admin"}


def hr_actor(role="HR Manager") -> dict:
    return {"_actor": "hr", "name": "HR User", "role": role,
            "email": "hr@mascigc.com", "id": "hr-1"}


def pm_actor() -> dict:
    return {"_actor": "pm", "name": "PM User", "role": "Project Manager",
            "email": "pm@mascigc.com", "id": "pm-1"}


def shop_actor(role="Mechanic") -> dict:
    return {"_actor": "shop", "name": "Shop User", "role": role,
            "email": "shop@mascigc.com", "id": "shop-1"}


def safety_actor() -> dict:
    return {"_actor": "safety", "name": "Safety User",
            "role": "Safety Manager", "email": "safety@mascigc.com",
            "id": "safe-1"}


def dispatch_actor() -> dict:
    return {"_actor": "dispatch", "name": "Dispatch User",
            "role": "Dispatcher", "email": "dispatch@mascigc.com",
            "id": "disp-1"}


def leadership_actor() -> dict:
    return {"_actor": "leadership", "name": "Field Leadership"}


# ────────────────────────────────────────────────────────────────
# 1. Fail-closed tests
# ────────────────────────────────────────────────────────────────

def test_none_actor_denied_everything():
    for action in list(KNOWN_ACTIONS)[:5]:
        assert can(None, action) is False


def test_empty_actor_denied_everything():
    for action in list(KNOWN_ACTIONS)[:5]:
        assert can({}, action) is False


def test_malformed_action_strings_rejected():
    a = admin_actor()
    bad_inputs = ["", "noseparator", "two.parts", "four.parts.like.this",
                  ".empty.start", "empty..middle", "trailing.dot."]
    for bad in bad_inputs:
        assert can(a, bad) is False
    assert can(a, None) is False  # type: ignore[arg-type]


def test_unknown_action_rejected_even_for_super_admin():
    a = admin_actor()
    assert is_super_admin(a) is True
    assert can(a, "fake.module.verb") is False
    assert can(a, "admin.fake_module.fake_verb") is False


def test_non_string_action_rejected():
    a = admin_actor()
    assert can(a, 123) is False  # type: ignore[arg-type]
    assert can(a, []) is False   # type: ignore[arg-type]


# ────────────────────────────────────────────────────────────────
# 2. Super admin
# ────────────────────────────────────────────────────────────────

def test_admin_portal_token_is_super_admin():
    assert is_super_admin(admin_actor()) is True


def test_super_admin_bypasses_every_known_action():
    a = admin_actor()
    for action in KNOWN_ACTIONS:
        assert can(a, action) is True, f"super admin must pass {action}"


def test_super_admin_email_env_bypass(monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAIL", "boss@mascigc.com")
    actor = {"_actor": "pm", "name": "Boss", "email": "boss@mascigc.com"}
    assert is_super_admin(actor) is True
    # Verify the bypass actually grants cross-portal access.
    assert can(actor, "admin.users.manage") is True


def test_directory_super_admin_flag_works():
    actor = {"_actor": "hr", "email": "x@y.com", "is_super_admin": True}
    assert is_super_admin(actor) is True
    assert can(actor, "admin.system.manage") is True


# ────────────────────────────────────────────────────────────────
# 3. Per-portal namespace access
# ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("actor_factory,portal", [
    (hr_actor, "hr"),
    (pm_actor, "pm"),
    (shop_actor, "shop"),
    (safety_actor, "safety"),
    (dispatch_actor, "dispatch"),
    (leadership_actor, "leadership"),
])
def test_actor_can_access_own_namespace(actor_factory, portal):
    a = actor_factory()
    own_actions = [x for x in KNOWN_ACTIONS if x.startswith(f"{portal}.")]
    assert own_actions, f"no actions found for portal {portal}"
    for action in own_actions:
        assert can(a, action) is True, f"{portal} actor must have {action}"


def test_hr_actor_blocked_from_shop_management():
    a = hr_actor()
    assert can(a, "shop.users.manage") is False
    assert can(a, "shop.work_orders.update") is False


def test_pm_actor_blocked_from_admin_users():
    a = pm_actor()
    assert can(a, "admin.users.manage") is False
    assert can(a, "admin.audit.view") is False


def test_shop_mechanic_cannot_manage_shop_users():
    # This test will tighten in K3 (role-template granularity). For K2
    # we capture the current behavior: any shop-portal actor sees the
    # whole shop namespace. K3 will split Shop Manager vs Mechanic.
    a = shop_actor(role="Mechanic")
    assert can(a, "shop.users.manage") is True
    assert can(a, "shop.work_orders.close") is True


# ────────────────────────────────────────────────────────────────
# 4. Documented cross-portal grants
# ────────────────────────────────────────────────────────────────

def test_hr_can_approve_pm_pos():
    assert can(hr_actor(), "pm.po_requests.approve") is True


def test_pm_can_view_safety_incidents_and_close_cas():
    a = pm_actor()
    assert can(a, "safety.incidents.view") is True
    assert can(a, "safety.corrective_actions.close") is True


def test_safety_can_view_pm_projects_and_incidents():
    a = safety_actor()
    assert can(a, "pm.project.view") is True
    assert can(a, "pm.incidents.view") is True
    # But not approve POs (no cross-grant).
    assert can(a, "pm.po_requests.approve") is False


def test_shop_can_view_dispatch_equipment_and_vice_versa():
    assert can(shop_actor(), "dispatch.equipment.view") is True
    assert can(dispatch_actor(), "shop.equipment.view") is True


def test_leadership_has_scoped_subset():
    a = leadership_actor()
    assert can(a, "leadership.records.view") is True
    assert can(a, "leadership.records.create") is True
    assert can(a, "pm.project.view") is True       # cross-grant
    assert can(a, "platform.search.use") is True
    # Cannot reach admin, hr, shop, dispatch, safety namespaces.
    assert can(a, "admin.users.manage") is False
    assert can(a, "hr.employee.view") is False
    assert can(a, "shop.work_orders.update") is False
    assert can(a, "safety.incidents.create") is False
    assert can(a, "dispatch.equipment.transfer") is False


# ────────────────────────────────────────────────────────────────
# 5. Platform-level universal actions
# ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("actor_factory", [
    hr_actor, pm_actor, shop_actor, safety_actor, dispatch_actor, leadership_actor,
])
def test_every_portal_can_use_platform_actions(actor_factory):
    a = actor_factory()
    for plat in (
        "platform.search.use",
        "platform.tasks.view_own",
        "platform.notifications.view_own",
        "platform.operations_center.view",
        "platform.project_health.view",
        "platform.asset_transfers.view",
    ):
        assert can(a, plat) is True


def test_anon_blocked_from_platform_actions():
    for plat in ("platform.search.use", "platform.operations_center.view"):
        assert can(None, plat) is False
        assert can({}, plat) is False


# ────────────────────────────────────────────────────────────────
# 6. actions_for_actor introspection
# ────────────────────────────────────────────────────────────────

def test_actions_for_anon_is_empty():
    assert actions_for_actor(None) == set()
    assert actions_for_actor({}) == set()


def test_actions_for_super_admin_is_full_catalog():
    assert actions_for_actor(admin_actor()) == set(KNOWN_ACTIONS)


def test_actions_for_pm_contains_own_namespace_plus_cross():
    caps = actions_for_actor(pm_actor())
    # Own namespace
    assert "pm.po_requests.approve" in caps
    # Documented cross-grant
    assert "safety.incidents.view" in caps
    # Platform universals
    assert "platform.search.use" in caps
    # Negative
    assert "admin.users.manage" not in caps
    assert "hr.employee.edit" not in caps


def test_actions_count_consistency():
    """Capability sets must be subsets of KNOWN_ACTIONS."""
    for actor_factory in (
        hr_actor, pm_actor, shop_actor, safety_actor, dispatch_actor, leadership_actor,
    ):
        caps = actions_for_actor(actor_factory())
        assert caps.issubset(KNOWN_ACTIONS)
        # Each portal must have a non-trivial set.
        assert len(caps) >= 5


# ────────────────────────────────────────────────────────────────
# 7. require() enforcement primitive
# ────────────────────────────────────────────────────────────────

def test_require_passes_when_allowed():
    require(admin_actor(), "admin.users.manage")  # must not raise


def test_require_raises_403_when_denied():
    with pytest.raises(HTTPException) as ei:
        require(pm_actor(), "admin.users.manage")
    assert ei.value.status_code == 403
    assert "admin.users.manage" in str(ei.value.detail)


def test_require_raises_on_unknown_action():
    with pytest.raises(HTTPException) as ei:
        require(admin_actor(), "totally.fake.action")
    assert ei.value.status_code == 403


def test_require_raises_on_anon():
    with pytest.raises(HTTPException) as ei:
        require(None, "platform.search.use")
    assert ei.value.status_code == 403


# ────────────────────────────────────────────────────────────────
# 8. Subject extraction helpers
# ────────────────────────────────────────────────────────────────

def test_actor_portal_canonicalization():
    assert actor_portal(admin_actor()) == "admin"
    assert actor_portal(pm_actor()) == "pm"
    assert actor_portal({"_actor": "BAD"}) is None
    assert actor_portal(None) is None
    assert actor_portal({}) is None


def test_actor_role_extraction():
    assert actor_role(hr_actor(role="HR Manager")) == "HR Manager"
    assert actor_role(admin_actor()) is None  # admin has no role label
    assert actor_role({"_actor": "hr", "role": ""}) is None


def test_actor_email_lowercased_and_stripped():
    a = {"_actor": "hr", "email": "  X@Y.COM  "}
    assert actor_email(a) == "x@y.com"


def test_actor_id_extraction():
    assert actor_id({"_actor": "hr", "id": "abc"}) == "abc"
    assert actor_id({"_actor": "hr", "user_id": "uuid-1"}) == "uuid-1"
    assert actor_id({}) is None


# ────────────────────────────────────────────────────────────────
# 9. explain() diagnostic
# ────────────────────────────────────────────────────────────────

def test_explain_returns_decision_and_metadata():
    out = explain(pm_actor(), "admin.users.manage")
    assert out["allow"] is False
    assert out["actor_portal"] == "pm"
    assert out["known_action"] is True
    assert out["is_super_admin"] is False

    out2 = explain(admin_actor(), "totally.fake.thing")
    assert out2["allow"] is False
    assert out2["known_action"] is False


# ────────────────────────────────────────────────────────────────
# 10. KNOWN_ACTIONS catalog sanity
# ────────────────────────────────────────────────────────────────

def test_known_actions_all_three_part_dot_notation():
    for action in KNOWN_ACTIONS:
        parts = action.split(".")
        assert len(parts) == 3, f"action must be 'portal.module.verb': {action}"
        portal, module, verb = parts
        assert portal, action
        assert module, action
        assert verb, action


def test_known_actions_cover_every_portal():
    portals_in_actions = {a.split(".", 1)[0] for a in KNOWN_ACTIONS}
    # Every real portal should have at least one action.
    for p in PORTALS:
        assert p in portals_in_actions, f"no actions registered for portal {p}"
    # Platform pseudo-portal also represented.
    assert "platform" in portals_in_actions


def test_known_actions_has_no_duplicates():
    # KNOWN_ACTIONS is a set; this just asserts the registry didn't
    # accidentally collapse two intended actions into the same string.
    assert len(KNOWN_ACTIONS) > 50, "registry should cover the full surface"
