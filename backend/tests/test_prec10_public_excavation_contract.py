from __future__ import annotations

import os
import uuid
from pathlib import Path

import requests


def _kv(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        return ""
    return ""


BASE_URL = (_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL") or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")


def test_public_excavation_uses_anonymous_safe_rosters_and_idempotent_submit():
    roster = requests.get(f"{BASE_URL}/api/hr/employee-roster/public", timeout=120)
    competent = requests.get(f"{BASE_URL}/api/employees/competent-persons/public", timeout=120)
    assert roster.status_code == 200
    assert competent.status_code == 200

    key = str(uuid.uuid4())
    payload = {
        "project_name": "Preview Excavation Contract Proof",
        "project_number": "OD-100",
        "date_of_work": "2026-08-10",
        "work_area": "North trench runtime proof",
        "foreman_name": "Public Foreman",
        "supervisor_name": "Public Foreman",
        "submitted_by": "public.excavation.contract@example.com",
        "depth_ft": 6,
        "depth_ge_4ft": True,
        "depth_ge_5ft": True,
        "protective_system": "Trench Box / Shielding",
        "inspection_before_entry_completed": True,
        "reinspection_required": False,
        "reinspection_completed": False,
    }
    first = requests.post(
        f"{BASE_URL}/api/trench-safety/excavations/public/submit",
        json=payload,
        headers={"Content-Type": "application/json", "Idempotency-Key": key},
        timeout=120,
    )
    second = requests.post(
        f"{BASE_URL}/api/trench-safety/excavations/public/submit",
        json=payload,
        headers={"Content-Type": "application/json", "Idempotency-Key": key},
        timeout=120,
    )
    first.raise_for_status()
    second.raise_for_status()
    body1 = first.json()
    body2 = second.json()
    assert body1["id"] == body2["id"]
    assert body1.get("doc_id") == body2.get("doc_id")
    assert body1["status"] == body2["status"]