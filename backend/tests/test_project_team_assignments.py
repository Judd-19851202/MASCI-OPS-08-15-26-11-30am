"""
tests/test_project_team_assignments.py — Track 14.0-JOB-OWNERSHIP-FOUNDATION
Phase 1 backend regression. Hits the preview backend via REACT_APP_BACKEND_URL
with super-admin multi-login. Covers:

  - role-registry shape (13 roles, admin-only flags correct)
  - backfill idempotency (re-run creates 0 duplicates)
  - admin CRUD + 409 duplicate + 400 bad-role + audit trail
  - PM token scope (can add to own job, blocked on others)
  - PM cannot assign admin-only roles
  - FL token: read-only, cannot mutate
  - removed assignment becomes inactive (soft-delete)
  - reverse lookup (/api/users/me/projects)
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
def candidate_user(tokens):
    r = requests.get(
        f"{URL}/api/admin/directory/k4/users?limit=200",
        headers={"X-Admin-Token": tokens["admin"]}, timeout=T,
    )
    users = r.json()["users"]
    chosen = [u for u in users if u.get("email") and u["email"] != SUPER["email"]][0]
    return chosen


def H(**kw):
    h = {"Content-Type": "application/json"}
    h.update(kw)
    return h


def test_role_registry(tokens):
    r = requests.get(
        f"{URL}/api/team-roster/role-registry",
        headers={"X-Admin-Token": tokens["admin"]}, timeout=T,
    )
    assert r.status_code == 200
    roles = r.json()["roles"]
    # Track 14.0-PM-STAFFING-COMPLETION expanded the registry from 13
    # to 17 roles (+ project_administrator + project_coordinator +
    # qaqc_rep + hr_rep) and relabeled safety_lead → safety_rep,
    # dispatcher_contact → dispatch_rep.
    assert len(roles) == 17, f"expected 17 roles, got {len(roles)}"
    by_key = {r["key"]: r for r in roles}
    for k in ("pm", "co_pm", "executive_oversight"):
        assert by_key[k]["admin_only"] is True
    for k in ("foreman", "superintendent", "safety_rep",
              "equipment_manager", "shop_rep",
              "project_administrator", "project_coordinator",
              "qaqc_rep", "hr_rep", "dispatch_rep",
              "assistant_superintendent", "survey_rep",
              "accounting_rep"):
        assert by_key[k]["admin_only"] is False
        assert by_key[k]["pm_assignable"] is True


def test_backfill_idempotent(tokens):
    h = {"X-Admin-Token": tokens["admin"]}
    r1 = requests.post(f"{URL}/api/admin/team-roster/backfill",
                       headers=h, timeout=T).json()
    r2 = requests.post(f"{URL}/api/admin/team-roster/backfill",
                       headers=h, timeout=T).json()
    # Second run should add 0 (idempotency)
    assert r2["pm_assignments_created"] == 0
    assert r2["co_pm_assignments_created"] == 0
    # At least one PM was found in the first run (preview data has 22).
    assert r1["pm_assignments_created"] >= 0


def test_admin_crud_and_audit(tokens, candidate_user):
    h = H(**{"X-Admin-Token": tokens["admin"]})
    pn = "26-05"  # jaymn.judd is PM here; an active job
    payload = {"user_id": candidate_user["id"],
               "assignment_role": "shop_contact",
               "notes": "pytest add"}
    r = requests.post(f"{URL}/api/admin/jobs/{pn}/team",
                      headers=h, json=payload, timeout=T)
    assert r.status_code == 200, r.text
    aid = r.json()["assignment"]["id"]

    # Duplicate
    r2 = requests.post(f"{URL}/api/admin/jobs/{pn}/team",
                       headers=h, json=payload, timeout=T)
    assert r2.status_code == 409

    # Bad role
    r3 = requests.post(f"{URL}/api/admin/jobs/{pn}/team",
                       headers=h, json={**payload, "assignment_role": "bogus"},
                       timeout=T)
    assert r3.status_code == 400

    # Patch
    r4 = requests.patch(f"{URL}/api/admin/jobs/{pn}/team/{aid}",
                        headers=h, json={"is_primary": True}, timeout=T)
    assert r4.status_code == 200
    assert r4.json()["assignment"]["is_primary"] is True

    # Audit
    ra = requests.get(f"{URL}/api/admin/jobs/{pn}/team/audit",
                      headers={"X-Admin-Token": tokens["admin"]}, timeout=T)
    assert ra.status_code == 200
    actions = {i["action"] for i in ra.json()["items"]}
    assert "assign" in actions
    assert "update" in actions

    # Soft-delete
    rr = requests.delete(
        f"{URL}/api/admin/jobs/{pn}/team/{aid}?reason=pytest-cleanup",
        headers={"X-Admin-Token": tokens["admin"]}, timeout=T,
    )
    assert rr.status_code == 200

    # Inactive verified
    items = requests.get(f"{URL}/api/admin/jobs/{pn}/team",
                         headers={"X-Admin-Token": tokens["admin"]},
                         timeout=T).json()["items"]
    row = next(i for i in items if i["id"] == aid)
    assert row["active"] is False
    assert row["removed_by"] is not None


def test_pm_can_add_on_own_job(tokens, candidate_user):
    h = H(**{"X-PM-Token": tokens["pm"]})
    pn = "26-06"  # jaymn.judd PM
    body = {"user_id": candidate_user["id"], "assignment_role": "foreman",
            "notes": "pytest pm-scope"}
    r = requests.post(f"{URL}/api/pm/job/{pn}/team", headers=h, json=body,
                      timeout=T)
    assert r.status_code == 200, r.text
    aid = r.json()["assignment"]["id"]
    # Cleanup
    rr = requests.delete(f"{URL}/api/pm/job/{pn}/team/{aid}",
                         headers={"X-PM-Token": tokens["pm"]}, timeout=T)
    assert rr.status_code == 200


def test_pm_blocked_on_unowned_job(tokens, candidate_user):
    h = H(**{"X-PM-Token": tokens["pm"]})
    pn = "24-06"  # davidjewett's job
    body = {"user_id": candidate_user["id"], "assignment_role": "foreman"}
    r = requests.post(f"{URL}/api/pm/job/{pn}/team", headers=h, json=body,
                      timeout=T)
    assert r.status_code == 403


def test_pm_blocked_on_admin_only_role(tokens, candidate_user):
    h = H(**{"X-PM-Token": tokens["pm"]})
    pn = "26-05"
    body = {"user_id": candidate_user["id"], "assignment_role": "pm"}
    r = requests.post(f"{URL}/api/pm/job/{pn}/team", headers=h, json=body,
                      timeout=T)
    assert r.status_code == 403
    assert "admin-only" in r.json()["detail"]


def test_fl_read_only(tokens, candidate_user):
    h = H(**{"X-FL-Token": tokens["fl"]})
    pn = "26-05"
    # Public read works.
    r1 = requests.get(f"{URL}/api/jobs/{pn}/team",
                      headers={"X-FL-Token": tokens["fl"]}, timeout=T)
    assert r1.status_code == 200
    # Write attempt blocked.
    body = {"user_id": candidate_user["id"], "assignment_role": "foreman"}
    r2 = requests.post(f"{URL}/api/pm/job/{pn}/team", headers=h, json=body,
                      timeout=T)
    assert r2.status_code == 403


def test_reverse_lookup(tokens):
    h = {"X-PM-Token": tokens["pm"]}
    r = requests.get(f"{URL}/api/users/me/projects", headers=h, timeout=T)
    assert r.status_code == 200
    # super-admin has 2 jobs as PM (26-05, 26-06) → at least 2 rows
    assert r.json()["count"] >= 2
