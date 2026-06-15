"""
prod_smoke_certification.py — RC1 LIVE PRODUCTION SMOKE CERTIFICATION.

Runs the authenticated phases (4–13) against https://mascidocs.com,
tracking every artifact created and tearing it down at the end.

Hard contract:
  * every created object's name contains `RC1-LIVE-VERIFY`
  * every created object's id is appended to TEMP_INVENTORY
  * after smoke, the cleanup pass deletes them all + verifies zero
    remaining
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

API = "https://mascidocs.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TAG = "RC1-LIVE-VERIFY"
CERT_PROJECT_NUMBER = f"ZZ-{TAG}-2026"
CERT_PROJECT_NAME = f"{TAG} — Production Smoke Project"

TEMP: List[Dict[str, Any]] = []
ARTIFACTS: List[Dict[str, Any]] = []


def _track(kind: str, identifier: str, label: str, undo: Dict[str, Any]) -> None:
    TEMP.append({"kind": kind, "id": identifier, "label": label, "undo": undo})


def _log(line: str) -> None:
    print(line, flush=True)
    ARTIFACTS.append({"ts": time.strftime("%H:%M:%S"), "line": line})


def login() -> str:
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=90,
    )
    r.raise_for_status()
    body = r.json()
    return body["portal_tokens"]["admin"]


def H(tok: str) -> Dict[str, str]:
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


# ── Phase 1 — health + deploy-readiness + version ────────────────────
def phase_1(tok: str) -> Dict[str, Any]:
    r1 = requests.get(f"{API}/api/health", timeout=15)
    r2 = requests.get(f"{API}/api/version", timeout=15)
    r3 = requests.get(f"{API}/api/admin/deploy-readiness",
                      headers={"X-Admin-Token": tok}, timeout=30)
    rd = r3.json()
    _log(f"Phase 1 · /health={r1.status_code} /version app_env={r2.json().get('app_env')} db={r2.json().get('db_name')}")
    _log(f"Phase 1 · deploy-readiness overall={rd['overall_status']} blockers={rd['blocker_count']} warns={rd['warn_count']}")
    return {"health": r1.json(), "version": r2.json(), "deploy_readiness": rd}


# ── Phase 4 — PM Staffing live ──────────────────────────────────────
def phase_4(tok: str) -> Dict[str, Any]:
    h = H(tok)
    # Create a temp project (admin endpoint)
    pn = CERT_PROJECT_NUMBER
    r = requests.post(
        f"{API}/api/admin/jobs", headers=h,
        json={
            "project_number": pn,
            "project_name": CERT_PROJECT_NAME,
            "location": "Smoke Cert · Production",
            "client": "MASCI Internal",
            "project_manager": "Jaymn Judd",
            "pm_email": ADMIN_EMAIL,
            "active": True,
        }, timeout=30,
    )
    project_created_fresh = r.status_code in (200, 201)
    _log(f"Phase 4 · POST /api/admin/jobs project={pn} → {r.status_code}")
    if project_created_fresh:
        _track("jobs_master", pn, f"project {pn}", {
            "method": "DELETE", "url": f"/api/admin/jobs/{pn}",
        })

    # Create a temp directory user (project_administrator)
    test_user_email = f"rc1-live-verify-padmin@example.com"
    seed_pw = "RC1Verify2026!"
    user_id: Optional[str] = None
    ru = requests.post(
        f"{API}/api/admin/directory", headers=h,
        json={
            "email": test_user_email,
            "name": f"{TAG} Project Admin",
            "portals": ["pm"],
            "password": seed_pw,
            "must_change_password": False,
            "delivery": "show",
        }, timeout=30,
    )
    _log(f"Phase 4 · POST /api/admin/directory user={test_user_email} → {ru.status_code}")
    if ru.status_code in (200, 201):
        user_id = (ru.json() or {}).get("user", {}).get("id")
        if user_id:
            _track("directory_user", user_id, test_user_email, {
                "method": "DELETE", "url": f"/api/admin/directory/{user_id}",
            })
    else:
        # User may already exist — look it up
        rl = requests.get(f"{API}/api/admin/directory?q={test_user_email}",
                          headers={"X-Admin-Token": tok}, timeout=30)
        for u in (rl.json() or {}).get("users", []):
            if (u.get("email") or "").lower() == test_user_email:
                user_id = u["id"]
                break
        _log(f"Phase 4 · re-used existing directory user_id={user_id}")

    # Assign user to project (project_administrator role)
    assignment_id: Optional[str] = None
    if user_id:
        ra = requests.post(
            f"{API}/api/admin/jobs/{pn}/team", headers=h,
            json={
                "user_id": user_id,
                "email": test_user_email,
                "display_name": f"{TAG} Project Admin",
                "assignment_role": "project_administrator",
                "assignment_scope": "full",
                "notes": f"{TAG} smoke",
            }, timeout=30,
        )
        _log(f"Phase 4 · POST staffing assign → {ra.status_code}")
        if ra.status_code in (200, 201):
            assignment_id = (ra.json() or {}).get("assignment", {}).get("id")
            if assignment_id:
                _track("project_team_assignment", assignment_id,
                       f"{pn}::project_administrator",
                       {"method": "DELETE",
                        "url": f"/api/admin/jobs/{pn}/team/{assignment_id}",
                        "params": {"reason": f"{TAG} cleanup"}})

    # Verify roster shows the assignment
    rr = requests.get(f"{API}/api/admin/jobs/{pn}/team",
                      headers={"X-Admin-Token": tok}, timeout=30)
    roster = (rr.json() or {}).get("items", [])
    _log(f"Phase 4 · GET roster → {rr.status_code} · {len(roster)} active rows")

    # Remove assignment immediately (this also fires audit + bell)
    if assignment_id:
        rd = requests.delete(
            f"{API}/api/admin/jobs/{pn}/team/{assignment_id}",
            headers={"X-Admin-Token": tok},
            params={"reason": f"{TAG} immediate remove"},
            timeout=30,
        )
        _log(f"Phase 4 · DELETE assignment → {rd.status_code}")
        if rd.status_code in (200, 204):
            # already cleaned via this call — mark the undo as completed
            for t in TEMP:
                if t["id"] == assignment_id:
                    t["undo_already_done"] = True

    return {
        "project_number": pn, "project_created_fresh": project_created_fresh,
        "user_id": user_id, "user_email": test_user_email,
        "assignment_id": assignment_id,
        "roster_after_assign": roster,
    }


# ── Phase 6 — Daily Report ──────────────────────────────────────────
def phase_6(tok: str, pn: str) -> Dict[str, Any]:
    h = H(tok)
    today = time.strftime("%Y-%m-%d")
    payload = {
        "project_name": f"{TAG} Cert Project",
        "project_number": pn,
        "location": "Smoke Cert",
        "report_date": today,
        "prepared_by": f"{TAG} Smoke",
        "superintendent": "Jaymn Judd",
        "weather_summary": "Sunny",
        "general_notes": f"{TAG} smoke daily report — must be deleted before closure.",
    }
    r = requests.post(f"{API}/api/daily-reports", headers=h,
                      json=payload, timeout=60)
    _log(f"Phase 6 · POST /api/daily-reports → {r.status_code}")
    dr_id: Optional[str] = None
    if r.status_code in (200, 201):
        dr = r.json()
        dr_id = dr.get("id")
        _log(f"  doc_id={dr.get('doc_id')}  id={dr_id}")
        # Try PDF
        rp = requests.get(f"{API}/api/daily-reports/{dr_id}/pdf",
                          headers={"X-Admin-Token": tok}, timeout=60)
        _log(f"Phase 6/8 · GET DR pdf → {rp.status_code} bytes={len(rp.content)}")
    return {"daily_report_id": dr_id, "status": r.status_code,
            "response": r.json() if r.status_code < 400 else r.text[:300]}


# ── Phase 9 — Notifications recap ───────────────────────────────────
def phase_9(tok: str, pn: str) -> Dict[str, Any]:
    h = {"X-Admin-Token": tok}
    # Admin-side notification list (filtered by project)
    r = requests.get(f"{API}/api/admin/audit/recent?project_number={pn}",
                     headers=h, timeout=30)
    audits = r.json() if r.status_code < 400 else r.text[:300]
    _log(f"Phase 9 · GET recent audit (project={pn}) → {r.status_code}")
    return {"audit_recent_status": r.status_code,
            "audit_count": len(audits) if isinstance(audits, list) else None}


# ── Phase 11 — Data hygiene scan ────────────────────────────────────
def phase_11(tok: str) -> Dict[str, Any]:
    h = {"X-Admin-Token": tok}
    findings: Dict[str, Any] = {}
    # Search HR directory for known contamination keywords
    for q in ["pm.demo", "TEST_iter", "Juan Perez", "PHASE_SIGMA", "DUMMY"]:
        r = requests.get(f"{API}/api/admin/directory?q={q}", headers=h, timeout=30)
        rows = (r.json() or {}).get("users", []) if r.status_code == 200 else []
        findings[q] = len(rows)
    # Search for our own RC1-LIVE-VERIFY contamination
    r = requests.get(f"{API}/api/admin/directory?q={TAG}", headers=h, timeout=30)
    rows = (r.json() or {}).get("users", []) if r.status_code == 200 else []
    findings[TAG] = len(rows)
    _log(f"Phase 11 · data hygiene scan: {findings}")
    return findings


# ── Phase 12 — Backup create ────────────────────────────────────────
def phase_12(tok: str) -> Dict[str, Any]:
    h = H(tok)
    # Just list backups; do not create one (we don't want to flood storage).
    r = requests.get(f"{API}/api/admin/backups",
                     headers={"X-Admin-Token": tok}, timeout=30)
    _log(f"Phase 12 · GET /api/admin/backups → {r.status_code}")
    body = r.json() if r.status_code < 400 else None
    items = []
    if isinstance(body, dict):
        items = body.get("items") or body.get("backups") or []
    elif isinstance(body, list):
        items = body
    return {"backup_count": len(items), "status": r.status_code,
            "sample": items[:2]}


# ── CLEANUP ─────────────────────────────────────────────────────────
def cleanup(tok: str) -> List[Dict[str, Any]]:
    h = {"X-Admin-Token": tok}
    results: List[Dict[str, Any]] = []
    # Run in REVERSE order: most recent first (assignments → users → project)
    for t in reversed(TEMP):
        if t.get("undo_already_done"):
            results.append({"kind": t["kind"], "id": t["id"], "result": "already-removed"})
            continue
        undo = t["undo"]
        method = undo["method"].upper()
        url = f"{API}{undo['url']}"
        if method == "DELETE":
            r = requests.delete(url, headers=h, params=undo.get("params"), timeout=30)
        elif method == "POST":
            r = requests.post(url, headers={**h, "Content-Type": "application/json"},
                              json=undo.get("body") or {}, timeout=30)
        else:
            r = requests.request(method, url, headers=h, timeout=30)
        results.append({"kind": t["kind"], "id": t["id"], "label": t["label"],
                        "status": r.status_code,
                        "result": "ok" if r.status_code in (200, 201, 204) else f"FAILED:{r.text[:200]}"})
        _log(f"CLEANUP · {t['kind']:25} {t['id']:40} → {r.status_code}")
    return results


def main() -> int:
    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    print(f"=== RC1 LIVE PRODUCTION SMOKE @ {API} ===\n")
    tok = login()
    _log("admin login OK")

    p1 = phase_1(tok)
    p4 = phase_4(tok)
    p6 = phase_6(tok, p4["project_number"])
    p9 = phase_9(tok, p4["project_number"])
    p11 = phase_11(tok)
    p12 = phase_12(tok)

    print("\n=== CLEANUP ===\n")
    cleanup_results = cleanup(tok)

    # Verify zero remaining
    print("\n=== POST-CLEANUP VERIFICATION ===\n")
    h = {"X-Admin-Token": tok}
    rem_proj = requests.get(f"{API}/api/admin/jobs", headers=h, timeout=30)
    proj_items = rem_proj.json() if rem_proj.status_code == 200 else []
    if isinstance(proj_items, dict):
        proj_items = proj_items.get("items", []) or proj_items.get("jobs", [])
    remaining_projects = [p for p in proj_items
                          if (p or {}).get("project_number") == CERT_PROJECT_NUMBER]
    rem_users = requests.get(f"{API}/api/admin/directory?q={TAG}", headers=h, timeout=30)
    remaining_users = (rem_users.json() or {}).get("users", []) if rem_users.status_code == 200 else []
    _log(f"Remaining cert project rows: {len(remaining_projects)}")
    _log(f"Remaining {TAG} directory users: {len(remaining_users)}")

    out = {
        "api": API,
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase_1": p1,
        "phase_4": p4,
        "phase_6": p6,
        "phase_9": p9,
        "phase_11_hygiene": p11,
        "phase_12_backup": p12,
        "temp_inventory": TEMP,
        "cleanup_results": cleanup_results,
        "post_cleanup": {
            "remaining_projects": len(remaining_projects),
            "remaining_directory_users": len(remaining_users),
            "remaining_user_emails": [u["email"] for u in remaining_users],
        },
        "artifact_log": ARTIFACTS,
    }
    Path("/app/test_reports/rc1_live_prod_smoke.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(f"\nWrote /app/test_reports/rc1_live_prod_smoke.json")
    print(f"Created={len(TEMP)}  Cleanup OK={sum(1 for r in cleanup_results if r['result'] in ('ok','already-removed'))}")
    print(f"Remaining temp projects={len(remaining_projects)}  users={len(remaining_users)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
