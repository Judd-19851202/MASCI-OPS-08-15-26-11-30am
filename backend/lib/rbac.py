"""
lib/rbac.py — Phase K2 · Centralized RBAC Service Layer.

ONE module. ONE permission brain. Replaces scattered `role == "..."`
string-equality checks across the codebase.

K2 is **non-enforcing**. This module ships as a library that nothing
yet depends on. Phase K6 (deferred, requires explicit user approval)
will incrementally swap the existing scattered checks for calls into
`can()` / `require()` here.

Design constraints (per user mandate):
  • simple, predictable, fast (zero DB calls per `can()`)
  • fail closed on unknown action / missing subject
  • super admin always passes (break-glass)
  • zero hardcoded `role == "..."` outside this file
  • frontend remains responsible for UI hiding only;
    this is the server-side source of truth.

Subject (actor) shape — matches `_require_any_portal_token` output:
    {
      "_actor": "admin" | "safety" | "hr" | "shop" | "pm" | "dispatch" | "leadership",
      "name":   str,
      "role":   str | None,                # portal-specific role label
      "email":  str | None,
      "id":     str | None,
      # plus arbitrary other fields from the per-portal user doc
    }

Action format:
    "<portal>.<module>.<verb>"
    e.g.  "admin.users.manage"
          "shop.work_orders.update"
          "pm.po_requests.approve"
          "hr.employee.edit"
          "safety.incidents.create"
          "dispatch.equipment.transfer"
          "leadership.records.create"

Context (ctx) is an optional dict of record-scope hints — used when
the decision depends on data (e.g. "PM can only update POs on jobs
they're assigned to"). K2 supports the structure; concrete scope
rules will land in K6 when we wire enforcement.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
# Portal / role canonicalization
# ────────────────────────────────────────────────────────────────

PORTALS: Tuple[str, ...] = (
    "admin", "hr", "pm", "shop", "safety", "dispatch", "leadership",
)


def actor_portal(actor: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return the canonical portal key the actor authenticated through."""
    if not actor:
        return None
    p = actor.get("_actor")
    return p if p in PORTALS else None


def actor_role(actor: Optional[Dict[str, Any]]) -> Optional[str]:
    """The portal-specific role label (e.g. 'HR Manager'). May be None
    for portals like Admin or Leadership where role is implicit."""
    if not actor:
        return None
    r = actor.get("role")
    return r if isinstance(r, str) and r.strip() else None


def actor_email(actor: Optional[Dict[str, Any]]) -> Optional[str]:
    if not actor:
        return None
    e = actor.get("email")
    return e.strip().lower() if isinstance(e, str) and e.strip() else None


def actor_id(actor: Optional[Dict[str, Any]]) -> Optional[str]:
    if not actor:
        return None
    for k in ("id", "user_id", "_id"):
        v = actor.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def is_super_admin(actor: Optional[Dict[str, Any]]) -> bool:
    """Super admin = admin portal token OR directory row flagged
    `is_super_admin=True` OR email matches SUPER_ADMIN_EMAIL env.

    K2: admin portal token implies super admin (matches today's
    enforcement). K3+ will narrow this once Executive Viewer role
    template ships.
    """
    if not actor:
        return False
    if actor.get("is_super_admin") is True:
        return True
    if actor_portal(actor) == "admin":
        return True
    sa_email = (os.environ.get("SUPER_ADMIN_EMAIL", "") or "").strip().lower()
    if sa_email and actor_email(actor) == sa_email:
        return True
    return False


# ────────────────────────────────────────────────────────────────
# Action registry — the catalog of every permission keyword the
# platform recognizes today. Used both as documentation and as a
# fail-closed gate (unknown action → False).
# ────────────────────────────────────────────────────────────────

# Canonical action vocabulary. Anything not listed here is rejected
# by `can()` to prevent typos from silently granting access.
KNOWN_ACTIONS: Set[str] = {
    # ── admin portal ───────────────────────────────────────────
    "admin.users.view",
    "admin.users.manage",
    "admin.audit.view",
    "admin.system.manage",
    "admin.integrations.view",
    "admin.integrations.manage",
    "admin.operational_signals.view",
    "admin.deploy_readiness.view",
    "admin.training.manage",
    "admin.banner.manage",
    "admin.email.send",

    # ── hr portal ──────────────────────────────────────────────
    "hr.employee.view",
    "hr.employee.create",
    "hr.employee.edit",
    "hr.employee.offboard",
    "hr.employee.suspend",
    "hr.employee.reactivate",
    "hr.training.assign",
    "hr.training.complete",
    "hr.documents.upload",
    "hr.documents.view",
    "hr.po_requests.approve",
    "hr.users.view",
    "hr.users.manage",
    "hr.payroll.view",

    # ── pm portal ──────────────────────────────────────────────
    "pm.project.view",
    "pm.project.edit",
    "pm.po_requests.view",
    "pm.po_requests.create",
    "pm.po_requests.approve",
    "pm.po_requests.reject",
    "pm.po_requests.assign_number",
    "pm.po_requests.upload_receipt",
    "pm.tasks.view",
    "pm.tasks.assign",
    "pm.project_health.view",
    "pm.daily_reports.view",
    "pm.incidents.view",

    # ── shop / fleet portal ────────────────────────────────────
    "shop.work_orders.view",
    "shop.work_orders.create",
    "shop.work_orders.update",
    "shop.work_orders.close",
    "shop.equipment.view",
    "shop.equipment.edit",
    "shop.equipment.transfer",
    "shop.parts.manage",
    "shop.users.view",
    "shop.users.manage",

    # ── safety portal ──────────────────────────────────────────
    "safety.incidents.view",
    "safety.incidents.create",
    "safety.incidents.edit",
    "safety.corrective_actions.create",
    "safety.corrective_actions.close",
    "safety.audits.view",
    "safety.audits.create",
    "safety.fire_extinguishers.view",
    "safety.fire_extinguishers.inspect",
    "safety.training.assign",
    "safety.users.view",
    "safety.users.manage",

    # ── dispatch portal ────────────────────────────────────────
    "dispatch.equipment.view",
    "dispatch.equipment.transfer",
    "dispatch.equipment.dispatch",
    "dispatch.fleet.view",
    "dispatch.users.view",
    "dispatch.users.manage",

    # ── leadership portal (shared MASCIGC for now) ─────────────
    "leadership.records.view",
    "leadership.records.create",
    "leadership.po_requests.create",
    "leadership.daily_reports.create",
    "leadership.incidents.create",

    # ── cross-cutting ──────────────────────────────────────────
    "platform.search.use",
    "platform.tasks.view_own",
    "platform.notifications.view_own",
    "platform.operations_center.view",
    "platform.project_health.view",
    "platform.asset_transfers.view",
}


def _parse_action(action: str) -> Optional[Tuple[str, str, str]]:
    """Split 'portal.module.verb' into its three parts. Returns None
    on malformed input (which forces a fail-closed in `can()`)."""
    if not isinstance(action, str):
        return None
    parts = action.split(".")
    if len(parts) != 3:
        return None
    portal, module, verb = parts
    if not portal or not module or not verb:
        return None
    return portal, module, verb


# ────────────────────────────────────────────────────────────────
# Default portal-to-actions map.
# K2 captures **today's enforcement** in one place. K3 will replace
# this with role-template lookups so org admins can customize.
# ────────────────────────────────────────────────────────────────

# A portal actor receives EVERY action whose namespace starts with
# that portal name. Cross-portal grants (e.g. HR Manager being able
# to approve POs) are explicit below.
_PLATFORM_ACTIONS_ALL_PORTALS: Tuple[str, ...] = (
    "platform.search.use",
    "platform.tasks.view_own",
    "platform.notifications.view_own",
    "platform.operations_center.view",
    "platform.project_health.view",
    "platform.asset_transfers.view",
)

# Explicit cross-portal grants. Keep this list tight — it is the
# only place actors get permissions outside their own namespace.
_CROSS_PORTAL_GRANTS: Dict[str, Set[str]] = {
    # Admin actor reads the entire platform but only manages its own
    # namespace. Real-world: System Admins use the unified UI.
    "admin": {
        # full namespace handled by namespace match below
        # cross-portal read access:
        "hr.employee.view",
        "hr.documents.view",
        "hr.users.view",
        "hr.payroll.view",
        "pm.project.view",
        "pm.po_requests.view",
        "pm.project_health.view",
        "pm.daily_reports.view",
        "pm.incidents.view",
        "shop.work_orders.view",
        "shop.equipment.view",
        "shop.users.view",
        "safety.incidents.view",
        "safety.corrective_actions.close",   # admin override
        "safety.audits.view",
        "safety.fire_extinguishers.view",
        "safety.users.view",
        "dispatch.equipment.view",
        "dispatch.fleet.view",
        "dispatch.users.view",
        "leadership.records.view",
    },
    # HR Manager can approve POs and view some cross-portal data.
    # Role-specific grants land in K3 role-templates; for K2 we
    # gate at the portal level (hr.*) plus this list.
    "hr": {
        "pm.po_requests.approve",   # HR Manager often approves PM POs today
        "pm.project.view",
        "pm.po_requests.view",
        "shop.users.view",         # HR sees shop users for onboarding
    },
    "pm": {
        "safety.incidents.view",
        "safety.corrective_actions.close",
    },
    "safety": {
        "pm.project.view",
        "pm.incidents.view",
    },
    "shop": {
        "dispatch.equipment.view",
    },
    "dispatch": {
        "shop.equipment.view",
    },
    # Field Leadership has access to a strict subset of cross-portal
    # data needed for daily field operations.
    "leadership": {
        "pm.project.view",
        "platform.search.use",
        "platform.tasks.view_own",
    },
}


# ────────────────────────────────────────────────────────────────
# Core decision API
# ────────────────────────────────────────────────────────────────


def can(actor: Optional[Dict[str, Any]], action: str, ctx: Optional[Dict[str, Any]] = None) -> bool:
    """Return True iff the actor is allowed to perform `action`.

    Fails closed on:
      • missing/empty actor
      • malformed action string
      • unknown action (not in KNOWN_ACTIONS)
      • unknown portal

    Super admin (admin token or SUPER_ADMIN_EMAIL) bypasses everything
    EXCEPT the KNOWN_ACTIONS catalog — they still fail on typos.
    """
    parsed = _parse_action(action)
    if parsed is None:
        return False
    if action not in KNOWN_ACTIONS:
        return False
    portal_of_action, _module, _verb = parsed

    # Super admin can do anything in the catalog.
    if is_super_admin(actor):
        return True

    actor_pkey = actor_portal(actor)
    if not actor_pkey:
        return False

    # Cross-cutting platform-level actions — every authenticated
    # portal actor gets these (search, own tasks, own notifications,
    # ops center, project health, asset transfers).
    if portal_of_action == "platform" and action in _PLATFORM_ACTIONS_ALL_PORTALS:
        return True

    # Namespace match: actor's portal owns the action's portal.
    if portal_of_action == actor_pkey:
        return True

    # Explicit cross-portal grant.
    cross = _CROSS_PORTAL_GRANTS.get(actor_pkey, set())
    if action in cross:
        return True

    return False


def require(actor: Optional[Dict[str, Any]], action: str, ctx: Optional[Dict[str, Any]] = None) -> None:
    """Raise HTTPException(403) if `can()` returns False. Use as the
    server-side enforcement primitive in route handlers."""
    if not can(actor, action, ctx):
        portal = actor_portal(actor) or "anon"
        logger.info(
            f"[rbac] denied portal={portal} email={actor_email(actor)} action={action}"
        )
        raise HTTPException(status_code=403, detail=f"Forbidden: {action}")


def actions_for_actor(actor: Optional[Dict[str, Any]]) -> Set[str]:
    """Return the full set of actions this actor can perform. Useful
    for surfacing 'capabilities' to the frontend so it can render the
    correct controls, while the server stays authoritative."""
    if is_super_admin(actor):
        return set(KNOWN_ACTIONS)
    portal = actor_portal(actor)
    if not portal:
        return set()
    own = {a for a in KNOWN_ACTIONS if a.startswith(f"{portal}.")}
    cross = set(_CROSS_PORTAL_GRANTS.get(portal, set()))
    platform = set(_PLATFORM_ACTIONS_ALL_PORTALS)
    return own | cross | platform


def explain(actor: Optional[Dict[str, Any]], action: str) -> Dict[str, Any]:
    """Diagnostic — returns the decision plus the reason. Intended for
    a future `/api/admin/rbac/explain` endpoint (out of K2 scope) and
    for unit-test readability."""
    decision = can(actor, action)
    return {
        "actor_portal": actor_portal(actor),
        "actor_role": actor_role(actor),
        "is_super_admin": is_super_admin(actor),
        "action": action,
        "known_action": action in KNOWN_ACTIONS,
        "parsed": _parse_action(action),
        "allow": decision,
    }


__all__ = [
    "PORTALS",
    "KNOWN_ACTIONS",
    "actor_portal",
    "actor_role",
    "actor_email",
    "actor_id",
    "is_super_admin",
    "can",
    "require",
    "actions_for_actor",
    "explain",
]
