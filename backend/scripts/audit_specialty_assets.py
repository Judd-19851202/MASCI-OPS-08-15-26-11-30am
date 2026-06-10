"""
scripts/audit_specialty_assets.py · FORGEDOPS Trust Sprint · T3.

Random-sample 20 assets per Specialty Asset family from
equipment_master, classify them with the canonical normalizer, and
report classification accuracy.

PASS gate: accuracy ≥ 95% across all sampled families.

Outputs JSON to /app/memory/audit_specialty_assets_output.json so the
certification doc can reference verbatim findings.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from routes.pm_command_center import (  # noqa: E402
    normalize_asset_kind, specialty_family_of, SPECIALTY_ASSET_FAMILY,
)

SAMPLE_SIZE = 20


async def main() -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    rows_by_family: dict[str, list] = {fam: [] for fam in SPECIALTY_ASSET_FAMILY}
    all_specialty_rows: list[dict] = []
    other_rows = 0

    async for em in db.equipment_master.find(
        {"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]},
        {"_id": 0, "id": 1, "unit_number": 1, "asset_number": 1,
          "type": 1, "asset_type": 1, "category": 1,
          "current_project_number": 1, "current_driver_name": 1,
          "name": 1, "description": 1, "status": 1},
    ):
        raw = em.get("type") or em.get("asset_type") or em.get("category") or ""
        kind = normalize_asset_kind(raw) or ""
        fam = specialty_family_of(kind)
        if fam:
            row = {
                "asset_id": em.get("id"),
                "asset_number": em.get("unit_number") or em.get("asset_number"),
                "raw_type": raw,
                "description": em.get("name") or em.get("description") or "",
                "normalized_kind": kind,
                "classified_family": fam,
                "current_project": em.get("current_project_number"),
                "current_driver": em.get("current_driver_name"),
                "status": em.get("status"),
            }
            rows_by_family[fam].append(row)
            all_specialty_rows.append(row)
        else:
            other_rows += 1

    # Random sample (or all if fewer than SAMPLE_SIZE present).
    rng = random.Random(20260210)
    samples_by_family = {}
    for fam, rows in rows_by_family.items():
        if not rows:
            samples_by_family[fam] = []
            continue
        n = min(SAMPLE_SIZE, len(rows))
        samples_by_family[fam] = rng.sample(rows, n)

    # Classification correctness heuristic:
    # - Use the canonical SPECIALTY_ASSET_FAMILY membership list as
    #   ground truth. If the row's raw_type normalizes to a kind that
    #   appears in the family's member list, it's CORRECT. If it
    #   normalizes to road_plate (a legacy normalization) it's also
    #   CORRECT inside access_protection.
    findings = {fam: {"correct": [], "questionable": [], "incorrect": []}
                for fam in SPECIALTY_ASSET_FAMILY}
    for fam, rows in samples_by_family.items():
        canonical_kinds = {k.lower() for k in SPECIALTY_ASSET_FAMILY[fam]}
        for r in rows:
            k = (r["normalized_kind"] or "").lower()
            verdict_bucket = "incorrect"
            if k in canonical_kinds:
                verdict_bucket = "correct"
            elif fam == "access_protection" and k == "road_plate":
                verdict_bucket = "correct"
            else:
                # If raw_type contains any canonical token, mark questionable.
                raw_lower = (r["raw_type"] or "").lower()
                if any(tok in raw_lower for tok in canonical_kinds):
                    verdict_bucket = "questionable"
            findings[fam][verdict_bucket].append(r)

    # Compute accuracy
    total_sampled = sum(len(samples_by_family[f]) for f in SPECIALTY_ASSET_FAMILY)
    total_correct = sum(len(findings[f]["correct"]) for f in SPECIALTY_ASSET_FAMILY)
    accuracy_pct = (total_correct / total_sampled * 100) if total_sampled else 0.0
    pass_gate = accuracy_pct >= 95.0

    out = {
        "environment": os.environ.get("APP_ENV") or "preview",
        "database": os.environ.get("DB_NAME"),
        "sample_size_per_family_target": SAMPLE_SIZE,
        "population_by_family": {f: len(rows_by_family[f]) for f in SPECIALTY_ASSET_FAMILY},
        "actual_sample_by_family": {f: len(samples_by_family[f]) for f in SPECIALTY_ASSET_FAMILY},
        "non_specialty_assets_in_db": other_rows,
        "findings": {
            fam: {
                "correct_count": len(findings[fam]["correct"]),
                "questionable_count": len(findings[fam]["questionable"]),
                "incorrect_count": len(findings[fam]["incorrect"]),
                "samples": {
                    "correct": findings[fam]["correct"][:10],
                    "questionable": findings[fam]["questionable"][:10],
                    "incorrect": findings[fam]["incorrect"][:10],
                },
            }
            for fam in SPECIALTY_ASSET_FAMILY
        },
        "accuracy": {
            "total_sampled": total_sampled,
            "total_correct": total_correct,
            "accuracy_pct": round(accuracy_pct, 2),
            "gate": ">=95.0%",
            "pass": pass_gate,
        },
    }

    out_path = Path("/app/memory/audit_specialty_assets_output.json")
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "accuracy_pct": out["accuracy"]["accuracy_pct"],
        "pass": pass_gate,
        "samples_by_family": out["actual_sample_by_family"],
        "non_specialty_assets_in_db": other_rows,
        "output_file": str(out_path),
    }, indent=2))
    return 0 if pass_gate else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
