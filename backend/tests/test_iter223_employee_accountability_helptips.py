"""iter223 — employee-accountability coaching family · Tier-2 HR-scoped.

"My check is short." "Where's my last paystub?" Highest-trust-impact
operational moment in HR's day. How HR responds determines:
  - credibility · escalation likelihood · morale · retention
  - the crew's perception of fairness

OPERATOR-STATED LOAD-BEARING ANCHOR (test-enforced verbatim):
  "The answer lives in the record — read first, respond second."

Operational principles (operator-stated):
  • read first · verify first · understand context first
  • respond human-first
  • avoid defensiveness · avoid bureaucracy · avoid escalation reflexes
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

EA_KEYS = [
    "employee-accountability",
    "employee-accountability.read-first",
    "employee-accountability.tone",
    "employee-accountability.verify",
    "employee-accountability.followup",
]


def _ea_tips() -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == "employee-accountability"
        or t["form_key"].startswith("employee-accountability.")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_seed_count():
    assert len(_ea_tips()) >= 12, (
        "Expected ≥12 employee-accountability tips (4 canonical + 3 read-first "
        "+ 2 tone + 2 verify + 1 followup)"
    )


def test_canonical_four_kinds_present():
    rows = [t for t in _ea_tips() if t["form_key"] == "employee-accountability"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"missing canonical kind {required!r}"


@pytest.mark.parametrize("form_key", EA_KEYS)
def test_each_form_key_has_at_least_one_tip(form_key):
    rows = [t for t in _ea_tips() if t["form_key"] == form_key]
    assert rows, f"{form_key} has no tips"


# ─────────────────────────────────────────────────────────────────────
# RBAC — strictly Tier-2 HR
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_hr_scoped_only():
    for t in _ea_tips():
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} has 'public' scope — "
            f"employee-accountability is HR-only Tier-2"
        )
        assert scopes & {"hr", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing hr/admin scope: {scopes}"
        )


def test_anon_caller_sees_no_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=employee-accountability",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json().get("count", 0) == 0


# ─────────────────────────────────────────────────────────────────────
# Bilingual + concise
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_bilingual():
    for t in _ea_tips():
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_all_tips_concise():
    for t in _ea_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# OPERATOR-STATED CULTURAL ANCHOR (load-bearing · verbatim · test-enforced)
# ─────────────────────────────────────────────────────────────────────
def test_anchor_read_first_respond_second():
    """Operator-stated anchor:
       'The answer lives in the record — read first, respond second.'

    This is the load-bearing cultural invariant for the entire family.
    If a future agent dilutes or removes the operator-stated voice,
    this test catches it."""
    rows = [
        t for t in _ea_tips()
        if t["form_key"] == "employee-accountability.read-first"
    ]
    full = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    # The exact anchor phrase must land verbatim somewhere in this family.
    assert "read first, respond second" in full, (
        "read-first family MUST contain the operator-stated anchor "
        "'read first, respond second' verbatim"
    )
    assert "the answer lives in the record" in full, (
        "read-first family MUST contain the operator-stated phrase "
        "'the answer lives in the record' verbatim"
    )


def test_top_level_why_anchors_trust():
    """The top-level 'why' must anchor on TRUST as the operational
    framing — not on accuracy, not on policy, not on speed. Trust is
    the operator-stated cultural firewall here."""
    why = next(
        (t for t in _ea_tips()
         if t["form_key"] == "employee-accountability" and t["kind"] == "why"),
        None,
    )
    assert why
    body = (why.get("body") or "").lower()
    assert "trust" in body, (
        "top-level 'why' MUST anchor on the word 'trust' "
        "(operator-stated cultural framing for the highest-trust-impact moment)"
    )


def test_top_level_who_anchors_fairness_travels():
    """The 'who' tip must teach that fairness stories travel — the
    response is heard by far more than just the employee at the
    counter. Operator-stated framing: the crew sees how HR handles
    these moments and judges the company by them."""
    who = next(
        (t for t in _ea_tips()
         if t["form_key"] == "employee-accountability" and t["kind"] == "who"),
        None,
    )
    assert who
    body = (who.get("body") or "").lower()
    assert "crew" in body, "who tip must reference the crew (the witness)"
    assert "fairness" in body or "travel" in body or "hear about it" in body, (
        "who tip must teach that the response is heard beyond the immediate "
        "conversation (operator-stated 'fairness stories travel' framing)"
    )


# ─────────────────────────────────────────────────────────────────────
# Operator-stated anti-pattern firewalls
# ─────────────────────────────────────────────────────────────────────
def test_escalate_addresses_defensive_reflex():
    """Operator-stated: 'avoid defensiveness · avoid escalation reflexes.'
    The escalate tip must explicitly name the self-awareness moment
    where HR notices its own defensiveness rising and chooses to pause."""
    esc = next(
        (t for t in _ea_tips()
         if t["form_key"] == "employee-accountability" and t["kind"] == "escalate"),
        None,
    )
    assert esc
    body = (esc.get("body") or "").lower()
    assert "defensive" in body, (
        "escalate tip MUST address the 'getting defensive' self-awareness "
        "moment (operator-stated anti-pattern)"
    )


def test_tone_family_explicitly_addresses_defensiveness():
    """The .tone leaf surface exists specifically to coach against
    defensiveness. It must explicitly name the anti-pattern, not just
    teach 'be calm.'"""
    rows = [t for t in _ea_tips() if t["form_key"] == "employee-accountability.tone"]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "defensive" in haystack, (
        ".tone leaf must explicitly name the defensiveness anti-pattern"
    )
    assert "calm" in haystack, (
        ".tone leaf must offer the operator-stated 'calm response wins' framing"
    )


def test_verify_teaches_open_not_closed_questions():
    """Operator-stated principle: 'investigate WITH them, not THEM.'
    The verify family must explicitly teach the open-question
    discipline that makes verification feel collaborative rather
    than interrogatory."""
    rows = [t for t in _ea_tips() if t["form_key"] == "employee-accountability.verify"]
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "open" in haystack, (
        "verify family must coach 'open questions' discipline "
        "(walk-me-through style)"
    )
    assert "with them" in haystack or "investigate with" in haystack or "with them, not" in haystack, (
        "verify family must coach 'investigate WITH them, not THEM' "
        "(operator-stated framing)"
    )


def test_followup_anchors_closing_the_loop():
    """Operator-stated: closing the loop matters more than the
    resolution. The followup family must explicitly teach this."""
    rows = [t for t in _ea_tips() if t["form_key"] == "employee-accountability.followup"]
    assert rows
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "loop" in haystack or "follow" in haystack or "confirmation" in haystack, (
        "followup family must coach the close-the-loop discipline"
    )


def test_read_first_example_demonstrates_concrete_workflow():
    """The .read-first 'example' tip must demonstrate the actual
    operational workflow with concrete details (specific dollar
    amount, specific hours, specific resolution timing) — abstract
    advice is the anti-pattern this leaf is fighting."""
    ex = next(
        (t for t in _ea_tips()
         if t["form_key"] == "employee-accountability.read-first"
         and t["kind"] == "example"),
        None,
    )
    assert ex
    body = ex.get("body") or ""
    import re
    has_dollar = bool(re.search(r"\$\d+", body))
    has_hours = bool(re.search(r"\d+(\.\d+)?\s*(hrs|hours|hour)", body, re.IGNORECASE))
    assert has_dollar or has_hours, (
        "read-first example must demonstrate concrete numbers (dollar "
        "amount or specific hours) — abstract examples defeat the leaf's purpose"
    )


# ─────────────────────────────────────────────────────────────────────
# Anti-legal-drift firewall (inherited from iter222)
# ─────────────────────────────────────────────────────────────────────
LEGAL_DRIFT_PHRASES = [
    "FMLA", "ADA-protected", "ADAAA", "Title VII", "EEOC",
    "Equal Employment Opportunity", "Family and Medical Leave Act",
    "Americans with Disabilities Act",
    "per company policy section", "see employee handbook section",
    "in accordance with section", "pursuant to policy",
    "you should consult", "it is illegal to", "violation of",
    "qualifying event", "designated representative",
]


@pytest.mark.parametrize("phrase", LEGAL_DRIFT_PHRASES)
def test_no_legal_drift(phrase):
    for t in _ea_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        assert phrase.lower() not in full.lower(), (
            f"{t['form_key']}/{t['kind']} contains legal-drift phrase "
            f"{phrase!r} — this surface is operational leadership, "
            f"not legal advice"
        )


# ─────────────────────────────────────────────────────────────────────
# Standard tone discipline (inherited from iter211→218 banlists)
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
]
CORPORATE_HR_PHRASES = [
    "human capital", "team member engagement", "stakeholder alignment",
    "performance management framework", "leverage synergies", "best-in-class",
]
HR_LEGAL_DRIFT_PHRASES = [
    "progressive discipline policy",
    "disciplinary action up to and including",
    "at-will employment",
    "performance improvement plan procedure",
]


def test_no_robotic_osha_tone():
    for t in _ea_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} OSHA tone: {bad}"


def test_no_corporate_hr_tone():
    for t in _ea_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_HR_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} corporate-HR: {bad}"


def test_no_hr_legal_drift_tone():
    for t in _ea_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in HR_LEGAL_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} HR-legal drift: {bad}"


# ─────────────────────────────────────────────────────────────────────
# Humanity anchors (each leaf must contain at least one)
# ─────────────────────────────────────────────────────────────────────
def test_each_leaf_contains_humanity_anchor():
    HUMANITY = [
        "employee", "person", "crew", "trust", "human",
        "humanly", "humanity", "fair", "fairness",
    ]
    for prefix in (
        "employee-accountability.read-first",
        "employee-accountability.tone",
        "employee-accountability.verify",
        "employee-accountability.followup",
    ):
        rows = [t for t in _ea_tips() if t["form_key"] == prefix]
        haystack = " ".join((t.get("body") or "").lower() for t in rows)
        hits = [a for a in HUMANITY if a in haystack]
        assert hits, (
            f"{prefix} contains no humanity anchor — drift risk. "
            f"Approved anchors: {HUMANITY}"
        )


# ─────────────────────────────────────────────────────────────────────
# Static UI wiring check
# ─────────────────────────────────────────────────────────────────────
def test_hr_accountability_page_wires_helptip_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/HrEmployeeAccountability.jsx").read_text()
    assert "HelpTipBlock" in src, "HrEmployeeAccountability.jsx must import HelpTipBlock"
    assert 'formKey="employee-accountability"' in src, (
        "HrEmployeeAccountability.jsx must render "
        "<HelpTipBlock formKey=\"employee-accountability\" />"
    )
