from __future__ import annotations

import pytest

from lib.notification_delivery import (
    DELIVERY_MODE_PROVIDER_LIVE,
    DELIVERY_MODE_SAFE_CAPTURE,
    DELIVERY_MODE_DISABLED,
    STATUS_CAPTURED_PREVIEW,
    STATUS_CONFIGURATION_BLOCKED,
    STATUS_PROVIDER_ACCEPTED,
    canonical_app_env,
    delivery_contract,
    determine_delivery_mode,
    key_is_configured,
    key_shape_valid,
    deliver_notification,
)


class _CaptureCollection:
    def __init__(self) -> None:
        self.rows = []

    async def insert_one(self, doc):
        self.rows.append(doc)


class _FakeDb:
    def __init__(self) -> None:
        self.notification_capture_v1 = _CaptureCollection()


def test_preview_selects_safe_capture_without_provider_key() -> None:
    env = {"APP_ENV": "preview", "RESEND_API_KEY": ""}
    contract = delivery_contract(env)
    assert canonical_app_env(env) == "preview"
    assert determine_delivery_mode(env) == DELIVERY_MODE_SAFE_CAPTURE
    assert contract["provider_key_required"] is False
    assert contract["blocking"] is False
    assert contract["provider_validation_status"] == "not_required"


def test_production_requires_live_provider_key() -> None:
    env = {"APP_ENV": "production", "RESEND_API_KEY": ""}
    contract = delivery_contract(env)
    assert determine_delivery_mode(env) == DELIVERY_MODE_PROVIDER_LIVE
    assert contract["blocking"] is True
    assert contract["provider_validation_status"] == "missing"


def test_production_placeholder_key_is_invalid() -> None:
    env = {"APP_ENV": "production", "RESEND_API_KEY": "placeholder-key"}
    contract = delivery_contract(env)
    assert key_is_configured(env["RESEND_API_KEY"]) is False
    assert contract["blocking"] is True
    assert contract["provider_validation_status"] == "missing"


def test_production_nonstandard_key_is_blocking() -> None:
    env = {"APP_ENV": "production", "RESEND_API_KEY": "abc123"}
    contract = delivery_contract(env)
    assert key_is_configured(env["RESEND_API_KEY"]) is True
    assert key_shape_valid(env["RESEND_API_KEY"]) is False
    assert contract["provider_validation_status"] == "invalid"


def test_unknown_environment_fails_safely() -> None:
    env = {"APP_ENV": "wat"}
    contract = delivery_contract(env)
    assert canonical_app_env(env) == "invalid"
    assert determine_delivery_mode(env) == DELIVERY_MODE_DISABLED
    assert contract["blocking"] is True


def test_preview_ignores_live_mode_override() -> None:
    env = {
        "APP_ENV": "preview",
        "RESEND_API_KEY": "re_invalid_but_unused",
        "NOTIFICATION_DELIVERY_MODE": DELIVERY_MODE_PROVIDER_LIVE,
    }
    contract = delivery_contract(env)
    assert contract["delivery_mode"] == DELIVERY_MODE_SAFE_CAPTURE
    assert contract["delivery_mode_source"] == "environment_forced_safe_capture"
    assert contract["provider_validation_status"] == "preview_override_ignored"
    assert contract["external_send_allowed"] is False


def test_production_ignores_safe_capture_override_and_fails_closed() -> None:
    env = {
        "APP_ENV": "production",
        "RESEND_API_KEY": "",
        "NOTIFICATION_DELIVERY_MODE": DELIVERY_MODE_SAFE_CAPTURE,
    }
    contract = delivery_contract(env)
    assert contract["delivery_mode"] == DELIVERY_MODE_PROVIDER_LIVE
    assert contract["delivery_mode_source"] == "environment_forced_provider_live"
    assert contract["blocking"] is True
    assert contract["provider_validation_status"] == "missing"


@pytest.mark.asyncio
async def test_preview_delivery_captures_without_provider_call() -> None:
    env = {
        "APP_ENV": "preview",
        "RESEND_API_KEY": "re_invalid_but_unused",
        "NOTIFICATION_DELIVERY_MODE": DELIVERY_MODE_PROVIDER_LIVE,
    }
    fake_db = _FakeDb()
    delivery = await deliver_notification(
        db=fake_db,
        workflow="daily-report",
        correlation_id="cid-test-preview",
        record_id="dr-preview-1",
        recipients=["pm@example.com"],
        subject="Preview capture proof",
        html="<p>preview capture</p>",
        metadata={"proof": True},
        env=env,
    )
    assert delivery["notification_state"] == STATUS_CAPTURED_PREVIEW
    assert delivery["provider_called"] is False
    assert delivery["provider_accepted"] is False
    assert delivery["delivery_mode"] == DELIVERY_MODE_SAFE_CAPTURE
    assert len(fake_db.notification_capture_v1.rows) == 1


@pytest.mark.asyncio
async def test_production_invalid_key_blocks_before_provider_call() -> None:
    env = {
        "APP_ENV": "production",
        "RESEND_API_KEY": "abc123",
    }
    fake_db = _FakeDb()
    delivery = await deliver_notification(
        db=fake_db,
        workflow="daily-report",
        correlation_id="cid-test-prod",
        record_id="dr-prod-1",
        recipients=["pm@example.com"],
        subject="Prod blocked proof",
        html="<p>prod blocked</p>",
        metadata={"proof": True},
        env=env,
    )
    assert delivery["notification_state"] == STATUS_CONFIGURATION_BLOCKED
    assert delivery["provider_called"] is False
    assert delivery["provider_accepted"] is False
    assert fake_db.notification_capture_v1.rows == []


def test_status_constants_are_stable() -> None:
    assert STATUS_CAPTURED_PREVIEW == "captured_preview"
    assert STATUS_CONFIGURATION_BLOCKED == "configuration_blocked"
    assert STATUS_PROVIDER_ACCEPTED == "provider_accepted"