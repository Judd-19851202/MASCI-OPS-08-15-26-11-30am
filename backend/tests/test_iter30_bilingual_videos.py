"""Iteration-30 pre-deploy QA — bilingual training-video schema.

Verifies:
  * GET /api/training/videos returns the new {en, es} shape for the 3 seeded
    field slugs and the URLs match the expected language markers.
  * PUT /api/admin/training/videos accepts BOTH legacy single-string and new
    {en, es} payloads, merge-updates correctly, and round-trips via GET.
  * PUT is admin-strict: PM token (supplied via X-PM-Token) must 401.
  * Old single-string entries get normalized to the new shape on read.

Conftest auto-injects X-Admin-Token on every requests call to the backend
host. For the negative-auth case we explicitly strip X-Admin-Token and
substitute X-PM-Token so we can prove the admin-strict gate rejects PM.
"""
import os
from pathlib import Path

import pytest
import requests


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

PM_PASSWORD = _read_kv(Path("/app/backend/.env"), "PM_PASSWORD") or "Maddix123!"


# --- Seeded bilingual slugs + expected language fingerprints -------------
SEEDED_SLUGS = {
    "field-01-hub-navigation": {
        "en_fingerprint": ("Hub_Navigating", "FINAL"),
        "es_fingerprint": ("Navegando", "_ES_"),
    },
    "field-02-daily-report": {
        "en_fingerprint": ("DailyReport", "FINAL"),
        "es_fingerprint": ("ReporteDiario", "_ES_"),
    },
    "field-03-equipment-preop": {
        "en_fingerprint": ("PreOp_FINAL",),
        "es_fingerprint": ("PreOp_ES",),
    },
}


# --- GET /api/training/videos shape ---------------------------------------
class TestTrainingVideosGet:
    def test_response_shape_is_dict_per_slug(self):
        r = requests.get(f"{BASE_URL}/api/training/videos", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "videos" in body and isinstance(body["videos"], dict)
        for slug in SEEDED_SLUGS:
            assert slug in body["videos"], f"missing slug {slug} in response"
            entry = body["videos"][slug]
            assert isinstance(entry, dict), f"entry for {slug} not dict: {entry}"
            assert "en" in entry and "es" in entry, f"missing en/es keys for {slug}"

    @pytest.mark.parametrize("slug,expected", list(SEEDED_SLUGS.items()))
    def test_en_url_contains_language_fingerprint(self, slug, expected):
        r = requests.get(f"{BASE_URL}/api/training/videos", timeout=15)
        entry = r.json()["videos"][slug]
        en_url = entry["en"]
        assert en_url.startswith("https://"), f"EN URL must be https: {en_url}"
        assert any(fp in en_url for fp in expected["en_fingerprint"]), (
            f"EN URL for {slug} missing any of {expected['en_fingerprint']}: {en_url}"
        )

    @pytest.mark.parametrize("slug,expected", list(SEEDED_SLUGS.items()))
    def test_es_url_contains_language_fingerprint(self, slug, expected):
        r = requests.get(f"{BASE_URL}/api/training/videos", timeout=15)
        entry = r.json()["videos"][slug]
        es_url = entry["es"]
        assert es_url.startswith("https://"), f"ES URL must be https: {es_url}"
        assert any(fp in es_url for fp in expected["es_fingerprint"]), (
            f"ES URL for {slug} missing any of {expected['es_fingerprint']}: {es_url}"
        )

    def test_en_and_es_urls_differ_per_slug(self):
        r = requests.get(f"{BASE_URL}/api/training/videos", timeout=15)
        videos = r.json()["videos"]
        for slug in SEEDED_SLUGS:
            en = videos[slug]["en"]
            es = videos[slug]["es"]
            assert en and es, f"{slug} missing en or es"
            assert en != es, f"{slug} EN and ES URLs identical — bad seed"


# --- PUT /api/admin/training/videos admin-strict gate --------------------
class TestTrainingVideosPutAuth:
    def _pm_token(self):
        r = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"password": PM_PASSWORD},
            timeout=10,
            headers={"X-Admin-Token": ""},  # make sure auto-inject doesn't taint
        )
        if r.status_code != 200:
            pytest.skip(f"PM login failed ({r.status_code}) — cannot test gate")
        return r.json().get("token", "")

    def test_pm_token_rejected_by_admin_strict(self):
        pm_token = self._pm_token()
        r = requests.put(
            f"{BASE_URL}/api/admin/training/videos",
            json={"videos": {"field-01-hub-navigation": {"en": "https://example.com/a.mp4"}}},
            timeout=10,
            headers={"X-Admin-Token": "", "X-PM-Token": pm_token},
        )
        assert r.status_code in (401, 403), (
            f"PM token must be rejected on admin-strict write, got {r.status_code}: {r.text[:200]}"
        )

    def test_no_token_rejected(self):
        r = requests.put(
            f"{BASE_URL}/api/admin/training/videos",
            json={"videos": {}},
            timeout=10,
            headers={"X-Admin-Token": ""},
        )
        assert r.status_code in (401, 403), r.status_code


# --- PUT round-trip: new bilingual shape + legacy string + clear ---------
class TestTrainingVideosPutRoundtrip:
    TEST_SLUG = "TEST_iter30_bilingual_slug"

    def teardown_method(self):
        # Clear the test slug (send None → deletes, per server logic)
        try:
            requests.put(
                f"{BASE_URL}/api/admin/training/videos",
                json={"videos": {self.TEST_SLUG: None}},
                timeout=10,
            )
        except Exception:
            pass

    def test_put_new_bilingual_shape_roundtrip(self):
        payload = {
            "videos": {
                self.TEST_SLUG: {
                    "en": "https://example.com/iter30_en.mp4",
                    "es": "https://example.com/iter30_es.mp4",
                }
            }
        }
        r = requests.put(
            f"{BASE_URL}/api/admin/training/videos", json=payload, timeout=10
        )
        assert r.status_code == 200, r.text
        # Round-trip via GET
        got = requests.get(f"{BASE_URL}/api/training/videos", timeout=10).json()["videos"]
        assert self.TEST_SLUG in got
        assert got[self.TEST_SLUG]["en"] == "https://example.com/iter30_en.mp4"
        assert got[self.TEST_SLUG]["es"] == "https://example.com/iter30_es.mp4"

    def test_put_legacy_single_string_stored_as_en(self):
        payload = {"videos": {self.TEST_SLUG: "https://example.com/iter30_legacy.mp4"}}
        r = requests.put(
            f"{BASE_URL}/api/admin/training/videos", json=payload, timeout=10
        )
        assert r.status_code == 200, r.text
        got = requests.get(f"{BASE_URL}/api/training/videos", timeout=10).json()["videos"]
        assert got[self.TEST_SLUG]["en"] == "https://example.com/iter30_legacy.mp4"
        assert got[self.TEST_SLUG]["es"] == ""

    def test_put_en_only_then_es_only_merges(self):
        # Set EN only
        requests.put(
            f"{BASE_URL}/api/admin/training/videos",
            json={"videos": {self.TEST_SLUG: {"en": "https://example.com/en.mp4"}}},
            timeout=10,
        )
        # Then set ES only — EN must survive
        r = requests.put(
            f"{BASE_URL}/api/admin/training/videos",
            json={"videos": {self.TEST_SLUG: {"es": "https://example.com/es.mp4"}}},
            timeout=10,
        )
        assert r.status_code == 200
        got = requests.get(f"{BASE_URL}/api/training/videos", timeout=10).json()["videos"]
        assert got[self.TEST_SLUG]["en"] == "https://example.com/en.mp4", "EN got wiped on ES-only put"
        assert got[self.TEST_SLUG]["es"] == "https://example.com/es.mp4"

    def test_default_field_slugs_untouched_after_admin_write(self):
        """A PUT on a custom slug must not disturb the 3 seeded field slugs."""
        before = requests.get(f"{BASE_URL}/api/training/videos", timeout=10).json()["videos"]
        requests.put(
            f"{BASE_URL}/api/admin/training/videos",
            json={"videos": {self.TEST_SLUG: {"en": "https://example.com/x.mp4"}}},
            timeout=10,
        )
        after = requests.get(f"{BASE_URL}/api/training/videos", timeout=10).json()["videos"]
        for slug in SEEDED_SLUGS:
            assert before[slug] == after[slug], (
                f"{slug} changed after unrelated PUT: {before[slug]} -> {after[slug]}"
            )
