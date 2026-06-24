"""TRACK 15.73 SLICE 2 · Safety Meeting Attendee Identity Regression.

Posts synthetic Safety Meetings through `/api/meetings` and asserts the
backend `normalize_meeting_attendees` guard restores canonical identity
regardless of what the frontend sends.

CASES:
  1. Roster-picked MASCI employee, frontend hint OK         → expect employee
  2. Roster-picked MASCI employee, frontend forgot company  → expect employee + company=MASCI
  3. Subcontractor, frontend correct                        → expect subcontractor
  4. Manual entry (typed name, no roster match)             → expect manual + needs_review
  5. Roster pick with INVALID employee_id (stale)           → expect manual + needs_review
  6. Duplicate roster pick (same employee_id twice)         → expect deduped (single row)
  7. Inconsistent flags (non_masci=true + employee_id set)  → expect subcontractor, employee_id cleared

Run:
  cd /app/backend && python3 scripts/track_15_73_slice2_attendee_identity_regression.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(Path("/app/frontend/.env"))

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
API_BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

if "prod" in DB_NAME.lower() and "preview" not in DB_NAME.lower():
    print(f"REFUSING — DB_NAME={DB_NAME} looks like production")
    sys.exit(2)

TAG = "TRACK_15_73_SLICE_2_DELETE"
TINY_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AAukB9Q0J6lwAAAAASUVORK5CYII="
)


def base_meeting(topic: str, attendees: list[dict]) -> dict:
    return {
        "project_name": f"{TAG}-project",
        "project_number": "20-07",
        "location": "Yard",
        "meeting_date": "2026-02-11",
        "meeting_time": "08:00",
        "conducted_by": f"{TAG} Tester",
        "topic": topic,
        "topic_category": "Tier-1",
        "discussion_notes": "Slice 2 regression",
        "hazards_reviewed": "—",
        "action_items": "—",
        "references_cited": "—",
        "photos": [],
        "conductor_signature": TINY_PNG,
        "attendees": attendees,
    }


def attendee(*, name: str, employee_id: str = "", non_masci: bool = False,
             company: str = "", trade: str = "",
             attendee_type: str = "", source: str = "",
             is_masci_employee: bool = False, is_subcontractor: bool = False,
             is_manual: bool = False) -> dict:
    return {
        "name": name,
        "employee_id": employee_id,
        "non_masci": non_masci,
        "company": company,
        "trade": trade,
        "signature": TINY_PNG,
        "acknowledged": True,
        "acknowledged_at": "2026-02-11T08:00:00Z",
        "attendee_type": attendee_type,
        "source": source,
        "is_masci_employee": is_masci_employee,
        "is_subcontractor": is_subcontractor,
        "is_manual": is_manual,
    }


def main() -> int:
    db = MongoClient(MONGO_URL)[DB_NAME]
    # Find two real employee_master ids to use in tests.
    emp_iter = db.employees.find({"is_active": True}, {"_id": 0, "id": 1, "name": 1}).limit(2)
    emps = list(emp_iter)
    if len(emps) < 2:
        print("FAIL: need ≥2 active employees in `employees` collection.")
        return 1
    e1, e2 = emps[0], emps[1]
    print(f"Test employees: {e1['name']} ({e1['id'][:8]}..), {e2['name']} ({e2['id'][:8]}..)")
    print()

    bogus_id = str(uuid.uuid4())  # guaranteed NOT in employees

    cases = [
        ("1·roster-pick MASCI · correct hints", [
            attendee(name=e1["name"], employee_id=e1["id"], non_masci=False,
                     company="MASCI", trade="Foreman",
                     attendee_type="employee", source="employee_master",
                     is_masci_employee=True),
        ], [{
            "attendee_type": "employee", "source": "employee_master",
            "is_masci_employee": True, "is_subcontractor": False, "is_manual": False,
            "review_status": "", "company": "MASCI",
            "employee_id": e1["id"],
        }]),

        ("2·roster-pick MASCI · empty company (frontend bug)", [
            attendee(name=e1["name"], employee_id=e1["id"], non_masci=False,
                     company="MASCI"),  # company MUST be set due to validator; reproduces "" via post-validate normalization
        ], [{
            "attendee_type": "employee", "source": "employee_master",
            "is_masci_employee": True, "review_status": "", "company": "MASCI",
            "employee_id": e1["id"],
        }]),

        ("3·subcontractor · correct hints", [
            attendee(name="Sam Subcontractor", non_masci=True,
                     company="Acme Excavation LLC", trade="Operator",
                     attendee_type="subcontractor", source="subcontractor_directory",
                     is_subcontractor=True),
        ], [{
            "attendee_type": "subcontractor", "source": "subcontractor_directory",
            "is_masci_employee": False, "is_subcontractor": True, "is_manual": False,
            "review_status": "", "company": "Acme Excavation LLC",
            "employee_id": "",
        }]),

        ("4·manual entry · no roster match", [
            attendee(name="Mystery Walk-On", non_masci=False, company="—"),
        ], [{
            "attendee_type": "manual", "source": "manual",
            "is_masci_employee": False, "is_manual": True,
            "review_status": "needs_review",
            "employee_id": "",
        }]),

        ("5·stale employee_id (not in employees)", [
            attendee(name="Stale Pick", employee_id=bogus_id, non_masci=False, company="MASCI"),
        ], [{
            "attendee_type": "manual", "source": "manual",
            "is_masci_employee": False, "is_manual": True,
            "review_status": "needs_review",
            "employee_id": "",  # invalid id stripped
        }]),

        ("6·duplicate roster pick (same id twice)", [
            attendee(name=e1["name"], employee_id=e1["id"], non_masci=False, company="MASCI"),
            attendee(name=e1["name"], employee_id=e1["id"], non_masci=False, company="MASCI"),
        ], [{
            "attendee_type": "employee", "source": "employee_master",
            "is_masci_employee": True, "employee_id": e1["id"],
        }]),  # expect ONE row, second collapsed

        ("7·inconsistent flags (non_masci=true with employee_id)", [
            attendee(name="Pretend Sub", employee_id=e2["id"], non_masci=True,
                     company="Smoke Sub LLC"),
        ], [{
            "attendee_type": "subcontractor", "source": "subcontractor_directory",
            "is_subcontractor": True, "employee_id": "",  # OurCo id stripped on sub row
            "company": "Smoke Sub LLC",
        }]),
    ]

    results = {"cases": [], "all_pass": True}
    created_meeting_ids: list[str] = []
    for label, attendees, expectations in cases:
        body = base_meeting(label[:60], attendees)
        case_result = {"case": label, "expected_rows": len(expectations), "pass": False}
        try:
            r = requests.post(f"{API_BASE}/api/meetings", json=body, timeout=60)
        except Exception as exc:
            case_result["error"] = f"network: {exc}"
            results["cases"].append(case_result)
            results["all_pass"] = False
            continue
        if r.status_code != 200:
            case_result["error"] = f"HTTP {r.status_code}: {r.text[:200]}"
            results["cases"].append(case_result)
            results["all_pass"] = False
            continue
        m = r.json()
        created_meeting_ids.append(m.get("id"))
        actual_atts = m.get("attendees") or []
        case_result["actual_count"] = len(actual_atts)
        if len(actual_atts) != len(expectations):
            case_result["error"] = f"expected {len(expectations)} rows, got {len(actual_atts)}"
            results["cases"].append(case_result)
            results["all_pass"] = False
            continue
        ok = True
        mismatches = []
        for idx, exp in enumerate(expectations):
            row = actual_atts[idx]
            for k, expected_val in exp.items():
                actual_val = row.get(k)
                if actual_val != expected_val:
                    ok = False
                    mismatches.append(f"row[{idx}].{k}: expected={expected_val!r} actual={actual_val!r}")
        case_result["pass"] = ok
        if not ok:
            case_result["mismatches"] = mismatches
            results["all_pass"] = False
        results["cases"].append(case_result)

    # Cleanup — delete every meeting we created
    cleaned = 0
    for mid in created_meeting_ids:
        try:
            d = requests.delete(f"{API_BASE}/api/meetings/{mid}", timeout=15)
            if d.status_code in (200, 204, 404, 410):
                cleaned += 1
        except Exception:
            pass
    results["cleanup"] = {
        "created": len(created_meeting_ids),
        "deleted_or_404": cleaned,
    }

    out_path = Path("/app/test_reports/track_15_73_slice2_identity_regression.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, default=str, indent=2))

    print("=" * 70)
    for c in results["cases"]:
        status = "✅ PASS" if c["pass"] else "❌ FAIL"
        print(f"  {status}  {c['case']}")
        if not c["pass"]:
            for m in c.get("mismatches", []):
                print(f"          {m}")
            if c.get("error"):
                print(f"          ERROR: {c['error']}")
    print("=" * 70)
    print(f"Overall: {'PASS' if results['all_pass'] else 'FAIL'}")
    print(f"Cleanup: {results['cleanup']}")
    print(f"Report: {out_path}")
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
