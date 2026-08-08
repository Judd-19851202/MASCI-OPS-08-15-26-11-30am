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
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion, is_synthetic_corrective_action


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
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    token = r.json().get("token")
    assert token, "missing safety token"
    return token


def test_due_date_normalizer_rejects_blank_strings():
    assert normalize_corrective_action_due_date("") is None
    assert normalize_corrective_action_due_date("   ") is None
    assert normalize_corrective_action_due_date("2026-08-08T19:12:44Z") == "2026-08-08"


def test_synthetic_corrective_action_classifier_flags_test_records_only():
    assert is_synthetic_corrective_action({
        "title": "iter160-ca-7a244f75",
        "description": "telemetry integration test",
        "project_number": "",
    }) is True
    assert is_synthetic_corrective_action({
        "title": "Workplace-violence review — confirm witnesses + police data + media exposure",
        "description": "Auto-issued from incident INC-2026-00488.",
        "project_number": "24-12",
    }) is False


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