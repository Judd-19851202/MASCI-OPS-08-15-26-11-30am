"""iter224 — employee-lifecycle coaching family · Tier-2 HR-scoped.

New-hire onboarding is the highest long-term culture-shaping
operational surface in the company. The first day decides:
  - retention · morale · trust · operational confidence
  - perception of leadership · perception of professionalism

OPERATOR-STATED LOAD-BEARING ANCHOR (test-enforced verbatim):
  "Get it right and they hear about the company; get it wrong and
   they hear about the bureaucracy."

Operational principles (operator-stated):
  • first-impression matters more than paperwork accuracy
  • human-first welcome, not forms-first welcome
  • collect documents WITHOUT making it feel like an interrogation
  • the hand-off to the supervisor is the actual onboarding moment

Subtle reinforcement (operator-stated · test-asserted):
  belonging · preparedness · professionalism · operational readiness
  · respect for crew reliance · showing up prepared.
  AVOID: corporate-culture fluff · motivational language · HR-branding
  tone · LMS drift.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

EL_KEYS = [
    "employee-lifecycle",
    "employee-lifecycle.first-impression",
    "employee-lifecycle.welcome",
    "employee-lifecycle.documents",
    "employee-lifecycle.day-one",
]


def _el_tips() -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == "employee-lifecycle"
        or t["form_key"].startswith("employee-lifecycle.")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_seed_count():
    assert len(_el_tips()) >= 12, (
        "Expected ≥12 employee-lifecycle tips (4 canonical + 3 "
        "first-impression + 2 welcome + 2 documents + 1 day-one)"
    )


def test_canonical_four_kinds_present():
    rows = [t for t in _el_tips() if t["form_key"] == "employee-lifecycle"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"missing canonical kind {required!r}"


@pytest.mark.parametrize("form_key", EL_KEYS)
def test_each_form_key_has_at_least_one_tip(form_key):
    rows = [t for t in _el_tips() if t["form_key"] == form_key]
    assert rows, f"{form_key} has no tips"


# ─────────────────────────────────────────────────────────────────────
# RBAC — strictly Tier-2 HR
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_hr_scoped_only():
    for t in _el_tips():
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} has 'public' scope — "
            f"employee-lifecycle is HR-only Tier-2"
        )
        assert scopes & {"hr", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing hr/admin scope: {scopes}"
        )


def test_anon_caller_sees_no_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=employee-lifecycle",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json().get("count", 0) == 0


# ─────────────────────────────────────────────────────────────────────
# Bilingual + concise
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_bilingual():
    for t in _el_tips():
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_all_tips_concise():
    for t in _el_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# OPERATOR-STATED CULTURAL ANCHOR (load-bearing · verbatim · enforced)
# ─────────────────────────────────────────────────────────────────────
def test_anchor_company_vs_bureaucracy_verbatim():
    """Operator-stated load-bearing anchor:
       'Get it right and they hear about the company; get it wrong
        and they hear about the bureaucracy.'

    This is THE cultural firewall for the entire family. If a future
    agent dilutes or removes the operator-stated voice, this test
    catches it.
    """
    rows = [
        t for t in _el_tips()
        if t["form_key"] == "employee-lifecycle.first-impression"
    ]
    full = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    # The two halves of the anchor must both land somewhere in the
    # first-impression family — verbatim.
    assert "hear about the company" in full, (
        "first-impression family MUST contain the operator-stated "
        "anchor phrase 'hear about the company' verbatim"
    )
    assert "hear about the bureaucracy" in full, (
        "first-impression family MUST contain the operator-stated "
        "anchor phrase 'hear about the bureaucracy' verbatim"
    )


def test_top_level_why_anchors_first_message():
    """The top-level 'why' must teach that onboarding is the first
    MESSAGE the company sends about how it treats people — not a
    checklist, not a compliance exercise."""
    why = next(
        (t for t in _el_tips()
         if t["form_key"] == "employee-lifecycle" and t["kind"] == "why"),
        None,
    )
    assert why
    body = (why.get("body") or "").lower()
    assert "first message" in body or "first day" in body, (
        "top-level 'why' MUST frame onboarding as the first message / "
        "first day the company sends, not as paperwork"
    )
    assert "checklist" in body or "paperwork" in body or "forms" in body, (
        "top-level 'why' MUST explicitly contrast against the "
        "checklist/paperwork framing"
    )


def test_top_level_who_names_supervisor_and_crew():
    """Operator-stated framing: onboarding is not just HR's transaction.
    The supervisor and the crew the new hire is joining are load-bearing
    participants. The 'who' tip must name both — anyone who reads this
    tip should walk away knowing the supervisor needs a heads-up before
    Day 1 and the crew needs a heads-up too."""
    who = next(
        (t for t in _el_tips()
         if t["form_key"] == "employee-lifecycle" and t["kind"] == "who"),
        None,
    )
    assert who
    body = (who.get("body") or "").lower()
    assert "supervisor" in body, (
        "who tip must name the SUPERVISOR — the hand-off recipient"
    )
    assert "crew" in body, (
        "who tip must name the CREW — onboarding affects the team "
        "the new hire is joining"
    )


def test_escalate_addresses_uncomfortable_submit_moment():
    """Operator-stated: 'Anything where you find yourself
    uncomfortable but the form is asking you to click Submit anyway.'

    The escalate tip must teach the self-awareness moment where HR
    notices the form is overriding their judgment and they need to
    pause."""
    esc = next(
        (t for t in _el_tips()
         if t["form_key"] == "employee-lifecycle" and t["kind"] == "escalate"),
        None,
    )
    assert esc
    body = (esc.get("body") or "").lower()
    assert "uncomfortable" in body or "submit" in body, (
        "escalate tip MUST address the moment when the form asks for "
        "Submit but the HR coordinator feels uncomfortable — that's "
        "the call-up trigger"
    )


def test_documents_family_teaches_non_interrogation_tone():
    """The .documents leaf exists specifically to coach away from
    treating I-9 collection like a border-screening exercise.
    Operator-stated framing: helping them JOIN the company, not
    SCREENING them."""
    rows = [
        t for t in _el_tips()
        if t["form_key"] == "employee-lifecycle.documents"
    ]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "interrogation" in haystack or "border" in haystack or "screening" in haystack, (
        ".documents leaf must explicitly contrast against the "
        "interrogation/border-screening anti-pattern"
    )


def test_welcome_family_teaches_forms_after_handshake():
    """The .welcome leaf must coach the sequence: human introduction
    FIRST, paperwork SECOND. Operator-stated framing: the paperwork
    takes the same five minutes whether it happens at minute one or
    minute ten — minute ten lands better."""
    rows = [
        t for t in _el_tips()
        if t["form_key"] == "employee-lifecycle.welcome"
    ]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "before" in haystack or "after" in haystack or "first" in haystack, (
        ".welcome leaf must teach a sequence (handshake/welcome before "
        "paperwork) — not just 'be friendly'"
    )


def test_day_one_handoff_teaches_phone_not_just_text():
    """The .day-one leaf must teach that the supervisor hand-off is
    confirmed by phone (or in person) — not just by a fire-and-forget
    text/email. Operator-stated discipline."""
    rows = [
        t for t in _el_tips()
        if t["form_key"] == "employee-lifecycle.day-one"
    ]
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "phone" in haystack or "call" in haystack or "in person" in haystack, (
        ".day-one leaf must coach a real hand-off confirmation "
        "(phone / call / in person), not just a text"
    )


def test_first_impression_example_demonstrates_concrete_workflow():
    """The .first-impression 'example' tip must demonstrate the actual
    Day-1 sequence with concrete operational details — abstract advice
    is the anti-pattern this leaf is fighting."""
    ex = next(
        (t for t in _el_tips()
         if t["form_key"] == "employee-lifecycle.first-impression"
         and t["kind"] == "example"),
        None,
    )
    assert ex
    body = (ex.get("body") or "").lower()
    # A real example mentions specific operational details — name,
    # parking, supervisor, etc. — not generic "make them feel welcome."
    operational_signals = [
        "name", "parking", "park", "supervisor", "coffee", "water",
        "entrance", "door",
    ]
    hits = [s for s in operational_signals if s in body]
    assert len(hits) >= 3, (
        f"first-impression example must demonstrate ≥3 concrete "
        f"operational signals (name, parking, supervisor, coffee, "
        f"entrance, etc.) — found only: {hits}"
    )


# ─────────────────────────────────────────────────────────────────────
# Subtle reinforcement anchors (operator-stated)
#   belonging · preparedness · professionalism · operational readiness
#   · respect for crew reliance · showing up prepared
# ─────────────────────────────────────────────────────────────────────
def test_family_subtly_reinforces_belonging_or_professionalism():
    """The family as a whole should land subtle reinforcement of:
       belonging · preparedness · professionalism · operational
       readiness · respect for crew reliance · showing up prepared.

    Anti-pattern: corporate-culture fluff, motivational language, or
    HR-branding tone. The signals must arrive through OPERATIONAL
    behaviors (organized, prepared, on-time, named, expected), not
    through slogans.
    """
    haystack = " ".join(
        ((t.get("body") or "")) for t in _el_tips()
    ).lower()
    operational_signals = [
        "organized", "welcoming", "serious", "prepared", "expected",
        "professional", "ready", "joining", "join", "supervisor",
        "crew",
    ]
    hits = [s for s in operational_signals if s in haystack]
    assert len(hits) >= 5, (
        f"family must subtly reinforce operational professionalism / "
        f"belonging through concrete behavior signals — found only: "
        f"{hits}"
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
    for t in _el_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        assert phrase.lower() not in full.lower(), (
            f"{t['form_key']}/{t['kind']} contains legal-drift phrase "
            f"{phrase!r} — onboarding coaching is operational "
            f"leadership, not legal advice"
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
    "onboarding journey", "employee experience platform",
    "employee value proposition", "talent acquisition pipeline",
]
HR_LEGAL_DRIFT_PHRASES = [
    "progressive discipline policy",
    "disciplinary action up to and including",
    "at-will employment",
    "performance improvement plan procedure",
]
MOTIVATIONAL_FLUFF_PHRASES = [
    "welcome aboard", "we are excited to have you",
    "you are now part of the family",
    "embark on this journey", "exciting opportunity ahead",
    "passionate about", "world-class",
]


def test_no_robotic_osha_tone():
    for t in _el_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} OSHA tone: {bad}"


def test_no_corporate_hr_tone():
    for t in _el_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_HR_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} corporate-HR: {bad}"


def test_no_hr_legal_drift_tone():
    for t in _el_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in HR_LEGAL_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} HR-legal drift: {bad}"


def test_no_motivational_fluff_tone():
    """Operator-stated hard-stop: no corporate-culture fluff, no
    motivational language, no HR-branding tone. The platform sounds
    like experienced operational leadership, NOT corporate onboarding
    software."""
    for t in _el_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in MOTIVATIONAL_FLUFF_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} motivational fluff: {bad} — "
            f"this is HR-branding tone, not operational leadership"
        )


# ─────────────────────────────────────────────────────────────────────
# Humanity anchors (each leaf must contain at least one)
# ─────────────────────────────────────────────────────────────────────
def test_each_leaf_contains_humanity_anchor():
    HUMANITY = [
        "employee", "person", "crew", "trust", "human",
        "humanly", "humanity", "fair", "fairness",
        "hire", "they", "their", "name",
    ]
    for prefix in (
        "employee-lifecycle.first-impression",
        "employee-lifecycle.welcome",
        "employee-lifecycle.documents",
        "employee-lifecycle.day-one",
    ):
        rows = [t for t in _el_tips() if t["form_key"] == prefix]
        haystack = " ".join((t.get("body") or "").lower() for t in rows)
        hits = [a for a in HUMANITY if a in haystack]
        assert hits, (
            f"{prefix} contains no humanity anchor — drift risk. "
            f"Approved anchors: {HUMANITY}"
        )


# ─────────────────────────────────────────────────────────────────────
# Static UI wiring check
# ─────────────────────────────────────────────────────────────────────
def test_hr_employees_page_wires_helptip_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/HrEmployees.jsx").read_text()
    assert "HelpTipBlock" in src, "HrEmployees.jsx must import HelpTipBlock"
    assert 'formKey="employee-lifecycle"' in src, (
        "HrEmployees.jsx must render "
        '<HelpTipBlock formKey="employee-lifecycle" />'
    )
