from __future__ import annotations

import sys
import time

sys.path.insert(0, "/app/backend")

from routes.draft_telemetry import DraftEvent  # noqa: E402, PLC0415


def test_scoped_daily_report_form_key_longer_than_legacy_limit_is_valid() -> None:
    event = DraftEvent(
        eventId="pw-long-form-key-12345678",
        event="draft.write.ok",
        actorId="actor-123",
        deviceId="device-123",
        formKey="daily-report::PROJECT-LONG-NUMBER-12345678901234567890::2026-07-08::primary",
        ts=int(time.time() * 1000),
        meta={"trigger": "debounce", "payloadBytes": 2048},
    )

    assert event.formKey.endswith("::primary")
    assert "PROJECT-LONG-NUMBER" in event.formKey