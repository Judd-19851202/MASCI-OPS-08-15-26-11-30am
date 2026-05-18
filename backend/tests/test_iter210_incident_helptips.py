"""iter210 — Safety Incident contextual coaching tips.

Wires HelpTip coverage into the high-risk Safety Incident form.

Same Tier-1 discipline as iter209:
  • public-scope (anonymous-readable — incident form is public-facing)
  • concise (≤80 EN words, ≤90 ES words per body)
  • bilingual
  • no protected workflow leakage
  • parent-context fall-up: leaf form_keys also return parent tips
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

INCIDENT_FORM_KEYS = [
    "incident",
    "incident.location",
    "incident.narrative",
    "incident.severity",
    "incident.witnesses",
    "incident.corrective",
]

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def test_incident_registry_seed_count():
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    incident_tips = [t for t in all_tips()
                     if t["form_key"] == "incident"
                     or t["form_key"].startswith("incident.")]
    assert len(incident_tips) >= 16, (
        f"Initial incident seed should land ≥16 tips; got {len(incident_tips)}"
    )


def test_incident_top_level_exposes_canonical_four_tips():
    """Top-level incident must offer Why / Who / Next / Escalate.
    This is the operator-stated canonical surface for any new form."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=incident",
        timeout=10.0,
    )
    assert r.status_code == 200
    kinds = {t["kind"] for t in r.json()["tips"]}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"incident top-level missing kind={required}; got {kinds}"
        )


@pytest.mark.parametrize("form_key", INCIDENT_FORM_KEYS)
def test_incident_tip_endpoint_anon_returns_tips(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    assert r.status_code == 200
    tips = r.json()["tips"]
    assert len(tips) >= 1, (
        f"{form_key} should return at least one tip (incl. parent fall-up)"
    )


def test_incident_leaf_includes_parent_context():
    """Leaf form_keys must also return the parent 'incident' tips."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=incident.severity",
        timeout=10.0,
    )
    keys = {t["form_key"] for t in r.json()["tips"]}
    assert "incident" in keys, (
        "Parent 'incident' tips must appear when querying a leaf"
    )
    assert "incident.severity" in keys


@pytest.mark.parametrize("form_key", INCIDENT_FORM_KEYS)
def test_incident_tips_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        assert t.get("title_es"), (
            f"{t['form_key']}/{t['kind']}: missing title_es"
        )
        assert t.get("body_es"), (
            f"{t['form_key']}/{t['kind']}: missing body_es"
        )


@pytest.mark.parametrize("form_key", INCIDENT_FORM_KEYS)
def test_incident_tips_concise(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}",
        timeout=10.0,
    )
    for t in r.json()["tips"]:
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, (
            f"{t['form_key']}/{t['kind']} EN too long ({wc_en} words)"
        )
        assert wc_es <= 90, (
            f"{t['form_key']}/{t['kind']} ES too long ({wc_es} words)"
        )


BANNED_WORKFLOW_PHRASES = [
    "User management — invite",
    "Audit log — every privileged",
    "Backups & restore — manual triggers",
    "Role templates — define",
    "Sessions — who is signed in",
]


@pytest.mark.parametrize("form_key", INCIDENT_FORM_KEYS)
def test_incident_tips_no_admin_leak(form_key):
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


def test_incident_tips_include_high_value_coaching_surfaces():
    """Operator priority list for Safety Incidents — every named surface
    must be covered by at least one tip."""
    expected = {
        "incident.location": {"why"},        # location accuracy
        "incident.narrative": {"why"},       # narrative quality
        "incident.witnesses": {"why"},       # witness handling
        "incident.severity":  {"why"},       # severity clarity
        "incident.corrective": {"why"},      # corrective-action expectations
        "incident":           {"escalate"},  # escalation timing
    }
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    by_key: dict[str, set[str]] = {}
    for t in all_tips():
        by_key.setdefault(t["form_key"], set()).add(t["kind"])
    for fk, kinds in expected.items():
        for k in kinds:
            assert k in by_key.get(fk, set()), (
                f"missing operator-priority tip: {fk}/{k}"
            )
