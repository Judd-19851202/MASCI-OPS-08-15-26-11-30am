"""iter226 — Dispatcher persona-loop closure · 3 coaching families.

The Dispatcher walkthrough scaffold was fleshed out per
walkthrough_pass.md §8 (arrival → first action → escalation
moment → end-of-day) and surfaced three operational gaps:

  1. Utilization tab read           (10:30)
  2. Cross-portal Daily Reports read (12:45)
  3. End-of-day handoff             (16:30)

This iter authors three Tier-2 dispatch+admin coaching families
to close those gaps and complete the Dispatcher persona loop.

OPERATOR-STATED LOAD-BEARING ANCHORS (test-enforced verbatim):
  dispatch.utilization:
    "Utilization is a decision tool, not a scoreboard."
  dispatch.daily-report-read:
    "The Daily Report is the dispatcher's routing intel — read
     it for movement, not for blame."
  dispatch.handoff:
    "The handoff is a conversation, not a calendar invite."
    "If tomorrow's plan changed, the foreman hears it from you
     tonight — not from the gate guard at 06:00."

Strategic hold preserved (per walkthrough_pass.md §10):
  Operator mid-day-defect surface is NOT addressed. Communication-
  discipline coaching deliberately stops at the end-of-day handoff
  and cross-portal read — mid-day-defect routing philosophy remains
  an operator-driven architectural decision.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

UTIL_KEYS = [
    "dispatch.utilization",
    "dispatch.utilization.scoreboard",
    "dispatch.utilization.redeploy",
]
DRR_KEYS = [
    "dispatch.daily-report-read",
    "dispatch.daily-report-read.routing-intel",
    "dispatch.daily-report-read.return-drift",
]
HANDOFF_KEYS = [
    "dispatch.handoff",
    "dispatch.handoff.communication",
    "dispatch.handoff.changes",
]
ALL_NEW_PREFIXES = ("dispatch.utilization", "dispatch.daily-report-read", "dispatch.handoff")


def _new_tips() -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"].startswith(ALL_NEW_PREFIXES)
    ]


def _family(prefix: str) -> list[dict]:
    return [
        t for t in _new_tips()
        if t["form_key"] == prefix or t["form_key"].startswith(prefix + ".")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_seed_count():
    assert len(_new_tips()) >= 25, (
        "Expected ≥25 iter226 tips (8 utilization + 8 daily-report-read "
        "+ 9 handoff)"
    )


@pytest.mark.parametrize("prefix", ["dispatch.utilization", "dispatch.daily-report-read", "dispatch.handoff"])
def test_canonical_four_kinds_present(prefix):
    rows = [t for t in _new_tips() if t["form_key"] == prefix]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"{prefix} missing canonical kind {required!r}"


@pytest.mark.parametrize("form_key", UTIL_KEYS + DRR_KEYS + HANDOFF_KEYS)
def test_each_form_key_has_at_least_one_tip(form_key):
    rows = [t for t in _new_tips() if t["form_key"] == form_key]
    assert rows, f"{form_key} has no tips"


# ─────────────────────────────────────────────────────────────────────
# RBAC — strictly Tier-2 dispatch+admin (no public, no leakage)
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_dispatch_admin_scoped_only():
    for t in _new_tips():
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} has 'public' scope — "
            f"iter226 dispatcher coaching is Tier-2 only"
        )
        assert scopes <= {"dispatch", "admin"}, (
            f"{t['form_key']}/{t['kind']} has out-of-scope scopes "
            f"{scopes} — allowed: dispatch / admin only"
        )
        assert scopes & {"dispatch", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing dispatch/admin: {scopes}"
        )


@pytest.mark.parametrize("prefix", ["dispatch.utilization", "dispatch.daily-report-read", "dispatch.handoff"])
def test_anon_caller_sees_no_tips(prefix):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={prefix}",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json().get("count", 0) == 0


# ─────────────────────────────────────────────────────────────────────
# Bilingual + concise
# ─────────────────────────────────────────────────────────────────────
def test_all_tips_bilingual():
    for t in _new_tips():
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_all_tips_concise():
    for t in _new_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# OPERATOR-STATED ANCHORS (load-bearing · verbatim · enforced)
# ─────────────────────────────────────────────────────────────────────
def test_anchor_utilization_decision_not_scoreboard():
    """Operator-stated anchor:
       'Utilization is a decision tool, not a scoreboard.'

    Must land verbatim somewhere in the dispatch.utilization family.
    """
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or ""))
        for t in _family("dispatch.utilization")
    ).lower()
    assert "decision tool, not a scoreboard" in haystack, (
        "dispatch.utilization family MUST contain the operator-stated "
        "anchor 'decision tool, not a scoreboard' verbatim"
    )


def test_anchor_routing_intel_movement_not_blame():
    """Operator-stated anchor:
       'The Daily Report is the dispatcher's routing intel — read it
        for movement, not for blame.'
    """
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or ""))
        for t in _family("dispatch.daily-report-read")
    ).lower()
    assert "routing intel" in haystack, (
        "dispatch.daily-report-read MUST contain 'routing intel' verbatim"
    )
    assert "movement, not for blame" in haystack or "movement, not blame" in haystack, (
        "dispatch.daily-report-read MUST contain the operator anchor "
        "'movement, not for blame' verbatim"
    )


def test_anchor_handoff_conversation_not_calendar_invite():
    """Operator-stated anchor:
       'The handoff is a conversation, not a calendar invite.'
    """
    haystack = " ".join(
        ((t.get("title") or "") + " " + (t.get("body") or ""))
        for t in _family("dispatch.handoff")
    ).lower()
    assert "conversation, not a calendar invite" in haystack, (
        "dispatch.handoff family MUST contain the operator-stated "
        "anchor 'conversation, not a calendar invite' verbatim"
    )


def test_anchor_handoff_gate_guard_06_00():
    """Operator-stated framing:
       'If tomorrow's plan changed, the foreman hears it from you
        tonight — not from the gate guard at 06:00.'

    The 06:00 gate-guard reference is the load-bearing operational
    image that makes the discipline land — abstract 'communicate
    clearly' advice defeats the point.
    """
    haystack = " ".join(
        ((t.get("body") or ""))
        for t in _family("dispatch.handoff")
    ).lower()
    assert "gate guard" in haystack, (
        "dispatch.handoff MUST keep the 'gate guard at 06:00' image — "
        "abstract communication advice loses the operational anchor"
    )
    assert "06:00" in haystack, (
        "dispatch.handoff MUST name the 06:00 next-morning failure mode"
    )


# ─────────────────────────────────────────────────────────────────────
# Operator-stated anti-patterns enforced per leaf
# ─────────────────────────────────────────────────────────────────────
def test_utilization_scoreboard_leaf_names_anti_pattern():
    """The .scoreboard leaf exists specifically to coach against
    naming-and-shaming and number-as-grade reading. Must explicitly
    name the anti-pattern."""
    rows = [t for t in _new_tips() if t["form_key"] == "dispatch.utilization.scoreboard"]
    haystack = " ".join(((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows).lower()
    assert "grade" in haystack or "scoreboard" in haystack, (
        ".scoreboard leaf must explicitly name the grade / scoreboard "
        "anti-pattern"
    )
    assert "shame" in haystack or "performance review" in haystack or "ask" in haystack, (
        ".scoreboard leaf must coach against name-and-shame / "
        "performance-review framing"
    )


def test_utilization_redeploy_leaf_teaches_call_first():
    """The .redeploy leaf must coach: phone call BEFORE Transfer
    ticket. Operator anchor inherited from iter225 outreach work."""
    rows = [t for t in _new_tips() if t["form_key"] == "dispatch.utilization.redeploy"]
    haystack = " ".join(((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows).lower()
    assert "call" in haystack or "phone" in haystack, (
        ".redeploy leaf must coach calling before opening the transfer"
    )
    assert "before" in haystack or "first" in haystack, (
        ".redeploy leaf must teach the ORDER: call FIRST, transfer SECOND"
    )


def test_daily_report_read_return_drift_names_ghost_rental():
    """The .return-drift leaf must explicitly name the 'ghost rental'
    operational concept — that's the load-bearing concrete framing."""
    rows = [t for t in _new_tips() if t["form_key"] == "dispatch.daily-report-read.return-drift"]
    haystack = " ".join(((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows).lower()
    assert "ghost rental" in haystack or "ghost-rental" in haystack, (
        ".return-drift leaf MUST name the 'ghost rental' concept "
        "(operator-stated concrete framing)"
    )


def test_handoff_communication_teaches_call_beats_text():
    """The .communication leaf must teach the operator-stated
    hierarchy: call > text > silent. Not just 'communicate well.'"""
    rows = [t for t in _new_tips() if t["form_key"] == "dispatch.handoff.communication"]
    haystack = " ".join(((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows).lower()
    assert "call" in haystack, ".communication must reference phone calls"
    assert "text" in haystack, ".communication must reference texts (the medium being deprioritized)"


def test_handoff_changes_teaches_changed_foremen_first():
    """The .changes leaf must teach SEQUENCING: foremen with
    changed plans get called FIRST, not by alphabetical name."""
    rows = [t for t in _new_tips() if t["form_key"] == "dispatch.handoff.changes"]
    haystack = " ".join(((t.get("title") or "") + " " + (t.get("body") or "")) for t in rows).lower()
    assert "first" in haystack or "sequence" in haystack, (
        ".changes leaf must teach calling changed-plan foremen FIRST"
    )


def test_handoff_communication_example_has_concrete_dialogue():
    """The .communication example must demonstrate a real call script
    with concrete details — abstract 'have a conversation' defeats
    the leaf."""
    ex = next(
        (t for t in _new_tips()
         if t["form_key"] == "dispatch.handoff.communication"
         and t["kind"] == "example"),
        None,
    )
    assert ex
    body = ex.get("body") or ""
    # Must have a quoted script
    assert "'" in body or "\u2018" in body or "\u201c" in body, (
        ".communication example must contain quoted dialogue"
    )
    # Must reference specific times or named people
    import re
    has_time = bool(re.search(r"\d{1,2}:\d{2}", body))
    has_name = bool(re.search(r"\b(Tony|Mike|Alex|Sam|Joe|Pat|Chris)\b", body))
    assert has_time or has_name, (
        ".communication example must reference concrete time-of-day or "
        "a named person — abstract examples defeat the leaf"
    )


# ─────────────────────────────────────────────────────────────────────
# Anti-legal-drift firewall (inherited)
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
    for t in _new_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        assert phrase.lower() not in full.lower(), (
            f"{t['form_key']}/{t['kind']} contains legal-drift phrase "
            f"{phrase!r}"
        )


# ─────────────────────────────────────────────────────────────────────
# Standard tone discipline (inherited)
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
]
CORPORATE_DRIFT_PHRASES = [
    "synergize", "stakeholder alignment", "leverage synergies",
    "best-in-class", "core competency",
    "operational excellence framework", "performance optimization",
    "operational intelligence platform",
]
# iter224 motivational-fluff banlist — inherited and extended for
# dispatch (no "operational excellence" branding, no "world-class
# dispatch" KPI-poster language).
MOTIVATIONAL_FLUFF_PHRASES = [
    "welcome aboard", "we are excited to have you",
    "embark on this journey", "exciting opportunity ahead",
    "passionate about", "world-class",
    "operational excellence", "operational journey",
    "best-in-class dispatch", "dispatch excellence",
]
# iter226-specific: anti-KPI-poster banlist. Utilization page is the
# highest-risk surface for KPI-dashboard tone drift. Hard-stop on
# scoreboard / leaderboard / grading language.
KPI_POSTER_PHRASES = [
    "key performance indicator", "kpi dashboard", "kpi metric",
    "performance grade", "scorecard system",
    "leaderboard rank", "performance ranking",
]


def test_no_robotic_osha_tone():
    for t in _new_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} OSHA tone: {bad}"


def test_no_corporate_drift_tone():
    for t in _new_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} corporate drift: {bad}"


def test_no_motivational_fluff_tone():
    """Inherited iter224 banlist, extended for dispatch with
    'operational excellence' / 'world-class dispatch' / 'dispatch
    excellence' — these are the dispatch flavor of HR-branding drift."""
    for t in _new_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in MOTIVATIONAL_FLUFF_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} motivational fluff: {bad}"
        )


def test_no_kpi_poster_tone():
    """iter226-specific: utilization page is the highest-risk
    surface for KPI-poster drift. Hard-stop on scoreboard,
    leaderboard, ranking, and grading language. The operator anchor
    is explicit on this: 'decision tool, not a scoreboard.'"""
    for t in _new_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in KPI_POSTER_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} KPI-poster drift: {bad}"
        )


# ─────────────────────────────────────────────────────────────────────
# Reviewer-side discipline check (iter218 pattern · daily-report-read)
# ─────────────────────────────────────────────────────────────────────
def test_daily_report_read_is_reviewer_side_voice():
    """The dispatch.daily-report-read family is a REVIEWER-SIDE
    surface (iter218 pattern). The coaching must speak to the
    person READING the report, not the person FILING it. Test:
    must use second-person verbs that imply reading/reviewing,
    not filing."""
    family = _family("dispatch.daily-report-read")
    haystack = " ".join((t.get("body") or "").lower() for t in family)
    # Must include reader-side verbs
    reader_signals = ["read it", "read the", "reading", "you read", "translate"]
    hits = [s for s in reader_signals if s in haystack]
    assert hits, (
        f"daily-report-read family must use reviewer-side voice (iter218 "
        f"pattern). Expected one of {reader_signals}, found none."
    )


# ─────────────────────────────────────────────────────────────────────
# Persona-anchor vocabulary (walkthrough_pass.md §5)
# ─────────────────────────────────────────────────────────────────────
def test_each_family_contains_persona_anchor():
    """walkthrough_pass.md §5: every tip body must contain at least
    one persona-anchor phrase. The dispatcher families MUST anchor
    in field-realism vocabulary."""
    PERSONA_ANCHORS = [
        "foreman", "crew", "super", "dispatch", "shop", "safety",
        "operator", "jobsite", "driver", "schedule", "field",
        "unit", "yard",
    ]
    for prefix in ALL_NEW_PREFIXES:
        family = _family(prefix)
        haystack = " ".join((t.get("body") or "").lower() for t in family)
        hits = [a for a in PERSONA_ANCHORS if a in haystack]
        assert len(hits) >= 3, (
            f"{prefix} family must anchor in ≥3 persona-vocabulary "
            f"phrases. Found: {hits}"
        )


# ─────────────────────────────────────────────────────────────────────
# Strategic-hold guard (walkthrough_pass.md §10)
# ─────────────────────────────────────────────────────────────────────
def test_iter226_does_not_violate_mid_day_defect_hold():
    """Per walkthrough_pass.md §10, the operator mid-day-defect
    surface is STRATEGIC HOLD. iter226 coaching must not silently
    drift into mid-day-defect routing prescriptions. The handoff
    family deliberately stops at end-of-day; the daily-report-read
    family deliberately stops at next-morning routing.

    Hard-stop: no iter226 tip should prescribe what to do when a
    unit goes down DURING the workday (that's the held architectural
    decision). They may REFERENCE such moments as escalate triggers,
    but must not author the routing playbook itself.
    """
    held_prescriptions = [
        "mid-day-defect routing", "defect routing playbook",
        "when a unit breaks mid-shift, do",
        "field-defect escalation chain",
    ]
    for t in _new_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""]).lower()
        bad = [p for p in held_prescriptions if p in full]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} drifted into the operator "
            f"mid-day-defect STRATEGIC HOLD: {bad}"
        )


# ─────────────────────────────────────────────────────────────────────
# Static UI wiring checks
# ─────────────────────────────────────────────────────────────────────
def test_admin_dispatch_wires_utilization_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/admin/AdminDispatch.jsx").read_text()
    assert 'formKey="dispatch.utilization"' in src, (
        "AdminDispatch.jsx must render "
        '<HelpTipBlock formKey="dispatch.utilization" />'
    )


def test_admin_dispatch_wires_handoff_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/admin/AdminDispatch.jsx").read_text()
    assert 'formKey="dispatch.handoff"' in src, (
        "AdminDispatch.jsx must render "
        '<HelpTipBlock formKey="dispatch.handoff" /> on overview tab'
    )


def test_daily_reports_dashboard_wires_reader_side_block():
    from pathlib import Path
    src = Path("/app/frontend/src/pages/DailyReportsDashboard.jsx").read_text()
    assert "HelpTipBlock" in src, (
        "DailyReportsDashboard.jsx must import HelpTipBlock"
    )
    assert 'formKey="dispatch.daily-report-read"' in src, (
        "DailyReportsDashboard.jsx must render reviewer-side "
        '<HelpTipBlock formKey="dispatch.daily-report-read" />'
    )
