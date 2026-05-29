"""
routes/odr/visibility.py — Field Leadership Visibility Doctrine projector.

Inherits FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md verbatim — never
mutates auth, only restricts UI / projector surfaces per role.

The four verbs FULL · LIMITED · SUMMARY · NONE drive query shape +
response shape. This module exposes the *helper* layer; routes
consult it on every read.

Mapping (V.1 ODR per master matrix):

| FLL | Verb |
|---|---|
| FLL-1 Foreman / Crew Lead     | FULL (own ODR only · today/tomorrow horizon) |
| FLL-2 General Foreman         | FULL (own crews · 3-day rolling window) |
| FLL-3 Superintendent          | FULL (entire project) |
| FLL-4 Senior Superintendent   | FULL (regional · assigned projects) |
| FLL-5 PM                      | LIMITED (cost+contract lens · no edit/return/approve from PM portal · per V.1 doctrine PM is read-only consumer) |
| FLL-6 Operations Leadership   | SUMMARY (no per-record review by default · per-record deep-drill logged) |

Auth still enforces who can call. Visibility decides what they see.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .enums import FLL, VisibilityVerb


# ── Actor → FLL resolution ───────────────────────────────────────────


def resolve_fll(actor: Dict[str, Any]) -> FLL:
    """Resolve calling actor to a Field Leadership Level.

    The actor dict comes from `_require_any_portal_token`. The
    `_actor` field tags the originating portal:
      admin · pm · hr · safety · shop · dispatch · fl

    For FL actors, the role string (Foreman / Superintendent /
    Senior Super) selects FLL-1 / FLL-3 / FLL-4. General Foreman is
    not yet a distinct tier — treated as FLL-2 only when the
    directory mirrors `general_foreman=True`.
    """
    if not isinstance(actor, dict):
        return "FLL-1"
    portal = (actor.get("_actor") or "").lower()
    if portal == "admin":
        # Operations Leadership flag opt-in; absent → admin remains FLL-6 by default
        if actor.get("operations_leader") is True:
            return "FLL-6"
        return "FLL-6"   # Admin defaults to FLL-6 (signal lens) for ODR surfaces
    if portal == "pm":
        return "FLL-5"
    if portal == "fl":
        role = (actor.get("role") or actor.get("fl_role") or "").lower()
        if "senior" in role:
            return "FLL-4"
        if "superintendent" in role:
            return "FLL-3"
        if actor.get("general_foreman") is True or "general" in role:
            return "FLL-2"
        return "FLL-1"
    # Safety / HR / Shop / Dispatch are not in the FLL doctrine; they
    # consume via projectors but are not "field leadership". For ODR
    # read surfaces they get LIMITED scope (no edit, no approve).
    return "FLL-5"


# ── Verb for the ODR system per FLL ──────────────────────────────────


_ODR_VERB_BY_FLL: Dict[str, VisibilityVerb] = {
    "FLL-1": "FULL",      # own ODR
    "FLL-2": "FULL",      # own crews
    "FLL-3": "FULL",      # entire project
    "FLL-4": "FULL",      # regional · assigned projects
    "FLL-5": "LIMITED",   # PM read-only consumer lens
    "FLL-6": "SUMMARY",   # signal-only by default
}


def odr_verb(fll: FLL) -> VisibilityVerb:
    return _ODR_VERB_BY_FLL.get(fll, "LIMITED")


# ── Scope filter (query shape) ───────────────────────────────────────


def build_odr_scope_filter(
    actor: Dict[str, Any],
    requested_project_id: Optional[str] = None,
    requested_crew_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], FLL, VisibilityVerb]:
    """Returns (mongo_filter, fll, verb).

    The doctrine governs WHICH ROWS the actor may see in a list /
    detail query. Auth still gates the endpoint; this narrows.
    """
    fll = resolve_fll(actor)
    verb = odr_verb(fll)
    q: Dict[str, Any] = {}

    actor_uid = (
        actor.get("id")
        or actor.get("user_id")
        or actor.get("uid")
        or actor.get("email")
        or ""
    )

    if fll == "FLL-1":
        # Foreman sees only own crew's ODRs.
        if actor_uid:
            q["project.foreman_uid"] = actor_uid
        if requested_crew_id:
            q["crew_profile.crew_id"] = requested_crew_id
    elif fll == "FLL-2":
        # General Foreman — scoped by directory.crews_managed (if present),
        # else falls back to own foreman_uid.
        crews_managed = actor.get("crews_managed") or []
        if crews_managed:
            q["crew_profile.crew_id"] = {"$in": crews_managed}
        elif actor_uid:
            q["project.foreman_uid"] = actor_uid
    elif fll == "FLL-3":
        # Superintendent — scoped by project assignment.
        if requested_project_id:
            q["project.project_id"] = requested_project_id
    elif fll == "FLL-4":
        # Senior Super — scoped by assigned region. Region scoping
        # uses directory.regional_projects[] when available.
        regional_projects = actor.get("regional_projects") or []
        if regional_projects:
            q["project.project_id"] = {"$in": regional_projects}
        elif requested_project_id:
            q["project.project_id"] = requested_project_id
    elif fll == "FLL-5":
        # PM — scoped by pm_uid + own project assignments.
        if requested_project_id:
            q["project.project_id"] = requested_project_id
        elif actor_uid:
            q["project.pm_uid"] = actor_uid
    elif fll == "FLL-6":
        # Admin / Ops Leadership — no row filter by default · SUMMARY verb
        # implies aggregations rather than raw rows in UI. The list
        # endpoint will compress fields client-side; query stays open.
        if requested_project_id:
            q["project.project_id"] = requested_project_id

    return q, fll, verb


# ── Field projection (response shape) ────────────────────────────────


# Fields a FLL-5 PM does NOT see on the ODR read (per doctrine — PM
# consumes the financial/contract lens, not raw coaching prompts or
# raw completion telemetry).
_PM_HIDDEN_FIELDS = {
    "completion_telemetry",        # admin-only diagnostic (O9)
    "readiness.coaching_prompts",  # author-only (O50)
    "reliability.sync_conflicts",  # operational noise for PM
    "reliability.device_fingerprint",
}

# Fields a FLL-6 admin (SUMMARY default) sees compressed. M0.1 keeps
# them visible — UI layer compresses to summary cards. Adjust here if
# a probe needs to enforce strictly.
_FLL6_HIDDEN_FIELDS: set = set()


def apply_field_projection(
    doc: Dict[str, Any], fll: FLL, verb: VisibilityVerb,
) -> Dict[str, Any]:
    """Strip fields the doctrine says this FLL must not see."""
    if doc is None:
        return doc
    # Always strip Mongo _id and the internal consumer_dispatch dict
    # (admin-only diagnostic).
    doc.pop("_id", None)

    if fll == "FLL-5":
        for path in _PM_HIDDEN_FIELDS:
            _strip_path(doc, path)
        # PM never gets raw `completion_telemetry`
        doc.pop("completion_telemetry", None)

    if fll == "FLL-1" or fll == "FLL-2":
        # Foremen never see `completion_telemetry` (their own data,
        # but doctrine reserves it as admin-diagnostic per O9).
        doc.pop("completion_telemetry", None)
        # Foremen never see `consumer_dispatch`.
        doc.pop("consumer_dispatch", None)

    if fll != "FLL-6":
        doc.pop("consumer_dispatch", None)

    return doc


def _strip_path(doc: Dict[str, Any], dotted: str) -> None:
    parts = dotted.split(".")
    cur: Any = doc
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return
        cur = cur[p]
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)


__all__ = [
    "resolve_fll",
    "odr_verb",
    "build_odr_scope_filter",
    "apply_field_projection",
]
