from __future__ import annotations

import asyncio
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


from lib.notification_delivery import STATUS_CAPTURED_PREVIEW, deliver_notification  # noqa: E402
from services.operations_control.control_plane import _deliver_email_transport  # noqa: E402


class _AsyncInsertCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        self.docs.append(doc)


class _FakeDb:
    def __init__(self):
        self.notification_capture_v1 = _AsyncInsertCollection()


def test_deliver_notification_safe_capture_preserves_to_cc_bcc(monkeypatch):
    import branding_resolver  # noqa: WPS433

    async def _sender(_db, *args, **kwargs):
        return "noreply@example.com"

    async def _reply(_db, *args, **kwargs):
        return "ops@example.com"

    monkeypatch.setattr(branding_resolver, "resolve_sender_email", _sender)
    monkeypatch.setattr(branding_resolver, "resolve_reply_to_email", _reply)
    monkeypatch.setenv("APP_ENV", "preview")

    db = _FakeDb()
    out = asyncio.run(
        deliver_notification(
            db=db,
            workflow="daily-report",
            correlation_id="cid-1",
            record_id="dr-1",
            recipients=["pm@example.com", "copm@example.com", "audit@example.com"],
            to_recipients=["pm@example.com"],
            cc_recipients=["copm@example.com"],
            bcc_recipients=["audit@example.com"],
            subject="Daily Report",
            html="<p>Attached.</p>",
            attachments=[{"filename": "daily.pdf", "content": "Zm9v"}],
            metadata={"kind": "daily-report"},
        )
    )

    assert out["notification_state"] == STATUS_CAPTURED_PREVIEW
    capture = db.notification_capture_v1.docs[0]
    assert capture["to"] == ["pm@example.com"]
    assert capture["cc"] == ["copm@example.com"]
    assert capture["bcc"] == ["audit@example.com"]
    assert capture["attachments"][0]["filename"] == "daily.pdf"


def test_control_plane_daily_report_email_uses_canonical_subject_body_and_attachment(monkeypatch):
    captured = {}

    async def _fake_deliver_notification(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "notification_state": "captured_preview", "provider_accepted": False}

    monkeypatch.setattr(
        "services.operations_control.control_plane.deliver_notification",
        _fake_deliver_notification,
    )

    workflow = {
        "trust_workflow": "oppc-daily-report-proof-chain",
        "id": "oppc.daily_report_to_oppc",
    }
    event_doc = {
        "id": "event-1",
        "event_type_id": "oppc.daily_report.submitted",
    }
    communication = {
        "id": "comm-1",
        "template_id": "oppc.daily_report.submitted.v1",
        "correlation_id": "cid-1",
        "record_id": "dr-1",
        "workflow_id": "oppc.daily_report_to_oppc",
        "resolution": {"pm_name": "Chris Wright"},
    }
    rendered = {
        "title": "Daily Report submitted — Runtime Project",
        "message": "generic",
        "email_note": "generic",
    }
    recipients = {
        "to": ["pm@example.com"],
        "cc": ["copm@example.com"],
        "all": ["pm@example.com", "copm@example.com"],
    }
    record = {
        "id": "dr-1",
        "doc_id": "DR-2026-00001",
        "project_name": "Runtime Project",
        "project_number": "26-06",
        "report_date": "2026-08-04",
        "prepared_by": "Foreman One",
        "location": "North side",
        "masci_crews": [],
        "subcontractors": [],
        "visitors": [],
        "equipment": [],
        "materials": [],
        "activities": [],
        "photos": [],
        "ai_accepted_summary": "Crews completed grading and utility verification.",
    }

    asyncio.run(
        _deliver_email_transport(
            db=object(),
            workflow=workflow,
            event_doc=event_doc,
            communication=communication,
            rendered=rendered,
            recipients=recipients,
            record=record,
        )
    )

    assert captured["subject"].startswith("[MASCI · DAILY]")
    assert captured["to_recipients"] == ["pm@example.com"]
    assert captured["cc_recipients"] == ["copm@example.com"]
    assert captured["attachments"] and captured["attachments"][0]["filename"].endswith(".pdf")
    html = captured["html"]
    assert "Operational Intelligence Summary" in html
    assert "OPPC proof chain" not in html
    assert "registered control-plane policy" not in html
    assert "Operations Control Plane" not in html
    assert captured["metadata"]["kind"] == "daily-report"