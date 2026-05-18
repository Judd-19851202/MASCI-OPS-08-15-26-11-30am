"""iter214 — Write-Up contextual coaching + due-process anchor.

Write-Ups are the operator's 5th-target rollout (after Daily Reports,
Incidents, Pre-Op, Checkout, Time Verification). The cultural tone:
write-ups are the RECORD of a conversation that already happened,
never a substitute for it. Coach toward facts-not-feelings, the talk
before the paper, and the employee's right to add their side.

The supervisor's word is on the line every bit as much as the
employee's — a write-up that says 'has an attitude problem' weakens
the file. A write-up that says 'arrived 22 minutes late, third time
this month, no call' strengthens it.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

WRITEUP_FORM_KEYS = [
    "writeup",
    "writeup.facts",
    "writeup.conversation",
    "writeup.due-process",
]


def _writeup_tips():
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == "writeup" or t["form_key"].startswith("writeup.")
    ]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure
# ─────────────────────────────────────────────────────────────────────
def test_writeup_seed_count():
    assert len(_writeup_tips()) >= 11


def test_writeup_top_level_canonical_four_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=writeup", timeout=10.0,
    )
    kinds = {t["kind"] for t in r.json()["tips"]}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds


@pytest.mark.parametrize("form_key", WRITEUP_FORM_KEYS)
def test_writeup_form_key_anon_readable(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


@pytest.mark.parametrize("form_key", WRITEUP_FORM_KEYS)
def test_writeup_tips_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


@pytest.mark.parametrize("form_key", WRITEUP_FORM_KEYS)
def test_writeup_tips_concise(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# ─────────────────────────────────────────────────────────────────────
# Tone discipline — banlists
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
    "the undersigned", "willful violation",
]

# Write-ups especially must avoid HR-legal-speak that erases the
# operational-leadership voice. These phrases drift into compliance-
# manual mode and dilute the field-leadership coaching tone.
HR_LEGAL_DRIFT_PHRASES = [
    "progressive discipline policy",
    "disciplinary action up to and including",
    "at-will employment",
    "performance improvement plan procedure",
]


@pytest.mark.parametrize("form_key", WRITEUP_FORM_KEYS)
def test_writeup_no_robotic_osha_tone(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} uses OSHA tone: {bad}"


def test_writeup_no_hr_legal_drift():
    for t in _writeup_tips():
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in HR_LEGAL_DRIFT_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} drifts into HR-legal mode: {bad}"
        )


# ─────────────────────────────────────────────────────────────────────
# Positive realism anchors — write-up specific
# ─────────────────────────────────────────────────────────────────────
def test_writeup_anchors_conversation_first():
    """The cultural anchor for write-ups: the conversation comes first,
    the paper is the record. Must be present in the top-level 'why'."""
    top_why = next(
        (t for t in _writeup_tips()
         if t["form_key"] == "writeup" and t["kind"] == "why"),
        None,
    )
    assert top_why, "missing top-level 'why' tip"
    body = (top_why.get("body") or "").lower()
    assert "conversation" in body, (
        "top-level 'why' must anchor on the conversation-first principle "
        "(operator-stated tone direction)"
    )


def test_writeup_facts_includes_example_with_concrete_time():
    """The 'example' tip on writeup.facts must demonstrate concreteness
    — specific time, date, or witness name. That's the operator-stated
    'facts not feelings' direction made testable."""
    ex = next(
        (t for t in _writeup_tips()
         if t["form_key"] == "writeup.facts" and t["kind"] == "example"),
        None,
    )
    assert ex, "missing facts example tip"
    body = (ex.get("body") or "")
    # Must contain either a clock time or a calendar date — concreteness
    # is the entire point.
    import re
    has_time = bool(re.search(r"\d{1,2}:\d{2}", body))
    has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}", body))
    assert has_time or has_date, (
        "facts example must contain a specific time or date "
        "(concreteness anchor)"
    )


def test_writeup_due_process_addresses_refusal_to_sign():
    """The 'refusal to sign' surface is the hardest cultural moment in
    a write-up. Coaching must explicitly address it."""
    rows = [t for t in _writeup_tips() if t["form_key"] == "writeup.due-process"]
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "sign" in haystack or "signing" in haystack, (
        "writeup.due-process must address the signature dynamic"
    )
    # And the coaching must clarify that signing != agreeing.
    assert any(p in haystack for p in (
        "received", "not 'i agree'", "doesn't void", "doesn’t void",
    )), (
        "writeup.due-process must clarify 'signature = received, not "
        "agreed' (cultural tone direction)"
    )


def test_writeup_facts_rejects_loaded_language_via_example():
    """The 'mistake' tip on writeup.facts must explicitly call out
    loaded-language patterns ('lazy', 'attitude', etc.). This is the
    common failure mode the operator wants caught at write time."""
    m = next(
        (t for t in _writeup_tips()
         if t["form_key"] == "writeup.facts" and t["kind"] == "mistake"),
        None,
    )
    assert m, "missing facts mistake tip"
    body = (m.get("body") or "").lower()
    assert any(p in body for p in ("loaded", "lazy", "attitude", "vague")), (
        "writeup.facts mistake tip must name a loaded-language pattern"
    )


# ─────────────────────────────────────────────────────────────────────
# RBAC — write-up coaching is public-scope (Tier 1 templating). The
# actual write-up RECORDS are portal-scoped, but the coaching about
# how to write a good one is intentionally public so supervisors can
# read it before signing into the form.
# ─────────────────────────────────────────────────────────────────────
def test_writeup_tips_public_scope():
    for t in _writeup_tips():
        assert "public" in (t.get("scopes") or []), (
            f"{t['form_key']}/{t['kind']} must be public-scope (Tier-1 "
            f"coaching template)"
        )
