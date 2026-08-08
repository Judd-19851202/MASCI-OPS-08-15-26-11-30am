from __future__ import annotations

from pathlib import Path

import requests


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")


def _request_with_retry(method: str, path: str, *, headers: dict | None = None, json_body: dict | None = None, attempts: int = 3):
    last_error = None
    for _ in range(attempts):
        try:
            return requests.request(method, f"{BASE_URL}{path}", headers=headers, json=json_body, timeout=45)
        except requests.RequestException as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError(f"failed request {method} {path}")


def _admin_headers() -> dict:
    r = _request_with_retry(
        "POST",
        "/api/auth/multi-login",
        json_body={"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return {
        "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin"),
        "X-Directory-Token": body.get("session_token"),
    }


def test_incident_archive_history_and_reopen_runtime_flow():
    headers = _admin_headers()
    create = _request_with_retry(
        "POST",
        "/api/incident-cases",
        headers=headers,
        json_body={
            "field_block": {
                "incident_type": "near_miss",
                "location_label": "Archive proof area",
                "job_number": "ZZ-RUNTIME-CERT-2026",
                "reporter_name": "Archive Proof Reporter",
                "reporter_role": "Foreman",
                "observed_conditions": "Archive lifecycle proof",
            }
        },
    )
    assert create.status_code == 200, create.text
    case_id = create.json()["id"]

    for state in [
        "FIELD_SUBMITTED",
        "SAFETY_INTAKE",
        "UNDER_INVESTIGATION",
        "CORRECTIVE_ACTIONS",
        "VERIFICATION",
        "CLOSED",
    ]:
        r = _request_with_retry(
            "POST",
            f"/api/incident-cases/{case_id}/transitions",
            headers=headers,
            json_body={"to_state": state, "reason": f"advance to {state}"},
        )
        assert r.status_code == 200, r.text

    archive = _request_with_retry(
        "POST",
        f"/api/incident-cases/{case_id}/archive",
        headers=headers,
        json_body={"reason": "preview archive certification"},
    )
    assert archive.status_code == 200, archive.text
    archived = archive.json()
    assert archived["archived"] is True
    assert archived["archived_reason"] == "preview archive certification"

    default_list = _request_with_retry("GET", "/api/incident-cases?limit=500", headers=headers)
    assert default_list.status_code == 200, default_list.text
    assert all(row.get("id") != case_id for row in default_list.json()["cases"])

    archived_list = _request_with_retry(
        "GET",
        "/api/incident-cases?include_archived=true&query=Archive%20Proof%20Reporter&limit=500",
        headers=headers,
    )
    assert archived_list.status_code == 200, archived_list.text
    assert any(row.get("id") == case_id and row.get("archived") is True for row in archived_list.json()["cases"])

    audit = _request_with_retry("GET", f"/api/incident-cases/{case_id}/audit", headers=headers)
    assert audit.status_code == 200, audit.text
    event_types = [row.get("event_type") for row in audit.json()]
    assert "case.archived" in event_types
    assert "case.closed" in event_types

    reopen = _request_with_retry(
        "POST",
        f"/api/incident-cases/{case_id}/transitions",
        headers=headers,
        json_body={"to_state": "REOPENED", "reason": "preview reopen certification"},
    )
    assert reopen.status_code == 200, reopen.text
    reopened = reopen.json()
    assert reopened["state"] == "REOPENED"
    assert reopened["archived"] is False
    assert reopened["archived_at"] == ""

    reopened_list = _request_with_retry(
        "GET",
        "/api/incident-cases?state=REOPENED&limit=500",
        headers=headers,
    )
    assert reopened_list.status_code == 200, reopened_list.text
    assert any(row.get("id") == case_id for row in reopened_list.json()["cases"])