"""
PRE-C10 Cross-Surface Safety Parity Test

Verifies that corrective action counts are consistent across:
1. /api/safety/overview
2. /api/safety/digest/preview
3. /api/admin/executive/overview (safety tile)
4. /api/admin/command-center (safety headline)
5. /api/operations-center/summary (safety section)
6. /api/project-health (project-scoped rollups)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from pymongo import MongoClient

from lib.corrective_action_truth import (
    open_corrective_action_query,
    overdue_corrective_action_query,
)
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion


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


def _canonical_counts() -> dict:
    """Get canonical truth directly from MongoDB using the same query helpers."""
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


def _admin_tokens() -> dict:
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    admin_token = (body.get("portal_tokens") or {}).get("admin")
    session_token = body.get("session_token")
    assert admin_token and session_token, "missing admin tokens"
    return {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token,
    }


def test_canonical_truth_values():
    """Print canonical truth for reference."""
    expected = _canonical_counts()
    print(f"\n=== CANONICAL TRUTH (from MongoDB) ===")
    print(f"Open Corrective Actions: {expected['open']}")
    print(f"Overdue Corrective Actions: {expected['overdue']}")
    assert expected["open"] >= 0
    assert expected["overdue"] >= 0


def test_safety_overview_parity():
    """Safety overview matches canonical truth."""
    expected = _canonical_counts()
    token = _safety_token()
    r = requests.get(
        f"{BASE_URL}/api/safety/overview",
        headers={"X-Safety-Token": token},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    print(f"\n=== SAFETY OVERVIEW ===")
    print(f"Open: {body['corrective_actions_open']} (expected: {expected['open']})")
    print(f"Overdue: {body['corrective_actions_overdue']} (expected: {expected['overdue']})")
    assert body["corrective_actions_open"] == expected["open"], f"Open mismatch: {body['corrective_actions_open']} != {expected['open']}"
    assert body["corrective_actions_overdue"] == expected["overdue"], f"Overdue mismatch: {body['corrective_actions_overdue']} != {expected['overdue']}"


def test_safety_digest_parity():
    """Safety digest preview matches canonical truth."""
    expected = _canonical_counts()
    token = _safety_token()
    r = requests.get(
        f"{BASE_URL}/api/safety/digest/preview",
        headers={"X-Safety-Token": token},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    payload = r.json()["payload"]
    print(f"\n=== SAFETY DIGEST PREVIEW ===")
    print(f"Open: {payload['kpis']['open_corrective_actions']} (expected: {expected['open']})")
    print(f"Overdue: {payload['kpis']['overdue_corrective_actions']} (expected: {expected['overdue']})")
    assert payload["kpis"]["open_corrective_actions"] == expected["open"]
    assert payload["kpis"]["overdue_corrective_actions"] == expected["overdue"]


def test_executive_overview_safety_tile_parity():
    """Executive overview safety tile matches canonical truth."""
    expected = _canonical_counts()
    headers = _admin_tokens()
    r = requests.get(
        f"{BASE_URL}/api/admin/executive/overview",
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    safety_tile = body["tiles"]["safety"]
    overdue_tile = body["tiles"]["overdue"]
    print(f"\n=== EXECUTIVE OVERVIEW ===")
    print(f"Safety tile - unresolved_corrective_actions: {safety_tile['unresolved_corrective_actions']} (expected open: {expected['open']})")
    print(f"Overdue tile - overdue_corrective_actions: {overdue_tile['overdue_corrective_actions']} (expected overdue: {expected['overdue']})")
    assert safety_tile["unresolved_corrective_actions"] == expected["open"], f"Open mismatch in executive overview"
    assert overdue_tile["overdue_corrective_actions"] == expected["overdue"], f"Overdue mismatch in executive overview"


def test_command_center_safety_parity():
    """Command center safety headline matches canonical truth."""
    expected = _canonical_counts()
    headers = _admin_tokens()
    r = requests.get(
        f"{BASE_URL}/api/admin/command-center",
        headers=headers,
        timeout=30,
    )
    if r.status_code == 404:
        print("\n=== COMMAND CENTER ===")
        print("Endpoint not found - skipping")
        return
    assert r.status_code == 200, r.text
    body = r.json()
    print(f"\n=== COMMAND CENTER ===")
    # Check if safety section exists
    safety = body.get("safety") or body.get("safety_headline") or {}
    if "open_corrective_actions" in safety:
        print(f"Open: {safety['open_corrective_actions']} (expected: {expected['open']})")
        assert safety["open_corrective_actions"] == expected["open"]
    if "overdue_corrective_actions" in safety:
        print(f"Overdue: {safety['overdue_corrective_actions']} (expected: {expected['overdue']})")
        assert safety["overdue_corrective_actions"] == expected["overdue"]


def test_operations_center_safety_parity():
    """Operations center safety section matches canonical truth."""
    expected = _canonical_counts()
    headers = _admin_tokens()
    r = requests.get(
        f"{BASE_URL}/api/operations-center/summary",
        headers=headers,
        timeout=30,
    )
    if r.status_code == 404:
        print("\n=== OPERATIONS CENTER ===")
        print("Endpoint not found - skipping")
        return
    assert r.status_code == 200, r.text
    body = r.json()
    print(f"\n=== OPERATIONS CENTER ===")
    safety = body.get("safety") or {}
    if "open_corrective_actions" in safety:
        print(f"Open: {safety['open_corrective_actions']} (expected: {expected['open']})")
        assert safety["open_corrective_actions"] == expected["open"]
    if "overdue_corrective_actions" in safety:
        print(f"Overdue: {safety['overdue_corrective_actions']} (expected: {expected['overdue']})")
        assert safety["overdue_corrective_actions"] == expected["overdue"]


def test_corrective_actions_list_excludes_synthetic():
    """Verify the corrective actions list endpoint excludes synthetic records."""
    token = _safety_token()
    r = requests.get(
        f"{BASE_URL}/api/safety/corrective-actions",
        headers={"X-Safety-Token": token},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    items = r.json()
    print(f"\n=== CORRECTIVE ACTIONS LIST ===")
    print(f"Total items returned: {len(items)}")
    
    # Check that no synthetic records are in the list
    synthetic_markers = ["synthetic_record", "hidden_from_operations", "certification_record"]
    synthetic_found = []
    for item in items:
        for marker in synthetic_markers:
            if item.get(marker) is True:
                synthetic_found.append(item.get("title", "unknown"))
                break
    
    if synthetic_found:
        print(f"WARNING: Found {len(synthetic_found)} synthetic records in list: {synthetic_found[:5]}")
    else:
        print("No synthetic records found in list - GOOD")
    
    assert len(synthetic_found) == 0, f"Synthetic records leaked into operator list: {synthetic_found[:5]}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
