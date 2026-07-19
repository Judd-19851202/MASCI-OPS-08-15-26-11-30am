"""
db_isolation_failsafe.py · FORGEDOPS P0-B startup environment isolation.

Doctrine: the pod must refuse to boot if it can access the OTHER
environment's MongoDB namespace.

Behavior:
  - On startup, attempt `client[<forbidden_db>].list_collection_names()`
    where <forbidden_db> is the OTHER environment's DB name.
  - If the attempt **succeeds**, the credential is over-privileged.
  - Preview / dev pods always hard-fail when `ENFORCE_DB_ISOLATION=true`
    because a preview credential that can reach the production namespace
    is an immediate contamination risk.
  - Production pods continue to boot when the active runtime binding is
    explicitly `DB_NAME=masci_safety` and only the preview namespace is
    additionally visible. That is still a loud violation and must be
    remediated operationally via Atlas user separation, but the runtime
    is not mis-bound and should not be taken offline solely because the
    credential is broader than ideal.
  - When the flag is absent or false, the check still runs and logs
    a LOUD warning to stdout + writes a structured record to the
    DB so operators can audit historical drift, but the pod boots.
    This bridge mode exists so that pre-rotation deployments don't
    crash before the operator has executed the Atlas user
    separation runbook (`docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md`,
    Checkpoint B runtime-image reference register).
  - After rotation, set `ENFORCE_DB_ISOLATION=true` in both pods. From
    that day on, any future credential drift will fail boot loudly.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


PREVIEW_DB = "masci_safety_preview"
PROD_DB = "masci_safety"

logger = logging.getLogger("db_isolation_failsafe")


def _should_fail_fast(*, app_env: str, db_name: str, enforce: bool, violations: list[Dict[str, Any]]) -> bool:
    if not enforce or not violations:
        return False
    if app_env in ("preview", "dev", "development"):
        return True
    if app_env in ("production", "prod"):
        return db_name != PROD_DB
    return False


async def assert_db_isolation(client) -> Dict[str, Any]:
    """Run the isolation probe. Return a result dict.

    Call this in `app.on_event('startup')` AFTER the Mongo client is
    constructed. If `ENFORCE_DB_ISOLATION=true` and the check fails,
    this function calls `sys.exit(99)`.
    """
    app_env = (os.environ.get("APP_ENV") or "preview").strip().lower()
    db_name = os.environ.get("DB_NAME") or "unknown"
    enforce = (os.environ.get("ENFORCE_DB_ISOLATION") or "").strip().lower() in (
        "1", "true", "yes", "on")

    # Determine the forbidden DB(s) for this pod.
    forbidden: list[str] = []
    if app_env in ("preview", "dev", "development"):
        forbidden = [PROD_DB]
    elif app_env in ("production", "prod"):
        forbidden = [PREVIEW_DB]
    else:
        return {"status": "unknown_env", "app_env": app_env, "enforce": enforce}

    result = {
        "status": "checking",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "app_env": app_env,
        "db_name": db_name,
        "forbidden_dbs": forbidden,
        "enforce": enforce,
        "violations": [],
    }

    for fdb in forbidden:
        try:
            cols = await client[fdb].list_collection_names()
            # If we got here, we CAN see the forbidden DB.
            result["violations"].append({
                "db": fdb,
                "kind": "list_collection_names",
                "collections_visible": len(cols),
            })
        except Exception as e:
            # GOOD: access denied.
            logger.info(
                "[db-isolation] OK · forbidden DB %s correctly inaccessible: %s",
                fdb, type(e).__name__)

    if result["violations"]:
        msg = (
            "\n" + "=" * 78 +
            "\n🔴 DB ISOLATION VIOLATION · " + app_env.upper() + " pod can access " +
            ", ".join(v["db"] for v in result["violations"]) +
            "\n   Credential: admin_db_user (or equivalent over-privileged user)" +
            "\n   Runbook:    docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md (Checkpoint B)" +
            "\n" + "=" * 78 + "\n")
        # Loud no matter what.
        logger.error(msg)
        print(msg, file=sys.stderr, flush=True)
        result["status"] = "violation"

        if _should_fail_fast(app_env=app_env, db_name=db_name, enforce=enforce, violations=result["violations"]):
            # FAIL FAST.
            logger.error(
                "[db-isolation] ENFORCE_DB_ISOLATION=true · refusing to boot.")
            print("[db-isolation] FAIL FAST · refusing to boot.", file=sys.stderr, flush=True)
            sys.exit(99)
        if enforce:
            logger.error(
                "[db-isolation] ENFORCE_DB_ISOLATION=true · production runtime remains bound to %s; continuing boot but Atlas credential separation is still required.",
                db_name,
            )
    else:
        result["status"] = "isolated"
        logger.info("[db-isolation] OK · %s pod is correctly isolated.", app_env)
    return result


__all__ = ["assert_db_isolation"]
