"""
routes/global_search.py — Iter155 (Phase 2.5) · Phase G.

UNIFIED, PERMISSION-SAFE GLOBAL SEARCH.

One search endpoint reachable from every portal. Returns role-aware,
permission-safe results across the platform's operational object
surface. Designed to be:

  * Fast        — asyncio.gather'd parallel probes, indexed regex,
                  per-kind limit, lightweight payloads
  * Safe        — each probe applies its own scope filter so a Safety
                  user NEVER sees an HR-only result, a PM only sees
                  records tied to their projects, Field Leadership only
                  sees their own POs, etc.
  * Lightweight — returns only id/title/subtitle/url/badge per row.
                  NO descriptions, NO base64 thumbnails, NO PII.
  * Predictable — closed-set categories, role-aware coverage list
                  echoed back in the response so the UI can render
                  "what you can search" without guessing.

CRITICAL: never include result counts for kinds the caller has no
access to. If a kind is out-of-scope, it's NOT probed and NOT echoed
— zero data leakage through counters or category labels.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request

from lib.enterprise_governance import build_governance_actor_context, require_governed_action
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from lib.synthetic_flr_filter import apply_synthetic_flr_exclusion
from masci.identity import format_employee_identity

logger = logging.getLogger(__name__)


# ─── Per-kind / per-role coverage map ─────────────────────────────────
# Each kind is one of the closed-set categories below. The actor's
# `_actor` role determines which kinds are probed. Admin = all.
#
# Why a static map: explicit > implicit. Reading this single dict tells
# you exactly which roles can search which kinds — no scattered if/else.

ALL_KINDS = (
    "tasks",
    "notifications",
    "employees",
    "equipment",
    "projects",
    "po_requests",
    "incidents",
    "corrective_actions",
    "fire_extinguishers",
    "safety_documents",
    "safety_training",
    "document_expirations",
    "operations_events",
    "field_leadership",
    "staffing",
    # TRACK 14.0-DISCOVERABILITY · Wave B (2026-02-15) — 5 critical
    # workflow probes the operator search-coverage audit identified as
    # missing. Probes only return rows the actor's HTTP gate already
    # admits (read-side parity with /api/daily-reports, /api/meetings,
    # /api/inspections, /api/trench-safety/assets, /api/jhas).
    "daily_reports",
    "meetings",
    "inspections",
    "trench_assets",
    "jha_plans",
)

# Role → tuple of kinds visible to that role. Admin gets everything.
KIND_VISIBILITY: Dict[str, tuple] = {
    "admin": ALL_KINDS,
    "safety": (
        "tasks", "notifications",
        "incidents", "corrective_actions",
        "fire_extinguishers", "safety_documents",
        "safety_training", "document_expirations",
        "employees", "equipment",
        "staffing",
        # Wave B additions — Safety reads these via _read_gate already.
        "meetings", "inspections", "jha_plans", "trench_assets",
    ),
    "hr": (
        "tasks", "notifications",
        "employees", "safety_training",
        "document_expirations", "field_leadership",
        "po_requests",
        "staffing",
        # Wave B — HR has /hr/daily-reports portal page (read-only).
        "daily_reports",
    ),
    "pm": (
        "tasks", "notifications",
        "projects", "po_requests",
        "incidents", "corrective_actions",
        "employees", "equipment",
        "staffing",
        # Wave B — PM-scoped via compute_pm_scope on each probe.
        "daily_reports", "meetings", "inspections", "jha_plans",
    ),
    "shop": (
        "tasks", "notifications",
        "equipment", "operations_events",
        "document_expirations",
        "staffing",
        # Wave B — Shop runs the trench-safety repair queue.
        "trench_assets",
    ),
    "dispatch": (
        "tasks", "notifications",
        "equipment", "operations_events",
        "projects",
        "staffing",
    ),
    "leadership": (
        "po_requests", "field_leadership",
    ),
}

# Friendly labels (per kind) for the UI grouping
KIND_LABELS: Dict[str, str] = {
    "tasks": "Tasks",
    "notifications": "Notifications",
    "employees": "Employees",
    "equipment": "Equipment / Assets",
    "projects": "Jobs / Projects",
    "po_requests": "PO Requests",
    "incidents": "Incidents",
    "corrective_actions": "Corrective Actions",
    "fire_extinguishers": "Fire Extinguishers",
    "safety_documents": "Safety Documents",
    "safety_training": "Training Records",
    "document_expirations": "Document Expirations",
    "operations_events": "Operations Events",
    "field_leadership": "Field Leadership Records",
    "staffing": "Project Staffing",
    # Wave B (TRACK 14.0-DISCOVERABILITY)
    "daily_reports": "Daily Reports",
    "meetings": "Safety Meetings",
    "inspections": "Site Inspections",
    "trench_assets": "Trench Safety Assets",
    "jha_plans": "JHA Plans",
}


def _safe_regex(q: str) -> Dict[str, str]:
    """Build a case-insensitive regex from user input. Always escapes."""
    return {"$regex": re.escape(q.strip()), "$options": "i"}


# ─── Spanish discoverability layer (TRACK 14.0-DISCOVERABILITY D-A11) ─
# Static EN ↔ ES vocabulary map applied to the query BEFORE the regex
# is built. A Spanish-speaking superintendent typing `incidente` should
# find the same incident a foreman typing `incident` finds. No data is
# translated — only the QUERY is expanded into the alternation regex so
# the existing English-stored records match. Per-language coverage is
# documented in `DISCOVERABILITY_SPANISH_CERT.md`.
#
# Bidirectional: ES → EN AND EN → ES (so `trench` ALSO matches a record
# that happens to be authored in Spanish, e.g. a notification body).
# Whole-token match only — `zanja` matches `zanja` but not `zanjado`.

ES_EN_SYNONYMS: Dict[str, tuple] = {
    # Safety / records
    "incidente":            ("incident",),
    "incidentes":           ("incident", "incidents"),
    "reporte":              ("report",),
    "reportes":             ("report", "reports"),
    "reporte diario":       ("daily report",),
    "reportes diarios":     ("daily report", "daily reports"),
    "reunion":              ("meeting",),
    "reuniones":            ("meeting", "meetings"),
    "reunion de seguridad": ("safety meeting", "toolbox"),
    "tailgate":             ("toolbox", "huddle"),
    "charla":               ("talk", "meeting"),
    "inspeccion":           ("inspection",),
    "inspecciones":         ("inspection", "inspections"),
    # Trench / excavation
    "zanja":                ("trench",),
    "zanjas":               ("trench", "trenches"),
    "excavacion":           ("excavation",),
    "excavaciones":         ("excavation", "excavations"),
    "caja de zanja":        ("trench box",),
    "placa":                ("plate", "road plate"),
    "placas":               ("plate", "road plate"),
    # Workforce
    "equipo":               ("equipment", "crew"),
    "equipos":              ("equipment", "crews"),
    "cuadrilla":            ("crew",),
    "capataz":              ("foreman",),
    "supervisor":           ("supervisor", "superintendent"),
    "superintendente":      ("superintendent",),
    "empleado":             ("employee",),
    "empleados":            ("employee", "employees"),
    "conductor":            ("driver",),
    "operador":             ("operator",),
    # HR / requests
    "solicitud":            ("request",),
    "solicitudes":          ("request", "requests"),
    "tiempo libre":         ("time off",),
    "vacaciones":           ("time off", "vacation"),
    # Project / JHA
    "proyecto":             ("project",),
    "proyectos":            ("project", "projects"),
    "trabajo":              ("job",),
    "obra":                 ("project", "job"),
    "plan":                 ("plan",),
    "planes":               ("plan", "plans"),
    "peligro":              ("hazard",),
    "peligros":             ("hazard", "hazards"),
    # Acronyms — symmetric (JHA / JHP unchanged across languages)
    "jha":                  ("jha",),
    "jhp":                  ("jhp",),
    "atp":                  ("atp", "jha"),  # Analisis de Trabajo Peligroso
    # Equipment / fleet
    "vehiculo":             ("vehicle", "truck"),
    "camion":               ("truck",),
    "flota":                ("fleet",),
    "mantenimiento":        ("maintenance", "pm"),
    "reparacion":           ("repair",),
    "reparaciones":         ("repair", "repairs"),
    # Cross-portal records / actions / leadership / expirations
    # (TRACK 14.0-DISCOVERABILITY-FINALIZATION)
    "registro":             ("record",),
    "registros":            ("record", "records"),
    "registro diario":      ("daily record", "operational record"),
    "accion":               ("action",),
    "acciones":             ("action", "actions"),
    "liderazgo":            ("leadership",),
    "liderazgo de campo":   ("field leadership",),
    "vencimiento":          ("expiration", "expiry"),
    "vencimientos":         ("expiration", "expirations", "expiry"),
    "expiracion":           ("expiration", "expiry"),
    "expiraciones":         ("expiration", "expirations"),
    "certificacion":        ("certification",),
    "certificaciones":      ("certification", "certifications"),
    "entrenamiento":        ("training",),
    "capacitacion":         ("training",),
}

# Build a parallel EN → ES map so an English query also catches any
# Spanish-authored data (rare but possible in bilingual notes).
_EN_ES_SYNONYMS: Dict[str, tuple] = {}
for _es, _en_list in ES_EN_SYNONYMS.items():
    for _en in _en_list:
        _EN_ES_SYNONYMS[_en] = tuple(set(_EN_ES_SYNONYMS.get(_en, ()) + (_es,)))


def _normalize_for_lookup(s: str) -> str:
    """ASCII-fold accents and lowercase for synonym table lookup."""
    # Cheap, dependency-free folding for the small ES character set we
    # actually use (á é í ó ú ñ ü). Avoid pulling unicodedata for a 7-char
    # map.
    table = str.maketrans({
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
        "Ñ": "n", "Ü": "u",
    })
    return s.strip().lower().translate(table)


def _bilingual_regex(q: str) -> Dict[str, str]:
    """Build a regex that matches `q` PLUS any EN/ES synonym tokens.

    Single-term mapping only — we don't try to parse phrases; we look up
    the whole normalized query in the table, and if it has matches we
    OR them into the regex. The original `q` is always preserved, so
    behavior is strictly additive — a query that doesn't have synonyms
    behaves identically to `_safe_regex(q)`.
    """
    key = _normalize_for_lookup(q)
    alternates = list(ES_EN_SYNONYMS.get(key, ())) + list(_EN_ES_SYNONYMS.get(key, ()))
    if not alternates:
        return _safe_regex(q)
    # Escape each alternate and the original query
    escaped = [re.escape(q.strip())] + [re.escape(a) for a in alternates]
    # Dedup while preserving order
    seen, dedup = set(), []
    for tok in escaped:
        low = tok.lower()
        if low not in seen:
            seen.add(low)
            dedup.append(tok)
    return {"$regex": "|".join(dedup), "$options": "i"}


def _row(
    kind: str, doc: Dict[str, Any],
    title: str, subtitle: Optional[str] = None,
    url: Optional[str] = None, status: Optional[str] = None,
    badge: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "kind": kind,
        "id": doc.get("id") or doc.get("_id"),
        "title": (title or "").strip()[:160] or "—",
        "subtitle": (subtitle or "").strip()[:200] or None,
        "url": url,
        "status": status,
        "badge": badge,
    }


def build_global_search_router(db, require_any_portal_token) -> APIRouter:
    router = APIRouter(tags=["global-search"])

    def _role(a: Dict[str, Any]) -> str:
        return a.get("_actor") or a.get("role") or "admin"

    def _search_url_for_role(role: str, *, admin_url: str, pm_url: str, safety_url: Optional[str] = None, hr_url: Optional[str] = None, default_url: Optional[str] = None) -> str:
        if role == "admin":
            return admin_url
        if role == "hr" and hr_url:
            return hr_url
        if role == "safety" and safety_url:
            return safety_url
        if role == "pm":
            return pm_url
        return default_url or pm_url

    # ─── PROBES ───────────────────────────────────────────────────
    # Each probe is short, well-bounded, and returns (kind, [rows]).
    # Probes catch their own exceptions so one bad probe never breaks
    # the whole search.

    async def _probe(
        kind: str, limit: int,
        runner: Callable[[], Awaitable[List[Dict[str, Any]]]],
    ) -> Optional[Dict[str, Any]]:
        try:
            rows = await runner()
            if rows:
                return {
                    "kind": kind, "label": KIND_LABELS.get(kind, kind),
                    "rows": rows[:limit], "count": len(rows[:limit]),
                }
        except Exception as e:  # noqa: BLE001
            logger.warning("[search] probe %s failed: %s", kind, e)
        return None

    @router.get("/api/search")
    async def search(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        q: str = Query(..., min_length=2, max_length=80),
        kinds: Optional[str] = Query(default=None,
            description="CSV filter — restricts to a subset of kinds the actor already has access to."),
        limit: int = Query(default=6, ge=1, le=15),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="global_search.use",
            resource_type="global_search",
            resource={"id": "global-search", "project_number": ""},
            requested_context={"query": q[:80], "kinds": kinds or "", "limit": limit},
            request=request,
        )
        governed_actor = await build_governance_actor_context(db, actor)
        role = _role(governed_actor)
        visible = list(KIND_VISIBILITY.get(role, ()))
        if not visible:
            return {
                "q": q, "role": role, "scope": [],
                "groups": [], "total": 0,
            }

        # Apply optional kind filter (still cannot exceed visible)
        if kinds:
            requested = {k.strip() for k in kinds.split(",") if k.strip()}
            visible = [k for k in visible if k in requested]
            if not visible:
                return {
                    "q": q, "role": role, "scope": [],
                    "groups": [], "total": 0,
                }

        rx = _bilingual_regex(q)

        # PM scope (project numbers) — None means unrestricted.
        pm_proj: Optional[List[str]] = None
        if str(governed_actor.get("governance_scope_mode") or "") != "global":
            pm_proj = list(governed_actor.get("project_numbers") or [])

        # Leadership actor id (for own-records scoping). Field Leadership
        # has no user record, so we fall back to "leadership" role match.
        actor_id = governed_actor.get("canonical_user_id") or governed_actor.get("id")

        # ── Per-kind probe runners ─────────────────────────────────
        async def run_tasks() -> List[Dict[str, Any]]:
            clauses = [{"$or": [{"title": rx}, {"source_module": rx}, {"linked_record_id": rx}]}]
            scope: List[Dict[str, Any]] = []
            if str(governed_actor.get("governance_scope_mode") or "") != "global":
                scope.append({"$or": [
                    {"assignee_role": role},
                    {"assignee_role": None},
                    {"created_by.role": role},
                ]})
            # PM scope: restrict tasks to those linked to PM-scoped projects.
            # Without this, a PM could see tasks across projects via search.
            # (P1 audit finding — Iter B fix.)
            if role == "pm" and pm_proj is not None:
                scope.append({"linked_project_number": {"$in": pm_proj}})
            q_doc = {"$and": clauses + scope} if scope else clauses[0]
            rows = []
            async for d in db.tasks.find(q_doc, {"_id": 0}).limit(limit * 2):
                rows.append(_row(
                    "tasks", d,
                    title=d.get("title") or "—",
                    subtitle=f"{d.get('source_module') or 'task'} · {d.get('priority') or 'Medium'}",
                    url=f"/tasks?id={d.get('id')}",
                    status=d.get("status"),
                    badge=d.get("priority"),
                ))
            return rows

        async def run_notifications() -> List[Dict[str, Any]]:
            clauses = [{"$or": [{"title": rx}, {"body": rx}, {"type": rx}]}]
            scope: List[Dict[str, Any]] = []
            if str(governed_actor.get("governance_scope_mode") or "") != "global":
                scope.append({"$or": [
                    {"recipient_role": role},
                    {"recipient_role": None},
                ]})
            q_doc = {"$and": clauses + scope} if scope else clauses[0]
            rows = []
            async for d in db.notifications.find(q_doc, {"_id": 0}).sort("created_at", -1).limit(limit * 2):
                rows.append(_row(
                    "notifications", d,
                    title=d.get("title") or d.get("type") or "—",
                    subtitle=(d.get("body") or "")[:180],
                    url="/tasks",
                    status=d.get("severity"),
                    badge=d.get("type"),
                ))
            return rows

        async def run_employees() -> List[Dict[str, Any]]:
            # Track 14.0-UXS-11F · global search must resolve any of:
            # James / Michael / Fisher / Jimmy / James Fisher /
            # Jimmy Fisher / James Michael Fisher to the same record.
            from lib.synthetic_hr_filter import apply_synthetic_hr_exclusion  # noqa: PLC0415
            q_doc = apply_synthetic_hr_exclusion({"$or": [
                {"name": rx},
                {"first_name": rx}, {"last_name": rx},
                {"legal_first_name": rx},
                {"legal_middle_name": rx},
                {"legal_last_name": rx},
                {"preferred_name": rx},
                {"employee_id": rx}, {"email": rx},
            ]})
            rows = []
            async for d in db.employees.find(q_doc, {"_id": 0}).limit(limit * 2):
                full = format_employee_identity(d) or d.get("name") \
                    or " ".join(p for p in [d.get("first_name"), d.get("last_name")] if p)
                rows.append(_row(
                    "employees", d,
                    title=full or d.get("employee_id") or "—",
                    subtitle=" · ".join(p for p in [d.get("role") or d.get("title"), d.get("department")] if p) or None,
                    url=f"/hr/employees?id={d.get('id')}",
                    status=d.get("lifecycle_status") or ("Active" if d.get("is_active") else "Inactive"),
                ))
            return rows

        async def run_equipment() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"unit_number": rx}, {"make_model": rx},
                {"vin": rx}, {"serial_number": rx}, {"type": rx},
            ]}
            rows = []
            async for d in db.equipment_master.find(q_doc, {"_id": 0}).limit(limit * 2):
                title = d.get("unit_number") or d.get("make_model") or "—"
                subtitle = " · ".join(p for p in [d.get("make_model") if d.get("unit_number") else None, d.get("type"), d.get("status")] if p) or None
                rows.append(_row(
                    "equipment", d,
                    title=str(title),
                    subtitle=subtitle,
                    url=f"/admin/assets?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_projects() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"project_number": rx}, {"name": rx}, {"location": rx},
            ]}
            if pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.projects.find(q_doc, {"_id": 0}).limit(limit * 2):
                rows.append(_row(
                    "projects", d,
                    title=d.get("project_number") or d.get("name") or "—",
                    subtitle=" · ".join(p for p in [d.get("name") if d.get("project_number") else None, d.get("location")] if p) or None,
                    url=_search_url_for_role(role, admin_url=f"/admin/jobs?id={d.get('id')}", pm_url=f"/pm/job/{d.get('project_number')}", default_url=f"/admin/jobs?id={d.get('id') if role == 'admin' else d.get('project_number')}") if d.get("project_number") else f"/admin/jobs?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_po_requests() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"po_number": rx}, {"description": rx},
                {"vendor": rx}, {"project_number": rx},
            ]}
            scope: List[Dict[str, Any]] = []
            if role == "leadership":
                clauses = [{"requested_by_role": "leadership"}]
                if actor_id:
                    clauses.append({"requested_by_user_id": actor_id})
                scope.append({"$or": clauses})
            if role == "pm" and pm_proj is not None:
                scope.append({"project_number": {"$in": pm_proj}})
            final = {"$and": [q_doc] + scope} if scope else q_doc
            rows = []
            async for d in db.po_requests.find(final, {"_id": 0}).sort("created_at", -1).limit(limit * 2):
                rows.append(_row(
                    "po_requests", d,
                    title=d.get("po_number") or d.get("description") or "—",
                    subtitle=" · ".join(p for p in [d.get("vendor"), d.get("project_number")] if p) or None,
                    url=f"/po-requests?id={d.get('id')}",
                    status=d.get("status"),
                    badge=d.get("urgency"),
                ))
            return rows

        async def run_incidents() -> List[Dict[str, Any]]:
            from lib.synthetic_safety_filter import apply_synthetic_incident_exclusion  # noqa: PLC0415
            q_doc = apply_synthetic_incident_exclusion({"$or": [
                {"title": rx}, {"description": rx},
                {"incident_type": rx}, {"project_number": rx},
            ]})
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.incidents.find(q_doc, {"_id": 0}).sort("incident_date", -1).limit(limit * 2):
                rows.append(_row(
                    "incidents", d,
                    title=d.get("title") or d.get("incident_type") or "—",
                    subtitle=" · ".join(p for p in [d.get("project_number"), d.get("incident_date")] if p) or None,
                    url=f"/incidents/{d.get('id')}",
                    status=d.get("severity"),
                ))
            return rows

        async def run_corrective_actions() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"title": rx}, {"description": rx},
                {"project_number": rx}, {"assigned_to_name": rx},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.corrective_actions.find(q_doc, {"_id": 0}).sort("due_date", 1).limit(limit * 2):
                rows.append(_row(
                    "corrective_actions", d,
                    title=d.get("title") or "—",
                    subtitle=" · ".join(p for p in [d.get("project_number"), d.get("priority"), d.get("due_date")] if p) or None,
                    url=f"/safety-portal/corrective-actions?id={d.get('id')}",
                    status=d.get("status"),
                    badge=d.get("priority"),
                ))
            return rows

        async def run_fire_extinguishers() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"unit_id": rx}, {"location_label": rx},
                {"location_kind": rx}, {"serial_number": rx},
            ]}
            rows = []
            async for d in db.fire_extinguishers.find(q_doc, {"_id": 0}).limit(limit * 2):
                rows.append(_row(
                    "fire_extinguishers", d,
                    title=d.get("unit_id") or "—",
                    subtitle=" · ".join(p for p in [d.get("location_label"), d.get("location_kind")] if p) or None,
                    url=f"/safety-portal/fire-extinguishers?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_safety_documents() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"title": rx}, {"category": rx},
                {"filename": rx},
            ]}
            rows = []
            async for d in db.safety_documents.find(q_doc, {"_id": 0}).sort("uploaded_at", -1).limit(limit * 2):
                rows.append(_row(
                    "safety_documents", d,
                    title=d.get("title") or d.get("filename") or "—",
                    subtitle=d.get("category"),
                    url=f"/safety-portal/documents?id={d.get('id')}",
                ))
            return rows

        async def run_safety_training() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"track": rx}, {"employee_name": rx},
                {"course_name": rx}, {"certificate_number": rx},
            ]}
            rows = []
            async for d in db.safety_training_records.find(q_doc, {"_id": 0}).sort("expiration_date", 1).limit(limit * 2):
                rows.append(_row(
                    "safety_training", d,
                    title=d.get("track") or d.get("course_name") or "—",
                    subtitle=" · ".join(p for p in [d.get("employee_name"), d.get("expiration_date")] if p) or None,
                    url=f"/safety-portal/training?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_document_expirations() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"document_type": rx}, {"description": rx},
                {"linked_employee_name": rx}, {"linked_equipment_unit": rx},
                {"linked_project_number": rx},
            ]}
            rows = []
            async for d in db.document_expirations.find(q_doc, {"_id": 0}).sort("expiration_date", 1).limit(limit * 2):
                rows.append(_row(
                    "document_expirations", d,
                    title=d.get("document_type") or d.get("description") or "—",
                    subtitle=" · ".join(p for p in [d.get("linked_employee_name") or d.get("linked_equipment_unit") or d.get("linked_project_number"), d.get("expiration_date")] if p) or None,
                    url=f"/document-expirations?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_operations_events() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"event_type": rx}, {"summary": rx},
                {"asset_id": rx}, {"employee_id": rx},
            ]}
            rows = []
            async for d in db.operations_events.find(q_doc, {"_id": 0}).sort("occurred_at", -1).limit(limit * 2):
                rows.append(_row(
                    "operations_events", d,
                    title=d.get("event_type") or d.get("summary") or "—",
                    subtitle=" · ".join(p for p in [d.get("asset_id"), d.get("employee_id")] if p) or None,
                    url=f"/admin/operations-events?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_field_leadership() -> List[Dict[str, Any]]:
            """Wave B — searchable FL records.

            TRACK 28.03 · Synthetic / certification / smoke FL records
            are excluded from global search — same doctrine as
            ``run_daily_reports`` (Cmd+K search is user-facing on
            every portal).
            """
            q_doc = {"$or": [
                {"kind": rx}, {"employee_name": rx},
                {"project_number": rx}, {"notes": rx},
            ]}
            scope: List[Dict[str, Any]] = []
            if role == "pm" and pm_proj is not None:
                scope.append({"project_number": {"$in": pm_proj}})
            base = {"$and": [q_doc] + scope} if scope else q_doc
            final = apply_synthetic_flr_exclusion(base)
            rows = []
            async for d in db.field_leadership_records.find(final, {"_id": 0}).sort("occurred_at", -1).limit(limit * 2):
                rows.append(_row(
                    "field_leadership", d,
                    title=d.get("kind") or "Field Leadership Record",
                    subtitle=" · ".join(p for p in [d.get("employee_name"), d.get("project_number")] if p) or None,
                    url=f"/leadership/records/{d.get('id')}",
                ))
            return rows

        async def run_staffing() -> List[Dict[str, Any]]:
            """Track 14.0-PM-STAFFING-UI-DISCOVERABILITY: search project
            team assignments by display_name, email, role label, or
            project_number. Honors PM scope. Returns deep-links to the
            project Team page."""
            q_doc = {"$and": [
                {"$or": [
                    {"display_name": rx},
                    {"email": rx},
                    {"assignment_role": rx},
                    {"role_label": rx},
                    {"project_number": rx},
                ]},
                {"active": True},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc["$and"].append({"project_number": {"$in": pm_proj}})
            rows = []
            async for d in db.project_team_assignments.find(q_doc, {"_id": 0}).limit(limit * 2):
                pn = d.get("project_number") or "—"
                # Apply same role label as project_team_assignments service
                try:
                    from routes.project_team_assignments import (  # noqa: PLC0415
                        ROLE_REGISTRY as _PTA_ROLES,
                    )
                    role_label = _PTA_ROLES.get(d.get("assignment_role"), d.get("assignment_role"))
                except Exception:
                    role_label = d.get("role_label") or d.get("assignment_role")
                rows.append(_row(
                    "staffing", d,
                    title=f"{d.get('display_name') or d.get('email') or '—'} · {role_label}",
                    subtitle=f"Project {pn}"
                    + (" · primary" if d.get("is_primary") else ""),
                    url=_search_url_for_role(role, admin_url=f"/admin/jobs/{pn}/team", pm_url=f"/pm/job/{pn}/team", default_url=f"/admin/jobs/{pn}/team"),
                    status="active" if d.get("active") else "inactive",
                    badge=d.get("assignment_role"),
                ))
            return rows

        async def run_daily_reports() -> List[Dict[str, Any]]:
            """Wave B — searchable daily reports. Project-scoped for PMs.

            TRACK 28.02B · Synthetic / certification / smoke rows are
            excluded from global search per the TRACK 24.9 doctrine
            (synthetic rows must never appear on user-facing screens —
            Cmd+K search is user-facing on every portal).
            """
            q_doc = {"$or": [
                {"report_number": rx}, {"project_name": rx},
                {"project_number": rx}, {"location": rx},
                {"prepared_by": rx}, {"weather_summary": rx},
            ]}
            scope: List[Dict[str, Any]] = []
            if role == "pm" and pm_proj is not None:
                scope.append({"project_number": {"$in": pm_proj}})
            base_q = {"$and": [q_doc] + scope} if scope else q_doc
            final = apply_synthetic_dr_exclusion(base_q)
            rows = []
            async for d in db.daily_reports.find(final, {"_id": 0}).sort("created_at", -1).limit(limit * 2):
                rows.append(_row(
                    "daily_reports", d,
                    title=d.get("report_number") or d.get("project_name") or "Daily Report",
                    subtitle=" · ".join(p for p in [
                        d.get("project_number"), d.get("report_date"), d.get("prepared_by"),
                    ] if p) or None,
                    url=_search_url_for_role(role, admin_url=f"/admin/daily/{d.get('id')}", pm_url=f"/pm/daily/{d.get('id')}", hr_url=f"/hr/daily-reports/{d.get('id')}", default_url=f"/pm/daily/{d.get('id')}"),
                    status=d.get("status"),
                ))
            return rows

        async def run_meetings() -> List[Dict[str, Any]]:
            """Wave B — searchable safety meetings. PM-scoped."""
            q_doc = {"$or": [
                {"topic": rx}, {"topic_category": rx},
                {"project_name": rx}, {"project_number": rx},
                {"location": rx}, {"conducted_by": rx},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.meetings.find(q_doc, {"_id": 0}).sort("meeting_date", -1).limit(limit * 2):
                rows.append(_row(
                    "meetings", d,
                    title=d.get("topic") or d.get("topic_category") or "Safety Meeting",
                    subtitle=" · ".join(p for p in [
                        d.get("project_name") or d.get("project_number"),
                        d.get("meeting_date"), d.get("conducted_by"),
                    ] if p) or None,
                    url=_search_url_for_role(role, admin_url=f"/admin/meetings/{d.get('id')}", pm_url=f"/pm/meetings/{d.get('id')}", safety_url=f"/safety-portal/meetings/{d.get('id')}", default_url=f"/pm/meetings/{d.get('id')}"),
                ))
            return rows

        async def run_inspections() -> List[Dict[str, Any]]:
            """Wave B — searchable site inspections. PM-scoped."""
            q_doc = {"$or": [
                {"inspection_number": rx}, {"project_name": rx},
                {"project_number": rx}, {"location": rx},
                {"inspector_name": rx}, {"inspection_type": rx},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.inspections.find(q_doc, {"_id": 0}).sort("inspection_date", -1).limit(limit * 2):
                rows.append(_row(
                    "inspections", d,
                    title=d.get("inspection_number") or d.get("inspection_type") or "Site Inspection",
                    subtitle=" · ".join(p for p in [
                        d.get("project_name") or d.get("project_number"),
                        d.get("inspection_date"), d.get("inspector_name"),
                    ] if p) or None,
                    url=_search_url_for_role(role, admin_url=f"/admin/inspections/{d.get('id')}", pm_url=f"/pm/inspections/{d.get('id')}", safety_url=f"/safety-portal/inspections/{d.get('id')}", default_url=f"/pm/inspections/{d.get('id')}"),
                ))
            return rows

        async def run_trench_assets() -> List[Dict[str, Any]]:
            """Wave B — searchable Trench Safety assets (boxes, plates, shores).
            Public Trench Safety dashboard is no-auth, so role-gating is
            relaxed — Admin / Safety / PM / Shop all need to find an
            asset by ID, type, model, or serial. No PM-scoping (assets
            move across projects)."""
            q_doc = {"$or": [
                {"asset_id": rx}, {"asset_type": rx},
                {"model": rx}, {"serial_number": rx},
                {"manufacturer": rx},
            ]}
            rows = []
            async for d in db.trench_safety_assets.find(q_doc, {"_id": 0}).sort("asset_id", 1).limit(limit * 2):
                aid = d.get("asset_id") or "—"
                rows.append(_row(
                    "trench_assets", d,
                    title=f"{aid} · {d.get('asset_type') or 'Trench Asset'}",
                    subtitle=" · ".join(p for p in [
                        d.get("model"), d.get("manufacturer"),
                        d.get("operational_status"),
                    ] if p) or None,
                    url=_search_url_for_role(role, admin_url=f"/admin/trench-safety/assets/{aid}", pm_url=f"/trench-safety/assets/{aid}", safety_url=f"/safety/trench-safety/assets/{aid}", default_url=f"/trench-safety/assets/{aid}"),
                    status=d.get("operational_status"),
                    badge=d.get("asset_type"),
                ))
            return rows

        async def run_jha_plans() -> List[Dict[str, Any]]:
            """Wave B — searchable JHA / JHP plans. PM-scoped."""
            q_doc = {"$or": [
                {"jha_number": rx}, {"job_title": rx},
                {"title": rx}, {"project_name": rx},
                {"project_number": rx}, {"prepared_by": rx},
                {"crew_lead": rx}, {"location": rx},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.jhas.find(q_doc, {"_id": 0}).sort("jha_date", -1).limit(limit * 2):
                rows.append(_row(
                    "jha_plans", d,
                    title=d.get("job_title") or d.get("jha_number") or d.get("title") or "JHA",
                    subtitle=" · ".join(p for p in [
                        d.get("project_name") or d.get("project_number"),
                        d.get("jha_date"), d.get("crew_lead") or d.get("prepared_by"),
                    ] if p) or None,
                    url=_search_url_for_role(role, admin_url=f"/admin/jha-plans?focus={d.get('id')}", pm_url=f"/admin/jha-plans?focus={d.get('id')}", safety_url=f"/safety-portal/jha-plans?focus={d.get('id')}", default_url="/jha"),
                ))
            return rows

        runners: Dict[str, Callable[[], Awaitable[List[Dict[str, Any]]]]] = {
            "tasks": run_tasks,
            "notifications": run_notifications,
            "employees": run_employees,
            "equipment": run_equipment,
            "projects": run_projects,
            "po_requests": run_po_requests,
            "incidents": run_incidents,
            "corrective_actions": run_corrective_actions,
            "fire_extinguishers": run_fire_extinguishers,
            "safety_documents": run_safety_documents,
            "safety_training": run_safety_training,
            "document_expirations": run_document_expirations,
            "operations_events": run_operations_events,
            "field_leadership": run_field_leadership,
            "staffing": run_staffing,
            "daily_reports": run_daily_reports,
            "meetings": run_meetings,
            "inspections": run_inspections,
            "trench_assets": run_trench_assets,
            "jha_plans": run_jha_plans,
        }

        coros = [_probe(k, limit, runners[k]) for k in visible if k in runners]
        results = await asyncio.gather(*coros, return_exceptions=False)
        groups = [r for r in results if r]

        return {
            "q": q,
            "role": role,
            "scope": list(visible),
            "groups": groups,
            "total": sum(g["count"] for g in groups),
        }

    return router


__all__ = [
    "build_global_search_router",
    "ALL_KINDS",
    "KIND_LABELS",
    "KIND_VISIBILITY",
]
