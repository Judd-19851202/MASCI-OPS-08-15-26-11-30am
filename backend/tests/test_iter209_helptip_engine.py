"""iter209 — Contextual Operational Guidance Engine (HelpTip)

Backend coverage:
  • /api/guidance/tips?form_key=<key> returns RBAC-filtered tips
  • Empty form_key returns empty
  • Parent-context fall-up: requesting "daily-report.crew" returns
    BOTH daily-report.crew tips AND daily-report tips
  • Bilingual: every seed tip has both title/body and title_es/body_es
  • Registry validation passes
  • Banned-phrase guardrail still applies: tips must not leak protected
    portal workflow content
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

ALL_FORM_KEYS = [
    "daily-report",
    "daily-report.crew",
    "daily-report.equipment",
    "daily-report.materials",
    "daily-report.photos",
    "daily-report.narrative",
]

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def test_tips_registry_validates_clean():
    import guidance  # noqa: F401
    from guidance.tips import validate_tips_registry, all_tips
    issues = validate_tips_registry(strict=False)
    assert issues == [], f"Tips registry has issues: {issues}"
    assert len(all_tips()) >= 16, (
        "Initial Daily-Report seed should land at least 16 tips"
    )


def test_tips_endpoint_anon_returns_daily_report_top_level():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=daily-report",
        timeout=10.0,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["form_key"] == "daily-report"
    assert data["count"] >= 3
    kinds = {t["kind"] for t in data["tips"]}
    # Top-level Daily Report should have why/who/next/escalate at minimum
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"daily-report top-level should expose kind={required}; "
            f"got {kinds}"
        )


def test_tips_endpoint_parent_context_fall_up():
    """Requesting a leaf form_key should also return parent-level tips."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=daily-report.crew",
        timeout=10.0,
    )
    assert r.status_code == 200
    tips = r.json()["tips"]
    form_keys_returned = {t["form_key"] for t in tips}
    assert "daily-report.crew" in form_keys_returned, (
        "Leaf-level crew tips must appear"
    )
    assert "daily-report" in form_keys_returned, (
        "Parent-level daily-report tips must also appear (fall-up)"
    )


def test_tips_endpoint_empty_form_key():
    r = httpx.get(f"{API_URL}/api/guidance/tips", timeout=10.0)
    assert r.status_code == 200
    assert r.json() == {"form_key": "", "tips": []}


@pytest.mark.parametrize("form_key", ALL_FORM_KEYS)
def test_tips_have_allowed_kinds(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    assert r.status_code == 200
    for t in r.json()["tips"]:
        assert t["kind"] in ALLOWED_KINDS, (
            f"tip kind {t['kind']!r} not in allowed set {ALLOWED_KINDS}"
        )


@pytest.mark.parametrize("form_key", ALL_FORM_KEYS)
def test_tips_are_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        # Every seed tip must have Spanish
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


@pytest.mark.parametrize("form_key", ALL_FORM_KEYS)
def test_tips_are_concise(form_key):
    """Tips must be coaching, not documentation. Hard cap of 80 words."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN body too long ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES body too long ({wc_es} words)"


BANNED_WORKFLOW_PHRASES = [
    "User management — invite",
    "Audit log — every privileged",
    "Backups & restore — manual triggers",
    "Role templates — define",
    "Sessions — who is signed in",
]


@pytest.mark.parametrize("form_key", ALL_FORM_KEYS)
def test_tips_do_not_leak_admin_workflows(form_key):
    """Tips must not enumerate protected portal workflow content."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        text = " ".join([t.get("body") or "", t.get("body_es") or ""])
        leaks = [p for p in BANNED_WORKFLOW_PHRASES if p in text]
        assert not leaks, (
            f"{t['form_key']}/{t['kind']} leaks workflow phrases: {leaks}"
        )


def test_tips_endpoint_long_form_key_is_truncated_not_500():
    """Defensive: oversized form_key must not 500 — server should
    truncate and respond cleanly with an empty / no-match result."""
    long_key = "a" * 5000
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={long_key}",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json()["tips"] == []
