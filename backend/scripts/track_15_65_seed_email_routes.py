"""
Track 15.65 — Email Routing V2 pre-seed script
==============================================

Idempotent seed for the 19 logical routes that Track 15.64 designed.

Usage
-----
    cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --dry-run
    cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --apply
    cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --verify

Refuses to run on production (`APP_ENV=production`) unless `--allow-prod`
is set. Default tenant is `masci`.

Outputs a JSON summary (created / updated / skipped / unchanged) on stdout
and a markdown digest at /app/memory/track_15_65_data/preseed_<mode>.json.

Hard rules honoured:
  - Never duplicates a recipient (case-insensitive de-dup).
  - Does not overwrite admin-customised rows unless `--force` is passed.
  - Validates every critical route has at least one recipient; emits a
    warning (and `exit 2`) if violated.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Bootstrap path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(HERE.parent / ".env")


TENANT_KEY = "masci"


def _env_list(key: str, default: List[str] | None = None) -> List[str]:
    raw = (os.environ.get(key) or "").strip()
    if not raw:
        return list(default or [])
    return [e.strip() for e in raw.split(",") if e.strip()]


# ----------------------------------------------------------------------------
# Wave-1 route catalog. Every field below traces back to
# TRACK_15_64_NOTIFICATION_FLOW_MAP.md and the live env vars in backend/.env.
# Defaults preserve current MASCI behaviour exactly.
# ----------------------------------------------------------------------------
def build_catalog() -> List[Dict[str, Any]]:
    super_admin = (os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com").strip()
    safety_to   = _env_list("SAFETY_FORMS_EMAIL_TO",      ["safety@mascigc.com", super_admin])
    backup_to   = _env_list("BACKUP_EMAIL_TO",            [super_admin])
    health_to   = _env_list("HEALTH_ALERT_RECIPIENTS")    or backup_to or [super_admin]
    outage_to   = _env_list("OUTAGE_ALERT_TO",            [super_admin])
    digest_to   = _env_list("SAFETY_DIGEST_TO_EMAIL",     ["safety@mascigc.com"])
    operator_to = _env_list("OPERATOR_DIGEST_RECIPIENTS") or digest_to or [super_admin]
    payroll_to  = _env_list("PAYROLL_VARIANCE_EMAIL_TO",  [super_admin])
    dead_letter = _env_list("ADMIN_DEAD_LETTER_EMAIL",    ["safety@mascigc.com"])
    dispatch_to = _env_list("DISPATCH_EMAIL")             or [super_admin]
    shop_mgr    = (os.environ.get("SHOP_MANAGER_EMAIL") or "shopmanager@mascigc.com").strip()
    lead_to     = [
        (os.environ.get("LEADERSHIP_ALWAYS_TO_1") or super_admin).strip(),
        (os.environ.get("LEADERSHIP_ALWAYS_TO_2") or "safety@mascigc.com").strip(),
    ]
    severe_cc   = _env_list("SEVERE_INCIDENT_CC")
    sender      = (os.environ.get("SENDER_EMAIL")  or "noreply@mascidocs.com").strip()
    reply_to    = (os.environ.get("REPLY_TO_EMAIL") or super_admin).strip()

    return [
        {
            "route_key": "COMPLIANCE_ALWAYS_CC",
            "display_name": "Compliance Always-CC",
            "description": "Office CC on every Inspection / Meeting / JHA / Daily Report / Incident / QA-QC submission.",
            "category": "compliance",
            "severity": "info",
            "to": [super_admin, "safety@mascigc.com"],
            "cc": [], "bcc": [],
            "owner_role": "Operations",
            "critical": False,
            "fallback_env_keys": [],
            "legacy_key": "always_cc",
        },
        {
            "route_key": "SAFETY_FORMS_TO",
            "display_name": "Safety Forms Distribution",
            "description": "Equipment Issuance / Training / Return reports.",
            "category": "compliance",
            "severity": "info",
            "to": safety_to, "cc": [], "bcc": [],
            "owner_role": "Safety Manager",
            "critical": False,
            "fallback_env_keys": ["SAFETY_FORMS_EMAIL_TO"],
            "legacy_key": "safety_forms_to",
        },
        {
            "route_key": "FIELD_LEADERSHIP_ALWAYS_TO",
            "display_name": "Field Leadership Always-CC",
            "description": "CC for the 10 Field Leadership form types.",
            "category": "leadership",
            "severity": "info",
            "to": lead_to, "cc": [], "bcc": [],
            "owner_role": "HR / Safety",
            "critical": False,
            "fallback_env_keys": ["LEADERSHIP_ALWAYS_TO_1", "LEADERSHIP_ALWAYS_TO_2"],
            "legacy_key": "leadership_always_to",
        },
        {
            "route_key": "PRE_OP_FAIL_FALLBACK",
            "display_name": "Pre-Op Fail Fallback",
            "description": "Single fallback when shop_users collection is empty (Pre-Op fail / OOS).",
            "category": "shop",
            "severity": "warn",
            "to": [shop_mgr], "cc": [], "bcc": [],
            "owner_role": "Shop Manager",
            "critical": False,
            "fallback_env_keys": ["SHOP_MANAGER_EMAIL"],
            "legacy_key": "shop_manager_fallback",
        },
        {
            "route_key": "INCIDENT_SEVERE_CC",
            "display_name": "Severe Incident CC",
            "description": "Extra CCs for WV / PI / severe incidents.",
            "category": "safety",
            "severity": "critical",
            "to": severe_cc, "cc": [], "bcc": [],
            "owner_role": "Safety Manager",
            "critical": False,  # extension layer, not the only recipient list
            "fallback_env_keys": ["SEVERE_INCIDENT_CC"],
            "legacy_key": "severe_incident_cc",
        },
        {
            "route_key": "BACKUP_ALERTS",
            "display_name": "Backup Pipeline Alerts",
            "description": "Daily auto-backup and manual backup email destination.",
            "category": "platform",
            "severity": "warn",
            "to": backup_to, "cc": [], "bcc": [],
            "owner_role": "Platform Admin",
            "critical": True,
            "fallback_env_keys": ["BACKUP_EMAIL_TO"],
            "legacy_key": "backup_email_to",
        },
        {
            "route_key": "HEALTH_ALERTS",
            "display_name": "Platform Health Alerts",
            "description": "Scheduler dead / backup stale / DB unreachable alerts.",
            "category": "platform",
            "severity": "critical",
            "to": health_to, "cc": [], "bcc": [],
            "owner_role": "Platform Admin",
            "critical": True,
            "fallback_env_keys": ["HEALTH_ALERT_RECIPIENTS", "BACKUP_EMAIL_TO"],
        },
        {
            "route_key": "OUTAGE_ALERTS",
            "display_name": "Platform Outage Alerts",
            "description": "Platform-wide outage notifications.",
            "category": "platform",
            "severity": "critical",
            "to": outage_to, "cc": [], "bcc": [],
            "owner_role": "Platform Admin",
            "critical": True,
            "fallback_env_keys": ["OUTAGE_ALERT_TO"],
        },
        {
            "route_key": "SAFETY_DIGEST_TO",
            "display_name": "Weekly Safety Digest",
            "description": "Monday 14:00 UTC digest of safety metrics.",
            "category": "digest",
            "severity": "info",
            "to": digest_to, "cc": [], "bcc": [],
            "owner_role": "Safety Manager",
            "critical": False,
            "fallback_env_keys": ["SAFETY_DIGEST_TO_EMAIL"],
        },
        {
            "route_key": "OPERATOR_DIGEST_RECIPIENTS",
            "display_name": "Daily Operator Digest",
            "description": "Daily operator status digest.",
            "category": "digest",
            "severity": "info",
            "to": operator_to, "cc": [], "bcc": [],
            "owner_role": "Operations",
            "critical": False,
            "fallback_env_keys": ["OPERATOR_DIGEST_RECIPIENTS", "SAFETY_DIGEST_TO_EMAIL"],
        },
        {
            "route_key": "PAYROLL_VARIANCE_TO",
            "display_name": "Payroll Variance Digest",
            "description": "Weekly payroll-variance summary.",
            "category": "digest",
            "severity": "info",
            "to": payroll_to, "cc": [], "bcc": [],
            "owner_role": "HR Manager",
            "critical": False,
            "fallback_env_keys": ["PAYROLL_VARIANCE_EMAIL_TO"],
        },
        {
            "route_key": "ADMIN_DEAD_LETTER_TO",
            "display_name": "Admin Dead-Letter",
            "description": "Unresolved field-submitter identity dead-letter.",
            "category": "platform",
            "severity": "warn",
            "to": dead_letter, "cc": [], "bcc": [],
            "owner_role": "Platform Admin",
            "critical": False,
            "fallback_env_keys": ["ADMIN_DEAD_LETTER_EMAIL"],
        },
        {
            "route_key": "DISPATCH_ROLE_TO",
            "display_name": "Dispatch Role Alerts",
            "description": "Dispatch-role fan-out (trench safety + dispatch board).",
            "category": "operations",
            "severity": "warn",
            "to": dispatch_to, "cc": [], "bcc": [],
            "owner_role": "Dispatcher",
            "critical": False,
            "fallback_env_keys": ["DISPATCH_EMAIL", "SUPER_ADMIN_EMAIL"],
        },
        {
            "route_key": "SUPER_ADMIN_TO",
            "display_name": "Super Admin Escalation",
            "description": "Platform-admin escalation channel.",
            "category": "platform",
            "severity": "critical",
            "to": [super_admin], "cc": [], "bcc": [],
            "owner_role": "Platform Admin",
            "critical": True,
            "fallback_env_keys": ["SUPER_ADMIN_EMAIL"],
        },
        {
            "route_key": "EXECUTIVE_DIGEST",
            "display_name": "Executive Digest",
            "description": "Weekly exec digest (post-Wave 1 wiring).",
            "category": "digest",
            "severity": "info",
            "to": [super_admin], "cc": [], "bcc": [],
            "owner_role": "Executive",
            "critical": False,
            "fallback_env_keys": [],
        },
        {
            "route_key": "ACCOUNT_INVITES_FROM",
            "display_name": "Account Invites Sender",
            "description": "Per-portal welcome / invite sender + reply-to.",
            "category": "branding",
            "severity": "info",
            "to": [], "cc": [], "bcc": [],
            "from_email": sender,
            "reply_to": reply_to,
            "owner_role": "Platform Admin",
            "critical": False,
            "fallback_env_keys": ["SENDER_EMAIL", "REPLY_TO_EMAIL"],
        },
        {
            "route_key": "PASSWORD_RESET_MONITORING_TO",
            "display_name": "Password Reset Monitoring",
            "description": "Optional CC on portal reset-link sends. Off by default.",
            "category": "security",
            "severity": "info",
            "to": [], "cc": [], "bcc": [],
            "owner_role": "Platform Admin",
            "critical": False,
            "enabled": False,
            "fallback_env_keys": [],
        },
        {
            "route_key": "TRENCH_SAFETY_PULSE_SAFETY",
            "display_name": "Trench Safety Pulse · safety role",
            "description": "Trench-safety pulse fan-out for the safety role.",
            "category": "safety",
            "severity": "warn",
            "to": digest_to or [super_admin], "cc": [], "bcc": [],
            "owner_role": "Safety Manager",
            "critical": False,
            "fallback_env_keys": ["SAFETY_DIGEST_TO_EMAIL", "SUPER_ADMIN_EMAIL"],
        },
        {
            "route_key": "TRENCH_SAFETY_PULSE_SHOP",
            "display_name": "Trench Safety Pulse · shop role",
            "description": "Trench-safety pulse fan-out for the shop role.",
            "category": "safety",
            "severity": "warn",
            "to": [shop_mgr], "cc": [], "bcc": [],
            "owner_role": "Shop Manager",
            "critical": False,
            "fallback_env_keys": ["SHOP_MANAGER_EMAIL"],
        },
    ]


def _dedup(emails: List[str]) -> List[str]:
    out: List[str] = []
    seen: set = set()
    for e in emails or []:
        s = str(e).strip()
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


async def run(mode: str, force: bool) -> Dict[str, Any]:
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    catalog = build_catalog()
    summary = {"created": [], "updated": [], "unchanged": [], "skipped": [], "errors": []}
    now_iso = datetime.now(timezone.utc).isoformat()

    for r in catalog:
        rk = r["route_key"]
        _id = f"{TENANT_KEY}::{rk}"
        try:
            existing = await db.email_routes.find_one({"_id": _id})
        except Exception as e:
            summary["errors"].append({"route_key": rk, "error": str(e)})
            continue

        new_doc = {
            "_id": _id,
            "tenant_key": TENANT_KEY,
            "route_key": rk,
            "display_name": r["display_name"],
            "description": r["description"],
            "category": r.get("category", "general"),
            "severity": r.get("severity", "info"),
            "to": _dedup(r.get("to") or []),
            "cc": _dedup(r.get("cc") or []),
            "bcc": _dedup(r.get("bcc") or []),
            "from_email": r.get("from_email"),
            "reply_to": r.get("reply_to"),
            "owner_role": r.get("owner_role"),
            "critical": bool(r.get("critical", False)),
            "enabled": bool(r.get("enabled", True)),
            "fallback_env_keys": list(r.get("fallback_env_keys") or []),
            "legacy_key": r.get("legacy_key"),
            "source": "seed",
            "version": 1,
            "updated_at": now_iso,
            "updated_by": "track_15_65_seed",
            "last_tested_at": None,
            "last_test_status": None,
        }

        # Critical-route safety: refuse to seed a critical route with empty TO.
        if new_doc["critical"] and not new_doc["to"]:
            summary["errors"].append({
                "route_key": rk,
                "error": "critical route resolved empty recipient list during seed",
            })
            continue

        if existing is None:
            new_doc["created_at"] = now_iso
            if mode == "apply":
                await db.email_routes.insert_one(new_doc)
            summary["created"].append(rk)
        else:
            customized = (existing.get("source") in ("admin", "manual")) or existing.get("admin_customized")
            if customized and not force:
                summary["skipped"].append({"route_key": rk, "reason": "admin_customized"})
                continue
            diff = {k: v for k, v in new_doc.items()
                    if k not in ("_id", "created_at") and existing.get(k) != v}
            if not diff:
                summary["unchanged"].append(rk)
                continue
            if mode == "apply":
                await db.email_routes.update_one(
                    {"_id": _id}, {"$set": {**diff, "updated_at": now_iso}}
                )
            summary["updated"].append({"route_key": rk, "fields": list(diff.keys())})

    # Index for tenant queries
    if mode == "apply":
        try:
            await db.email_routes.create_index([("tenant_key", 1), ("route_key", 1)])
            await db.email_routing_audit_v2.create_index([("tenant_key", 1), ("ts", -1)])
        except Exception:
            pass

    return {
        "mode": mode,
        "tenant_key": TENANT_KEY,
        "force": force,
        "ts": now_iso,
        "summary": summary,
        "total_routes": len(catalog),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="report changes without writing")
    g.add_argument("--apply", action="store_true", help="write changes to MongoDB")
    g.add_argument("--verify", action="store_true", help="read-only audit of the route catalog")
    p.add_argument("--force", action="store_true", help="overwrite admin-customised rows")
    p.add_argument("--allow-prod", action="store_true",
                   help="allow execution against APP_ENV=production (default: refuse)")
    args = p.parse_args()

    app_env = (os.environ.get("APP_ENV") or "").strip().lower()
    if app_env == "production" and not args.allow_prod:
        print(json.dumps({
            "ok": False,
            "error": "refusing to run against APP_ENV=production without --allow-prod",
        }, indent=2))
        sys.exit(1)

    mode = "dry-run" if args.dry_run else ("apply" if args.apply else "verify")
    result = asyncio.run(run(mode=mode, force=args.force))

    out_path = Path("/app/memory/track_15_65_data") / f"preseed_{mode}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

    exit_code = 0
    if result["summary"]["errors"]:
        exit_code = 2
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
