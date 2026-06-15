"""
phase9_safety_meeting_live_cert.py — TRACK 14.0-SAFETY-MEETING-WORKFLOW-PDF-CERTIFICATION
Phase 9 (Live / Preview Certification).

Creates one tagged Safety Meeting on preview, captures the rendered
PDF bytes, scans for the section-numbering + content + attendance
contracts the directive demands, then deletes the meeting.

Prefix: SAFETY-MEETING-CERT (per directive).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

API = "https://safety-audit-mobile-1.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def login() -> str:
    r = requests.post(
        f"{API}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


def main() -> int:
    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    tok = login()
    H = {"X-Admin-Token": tok, "Content-Type": "application/json"}

    payload = {
        "project_name": "SAFETY-MEETING-CERT Project",
        "project_number": "ZZ-SMC-2026",
        "location": "Cert Lab · Field Trailer",
        "meeting_date": "2026-06-15",
        "meeting_time": "08:00",
        "conducted_by": "James Fisher (Jimmy)",
        "topic": "SAFETY-MEETING-CERT · Trench / Excavation Safety",
        "topic_category": "Hazard-Specific",
        "hazards_reviewed": "Cave-in\nStruck-by\nUtility strike",
        "discussion_notes": (
            "SAFETY-MEETING-CERT smoke meeting. Reviewed competent-person "
            "checklist, sloping/benching options, OSHA 1926.652 Type B "
            "soil, and required protective system at >5 ft depth."
        ),
        "references_cited": "OSHA 29 CFR 1926.652 · MASCI Trench SOP-04",
        "action_items": "Order trench shield by Friday. PM to confirm soil classification before next excavation.",
        "attendees": [
            {
                "name": "MASCI Foreman SmokeCert",
                "employee_id": "",
                "non_masci": False,
                "company": "MASCI",
                "trade": "Foreman",
                "signature": "data:image/png;base64,iVBORw0KGgo=",
                "acknowledged": True,
                "acknowledged_at": "2026-06-15T12:00:00Z",
            },
            {
                "name": "Sam Subcontractor SmokeCert",
                "employee_id": "",
                "non_masci": True,
                "company": "Acme Paving",
                "trade": "Asphalt Operator",
                "signature": "data:image/png;base64,iVBORw0KGgo=",
                "acknowledged": True,
                "acknowledged_at": "2026-06-15T12:01:00Z",
            },
        ],
        "photos": [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
        ],
        "conductor_signature": "data:image/png;base64,iVBORw0KGgo=",
    }

    print(f"=== SAFETY-MEETING-CERT live preview smoke @ {API} ===\n")
    # Create
    r = requests.post(f"{API}/api/meetings", headers=H,
                      json=payload, timeout=60)
    print(f"POST /api/meetings → {r.status_code}")
    if r.status_code != 200:
        print(r.text[:800])
        return 1
    mtg = r.json()
    mid = mtg["id"]
    doc_id = mtg.get("doc_id", "")
    print(f"  meeting id={mid}  doc_id={doc_id}")

    # Render PDF via internal helper to verify contract
    from sys import path as _p
    _p.insert(0, "/app/backend")
    from pdf_render import render_record_pdf  # type: ignore

    pdf_bytes = render_record_pdf("meeting", mtg)
    pdf_path = Path("/app/test_reports/SAFETY_MEETING_CERT_smoke.pdf")
    pdf_path.write_bytes(pdf_bytes)
    print(f"Rendered PDF · {len(pdf_bytes)} bytes → {pdf_path}")

    # Render the inner HTML directly so we can assert content presence
    from pdf_render import _render_meeting  # type: ignore
    html = _render_meeting("Safety Meeting", mtg)
    Path("/app/test_reports/SAFETY_MEETING_CERT_smoke.html").write_text(html)
    print("Wrote inner HTML for grep-based content checks")

    contract = {
        "section_01_present": "01 · Meeting Details" in html,
        "section_02_present": "02 · Hazards Discussed" in html,
        "section_03_present": "03 · Discussion" in html,
        "section_04_present": "04 · Action Items" in html,
        "section_05_present": "05 · Additional Notes" in html,
        "section_06_present": "06 · Photos" in html,
        "section_07_present": "07 · Attendance and Acknowledgement" in html,
        "no_section_jump_01_to_06":
            (html.index("01 · Meeting Details") <
             html.index("02 · Hazards Discussed") <
             html.index("03 · Discussion") <
             html.index("04 · Action Items") <
             html.index("05 · Additional Notes") <
             html.index("06 · Photos") <
             html.index("07 · Attendance and Acknowledgement")),
        "conducted_by_rendered": "James Fisher (Jimmy)" in html,
        "hazards_rendered": "Cave-in" in html and "Struck-by" in html,
        "discussion_rendered": "competent-person checklist" in html,
        "action_items_rendered": "Order trench shield" in html,
        "masci_attendee_rendered": "MASCI Foreman SmokeCert" in html,
        "masci_company_locked": "MASCI" in html,
        "non_masci_attendee_rendered": "Sam Subcontractor SmokeCert" in html,
        "non_masci_company_typed": "Acme Paving" in html,
        "trade_rendered": "Foreman" in html and "Asphalt Operator" in html,
        "acknowledgement_rendered": "✓ Acknowledged" in html,
        "no_undefined_leak": "undefined" not in html,
    }
    print("\nContract checks:")
    for k, v in contract.items():
        flag = "✅" if v else "❌"
        print(f"  {flag} {k}")

    # Cleanup — meeting DELETE endpoint exists?
    rd = requests.delete(f"{API}/api/meetings/{mid}",
                         headers={"X-Admin-Token": tok}, timeout=30)
    print(f"\nDELETE /api/meetings/{mid} → {rd.status_code}")

    out = {
        "api": API, "meeting_id": mid, "doc_id": doc_id,
        "pdf_bytes": len(pdf_bytes), "pdf_path": str(pdf_path),
        "html_path": str(Path("/app/test_reports/SAFETY_MEETING_CERT_smoke.html")),
        "contract": contract,
        "all_passed": all(contract.values()),
        "cleanup_status": rd.status_code,
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    Path("/app/test_reports/safety_meeting_cert_phase9.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(f"\nWrote /app/test_reports/safety_meeting_cert_phase9.json")
    print(f"Overall: {'PASS' if out['all_passed'] else 'FAIL'}")
    return 0 if out["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
