"""
Motive service · M-1 live implementation.

Reuses the existing integration framework verbatim:
  - `integration_settings` row holds credentials (api_key_value, webhook_secret_value, enabled)
  - `asset_mappings` collection hydrates vehicle + asset records
  - `employee_mappings` collection hydrates driver records
  - `motive_events` collection persists webhook + sync events
  - dispatch_lifecycle._record_transition() seam used for geofence events later
  - existing sync_logs / error_logs for observability
  - existing scheduler pattern (asyncio.create_task) for polling

NO new portal · NO new auth · NO new lifecycle · NO new fleet system.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

PROVIDER = "motive"
DEFAULT_API_BASE = "https://api.gomotive.com"
HTTP_TIMEOUT = 30.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class MotiveService:
    """Live Motive API client. All methods async."""

    def __init__(self, db, settings_doc: Optional[dict] = None):
        self.db = db
        self.settings = settings_doc or {}

    # ── Credential resolution ────────────────────────────────────────
    @property
    def api_key(self) -> str:
        # Prefer settings row (set via Admin Integration Center) and
        # fall back to env so the operator can paste once into the
        # Emergent dashboard if they prefer.
        return (
            (self.settings.get("api_key_value") or "").strip()
            or (os.environ.get("MOTIVE_API_KEY") or "").strip()
        )

    @property
    def api_base(self) -> str:
        return (
            (self.settings.get("api_base") or "").strip()
            or (os.environ.get("MOTIVE_API_BASE") or "").strip()
            or DEFAULT_API_BASE
        )

    @property
    def is_live(self) -> bool:
        # Provider considered live if a key is present. The
        # `enabled` flag on the settings row is the operator's master
        # switch; when False the framework short-circuits before
        # calling this service.
        if not self.api_key:
            return False
        if "enabled" in self.settings and not self.settings.get("enabled"):
            return False
        return True

    @property
    def is_demo(self) -> bool:
        return bool(self.settings.get("demo_mode"))

    # ── HTTP helper ──────────────────────────────────────────────────
    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_base.rstrip('/')}{path}"
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(url, headers=headers, params=params or {})
        if r.status_code >= 400:
            raise RuntimeError(f"Motive {r.status_code} {path}: {r.text[:240]}")
        return r.json()

    # ── 1. Test connection ───────────────────────────────────────────
    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_live:
            return {"ok": False, "status": "awaiting_credentials",
                    "message": "Motive credentials not configured yet."}
        try:
            data = await self._get("/v3/vehicle_locations", {"per_page": 1})
            count = len(data.get("vehicles", []))
            return {"ok": True, "status": "live",
                    "message": f"Motive live · vehicle_locations probe returned {count} row(s)."}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "status": "error", "message": str(e)[:240]}

    # ── 2. Sync assets (vehicles + Asset Gateway) ────────────────────
    async def sync_assets(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        if not self.is_live:
            return _awaiting("sync_assets")
        created, updated, errors = 0, 0, 0

        # 2a · Vehicles
        try:
            page = 1
            while True:
                data = await self._get("/v3/vehicle_locations",
                                       {"per_page": 100, "page_no": page})
                vehicles = data.get("vehicles", [])
                for wrap in vehicles:
                    v = wrap.get("vehicle") or {}
                    vid = str(v.get("id") or "").strip()
                    if not vid:
                        continue
                    loc = v.get("current_location") or {}
                    payload = {
                        "provider": PROVIDER,
                        "asset_kind": "vehicle",
                        "motive": {
                            "vehicle_id": vid,
                            "asset_id": None,
                            "driver_id": None,
                            "device_id": v.get("vehicle_gateway") and (v["vehicle_gateway"].get("serial") if isinstance(v.get("vehicle_gateway"), dict) else None),
                            "gps_enabled": bool(loc.get("lat")),
                            "dashcam_enabled": False,
                            "number": v.get("number"),
                            "vin": v.get("vin"),
                            "make": v.get("make"),
                            "model": v.get("model"),
                            "year": v.get("year"),
                            "lat": loc.get("lat"),
                            "lon": loc.get("lon"),
                            "located_at": loc.get("located_at"),
                            "city": loc.get("city"),
                            "state": loc.get("state"),
                            "speed_kph": loc.get("kph"),
                        },
                        "updated_at": _now_iso(),
                    }
                    res = await self.db.asset_mappings.update_one(
                        {"provider": PROVIDER, "motive.vehicle_id": vid},
                        {"$set": payload, "$setOnInsert": _asset_mapping_defaults()},
                        upsert=True,
                    )
                    if res.upserted_id:
                        created += 1
                    elif res.modified_count:
                        updated += 1
                pg = data.get("pagination") or {}
                if not pg or page >= int(pg.get("total_pages") or page) or not vehicles:
                    break
                page += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning(f"[motive sync_assets vehicles] {e}")

        # 2b · Assets (Asset Gateway · construction equipment)
        try:
            page = 1
            while True:
                data = await self._get("/v1/assets", {"per_page": 100, "page_no": page})
                assets = data.get("assets", [])
                for wrap in assets:
                    a = wrap.get("asset") or {}
                    aid = str(a.get("id") or "").strip()
                    if not aid:
                        continue
                    ag = a.get("asset_gateway") or {}
                    payload = {
                        "provider": PROVIDER,
                        "asset_kind": "equipment",
                        "motive": {
                            "vehicle_id": None,
                            "asset_id": aid,
                            "driver_id": None,
                            "device_id": (ag.get("serial") if isinstance(ag, dict) else None),
                            "gps_enabled": bool(ag),
                            "dashcam_enabled": False,
                            "name": a.get("name"),
                            "vin": a.get("vin"),
                            "make": a.get("make"),
                            "model": a.get("model"),
                            "year": a.get("year"),
                            "type": a.get("type"),
                            "status": a.get("status"),
                        },
                        "updated_at": _now_iso(),
                    }
                    res = await self.db.asset_mappings.update_one(
                        {"provider": PROVIDER, "motive.asset_id": aid},
                        {"$set": payload, "$setOnInsert": _asset_mapping_defaults()},
                        upsert=True,
                    )
                    if res.upserted_id:
                        created += 1
                    elif res.modified_count:
                        updated += 1
                pg = data.get("pagination") or {}
                if not pg or page >= int(pg.get("total_pages") or page) or not assets:
                    break
                page += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning(f"[motive sync_assets assets] {e}")

        await _write_sync_log(self.db, "sync_assets", triggered_by, created, updated, errors)
        return {"ok": errors == 0, "status": "ok" if errors == 0 else "partial",
                "operation": "sync_assets",
                "records_created": created, "records_updated": updated, "errors": errors,
                "message": f"Synced vehicles+assets · created={created} updated={updated} errors={errors}"}

    # ── 3. Sync drivers ──────────────────────────────────────────────
    async def sync_users(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        if not self.is_live:
            return _awaiting("sync_users")
        created, updated, errors = 0, 0, 0
        try:
            page = 1
            while True:
                data = await self._get("/v1/driver_locations", {"per_page": 100, "page_no": page})
                users = data.get("users", [])
                for wrap in users:
                    u = wrap.get("user") or {}
                    did = str(u.get("id") or "").strip()
                    if not did:
                        continue
                    loc = u.get("current_location") or {}
                    cv = u.get("current_vehicle") or {}
                    payload = {
                        "provider": PROVIDER,
                        "motive": {
                            "driver_id": did,
                            "first_name": u.get("first_name"),
                            "last_name": u.get("last_name"),
                            "username": u.get("username"),
                            "email": u.get("email"),
                            "company_id": u.get("driver_company_id"),
                            "status": u.get("status"),
                            "role": u.get("role"),
                            "current_vehicle_id": cv.get("id") if isinstance(cv, dict) else None,
                            "lat": loc.get("lat"),
                            "lon": loc.get("lon"),
                            "located_at": loc.get("located_at"),
                        },
                        "updated_at": _now_iso(),
                    }
                    res = await self.db.employee_mappings.update_one(
                        {"provider": PROVIDER, "motive.driver_id": did},
                        {"$set": payload, "$setOnInsert": _employee_mapping_defaults()},
                        upsert=True,
                    )
                    if res.upserted_id:
                        created += 1
                    elif res.modified_count:
                        updated += 1
                pg = data.get("pagination") or {}
                if not pg or page >= int(pg.get("total_pages") or page) or not users:
                    break
                page += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning(f"[motive sync_users] {e}")

        await _write_sync_log(self.db, "sync_users", triggered_by, created, updated, errors)
        return {"ok": errors == 0, "status": "ok" if errors == 0 else "partial",
                "operation": "sync_users",
                "records_created": created, "records_updated": updated, "errors": errors}

    # ── 4. Sync geofences ────────────────────────────────────────────
    async def sync_geofences(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        if not self.is_live:
            return _awaiting("sync_geofences")
        created, updated, errors = 0, 0, 0
        try:
            page = 1
            while True:
                data = await self._get("/v1/geofences", {"per_page": 100, "page_no": page})
                fences = data.get("geofences", [])
                for wrap in fences:
                    g = wrap.get("geofence") or {}
                    gid = str(g.get("id") or "").strip()
                    if not gid:
                        continue
                    payload = {
                        "provider": PROVIDER,
                        "motive_geofence_id": gid,
                        "name": g.get("name"),
                        "status": g.get("status"),
                        "address": g.get("address"),
                        "category": g.get("category"),
                        "location_points": g.get("location_points") or [],
                        "updated_at": _now_iso(),
                    }
                    res = await self.db.motive_geofences.update_one(
                        {"motive_geofence_id": gid},
                        {"$set": payload, "$setOnInsert": {"id": _new_id(), "created_at": _now_iso()}},
                        upsert=True,
                    )
                    if res.upserted_id:
                        created += 1
                    elif res.modified_count:
                        updated += 1
                pg = data.get("pagination") or {}
                if not pg or page >= int(pg.get("total_pages") or page) or not fences:
                    break
                page += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning(f"[motive sync_geofences] {e}")

        await _write_sync_log(self.db, "sync_geofences", triggered_by, created, updated, errors)
        return {"ok": errors == 0, "status": "ok" if errors == 0 else "partial",
                "operation": "sync_geofences",
                "records_created": created, "records_updated": updated, "errors": errors}

    # ── 5. Sync events (polling backfill — webhooks are primary) ─────
    async def sync_events(self, *, triggered_by: str = "system") -> Dict[str, Any]:
        """Polling backfill for missed webhooks. Re-runs a vehicle
        location pull and persists each row to motive_events so the
        Dispatch board has a recent ground truth even if a webhook
        was dropped."""
        if not self.is_live:
            return _awaiting("sync_events")
        created, errors = 0, 0
        try:
            data = await self._get("/v3/vehicle_locations", {"per_page": 100})
            for wrap in data.get("vehicles", []):
                v = wrap.get("vehicle") or {}
                loc = v.get("current_location") or {}
                if not loc.get("lat"):
                    continue
                await self.db.motive_events.insert_one({
                    "id": _new_id(),
                    "provider": PROVIDER,
                    "event_kind": "vehicle_gps",
                    "source": "poll",
                    "event_at": loc.get("located_at") or _now_iso(),
                    "received_at": _now_iso(),
                    "vehicle_id": str(v.get("id") or ""),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                    "speed_kph": loc.get("kph"),
                    "bearing": loc.get("bearing"),
                    "city": loc.get("city"),
                    "state": loc.get("state"),
                    "raw": v,
                })
                created += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning(f"[motive sync_events] {e}")

        await _write_sync_log(self.db, "sync_events", triggered_by, created, 0, errors)
        return {"ok": errors == 0, "status": "ok" if errors == 0 else "partial",
                "operation": "sync_events", "records_created": created,
                "records_updated": 0, "errors": errors}

    # ── 6. Process webhook ───────────────────────────────────────────
    async def process_webhook(self, *, raw_body: bytes, headers: Dict[str, str],
                              test_mode: bool = False) -> Dict[str, Any]:
        """Route a Motive webhook by event type. Signature verification
        is handled UPSTREAM in routes/integrations/webhooks.py. This
        method only persists + dispatches."""
        try:
            body = json.loads(raw_body.decode("utf-8") or "{}")
        except Exception:
            body = {}

        # Motive's webhook envelopes vary by event; capture defensively.
        event_kind = (
            body.get("event_type")
            or body.get("type")
            or body.get("event")
            or "unknown"
        )
        vehicle = body.get("vehicle") or {}
        vehicle_id = str(vehicle.get("id") or body.get("vehicle_id") or "").strip()
        loc = body.get("location") or vehicle.get("current_location") or {}

        # P1.5 · Extract operationally meaningful fields per the
        # Webhook Intelligence Audit. Storage only — NO workflow
        # transitions, NO holds, NO work-order creation. Each family
        # writes into the same `motive_events` doc with a normalized
        # `classification` so MASCI surfaces can render them without
        # parsing raw JSON.
        family = _classify_family(event_kind)
        classification = _classify_event(family, event_kind, body, vehicle, loc)

        await self.db.motive_events.insert_one({
            "id": _new_id(),
            "provider": PROVIDER,
            "event_kind": event_kind,
            "event_family": family,
            "source": "webhook",
            "event_at": body.get("event_time") or body.get("occurred_at") or loc.get("located_at") or _now_iso(),
            "received_at": _now_iso(),
            "vehicle_id": vehicle_id,
            "driver_id": str((body.get("driver") or {}).get("id") or body.get("driver_id") or "").strip(),
            "lat": loc.get("lat"),
            "lon": loc.get("lon"),
            "raw": body,
            "test_mode": test_mode,
            **classification,
        })

        # Light routing for vehicle_gps — keep hydrated mapping row fresh
        if event_kind in ("vehicle_gps", "vehicle_location_received") and vehicle_id and loc.get("lat"):
            try:
                await self.db.asset_mappings.update_one(
                    {"provider": PROVIDER, "motive.vehicle_id": vehicle_id},
                    {"$set": {
                        "motive.lat": loc.get("lat"),
                        "motive.lon": loc.get("lon"),
                        "motive.located_at": loc.get("located_at") or _now_iso(),
                        "updated_at": _now_iso(),
                    }},
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[motive webhook hydrate] {e}")

        return {"ok": True, "status": "stored", "stored": True,
                "event_kind": event_kind, "event_family": family,
                "severity": classification.get("severity"),
                "vehicle_id": vehicle_id or None}

    async def create_corrective_action_from_event(self, motive_event_id: str) -> Dict[str, Any]:
        evt = await self.db.motive_events.find_one({"id": motive_event_id})
        if not evt:
            return {"ok": False, "status": "not_found"}
        return {"ok": True, "status": "noted",
                "motive_event_id": motive_event_id,
                "event_kind": evt.get("event_kind"),
                "message": "CA seam ready — wire to existing safety_corrective_actions pipeline when needed."}


# ── helpers ──────────────────────────────────────────────────────────
async def _write_sync_log(db, op: str, triggered_by: str, created: int, updated: int, errors: int):
    """Persist a sync log in the canonical Integration Center schema
    AND stamp last_sync_at + last_successful_sync_at/last_failed_sync_at
    on the integration_settings row so the Admin UI overview tile
    reflects reality without a page reload."""
    now = _now_iso()
    status = "Success" if errors == 0 else ("Partial" if (created + updated) > 0 else "Failed")
    try:
        await db.integration_sync_logs.insert_one({
            "id": _new_id(),
            "integration": PROVIDER,
            "sync_type": op,
            "status": status,
            "started_at": now,
            "completed_at": now,
            "duration_ms": 0,
            "records_created": created,
            "records_updated": updated,
            "records_skipped": 0,
            "records_failed": errors,
            "error_message": None,
            "triggered_by": triggered_by,
            "environment": (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "production").strip(),
            "notes": "",
        })
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[motive sync_log] {e}")

    # Stamp the settings row so /api/admin/integrations/overview
    # reflects the latest sync without recomputing from logs.
    try:
        patch = {"last_sync_at": now, "updated_at": now}
        if errors == 0:
            patch["last_successful_sync_at"] = now
            patch["last_sync_error"] = None
        else:
            patch["last_failed_sync_at"] = now
        await db.integration_settings.update_one(
            {"provider": PROVIDER}, {"$set": patch}
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[motive sync_stamp] {e}")


def _awaiting(op: str) -> Dict[str, Any]:
    return {"ok": False, "status": "awaiting_credentials", "operation": op,
            "records_created": 0, "records_updated": 0,
            "message": f"{op} skipped — Motive credentials not configured."}


def _asset_mapping_defaults() -> Dict[str, Any]:
    """Inserted only on first discovery so docs match the canonical
    schema produced by Integration Center CSV import — keeps the
    mappings wizard + cross-provider join logic happy."""
    return {
        "id": _new_id(),
        "created_at": _now_iso(),
        "masci_equipment_id": "",
        "masci_unit_number": "",
        "masci_equipment_name": "",
        "masci_equipment_type": "",
        "maintainx": {"asset_id": "", "location_id": "", "pm_schedule_id": "",
                      "last_sync_at": None, "mapping_status": "Unmapped"},
        "mapping_confidence": "low",
        "mapping_notes": "Auto-discovered by Motive sync.",
        "active": True,
    }


def _employee_mapping_defaults() -> Dict[str, Any]:
    return {
        "id": _new_id(),
        "created_at": _now_iso(),
        "masci_employee_id": "",
        "masci_employee_name": "",
        "masci_employee_trade": "",
        "masci_employee_role": "",
        "masci_employee_email": "",
        "maintainx": {"user_id": "", "name": "", "email": "", "role": "",
                      "last_sync_at": None, "mapping_status": "Unmapped"},
        "mapping_notes": "Auto-discovered by Motive sync.",
        "active": True,
    }


# ── P1.5 · Event classifier (read-only · no workflow side-effects) ──
def _classify_family(event_kind: str) -> str:
    """Map raw Motive event_type to the authorized event families.
    P1.5: harsh_event, fault_code, dvir, geofence_enter/exit, vehicle_gps.
    P1.6: + hos_violation, gateway_disconnected, gateway_reconnected,
           asset_geofence_enter, asset_geofence_exit, ai_coach_recap,
           fault_code_closed (closed variant of fault_code).
    Anything else stays 'other' for forensic storage."""
    k = (event_kind or "").lower()
    if k in ("vehicle_gps", "vehicle_location_received"):
        return "vehicle_gps"
    if k.startswith("harsh") or k in ("hard_brake", "hard_braking", "speeding", "harsh_acceleration", "harsh_cornering"):
        return "harsh_event"
    # Fault code: keep close events in their own band so the decorator
    # can render "resolved" language and the priority model can rank
    # them differently.
    if k in ("fault_code_closed", "fault_closed", "fault_code_resolved", "dtc_closed"):
        return "fault_code_closed"
    if k in ("fault_code", "fault_code_raised", "fault_code_opened", "dtc") or k.startswith("fault"):
        return "fault_code"
    if k.startswith("dvir") or k in ("inspection_report_created", "inspection_report_updated", "inspection_report"):
        return "dvir"
    if k in ("asset_geofence_enter", "asset_geofence_entered", "asset_geofence_entry"):
        return "asset_geofence_enter"
    if k in ("asset_geofence_exit", "asset_geofence_exited", "asset_geofence_left"):
        return "asset_geofence_exit"
    if k in ("geofence_enter", "geofence_entered", "geofence_entry", "vehicle_geofence_enter"):
        return "geofence_enter"
    if k in ("geofence_exit", "geofence_exited", "geofence_left", "vehicle_geofence_exit"):
        return "geofence_exit"
    if k in ("hos_violation", "hos_violation_created", "hos_violation_updated", "hos_violation_raised"):
        return "hos_violation"
    if k in ("vehicle_gateway_disconnected", "gateway_disconnected"):
        return "gateway_disconnected"
    if k in ("vehicle_gateway_disconnect_ended", "gateway_disconnect_ended", "gateway_reconnected"):
        return "gateway_reconnected"
    if k in ("ai_coach_recap_created", "ai_coach_recap", "ai_coach_recap_updated"):
        return "ai_coach_recap"
    return "other"


_SEVERITY_BY_SUBTYPE = {
    # harsh_event subtypes
    "hard_brake": "high", "hard_braking": "high",
    "harsh_acceleration": "medium",
    "harsh_cornering": "medium",
    "speeding": "medium",
    "seatbelt_violation": "low",
    # dvir
    "dvir_submitted": "info",
    "dvir_defect": "high",
    "dvir_out_of_service": "critical",
    "dvir_signed": "info",
    # geofence
    "geofence_enter": "info",
    "geofence_exit": "info",
    "asset_geofence_enter": "info",
    "asset_geofence_exit": "info",
    # vehicle_gps
    "vehicle_gps": "info",
    # P1.6 priority ladder
    "hos_violation": "critical",
    "vehicle_gateway_disconnected": "critical",
    "vehicle_gateway_disconnect_ended": "low",
    "fault_code_closed": "medium",
    "ai_coach_recap": "medium",
}

# P1.6 · Operational priority bands (display order + notification gating).
# Used by surfaces to decide whether a row deserves the Notifications bell
# vs the historical timeline. Pure metadata — never auto-triggers action.
_PRIORITY_BY_FAMILY = {
    "hos_violation": "critical",
    "gateway_disconnected": "critical",
    "dvir": "high",                    # high when defect or OOS (raised by classifier)
    "asset_geofence_exit": "high",     # exit of job site is the billable signal
    "fault_code": "high",
    "harsh_event": "high",
    "geofence_enter": "medium",
    "geofence_exit": "medium",
    "asset_geofence_enter": "medium",
    "ai_coach_recap": "medium",
    "fault_code_closed": "medium",
    "gateway_reconnected": "low",
    "vehicle_gps": "low",
    "other": "low",
}


def _classify_event(family: str, event_kind: str, body: Dict[str, Any],
                    vehicle: Dict[str, Any], loc: Dict[str, Any]) -> Dict[str, Any]:
    """Return a flat dict of normalized visibility fields. Pure data
    extraction — never mutates other collections, never opens work
    orders or holds. Surfaces consume these fields directly."""
    sev_hint = body.get("severity") or _SEVERITY_BY_SUBTYPE.get((event_kind or "").lower(), "info")
    # P1.6 fallback for new families
    if (not body.get("severity")) and family in _PRIORITY_BY_FAMILY:
        # Use priority as severity hint when payload omits one
        pri = _PRIORITY_BY_FAMILY[family]
        sev_hint = {
            "critical": "critical", "high": "high",
            "medium": "medium", "low": "low",
        }.get(pri, sev_hint)
    out: Dict[str, Any] = {
        "severity": sev_hint,
        "priority": _PRIORITY_BY_FAMILY.get(family, "low"),
        "subtype": body.get("subtype") or body.get("type") or "",
        "address": loc.get("address") or loc.get("current_location") or "",
        "city": loc.get("city") or "",
        "state": loc.get("state") or "",
        "speed_kph": loc.get("kph") or body.get("speed_kph"),
    }
    if family == "harsh_event":
        out["harsh"] = {
            "subtype": (body.get("subtype") or event_kind or "").lower(),
            "speed_mph": body.get("speed_mph"),
            "coaching_required": bool(body.get("coaching_required")),
            "video_url": body.get("video_url") or "",
            "duration_seconds": body.get("duration_seconds"),
        }
    elif family == "fault_code":
        out["fault"] = {
            "dtc_code": body.get("dtc_code") or body.get("code") or "",
            "mil_status": bool(body.get("mil_status")),
            "description": body.get("description") or body.get("dtc_description") or "",
            "set_at": body.get("set_at") or body.get("event_time"),
            "cleared_at": body.get("cleared_at"),
            "state": "opened",
        }
        if (body.get("severity") or "").lower() in ("red", "critical", "severe") or body.get("mil_status"):
            out["severity"] = "critical"
    elif family == "fault_code_closed":
        # P1.6 · Decorate "Fault X resolved" — mirrors fault_code shape
        # so the same UI row template renders without branching.
        out["fault"] = {
            "dtc_code": body.get("dtc_code") or body.get("code") or "",
            "mil_status": bool(body.get("mil_status")),
            "description": body.get("description") or body.get("dtc_description") or "",
            "set_at": body.get("set_at"),
            "cleared_at": body.get("cleared_at") or body.get("event_time"),
            "state": "closed",
            "duration_seconds": body.get("duration_seconds"),
        }
    elif family == "dvir":
        defects = body.get("defects") or []
        oos = bool(body.get("out_of_service"))
        out["dvir"] = {
            "status": body.get("status") or "",
            "defect_count": len(defects),
            "defects": defects[:25],
            "out_of_service": oos,
            "mechanic_signed_by": (body.get("mechanic") or {}).get("name") or "",
            "is_update": (event_kind or "").lower() in ("dvir_updated", "inspection_report_updated"),
        }
        if oos:
            out["severity"] = "critical"
        elif defects:
            out["severity"] = "high"
    elif family in ("geofence_enter", "geofence_exit",
                    "asset_geofence_enter", "asset_geofence_exit"):
        g = body.get("geofence") or {}
        asset_side = family.startswith("asset_")
        transition = "enter" if family.endswith("enter") else "exit"
        out["geofence"] = {
            "id": str(g.get("id") or "").strip(),
            "name": g.get("name") or "",
            "category": g.get("category") or "",
            "address": g.get("address") or "",
            "dwell_seconds": body.get("dwell_seconds") if transition == "exit" else None,
            "transition": transition,
            "side": "asset" if asset_side else "vehicle",
        }
        if asset_side:
            a = body.get("asset") or {}
            out["asset"] = {
                "id": str(a.get("id") or "").strip(),
                "name": a.get("name") or "",
                "kind": a.get("type") or a.get("kind") or "",
                "battery_level": (body.get("gateway") or {}).get("battery_level"),
            }
    elif family == "hos_violation":
        d = body.get("driver") or {}
        out["hos"] = {
            "violation_type": body.get("violation_type") or body.get("type") or "",
            "duty_status": body.get("duty_status") or "",
            "cycle": body.get("cycle") or "",
            "driver_id": str(d.get("id") or body.get("driver_id") or "").strip(),
            "driver_name": d.get("name") or "",
            "threshold_minutes": body.get("threshold_minutes"),
            "exceeded_by_minutes": body.get("exceeded_by_minutes"),
            "is_update": (event_kind or "").lower().endswith("_updated"),
        }
    elif family == "gateway_disconnected":
        out["gateway"] = {
            "device_id": str((body.get("device") or {}).get("id") or body.get("device_id") or "").strip(),
            "last_reported_at": body.get("last_reported_at") or (vehicle.get("current_location") or {}).get("located_at"),
            "last_known_address": (body.get("last_known_location") or {}).get("address") or out["address"],
            "since": body.get("disconnect_event_time") or body.get("event_time"),
        }
    elif family == "gateway_reconnected":
        out["gateway"] = {
            "device_id": str((body.get("device") or {}).get("id") or body.get("device_id") or "").strip(),
            "offline_duration_seconds": body.get("offline_duration_seconds") or body.get("duration_seconds"),
            "reconnected_at": body.get("reconnect_event_time") or body.get("event_time"),
        }
    elif family == "ai_coach_recap":
        d = body.get("driver") or {}
        period = body.get("period") or {}
        out["ai_coach"] = {
            "driver_id": str(d.get("id") or body.get("driver_id") or "").strip(),
            "driver_name": d.get("name") or "",
            "score": body.get("score"),
            "score_delta": body.get("score_delta"),
            "period_start": period.get("start") or body.get("period_start"),
            "period_end": period.get("end") or body.get("period_end"),
            "event_counts": body.get("event_counts") or {},
            "trend": body.get("trend") or "",
            "recommendation": body.get("recommendation") or "",
        }
    return out


__all__ = ["MotiveService", "PROVIDER"]
