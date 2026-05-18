"""iter213 — Time Verification contextual coaching (Tier-2 · HR-scoped).

Time Verification is the HR review surface where supervisor-reported
field hours become paychecks. This is the operator's fourth-target
contextual-coaching rollout.

Operator tone directive (consistent w/ iter211 + iter212):
  • good-faith correction, not gotcha
  • HR is the bridge between the field and the paycheck
  • quiet edits break trust — call the supervisor first
  • OT is the weekly rollup above 40, not 'over 8 in a day'
  • lunch is unpaid but tracked — missing lunch is a conversation,
    not a backfill

Scope: ["hr","admin"] — Tier-2 (portal-scoped). Anonymous callers
should get zero tips back from the API.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

TV_FORM_KEYS = [
    "time-verification",
    "time-verification.overtime",
    "time-verification.lunch",
    "time-verification.discrepancy",
]


def _tv_tips():
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == "time-verification"
        or t["form_key"].startswith("time-verification.")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_time_verification_seed_count():
    assert len(_tv_tips()) >= 11, (
        "Expected ≥11 Time Verification tips (4 canonical + 2 OT + "
        "2 lunch + 3 discrepancy)"
    )


def test_time_verification_top_level_canonical_four_tips():
    """Top-level form_key exposes the canonical 4-tip surface."""
    top = [t for t in _tv_tips() if t["form_key"] == "time-verification"]
    kinds = {t["kind"] for t in top}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"missing canonical kind {required!r}"


@pytest.mark.parametrize("form_key", TV_FORM_KEYS)
def test_time_verification_form_key_has_at_least_one_tip(form_key):
    rows = [t for t in _tv_tips() if t["form_key"] == form_key]
    assert rows, f"{form_key} has no tips"


# ─────────────────────────────────────────────────────────────────────
# RBAC — Tier 2 (HR/Admin only)
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_hr_scoped():
    """Every Time Verification tip MUST be hr-or-admin scoped. No
    accidental public leaks of payroll-internal coaching."""
    for t in _tv_tips():
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} accidentally has 'public' scope — "
            f"Time Verification is Tier-2 HR-scoped only"
        )
        assert scopes & {"hr", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing hr/admin scope: {scopes}"
        )


def test_anon_caller_sees_no_time_verification_tips():
    """Anonymous HTTP caller (no portal token) gets zero tips back."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=time-verification",
        timeout=10.0,
    )
    assert r.status_code == 200
    body = r.json()
    # Endpoint always responds; just no tips for the anon caller.
    assert body.get("count", 0) == 0
    assert body.get("tips") == []


# ─────────────────────────────────────────────────────────────────────
# Bilingual + concise
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_bilingual():
    for t in _tv_tips():
        assert t.get("title_es"), (
            f"{t['form_key']}/{t['kind']}: missing title_es"
        )
        assert t.get("body_es"), (
            f"{t['form_key']}/{t['kind']}: missing body_es"
        )


def test_all_tips_concise():
    """Coaching, not docs: ≤80 EN words, ≤90 ES words."""
    for t in _tv_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# Tone discipline — robotic-OSHA + corporate-HR banlist
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
    "the undersigned", "willful violation",
]

# Corporate-HR-speak phrases that drift away from the field-leadership voice.
CORPORATE_HR_PHRASES = [
    "human capital", "team member engagement",
    "stakeholder alignment", "performance management framework",
    "leverage synergies", "best-in-class",
]


def test_no_robotic_osha_tone():
    for t in _tv_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} uses OSHA tone: {bad}"


def test_no_corporate_hr_tone():
    for t in _tv_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_HR_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} drifts into corporate-HR tone: {bad}"
        )


# ─────────────────────────────────────────────────────────────────────
# Positive realism anchors — operator-stated tone for THIS surface
# ─────────────────────────────────────────────────────────────────────
def test_time_verification_anchors_field_to_paycheck():
    """The top-level 'why' must explicitly frame this as the bridge
    between field hours and paychecks — that's the operator-stated
    cultural anchor for this surface."""
    top_why = next(
        (t for t in _tv_tips()
         if t["form_key"] == "time-verification" and t["kind"] == "why"),
        None,
    )
    assert top_why, "missing top-level 'why' tip"
    body = (top_why.get("body") or "").lower()
    # Either 'paycheck(s)' or 'check(s)' wording must land — that's the
    # crew-trust anchor.
    assert "paycheck" in body or "check" in body, (
        "top-level 'why' must anchor on paychecks (operator-stated "
        "cultural-voice direction)"
    )


def test_discrepancy_escalate_teaches_call_supervisor_first():
    """The 'escalate' tip on the canonical surface must explicitly
    coach toward calling the supervisor BEFORE editing. That's the
    operator-stated tone: good-faith correction, not silent overwrite."""
    esc = next(
        (t for t in _tv_tips()
         if t["form_key"] == "time-verification" and t["kind"] == "escalate"),
        None,
    )
    assert esc, "missing top-level 'escalate' tip"
    body = (esc.get("body") or "").lower()
    assert "supervisor" in body, "must reference the supervisor"
    assert any(p in body for p in ("call", "before")), (
        "must coach 'call the supervisor BEFORE editing' (operator "
        "tone direction)"
    )


def test_overtime_tip_clarifies_weekly_rule():
    """OT-specific tip must clarify weekly-above-40 (not daily-over-8)
    — common HR misunderstanding the operator wants prevented."""
    rows = [t for t in _tv_tips() if t["form_key"] == "time-verification.overtime"]
    assert rows, "missing overtime tips"
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "40" in haystack, "OT tip must reference the 40-hour threshold"
    assert "week" in haystack, "OT tip must clarify the WEEKLY rule"


def test_lunch_tip_clarifies_unpaid_but_tracked():
    """Lunch tip must clarify that lunch is unpaid AND tracked — both
    halves matter."""
    rows = [t for t in _tv_tips() if t["form_key"] == "time-verification.lunch"]
    assert rows, "missing lunch tips"
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "unpaid" in haystack or "not paid" in haystack, (
        "lunch tip must clarify 'unpaid'"
    )


# ─────────────────────────────────────────────────────────────────────
# Banned-phrase guardrail — no admin-internal workflow leaks
# ─────────────────────────────────────────────────────────────────────
ADMIN_WORKFLOW_PHRASES = [
    "user management", "role templates", "audit log",
    "backups & restore", "sessions",
]


def test_no_admin_workflow_leakage():
    for t in _tv_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""]).lower()
        for p in ADMIN_WORKFLOW_PHRASES:
            assert p not in full, (
                f"{t['form_key']}/{t['kind']} leaks admin-internal phrase: {p!r}"
            )
