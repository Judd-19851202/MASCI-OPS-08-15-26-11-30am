"""Phase 8B — CSV import for trench safety assets.

Strict adoption of the certified write path:
  • POST /import/preview parses + validates a CSV body without writing
    anything; returns a per-row diagnosis (will_insert / duplicate /
    error / skipped) so the operator can confirm before committing.
  • POST /import commits validated rows through the SAME create logic
    used by /trench-safety/assets — no parallel insert path. Each row
    is persisted via insert_one + upsert_equipment_master_mirror +
    write_audit, identical to the single-asset create endpoint.

No new collection. No parallel state machine. Duplicates are detected
by asset_id against the live registry.
"""
from __future__ import annotations

import csv
import io
import uuid
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ._helpers import (
    now_iso,
    upsert_equipment_master_mirror,
    write_audit,
)
from ._models import (
    ASSET_TYPES,
    CONDITIONS,
    OPERATIONAL_STATUSES,
)


# ────────────────────────────────────────────────────────────────────────
# Payload schemas
# ────────────────────────────────────────────────────────────────────────

class ImportRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    row_index: int
    asset_id: str = ""
    asset_type: str = "Trench Box"
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    size: str = ""
    color: str = ""
    condition: str = "Good"
    notes: str = ""
    yard_location: str = "MASCI Yard"
    # Road plate physical
    length_in: Optional[float] = None
    width_in: Optional[float] = None
    thickness_in: Optional[float] = None
    weight_lbs: Optional[float] = None
    material: Optional[str] = None
    rated_capacity_lb: Optional[float] = None
    markings: Optional[str] = None
    anti_skid_status: Optional[str] = None


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    csv_text: str = Field(min_length=1)


# CSV column → asset field mapping. Header names are lower-cased and
# stripped before lookup. Extra columns are ignored.
_HEADER_ALIASES = {
    "asset id": "asset_id", "asset_id": "asset_id", "id": "asset_id",
    "asset type": "asset_type", "asset_type": "asset_type", "type": "asset_type",
    "manufacturer": "manufacturer", "make": "manufacturer",
    "model": "model",
    "serial number": "serial_number", "serial_number": "serial_number", "serial": "serial_number",
    "size": "size",
    "color": "color", "colour": "color",
    "condition": "condition",
    "notes": "notes",
    "yard": "yard_location", "yard_location": "yard_location", "location": "yard_location",
    # Road plate
    "length (in)": "length_in", "length_in": "length_in", "length": "length_in",
    "width (in)": "width_in", "width_in": "width_in", "width": "width_in",
    "thickness (in)": "thickness_in", "thickness_in": "thickness_in", "thickness": "thickness_in",
    "weight (lb)": "weight_lbs", "weight_lbs": "weight_lbs", "weight": "weight_lbs",
    "material": "material",
    "rated capacity (lb)": "rated_capacity_lb", "rated_capacity_lb": "rated_capacity_lb", "capacity": "rated_capacity_lb",
    "markings": "markings",
    "anti-skid": "anti_skid_status", "anti_skid_status": "anti_skid_status", "antiskid": "anti_skid_status",
}

_NUMERIC_FIELDS = {
    "length_in", "width_in", "thickness_in", "weight_lbs", "rated_capacity_lb",
}


def _parse_csv(csv_text: str) -> List[Dict[str, Any]]:
    """Parse a CSV body into a list of partial-asset dicts.

    Tolerant: ignores unknown columns, blank trailing rows. Numeric
    fields are coerced to float; condition/asset_type values pass
    through unchanged for the validator.
    """
    rows: List[Dict[str, Any]] = []
    reader = csv.reader(io.StringIO(csv_text))
    headers: List[str] = []
    for raw_idx, raw in enumerate(reader):
        if raw_idx == 0:
            headers = [(h or "").strip().lower() for h in raw]
            continue
        if not raw or all(not (c or "").strip() for c in raw):
            continue
        rec: Dict[str, Any] = {"row_index": raw_idx}
        for i, cell in enumerate(raw):
            if i >= len(headers):
                break
            key = _HEADER_ALIASES.get(headers[i])
            if not key:
                continue
            v = (cell or "").strip()
            if not v:
                continue
            if key in _NUMERIC_FIELDS:
                try:
                    rec[key] = float(v)
                except ValueError:
                    rec[key] = v  # keep raw; validator will flag
            else:
                rec[key] = v
        rows.append(rec)
    return rows


def _validate_row(rec: Dict[str, Any], existing_ids: Set[str]) -> Dict[str, Any]:
    """Return a diagnosis dict: {status, errors[], asset_id, ...}.

    Status ∈ { will_insert, duplicate, error, skipped }.
    """
    errors: List[str] = []
    asset_id = (rec.get("asset_id") or "").strip().upper()
    asset_type = rec.get("asset_type") or "Trench Box"
    condition = rec.get("condition") or "Good"
    if not asset_id:
        errors.append("asset_id is required")
    if asset_type not in ASSET_TYPES:
        errors.append(f"asset_type {asset_type!r} not in {list(ASSET_TYPES)}")
    if condition not in CONDITIONS:
        errors.append(f"condition {condition!r} not in {list(CONDITIONS)}")
    for f in _NUMERIC_FIELDS:
        if f in rec and not isinstance(rec[f], (int, float)):
            errors.append(f"{f} must be numeric")
    if errors:
        return {
            "row_index": rec.get("row_index"),
            "asset_id": asset_id,
            "asset_type": asset_type,
            "status": "error",
            "errors": errors,
        }
    if asset_id in existing_ids:
        return {
            "row_index": rec.get("row_index"),
            "asset_id": asset_id,
            "asset_type": asset_type,
            "status": "duplicate",
            "errors": [],
        }
    return {
        "row_index": rec.get("row_index"),
        "asset_id": asset_id,
        "asset_type": asset_type,
        "status": "will_insert",
        "errors": [],
    }


def register_import_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
) -> None:

    @api_router.post("/trench-safety/assets/import/preview")
    async def import_preview(
        body: ImportRequest,
        _actor: dict = Depends(require_safety_or_admin),
    ):
        rows = _parse_csv(body.csv_text)
        if len(rows) > 500:
            raise HTTPException(413, "Import limited to 500 rows per file")
        existing = await db.trench_safety_assets.find({}, {"_id": 0, "asset_id": 1}).to_list(5000)
        existing_ids: Set[str] = {(d.get("asset_id") or "").upper() for d in existing}
        diagnoses = [_validate_row(r, existing_ids) for r in rows]
        # Also detect inline duplicates (same asset_id appearing twice in CSV)
        seen: Dict[str, int] = {}
        for d in diagnoses:
            aid = d["asset_id"]
            if not aid:
                continue
            if aid in seen and d["status"] == "will_insert":
                d["status"] = "error"
                d["errors"] = ["duplicate asset_id within file"]
            seen[aid] = d["row_index"]
        counts = {"will_insert": 0, "duplicate": 0, "error": 0}
        for d in diagnoses:
            counts[d["status"]] = counts.get(d["status"], 0) + 1
        return {
            "total_rows": len(rows),
            "counts": counts,
            "diagnoses": diagnoses,
            "raw_rows": rows,
        }

    @api_router.post("/trench-safety/assets/import")
    async def import_commit(
        body: ImportRequest,
        actor: dict = Depends(require_safety_or_admin),
    ):
        rows = _parse_csv(body.csv_text)
        if len(rows) > 500:
            raise HTTPException(413, "Import limited to 500 rows per file")
        existing = await db.trench_safety_assets.find({}, {"_id": 0, "asset_id": 1}).to_list(5000)
        existing_ids: Set[str] = {(d.get("asset_id") or "").upper() for d in existing}
        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "import"
        inserted: List[str] = []
        skipped: List[Dict[str, Any]] = []
        for r in rows:
            diag = _validate_row(r, existing_ids)
            if diag["status"] != "will_insert":
                skipped.append(diag)
                continue
            # Build the same doc shape `assets.create_asset` would.
            aid = diag["asset_id"]
            doc: Dict[str, Any] = {
                "id": str(uuid.uuid4()),
                "asset_id": aid,
                "asset_category": "Trench Safety",
                "asset_type": r.get("asset_type") or "Trench Box",
                "manufacturer": r.get("manufacturer") or "",
                "model": r.get("model") or "",
                "serial_number": r.get("serial_number") or "",
                "size": r.get("size") or "",
                "color": r.get("color") or "",
                "condition": r.get("condition") or "Good",
                "operational_status": "Available",
                "current_location": r.get("yard_location") or "MASCI Yard",
                "yard_location": r.get("yard_location") or "MASCI Yard",
                "notes": r.get("notes") or "",
                "qr_code_value": aid,
                "qr_url": f"/trench-safety/assets/{aid}",
                "tabulated_data_file_id": None,
                "tabulated_data_filename": "",
                "tabulated_data_missing": True,
                "last_inspection_at": None,
                "next_inspection_due": None,
                "last_repair_at": None,
                "certification_expires_at": None,
                "missing_serial_number": not bool(r.get("serial_number")),
                "missing_manufacturer": not bool(r.get("manufacturer")),
                "needs_review": False,
                "requires_certification": False,
                "is_active": True,
                "retired_at": None,
                "retired_reason": None,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "created_by": f"csv_import:{actor_email}",
                "updated_by": f"csv_import:{actor_email}",
                # Road plate optional fields
                "length_in": r.get("length_in"),
                "width_in": r.get("width_in"),
                "thickness_in": r.get("thickness_in"),
                "weight_lbs": r.get("weight_lbs"),
                "material": r.get("material"),
                "rated_capacity_lb": r.get("rated_capacity_lb"),
                "markings": r.get("markings"),
                "anti_skid_status": r.get("anti_skid_status"),
            }
            await db.trench_safety_assets.insert_one(doc)
            doc.pop("_id", None)
            await upsert_equipment_master_mirror(db, doc)
            await write_audit(
                db, kind="trench_asset_created", asset_id=aid,
                actor=actor, detail={
                    "source": "csv_import",
                    "asset_type": doc["asset_type"],
                    "row_index": r.get("row_index"),
                },
            )
            inserted.append(aid)
            existing_ids.add(aid)
        # Single batch audit summary
        await write_audit(
            db, kind="trench_csv_import_batch",
            asset_id="(batch)",
            actor=actor,
            detail={
                "inserted_count": len(inserted),
                "skipped_count": len(skipped),
                "inserted_ids": inserted[:50],
            },
        )
        return {
            "inserted": inserted,
            "inserted_count": len(inserted),
            "skipped": skipped,
            "skipped_count": len(skipped),
        }
