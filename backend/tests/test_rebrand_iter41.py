"""Iter 41: Rebrand (ForgedOps LLC), PDF footers, auth flows, smoke routes."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ADMIN_PWD = "MASCI1982!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PWD = "ChrisRocksThis2026"
SHOP_PWD = "Nothappy123!"
SAFETY_PWD = "1982"
DEV_PWD = "Maddix8530!"


# ── Auth flows ────────────────────────────────────────
class TestAuth:
    def test_admin_login(self):
        r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PWD}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("token")

    def test_pm_login(self):
        r = requests.post(f"{BASE_URL}/api/pm/login", json={"email": PM_EMAIL, "password": PM_PWD}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("token")

    def test_shop_login(self):
        r = requests.post(f"{BASE_URL}/api/shop/login", json={"password": SHOP_PWD}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("token")

    def test_safety_forms_login(self):
        r = requests.post(f"{BASE_URL}/api/safety-forms/login", json={"password": SAFETY_PWD}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("token")

    def test_dev_login(self):
        r = requests.post(f"{BASE_URL}/api/dev/login", json={"password": DEV_PWD}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("token")


# ── Health / version ──────────────────────────────────
class TestHealthVersion:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200

    def test_version(self):
        r = requests.get(f"{BASE_URL}/api/version", timeout=15)
        assert r.status_code == 200


# ── PDF footer rebrand ────────────────────────────────
@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PWD}, timeout=20)
    assert r.status_code == 200
    return {"X-Admin-Token": r.json()["token"]}


def _pdf_text(content: bytes) -> str:
    """Extract text from PDF using pypdf (decompresses FlateDecode streams)."""
    import io as _io
    import pypdf
    reader = pypdf.PdfReader(_io.BytesIO(content))
    chunks = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            pass
    return "\n".join(chunks)


class TestPdfFooters:
    def _assert_footer(self, content: bytes, ctx: str):
        assert content[:4] == b"%PDF", f"{ctx}: not a PDF (got {content[:8]!r})"
        text = _pdf_text(content)
        # Must include new branding
        assert "ForgedOps" in text, f"{ctx}: ForgedOps not found in PDF"
        assert "MASCI HUB" in text, f"{ctx}: 'MASCI HUB' not in PDF"
        assert "2026" in text, f"{ctx}: 2026 copyright not in PDF"
        # Must NOT include old company name (person name 'Jaymn Judd' allowed,
        # 'Judd Group' is the company brand we removed)
        assert "Judd Group" not in text, f"{ctx}: stale 'Judd Group' still present"

    def test_daily_report_pdf_render(self):
        """Render a Daily Report PDF directly via pdf_render.render_record_pdf
        (no GET-by-id endpoint exists). Verifies the new footer."""
        import sys
        sys.path.insert(0, "/app/backend")
        from pdf_render import render_record_pdf
        record = {
            "id": "TEST_DR_REBRAND",
            "report_date": "2026-05-07",
            "project_number": "TEST-001",
            "project_name": "Rebrand Test Job",
            "prepared_by": "Test User",
            "weather": "Clear",
            "crew_count": 4,
            "tasks_completed": "Rebrand verification",
        }
        pdf_bytes = render_record_pdf("daily-report", record)
        self._assert_footer(pdf_bytes, "daily-report PDF (direct render)")

    def test_inspection_pdf_render(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from pdf_render import render_record_pdf
        record = {
            "id": "TEST_INSP_REBRAND",
            "inspection_date": "2026-05-07",
            "project_number": "TEST-001",
            "project_name": "Rebrand Test Job",
            "inspector_name": "Test Inspector",
            "items": [],
        }
        pdf_bytes = render_record_pdf("inspection", record)
        self._assert_footer(pdf_bytes, "inspection PDF (direct render)")

    def test_training_packet_en(self):
        # public endpoint for field track
        r = requests.get(f"{BASE_URL}/api/training/packet.pdf?track=field&lang=en", timeout=120)
        assert r.status_code == 200, r.text[:300]
        self._assert_footer(r.content, "training packet EN")

    def test_training_packet_es(self):
        r = requests.get(f"{BASE_URL}/api/training/packet.pdf?track=field&lang=es", timeout=120)
        assert r.status_code == 200, r.text[:300]
        self._assert_footer(r.content, "training packet ES")

    def test_email_sender_format_uses_forgedops_naming(self):
        """The email sender format is 'MASCI HUB Notifications <{SENDER_EMAIL}>'.
        We verify by reading server.py source — the unified literal must appear
        and there should be NO references to 'Judd Group' as a sender."""
        with open("/app/backend/server.py", "r") as f:
            src = f.read()
        assert 'MASCI HUB Notifications' in src, "expected 'MASCI HUB Notifications' sender literal"
        # Person name 'Jaymn Judd' OK, but 'Judd Group' as sender is not
        # We don't inspect every line, just confirm no 'Judd Group <' occurrences
        assert 'Judd Group <' not in src
        assert 'Judd Group LLC' not in src
