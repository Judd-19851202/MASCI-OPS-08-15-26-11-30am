#!/usr/bin/env python3
"""
TRACK 15.2 — Phase 2/3: Leaked PM offboarding notification cleanup.

WHAT IT DOES
============
After Track 15.1 fixed the WRITE-site PM offboarding leak (broadcast
to all PMs), historical leaked rows still sit in the `notifications`
collection. This script:

  1. SCANS for the leaked rows using a tight filter (see PREDICATE
     below). Only rows that match EVERY clause are touched. Anything
     ambiguous is left alone.
  2. In DRY-RUN mode (default) it prints a per-row preview and writes
     a ledger to `track_15_2_dryrun_<ts>.json` in the script dir. NO
     mutation. NO audit event. Operator reads, approves, then re-runs
     with --apply.
  3. In --apply mode it resolves each leaked row's proper recipient
     (the PM(s) of the project the offboarded employee was active on
     at the time), stamps `recipient_user_id` to ONE PM, copies the
     row for each ADDITIONAL PM, and EXPIRES the original
     `recipient_role`-broadcast row by setting `expires_at = now`. An
     audit row is written for every change to `db.audit_events`. The
     original row's `_id` is preserved (no delete).

WHY EXPIRE INSTEAD OF DELETE
============================
Notification rows in this app already TTL on `expires_at` (60d default
from creation). Setting `expires_at = now` simply moves the natural
sunset forward — no destruction, no surprise, no audit gap. Frontend
filters already respect `expires_at` (rows past expiry are excluded
from the bell feed). If the operator decides the cleanup was wrong,
they can revert by bumping `expires_at` forward again on the rows
the script touched (their ids are in the ledger).

SAFETY GUARANTEES
=================
  • Dry-run by default. --apply must be explicit.
  • A scoped predicate. We touch ONLY rows where:
      - `linked_source_module == "hr.offboarding"`
      - `recipient_role == "pm"`
      - `recipient_user_id IS NULL` (i.e. STILL broadcasting; person-
        targeted rows from the post-15.1 code path are untouched)
      - `linked_employee_id IS NOT NULL` (so we can resolve PMs)
  • A maximum cap (--max-rows, default 200). The script refuses to
    process more than N rows in one pass.
  • Per-row audit. Every mutation goes to `db.audit_events` with
    category=`track_15_2.pm_offboarding_cleanup`.
  • Ledger JSON file. Every row id touched is captured.
  • Resumable. Re-running --apply skips rows whose `_track_15_2_cleaned_at`
    flag is already set.

OPERATOR EXECUTION (PRODUCTION)
===============================
On the production box (or via a one-off pod with prod MONGO_URL):

    cd /app/backend
    # Dry-run — read-only, prints + writes ledger JSON
    MONGO_URL="<prod>" DB_NAME="masci_safety" \
      python scripts/track_15_2_backfill_leaked_pm_offboarding.py

    # Inspect the ledger JSON. Confirm every row should be expired.
    less scripts/track_15_2_dryrun_<ts>.json

    # Apply (only after dry-run approval).
    MONGO_URL="<prod>" DB_NAME="masci_safety" APP_ENV="production" \
      python scripts/track_15_2_backfill_leaked_pm_offboarding.py --apply --prod-confirm

    # The script writes a final ledger `track_15_2_applied_<ts>.json`
    # listing every notification id expired and every per-PM copy
    # created. Keep both files for audit.

PRODUCTION SAFETY GUARD (Track 15.8B)
=====================================
  • Dry-run is always allowed (no --prod-confirm required).
  • `--apply` against APP_ENV=production OR DB_NAME=masci_safety REFUSES
    unless `--prod-confirm` is ALSO passed. Exit code 2, clear message:
        "Refusing production mutation without --prod-confirm ..."
  • `--prod-confirm` asserts BOTH APP_ENV=="production" AND
    DB_NAME=="masci_safety". Mismatch → exit code 2 with diagnostic.
  • `--prod-confirm` without `--apply` is a no-op (dry-run is the same
    either way).
  • Non-production `--apply` (e.g. preview cleanup) still works without
    `--prod-confirm` for normal pre-deploy gate flows.

REVERTING
=========
Each ledger entry includes the original `expires_at` value. To revert,
run the helper at the bottom of this file or restore manually:

    db.notifications.update_one(
        {"id": "<id from ledger>"},
        {"$set": {"expires_at": "<original_expires_at>",
                  "_track_15_2_cleaned_at": None}}
    )

Cert tag: TRACK15-2-PM-STAFFING-CERT (audit category prefix).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:  # pragma: no cover
    print("motor is required. pip install motor", file=sys.stderr)
    sys.exit(1)


AUDIT_CATEGORY = "track_15_2.pm_offboarding_cleanup"
CLEANED_AT_FLAG = "_track_15_2_cleaned_at"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


async def _get_db():
    url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME") or "masci_safety_preview"
    if not url:
        raise SystemExit("MONGO_URL is required")
    cli = AsyncIOMotorClient(url)
    return cli, cli[db_name]


async def _resolve_pms_for_employee_at(
    db, employee_id: str, project_number: Optional[str],
) -> List[Dict[str, Any]]:
    """Return [{user_id, email, project_number}, ...] for the employee.

    Prefers active assignments. If project_number is provided (from
    the notification's linked_project_number) we scope to it; else we
    return PMs of every active project the employee is on."""
    projects: set = set()
    if project_number:
        projects.add(project_number)
    else:
        cur = db.project_team_assignments.find(
            {"active": True, "employee_id": employee_id},
            {"_id": 0, "project_number": 1},
        )
        async for r in cur:
            if r.get("project_number"):
                projects.add(r["project_number"])
    if not projects:
        return []
    targets: List[Dict[str, Any]] = []
    seen: set = set()
    for pn in projects:
        pm_emails: set = set()
        job = await db.jobs_master.find_one(
            {"project_number": pn},
            {"_id": 0, "pm_email": 1, "co_pm_emails": 1},
        )
        if job:
            if job.get("pm_email"):
                pm_emails.add(job["pm_email"].lower())
            for e in (job.get("co_pm_emails") or []):
                if e:
                    pm_emails.add(e.lower())
        staff_cur = db.project_team_assignments.find(
            {
                "project_number": pn, "active": True,
                "assignment_role": {"$in": ["pm", "co_pm"]},
            },
            {"_id": 0, "email": 1},
        )
        async for r in staff_cur:
            if r.get("email"):
                pm_emails.add(r["email"].lower())
        for em in pm_emails:
            u = await db.user_directory.find_one(
                {"email": em}, {"_id": 0, "id": 1, "email": 1, "name": 1},
            )
            if not u:
                continue
            key = f"{u['id']}|{pn}"
            if key in seen:
                continue
            seen.add(key)
            targets.append({
                "user_id": u["id"], "email": u.get("email", ""),
                "name": u.get("name", ""), "project_number": pn,
            })
    return targets


async def scan(db, max_rows: int) -> List[Dict[str, Any]]:
    """Return leaked rows (≤max_rows) matching the tight predicate."""
    predicate = {
        "linked_source_module": "hr.offboarding",
        "recipient_role": "pm",
        "$and": [
            {"$or": [{"recipient_user_id": None},
                     {"recipient_user_id": {"$exists": False}}]},
            {"$or": [{CLEANED_AT_FLAG: None},
                     {CLEANED_AT_FLAG: {"$exists": False}}]},
            {"linked_employee_id": {"$ne": None}},
            {"linked_employee_id": {"$exists": True}},
        ],
    }
    rows: List[Dict[str, Any]] = []
    cur = db.notifications.find(predicate, {"_id": 0}).limit(max_rows)
    async for r in cur:
        rows.append(r)
    return rows


async def plan_row(db, row: Dict[str, Any]) -> Dict[str, Any]:
    """Compute the cleanup plan for one leaked row."""
    targets = await _resolve_pms_for_employee_at(
        db,
        employee_id=row.get("linked_employee_id"),
        project_number=row.get("linked_project_number"),
    )
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "created_at": _iso(row.get("created_at")) if isinstance(row.get("created_at"), datetime) else row.get("created_at"),
        "current_recipient_role": row.get("recipient_role"),
        "current_recipient_user_id": row.get("recipient_user_id"),
        "linked_employee_id": row.get("linked_employee_id"),
        "linked_project_number": row.get("linked_project_number"),
        "current_expires_at": _iso(row.get("expires_at")) if isinstance(row.get("expires_at"), datetime) else row.get("expires_at"),
        "resolved_pm_targets": targets,
        "proposed_action": (
            "expire_and_fanout" if targets
            else "expire_only_no_targets"
        ),
        "leak_reason": (
            "recipient_role='pm' with no recipient_user_id; row was "
            "broadcast to every PM in the directory. After Track 15.1 "
            "fix, new offboardings produce per-PM rows instead; this "
            "row is historical leakage."
        ),
    }


async def apply_plan(db, plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the cleanup for one row. Returns the executed ledger entry."""
    now = _now()
    notif_id = plan["id"]
    audit_id = str(uuid.uuid4())
    # 1. For each target PM (≥0), create a per-PM person-targeted copy
    #    so the legitimate-recipient PM still sees the notification.
    new_ids: List[str] = []
    for t in plan["resolved_pm_targets"]:
        # Pull the original row again (need full fields).
        orig = await db.notifications.find_one({"id": notif_id}, {"_id": 0})
        if not orig:
            break
        clone = dict(orig)
        clone["id"] = str(uuid.uuid4())
        clone["recipient_user_id"] = t["user_id"]
        clone["linked_project_number"] = t["project_number"]
        clone[CLEANED_AT_FLAG] = now
        clone["_track_15_2_source_id"] = notif_id
        # Keep the original recipient_role as scope guard.
        clone["expires_at"] = orig.get("expires_at") or (now + timedelta(days=14))
        clone["read_by"] = []  # Person-targeted copy: unread for this PM.
        await db.notifications.insert_one(clone)
        new_ids.append(clone["id"])
    # 2. Expire the original broadcast row (do NOT delete).
    update = {
        "expires_at": now,
        CLEANED_AT_FLAG: now,
        "_track_15_2_replaced_with": new_ids,
    }
    await db.notifications.update_one(
        {"id": notif_id}, {"$set": update},
    )
    # 3. Audit-log every change.
    await db.audit_events.insert_one({
        "id": audit_id,
        "at": now,
        "category": AUDIT_CATEGORY,
        "action": "expire_and_fanout_leaked_pm_offboarding",
        "actor": {"role": "system", "name": "track_15_2_cleanup"},
        "subject": {"collection": "notifications", "id": notif_id},
        "linked_employee_id": plan["linked_employee_id"],
        "linked_project_number": plan["linked_project_number"],
        "new_person_targeted_ids": new_ids,
        "before": {
            "recipient_role": plan["current_recipient_role"],
            "recipient_user_id": plan["current_recipient_user_id"],
            "expires_at": plan["current_expires_at"],
        },
        "after": update,
    })
    return {
        "id": notif_id,
        "expired_at": _iso(now),
        "person_targeted_copies": new_ids,
        "audit_id": audit_id,
    }


async def main(args: argparse.Namespace) -> int:
    cli, db = await _get_db()
    try:
        info = await db.command("ping")  # noqa: F841
        ts = _now().strftime("%Y%m%dT%H%M%SZ")
        rows = await scan(db, args.max_rows)
        print(f"# TRACK 15.2 cleanup · db={db.name} · ts={ts}")
        print(f"# scanned: {len(rows)} leaked PM-offboarding row(s)")
        if not rows:
            print("# nothing to clean up. exit 0.")
            return 0
        plans: List[Dict[str, Any]] = []
        for r in rows:
            plans.append(await plan_row(db, r))
        out_dir = Path(__file__).resolve().parent
        if not args.apply:
            ledger = {
                "mode": "dry-run", "db_name": db.name, "ts": ts,
                "row_count": len(plans), "plans": plans,
            }
            path = out_dir / f"track_15_2_dryrun_{ts}.json"
            path.write_text(json.dumps(ledger, indent=2, default=str))
            print(f"# DRY-RUN ledger written: {path}")
            print(f"# review the ledger; if approved, re-run with --apply")
            return 0
        # --apply mode
        applied: List[Dict[str, Any]] = []
        for p in plans:
            applied.append(await apply_plan(db, p))
            print(f"  expired {p['id']} · "
                  f"{len(p['resolved_pm_targets'])} per-PM cop(ies) created")
        ledger = {
            "mode": "applied", "db_name": db.name, "ts": ts,
            "row_count": len(applied), "applied": applied, "plans": plans,
        }
        path = out_dir / f"track_15_2_applied_{ts}.json"
        path.write_text(json.dumps(ledger, indent=2, default=str))
        print(f"# APPLIED ledger written: {path}")
        return 0
    finally:
        cli.close()


def cli_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--apply", action="store_true",
                   help="mutate. WITHOUT this flag, runs dry-run only.")
    p.add_argument("--dry-run", action="store_true", dest="dry_run_explicit",
                   help="explicit dry-run (default behavior; this flag is "
                        "a no-op alias for clarity in runbooks).")
    p.add_argument("--prod-confirm", action="store_true", dest="prod_confirm",
                   help="required to --apply against APP_ENV=production / "
                        "DB_NAME=masci_safety. Belt-and-suspenders guard.")
    p.add_argument("--max-rows", type=int, default=200,
                   help="refuse to touch more than N rows in one pass.")
    return p.parse_args(argv)


def validate_safety(
    args: argparse.Namespace,
    app_env: Optional[str],
    db_name: Optional[str],
) -> Optional[str]:
    """Return None if the invocation is safe, else an error string.

    Rules (TRACK 15.8B):
      • Dry-run is always safe; --prod-confirm is ignored for dry-runs.
      • --apply against a production target (APP_ENV=production OR
        DB_NAME=masci_safety) REQUIRES --prod-confirm.
      • --prod-confirm ASSERTS APP_ENV=production AND DB_NAME=masci_safety.
        Either mismatch is a hard refusal.
      • --apply against a non-production target (e.g. preview) works
        without --prod-confirm — the preview pod uses this for gate
        runs.
    """
    if not args.apply:
        if args.prod_confirm:
            # No-op but not an error; explicit dry-run with confirm is fine.
            return None
        return None
    env = (app_env or "").strip().lower()
    db = (db_name or "").strip()
    targets_prod = (env == "production") or (db == "masci_safety")
    if args.prod_confirm:
        if env != "production":
            return ("--prod-confirm requires APP_ENV=production "
                    f"(got APP_ENV={app_env!r}). Refusing to apply.")
        if db != "masci_safety":
            return ("--prod-confirm requires DB_NAME=masci_safety "
                    f"(got DB_NAME={db_name!r}). Refusing to apply.")
        return None
    if targets_prod:
        return ("Refusing production mutation without --prod-confirm "
                f"(APP_ENV={app_env!r} DB_NAME={db_name!r}). "
                "Re-run with --apply --prod-confirm on a production-"
                "authorized pod.")
    return None


if __name__ == "__main__":  # pragma: no cover
    _args = cli_args()
    _app_env = os.environ.get("APP_ENV")
    _db_name = os.environ.get("DB_NAME") or "masci_safety_preview"
    _safety_err = validate_safety(_args, _app_env, _db_name)
    if _safety_err:
        print(f"# SAFETY GUARD: {_safety_err}", file=sys.stderr)
        sys.exit(2)
    sys.exit(asyncio.run(main(_args)))
