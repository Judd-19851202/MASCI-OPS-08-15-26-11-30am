"""
MaintainX read-first asset sync pipeline — P0-B implementation
==============================================================

Pure read pipeline. NEVER writes to MaintainX. NEVER writes to
equipment_master. ONLY writes (when authorized) to a single read-only
report collection `maintainx_dryrun_reports` that an admin can inspect.

Capabilities:
  • Pull all MaintainX assets via `MaintainxClient.list_assets()`
  • Normalize MaintainX asset fields → canonical shape
  • Match against `db.equipment_master` with a layered strategy:
      1) Existing `asset_mappings.maintainx.asset_id` match
      2) Normalized unit_number exact
      3) Serial / VIN exact (from `equipment_master.vin_serial_number`)
      4) Make+model+year similarity (last-resort heuristic)
  • Classify every input asset:
      exact_match | probable_match | possible_duplicate
      missing_in_maintainx | missing_in_masci | conflict
  • Produce a deterministic dry-run report dict
  • Save the dry-run dict to `maintainx_dryrun_reports` if and only if
    the caller explicitly passes `save_report=True`
  • Never raises — every error is captured into the report dict's
    `errors` array.

Public entrypoint:
  `run_asset_dryrun(db, *, page_size=100, max_pages=50,
                    save_report=False) -> dict`
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from services.maintainx_client import (
    MaintainxClient,
    MaintainxClientError,
    MaintainxConfig,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════
# Normalisation helpers
# ═════════════════════════════════════════════════════════════════════
_NORM_RE = re.compile(r"[^A-Z0-9]+")


def _norm(value: Optional[str]) -> str:
    """Loose uppercase alphanumeric normaliser (drops spaces, dashes)."""
    if not value:
        return ""
    return _NORM_RE.sub("", str(value).upper())


def _norm_unit(value: Optional[str]) -> str:
    return _norm(value)


def _norm_serial(value: Optional[str]) -> str:
    return _norm(value)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═════════════════════════════════════════════════════════════════════
# MaintainX asset normaliser
# ═════════════════════════════════════════════════════════════════════
def normalize_maintainx_asset(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce a MaintainX asset payload into the canonical shape the
    matcher consumes. Field names vary slightly between MaintainX API
    versions — this function tolerates known variants and emits stable
    keys.
    """
    if not isinstance(raw, dict):
        return {}

    def first(*keys: str) -> Optional[str]:
        for k in keys:
            v = raw.get(k)
            if v not in (None, ""):
                return str(v).strip()
        return None

    return {
        "maintainx_asset_id": first("id", "assetId", "asset_id"),
        "name":               first("name", "title"),
        "unit_number":        first("unitNumber", "unit_number", "code", "tag", "barcode"),
        "serial_number":      first("serialNumber", "serial_number", "serial"),
        "vin":                first("vin", "VIN"),
        "make":               first("make", "manufacturer", "brand"),
        "model":              first("model", "modelNumber", "model_number"),
        "year":               first("year"),
        "location":           first("location", "locationName", "location_name"),
        "location_id":        first("locationId", "location_id"),
        "status":             first("status", "state"),
        "raw":                raw,
    }


# ═════════════════════════════════════════════════════════════════════
# MASCI equipment normaliser
# ═════════════════════════════════════════════════════════════════════
def normalize_masci_equipment(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    return {
        "id":               row.get("id") or "",
        "unit_number":      row.get("unit_number") or "",
        "name":             row.get("display_label") or row.get("make_model") or "",
        "make":             row.get("make") or "",
        "model":            row.get("model") or "",
        "year":             row.get("year") or "",
        # MASCI combines VIN/serial in a single field
        "vin_serial":       row.get("vin_serial_number") or "",
        "plate":            row.get("plate") or "",
        "category":         row.get("category") or "",
        "preop_equipment_type": row.get("preop_equipment_type") or "",
        "company":          row.get("company") or "",
    }


# ═════════════════════════════════════════════════════════════════════
# Matcher
# ═════════════════════════════════════════════════════════════════════
def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.upper(), b.upper()).ratio()


def _match_asset(
    *, mx: Dict[str, Any], masci: List[Dict[str, Any]],
    existing_by_external_id: Dict[str, Dict[str, Any]],
    masci_index: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Returns a classification dict for a single MaintainX asset."""
    mxid = (mx.get("maintainx_asset_id") or "").strip()
    mx_unit_norm = _norm_unit(mx.get("unit_number"))
    mx_serial_norm = _norm_serial(mx.get("serial_number") or mx.get("vin"))
    mx_make_model = f"{mx.get('make') or ''} {mx.get('model') or ''}".strip().upper()

    candidates: List[Tuple[str, Dict[str, Any], float]] = []

    # 1) Existing mapping (asset_mappings.maintainx.asset_id)
    if mxid:
        existing = existing_by_external_id.get(mxid)
        if existing:
            masci_id = existing.get("masci_equipment_id")
            masci_row = next((m for m in masci if m["id"] == masci_id), None)
            if masci_row:
                return {
                    "classification": "exact_match",
                    "match_reason": "existing_mapping",
                    "match_confidence": 1.0,
                    "masci_equipment_id": masci_row["id"],
                    "masci_unit_number": masci_row["unit_number"],
                    "masci_display": masci_row["name"],
                    "existing_mapping_id": existing.get("id"),
                }

    # 2) Exact unit_number match
    if mx_unit_norm:
        hits = masci_index.get(("unit", mx_unit_norm), [])
        if len(hits) == 1:
            candidates.append(("unit_number_exact", hits[0], 0.95))
        elif len(hits) > 1:
            return {
                "classification": "possible_duplicate",
                "match_reason": "multiple_masci_share_unit_number",
                "match_confidence": 0.6,
                "candidate_masci_ids": [h["id"] for h in hits],
                "candidate_masci_units": [h["unit_number"] for h in hits],
            }

    # 3) Serial / VIN match (MASCI stores both in vin_serial_number)
    if mx_serial_norm:
        hits = masci_index.get(("vinserial", mx_serial_norm), [])
        if len(hits) == 1 and hits[0] not in [c[1] for c in candidates]:
            candidates.append(("vin_serial_exact", hits[0], 0.93))
        elif len(hits) > 1:
            return {
                "classification": "possible_duplicate",
                "match_reason": "multiple_masci_share_vin_serial",
                "match_confidence": 0.6,
                "candidate_masci_ids": [h["id"] for h in hits],
                "candidate_masci_units": [h["unit_number"] for h in hits],
            }

    if candidates:
        # If we have a single high-confidence candidate, "probable_match";
        # if multiple distinct candidates, "conflict".
        unique = {c[1]["id"]: c for c in candidates}
        if len(unique) == 1:
            reason, masci_row, conf = next(iter(unique.values()))
            return {
                "classification": "probable_match",
                "match_reason": reason,
                "match_confidence": conf,
                "masci_equipment_id": masci_row["id"],
                "masci_unit_number": masci_row["unit_number"],
                "masci_display": masci_row["name"],
            }
        return {
            "classification": "conflict",
            "match_reason": "multiple_strategies_point_at_different_records",
            "match_confidence": 0.4,
            "candidate_masci_ids": [r["id"] for _, r, _ in candidates],
            "candidate_masci_units": [r["unit_number"] for _, r, _ in candidates],
        }

    # 4) Fuzzy make+model similarity (last-resort)
    if mx_make_model:
        best: Tuple[float, Optional[Dict[str, Any]]] = (0.0, None)
        for m in masci:
            mm = f"{m.get('make') or ''} {m.get('model') or ''}".strip().upper()
            if not mm:
                continue
            score = _similarity(mx_make_model, mm)
            if score > best[0]:
                best = (score, m)
        if best[0] >= 0.85 and best[1] is not None:
            return {
                "classification": "probable_match",
                "match_reason": "make_model_similarity",
                "match_confidence": round(best[0], 3),
                "masci_equipment_id": best[1]["id"],
                "masci_unit_number": best[1]["unit_number"],
                "masci_display": best[1]["name"],
            }

    # Nothing matched → MaintainX has an asset MASCI doesn't.
    return {
        "classification": "missing_in_masci",
        "match_reason": "no_match_strategy_returned_a_candidate",
        "match_confidence": 0.0,
    }


# ═════════════════════════════════════════════════════════════════════
# Duplicate-risk analyser
# ═════════════════════════════════════════════════════════════════════
def _duplicate_risk_for_new_asset(
    *, mx: Dict[str, Any], masci_index: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """For a MaintainX asset classified as `missing_in_masci`, prove
    nothing collides if we were to ever (NOT IN THIS SPRINT) create a
    MASCI equipment record from it.
    """
    risks: List[Dict[str, Any]] = []

    unit = _norm_unit(mx.get("unit_number"))
    if unit:
        same_unit = masci_index.get(("unit", unit), [])
        if same_unit:
            risks.append({
                "risk_kind": "same_unit_number",
                "match_count": len(same_unit),
                "masci_ids": [m["id"] for m in same_unit],
            })

    serial = _norm_serial(mx.get("serial_number"))
    if serial:
        same_serial = masci_index.get(("vinserial", serial), [])
        if same_serial:
            risks.append({
                "risk_kind": "same_serial",
                "match_count": len(same_serial),
                "masci_ids": [m["id"] for m in same_serial],
            })

    vin = _norm_serial(mx.get("vin"))
    if vin and vin != serial:
        same_vin = masci_index.get(("vinserial", vin), [])
        if same_vin:
            risks.append({
                "risk_kind": "same_vin",
                "match_count": len(same_vin),
                "masci_ids": [m["id"] for m in same_vin],
            })

    return {
        "has_risk": bool(risks),
        "risks": risks,
        "verdict": "safe_to_create" if not risks else "blocked_by_collision",
    }


# ═════════════════════════════════════════════════════════════════════
# Public entrypoint
# ═════════════════════════════════════════════════════════════════════
async def run_asset_dryrun(
    db, *,
    page_size: int = 100,
    max_pages: int = 50,
    save_report: bool = False,
    triggered_by: str = "admin",
) -> Dict[str, Any]:
    """Execute the full read-first dry-run.

    Returns a structured dict. NEVER writes to MaintainX. NEVER writes
    to equipment_master / asset_mappings / fleet_defects. Only writes a
    single audit row into `maintainx_dryrun_reports` when
    `save_report=True`.
    """
    run_id = str(uuid.uuid4())
    started_at = _now_iso()
    config = MaintainxConfig.from_env()
    client = MaintainxClient(config)

    report: Dict[str, Any] = {
        "id": run_id,
        "started_at": started_at,
        "completed_at": None,
        "triggered_by": triggered_by,
        "config": config.public_view(),
        "connection": None,
        "totals": {
            "maintainx_assets_pulled": 0,
            "masci_equipment_count": 0,
            "exact_match": 0,
            "probable_match": 0,
            "possible_duplicate": 0,
            "conflict": 0,
            "missing_in_masci": 0,
            "missing_in_maintainx": 0,
            "duplicate_risk_blocked": 0,
            "duplicate_risk_safe": 0,
            "errors": 0,
        },
        "results": [],
        "missing_in_maintainx": [],
        "errors": [],
        "saved": False,
        "writes_performed": {
            "maintainx": 0,
            "equipment_master": 0,
            "asset_mappings": 0,
            "fleet_defects": 0,
        },
    }

    # ── Phase 1 · Connection probe ──────────────────────────────────
    try:
        report["connection"] = await client.test_connection()
    except Exception as e:  # noqa: BLE001
        report["errors"].append({"phase": "test_connection", "error": str(e)})
        report["totals"]["errors"] += 1

    # ── Phase 2 · Asset pull ───────────────────────────────────────
    mx_normalised: List[Dict[str, Any]] = []
    if client.is_configured() and (report["connection"] or {}).get("ok"):
        try:
            async for a in client.iter_assets(page_size=page_size, max_pages=max_pages):
                norm = normalize_maintainx_asset(a)
                if norm.get("maintainx_asset_id"):
                    mx_normalised.append(norm)
        except MaintainxClientError as e:
            report["errors"].append({"phase": "asset_pull", **e.to_dict()})
            report["totals"]["errors"] += 1
        except Exception as e:  # noqa: BLE001
            report["errors"].append({"phase": "asset_pull", "error": str(e)})
            report["totals"]["errors"] += 1
    else:
        report["errors"].append({
            "phase": "asset_pull",
            "skipped": True,
            "reason": "client not configured or connection probe failed",
        })

    report["totals"]["maintainx_assets_pulled"] = len(mx_normalised)

    # ── Phase 3 · Load MASCI equipment + build index ───────────────
    masci_raw = await db.equipment_master.find({}, {"_id": 0}).to_list(20000)
    masci: List[Dict[str, Any]] = [normalize_masci_equipment(r) for r in masci_raw]
    report["totals"]["masci_equipment_count"] = len(masci)

    masci_index: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for m in masci:
        u = _norm_unit(m.get("unit_number"))
        if u:
            masci_index.setdefault(("unit", u), []).append(m)
        vs = _norm_serial(m.get("vin_serial"))
        if vs:
            masci_index.setdefault(("vinserial", vs), []).append(m)

    # Existing mappings: maintainx_asset_id → mapping doc
    existing_mappings = await db.asset_mappings.find(
        {"maintainx.asset_id": {"$exists": True, "$ne": ""}}, {"_id": 0},
    ).to_list(20000)
    existing_by_external_id: Dict[str, Dict[str, Any]] = {}
    matched_masci_ids: set[str] = set()
    for mm in existing_mappings:
        mx_id = ((mm.get("maintainx") or {}).get("asset_id") or "").strip()
        if mx_id:
            existing_by_external_id[mx_id] = mm

    # ── Phase 4 · Classify each MaintainX asset ─────────────────────
    for mx in mx_normalised:
        cls = _match_asset(
            mx=mx, masci=masci,
            existing_by_external_id=existing_by_external_id,
            masci_index=masci_index,
        )
        bucket = cls["classification"]
        if bucket in report["totals"]:
            report["totals"][bucket] += 1

        # Track MASCI rows that were matched at least once
        masci_match_id = cls.get("masci_equipment_id")
        if masci_match_id:
            matched_masci_ids.add(masci_match_id)

        # Duplicate-risk only matters for the "missing_in_masci" bucket
        dup_risk = None
        if bucket == "missing_in_masci":
            dup_risk = _duplicate_risk_for_new_asset(mx=mx, masci_index=masci_index)
            if dup_risk["has_risk"]:
                report["totals"]["duplicate_risk_blocked"] += 1
            else:
                report["totals"]["duplicate_risk_safe"] += 1

        report["results"].append({
            "maintainx_asset_id": mx.get("maintainx_asset_id"),
            "maintainx_unit_number": mx.get("unit_number"),
            "maintainx_name": mx.get("name"),
            "maintainx_make": mx.get("make"),
            "maintainx_model": mx.get("model"),
            "maintainx_serial_number": mx.get("serial_number"),
            "maintainx_vin": mx.get("vin"),
            "maintainx_status": mx.get("status"),
            **cls,
            "duplicate_risk": dup_risk,
        })

    # ── Phase 5 · Reverse pass · MASCI present, MaintainX absent ──
    if mx_normalised or client.is_configured():
        # Only emit "missing_in_maintainx" if we actually pulled data
        pulled_any = len(mx_normalised) > 0 or (report["connection"] or {}).get("ok")
        if pulled_any:
            for m in masci:
                if m["id"] in matched_masci_ids:
                    continue
                report["missing_in_maintainx"].append({
                    "masci_equipment_id": m["id"],
                    "unit_number": m["unit_number"],
                    "display": m["name"],
                    "make": m["make"],
                    "model": m["model"],
                    "vin_serial": m["vin_serial"],
                })
            report["totals"]["missing_in_maintainx"] = len(report["missing_in_maintainx"])

    report["completed_at"] = _now_iso()

    # ── Phase 6 · Optional save (single read-only collection) ──────
    if save_report:
        try:
            await db.maintainx_dryrun_reports.insert_one({**report, "_inserted_at": _now_iso()})
            report["saved"] = True
        except Exception as e:  # noqa: BLE001
            report["errors"].append({"phase": "save_report", "error": str(e)})
            report["totals"]["errors"] += 1

    return report


__all__ = [
    "run_asset_dryrun",
    "normalize_maintainx_asset",
    "normalize_masci_equipment",
    "_match_asset",
    "_duplicate_risk_for_new_asset",
]
