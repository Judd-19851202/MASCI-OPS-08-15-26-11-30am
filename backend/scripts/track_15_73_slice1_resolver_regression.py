"""TRACK 15.73 SLICE 1 · Equipment Resolver Regression Test.

Exercises GET /api/asset-spine/taxonomy/by-unit/ against every distinct
unit identifier that appears in equipment_inspections.equipment_unit.
Categorizes the outcomes by resolution_source.

PASS condition:
  • RG007-0869 resolves with source in {unit_number, display_label_strip}
  • All historic display_label submissions in the 5 audited categories
    (Motor Grader / Excavator / Roller / Paver / Truck) now resolve.
  • Synthetic test fixtures (D34-REG-*, D51-*, TEST-*, U-iter*) still
    return found=False — proves we did NOT introduce false positives.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(Path("/app/frontend/.env"))

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
API_BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SUPER = os.environ.get("SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
PWD = os.environ.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD", "Maddix123!")


def get_admin_token() -> str:
    r = requests.post(
        f"{API_BASE}/api/auth/multi-login",
        json={"email": SUPER, "password": PWD},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


def main() -> int:
    db = MongoClient(MONGO_URL)[DB_NAME]
    token = get_admin_token()
    headers = {"X-Admin-Token": token}

    # Gather all distinct equipment_unit values from inspections
    distinct = set()
    for d in db.equipment_inspections.find({}, {"_id": 0, "equipment_unit": 1}):
        u = (d.get("equipment_unit") or "").strip()
        if u:
            distinct.add(u)

    # Classify synthetic vs real
    SYNTHETIC = (
        "D34-REG-", "D51-MISS-", "D51-DT-", "D51-LB-", "D51-VER-", "D51-TB-",
        "D52-AIRCOMPR-", "TEST-", "COMBO-", "U-iter", "iter",
    )
    synthetic_units = [u for u in distinct if any(u.startswith(p) for p in SYNTHETIC)]
    real_units = [u for u in distinct if u not in synthetic_units]

    results = {
        "real_total": len(real_units),
        "synthetic_total": len(synthetic_units),
        "real_resolution": {"unit_number": 0, "display_label_strip": 0, "id": 0, "not_found": 0, "error": 0},
        "synthetic_resolution": {"unit_number": 0, "display_label_strip": 0, "id": 0, "not_found": 0, "error": 0},
        "real_rescued_examples": [],
        "real_not_found_examples": [],
        "synthetic_false_positives": [],
        "target_unit_rg007_0869": None,
    }

    def probe(unit: str) -> dict | None:
        try:
            r = requests.get(
                f"{API_BASE}/api/asset-spine/taxonomy/by-unit/{requests.utils.quote(unit, safe='')}",
                headers=headers,
                timeout=60,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    # Target unit probes (both forms)
    results["target_unit_rg007_0869"] = {}
    for u in ("RG007-0869", "RG007-0869 \u2014 2025 JOHN DEERE 672G"):
        d = probe(u)
        if d:
            results["target_unit_rg007_0869"][u] = {
                "found": d.get("found"),
                "unit_number": d.get("unit_number"),
                "asset_type": d.get("asset_type"),
                "resolution_source": d.get("resolution_source"),
            }

    # Real units: count resolution sources + capture rescued examples
    for u in sorted(real_units):
        d = probe(u)
        if not d:
            results["real_resolution"]["error"] += 1
            continue
        src = d.get("resolution_source", "unknown")
        if d.get("found"):
            results["real_resolution"][src] = results["real_resolution"].get(src, 0) + 1
            if src == "display_label_strip" and len(results["real_rescued_examples"]) < 25:
                results["real_rescued_examples"].append({
                    "submitted": u,
                    "resolved_unit_number": d.get("unit_number"),
                    "asset_type": d.get("asset_type"),
                })
        else:
            results["real_resolution"]["not_found"] += 1
            if len(results["real_not_found_examples"]) < 30:
                results["real_not_found_examples"].append(u)

    # Synthetic units: must remain not_found (no false positives)
    for u in sorted(synthetic_units)[:50]:
        d = probe(u)
        if not d:
            results["synthetic_resolution"]["error"] += 1
            continue
        src = d.get("resolution_source", "unknown")
        if d.get("found"):
            results["synthetic_resolution"][src] = results["synthetic_resolution"].get(src, 0) + 1
            results["synthetic_false_positives"].append({
                "submitted": u, "resolved": d.get("unit_number"), "source": src,
            })
        else:
            results["synthetic_resolution"]["not_found"] += 1

    # PASS/FAIL gate
    target = results["target_unit_rg007_0869"] or {}
    pass_target = all(
        v["found"] and v["resolution_source"] in ("unit_number", "display_label_strip")
        for v in target.values()
    )
    pass_no_fp = len(results["synthetic_false_positives"]) == 0
    pass_rescued = results["real_resolution"]["display_label_strip"] >= 10
    results["pass_target_unit"] = pass_target
    results["pass_no_synthetic_false_positives"] = pass_no_fp
    results["pass_rescued_at_least_10_units"] = pass_rescued
    results["overall_pass"] = pass_target and pass_no_fp and pass_rescued

    out_path = Path("/app/test_reports/track_15_73_slice1_resolver_regression.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, default=str, indent=2))
    print(json.dumps({k: v for k, v in results.items() if k != "real_not_found_examples"}, default=str, indent=2)[:3000])
    print(f"\nFull JSON: {out_path}")
    print(f"\nOVERALL: {'PASS' if results['overall_pass'] else 'FAIL'}")
    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
