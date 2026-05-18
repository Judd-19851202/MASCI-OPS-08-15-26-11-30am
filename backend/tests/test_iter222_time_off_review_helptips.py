"""iter222 — time-off-review coaching family · Tier-2 HR-scoped.

Highest cultural-drift-risk surface in the platform. The operator
explicitly named:
  • bereavement is granted, never debated
  • a pattern is a conversation, not a denial
  • vacation is a yes with timing
  • medical leave: plan around it, don't dig into it

These are the load-bearing operational-leadership anchors. The tests
below assert all four anchor phrases land verbatim in their tip
bodies, plus enforce the strict anti-legal-drift discipline: this
surface coaches OPERATIONAL LEADERSHIP, not legal policy.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

TOR_KEYS = [
    "time-off-review",
    "time-off-review.bereavement",
    "time-off-review.pattern",
    "time-off-review.vacation",
    "time-off-review.medical",
]


def _tor_tips() -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == "time-off-review"
        or t["form_key"].startswith("time-off-review.")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_time_off_review_seed_count():
    assert len(_tor_tips()) >= 12, (
        "Expected ≥12 time-off-review tips (4 canonical + 3 bereavement + "
        "3 pattern + 2 vacation + 2 medical)"
    )


def test_canonical_four_kinds_present():
    rows = [t for t in _tor_tips() if t["form_key"] == "time-off-review"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"missing canonical kind {required!r}"


@pytest.mark.parametrize("form_key", TOR_KEYS)
def test_each_form_key_has_at_least_one_tip(form_key):
    rows = [t for t in _tor_tips() if t["form_key"] == form_key]
    assert rows, f"{form_key} has no tips"


# ─────────────────────────────────────────────────────────────────────
# RBAC — strictly Tier-2 HR
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_hr_scoped_only():
    for t in _tor_tips():
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} has 'public' scope — "
            f"time-off review is HR-only Tier-2"
        )
        assert scopes & {"hr", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing hr/admin scope: {scopes}"
        )


def test_anon_caller_sees_no_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=time-off-review",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json().get("count", 0) == 0


# ─────────────────────────────────────────────────────────────────────
# Bilingual + concise
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_bilingual():
    for t in _tor_tips():
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_all_tips_concise():
    for t in _tor_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# OPERATOR-STATED CULTURAL ANCHORS (load-bearing)
# These are the verbatim anchors the operator named approving iter222.
# Tests fail if a future agent dilutes or removes the cultural voice.
# ─────────────────────────────────────────────────────────────────────
def test_anchor_bereavement_granted_never_debated():
    """Operator-stated anchor: 'Bereavement is granted, never debated.'"""
    rows = [
        t for t in _tor_tips()
        if t["form_key"] == "time-off-review.bereavement"
    ]
    haystack_titles = " ".join((t.get("title") or "") for t in rows).lower()
    haystack_bodies = " ".join((t.get("body") or "") for t in rows).lower()
    # The exact anchor phrase must land in either a title or body —
    # the operator chose this wording deliberately.
    full = haystack_titles + " " + haystack_bodies
    assert "granted, never debated" in full or "granted; never debated" in full, (
        "bereavement family must contain the operator-stated anchor "
        "'granted, never debated' verbatim"
    )


def test_anchor_pattern_is_a_conversation_not_a_denial():
    """Operator-stated anchor: 'A pattern is a conversation, not a denial.'"""
    rows = [
        t for t in _tor_tips()
        if t["form_key"] == "time-off-review.pattern"
    ]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "conversation, not a denial" in haystack, (
        "pattern family must contain the operator-stated anchor "
        "'conversation, not a denial' verbatim"
    )


def test_anchor_vacation_is_yes_with_timing():
    """Operator-stated anchor: 'Vacation is a yes with timing.'"""
    rows = [
        t for t in _tor_tips()
        if t["form_key"] == "time-off-review.vacation"
    ]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "yes with timing" in haystack, (
        "vacation family must contain the operator-stated anchor "
        "'yes with timing' verbatim"
    )


def test_anchor_medical_plan_around_dont_dig_into():
    """Operator-stated anchor: medical leave coaching must teach
    'plan around it, don't dig into it' — privacy + planning. The
    exact phrasing matters because it differentiates operational
    leadership ('plan around') from intrusion ('dig into')."""
    rows = [
        t for t in _tor_tips()
        if t["form_key"] == "time-off-review.medical"
    ]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "plan around" in haystack, (
        "medical family must teach 'plan around' (operational leadership)"
    )
    assert "don't dig" in haystack or "dig into it" in haystack or "not your business" in haystack, (
        "medical family must teach the don't-dig-into-it privacy boundary"
    )


def test_top_level_why_anchors_judgment_not_policy():
    """The top-level why must explicitly anchor on JUDGMENT (operator-
    stated framing) and explicitly NOT on policy/compliance/rules.
    This is the cultural-drift firewall for this entire family."""
    why = next(
        (t for t in _tor_tips()
         if t["form_key"] == "time-off-review" and t["kind"] == "why"),
        None,
    )
    assert why
    body = (why.get("body") or "").lower()
    assert "judgment" in body, (
        "top-level 'why' must anchor on 'judgment calls' (operator-stated "
        "cultural-leadership framing)"
    )


# ─────────────────────────────────────────────────────────────────────
# ANTI-LEGAL-DRIFT (this surface is the highest-risk area in platform)
# Per iter222 operator directive: OPERATIONAL LEADERSHIP GUIDANCE,
# NOT LEGAL ADVICE. No statutes, no policy citations, no compliance-
# manual voice.
# ─────────────────────────────────────────────────────────────────────
LEGAL_DRIFT_PHRASES = [
    # Statute references — NEVER in coaching
    "FMLA", "ADA-protected", "ADAAA", "Title VII", "EEOC",
    "Equal Employment Opportunity", "Family and Medical Leave Act",
    "Americans with Disabilities Act",
    # Policy-citation patterns
    "per company policy section",
    "see employee handbook section",
    "in accordance with section",
    "pursuant to policy",
    # Legal-advice tone
    "you should consult", "it is illegal to", "violation of",
    # Compliance-manual cliches
    "qualifying event", "designated representative",
    "leave of absence policy procedure",
]


@pytest.mark.parametrize("phrase", LEGAL_DRIFT_PHRASES)
def test_no_legal_drift(phrase):
    """time-off-review is OPERATIONAL LEADERSHIP guidance, not legal
    advice. Statute references, policy citations, and legal-advice
    tone must not appear. Those belong to HR's training, not the
    contextual coaching surface."""
    for t in _tor_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        assert phrase.lower() not in full.lower(), (
            f"{t['form_key']}/{t['kind']} contains legal-drift phrase "
            f"{phrase!r} — this surface is operational leadership, not "
            f"legal advice"
        )


# ─────────────────────────────────────────────────────────────────────
# Standard tone discipline (inherited from iter211→218 banlists)
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
    "the undersigned", "willful violation",
]

CORPORATE_HR_PHRASES = [
    "human capital", "team member engagement",
    "stakeholder alignment", "performance management framework",
    "leverage synergies", "best-in-class",
]

HR_LEGAL_DRIFT_PHRASES = [
    "progressive discipline policy",
    "disciplinary action up to and including",
    "at-will employment",
    "performance improvement plan procedure",
]


def test_no_robotic_osha_tone():
    for t in _tor_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} OSHA tone: {bad}"


def test_no_corporate_hr_tone():
    for t in _tor_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_HR_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} corporate-HR: {bad}"


def test_no_hr_legal_drift_tone():
    for t in _tor_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in HR_LEGAL_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} HR-legal drift: {bad}"


# ─────────────────────────────────────────────────────────────────────
# Positive realism — humanity, accountability, leadership realism
# ─────────────────────────────────────────────────────────────────────
def test_family_contains_humanity_anchors():
    """At least one humanity anchor (employee · person · family · grief ·
    crew · trust) must surface in each leaf surface — that's how we
    enforce 'operational leadership with humanity' vs 'compliance robot'."""
    HUMANITY_ANCHORS = [
        "employee", "person", "family", "grief", "crew", "trust",
        "humanly", "humanity",
    ]
    for prefix in ("time-off-review.bereavement", "time-off-review.pattern",
                   "time-off-review.vacation", "time-off-review.medical"):
        rows = [t for t in _tor_tips() if t["form_key"] == prefix]
        haystack = " ".join((t.get("body") or "").lower() for t in rows)
        hits = [a for a in HUMANITY_ANCHORS if a in haystack]
        assert hits, (
            f"{prefix} family contains no humanity anchor — drift risk. "
            f"Approved anchors: {HUMANITY_ANCHORS}"
        )


def test_bereavement_escalate_doesnt_deny_first():
    """Cultural-leadership invariant: even when bereavement looks
    suspicious, the coaching must teach approve-then-investigate,
    never deny-to-investigate. This is the operator's explicit
    'you approve, then talk' framing."""
    esc = next(
        (t for t in _tor_tips()
         if t["form_key"] == "time-off-review.bereavement"
         and t["kind"] == "escalate"),
        None,
    )
    assert esc
    body = (esc.get("body") or "").lower()
    # Must NOT teach the deny-to-investigate anti-pattern.
    assert "deny" not in body or "don't deny" in body or "you don't deny" in body, (
        "bereavement escalate must NOT teach denying for investigation; "
        "must explicitly teach approve-then-talk"
    )
    # Must explicitly teach the approve-first sequence.
    assert "approve" in body, (
        "bereavement escalate must explicitly teach 'approve, then talk' "
        "(operator-stated cultural directive)"
    )


def test_pattern_next_separates_request_from_conversation():
    """Cultural-leadership invariant: the 'pattern' coaching must
    EXPLICITLY separate the current request approval from the
    pattern conversation. The two cannot be conflated — that's the
    entire iter222 anchor."""
    nxt = next(
        (t for t in _tor_tips()
         if t["form_key"] == "time-off-review.pattern"
         and t["kind"] == "next"),
        None,
    )
    assert nxt
    body = (nxt.get("body") or "").lower()
    assert "approve the current" in body or "approve the request" in body, (
        "pattern 'next' must teach approving the current request"
    )
    assert "separately" in body or "then," in body or "then, separately" in body, (
        "pattern 'next' must teach SEPARATELY having the conversation"
    )


# ─────────────────────────────────────────────────────────────────────
# Static UI wiring check (the Time Off page must surface the family)
# ─────────────────────────────────────────────────────────────────────
def test_hr_time_off_page_wires_helptip_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/HrTimeOff.jsx").read_text()
    assert "HelpTipBlock" in src, (
        "HrTimeOff.jsx must import HelpTipBlock"
    )
    assert 'formKey="time-off-review"' in src, (
        "HrTimeOff.jsx must render <HelpTipBlock formKey=\"time-off-review\" />"
    )
