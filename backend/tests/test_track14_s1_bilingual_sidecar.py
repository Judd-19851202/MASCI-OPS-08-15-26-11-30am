"""
TRACK 14.0-S1 Amendment A · bilingual record sidecar regression tests.

Verifies the foundational contract for bilingual operation:

  • Original-language strings can be persisted in a sidecar collection
    keyed by (form_type, form_id) without touching the canonical form
    collection's schema.
  • Accented Spanish characters round-trip character-for-character.
  • Reads succeed for any authenticated portal token; reject unauth.
  • Empty originals → graceful no-op response (not an error).
  • Size caps reject hostile payloads.

Run:
    cd /app/backend && python -m pytest tests/test_track14_s1_bilingual_sidecar.py -v
"""
from __future__ import annotations

import os
import uuid

import pytest


@pytest.fixture(scope="module")
def api_url() -> str:
    """Read the public preview URL from /app/frontend/.env."""
    env_path = "/app/frontend/.env"
    if not os.path.exists(env_path):
        pytest.skip("frontend .env missing")
    with open(env_path) as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    pytest.skip("REACT_APP_BACKEND_URL not in .env")


@pytest.fixture(scope="module")
def admin_token(api_url) -> str:
    """Get a multi-login admin token."""
    requests = pytest.importorskip("requests")
    r = requests.post(
        f"{api_url}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=45,
    )
    assert r.status_code == 200, r.text
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok, "admin portal token missing"
    return tok


@pytest.fixture
def cert_hr_token(api_url) -> str:
    requests = pytest.importorskip("requests")
    r = requests.post(
        f"{api_url}/api/hr/login",
        json={"email": "cert.hr@example.com", "password": "CertProof2026!"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_round_trip_preserves_spanish_accents(api_url, admin_token):
    requests = pytest.importorskip("requests")
    form_id = f"TRUST-S1-CERT-{uuid.uuid4().hex[:8]}"
    originals = {
        "/discussion_notes": "Se instalaron 120 pies lineales de tubería.",
        "/hazards_reviewed": "Riesgo de derrumbe en la zanja. Caja de zanja en uso. Información crítica.",
        "/action_items": "Reunión mañana a las 7 AM. Verificar atención al equipo.",
    }
    r = requests.post(
        f"{api_url}/api/bilingual-records",
        headers={"X-Admin-Token": admin_token},
        json={
            "form_type": "meeting",
            "form_id": form_id,
            "original_language": "es",
            "originals": originals,
            "translation_source": "llm",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json()["stored"] is True

    g = requests.get(
        f"{api_url}/api/bilingual-records/meeting/{form_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert g.status_code == 200, g.text
    body = g.json()
    assert body["found"] is True
    rec = body["record"]
    # Character-for-character preservation — accents intact.
    for k, v in originals.items():
        assert rec["originals"][k] == v, (
            f"original at {k!r} drifted: stored={rec['originals'][k]!r} "
            f"expected={v!r}"
        )
    assert rec["original_language"] == "es"
    assert rec["translation_source"] == "llm"


def test_empty_originals_is_graceful_noop(api_url, admin_token):
    requests = pytest.importorskip("requests")
    r = requests.post(
        f"{api_url}/api/bilingual-records",
        headers={"X-Admin-Token": admin_token},
        json={
            "form_type": "incident",
            "form_id": f"TRUST-S1-EMPTY-{uuid.uuid4().hex[:6]}",
            "original_language": "es",
            "originals": {},
            "translation_source": "llm",
        },
        timeout=15,
    )
    assert r.status_code == 200
    assert r.json()["stored"] is False
    assert r.json()["reason"] == "empty_originals"


def test_oversized_payload_rejected(api_url, admin_token):
    requests = pytest.importorskip("requests")
    huge = "x" * 9000  # >8 KB single field
    r = requests.post(
        f"{api_url}/api/bilingual-records",
        headers={"X-Admin-Token": admin_token},
        json={
            "form_type": "meeting",
            "form_id": "TRUST-S1-BIG",
            "original_language": "es",
            "originals": {"/notes": huge},
        },
        timeout=15,
    )
    assert r.status_code == 413, r.text


def test_too_many_originals_rejected(api_url, admin_token):
    requests = pytest.importorskip("requests")
    too_many = {f"/k{i}": f"valor {i}" for i in range(100)}
    r = requests.post(
        f"{api_url}/api/bilingual-records",
        headers={"X-Admin-Token": admin_token},
        json={
            "form_type": "meeting",
            "form_id": "TRUST-S1-TOOMANY",
            "original_language": "es",
            "originals": too_many,
        },
        timeout=15,
    )
    assert r.status_code == 413, r.text


def test_cross_portal_read_allowed(api_url, admin_token, cert_hr_token):
    """Any authenticated portal token may read the sidecar — needed so
    PMs / HR / Safety viewing a record in their portal can render the
    bilingual original alongside the English canonical content."""
    requests = pytest.importorskip("requests")
    form_id = f"TRUST-S1-CROSS-{uuid.uuid4().hex[:8]}"
    # Admin writes
    requests.post(
        f"{api_url}/api/bilingual-records",
        headers={"X-Admin-Token": admin_token},
        json={
            "form_type": "incident",
            "form_id": form_id,
            "original_language": "es",
            "originals": {"/description": "Casi caída desde plataforma."},
        },
        timeout=15,
    ).raise_for_status()
    # HR reads
    g = requests.get(
        f"{api_url}/api/bilingual-records/incident/{form_id}",
        headers={"X-HR-Token": cert_hr_token},
        timeout=15,
    )
    assert g.status_code == 200, g.text
    assert g.json()["record"]["originals"]["/description"] == \
        "Casi caída desde plataforma."


def test_unauthenticated_get_blocked(api_url):
    requests = pytest.importorskip("requests")
    r = requests.get(
        f"{api_url}/api/bilingual-records/meeting/whatever",
        timeout=15,
    )
    assert r.status_code == 401


def test_missing_record_returns_found_false(api_url, admin_token):
    requests = pytest.importorskip("requests")
    r = requests.get(
        f"{api_url}/api/bilingual-records/meeting/DEFINITELY-NOT-A-REAL-ID",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert r.status_code == 200
    assert r.json()["found"] is False
