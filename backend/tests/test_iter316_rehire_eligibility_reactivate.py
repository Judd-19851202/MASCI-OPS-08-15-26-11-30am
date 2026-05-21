"""
iter316 · Employee lifecycle rehire eligibility + reactivation closure.

Operator gap closed:
  • Terminations now require a STRUCTURED rehire eligibility choice
    (eligible / not_eligible / review_required) — the platform must
    never silently assume "eligible".
  • not_eligible and review_required require a short structured
    reason; eligible does not.
  • A bounded reactivate/rehire endpoint flips inactive/terminated
    employees back to Active or Pending Hire while preserving the
    write-once original_hire_date and appending a `kind="reactivate"`
    event to status_history.
  • An informational duplicate warning is returned when HR tries to
    add a new employee whose name or email matches an inactive or
    terminated employee — HR bypasses with `?force=true`.
  • New rehire_eligibility filter on the list endpoint.

Tests use the same live-preview / HR-auth pattern as iter312/iter313.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE_FILE = REPO_ROOT / "backend/routes/employee_lifecycle.py"
HR_EMPLOYEES_JSX = REPO_ROOT / "frontend/src/pages/HrEmployees.jsx"
EMPLOYEES_API_JS = REPO_ROOT / "frontend/src/lib/employeesApi.js"
TIPS_EN = REPO_ROOT / "backend/guidance/tips.py"
TIPS_ES = REPO_ROOT / "backend/guidance/tips_es.py"


def _kv(p: Path, k: str) -> str:
    try:
        with p.open() as f:
            for line in f:
                if line.startswith(f"{k}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _kv(REPO_ROOT / "frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

HR_EMAIL = "hrmanager@mascigc.com"
HR_PASSWORD = "HRTesting2026!"


def _hr_token() -> str:
    r = requests.post(
        f"{URL}/api/hr/login",
        json={"email": HR_EMAIL, "password": HR_PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _create(tok: str, name: str, email: str = "", force: bool = False) -> str:
    params = {"force": "true"} if force else {}
    r = requests.post(
        f"{URL}/api/hr/employees",
        headers={"X-HR-Token": tok},
        json={"name": name, "email": email, "lifecycle_status": "Active",
              "original_hire_date": "2024-01-15"},
        params=params,
        timeout=10,
    )
    return r


def _purge(name_prefix: str = "iter316_pytest"):
    """Best-effort cleanup of test employees via mongo to keep the suite
    self-contained without leaving rows behind."""
    try:
        import asyncio
        from dotenv import load_dotenv
        from motor.motor_asyncio import AsyncIOMotorClient
        load_dotenv(str(REPO_ROOT / "backend/.env"))

        async def _do():
            c = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = c[os.environ["DB_NAME"]]
            await db.employees.delete_many({
                "name": {"$regex": f"^{name_prefix}", "$options": "i"},
            })
        asyncio.run(_do())
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Runtime behavior — rehire eligibility on termination.
# ---------------------------------------------------------------------------


def test_iter316_termination_without_rehire_eligibility_defaults_to_review_required():
    """If HR omits rehire_eligibility on a transition into Terminated,
    the platform must NOT assume eligible — it defaults to
    review_required and then 400s because review_required REQUIRES a
    reason."""
    tok = _hr_token()
    name = "iter316_pytest_default"
    r = _create(tok, name)
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "involuntary"},
            timeout=10,
        )
        assert r2.status_code == 400, r2.text
        detail = (r2.json() or {}).get("detail", "")
        assert "rehire_eligibility_reason" in detail
        assert "review_required" in detail
    finally:
        _purge("iter316_pytest_default")


def test_iter316_termination_with_not_eligible_requires_reason():
    """not_eligible without a reason must be rejected."""
    tok = _hr_token()
    name = "iter316_pytest_notelig"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "involuntary",
                  "rehire_eligibility": "not_eligible"},
            timeout=10,
        )
        assert r2.status_code == 400
        assert "rehire_eligibility_reason" in (r2.json() or {}).get("detail", "")
    finally:
        _purge("iter316_pytest_notelig")


def test_iter316_termination_with_eligible_does_not_require_reason():
    """`eligible` is the only value that does NOT require a reason."""
    tok = _hr_token()
    name = "iter316_pytest_elig"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "eligible"},
            timeout=10,
        )
        assert r2.status_code == 200, r2.text
        emp = (r2.json() or {}).get("employee") or {}
        assert emp.get("rehire_eligibility") == "eligible"
        # No stale reason from a prior cycle should ride along.
        assert (emp.get("rehire_eligibility_reason") or "") == ""
    finally:
        _purge("iter316_pytest_elig")


def test_iter316_termination_with_review_required_and_reason_persists():
    tok = _hr_token()
    name = "iter316_pytest_review"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "review_required",
                  "rehire_eligibility_reason": "Supervisor weigh-in needed"},
            timeout=10,
        )
        assert r2.status_code == 200
        emp = r2.json().get("employee", {})
        assert emp.get("rehire_eligibility") == "review_required"
        assert emp.get("rehire_eligibility_reason") == "Supervisor weigh-in needed"
        assert emp.get("separation_type") == "voluntary"
    finally:
        _purge("iter316_pytest_review")


def test_iter316_invalid_rehire_eligibility_rejected():
    tok = _hr_token()
    name = "iter316_pytest_invalid"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "maybe"},
            timeout=10,
        )
        assert r2.status_code == 422 or r2.status_code == 400
    finally:
        _purge("iter316_pytest_invalid")


# ---------------------------------------------------------------------------
# Reactivation / rehire.
# ---------------------------------------------------------------------------


def test_iter316_reactivate_preserves_original_hire_date_and_records_rehire_date():
    tok = _hr_token()
    name = "iter316_pytest_reactivate"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "eligible"},
            timeout=10,
        ).raise_for_status()
        # Reactivate
        r3 = requests.post(
            f"{URL}/api/hr/employees/{eid}/reactivate",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Active",
                  "rehire_date": "2026-06-15",
                  "reason": "Operator-approved rehire"},
            timeout=10,
        )
        assert r3.status_code == 200, r3.text
        emp = r3.json().get("employee", {})
        assert emp.get("lifecycle_status") == "Active"
        assert emp.get("is_active") is True
        # Original hire date PRESERVED.
        assert emp.get("original_hire_date") == "2024-01-15"
        # Rehire date recorded.
        assert emp.get("rehire_date") == "2026-06-15"
        # Termination dates cleared from the live record.
        assert emp.get("termination_date") in (None, "")
        assert emp.get("last_day_worked") in (None, "")
        # Status history gained a reactivate event.
        history = emp.get("status_history") or []
        kinds = [h.get("kind") for h in history]
        assert "reactivate" in kinds
        last = history[-1]
        assert last.get("kind") == "reactivate"
        assert last.get("rehire_date") == "2026-06-15"
        assert last.get("preserved_original_hire_date") == "2024-01-15"
        # The reactivate event captures the previous termination data
        # for the audit trail (operator mandate: preserve prior
        # termination record in history).
        assert "preserved_termination_date" in last
        assert last.get("preserved_rehire_eligibility") == "eligible"
    finally:
        _purge("iter316_pytest_reactivate")


def test_iter316_reactivate_only_from_inactive_or_offboarded():
    """Active → Active reactivate must be rejected (409)."""
    tok = _hr_token()
    name = "iter316_pytest_active_reactivate"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees/{eid}/reactivate",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Active", "rehire_date": "2026-06-15"},
            timeout=10,
        )
        assert r2.status_code == 409
        assert "Cannot reactivate" in (r2.json() or {}).get("detail", "")
    finally:
        _purge("iter316_pytest_active_reactivate")


def test_iter316_reactivate_only_to_active_or_pending_hire():
    tok = _hr_token()
    name = "iter316_pytest_bad_target"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "eligible"},
            timeout=10,
        ).raise_for_status()
        r3 = requests.post(
            f"{URL}/api/hr/employees/{eid}/reactivate",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Seasonal", "rehire_date": "2026-07-01"},
            timeout=10,
        )
        # Pydantic rejects an out-of-range enum value before the route
        # body runs (422).
        assert r3.status_code in (400, 422)
    finally:
        _purge("iter316_pytest_bad_target")


def test_iter316_original_hire_date_remains_write_once_through_reactivate():
    """Write-once enforcement on original_hire_date persists across
    a reactivation cycle (audit-flagged risk #1)."""
    tok = _hr_token()
    name = "iter316_pytest_write_once"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "eligible"},
            timeout=10,
        ).raise_for_status()
        requests.post(
            f"{URL}/api/hr/employees/{eid}/reactivate",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Active", "rehire_date": "2026-06-15"},
            timeout=10,
        ).raise_for_status()
        # Try to overwrite original_hire_date — must be blocked.
        r4 = requests.patch(
            f"{URL}/api/hr/employees/{eid}",
            headers={"X-HR-Token": tok},
            json={"original_hire_date": "2020-01-01"},
            timeout=10,
        )
        assert r4.status_code in (400, 409)
        # Confirm the value did NOT change.
        r5 = requests.get(
            f"{URL}/api/hr/employees/{eid}/offboarding-summary",
            headers={"X-HR-Token": tok},
            timeout=10,
        )
        assert r5.status_code == 200
        emp = r5.json().get("employee", {})
        assert emp.get("original_hire_date") == "2024-01-15"
    finally:
        _purge("iter316_pytest_write_once")


# ---------------------------------------------------------------------------
# Duplicate prevention warning.
# ---------------------------------------------------------------------------


def test_iter316_inactive_name_match_returns_informational_warning():
    """Creating an employee with the same name as an inactive/terminated
    record must return a structured `possible_existing_inactive`
    payload, NOT a hard "already exists" block."""
    tok = _hr_token()
    name = "iter316_pytest_dup_name"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "eligible"},
            timeout=10,
        ).raise_for_status()
        # Same name (case-insensitive) — must trigger the warning.
        r2 = requests.post(
            f"{URL}/api/hr/employees",
            headers={"X-HR-Token": tok},
            json={"name": name.upper(), "lifecycle_status": "Active"},
            timeout=10,
        )
        assert r2.status_code == 409
        detail = (r2.json() or {}).get("detail")
        assert isinstance(detail, dict)
        assert detail.get("error") == "possible_existing_inactive"
        assert detail.get("candidate", {}).get("id") == eid
        assert detail.get("candidate", {}).get("lifecycle_status") == "Terminated"

        # ?force=true bypasses the warning.
        r3 = requests.post(
            f"{URL}/api/hr/employees?force=true",
            headers={"X-HR-Token": tok},
            json={"name": name, "lifecycle_status": "Active"},
            timeout=10,
        )
        assert r3.status_code == 200, r3.text
        assert r3.json().get("id") != eid
    finally:
        _purge("iter316_pytest_dup_name")


def test_iter316_inactive_email_match_also_triggers_warning():
    tok = _hr_token()
    name = "iter316_pytest_dup_email"
    email = "iter316.pytest.dupe@masci.test.local"
    r = _create(tok, name, email=email)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "eligible"},
            timeout=10,
        ).raise_for_status()
        # Different name, same email — must trigger.
        r2 = requests.post(
            f"{URL}/api/hr/employees",
            headers={"X-HR-Token": tok},
            json={"name": "Completely Different Name",
                  "email": email,
                  "lifecycle_status": "Active"},
            timeout=10,
        )
        assert r2.status_code == 409
        detail = (r2.json() or {}).get("detail")
        assert isinstance(detail, dict)
        assert detail.get("error") == "possible_existing_inactive"
    finally:
        _purge("iter316_pytest_dup_email")


def test_iter316_active_name_collision_still_strictly_blocked():
    """An ACTIVE same-name record still produces a strict 409 — the
    informational warning is reserved for inactive/terminated matches
    so HR doesn't accidentally create a second active record."""
    tok = _hr_token()
    name = "iter316_pytest_active_collision"
    r = _create(tok, name)
    assert r.status_code == 200
    try:
        r2 = requests.post(
            f"{URL}/api/hr/employees",
            headers={"X-HR-Token": tok},
            json={"name": name, "lifecycle_status": "Active"},
            timeout=10,
        )
        assert r2.status_code == 409
        # Strict string detail, NOT the structured warning dict.
        assert isinstance((r2.json() or {}).get("detail"), str)
    finally:
        _purge("iter316_pytest_active_collision")


# ---------------------------------------------------------------------------
# Filters.
# ---------------------------------------------------------------------------


def test_iter316_list_rehire_eligibility_filter():
    """`rehire_eligibility=review_required` returns only those rows."""
    tok = _hr_token()
    name = "iter316_pytest_filter"
    r = _create(tok, name)
    assert r.status_code == 200
    eid = r.json()["id"]
    try:
        requests.post(
            f"{URL}/api/hr/employees/{eid}/status",
            headers={"X-HR-Token": tok},
            json={"lifecycle_status": "Terminated",
                  "separation_type": "voluntary",
                  "rehire_eligibility": "review_required",
                  "rehire_eligibility_reason": "iter316 filter test"},
            timeout=10,
        ).raise_for_status()
        r2 = requests.get(
            f"{URL}/api/hr/employees",
            headers={"X-HR-Token": tok},
            params={"show_inactive": "true",
                    "rehire_eligibility": "review_required"},
            timeout=10,
        )
        assert r2.status_code == 200
        items = (r2.json() or {}).get("items") or []
        # Our test row must appear and every row must have the filter
        # value (no leakage of other eligibility states).
        names = [it.get("name") for it in items]
        assert name in names
        for it in items:
            assert it.get("rehire_eligibility") == "review_required"

        # Invalid value rejected.
        r3 = requests.get(
            f"{URL}/api/hr/employees",
            headers={"X-HR-Token": tok},
            params={"rehire_eligibility": "maybe"},
            timeout=10,
        )
        assert r3.status_code == 400
    finally:
        _purge("iter316_pytest_filter")


# ---------------------------------------------------------------------------
# Static-code invariants — keep the contract from silently drifting.
# ---------------------------------------------------------------------------


def test_iter316_route_module_invariants():
    src = ROUTE_FILE.read_text()
    # Allowed rehire eligibility values are declared centrally.
    assert "ALLOWED_REHIRE_ELIGIBILITY = {" in src
    for v in ("eligible", "not_eligible", "review_required"):
        assert f'"{v}"' in src
    # Reason-required pair must include exactly the two values that
    # operator mandated need a reason.
    assert (
        "_REHIRE_ELIGIBILITY_REQUIRES_REASON = "
        '{"not_eligible", "review_required"}'
    ) in src
    # Reactivate route registered with HR-or-Admin gate.
    assert (
        '@router.post("/api/hr/employees/{employee_id}/reactivate")'
        in src
    )
    # Reactivatable status set is the operator-mandated four.
    assert (
        '_REACTIVATABLE_STATUSES = '
        '{"Inactive", "Terminated", "Resigned", "Retired"}'
    ) in src
    # rehire_date is part of the write-once-protection date list but
    # NOT itself write-once.
    assert '"rehire_date"' in src
    assert '_WRITE_ONCE_FIELDS = ("original_hire_date",)' in src
    # Helper for inactive duplicate match exists.
    assert "_find_inactive_match" in src
    # Index includes rehire_eligibility for filter performance.
    assert 'await db.employees.create_index("rehire_eligibility")' in src


def test_iter316_frontend_invariants():
    src = HR_EMPLOYEES_JSX.read_text()
    # New rehire-eligibility filter dropdown.
    assert 'data-testid="hremp-rehire-filter"' in src
    assert "rehire_eligibility" in src
    # Status-change form fields for rehire eligibility.
    assert 'data-testid="hremp-rehire-eligibility"' in src
    assert 'data-testid="hremp-rehire-reason"' in src
    # Reactivate dialog + trigger.
    assert 'data-testid="hremp-reactivate-trigger"' in src
    assert 'data-testid="hremp-reactivate-confirm"' in src
    assert 'data-testid="hremp-reactivate-rehire-date"' in src
    # Drawer display fields.
    assert 'data-testid="hremp-rehire-eligibility-display"' in src
    assert 'data-testid="hremp-rehire-date-display"' in src
    # Duplicate warning surface in AddDialog.
    assert 'data-testid="hremp-add-dup-warning"' in src
    assert 'data-testid="hremp-add-dup-reactivate"' in src
    assert 'data-testid="hremp-add-dup-force"' in src
    # Coaching family wired.
    assert 'formKey="employee-lifecycle.rehire"' in src

    # employeesApi.js wires the new endpoint.
    api = EMPLOYEES_API_JS.read_text()
    assert "reactivateHrEmployee" in api
    assert "/hr/employees/${id}/reactivate" in api
    assert "force: \"true\"" in api or 'force ? { force: "true" }' in api


def test_iter316_coaching_family_present_en_es():
    en = TIPS_EN.read_text()
    es = TIPS_ES.read_text()
    # 4 EN tips: why / mistake / next / escalate
    assert '"form_key": "employee-lifecycle.rehire"' in en
    for kind in ("why", "mistake", "next", "escalate"):
        # Each kind appears at least once under the rehire form key.
        block_pattern = re.compile(
            r'"form_key":\s*"employee-lifecycle\.rehire",\s*'
            r'"kind":\s*"' + kind + r'"'
        )
        assert block_pattern.search(en), (
            f"missing employee-lifecycle.rehire / {kind} tip in EN"
        )
        # ES translation present
        assert f'("employee-lifecycle.rehire", "{kind}")' in es, (
            f"missing ES translation for employee-lifecycle.rehire / {kind}"
        )
