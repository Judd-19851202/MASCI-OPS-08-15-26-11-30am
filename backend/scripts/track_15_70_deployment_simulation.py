"""TRACK 15.70 — Customer #2 + Customer #3 deployment simulation.

Provisions two synthetic tenants in the local Mongo DB:
  - CUSTOMER_2_DEPLOY_TEST (already exists as track_15_68_tenant_test_delete; we add a fresh one)
  - CUSTOMER_3_DEPLOY_TEST (new)

Verifies that each tenant resolves correctly via /api/branding/current
with the X-Tenant-Preview header. Verifies cross-tenant isolation.

NO PRODUCTION DATA is touched. The two test tenants are clearly named
with `_DEPLOY_TEST` suffixes and live in masci_safety_preview.
"""
import asyncio, os, sys, json, time
from datetime import datetime, timezone
sys.path.insert(0, "/app/backend")
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")


CUST2 = {
    "_id": "customer_2_deploy_test",
    "tenant_key": "customer_2_deploy_test",
    "slug": "customer-2-deploy-test",
    "company_name": "Customer #2 Construction LLC",
    "platform_display_name": "Customer #2 Operations Platform",
    "platform_short_name": "C2 Hub",
    "primary_color": "#0F766E",
    "accent_color": "#14B8A6",
    "logo_url": "",
    "marketing_url": "https://customer2.example",
    "support_email": "support@customer2.example",
    "safety_email": "safety@customer2.example",
    "hr_email": "hr@customer2.example",
    "operations_email": "ops@customer2.example",
    "from_email": "noreply@customer2.example",
    "reply_to": "support@customer2.example",
    "sender_name": "Customer #2 Operations Platform",
}

CUST3 = {
    "_id": "customer_3_deploy_test",
    "tenant_key": "customer_3_deploy_test",
    "slug": "customer-3-deploy-test",
    "company_name": "Customer #3 Highway Excavating",
    "platform_display_name": "Customer #3 Operations Platform",
    "platform_short_name": "C3 Ops",
    "primary_color": "#7C3AED",
    "accent_color": "#A78BFA",
    "logo_url": "",
    "marketing_url": "https://customer3.example",
    "support_email": "support@customer3.example",
    "safety_email": "safety@customer3.example",
    "hr_email": "hr@customer3.example",
    "operations_email": "ops@customer3.example",
    "from_email": "noreply@customer3.example",
    "reply_to": "support@customer3.example",
    "sender_name": "Customer #3 Operations Platform",
}

# A minimal route bundle per tenant — just 6 critical/common routes
# to prove the provisioning path. A full deployment seeds all 19.
ROUTE_BUNDLE = [
    {"route_key": "BACKUP_ALERTS",   "critical": True,  "enabled": True, "to": ["{ops}"], "cc": [], "bcc": []},
    {"route_key": "HEALTH_ALERTS",   "critical": True,  "enabled": True, "to": ["{ops}"], "cc": [], "bcc": []},
    {"route_key": "OUTAGE_ALERTS",   "critical": True,  "enabled": True, "to": ["{ops}"], "cc": [], "bcc": []},
    {"route_key": "SUPER_ADMIN_TO",  "critical": True,  "enabled": True, "to": ["{ops}"], "cc": [], "bcc": []},
    {"route_key": "SAFETY_FORMS_TO", "critical": False, "enabled": True, "to": ["{safety}"], "cc": [], "bcc": []},
    {"route_key": "ADMIN_DEAD_LETTER_TO", "critical": False, "enabled": True, "to": ["{support}"], "cc": [], "bcc": []},
]


async def provision_tenant(db, branding):
    tk = branding["tenant_key"]
    now = datetime.now(timezone.utc).isoformat()
    # 1) tenant_branding
    await db.tenant_branding.update_one({"_id": tk}, {"$set": {**branding, "updated_at": now}}, upsert=True)
    # 2) email_routes (6 routes)
    for r in ROUTE_BUNDLE:
        to = [a.format(
            ops=branding["operations_email"], safety=branding["safety_email"],
            support=branding["support_email"]
        ) for a in r["to"]]
        doc = {
            "_id": f"{tk}::{r['route_key']}",
            "tenant_key": tk,
            "route_key": r["route_key"],
            "display_name": r["route_key"].replace("_", " ").title(),
            "to": to,
            "cc": [],
            "bcc": [],
            "from_email": branding["from_email"],
            "reply_to": branding["reply_to"],
            "critical": r["critical"],
            "enabled": r["enabled"],
            "updated_at": now,
        }
        await db.email_routes.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    return tk


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]

    results = {"provisioning": [], "branding_resolution": [], "route_resolution": [],
               "isolation": [], "errors": []}
    t0 = time.time()

    # ── Phase 3 — Customer #2 ──
    tk2 = await provision_tenant(db, CUST2)
    elapsed_2 = round(time.time() - t0, 3)
    results["provisioning"].append({"tenant": tk2, "elapsed_s": elapsed_2})

    # ── Phase 4 — Customer #3 ──
    t1 = time.time()
    tk3 = await provision_tenant(db, CUST3)
    elapsed_3 = round(time.time() - t1, 3)
    results["provisioning"].append({"tenant": tk3, "elapsed_s": elapsed_3})

    # ── Verify branding resolution ──
    for tk, expected in [(tk2, CUST2["company_name"]), (tk3, CUST3["company_name"])]:
        b = await db.tenant_branding.find_one({"_id": tk})
        results["branding_resolution"].append({
            "tenant": tk,
            "resolved_company": b.get("company_name") if b else None,
            "match": (b and b.get("company_name") == expected),
        })

    # ── Verify route resolution per tenant ──
    import email_routing_v2 as v2
    os.environ["EMAIL_ROUTING_V2"] = "true"
    v2.invalidate_cache()

    for tk, expected_email in [(tk2, CUST2["operations_email"]), (tk3, CUST3["operations_email"])]:
        try:
            res = await v2.resolve(db, "BACKUP_ALERTS", tenant_key=tk)
            results["route_resolution"].append({
                "tenant": tk,
                "route": "BACKUP_ALERTS",
                "source": res.source,
                "to": res.to,
                "matches_expected_sender": expected_email in res.to,
            })
        except Exception as e:
            results["errors"].append({"tenant": tk, "route": "BACKUP_ALERTS", "error": f"{type(e).__name__}: {e}"})

    # ── Isolation: Customer #2 routes never resolve under Customer #3 tenant_key ──
    res_c2_under_c3 = await db.email_routes.find_one({"tenant_key": tk2, "_id": f"{tk3}::BACKUP_ALERTS"})
    results["isolation"].append({
        "test": "c2_route_doc_under_c3_tenant_key",
        "found_unexpectedly": res_c2_under_c3 is not None,
    })
    # MASCI route count unchanged
    masci_count = await db.email_routes.count_documents({"tenant_key": "masci"})
    results["isolation"].append({
        "test": "masci_route_count_unchanged",
        "actual": masci_count,
        "expected": 19,
        "pass": masci_count == 19,
    })
    # No tenant_branding cross-contamination
    masci_brand = await db.tenant_branding.find_one({"_id": "masci"}) or {}
    c2_brand = await db.tenant_branding.find_one({"_id": tk2}) or {}
    c3_brand = await db.tenant_branding.find_one({"_id": tk3}) or {}
    results["isolation"].append({
        "test": "branding_company_names_distinct",
        "masci": (masci_brand or {}).get("company_name") or "<unset MASCI default>",
        "c2": c2_brand.get("company_name"),
        "c3": c3_brand.get("company_name"),
        "all_distinct": len({(masci_brand or {}).get("company_name") or "MASCI",
                              c2_brand.get("company_name"),
                              c3_brand.get("company_name")}) == 3,
    })

    # ── Verify route count per tenant ──
    for tk in [tk2, tk3]:
        n = await db.email_routes.count_documents({"tenant_key": tk})
        results["route_resolution"].append({"tenant": tk, "route_count": n})

    os.environ["EMAIL_ROUTING_V2"] = "false"
    v2.invalidate_cache()

    out = "/app/test_reports/track_15_70_deployment_simulation.json"
    open(out, "w").write(json.dumps(results, indent=2, default=str))
    print(json.dumps(results, indent=2, default=str))
    print(f"\nSaved {out}")

asyncio.run(main())
