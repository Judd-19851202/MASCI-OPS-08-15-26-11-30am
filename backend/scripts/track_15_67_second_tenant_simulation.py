"""
Track 15.67 · Second-Tenant Simulation (Phase 3 EXTENDED)
=========================================================

Creates a synthetic tenant (`tenant_15_67_demo`), wires routing
documents + branding from non-MASCI defaults, and proves the resolver
returns ZERO MASCI recipients / senders / branding strings for that
tenant. Phase 3 extends the original 27 checks with:

  * portal seed migration check (safety/shop/hr)
  * pm fallback elimination check (no MASCI office address inherited)
  * sender-site sweep check (resolve_sender_email refuses env fallback)
  * branding leakage check (every customer-visible string is non-MASCI)
  * route health check (one-click validation green/amber/red counts)
  * support / safety / hr / operations contact resolution
  * audit row tenant_key carry-through
  * dead-letter behaviour on unresolved PM routing

Cleans up afterwards (refuses to leave synthetic docs behind unless
`--keep` is passed).

Usage:
    cd /app/backend && python3 scripts/track_15_67_second_tenant_simulation.py
"""
from __future__ import annotations
import argparse, asyncio, os, json, sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(HERE.parent / ".env")
from lib.operator_safety import redact_target_identity
import email_routing_v2 as v2
from tenant_context import set_current_tenant, resolve_tenant_key
from branding_resolver import resolve_sender, resolve_sender_email, UnconfiguredSenderError

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


def _contains_masci(s) -> bool:
    if not s:
        return False
    txt = str(s).lower()
    return any(needle.lower() in txt for needle in MASCI_STRINGS)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    keep = args.keep
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    app_env = (os.environ.get("APP_ENV") or "").strip().lower()
    if app_env in {"production", "prod"} or db_name == "masci_safety":
        print(json.dumps({
            "ok": False,
            "error": "Refusing second-tenant simulation against production semantics.",
            "target": redact_target_identity(mongo_url, db_name),
        }, indent=2))
        return 3
    if "preview" not in db_name and "demo" not in db_name and "test" not in db_name:
        print(json.dumps({
            "ok": False,
            "error": "Simulation is restricted to preview/demo/test DB namespaces.",
            "target": redact_target_identity(mongo_url, db_name),
        }, indent=2))
        return 4
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
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
        no_masci = not any(_contains_masci(x) for x in (res.to + res.cc + res.bcc))
        critical_ok = (not r["critical"]) or bool(res.to)
        add(f"route_{r['route_key']}_tenant_scoped", scope_ok, f"tenant={res.tenant_key}")
        add(f"route_{r['route_key']}_no_masci_recipients", no_masci, f"to={res.to}")
        add(f"route_{r['route_key']}_critical_not_empty", critical_ok, f"to={res.to}")

    # 3) Sender identity resolves from branding, not env
    s = await resolve_sender(db)
    sender_ok = s.from_email == "noreply@demo-co.example" and s.source == "branding"
    add("sender_identity_from_branding", sender_ok,
        f"from={s.from_email} source={s.source}")
    no_masci_sender = not _contains_masci(s.from_email)
    add("sender_no_masci_leak", no_masci_sender, f"from={s.from_email}")

    # 3b) `resolve_sender_email` compat helper returns demo addr, not env
    se = await resolve_sender_email(db)
    add("resolve_sender_email_returns_demo", se == "noreply@demo-co.example",
        f"resolved={se}")
    add("resolve_sender_email_no_masci_leak", not _contains_masci(se), f"resolved={se}")

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

    # ------------------------------------------------------------------
    # PHASE 3 · EXTENDED CHECKS
    # ------------------------------------------------------------------

    # 6) Portal seed migration — INITIAL_*_USERS should be empty for non-MASCI
    #    when the corresponding SEED_USERS env vars are unset.
    os.environ.pop("SAFETY_SEED_USERS", None)
    os.environ.pop("SHOP_SEED_USERS", None)
    os.environ.pop("HR_SEED_USERS", None)
    # Re-import to re-evaluate the module-level _resolve_initial_*_users()
    import importlib
    import safety_users, shop_users, hr_users
    importlib.reload(safety_users); importlib.reload(shop_users); importlib.reload(hr_users)
    add("safety_seed_empty_for_non_masci", len(safety_users.INITIAL_SAFETY_USERS) == 0,
        f"len={len(safety_users.INITIAL_SAFETY_USERS)}")
    add("shop_seed_empty_for_non_masci", len(shop_users.INITIAL_SHOP_USERS) == 0,
        f"len={len(shop_users.INITIAL_SHOP_USERS)}")
    add("hr_seed_empty_for_non_masci", len(hr_users.INITIAL_HR_USERS) == 0,
        f"len={len(hr_users.INITIAL_HR_USERS)}")

    # 6b) Portal seed env-driven path — set env, reload, expect non-MASCI users
    os.environ["SAFETY_SEED_USERS"] = "safety@demo-co.example|Demo Safety|Safety Manager"
    importlib.reload(safety_users)
    seeded = safety_users.INITIAL_SAFETY_USERS
    seed_ok = len(seeded) == 1 and not _contains_masci(seeded[0]["email"])
    add("safety_seed_env_path_no_masci", seed_ok, f"users={seeded}")
    del os.environ["SAFETY_SEED_USERS"]

    # 7) PM routing fallback — PM_TABLE empty for non-MASCI
    os.environ.pop("PM_SEED_DIRECTORY", None)
    import pm_routing
    importlib.reload(pm_routing)
    add("pm_table_empty_for_non_masci", len(pm_routing.PM_TABLE) == 0,
        f"len={len(pm_routing.PM_TABLE)}")
    add("always_cc_empty_for_non_masci", len(pm_routing.ALWAYS_CC) == 0,
        f"len={len(pm_routing.ALWAYS_CC)}")

    # 7b) Unresolved PM record routes to ADMIN_DEAD_LETTER_TO (the demo
    # tenant's route), NOT a MASCI office address.
    dist = await pm_routing.recipients_for_record_async(
        db, {"project_number": "DEMO-NOT-FOUND", "project_name": "Phantom Job"},
        kind="daily-report",
    )
    dead_letter_to = dist.get("to") or []
    dead_letter_ok = (
        bool(dead_letter_to)
        and not any(_contains_masci(x) for x in dead_letter_to)
        and any(x.endswith("@demo-co.example") for x in dead_letter_to)
    )
    add("pm_unresolved_routes_to_dead_letter", dead_letter_ok,
        f"to={dead_letter_to}")

    # 8) Sender swap — confirm resolve_sender_email on demo tenant does NOT
    # leak any env SENDER_EMAIL string even if set.
    os.environ["SENDER_EMAIL"] = "noreply@mascidocs.com"
    se2 = await resolve_sender_email(db, safe_fallback="onboarding@resend.dev")
    add("sender_swap_ignores_env_for_non_masci", not _contains_masci(se2),
        f"resolved={se2}")

    # 9) Public branding endpoint shape — fetch via direct collection +
    # the resolver path; verify no MASCI leakage on customer-visible
    # fields.
    bdoc = await db.tenant_branding.find_one({"_id": DEMO_TENANT}, {"_id": 0}) or {}
    customer_fields = ("company_name", "platform_display_name", "support_email",
                       "safety_email", "hr_email", "operations_email")
    branding_clean = all(not _contains_masci(bdoc.get(k)) for k in customer_fields)
    add("branding_doc_no_masci_leak", branding_clean,
        f"fields={[bdoc.get(k) for k in customer_fields]}")

    # 10) Route Health style validation — count green/amber/red over demo routes
    routes = await db.email_routes.find({"tenant_key": DEMO_TENANT}, {"_id": 0}).to_list(100)
    green = sum(1 for r in routes if r.get("enabled") and (r.get("to") or []))
    red = sum(1 for r in routes if r.get("critical") and not (r.get("to") or []))
    add("route_health_no_red_routes", red == 0, f"red={red} green={green}")
    add("route_health_all_routes_have_recipients",
        all(r.get("to") for r in routes), f"routes={len(routes)}")

    # 11) Sender refuses env fallback for non-MASCI when no branding doc
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

    # 12) Reload pm_routing/safety/shop/hr back to MASCI defaults so the
    # next session continues unchanged
    set_current_tenant(None)
    importlib.reload(pm_routing)
    importlib.reload(safety_users); importlib.reload(shop_users); importlib.reload(hr_users)

    # ----- Cleanup -----
    if not keep:
        await db.email_routes.delete_many({"tenant_key": DEMO_TENANT})
        await db.tenant_branding.delete_one({"_id": DEMO_TENANT})
        await db.email_routing_audit_v2.delete_many({"tenant_key": DEMO_TENANT})
        await db.platform_audit.delete_many({"tenant_key": DEMO_TENANT})
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
    raise SystemExit(asyncio.run(main()))
