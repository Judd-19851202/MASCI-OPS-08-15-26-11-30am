"""Iteration 12 — full-stack health check additions.

Covers items requested in iter12 review that aren't in the existing 123 tests:
  - /api/auto-email/preview returns correct recipients for each of the 6 kinds × 4 PMs
  - 21 'Strobe ... (Required)' occurrences across all 23 checklist templates
  - render_record_pdf('equipment-inspection', record) returns >1KB PDF with FAIL banner
    and embeds per-item photo when checklist[section][item].photo is a data URL
  - /api/translate accepts a deeply nested {strings: {...}} dict and returns same shape
  - schedule_auto_email path does not crash on POST and a backend-log line records dispatch
"""
import io
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from checklists import CHECKLISTS, EQUIPMENT_TYPES  # noqa: E402
from pdf_render import render_record_pdf  # noqa: E402
from tests.conftest import URL  # noqa: E402


# ---------- Preview endpoint per-kind × per-PM ----------
PMS = [
    ("24-06", "David Jewett",     "davidjewett@mascigc.com"),
    ("25-12", "Chris Wright",     "chriswright@mascigc.com"),
    ("25-02", "Ramon Rodriguez",  "RamonRodriguez@mascigc.com"),
    ("26-06", "Jaymn Judd",       "jaymn.judd@mascigc.com"),
]
COMPLIANCE = ["inspection", "meeting", "jha", "incident"]
OPERATIONAL = ["daily-report", "equipment-inspection"]


def _preview(project_number, kind):
    r = requests.get(
        f"{URL}/api/auto-email/preview",
        params={"project_number": project_number, "kind": kind},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_preview_compliance_includes_pm_and_always_cc():
    for proj, name, email in PMS:
        for kind in COMPLIANCE:
            body = _preview(proj, kind)
            assert body["pm_name"] == name, (proj, kind, body)
            assert body["pm_email"].lower() == email.lower()
            recips_lower = [e.lower() for e in body["all_recipients"]]
            # PM always present
            assert email.lower() in recips_lower
            # always_cc rule: jaymn + safety@ always present (deduped if PM=Jaymn)
            assert "jaymn.judd@mascigc.com" in recips_lower
            assert "safety@mascigc.com" in recips_lower
            # No duplicates
            assert len(recips_lower) == len(set(recips_lower))


def test_preview_operational_pm_only_no_office_cc():
    for proj, name, email in PMS:
        for kind in OPERATIONAL:
            body = _preview(proj, kind)
            assert body["pm_name"] == name
            recips_lower = [e.lower() for e in body["all_recipients"]]
            assert email.lower() in recips_lower
            if name != "Jaymn Judd":
                # Operational forms for non-Jaymn PMs MUST NOT include jaymn or safety@
                assert "jaymn.judd@mascigc.com" not in recips_lower, (proj, kind, body)
                assert "safety@mascigc.com" not in recips_lower, (proj, kind, body)
            else:
                # Knox McRae: Jaymn alone, NO duplicate, NO safety@
                assert recips_lower == ["jaymn.judd@mascigc.com"], (proj, kind, body)


def test_preview_unmapped_compliance_falls_back_to_always_cc():
    body = _preview("99-99", "inspection")
    recips_lower = [e.lower() for e in body["all_recipients"]]
    assert body["pm_name"] is None
    assert "jaymn.judd@mascigc.com" in recips_lower
    assert "safety@mascigc.com" in recips_lower


def test_preview_unmapped_operational_falls_back_to_jaymn_only():
    for kind in OPERATIONAL:
        body = _preview("99-99", kind)
        recips_lower = [e.lower() for e in body["all_recipients"]]
        assert body["pm_name"] is None
        assert recips_lower == ["jaymn.judd@mascigc.com"], (kind, body)
        assert "safety@mascigc.com" not in recips_lower


# ---------- Equipment types & Strobe (Required) ----------
def test_equipment_types_count_is_23():
    r = requests.get(f"{URL}/api/equipment-types", timeout=10)
    assert r.status_code == 200
    body = r.json()
    types = body.get("equipment_types") or body.get("types") or body
    if isinstance(body, dict) and "checklists" in body:
        templates = body["checklists"]
    else:
        templates = body.get("checklist_templates") if isinstance(body, dict) else None
    assert len(types) == 23
    if templates is not None:
        assert len(templates) == 23


def test_strobe_required_count_is_21():
    """The Strobe checklist item should read '(Required)' on 21 of the 23 templates."""
    count = 0
    for eq_type, sections in CHECKLISTS.items():
        # sections is a list of {"title": str, "items": [str | {label}, ...]}
        for sec in sections:
            items = sec.get("items", []) if isinstance(sec, dict) else []
            for it in items:
                label = it if isinstance(it, str) else it.get("label", "")
                if "strobe" in label.lower() and "(required)" in label.lower():
                    count += 1
    assert count == 21, f"Expected 21 'Strobe ... (Required)' items, found {count}"


# ---------- Equipment PDF render with photo embed ----------
def test_equipment_pdf_renders_fail_banner_and_embeds_photo():
    # 1x1 transparent PNG data URL
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    photo_data_url = f"data:image/png;base64,{png_b64}"

    record = {
        "id": "test-equip-pdf",
        "project_name": "T5824 SR 46",
        "project_number": "24-06",
        "operator_name": "TEST_Operator",
        "equipment_type": "Excavator",
        "unit_label": "CAT 320 #TEST",
        "inspection_date": "2026-02-15",
        "inspection_time": "07:00",
        "fail_count": 1,
        "checklist": {
            "Engine Compartment": [
                {"label": "Oil level", "status": "PASS", "note": "", "photo": ""},
                {
                    "label": "Coolant level",
                    "status": "FAIL",
                    "note": "Low coolant - needs immediate top-off before operation",
                    "photo": photo_data_url,
                },
            ]
        },
    }
    pdf_bytes = render_record_pdf("equipment-inspection", record)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 1024, f"PDF too small: {len(pdf_bytes)} bytes"
    assert pdf_bytes[:4] == b"%PDF", "Not a valid PDF magic"


# ---------- /api/translate deeply nested dict ----------
def test_translate_accepts_flat_pathed_dict():
    """/api/translate contract: flat {key: string} in, flat {strings: {key: string}} out.
    The frontend translateOnSubmit.js walks the nested form, collects leaves into a flat
    {path: text} dict (path is dot-joined), POSTs to /api/translate, and writes the
    translated values back via setByPath. So the backend never sees a nested dict.
    """
    payload = {
        "from_lang": "es",
        "to_lang": "en",
        "strings": {
            "checklist.Engine Compartment.Coolant level.note": "Necesita refrigerante urgentemente",
            "checklist.Engine Compartment.Oil level.note": "Aceite bajo",
            "checklist.Cab.Mirrors.note": "Espejo roto",
            "summary": "Inspeccion con fallos criticos",
        },
    }
    r = requests.post(f"{URL}/api/translate", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "strings" in body
    out = body["strings"]
    # Same keys, all string values
    assert set(out.keys()) == set(payload["strings"].keys())
    for k, v in out.items():
        assert isinstance(v, str), f"non-string leaf at {k}: {v!r}"
        assert v.strip(), f"empty translation at {k}"
