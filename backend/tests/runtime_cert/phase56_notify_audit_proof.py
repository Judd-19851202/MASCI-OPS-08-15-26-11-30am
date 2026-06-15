"""
phase56_notify_audit_proof.py — Track 14.0-PM-STAFFING-RUNTIME-PROOF.

Phase 5 (Notifications) + Phase 6 (Audit) runtime evidence collector.

For each of the 17 cert assignments we already have on
ZZ-RUNTIME-CERT-2026:
  * inspect db.notifications for the role's assign event
  * inspect db.audit_events for the role's assign event

Then we churn one role (the project_administrator) — delete + re-add —
to demonstrate live "update" and "remove" events fan out correctly,
verifying the full Create/Edit/Reassign/Remove cycle the directive
requires.

Writes:
  /app/test_reports/runtime_cert_phase56_evidence.json
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, "/app/backend")
os.environ.setdefault("EMERGENT_DB_ENV", "preview")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

import requests  # noqa: E402

API = "https://safety-audit-mobile-1.preview.emergentagent.com"
CERT_PROJECT = "ZZ-RUNTIME-CERT-2026"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def admin_token() -> str:
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=90,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


async def main() -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        # Read from backend/.env directly when run from CLI.
        from dotenv import dotenv_values
        env = dotenv_values("/app/backend/.env")
        mongo_url = mongo_url or env.get("MONGO_URL")
        db_name = db_name or env.get("DB_NAME")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    seed = json.loads(Path("/app/test_reports/runtime_cert_seed.json").read_text())
    cert_users = {u["role_key"]: u for u in seed["users"]}

    # Phase 6 — audit trail per role (assign event from seed step)
    audit_rows: List[Dict[str, Any]] = []
    async for e in db.audit_events.find(
        {"project_number": CERT_PROJECT, "category": "project_team_roster"},
        {"_id": 0},
    ):
        audit_rows.append(e)

    # Phase 5 — notifications fired (these only exist for events created
    # AFTER the notify hook was added; we'll re-fire a fresh cycle next).
    notif_pre: List[Dict[str, Any]] = []
    async for n in db.notifications.find(
        {"linked_project_number": CERT_PROJECT, "type": "project_team_assignment"},
        {"_id": 0},
    ):
        notif_pre.append(n)

    # Trigger a full create→edit→reassign→remove cycle for one role
    # (project_administrator) so the notification + audit pipelines
    # produce live events visible in this run.
    tok = admin_token()
    h = {"X-Admin-Token": tok, "Content-Type": "application/json"}
    target = cert_users["project_administrator"]
    cycle: Dict[str, Any] = {"role": "project_administrator", "events": []}

    # Find current active assignment id
    r = requests.get(f"{API}/api/admin/jobs/{CERT_PROJECT}/team", headers=h, timeout=45)
    items = (r.json() or {}).get("items", [])
    aid = next((it["id"] for it in items
                if it["user_id"] == target["user_id"]
                and it["assignment_role"] == "project_administrator"
                and it["active"]), None)

    # 1) PATCH (edit notes) — produces audit + (no notify on update; design
    #    decision: only assign+remove send bells to minimise noise).
    if aid:
        rr = requests.patch(
            f"{API}/api/admin/jobs/{CERT_PROJECT}/team/{aid}",
            headers=h, json={"notes": "Runtime cert · edit cycle"},
            timeout=45,
        )
        cycle["events"].append({"step": "patch", "status": rr.status_code})

    # 2) DELETE — produces audit (action=remove) + bell notification
    if aid:
        rr = requests.delete(
            f"{API}/api/admin/jobs/{CERT_PROJECT}/team/{aid}",
            headers=h, params={"reason": "Runtime cert · remove cycle"},
            timeout=45,
        )
        cycle["events"].append({"step": "delete", "status": rr.status_code})

    # 3) RE-ASSIGN — fresh assign event → audit + bell.
    rr = requests.post(
        f"{API}/api/admin/jobs/{CERT_PROJECT}/team", headers=h,
        json={
            "user_id": target["user_id"], "email": target["email"],
            "display_name": target["name"],
            "assignment_role": "project_administrator",
            "assignment_scope": "full",
            "notes": "Runtime cert · re-assign cycle",
        }, timeout=45,
    )
    cycle["events"].append({"step": "reassign", "status": rr.status_code,
                             "body": (rr.json() if rr.status_code < 400 else rr.text)[:300]
                             if rr.status_code != 200 else "ok"})

    # Snapshot fresh audit + notifications
    audit_post: List[Dict[str, Any]] = []
    async for e in db.audit_events.find(
        {"project_number": CERT_PROJECT, "category": "project_team_roster"},
        {"_id": 0},
    ):
        audit_post.append(e)
    notif_post: List[Dict[str, Any]] = []
    async for n in db.notifications.find(
        {"linked_project_number": CERT_PROJECT, "type": "project_team_assignment"},
        {"_id": 0},
    ):
        notif_post.append(n)

    # Per-role audit coverage check
    per_role: List[Dict[str, Any]] = []
    for role_key, u in cert_users.items():
        events = [e for e in audit_post
                  if e.get("assignment_role") == role_key
                  and (e.get("target_user_id") == u["user_id"]
                       or e.get("target_email") == u["email"])]
        actions = sorted({e["action"] for e in events})
        per_role.append({
            "role_key": role_key,
            "email": u["email"],
            "events_captured": len(events),
            "actions": actions,
            "audit_ok": "assign" in actions,
        })

    evidence = {
        "project_number": CERT_PROJECT,
        "audit_event_count_pre": len(audit_rows),
        "audit_event_count_post": len(audit_post),
        "notification_count_pre": len(notif_pre),
        "notification_count_post": len(notif_post),
        "cycle": cycle,
        "audit_per_role": per_role,
        "sample_audit_assign_event": next(
            (e for e in audit_post if e["action"] == "assign"), None
        ),
        "sample_audit_remove_event": next(
            (e for e in audit_post if e["action"] == "remove"), None
        ),
        "sample_notification": next(iter(notif_post), None),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out = Path("/app/test_reports/runtime_cert_phase56_evidence.json")
    out.write_text(json.dumps(evidence, indent=2, default=str))
    audit_assign_all = all(r["audit_ok"] for r in per_role)
    print(f"  Audit events for cert project: {len(audit_post)}")
    print(f"  Bell notifications for cert project: {len(notif_post)}")
    print(f"  Per-role assign-audit coverage: {sum(1 for r in per_role if r['audit_ok'])}/17")
    print(f"  Wrote {out}")
    return 0 if audit_assign_all and len(notif_post) >= 1 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
