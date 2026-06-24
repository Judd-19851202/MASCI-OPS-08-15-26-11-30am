"""TRACK 15.73Q · Daily Report PM-Email Coverage Audit.

Read-only audit. Preview DB (`masci_safety_preview`) as proxy. Same query
shape can be re-run against production by the operator (operator owns
production DB access).

Outputs:
  /app/test_reports/track_15_73q_pm_email_audit.json
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

if "prod" in DB_NAME.lower() and "preview" not in DB_NAME.lower():
    print(f"REFUSING — DB_NAME={DB_NAME} looks like production")
    sys.exit(2)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def main() -> dict:
    db = MongoClient(MONGO_URL)[DB_NAME]

    # ---------- recent DR project counts (last 180 days) ----------
    dr_counts: Counter[str] = Counter()
    dr_latest: dict[str, str] = {}
    for d in db.daily_reports.find({}, {"_id": 0, "project_number": 1, "report_date": 1}):
        pn = (d.get("project_number") or "").strip()
        if not pn:
            continue
        dr_counts[pn] += 1
        rd = (d.get("report_date") or "").strip()
        if rd > dr_latest.get(pn, ""):
            dr_latest[pn] = rd

    # ---------- jobs_master active projects ----------
    jm_rows = list(
        db.jobs_master.find(
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"_id": 0, "project_number": 1, "project_name": 1,
             "project_manager": 1, "pm_email": 1, "co_pm_emails": 1,
             "active": 1},
        )
    )
    jm_by_pn = {(r.get("project_number") or "").strip(): r for r in jm_rows if r.get("project_number")}

    # ---------- categorize ----------
    rows = []
    counters = {
        "active_with_pm_email": 0,
        "active_missing_pm_email": 0,
        "active_with_pm_name_no_email": 0,
        "active_with_co_pm_email_only": 0,
        "active_total_no_pm_no_copm": 0,
        "active_malformed_pm_email": 0,
        "dr_projects_with_no_jobs_master_row": 0,
    }

    for pn, row in sorted(jm_by_pn.items()):
        pm_email = (row.get("pm_email") or "").strip()
        pm_name = (row.get("project_manager") or "").strip()
        co_emails = [e for e in (row.get("co_pm_emails") or []) if e and isinstance(e, str)]
        recent_drs = dr_counts.get(pn, 0)
        last_dr = dr_latest.get(pn, "")
        status_flags: list[str] = []

        if pm_email and EMAIL_RE.match(pm_email):
            counters["active_with_pm_email"] += 1
            status_flags.append("pm_email_ok")
        elif pm_email:
            counters["active_malformed_pm_email"] += 1
            status_flags.append(f"pm_email_malformed:{pm_email!r}")
        else:
            counters["active_missing_pm_email"] += 1
            status_flags.append("pm_email_blank")
            if pm_name:
                counters["active_with_pm_name_no_email"] += 1
                status_flags.append(f"pm_name_only:{pm_name!r}")
            if co_emails:
                counters["active_with_co_pm_email_only"] += 1
                status_flags.append(f"co_pm_only:{co_emails}")
            else:
                counters["active_total_no_pm_no_copm"] += 1
                status_flags.append("no_pm_no_copm")

        rows.append({
            "project_number": pn,
            "project_name": row.get("project_name"),
            "pm_name": pm_name,
            "pm_email": pm_email,
            "co_pm_emails": co_emails,
            "active": row.get("active"),
            "recent_dr_count": recent_drs,
            "last_dr_date": last_dr,
            "status": status_flags,
        })

    # DR projects with NO jobs_master row at all
    dr_orphan_projects = []
    for pn, n in dr_counts.most_common():
        if pn in jm_by_pn:
            continue
        if any(pn.startswith(p) for p in ("ITER", "iter", "0000-TEST", "W1A-")):
            continue
        counters["dr_projects_with_no_jobs_master_row"] += 1
        dr_orphan_projects.append({
            "project_number": pn,
            "recent_dr_count": n,
            "last_dr_date": dr_latest.get(pn, ""),
        })

    # Sort rows by impact (most recent DRs first)
    rows.sort(key=lambda r: (-r["recent_dr_count"], r["project_number"]))
    missing = [r for r in rows if "pm_email_blank" in r["status"] or any("malformed" in s for s in r["status"])]
    return {
        "db_name": DB_NAME,
        "jobs_master_active_total": len(jm_by_pn),
        "daily_reports_distinct_projects_180d": len(dr_counts),
        "counters": counters,
        "active_projects": rows,
        "missing_pm_email_active_projects": missing,
        "dr_orphan_projects_no_jobs_master_row": dr_orphan_projects[:50],
    }


if __name__ == "__main__":
    out = main()
    out_path = Path("/app/test_reports/track_15_73q_pm_email_audit.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, default=str, indent=2))
    c = out["counters"]
    print(f"DB: {out['db_name']}")
    print(f"jobs_master active total: {out['jobs_master_active_total']}")
    print(f"daily_reports distinct projects (180d): {out['daily_reports_distinct_projects_180d']}")
    print()
    print("Counters:")
    for k, v in c.items():
        print(f"  {k}: {v}")
    print()
    print("MISSING PM EMAIL — active projects sorted by DR impact:")
    for r in out["missing_pm_email_active_projects"][:15]:
        print(f"  {r['project_number']:18s}  DRs={r['recent_dr_count']:3d}  last={r['last_dr_date']}  pm_name={r['pm_name']!r:20s}  co_pm={r['co_pm_emails']}")
    print()
    print(f"DR projects WITHOUT jobs_master row (non-synthetic): {len(out['dr_orphan_projects_no_jobs_master_row'])}")
    for r in out["dr_orphan_projects_no_jobs_master_row"][:10]:
        print(f"  {r['project_number']:18s}  DRs={r['recent_dr_count']:3d}  last={r['last_dr_date']}")
    print(f"\nFull JSON: {out_path}")
