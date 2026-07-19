"""
TRACK 15.28C — Notification System Canonicalization · Migration Script
======================================================================

Strict in-place migration. Operator decisions locked:
  • PM scope source            = project_team_assignments (active only)
  • PM unscoped events         = suppressed unless pm_broadcast=True
  • Idempotency window         = PERMANENT (one event → one row, ever)
  • Legacy row mode            = in-place mutate, keep `id`, drop legacy fields
  • Dormant endpoint retirement = handlers deleted (separate code change)

Migration phases:
  Ⅰ.   Backfill `event_id` + `idempotency_key` on all 9,742 existing rows.
       Permanent dedupe ⇒ collapse pre-existing duplicates (TB-03 49× etc).
  Ⅱ.   Migrate 552 legacy `kind/audience/user_email` rows in `db.notifications`
       to canonical schema in place. Drop legacy fields.
  Ⅲ.   Migrate 162 rows from `db.tasks_notifications` into `db.notifications`
       (canonical shape), then drop `db.tasks_notifications`.
  Ⅳ.   Remove 7 `itest-mech-*` orphan rows.
  Ⅴ.   Print verification table.

Run order:
    python3 -m backend.scripts.track_15_28c_canonicalization_migration --dry-run
    python3 -m backend.scripts.track_15_28c_canonicalization_migration --apply

The script is RE-ENTRANT — running --apply twice yields the same result
(no duplicates, no orphans).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(str(ROOT / "backend" / ".env"))

import os  # noqa: E402
from pymongo import MongoClient  # noqa: E402
from lib.operator_safety import (  # noqa: E402
    redact_target_identity,
    require_cli_backup_ack,
    require_cli_confirmation,
    require_cli_execute,
    require_cli_runtime_guard,
)


def compute_idempotency_key(payload: Dict[str, Any]) -> str:
    """Mirror of routes.tasks_notifications.compute_idempotency_key.
    Re-declared here so the migration is self-contained."""
    parts = [
        str(payload.get("type") or ""),
        str(payload.get("linked_source_record_id") or ""),
        str(payload.get("linked_task_id") or ""),
        str(payload.get("recipient_role") or ""),
        str(payload.get("recipient_user_id") or ""),
        str(payload.get("linked_request_id") or ""),
        str(payload.get("linked_equipment_id") or ""),
        str(payload.get("linked_employee_id") or ""),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _resolve_user_id_from_email(db, email: str) -> Optional[str]:
    """Look up a canonical user_id given an email across every directory."""
    if not email:
        return None
    e = email.strip().lower()
    cols = [
        "hr_users", "safety_users", "shop_users", "dispatch_users",
        "field_leadership_users", "users", "user_directory",
        "project_managers", "employees",
    ]
    for c in cols:
        try:
            doc = db[c].find_one({"email": e}, {"id": 1, "_id": 0})
            if doc and doc.get("id"):
                return doc["id"]
        except Exception:
            continue
    return None


def phase_i_backfill_keys(db, apply: bool) -> Dict[str, int]:
    """Backfill event_id + idempotency_key on EVERY notifications row
    that lacks them. Permanent dedupe: when two existing rows resolve
    to the same key, KEEP THE FIRST, delete the rest."""
    total = db.notifications.count_documents({})
    seen_keys: Dict[str, str] = {}        # idem_key → kept-doc id
    backfilled = 0
    duplicate_drops = 0
    untouched = 0

    # Iterate oldest-first so the FIRST-CREATED row is the survivor.
    for d in db.notifications.find({}, sort=[("created_at", 1)]):
        rid = d.get("id")
        # Build the canonical payload-shape from whatever schema is present.
        payload = {
            "type": d.get("type") or d.get("kind") or "system",
            "linked_source_record_id": (
                d.get("linked_source_record_id")
                or d.get("ref_id")
                or d.get("linked_request_id")
                or d.get("target_id")
            ),
            "linked_task_id": d.get("linked_task_id"),
            "recipient_role": d.get("recipient_role") or d.get("audience"),
            "recipient_user_id": d.get("recipient_user_id") or d.get("user_id"),
            "linked_request_id": d.get("linked_request_id"),
            "linked_equipment_id": d.get("linked_equipment_id"),
            "linked_employee_id": d.get("linked_employee_id"),
        }
        key = compute_idempotency_key(payload)
        # Survivor logic
        if key in seen_keys:
            duplicate_drops += 1
            if apply:
                db.notifications.delete_one({"_id": d["_id"]})
            continue
        seen_keys[key] = rid
        update_set: Dict[str, Any] = {}
        if not d.get("idempotency_key"):
            update_set["idempotency_key"] = key
        if not d.get("event_id"):
            update_set["event_id"] = str(uuid.uuid4())
        if update_set:
            backfilled += 1
            if apply:
                db.notifications.update_one(
                    {"_id": d["_id"]}, {"$set": update_set},
                )
        else:
            untouched += 1
    return {
        "scanned": total,
        "duplicate_drops": duplicate_drops,
        "backfilled": backfilled,
        "untouched": untouched,
        "distinct_keys": len(seen_keys),
    }


def phase_ii_legacy_in_place(db, apply: bool) -> Dict[str, int]:
    """Mutate 552 legacy rows in `db.notifications` (kind/audience/
    user_email/user_id/read) to canonical (type/recipient_role/
    recipient_user_id/read_by). Drop legacy fields."""
    cursor = db.notifications.find({"kind": {"$exists": True}})
    rewritten = 0
    skipped = 0
    for d in cursor:
        rid = d.get("id")
        legacy_kind = d.get("kind")
        legacy_audience = d.get("audience")
        legacy_user_id = d.get("user_id")
        legacy_user_email = d.get("user_email")
        legacy_read = d.get("read")
        legacy_url = d.get("url") or d.get("ref_url")
        legacy_linked_req = d.get("linked_request_id")
        legacy_ref_id = d.get("ref_id")
        legacy_request_kind = d.get("request_kind")
        legacy_user_directory = d.get("user_directory")
        legacy_body = d.get("body")

        # Resolve recipient_user_id with fall-back to email lookup.
        ruid = legacy_user_id
        if (not ruid or ruid in ("hr_inbox", "admin", "")) and legacy_user_email:
            ruid_resolved = _resolve_user_id_from_email(db, legacy_user_email)
            if ruid_resolved:
                ruid = ruid_resolved
            else:
                ruid = None

        # Audience → recipient_role
        role_map = {
            "hr": "hr",
            "safety": "safety",
            "shop": "shop",
            "dispatch": "dispatch",
            "pm": "pm",
            "leadership": "leadership",
            "asset_admin": "asset_admin",
            "fl": "fl",
            "admin": "admin",
        }
        recipient_role = role_map.get(
            (legacy_audience or "").lower(),
            "admin" if legacy_kind == "oa_assignment" else "hr"
            if legacy_kind == "hr.employee_request" else "admin",
        )

        # Build read_by from legacy boolean.
        read_by: List[Dict[str, Any]] = []
        if legacy_read is True:
            read_by.append({
                "role": recipient_role,
                "user_id": ruid,
                "at": d.get("created_at") or datetime.now(timezone.utc),
            })

        canonical_payload = {
            "type": legacy_kind,
            "linked_source_record_id": legacy_ref_id or legacy_linked_req,
            "recipient_role": recipient_role,
            "recipient_user_id": ruid,
            "linked_request_id": legacy_linked_req,
        }
        idem_key = compute_idempotency_key(canonical_payload)

        set_payload: Dict[str, Any] = {
            "type": legacy_kind,
            "recipient_role": recipient_role,
            "recipient_user_id": ruid,
            "read_by": read_by,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "severity": d.get("severity", "Info").capitalize()
            if isinstance(d.get("severity"), str) else "Info",
            "expires_at": d.get("expires_at"),
            "linked_source_module": d.get("linked_source_module")
            or ("hr.employee_request" if legacy_kind == "hr.employee_request"
                else "operations_action" if legacy_kind == "oa_assignment"
                else legacy_kind),
            "linked_source_record_id": legacy_ref_id or legacy_linked_req,
            "linked_request_id": legacy_linked_req,
            "link_url": d.get("link_url") or legacy_url,
            "pm_broadcast": False,
            "delivery": {"internal": True, "email": False, "push": False, "sms": False},
            "idempotency_key": idem_key,
            "event_id": d.get("event_id") or str(uuid.uuid4()),
        }
        # body field (oa_assignment) → message
        if not d.get("message") and legacy_body:
            set_payload["message"] = legacy_body

        # Drop legacy fields after the migration.
        unset_fields = {
            "kind": "",
            "audience": "",
            "user_email": "",
            "user_id": "",
            "user_directory": "",
            "read": "",
            "url": "",
            "ts": "",
            "request_kind": "",
            "ref_kind": "",
            "ref_id": "",
            "ref_url": "",
            "body": "",
        }
        rewritten += 1
        if apply:
            try:
                db.notifications.update_one(
                    {"_id": d["_id"]},
                    {"$set": set_payload, "$unset": unset_fields},
                )
            except Exception as exc:
                # Idempotency-key collision: the canonical-shape twin
                # of this row already exists post-migration. Delete the
                # legacy duplicate to honour permanent dedupe.
                msg = str(exc).lower()
                if "duplicate key" in msg and "idempotency_key" in msg:
                    db.notifications.delete_one({"_id": d["_id"]})
                    skipped += 1
                    rewritten -= 1
                else:
                    raise
    return {"rewritten": rewritten, "deleted_as_dup": skipped}


def phase_iii_tasks_notifications(db, apply: bool) -> Dict[str, int]:
    """Migrate `db.tasks_notifications` → `db.notifications` (canonical)
    then drop the source collection."""
    src = db.tasks_notifications
    if "tasks_notifications" not in db.list_collection_names():
        return {"migrated": 0, "dup_skipped": 0, "dropped": False}
    migrated = 0
    dup_skipped = 0
    for d in src.find({}):
        kind = d.get("kind") or "pm_engine.event"
        audience_role = (d.get("audience_role") or "shop").lower()
        role_map = {
            "mechanic": "shop",
            "shop": "shop",
            "shop_manager": "shop",
            "pm": "pm",
            "admin": "admin",
        }
        recipient_role = role_map.get(audience_role, "shop")
        ruid = d.get("audience_id")
        unit = d.get("unit_number") or ""
        pm_name = d.get("pm_name") or ""
        summary = d.get("summary") or ""
        canonical_payload = {
            "type": f"pm_engine.{kind}",
            "linked_source_record_id": f"{unit}:{kind}",
            "recipient_role": recipient_role,
            "recipient_user_id": ruid,
            "linked_equipment_id": unit or None,
        }
        idem_key = compute_idempotency_key(canonical_payload)
        # Read posture from legacy `read_at`.
        read_by: List[Dict[str, Any]] = []
        if d.get("read_at"):
            read_by.append({
                "role": recipient_role,
                "user_id": ruid,
                "at": d.get("read_at"),
            })
        new_doc = {
            "id": d.get("id") or str(uuid.uuid4()),
            "event_id": str(uuid.uuid4()),
            "idempotency_key": idem_key,
            "type": f"pm_engine.{kind}"[:64],
            "title": f"{pm_name} · {unit}".strip(" ·"),
            "message": summary or None,
            "severity": "Info",
            "recipient_role": recipient_role,
            "recipient_user_id": ruid,
            "pm_broadcast": False,
            "linked_source_module": "pm_engine",
            "linked_source_record_id": f"{unit}:{kind}",
            "linked_equipment_id": unit or None,
            "linked_task_id": None,
            "linked_project_number": None,
            "linked_employee_id": None,
            "linked_request_id": None,
            "link_url": None,
            "created_at": d.get("created_at") or datetime.now(timezone.utc),
            "expires_at": None,
            "read_by": read_by,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "delivery": {"internal": True, "email": False, "push": False, "sms": False},
        }
        if apply:
            try:
                db.notifications.insert_one(new_doc)
                migrated += 1
            except Exception as exc:
                msg = str(exc).lower()
                if "duplicate key" in msg and "idempotency_key" in msg:
                    dup_skipped += 1
                else:
                    raise
        else:
            migrated += 1
    if apply:
        db.tasks_notifications.drop()
    return {"migrated": migrated, "dup_skipped": dup_skipped, "dropped": apply}


def phase_iv_orphan_cleanup(db, apply: bool) -> Dict[str, int]:
    """Delete the 7 test-fixture orphan rows (`itest-mech-*`)."""
    q = {"recipient_user_id": {"$regex": "^itest-mech-"}}
    cnt = db.notifications.count_documents(q)
    deleted = 0
    if apply and cnt:
        res = db.notifications.delete_many(q)
        deleted = res.deleted_count
    return {"found": cnt, "deleted": deleted}


def verification_table(db) -> Dict[str, Any]:
    total = db.notifications.count_documents({})
    legacy_kind = db.notifications.count_documents({"kind": {"$exists": True}})
    legacy_audience = db.notifications.count_documents({"audience": {"$exists": True}})
    legacy_user_email = db.notifications.count_documents({"user_email": {"$exists": True}})
    legacy_read = db.notifications.count_documents({"read": {"$exists": True}})
    with_event_id = db.notifications.count_documents({"event_id": {"$exists": True}})
    with_idem = db.notifications.count_documents({"idempotency_key": {"$exists": True}})
    with_pm_bcast = db.notifications.count_documents({"pm_broadcast": True})
    canonical = db.notifications.count_documents({"type": {"$exists": True}})
    cols = db.list_collection_names()
    tasks_notif_present = "tasks_notifications" in cols
    return {
        "total_rows": total,
        "rows_with_legacy_kind": legacy_kind,
        "rows_with_legacy_audience": legacy_audience,
        "rows_with_legacy_user_email": legacy_user_email,
        "rows_with_legacy_read_bool": legacy_read,
        "rows_with_event_id": with_event_id,
        "rows_with_idempotency_key": with_idem,
        "rows_with_pm_broadcast_true": with_pm_bcast,
        "rows_with_canonical_type": canonical,
        "tasks_notifications_collection_present": tasks_notif_present,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", default=False)
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--backup-ack", action="store_true")
    args = parser.parse_args()
    apply = bool(args.apply) and not args.dry_run if args.apply else False
    if args.apply:
        apply = True

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    app_env = os.environ.get("APP_ENV") or ""
    if not mongo_url or not db_name:
        print("FATAL: MONGO_URL / DB_NAME not set.", file=sys.stderr)
        return 2
    target = redact_target_identity(mongo_url, db_name)
    if apply:
        try:
            require_cli_execute(args.apply)
            require_cli_confirmation(args.confirm, expected="RUN_CANONICALIZATION_MIGRATION")
            require_cli_backup_ack(args.backup_ack)
            require_cli_runtime_guard(
                app_env=app_env,
                db_name=db_name,
                allow_production=args.allow_production,
                expected_db_name="masci_safety",
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 3
    client = MongoClient(mongo_url)
    db = client[db_name]

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\n==== TRACK 15.28C MIGRATION · MODE={mode} · DB={db_name} ====\n")
    print(json.dumps({"target": target, "mode": mode, "confirmation_token": "RUN_CANONICALIZATION_MIGRATION"}, indent=2))

    print("BEFORE:")
    for k, v in verification_table(db).items():
        print(f"  {k:45s}: {v}")
    print()

    print("PHASE I — Backfill event_id + idempotency_key + collapse dupes")
    r1 = phase_i_backfill_keys(db, apply=apply)
    for k, v in r1.items():
        print(f"  {k:45s}: {v}")
    print()

    print("PHASE II — Legacy 552 rows in-place migration")
    r2 = phase_ii_legacy_in_place(db, apply=apply)
    for k, v in r2.items():
        print(f"  {k:45s}: {v}")
    print()

    print("PHASE III — tasks_notifications → notifications")
    r3 = phase_iii_tasks_notifications(db, apply=apply)
    for k, v in r3.items():
        print(f"  {k:45s}: {v}")
    print()

    print("PHASE IV — Orphan cleanup (itest-mech-*)")
    r4 = phase_iv_orphan_cleanup(db, apply=apply)
    for k, v in r4.items():
        print(f"  {k:45s}: {v}")
    print()

    print("AFTER:")
    for k, v in verification_table(db).items():
        print(f"  {k:45s}: {v}")
    print()

    if not apply:
        print("DRY-RUN COMPLETE — no writes performed. Pass --apply to commit.")
    else:
        print("APPLY COMPLETE — all migrations committed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
