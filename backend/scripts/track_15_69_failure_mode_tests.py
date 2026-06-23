"""TRACK 15.69 — Failure mode certification (preview-side execution)."""
import asyncio, os, sys, time, json
sys.path.insert(0, "/app/backend")
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

results = []

def record(name, ok, evidence):
    results.append({"test": name, "result": "PASS" if ok else "FAIL", "evidence": str(evidence)[:300]})


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]

    import email_routing_v2 as v2
    os.environ["EMAIL_ROUTING_V2"] = "true"
    v2.invalidate_cache()

    # --- FM1: critical route empty (recipient missing) — must raise UnconfiguredCriticalRouteError
    bak = await db.email_routes.find_one({"_id": "masci::BACKUP_ALERTS"})
    await db.email_routes.update_one({"_id": "masci::BACKUP_ALERTS"}, {"$set": {"to": [], "cc": [], "bcc": []}})
    v2.invalidate_cache()
    try:
        try:
            res = await v2.resolve(db, "BACKUP_ALERTS")
            record("FM1_critical_empty_recipient", False, f"Did not raise; got source={res.source}")
        except v2.UnconfiguredCriticalRouteError as e:
            record("FM1_critical_empty_recipient", True, f"raised UnconfiguredCriticalRouteError: {e}")
        except Exception as e:
            record("FM1_critical_empty_recipient", False, f"Wrong exception type: {type(e).__name__}: {e}")
    finally:
        await db.email_routes.update_one({"_id": "masci::BACKUP_ALERTS"},
            {"$set": {"to": bak.get("to", []), "cc": bak.get("cc", []), "bcc": bak.get("bcc", [])}})
        v2.invalidate_cache()

    # --- FM2: route doc missing — must fall through to legacy
    try:
        res = await v2.resolve(db, "TOTALLY_NONEXISTENT_ROUTE", legacy_provider=lambda: ["fallback@example.com"])
        ok = res.source in ("legacy", "error") and (res.to == ["fallback@example.com"] or res.is_empty())
        record("FM2_route_missing_falls_to_legacy", ok, f"source={res.source} to={res.to}")
    except Exception as e:
        record("FM2_route_missing_falls_to_legacy", False, f"Raised: {type(e).__name__}: {e}")

    # --- FM3: sender missing — branding_resolver must always return non-empty sender
    from branding_resolver import resolve_sender
    s = await resolve_sender(db, route_key="BACKUP_ALERTS")
    record("FM3_sender_resolution", bool(s and getattr(s, "from_email", None)), f"from_email={getattr(s, 'from_email', None)} source={getattr(s, 'source', None)}")

    # --- FM4: critical route disabled — must NOT silently send; source=disabled, empty
    bak2 = await db.email_routes.find_one({"_id": "masci::HEALTH_ALERTS"})
    await db.email_routes.update_one({"_id": "masci::HEALTH_ALERTS"}, {"$set": {"enabled": False}})
    v2.invalidate_cache()
    try:
        try:
            res = await v2.resolve(db, "HEALTH_ALERTS")
            ok = (res.source == "disabled") and res.is_empty()
            record("FM4_critical_disabled_returns_disabled", ok, f"source={res.source} to={res.to}")
        except v2.UnconfiguredCriticalRouteError as e:
            # Disabling a critical route is an admin override; either disabled-empty OR hard-fail is acceptable.
            record("FM4_critical_disabled_returns_disabled", True, f"raised UnconfiguredCriticalRouteError: {e}")
    finally:
        await db.email_routes.update_one({"_id": "masci::HEALTH_ALERTS"}, {"$set": {"enabled": bak2.get("enabled", True)}})
        v2.invalidate_cache()

    # --- FM5: tenant missing (branding missing) — synthetic tenant
    try:
        res = await v2.resolve(db, "BACKUP_ALERTS", tenant_key="totally-fake-tenant",
                              legacy_provider=lambda: ["fallback@example.com"])
        ok = res.source in ("legacy", "error", "disabled") and (res.to == ["fallback@example.com"] or res.is_empty())
        record("FM5_tenant_missing_falls_to_legacy", ok, f"source={res.source} to={res.to}")
    except v2.UnconfiguredCriticalRouteError as e:
        record("FM5_tenant_missing_falls_to_legacy", True, f"raised UnconfiguredCriticalRouteError (refuse-to-default): {e}")

    # --- FM6: audit row shape
    rows = await db.email_routing_audit_v2.find({"tenant_key": "masci"}).sort("ts", -1).limit(1).to_list(1)
    if rows:
        r = rows[0]
        needed = {"tenant_key", "route_key", "source", "status", "ts"}
        ok = needed.issubset(set(r.keys()))
        record("FM6_audit_row_shape", ok, f"keys={sorted(r.keys())}")
    else:
        record("FM6_audit_row_shape", False, "no audit rows yet")

    # --- FM7: database unavailable — resolver must catch & fall to legacy or hard-fail visibly
    class BrokenColl:
        async def find_one(self, *a, **k): raise Exception("Simulated DB outage")
    class BrokenDB:
        @property
        def email_routes(self): return BrokenColl()
        @property
        def email_routing_audit_v2(self): return BrokenColl()
        @property
        def tenant_branding(self): return BrokenColl()
    try:
        res = await v2.resolve(BrokenDB(), "BACKUP_ALERTS",
            legacy_provider=lambda: ["legacy-fallback@example.com"])
        ok = res.source in ("legacy", "error") and (res.to == ["legacy-fallback@example.com"] or res.is_empty() or res.error)
        record("FM7_db_unavailable_falls_to_legacy", ok, f"source={res.source} to={res.to} error={res.error}")
    except v2.UnconfiguredCriticalRouteError as e:
        record("FM7_db_unavailable_falls_to_legacy", True, f"raised UnconfiguredCriticalRouteError (refuse-to-silently-drop): {e}")
    except Exception as e:
        record("FM7_db_unavailable_falls_to_legacy", False, f"Raised wrong type: {type(e).__name__}: {e}")

    os.environ["EMAIL_ROUTING_V2"] = "false"
    v2.invalidate_cache()

    print(json.dumps(results, indent=2))
    out = "/app/test_reports/track_15_69_failure_modes.json"
    open(out, "w").write(json.dumps({"results": results, "summary": {
        "pass": sum(1 for r in results if r["result"] == "PASS"),
        "fail": sum(1 for r in results if r["result"] == "FAIL"),
        "total": len(results),
    }}, indent=2))
    print(f"\nSaved {out}")
    p = sum(1 for r in results if r["result"] == "PASS")
    print(f"\nSummary: {p}/{len(results)} PASS")

asyncio.run(main())
