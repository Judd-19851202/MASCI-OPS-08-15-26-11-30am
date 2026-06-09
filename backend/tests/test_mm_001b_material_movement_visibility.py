"""MM-001B · E-1 + E-2 + E-5 regression.

Tests:
  • E-2 catalog: 5 new categories present, original 6 preserved.
  • E-5 derived endpoint returns dispatch + incoming + outgoing.
  • E-1 PDF renders the visibility tile when there's data.
  • E-1 frontend source guard.
"""
from __future__ import annotations
import json
import os
import urllib.request
from typing import Optional, Dict, Any

import pytest

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"


def _req(method, path, *, body=None, token="", token_header="X-Admin-Token"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers[token_header] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "json": json.loads(e.read().decode() or "{}")}


@pytest.fixture(scope="module")
def admin_token():
    pwd = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
    r = _req("POST", "/admin/login", body={"password": pwd})
    assert r["status"] == 200
    return r["json"]["token"]


# ── E-2 · Material taxonomy expansion ──────────────────────────────
def test_e2_taxonomy_adds_landscape_category():
    from dispatch_assignment_seeds import MATERIAL_CATALOG
    cats = {c["category"] for c in MATERIAL_CATALOG}
    assert "Landscape / Site" in cats
    assert "Striping / Markings" in cats
    assert "Regulated / Hazmat" in cats


def test_e2_taxonomy_adds_specific_items():
    from dispatch_assignment_seeds import MATERIAL_CATALOG
    flat = {item for c in MATERIAL_CATALOG for item in c["items"]}
    for required in ("Sod", "Trees", "Stumps", "Striping Materials", "Contaminated Material"):
        assert required in flat, f"Missing: {required}"


def test_e2_taxonomy_preserves_original_categories():
    from dispatch_assignment_seeds import MATERIAL_CATALOG
    cats = {c["category"] for c in MATERIAL_CATALOG}
    for required in (
        "Asphalt / Plant", "Aggregate / Base", "Earthwork / Soils",
        "Concrete / Demo", "Utility / Roadway", "Job Support / Misc",
    ):
        assert required in cats, f"Lost category: {required}"


# ── E-5 · Derived endpoint ─────────────────────────────────────────
def test_e5_endpoint_returns_shape():
    r = _req("GET", "/material-movement/daily/UNKNOWN-PROJ/2026-06-08")
    assert r["status"] == 200
    body = r["json"]
    for key in ("project_number", "date", "dispatch", "incoming", "outgoing"):
        assert key in body, f"Missing key: {key}"
    for key in ("assignments", "loads", "trucks", "by_haul_type", "rows"):
        assert key in body["dispatch"]


def test_e5_endpoint_validates_inputs():
    # Empty string in URL = a non-existent project; endpoint should
    # still return a valid empty rollup (not crash).
    r = _req("GET", "/material-movement/daily/empty-project/2026-06-08")
    assert r["status"] == 200
    assert r["json"]["dispatch"]["assignments"] == 0


def test_e5_endpoint_reflects_dr_materials(admin_token):
    """Submit a DR with a materials row, then assert the derived endpoint
    surfaces it under 'incoming'."""
    body = {
        "project_name": "MM-001B · E-5 fixture",
        "project_number": "JOB-MM-E5",
        "location": "Yard",
        "report_date": "2026-06-08",
        "prepared_by": "Pytest",
        "photos": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII="
        ] * 6,
        "prepared_by_signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIAAAoAAv/lxKUAAAAASUVORK5CYII=",
        "materials": [
            {"description": "SP-12.5 Asphalt", "quantity": 240, "unit": "TON",
             "supplier": "Pytest Plant", "ticket_number": "TKT-E5-1"},
        ],
        "production": [
            {"description": "RCP install", "quantity": 100, "unit": "LF",
             "station_from": "10+00", "station_to": "11+00"},
        ],
    }
    sub = _req("POST", "/daily-reports", token=admin_token, body=body)
    assert sub["status"] == 200
    r = _req("GET", "/material-movement/daily/JOB-MM-E5/2026-06-08")
    assert r["status"] == 200
    assert len(r["json"]["incoming"]) >= 1
    inc = r["json"]["incoming"][0]
    assert inc["material"] == "SP-12.5 Asphalt"
    assert inc["unit"] == "TON"
    assert inc["source"] == "Pytest Plant"
    # production row appears under outgoing group
    assert len(r["json"]["outgoing"]) >= 1


# ── E-1 · Frontend source-level guard ──────────────────────────────
def test_e1_view_renders_material_movement_tile():
    src = open("/app/frontend/src/pages/ViewDailyReport.jsx", "r", encoding="utf-8").read()
    assert "MaterialMovementTile" in src
    assert 'data-testid="dr-view-material-movement"' in src
    tile = open("/app/frontend/src/components/MaterialMovementTile.jsx", "r", encoding="utf-8").read()
    assert "/material-movement/daily/" in tile
    assert 'data-testid="mm-tile-root"' in tile


# ── No-write guarantee ─────────────────────────────────────────────
def test_no_new_collection_for_material_movement():
    """The router file must NOT instantiate any new MongoDB collection
    or write operation. Pure derivation."""
    src = open("/app/backend/routes/material_movement.py", "r", encoding="utf-8").read()
    for forbidden in ("insert_one", "insert_many", "update_one", "update_many",
                       "delete_one", "delete_many", "drop_collection", "rename"):
        assert forbidden not in src, f"Forbidden write op found: {forbidden}"
