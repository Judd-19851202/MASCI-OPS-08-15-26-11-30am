"""iter211 — Pre-Op Equipment Inspection contextual coaching.

Highest-frequency operational coaching surface on the platform.
Same Tier-1 discipline as iter209/210: concise, bilingual, public,
no workflow leak. Plus tone-specific assertions: the operator
explicitly directed away from robotic OSHA tone, toward accountability
and ownership coaching.
"""
import os
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

PREOP_FORM_KEYS = [
    "preop",
    "preop.fluids",
    "preop.tires-tracks",
    "preop.controls",
    "preop.defects",
    "preop.signoff",
]

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


def test_preop_seed_count():
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    preop = [t for t in all_tips()
             if t["form_key"] == "preop"
             or t["form_key"].startswith("preop.")]
    assert len(preop) >= 14, (
        f"Initial Pre-Op seed should land ≥14 tips; got {len(preop)}"
    )


def test_preop_top_level_canonical_four_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=preop", timeout=10.0
    )
    kinds = {t["kind"] for t in r.json()["tips"]}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds, (
            f"preop top-level missing kind={required}; got {kinds}"
        )


@pytest.mark.parametrize("form_key", PREOP_FORM_KEYS)
def test_preop_endpoint_anon_returns_tips(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0
    )
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


@pytest.mark.parametrize("form_key", PREOP_FORM_KEYS)
def test_preop_tips_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0
    )
    for t in r.json()["tips"]:
        assert t.get("title_es"), (
            f"{t['form_key']}/{t['kind']}: missing title_es"
        )
        assert t.get("body_es"), (
            f"{t['form_key']}/{t['kind']}: missing body_es"
        )


@pytest.mark.parametrize("form_key", PREOP_FORM_KEYS)
def test_preop_tips_concise(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0
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


# ─────────────────────────────────────────────────────────────────────
# Tone guardrail — operator directive: lean into operational realism,
# ownership, professionalism. Avoid robotic OSHA tone, fear-based
# language, corporate/legal overload.
# ─────────────────────────────────────────────────────────────────────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with",
    "pursuant to",
    "in compliance with applicable",
    "OSHA-mandated",
    "regulatory requirement",
    "shall be required to",
    "the undersigned",
    "willful violation",
]


@pytest.mark.parametrize("form_key", PREOP_FORM_KEYS)
def test_preop_tips_not_robotic_osha_tone(form_key):
    """The whole point of Pre-Op coaching is to NOT read like an OSHA
    handbook. Hard-fail if any robotic phrase slips into the registry."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0
    )
    for t in r.json()["tips"]:
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, (
            f"{t['form_key']}/{t['kind']} uses robotic OSHA tone: {bad}"
        )


def test_preop_operator_priority_surfaces_covered():
    """Operator directive enumerated 6 priority surfaces. Every one must
    have at least one Why-coaching tip."""
    expected = [
        "preop",
        "preop.fluids",
        "preop.tires-tracks",
        "preop.controls",
        "preop.defects",
        "preop.signoff",
    ]
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    by_key: dict[str, set[str]] = {}
    for t in all_tips():
        by_key.setdefault(t["form_key"], set()).add(t["kind"])
    for fk in expected:
        assert "why" in by_key.get(fk, set()), (
            f"missing operator-priority Why tip at {fk}"
        )


def test_preop_signoff_includes_pressure_escalate_tip():
    """Operator explicitly wanted 'when pressure to sign feels wrong'
    coaching. Specifically asserted because it's the highest-value
    cultural-safety surface on the platform."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=preop.signoff", timeout=10.0
    )
    has_pressure_tip = any(
        t["kind"] == "escalate"
        and "pressure" in (t.get("body") or "").lower()
        for t in r.json()["tips"]
    )
    assert has_pressure_tip, (
        "preop.signoff must include an 'escalate' tip covering "
        "supervisor pressure to sign"
    )


def test_preop_defects_explains_photo_requirement():
    """Photo + 1-sentence note is the operator-stated rule; one of the
    Pre-Op defects tips must articulate it explicitly."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=preop.defects", timeout=10.0
    )
    has_photo_rule = any(
        "photo" in (t.get("body") or "").lower()
        for t in r.json()["tips"]
    )
    assert has_photo_rule, (
        "preop.defects must include explicit photo coaching"
    )
