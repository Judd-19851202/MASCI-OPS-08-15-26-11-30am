"""TRACK 16.15 · Operational Cleanup Companion.

Turns existing Track 16.12 intelligence + Track 16.14 learning signals
into focused action lists. NEVER introduces new scoring. Source data
is read-only; only ``transport_action_items`` may be created (one row
per affected entity + signal, deduped by ``event_key``).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TENANT = "masci"
SCHEMA_VERSION = "16.15.0"
DEFAULT_DAYS = 30
MAX_DAYS = 365


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse(v: Any) -> Optional[datetime]:
    if not isinstance(v, str) or len(v) < 10:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Canonical signal catalog. Each entry maps to an existing data source.
# No new scoring; all severities + labels are static metadata.
# ---------------------------------------------------------------------------
SIGNAL_CATALOG: Dict[str, Dict[str, Any]] = {
    "insurance_expiring_soon": {
        "title": "Insurance expires soon",
        "description": "Carrier insurance documents approaching expiration.",
        "severity": "action_required",
        "source": "transport_operations_intelligence",
        "entity_types": ["carrier"],
        "recommended_action": (
            "Review affected carriers and request updated insurance "
            "certificates."),
        "action_type": "cleanup_insurance_expiring",
    },
    "inspection_overdue": {
        "title": "Inspection overdue",
        "description": "Truck inspections past due or expired.",
        "severity": "action_required",
        "source": "transport_operations_intelligence",
        "entity_types": ["truck"],
        "recommended_action": (
            "Schedule a fresh MASCI Hauler Readiness Inspection."),
        "action_type": "cleanup_inspection_overdue",
    },
    "orientation_expiring": {
        "title": "Orientation expiring",
        "description": "Driver orientation certificates approaching expiry.",
        "severity": "watch",
        "source": "transport_operations_intelligence",
        "entity_types": ["driver"],
        "recommended_action": "Refresh annual orientation.",
        "action_type": "cleanup_orientation_expiring",
    },
    "orientation_incomplete": {
        "title": "Orientation incomplete",
        "description": "Driver has no current orientation certificate.",
        "severity": "action_required",
        "source": "transport_operations_intelligence",
        "entity_types": ["driver"],
        "recommended_action": "Complete driver orientation modules.",
        "action_type": "cleanup_orientation_incomplete",
    },
    "missing_driver_docs": {
        "title": "Driver documents missing or expired",
        "description": "Driver documents past expiry.",
        "severity": "action_required",
        "source": "transport_operations_intelligence",
        "entity_types": ["driver"],
        "recommended_action": "Renew expired driver documents.",
        "action_type": "cleanup_document_gap",
    },
    "packet_needs_correction": {
        "title": "Carrier packet needs correction",
        "description": "Carrier packet is not in approved status.",
        "severity": "action_required",
        "source": "transport_operations_intelligence",
        "entity_types": ["carrier"],
        "recommended_action": "Approve carrier packet via Transportation admin.",
        "action_type": "cleanup_packet_needs_correction",
    },
    "hr_sync_mismatch": {
        "title": "HR sync mismatch",
        "description": "Driver projection out of sync with HR lifecycle.",
        "severity": "action_required",
        "source": "transport_sync_monitor",
        "entity_types": ["driver"],
        "recommended_action": (
            "Re-sync HR projection or update Transportation linkage."),
        "action_type": "cleanup_hr_sync_mismatch",
    },
    "route_needs_configuration": {
        "title": "Email routes need configuration",
        "description": "Email route keys flagged needs_configuration.",
        "severity": "watch",
        "source": "transport_automation",
        "entity_types": ["email_route"],
        "recommended_action": "Configure recipients for needs-configuration routes.",
        "action_type": "cleanup_route_needs_configuration",
    },
    "truck_readiness_gap": {
        "title": "Truck readiness gap",
        "description": "Trucks with inspection issues or safety holds.",
        "severity": "action_required",
        "source": "transport_operations_intelligence",
        "entity_types": ["truck"],
        "recommended_action": "Resolve inspection findings or safety hold.",
        "action_type": "cleanup_truck_readiness_gap",
    },
    "carrier_document_gap": {
        "title": "Carrier document gap",
        "description": "Carriers with stale or missing required documents.",
        "severity": "watch",
        "source": "transport_operations_intelligence",
        "entity_types": ["carrier"],
        "recommended_action": "Request updated carrier documentation.",
        "action_type": "cleanup_carrier_document_gap",
    },
    "repeated_watch_item": {
        "title": "Repeated recommendation watch item",
        "description": (
            "Same watch label appears across multiple recommendations."),
        "severity": "watch",
        "source": "transport_dispatch_learning",
        "entity_types": ["watch_label"],
        "recommended_action": (
            "Target the underlying record(s) producing the watch item."),
        "action_type": "cleanup_repeated_watch_item",
    },
    "frequent_excluded_reason": {
        "title": "Frequent excluded reason",
        "description": "Same reason excludes many entities from dispatch.",
        "severity": "watch",
        "source": "transport_dispatch_learning",
        "entity_types": ["excluded_reason"],
        "recommended_action": (
            "Address the underlying compliance gap producing the reason."),
        "action_type": "cleanup_frequent_excluded_reason",
    },
}


# ---------------------------------------------------------------------------
# Signal-specific affected-record loaders (read-only).
# ---------------------------------------------------------------------------
async def _affected_from_documents(db, *, kind: str
                                    ) -> List[Dict[str, Any]]:
    """Driver documents expired / expiring soon."""
    rows = await db.driver_documents.find({"tenant": TENANT}).to_list(2000)
    out: List[Dict[str, Any]] = []
    now = _now()
    for d in rows:
        exp = _parse(d.get("expires_at"))
        if not exp:
            continue
        days = int((exp - now).total_seconds() // 86400)
        if kind == "missing_driver_docs" and days < 0:
            out.append({
                "entity_type": "driver_document",
                "entity_id": d.get("id"),
                "display_name": d.get("document_type") or d.get("name") or d.get("id"),
                "current_state": "expired",
                "reason": "Document expired",
                "due_date": d.get("expires_at"),
                "severity": "action_required",
                "direct_link": (
                    "/admin/transportation/drivers/"
                    f"{d.get('transport_person_id')}"),
                "transport_person_id": d.get("transport_person_id"),
            })
    return out


async def _affected_insurance(db) -> List[Dict[str, Any]]:
    """Carrier insurance-style documents nearing expiry."""
    rows = await db.driver_documents.find({"tenant": TENANT}).to_list(2000)
    out: List[Dict[str, Any]] = []
    now = _now()
    for d in rows:
        if "insurance" not in (d.get("document_type") or "").lower():
            continue
        exp = _parse(d.get("expires_at"))
        if not exp:
            continue
        days = int((exp - now).total_seconds() // 86400)
        if 0 <= days <= 30:
            out.append({
                "entity_type": "driver_document",
                "entity_id": d.get("id"),
                "display_name": d.get("document_type") or "Insurance certificate",
                "current_state": f"expires_in_{days}_days",
                "reason": f"Insurance expires in {days} day(s)",
                "due_date": d.get("expires_at"),
                "severity": "action_required",
                "direct_link": (
                    "/admin/transportation/drivers/"
                    f"{d.get('transport_person_id')}"),
                "transport_person_id": d.get("transport_person_id"),
            })
    return out


async def _affected_orientation(db, *, kind: str) -> List[Dict[str, Any]]:
    """Drivers with expiring or missing orientation certificates."""
    out: List[Dict[str, Any]] = []
    persons = await db.transport_persons.find(
        {"tenant": TENANT}).to_list(2000)
    now = _now()
    for p in persons:
        cert = await db.transport_certificates.find_one({
            "tenant": TENANT, "transport_person_id": p["id"]},
            sort=[("issued_at", -1)])
        if kind == "orientation_incomplete":
            if not cert:
                out.append({
                    "entity_type": "driver",
                    "entity_id": p.get("id"),
                    "display_name": (
                        f"{p.get('first_name','')} "
                        f"{p.get('last_name','')}").strip() or p.get("id"),
                    "current_state": "no_certificate",
                    "reason": "No orientation certificate on file",
                    "due_date": None,
                    "severity": "action_required",
                    "direct_link": f"/admin/transportation/drivers/{p['id']}",
                })
            continue
        # orientation_expiring
        if not cert:
            continue
        exp = _parse(cert.get("expires_at"))
        if not exp:
            continue
        days = int((exp - now).total_seconds() // 86400)
        if 0 <= days <= 60:
            out.append({
                "entity_type": "driver",
                "entity_id": p.get("id"),
                "display_name": (
                    f"{p.get('first_name','')} "
                    f"{p.get('last_name','')}").strip() or p.get("id"),
                "current_state": f"expires_in_{days}_days",
                "reason": f"Orientation expires in {days} day(s)",
                "due_date": cert.get("expires_at"),
                "severity": "watch",
                "direct_link": f"/admin/transportation/drivers/{p['id']}",
            })
    return out


async def _affected_inspections(db) -> List[Dict[str, Any]]:
    """Trucks with overdue inspections."""
    out: List[Dict[str, Any]] = []
    trucks = await db.transport_trucks.find(
        {"tenant": TENANT}).to_list(2000)
    now = _now()
    for t in trucks:
        ins = await db.transport_truck_inspections.find_one({
            "tenant": TENANT, "transport_truck_id": t["id"]},
            sort=[("inspected_at", -1)])
        result = (ins or {}).get("result")
        days_since = None
        if ins:
            insd = _parse(ins.get("inspected_at"))
            if insd:
                days_since = int((now - insd).days)
        if not ins or result == "not_ready" or (
            days_since is not None and days_since >= 180
        ):
            out.append({
                "entity_type": "truck",
                "entity_id": t.get("id"),
                "display_name": t.get("truck_number") or t.get("id"),
                "current_state": result or "missing",
                "reason": (
                    "No inspection on file" if not ins
                    else ("Inspection result: not ready"
                          if result == "not_ready"
                          else f"Last inspected {days_since} days ago")),
                "due_date": (ins or {}).get("inspected_at"),
                "severity": "action_required",
                "direct_link": f"/admin/transportation/trucks/{t['id']}",
            })
    return out


async def _affected_packets(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    carriers = await db.carriers.find({"tenant": TENANT}).to_list(2000)
    for c in carriers:
        pkt = await db.transport_carrier_packets.find_one(
            {"tenant": TENANT, "carrier_id": c["id"]})
        status = (pkt or {}).get("status")
        if status != "approved":
            out.append({
                "entity_type": "carrier",
                "entity_id": c.get("id"),
                "display_name": c.get("legal_name") or c.get("id"),
                "current_state": status or "missing",
                "reason": f"Carrier packet status: {status or 'missing'}",
                "due_date": None,
                "severity": "action_required",
                "direct_link": f"/admin/transportation/carriers/{c['id']}",
            })
    return out


async def _affected_hr_sync(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    persons = await db.transport_persons.find(
        {"tenant": TENANT, "kind": "masci_employee"}).to_list(2000)
    for p in persons:
        proj = (p.get("hr_projection") or {})
        state = proj.get("transport_state")
        if state in ("not_dispatchable", "needs_correction", "suspended"):
            out.append({
                "entity_type": "driver",
                "entity_id": p.get("id"),
                "display_name": (
                    f"{p.get('first_name','')} "
                    f"{p.get('last_name','')}").strip() or p.get("id"),
                "current_state": state,
                "reason": ", ".join(proj.get("reason_labels") or [])[:240]
                           or "HR projection mismatch",
                "due_date": proj.get("synced_at"),
                "severity": "action_required",
                "direct_link": f"/admin/transportation/drivers/{p['id']}",
            })
    return out


async def _affected_truck_readiness(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    elig = await db.transport_eligibility_state.find({
        "tenant": TENANT, "target_type": "truck",
        "state": {"$in": ["not_dispatchable", "suspended",
                            "needs_correction", "expired"]}}).to_list(2000)
    for e in elig:
        truck = await db.transport_trucks.find_one(
            {"tenant": TENANT, "id": e.get("target_id")})
        if not truck:
            continue
        out.append({
            "entity_type": "truck",
            "entity_id": truck.get("id"),
            "display_name": truck.get("truck_number") or truck.get("id"),
            "current_state": e.get("state"),
            "reason": ", ".join(
                r.get("label") or r.get("code") or ""
                for r in (e.get("reasons") or [])[:3])[:240] or "Eligibility blocked",
            "due_date": None,
            "severity": "action_required",
            "direct_link": f"/admin/transportation/trucks/{truck['id']}",
        })
    return out


async def _affected_carrier_documents(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    elig = await db.transport_eligibility_state.find({
        "tenant": TENANT, "target_type": "carrier",
        "state": {"$in": ["needs_correction", "expired"]}}).to_list(2000)
    for e in elig:
        carrier = await db.carriers.find_one(
            {"tenant": TENANT, "id": e.get("target_id")})
        if not carrier:
            continue
        out.append({
            "entity_type": "carrier",
            "entity_id": carrier.get("id"),
            "display_name": carrier.get("legal_name") or carrier.get("id"),
            "current_state": e.get("state"),
            "reason": ", ".join(
                r.get("label") or r.get("code") or ""
                for r in (e.get("reasons") or [])[:3])[:240]
                or "Carrier documentation gap",
            "due_date": None,
            "severity": "watch",
            "direct_link": f"/admin/transportation/carriers/{carrier['id']}",
        })
    return out


async def _affected_route_config(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        rows = await db.email_routes.find(
            {"tenant": TENANT}).to_list(500)
    except Exception:  # noqa: BLE001
        rows = []
    for r in rows:
        if r.get("status") == "needs_configuration":
            out.append({
                "entity_type": "email_route",
                "entity_id": r.get("route_key"),
                "display_name": r.get("display_name") or r.get("route_key"),
                "current_state": "needs_configuration",
                "reason": "Email route is missing recipients",
                "due_date": None,
                "severity": "watch",
                "direct_link": "/admin/transportation/command-queue",
            })
    return out


async def _affected_learning(db, *, signal_key: str, days: int
                              ) -> List[Dict[str, Any]]:
    """For learning-derived signals, treat each repeated watch label /
    excluded reason as an affected 'entity' itself."""
    out: List[Dict[str, Any]] = []
    try:
        if signal_key == "repeated_watch_item":
            from lib.transport_dispatch_learning import build_common_watch_items
            data = await build_common_watch_items(db, days=days)
            for p in (data.get("patterns") or [])[:10]:
                if p.get("count", 0) >= 3:
                    out.append({
                        "entity_type": "watch_label",
                        "entity_id": p["label"][:120],
                        "display_name": p["label"],
                        "current_state": "recurring",
                        "reason": f"Appeared in {p['count']} watch lists",
                        "due_date": None,
                        "severity": "watch",
                        "direct_link": "/admin/transportation/intelligence/learning",
                    })
        elif signal_key == "frequent_excluded_reason":
            from lib.transport_dispatch_learning import (
                build_excluded_reason_patterns,
            )
            data = await build_excluded_reason_patterns(db, days=days)
            for p in (data.get("patterns") or [])[:10]:
                if p.get("count", 0) >= 3:
                    out.append({
                        "entity_type": "excluded_reason",
                        "entity_id": p["label"][:120],
                        "display_name": p["label"],
                        "current_state": "recurring",
                        "reason": f"Excluded {p['count']} entities",
                        "due_date": None,
                        "severity": "watch",
                        "direct_link": "/admin/transportation/intelligence/learning",
                    })
    except Exception:  # noqa: BLE001
        pass
    return out


_AFFECTED_LOADERS = {
    "insurance_expiring_soon": lambda db, days: _affected_insurance(db),
    "inspection_overdue": lambda db, days: _affected_inspections(db),
    "orientation_expiring": lambda db, days: _affected_orientation(
        db, kind="orientation_expiring"),
    "orientation_incomplete": lambda db, days: _affected_orientation(
        db, kind="orientation_incomplete"),
    "missing_driver_docs": lambda db, days: _affected_from_documents(
        db, kind="missing_driver_docs"),
    "packet_needs_correction": lambda db, days: _affected_packets(db),
    "hr_sync_mismatch": lambda db, days: _affected_hr_sync(db),
    "route_needs_configuration": lambda db, days: _affected_route_config(db),
    "truck_readiness_gap": lambda db, days: _affected_truck_readiness(db),
    "carrier_document_gap": lambda db, days: _affected_carrier_documents(db),
    "repeated_watch_item": lambda db, days: _affected_learning(
        db, signal_key="repeated_watch_item", days=days),
    "frequent_excluded_reason": lambda db, days: _affected_learning(
        db, signal_key="frequent_excluded_reason", days=days),
}


def _signal_dict(key: str, *, count: int) -> Dict[str, Any]:
    meta = SIGNAL_CATALOG[key]
    return {
        "signal_key": key,
        "title": meta["title"],
        "description": meta["description"],
        "severity": meta["severity"],
        "affected_count": count,
        "source": meta["source"],
        "source_count": count,  # 1:1 — every affected record is a source count
        "recommended_action": meta["recommended_action"],
        "entity_types": meta["entity_types"],
        "action_type": meta["action_type"],
        "first_seen_at": None,
        "last_seen_at": _now_iso(),
        "schema_version": SCHEMA_VERSION,
    }


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------
async def build_cleanup_signals(
    db, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    days = max(1, min(int(days), MAX_DAYS))
    signals: List[Dict[str, Any]] = []
    for key in SIGNAL_CATALOG:
        try:
            items = await _AFFECTED_LOADERS[key](db, days)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cleanup signal %s loader failed: %s", key, exc)
            items = []
        if items:
            signals.append(_signal_dict(key, count=len(items)))
    # Sort: action_required first, then by affected_count desc.
    signals.sort(key=lambda s: (
        0 if s["severity"] == "action_required" else 1,
        -s["affected_count"],
    ))
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "range": {"days": days},
        "signals": signals,
        "note": ("No additional scoring is performed — all signals are "
                  "derived from existing intelligence data."),
    }


async def build_cleanup_signal_detail(
    db, signal_key: str, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    if signal_key not in SIGNAL_CATALOG:
        return {"ok": False, "error": "unknown_signal",
                "schema_version": SCHEMA_VERSION,
                "generated_at": _now_iso()}
    days = max(1, min(int(days), MAX_DAYS))
    items = await _AFFECTED_LOADERS[signal_key](db, days)
    # Annotate with any existing action items.
    action_type = SIGNAL_CATALOG[signal_key]["action_type"]
    annotated: List[Dict[str, Any]] = []
    for it in items:
        ev_key = _event_key(signal_key, it.get("entity_id"))
        ai = await db.transport_action_items.find_one({
            "tenant": TENANT, "related_event_key": ev_key,
            "status": {"$in": ["open", "in_progress"]}})
        annotated.append({
            **it,
            "recommended_action": SIGNAL_CATALOG[signal_key]["recommended_action"],
            "existing_action_item_id": (ai or {}).get("id"),
            "action_status": (ai or {}).get("status"),
            "last_activity_at": (ai or {}).get("updated_at"),
        })
    meta = _signal_dict(signal_key, count=len(items))
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "signal": meta,
        "affected": annotated,
        "action_type": action_type,
    }


def _event_key(signal_key: str, entity_id: Optional[str]) -> str:
    return f"cleanup::{signal_key}::{entity_id or 'unknown'}"


async def materialize_cleanup_actions(
    db, signal_key: str, *, actor: Optional[str] = None,
    days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    if signal_key not in SIGNAL_CATALOG:
        return {"ok": False, "error": "unknown_signal",
                "schema_version": SCHEMA_VERSION,
                "generated_at": _now_iso()}
    meta = SIGNAL_CATALOG[signal_key]
    items = await _AFFECTED_LOADERS[signal_key](db, days)
    created = 0
    skipped = 0
    existing_total = 0
    now = _now_iso()
    for it in items:
        ev_key = _event_key(signal_key, it.get("entity_id"))
        ai = await db.transport_action_items.find_one({
            "tenant": TENANT, "related_event_key": ev_key,
            "status": {"$in": ["open", "in_progress"]}})
        if ai:
            existing_total += 1
            skipped += 1
            continue
        try:
            await db.transport_action_items.insert_one({
                "id": uuid.uuid4().hex,
                "tenant": TENANT,
                "source": "intelligence_cleanup",
                "action_type": meta["action_type"],
                "severity": meta["severity"],
                "entity_type": it.get("entity_type"),
                "entity_id": it.get("entity_id"),
                "title": meta["title"],
                "description": it.get("reason") or meta["description"],
                "recommended_action": meta["recommended_action"],
                "direct_link": it.get("direct_link"),
                "due_date": it.get("due_date"),
                "status": "open",
                "assigned_role": "transportation_admin",
                "assigned_user_id": None,
                "related_route_key": "TRANSPORT_CLEANUP_COMPANION",
                "related_event_key": ev_key,
                "related_signal_key": signal_key,
                "created_at": now, "updated_at": now,
                "resolved_at": None, "resolved_by": None,
            })
            created += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("cleanup materialize insert failed: %s", exc)
    # Audit.
    try:
        await db.transport_intelligence_audit.insert_one({
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": "transport_cleanup_actions_materialized",
            "subject_type": "cleanup_signal",
            "subject_id": signal_key,
            "actor": actor or "admin",
            "schema_version": SCHEMA_VERSION,
            "ts": now,
            "snapshot": {"signal_key": signal_key,
                          "created": created, "skipped": skipped,
                          "existing": existing_total,
                          "affected": len(items)},
        })
    except Exception:  # noqa: BLE001
        pass
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "generated_at": now,
        "signal_key": signal_key,
        "created": created,
        "skipped_duplicates": skipped,
        "existing_action_count": existing_total,
        "affected_total": len(items),
        "last_materialized_at": now,
    }


# ---------------------------------------------------------------------------
# View audit helpers
# ---------------------------------------------------------------------------
async def record_cleanup_view(
    db, *, kind: str, signal_key: Optional[str] = None,
    viewer_role: str = "admin",
) -> None:
    """Lightweight view audit. Best-effort."""
    try:
        await db.transport_intelligence_audit.insert_one({
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": kind,
            "subject_type": "cleanup_signal",
            "subject_id": signal_key,
            "actor": viewer_role,
            "schema_version": SCHEMA_VERSION,
            "ts": _now_iso(),
        })
    except Exception:  # noqa: BLE001
        pass
