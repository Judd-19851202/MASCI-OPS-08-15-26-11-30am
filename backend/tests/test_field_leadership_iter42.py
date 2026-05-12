"""Field Leadership module — iter42 backend regression."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to frontend env
    try:
        with open("/app/frontend/.env") as f:
            for ln in f:
                if ln.startswith("REACT_APP_BACKEND_URL"):
                    BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

API = f"{BASE_URL}/api/field-leadership"


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(f"{API}/login", json={"password": "MASCIGC"}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "MASCI1982!"}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(f"{BASE_URL}/api/pm/login",
                      json={"email": "chriswright@mascigc.com", "password": "ChrisRocksThis2026"},
                      timeout=15)
    if r.status_code != 200:
        pytest.skip(f"PM login failed: {r.status_code} {r.text}")
    return r.json()["token"]


def H(tok, kind="leadership"):
    # IMPORTANT: conftest auto-injects X-Admin-Token on every request via
    # setdefault. We override it to empty string so leadership/PM-only
    # tests actually exercise the leadership/PM gates.
    if kind == "admin":
        return {"X-Admin-Token": tok}
    if kind == "pm":
        return {"X-PM-Token": tok, "X-Admin-Token": ""}
    return {"X-Leadership-Token": tok, "X-Admin-Token": ""}


# ---------- AUTH ----------

def test_login_wrong_password():
    r = requests.post(f"{API}/login", json={"password": "WRONG"}, timeout=10)
    assert r.status_code == 401


def test_login_correct(leadership_token):
    assert isinstance(leadership_token, str) and len(leadership_token) > 20


def test_check_leadership(leadership_token):
    r = requests.get(f"{API}/check", headers=H(leadership_token), timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True and j["role"] == "leadership"


def test_check_admin(admin_token):
    r = requests.get(f"{API}/check", headers=H(admin_token, "admin"), timeout=10)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


# ---------- LOOKUP ----------

def test_jobs(leadership_token):
    r = requests.get(f"{API}/jobs", headers=H(leadership_token), timeout=15)
    assert r.status_code == 200
    items = r.json()["items"]
    assert isinstance(items, list) and len(items) > 0
    sample = items[0]
    for k in ["project_number", "project_name"]:
        assert k in sample


def test_employees_list(leadership_token):
    r = requests.get(f"{API}/employees", headers=H(leadership_token), timeout=15)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 100  # preview should have ~235


def test_employee_inline_create(leadership_token):
    payload = {"name": "TEST_FL_Employee_iter42", "trade": "Operator"}
    r = requests.post(f"{API}/employees", headers=H(leadership_token),
                      json=payload, timeout=15)
    assert r.status_code == 200
    eid = r.json()["id"]
    # Verify visible
    r2 = requests.get(f"{API}/employees", headers=H(leadership_token), timeout=15)
    names = [x["name"] for x in r2.json()["items"]]
    assert "TEST_FL_Employee_iter42" in names
    return eid


# ---------- CREATE / LIST / DELETE for all 10 kinds ----------

ALL_KINDS = [
    "write_up", "verbal_coaching", "attendance", "recognition",
    "equipment_checkout", "new_employee_eval", "crew_eval",
    "promotion_recommendation", "training_deficiency", "supervisor_notes",
]


def _minimal_payload(kind):
    return {
        "kind": kind,
        "project_number": "TEST-FL-001",
        "project_name": "Iter42 Test Job",
        "assigned_pm": "Test PM",
        "assigned_pm_email": "testpm@example.com",
        "employee_name": "TEST_FL_Sub_Employee",
        "supervisor_name": "TEST_Foreman",
        "details": {"summary": "iter42 regression"},
        "language": "en",
    }


@pytest.mark.parametrize("kind", [k for k in ALL_KINDS if k != "supervisor_notes"])
def test_create_all_kinds_leadership(kind, leadership_token):
    r = requests.post(API, headers=H(leadership_token),
                      json=_minimal_payload(kind), timeout=20)
    assert r.status_code == 200, f"{kind}: {r.status_code} {r.text[:200]}"
    rec = r.json()
    assert rec["ok"] is True
    assert "id" in rec


def test_supervisor_notes_no_longer_creatable(leadership_token):
    """Iter70 update: the Supervisor Notes Log tile was replaced with
    the Employee Termination workflow. The `supervisor_notes` kind was
    removed from FIELD_LEADERSHIP_KINDS so it can no longer be POSTed.
    Existing DB rows still render via the PDF + view endpoints (the
    field_leadership_pdf title map keeps the entry).

    Pin the new reality — POSTing supervisor_notes returns 400."""
    r = requests.post(API, headers=H(leadership_token),
                      json=_minimal_payload("supervisor_notes"), timeout=15)
    assert r.status_code == 400, (
        f"Iter70 removed supervisor_notes from the writable kind list. "
        f"Expected 400, got {r.status_code}. If supervisor_notes was "
        f"deliberately re-added, update this test to match."
    )


def test_employee_termination_creatable_by_leadership(leadership_token):
    """Iter70: the replacement workflow. Employee Termination must be
    POSTable by Field Leadership (MASCIGC) password the same way
    Supervisor Notes used to be."""
    payload = _minimal_payload("employee_termination")
    payload["details"] = {
        "separation_type": "Performance Issues",
        "detailed_explanation": "Iter42 regression test minimum 40 character explanation goes here for coverage.",
        "prior_disciplinary_actions": "Written Warning",
        "rehire_eligibility": "No",
        "law_enforcement_involved": "No",
    }
    r = requests.post(API, headers=H(leadership_token), json=payload, timeout=15)
    assert r.status_code == 200, f"create returned {r.status_code}: {r.text[:200]}"
    body = r.json()
    rec = body.get("record") or body
    assert rec["kind"] == "employee_termination"
    # Cleanup
    rid = rec.get("id")
    if rid:
        requests.delete(f"{API}/{rid}", headers=H(leadership_token), timeout=10)


def test_employee_termination_creatable_by_admin(admin_token):
    """Same as above, via the admin token path."""
    payload = _minimal_payload("employee_termination")
    payload["details"] = {
        "separation_type": "Safety Violation",
        "detailed_explanation": "Admin-path regression test minimum 40 character explanation goes here for coverage.",
        "prior_disciplinary_actions": "Final Warning",
        "rehire_eligibility": "Conditional",
        "rehire_conditions": "6 month re-eval.",
        "law_enforcement_involved": "No",
    }
    r = requests.post(API, headers=H(admin_token, "admin"), json=payload, timeout=20)
    assert r.status_code == 200, f"admin create returned {r.status_code}: {r.text[:200]}"
    body = r.json()
    rec = body.get("record") or body
    assert rec["kind"] == "employee_termination"
    rid = rec.get("id")
    if rid:
        requests.delete(f"{API}/{rid}", headers=H(admin_token, "admin"), timeout=10)


# ---------- LIST + filters ----------

def test_list_with_counts(leadership_token):
    r = requests.get(API, headers=H(leadership_token), timeout=20)
    assert r.status_code == 200
    j = r.json()
    assert "items" in j and "counts_by_kind" in j
    cbk = j["counts_by_kind"]
    for k in ALL_KINDS:
        assert k in cbk


def test_list_filter_kind(leadership_token):
    r = requests.get(API, headers=H(leadership_token),
                     params={"kind": "write_up"}, timeout=20)
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["kind"] == "write_up" for i in items)


def test_list_filter_employee(leadership_token):
    r = requests.get(API, headers=H(leadership_token),
                     params={"employee": "TEST_FL_Sub"}, timeout=20)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1


def test_list_filter_dates(leadership_token):
    from datetime import datetime, timedelta
    df = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    dt = datetime.utcnow().strftime("%Y-%m-%d")
    r = requests.get(API, headers=H(leadership_token),
                     params={"date_from": df, "date_to": dt}, timeout=20)
    assert r.status_code == 200


# ---------- GET single + PDF ----------

@pytest.fixture(scope="module")
def created_record(leadership_token):
    payload = _minimal_payload("write_up")
    payload["details"] = {"category": "Safety", "severity": "Verbal Warning",
                          "description": "iter42 PDF test", "corrective_action": "training"}
    r = requests.post(API, headers=H(leadership_token), json=payload, timeout=20)
    assert r.status_code == 200
    return r.json()["id"]


def test_get_record(created_record, leadership_token):
    r = requests.get(f"{API}/{created_record}", headers=H(leadership_token), timeout=15)
    assert r.status_code == 200
    assert r.json()["id"] == created_record


def test_pdf_bytes_and_footer(created_record, leadership_token):
    r = requests.get(f"{API}/{created_record}/pdf",
                     headers=H(leadership_token), timeout=30)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"
    # extract text via pypdf
    try:
        from pypdf import PdfReader
        import io as _io
        reader = PdfReader(_io.BytesIO(r.content))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        text = r.content.decode("latin-1", errors="ignore")
    assert "MASCI HUB" in text
    assert "ForgedOps" in text
    assert "2026" in text
    assert "Judd Group" not in text


def test_delete_as_leadership_forbidden(created_record, leadership_token):
    # Use a fresh record for isolation
    pl = _minimal_payload("recognition")
    pl["employee_name"] = "TEST_DEL_target"
    r0 = requests.post(API, headers=H(leadership_token), json=pl, timeout=15)
    rid = r0.json()["id"]
    r = requests.delete(f"{API}/{rid}", headers=H(leadership_token), timeout=15)
    # Endpoint requires admin; leadership should be 401/403
    assert r.status_code in (401, 403)


def test_delete_as_admin(admin_token, leadership_token):
    pl = _minimal_payload("recognition")
    pl["employee_name"] = "TEST_DEL_admin"
    r0 = requests.post(API, headers=H(leadership_token), json=pl, timeout=15)
    rid = r0.json()["id"]
    r = requests.delete(f"{API}/{rid}", headers=H(admin_token, "admin"), timeout=15)
    assert r.status_code == 200


def test_export_csv(leadership_token):
    r = requests.get(f"{API}/export/csv", headers=H(leadership_token), timeout=30)
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "Form Type" in r.text


def test_pm_scoping(pm_token):
    # PM token works on field-leadership/check
    r = requests.get(f"{API}/check", headers=H(pm_token, "pm"), timeout=10)
    assert r.status_code == 200
    # PM listing should NOT include our TEST-FL-001 records (PM not assigned to that fake job)
    r2 = requests.get(API, headers=H(pm_token, "pm"), timeout=20)
    assert r2.status_code == 200
    items = r2.json()["items"]
    fake_job_records = [i for i in items if i.get("project_number") == "TEST-FL-001"]
    assert len(fake_job_records) == 0, \
        f"PM should not see records for unassigned project, found {len(fake_job_records)}"
