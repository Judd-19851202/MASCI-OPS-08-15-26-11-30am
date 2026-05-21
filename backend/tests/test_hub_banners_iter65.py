"""Backend tests for Hub Banner Messaging System (iter65).

Covers:
- POST /api/admin/banners with auto-translate
- GET /api/banners/active (device annotation, expired filter, severity sort)
- ack/dismiss idempotency
- admin auth gating on /api/admin/banners
- PATCH severity + clear expires_at
- DELETE + audit log
- translate preview endpoint
- severity validation
"""
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ADMIN_PASSWORD = "MASCI1982!"

created_ids: list[str] = []


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    tok = data.get("token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def cleanup_banners(admin_headers):
    """Idempotent test-banner cleanup.

    Runs in TWO phases:

    1. **Pre-test sweep** (before yield): admin lists all banners and
       deletes anything whose `title_en` starts with the canonical
       `TEST_` prefix. This is a self-healing safety net — if a prior
       test run was interrupted (CTRL-C, timeout, pod restart) and left
       orphan TEST banners in the preview DB, they get cleaned up
       before the new run starts. Without this sweep, orphan TEST
       banners render on every preview page load and condition crews to
       ignore real advisories — a real operational-trust hazard.

    2. **Post-test sweep** (after yield): explicit per-id deletion
       (legacy behavior) PLUS a final TEST_-prefix sweep that catches
       any banner the per-test code created but never appended to
       `created_ids` (e.g. interrupted test, conditional skip path).

    The TEST_ prefix is the contract — every banner created by this
    test module uses `_create_banner` which defaults `title_en` to
    `TEST_Heat Advisory <hex>`. Banners created by the live admin UI
    or by production traffic NEVER start with `TEST_`, so this sweep
    is safe to run against the shared preview DB.
    """
    def _sweep_test_prefix():
        try:
            r = requests.get(f"{BASE_URL}/api/admin/banners", headers=admin_headers, timeout=20)
            if r.status_code != 200:
                return
            for b in (r.json() or {}).get("banners", []) or []:
                title = (b.get("title_en") or "")
                if title.startswith("TEST_"):
                    try:
                        requests.delete(
                            f"{BASE_URL}/api/admin/banners/{b['id']}",
                            headers=admin_headers,
                            timeout=15,
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    # Phase 1 · pre-test sweep — self-heal any prior-run orphan TEST_* banners.
    _sweep_test_prefix()

    yield

    # Phase 2a · explicit per-id cleanup (the original behavior).
    for bid in list(created_ids):
        try:
            requests.delete(f"{BASE_URL}/api/admin/banners/{bid}", headers=admin_headers, timeout=15)
        except Exception:
            pass

    # Phase 2b · belt-and-suspenders TEST_-prefix sweep — catches any
    # banner the test body created but never appended to created_ids
    # (e.g. early-exit, conditional skip, exception path).
    _sweep_test_prefix()


def _create_banner(headers, **overrides):
    payload = {
        "title_en": overrides.pop("title_en", f"TEST_Heat Advisory {uuid.uuid4().hex[:6]}"),
        "body_en": overrides.pop("body_en", "Drink water every 15 minutes."),
        "severity": overrides.pop("severity", "advisory"),
        "require_ack": overrides.pop("require_ack", False),
        "auto_translate": overrides.pop("auto_translate", True),
    }
    payload.update(overrides)
    r = requests.post(f"{BASE_URL}/api/admin/banners", headers=headers, json=payload, timeout=60)
    return r


class TestBannerCRUD:
    def test_create_banner_auto_translates_to_spanish(self, admin_headers):
        r = _create_banner(admin_headers, title_en="TEST_Heat Advisory", body_en="High heat today. Drink water.")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        b = data["banner"]
        assert "_id" not in b, "Mongo _id leaked"
        assert b["id"]
        assert b["title_en"] == "TEST_Heat Advisory"
        assert b["severity"] == "advisory"
        # Spanish fields populated (either translated or English fallback) but must be non-empty
        assert b["title_es"], "title_es must populate"
        assert b["body_es"], "body_es must populate"
        created_ids.append(b["id"])

    def test_list_admin_banners_requires_token(self):
        # conftest auto-attaches X-Admin-Token; override with an invalid one
        r = requests.get(
            f"{BASE_URL}/api/admin/banners",
            headers={"X-Admin-Token": "definitely-not-a-real-token"},
            timeout=15,
        )
        assert r.status_code in (401, 403), f"expected 401/403 with bad token, got {r.status_code}"

    def test_list_admin_banners_returns_stats(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/banners", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert isinstance(data["banners"], list)
        for b in data["banners"]:
            assert "ack_count" in b
            assert "dismiss_count" in b
            assert "_id" not in b

    def test_severity_validation_rejects_invalid(self, admin_headers):
        r = _create_banner(admin_headers, severity="emergency")
        assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text}"

    def test_patch_updates_only_provided_fields(self, admin_headers):
        r = _create_banner(admin_headers, severity="info")
        assert r.status_code == 200
        bid = r.json()["banner"]["id"]
        created_ids.append(bid)
        orig_title = r.json()["banner"]["title_en"]

        # PATCH severity only
        p = requests.patch(f"{BASE_URL}/api/admin/banners/{bid}", headers=admin_headers, json={"severity": "warning"}, timeout=15)
        assert p.status_code == 200, p.text
        upd = p.json()["banner"]
        assert upd["severity"] == "warning"
        assert upd["title_en"] == orig_title

    def test_patch_clear_expires_at(self, admin_headers):
        future = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
        r = _create_banner(admin_headers, expires_at=future, severity="info")
        assert r.status_code == 200
        bid = r.json()["banner"]["id"]
        created_ids.append(bid)
        assert r.json()["banner"]["expires_at"] is not None

        p = requests.patch(f"{BASE_URL}/api/admin/banners/{bid}", headers=admin_headers, json={"expires_at": ""}, timeout=15)
        assert p.status_code == 200, p.text
        assert p.json()["banner"]["expires_at"] is None

    def test_expired_banner_excluded_from_active(self, admin_headers):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        r = _create_banner(admin_headers, title_en="TEST_Expired_Banner", expires_at=past, severity="info")
        assert r.status_code == 200, r.text
        bid = r.json()["banner"]["id"]
        created_ids.append(bid)

        a = requests.get(f"{BASE_URL}/api/banners/active", timeout=15)
        assert a.status_code == 200
        ids = [b["id"] for b in a.json().get("banners", [])]
        assert bid not in ids, "expired banner should not appear in /banners/active"

    def test_active_sorted_critical_first(self, admin_headers):
        # Create info + critical
        r1 = _create_banner(admin_headers, title_en="TEST_info_sort", severity="info")
        r2 = _create_banner(admin_headers, title_en="TEST_critical_sort", severity="critical", require_ack=True)
        assert r1.status_code == 200 and r2.status_code == 200
        id_info = r1.json()["banner"]["id"]
        id_crit = r2.json()["banner"]["id"]
        created_ids.extend([id_info, id_crit])

        a = requests.get(f"{BASE_URL}/api/banners/active", timeout=15)
        assert a.status_code == 200
        banners_list = a.json()["banners"]
        sevs = [b["severity"] for b in banners_list if b["id"] in (id_info, id_crit)]
        # critical should appear before info in the list
        pos_crit = next(i for i, b in enumerate(banners_list) if b["id"] == id_crit)
        pos_info = next(i for i, b in enumerate(banners_list) if b["id"] == id_info)
        assert pos_crit < pos_info, f"critical must sort before info; got sevs ordered: {sevs}"

    def test_acknowledge_idempotent(self, admin_headers):
        r = _create_banner(admin_headers, severity="warning", require_ack=True)
        assert r.status_code == 200
        bid = r.json()["banner"]["id"]
        created_ids.append(bid)
        device = f"test-device-{uuid.uuid4().hex[:8]}"

        for _ in range(3):
            ack = requests.post(f"{BASE_URL}/api/banners/{bid}/acknowledge", json={"device_id": device}, timeout=15)
            assert ack.status_code == 200, ack.text

        # admin sees ack_count == 1 (idempotent via $addToSet)
        list_r = requests.get(f"{BASE_URL}/api/admin/banners", headers=admin_headers, timeout=15)
        match = next((b for b in list_r.json()["banners"] if b["id"] == bid), None)
        assert match is not None
        assert match["ack_count"] == 1, f"ack_count should be 1 idempotent, got {match['ack_count']}"

        # active feed with device_id annotates acknowledged=true
        a = requests.get(f"{BASE_URL}/api/banners/active", params={"device_id": device}, timeout=15)
        b = next((x for x in a.json()["banners"] if x["id"] == bid), None)
        assert b is not None
        assert b["acknowledged"] is True

    def test_dismiss_idempotent(self, admin_headers):
        r = _create_banner(admin_headers, severity="info")
        bid = r.json()["banner"]["id"]
        created_ids.append(bid)
        device = f"test-device-{uuid.uuid4().hex[:8]}"
        for _ in range(2):
            d = requests.post(f"{BASE_URL}/api/banners/{bid}/dismiss", json={"device_id": device}, timeout=15)
            assert d.status_code == 200
        list_r = requests.get(f"{BASE_URL}/api/admin/banners", headers=admin_headers, timeout=15)
        match = next((b for b in list_r.json()["banners"] if b["id"] == bid), None)
        assert match["dismiss_count"] == 1

    def test_acknowledge_unknown_banner_404(self):
        r = requests.post(f"{BASE_URL}/api/banners/nonexistent-id/acknowledge", json={"device_id": "dev-x"}, timeout=15)
        assert r.status_code == 404

    def test_translate_preview_endpoint(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/banners/translate",
            headers=admin_headers,
            json={"title_en": "Hurricane Warning", "body_en": "Secure all equipment immediately."},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert "title_es" in data and "body_es" in data
        assert data["title_es"]
        assert data["body_es"]

    def test_translate_preview_requires_admin(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/banners/translate",
            json={"title_en": "x", "body_en": "y"},
            headers={"X-Admin-Token": "definitely-not-a-real-token"},
            timeout=15,
        )
        assert r.status_code in (401, 403)

    def test_delete_and_audit_log(self, admin_headers):
        r = _create_banner(admin_headers, title_en="TEST_to_delete", severity="info")
        bid = r.json()["banner"]["id"]

        d = requests.delete(f"{BASE_URL}/api/admin/banners/{bid}", headers=admin_headers, timeout=15)
        assert d.status_code == 200
        assert d.json()["ok"] is True

        # GET active should not include it
        a = requests.get(f"{BASE_URL}/api/banners/active", timeout=15)
        ids = [b["id"] for b in a.json().get("banners", [])]
        assert bid not in ids

        # Audit log records create + delete
        au = requests.get(f"{BASE_URL}/api/admin/banners/{bid}/audit", headers=admin_headers, timeout=15)
        assert au.status_code == 200
        actions = [row["action"] for row in au.json()["audit"]]
        assert "create" in actions
        assert "delete" in actions


class TestRegression:
    """Verify existing endpoints still work alongside new banner module."""

    def test_admin_login_still_works(self):
        r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_daily_reports_endpoint_responds(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/daily-reports", headers=admin_headers, timeout=20)
        # Whether empty or populated, should be 200
        assert r.status_code == 200, f"daily-reports failed: {r.status_code} {r.text[:200]}"
