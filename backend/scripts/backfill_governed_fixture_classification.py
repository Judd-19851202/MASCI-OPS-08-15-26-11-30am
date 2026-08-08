from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.governed_fixture_evidence import (  # noqa: E402
    FIXTURE_EVIDENCE_RULES,
    governed_fixture_markers,
    normalize_explicit_governed_markers,
)


COLLECTION_BY_FAMILY = {
    "employees": "employees",
    "field_leadership_records": "field_leadership_records",
    "daily_reports": "daily_reports",
    "incidents": "incidents",
    "meetings": "meetings",
    "jhas": "jhas",
    "inspections": "inspections",
    "training_records": "safety_training_records",
    "safety_issuances": "safety_equipment_issuances",
    "dispatch_assignments": "dispatch_assignments",
    "equipment_inspections": "equipment_inspections",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_env() -> None:
    env_path = BACKEND_ROOT / ".env"
    for raw in env_path.read_text().splitlines():
        if "=" not in raw or raw.strip().startswith("#"):
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] in ('"', "'") and value[-1] == value[0]:
            value = ast.literal_eval(value)
        os.environ.setdefault(key, value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview-only backfill for explicit governed fixture classification markers.",
    )
    parser.add_argument(
        "--family",
        action="append",
        dest="families",
        help="Limit backfill to one or more family ids.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist updates. Without this flag the script is dry-run only.",
    )
    parser.add_argument(
        "--allow-preview-write",
        action="store_true",
        help="Required together with --apply to mutate preview data.",
    )
    return parser


def _iter_families(selected: Iterable[str] | None) -> List[str]:
    if not selected:
        return list(COLLECTION_BY_FAMILY.keys())
    allowed = set(COLLECTION_BY_FAMILY.keys())
    wanted = [family for family in selected if family in allowed]
    unknown = sorted(set(selected) - allowed)
    if unknown:
        raise SystemExit(f"Unknown family ids: {', '.join(unknown)}")
    return wanted


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.apply and not args.allow_preview_write:
        raise SystemExit("Refusing to mutate data without --allow-preview-write")

    _load_env()
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    run_id = str(uuid.uuid4())
    families = _iter_families(args.families)
    summary: Dict[str, Any] = {
        "run_id": run_id,
        "started_at": _now_iso(),
        "mode": "apply" if args.apply else "dry_run",
        "families": [],
    }

    for family in families:
        collection = COLLECTION_BY_FAMILY[family]
        family_summary: Dict[str, Any] = {
            "family_id": family,
            "collection": collection,
            "rule_count": len(FIXTURE_EVIDENCE_RULES.get(family, [])),
            "matched": 0,
            "updated": 0,
            "samples": [],
        }
        for row in db[collection].find({}, None):
            markers = normalize_explicit_governed_markers(row) or governed_fixture_markers(row, family)
            if not markers:
                continue
            family_summary["matched"] += 1
            if len(family_summary["samples"]) < 5:
                sample = {k: row.get(k) for k in ("id", "doc_id", "project_number", "project_name", "name", "employee_name", "truck_id", "operator_name") if row.get(k) not in (None, "")}
                sample.update({
                    "governed_classification_source": markers.get("governed_classification_source"),
                    "technical_record_classification": markers.get("technical_record_classification"),
                })
                family_summary["samples"].append(sample)

            needs_update = any(row.get(key) != value for key, value in markers.items())
            if not needs_update:
                continue
            if args.apply:
                db[collection].update_one(
                    {"_id": row["_id"]},
                    {"$set": markers},
                )
            family_summary["updated"] += 1
        summary["families"].append(family_summary)

    summary["finished_at"] = _now_iso()
    if args.apply:
        db.enterprise_governance_audit.insert_one(
            {
                "id": run_id,
                "audit_type": "governed_fixture_classification_backfill",
                "created_at": summary["finished_at"],
                "mode": summary["mode"],
                "summary": summary,
            }
        )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())