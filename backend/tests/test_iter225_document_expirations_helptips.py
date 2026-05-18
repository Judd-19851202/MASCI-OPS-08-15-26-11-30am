"""iter225 — document-expirations coaching family · Tier-2 hr+safety+admin.

Document-expiration handling is one of the clearest operational
indicators of whether a company feels HUMAN or BUREAUCRATIC. Every
row is somebody's CDL, medical card, OSHA-10, or first-aid cert —
the things they need to keep working. How the company chases them
down is how the company tells them whether they matter.

OPERATOR-STATED LOAD-BEARING ANCHOR (test-enforced verbatim):
  "Phone call beats email blast."

Operational principles (operator-stated):
  • direct leadership engagement over passive bureaucracy
  • accountability through proactive communication
  • operational respect (the operator's CDL is their livelihood)
  • triage with judgment — not everything 30-day-out is urgent
  • when the same person keeps expiring, fix the SYSTEM not the
    SYMPTOM
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

DE_KEYS = [
    "document-expirations",
    "document-expirations.outreach",
    "document-expirations.cdl",
    "document-expirations.triage",
    "document-expirations.cadence",
]


def _de_tips() -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == "document-expirations"
        or t["form_key"].startswith("document-expirations.")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_seed_count():
    assert len(_de_tips()) >= 12, (
        "Expected ≥12 document-expirations tips (4 canonical + 3 "
        "outreach + 2 cdl + 2 triage + 1 cadence)"
    )


def test_canonical_four_kinds_present():
    rows = [t for t in _de_tips() if t["form_key"] == "document-expirations"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"missing canonical kind {required!r}"


@pytest.mark.parametrize("form_key", DE_KEYS)
def test_each_form_key_has_at_least_one_tip(form_key):
    rows = [t for t in _de_tips() if t["form_key"] == form_key]
    assert rows, f"{form_key} has no tips"


# ─────────────────────────────────────────────────────────────────────
# RBAC — Tier-2 hr/safety/admin (no public, no shop, no dispatch)
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_scoped_to_hr_safety_admin():
    for t in _de_tips():
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} has 'public' scope — "
            f"document-expirations is Tier-2 authenticated only"
        )
        assert scopes <= {"hr", "safety", "admin"}, (
            f"{t['form_key']}/{t['kind']} has out-of-scope scopes "
            f"{scopes} — allowed: hr / safety / admin only"
        )
        assert scopes & {"hr", "safety", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing all of "
            f"hr/safety/admin: {scopes}"
        )


def test_anon_caller_sees_no_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=document-expirations",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json().get("count", 0) == 0


# ─────────────────────────────────────────────────────────────────────
# Bilingual + concise
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_bilingual():
    for t in _de_tips():
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_all_tips_concise():
    for t in _de_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# OPERATOR-STATED CULTURAL ANCHOR (load-bearing · verbatim · enforced)
# ─────────────────────────────────────────────────────────────────────
def test_anchor_phone_call_beats_email_blast_verbatim():
    """Operator-stated load-bearing anchor:
       'Phone call beats email blast.'

    This is THE cultural firewall for the entire family. The .outreach
    leaf surface exists specifically to land this anchor — if a future
    agent dilutes or removes it, this test catches it.
    """
    rows = [
        t for t in _de_tips()
        if t["form_key"] == "document-expirations.outreach"
    ]
    full = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "phone call beats email blast" in full, (
        "outreach family MUST contain the operator-stated anchor "
        "'phone call beats email blast' verbatim (title OR body)"
    )


def test_top_level_why_anchors_people_not_paperwork():
    """The top-level 'why' must frame the list as PEOPLE, not as
    rows on a compliance tracker. Operator-stated framing: every row
    is somebody's CDL / medical card / cert."""
    why = next(
        (t for t in _de_tips()
         if t["form_key"] == "document-expirations" and t["kind"] == "why"),
        None,
    )
    assert why
    body = (why.get("body") or "").lower()
    assert "people" in body or "person" in body or "somebody" in body or "people, not" in body, (
        "top-level 'why' MUST frame the list as people, not paperwork"
    )
    # And must explicitly contrast the phone-call vs email-blast framing
    assert "phone call" in body or "bulk email" in body or "name" in body, (
        "top-level 'why' MUST connect the operational choice "
        "(phone call vs email blast / 'we know your name')"
    )


def test_top_level_who_names_downstream_consequences():
    """The 'who' tip must teach that a lapsed cert cascades:
       supervisor redeploys · dispatch loses a truck · safety blocks
       the site · owners hear about it. Operator-stated framing."""
    who = next(
        (t for t in _de_tips()
         if t["form_key"] == "document-expirations" and t["kind"] == "who"),
        None,
    )
    assert who
    body = (who.get("body") or "").lower()
    # Must name at least 3 of the downstream roles
    roles = ["supervisor", "dispatch", "safety", "employee", "owner"]
    hits = [r for r in roles if r in body]
    assert len(hits) >= 3, (
        f"who tip must name ≥3 downstream-consequence roles — found: {hits}"
    )


def test_escalate_addresses_system_not_symptom():
    """Operator-stated: 'when the same person keeps expiring, fix the
    SYSTEM, not the SYMPTOM.' The escalate tip must teach this
    pattern-recognition discipline — not just 'call HR.'"""
    esc = next(
        (t for t in _de_tips()
         if t["form_key"] == "document-expirations" and t["kind"] == "escalate"),
        None,
    )
    assert esc
    body = (esc.get("body") or "").lower()
    assert "system" in body, (
        "escalate tip MUST coach the 'system problem, not reminder "
        "problem' pattern (operator-stated cultural framing)"
    )


def test_outreach_mistake_names_email_only_anti_pattern():
    """The .outreach leaf must explicitly name the 'sent the email,
    called it outreach' anti-pattern — that's the bureaucratic-drift
    trap the entire anchor is fighting."""
    rows = [
        t for t in _de_tips()
        if t["form_key"] == "document-expirations.outreach"
        and t["kind"] == "mistake"
    ]
    assert rows
    body = (rows[0].get("body") or "").lower()
    assert "email" in body, (
        ".outreach mistake tip MUST name the email-only anti-pattern"
    )
    assert "auto" in body or "same" in body or "bulk" in body, (
        ".outreach mistake tip MUST name the auto-generated / "
        "repeat-send anti-pattern (not just 'send better emails')"
    )


def test_outreach_example_demonstrates_concrete_call_script():
    """The .outreach 'example' tip must demonstrate an actual phone
    call with concrete operational details (named person, specific
    date, specific calendar block, specific follow-up). Abstract
    advice defeats this leaf's purpose."""
    ex = next(
        (t for t in _de_tips()
         if t["form_key"] == "document-expirations.outreach"
         and t["kind"] == "example"),
        None,
    )
    assert ex
    body = (ex.get("body") or "")
    # Must contain a quoted phrase (real script dialogue)
    assert "'" in body or "\u2018" in body or "\u201c" in body, (
        ".outreach example must contain a quoted script (real dialogue), "
        "not abstract 'have a conversation' advice"
    )
    # Must name a specific date pattern (month name, day number, etc.)
    import re
    has_date_pattern = bool(re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
        r"\d{1,2}(st|nd|rd|th)?)\b",
        body, re.IGNORECASE,
    ))
    assert has_date_pattern, (
        ".outreach example must reference a concrete date "
        "(specific month or day number) — abstract examples defeat "
        "the leaf's purpose"
    )


def test_cdl_family_teaches_separate_medical_card_expiration():
    """Operational realism: the DOT medical card is a SEPARATE
    expiration from the CDL itself. Missing this is a classic
    rookie HR mistake. The .cdl leaf must teach it."""
    rows = [t for t in _de_tips() if t["form_key"] == "document-expirations.cdl"]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "medical card" in haystack, (
        ".cdl family must teach that the DOT medical card is a "
        "separate expiration from the CDL itself"
    )


def test_triage_family_teaches_impact_over_date():
    """The .triage leaf must coach reading the list by OPERATIONAL
    IMPACT (what stops work first), not just by date. Operator-stated
    discipline: a first-aid cert in 90 days ≠ a medical card in 8."""
    rows = [t for t in _de_tips() if t["form_key"] == "document-expirations.triage"]
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows
    ).lower()
    assert "judgment" in haystack or "stops work" in haystack or "impact" in haystack, (
        ".triage family must coach judgment / impact-based "
        "prioritization, not just date-sorting"
    )


def test_cadence_family_teaches_weekly_rhythm():
    """The .cadence leaf must teach that a fixed weekly slot prevents
    the twice-a-year fire drill. Operator-stated rhythm discipline."""
    rows = [t for t in _de_tips() if t["form_key"] == "document-expirations.cadence"]
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "weekly" in haystack or "week" in haystack, (
        ".cadence family must coach a weekly rhythm"
    )
    assert "rhythm" in haystack or "same time" in haystack or "fixed" in haystack, (
        ".cadence family must teach the recurring/fixed-slot discipline"
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
    for t in _de_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        assert phrase.lower() not in full.lower(), (
            f"{t['form_key']}/{t['kind']} contains legal-drift phrase "
            f"{phrase!r} — document-expirations is operational "
            f"leadership coaching, not legal advice"
        )


# ─────────────────────────────────────────────────────────────────────
# Standard tone discipline (inherited from iter211→224)
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
]
CORPORATE_HR_PHRASES = [
    "human capital", "team member engagement", "stakeholder alignment",
    "performance management framework", "leverage synergies", "best-in-class",
    "compliance posture", "compliance ecosystem",
    "automated workflow optimization",
]
HR_LEGAL_DRIFT_PHRASES = [
    "progressive discipline policy",
    "disciplinary action up to and including",
    "at-will employment",
    "performance improvement plan procedure",
]
# iter224 motivational-fluff banlist — inherited and extended for this
# surface (no "we're committed to compliance" branding tone).
MOTIVATIONAL_FLUFF_PHRASES = [
    "welcome aboard", "we are excited to have you",
    "embark on this journey", "exciting opportunity ahead",
    "passionate about", "world-class",
    "committed to compliance", "compliance journey",
    "compliance excellence",
]


def test_no_robotic_osha_tone():
    for t in _de_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} OSHA tone: {bad}"


def test_no_corporate_hr_tone():
    for t in _de_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_HR_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} corporate-HR: {bad}"


def test_no_hr_legal_drift_tone():
    for t in _de_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in HR_LEGAL_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} HR-legal drift: {bad}"


def test_no_motivational_fluff_tone():
    """Operator-stated hard-stop (iter224): no corporate-culture
    fluff, no motivational language, no HR-branding tone. Inherited
    here and extended with compliance-branding phrases ('committed
    to compliance' / 'compliance journey') — these are the same
    drift just dressed up for a different page."""
    for t in _de_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in MOTIVATIONAL_FLUFF_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} motivational fluff: {bad} — "
            f"compliance-branding tone is still HR-branding tone"
        )


# ─────────────────────────────────────────────────────────────────────
# Humanity anchors (each leaf must contain at least one)
# ─────────────────────────────────────────────────────────────────────
def test_each_leaf_contains_humanity_anchor():
    HUMANITY = [
        "employee", "person", "people", "crew", "trust", "human",
        "humanity", "fair", "fairness", "driver", "they", "their",
        "name", "livelihood", "operator",
    ]
    for prefix in (
        "document-expirations.outreach",
        "document-expirations.cdl",
        "document-expirations.triage",
        "document-expirations.cadence",
    ):
        rows = [t for t in _de_tips() if t["form_key"] == prefix]
        haystack = " ".join((t.get("body") or "").lower() for t in rows)
        hits = [a for a in HUMANITY if a in haystack]
        assert hits, (
            f"{prefix} contains no humanity anchor — drift risk. "
            f"Approved anchors: {HUMANITY}"
        )


# ─────────────────────────────────────────────────────────────────────
# Subtle reinforcement (operator-stated):
#   direct leadership engagement · accountability · operational
#   respect · proactive communication
# ─────────────────────────────────────────────────────────────────────
def test_family_reinforces_proactive_engagement():
    """The family as a whole must subtly reinforce direct leadership
    engagement / proactive communication / accountability — NOT
    bureaucratic compliance. Signals must arrive through OPERATIONAL
    behaviors (call, talk, calendar, follow up), not slogans."""
    haystack = " ".join(((t.get("body") or "")) for t in _de_tips()).lower()
    proactive_signals = [
        "call", "phone", "talk", "calendar", "follow up", "follow-up",
        "confirm", "appointment", "block", "schedule", "rhythm",
    ]
    hits = [s for s in proactive_signals if s in haystack]
    assert len(hits) >= 5, (
        f"family must subtly reinforce direct leadership engagement / "
        f"proactive communication — found only: {hits}"
    )


# ─────────────────────────────────────────────────────────────────────
# Static UI wiring check
# ─────────────────────────────────────────────────────────────────────
def test_document_expirations_page_wires_helptip_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/DocumentExpirations.jsx").read_text()
    assert "HelpTipBlock" in src, "DocumentExpirations.jsx must import HelpTipBlock"
    assert 'formKey="document-expirations"' in src, (
        "DocumentExpirations.jsx must render "
        '<HelpTipBlock formKey="document-expirations" />'
    )
