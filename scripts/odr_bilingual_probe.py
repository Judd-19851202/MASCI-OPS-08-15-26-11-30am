#!/usr/bin/env python3
"""
odr_bilingual_probe.py — Phase V.1 · M0.2A.

Defends the ODR bilingual contract. Validates:

  B1. Catalog has ≥ 1 prompt_key per ODR section.
  B2. Every prompt_key carries ≥ 4 EN bullets AND ≥ 4 ES bullets.
  B3. Every crew override (if present) carries ≥ 4 bullets per language.
  B4. No empty / whitespace-only bullets.
  B5. Crew universe coverage — every enum.CrewType resolves (catalog
      base fallback is acceptable; overlay is optional).
  B6. Every `odr.readiness.coaching_prompts[*].prompt_key` referenced
      in the live Mongo resolves in the catalog (orphan-key guard).
  B7. Every `odr` row preserves bilingual fields' shape — when a
      LocalizedString has a non-empty `text`, no field is "lang=es"
      without `original_lang` set.

Usage:
  python3 scripts/odr_bilingual_probe.py [--gate]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "backend" / ".env")
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from routes.odr.guidance_catalog import (  # noqa: E402
    CATALOG, CATALOG_CREW_TYPES, catalog_health,
)
from routes.odr.enums import CrewType  # noqa: E402,F401

REPORT_PATH = REPO_ROOT / "memory" / "ODR_BILINGUAL_PROBE_REPORT.md"

# Enum-defined CrewType literals (mirrors enums.CrewType).
ENUM_CREW_TYPES = {
    "pipe", "utility", "grading", "fine_grade", "stabilization",
    "concrete", "structures", "curb", "sidewalk", "milling",
    "paving", "mot", "survey", "airfield", "electrical", "other",
}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bullet_ok(b: str) -> bool:
    return isinstance(b, str) and len(b.strip()) >= 8


async def run(gate: bool) -> int:
    failures: list[dict] = []
    warnings: list[dict] = []

    # ── B1: ≥1 prompt_key per ODR section ────────────────────────────
    h = catalog_health()
    odr_sections_expected = {
        "project", "manpower", "equipment", "subcontractors",
        "materials", "production_segments", "delays",
        "extra_work", "constraints", "safety", "weather_impact",
        "photos", "tomorrow", "plan_vs_actual", "signature",
        "review",
    }
    covered = set(h["sections_covered"])
    missing_sections = sorted(odr_sections_expected - covered)
    # `subcontractors` and `review` are catalog-optional in M0.2A — we
    # warn but don't fail.
    hard_missing = [s for s in missing_sections if s not in ("subcontractors", "review")]
    if hard_missing:
        failures.append({
            "check": "B1",
            "name": "section_coverage",
            "missing": hard_missing,
        })
    if missing_sections:
        warnings.append({
            "check": "B1",
            "name": "section_coverage_soft",
            "missing": missing_sections,
        })

    # ── B2: ≥4 EN + ≥4 ES bullets ────────────────────────────────────
    below_en = h["en_keys_below_floor"]
    below_es = h["es_keys_below_floor"]
    if below_en:
        failures.append({
            "check": "B2",
            "name": "en_floor_below_4",
            "keys": below_en,
        })
    if below_es:
        failures.append({
            "check": "B2",
            "name": "es_floor_below_4",
            "keys": below_es,
        })

    # ── B3: crew overrides ≥4 bullets per lang ───────────────────────
    crew_issues = []
    for key, entry in CATALOG.items():
        for crew, overlay in (entry.get("crew_overrides") or {}).items():
            for lang in ("en", "es"):
                bullets = overlay.get(lang) or []
                if len(bullets) < 4:
                    crew_issues.append({
                        "prompt_key": key, "crew": crew,
                        "lang": lang, "count": len(bullets),
                    })
    if crew_issues:
        failures.append({
            "check": "B3",
            "name": "crew_override_floor_below_4",
            "issues": crew_issues,
        })

    # ── B4: no empty bullets ─────────────────────────────────────────
    empty_bullets = []
    for key, entry in CATALOG.items():
        for lang in ("en", "es"):
            for i, b in enumerate(entry.get(lang) or []):
                if not _bullet_ok(b):
                    empty_bullets.append({
                        "prompt_key": key, "lang": lang,
                        "index": i, "value": str(b)[:50],
                    })
        for crew, overlay in (entry.get("crew_overrides") or {}).items():
            for lang in ("en", "es"):
                for i, b in enumerate(overlay.get(lang) or []):
                    if not _bullet_ok(b):
                        empty_bullets.append({
                            "prompt_key": key, "lang": lang,
                            "crew": crew, "index": i,
                            "value": str(b)[:50],
                        })
    if empty_bullets:
        failures.append({
            "check": "B4",
            "name": "empty_or_short_bullets",
            "issues": empty_bullets[:30],
        })

    # ── B5: crew universe coverage (fallback acceptable) ─────────────
    # Every CrewType from the enum must resolve at least one prompt_key
    # (overlay or base fallback). Base fallback always exists since the
    # base entry is required — so this passes as long as B1 + B2 pass.
    catalog_universe_gap = [
        c for c in CATALOG_CREW_TYPES if c not in ENUM_CREW_TYPES
        and c not in ("drainage", "asphalt", "striping", "demo", "earthwork")
    ]
    if catalog_universe_gap:
        warnings.append({
            "check": "B5",
            "name": "catalog_universe_extra",
            "extra": catalog_universe_gap,
        })
    enum_universe_gap = [c for c in ENUM_CREW_TYPES if c not in CATALOG_CREW_TYPES]
    if enum_universe_gap:
        failures.append({
            "check": "B5",
            "name": "enum_crew_not_in_catalog_universe",
            "missing": enum_universe_gap,
        })

    # ── B6: orphan prompt_keys in live ODR readiness ─────────────────
    url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(url, tz_aware=True)
    db = client[db_name]
    orphan_keys = []
    cur = db.odr.find(
        {}, {"_id": 0, "id": 1, "readiness.coaching_prompts": 1}
    )
    odrs_scanned = 0
    async for row in cur:
        odrs_scanned += 1
        rd = row.get("readiness") or {}
        for prompt in (rd.get("coaching_prompts") or []):
            pk = prompt.get("prompt_key")
            if pk and pk not in CATALOG:
                orphan_keys.append({"odr_id": row.get("id"), "prompt_key": pk})
    if orphan_keys:
        failures.append({
            "check": "B6",
            "name": "orphan_prompt_key_in_live_data",
            "issues": orphan_keys[:20],
        })

    # ── B7: localized field shape integrity ─────────────────────────
    shape_violations = []
    cur = db.odr.find(
        {}, {"_id": 0, "id": 1,
             "tomorrow.planned_work": 1,
             "weather_impact.description": 1,
             "delays.entries": 1}
    )
    async for row in cur:
        for path in (
            (row.get("tomorrow") or {}).get("planned_work"),
            (row.get("weather_impact") or {}).get("description"),
        ):
            if isinstance(path, dict):
                if path.get("original") and not path.get("original_lang"):
                    shape_violations.append({
                        "odr_id": row.get("id"),
                        "violation": "original_present_without_original_lang",
                    })
        for entry in ((row.get("delays") or {}).get("entries") or []):
            desc = entry.get("description") or {}
            if desc.get("original") and not desc.get("original_lang"):
                shape_violations.append({
                    "odr_id": row.get("id"),
                    "violation": "delays.entries[].description_original_without_lang",
                })
    if shape_violations:
        warnings.append({
            "check": "B7",
            "name": "localized_field_shape",
            "issues": shape_violations[:20],
        })

    # ── render report ────────────────────────────────────────────────
    lines = [
        "# ODR Bilingual Probe Report",
        "",
        f"_Generated {_utc_iso()} · env={os.environ.get('APP_ENV')} · db={db_name}_",
        "",
        "## Catalog snapshot",
        f"- Prompt keys: **{h['prompt_keys']}**",
        f"- EN keys meeting ≥4 floor: **{h['en_keys_meeting_floor']}**",
        f"- ES keys meeting ≥4 floor: **{h['es_keys_meeting_floor']}**",
        f"- Sections covered: **{', '.join(h['sections_covered'])}**",
        f"- Crews with overlays: **{', '.join(h['crews_with_overrides'])}**",
        f"- ODRs scanned: **{odrs_scanned}**",
        "",
        "## Checks",
    ]
    for check_id, name in [
        ("B1", "≥1 prompt_key per ODR section"),
        ("B2", "≥4 EN + ≥4 ES bullets per prompt_key"),
        ("B3", "Crew overlay floors ≥4"),
        ("B4", "No empty / whitespace-only bullets"),
        ("B5", "Crew universe coverage"),
        ("B6", "No orphan prompt_keys in live ODR data"),
        ("B7", "Localized field shape integrity"),
    ]:
        marker = "✅"
        for f in failures:
            if f["check"] == check_id:
                marker = "❌"
                break
        for w in warnings:
            if w["check"] == check_id and marker == "✅":
                marker = "⚠️"
        lines.append(f"- {marker} **{check_id}** · {name}")
    if failures:
        lines += ["", "## Failures"]
        for f in failures:
            lines.append(f"### {f['check']} · {f['name']}")
            lines.append("```")
            lines.append(json.dumps(f, indent=2, default=str))
            lines.append("```")
    if warnings:
        lines += ["", "## Warnings"]
        for w in warnings:
            lines.append(f"### {w['check']} · {w['name']}")
            lines.append("```")
            lines.append(json.dumps(w, indent=2, default=str))
            lines.append("```")
    REPORT_PATH.write_text("\n".join(lines) + "\n")

    print(f"odr_bilingual_probe · env={os.environ.get('APP_ENV')} · db={db_name}")
    print(f"  prompt_keys={h['prompt_keys']}  EN_min4={h['en_keys_meeting_floor']}  "
          f"ES_min4={h['es_keys_meeting_floor']}")
    print(f"  ODRs scanned={odrs_scanned}  failures={len(failures)}  warnings={len(warnings)}")
    if failures:
        for f in failures:
            print(f"  ❌ {f['check']} · {f['name']}")
        if gate:
            return 1
    else:
        print("  ✅ all checks passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    return asyncio.run(run(gate=args.gate))


if __name__ == "__main__":
    sys.exit(main())
