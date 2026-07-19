"""
seed_equipment_make_model.py

Splits the existing `make_model` field on every equipment_master document into
separate `make` and `model` fields, using a known multi-word manufacturer set.
Backs up the existing JSON file and updates BOTH:
  - /app/backend/data/equipment_master.json (source-of-truth file)
  - MongoDB collection `equipment_master`

Run:
  python3 /app/backend/scripts/seed_equipment_make_model.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient
from lib.operator_safety import (
    redact_target_identity,
    require_cli_backup_ack,
    require_cli_confirmation,
    require_cli_execute,
    require_cli_runtime_guard,
)

ROOT = Path("/app/backend")
DATA = ROOT / "data" / "equipment_master.json"

# Multi-word manufacturer prefixes — order matters (longest first).
MULTI_WORD_MAKES = [
    "Down to Earth",
    "Eager Beaver",
    "Big Tex",
    "BIG TEX",
    "John Deere",
    "JOHN DEERE",
    "Lay Mor",
    "LAY MOR",
    "Ingersoll Rand",
    "INGERSOLL RAND",
    "Buffalo Turbine",
    "Witzco Challenger",
    "Carry-On",
    "CARRY ON",
    "CARRY-ON",
    "Sure Trac",
    "SURE TRAC",
    "Direct Connect",
    "Terex Finlay",
    "Terex-Finlay",
    "TEREX FINLAY",
    "Hypac / Hyster",
    "Hypac/Hyster",
    "MACK - CXU613",  # special-case: this row was odd, treat make=Mack
    "Freightliner-M2",
    "Int'l.",
    "Eager Beaver/",
    "Witzco",
    "WITZCO",
    "MAC",
    "PDQ",
    "TCTR",
    "NVAE",
    "DETA",
    "ASPT",
    "SSP",
    "VMA/Pace/Cargo",
    "Bendron/Titan",
    "FVCG/Cargo",
    "Mobile",
    "Lark",
    "Eager",
    "Anvil",
    "ANVIL",
    "Anderson",
    "EASD",
    "Haulmark",
    "Witzco",
    "Big T",
    "Freedom",
    "Dorsey",
    "TRAILSTAR",
    "Econoline",
    "Etnyre",
    "Wabash",
    "KRAFTSMAN",
    "CVRD WAGON",
    "Down",
    "Covered TA",
    "7X12 DIAMOND",
    "DOOSAN",
    "BAOLI",
    "AGT",
    "BELL",
    "DYNAPAC",
    "Dynapac",
    "WIRTGEN",
    "Wirtgen",
    "VOGELE",
    "Vogele",
    "TOYOTA",
    "Toyota",
    "DODGE",
    "Dodge",
    "MACK",
    "Mack",
    "CASE",
    "Case",
    "Case 30Ton",
    "KOMATSU",
    "Komatsu",
    "KOBELCO",
    "Kobelco",
    "HYUNDAI",
    "Hyundai",
    "KUBOTA",
    "Kubota",
    "BOMAG",
    "Bomag",
    "Leeboy",
    "LEEBOY",
    "Hamm",
    "HAMM",
    "Sakai",
    "SAKAI",
    "Ingram",
    "INGRAM",
    "Rosco",
    "ROSCO",
    "takeuchi",
    "Takeuchi",
    "TAKEICHI",
    "TAKEUCHI",
    "Chevy",
    "CHEVY",
    "Freightliner",
    "FREIGHTLINER",
    "FRHT",
    "RAM",
    "GMC",
    "International",
    "INTERNATIONAL",
    "Roadtec",
    "ROADTEC",
    "Kenworth",
    "KENWORTH",
    "CAT",
    "Caterpillar",
    "CATERPILLAR",
    "Ford",
    "FORD",
    "Isuzu",
    "ISUZU",
    "Peterbilt",
    "PETERBILT",
    "Honda",
    "HONDA",
    "Nissan",
    "NISSAN",
    "Genie",
    "GENIE",
    "Snorkel",
    "SNORKEL",
    "Yale",
    "YALE",
    "MANITOU",
    "Manitou",
    "SANY",
    "Sany",
    "Sullivan",
    "SULLIVAN",
    "Ironhorse",
    "IRONHORSE",
    "Acura",
    "Garmin",
    "Wacker",
    "WACKER",
    "JEEP",
    "Jeep",
    "Magnum",
    "Holland",
    "Challenger",
    "CHALLENGER",
    "Hyster",
    "Wide",
    "Caterpillar/Kobelco",
    "All",
    "JD",
    "Bell",
    "Volvo",
    "VOLVO",
    "Komatsu/CAT",
]


def split_make_model(make_model: str) -> tuple[str, str]:
    """Best-effort split of an arbitrary make_model string into (make, model)."""
    if not make_model:
        return "", ""
    s = str(make_model).strip()
    if not s:
        return "", ""

    # Try multi-word makes first (longest match).
    for prefix in sorted(MULTI_WORD_MAKES, key=len, reverse=True):
        # Match prefix followed by space, dash or end of string.
        if s.lower().startswith(prefix.lower()):
            tail = s[len(prefix):].strip(" -")
            return prefix.title() if prefix.isupper() else prefix, tail

    # Fallback: first whitespace token = make, rest = model
    parts = re.split(r"\s+", s, maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--allow-production", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--backup-ack", action="store_true")
    args = ap.parse_args()

    env = dotenv_values(str(ROOT / ".env"))
    mongo_url = env.get("MONGO_URL") or os.environ.get("MONGO_URL")
    db_name = env.get("DB_NAME") or os.environ.get("DB_NAME")
    app_env = env.get("APP_ENV") or os.environ.get("APP_ENV") or ""
    if not (mongo_url and db_name):
        print("ERROR: MONGO_URL / DB_NAME missing from /app/backend/.env", file=sys.stderr)
        return 2

    target = redact_target_identity(mongo_url, db_name)
    if args.execute:
        try:
            require_cli_execute(args.execute)
            require_cli_confirmation(args.confirm, expected="SEED_EQUIPMENT_MAKE_MODEL")
            require_cli_backup_ack(args.backup_ack)
            require_cli_runtime_guard(
                app_env=app_env,
                db_name=db_name,
                allow_production=args.allow_production,
                expected_db_name="masci_safety",
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 3

    if not DATA.exists():
        print(f"ERROR: missing source file {DATA}", file=sys.stderr)
        return 4

    # Backup the JSON file
    if DATA.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        bak = DATA.with_suffix(f".{ts}.bak.json")
        shutil.copy2(DATA, bak)
        print(f"[backup] {DATA} -> {bak.name}")

    items: list[dict] = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"[load] {len(items)} items from {DATA}")

    # --- Mutate items ---
    fixed = 0
    for item in items:
        mm = (item.get("make_model") or "").strip()
        existing_make = (item.get("make") or "").strip()
        existing_model = (item.get("model") or "").strip()
        if existing_make and existing_model:
            continue
        if not mm:
            continue
        make, model = split_make_model(mm)
        if make and not existing_make:
            item["make"] = make
            fixed += 1
        if model and not existing_model:
            item["model"] = model

    print(f"[split] populated make/model on {fixed} items")

    if not args.execute:
        print(json.dumps({
            "mode": "dry-run",
            "target": target,
            "items": len(items),
            "fixed": fixed,
        }, indent=2))
        return 0

    # Write JSON back atomically
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    print(f"[write] {DATA} updated")

    # --- Mongo update ---
    client = MongoClient(mongo_url)
    db = client[db_name]
    coll = db.equipment_master

    upd_count = 0
    for item in items:
        if not item.get("make"):
            continue
        q = {"id": item.get("id")} if item.get("id") else {"display_label": item.get("display_label")}
        res = coll.update_one(q, {"$set": {"make": item["make"], "model": item.get("model", "")}})
        if res.modified_count:
            upd_count += 1

    print(f"[mongo] updated {upd_count} equipment_master documents in db={db_name}")

    # Sanity sample
    sample = list(
        coll.find(
            {"make": {"$ne": ""}}, {"_id": 0, "display_label": 1, "make": 1, "model": 1},
        ).limit(5)
    )
    print("[sample]")
    for s in sample:
        print(f"  - {s.get('display_label'):60s} | make={s.get('make'):20s} | model={s.get('model')}")

    print("DONE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
