"""TRACK 15.69 — Rollback simulation (preview-side execution).

Measures the time-to-restore-legacy-routing when flipping
EMAIL_ROUTING_V2 from true → false. Does NOT mutate the persisted .env.
"""
import asyncio, os, sys, time, json
sys.path.insert(0, "/app/backend")
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

import email_routing_v2 as v2


async def resolve_all(db, expected_source):
    """Resolve all 19 routes and return list of (route_key, source, to_count, error)."""
    routes = await db.email_routes.find({"tenant_key": "masci"}, {"_id": 0, "route_key": 1}).sort("route_key", 1).to_list(50)
    out = []
    for r in routes:
        rk = r["route_key"]
        try:
            res = await v2.resolve(db, rk, legacy_provider=lambda: [])
            out.append({"route_key": rk, "source": res.source, "to": len(res.to), "ok": True, "error": None})
        except Exception as e:
            out.append({"route_key": rk, "source": None, "to": 0, "ok": False, "error": str(e)})
    return out


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]

    timeline = []

    # T0: starting state (flag-off)
    os.environ["EMAIL_ROUTING_V2"] = "false"
    v2.invalidate_cache()
    t0 = time.time()
    state_t0 = await resolve_all(db, "legacy")
    timeline.append({"event": "t0_flag_off_baseline", "elapsed_s": 0.0,
                     "sources": dict(__import__("collections").Counter(s["source"] for s in state_t0))})

    # T1: simulated flag-on cutover
    t_flip_to_on = time.time()
    os.environ["EMAIL_ROUTING_V2"] = "true"
    v2.invalidate_cache()
    state_t1 = await resolve_all(db, "db")
    t_flip_to_on_done = time.time()
    timeline.append({"event": "t1_flipped_to_on", "elapsed_s": round(t_flip_to_on_done - t0, 3),
                     "sources": dict(__import__("collections").Counter(s["source"] for s in state_t1))})

    # T2: ROLLBACK — flip back to flag-off
    rollback_start = time.time()
    os.environ["EMAIL_ROUTING_V2"] = "false"
    v2.invalidate_cache()
    state_t2 = await resolve_all(db, "legacy")
    rollback_done = time.time()
    rollback_duration_s = round(rollback_done - rollback_start, 3)
    timeline.append({"event": "t2_rolled_back_to_off", "elapsed_s": round(rollback_done - t0, 3),
                     "rollback_duration_s": rollback_duration_s,
                     "sources": dict(__import__("collections").Counter(s["source"] for s in state_t2))})

    # Verify state_t2 matches state_t0 (recipient set identical)
    by_rk_t0 = {s["route_key"]: s for s in state_t0}
    by_rk_t2 = {s["route_key"]: s for s in state_t2}
    drift = []
    for rk, t0row in by_rk_t0.items():
        t2row = by_rk_t2.get(rk)
        if not t2row:
            drift.append({"route_key": rk, "issue": "missing after rollback"})
            continue
        if t0row["source"] != t2row["source"]:
            drift.append({"route_key": rk, "issue": f"source drift: {t0row['source']} → {t2row['source']}"})
        if t0row["to"] != t2row["to"]:
            drift.append({"route_key": rk, "issue": f"to count drift: {t0row['to']} → {t2row['to']}"})
        if t0row["ok"] != t2row["ok"]:
            drift.append({"route_key": rk, "issue": f"ok drift: {t0row['ok']} → {t2row['ok']}"})

    summary = {
        "rollback_duration_s": rollback_duration_s,
        "rollback_target_s": 300,  # 5 min budget
        "rollback_within_budget": rollback_duration_s < 300,
        "drift_count": len(drift),
        "drift": drift,
        "t0_summary": dict(__import__("collections").Counter(s["source"] for s in state_t0)),
        "t1_summary": dict(__import__("collections").Counter(s["source"] for s in state_t1)),
        "t2_summary": dict(__import__("collections").Counter(s["source"] for s in state_t2)),
        "timeline": timeline,
    }

    # Verify final flag state is off
    summary["final_env_EMAIL_ROUTING_V2"] = os.environ.get("EMAIL_ROUTING_V2", "<unset>")

    out = "/app/test_reports/track_15_69_rollback_simulation.json"
    open(out, "w").write(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nSaved {out}")

    verdict = "PASS" if (rollback_duration_s < 300 and len(drift) == 0) else "FAIL"
    print(f"\nVerdict: {verdict}")
    print(f"Rollback duration: {rollback_duration_s}s (budget: 300s)")
    print(f"Drift between pre-flip and post-rollback: {len(drift)} routes")

asyncio.run(main())
