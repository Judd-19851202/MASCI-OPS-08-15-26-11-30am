"""Track 24.3 - Backend API E2E tests for DR V3 ES->EN translation endpoint + regressions."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
TRANSLATE_URL = f"{BASE_URL}/api/translate/dr-v3-freetext"

SPANISH_CHARS = set("ñáéíóúü¿¡ÑÁÉÍÓÚÜ")


def _has_spanish_chars(s: str) -> bool:
    return any(c in SPANISH_CHARS for c in s)


class TestTranslateDrV3Freetext:
    def test_success_small_es_payload_preserves_tokens(self):
        payload = {
            "fields": {
                "excavation.soil_notes": "Suelo tipo B con piedras grandes",
                "general_notes": "Cuadrilla trabajando en Sta 12+50 con excavadora 24-12",
            },
            "preserve_tokens": ["Sta 12+50", "24-12"],
        }
        r = requests.post(TRANSLATE_URL, json=payload, timeout=60)
        assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"
        data = r.json()
        assert data.get("ok") is True, data
        translations = data.get("translations", {})
        assert "excavation.soil_notes" in translations
        assert "general_notes" in translations
        gn = translations["general_notes"]
        assert "Sta 12+50" in gn, f"preserve token missing: {gn}"
        assert "24-12" in gn, f"preserve token missing: {gn}"
        assert not _has_spanish_chars(gn), f"spanish chars leaked: {gn}"
        assert not _has_spanish_chars(translations["excavation.soil_notes"])
        meta = data.get("translation_metadata") or {}
        # Provider/model/timestamp are present under translation_* keys
        assert meta.get("translation_provider"), meta
        assert meta.get("translation_model"), meta
        assert meta.get("translation_timestamp"), meta
        assert "translated_field_paths" in meta

    def test_empty_fields_returns_ok_empty(self):
        r = requests.post(TRANSLATE_URL, json={"fields": {}}, timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("ok") is True
        assert data.get("translations", {}) == {}

    def test_payload_too_large_returns_413(self):
        big_text = "x" * 40001
        r = requests.post(TRANSLATE_URL, json={"fields": {"a": big_text}}, timeout=30)
        assert r.status_code == 413, f"expected 413, got {r.status_code}: {r.text[:200]}"
        body = r.text
        assert "payload_too_large" in body or "too_large" in body.lower()

    def test_too_many_fields_returns_413(self):
        fields = {f"k{i}": "hola" for i in range(101)}
        r = requests.post(TRANSLATE_URL, json={"fields": fields}, timeout=30)
        assert r.status_code == 413, f"expected 413, got {r.status_code}: {r.text[:200]}"
        assert "too_many_fields" in r.text or "too_many" in r.text.lower()


class TestDailyReportsRegression:
    def test_next_number_endpoint_ok(self):
        r = requests.get(f"{BASE_URL}/api/daily-reports/next-number", timeout=15)
        assert r.status_code == 200, r.text[:200]

    def test_en_submit_regression(self):
        body = {
            "project_name": "TEST_Regression Project",
            "project_number": "TEST-24-3-REG",
            "location": "TEST loc",
            "report_date": "2026-01-15",
            "prepared_by": "TEST User",
            "general_notes": "Standard EN submission regression",
            "submit_language": "en",
        }
        r = requests.post(f"{BASE_URL}/api/daily-reports", json=body, timeout=30)
        # Accept 200/201/422 (validation may want more fields); assert NOT 500
        assert r.status_code < 500, f"server error: {r.status_code} {r.text[:300]}"

    def test_excavation_flow_regression_422(self):
        body = {
            "project_name": "TEST_Excavation Regression",
            "project_number": "TEST-24-3-EXC",
            "location": "TEST",
            "report_date": "2026-01-15",
            "prepared_by": "TEST",
            "general_notes": "",
            "submit_language": "en",
            "excavation_activity_today": "Yes",
            "linked_excavation_ids": [],
        }
        r = requests.post(f"{BASE_URL}/api/daily-reports", json=body, timeout=30)
        # Expected: 422 excavation_record_required
        assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text[:300]}"
        assert "excavation_record_required" in r.text or "excavation" in r.text.lower()
