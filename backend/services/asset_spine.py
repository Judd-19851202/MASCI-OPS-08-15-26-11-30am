"""
services/asset_spine.py · FORGEDOPS P0.1 · Canonical Asset Spine Service.

Doctrine (per MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md):
  ForgedOps owns asset identity, ownership, classification, status,
  assignment, history, lifecycle. Motive / FleetWatcher / MaintainX
  validate, observe, and enrich. They never create or retire assets.

Single source-of-truth collection: `equipment_master`. This service
NEVER creates a parallel asset collection. It only consolidates the
contract — canonicalizing field names, enforcing audit, and unifying
reads across the legacy fragmented surface.

Public surface:
    AssetSpine(db).list_assets(...)           — paged catalog
    AssetSpine(db).get_asset(asset_id)        — single asset
    AssetSpine(db).get_profile(asset_id)      — fused profile (GPS + DVIR
                                                + maintenance + history)
    AssetSpine(db).create_asset(...)          — operator-authored insert
    AssetSpine(db).update_asset(...)          — partial patch
    AssetSpine(db).retire_asset(asset_id, ...) — retirement workflow
    AssetSpine(db).activate_asset(asset_id, ...) — un-retire (admin only)
    AssetSpine(db).health()                   — fleet-level health counts
    AssetSpine(db).scan_health()              — run all detectors and
                                                persist a health-run row

This module is read-mostly. Every mutation appends to `admin_audit_log`
AND `audit_events` AND `master_history` so the asset's lifecycle is
fully reconstructible from any one collection.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical field contract
# ---------------------------------------------------------------------------

# Mapping legacy field → canonical field. The service exposes the
# canonical name in API responses while preserving the legacy field in
# the document so existing readers continue to work.
LEGACY_TO_CANONICAL = {
    "is_active": "active",
    "label": "asset_name",
    "unit_number": "asset_number",
    "vin_serial_number": "vin",
}

CANONICAL_FIELDS = {
    "asset_id",            # uuid (== id)
    "asset_number",        # unit_number / fleet number
    "asset_name",          # human label
    "asset_type",          # truck / trailer / excavator / ...
    "asset_category",      # heavy / light / attachment / portable
    "asset_status",        # ACTIVE / OOS / RETIRED / MAINT
    "ownership",           # company / lease / rental
    "department",
    "cost_center",
    "manufacturer",
    "make",
    "model",
    "year",
    "serial_number",
    "vin",
    "license_plate",
    "motive_asset_id",
    "fleetwatcher_asset_id",
    "maintainx_asset_id",
    "purchase_date",
    "in_service_date",
    "retirement_date",
    "assigned_project_id",
    "assigned_project_name",
    "assigned_driver_id",
    "assigned_supervisor_id",
    "assigned_dispatcher_id",
    "current_location",
    "current_gps_status",       # ACTIVE / STALE / OFFLINE / unknown
    "current_dvir_status",      # PASS / FAIL / PENDING / unknown
    "current_maintenance_status", # OK / DUE / OVERDUE / unknown
    "created_by",
    "created_at",
    "last_modified_by",
    "last_modified_at",
    "active",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def project_asset(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the canonical view of an `equipment_master` row.

    Legacy fields are read once and surfaced under the canonical name.
    The document is NOT mutated. Unknown / missing fields are emitted as
    None so the consumer can render a stable shape.
    """
    if not doc:
        return {}

    def _get(*keys):
        for k in keys:
            v = doc.get(k)
            if v not in (None, ""):
                return v
        return None

    is_active_raw = doc.get("is_active")
    if is_active_raw is None:
        is_active_raw = doc.get("active")
    active = bool(is_active_raw) if is_active_raw is not None else True

    return {
        "asset_id": doc.get("id") or doc.get("asset_id"),
        "asset_number": _get("unit_number", "asset_number"),
        "asset_name": _get("label", "display_label", "asset_name"),
        "asset_type": _get("type", "asset_type", "preop_equipment_type"),
        "asset_category": doc.get("category") or doc.get("asset_category"),
        "asset_status": doc.get("status") or doc.get("operational_status") or doc.get("asset_status"),
        "ownership": doc.get("company") or doc.get("ownership"),
        "department": doc.get("department"),
        "cost_center": doc.get("cost_center"),
        "manufacturer": doc.get("manufacturer") or doc.get("make"),
        "make": doc.get("make"),
        "model": doc.get("model"),
        "year": doc.get("year"),
        "serial_number": doc.get("serial_number"),
        "vin": _get("vin_serial_number", "vin"),
        "license_plate": doc.get("license_plate"),
        "motive_asset_id": doc.get("motive_asset_id"),
        "motive_vehicle_id": doc.get("motive_vehicle_id"),
        "fleetwatcher_asset_id": doc.get("fleetwatcher_asset_id"),
        "maintainx_asset_id": doc.get("maintainx_asset_id"),
        "purchase_date": doc.get("purchase_date"),
        "in_service_date": doc.get("in_service_date"),
        "retirement_date": doc.get("retirement_date") or doc.get("retired_at"),
        # ── Track 13.31B Day-0 canonical taxonomy ────────────────────────
        "asset_class":            doc.get("asset_class"),
        "asset_subtype":          doc.get("asset_subtype"),
        "taxonomy_verified":      doc.get("taxonomy_verified"),
        "taxonomy_source":        doc.get("taxonomy_source"),
        "asset_category_version": doc.get("asset_category_version"),
        "legacy_category":        doc.get("legacy_category") or doc.get("category"),
        "legacy_preop_equipment_type": doc.get("legacy_preop_equipment_type") or doc.get("preop_equipment_type"),
        "legacy_type":            doc.get("legacy_type") or doc.get("type"),
        # ── Track 13.31B Day-1 administrative fields ────────────────────
        "registration_number":     doc.get("registration_number"),
        "registration_state":      doc.get("registration_state"),
        "registration_expiration": doc.get("registration_expiration"),
        "insurance_carrier":       doc.get("insurance_carrier"),
        "insurance_policy_number": doc.get("insurance_policy_number"),
        "insurance_expiration":    doc.get("insurance_expiration"),
        "title_status":            doc.get("title_status"),
        "warranty_expiration":     doc.get("warranty_expiration"),
        # D6 · additional renewal mirror fields for GPS / Survey / Tech assets
        "dot_expiration":          doc.get("dot_expiration"),
        "calibration_expiration":  doc.get("calibration_expiration"),
        "inspection_expiration":   doc.get("inspection_expiration"),
        "lifecycle_status":        doc.get("lifecycle_status"),
        "division":                doc.get("division"),
        "region":                  doc.get("region"),
        "supervisor_id":           doc.get("supervisor_id"),
        "gps_device_id":           doc.get("gps_device_id"),
        "normalized_company":      doc.get("normalized_company"),
        "assigned_project_id": doc.get("current_project_id"),
        "assigned_project_name": doc.get("current_project_name") or doc.get("current_project_number"),
        "assigned_driver_id": doc.get("assigned_driver_id"),
        "assigned_supervisor_id": doc.get("assigned_supervisor_id"),
        "assigned_dispatcher_id": doc.get("assigned_dispatcher_id"),
        "current_location": doc.get("current_location") or doc.get("location"),
        "current_gps_status": doc.get("current_gps_status"),
        "current_dvir_status": doc.get("current_dvir_status") or doc.get("last_inspection_result"),
        "current_maintenance_status": doc.get("current_maintenance_status"),
        "created_by": doc.get("created_by"),
        "created_at": doc.get("created_at"),
        "last_modified_by": doc.get("last_modified_by") or doc.get("updated_by"),
        "last_modified_at": doc.get("updated_at") or doc.get("last_modified_at"),
        "active": active,
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AssetSpine:
    """Canonical service. Hold instance per request; never module-level."""

    def __init__(self, db):
        self.db = db

    # ----- READ ----------------------------------------------------------

    def _asset_query(self, *, active_only=True, asset_type=None, search=None):
        q: Dict[str, Any] = {}
        if active_only:
            q["$or"] = [
                {"is_active": {"$ne": False}},
                {"active": {"$ne": False}},
            ]
        if asset_type:
            q["$and"] = q.get("$and", []) + [{
                "$or": [
                    {"type": asset_type},
                    {"asset_type": asset_type},
                    {"category": asset_type},
                ]
            }]
        if search:
            s = search.strip()
            if s:
                rx = {"$regex": s, "$options": "i"}
                q["$and"] = q.get("$and", []) + [{
                    "$or": [
                        {"unit_number": rx},
                        {"label": rx},
                        {"display_label": rx},
                        {"make": rx},
                        {"model": rx},
                        {"manufacturer": rx},
                        {"serial_number": rx},
                        {"vin_serial_number": rx},
                    ]
                }]
        return q

    async def count_assets(self, *, active_only=True, asset_type=None, search=None) -> int:
        return await self.db.equipment_master.count_documents(
            self._asset_query(active_only=active_only, asset_type=asset_type, search=search))

    async def list_assets(
        self,
        *,
        active_only: bool = True,
        asset_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 200,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        q = self._asset_query(active_only=active_only, asset_type=asset_type, search=search)
        cur = self.db.equipment_master.find(q).sort("unit_number", 1).skip(int(skip)).limit(int(limit))
        out: List[Dict[str, Any]] = []
        async for doc in cur:
            out.append(project_asset(doc))
        return out

    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.db.equipment_master.find_one({"id": asset_id})
        if not doc:
            doc = await self.db.equipment_master.find_one({"asset_id": asset_id})
        return project_asset(doc) if doc else None

    async def get_profile(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Fused asset profile: identity + integrations + recent activity.

        Pulls — read-only — from equipment_inspections, fleet_defects,
        dispatch_assignments, motive_events, asset_mappings,
        asset_transfers, admin_audit_log.
        """
        asset = await self.get_asset(asset_id)
        if not asset:
            return None

        unit = asset["asset_number"]
        out: Dict[str, Any] = {"asset": asset}

        # --- Integration mappings -----------------------------------------
        motive_map = await self.db.asset_mappings.find_one({
            "$or": [
                {"masci_equipment_id": asset_id},
                {"masci_unit_number": unit},
            ]
        })
        out["integration_status"] = {
            "motive": {
                "mapped": bool(motive_map),
                "motive_asset_id": (motive_map or {}).get("motive_asset_id"),
                "last_seen_at": (motive_map or {}).get("last_seen_at"),
            },
            "maintainx": {
                "mapped": bool(asset.get("maintainx_asset_id")),
                "maintainx_asset_id": asset.get("maintainx_asset_id"),
            },
            "fleetwatcher": {
                "mapped": bool(asset.get("fleetwatcher_asset_id")),
                "fleetwatcher_asset_id": asset.get("fleetwatcher_asset_id"),
            },
        }

        # --- Recent DVIR / inspections (last 5) --------------------------
        dvir_cur = self.db.equipment_inspections.find(
            {"$or": [{"unit_number": unit}, {"asset_id": asset_id}]}
        ).sort("created_at", -1).limit(5)
        out["dvir_history"] = [
            {k: v for k, v in d.items() if k != "_id"}
            async for d in dvir_cur
        ]

        # --- Open / recent fleet defects (last 5) ------------------------
        defects_cur = self.db.fleet_defects.find(
            {"$or": [{"unit_number": unit}, {"asset_id": asset_id}]}
        ).sort("created_at", -1).limit(5)
        out["maintenance_history"] = [
            {k: v for k, v in d.items() if k != "_id"}
            async for d in defects_cur
        ]

        # --- Recent assignments (last 10) --------------------------------
        assn_cur = self.db.dispatch_assignments.find(
            {"$or": [{"truck_id": unit}, {"asset_id": asset_id}, {"truck_id": asset_id}]}
        ).sort("assigned_at", -1).limit(10)
        out["assignment_history"] = [
            {k: v for k, v in d.items() if k != "_id"}
            async for d in assn_cur
        ]

        # --- Recent Motive events (last 5) -------------------------------
        if motive_map:
            mev_cur = self.db.motive_events.find(
                {"motive_asset_id": (motive_map or {}).get("motive_asset_id")}
            ).sort("event_at", -1).limit(5)
            out["gps_history"] = [
                {k: v for k, v in d.items() if k != "_id"}
                async for d in mev_cur
            ]
        else:
            out["gps_history"] = []

        # --- Asset transfers (provenance, full) --------------------------
        xfer_cur = self.db.asset_transfers.find(
            {"$or": [{"asset_id": asset_id}, {"unit_number": unit}]}
        ).sort("created_at", -1).limit(20)
        out["transfer_history"] = [
            {k: v for k, v in d.items() if k != "_id"}
            async for d in xfer_cur
        ]

        # --- Audit history (admin_audit_log entries for this asset, 20) -
        audit_cur = self.db.admin_audit_log.find(
            {"$or": [
                {"target_id": asset_id},
                {"meta.asset_id": asset_id},
                {"meta.unit_number": unit},
            ]}
        ).sort("at", -1).limit(20)
        out["audit_history"] = [
            {k: v for k, v in d.items() if k != "_id"}
            async for d in audit_cur
        ]

        return out

    # ----- WRITE (all mutations audited) ---------------------------------

    async def _audit(
        self,
        *,
        action: str,
        target_id: str,
        before: Optional[Dict[str, Any]],
        after: Optional[Dict[str, Any]],
        actor: str,
        reason: Optional[str] = None,
    ) -> None:
        try:
            await self.db.admin_audit_log.insert_one({
                "id": _new_id(),
                "at": _now_iso(),
                "actor": actor,
                "action": action,
                "target_collection": "equipment_master",
                "target_id": target_id,
                "before": before,
                "after": after,
                "reason": reason,
            })
        except Exception as e:
            logger.warning("[asset_spine] admin_audit_log insert failed: %s", e)
        try:
            await self.db.audit_events.insert_one({
                "id": _new_id(),
                "at": _now_iso(),
                "kind": action,
                "actor": actor,
                "asset_id": target_id,
            })
        except Exception:
            pass

    async def create_asset(
        self,
        payload: Dict[str, Any],
        *,
        actor: str,
    ) -> Dict[str, Any]:
        aid = payload.get("asset_id") or _new_id()
        unit = (payload.get("asset_number") or payload.get("unit_number") or "").strip()
        if not unit:
            raise ValueError("asset_number is required")
        existing = await self.db.equipment_master.find_one({
            "$or": [{"unit_number": unit}, {"asset_number": unit}]
        })
        if existing:
            raise ValueError(f"asset_number {unit!r} already exists (id={existing.get('id')})")

        now = _now_iso()
        doc: Dict[str, Any] = {
            "id": aid,
            "asset_id": aid,
            "unit_number": unit,
            "asset_number": unit,
            "label": payload.get("asset_name") or payload.get("label") or unit,
            "asset_name": payload.get("asset_name") or unit,
            "type": payload.get("asset_type") or payload.get("type"),
            "asset_type": payload.get("asset_type") or payload.get("type"),
            "category": payload.get("asset_category") or payload.get("category"),
            "asset_category": payload.get("asset_category") or payload.get("category"),
            "status": payload.get("asset_status") or "ACTIVE",
            "asset_status": payload.get("asset_status") or "ACTIVE",
            "company": payload.get("ownership") or payload.get("company"),
            "ownership": payload.get("ownership"),
            "department": payload.get("department"),
            "cost_center": payload.get("cost_center"),
            "manufacturer": payload.get("manufacturer") or payload.get("make"),
            "make": payload.get("make"),
            "model": payload.get("model"),
            "year": payload.get("year"),
            "serial_number": payload.get("serial_number"),
            "vin_serial_number": payload.get("vin") or payload.get("vin_serial_number"),
            "vin": payload.get("vin"),
            "license_plate": payload.get("license_plate"),
            "motive_asset_id": payload.get("motive_asset_id"),
            "motive_vehicle_id": payload.get("motive_vehicle_id"),
            "fleetwatcher_asset_id": payload.get("fleetwatcher_asset_id"),
            "maintainx_asset_id": payload.get("maintainx_asset_id"),
            "purchase_date": payload.get("purchase_date"),
            "in_service_date": payload.get("in_service_date") or now,
            "retirement_date": None,
            "retired_at": None,
            "is_active": True,
            "active": True,
            # ── Track 13.31B Day-0 canonical taxonomy ────────────────────
            "asset_class":            payload.get("asset_class"),
            "asset_subtype":          payload.get("asset_subtype"),
            "taxonomy_verified":      payload.get("taxonomy_verified"),
            "taxonomy_source":        payload.get("taxonomy_source"),
            "asset_category_version": "1.0.0",
            # ── Track 13.31B Day-1 administrative fields ────────────────
            "registration_number":     payload.get("registration_number"),
            "registration_state":      payload.get("registration_state"),
            "registration_expiration": payload.get("registration_expiration"),
            "insurance_carrier":       payload.get("insurance_carrier"),
            "insurance_policy_number": payload.get("insurance_policy_number"),
            "insurance_expiration":    payload.get("insurance_expiration"),
            "title_status":            payload.get("title_status"),
            "warranty_expiration":     payload.get("warranty_expiration"),
            "dot_expiration":          payload.get("dot_expiration"),
            "calibration_expiration":  payload.get("calibration_expiration"),
            "inspection_expiration":   payload.get("inspection_expiration"),
            "lifecycle_status":        payload.get("lifecycle_status"),
            "division":                payload.get("division"),
            "region":                  payload.get("region"),
            "supervisor_id":           payload.get("supervisor_id"),
            "gps_device_id":           payload.get("gps_device_id"),
            "normalized_company":      payload.get("normalized_company"),
            "created_by": actor,
            "created_at": now,
            "last_modified_by": actor,
            "last_modified_at": now,
            "updated_by": actor,
            "updated_at": now,
            "linked_collection": "asset_spine:create",
        }
        await self.db.equipment_master.insert_one(doc)
        await self._audit(
            action="ASSET_CREATE",
            target_id=aid,
            before=None,
            after=project_asset(doc),
            actor=actor,
        )
        return project_asset(doc)

    async def update_asset(
        self,
        asset_id: str,
        patch: Dict[str, Any],
        *,
        actor: str,
    ) -> Optional[Dict[str, Any]]:
        doc = await self.db.equipment_master.find_one({"id": asset_id})
        if not doc:
            return None
        before = project_asset(doc)
        now = _now_iso()
        update: Dict[str, Any] = {}
        legal_keys = {
            "asset_name", "label", "asset_type", "type", "asset_category", "category",
            "ownership", "company", "department", "cost_center",
            "manufacturer", "make", "model", "year", "serial_number",
            "vin", "vin_serial_number", "license_plate",
            "motive_asset_id", "motive_vehicle_id",
            "fleetwatcher_asset_id", "maintainx_asset_id",
            "purchase_date", "in_service_date",
            "asset_status", "status",
            "assigned_driver_id", "assigned_supervisor_id", "assigned_dispatcher_id",
            "current_location", "location",
            # ── Track 13.31B Day-0 canonical taxonomy ────────────────────
            "asset_class", "asset_subtype", "taxonomy_verified", "taxonomy_source",
            "taxonomy_verified_at", "taxonomy_review_reason",
            # ── Track 13.31B Day-1 administrative fields ────────────────
            "registration_number", "registration_state", "registration_expiration",
            "insurance_carrier", "insurance_policy_number", "insurance_expiration",
            "title_status", "warranty_expiration", "dot_expiration", "calibration_expiration",
            "inspection_expiration",
            "lifecycle_status", "division", "region", "supervisor_id",
            "gps_device_id", "normalized_company",
        }
        for k, v in patch.items():
            if k in legal_keys:
                update[k] = v
        # Mirror canonical → legacy so `project_asset` (which prefers legacy
        # fields when present) sees the new value.
        if "asset_name" in patch:
            update["label"] = patch["asset_name"]
        if "asset_type" in patch:
            update["type"] = patch["asset_type"]
        if "asset_category" in patch:
            update["category"] = patch["asset_category"]
        if "asset_status" in patch:
            update["status"] = patch["asset_status"]
        if "ownership" in patch:
            update["company"] = patch["ownership"]
        if "vin" in patch:
            update["vin_serial_number"] = patch["vin"]
        # Auto-stamp taxonomy_verified_at when verified flips True without explicit timestamp.
        if patch.get("taxonomy_verified") is True and "taxonomy_verified_at" not in patch:
            update["taxonomy_verified_at"] = now
        # Clear review reason when manual verification lands.
        if patch.get("taxonomy_verified") is True and "taxonomy_review_reason" not in patch:
            update["taxonomy_review_reason"] = None
        if not update:
            return before
        update["last_modified_by"] = actor
        update["last_modified_at"] = now
        update["updated_by"] = actor
        update["updated_at"] = now
        await self.db.equipment_master.update_one({"id": asset_id}, {"$set": update})
        doc2 = await self.db.equipment_master.find_one({"id": asset_id})
        after = project_asset(doc2)
        await self._audit(
            action="ASSET_UPDATE",
            target_id=asset_id,
            before=before,
            after=after,
            actor=actor,
        )
        return after

    async def retire_asset(
        self,
        asset_id: str,
        *,
        actor: str,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        doc = await self.db.equipment_master.find_one({"id": asset_id})
        if not doc:
            return None
        if doc.get("is_active") is False or doc.get("active") is False:
            return project_asset(doc)
        before = project_asset(doc)
        now = _now_iso()
        await self.db.equipment_master.update_one(
            {"id": asset_id},
            {"$set": {
                "is_active": False,
                "active": False,
                "asset_status": "RETIRED",
                "status": "RETIRED",
                "retired_at": now,
                "retirement_date": now,
                "last_modified_by": actor,
                "last_modified_at": now,
                "updated_by": actor,
                "updated_at": now,
            }},
        )
        # Append a transfer record (type=RETIRE) for provenance.
        try:
            await self.db.asset_transfers.insert_one({
                "id": _new_id(),
                "asset_id": asset_id,
                "unit_number": doc.get("unit_number"),
                "type": "RETIRE",
                "from_location": doc.get("current_location") or doc.get("location"),
                "to_location": None,
                "created_at": now,
                "created_by": actor,
                "reason": reason,
                "state": "completed",
            })
        except Exception as e:
            logger.warning("[asset_spine] asset_transfers retire row failed: %s", e)
        after = await self.get_asset(asset_id)
        await self._audit(
            action="ASSET_RETIRE",
            target_id=asset_id,
            before=before,
            after=after,
            actor=actor,
            reason=reason,
        )
        return after

    async def activate_asset(
        self,
        asset_id: str,
        *,
        actor: str,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        doc = await self.db.equipment_master.find_one({"id": asset_id})
        if not doc:
            return None
        before = project_asset(doc)
        now = _now_iso()
        await self.db.equipment_master.update_one(
            {"id": asset_id},
            {"$set": {
                "is_active": True,
                "active": True,
                "asset_status": "ACTIVE",
                "status": "ACTIVE",
                "retired_at": None,
                "retirement_date": None,
                "last_modified_by": actor,
                "last_modified_at": now,
                "updated_by": actor,
                "updated_at": now,
            }},
        )
        after = await self.get_asset(asset_id)
        await self._audit(
            action="ASSET_ACTIVATE",
            target_id=asset_id,
            before=before,
            after=after,
            actor=actor,
            reason=reason,
        )
        return after

    async def transfer_asset(
        self,
        asset_id: str,
        *,
        actor: str,
        to_project_id: Optional[str] = None,
        to_project_name: Optional[str] = None,
        to_department: Optional[str] = None,
        to_ownership: Optional[str] = None,
        to_location: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        P0.7 · Transfer workflow. Capture ownership / department / project /
        location changes as a single auditable event. Updates the canonical
        asset AND writes an `asset_transfers` row of type=TRANSFER. Every
        previous-state value is preserved in the audit chain.
        """
        doc = await self.db.equipment_master.find_one({"id": asset_id})
        if not doc:
            return None
        before = project_asset(doc)
        now = _now_iso()
        upd: Dict[str, Any] = {
            "last_modified_by": actor, "last_modified_at": now,
            "updated_by": actor, "updated_at": now,
        }
        delta: Dict[str, Any] = {}
        if to_project_id is not None:
            upd["current_project_id"] = to_project_id
            delta["project_id"] = {"from": doc.get("current_project_id"), "to": to_project_id}
        if to_project_name is not None:
            upd["current_project_name"] = to_project_name
            delta["project_name"] = {"from": doc.get("current_project_name"), "to": to_project_name}
        if to_department is not None:
            upd["department"] = to_department
            delta["department"] = {"from": doc.get("department"), "to": to_department}
        if to_ownership is not None:
            upd["ownership"] = to_ownership
            upd["company"] = to_ownership
            delta["ownership"] = {"from": doc.get("company") or doc.get("ownership"), "to": to_ownership}
        if to_location is not None:
            upd["current_location"] = to_location
            delta["location"] = {"from": doc.get("current_location"), "to": to_location}
        if not delta:
            return before
        await self.db.equipment_master.update_one({"id": asset_id}, {"$set": upd})
        try:
            await self.db.asset_transfers.insert_one({
                "id": _new_id(), "asset_id": asset_id,
                "unit_number": doc.get("unit_number"),
                "type": "TRANSFER", "delta": delta,
                "from_location": doc.get("current_location"),
                "to_location": to_location,
                "created_at": now, "created_by": actor,
                "reason": reason, "state": "completed",
            })
        except Exception as e:
            logger.warning("[asset_spine] transfer ledger row failed: %s", e)
        after = await self.get_asset(asset_id)
        await self._audit(
            action="ASSET_TRANSFER",
            target_id=asset_id, before=before, after=after,
            actor=actor, reason=reason,
        )
        return after

    # ----- ONBOARDING (P0.6) ---------------------------------------------

    ONBOARDING_STEPS = (
        "purchase", "delivery", "gps_install", "motive_mapped",
        "fleetwatcher_mapped", "maintainx_mapped",
        "classified", "department_assigned",
        "dispatch_visible", "pm_visible", "operations_visible",
        "activated",
    )

    async def advance_onboarding(
        self,
        asset_id: str,
        *,
        step: str,
        actor: str,
        note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a single onboarding step as complete. Persists a step row in
        `asset_onboarding_steps` AND mirrors the latest step into
        equipment_master.onboarding.{step}=true for fast read. Asset
        becomes active only after `step=activated` is completed.
        """
        if step not in self.ONBOARDING_STEPS:
            raise ValueError(f"unknown onboarding step: {step!r}")
        doc = await self.db.equipment_master.find_one({"id": asset_id})
        if not doc:
            return None
        now = _now_iso()
        ob = (doc.get("onboarding") or {}).copy()
        ob[step] = {"completed_at": now, "actor": actor, "note": note}
        upd = {"onboarding": ob, "last_modified_by": actor, "last_modified_at": now,
               "updated_by": actor, "updated_at": now}
        if step == "activated":
            upd["is_active"] = True
            upd["active"] = True
            upd["asset_status"] = "ACTIVE"
            upd["status"] = "ACTIVE"
        await self.db.equipment_master.update_one({"id": asset_id}, {"$set": upd})
        try:
            await self.db.asset_onboarding_steps.insert_one({
                "id": _new_id(), "asset_id": asset_id, "unit_number": doc.get("unit_number"),
                "step": step, "actor": actor, "note": note, "at": now,
            })
        except Exception as e:
            logger.warning("[asset_spine] onboarding step persist failed: %s", e)
        after = await self.get_asset(asset_id)
        await self._audit(
            action=f"ASSET_ONBOARD_{step.upper()}",
            target_id=asset_id, before=None, after={"step": step},
            actor=actor, reason=note,
        )
        return after

    # ----- HEALTH --------------------------------------------------------

    async def health(self) -> Dict[str, Any]:
        """Live fleet-level counts. Cheap. Safe to call frequently."""
        total = await self.db.equipment_master.count_documents({})
        active = await self.db.equipment_master.count_documents({
            "$and": [
                {"$or": [{"is_active": True}, {"active": True}, {"is_active": {"$exists": False}}]},
                {"$or": [{"retired_at": None}, {"retired_at": {"$exists": False}}]},
            ]
        })
        retired = await self.db.equipment_master.count_documents({
            "$or": [{"is_active": False}, {"active": False}, {"asset_status": "RETIRED"}]
        })
        inactive = max(total - active - retired, 0)

        # Mapping coverage to Motive.
        # NOTE: must count rows with a *real* masci_equipment_id value,
        # not just the field being present. Auto-link seeds the row at
        # ingestion time with masci_equipment_id="" — those rows must
        # not be counted as "mapped" or coverage_pct gets stuck at
        # the count of all motive imports (e.g. 190 / 596 = 31.9 %)
        # forever instead of reflecting actual linked count.
        try:
            mapped = await self.db.asset_mappings.count_documents({
                "masci_equipment_id": {"$nin": [None, ""]},
            })
        except Exception:
            mapped = 0
        coverage_pct = round(100.0 * mapped / max(active, 1), 1) if active > 0 else 0.0
        unmapped = max(active - mapped, 0)

        try:
            queue_depth = await self.db.asset_mapping_proposals.count_documents({"status": {"$in": ["Imported", "Matched"]}})
        except Exception:
            queue_depth = 0

        try:
            conflicts = await self.db.project_identity_conflicts.count_documents({})
        except Exception:
            conflicts = 0

        last_run = await self.db.asset_spine_health_runs.find_one(
            {}, sort=[("at", -1)]
        ) if "asset_spine_health_runs" in await self.db.list_collection_names() else None

        return {
            "total_assets": total,
            "active_assets": active,
            "inactive_assets": inactive,
            "retired_assets": retired,
            "mapped_to_motive": mapped,
            "unmapped_to_motive": unmapped,
            "motive_coverage_pct": coverage_pct,
            "mapping_queue_depth": queue_depth,
            "conflicts": conflicts,
            "last_scan_at": (last_run or {}).get("at") if last_run else None,
            "last_scan_findings": (last_run or {}).get("findings_summary") if last_run else None,
        }

    async def scan_health(self, *, actor: str = "system") -> Dict[str, Any]:
        """
        Run all four detectors and persist the result row.

        Detectors (all READ-ONLY against operational data):
          - duplicate_vin / duplicate_serial / duplicate_unit_number
          - retired_but_active (active=false + motive event < 72h)
          - orphaned (active=true + no motive_event in 30 days
                     AND no inspection in 30 days)
          - unsynced (active=true but no asset_mappings entry)
        """
        from services.asset_spine_detection import run_detectors  # local import: optional
        findings = await run_detectors(self.db)
        run = {
            "id": _new_id(),
            "at": _now_iso(),
            "actor": actor,
            "findings_summary": {
                "duplicates": len(findings.get("duplicates", [])),
                "retired_but_active": len(findings.get("retired_but_active", [])),
                "orphaned": len(findings.get("orphaned", [])),
                "unsynced": len(findings.get("unsynced", [])),
            },
            "findings": findings,
        }
        try:
            await self.db.asset_spine_health_runs.insert_one(run)
        except Exception as e:
            logger.warning("[asset_spine] health run persist failed: %s", e)
        # motor.insert_one mutates `run` with _id — strip it before returning.
        run.pop("_id", None)
        return run
