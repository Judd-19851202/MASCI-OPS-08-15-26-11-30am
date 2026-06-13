"""Track 13.31B-D5.1 BUILD · Smart Pre-Op / DVIR canonical write stamp.

Single helper called by both:
  • routes/equipment.py → /api/equipment-inspections (Pre-Op)
  • routes/fleet_ops.py → /api/fleet/inspections (DVIR)

After an inspection row is inserted, this helper resolves the canonical
classification for the submitted unit through `equipment_master` +
`services.asset_taxonomy.resolve_classification` and patches the row in
place with additive canonical fields.

Doctrine:
  • Equipment Master is canonical.
  • Asset Spine is the read-side resolver.
  • Pre-Op / DVIR are write-side consumers — they stamp, they do not
    classify on their own.
  • Legacy fields stay untouched for historical compatibility.
  • Unknown units stay unknown — no fabrication.

Output fields stamped onto the inspection row:
  asset_id                       (equipment_master.id)
  asset_class                    (canonical)
  asset_type                     (canonical)
  asset_subtype                  (canonical, optional)
  taxonomy_source                (canonical|legacy_mapped|needs_review|unmatched)
  taxonomy_verified              (bool · True only when equipment_master row is verified)
  classification_status          (verified|mapped|needs_review|unmatched)
  taxonomy_review_reason         (string|None)
  legacy_equipment_type          (preserved from original submission for audit)
  template_status                (template_present|missing_template)
  template_recommended           (canonical asset_type chosen for template routing,
                                  or None when needs_review/unmatched)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from services.asset_taxonomy import resolve_classification
from services.inspection_templates import (
    has_template as _registry_has_template,
    template_key_for as _registry_template_key_for,
    template_status_for as _registry_template_status_for,
)

logger = logging.getLogger(__name__)

# Track 13.31B-D5.2 retired the hand-maintained whitelists in favour of
# the canonical registry in ``services.inspection_templates``. The two
# constants below remain exported for backward-compat with D5.1 callers
# (they now resolve through the registry, restricted by ``applies_to``).
def _types_for(applies_to: str) -> frozenset:
    from services.inspection_templates import INSPECTION_TEMPLATES as _R
    return frozenset(at for at, t in _R.items() if t["applies_to"] == applies_to)


EXISTING_PREOP_TEMPLATES: frozenset = _types_for("pre_op")
EXISTING_DVIR_TEMPLATES: frozenset = _types_for("dvir")


async def resolve_unit_canonical(
    db, unit_number: str, legacy_equipment_type: str = "",
) -> Dict[str, Any]:
    """Look up the canonical classification for `unit_number`.

    Returns a dict suitable for $set onto an inspection row. Always
    returns the same keys so consumers don't branch on absence.
    """
    unit_number = (unit_number or "").strip()
    if not unit_number:
        return _unmatched_stamp(legacy_equipment_type=legacy_equipment_type)

    import re as _re
    eq = await db.equipment_master.find_one(
        {"unit_number": {"$regex": f"^{_re.escape(unit_number)}$", "$options": "i"}},
        {
            "_id": 0, "id": 1, "unit_number": 1,
            "asset_class": 1, "asset_type": 1, "asset_subtype": 1,
            "taxonomy_verified": 1, "taxonomy_source": 1,
            "category": 1, "type": 1, "preop_equipment_type": 1,
            "legacy_category": 1, "legacy_type": 1, "legacy_preop_equipment_type": 1,
        },
    )
    if not eq:
        return _unmatched_stamp(legacy_equipment_type=legacy_equipment_type)

    cls = resolve_classification(eq)
    src = cls["classification_source"]
    # Map resolver source → inspection-row classification_status vocabulary.
    if src == "canonical":
        status = "verified"
    elif src == "legacy_mapped":
        status = "mapped"
    else:
        status = "needs_review"

    asset_type = cls["asset_type"]
    template_present = _registry_has_template(asset_type)
    return {
        "asset_id": eq.get("id"),
        "asset_class": cls["asset_class"],
        "asset_type": asset_type,
        "asset_subtype": cls["asset_subtype"],
        "taxonomy_source": src,
        "taxonomy_verified": bool(cls["classification_verified"]),
        "classification_status": status,
        "taxonomy_review_reason": cls["review_reason"],
        "legacy_equipment_type": legacy_equipment_type or "",
        "template_status": "available" if template_present else "missing_template",
        "template_key": _registry_template_key_for(asset_type),
        "template_source": "canonical_asset_type" if template_present else None,
        "template_recommended": asset_type if status != "needs_review" else None,
    }


def _template_status_for(asset_type: Optional[str], existing: frozenset) -> str:
    # Backward-compat wrapper used only by the D5.1 callers.
    return _registry_template_status_for(asset_type)


def _unmatched_stamp(legacy_equipment_type: str = "") -> Dict[str, Any]:
    return {
        "asset_id": None,
        "asset_class": None,
        "asset_type": None,
        "asset_subtype": None,
        "taxonomy_source": "unmatched",
        "taxonomy_verified": False,
        "classification_status": "unmatched",
        "taxonomy_review_reason": "no_equipment_master_match",
        "legacy_equipment_type": legacy_equipment_type or "",
        "template_status": "missing_template",
        "template_key": None,
        "template_source": None,
        "template_recommended": None,
    }


async def stamp_inspection_canonical(
    db, inspection_id: str, unit_number: str,
    legacy_equipment_type: str = "",
    template_set: Optional[frozenset] = None,
) -> Dict[str, Any]:
    """Resolve canonical classification for `unit_number` and $set the
    canonical fields onto `equipment_inspections` row `inspection_id`.

    Returns the stamped dict (or {} if no inspection_id given). Safe to
    call fire-and-forget — exceptions are caught and logged.
    """
    if not inspection_id:
        return {}
    try:
        stamp = await resolve_unit_canonical(db, unit_number, legacy_equipment_type=legacy_equipment_type)
        if template_set is not None and stamp.get("asset_type"):
            # Restrict by applies_to (pre_op vs dvir) — if the asset_type
            # has a template that does not match the caller's surface,
            # treat as missing_template for this call. e.g. a Skid Steer
            # template is pre_op, so a DVIR caller would see missing.
            if stamp["asset_type"] not in template_set:
                stamp["template_status"] = "missing_template"
                stamp["template_source"] = None
        await db.equipment_inspections.update_one(
            {"id": inspection_id}, {"$set": stamp},
        )
        return stamp
    except Exception as exc:  # noqa: BLE001 — never abort the inspection save.
        logger.warning(
            "[inspection_classification] stamp failed inspection_id=%s unit=%s err=%s",
            inspection_id, unit_number, exc,
        )
        return {}
