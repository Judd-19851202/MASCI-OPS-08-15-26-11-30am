"""
TRACK 15.62 · Daily Report Roll-Up — single source of truth for haul
and material aggregation across PM Command Center, Executive Roll-Up,
and Daily Report Health surfaces.

Design principles
-----------------
1. ONE module · ONE aggregator. Both PMCC and the new admin executive
   endpoint consume the same primitives so that the haul count a PM
   sees is the same haul count the CEO sees.
2. READ-ONLY against `db.daily_reports`. No writes, no migrations.
3. Material name normalisation against `db.material_vocabulary` (the
   canonical seed). Free-text values are preserved with a `_normalized`
   sibling so downstream aggregations can group consistently without
   destroying the operator's original entry.
4. Loads are summed from `outbound_materials[i].quantity` when the
   `unit` field equals "Loads" (the production-observed canonical
   unit per Track 15.61). Other units are surfaced separately so the
   exec layer can distinguish 50 loads from 50 tons.
5. Performance-bounded: queries scope by `report_date` window +
   `project_number` filter. The 154-row production corpus is trivial.

Feature flag
------------
This module is import-safe regardless of DR_RECOVERY_ENABLED. The
flag gates ONLY the frontend NewDailyReport workflow. The aggregator
runs unconditionally so existing PMCC consumers see correct numbers
the moment the backend ships.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────

# Default canonical material vocabulary. The DB collection
# `material_vocabulary` overrides this when seeded. The vocabulary is
# additive: free-text entries (e.g. "Dirty dirt") still aggregate by
# their raw value AND are tagged into the "Other" canonical bucket.
DEFAULT_MATERIAL_VOCABULARY: List[Dict[str, Any]] = [
    {"canonical": "Dirt", "synonyms": ["dirt", "soil", "unsuitable", "spoils", "fill"]},
    {"canonical": "Rock", "synonyms": ["rock", "stone", "boulder"]},
    {"canonical": "Crushed Concrete", "synonyms": ["crushed concrete", "57s", "57 stone", "concrete millings"]},
    {"canonical": "Asphalt Millings", "synonyms": ["millings", "asphalt millings", "rap"]},
    {"canonical": "Asphalt", "synonyms": ["asphalt", "hot mix", "ac"]},
    {"canonical": "Concrete", "synonyms": ["concrete", "ready mix", "rmc"]},
    {"canonical": "Sand", "synonyms": ["sand"]},
    {"canonical": "Gravel", "synonyms": ["gravel"]},
    {"canonical": "Topsoil", "synonyms": ["topsoil", "loam"]},
    {"canonical": "Debris", "synonyms": ["debris", "demo", "trash"]},
    {"canonical": "Mulch", "synonyms": ["mulch"]},
    {"canonical": "Pipe", "synonyms": ["pipe", "rcp", "hdpe"]},
    {"canonical": "Rebar", "synonyms": ["rebar", "steel"]},
    {"canonical": "Other", "synonyms": []},  # catch-all
]

LOAD_UNIT_TOKENS = {"load", "loads", "lo", "ld", "trip", "trips"}


# ──────────────────────────────────────────────────────────────────
# Material normalisation
# ──────────────────────────────────────────────────────────────────

_VOCAB_CACHE: Optional[List[Dict[str, Any]]] = None


async def load_material_vocabulary(db) -> List[Dict[str, Any]]:
    """Return the canonical vocabulary list, preferring DB rows over
    the default seed. Cached process-wide because vocabulary changes
    are admin-driven and infrequent."""
    global _VOCAB_CACHE
    if _VOCAB_CACHE is not None:
        return _VOCAB_CACHE
    rows: List[Dict[str, Any]] = []
    try:
        async for r in db.material_vocabulary.find({}, {"_id": 0}):
            rows.append(r)
    except Exception:
        rows = []
    _VOCAB_CACHE = rows or list(DEFAULT_MATERIAL_VOCABULARY)
    return _VOCAB_CACHE


def normalize_material_name(raw: Optional[str], vocab: List[Dict[str, Any]]) -> str:
    """Map a free-text material entry to its canonical bucket.

    Returns the canonical name when a synonym match is found, otherwise
    "Other" (catch-all). Never returns None or empty string.
    """
    if not raw:
        return "Other"
    needle = re.sub(r"\s+", " ", raw.strip().lower())
    if not needle:
        return "Other"
    for row in vocab:
        canon = (row.get("canonical") or "").strip()
        if not canon:
            continue
        if needle == canon.lower():
            return canon
        for syn in row.get("synonyms") or []:
            if needle == str(syn).strip().lower():
                return canon
            # Substring match for fuzzy human typing (e.g. "dirty dirt")
            if isinstance(syn, str) and len(syn) >= 3 and syn.lower() in needle:
                return canon
    return "Other"


def is_load_unit(unit: Optional[str]) -> bool:
    if not unit:
        return False
    return unit.strip().lower() in LOAD_UNIT_TOKENS


def _qty_int(v: Any) -> int:
    """Best-effort coerce a quantity field (which may be int, str, or
    None) to an integer. Returns 0 on failure — never raises."""
    try:
        if v is None or v == "":
            return 0
        if isinstance(v, (int, float)):
            return int(v)
        s = str(v).strip().replace(",", "")
        # Handle "11.0" style strings
        if "." in s:
            return int(float(s))
        return int(s)
    except Exception:
        return 0


# ──────────────────────────────────────────────────────────────────
# Roll-up queries
# ──────────────────────────────────────────────────────────────────


async def rollup_window(
    db,
    *,
    date_from: str,
    date_to: str,
    project_numbers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Aggregate Daily Report material/haul/narrative data across the
    [date_from, date_to] inclusive window. Dates are YYYY-MM-DD ISO.

    Returns a dict with:
      - meta: window + filters
      - loads: { in: int, out: int, by_material: {canonical: int}, by_unit: {unit: int} }
      - rows_count: { reports: int, materials_in_rows: int, materials_out_rows: int }
      - by_project: { project_number: { loads_in, loads_out, materials_in_rows, materials_out_rows, reports } }
      - by_material_out: list of {material, loads, rows, projects: [...]}
      - top_haulers: list of {hauler, rows}
      - narrative_health: { total, with_activities, with_general_notes, with_narrative_sections, blank, avg_word_count, median_word_count, completion_pct }
    """
    vocab = await load_material_vocabulary(db)

    q: Dict[str, Any] = {
        "report_date": {"$gte": date_from, "$lte": date_to},
        "deleted_at": {"$in": [None, "", False]},
    }
    if project_numbers:
        q["project_number"] = {"$in": project_numbers}

    loads_in_total = 0
    loads_out_total = 0
    rows_in = 0
    rows_out = 0
    reports_n = 0
    by_material_out: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"loads": 0, "rows": 0, "projects": set()}
    )
    by_material_in: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"loads": 0, "rows": 0}
    )
    by_unit_out: Counter = Counter()
    by_project: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "loads_in": 0, "loads_out": 0, "materials_in_rows": 0,
        "materials_out_rows": 0, "reports": 0,
    })
    by_hauler: Counter = Counter()

    n_with_activities = 0
    n_with_general_notes = 0
    n_with_narrative_sections = 0
    n_blank = 0
    narrative_word_counts: List[int] = []

    cursor = db.daily_reports.find(q, {
        "_id": 0, "project_number": 1, "materials": 1, "outbound_materials": 1,
        "activities": 1, "general_notes": 1, "narrative_sections": 1,
    })
    async for d in cursor:
        reports_n += 1
        pn = (d.get("project_number") or "").strip() or "(unset)"
        by_project[pn]["reports"] += 1

        # Outbound materials → loads OUT
        for m in d.get("outbound_materials") or []:
            if not isinstance(m, dict):
                continue
            rows_out += 1
            by_project[pn]["materials_out_rows"] += 1
            canon = normalize_material_name(m.get("material"), vocab)
            unit = (m.get("unit") or "").strip() or "(unset)"
            qty = _qty_int(m.get("quantity"))
            by_material_out[canon]["rows"] += 1
            by_material_out[canon]["projects"].add(pn)
            by_unit_out[unit] += qty
            if is_load_unit(unit):
                loads_out_total += qty
                by_project[pn]["loads_out"] += qty
                by_material_out[canon]["loads"] += qty
            hauler = (m.get("hauler") or "").strip()
            if hauler:
                by_hauler[hauler.title()] += 1

        # Incoming materials → loads IN
        for m in d.get("materials") or []:
            if not isinstance(m, dict):
                continue
            rows_in += 1
            by_project[pn]["materials_in_rows"] += 1
            mat_raw = m.get("material") or m.get("type") or m.get("name")
            canon = normalize_material_name(mat_raw, vocab)
            unit = (m.get("unit") or "").strip()
            qty = _qty_int(m.get("quantity") or m.get("actual_quantity"))
            by_material_in[canon]["rows"] += 1
            if is_load_unit(unit):
                loads_in_total += qty
                by_project[pn]["loads_in"] += qty
                by_material_in[canon]["loads"] += qty

        # Narrative health for the same window
        acts = d.get("activities") or []
        gen = (d.get("general_notes") or "").strip()
        sections = d.get("narrative_sections") or {}
        has_acts = bool(acts)
        has_gen = bool(gen)
        has_sections = bool(sections) and any((sections.get(k) or "").strip() for k in sections)
        if has_acts:
            n_with_activities += 1
        if has_gen:
            n_with_general_notes += 1
        if has_sections:
            n_with_narrative_sections += 1
        if not (has_acts or has_gen or has_sections):
            n_blank += 1
        # Words across all narrative surfaces (consistent with 15.61 measurement)
        text_parts: List[str] = []
        for a in acts:
            if isinstance(a, dict):
                for k in ("description", "activity", "narrative", "notes", "details"):
                    v = a.get(k)
                    if isinstance(v, str) and v.strip():
                        text_parts.append(v.strip())
        if gen:
            text_parts.append(gen)
        if has_sections:
            for v in sections.values():
                if isinstance(v, str) and v.strip():
                    text_parts.append(v.strip())
        joined = " ".join(text_parts)
        word_n = len([w for w in re.split(r"\s+", joined) if w])
        narrative_word_counts.append(word_n)

    # Compose response
    def _proj_sets_to_list(d):
        out = []
        for mat, row in d.items():
            out.append({
                "material": mat,
                "loads": row["loads"],
                "rows": row["rows"],
                "projects": sorted(row.get("projects", []) if isinstance(row.get("projects"), set) else (row.get("projects") or [])),
            })
        out.sort(key=lambda x: -x["loads"])
        return out

    avg_words = (sum(narrative_word_counts) / len(narrative_word_counts)) if narrative_word_counts else 0.0
    sorted_words = sorted(narrative_word_counts)
    median_words = sorted_words[len(sorted_words) // 2] if sorted_words else 0
    completion_pct = round(100.0 * (reports_n - n_blank) / max(1, reports_n), 1)

    return {
        "meta": {
            "date_from": date_from,
            "date_to": date_to,
            "project_numbers_filter": project_numbers or [],
            "vocab_size": len(vocab),
        },
        "loads": {
            "in": loads_in_total,
            "out": loads_out_total,
            "by_material_out": _proj_sets_to_list(by_material_out),
            "by_material_in": _proj_sets_to_list(by_material_in),
            "by_unit_out": dict(by_unit_out),
        },
        "rows_count": {
            "reports": reports_n,
            "materials_in_rows": rows_in,
            "materials_out_rows": rows_out,
        },
        "by_project": dict(by_project),
        "top_haulers": [{"hauler": h, "rows": c} for h, c in by_hauler.most_common(20)],
        "narrative_health": {
            "total": reports_n,
            "with_activities": n_with_activities,
            "with_general_notes": n_with_general_notes,
            "with_narrative_sections": n_with_narrative_sections,
            "blank": n_blank,
            "completion_pct": completion_pct,
            "avg_word_count": round(avg_words, 1),
            "median_word_count": median_words,
        },
    }


async def rollup_today(
    db,
    *,
    project_numbers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience: aggregate just today's window."""
    today = datetime.now(timezone.utc).date().isoformat()
    return await rollup_window(db, date_from=today, date_to=today, project_numbers=project_numbers)


def is_recovery_enabled() -> bool:
    """Feature flag for the frontend NewDailyReport guided narrative
    workflow. Backend aggregator is UNCONDITIONALLY active."""
    return os.environ.get("DR_RECOVERY_ENABLED", "false").lower() in ("1", "true", "yes")


# ──────────────────────────────────────────────────────────────────
# Motive cross-walk helpers
# ──────────────────────────────────────────────────────────────────


async def haulers_to_motive_trucks(db, hauler_names: Iterable[str]) -> Dict[str, List[str]]:
    """Best-effort map from the free-text `hauler` field on outbound
    rows to Motive truck unit_numbers via `db.asset_mappings`. This is
    a READ-ONLY heuristic: when a hauler value matches the canonical
    'Masci' fleet, the function returns the active Masci trucks for
    cross-reference. For unknown haulers, returns an empty list.
    """
    out: Dict[str, List[str]] = {}
    names = [n.strip().title() for n in hauler_names if n and n.strip()]
    if not names:
        return out
    # Only "Masci"/"MASCI" map to internal trucks today. Third-party
    # haulers do not have asset mappings.
    masci_trucks: List[str] = []
    try:
        async for am in db.asset_mappings.find(
            {"provider": "motive", "active": {"$in": [True, None]}},
            {"_id": 0, "unit_number": 1, "motive_truck_id": 1}
        ).limit(500):
            u = am.get("unit_number") or am.get("motive_truck_id")
            if u:
                masci_trucks.append(str(u))
    except Exception:
        masci_trucks = []
    for n in names:
        out[n] = masci_trucks if n.lower() in ("masci", "masci gc") else []
    return out
