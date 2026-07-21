from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "/app/backend")

from lib.governed_certification_lane import (  # noqa: E402, PLC0415
    GOVERNED_CERTIFICATION_CO_PM_EMAILS,
    apply_governed_daily_report_lane,
    build_governed_routing_override,
)
from pm_routing import recipients_for_record_async  # noqa: E402, PLC0415
from routes.daily_reports import (  # noqa: E402, PLC0415
    _apply_certification_record_safety,
    _should_schedule_daily_report_email,
)


def test_governed_lane_auto_classifies_runtime_cert_daily_report() -> None:
    doc = apply_governed_daily_report_lane(
        {
            "id": "dr-governed-1",
            "project_number": "ZZ-RUNTIME-CERT-2026",
            "project_name": "Runtime Certification — Internal Test Project",
            "prepared_by": "Certification Foreman",
            "prepared_by_identity": {
                "directory": "fl",
                "user_id": "cert.foreman@example.com",
                "name": "Certification Foreman",
                "email": "cert.foreman@example.com",
                "role": "Foreman",
            },
        },
        project_doc={
            "project_number": "ZZ-RUNTIME-CERT-2026",
            "project_name": "Runtime Certification — Internal Test Project",
            "pm_email": "jaymn.judd@mascigc.com",
            "co_pm_emails": ["cert.copm@example.com"],
            "active": True,
        },
    )
    doc = _apply_certification_record_safety(doc)

    assert doc["certification_record"] is True
    assert doc["synthetic_record"] is True
    assert doc["hidden_from_operations"] is True
    assert doc["email_dispatch_suppressed"] is False
    assert doc["certification_lane_allows_email"] is True
    assert doc["certification_release_reason"] == "governed_production_certification_lane"
    assert doc["routing_override"]["to"] == ["jaymn.judd@mascigc.com"]
    assert doc["routing_override"]["cc"] == []
    assert doc["certification_lane"]["project_verified"] is True
    assert doc["certification_lane"]["identity_verified"] is True
    assert doc["certification_lane"]["project_snapshot"]["pm_email"] == "jaymn.judd@mascigc.com"
    assert doc["certification_lane"]["recipient_validation"]["placeholder_example_domain_selected"] is False
    assert doc["certification_lane"]["recipient_validation"]["resolved_to"] == [
        "jaymn.judd@mascigc.com"
    ]
    assert doc["routing_override"]["recipient_source"] == "project_doc"
    assert "trust-spine" in doc["certification_required_workflows"]
    assert "pdf" in doc["certification_required_workflows"]
    assert _should_schedule_daily_report_email(doc) is True


def test_governed_lane_skips_placeholder_project_recipients_and_uses_env_fallback(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_DEAD_LETTER_EMAIL", "preview-cert@mascigc.com")
    monkeypatch.setenv("BACKUP_EMAIL_TO", "preview-cert-cc@mascigc.com")

    routing = build_governed_routing_override(
        project_doc={
            "pm_email": "cert.pm@example.com",
            "co_pm_emails": ["cert.copm@example.com"],
        }
    )

    assert routing["to"] == ["preview-cert@mascigc.com"]
    assert routing["cc"] == ["preview-cert-cc@mascigc.com"]
    assert routing["recipient_source"] == "environment_fallback"
    assert all("example.com" not in email for email in routing["all"])


def test_generic_certification_record_still_suppresses_email() -> None:
    doc = _apply_certification_record_safety(
        {
            "id": "dr-cert-explicit",
            "certification_record": True,
            "project_number": "26-07",
        }
    )
    assert doc["email_dispatch_suppressed"] is True
    assert _should_schedule_daily_report_email(doc) is False


class _FakeCollection:
    async def find_one(self, *_args, **_kwargs):
        return None

    def find(self, *_args, **_kwargs):
        return _FakeCursor([])


class _FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def __aiter__(self):
        self._iter = iter(self.rows)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class _FakeDB:
    jobs_master = _FakeCollection()
    project_managers = _FakeCollection()
    project_team_assignments = _FakeCollection()


def test_pm_routing_honors_governed_override_recipients() -> None:
    async def _run():
        return await recipients_for_record_async(
            _FakeDB(),
            {
                "project_number": "ZZ-RUNTIME-CERT-2026",
                "routing_override": {
                    "enabled": True,
                    "pm_name": "Certification PM",
                        "to": ["cert.pm@example.com"],
                    "cc": GOVERNED_CERTIFICATION_CO_PM_EMAILS,
                },
            },
            kind="daily-report",
        )

    dist = asyncio.run(_run())
    assert dist["pm_email"] == "cert.pm@example.com"
    assert dist["to"] == ["cert.pm@example.com"]
    assert dist["cc"] == GOVERNED_CERTIFICATION_CO_PM_EMAILS
    assert dist["all"] == ["cert.pm@example.com", *GOVERNED_CERTIFICATION_CO_PM_EMAILS]