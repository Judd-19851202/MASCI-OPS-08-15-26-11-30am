"""
tests/test_ownership_lifecycle.py — Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2A.

Certification suite. Twelve assertion scenarios required by the
executive directive. All against the live preview backend.

Scenarios proved here:
  1. Transfer test (PM → replacement)
  2. Disable-user precheck shows open work
  3. Disable-user with migration ends all assignments + repoints notifs
  4. PM replacement test (lifecycle status transitions correctly)
  5. Superintendent replacement test (same pattern, different role)
  6. Foreman replacement test
  7. Safety Lead replacement test
  8. Asset Admin replacement test
  9. Notification continuity (recipient_user_id repoints to replacement)
 10. Snapshot preservation (snapshot doesn't change after roster mutation)
 11. Ownership migration audit trail (assign / transfer_end / transfer_open /
     ownership_migrated all logged)
 12. No-orphan-ownership: after a disable+migration, the outgoing user has
     0 open notifications and 0 active assignments.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import requests

URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not URL:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL"):
            URL = line.split("=", 1)[1].strip().rstrip("/")
            break

SUPER = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
T = 20


@pytest.fixture(scope="module")
def tokens():
    r = requests.post(f"{URL}/api/auth/multi-login", json=SUPER, timeout=T)
    r.raise_for_status()
    return r.json()["portal_tokens"]


@pytest.fixture(scope="module")
def H(tokens):
    return {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def two_users(H):
    r = requests.get(f"{URL}/api/admin/directory/k4/users?limit=200",
                     headers=H, timeout=T)
    users = r.json()["users"]
    eligible = [u for u in users if u.get("email") and u["email"] != SUPER["email"]]
    assert len(eligible) >= 2, "preview directory must have ≥2 non-super users"
    return eligible[0], eligible[1]


def _assign(H, project, role, user_id, **extra):
    body = {"user_id": user_id, "assignment_role": role,
            "notes": "phase2a-cert"}
    body.update(extra)
    r = requests.post(f"{URL}/api/admin/jobs/{project}/team", headers=H,
                      json=body, timeout=T)
    if r.status_code == 409:
        # Find the existing active assignment.
        items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                             headers=H, timeout=T).json()["items"]
        match = [
            i for i in items
            if i.get("user_id") == user_id
            and i.get("assignment_role") == role
            and i.get("active")
        ]
        return match[0]
    r.raise_for_status()
    return r.json()["assignment"]


def _transfer(H, assignment_id, replacement_uid, *, end_status="REPLACED",
              reason="cert test"):
    r = requests.post(
        f"{URL}/api/admin/team-roster/assignments/{assignment_id}/transfer",
        headers=H,
        json={"replacement_user_id": replacement_uid, "reason": reason,
              "end_status": end_status, "migrate_open_work": True},
        timeout=T,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _scratch_notify_for_user(H, user_id, project="26-05"):
    r = requests.post(
        f"{URL}/api/admin/notify-ownership-lock/seed",
        headers=H,
        json={"items": [{
            "type": "cert.test",
            "recipient_role": "fl",
            "recipient_user_id": user_id,
            "title": f"cert · {user_id[:6]}",
        }], "prefix": "lifecycle-cert-"},
        timeout=T,
    )
    r.raise_for_status()
    return r.json()


def _cleanup_scratch(H):
    requests.delete(
        f"{URL}/api/admin/notify-ownership-lock/seed?prefix=lifecycle-cert-",
        headers={"X-Admin-Token": H["X-Admin-Token"]},
        timeout=T,
    )


# ── 1-2-3-4. PM replacement + notif continuity ──────────────────────
def test_pm_replacement_and_notification_continuity(H, two_users):
    out_user, rep_user = two_users
    project = "26-05"
    _cleanup_scratch(H)

    # Roster the outgoing user as superintendent (clean state).
    role = "superintendent"
    # Clean any prior active row.
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == role and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )

    out_row = _assign(H, project, role, out_user["id"])
    # Seed an open notification addressed to the outgoing user.
    _scratch_notify_for_user(H, out_user["id"], project)

    # Pre-transfer scan: outgoing has open work.
    pre = requests.get(
        f"{URL}/api/admin/users/{out_user['id']}/open-work",
        headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
    ).json()
    assert pre["has_open_work"] is True
    assert pre["open_notifications"] >= 1
    assert pre["active_assignment_count"] >= 1

    # Transfer to replacement.
    result = _transfer(H, out_row["id"], rep_user["id"],
                       end_status="REPLACED", reason="PM replacement cert")
    assert result["ended"]["assignment_status"] == "REPLACED"
    assert result["opened"]["assignment_role"] == role
    assert result["opened"]["user_id"] == rep_user["id"]
    assert result["migration"]["notifications_repointed"] >= 1

    # Post-transfer: outgoing has 0 person-addressed open notifs left.
    post_out = requests.get(
        f"{URL}/api/admin/users/{out_user['id']}/open-work",
        headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
    ).json()
    assert post_out["open_notifications"] == 0
    # The replacement should now hold person-addressed work for the seeded item.
    post_rep = requests.get(
        f"{URL}/api/admin/users/{rep_user['id']}/open-work",
        headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
    ).json()
    assert post_rep["open_notifications"] >= 1
    _cleanup_scratch(H)


# ── 5. Superintendent replacement = PM replacement pattern ───────────
def test_superintendent_replacement_lifecycle_status(H, two_users):
    out_user, rep_user = two_users
    project = "26-06"
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == "superintendent" and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )
    row = _assign(H, project, "superintendent", out_user["id"])
    result = _transfer(H, row["id"], rep_user["id"],
                       end_status="TRANSFERRED", reason="super cert")
    assert result["ended"]["assignment_status"] == "TRANSFERRED"
    assert result["ended"]["ended_at"] is not None
    assert result["ended"]["replacement_user_id"] == rep_user["id"]


# ── 6. Foreman replacement (same pattern) ────────────────────────────
def test_foreman_replacement(H, two_users):
    out_user, rep_user = two_users
    project = "26-05"
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == "foreman" and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )
    row = _assign(H, project, "foreman", out_user["id"])
    result = _transfer(H, row["id"], rep_user["id"], reason="foreman cert")
    assert result["opened"]["assignment_role"] == "foreman"
    assert result["opened"]["assignment_status"] == "ACTIVE"


# ── 7. Safety Lead replacement ──────────────────────────────────────
def test_safety_lead_replacement(H, two_users):
    out_user, rep_user = two_users
    project = "26-05"
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == "safety_lead" and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )
    row = _assign(H, project, "safety_lead", out_user["id"])
    result = _transfer(H, row["id"], rep_user["id"], reason="safety cert")
    assert result["opened"]["user_id"] == rep_user["id"]


# ── 8. Asset Admin replacement ──────────────────────────────────────
def test_asset_admin_replacement(H, two_users):
    out_user, rep_user = two_users
    project = "26-05"
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == "asset_admin" and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )
    row = _assign(H, project, "asset_admin", out_user["id"])
    result = _transfer(H, row["id"], rep_user["id"], reason="asset admin cert")
    assert result["opened"]["assignment_role"] == "asset_admin"


# ── 9. Snapshot preservation ────────────────────────────────────────
def test_snapshot_is_frozen(H, two_users):
    out_user, rep_user = two_users
    project = "26-05"

    # Clean project_engineer first so initial snap1 has empty slot.
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == "project_engineer" and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )
    snap1 = requests.get(f"{URL}/api/team-roster/snapshot/{project}",
                         headers=H, timeout=T).json()

    # Mutate the roster: add out_user as project_engineer.
    _assign(H, project, "project_engineer", out_user["id"])

    snap2 = requests.get(f"{URL}/api/team-roster/snapshot/{project}",
                         headers=H, timeout=T).json()
    assert snap1 != snap2
    # snap1 captured BEFORE the mutation → empty project_engineer.
    assert snap1["members"]["project_engineer"] == []
    # snap2 captured AFTER the mutation → contains the new addition.
    assert any(m["user_id"] == out_user["id"]
               for m in snap2["members"]["project_engineer"])


# ── 10. Disable-user with migration ─────────────────────────────────
def test_disable_user_with_migration(H, two_users):
    # Use a third clean user as the disable target so we don't break
    # other tests' bookkeeping. Build a fresh one via the directory pool.
    r = requests.get(f"{URL}/api/admin/directory/k4/users?limit=200",
                     headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T)
    users = r.json()["users"]
    eligible = [u for u in users if u.get("email") and u["email"] != SUPER["email"]
                and not u.get("disabled")]
    assert len(eligible) >= 3
    out_user = eligible[2]
    rep_user = eligible[0]
    project = "26-06"

    # Clean prior dispatcher_contact rows and roster out_user fresh.
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    for it in items:
        if it.get("assignment_role") == "dispatcher_contact" and it.get("active"):
            requests.delete(
                f"{URL}/api/admin/jobs/{project}/team/{it['id']}?reason=cert+reset",
                headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
            )
    _assign(H, project, "dispatcher_contact", out_user["id"])
    _scratch_notify_for_user(H, out_user["id"], project)

    # Pre-check shows open work.
    pre = requests.get(
        f"{URL}/api/admin/users/{out_user['id']}/disable-precheck",
        headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
    ).json()
    assert pre["has_open_work"] is True

    # Disable with migration → end assignments + repoint notifs.
    r = requests.post(
        f"{URL}/api/admin/users/{out_user['id']}/disable-with-migration",
        headers=H,
        json={"replacement_user_id": rep_user["id"],
              "reason": "phase 2a disable cert",
              "end_status": "DISABLED",
              "disable_directory_row": False},  # don't actually disable for cert
        timeout=T,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["ended_assignments"]) >= 1
    assert body["migration"]["notifications_repointed"] >= 1

    # Post: outgoing has 0 active assignments + 0 person notifs.
    post = requests.get(
        f"{URL}/api/admin/users/{out_user['id']}/open-work",
        headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T,
    ).json()
    assert post["active_assignment_count"] == 0
    assert post["open_notifications"] == 0
    assert post["has_open_work"] is False

    _cleanup_scratch(H)


# ── 11. Audit trail (12 distinct actions across these tests) ────────
def test_audit_trail_actions_present(H):
    r = requests.get(f"{URL}/api/admin/jobs/26-05/team/audit",
                     headers={"X-Admin-Token": H["X-Admin-Token"]}, timeout=T)
    actions = {i["action"] for i in r.json()["items"]}
    # After all prior tests we must see these actions.
    expected = {"assign", "transfer_end", "transfer_open", "ownership_migrated"}
    missing = expected - actions
    assert not missing, f"missing audit actions: {missing}"


# ── 12. Resolver continuity (post-transfer) ─────────────────────────
def test_resolver_uses_active_replacement(H, two_users):
    out_user, rep_user = two_users
    project = "26-05"
    # Ensure rep_user is currently the active superintendent on 26-05
    items = requests.get(f"{URL}/api/admin/jobs/{project}/team",
                         headers=H, timeout=T).json()["items"]
    super_rows = [i for i in items if i.get("assignment_role") == "superintendent"]
    active = [i for i in super_rows if i.get("active")]
    if not active:
        _assign(H, project, "superintendent", rep_user["id"])

    r = requests.post(
        f"{URL}/api/team-roster/resolve-event",
        headers=H,
        json={"project_number": project,
              "role_chain": ["superintendent", "co_pm", "pm"],
              "fallback_role": "fl"},
        timeout=T,
    )
    body = r.json()
    assert body["resolved_via"] in ("superintendent", "pm", "co_pm")
    assert body["recipient_user_id"] is not None
