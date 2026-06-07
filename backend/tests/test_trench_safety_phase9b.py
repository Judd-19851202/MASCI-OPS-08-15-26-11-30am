"""Phase 9B — Report Automation & Distribution tests.

Validates PDF + XLSX exports, presets CRUD, subscriptions CRUD + run,
Road Plate package install (idempotent), Leadership Digest, and the
cron `run-due` entrypoint.
"""
from __future__ import annotations

import io
import os
import sys
import uuid
from pathlib import Path

import pytest
import requests

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

API = os.environ.get("TS_API_BASE", "http://localhost:8001")


def _admin_token() -> str:
    pwd = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


# ─────────────────────────────────────────────────────────────────────
# PDF + XLSX exports
# ─────────────────────────────────────────────────────────────────────
def test_pdf_export_returns_pdf(token):
    r = requests.get(
        f"{API}/api/trench-safety/reports/executive/export.pdf",
        headers={"X-Admin-Token": token}, timeout=30,
    )
    r.raise_for_status()
    assert r.headers["content-type"].startswith("application/pdf")
    body = r.content
    assert body[:4] == b"%PDF", "expected PDF magic bytes"
    # Some reasonable minimum size
    assert len(body) > 800


def test_xlsx_export_returns_xlsx(token):
    r = requests.get(
        f"{API}/api/trench-safety/reports/road-plate/export.xlsx",
        headers={"X-Admin-Token": token}, timeout=20,
    )
    r.raise_for_status()
    assert "spreadsheetml.sheet" in r.headers["content-type"]
    # XLSX is a zip — first 2 bytes = PK
    assert r.content[:2] == b"PK"


def test_pdf_export_unknown_report_404(token):
    r = requests.get(
        f"{API}/api/trench-safety/reports/no-such-thing/export.pdf",
        headers={"X-Admin-Token": token}, timeout=15,
    )
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Presets CRUD
# ─────────────────────────────────────────────────────────────────────
def test_preset_crud(token):
    create = requests.post(
        f"{API}/api/trench-safety/reports/presets",
        headers=_h(token),
        json={"name": "Road Plates Only", "report_id": "road-plate",
              "filters": {"asset_type": "Road Plate"}}, timeout=15,
    )
    create.raise_for_status()
    pid = create.json()["id"]
    # List includes it
    lst = requests.get(f"{API}/api/trench-safety/reports/presets",
                       headers=_h(token), timeout=15)
    lst.raise_for_status()
    ids = [it["id"] for it in lst.json().get("items", [])]
    assert pid in ids
    # Update
    upd = requests.put(
        f"{API}/api/trench-safety/reports/presets/{pid}",
        headers=_h(token), json={"name": "RP Only · Renamed"}, timeout=15,
    )
    upd.raise_for_status()
    assert upd.json()["name"] == "RP Only · Renamed"
    # Delete
    dele = requests.delete(
        f"{API}/api/trench-safety/reports/presets/{pid}",
        headers=_h(token), timeout=15,
    )
    dele.raise_for_status()
    assert dele.json()["deleted"] == pid


def test_preset_rejects_bad_report(token):
    r = requests.post(
        f"{API}/api/trench-safety/reports/presets",
        headers=_h(token),
        json={"name": "x", "report_id": "no-such"}, timeout=10,
    )
    assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────
# Subscriptions CRUD + run
# ─────────────────────────────────────────────────────────────────────
def test_subscription_crud_and_manual_run(token):
    body = {
        "name": f"Test sub {uuid.uuid4().hex[:6]}",
        "report_id": "executive",
        "frequency": "weekly",
        "format": "csv",
        "recipients": ["qa-test@example.com"],
        "filters": {},
        "enabled": True,
    }
    create = requests.post(
        f"{API}/api/trench-safety/reports/subscriptions",
        headers=_h(token), json=body, timeout=15,
    )
    create.raise_for_status()
    sub = create.json()
    sid = sub["id"]
    assert sub["frequency"] == "weekly"
    assert sub["format"] == "csv"
    assert sub["enabled"] is True
    assert sub["next_due_at"]
    try:
        # Update
        upd = requests.put(
            f"{API}/api/trench-safety/reports/subscriptions/{sid}",
            headers=_h(token),
            json={"format": "pdf", "enabled": False}, timeout=15,
        )
        upd.raise_for_status()
        new = upd.json()
        assert new["format"] == "pdf"
        assert new["enabled"] is False
        # Manual fire
        run = requests.post(
            f"{API}/api/trench-safety/reports/subscriptions/{sid}/run",
            headers=_h(token), timeout=30,
        )
        run.raise_for_status()
        body = run.json()
        assert "delivery" in body
        assert body["delivery"]["status"] in ("sent", "skipped", "no_recipients", "email_disabled")
    finally:
        requests.delete(
            f"{API}/api/trench-safety/reports/subscriptions/{sid}",
            headers=_h(token), timeout=10,
        )


# ─────────────────────────────────────────────────────────────────────
# Road Plate Leadership Package (idempotent)
# ─────────────────────────────────────────────────────────────────────
def test_install_road_plate_package_idempotent(token):
    r1 = requests.post(
        f"{API}/api/trench-safety/reports/subscriptions/install-road-plate-package",
        headers=_h(token), timeout=20,
    )
    r1.raise_for_status()
    b1 = r1.json()
    created_count_1 = b1["created_count"]
    skipped_1 = b1["skipped_count"]
    # 4-subscription package
    assert created_count_1 + skipped_1 == 4
    # Re-install — must be fully idempotent (4 skipped, 0 created)
    r2 = requests.post(
        f"{API}/api/trench-safety/reports/subscriptions/install-road-plate-package",
        headers=_h(token), timeout=20,
    )
    r2.raise_for_status()
    b2 = r2.json()
    assert b2["created_count"] == 0
    assert b2["skipped_count"] == 4


# ─────────────────────────────────────────────────────────────────────
# Leadership Digest
# ─────────────────────────────────────────────────────────────────────
def test_digest_generate_and_render(token):
    gen = requests.post(
        f"{API}/api/trench-safety/reports/digest/generate?send=false",
        headers=_h(token), timeout=25,
    )
    gen.raise_for_status()
    doc = gen.json()
    assert doc["id"]
    assert doc["delivery"]["status"] == "not_sent"
    # Detail
    detail = requests.get(
        f"{API}/api/trench-safety/reports/digest/{doc['id']}",
        headers=_h(token), timeout=15,
    )
    detail.raise_for_status()
    assert detail.json()["id"] == doc["id"]
    # HTML
    html_r = requests.get(
        f"{API}/api/trench-safety/reports/digest/{doc['id']}/html",
        headers=_h(token), timeout=15,
    )
    html_r.raise_for_status()
    assert "Leadership Digest" in html_r.text
    assert "Top 3 Risks" in html_r.text


def test_digest_current_and_history(token):
    cur = requests.get(f"{API}/api/trench-safety/reports/digest/current",
                       headers=_h(token), timeout=15)
    cur.raise_for_status()
    assert "snapshot" in cur.json()
    hist = requests.get(f"{API}/api/trench-safety/reports/digest/history?limit=10",
                        headers=_h(token), timeout=15)
    hist.raise_for_status()
    assert "items" in hist.json()


# ─────────────────────────────────────────────────────────────────────
# Cron entrypoint (run-due)
# ─────────────────────────────────────────────────────────────────────
def test_run_due_processes_zero_or_more(token):
    r = requests.post(
        f"{API}/api/trench-safety/reports/subscriptions/run-due",
        headers=_h(token), timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    assert "processed" in body
    assert "count" in body
    assert isinstance(body["count"], int)
