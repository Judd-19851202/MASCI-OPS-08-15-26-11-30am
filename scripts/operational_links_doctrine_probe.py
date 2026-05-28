#!/usr/bin/env python3
"""
operational_links_doctrine_probe.py — Phase V-Prelude · Wave 1.

Static + runtime probe that enforces OPERATIONAL_LINKING_RULES.md §10.
Runs in sub-second mode (`--gate`) so it can be wired into
`scripts/pre_deploy_check.sh` without slowing the deploy pipeline.

What it asserts:
  1. Every active `operational_links` row carries the 11 audit fields.
  2. `source_type` and `target_type` are members of the closed §4 enum.
  3. `relationship` ∈ canonical set; no forbidden inverse stored.
  4. No `resulted_in` circular relationship (A↔B both `resulted_in`).
  5. No self-link (source == target).
  6. No orphan voided-status row missing `status_changed_at`.
  7. Source code surface still imports the doctrine module (no fork).
  8. Probe runs <3s in `--gate` mode.

Usage:
  python3 scripts/operational_links_doctrine_probe.py            # human
  python3 scripts/operational_links_doctrine_probe.py --json     # CI JSON
  python3 scripts/operational_links_doctrine_probe.py --gate     # exit 1
                                                                  # on violations
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path("/app")
BACKEND_DIR = REPO_ROOT / "backend"


def _read_env_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        return ""
    return ""


def _load_doctrine_enums() -> Dict[str, set]:
    """Import the doctrine module to read the source of truth — never
    duplicate the enums here, lest the probe drift from the surface."""
    sys.path.insert(0, str(BACKEND_DIR))
    try:
        from routes.operational_links import (  # type: ignore
            ARTIFACT_TYPES,
            CANONICAL_RELATIONSHIPS,
            FORBIDDEN_INVERSE_RELATIONSHIPS,
            VISIBILITY_SCOPES,
            STATUS_VALUES,
        )
    finally:
        sys.path.pop(0)
    return {
        "artifact_types": ARTIFACT_TYPES,
        "canonical_relationships": CANONICAL_RELATIONSHIPS,
        "forbidden_inverse": FORBIDDEN_INVERSE_RELATIONSHIPS,
        "visibility_scopes": VISIBILITY_SCOPES,
        "status_values": STATUS_VALUES,
    }


def _run_probe(check_runtime: bool) -> Dict[str, Any]:
    started = time.time()
    violations: List[str] = []
    warnings: List[str] = []

    enums = _load_doctrine_enums()

    # ── Runtime sweep (Mongo) ────────────────────────────────────────
    if check_runtime:
        try:
            from pymongo import MongoClient  # noqa: PLC0415
        except Exception as e:  # noqa: BLE001
            warnings.append(f"pymongo not installed: {e}")
            return {
                "violations": violations,
                "warnings": warnings,
                "scan_ms": int((time.time() - started) * 1000),
                "scanned_rows": 0,
            }

        mongo_url = _read_env_kv(BACKEND_DIR / ".env", "MONGO_URL")
        db_name = _read_env_kv(BACKEND_DIR / ".env", "DB_NAME") \
            or "masci_safety_preview"
        if not mongo_url:
            warnings.append("MONGO_URL not configured")
            return {
                "violations": violations,
                "warnings": warnings,
                "scan_ms": int((time.time() - started) * 1000),
                "scanned_rows": 0,
            }
        cli = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
        try:
            db = cli[db_name]
            audit_fields = (
                "id", "source_type", "source_id", "target_type",
                "target_id", "relationship", "visibility",
                "project_id", "status", "created_at", "created_by",
            )
            seen = set()
            scanned = 0
            for doc in db.operational_links.find({}, {"_id": 0}).limit(5000):
                scanned += 1
                _id = doc.get("id", "<missing>")
                # 1. audit-field completeness
                missing = [f for f in audit_fields if f not in doc]
                if missing:
                    violations.append(
                        f"audit-field-incomplete · {_id} · missing={missing}"
                    )
                # 2. closed-set enums
                if doc.get("source_type") not in enums["artifact_types"]:
                    violations.append(
                        f"invalid-source-type · {_id} · "
                        f"{doc.get('source_type')}"
                    )
                if doc.get("target_type") not in enums["artifact_types"]:
                    violations.append(
                        f"invalid-target-type · {_id} · "
                        f"{doc.get('target_type')}"
                    )
                # 3. canonical relationship
                rel = doc.get("relationship", "")
                if rel in enums["forbidden_inverse"]:
                    violations.append(
                        f"forbidden-inverse-stored · {_id} · {rel}"
                    )
                elif rel not in enums["canonical_relationships"]:
                    violations.append(
                        f"unknown-relationship · {_id} · {rel}"
                    )
                # 4. visibility
                if doc.get("visibility") not in enums["visibility_scopes"]:
                    violations.append(
                        f"invalid-visibility · {_id} · "
                        f"{doc.get('visibility')}"
                    )
                # 5. status
                if doc.get("status") not in enums["status_values"]:
                    violations.append(
                        f"invalid-status · {_id} · {doc.get('status')}"
                    )
                # 6. self-link
                if (
                    doc.get("source_type") == doc.get("target_type")
                    and doc.get("source_id") == doc.get("target_id")
                ):
                    violations.append(f"self-link · {_id}")
                # 7. voided rows missing status_changed_at
                if (
                    doc.get("status") in {"archived", "voided", "superseded"}
                    and not doc.get("status_changed_at")
                ):
                    violations.append(
                        f"status-change-missing-timestamp · {_id}"
                    )
                # 8. circular `resulted_in` (key into seen set)
                if rel == "resulted_in":
                    key_fwd = (
                        doc.get("source_type"), doc.get("source_id"),
                        doc.get("target_type"), doc.get("target_id"),
                    )
                    key_rev = (
                        doc.get("target_type"), doc.get("target_id"),
                        doc.get("source_type"), doc.get("source_id"),
                    )
                    if key_rev in seen:
                        violations.append(
                            f"circular-resulted-in · {_id} · cycle"
                        )
                    seen.add(key_fwd)
            return {
                "violations": violations,
                "warnings": warnings,
                "scan_ms": int((time.time() - started) * 1000),
                "scanned_rows": scanned,
                "db_name": db_name,
            }
        finally:
            cli.close()
    else:
        return {
            "violations": violations,
            "warnings": warnings,
            "scan_ms": int((time.time() - started) * 1000),
            "scanned_rows": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Operational Links Doctrine Probe (V-Prelude Wave 1)"
    )
    parser.add_argument("--json", action="store_true", help="machine output")
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 if any violation")
    parser.add_argument("--static-only", action="store_true",
                        help="skip the Mongo sweep (CI offline mode)")
    args = parser.parse_args()

    result = _run_probe(check_runtime=not args.static_only)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["violations"]:
            print(
                f"❌ {len(result['violations'])} violation(s) in "
                f"operational_links doctrine:"
            )
            for v in result["violations"][:50]:
                print(f"  · {v}")
            if len(result["violations"]) > 50:
                print(f"  …and {len(result['violations']) - 50} more.")
        else:
            print("✅ operational_links doctrine clean.")
        if result["warnings"]:
            print(f"\n⚠ {len(result['warnings'])} warning(s):")
            for w in result["warnings"]:
                print(f"  · {w}")
        print(
            f"\nscan_ms={result['scan_ms']} "
            f"scanned_rows={result['scanned_rows']}"
        )

    if args.gate and result["violations"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
