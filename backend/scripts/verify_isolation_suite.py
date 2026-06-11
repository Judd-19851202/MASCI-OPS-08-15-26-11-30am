"""
scripts/verify_isolation_suite.py · FORGEDOPS P0 verification suite.

PREPARED · NOT auto-executed.

Six entry points (operator runs each manually after Atlas user
separation completes). Each prints PASS/FAIL with reasons and exits
non-zero on failure.

Usage:
    python scripts/verify_isolation_suite.py preview_cannot_read_production
    python scripts/verify_isolation_suite.py production_cannot_read_preview
    python scripts/verify_isolation_suite.py db_isolation
    python scripts/verify_isolation_suite.py post_rotation_health
    python scripts/verify_isolation_suite.py production_stability
    python scripts/verify_isolation_suite.py trust_sprint_completion

ALSO callable via the matching named wrapper scripts:
  verify_preview_cannot_read_production.py
  verify_production_cannot_read_preview.py
  verify_db_isolation.py
  verify_post_rotation_health.py
  verify_production_stability.py
  verify_trust_sprint_completion.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure

load_dotenv("/app/backend/.env")

PREVIEW_DB = "masci_safety_preview"
PROD_DB = "masci_safety"


def _stamp(msg, ok=True):
    icon = "🟢 PASS" if ok else "🔴 FAIL"
    print(f"{icon} · {datetime.now(timezone.utc).isoformat()} · {msg}")


async def _expect_unauthorized(client, forbidden_db: str) -> bool:
    try:
        cols = await client[forbidden_db].list_collection_names()
        _stamp(f"can list {forbidden_db} ({len(cols)} cols) — expected Unauthorized", ok=False)
        return False
    except OperationFailure as e:
        if "not authorized" in str(e).lower() or "unauthorized" in str(e).lower():
            _stamp(f"{forbidden_db} correctly returned Unauthorized")
            return True
        _stamp(f"{forbidden_db} unexpected OperationFailure: {e}", ok=False)
        return False
    except Exception as e:  # noqa: BLE001
        _stamp(f"{forbidden_db} unexpected error: {type(e).__name__}: {e}", ok=False)
        return False


async def preview_cannot_read_production() -> int:
    """Run FROM PREVIEW POD. Must show Unauthorized on masci_safety."""
    if os.environ.get("APP_ENV", "").strip().lower() != "preview":
        _stamp("not running in preview env — skip", ok=False); return 2
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    ok = await _expect_unauthorized(client, PROD_DB)
    client.close()
    return 0 if ok else 1


async def production_cannot_read_preview() -> int:
    if os.environ.get("APP_ENV", "").strip().lower() != "production":
        _stamp("not running in production env — skip", ok=False); return 2
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    ok = await _expect_unauthorized(client, PREVIEW_DB)
    client.close()
    return 0 if ok else 1


async def db_isolation() -> int:
    """Env-aware: runs the correct probe based on APP_ENV."""
    env = os.environ.get("APP_ENV", "").strip().lower()
    if env == "preview": return await preview_cannot_read_production()
    if env == "production": return await production_cannot_read_preview()
    _stamp(f"unknown APP_ENV={env!r}", ok=False); return 2


async def post_rotation_health() -> int:
    """API + DB + isolation triple check.

    Hardened 2026-02-10: every httpx call is wrapped so a network
    blip does not raise an unhandled exception and the chain caller
    (trust_sprint_completion) sees a definitive exit code.
    """
    import httpx
    base = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
    all_ok = True
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            try:
                r = await c.get(f"{base}/api/health")
                if r.status_code == 200:
                    _stamp("api/health = 200")
                else:
                    _stamp(f"api/health = {r.status_code}", ok=False); all_ok = False
            except Exception as e:  # noqa: BLE001
                _stamp(f"api/health unreachable: {type(e).__name__}: {e}", ok=False); all_ok = False
            try:
                r = await c.get(f"{base}/api/platform/data-truth")
                if r.status_code == 200:
                    j = r.json()
                    env = j.get("environment"); db = j.get("database")
                    _stamp(f"data-truth env={env} db={db}")
                    expected_db = (PREVIEW_DB if env == "preview"
                                   else PROD_DB if env == "production" else None)
                    if expected_db and db != expected_db:
                        _stamp(f"db mismatch: got {db}, expected {expected_db}", ok=False); all_ok = False
                else:
                    _stamp(f"data-truth = {r.status_code}", ok=False); all_ok = False
            except Exception as e:  # noqa: BLE001
                _stamp(f"data-truth unreachable: {type(e).__name__}: {e}", ok=False); all_ok = False
    except Exception as e:  # noqa: BLE001
        _stamp(f"httpx client init failed: {type(e).__name__}: {e}", ok=False); all_ok = False
    iso_ok = (await db_isolation()) == 0
    if not iso_ok: all_ok = False
    return 0 if all_ok else 1


async def production_stability() -> int:
    """Spot-check critical endpoints respond + DB queries succeed.

    Must run ONLY from a production pod. Without this guard the script
    silently passes against the preview DB, masking F-20 (wrong-env false
    positive). Audit 2026-02-10 confirmed the guard was missing.
    """
    env = os.environ.get("APP_ENV", "").strip().lower()
    if env != "production":
        _stamp(f"refusing to run · APP_ENV={env!r} · production_stability is production-only", ok=False)
        return 2
    db_name = os.environ.get("DB_NAME", "").strip()
    if db_name != PROD_DB:
        _stamp(f"refusing to run · DB_NAME={db_name!r} ≠ {PROD_DB!r}", ok=False)
        return 2
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[db_name]
    all_ok = True
    for col in ("employees", "jobs_master", "equipment_master",
                "dispatch_assignments", "fleet_defects", "incidents"):
        try:
            n = await db[col].count_documents({})
            _stamp(f"{col}.count = {n}")
        except Exception as e:  # noqa: BLE001
            _stamp(f"{col} read failed: {e}", ok=False); all_ok = False
    client.close()
    return 0 if all_ok else 1


async def trust_sprint_completion() -> int:
    """Final gate. Calls db_isolation + post_rotation_health + stability."""
    rc1 = await db_isolation()
    rc2 = await post_rotation_health()
    rc3 = await production_stability()
    rc = max(rc1, rc2, rc3)
    if rc == 0:
        _stamp("ALL THREE PASSED — workstream eligible for closure.")
    else:
        _stamp(f"completion blocked (db_iso={rc1} health={rc2} stab={rc3})", ok=False)
    return rc


HANDLERS = {
    "preview_cannot_read_production": preview_cannot_read_production,
    "production_cannot_read_preview": production_cannot_read_preview,
    "db_isolation":                   db_isolation,
    "post_rotation_health":           post_rotation_health,
    "production_stability":           production_stability,
    "trust_sprint_completion":        trust_sprint_completion,
}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in HANDLERS:
        print("usage: python verify_isolation_suite.py <" +
              "|".join(HANDLERS.keys()) + ">", file=sys.stderr)
        sys.exit(2)
    sys.exit(asyncio.run(HANDLERS[sys.argv[1]]()))
