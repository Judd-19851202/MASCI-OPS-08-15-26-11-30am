"""
Track 15.67 · Second-Tenant Simulation
=======================================

Creates a synthetic tenant (`tenant_15_67_demo`), wires routing
documents + branding from non-MASCI defaults, and proves the resolver
returns ZERO MASCI recipients / senders / branding strings for that
tenant. Cleans up afterwards (refuses to leave synthetic docs behind
unless `--keep` is passed).

Usage:
    cd /app/backend && python3 scripts/track_15_67_second_tenant_simulation.py
"""
from __future__ import annotations
import asyncio, os, json, sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(HERE.parent / ".env")
import email_routing_v2 as v2
from tenant_context import set_current_tenant, resolve_tenant_key
from branding_resolver import resolve_sender, UnconfiguredSenderError

DEMO_TENANT = "tenant_15_67_demo"

DEMO_BRANDING = {
    "_id": DEMO_TENANT,
    "tenant_key": DEMO_TENANT,
    "company_name": "Demo Construction LLC",
    "platform_display_name": "Demo Ops Platform",
    "sender_name": "Demo Ops Platform",
    "from_email": "noreply@demo-co.example",
    "reply_to": "ops@demo-co.example",
    "support_email": "help@demo-co.example",
    "safety_email": "safety@demo-co.example",
    "hr_email": "hr@demo-co.example",
    "operations_email": "ops@demo-co.example",
    "primary_color": "#0F766E",
    "logo_url": None,
    "source": "synthetic_simulation",
    "created_at": datetime.now(timezone.utc).isoformat(),
}

DEMO_ROUTES = [
    {"route_key": "SAFETY_FORMS_TO", "to": ["safety@demo-co.example"], "critical": False},
    {"route_key": "HEALTH_ALERTS", "to": ["ops@demo-co.example"], "critical": True},
    {"route_key": "OUTAGE_ALERTS", "to": ["ops@demo-co.example"], "critical": True},
    {"route_key": "BACKUP_ALERTS", "to": ["ops@demo-co.example"], "critical": True},
    {"route_key": "SUPER_ADMIN_TO", "to": ["admin@demo-co.example"], "critical": True},
    {"route_key": "COMPLIANCE_ALWAYS_CC", "to": ["compliance@demo-co.example"], "critical": False},
    {"route_key": "ADMIN_DEAD_LETTER_TO", "to": ["ops@demo-co.example"], "critical": False},
]

MASCI_STRINGS = ("mascigc.com", "mascidocs.com", "jaymn", "MASCI", "masci")


async def main():
    keep = "--keep" in sys.argv
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    report = {"tenant": DEMO_TENANT, "ts": datetime.now(timezone.utc).isoformat(),
              "checks": [], "summary": {"pass": 0, "fail": 0}}

    # ----- Seed -----
    await db.tenant_branding.replace_one({"_id": DEMO_TENANT}, DEMO_BRANDING, upsert=True)
    for r in DEMO_ROUTES:
        doc = {
            "_id": f"{DEMO_TENANT}::{r['route_key']}",
            "tenant_key": DEMO_TENANT, "route_key": r["route_key"],
            "display_name": r["route_key"].replace("_", " ").title(),
            "description": f"Synthetic test route for {DEMO_TENANT}",
            "category": "synthetic", "severity": "warn",
            "to": r["to"], "cc": [], "bcc": [],
            "enabled": True, "critical": r["critical"],
            "source": "synthetic_simulation",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.email_routes.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    def add(name, ok, detail=""):
        report["checks"].append({"check": name, "ok": ok, "detail": detail})
        report["summary"]["pass" if ok else "fail"] += 1

    # ----- Activate tenant context -----
    set_current_tenant(DEMO_TENANT)
    os.environ["EMAIL_ROUTING_V2"] = "true"
    v2.invalidate_cache()

    # 1) Tenant resolution
    add("tenant_resolution_returns_demo", resolve_tenant_key() == DEMO_TENANT,
        f"resolved={resolve_tenant_key()}")

    # 2) Routes are tenant-scoped (no MASCI inheritance)
    for r in DEMO_ROUTES:
        res = await v2.resolve(db, r["route_key"])
        scope_ok = res.tenant_key == DEMO_TENANT
        no_masci = not any(any(s in x for s in MASCI_STRINGS) for x in (res.to + res.cc + res.bcc))
        critical_ok = (not r["critical"]) or bool(res.to)
        add(f"route_{r['route_key']}_tenant_scoped", scope_ok, f"tenant={res.tenant_key}")
        add(f"route_{r['route_key']}_no_masci_recipients", no_masci, f"to={res.to}")
        add(f"route_{r['route_key']}_critical_not_empty", critical_ok, f"to={res.to}")

    # 3) Sender identity resolves from branding, not env
    s = await resolve_sender(db)
    sender_ok = s.from_email == "noreply@demo-co.example" and s.source == "branding"
    add("sender_identity_from_branding", sender_ok,
        f"from={s.from_email} source={s.source}")
    no_masci_sender = not any(x in s.from_email for x in MASCI_STRINGS)
    add("sender_no_masci_leak", no_masci_sender, f"from={s.from_email}")

    # 4) Audit rows carry tenant_key
    await v2.write_audit(db, route_key="SAFETY_FORMS_TO", tenant_key=DEMO_TENANT,
                         source="db", to_count=1, cc_count=0, bcc_count=0,
                         status="dry_run", calling_module="simulation", dry_run=True)
    cnt = await db.email_routing_audit_v2.count_documents({"tenant_key": DEMO_TENANT})
    add("audit_rows_carry_demo_tenant_key", cnt >= 1, f"count={cnt}")

    # 5) Unknown route does NOT silently fall back to MASCI
    res2 = await v2.resolve(db, "DOES_NOT_EXIST_FOR_DEMO", legacy_provider=lambda: [])
    add("unknown_route_does_not_leak_masci", not res2.to and res2.tenant_key == DEMO_TENANT,
        f"to={res2.to} tenant={res2.tenant_key}")

    # 6) Sender refuses env fallback for non-MASCI
    os.environ["SENDER_EMAIL"] = "noreply@mascidocs.com"
    # Branding doc exists so resolver uses it; remove branding to force fallback path
    await db.tenant_branding.delete_one({"_id": DEMO_TENANT})
    v2.invalidate_cache()
    try:
        s2 = await resolve_sender(db)
        add("non_masci_tenant_refuses_env_fallback", False,
            f"unexpectedly resolved to {s2.from_email}")
    except UnconfiguredSenderError as e:
        add("non_masci_tenant_refuses_env_fallback", True, str(e)[:120])
    # Restore branding for cleanup symmetry
    await db.tenant_branding.replace_one({"_id": DEMO_TENANT}, DEMO_BRANDING, upsert=True)

    # ----- Cleanup -----
    set_current_tenant(None)
    if not keep:
        await db.email_routes.delete_many({"tenant_key": DEMO_TENANT})
        await db.tenant_branding.delete_one({"_id": DEMO_TENANT})
        await db.email_routing_audit_v2.delete_many({"tenant_key": DEMO_TENANT})
        report["cleanup"] = "done"
    else:
        report["cleanup"] = "skipped (--keep)"

    # Reset env
    os.environ["EMAIL_ROUTING_V2"] = "false"
    v2.invalidate_cache()

    out_path = Path("/app/test_reports/track_15_67_second_tenant_simulation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["summary"], indent=2))
    sys.exit(0 if report["summary"]["fail"] == 0 else 2)


if __name__ == "__main__":
    asyncio.run(main())
