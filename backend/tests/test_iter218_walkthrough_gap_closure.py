"""iter218 — Close the four iter217 walkthrough P0 gaps with authored coaching.

This iter is the editorial side of the iter217 self-validating loop:
walkthrough surfaced a gap → author the coaching → re-run the
walkthrough → watch the actionable-finding count drop.

Gaps closed:
  1. field-leadership.records      — reviewer-side coaching for supers
  2. crew_eval                     — migrated from legacy WhyItMattersPanel
  3. dispatch.idle-alerts          — Tier-2 dispatcher coaching
  4. dispatch.holds                — Tier-2 dispatcher coaching

Plus public-hub Day-1 "Start Here" entry (visual; verified by walkthrough).
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)


def _tips_under(prefix: str) -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == prefix or t["form_key"].startswith(prefix + ".")
    ]


# ═════════════════════════════════════════════════════════════════════
# Gap #1 — field-leadership.records (reviewer-side coaching)
# Scope: leadership + admin + pm
# ═════════════════════════════════════════════════════════════════════

REC_KEYS = ["field-leadership.records", "field-leadership.records.review-tone"]


def test_records_seed_count():
    rows = _tips_under("field-leadership.records")
    assert len(rows) >= 6, f"expected ≥6 records tips, got {len(rows)}"


def test_records_canonical_four_tips_present():
    rows = [t for t in _tips_under("field-leadership.records")
            if t["form_key"] == "field-leadership.records"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, f"records missing canonical {required!r}"


def test_records_tier2_scope_correct():
    """Reviewer-side coaching: scope must be {leadership, admin, pm} —
    field staff don't review records, only file them."""
    for t in _tips_under("field-leadership.records"):
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} accidentally has 'public' scope — "
            f"reviewer-side coaching is Tier-2"
        )
        assert scopes & {"leadership", "admin", "pm"}, (
            f"{t['form_key']}/{t['kind']} missing leadership/admin/pm scope: {scopes}"
        )


def test_records_anon_blocked():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=field-leadership.records",
        timeout=10.0,
    )
    assert r.status_code == 200
    assert r.json().get("count", 0) == 0


def test_records_anchors_reviewing_not_auditing():
    """The cultural anchor for reviewer-side coaching: reviewing is
    NOT auditing. Must surface in the top-level 'why'."""
    top_why = next(
        (t for t in _tips_under("field-leadership.records")
         if t["form_key"] == "field-leadership.records" and t["kind"] == "why"),
        None,
    )
    assert top_why
    body = (top_why.get("body") or "").lower()
    assert "auditing" in body or "audit" in body, (
        "top-level 'why' must contrast reviewing vs auditing "
        "(operator-stated tone direction)"
    )


def test_records_escalate_coaches_call_dont_edit():
    """When something looks wrong: the tip must coach calling the
    foreman, never silent editing."""
    next_tip = next(
        (t for t in _tips_under("field-leadership.records")
         if t["form_key"] == "field-leadership.records" and t["kind"] == "next"),
        None,
    )
    assert next_tip
    body = (next_tip.get("body") or "").lower()
    assert "foreman" in body, "next tip must reference the foreman"
    assert "source" in body or "silent" in body, (
        "next tip must coach 'fix at the source, never silent edit' anchor"
    )


# ═════════════════════════════════════════════════════════════════════
# Gap #2 — crew_eval (migrated from legacy WhyItMattersPanel)
# Scope: leadership + admin
# ═════════════════════════════════════════════════════════════════════

CREWEVAL_KEYS = ["crew_eval", "crew_eval.calibration", "crew_eval.evidence"]


def test_crew_eval_seed_count():
    assert len(_tips_under("crew_eval")) >= 8


def test_crew_eval_canonical_four_tips_present():
    rows = [t for t in _tips_under("crew_eval") if t["form_key"] == "crew_eval"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds


def test_crew_eval_tier2_scope_leadership_admin_only():
    for t in _tips_under("crew_eval"):
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes
        assert scopes & {"leadership", "admin"}


def test_crew_eval_anchors_calibration_beats_scoring():
    rows = _tips_under("crew_eval.calibration")
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "calibration" in haystack or "average" in haystack, (
        "calibration coaching must surface the 'compare to average' anchor"
    )


def test_crew_eval_evidence_example_concrete():
    """The example tip must demonstrate concreteness — date, unit ID,
    or specific named event. Same evidence-not-vibes standard as iter214."""
    import re
    ex = next(
        (t for t in _tips_under("crew_eval")
         if t["form_key"] == "crew_eval.evidence" and t["kind"] == "example"),
        None,
    )
    assert ex
    body = ex.get("body") or ""
    has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}", body))
    has_unit = bool(re.search(r"\b[Uu]nit \d+\b", body))
    assert has_date or has_unit, (
        "crew_eval.evidence example must contain a specific date or unit ID"
    )


def test_crew_eval_escalate_coaches_call_hr():
    esc = next(
        (t for t in _tips_under("crew_eval")
         if t["form_key"] == "crew_eval" and t["kind"] == "escalate"),
        None,
    )
    assert esc
    body = (esc.get("body") or "").lower()
    assert "hr" in body, "crew_eval escalate must coach HR call-up"


# ═════════════════════════════════════════════════════════════════════
# Gap #3 — dispatch.idle-alerts
# Scope: dispatch + admin
# ═════════════════════════════════════════════════════════════════════

def test_idle_alerts_seed_count():
    assert len(_tips_under("dispatch.idle-alerts")) >= 6


def test_idle_alerts_canonical_four_tips_present():
    rows = [t for t in _tips_under("dispatch.idle-alerts")
            if t["form_key"] == "dispatch.idle-alerts"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds


def test_idle_alerts_tier2_dispatch_scoped():
    for t in _tips_under("dispatch.idle-alerts"):
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes
        assert scopes & {"dispatch", "admin"}


def test_idle_alerts_anchors_opportunity_not_blame():
    top_why = next(
        (t for t in _tips_under("dispatch.idle-alerts")
         if t["form_key"] == "dispatch.idle-alerts" and t["kind"] == "why"),
        None,
    )
    assert top_why
    body = (top_why.get("body") or "").lower()
    assert "opportunity" in body or "discovery" in body, (
        "idle-alerts 'why' must frame as opportunity/discovery (not blame)"
    )
    # Anti-blame discipline check
    assert "wasting" not in body or "isn't" in body, (
        "idle-alerts 'why' must explicitly reject the 'wasting equipment' framing"
    )


def test_idle_alerts_thresholds_explains_7_14_30():
    rows = _tips_under("dispatch.idle-alerts.thresholds")
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    for n in ("7", "14", "30"):
        assert n in haystack, (
            f"threshold coaching must reference the {n}-day threshold"
        )


# ═════════════════════════════════════════════════════════════════════
# Gap #4 — dispatch.holds
# Scope: dispatch + admin
# ═════════════════════════════════════════════════════════════════════

def test_holds_seed_count():
    assert len(_tips_under("dispatch.holds")) >= 6


def test_holds_canonical_four_tips_present():
    rows = [t for t in _tips_under("dispatch.holds")
            if t["form_key"] == "dispatch.holds"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds


def test_holds_tier2_dispatch_scoped():
    for t in _tips_under("dispatch.holds"):
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes
        assert scopes & {"dispatch", "admin"}


def test_holds_anchors_dispatch_doesnt_release():
    """The cultural anchor: dispatch sees and routes around holds —
    Safety/Shop releases them. Must be explicit in the top-level 'why'."""
    top_why = next(
        (t for t in _tips_under("dispatch.holds")
         if t["form_key"] == "dispatch.holds" and t["kind"] == "why"),
        None,
    )
    assert top_why
    body = (top_why.get("body") or "").lower()
    assert "second-guess" in body or "decision" in body or "route around" in body, (
        "holds 'why' must coach the see-route-around-don't-decide anchor"
    )


def test_holds_who_explains_three_classes():
    """Tip must explain the three hold classes: Safety / Maintenance /
    Pending — that's the dispatcher's primary mental model."""
    who = next(
        (t for t in _tips_under("dispatch.holds")
         if t["form_key"] == "dispatch.holds" and t["kind"] == "who"),
        None,
    )
    assert who
    body = (who.get("body") or "").lower()
    for klass in ("safety", "maintenance", "pending"):
        assert klass in body, f"holds 'who' must explain {klass!r} class"


# ═════════════════════════════════════════════════════════════════════
# Cross-cutting — bilingual + concise + tone discipline
# ═════════════════════════════════════════════════════════════════════

ALL_ITER218 = (
    _tips_under.__name__ and None  # no-op; only here so import-time eval is harmless
)


def _all_iter218_tips():
    return (
        _tips_under("field-leadership.records")
        + _tips_under("crew_eval")
        + _tips_under("dispatch.idle-alerts")
        + _tips_under("dispatch.holds")
    )


def test_all_iter218_tips_bilingual():
    for t in _all_iter218_tips():
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_all_iter218_tips_concise():
    for t in _all_iter218_tips():
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
    "the undersigned", "willful violation",
]

CORPORATE_DRIFT_PHRASES = [
    "human capital", "stakeholder alignment", "leverage synergies",
    "best-in-class", "core competency", "deliverables-driven",
    "value-add proposition", "right-size",
]

HR_LEGAL_DRIFT_PHRASES = [
    "progressive discipline policy",
    "disciplinary action up to and including",
    "at-will employment",
    "performance improvement plan procedure",
]


def test_no_osha_drift_iter218():
    for t in _all_iter218_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} uses OSHA tone: {bad}"


def test_no_corporate_drift_iter218():
    for t in _all_iter218_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} drifts MBA-speak: {bad}"


def test_no_hr_legal_drift_iter218():
    """crew_eval is especially exposed to HR-legal drift — guard it."""
    for t in _tips_under("crew_eval"):
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in HR_LEGAL_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} HR-legal drift: {bad}"


def test_iter218_field_realism_anchors_present():
    """At least one persona-anchor phrase must surface across each
    family. Anchors: foreman, crew, super, dispatch, HR, PM, Shop,
    Safety, operator."""
    families = [
        ("field-leadership.records", "field-leadership.records"),
        ("crew_eval", "crew_eval"),
        ("dispatch.idle-alerts", "dispatch.idle-alerts"),
        ("dispatch.holds", "dispatch.holds"),
    ]
    for label, prefix in families:
        haystack = " ".join(
            (t.get("body") or "").lower() for t in _tips_under(prefix)
        )
        anchors = ["foreman", "crew", "super", "dispatch",
                   "hr", "pm", "shop", "safety", "operator"]
        hits = [a for a in anchors if a in haystack]
        assert hits, (
            f"{label} family has NO persona-anchor phrase. Approved: {anchors}."
        )


# ═════════════════════════════════════════════════════════════════════
# Public-hub Day-1 entry — Hub.jsx static check (no playwright needed)
# ═════════════════════════════════════════════════════════════════════

def test_public_hub_has_day_one_start_here_entry():
    """The iter218 discoverability fix: Hub.jsx must surface a
    Day-1 'Start Here' entry to anonymous (no-session) callers."""
    from pathlib import Path
    src = Path("/app/frontend/src/pages/Hub.jsx").read_text()
    assert "hub-day-one-start-here" in src, (
        "Hub.jsx must contain the iter218 hub-day-one-start-here testid"
    )
    assert "role-new-employee" in src, (
        "Hub.jsx Day-1 link must target /guidance/role-new-employee "
        "(the existing public 'New Employee' onboarding article)"
    )
    assert "!session" in src or "{ !session" in src or "!session &&" in src, (
        "Day-1 entry must be conditional on no active session "
        "(returning users don't need it)"
    )
