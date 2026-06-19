"""TRACK 15.41 · Generate BEFORE+AFTER PDFs for the Top 6 operational
PDFs and dump their extracted text for field-by-field comparison.

Usage:
    cd /app/backend && python3 scripts/track_15_41_pdf_baseline.py <phase>

  <phase> = 'before' | 'after'

Writes:
    /tmp/track_15_41/{phase}/safety_meeting.pdf
    /tmp/track_15_41/{phase}/safety_meeting.txt
    ... (one .pdf + .txt per PDF type)

Then the diff script `track_15_41_pdf_compare.py` ensures every line of
text from the BEFORE file appears in the AFTER file (superset rule).
"""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from pymongo import MongoClient
from pdfminer.high_level import extract_text

OUT_BASE = Path("/tmp/track_15_41")


def _db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def _dump(name: str, pdf_bytes: bytes, phase: str):
    d = OUT_BASE / phase
    d.mkdir(parents=True, exist_ok=True)
    pdf_path = d / f"{name}.pdf"
    txt_path = d / f"{name}.txt"
    pdf_path.write_bytes(pdf_bytes)
    text = extract_text(str(pdf_path)) or ""
    txt_path.write_text(text)
    print(f"  {name:30s}  bytes={len(pdf_bytes):>7d}  textlen={len(text):>6d}")


def _synthesize_return(issuance):
    """Build a synthetic return record from an issuance so we can certify
    render_return_pdf even when preview has no actual returns."""
    items = issuance.get("items") or []
    return {
        "id": "RTN-SYNTH-15_41",
        "doc_id": "RTN-SYNTH-15_41",
        "return_number": "RTN-15.41-CERT",
        "issuance_id": issuance.get("id"),
        "returned_by_name": "Track 15.41 Cert Returner",
        "returned_by_employee_id": "TRK-15-41",
        "returned_at": "2026-06-19T13:00:00Z",
        "supervisor_name": "Track 15.41 Cert Supervisor",
        "supervisor_signature": "",
        "employee_signature": "",
        "notes": "Cert-synth return notes — must survive the foundation refactor.",
        "items": [
            {
                "asset_id": (it.get("asset_id") or "—"),
                "description": it.get("description") or "",
                "quantity_returned": it.get("quantity") or 0,
                "condition": "returned-ok",
                "condition_note": "",
            }
            for it in items
        ],
        "project_name": issuance.get("project_name"),
        "project_number": issuance.get("project_number"),
    }


def main(phase: str):
    db = _db()

    # 1. Safety Meeting (pdf_render.render_record_pdf 'meeting')
    rec = db.meetings.find_one({"id": "00fd0791-7366-426b-b4fd-00c6208c7c05"}) or db.meetings.find_one()
    if rec:
        from pdf_render import render_record_pdf
        _dump("safety_meeting", render_record_pdf("meeting", rec), phase)

    # 2. Daily Report
    rec = db.daily_reports.find_one({"id": "4cab04c6-a17d-47d6-a02c-2942538cfcd5"}) or db.daily_reports.find_one()
    if rec:
        from pdf_render import render_record_pdf
        _dump("daily_report", render_record_pdf("daily-report", rec), phase)

    # 3. JHA (renders via pdf_render with 'jha' kind)
    rec = db.jhas.find_one()
    if rec:
        from pdf_render import render_record_pdf
        _dump("jha", render_record_pdf("jha", rec), phase)

    # 4. Equipment Issuance
    issuance = db.safety_equipment_issuances.find_one({"id": "54e109fe-14d4-42a7-bb49-16ce4e8877a4"}) or db.safety_equipment_issuances.find_one()
    if issuance:
        from routes.safety_forms import render_issuance_pdf
        _dump("equipment_issuance", render_issuance_pdf(issuance), phase)

        # 5. Equipment Return (synthetic when no real returns exist)
        from routes.safety_forms import render_return_pdf
        ret = _synthesize_return(issuance)
        _dump("equipment_return", render_return_pdf(issuance, ret), phase)

    # 6. Training Acknowledgement
    tr = db.safety_equipment_trainings.find_one({"id": "603a1d13-0acb-4668-a83a-a7743982f92a"}) or db.safety_equipment_trainings.find_one()
    if tr:
        from routes.safety_forms import render_training_pdf
        _dump("training_acknowledgement", render_training_pdf(tr), phase)


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "before"
    assert phase in ("before", "after")
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    print(f"=== Track 15.41 baseline · phase={phase} ===")
    main(phase)
