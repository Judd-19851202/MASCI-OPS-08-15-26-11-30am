import os
import time
import uuid
from typing import Any, Dict, Optional

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

API = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com") + "/api"


def _call(method: str, url: str, **kwargs):
    last_exc = None
    for _ in range(3):
        try:
            return requests.request(method, url, **kwargs)
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(1)
    if last_exc:
        raise last_exc
    raise RuntimeError("request retry helper exhausted")


def _req(
    method: str,
    path: str,
    *,
    token: str,
    directory_token: str,
    body: Optional[Dict[str, Any]] = None,
    token_header: str = "X-Admin-Token",
) -> Dict[str, Any]:
    url = f"{API}{path}"
    headers = {
        "Content-Type": "application/json",
        token_header: token,
        "X-Directory-Token": directory_token,
    }
    try:
        resp = _call(method, url, headers=headers, json=body, timeout=30)
        try:
            payload = resp.json()
        except Exception:
            payload = {"detail": resp.text}
        return {"status": resp.status_code, "json": payload}
    except requests.HTTPError as e:
        payload = e.response.text if getattr(e, "response", None) else ""
        try:
            parsed = resp.json() if payload else {"detail": str(e)}
        except Exception:
            parsed = {"detail": payload or str(e)}
        return {"status": e.response.status_code if e.response else 500, "json": parsed}


@pytest.fixture(scope="module")
def auth_bundle():
    r = _call(
        "POST",
        f"{API}/auth/multi-login",
        json={
            "email": os.environ.get("SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com"),
            "password": os.environ.get("SUPER_ADMIN_PASS", "Maddix123!"),
        },
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    body = r.json()
    assert (body.get("portal_tokens") or {}).get("admin"), body
    assert body.get("session_token"), body
    return body


@pytest.fixture(scope="module")
def admin_token(auth_bundle):
    return auth_bundle["portal_tokens"]["admin"]


@pytest.fixture(scope="module")
def directory_token(auth_bundle):
    return auth_bundle["session_token"]


@pytest.fixture(scope="module")
def mongo_db():
    cfg = dotenv_values("/app/backend/.env")
    client = MongoClient(cfg["MONGO_URL"])
    return client[cfg["DB_NAME"]]


@pytest.fixture(scope="module")
def created_oa(admin_token, directory_token):
    body = {
        "title": "T-PYTEST · OA-1 scratch",
        "category": "truck_down",
        "priority": "high",
        "job_number": "JT-OPS-001",
        "job_name": "Pytest Job",
        "location": "Test Bay",
        "description": "Test fixture · created by test_oa1_operations_actions.py",
    }
    r = _req("POST", "/operations-actions", token=admin_token, directory_token=directory_token, body=body)
    assert r["status"] == 200, r
    assert r["json"]["oa_number"].startswith("OA-")
    return r["json"]


def test_invalid_token_rejected():
    r = _req("GET", "/operations-actions/summary", token="not-a-real-token", directory_token="bad-dir")
    assert r["status"] in (401, 403)


def test_directory_token_required(auth_bundle):
    token = auth_bundle["portal_tokens"]["admin"]
    r = _call(
        "GET",
        f"{API}/operations-actions",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    assert r.status_code in (401, 403)


def test_list_returns_shape(admin_token, directory_token):
    r = _req("GET", "/operations-actions", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    assert {"count", "total", "actions"}.issubset(r["json"].keys())
    first = (r["json"].get("actions") or [{}])[0]
    assert "history" not in first
    assert "notes" not in first
    assert "photos" not in first


def test_summary_returns_six_status_counts(admin_token, directory_token):
    r = _req("GET", "/operations-actions/summary", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    counts = r["json"]["counts"]
    assert set(counts.keys()) == {"open", "assigned", "in_progress", "waiting", "completed", "closed"}


def test_create_mints_oa_number_and_status_open(created_oa):
    assert created_oa["oa_number"].startswith("OA-")
    assert created_oa["status"] == "open"
    assert created_oa["history"][0]["kind"] == "created"
    assert created_oa["created_by"]["id"] != "admin"
    assert created_oa["created_by"].get("email")


def test_create_with_owner_assigns_immediately(admin_token, directory_token):
    owner = {"directory": "user_directory", "id": "admin", "name": "Admin", "email": ""}
    r = _req(
        "POST",
        "/operations-actions",
        token=admin_token,
        directory_token=directory_token,
        body={
            "title": "T-PYTEST · with owner",
            "category": "utility_conflict",
            "priority": "normal",
            "description": "",
            "owner": owner,
        },
    )
    assert r["status"] == 200
    assert r["json"]["status"] == "assigned"
    assert r["json"]["current_owner"]["id"] == "admin"


def test_create_invalid_category_rejected(admin_token, directory_token):
    r = _req(
        "POST",
        "/operations-actions",
        token=admin_token,
        directory_token=directory_token,
        body={"title": "bad", "category": "not_a_category", "priority": "normal"},
    )
    assert r["status"] == 422


def test_create_invalid_priority_rejected(admin_token, directory_token):
    r = _req(
        "POST",
        "/operations-actions",
        token=admin_token,
        directory_token=directory_token,
        body={"title": "bad", "category": "other", "priority": "ULTRA"},
    )
    assert r["status"] == 422


def test_read_existing(admin_token, directory_token, created_oa):
    r = _req("GET", f"/operations-actions/{created_oa['id']}", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    assert r["json"]["id"] == created_oa["id"]


def test_read_missing_returns_404(admin_token, directory_token):
    r = _req("GET", "/operations-actions/does-not-exist", token=admin_token, directory_token=directory_token)
    assert r["status"] == 404


def test_patch_updates_fields_and_appends_history(admin_token, directory_token, created_oa):
    r = _req(
        "PATCH",
        f"/operations-actions/{created_oa['id']}",
        token=admin_token,
        directory_token=directory_token,
        body={"priority": "critical", "location": "Updated bay"},
    )
    assert r["status"] == 200
    assert r["json"]["priority"] == "critical"
    assert r["json"]["location"] == "Updated bay"
    assert any(h["kind"] == "updated" for h in r["json"]["history"])


def test_assign_flips_open_to_assigned(admin_token, directory_token, created_oa):
    r = _req(
        "POST",
        f"/operations-actions/{created_oa['id']}/assign",
        token=admin_token,
        directory_token=directory_token,
        body={"owner": {"directory": "user_directory", "id": "admin", "name": "Admin", "email": ""}},
    )
    assert r["status"] == 200
    assert r["json"]["current_owner"]["id"] == "admin"
    assert r["json"]["status"] == "assigned"


def test_assign_invalid_directory_rejected(admin_token, directory_token, created_oa):
    r = _req(
        "POST",
        f"/operations-actions/{created_oa['id']}/assign",
        token=admin_token,
        directory_token=directory_token,
        body={"owner": {"directory": "not_a_directory", "id": "x"}},
    )
    assert r["status"] == 422


def test_status_progression_full_cycle(admin_token, directory_token):
    body = {
        "title": "T-CYCLE",
        "category": "other",
        "priority": "low",
        "owner": {"directory": "user_directory", "id": "admin", "name": "Admin", "email": ""},
    }
    oa = _req("POST", "/operations-actions", token=admin_token, directory_token=directory_token, body=body)["json"]
    assert oa["status"] == "assigned"
    for nxt in ["in_progress", "waiting", "completed", "closed"]:
        r = _req(
            "POST",
            f"/operations-actions/{oa['id']}/status",
            token=admin_token,
            directory_token=directory_token,
            body={"status": nxt},
        )
        assert r["status"] == 200, r
        assert r["json"]["status"] == nxt
    r = _req(
        "POST",
        f"/operations-actions/{oa['id']}/status",
        token=admin_token,
        directory_token=directory_token,
        body={"status": "open"},
    )
    assert r["status"] == 409


def test_status_invalid_value_rejected(admin_token, directory_token, created_oa):
    r = _req(
        "POST",
        f"/operations-actions/{created_oa['id']}/status",
        token=admin_token,
        directory_token=directory_token,
        body={"status": "rejected"},
    )
    assert r["status"] == 422


def test_status_assigned_without_owner_blocked(admin_token, directory_token):
    oa = _req(
        "POST",
        "/operations-actions",
        token=admin_token,
        directory_token=directory_token,
        body={"title": "T-NO-OWNER", "category": "other", "priority": "low"},
    )["json"]
    assert oa["status"] == "open"
    r = _req(
        "POST",
        f"/operations-actions/{oa['id']}/status",
        token=admin_token,
        directory_token=directory_token,
        body={"status": "assigned"},
    )
    assert r["status"] == 409


def test_add_note(admin_token, directory_token, created_oa):
    r = _req(
        "POST",
        f"/operations-actions/{created_oa['id']}/notes",
        token=admin_token,
        directory_token=directory_token,
        body={"body_en": "Pytest note · second line"},
    )
    assert r["status"] == 200
    assert r["json"]["body_en"].startswith("Pytest")
    full = _req("GET", f"/operations-actions/{created_oa['id']}", token=admin_token, directory_token=directory_token)["json"]
    kinds = [h["kind"] for h in full["history"]]
    assert "note_added" in kinds


def test_owner_search_returns_results(admin_token, directory_token):
    r = _req("GET", "/operations-actions/owner-search?q=jaymn", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    assert "results" in r["json"]


def test_owner_search_empty_query_returns_empty(admin_token, directory_token):
    r = _req("GET", "/operations-actions/owner-search?q=", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    assert r["json"]["results"] == []


def test_list_filter_by_status(admin_token, directory_token):
    r = _req("GET", "/operations-actions?status=open", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    for a in r["json"]["actions"]:
        assert a["status"] == "open"


def test_list_filter_by_category(admin_token, directory_token):
    r = _req("GET", "/operations-actions?category=truck_down", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    for a in r["json"]["actions"]:
        assert a["category"] == "truck_down"


def test_list_search_q(admin_token, directory_token):
    r = _req("GET", "/operations-actions?q=T-PYTEST", token=admin_token, directory_token=directory_token)
    assert r["status"] == 200
    assert r["json"]["total"] >= 1


def test_list_filter_invalid_status_rejected(admin_token, directory_token):
    r = _req("GET", "/operations-actions?status=NOPE", token=admin_token, directory_token=directory_token)
    assert r["status"] == 422


def test_photo_upload_rejects_non_image(admin_token, directory_token, created_oa):
    r = requests.post(
        f"{API}/operations-actions/{created_oa['id']}/photos",
        headers={
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token,
        },
        files={"file": ("fake.jpg", b"THIS IS NOT AN IMAGE", "image/jpeg")},
        timeout=10,
    )
    assert r.status_code == 422


def test_assign_same_owner_is_noop_and_does_not_duplicate_notif(admin_token, directory_token, mongo_db, created_oa):
    r1 = _req(
        "POST",
        f"/operations-actions/{created_oa['id']}/assign",
        token=admin_token,
        directory_token=directory_token,
        body={"owner": {"directory": "user_directory", "id": "admin", "name": "Admin", "email": ""}},
    )
    assert r1["status"] == 200
    before = mongo_db.notifications.count_documents({"type": "oa_assignment", "linked_source_record_id": created_oa["id"]})
    r2 = _req(
        "POST",
        f"/operations-actions/{created_oa['id']}/assign",
        token=admin_token,
        directory_token=directory_token,
        body={"owner": {"directory": "user_directory", "id": "admin", "name": "Admin", "email": ""}},
    )
    assert r2["status"] == 200
    after = mongo_db.notifications.count_documents({"type": "oa_assignment", "linked_source_record_id": created_oa["id"]})
    assert len(r2["json"].get("history") or []) == len(r1["json"].get("history") or [])
    assert after == before


def test_trust_events_written_for_mutations(admin_token, directory_token, mongo_db):
    oa = _req(
        "POST",
        "/operations-actions",
        token=admin_token,
        directory_token=directory_token,
        body={
            "title": "T-TRUST",
            "category": "other",
            "priority": "normal",
            "owner": {"directory": "user_directory", "id": "admin", "name": "Admin", "email": ""},
        },
    )["json"]
    _req(
        "POST",
        f"/operations-actions/{oa['id']}/status",
        token=admin_token,
        directory_token=directory_token,
        body={"status": "in_progress"},
    )
    _req(
        "POST",
        f"/operations-actions/{oa['id']}/notes",
        token=admin_token,
        directory_token=directory_token,
        body={"body_en": "trust smoke"},
    )
    rows = list(mongo_db.trust_spine_events.find({"workflow": "operations-action", "record_id": oa["id"]}, {"_id": 0, "stage": 1, "status": 1}))
    stages = {r.get("stage") for r in rows}
    assert "record_created" in stages
    assert "audit_written" in stages
    assert "completed" in stages