#!/usr/bin/env python3
"""
qa_audit.py — Iter142 (Phase-1 Iter D). One-shot QA sweeper used to
generate the perf + TTL audit reports under /app/QA_PERF_AUDIT.md.

Usage:
    python3 /app/scripts/qa_audit.py             # writes the markdown
    python3 /app/scripts/qa_audit.py --print     # also dumps to stdout

What it inspects:
  • Every hot list endpoint pattern (top 10) — runs `explain()` on a
    representative query and surfaces collection-scan offenders.
  • TTL coverage — flags telemetry collections without TTL indexes.
  • Index footprint per collection — counts indexes + total size.

Read-only — does NOT create / modify any indexes. The report names
the exact `create_index` calls to apply. The matching MIGRATION at
the bottom of the report is idempotent (we already create_index in
startup hooks, but the script gives an audit-trail copy).
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "backend" / ".env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

# ── Collections worth keeping a TTL index on (telemetry + ephemeral) ──
TTL_RECOMMENDED = {
    "r2_degraded_events":   60 * 60 * 24 * 30,   # 30 days
    "digest_runs":          60 * 60 * 24 * 90,   # 90 days
    "system_health_events": 60 * 60 * 24 * 30,
    "audit_events":         60 * 60 * 24 * 365,  # 1 year (compliance)
    "alert_events":         60 * 60 * 24 * 90,
    "admin_audit":          60 * 60 * 24 * 365,
    "login_attempts":       60 * 60 * 24 * 30,
    "integration_error_logs": 60 * 60 * 24 * 90,
    "brute_force_blocks":   60 * 60 * 24 * 7,
}

# ── Top-10 hot list endpoints. Each tuple: (collection, query, sort,
# limit, description). Used to detect collection scans via explain(). ──
HOT_QUERIES: List[Dict[str, Any]] = [
    {"coll": "incidents",              "filter": {"deleted_at": None},       "sort": [("created_at", -1)], "limit": 50, "label": "GET /api/incidents"},
    {"coll": "corrective_actions",     "filter": {"status": "Open"},          "sort": [("due_date", 1)],    "limit": 50, "label": "GET /api/safety/corrective-actions?status=Open"},
    {"coll": "fire_extinguishers",     "filter": {"next_due_date": {"$exists": True}}, "sort": [("next_due_date", 1)], "limit": 100, "label": "Fire ext due-soon dashboard"},
    {"coll": "equipment_inspections",  "filter": {"inspection_date": {"$exists": True}}, "sort": [("inspection_date", -1)], "limit": 50, "label": "Shop pre-op trends list"},
    {"coll": "equipment_master",       "filter": {"deleted_at": None},        "sort": [("unit_number", 1)], "limit": 200, "label": "Equipment master list"},
    {"coll": "employees",              "filter": {"deleted_at": None},        "sort": [("name", 1)],        "limit": 500, "label": "Employees roster"},
    {"coll": "safety_training_records","filter": {"employee_master_id": {"$exists": True}}, "sort": [("expiration_date", 1)], "limit": 100, "label": "Trainings expiring soon"},
    {"coll": "operations_events",      "filter": {"status": "active"},        "sort": [("created_at", -1)], "limit": 50, "label": "Operations events feed"},
    {"coll": "field_leadership_records","filter": {"deleted_at": None},        "sort": [("occurred_at", -1)], "limit": 50, "label": "HR FL records list"},
    {"coll": "daily_reports",          "filter": {"report_date": {"$exists": True}}, "sort": [("report_date", -1)], "limit": 50, "label": "PM daily reports"},
]

INDEX_RECOMMENDATIONS = {
    # collection → list[(name, key_spec)]
    "incidents":              [("incident_date_desc", [("incident_date", -1)])],
    "corrective_actions":     [("status_due", [("status", 1), ("due_date", 1)])],
    "fire_extinguishers":     [("next_due", [("next_due_date", 1)])],
    "equipment_inspections":  [("inspection_date_desc", [("inspection_date", -1)])],
    "safety_training_records":[("exp_asc", [("expiration_date", 1)])],
    "operations_events":      [("status_created", [("status", 1), ("created_at", -1)]),
                               ("asset_lookup",  [("asset_id", 1)]),
                               ("employee_lookup", [("employee_id", 1)])],
    "field_leadership_records":[("occurred_desc", [("occurred_at", -1)]),
                                ("emp_name", [("employee_name", 1)])],
    "daily_reports":          [("report_date_desc", [("report_date", -1)])],
}


async def _ttl_audit(db) -> Dict[str, Any]:
    rows = []
    for coll, ttl_secs in TTL_RECOMMENDED.items():
        try:
            idxs = await db[coll].index_information()
            has_ttl = any("expireAfterSeconds" in v for v in idxs.values())
            current_ttl = next(
                (v.get("expireAfterSeconds") for v in idxs.values()
                 if "expireAfterSeconds" in v), None,
            )
            rows.append({
                "collection": coll,
                "recommended_ttl_days": ttl_secs // 86400,
                "current_ttl_days": (current_ttl // 86400) if current_ttl else None,
                "ok": has_ttl,
            })
        except Exception as e:  # noqa: BLE001
            rows.append({"collection": coll, "ok": False,
                         "current_ttl_days": None,
                         "recommended_ttl_days": ttl_secs // 86400,
                         "error": str(e)[:120]})
    return {"rows": rows}


async def _explain_audit(db) -> Dict[str, Any]:
    rows = []
    for q in HOT_QUERIES:
        try:
            cur = db[q["coll"]].find(q["filter"]).sort(q["sort"]).limit(q["limit"])
            plan = await cur.explain()
            winning = plan.get("queryPlanner", {}).get("winningPlan", {})

            def _walk(node, acc):
                if not isinstance(node, dict):
                    return
                stage = node.get("stage") or node.get("inputStage", {}).get("stage")
                if stage:
                    acc.append(stage)
                for k in ("inputStage", "inputStages", "stages"):
                    v = node.get(k)
                    if isinstance(v, list):
                        for sub in v:
                            _walk(sub, acc)
                    elif isinstance(v, dict):
                        _walk(v, acc)
            stages: List[str] = []
            _walk(winning, stages)
            uses_index = any(s in ("IXSCAN", "COUNT_SCAN", "DISTINCT_SCAN") for s in stages)
            uses_collscan = "COLLSCAN" in stages
            rows.append({
                "label": q["label"],
                "coll": q["coll"],
                "stages": " · ".join(stages) or "?",
                "uses_index": uses_index,
                "scan": uses_collscan,
            })
        except Exception as e:  # noqa: BLE001
            rows.append({"label": q["label"], "coll": q["coll"],
                         "stages": f"explain failed: {str(e)[:80]}",
                         "uses_index": False, "scan": False})
    return {"rows": rows}


async def _index_footprint(db) -> List[Dict[str, Any]]:
    out = []
    coll_names = await db.list_collection_names()
    for c in sorted(coll_names):
        try:
            idxs = await db[c].index_information()
            out.append({"collection": c, "index_count": len(idxs)})
        except Exception:  # noqa: BLE001
            pass
    return out


def _md_section_ttl(rows: List[Dict[str, Any]]) -> str:
    lines = ["## TTL Coverage Audit\n",
             "| Collection | Recommended | Current | OK |",
             "|---|---|---|---|"]
    for r in rows:
        ok = "✅" if r.get("ok") else "❌"
        cur = f"{r['current_ttl_days']}d" if r.get("current_ttl_days") else "—"
        rec = f"{r['recommended_ttl_days']}d"
        lines.append(f"| `{r['collection']}` | {rec} | {cur} | {ok} |")
    return "\n".join(lines) + "\n"


def _md_section_explain(rows: List[Dict[str, Any]]) -> str:
    lines = ["## Query Plan Audit (top 10 hot endpoints)\n",
             "| Endpoint | Coll | Plan | Index | COLLSCAN |",
             "|---|---|---|---|---|"]
    for r in rows:
        idx = "✅" if r["uses_index"] else "—"
        scan = "❌ SCAN" if r["scan"] else "—"
        lines.append(f"| {r['label']} | `{r['coll']}` | `{r['stages']}` | {idx} | {scan} |")
    return "\n".join(lines) + "\n"


def _md_section_indexes(rows: List[Dict[str, Any]]) -> str:
    lines = ["## Index Footprint\n",
             "| Collection | Index Count |",
             "|---|---|"]
    for r in rows:
        lines.append(f"| `{r['collection']}` | {r['index_count']} |")
    return "\n".join(lines) + "\n"


def _md_section_recommendations() -> str:
    lines = ["## Recommended Index Additions\n",
             "Apply via `create_index` in the matching startup hook. ",
             "All `create_index` calls are idempotent — safe to re-run.\n"]
    for coll, specs in INDEX_RECOMMENDATIONS.items():
        for name, key_spec in specs:
            spec_str = ", ".join([f"('{k}', {d})" for k, d in key_spec])
            lines.append(f"- **`{coll}`** index `{name}` — `await db.{coll}.create_index([{spec_str}])`")
    return "\n".join(lines) + "\n"


async def main(do_print: bool) -> None:
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    ttl = await _ttl_audit(db)
    expl = await _explain_audit(db)
    foot = await _index_footprint(db)

    md = f"""# QA · Perf + TTL Audit

_Generated {_dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_

Read-only sweep. Surfaces collection-scan offenders, missing TTL
indexes, and per-collection index footprint.

{_md_section_explain(expl["rows"])}
{_md_section_ttl(ttl["rows"])}
{_md_section_recommendations()}
{_md_section_indexes(foot)}
"""
    out_path = ROOT / "QA_PERF_AUDIT.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"wrote {out_path}")
    if do_print:
        print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", default=False)
    args = ap.parse_args()
    asyncio.run(main(args.print))
