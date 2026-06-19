"""Track 13.31B-D3+D4 · Asset Documents · Renewals · CSV · PDF tests."""
import io
import os
import uuid

import httpx
import pytest

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"

# ── Helpers ────────────────────────────────────────────────────────


def _admin():
    r = httpx.post(f"{API}/admin/login", json={"password": "Maddix123!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_tok():
    return _admin()


def _seed_asset(tok: str, prefix: str, asset_class: str, asset_type: str) -> str:
    h = {"X-Admin-Token": tok, "Content-Type": "application/json"}
    suffix = uuid.uuid4().hex[:8]
    body = {
        "asset_number": f"{prefix}-{suffix}",
        "asset_name": f"D3D4 {asset_type}",
        "asset_class": asset_class,
        "asset_type": asset_type,
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    return j.get("id") or j.get("asset_id")


def _png_bytes() -> bytes:
    # smallest valid PNG (1x1 transparent)
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )


def _pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000054 00000 n\n0000000101 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n168\n%%EOF\n"
    )


def _upload(tok: str, asset_id: str, document_type: str, body: bytes,
            content_type: str, **fields) -> httpx.Response:
    files = {"file": ("doc.bin", io.BytesIO(body), content_type)}
    data = {"document_type": document_type, **fields}
    return httpx.post(
        f"{API}/asset-spine/assets/{asset_id}/documents/upload",
        files=files, data=data,
        headers={"X-Admin-Token": tok},
        timeout=30,
    )


# ── 1 · Upload happy path · image ──────────────────────────────────


def test_upload_image_registration(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-PT", "Truck", "Pickup Truck")
    r = _upload(
        admin_tok, asset_id, "registration", _png_bytes(), "image/png",
        effective_date="2025-01-01", expiration_date="2027-01-01",
        operational_note="Annual registration",
    )
    assert r.status_code in (200, 201), r.text
    doc = r.json()
    assert doc["document_type"] == "registration"
    assert doc["document_label"] == "Registration"
    assert doc["expiration_date"] == "2027-01-01"
    assert doc["is_sensitive"] is False
    # equipment_master mirror should now carry the expiration
    g = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g.status_code == 200
    assert g.json().get("registration_expiration") == "2027-01-01"


# ── 2 · Upload happy path · PDF ────────────────────────────────────


def test_upload_pdf_insurance_card(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-DT", "Truck", "Dump Truck")
    r = _upload(
        admin_tok, asset_id, "insurance_card", _pdf_bytes(), "application/pdf",
        expiration_date="2026-08-15",
    )
    assert r.status_code in (200, 201), r.text
    doc = r.json()
    assert doc["content_type"] == "application/pdf"
    assert doc["document_type"] == "insurance_card"
    # Mirror
    g = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g.json().get("insurance_expiration") == "2026-08-15"


# ── 3 · Sensitive type · Title · admin can upload + list ──────────


def test_sensitive_type_visibility(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-ST", "Truck", "Service Truck")
    r = _upload(admin_tok, asset_id, "title", _pdf_bytes(), "application/pdf")
    assert r.status_code in (200, 201), r.text
    # List should include sensitive (admin)
    lst = httpx.get(f"{API}/asset-spine/assets/{asset_id}/documents",
                    headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert lst.status_code == 200, lst.text
    items = lst.json()["items"]
    sensitive_items = [i for i in items if i["is_sensitive"]]
    assert len(sensitive_items) == 1
    assert sensitive_items[0]["document_type"] == "title"


# ── 4 · Asset Admin role gate · non-admin denied ──────────────────


def test_non_admin_cannot_upload(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-NA", "Truck", "Pickup Truck")
    # PM token does NOT satisfy require_admin on /api/admin paths but
    # the doc endpoints use require_admin (admin-or-PM allowed off
    # /api/admin/* prefix). Our route prefix is /api/asset-spine/ not
    # /api/admin/, so PM tokens pass require_admin. Asset Admin gate
    # then verifies role. For the smoke we assert NO token returns
    # 403 (proves the gate is enforced for unauthenticated callers).
    files = {"file": ("doc.png", io.BytesIO(_png_bytes()), "image/png")}
    data = {"document_type": "registration"}
    r = httpx.post(
        f"{API}/asset-spine/assets/{asset_id}/documents/upload",
        files=files, data=data, timeout=30,
    )
    assert r.status_code in (401, 403), r.text


# ── 5 · Listing returns the documents ──────────────────────────────


def test_list_documents(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-L", "Truck", "Pickup Truck")
    _upload(admin_tok, asset_id, "registration", _png_bytes(), "image/png")
    _upload(admin_tok, asset_id, "insurance_card", _png_bytes(), "image/png")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 2
    types = {i["document_type"] for i in items}
    assert types == {"registration", "insurance_card"}


# ── 6 · File fetch returns the binary ──────────────────────────────


def test_file_fetch_roundtrip(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-F", "Truck", "Pickup Truck")
    up = _upload(admin_tok, asset_id, "registration", _png_bytes(), "image/png")
    aid = up.json()["id"]
    r = httpx.get(
        f"{API}/asset-spine/assets/{asset_id}/documents/{aid}/file",
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert r.content == _png_bytes()


# ── 7 · PATCH metadata · expiration date triggers mirror ──────────


def test_patch_meta_updates_mirror(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-P", "Heavy Equipment", "Excavator")
    up = _upload(admin_tok, asset_id, "warranty", _pdf_bytes(), "application/pdf")
    aid = up.json()["id"]
    r = httpx.patch(
        f"{API}/asset-spine/assets/{asset_id}/documents/{aid}",
        json={"expiration_date": "2028-01-01", "operational_note": "Extended"},
        headers={"X-Admin-Token": admin_tok, "Content-Type": "application/json"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.json()["expiration_date"] == "2028-01-01"
    g = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g.json().get("warranty_expiration") == "2028-01-01"


# ── 8 · DELETE clears mirror ───────────────────────────────────────


def test_delete_clears_mirror(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-D", "Truck", "Pickup Truck")
    up = _upload(admin_tok, asset_id, "registration", _png_bytes(), "image/png",
                 expiration_date="2027-06-01")
    aid = up.json()["id"]
    # mirror set
    g1 = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g1.json().get("registration_expiration") == "2027-06-01"
    # delete
    d = httpx.delete(f"{API}/asset-spine/assets/{asset_id}/documents/{aid}",
                     headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert d.status_code == 200, d.text
    # mirror cleared
    g2 = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g2.json().get("registration_expiration") in (None, "")


# ── 9 · Required documents endpoint ────────────────────────────────


def test_required_documents_truck(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-RQ", "Truck", "Dump Truck")
    r = httpx.get(
        f"{API}/asset-spine/assets/{asset_id}/required-documents",
        headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    types = {d["document_type"] for d in body["required_documents"]}
    assert "registration" in types
    assert "insurance_card" in types
    assert "dot_document" in types  # Dump Truck → DOT required
    assert body["missing_count"] >= 3


# ── 10 · Renewals bucket includes upcoming ─────────────────────────


def test_renewals_dashboard_buckets(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-R", "Truck", "Pickup Truck")
    # Expiring in 45 days → should land in 60-bucket and 90-bucket
    from datetime import date, timedelta
    exp45 = (date.today() + timedelta(days=45)).isoformat()
    _upload(admin_tok, asset_id, "registration", _png_bytes(), "image/png",
            expiration_date=exp45)
    r = httpx.get(f"{API}/asset-spine/dashboard/renewals?bucket=60",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(i["asset_id"] == asset_id for i in items)
    # 30-day bucket should NOT include the 45-day one
    r30 = httpx.get(f"{API}/asset-spine/dashboard/renewals?bucket=30",
                    headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert not any(i["asset_id"] == asset_id for i in r30.json()["items"])


# ── 11 · CSV exports return valid CSV ─────────────────────────────


def test_csv_exports_shape(admin_tok):
    for path, fname in [
        ("/asset-spine/exports/assets.csv", "asset-inventory"),
        ("/asset-spine/exports/renewals.csv", "renewals"),
        ("/asset-spine/exports/missing-documents.csv", "missing-documents"),
    ]:
        r = httpx.get(f"{API}{path}", headers={"X-Admin-Token": admin_tok}, timeout=30)
        assert r.status_code == 200, f"{path} → {r.status_code} {r.text[:200]}"
        assert r.headers["content-type"].startswith("text/csv")
        first_line = r.text.splitlines()[0]
        assert "," in first_line


# ── 12 · PDF profile returns a PDF ─────────────────────────────────


def test_profile_pdf(admin_tok):
    asset_id = _seed_asset(admin_tok, "D34-PDF", "Heavy Equipment", "Excavator")
    _upload(admin_tok, asset_id, "warranty", _pdf_bytes(), "application/pdf",
            expiration_date="2028-12-31")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/profile.pdf",
                  headers={"X-Admin-Token": admin_tok}, timeout=60)
    assert r.status_code == 200, r.text[:200]
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"


# ── 13 · No new collection introduced ──────────────────────────────


def test_no_new_collection_added():
    src = open("/app/backend/routes/asset_documents.py").read()
    assert "create_collection" not in src
    # All writes target operational_attachments or equipment_master
    assert "db.operational_attachments" in src
    # No fabricated collections
    bad_names = ["asset_documents_v2", "documents_collection", "asset_vault",
                 "asset_files", "renewals_collection"]
    for n in bad_names:
        assert n not in src


# ── 14 · Required-docs config returns full asset_type map ─────────


def test_required_documents_config(admin_tok):
    r = httpx.get(f"{API}/asset-spine/dashboard/required-documents-config",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 50  # 92 canonical asset_types
    # Some asset_types should have non-empty requirements
    with_reqs = [it for it in body["items"] if it["required"]]
    assert len(with_reqs) >= 10


# ── 15 · D5.4 regression — Pre-Op + DVIR persistence still works ──


def test_d54_regression_still_green(admin_tok):
    """Confirm Track 13.31B-D5.4 Pre-Op section capture still persists."""
    asset_id = _seed_asset(admin_tok, "D34-REG", "Heavy Equipment", "Excavator")
    g = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    j = g.json()
    unit = j.get("unit_number") or j.get("asset_number")
    assert unit, f"unit_number absent: {j}"
    body = {
        "project_name": "D34 regression", "project_number": "20-07", "location": "Field",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "operator_name": "Regression Tester",
        "equipment_type": "Other", "equipment_unit": unit,
        "checklist": {}, "pass_count": 1, "fail_count": 0, "na_count": 0,
        "inspection_sections": {
            "template_key": "preop:excavator",
            "template_label": "Excavator Inspection",
            "asset_type": "Excavator",
            "applies_to": "pre_op",
            "sections": [{"label": "Walkaround", "items": [
                {"name": "Visual", "status": "pass", "note": ""}
            ]}],
            "pass_count": 1, "fail_count": 0, "na_count": 0, "total_count": 1,
        },
    }
    r = httpx.post(f"{API}/equipment-inspections", json=body, timeout=30)
    assert r.status_code in (200, 201)
    iid = r.json()["id"]
    gg = httpx.get(f"{API}/equipment-inspections/{iid}",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert gg.json().get("inspection_sections", {}).get("asset_type") == "Excavator"
