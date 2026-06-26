"""TRACK 15.93 · Zero-Touch Production Deployment Hardening.

Canonical system bootstrap service. ONE entry point. Runs on every
backend startup. Guarantees required system records exist before the
readiness gate flips, so a fresh deploy is operational without any
manual seed step.

Contract
========

* Idempotent — safe to run unlimited times. Create-if-missing only.
* Admin-safe — NEVER overwrites rows where ``source in {"admin","manual"}``
  or ``admin_customized=True``. Operator edits are sacred.
* Critical-route safety — refuses to insert a critical route with an
  empty TO list (matches the seed script's behaviour).
* Append-only history — every run writes one document to
  ``db.system_bootstrap_history`` for forensics. The latest run is
  also mirrored on ``db.system_bootstrap_status`` (single doc,
  ``_id="latest"``) for fast readiness-gate reads.
* Non-fatal failure — if a step errors, the step is marked failed and
  the bootstrap result is ``ok=False``; the process does NOT crash.
  The readiness gate is responsible for blocking deploy in that case.

This module re-uses the catalog from
``scripts/track_15_65_seed_email_routes.py`` (single source of truth
for the canonical 19-route catalog). It does NOT duplicate that logic.

Bootstrap version bumps when the contract or step list changes.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend/scripts is importable to re-use build_catalog().
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Re-use the canonical catalog builder. Single source of truth.
from track_15_65_seed_email_routes import build_catalog, _dedup, TENANT_KEY  # noqa: E402


BOOTSTRAP_VERSION = 1
"""Bump when the bootstrap contract changes (new steps, new invariants)."""


logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _ensure_email_routes(db) -> Dict[str, Any]:
    """Step: ``email_routes`` first-time initialization.

    Reads the canonical catalog (env-derived recipients) and inserts
    each missing route document. Never updates existing rows. Never
    deletes. Refuses to insert a critical route with empty TO.
    """
    step: Dict[str, Any] = {
        "name": "email_routes",
        "status": "ok",
        "created": [],
        "skipped_existing": [],
        "skipped_admin_customized": [],
        "skipped_critical_empty": [],
        "errors": [],
        "total_catalog": 0,
        "missing_items": [],
    }
    try:
        catalog = build_catalog()
    except Exception as e:  # noqa: BLE001
        step["status"] = "failed"
        step["errors"].append({"phase": "build_catalog", "error": str(e)})
        return step

    step["total_catalog"] = len(catalog)
    now_iso = _iso_now()

    for route in catalog:
        rk = route["route_key"]
        _id = f"{TENANT_KEY}::{rk}"
        try:
            existing = await db.email_routes.find_one({"_id": _id})
        except Exception as e:  # noqa: BLE001
            step["status"] = "failed"
            step["errors"].append({"route_key": rk, "phase": "find", "error": str(e)})
            continue

        if existing is not None:
            # NEVER overwrite — even if the catalog changed. Operator
            # edits + prior seeds are both preserved.
            customized = (
                existing.get("source") in ("admin", "manual")
                or existing.get("admin_customized")
            )
            if customized:
                step["skipped_admin_customized"].append(rk)
            else:
                step["skipped_existing"].append(rk)
            continue

        # Build the fresh doc (mirrors seed script schema exactly).
        new_doc = {
            "_id": _id,
            "tenant_key": TENANT_KEY,
            "route_key": rk,
            "display_name": route["display_name"],
            "description": route["description"],
            "category": route.get("category", "general"),
            "severity": route.get("severity", "info"),
            "to": _dedup(route.get("to") or []),
            "cc": _dedup(route.get("cc") or []),
            "bcc": _dedup(route.get("bcc") or []),
            "from_email": route.get("from_email"),
            "reply_to": route.get("reply_to"),
            "owner_role": route.get("owner_role"),
            "critical": bool(route.get("critical", False)),
            "enabled": bool(route.get("enabled", True)),
            "fallback_env_keys": list(route.get("fallback_env_keys") or []),
            "legacy_key": route.get("legacy_key"),
            "source": "bootstrap",
            "version": 1,
            "created_at": now_iso,
            "updated_at": now_iso,
            "updated_by": "system_bootstrap",
            "last_tested_at": None,
            "last_test_status": None,
        }

        # Critical-route safety — refuse to seed an empty critical route.
        if new_doc["critical"] and not new_doc["to"]:
            step["skipped_critical_empty"].append(rk)
            step["missing_items"].append(
                f"critical route {rk} has no recipient (env vars unset)"
            )
            continue

        try:
            await db.email_routes.insert_one(new_doc)
            step["created"].append(rk)
        except Exception as e:  # noqa: BLE001
            # Race-safe: someone else may have created it between our
            # find_one and insert_one. Treat duplicate-key as skip.
            msg = str(e).lower()
            if "duplicate" in msg or "e11000" in msg:
                step["skipped_existing"].append(rk)
                continue
            step["status"] = "failed"
            step["errors"].append({"route_key": rk, "phase": "insert", "error": str(e)})

    # Critical-route presence verification (mirrors the trust-gate
    # check in lib/master_data_trust.py exactly).
    critical_keys = {
        "COMPLIANCE_ALWAYS_CC": "Compliance Always-CC catch-all",
        "SAFETY_FORMS_TO": "Safety Forms inbox",
        "PRE_OP_FAIL_FALLBACK": "Pre-Op / DVIR fail fallback (shop manager)",
    }
    for key, label in critical_keys.items():
        try:
            row = await db.email_routes.find_one(
                {"route_key": key, "enabled": True}, {"_id": 0, "to": 1}
            )
        except Exception:
            row = None
        to_list = (row or {}).get("to") or []
        if not [a for a in to_list if (a or "").strip()]:
            step["missing_items"].append(label)

    # Index creation (idempotent — safe across restarts).
    try:
        await db.email_routes.create_index([("tenant_key", 1), ("route_key", 1)])
    except Exception:
        pass

    return step


async def _ensure_history_indexes(db) -> Dict[str, Any]:
    """Step: ensure the bootstrap-history collection has its index."""
    step: Dict[str, Any] = {"name": "history_indexes", "status": "ok", "errors": []}
    try:
        await db.system_bootstrap_history.create_index([("ts", -1)])
    except Exception as e:  # noqa: BLE001
        step["status"] = "failed"
        step["errors"].append(str(e))
    return step


async def run_system_bootstrap(db) -> Dict[str, Any]:
    """Run the canonical system bootstrap. Returns the result envelope.

    Result shape (also persisted to ``db.system_bootstrap_status``
    under ``_id="latest"`` and appended to ``db.system_bootstrap_history``)::

        {
          "version": 1,
          "started_at": "...",
          "completed_at": "...",
          "ok": bool,
          "steps": [
            {"name": "email_routes", "status": "ok"|"failed", ...},
            ...
          ],
          "missing_items": [...],   # flat list across all steps
          "tenant_key": "masci",
        }
    """
    started_at = _iso_now()
    result: Dict[str, Any] = {
        "version": BOOTSTRAP_VERSION,
        "started_at": started_at,
        "completed_at": None,
        "ok": True,
        "steps": [],
        "missing_items": [],
        "tenant_key": TENANT_KEY,
    }

    # Step 1 — history indexes (cheap, runs first so subsequent step
    # records can be queried efficiently if needed).
    step_idx = await _ensure_history_indexes(db)
    result["steps"].append(step_idx)
    if step_idx["status"] != "ok":
        result["ok"] = False

    # Step 2 — email_routes catalog first-time initialization.
    step_routes = await _ensure_email_routes(db)
    result["steps"].append(step_routes)
    if step_routes["status"] != "ok":
        result["ok"] = False
    result["missing_items"].extend(step_routes.get("missing_items") or [])

    # Final verdict: critical missing_items also mean not-ok.
    if result["missing_items"]:
        result["ok"] = False

    completed_at = _iso_now()
    result["completed_at"] = completed_at

    # Persist — latest pointer + append history. Both are best-effort:
    # if persistence itself fails we still log + return the in-memory
    # result so the readiness gate can react.
    try:
        await db.system_bootstrap_status.replace_one(
            {"_id": "latest"}, {"_id": "latest", **result}, upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[system-bootstrap] failed to persist 'latest' status: %s", e)
    try:
        await db.system_bootstrap_history.insert_one(
            {"ts": completed_at, **{k: v for k, v in result.items() if k != "_id"}}
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[system-bootstrap] failed to append history row: %s", e)

    return result


async def read_latest_bootstrap_status(db) -> Dict[str, Any] | None:
    """Read the most recent bootstrap result. Returns None if the
    bootstrap has never run (e.g. legacy DB from before 15.93).

    Used by the deployment-readiness endpoint to publish bootstrap
    state and to fail the gate when bootstrap incomplete.
    """
    try:
        doc = await db.system_bootstrap_status.find_one({"_id": "latest"})
    except Exception:
        return None
    if not doc:
        return None
    doc.pop("_id", None)
    return doc
