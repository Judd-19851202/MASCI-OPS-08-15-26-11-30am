"""
lib/role_templates.py — Phase K3 · Role Template System.

Centralized role-template inheritance layer. **NON-ENFORCING.** Ships
as a data model + seed + resolver. Nothing in `routes/*` reads it yet;
Phase K6 (deferred, requires explicit approval) will wire enforcement.

Built on top of:
  • K1 unified identity mirror (`user_directory` collection)
  • K2 centralized RBAC service (`lib/rbac.KNOWN_ACTIONS` action catalog)

Design constraints (per user mandate):
  • non-enforcing · migration-safe · backward-compatible · silent
  • fail closed on unknown action / malformed template / inheritance loop
  • super admin remains universal (rbac.is_super_admin)
  • idempotent seed
  • fast resolution (templates loaded once, cached at call site)
  • all actions cross-checked against `rbac.KNOWN_ACTIONS` — no ad-hoc strings

Collection: `role_templates`

Document shape:
  {
    "id":          "rt-shop-mechanic",         # stable slug, primary key
    "portal":      "shop",                     # canonical portal key
    "name":        "Mechanic",                 # display label
    "description": "Bench mechanic ...",
    "inherits_from": ["rt-shop-base"],         # parent template ids (may be empty)
    "actions":     ["shop.work_orders.view"],  # action keys in rbac.KNOWN_ACTIONS
    "record_scope": {"shop.work_orders": "assigned"},   # future K6 enforcement
    "hierarchy_level": 1,                      # 1=lowest, higher=broader
    "active":      True,
    "system":      True,                       # built-in (True) vs custom (False)
    "created_by":  None,
    "updated_by":  None,
    "created_at":  "<iso>",
    "updated_at":  "<iso>",
    "schema_version": 1,
  }

The resolver (`resolve_actions`) flattens inheritance via topological
walk. Cycles, missing parents, and unknown action keys are all fatal
during validation — templates with any of these never get seeded, and
existing rows that fail validation are skipped (and logged).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from lib.rbac import KNOWN_ACTIONS, PORTALS

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────────────────────────────────────────────
# Built-in seed templates.
#
# Every action MUST already exist in rbac.KNOWN_ACTIONS or seeding
# will refuse the row (logged warning, never raises). This keeps K3
# and K2 in lock-step — adding new behaviors requires updating BOTH
# the catalog and the templates that grant them.
# ────────────────────────────────────────────────────────────────

SEED_TEMPLATES: List[Dict[str, Any]] = [

    # ── ADMIN ──────────────────────────────────────────────────
    {
        "id": "rt-admin-system",
        "portal": "admin",
        "name": "System Admin",
        "description": "Full platform access. Break-glass operator.",
        "inherits_from": [],
        # Empty actions list — System Admin gates through is_super_admin()
        # at the rbac layer, not template membership.
        "actions": [],
        "hierarchy_level": 10,
        "system": True,
    },
    {
        "id": "rt-admin-executive-viewer",
        "portal": "admin",
        "name": "Executive Viewer",
        "description": "Read-only access to dashboards and analytics.",
        "inherits_from": [],
        "actions": [
            "admin.audit.view",
            "admin.integrations.view",
            "admin.operational_signals.view",
            "admin.deploy_readiness.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "hierarchy_level": 5,
        "system": True,
    },

    # ── HR ─────────────────────────────────────────────────────
    {
        "id": "rt-hr-readonly",
        "portal": "hr",
        "name": "HR Read Only",
        "description": "Read-only HR data.",
        "inherits_from": [],
        "actions": [
            "hr.employee.view",
            "hr.documents.view",
            "hr.users.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "hierarchy_level": 1,
        "system": True,
    },
    {
        "id": "rt-hr-payroll",
        "portal": "hr",
        "name": "Payroll Specialist",
        "description": "Payroll + limited employee visibility.",
        "inherits_from": ["rt-hr-readonly"],
        "actions": ["hr.payroll.view"],
        "hierarchy_level": 2,
        "system": True,
    },
    {
        "id": "rt-hr-coordinator",
        "portal": "hr",
        "name": "HR Coordinator",
        "description": "Operational HR support — training, documents, intake.",
        "inherits_from": ["rt-hr-readonly"],
        "actions": [
            "hr.training.assign",
            "hr.training.complete",
            "hr.documents.upload",
            "hr.employee.create",
            "hr.employee.edit",
        ],
        "hierarchy_level": 3,
        "system": True,
    },
    {
        "id": "rt-hr-manager",
        "portal": "hr",
        "name": "HR Manager",
        "description": "Full HR portal authority + cross-portal PO approval.",
        "inherits_from": ["rt-hr-coordinator", "rt-hr-payroll"],
        "actions": [
            "hr.employee.offboard",
            "hr.employee.suspend",
            "hr.employee.reactivate",
            "hr.users.manage",
            "hr.po_requests.approve",
            "pm.po_requests.view",
            "pm.po_requests.approve",
            "pm.project.view",
            "shop.users.view",
        ],
        "hierarchy_level": 5,
        "system": True,
    },
    {
        "id": "rt-hr-other",
        "portal": "hr",
        "name": "Other",
        "description": "Custom / unscoped HR access. Empty by default.",
        "inherits_from": [],
        "actions": [],
        "hierarchy_level": 0,
        "system": True,
    },

    # ── PM ─────────────────────────────────────────────────────
    {
        "id": "rt-pm-readonly",
        "portal": "pm",
        "name": "PM Read Only",
        "description": "Read-only access to PM data.",
        "inherits_from": [],
        "actions": [
            "pm.project.view",
            "pm.po_requests.view",
            "pm.project_health.view",
            "pm.daily_reports.view",
            "pm.incidents.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "record_scope": {"pm.project": "assigned", "pm.po_requests": "assigned_projects"},
        "hierarchy_level": 1,
        "system": True,
    },
    {
        "id": "rt-pm-coordinator",
        "portal": "pm",
        "name": "PM Coordinator",
        "description": "PM support — PO creation, daily-report visibility.",
        "inherits_from": ["rt-pm-readonly"],
        "actions": ["pm.po_requests.create"],
        "hierarchy_level": 2,
        "system": True,
    },
    {
        "id": "rt-pm-engineer",
        "portal": "pm",
        "name": "Project Engineer",
        "description": "Project engineering — projects, POs, technical review.",
        "inherits_from": ["rt-pm-coordinator"],
        "actions": ["pm.project.edit"],
        "hierarchy_level": 3,
        "system": True,
    },
    {
        "id": "rt-pm-assistant",
        "portal": "pm",
        "name": "Assistant PM",
        "description": "Assistant project manager — PO upload + receipt handling.",
        "inherits_from": ["rt-pm-engineer"],
        "actions": ["pm.po_requests.upload_receipt", "pm.po_requests.assign_number"],
        "hierarchy_level": 4,
        "system": True,
    },
    {
        "id": "rt-pm-manager",
        "portal": "pm",
        "name": "Project Manager",
        "description": "Full PM authority over assigned projects.",
        "inherits_from": ["rt-pm-assistant"],
        "actions": [
            "pm.po_requests.approve",
            "pm.po_requests.reject",
            "pm.tasks.view",
            "pm.tasks.assign",
            "safety.incidents.view",
            "safety.corrective_actions.close",
        ],
        "hierarchy_level": 5,
        "system": True,
    },
    {
        "id": "rt-pm-other",
        "portal": "pm",
        "name": "Other",
        "description": "Custom / unscoped PM access.",
        "inherits_from": [],
        "actions": [],
        "hierarchy_level": 0,
        "system": True,
    },

    # ── SHOP ──────────────────────────────────────────────────
    {
        "id": "rt-shop-readonly",
        "portal": "shop",
        "name": "Shop Read Only",
        "description": "Read-only shop data.",
        "inherits_from": [],
        "actions": [
            "shop.work_orders.view",
            "shop.equipment.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "record_scope": {"shop.work_orders": "assigned"},
        "hierarchy_level": 1,
        "system": True,
    },
    {
        "id": "rt-shop-mechanic",
        "portal": "shop",
        "name": "Mechanic",
        "description": "Assigned work orders only. No management views.",
        "inherits_from": ["rt-shop-readonly"],
        "actions": ["shop.work_orders.update"],
        "record_scope": {"shop.work_orders": "assigned"},
        "hierarchy_level": 2,
        "system": True,
    },
    {
        "id": "rt-shop-service-writer",
        "portal": "shop",
        "name": "Service Writer",
        "description": "Service intake — creates/views work orders for the shop.",
        "inherits_from": ["rt-shop-readonly"],
        "actions": ["shop.work_orders.create"],
        "hierarchy_level": 2,
        "system": True,
    },
    {
        "id": "rt-shop-parts-coordinator",
        "portal": "shop",
        "name": "Parts Coordinator",
        "description": "Parts inventory + work-order coordination.",
        "inherits_from": ["rt-shop-readonly"],
        "actions": ["shop.parts.manage"],
        "hierarchy_level": 2,
        "system": True,
    },
    {
        "id": "rt-shop-manager",
        "portal": "shop",
        "name": "Shop Manager",
        "description": "Full shop authority — work orders, equipment, users.",
        "inherits_from": ["rt-shop-mechanic", "rt-shop-service-writer", "rt-shop-parts-coordinator"],
        "actions": [
            "shop.work_orders.close",
            "shop.equipment.edit",
            "shop.equipment.transfer",
            "shop.users.view",
            "shop.users.manage",
            "dispatch.equipment.view",
        ],
        "hierarchy_level": 5,
        "system": True,
    },
    {
        "id": "rt-shop-other",
        "portal": "shop",
        "name": "Other",
        "description": "Custom / unscoped shop access.",
        "inherits_from": [],
        "actions": [],
        "hierarchy_level": 0,
        "system": True,
    },

    # ── SAFETY ────────────────────────────────────────────────
    {
        "id": "rt-safety-readonly",
        "portal": "safety",
        "name": "Safety Read Only",
        "description": "Read-only safety data.",
        "inherits_from": [],
        "actions": [
            "safety.incidents.view",
            "safety.audits.view",
            "safety.fire_extinguishers.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "hierarchy_level": 1,
        "system": True,
    },
    {
        "id": "rt-safety-coordinator",
        "portal": "safety",
        "name": "Safety Coordinator",
        "description": "Field safety support — incidents, audits, fire-ext inspections.",
        "inherits_from": ["rt-safety-readonly"],
        "actions": [
            "safety.incidents.create",
            "safety.incidents.edit",
            "safety.corrective_actions.create",
            "safety.audits.create",
            "safety.fire_extinguishers.inspect",
            "pm.project.view",
            "pm.incidents.view",
        ],
        "hierarchy_level": 3,
        "system": True,
    },
    {
        "id": "rt-safety-director",
        "portal": "safety",
        "name": "Safety Director",
        "description": "Full safety portal authority. Closes CAs, assigns training.",
        "inherits_from": ["rt-safety-coordinator"],
        "actions": [
            "safety.corrective_actions.close",
            "safety.training.assign",
            "safety.users.view",
            "safety.users.manage",
        ],
        "hierarchy_level": 5,
        "system": True,
    },
    {
        "id": "rt-safety-other",
        "portal": "safety",
        "name": "Other",
        "description": "Custom / unscoped safety access.",
        "inherits_from": [],
        "actions": [],
        "hierarchy_level": 0,
        "system": True,
    },

    # ── DISPATCH ──────────────────────────────────────────────
    {
        "id": "rt-dispatch-readonly",
        "portal": "dispatch",
        "name": "Dispatch Read Only",
        "description": "Read-only dispatch data.",
        "inherits_from": [],
        "actions": [
            "dispatch.equipment.view",
            "dispatch.fleet.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "hierarchy_level": 1,
        "system": True,
    },
    {
        "id": "rt-dispatch-dispatcher",
        "portal": "dispatch",
        "name": "Dispatcher",
        "description": "Day-to-day dispatch operations.",
        "inherits_from": ["rt-dispatch-readonly"],
        "actions": ["dispatch.equipment.dispatch", "shop.equipment.view"],
        "hierarchy_level": 3,
        "system": True,
    },
    {
        "id": "rt-dispatch-fleet-coordinator",
        "portal": "dispatch",
        "name": "Fleet Coordinator",
        "description": "Fleet movements + transfers.",
        "inherits_from": ["rt-dispatch-dispatcher"],
        "actions": ["dispatch.equipment.transfer"],
        "hierarchy_level": 4,
        "system": True,
    },
    {
        "id": "rt-dispatch-manager",
        "portal": "dispatch",
        "name": "Dispatch Manager",
        "description": "Full dispatch authority + user management.",
        "inherits_from": ["rt-dispatch-fleet-coordinator"],
        "actions": ["dispatch.users.view", "dispatch.users.manage"],
        "hierarchy_level": 5,
        "system": True,
    },
    {
        "id": "rt-dispatch-other",
        "portal": "dispatch",
        "name": "Other",
        "description": "Custom / unscoped dispatch access.",
        "inherits_from": [],
        "actions": [],
        "hierarchy_level": 0,
        "system": True,
    },

    # ── FIELD LEADERSHIP ──────────────────────────────────────
    # Hierarchy: Foreman < Superintendent < Senior Superintendent.
    # Each tier inherits the lower tier's actions; broader visibility
    # is layered on top. Record-scope tightening is K6 work.
    {
        "id": "rt-leadership-foreman",
        "portal": "leadership",
        "name": "Foreman",
        "description": "Crew/job-level field leadership. Records, daily reports, incidents, POs.",
        "inherits_from": [],
        "actions": [
            "leadership.records.view",
            "leadership.records.create",
            "leadership.po_requests.create",
            "leadership.daily_reports.create",
            "leadership.incidents.create",
            "pm.project.view",
            "platform.search.use",
            "platform.tasks.view_own",
            "platform.notifications.view_own",
            "platform.operations_center.view",
            "platform.project_health.view",
            "platform.asset_transfers.view",
        ],
        "record_scope": {"pm.project": "assigned_jobs"},
        "hierarchy_level": 1,
        "system": True,
    },
    {
        "id": "rt-leadership-superintendent",
        "portal": "leadership",
        "name": "Superintendent",
        "description": "Project/job-level oversight. Inherits Foreman scope.",
        "inherits_from": ["rt-leadership-foreman"],
        # No additional actions yet — distinction lives in record_scope
        # widening (Foreman = crew/job · Sup = project-level).
        "actions": [],
        "record_scope": {"pm.project": "assigned_projects"},
        "hierarchy_level": 2,
        "system": True,
    },
    {
        "id": "rt-leadership-senior-superintendent",
        "portal": "leadership",
        "name": "Senior Superintendent",
        "description": "Multi-project visibility. Inherits Superintendent scope.",
        "inherits_from": ["rt-leadership-superintendent"],
        "actions": [],
        # Broadest leadership scope; concrete enforcement in K6.
        "record_scope": {"pm.project": "multi_project"},
        "hierarchy_level": 3,
        "system": True,
    },
]


# ────────────────────────────────────────────────────────────────
# Validation
# ────────────────────────────────────────────────────────────────


class TemplateValidationError(Exception):
    """Raised internally; never escapes the public API. Validation
    failures are logged and the offending row is skipped."""


def _validate_one(t: Dict[str, Any]) -> None:
    if not isinstance(t, dict):
        raise TemplateValidationError("template must be a dict")
    for key in ("id", "portal", "name"):
        v = t.get(key)
        if not isinstance(v, str) or not v.strip():
            raise TemplateValidationError(f"missing/empty '{key}'")
    if t["portal"] not in PORTALS:
        raise TemplateValidationError(f"unknown portal: {t['portal']}")
    if not t["id"].startswith("rt-"):
        raise TemplateValidationError("template id must start with 'rt-'")
    inherits = t.get("inherits_from") or []
    if not isinstance(inherits, list):
        raise TemplateValidationError("inherits_from must be a list")
    if t["id"] in inherits:
        raise TemplateValidationError(f"self-inheritance not allowed: {t['id']}")
    actions = t.get("actions") or []
    if not isinstance(actions, list):
        raise TemplateValidationError("actions must be a list")
    for a in actions:
        if not isinstance(a, str):
            raise TemplateValidationError(f"non-string action: {a!r}")
        if a not in KNOWN_ACTIONS:
            raise TemplateValidationError(f"unknown action (not in rbac.KNOWN_ACTIONS): {a}")
    rs = t.get("record_scope")
    if rs is not None and not isinstance(rs, dict):
        raise TemplateValidationError("record_scope must be a dict or absent")


def _detect_cycles(templates_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    """Return the ids of templates that participate in any inheritance
    cycle (Tarjan-style DFS). Cycles are fatal — templates inside them
    are skipped at seed time and dropped from `resolve_actions`."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {tid: WHITE for tid in templates_by_id}
    cyclic: Set[str] = set()

    def visit(node: str, path: List[str]) -> None:
        if color.get(node) == GRAY:
            # Cycle: collect everything from where node first appears in path.
            try:
                idx = path.index(node)
                cyclic.update(path[idx:])
            except ValueError:
                cyclic.add(node)
            return
        if color.get(node) == BLACK:
            return
        color[node] = GRAY
        path.append(node)
        for parent in (templates_by_id.get(node, {}).get("inherits_from") or []):
            if parent in templates_by_id:
                visit(parent, path)
        path.pop()
        color[node] = BLACK

    for tid in list(templates_by_id.keys()):
        if color[tid] == WHITE:
            visit(tid, [])

    return sorted(cyclic)


# ────────────────────────────────────────────────────────────────
# Resolution (in-memory and via DB)
# ────────────────────────────────────────────────────────────────


def _resolve_in_memory(template_id: str, templates_by_id: Dict[str, Dict[str, Any]]) -> Set[str]:
    """Walk inheritance and union actions. Skips cyclic / missing
    parents (returns the partial set rather than raising). Designed to
    fail closed: malformed inputs yield narrower (never broader) sets."""
    if not template_id or template_id not in templates_by_id:
        return set()
    cyclic = set(_detect_cycles(templates_by_id))
    seen: Set[str] = set()
    acc: Set[str] = set()

    def walk(tid: str) -> None:
        if tid in seen or tid in cyclic:
            return
        seen.add(tid)
        t = templates_by_id.get(tid)
        if not t:
            return
        for a in (t.get("actions") or []):
            if a in KNOWN_ACTIONS:
                acc.add(a)
        for parent in (t.get("inherits_from") or []):
            walk(parent)

    walk(template_id)
    return acc


async def resolve_actions(db, template_id: str) -> Set[str]:
    """Async DB-backed resolver. Loads ALL templates once, then walks
    the inheritance graph. Returns the flattened action set for the
    requested template. Empty set if the id is unknown."""
    rows = [d async for d in db.role_templates.find({}, {"_id": 0})]
    by_id = {r["id"]: r for r in rows if isinstance(r.get("id"), str)}
    return _resolve_in_memory(template_id, by_id)


async def get_template(db, template_id: str) -> Optional[Dict[str, Any]]:
    return await db.role_templates.find_one({"id": template_id}, {"_id": 0})


async def list_templates(db, portal: Optional[str] = None) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if portal:
        q["portal"] = portal
    return [d async for d in db.role_templates.find(q, {"_id": 0}).sort("portal", 1)]


# ────────────────────────────────────────────────────────────────
# Indexes + Seed
# ────────────────────────────────────────────────────────────────


async def ensure_indexes(db) -> None:
    try:
        await db.role_templates.create_index("id", unique=True, name="id_unique")
        await db.role_templates.create_index("portal", name="portal_idx")
        await db.role_templates.create_index("active", name="active_idx")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[role-templates] ensure_indexes warning: {e}")


async def seed_role_templates(db) -> Dict[str, int]:
    """Idempotent seed of all built-in role templates.

    Pre-flight checks:
      • Each template validated individually (`_validate_one`).
      • Cross-template cycle detection — any template in a cycle is
        SKIPPED at seed time, NOT inserted with a broken parent chain.

    For each valid template:
      • If absent → insert
      • If present → update name/description/inherits_from/actions/
        record_scope/hierarchy_level/active fields, BUT preserve the
        original `created_at` / `created_by` fields. Custom templates
        added by admins (system != True) are NEVER touched here.
    """
    await ensure_indexes(db)

    valid: List[Dict[str, Any]] = []
    for t in SEED_TEMPLATES:
        try:
            _validate_one(t)
            valid.append(t)
        except TemplateValidationError as e:
            logger.warning(f"[role-templates] invalid seed {t.get('id')}: {e}")

    by_id = {t["id"]: t for t in valid}
    cyclic = set(_detect_cycles(by_id))
    if cyclic:
        logger.warning(f"[role-templates] inheritance cycle detected: {cyclic}")
        for cid in cyclic:
            by_id.pop(cid, None)

    inserted = 0
    updated = 0
    now = _now()

    for t in by_id.values():
        existing = await db.role_templates.find_one({"id": t["id"]}, {"_id": 0})
        if existing is None:
            doc = {
                **t,
                "active": True,
                "created_by": None,
                "updated_by": None,
                "created_at": now,
                "updated_at": now,
                "schema_version": 1,
            }
            await db.role_templates.insert_one(doc)
            inserted += 1
            continue

        # Don't touch custom (non-system) rows.
        if not existing.get("system"):
            continue

        await db.role_templates.update_one(
            {"id": t["id"]},
            {"$set": {
                "portal": t["portal"],
                "name": t["name"],
                "description": t.get("description", ""),
                "inherits_from": t.get("inherits_from") or [],
                "actions": t.get("actions") or [],
                "record_scope": t.get("record_scope") or {},
                "hierarchy_level": t.get("hierarchy_level", 0),
                "active": True,
                "system": True,
                "updated_at": now,
                "schema_version": 1,
            }},
        )
        updated += 1

    return {"valid": len(by_id), "inserted": inserted, "updated": updated, "cyclic_skipped": len(cyclic)}


async def run_startup_seed(db) -> None:
    """FastAPI startup hook. Logs results, never raises."""
    try:
        stats = await seed_role_templates(db)
        logger.info(
            "[role-templates] startup seed complete: "
            f"valid={stats['valid']} inserted={stats['inserted']} "
            f"updated={stats['updated']} cyclic_skipped={stats['cyclic_skipped']}"
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[role-templates] startup seed failed: {e}")


__all__ = [
    "SEED_TEMPLATES",
    "TemplateValidationError",
    "ensure_indexes",
    "seed_role_templates",
    "run_startup_seed",
    "resolve_actions",
    "get_template",
    "list_templates",
]
