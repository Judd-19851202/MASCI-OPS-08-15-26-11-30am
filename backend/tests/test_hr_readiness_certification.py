"""
tests/test_hr_readiness_certification.py — Track 14.0-HR-READINESS

Regression coverage for the HR operational readiness sweep:

  1. Submitting a `new_hire` (or `termination`) employee request fans
     out an in-app notification to every active HR user with a
     `link_url=/hr/employee-requests?id=<rid>` so the bell click-through
     lands directly on the queue. The previous behaviour was a silent
     insert with no notification — HR would click the bell and find
     nothing.

  2. The HR Queue page deep-links via `?id=<rid>`: the matching card
     is highlighted, auto-scrolled, and the approval dialog opens
     automatically so HR can act in a single click.

  3. The submit schema (`EmployeeRequestCreate`) and the approve
     schema (`EmployeeRequestApprove`) both accept
     `legal_first_name` / `legal_middle_name` / `legal_last_name` /
     `preferred_name` so the field submission preserves identity
     granularity ("James Michael Fisher (Jimmy)" pattern).

  4. The approval handler persists `preferred_name` + legal name
     parts on the created employee record.

These are static-analysis assertions — no live DB writes — so they
run anywhere.

Closure ledger:
/app/memory/TRACK_14_0_HR_READINESS_CERTIFICATION_SWEEP_CLOSURE.md
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path("/app")
EMPLOYEE_REQUESTS = REPO / "backend/routes/employee_requests.py"
FIELD_LEADERSHIP = REPO / "backend/routes/field_leadership.py"
HR_QUEUE_JSX = REPO / "frontend/src/pages/HrEmployeeRequestsQueue.jsx"


# ── Notification fan-out on submit ────────────────────────────────


def test_employee_request_submit_creates_hr_notification():
    """submit_request must call _notify_hr_queue_pending so the
    new pending row is visible from the HR bell. Without this the
    `/api/employee-requests` POST silently inserts a row that no
    operator ever sees ('click and nothing happens')."""
    text = EMPLOYEE_REQUESTS.read_text()
    assert "_notify_hr_queue_pending" in text, (
        "employee_requests.py no longer defines _notify_hr_queue_pending. "
        "Restore the helper or HR will lose the bell click-through.")
    # The submit handler must invoke the helper after the insert.
    start = text.find("async def submit_request(")
    assert start > 0, "submit_request endpoint missing"
    body = text[start:start + 5000]
    assert "_notify_hr_queue_pending(db, doc, kind)" in body, (
        "submit_request no longer fans out the bell notification."
    )


def test_field_leadership_inline_add_creates_hr_notification():
    """The field-leadership inline-add path produces an
    `employee_requests` row too — and must also fan out an HR
    notification so the bell click-through path works regardless of
    where the request originated."""
    text = FIELD_LEADERSHIP.read_text()
    assert "_notify_hr_queue_pending" in text, (
        "field_leadership.py no longer imports / calls "
        "_notify_hr_queue_pending after employee_requests.insert_one. "
        "Restore the call or FL-originated requests lose bell click-through.")


def test_hr_notification_link_url_format():
    """The notification link_url must be `/hr/employee-requests?id=<rid>`
    so the queue page's deep-link useEffect can highlight + auto-open
    the matching request."""
    text = EMPLOYEE_REQUESTS.read_text()
    assert "link_url = f\"/hr/employee-requests?id={rid}\"" in text, (
        "_notify_hr_queue_pending changed the link_url format. The "
        "queue page expects /hr/employee-requests?id=<rid>.")


# ── Legal-name + preferred-name schema contract ───────────────────


def test_create_schema_accepts_legal_and_preferred_names():
    """EmployeeRequestCreate must accept legal_first_name /
    legal_middle_name / legal_last_name / preferred_name so the
    field submission preserves identity granularity."""
    text = EMPLOYEE_REQUESTS.read_text()
    for field in (
        "legal_first_name: Optional[str]",
        "legal_middle_name: Optional[str]",
        "legal_last_name: Optional[str]",
        "preferred_name: Optional[str]",
    ):
        assert field in text, (
            f"EmployeeRequestCreate schema lost {field!r}. HR identity "
            "granularity is broken — restore the field.")


def test_approve_schema_accepts_legal_and_preferred_names():
    """EmployeeRequestApprove must accept the same identity fields so
    HR can edit names + preferred name during approval. Previously
    posting preferred_name returned 422 ('extra_forbidden')."""
    text = EMPLOYEE_REQUESTS.read_text()
    start = text.find("class EmployeeRequestApprove(BaseModel):")
    assert start > 0
    body = text[start:start + 1500]
    for field in (
        "legal_first_name: Optional[str]",
        "legal_middle_name: Optional[str]",
        "legal_last_name: Optional[str]",
        "preferred_name: Optional[str]",
    ):
        assert field in body, (
            f"EmployeeRequestApprove schema lost {field!r}. The HR "
            "queue Approve modal cannot send the identity update.")


def test_approval_persists_preferred_name_on_employee():
    """The approve handler builds the employees doc with legal_* +
    preferred_name keys so directory views and field forms can
    display James Fisher (Jimmy)."""
    text = EMPLOYEE_REQUESTS.read_text()
    start = text.find("async def approve_request(")
    assert start > 0
    body = text[start:start + 8000]
    for needle in (
        '"legal_first_name": payload.get("legal_first_name")',
        '"legal_middle_name": payload.get("legal_middle_name")',
        '"legal_last_name": payload.get("legal_last_name")',
        '"preferred_name": payload.get("preferred_name")',
    ):
        assert needle in body, (
            f"approve_request no longer persists {needle.split(':')[0]!s} "
            "on the created employee. Identity loss on approval — fix it."
        )


# ── HR Queue page deep-link contract ──────────────────────────────


def test_hr_queue_page_reads_deep_link_id():
    """HrEmployeeRequestsQueue must read the `id` URL search param so
    bell click-through can land on the queue and auto-open the
    matching request's approval dialog."""
    text = HR_QUEUE_JSX.read_text()
    assert "useSearchParams" in text, (
        "HrEmployeeRequestsQueue no longer imports useSearchParams. "
        "Bell deep-link broken.")
    assert 'searchParams.get("id")' in text, (
        "HrEmployeeRequestsQueue no longer reads ?id from the URL. "
        "Bell deep-link broken.")
    # The effect must fire openApprove on the matched item.
    assert "openApprove(target)" in text, (
        "HrEmployeeRequestsQueue no longer auto-opens the approval "
        "dialog for the deep-linked request. Bell click-through "
        "becomes a hunt-and-click for HR — that is the exact "
        "'click does nothing' regression this track exists to "
        "prevent.")
    # The row must visibly highlight when matched.
    assert "deepLinkRequestId === req.id" in text, (
        "HrEmployeeRequestsQueue no longer highlights the deep-linked "
        "row — HR loses the visual cue.")
