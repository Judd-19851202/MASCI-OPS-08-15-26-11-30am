from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests
from pymongo import MongoClient

from lib.corrective_action_truth import (
    normalize_corrective_action_due_date,
    open_corrective_action_query,
    overdue_corrective_action_query,
)
from lib.synthetic_corrective_action_filter import (
    TECHNICAL_AUDIT_ONLY_SCOPE,
    apply_synthetic_corrective_action_exclusion,
    is_hidden_corrective_action,
    synthetic_corrective_action_markers,
)


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
MONGO_URL = _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = _read_env("/app/backend/.env", "DB_NAME")
SAFETY_EMAIL = "cert.safety@example.com"
SAFETY_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"


def _post_with_retry(path: str, payload: dict, attempts: int = 3):
    last_error = None
    for _ in range(attempts):
        try:
            return requests.post(f"{BASE_URL}{path}", json=payload, timeout=45)
        except requests.RequestException as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError(f"failed to POST {path}")


def _canonical_counts() -> dict:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    today_iso = datetime.now(timezone.utc).date().isoformat()
    return {
        "open": db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion(open_corrective_action_query())
        ),
        "overdue": db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=today_iso))
        ),
    }


def _safety_token() -> str:
    r = _post_with_retry(
        "/api/safety/login",
        {"email": SAFETY_EMAIL, "password": SAFETY_PASSWORD},
    )
    assert r.status_code == 200, r.text
    token = r.json().get("token")
    assert token, "missing safety token"
    return token


def _admin_headers() -> dict:
    r = _post_with_retry(
        "/api/auth/multi-login",
        {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return {
        "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin"),
        "X-Directory-Token": body.get("session_token"),
    }


def test_due_date_normalizer_rejects_blank_strings():
    assert normalize_corrective_action_due_date("") is None
    assert normalize_corrective_action_due_date("   ") is None
    assert normalize_corrective_action_due_date("2026-08-08T19:12:44Z") == "2026-08-08"


def test_hidden_corrective_action_classifier_requires_explicit_governed_markers():
    assert is_hidden_corrective_action({
        "title": "iter160-ca-7a244f75",
        "description": "telemetry integration test",
        "project_number": "",
    }) is False
    hidden = synthetic_corrective_action_markers({"source_kind": "synthetic_test"})
    assert hidden["technical_record_classification"] == "synthetic_test"
    assert hidden["truth_visibility_scope"] == TECHNICAL_AUDIT_ONLY_SCOPE
    assert hidden["hidden_from_operations"] is True
    assert hidden["synthetic_record"] is True
    assert hidden["certification_record"] is False
    assert is_hidden_corrective_action(hidden) is True


def test_hidden_corrective_actions_have_governed_classification_metadata():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    missing = db.corrective_actions.count_documents({
        "$and": [
            {
                "$or": [
                    {"synthetic_record": True},
                    {"hidden_from_operations": True},
                    {"certification_record": True},
                ]
            },
            {"technical_record_classification": {"$in": [None, ""]}},
        ]
    })
    assert missing == 0, f"Hidden corrective actions missing governed classification: {missing}"


def test_hidden_corrective_action_is_excluded_from_operator_list_but_auditable_for_admin():
    safety_token = _safety_token()
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    title = f"synthetic-test-ca-{datetime.now(timezone.utc).timestamp()}"
    created_id = None
    try:
        create = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            headers={"X-Safety-Token": safety_token},
            json={
                "title": title,
                "description": "preview synthetic corrective action audit proof",
                "source_kind": "synthetic_test",
                "priority": "Medium",
                "due_date": "2026-08-01",
            },
            timeout=30,
        )
        assert create.status_code == 200, create.text
        body = create.json()
        created_id = body["id"]
        assert body["technical_record_classification"] == "synthetic_test"
        assert body["hidden_from_operations"] is True

        operator_list = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            headers={"X-Safety-Token": safety_token},
            timeout=30,
        )
        assert operator_list.status_code == 200, operator_list.text
        assert all(row.get("id") != created_id for row in operator_list.json())

        admin_list = requests.get(
            f"{BASE_URL}/api/admin/safety/corrective-actions/technical",
            params={"q": title},
            headers=_admin_headers(),
            timeout=30,
        )
        assert admin_list.status_code == 200, admin_list.text
        items = admin_list.json()["items"]
        assert any(row.get("id") == created_id for row in items)
    finally:
        if created_id:
            db.corrective_actions.delete_one({"id": created_id})


def test_hidden_corrective_action_is_excluded_from_exports_and_notification_digests():
    safety_token = _safety_token()
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    title = f"synthetic-export-proof-{datetime.now(timezone.utc).timestamp()}"
    created_id = None
    try:
        before_safety = requests.get(
            f"{BASE_URL}/api/safety/notifications/digest",
            headers={"X-Safety-Token": safety_token},
            timeout=30,
        )
        assert before_safety.status_code == 200, before_safety.text
        before_admin = requests.get(
            f"{BASE_URL}/api/admin/notifications/digest",
            headers=_admin_headers(),
            timeout=30,
        )
        assert before_admin.status_code == 200, before_admin.text

        create = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            headers={"X-Safety-Token": safety_token},
            json={
                "title": title,
                "description": "hidden corrective action export/digest proof",
                "source_kind": "synthetic_test",
                "priority": "High",
                "due_date": "2026-07-01",
            },
            timeout=30,
        )
        assert create.status_code == 200, create.text
        created_id = create.json()["id"]

        export_resp = requests.get(
            f"{BASE_URL}/api/safety/exports/corrective-actions?format=csv",
            headers={"X-Safety-Token": safety_token},
            timeout=30,
        )
        assert export_resp.status_code == 200, export_resp.text
        assert title not in export_resp.text

        after_safety = requests.get(
            f"{BASE_URL}/api/safety/notifications/digest",
            headers={"X-Safety-Token": safety_token},
            timeout=30,
        )
        assert after_safety.status_code == 200, after_safety.text
        after_admin = requests.get(
            f"{BASE_URL}/api/admin/notifications/digest",
            headers=_admin_headers(),
            timeout=30,
        )
        assert after_admin.status_code == 200, after_admin.text

        assert after_safety.json()["summary"]["overdue_capas"] == before_safety.json()["summary"]["overdue_capas"]
        assert after_safety.json()["summary"]["total_open"] == before_safety.json()["summary"]["total_open"]
        assert after_admin.json()["summary"]["total_open"] == before_admin.json()["summary"]["total_open"]
    finally:
        if created_id:
            db.corrective_actions.delete_one({"id": created_id})


def test_safety_overview_matches_canonical_corrective_action_counts():
    expected = _canonical_counts()
    token = _safety_token()
    r = requests.get(
        f"{BASE_URL}/api/safety/overview",
        headers={"X-Safety-Token": token},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["corrective_actions_open"] == expected["open"]
    assert body["corrective_actions_overdue"] == expected["overdue"]


def test_safety_digest_matches_canonical_corrective_action_counts():
    expected = _canonical_counts()
    token = _safety_token()
    r = requests.get(
        f"{BASE_URL}/api/safety/digest/preview",
        headers={"X-Safety-Token": token},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    payload = r.json()["payload"]
    assert payload["kpis"]["open_corrective_actions"] == expected["open"]
    assert payload["kpis"]["overdue_corrective_actions"] == expected["overdue"]