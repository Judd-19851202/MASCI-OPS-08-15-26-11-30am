"""
TRACK 14.0-S1-B1 THROUGH B10 · Amendment B Operational Certification.

This is the canonical regression suite that proves the platform is
BILINGUAL OPERATIONAL — not merely "translated".

Success criteria (per Amendment B):

  A Spanish-speaking foreman can submit a record in Spanish; the
  canonical operational record stored on the server is in English (so
  PDFs / notifications / search / exports all read clean English); and
  the original Spanish is preserved in the bilingual sidecar for audit.

What this suite proves end-to-end:

  1. POST /api/translate produces English using MASCI Heavy Civil
     glossary terms (not generic dictionary equivalents) — Amendment D.
  2. The bilingual sidecar round-trips Spanish character-for-character
     for the ten critical workflow form_types.
  3. The /api/translate endpoint preserves numbers, abbreviations, and
     proper nouns exactly.

These tests run against the live preview backend.
"""
from __future__ import annotations

import os
import uuid

import pytest


# Heavy Civil / MASCI glossary anchors — these are the EXACT English terms
# the platform must produce when given the Spanish on the left. If any of
# these regress to generic Google-style translations, the suite fails and
# the operational PDF / notification / search outputs cannot be trusted.
GLOSSARY_ANCHORS = [
    # (spanish_input, english_anchor_substring)
    ("cuasi accidente", "near miss"),
    ("caja de zanja", "trench box"),
    ("escudo de zanja", "trench shield"),
    ("placa vial", "road plate"),
    ("riego de liga", "tack coat"),
    ("estación elevadora", "lift station"),
    ("acción correctiva", "corrective action"),
    ("causa raíz", "root cause"),
    ("capataz", "foreman"),
    ("EPP", "PPE"),
    ("rellenado", "backfill"),
    ("compactación", "compaction"),
    ("subrasante", "subgrade"),
    ("espacio confinado", "confined space"),
    ("línea de fuerza", "force main"),
    ("alcantarillado por gravedad", "gravity sewer"),
    ("drenaje pluvial", "storm drain"),
    ("hidrante", "hydrant"),
    ("válvula", "valve"),
    ("cruce de servicios públicos", "utility crossing"),
    ("benchmark", "benchmark"),
    ("permiso de trabajo", "work permit"),
    ("bloqueo y etiquetado", "lock-out"),
    ("solicitud de tiempo libre", "time-off request"),
    ("operador", "operator"),
]


# The ten critical workflows certified by Amendment B execution order.
CRITICAL_FORM_TYPES = [
    "daily_report",
    "meeting",
    "incident",
    "corrective_action",
    "trench_excavation",
    "equipment_inspection",
    "employee_request",
    "time_off",
    "qaqc",
    "field_leadership",  # JHP / JHA / field-leadership workflow
]


@pytest.fixture(scope="module")
def api_url() -> str:
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


# ── AMENDMENT D · Glossary Certification ──────────────────────────────


def test_translate_endpoint_uses_masci_heavy_civil_glossary(api_url):
    """All MASCI Heavy Civil anchors round-trip to operational English.

    This proves the system prompt baked into /api/translate produces the
    EXACT English terminology the office expects to read in PDFs and
    notifications. A failure here means downstream operational output
    is contaminated with literal / Google-style translations.
    """
    requests = pytest.importorskip("requests")
    # Build one batched request per anchor — the LLM call is paid by
    # token count, so batching keeps the suite cheap and fast.
    strings = {
        f"k{i}": f"En el sitio: {es}. Necesita atención."
        for i, (es, _) in enumerate(GLOSSARY_ANCHORS)
    }
    r = requests.post(
        f"{api_url}/api/translate",
        json={"from_lang": "es", "to_lang": "en", "strings": strings},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    out = r.json()["strings"]
    misses = []
    for i, (es, en_anchor) in enumerate(GLOSSARY_ANCHORS):
        english = (out.get(f"k{i}") or "").lower()
        if en_anchor.lower() not in english:
            misses.append(f"  · {es!r} → {english!r} (expected {en_anchor!r})")
    assert not misses, (
        "MASCI Heavy Civil glossary anchors missing from translated "
        "output. The LLM is producing generic translations that will "
        "confuse the English-speaking office. Failures:\n"
        + "\n".join(misses)
    )


def test_translate_preserves_numbers_dates_and_proper_nouns(api_url):
    requests = pytest.importorskip("requests")
    cases = {
        "n1": "Excavamos 120 pies lineales el 03/14/2026.",
        "n2": "Proyecto MASCI-2024-118 con FDOT inspector José Hernández.",
        "n3": "Cumple ASTM D6938; densidad 95.2%.",
    }
    r = requests.post(
        f"{api_url}/api/translate",
        json={"from_lang": "es", "to_lang": "en", "strings": cases},
        timeout=45,
    )
    assert r.status_code == 200
    out = r.json()["strings"]
    assert "120" in out["n1"]
    assert "03/14/2026" in out["n1"] or "2026-03-14" in out["n1"] or "March 14, 2026" in out["n1"]
    assert "MASCI-2024-118" in out["n2"]
    assert "FDOT" in out["n2"]
    assert "José Hernández" in out["n2"] or "Jose Hernandez" in out["n2"]
    assert "ASTM D6938" in out["n3"]
    assert "95.2" in out["n3"]


# ── AMENDMENT B · End-to-end pipeline simulation ──────────────────────


def _write_sidecar(requests, api_url, admin_token, form_type, form_id, originals):
    return requests.post(
        f"{api_url}/api/bilingual-records",
        headers={"X-Admin-Token": admin_token},
        json={
            "form_type": form_type,
            "form_id": form_id,
            "original_language": "es",
            "originals": originals,
            "translation_source": "llm",
        },
        timeout=15,
    )


@pytest.mark.parametrize("form_type", CRITICAL_FORM_TYPES)
def test_critical_workflow_sidecar_roundtrip(api_url, admin_token, form_type):
    """For each of the ten critical workflows, prove that:

    1. The Spanish originals can be persisted in the sidecar.
    2. They round-trip character-for-character.
    3. The bilingual record indexes against the canonical form_id so
       a PM viewing the English record can fetch the original Spanish
       without scanning the whole collection.
    """
    requests = pytest.importorskip("requests")
    form_id = f"CERT-S1-B-{form_type}-{uuid.uuid4().hex[:8]}"
    originals = {
        "/title": "Inspección crítica de zanja",
        "/notes": "Operador reportó cuasi accidente. Caja de zanja inspeccionada.",
        "/action": "Reunión de seguridad mañana. Capataz dirige.",
    }
    r = _write_sidecar(requests, api_url, admin_token, form_type, form_id, originals)
    assert r.status_code == 200, r.text
    assert r.json()["stored"] is True

    g = requests.get(
        f"{api_url}/api/bilingual-records/{form_type}/{form_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert g.status_code == 200
    rec = g.json()["record"]
    assert rec["form_type"] == form_type
    assert rec["form_id"] == form_id
    for k, v in originals.items():
        assert rec["originals"][k] == v


def test_end_to_end_translate_then_sidecar_pipeline(api_url, admin_token):
    """Simulates a Spanish-speaking foreman submitting a daily report:

      1. Frontend collects Spanish prose.
      2. translateUserInput → /api/translate returns clean MASCI English.
      3. Canonical record (would be) stored with English values.
      4. persistBilingualSidecar → /api/bilingual-records stores the
         original Spanish keyed by the canonical form_id.

    The test then verifies that the EN payload contains operational
    Heavy Civil English and that the sidecar has the original ES.
    """
    requests = pytest.importorskip("requests")
    es_payload = {
        "/discussion_notes": (
            "Hoy trabajamos en el alcantarillado por gravedad. El "
            "capataz pidió una acción correctiva por el cuasi accidente "
            "cerca de la caja de zanja."
        ),
        "/hazards_reviewed": (
            "Riesgo de derrumbe. Necesitamos placa vial sobre la zanja "
            "para el cruce de servicios públicos. Operador usa EPP."
        ),
        "/action_items": (
            "Reunión de seguridad mañana a las 7 AM. Revisar rellenado "
            "y compactación de la subrasante."
        ),
    }

    # Step 1 · Translate (proves the office reads English)
    t = requests.post(
        f"{api_url}/api/translate",
        json={"from_lang": "es", "to_lang": "en", "strings": es_payload},
        timeout=60,
    )
    assert t.status_code == 200, t.text
    en = t.json()["strings"]
    # The office MUST see Heavy Civil operational English.
    blob = " ".join(en.values()).lower()
    must_contain = [
        "gravity sewer", "foreman", "corrective action", "near miss",
        "trench box", "road plate", "utility crossing", "ppe",
        "safety meeting", "backfill", "compaction", "subgrade",
    ]
    missing = [w for w in must_contain if w not in blob]
    assert not missing, (
        f"Operational English missing required Heavy Civil terms: {missing}. "
        f"Got: {en!r}"
    )
    # And NO Spanish accent-bearing words should leak into the English.
    spanish_leakage = ["cuasi", "caja", "zanja", "rellenado", "compactación", "subrasante"]
    leaked = [w for w in spanish_leakage if w in blob]
    assert not leaked, f"Spanish leaked into English operational output: {leaked}"

    # Step 2 · Persist the original Spanish in the sidecar.
    form_id = f"E2E-DAILY-{uuid.uuid4().hex[:8]}"
    w = _write_sidecar(
        requests, api_url, admin_token, "daily_report", form_id, es_payload,
    )
    assert w.status_code == 200
    g = requests.get(
        f"{api_url}/api/bilingual-records/daily_report/{form_id}",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert g.status_code == 200
    stored = g.json()["record"]["originals"]
    # Accent + character preservation.
    for k, v in es_payload.items():
        assert stored[k] == v


def test_translate_short_circuits_when_from_eq_to(api_url):
    """en→en (or es→es) must short-circuit so we don't waste LLM tokens
    or risk drift on English-typed records."""
    requests = pytest.importorskip("requests")
    r = requests.post(
        f"{api_url}/api/translate",
        json={
            "from_lang": "en",
            "to_lang": "en",
            "strings": {"a": "Foreman reported a near miss at the trench box."},
        },
        timeout=15,
    )
    assert r.status_code == 200
    assert (
        r.json()["strings"]["a"]
        == "Foreman reported a near miss at the trench box."
    )
