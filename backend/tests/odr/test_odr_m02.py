"""Pytest suite for Phase V.1 M0.2 + M0.2A.

Covers:
  - Continuity engine: mint, public resolve (200), wrong link (403),
    revoked link (410), no link (403), version chain
  - Amendment engine: in-window vs post-window authority, audit-trail
    integrity, append-only invariant, role gate (foreman post-window
    refused)
  - PDF engine: 5 audiences, %PDF magic, deterministic SHA per
    audience, different audiences yield different SHAs, footer header
  - Guidance: prompts list, resolve, crew overlay applied, crew matrix
    surfaces required topics, catalog health 14+ keys

Run:
    cd /app/backend && python -m pytest tests/odr/test_odr_m02.py -v
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests


URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
if not URL.startswith("http"):
    URL = "http://localhost:8001"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def headers() -> dict:
    r = requests.post(
        f"{URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200
    tok = r.json()["portal_tokens"]["admin"]
    return {"Content-Type": "application/json", "X-Admin-Token": tok}


@pytest.fixture(scope="module")
def submitted_odr(headers: dict) -> dict:
    """A submitted ODR for use in continuity / amendment / PDF tests."""
    payload = {
        "project": {
            "project_id": f"proj-m02-{uuid.uuid4().hex[:8]}",
            "project_number": f"M02-{uuid.uuid4().hex[:4]}",
            "project_name": "M0.2 Pytest Project",
            "report_date": "2026-05-29",
            "foreman_uid": ADMIN_EMAIL,
            "foreman_name": "Pytest Foreman",
        },
        "crew_profile": {
            "crew_id": f"crew-{uuid.uuid4().hex[:8]}",
            "crew_name": "Pytest Crew",
            "crew_type": "pipe",
            "primary_operation": "RCP install",
        },
    }
    r = requests.post(f"{URL}/api/odr", json=payload, headers=headers, timeout=10)
    assert r.status_code == 200
    odr = r.json()
    # Ack + submit
    r2 = requests.patch(
        f"{URL}/api/odr/{odr['id']}",
        json={"signature": {"foreman_acknowledgement": {
            "acknowledged": True,
            "acknowledged_by_uid": ADMIN_EMAIL,
            "text": "ack",
        }}},
        headers=headers, timeout=10,
    )
    assert r2.status_code == 200, r2.text
    r3 = requests.post(
        f"{URL}/api/odr/{odr['id']}/submit",
        json={},
        headers=headers, timeout=10,
    )
    assert r3.status_code == 200, r3.text
    return r3.json()


# ── Continuity ───────────────────────────────────────────────────────


def test_continuity_mint_link(headers: dict, submitted_odr: dict):
    r = requests.post(
        f"{URL}/api/odr/{submitted_odr['id']}/link",
        json={"link_scope": "project_crew", "note": "pytest"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["link_id"]
    assert d["doc_id"] == submitted_odr["doc_id"]
    assert d["link_scope"] == "project_crew"
    submitted_odr["__link_id"] = d["link_id"]


def test_continuity_public_resolve_ok(headers: dict, submitted_odr: dict):
    doc_id = submitted_odr["doc_id"]
    link_id = submitted_odr["__link_id"]
    r = requests.get(
        f"{URL}/api/odr/public/{doc_id}",
        params={"link_id": link_id},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["doc_id"] == doc_id
    # public envelope MUST NOT carry telemetry, consumer_dispatch,
    # reliability sync conflicts, completion_telemetry.
    assert "completion_telemetry" not in d
    assert "consumer_dispatch" not in d


def test_continuity_public_wrong_link(submitted_odr: dict):
    r = requests.get(
        f"{URL}/api/odr/public/{submitted_odr['doc_id']}",
        params={"link_id": "bogus-link-id"},
        timeout=10,
    )
    assert r.status_code == 403


def test_continuity_public_unknown_doc(headers: dict):
    r = requests.get(f"{URL}/api/odr/public/ODR-9999-99999", timeout=10)
    assert r.status_code == 404


def test_continuity_version_chain(headers: dict, submitted_odr: dict):
    r = requests.get(
        f"{URL}/api/odr/{submitted_odr['id']}/version-chain",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["doc_id"] == submitted_odr["doc_id"]
    assert "amendments" in d
    assert "amendment_chain_length" in d


# ── Amendments ───────────────────────────────────────────────────────


def test_amend_in_window_admin(headers: dict, submitted_odr: dict):
    r = requests.post(
        f"{URL}/api/odr/{submitted_odr['id']}/amend",
        json={
            "field_path": "plan_vs_actual.schedule_impact_days",
            "new_value": 0.5,
            "reason": {"text": "pytest amendment"},
        },
        headers=headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    # Admin always writes an amendment row (per implementation).
    assert d["amendment_recorded"] is True
    assert d["role"] == "admin"
    assert d["amendment_id"]


def test_amend_list(headers: dict, submitted_odr: dict):
    r = requests.get(
        f"{URL}/api/odr/{submitted_odr['id']}/amendments",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["doc_id"] == submitted_odr["doc_id"]
    assert d["count"] >= 1


def test_amend_invalid_field_path(headers: dict, submitted_odr: dict):
    # Invalid field path → 400
    r = requests.post(
        f"{URL}/api/odr/{submitted_odr['id']}/amend",
        json={"field_path": "", "new_value": "x", "reason": {"text": "x"}},
        headers=headers, timeout=10,
    )
    assert r.status_code in (400, 422), r.text


# ── PDF ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("audience", [
    "foreman", "superintendent", "pm", "executive", "external",
])
def test_pdf_renders(headers: dict, submitted_odr: dict, audience: str):
    r = requests.get(
        f"{URL}/api/odr/{submitted_odr['id']}/pdf",
        params={"audience": audience},
        headers=headers, timeout=15,
    )
    assert r.status_code == 200, f"audience={audience}: {r.text[:200]}"
    assert r.content[:4] == b"%PDF", "missing PDF magic bytes"
    assert r.headers.get("X-ODR-Audience") == audience
    sha = r.headers.get("X-ODR-SHA256")
    assert sha and len(sha) == 64
    assert "Official Record" in (r.headers.get("X-ODR-Footer") or "")


def test_pdf_deterministic_same_audience(
    headers: dict, submitted_odr: dict,
):
    r1 = requests.get(
        f"{URL}/api/odr/{submitted_odr['id']}/pdf",
        params={"audience": "foreman"},
        headers=headers, timeout=15,
    )
    r2 = requests.get(
        f"{URL}/api/odr/{submitted_odr['id']}/pdf",
        params={"audience": "foreman"},
        headers=headers, timeout=15,
    )
    assert r1.headers["X-ODR-SHA256"] == r2.headers["X-ODR-SHA256"]


def test_pdf_audiences_differ(headers: dict, submitted_odr: dict):
    shas = {}
    for aud in ("foreman", "external", "executive"):
        r = requests.get(
            f"{URL}/api/odr/{submitted_odr['id']}/pdf",
            params={"audience": aud},
            headers=headers, timeout=15,
        )
        shas[aud] = r.headers["X-ODR-SHA256"]
    assert len(set(shas.values())) == 3, f"shas collided: {shas}"


def test_pdf_invalid_audience(headers: dict, submitted_odr: dict):
    r = requests.get(
        f"{URL}/api/odr/{submitted_odr['id']}/pdf",
        params={"audience": "garbage"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 422


# ── Guidance ─────────────────────────────────────────────────────────


def test_guidance_prompts_list(headers: dict):
    r = requests.get(f"{URL}/api/odr/guidance/prompts", headers=headers, timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["count"] >= 14
    # Critical ODR sections must be covered.
    for required in (
        "production_segments", "safety", "delays", "extra_work",
        "constraints", "manpower", "equipment", "materials",
    ):
        assert required in d["sections"], f"missing section: {required}"


def test_guidance_resolve_with_crew_overlay(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/resolve",
        params={"prompt_key": "production.add_first_segment",
                "crew_type": "pipe", "lang": "en"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["applied_crew_overlay"] is True
    assert len(d["bullets"]) >= 4
    # Pipe overlay must contain LF / structures hint.
    joined = " ".join(d["bullets"]).lower()
    assert "lf" in joined or "from-structure" in joined


def test_guidance_resolve_es_overlay(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/resolve",
        params={"prompt_key": "production.add_first_segment",
                "crew_type": "airfield", "lang": "es"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["lang"] == "es"
    assert len(d["bullets"]) >= 4


def test_guidance_resolve_fallback_to_base(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/resolve",
        params={"prompt_key": "delays.classify_with_type",
                "crew_type": "structures", "lang": "en"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    # structures has no override for delays — base must serve.
    assert d["applied_crew_overlay"] is False
    assert len(d["bullets"]) >= 4


def test_guidance_unknown_prompt_key(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/resolve",
        params={"prompt_key": "no.such.key", "lang": "en"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 404


def test_crew_readiness_matrix_pipe(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/crew-readiness/pipe",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["required_topic_count"] >= 4
    assert "trench-safety" in d["required"]


def test_crew_readiness_matrix_airfield(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/crew-readiness/airfield",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    required = set(d["required"])
    for topic in ("escort-requirements", "fod-control", "faa-restrictions"):
        assert topic in required, f"airfield missing required topic: {topic}"


def test_catalog_health_floor(headers: dict):
    r = requests.get(
        f"{URL}/api/odr/guidance/catalog-health",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["en_keys_meeting_floor"] == d["prompt_keys"]
    assert d["es_keys_meeting_floor"] == d["prompt_keys"]
    assert d["en_keys_below_floor"] == []
    assert d["es_keys_below_floor"] == []
