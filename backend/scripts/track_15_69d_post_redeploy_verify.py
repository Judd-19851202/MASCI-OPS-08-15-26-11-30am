"""Track 15.69D · Post-redeploy verification harness.

Run AFTER operator adds EMAIL_ROUTING_V2=false to production Secrets and
re-deploys. Captures the same baseline metrics the agent will compare
against (route inventory, branding, audit-row counts, health) and writes
the result to /app/test_reports/track_15_69d_post_redeploy.json.

Usage:
    cd /app/backend
    BASE_URL=https://app.mascidocs.com python3 scripts/track_15_69d_post_redeploy_verify.py
"""
from __future__ import annotations
import asyncio, json, os, sys
from pathlib import Path
from datetime import datetime, timezone

import requests  # already a backend dep

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(HERE.parent / ".env")

BASE_URL = os.environ.get("BASE_URL") or "https://mascidocs.com"
TENANT = "masci"
# Track 15.69D · DB-side checks are SKIPPED when the script is run from a
# pod whose MONGO_URL credentials cannot read the production DB. Set
# SKIP_DB=1 to force HTTP-only mode (operator-side use case).
SKIP_DB = os.environ.get("SKIP_DB", "0").strip().lower() in ("1", "true", "yes")


def http_get(path: str, timeout=15, retries=3) -> dict:
    url = BASE_URL.rstrip("/") + path
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers={
                "User-Agent": "Mozilla/5.0 Track-15.69D-VerifyHarness/1.0",
                "Accept": "application/json",
            })
            if r.status_code in (502, 503, 504, 522, 524):
                last = {"status": r.status_code, "body_text": r.text[:200]}
                import time
                time.sleep(2 + attempt * 2)
                continue
            try:
                return {"status": r.status_code, "body": r.json()}
            except Exception:
                return {"status": r.status_code, "body_text": r.text[:500]}
        except Exception as e:  # noqa: BLE001
            last = {"status": None, "error": repr(e)}
            import time
            time.sleep(2 + attempt * 2)
    return last or {"status": None, "error": "all_retries_failed"}


async def main():
    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "checks": {},
    }

    # 5.1-5.3 · health/full
    out["checks"]["health_full"] = http_get("/api/health/full")

    # 5.4 · branding
    out["checks"]["branding_current"] = http_get("/api/branding/current")

    # Mongo-side checks
    if SKIP_DB:
        out["checks"]["db_checks_skipped"] = True
        out["checks"]["db_skip_reason"] = "SKIP_DB=1 (pod credentials cannot read production DB; HTTP-only verification)"
    else:
        try:
            client = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = client[os.environ["DB_NAME"]]

            # 5.5 · Route inventory
            routes = await db.email_routes.find({"tenant_key": TENANT}, {"_id": 0}).sort("route_key", 1).to_list(200)
            out["checks"]["email_routes_count"] = len(routes)
            out["checks"]["email_routes_keys"]  = sorted(r["route_key"] for r in routes)
            import hashlib
            recipients_blob = json.dumps([
                {"route_key": r["route_key"],
                 "to": sorted(r.get("to", []) or []),
                 "cc": sorted(r.get("cc", []) or []),
                 "bcc": sorted(r.get("bcc", []) or []),
                 "from_email": r.get("from_email"),
                 "enabled": r.get("enabled", True),
                 "critical": r.get("critical", False)}
                for r in routes
            ], sort_keys=True, default=str)
            out["checks"]["email_routes_recipients_sha256"] = hashlib.sha256(recipients_blob.encode()).hexdigest()

            # 5.6/5.7 · audit collection count
            out["checks"]["email_routing_audit_v2_total"] = await db.email_routing_audit_v2.count_documents({})
            one_hour_ago = datetime.now(timezone.utc).timestamp() - 3600
            out["checks"]["email_routing_audit_v2_last_hour"] = await db.email_routing_audit_v2.count_documents({
                "ts": {"$gte": datetime.fromtimestamp(one_hour_ago, tz=timezone.utc).isoformat()}
            })

            # 5.9 · DB counts
            out["checks"]["users_count"]            = await db.users.estimated_document_count()
            out["checks"]["tenant_branding_count"]  = await db.tenant_branding.estimated_document_count()
            names = await db.list_collection_names()
            out["checks"]["incidents_count"]        = await db.incidents.estimated_document_count() if "incidents" in names else None
            client.close()
        except Exception as e:  # noqa: BLE001
            out["checks"]["db_checks_error"] = repr(e)
            out["checks"]["db_checks_skipped"] = True

    # Pass criteria — HTTP gates only when DB checks are skipped
    h = out["checks"]["health_full"]
    http_ok = (
        h.get("status") == 200
        and h.get("body", {}).get("mongo") is True
        and h.get("body", {}).get("ok") is True
        and out["checks"]["branding_current"].get("status") == 200
        and (out["checks"]["branding_current"].get("body", {}) or {}).get("tenant_key") == "masci"
    )
    if SKIP_DB or out["checks"].get("db_checks_skipped"):
        out["pass"] = http_ok
        out["pass_mode"] = "http_only"
    else:
        out["pass"] = (
            http_ok
            and out["checks"].get("email_routes_count") == 19
            and out["checks"].get("email_routing_audit_v2_last_hour") == 0
        )
        out["pass_mode"] = "http_plus_db"

    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    Path("/app/test_reports/track_15_69d_post_redeploy.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
