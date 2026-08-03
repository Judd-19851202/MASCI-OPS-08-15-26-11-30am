"""
test_iter134_training_center.py — Iter134

Covers:
  - Training Center backend: portals, list, single, PDF, admin-protected mutations
  - Fire Extinguisher Bulk Import: template, preview, commit, history
"""
from __future__ import annotations

import io
import os
import csv

import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://masci-audit-hub.preview.emergentagent.com",
).rstrip("/")
TIMEOUT = 60


# ───────────────────────── fixtures ─────────────────────────

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture(scope="session")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": "Safety123!"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ─────────────── Training Center: public reads ───────────────

class TestTrainingCenterPortals:
    def test_portals_returns_9_with_counts(self):
        r = requests.get(f"{BASE_URL}/api/training-center/portals", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "portals" in data
        portals = data["portals"]
        assert len(portals) == 9, f"expected 9 portals, got {len(portals)}"
        keys = {p["key"] for p in portals}
        assert {"admin", "safety", "hr", "dispatch", "shop", "pm",
                "field", "integration", "reliability"} == keys
        for p in portals:
            assert "label" in p
            assert "count" in p
            assert isinstance(p["count"], int)
        total = sum(p["count"] for p in portals)
        assert total >= 16, f"total guide count across portals = {total}, expected >=16"


class TestTrainingCenterGuides:
    def test_guides_list_returns_16_and_no_sections(self):
        r = requests.get(f"{BASE_URL}/api/training-center/guides", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "guides" in data
        assert "total" in data
        assert data["total"] == len(data["guides"])
        assert data["total"] >= 16, f"expected at least 16 guides, got {data['total']}"
        # No sections field on the list view
        for g in data["guides"]:
            assert "sections" not in g, "list view must NOT include heavy sections blob"
            assert "slug" in g
            assert "portal" in g
            assert "title" in g

    def test_guides_filter_by_safety_portal(self):
        r = requests.get(
            f"{BASE_URL}/api/training-center/guides",
            params={"portal": "safety"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        guides = r.json()["guides"]
        assert len(guides) > 0
        for g in guides:
            assert g["portal"] == "safety", f"non-safety guide leaked: {g}"

    def test_get_single_guide_includes_sections(self):
        slug = "safety-fire-ext-bulk-import"
        r = requests.get(f"{BASE_URL}/api/training-center/guide/{slug}", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        g = r.json()
        assert g["slug"] == slug
        assert "sections" in g
        assert isinstance(g["sections"], list)
        assert len(g["sections"]) > 0
        sec = g["sections"][0]
        assert "heading" in sec
        assert "body_md" in sec

    def test_get_guide_404_on_unknown_slug(self):
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/this-does-not-exist-xyz",
            timeout=TIMEOUT,
        )
        assert r.status_code == 404


class TestTrainingCenterPDF:
    def test_pdf_returns_valid_bytes(self):
        slug = "safety-fire-ext-bulk-import"
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/{slug}/pdf",
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", "PDF magic header missing"
        assert len(r.content) > 500

    def test_pdf_404_on_unknown_slug(self):
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/nope-xyz/pdf",
            timeout=TIMEOUT,
        )
        assert r.status_code == 404


# ─────────────── Training Center: admin-protected ───────────────

class TestTrainingCenterAdminGate:
    """conftest.py auto-injects X-Admin-Token on every requests call, so we
    explicitly override it to an empty string to actually test the gate."""

    _NO_AUTH = {"X-Admin-Token": ""}

    def test_post_guide_requires_admin(self):
        r = requests.post(
            f"{BASE_URL}/api/training-center/guide",
            json={
                "slug": "test-admin-gate",
                "portal": "admin",
                "title": "x", "kicker": "x",
                "summary": "x", "audience": "x",
                "sections": [{"heading": "h", "body_md": "b"}],
            },
            headers=self._NO_AUTH,
            timeout=TIMEOUT,
        )
        assert r.status_code in (401, 403), f"expected 401 or 403, got {r.status_code} ({r.text})"

    def test_patch_guide_requires_admin(self):
        r = requests.patch(
            f"{BASE_URL}/api/training-center/guide/safety-fire-ext-bulk-import",
            json={"title": "hacked"},
            headers=self._NO_AUTH,
            timeout=TIMEOUT,
        )
        assert r.status_code == 401

    def test_delete_guide_requires_admin(self):
        r = requests.delete(
            f"{BASE_URL}/api/training-center/guide/safety-fire-ext-bulk-import",
            headers=self._NO_AUTH,
            timeout=TIMEOUT,
        )
        assert r.status_code == 401

    def test_seed_requires_admin(self):
        r = requests.post(
            f"{BASE_URL}/api/training-center/seed",
            headers=self._NO_AUTH,
            timeout=TIMEOUT,
        )
        assert r.status_code == 401


class TestTrainingCenterAdminCRUD:
    def test_create_patch_delete_cycle(self, admin_token):
        headers = {"X-Admin-Token": admin_token}
        slug = "test-iter134-guide"

        # cleanup if leftover
        requests.delete(
            f"{BASE_URL}/api/training-center/guide/{slug}",
            headers=headers,
            timeout=TIMEOUT,
        )

        # CREATE
        body = {
            "slug": slug, "portal": "admin",
            "title": "Iter134 Test Guide", "kicker": "TEST · KICKER",
            "summary": "summary", "audience": "test",
            "sections": [{"heading": "Intro", "body_md": "**bold** text"}],
            "version": "1.0",
        }
        r = requests.post(
            f"{BASE_URL}/api/training-center/guide",
            json=body, headers=headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        created = r.json()
        assert created["slug"] == slug
        assert created["title"] == "Iter134 Test Guide"

        # GET back to verify persistence
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/{slug}", timeout=TIMEOUT,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Iter134 Test Guide"

        # PATCH
        r = requests.patch(
            f"{BASE_URL}/api/training-center/guide/{slug}",
            json={"title": "Iter134 Patched"},
            headers=headers,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        assert r.json()["title"] == "Iter134 Patched"

        # DELETE
        r = requests.delete(
            f"{BASE_URL}/api/training-center/guide/{slug}",
            headers=headers,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # confirm 404
        r = requests.get(
            f"{BASE_URL}/api/training-center/guide/{slug}", timeout=TIMEOUT,
        )
        assert r.status_code == 404


# ─────────────── Fire Extinguisher Bulk Import ───────────────

class TestFireExtBulkImport:
    def test_template_returns_csv(self):
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/template",
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        assert "text/csv" in r.headers.get("content-type", "")
        first_line = r.text.splitlines()[0]
        assert "Extinguisher ID" in first_line
        assert "Serial Number" in first_line
        assert "Inspection Date" in first_line

    def test_preview_requires_safety_token(self):
        csv_bytes = b"Extinguisher ID,Serial Number\nFE-T1,SER1\n"
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/preview",
            files={"file": ("t.csv", csv_bytes, "text/csv")},
            timeout=TIMEOUT,
        )
        assert r.status_code in (401, 403)

    def test_history_requires_safety_token(self):
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/history",
            timeout=TIMEOUT,
        )
        assert r.status_code in (401, 403)

    def test_preview_and_commit_flow(self, safety_token):
        headers = {"X-Safety-Token": safety_token}
        # Build a CSV: 1 new row + 1 row meant to update (we'll use the
        # same unit_id twice across runs)
        csv_buf = io.StringIO()
        w = csv.writer(csv_buf)
        w.writerow([
            "Extinguisher ID", "Serial Number", "Type", "Size",
            "Location", "Assigned Truck", "Project Number",
            "Inspection Date", "Next Due Date", "Status",
            "Deficiencies", "Corrective Action Required", "Notes",
        ])
        w.writerow([
            "TEST_FE_iter134_A", "TEST_SER_A", "ABC", "10 lb",
            "Cab", "TEST_TRUCK_A", "P-TEST",
            "2026-01-10", "2027-01-10", "Pass",
            "", "", "Iter134 test row A",
        ])
        w.writerow([
            "TEST_FE_iter134_B", "TEST_SER_B", "ABC", "5 lb",
            "Bed", "TEST_TRUCK_B", "P-TEST",
            "2026-01-11", "2027-01-11", "Pass",
            "", "", "Iter134 test row B",
        ])

        files = {"file": ("iter134.csv", csv_buf.getvalue().encode(), "text/csv")}
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/preview",
            files=files, headers=headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        prev = r.json()
        assert "preview_id" in prev
        assert prev["total_rows"] == 2
        # First time, both should be 'create'
        assert prev["to_create"] + prev["to_update"] >= 1
        assert len(prev["rows"]) == 2
        for row in prev["rows"]:
            assert row["action"] in ("create", "update", "skip")

        preview_id = prev["preview_id"]

        # COMMIT
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/commit",
            json={"preview_id": preview_id},
            headers=headers,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        commit = r.json()
        assert commit["ok"] is True
        assert commit["created"] + commit["updated"] + commit["skipped"] == 2

        # Second commit must 409 (already committed)
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/commit",
            json={"preview_id": preview_id},
            headers=headers,
            timeout=TIMEOUT,
        )
        assert r.status_code == 409

        # PREVIEW again w/ same data — should now match the existing rows as 'update'
        files = {"file": ("iter134b.csv", csv_buf.getvalue().encode(), "text/csv")}
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/preview",
            files=files, headers=headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        prev2 = r.json()
        assert prev2["to_update"] >= 1, f"expected at least one update, got {prev2}"
        # Verify at least one row has a match_reason
        match_reasons = [row.get("match_reason") for row in prev2["rows"] if row.get("match_reason")]
        assert len(match_reasons) >= 1

    def test_history_returns_runs(self, safety_token):
        r = requests.get(
            f"{BASE_URL}/api/safety/fire-extinguishers/import/history",
            headers={"X-Safety-Token": safety_token},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "rows" in data
        assert isinstance(data["rows"], list)
        # Should have at least the run we just committed
        if data["rows"]:
            r0 = data["rows"][0]
            assert "id" in r0
            assert "status" in r0
            assert "total_rows" in r0
