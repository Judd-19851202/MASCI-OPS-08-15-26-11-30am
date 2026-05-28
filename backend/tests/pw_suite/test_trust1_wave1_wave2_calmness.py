"""TRUST-1 · Wave 1 + Wave 2 · 2026-05-27.

End-to-end regression for the calmness contract of the new operator-
facing trust affordances added in Phase TRUST-1:

  * TF-022 — Support ID popover on NewDailyReport
      - Hidden by default behind a calm life-buoy button
      - Opens on click → shows "Support ID" + device-id value
      - Wording MUST NOT contain forbidden technical terms
      - Copy button is present and operable
  * TF-004 — Quota warning chip
      - Hidden by default on a normal device (>20% headroom)
  * TF-016 — Discarded-draft recovery notice
      - Hidden by default (no archive entry to recover)

Mobile viewport only — this is the field surface that the doctrine
applies to.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.parametrize("viewport_name", ["mobile"], indirect=True)]

_DAILY_REPORT_PATH = "/daily/submit"

_FORBIDDEN_TERMS = [
    "Fingerprint",
    "Tracking ID",
    "Device UUID",
    "Debug ID",
    "QuotaExceededError",
    "navigator.storage",
    "IndexedDB",
]


def _wait_for_form(page):
    page.wait_for_selector("text=Daily Job Report", timeout=15_000)
    page.wait_for_selector('[data-testid="daily-report-draft-pill"]', timeout=10_000)


def test_support_id_button_renders_in_header(page, base_url, viewport_name):
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    btn = page.locator('[data-testid="daily-report-support-id"]').first
    btn.wait_for(state="visible", timeout=5_000)
    # The button is calm (icon-only), not a chip.
    assert btn.get_attribute("aria-label") == "Show Support ID"


def test_support_id_popover_opens_with_calm_wording(page, base_url, viewport_name):
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    btn = page.locator('[data-testid="daily-report-support-id"]').first
    btn.click()
    pop = page.locator('[data-testid="daily-report-support-id-popover"]').first
    pop.wait_for(state="visible", timeout=3_000)
    text = (pop.text_content() or "").strip()
    # Must contain the preferred operator-facing label.
    assert "Support ID" in text, f"missing 'Support ID' label: {text!r}"
    # Must NOT contain any of the forbidden enterprise / debug terms.
    for term in _FORBIDDEN_TERMS:
        assert term not in text, (
            f"TF-022 doctrine violation — popover contains forbidden term "
            f"{term!r}. Calmness regression. Full text: {text!r}"
        )
    # Reassuring sub-line check (no scary language).
    assert "office" in text.lower(), (
        f"popover missing 'office' reassurance language: {text!r}"
    )
    # Device id value must be present and well-formed.
    val = page.locator('[data-testid="daily-report-support-id-value"]').first
    val_text = (val.text_content() or "").strip()
    assert val_text.startswith("d."), f"device id format unexpected: {val_text!r}"


def test_support_id_popover_has_copy_button(page, base_url, viewport_name):
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.locator('[data-testid="daily-report-support-id"]').first.click()
    copy_btn = page.locator('[data-testid="daily-report-support-id-copy"]').first
    copy_btn.wait_for(state="visible", timeout=3_000)
    # aria-label should be operator-friendly.
    assert copy_btn.get_attribute("aria-label") == "Copy Support ID"


def test_quota_chip_hidden_in_normal_session(page, base_url, viewport_name):
    """The quota warning chip MUST be hidden by default on a normal
    device — the operator should never see it unless storage is
    actually pressured (ratio >= 80%). Surfacing it in routine
    use would defeat the calmness doctrine."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1500)  # let probe land
    chip = page.locator('[data-testid="daily-report-quota-chip"]').first
    assert chip.count() == 0, "quota chip surfaced unexpectedly on a normal-storage device"


def test_recovery_notice_hidden_when_no_archive(page, base_url, viewport_name):
    """The TF-016 recovery banner only renders when a soft-deleted
    draft exists in the 24h archive store. On a fresh mount, it MUST
    NOT be visible — that would be alarming."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    page.wait_for_timeout(1000)
    notice = page.locator('[data-testid="daily-report-draft-recovery"]').first
    assert notice.count() == 0, "draft-recovery notice surfaced with no archive entry"
