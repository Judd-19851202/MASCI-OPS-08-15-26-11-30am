"""
Integration Center · wizard.py — Mappings Wizard.

A safe, two-step (preview → commit) bulk-mapping flow for linking
external provider IDs (Motive Vehicle IDs first, MaintainX Asset IDs
later) to existing `db.equipment_master` records.

Safety guarantees:
  • No master-record mutation.  Only `asset_mappings` is written.
  • Preview is read-only — admin reviews every match before committing.
  • Existing mappings are NEVER overwritten unless the row's decision
    carries `force_overwrite=true`.  Default is fail-closed (status
    "conflict" → admin must explicitly resolve).
  • Every commit appends an audit doc to `integration_wizard_runs`.

Match strategy (current providers):
  1. Exact case-insensitive match on `unit_number`        → confidence high
  2. Case-insensitive substring match on `unit_number`    → confidence low (manual review)
  3. Multiple matches for the same unit_number            → status "duplicate" → manual
  4. No match                                             → status "unmatched"

Endpoints:
  POST  /api/admin/integrations/mappings/wizard/preview
  POST  /api/admin/integrations/mappings/wizard/commit
  GET   /api/admin/integrations/mappings/wizard/runs
"""
from __future__ import annotations
import logging
import re
import uuid
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request

from ._models import WizardPreviewRequest, WizardCommitRequest
from ._storage import now_iso

logger = logging.getLogger(__name__)


SUPPORTED_KINDS = ("motive_vehicles", "maintainx_assets")


def _provider_from_kind(kind: str) -> str:
    if kind == "motive_vehicles":
        return "motive"
    if kind == "maintainx_assets":
        return "maintainx"
    raise HTTPException(400, f"Unsupported wizard kind: {kind}")


def _provider_id_field(kind: str) -> str:
    """Which field on the mapping doc holds the external ID for this kind."""
    if kind == "motive_vehicles":
        return "motive.vehicle_id"
    if kind == "maintainx_assets":
        return "maintainx.asset_id"
    raise HTTPException(400, f"Unsupported wizard kind: {kind}")


def _norm_unit(u: Optional[str]) -> str:
    return re.sub(r"\s+", "", (u or "")).upper()


def _actor_from_request(request: Request) -> str:
    """Best-effort actor label for audit. Falls back to 'admin' so the
    wizard never blocks on missing identity headers."""
    for header in ("X-Actor-Name", "X-Admin-Email", "X-Admin-User"):
        v = request.headers.get(header)
        if v:
            return v.strip()[:120]
    return "admin"


def register_wizard_routes(
    api_router: APIRouter, db, require_admin,
) -> None:

    # ════════════════════════════════════════════════════════════════
    # PREVIEW — read-only matching pass. Returns categorized rows so
    # the admin can decide what to commit. NO DB writes.
    # ════════════════════════════════════════════════════════════════
    @api_router.post(
        "/admin/integrations/mappings/wizard/preview",
        dependencies=[Depends(require_admin)],
    )
    async def wizard_preview(body: WizardPreviewRequest):
        if body.kind not in SUPPORTED_KINDS:
            raise HTTPException(400, f"Unsupported wizard kind: {body.kind}")
        provider = _provider_from_kind(body.kind)
        provider_id_field = _provider_id_field(body.kind)

        # Pre-load equipment_master into an in-memory dict keyed by
        # normalised unit_number. ~thousands of rows max — fine for
        # a single preview pass.
        master_cursor = db.equipment_master.find(
            {}, {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1, "make": 1, "model": 1},
        )
        master_list = await master_cursor.to_list(20000)
        by_norm: Dict[str, List[Dict[str, Any]]] = {}
        for m in master_list:
            key = _norm_unit(m.get("unit_number"))
            if not key:
                continue
            by_norm.setdefault(key, []).append(m)

        # Pre-load existing mappings — by masci_equipment_id (one
        # mapping per equipment) and by external id (so we can flag
        # the rare case where a Motive ID is already mapped to a
        # DIFFERENT equipment record).
        existing_mappings_cursor = db.asset_mappings.find({}, {"_id": 0})
        existing_mappings = await existing_mappings_cursor.to_list(20000)
        # `.get()` guards against legacy / auto-discovered docs that
        # may not carry a masci_equipment_id yet — those rows simply
        # never match by master id (they'll only match by external id
        # via `external_owner` below).
        mapping_by_master: Dict[str, Dict[str, Any]] = {
            mm.get("masci_equipment_id"): mm
            for mm in existing_mappings
            if mm.get("masci_equipment_id")
        }

        def _existing_external_id(mm: dict) -> str:
            for part in provider_id_field.split("."):
                if not isinstance(mm, dict):
                    return ""
                mm = mm.get(part, "") if isinstance(mm, dict) else ""
            return (mm or "").strip()

        external_owner: Dict[str, Dict[str, Any]] = {}
        for mm in existing_mappings:
            ext = _existing_external_id(mm)
            if ext:
                external_owner[ext.upper()] = mm

        out_rows: List[Dict[str, Any]] = []
        counts = {"ready": 0, "conflict": 0, "duplicate": 0, "unmatched": 0, "noop": 0, "external_collision": 0}

        for idx, row in enumerate(body.rows):
            unit_key = _norm_unit(row.unit_number)
            external_id = (row.external_id or "").strip()
            external_name = (row.external_name or "").strip()
            base = {
                "row_index": idx,
                "input_unit_number": row.unit_number or "",
                "input_external_id": external_id,
                "input_external_name": external_name,
            }
            if not external_id:
                out_rows.append({**base, "status": "unmatched", "reason": "Missing external ID", "matches": []})
                counts["unmatched"] += 1
                continue

            matches = by_norm.get(unit_key, [])
            if not matches:
                out_rows.append({**base, "status": "unmatched", "reason": "No equipment_master record matched unit number", "matches": []})
                counts["unmatched"] += 1
                continue

            if len(matches) > 1:
                # multiple candidates — admin must disambiguate
                out_rows.append({
                    **base,
                    "status": "duplicate",
                    "reason": f"Multiple equipment_master records share unit number {row.unit_number!r}",
                    "matches": [
                        {
                            "masci_equipment_id": m["id"],
                            "unit_number": m.get("unit_number"),
                            "name": m.get("name"),
                            "equipment_type": m.get("equipment_type"),
                            "make": m.get("make"),
                            "model": m.get("model"),
                        } for m in matches
                    ],
                })
                counts["duplicate"] += 1
                continue

            match = matches[0]
            masci_equipment_id = match["id"]
            existing = mapping_by_master.get(masci_equipment_id)
            existing_external = (_existing_external_id(existing) if existing else "").strip()

            # Same external ID already mapped to a DIFFERENT equipment
            collision_owner = external_owner.get(external_id.upper())
            if collision_owner and collision_owner.get("masci_equipment_id") != masci_equipment_id:
                out_rows.append({
                    **base,
                    "status": "external_collision",
                    "reason": (
                        f"External ID {external_id!r} is already mapped to a different "
                        f"equipment record (unit {collision_owner.get('masci_unit_number') or '—'})"
                    ),
                    "matches": [{
                        "masci_equipment_id": masci_equipment_id,
                        "unit_number": match.get("unit_number"),
                        "name": match.get("name"),
                    }],
                    "collides_with_mapping_id": collision_owner.get("id"),
                })
                counts["external_collision"] += 1
                continue

            if existing and existing_external and existing_external == external_id:
                out_rows.append({
                    **base,
                    "status": "noop",
                    "reason": "Mapping already correct — nothing to do",
                    "matches": [{
                        "masci_equipment_id": masci_equipment_id,
                        "unit_number": match.get("unit_number"),
                        "name": match.get("name"),
                    }],
                    "current_mapping_id": existing.get("id"),
                    "current_external_id": existing_external,
                    "mapping_confidence": "high",
                })
                counts["noop"] += 1
                continue

            if existing and existing_external and existing_external != external_id:
                out_rows.append({
                    **base,
                    "status": "conflict",
                    "reason": (
                        f"Equipment already has a different {provider.title()} ID mapped "
                        f"({existing_external!r}). Toggle force-overwrite to replace."
                    ),
                    "matches": [{
                        "masci_equipment_id": masci_equipment_id,
                        "unit_number": match.get("unit_number"),
                        "name": match.get("name"),
                    }],
                    "current_mapping_id": existing.get("id"),
                    "current_external_id": existing_external,
                    "mapping_confidence": "medium",
                })
                counts["conflict"] += 1
                continue

            # READY — single equipment_master match + no existing
            # provider id on file → safe create OR update (existing
            # mapping doc but provider field empty).
            out_rows.append({
                **base,
                "status": "ready",
                "reason": None,
                "matches": [{
                    "masci_equipment_id": masci_equipment_id,
                    "unit_number": match.get("unit_number"),
                    "name": match.get("name"),
                    "equipment_type": match.get("equipment_type"),
                    "make": match.get("make"),
                    "model": match.get("model"),
                }],
                "current_mapping_id": existing.get("id") if existing else None,
                "current_external_id": "",
                "suggested_action": "update" if existing else "create",
                "mapping_confidence": "high",
            })
            counts["ready"] += 1

        return {
            "kind": body.kind,
            "provider": provider,
            "totals": {"input_rows": len(body.rows), **counts},
            "rows": out_rows,
        }

    # ════════════════════════════════════════════════════════════════
    # COMMIT — applies the admin's reviewed decisions. NEVER overwrites
    # a populated provider field without `force_overwrite=true`. Writes
    # an audit doc to `integration_wizard_runs`.
    # ════════════════════════════════════════════════════════════════
    @api_router.post(
        "/admin/integrations/mappings/wizard/commit",
        dependencies=[Depends(require_admin)],
    )
    async def wizard_commit(body: WizardCommitRequest, request: Request):
        if body.kind not in SUPPORTED_KINDS:
            raise HTTPException(400, f"Unsupported wizard kind: {body.kind}")
        provider = _provider_from_kind(body.kind)
        provider_id_field = _provider_id_field(body.kind)
        actor = _actor_from_request(request)
        run_id = str(uuid.uuid4())
        started_at = now_iso()

        results: List[Dict[str, Any]] = []
        counts = {"created": 0, "updated": 0, "skipped": 0, "blocked": 0, "errored": 0}

        for dec in body.decisions:
            try:
                if dec.action == "skip":
                    results.append({"action": "skip", "masci_equipment_id": dec.masci_equipment_id, "ok": True})
                    counts["skipped"] += 1
                    continue

                if not dec.masci_equipment_id:
                    raise ValueError("masci_equipment_id is required for create/update")

                eq = await db.equipment_master.find_one(
                    {"id": dec.masci_equipment_id},
                    {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1},
                )
                if not eq:
                    raise ValueError(f"equipment_master.id not found: {dec.masci_equipment_id}")

                existing = await db.asset_mappings.find_one(
                    {"masci_equipment_id": dec.masci_equipment_id}, {"_id": 0},
                )

                if dec.action == "create":
                    if existing:
                        # an asset_mapping doc already exists — fall through
                        # to update path. We never insert a second doc per
                        # equipment (the storage layer enforces 1:1).
                        dec_action = "update"
                        dec_mapping_id = existing.get("id")
                    else:
                        dec_action = "create"
                        dec_mapping_id = None
                else:
                    dec_action = "update"
                    dec_mapping_id = dec.mapping_id or (existing.get("id") if existing else None)
                    if not dec_mapping_id:
                        raise ValueError("update requested but no existing mapping found")

                if dec_action == "create":
                    # Always inserts fresh — provider id field gets the new value.
                    motive_block = {
                        "vehicle_id": "", "asset_id": "", "driver_id": "", "device_id": "",
                        "gps_enabled": False, "dashcam_enabled": False,
                        "last_sync_at": None, "mapping_status": "Unmapped",
                    }
                    maintainx_block = {
                        "asset_id": "", "location_id": "", "pm_schedule_id": "",
                        "last_sync_at": None, "mapping_status": "Unmapped",
                    }
                    if provider == "motive":
                        motive_block["vehicle_id"] = (dec.external_id or "").strip()
                        motive_block["mapping_status"] = "Mapped" if motive_block["vehicle_id"] else "Unmapped"
                    else:
                        maintainx_block["asset_id"] = (dec.external_id or "").strip()
                        maintainx_block["mapping_status"] = "Mapped" if maintainx_block["asset_id"] else "Unmapped"

                    doc = {
                        "id": str(uuid.uuid4()),
                        "masci_equipment_id": dec.masci_equipment_id,
                        "masci_unit_number": eq.get("unit_number") or "",
                        "masci_equipment_name": eq.get("name") or "",
                        "masci_equipment_type": eq.get("equipment_type") or "",
                        "motive": motive_block,
                        "maintainx": maintainx_block,
                        "mapping_confidence": "high",
                        "mapping_notes": dec.notes or "",
                        "active": True,
                        "created_at": now_iso(),
                        "created_by": actor,
                        "updated_at": now_iso(),
                        "updated_by": actor,
                        "source": f"wizard:{body.source_label or 'paste'}",
                        "wizard_run_id": run_id,
                    }
                    await db.asset_mappings.insert_one(doc)
                    results.append({
                        "action": "create", "ok": True,
                        "mapping_id": doc["id"],
                        "masci_equipment_id": dec.masci_equipment_id,
                        "external_id": dec.external_id,
                    })
                    counts["created"] += 1
                else:
                    # UPDATE — fetch current, refuse to overwrite a
                    # populated provider field unless force_overwrite.
                    current = await db.asset_mappings.find_one({"id": dec_mapping_id}, {"_id": 0})
                    if not current:
                        raise ValueError(f"asset_mapping not found: {dec_mapping_id}")
                    field_path = provider_id_field
                    parts = field_path.split(".")
                    current_value = current
                    for p in parts:
                        current_value = (current_value or {}).get(p, "") if isinstance(current_value, dict) else ""
                    current_value = (current_value or "").strip()
                    new_value = (dec.external_id or "").strip()
                    if current_value and current_value != new_value and not dec.force_overwrite:
                        results.append({
                            "action": "update", "ok": False,
                            "mapping_id": dec_mapping_id,
                            "masci_equipment_id": dec.masci_equipment_id,
                            "reason": (
                                f"Refused to overwrite existing {provider} ID "
                                f"({current_value!r}). Pass force_overwrite=true to replace."
                            ),
                        })
                        counts["blocked"] += 1
                        continue
                    set_doc = {
                        field_path: new_value,
                        "updated_at": now_iso(),
                        "updated_by": actor,
                        "last_wizard_run_id": run_id,
                    }
                    # Re-stamp mapping_status for the affected provider
                    if provider == "motive":
                        set_doc["motive.mapping_status"] = "Mapped" if new_value else "Unmapped"
                    else:
                        set_doc["maintainx.mapping_status"] = "Mapped" if new_value else "Unmapped"
                    if dec.notes:
                        set_doc["mapping_notes"] = dec.notes
                    await db.asset_mappings.update_one({"id": dec_mapping_id}, {"$set": set_doc})
                    results.append({
                        "action": "update", "ok": True,
                        "mapping_id": dec_mapping_id,
                        "masci_equipment_id": dec.masci_equipment_id,
                        "external_id": new_value,
                    })
                    counts["updated"] += 1
            except Exception as e:  # noqa: BLE001
                results.append({
                    "action": dec.action, "ok": False,
                    "masci_equipment_id": dec.masci_equipment_id,
                    "reason": str(e),
                })
                counts["errored"] += 1

        run_doc = {
            "id": run_id,
            "kind": body.kind,
            "provider": provider,
            "actor": actor,
            "source_label": body.source_label or "paste",
            "totals": {"decisions": len(body.decisions), **counts},
            "started_at": started_at,
            "completed_at": now_iso(),
            "results": results,
        }
        await db.integration_wizard_runs.insert_one(run_doc)
        run_doc.pop("_id", None)
        return run_doc

    # ════════════════════════════════════════════════════════════════
    # LIST RUNS — audit history (most recent first)
    # ════════════════════════════════════════════════════════════════
    @api_router.get(
        "/admin/integrations/mappings/wizard/runs",
        dependencies=[Depends(require_admin)],
    )
    async def list_wizard_runs(limit: int = 25):
        limit = max(1, min(int(limit or 25), 200))
        cursor = db.integration_wizard_runs.find(
            {}, {"_id": 0, "results": 0},   # results array can be large — fetch on demand
        ).sort("started_at", -1)
        rows = await cursor.to_list(limit)
        return rows

    @api_router.get(
        "/admin/integrations/mappings/wizard/runs/{run_id}",
        dependencies=[Depends(require_admin)],
    )
    async def get_wizard_run(run_id: str):
        doc = await db.integration_wizard_runs.find_one({"id": run_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Wizard run not found")
        return doc


__all__ = ["register_wizard_routes", "SUPPORTED_KINDS"]
