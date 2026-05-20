"""iter270 — Safety Meeting coaching family parity test.

Closes the operational coaching parity gap. Safety Meeting was the only
high-cadence safety workflow without an embedded HelpTip family — every
other mature workflow (incident, writeup, daily-report, preop, checkout,
time-verification, crew_eval, etc.) has one.

Same Tier-1 discipline as iter210 (incident):
  • public-scope (anonymous-readable — meeting form is public-facing)
  • concise (≤80 EN words, ≤90 ES words per body)
  • bilingual
  • no protected workflow leakage
  • parent-context fall-up: leaf form_keys also return parent tips
  • operator-priority surfaces covered (don't pencil-whip, tie to today's
    work, escalation, photos prove the meeting happened where work was)
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

MEETING_FORM_KEYS = [
    "meeting",
    "meeting.context",
    "meeting.topic",
    "meeting.attendees",
    "meeting.photos",
    "meeting.signoff",
]

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def test_meeting_registry_seed_count():
    """Coaching parity benchmark: incident landed 18 tips. Meeting must
    match or exceed (22 expected · 4 form-root + 3·5·4·3·3 sections)."""
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    meeting_tips = [
        t for t in all_tips()
        if t["form_key"] == "meeting" or t["form_key"].startswith("meeting.")
    ]
    assert len(meeting_tips) >= 22, (
        f"Meeting coaching family should land ≥22 tips for parity; "
        f"got {len(meeting_tips)}"
    )


def test_meeting_top_level_exposes_canonical_four_tips():
    """Top-level meeting must offer Why / Who / Next / Escalate — same
    canonical surface as incident / daily-report / writeup."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=meeting",
        timeout=10.0,
    )
    assert r.status_code == 200
    kinds = {t["kind"] for t in r.json()["tips"]}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"meeting top-level missing kind={required}; got {kinds}"
        )


@pytest.mark.parametrize("form_key", MEETING_FORM_KEYS)
def test_meeting_tip_endpoint_anon_returns_tips(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    assert r.status_code == 200
    tips = r.json()["tips"]
    assert len(tips) >= 1, (
        f"{form_key} should return at least one tip (incl. parent fall-up)"
    )


def test_meeting_leaf_includes_parent_context():
    """Leaf form_keys must also return the parent 'meeting' tips —
    proves the form_key prefix-ladder works for the new family."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=meeting.topic",
        timeout=10.0,
    )
    keys = {t["form_key"] for t in r.json()["tips"]}
    assert "meeting" in keys, (
        "Parent 'meeting' tips must appear when querying a leaf"
    )
    assert "meeting.topic" in keys


@pytest.mark.parametrize("form_key", MEETING_FORM_KEYS)
def test_meeting_tips_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        if not t["form_key"].startswith("meeting"):
            continue  # parent fall-ups outside meeting are validated elsewhere
        assert t.get("title_es"), (
            f"{t['form_key']}/{t['kind']}: missing title_es"
        )
        assert t.get("body_es"), (
            f"{t['form_key']}/{t['kind']}: missing body_es"
        )


@pytest.mark.parametrize("form_key", MEETING_FORM_KEYS)
def test_meeting_tips_concise(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        if not t["form_key"].startswith("meeting"):
            continue
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, (
            f"{t['form_key']}/{t['kind']} EN too long ({wc_en} words)"
        )
        assert wc_es <= 90, (
            f"{t['form_key']}/{t['kind']} ES too long ({wc_es} words)"
        )


@pytest.mark.parametrize("form_key", MEETING_FORM_KEYS)
def test_meeting_tips_kinds_valid(form_key):
    """Every tip kind must be in the canonical allow-list."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        assert t["kind"] in ALLOWED_KINDS, (
            f"{t['form_key']}/{t['kind']}: invalid kind"
        )


# ─── LMS / corporate / motivational drift guardrail ────────────────────
# The operator explicitly named the tones we DO NOT want. If any of these
# phrases appears in a meeting-family tip body (EN or ES), the test fails.
BANNED_TONE_PHRASES = [
    "training module",
    "course completion",
    "learning objective",
    "engage in active learning",
    "best practices",
    "stakeholders",
    "synergy",
    "leverage",
    "empower",
    "módulo de capacitación",
    "objetivos de aprendizaje",
    "mejores prácticas",
]


@pytest.mark.parametrize("form_key", MEETING_FORM_KEYS)
def test_meeting_tips_tone_not_lms(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        if not t["form_key"].startswith("meeting"):
            continue
        text = " ".join([
            (t.get("body") or "").lower(),
            (t.get("body_es") or "").lower(),
        ])
        for phrase in BANNED_TONE_PHRASES:
            assert phrase.lower() not in text, (
                f"{t['form_key']}/{t['kind']} drifts into LMS tone: "
                f"'{phrase}' appears in body"
            )


def test_meeting_tips_cover_operator_priority_surfaces():
    """Operator's named themes from the iter270 directive:
        • don't pencil-whip meetings
        • tie discussion to TODAY'S work
        • use incident patterns as conversation starters
        • make crews participate
        • escalation discipline
        • photos prove meeting happened where work happened
        • foreman operational guidance (when, mistakes)
    Each themed kind must exist somewhere in the meeting family."""
    expected = {
        "meeting":             {"why", "escalate"},     # pencil-whip / escalation
        "meeting.context":     {"mistake", "when"},     # timing + flag discipline
        "meeting.topic":       {"why", "mistake", "example", "escalate"},  # the heart
        "meeting.attendees":   {"why", "escalate"},     # roster + refusal handling
        "meeting.photos":      {"why", "example"},      # frame that proves it
        "meeting.signoff":     {"why", "next"},         # last-act discipline + follow-up
    }
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    by_key: dict[str, set[str]] = {}
    for t in all_tips():
        by_key.setdefault(t["form_key"], set()).add(t["kind"])
    for fk, kinds in expected.items():
        for k in kinds:
            assert k in by_key.get(fk, set()), (
                f"missing operator-priority coaching surface: {fk}/{k}"
            )


def test_meeting_family_uses_public_scope_only():
    """Field forms are public-readable. The meeting family must follow
    that contract (matches incident, daily-report, preop)."""
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    for t in all_tips():
        if not (t["form_key"] == "meeting"
                or t["form_key"].startswith("meeting.")):
            continue
        scopes = set(t.get("scopes") or [])
        assert "public" in scopes, (
            f"{t['form_key']}/{t['kind']} must be public-scoped "
            f"(got {scopes})"
        )


def test_meeting_registry_validator_passes_after_seed():
    """The existing validate_tips_registry() guard must remain clean
    after the iter270 append — no missing fields, invalid kinds,
    or word-count overruns introduced."""
    import guidance  # noqa: F401
    from guidance.tips import validate_tips_registry
    issues = validate_tips_registry(strict=False)
    meeting_issues = [i for i in issues if "meeting" in i]
    assert not meeting_issues, (
        f"validate_tips_registry surfaced meeting-family issues: "
        f"{meeting_issues}"
    )
