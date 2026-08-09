from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from lib.synthetic_hr_filter import apply_synthetic_hr_exclusion


EMPLOYEE_PREFIX = "EMP"
EMPLOYEE_WIDTH = 6

EQUIPMENT_PREFIX_BY_HINT = {
    "truck": "TRK",
    "haul truck": "TRK",
    "pickup": "PKU",
    "trailer": "TRL",
    "excavator": "EXC",
    "dozer": "DOZ",
    "loader": "LDR",
    "skid": "SKD",
    "generator": "GEN",
    "compactor": "CMP",
    "roller": "ROL",
    "forklift": "LFT",
    "backhoe": "BHO",
    "light tower": "LGT",
    "laser": "LSR",
    "sweeper": "SWP",
}


def normalize_token(raw: Any) -> str:
    return re.sub(r"\s+", " ", str(raw or "").strip())


def upper_token(raw: Any) -> str:
    return normalize_token(raw).upper()


def extract_sequence(raw: str, *, prefix: str) -> Optional[int]:
    m = re.match(rf"^{re.escape(prefix)}-(\d+)$", upper_token(raw))
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def next_employee_id(existing_ids: Set[str]) -> str:
    max_n = 0
    for raw in existing_ids:
        seq = extract_sequence(raw, prefix=EMPLOYEE_PREFIX)
        if seq is not None:
            max_n = max(max_n, seq)
    return f"{EMPLOYEE_PREFIX}-{max_n + 1:0{EMPLOYEE_WIDTH}d}"


def classify_equipment_prefix(doc: Dict[str, Any]) -> str:
    hay = " ".join(
        upper_token(doc.get(k))
        for k in ("preop_equipment_type", "category", "display_label", "make", "model")
        if normalize_token(doc.get(k))
    ).lower()
    for needle, prefix in EQUIPMENT_PREFIX_BY_HINT.items():
        if needle in hay:
            return prefix
    return "EQP"


def canonicalize_existing_unit(doc: Dict[str, Any]) -> Optional[str]:
    candidates = [
        normalize_token(doc.get("unit_number")),
        normalize_token(doc.get("asset_number")),
        normalize_token(doc.get("display_label")),
    ]
    for raw in candidates:
        if not raw:
            continue
        compact = upper_token(raw)
        # Reject clearly synthetic/test identifiers that should never become canonical production unit numbers.
        if compact.startswith("TB-") or compact.startswith("TEST-") or compact.startswith("VALIDATION"):
            continue
        if len(compact) <= 2:
            continue
        # Plain descriptive labels are not stable unit numbers; keep them for context only.
        if re.fullmatch(r"[0-9]{4}\s+[A-Z0-9\-#/ ]+", compact):
            continue
        if " " in compact and not re.match(r"^[A-Z]{2,4}-\d{3,6}$", compact):
            continue
        # If it already looks like a canonical unit, preserve it.
        if re.match(r"^[A-Z0-9][A-Z0-9\-/# ]{2,63}$", compact):
            return compact
    return None


def next_equipment_unit(prefix: str, existing_tokens: Set[str]) -> str:
    prefix = upper_token(prefix) or "EQP"
    max_n = 0
    for raw in existing_tokens:
        m = re.match(rf"^{re.escape(prefix)}-(\d{{3,6}})$", upper_token(raw))
        if not m:
            continue
        try:
            max_n = max(max_n, int(m.group(1)))
        except Exception:
            continue
    width = 6 if prefix == "EQP" else 3
    return f"{prefix}-{max_n + 1:0{width}d}"


async def preview_master_data_backfill(db: Any) -> Dict[str, Any]:
    employees = await db.employees.find(apply_synthetic_hr_exclusion({}), {"_id": 0, "id": 1, "name": 1, "employee_id": 1, "active": 1}).to_list(length=None)
    equipment = await db.equipment_master.find({}, {"_id": 0, "id": 1, "unit_number": 1, "asset_number": 1, "display_label": 1, "preop_equipment_type": 1, "category": 1, "make": 1, "model": 1, "active": 1}).to_list(length=None)

    existing_employee_ids = {upper_token(row.get("employee_id")) for row in employees if normalize_token(row.get("employee_id"))}
    employee_plan: List[Dict[str, Any]] = []
    for row in sorted(employees, key=lambda r: upper_token(r.get("name") or r.get("id"))):
        is_active = (
            row.get("active") is True
            or row.get("is_active") is True
            or ("active" not in row and "is_active" not in row)
        )
        if not is_active:
            continue
        if normalize_token(row.get("employee_id")):
            continue
        new_id = next_employee_id(existing_employee_ids)
        existing_employee_ids.add(new_id)
        employee_plan.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "employee_id": new_id,
        })

    existing_equipment_tokens: Set[str] = set()
    for row in equipment:
        for field in ("unit_number", "asset_number", "display_label"):
            val = upper_token(row.get(field))
            if val:
                existing_equipment_tokens.add(val)

    equipment_plan: List[Dict[str, Any]] = []
    for row in sorted(equipment, key=lambda r: upper_token(r.get("display_label") or r.get("id"))):
        if normalize_token(row.get("unit_number")):
            continue
        candidate = canonicalize_existing_unit(row)
        source = "canonicalized_existing_identifier" if candidate else "generated_prefix_sequence"
        if candidate and candidate not in existing_equipment_tokens:
            new_unit = candidate
        else:
            prefix = classify_equipment_prefix(row)
            new_unit = next_equipment_unit(prefix, existing_equipment_tokens)
        existing_equipment_tokens.add(new_unit)
        equipment_plan.append({
            "id": row.get("id"),
            "display_label": row.get("display_label"),
            "category": row.get("category"),
            "preop_equipment_type": row.get("preop_equipment_type"),
            "make": row.get("make"),
            "model": row.get("model"),
            "asset_number": row.get("asset_number"),
            "unit_number": new_unit,
            "source": source,
        })

    return {
        "employee_plan": employee_plan,
        "equipment_plan": equipment_plan,
        "summary": {
            "employees_missing_employee_id": len(employee_plan),
            "equipment_missing_unit_number": len(equipment_plan),
        },
    }


async def apply_master_data_backfill(db: Any) -> Dict[str, Any]:
    plan = await preview_master_data_backfill(db)
    employee_updates = 0
    for row in plan["employee_plan"]:
        res = await db.employees.update_one({"id": row["id"]}, {"$set": {"employee_id": row["employee_id"]}})
        employee_updates += int(res.modified_count or 0)

    equipment_updates = 0
    for row in plan["equipment_plan"]:
        res = await db.equipment_master.update_one({"id": row["id"]}, {"$set": {"unit_number": row["unit_number"]}})
        equipment_updates += int(res.modified_count or 0)

    return {
        "ok": True,
        "employee_updates": employee_updates,
        "equipment_updates": equipment_updates,
        "summary": plan["summary"],
        "employee_plan_sample": plan["employee_plan"][:20],
        "equipment_plan_sample": plan["equipment_plan"][:20],
    }


__all__ = [
    "apply_master_data_backfill",
    "preview_master_data_backfill",
]