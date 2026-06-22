"""
Track 15.65 — Parity verification harness
==========================================

For every seeded route, resolves recipients (a) with EMAIL_ROUTING_V2=false
(legacy env path) and (b) with EMAIL_ROUTING_V2=true (DB-first path).
Asserts the two results match (modulo intentional drift documented in the
report). NEVER sends a real email — every send path is dry-run only.

Usage:
    cd /app/backend && python3 scripts/track_15_65_parity_verify.py
Output:
    /app/test_reports/track_15_65_parity.json
    /app/memory/track_15_65_data/parity_summary.md
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(HERE.parent / ".env")

import email_routing_v2 as v2  # noqa: E402

TENANT = "masci"

ROUTE_LEGACY_PROVIDERS = {
    "SAFETY_FORMS_TO": lambda: (os.environ.get("SAFETY_FORMS_EMAIL_TO") or "safety@mascigc.com,jaymn.judd@mascigc.com").split(","),
    "FIELD_LEADERSHIP_ALWAYS_TO": lambda: [
        os.environ.get("LEADERSHIP_ALWAYS_TO_1") or "jaymn.judd@mascigc.com",
        os.environ.get("LEADERSHIP_ALWAYS_TO_2") or "safety@mascigc.com",
    ],
    "PRE_OP_FAIL_FALLBACK": lambda: os.environ.get("SHOP_MANAGER_EMAIL") or "shopmanager@mascigc.com",
    "INCIDENT_SEVERE_CC": lambda: [e.strip() for e in (os.environ.get("SEVERE_INCIDENT_CC") or "").split(",") if e.strip()],
    "BACKUP_ALERTS": lambda: [e.strip() for e in (os.environ.get("BACKUP_EMAIL_TO") or "").split(",") if e.strip()],
    "HEALTH_ALERTS": lambda: [e.strip() for e in (os.environ.get("HEALTH_ALERT_RECIPIENTS") or os.environ.get("BACKUP_EMAIL_TO") or "safety@mascigc.com").split(",") if e.strip()],
    "OUTAGE_ALERTS": lambda: [os.environ.get("OUTAGE_ALERT_TO") or "jaymn.judd@mascigc.com"],
    "SAFETY_DIGEST_TO": lambda: [os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com"],
    "OPERATOR_DIGEST_RECIPIENTS": lambda: [e.strip() for e in (os.environ.get("OPERATOR_DIGEST_RECIPIENTS") or os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com").split(",") if e.strip()],
    "PAYROLL_VARIANCE_TO": lambda: [e.strip() for e in (os.environ.get("PAYROLL_VARIANCE_EMAIL_TO") or os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com").split(",") if e.strip()],
    "ADMIN_DEAD_LETTER_TO": lambda: [(os.environ.get("ADMIN_DEAD_LETTER_EMAIL") or "safety@mascigc.com")],
    "DISPATCH_ROLE_TO": lambda: [(os.environ.get("DISPATCH_EMAIL") or os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com")],
    "SUPER_ADMIN_TO": lambda: [os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com"],
    "COMPLIANCE_ALWAYS_CC": lambda: ["jaymn.judd@mascigc.com", "safety@mascigc.com"],
    "TRENCH_SAFETY_PULSE_SAFETY": lambda: [os.environ.get("SAFETY_DIGEST_TO_EMAIL") or os.environ.get("SUPER_ADMIN_EMAIL") or "safety@mascigc.com"],
    "TRENCH_SAFETY_PULSE_SHOP": lambda: [os.environ.get("SHOP_MANAGER_EMAIL") or "shopmanager@mascigc.com"],
}


async def main() -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    cursor = db.email_routes.find({"tenant_key": TENANT}, {"_id": 0}).sort("route_key", 1)
    routes = await cursor.to_list(100)

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tenant": TENANT,
        "route_count": len(routes),
        "results": [],
        "summary": {"match": 0, "mismatch": 0, "skipped_no_legacy": 0, "critical_empty": 0},
    }

    for doc in routes:
        rk = doc["route_key"]
        provider = ROUTE_LEGACY_PROVIDERS.get(rk)

        # Flag OFF — must equal legacy provider output exactly
        os.environ["EMAIL_ROUTING_V2"] = "false"
        v2.invalidate_cache()
        if provider is None:
            off_res = await v2.resolve(db, rk, legacy_provider=None)
            legacy_set: set = set()
            skipped = True
        else:
            off_res = await v2.resolve(db, rk, legacy_provider=provider)
            legacy_list = provider()
            if isinstance(legacy_list, str):
                legacy_list = [legacy_list]
            legacy_set = {e.strip().lower() for e in legacy_list if e and e.strip()}
            skipped = False

        # Flag ON — must equal DB doc
        os.environ["EMAIL_ROUTING_V2"] = "true"
        v2.invalidate_cache()
        on_res = await v2.resolve(db, rk, legacy_provider=provider)

        off_set = {e.lower() for e in (off_res.to + off_res.cc + off_res.bcc)}
        on_set = {e.lower() for e in (on_res.to + on_res.cc + on_res.bcc)}

        # Critical-route empty guard (matches the resolver's UnconfiguredCriticalRouteError)
        critical_empty = bool(doc.get("critical")) and not on_set
        if critical_empty:
            report["summary"]["critical_empty"] += 1

        # When provider is missing, V2 against an enabled route is allowed
        # to introduce new recipients (the DB doc is the source of truth).
        if skipped:
            match = True
            report["summary"]["skipped_no_legacy"] += 1
        else:
            match = (off_set == legacy_set) and (on_set == legacy_set or on_set == set(e.lower() for e in doc.get("to", []) + doc.get("cc", []) + doc.get("bcc", [])))

        result_row = {
            "route_key": rk,
            "critical": bool(doc.get("critical")),
            "enabled": bool(doc.get("enabled", True)),
            "flag_off_to": off_res.to, "flag_off_cc": off_res.cc, "flag_off_bcc": off_res.bcc, "flag_off_source": off_res.source,
            "flag_on_to":  on_res.to,  "flag_on_cc":  on_res.cc,  "flag_on_bcc":  on_res.bcc,  "flag_on_source":  on_res.source,
            "legacy_provided": not skipped,
            "match": match,
        }
        if not match:
            result_row["diff"] = {
                "off_minus_legacy": sorted(off_set - legacy_set),
                "legacy_minus_off": sorted(legacy_set - off_set),
                "on_minus_db":      sorted(on_set - {e.lower() for e in doc.get("to", []) + doc.get("cc", []) + doc.get("bcc", [])}),
            }
            report["summary"]["mismatch"] += 1
        else:
            report["summary"]["match"] += 1
        report["results"].append(result_row)

    # Reset flag so module state is clean
    os.environ["EMAIL_ROUTING_V2"] = "false"
    v2.invalidate_cache()

    out_json = Path("/app/test_reports/track_15_65_parity.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2))

    summary_md = ["# Track 15.65 — Parity Verification Summary",
                  "",
                  f"Run: {report['ts']}",
                  f"Tenant: {report['tenant']}",
                  f"Routes: {report['route_count']}",
                  f"Match: {report['summary']['match']}",
                  f"Mismatch: {report['summary']['mismatch']}",
                  f"Skipped (no legacy provider): {report['summary']['skipped_no_legacy']}",
                  f"Critical routes resolving empty under V2: {report['summary']['critical_empty']}",
                  "",
                  "| Route | crit | match | flag-off src | flag-on src | flag-off TO count | flag-on TO count |",
                  "|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        summary_md.append(f"| `{r['route_key']}` | {r['critical']} | {'✅' if r['match'] else '❌'} | "
                          f"{r['flag_off_source']} | {r['flag_on_source']} | "
                          f"{len(r['flag_off_to'])} | {len(r['flag_on_to'])} |")
    Path("/app/memory/track_15_65_data/parity_summary.md").write_text("\n".join(summary_md))

    print(json.dumps(report["summary"], indent=2))
    sys.exit(0 if report["summary"]["mismatch"] == 0 and report["summary"]["critical_empty"] == 0 else 2)


if __name__ == "__main__":
    asyncio.run(main())
