"""
prod_smoke_cleanup_pass2.py — Idempotent cleanup of any leftover
RC1-LIVE-VERIFY data in production.

Run after the smoke certification to guarantee zero residue.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

API = "https://mascidocs.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TAG = "RC1-LIVE-VERIFY"


def login() -> str:
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


def main() -> int:
    tok = login()
    h = {"X-Admin-Token": tok}
    actions = []
    print(f"=== CLEANUP PASS 2 @ {API} ===\n")

    # 1) Find all jobs whose project_number / project_name contains our TAG
    r = requests.get(f"{API}/api/admin/jobs", headers=h, timeout=30)
    jobs_body = r.json() if r.status_code == 200 else {}
    items = jobs_body.get("items", []) if isinstance(jobs_body, dict) else jobs_body
    target_jobs = [j for j in items
                   if TAG in (j.get("project_number") or "")
                   or TAG in (j.get("project_name") or "")
                   or TAG.lower() in (j.get("project_number") or "").lower()
                   or TAG.lower() in (j.get("project_name") or "").lower()]
    print(f"Jobs with TAG: {len(target_jobs)}")
    for j in target_jobs:
        jid = j.get("id")
        pn = j.get("project_number")
        # Step 1a: remove any active staffing assignments first
        rr = requests.get(f"{API}/api/admin/jobs/{pn}/team", headers=h, timeout=30)
        if rr.status_code == 200:
            roster = (rr.json() or {}).get("items", [])
            for r2 in roster:
                if not r2.get("active"):
                    continue
                rd = requests.delete(
                    f"{API}/api/admin/jobs/{pn}/team/{r2['id']}",
                    headers=h, params={"reason": f"{TAG} pass-2 cleanup"},
                    timeout=30,
                )
                actions.append({"kind": "staffing_assignment",
                                 "id": r2["id"], "pn": pn,
                                 "status": rd.status_code})
                print(f"  ✓ DELETE staffing {r2['id']} on {pn} → {rd.status_code}")
        # Step 1b: archive/delete the job (DELETE by id — soft delete)
        rj = requests.delete(f"{API}/api/admin/jobs/{jid}", headers=h, timeout=30)
        actions.append({"kind": "job", "id": jid, "pn": pn, "status": rj.status_code})
        print(f"  ✓ DELETE job id={jid} pn={pn} → {rj.status_code}")

    # 2) Find all directory users whose email contains rc1-live-verify
    r = requests.get(f"{API}/api/admin/directory?q=rc1-live-verify", headers=h, timeout=30)
    target_users = []
    if r.status_code == 200:
        for u in (r.json() or {}).get("users", []):
            em = (u.get("email") or "").lower()
            nm = (u.get("name") or "").lower()
            if "rc1-live-verify" in em or "rc1-live-verify" in nm or TAG.lower() in em or TAG.lower() in nm:
                target_users.append(u)
    print(f"\nUsers with TAG: {len(target_users)}")
    for u in target_users:
        ru = requests.delete(f"{API}/api/admin/directory/{u['id']}", headers=h, timeout=30)
        actions.append({"kind": "directory_user", "id": u["id"],
                        "email": u["email"], "status": ru.status_code})
        print(f"  ✓ DELETE user {u['email']} ({u['id']}) → {ru.status_code}")

    # 3) Daily reports — frozen by constitutional immutability.
    # Report the leftover DR doc_id(s) honestly.
    r = requests.get(f"{API}/api/daily-reports?project_number=", headers=h, timeout=30)
    leftover_drs = []
    if r.status_code == 200:
        for dr in (r.json() or []):
            label = (dr.get("project_name") or "") + " " + (dr.get("prepared_by") or "") + " " + (dr.get("project_number") or "")
            if TAG in label:
                leftover_drs.append({"id": dr.get("id"),
                                     "doc_id": dr.get("doc_id"),
                                     "project_number": dr.get("project_number"),
                                     "prepared_by": dr.get("prepared_by"),
                                     "report_date": dr.get("report_date")})
    print(f"\nDaily reports with TAG (immutable): {len(leftover_drs)}")
    for dr in leftover_drs:
        print(f"  • {dr['doc_id']} pn={dr['project_number']} date={dr['report_date']}")

    # Post-cleanup audit
    r = requests.get(f"{API}/api/admin/jobs", headers=h, timeout=30)
    remaining_jobs = []
    body = r.json()
    items = body.get("items", []) if isinstance(body, dict) else body
    remaining_jobs = [j for j in items if TAG in (j.get("project_number") or "")
                      or TAG in (j.get("project_name") or "")]

    r = requests.get(f"{API}/api/admin/directory?q=rc1-live-verify", headers=h, timeout=30)
    rem_users = []
    if r.status_code == 200:
        for u in (r.json() or {}).get("users", []):
            em = (u.get("email") or "").lower()
            if "rc1-live-verify" in em:
                rem_users.append(u)

    print(f"\n=== POST-CLEANUP AUDIT ===")
    print(f"Remaining jobs with TAG: {len(remaining_jobs)}")
    print(f"Remaining directory users with TAG: {len(rem_users)}")
    print(f"Daily reports with TAG (immutable, expected ≥ 1): {len(leftover_drs)}")

    out = {
        "api": API, "tag": TAG,
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actions": actions,
        "remaining_jobs": remaining_jobs,
        "remaining_directory_users": rem_users,
        "immutable_daily_reports": leftover_drs,
    }
    Path("/app/test_reports/rc1_live_prod_cleanup_pass2.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(f"\nWrote /app/test_reports/rc1_live_prod_cleanup_pass2.json")
    return 0 if len(remaining_jobs) == 0 and len(rem_users) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
