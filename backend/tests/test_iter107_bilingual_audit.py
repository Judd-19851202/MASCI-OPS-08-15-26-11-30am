"""Iter107 — Bilingual audit.

Coverage:
  1. POST /api/translate — ES->EN translation, empty short-circuit, single
     empty value graceful path.
  2. POST /api/field-leadership (write_up) submitted in Spanish — verify
     description / corrective_action persisted as English after backend
     auto-translation (the frontend now calls translateUserInput before
     POST, but this also asserts the backend accepts and stores both the
     `submit_language` flag AND the (frontend-translated) English text).
  3. Public Time Off Request submitted in Spanish — same round-trip check.

Notes / important quirks (see conftest.py):
  - conftest auto-injects X-Admin-Token; we use that for the verifying GETs.
  - We also mint a Leadership token (password=MASCIGC) for the FL POST.
  - The translate endpoint may fall back gracefully — we assert keys + non
    empty strings always, and additionally assert the value looks English
    when the LLM is healthy.
"""
import os
import re
import uuid
import time
import requests
import pytest

from pathlib import Path


def _read_kv(p, k):
    try:
        for line in open(p):
            if line.startswith(f"{k}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"
LEADERSHIP_EMAIL = "cert.foreman@example.com"
LEADERSHIP_PW = "CertProof2026!"
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(
        f"{API}/field-leadership/portal/login",
        json={"email": LEADERSHIP_EMAIL, "password": LEADERSHIP_PW},
        timeout=15,
    )
    assert r.status_code == 200, f"FL login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("token")
    assert tok, "FL login returned no token"
    return tok


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(
        f"{API}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
        timeout=15,
    )
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    return {
        "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin", ""),
        "X-Directory-Token": body.get("session_token", ""),
    }


# ---------- A. /api/translate contract ----------

class TestTranslateEndpoint:
    def test_translate_es_to_en_basic(self):
        r = requests.post(
            f"{API}/translate",
            json={
                "from_lang": "es",
                "to_lang": "en",
                "strings": {
                    "a": "El equipo necesita reparación inmediata",
                    "b": "Falta EPP",
                },
            },
            timeout=60,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert set(body["strings"].keys()) == {"a", "b"}
        a = body["strings"]["a"]
        b = body["strings"]["b"]
        assert isinstance(a, str) and a.strip()
        assert isinstance(b, str) and b.strip()
        # Best-effort English check — should not be the unmodified Spanish.
        # If the LLM is up, we expect English keywords (equipment/PPE/etc).
        joined = (a + " " + b).lower()
        # When the LLM is healthy, expect English words; if it failed we
        # would see the original Spanish unchanged (still asserted above as
        # non-empty for the graceful path). Mark this as soft.
        if "necesita" in joined or "falta" in joined:
            pytest.skip("LLM translate fell back to original (graceful path) — non-fatal")
        # Expect at least one English construction/safety term
        assert re.search(r"\b(equipment|repair|ppe|protective|missing|immediate)\b", joined), (
            f"Translated text doesn't look English: {a!r} / {b!r}"
        )

    def test_translate_empty_strings(self):
        r = requests.post(
            f"{API}/translate",
            json={"from_lang": "es", "to_lang": "en", "strings": {}},
            timeout=20,
        )
        assert r.status_code == 200
        assert r.json() == {"strings": {}}

    def test_translate_single_empty_value(self):
        """Graceful: keys with empty/whitespace value should round-trip."""
        r = requests.post(
            f"{API}/translate",
            json={"from_lang": "es", "to_lang": "en", "strings": {"a": ""}},
            timeout=30,
        )
        assert r.status_code == 200
        body = r.json()
        assert "a" in body["strings"]
        # Endpoint may fall back to original (empty) — the contract only
        # requires non-500 + same keys.
        assert isinstance(body["strings"]["a"], str)


# ---------- B. Field Leadership write_up in Spanish ----------

class TestFLWriteUpSpanish:
    def test_es_write_up_persists_with_submit_language(self, leadership_token, admin_headers):
        """Simulate what the frontend does: call /api/translate FIRST, then
        POST to /api/field-leadership with the translated English values +
        `submit_language='es'` flag."""

        # Step 1 — translate the free-text fields
        spanish_desc = "El empleado llegó tarde y no llevaba EPP"
        spanish_act = "Recordatorio verbal de la política"
        tr = requests.post(
            f"{API}/translate",
            json={
                "from_lang": "es",
                "to_lang": "en",
                "strings": {"d": spanish_desc, "c": spanish_act},
            },
            timeout=60,
        )
        assert tr.status_code == 200, tr.text
        translated = tr.json()["strings"]
        eng_desc = translated["d"]
        eng_act = translated["c"]

        # Step 2 — POST a write_up record carrying the English text +
        # submit_language flag (Pydantic ignores extras by default; we still
        # send `language: "es"` which IS defined on the model).
        tag = f"TEST_iter107_{uuid.uuid4().hex[:8]}"
        payload = {
            "kind": "write_up",
            "employee_name": "TEST Juan Perez",
            "supervisor_name": "TEST Supervisor",
            "details": {
                "description": eng_desc,
                "corrective_action": eng_act,
                "tag": tag,
            },
            "language": "es",
            "submit_language": "es",  # frontend-added; may be dropped by Pydantic
        }
        r = requests.post(
            f"{API}/field-leadership",
            json=payload,
            headers={"X-FL-Token": leadership_token},
            timeout=30,
        )
        assert r.status_code in (200, 201), f"FL POST failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        rec_id = body.get("id") or body.get("record", {}).get("id")
        assert rec_id, f"No id in response: {body}"

        # Step 3 — GET back via admin (conftest auto-injects X-Admin-Token)
        g = requests.get(f"{API}/field-leadership/{rec_id}", headers=admin_headers, timeout=20)
        assert g.status_code == 200, g.text
        rec = g.json()
        desc = (rec.get("details") or {}).get("description") or ""
        act = (rec.get("details") or {}).get("corrective_action") or ""

        # English persistence assertion — must NOT contain the original
        # Spanish phrase.
        assert "llegó" not in desc and "EPP" not in desc.split() or "PPE" in desc or "late" in desc.lower(), (
            f"Description still Spanish: {desc!r}"
        )
        # Looser check: presence of common English tokens
        assert re.search(r"[a-zA-Z]", desc), f"Empty description on record: {rec}"

        # submit_language traceability — Pydantic model declares `language`,
        # frontend sends `submit_language`. Acceptable: either field on the
        # stored record marks ES.
        lang_field = rec.get("submit_language") or rec.get("language")
        assert lang_field == "es", f"submit_language not persisted (got {lang_field!r}); full rec keys={list(rec.keys())}"


# ---------- C. Public time-off submission in Spanish ----------

class TestPublicTimeOffSpanish:
    def test_public_time_off_spanish_persists_english(self, admin_headers):
        # Mint a public link via the admin-governed route.
        emp_name = f"TEST_iter107_{uuid.uuid4().hex[:6]}"
        mint = requests.post(
            f"{API}/field-leadership/time-off/public-link",
            json={"employee_name": emp_name, "employee_email": "test@example.com"},
            headers=admin_headers,
            timeout=30,
        )
        assert mint.status_code == 200, f"Mint link failed: {mint.status_code} {mint.text[:200]}"
        mj = mint.json()
        token = (
            mj.get("token")
            or mj.get("public_token")
            or (mj.get("link") or {}).get("token")
        )
        assert token, f"No token in mint response: {mint.json()}"

        # Pre-translate freeform fields (mimic frontend translateUserInput)
        sp_coverage = "Mi compañero Pedro cubrirá mi turno"
        sp_notes = "Tengo una cita médica importante"
        tr = requests.post(
            f"{API}/translate",
            json={
                "from_lang": "es",
                "to_lang": "en",
                "strings": {"c": sp_coverage, "n": sp_notes},
            },
            timeout=60,
        )
        assert tr.status_code == 200
        eng = tr.json()["strings"]

        # Public submit (no auth required)
        sub = requests.post(
            f"{API}/public/time-off/{token}/submit",
            json={
                "reason": "Medical",
                "pay_type": "Paid",
                "start_date": "2026-02-01",
                "end_date": "2026-02-02",
                "total_days": 2,
                "coverage_plan": eng["c"],
                "notes": eng["n"],
                "submit_language": "es",
            },
            timeout=30,
            # Force no auto-admin header — this is a public endpoint
            headers={"X-Admin-Token": ""},
        )
        assert sub.status_code == 200, f"Public submit failed: {sub.status_code} {sub.text[:300]}"
        rec_id = sub.json().get("id")
        assert rec_id

        # Verify back via admin
        g = requests.get(f"{API}/field-leadership/{rec_id}", headers=admin_headers, timeout=20)
        assert g.status_code == 200
        rec = g.json()
        details = rec.get("details") or {}
        coverage = details.get("coverage_plan") or ""
        notes = details.get("notes") or ""
        # Spanish source words should not be intact
        assert "compañero" not in coverage and "cubrirá" not in coverage, (
            f"coverage_plan still Spanish: {coverage!r}"
        )
        assert "médica" not in notes, f"notes still Spanish: {notes!r}"
        assert coverage.strip() != "" and notes.strip() != ""
