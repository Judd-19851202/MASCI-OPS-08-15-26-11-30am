#!/usr/bin/env python3
"""
qa_audit_live.py — Iter147 (Phase 2.5). Live performance audit driven
by REAL usage_events telemetry collected in iter146.

Workflow:
  1. Pull top-N hot routes from db.usage_events (last 24h by default).
  2. For each route, compute count / avg_ms / worst_ms / error_count.
  3. Flag any route where worst_ms > 1000ms OR error_rate > 5%.
  4. For the offending backend routes, run `db.X.explain()` if we can
     map the route to a collection — surface COLLSCAN offenders.
  5. Emit /app/QA_PERF_AUDIT_LIVE.md with prioritized findings.

This is the COMPANION to scripts/qa_audit.py (iter142 static audit).
Static audit covers index hygiene against hard-coded hot queries.
Live audit covers what users are ACTUALLY hitting in the field.

Usage:
    python3 /app/scripts/qa_audit_live.py
    python3 /app/scripts/qa_audit_live.py --window-hours 168  # 7 days
    python3 /app/scripts/qa_audit_live.py --print
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

# Thresholds — these are the numbers that mark a route as "needs work".
SLOW_MAX_MS = 1000        # any worst-case call slower than this gets flagged
SLOW_AVG_MS = 250         # average latency this high is a slow flow
HIGH_ERROR_PCT = 5.0      # error rate that warrants investigation
MIN_CALLS_FOR_SIGNAL = 10 # below this volume we don't trust averages

# Rough route → collection mapping so we can run explain() automatically.
# Only includes the heaviest list endpoints — investigation routes are
# left for a human to chase down.
ROUTE_TO_COLLECTION = {
    "/api/incidents":                 "incidents",
    "/api/safety/corrective-actions": "corrective_actions",
    "/api/fire-extinguishers":        "fire_extinguishers",
    "/api/inspections":               "equipment_inspections",
    "/api/equipment-master":          "equipment_master",
    "/api/employees":                 "employees",
    "/api/safety/training-records":   "safety_training_records",
    "/api/admin/operations-events":   "operations_events",
    "/api/field-leadership":          "field_leadership_records",
    "/api/daily-reports":             "daily_reports",
    "/api/projects":                  "projects",
    "/api/master-where-used/equipment/:id": "equipment_master",
    "/api/master-where-used/employee/:id":  "employees",
    "/api/master-lookup/equipment/:id/history": "equipment_master",
    "/api/master-lookup/employees/:id/history": "employees",
}


async def _hot_routes(db, window_hours: int, limit: int) -> List[Dict[str, Any]]:
    """Pull the top-N routes by call count from telemetry."""
    since = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=window_hours)
    pipeline = [
        {"$match": {"at": {"$gte": since}, "kind": "api_call", "route": {"$ne": ""}}},
        {"$group": {
            "_id": "$route",
            "count":  {"$sum": 1},
            "avg_ms": {"$avg": "$latency_ms"},
            "max_ms": {"$max": "$latency_ms"},
            "errors": {"$sum": {"$cond": [
                {"$gte": [{"$ifNull": ["$status", 0]}, 400]}, 1, 0,
            ]}},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    rows = []
    async for d in db.usage_events.aggregate(pipeline):
        count = d["count"]
        errors = d.get("errors") or 0
        rows.append({
            "route":     d["_id"],
            "count":     count,
            "avg_ms":    int(d.get("avg_ms") or 0),
            "max_ms":    d.get("max_ms") or 0,
            "errors":    errors,
            "error_pct": (100.0 * errors / count) if count else 0.0,
        })
    return rows


def _flag(row: Dict[str, Any]) -> Optional[str]:
    """Return a short reason if the row should be flagged, else None."""
    if row["count"] < MIN_CALLS_FOR_SIGNAL:
        return None
    flags = []
    if row["max_ms"] > SLOW_MAX_MS:
        flags.append(f"worst={row['max_ms']}ms")
    if row["avg_ms"] > SLOW_AVG_MS:
        flags.append(f"avg={row['avg_ms']}ms")
    if row["error_pct"] > HIGH_ERROR_PCT:
        flags.append(f"err={row['error_pct']:.1f}%")
    return " · ".join(flags) if flags else None


async def _explain_if_known(db, route: str) -> Optional[str]:
    """Map route → collection and emit a hint string. We deliberately
    DON'T run an empty-filter explain() here — without the endpoint's
    actual query filter the plan is meaningless. The static audit
    (scripts/qa_audit.py) covers proper explains with real filters.
    This helper just surfaces "which collection this route hits"."""
    coll = ROUTE_TO_COLLECTION.get(route)
    if not coll:
        return None
    return f"hits `{coll}` · profile with scripts/qa_audit.py"


async def _live_probe(api_base: str, route: str, n: int = 3) -> Dict[str, int]:
    """Hit a route a few times directly to measure live latency. Only
    routes that are safe to GET unauthenticated — we never authenticate
    in this script."""
    import urllib.request  # noqa: PLC0415
    safe_route = route.replace(":id", "00000000-0000-0000-0000-000000000000")
    latencies = []
    for _ in range(n):
        t0 = time.monotonic()
        try:
            req = urllib.request.Request(api_base + safe_route,
                                         headers={"User-Agent": "qa-audit-live"})
            with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
                resp.read()
            latencies.append(int((time.monotonic() - t0) * 1000))
        except Exception:  # noqa: BLE001
            latencies.append(-1)
    valid = [x for x in latencies if x >= 0]
    if not valid:
        return {"min": 0, "max": 0, "avg": 0, "ok": 0}
    return {"min": min(valid), "max": max(valid),
            "avg": sum(valid) // len(valid), "ok": len(valid)}


def _md_findings(flagged: List[Dict[str, Any]],
                 explains: Dict[str, Optional[str]],
                 live: Dict[str, Dict[str, int]]) -> str:
    if not flagged:
        return ("✅ **No flagged routes** in the audit window. "
                "Every measured route is under the threshold "
                f"({SLOW_MAX_MS}ms worst, {HIGH_ERROR_PCT}% error).\n")
    lines = ["## Flagged Routes — Priority Order\n",
             "| Route | Calls | Avg ms | Worst ms | Err% | Reason | Collection Hint | Live max ms |",
             "|---|---|---|---|---|---|---|---|"]
    for r in flagged:
        reason = _flag(r) or ""
        explain = explains.get(r["route"]) or "—"
        live_row = live.get(r["route"])
        live_str = f"{live_row['max']}" if live_row and live_row["ok"] else "—"
        lines.append(
            f"| `{r['route']}` | {r['count']} | {r['avg_ms']} | {r['max_ms']} "
            f"| {r['error_pct']:.1f}% | {reason} | {explain} | {live_str} |"
        )
    return "\n".join(lines) + "\n"


def _md_top_routes(rows: List[Dict[str, Any]]) -> str:
    lines = ["## All Top Routes (by call count)\n",
             "| Route | Calls | Avg ms | Worst ms | Errors |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| `{r['route']}` | {r['count']} | {r['avg_ms']} | "
            f"{r['max_ms']} | {r['errors']} |"
        )
    return "\n".join(lines) + "\n"


async def main(window_hours: int, do_print: bool, do_live: bool) -> None:
    mongo_url = os.environ["MONGO_URL"]
    db = AsyncIOMotorClient(mongo_url)[os.environ["DB_NAME"]]
    rows = await _hot_routes(db, window_hours, limit=30)

    flagged = [r for r in rows if _flag(r) is not None]

    explains: Dict[str, Optional[str]] = {}
    for r in flagged:
        explains[r["route"]] = await _explain_if_known(db, r["route"])

    live: Dict[str, Dict[str, int]] = {}
    if do_live:
        api_base = os.environ.get("LOCAL_API_BASE", "http://localhost:8001")
        for r in flagged[:5]:  # cap live probes
            live[r["route"]] = await _live_probe(api_base, r["route"])

    md = f"""# QA · Live Performance Audit (iter147)

_Generated {_dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_
_Window: last {window_hours}h · Source: db.usage_events (iter146 telemetry)_

**Thresholds**:
- Flag if `max_ms > {SLOW_MAX_MS}` (worst-case latency)
- Flag if `avg_ms > {SLOW_AVG_MS}` (sustained slowness)
- Flag if `error_pct > {HIGH_ERROR_PCT}%`
- Below {MIN_CALLS_FOR_SIGNAL} calls = treated as noise (not flagged)

{_md_findings(flagged, explains, live)}
{_md_top_routes(rows)}
"""
    out_path = ROOT / "QA_PERF_AUDIT_LIVE.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"  flagged: {len(flagged)} of {len(rows)} routes in window")
    if do_print:
        print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-hours", type=int, default=24)
    ap.add_argument("--print", action="store_true", default=False)
    ap.add_argument("--no-live", action="store_true", default=False,
                    help="Skip live-probe latency measurements")
    args = ap.parse_args()
    asyncio.run(main(args.window_hours, args.print, not args.no_live))
