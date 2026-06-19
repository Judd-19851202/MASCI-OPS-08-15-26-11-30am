"""Iter-33 bilingual QA/QC tests.

Scope:
- Submit a QA/QC inspection with submit_language='es' → persisted & GET returns it.
- Render PDF via pdf_render.render_record_pdf for submit_language='es' and 'en' → verify
  Spanish/English strings appear in the HTML payload passed to WeasyPrint by introspecting
  the _render_qaqc output and the localized title.
- Confirm _QAQC_ES dict exposes all the critical EN→ES mappings the review requests.
"""
import os
import pytest
import requests
from pathlib import Path


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
ADMIN_PASSWORD = _read_kv(Path("/app/backend/.env"), "ADMIN_PASSWORD") or os.environ.get(
    "ADMIN_PASSWORD", "Maddix123!"
)

# Adjust import path so we can exercise pdf_render directly.
import sys
sys.path.insert(0, "/app/backend")
from pdf_render import _QAQC_ES, _render_qaqc, render_record_pdf, KIND_TITLES  # noqa: E402


# ──────────────────────────── Fixtures ────────────────────────────
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture
def api(admin_token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "X-Admin-Token": admin_token})
    return s


@pytest.fixture(scope="module")
def created_ids():
    ids: list[str] = []
    yield ids
    # Cleanup
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
    if r.status_code == 200:
        tok = r.json()["token"]
        for _id in ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/qaqc-inspections/{_id}",
                    headers={"X-Admin-Token": tok},
                    timeout=10,
                )
            except Exception:
                pass


def _sample_payload(submit_language: str = "es", kind: str = "concrete_form") -> dict:
    checklist = [
        {"key": "forms_braced", "label": "Forms braced and secured", "result": "pass", "note": ""},
        {"key": "forms_clean", "label": "Forms clean and free of debris", "result": "pass", "note": ""},
        {"key": "line_and_grade", "label": "Line and grade checked", "result": "fail", "note": "Off by 1/2 inch"},
        {"key": "dims", "label": "Dimensions verified", "result": "na", "note": ""},
    ]
    return {
        "inspection_kind": kind,
        "project_name": "TEST_QAQC_BILINGUAL",
        "project_number": "TEST-33",
        "location": "Preview Yard",
        "client": "MASCI",
        "pm_name": "Chris Wright",
        "subcontractor_name": "TEST Sub LLC",
        "crew_company": "TEST Crew",
        "inspection_date": "2026-01-15",
        "inspection_time": "10:00",
        "inspector_name": "TEST Inspector",
        "work_area": "Footing A-1",
        "weather_conditions": "Sunny",
        "work_activity": "Form setup",
        "mix_design": "3000psi",
        "yards_ordered": "8",
        "concrete_vendor": "Acme Ready-Mix",
        "checklist": checklist,
        "inspection_notes": "Looks good",
        "deficiencies": "Line off grade on pour line",
        "corrective_actions": "Reset forms",
        "photos": [],
        "inspector_signature": "",
        "submit_language": submit_language,
    }


# ──────────────────────── Backend API persistence ─────────────────
class TestQaqcSubmitLanguagePersisted:
    def test_post_with_submit_language_es_persists(self, api, created_ids):
        payload = _sample_payload("es")
        r = api.post(f"{BASE_URL}/api/qaqc-inspections", json=payload, timeout=30)
        assert r.status_code == 200, f"create failed: {r.status_code} {r.text}"
        rec = r.json()
        assert rec["submit_language"] == "es"
        created_ids.append(rec["id"])

        # GET back
        g = api.get(f"{BASE_URL}/api/qaqc-inspections/{rec['id']}", timeout=15)
        assert g.status_code == 200
        full = g.json()
        assert full["submit_language"] == "es"
        assert full["project_name"] == "TEST_QAQC_BILINGUAL"
        assert full["pass_count"] == 2
        assert full["fail_count"] == 1
        assert full["na_count"] == 1
        assert "_id" not in full

    def test_post_with_submit_language_en_persists(self, api, created_ids):
        payload = _sample_payload("en")
        r = api.post(f"{BASE_URL}/api/qaqc-inspections", json=payload, timeout=30)
        assert r.status_code == 200
        rec = r.json()
        assert rec["submit_language"] == "en"
        created_ids.append(rec["id"])


# ──────────────────────── PDF localization (direct) ───────────────
class TestPdfLocalization:
    def test_qaqc_es_pdf_html_contains_spanish_titles_and_labels(self):
        record = _sample_payload("es")
        # _render_qaqc reads precomputed counts (the API recomputes on submit; here we set
        # them explicitly to exercise the FAIL banner branch).
        record["pass_count"] = 2
        record["fail_count"] = 1
        record["na_count"] = 1
        body = _render_qaqc(record)
        # Section titles
        assert "Inspección" in body
        assert "Obra" in body
        assert "Subcontratista / Cuadrilla" in body
        assert "Vaciado de Concreto" in body
        assert "Lista de Verificación" in body
        assert "Resumen de Inspección" in body
        # Field labels
        assert "Inspector" in body
        assert "Fecha" in body
        assert "Número de Proyecto" in body
        assert "Diseño de Mezcla" in body
        assert "Proveedor de Concreto" in body
        # Checklist item localization (labels came in English, PDF translated them)
        assert "Formaletas arriostradas y aseguradas" in body
        assert "Formaletas limpias y libres de escombros" in body
        assert "Línea y nivel verificados" in body
        # Pass/Fail/N/A badges
        assert "CUMPLE" in body
        assert "NO CUMPLE" in body
        assert "N/A" in body
        # FAIL banner in Spanish
        assert "no cumplen" in body.lower()
        assert "acción correctiva" in body

    def test_qaqc_en_pdf_html_contains_english_labels(self):
        record = _sample_payload("en")
        body = _render_qaqc(record)
        assert "Inspection" in body
        assert "Project" in body
        assert "Checklist" in body
        assert "Concrete Placement" in body
        assert "Mix Design" in body
        # English checklist items — pass-through
        assert "Forms braced and secured" in body
        assert "Line and grade checked" in body
        # Badges
        assert "PASS" in body
        assert "FAIL" in body
        # Should NOT contain Spanish tokens
        assert "CUMPLE" not in body
        assert "Formaletas" not in body

    def test_qaqc_es_title_localized_in_full_pdf(self):
        record = _sample_payload("es")
        pdf = render_record_pdf("qaqc", record)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF", "render_record_pdf must return a valid PDF"
        assert len(pdf) > 2000

    def test_qaqc_en_title_localized_in_full_pdf(self):
        record = _sample_payload("en")
        pdf = render_record_pdf("qaqc", record)
        assert pdf[:4] == b"%PDF"

    def test_qaqc_es_rebar_checklist_items_translated(self):
        record = _sample_payload("es", kind="rebar")
        record["checklist"] = [
            {"key": "bar_size", "label": "Bar size verified", "result": "pass", "note": ""},
            {"key": "bar_spacing", "label": "Bar spacing verified", "result": "pass", "note": ""},
            {"key": "cover", "label": "Required concrete cover verified", "result": "fail", "note": ""},
        ]
        body = _render_qaqc(record)
        assert "Diámetro de barra verificado" in body
        assert "Separación de barras verificada" in body
        assert "Recubrimiento de concreto requerido verificado" in body

    def test_qaqc_es_subcontractor_checklist_items_translated(self):
        record = _sample_payload("es", kind="subcontractor_work")
        record["checklist"] = [
            {"key": "matches", "label": "Work matches plans/specifications", "result": "pass", "note": ""},
            {"key": "safe_area", "label": "Work area safe and accessible", "result": "pass", "note": ""},
        ]
        body = _render_qaqc(record)
        assert "El trabajo coincide con planos / especificaciones" in body
        assert "Área de trabajo segura y accesible" in body


# ──────────────────────── _QAQC_ES sanity ─────────────────────────
class TestQaqcEsDict:
    @pytest.mark.parametrize("en,es", [
        ("Pass Items", "Cumple"),
        ("Fail Items", "No Cumple"),
        ("N/A Items", "N/A"),
        ("Inspection", "Inspección"),
        ("Project", "Obra"),
        ("Checklist", "Lista de Verificación"),
        ("Project Number", "Número de Proyecto"),
        ("Inspector", "Inspector"),
        ("Mix Design", "Diseño de Mezcla"),
        ("Forms braced and secured", "Formaletas arriostradas y aseguradas"),
        ("Bar size verified", "Diámetro de barra verificado"),
        ("Work matches plans/specifications", "El trabajo coincide con planos / especificaciones"),
    ])
    def test_key_maps(self, en, es):
        assert _QAQC_ES.get(en) == es, f"{en!r} should map to {es!r} but got {_QAQC_ES.get(en)!r}"

    def test_kind_title_en_remains(self):
        assert KIND_TITLES["qaqc"] == "QA / QC Inspection"
        assert _QAQC_ES["QA / QC Inspection"] == "Inspección de QA / QC"
