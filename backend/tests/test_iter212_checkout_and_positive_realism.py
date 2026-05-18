"""iter212 — Equipment Checkout contextual coaching + positive realism anchor.

Equipment Checkout is the accountability handshake. Tips here are about
trust, ownership, and the operator-after-you / operator-before-you
relationship.

This file also lands the operator-approved POSITIVE REALISM ANCHOR
test that runs across ALL major workflow families (daily-report,
incident, preop, checkout). It guarantees every family contains at
least one anchor phrase from the approved cultural-voice list. The
operator framed this as converting the tone discipline from "blocks
the bad" (iter211 robotic-OSHA banlist) to "guarantees the good".
"""
import os
import re
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)

CHECKOUT_FORM_KEYS = [
    "checkout",
    "checkout.condition",
    "checkout.signature",
    "checkout.return-expectations",
    "checkout.photos",
]


# ─────────────────────────────────────────────────────────────────────
# Coverage / structure tests
# ─────────────────────────────────────────────────────────────────────
def test_checkout_seed_count():
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    co = [t for t in all_tips()
          if t["form_key"] == "checkout"
          or t["form_key"].startswith("checkout.")]
    assert len(co) >= 12


def test_checkout_top_level_canonical_four_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=checkout", timeout=10.0,
    )
    kinds = {t["kind"] for t in r.json()["tips"]}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds


@pytest.mark.parametrize("form_key", CHECKOUT_FORM_KEYS)
def test_checkout_endpoint_anon_readable(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


@pytest.mark.parametrize("form_key", CHECKOUT_FORM_KEYS)
def test_checkout_tips_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


@pytest.mark.parametrize("form_key", CHECKOUT_FORM_KEYS)
def test_checkout_tips_concise(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


# Re-run the iter211 robotic-OSHA banlist on checkout content
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
    "the undersigned", "willful violation",
]


@pytest.mark.parametrize("form_key", CHECKOUT_FORM_KEYS)
def test_checkout_no_robotic_osha_tone(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} uses OSHA tone: {bad}"


def test_checkout_signature_includes_accountability_escalate():
    """The signature surface is the highest-stakes cultural-safety moment
    on the checkout form. There must be an 'escalate' tip teaching the
    'when NOT to sign' pattern."""
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=checkout.signature", timeout=10.0,
    )
    has_escalate = any(
        t["kind"] == "escalate"
        and any(p in (t.get("body") or "").lower() for p in ("sign", "supervisor", "stop"))
        for t in r.json()["tips"]
    )
    assert has_escalate, (
        "checkout.signature must include an 'escalate' tip for "
        "'when NOT to sign' coaching"
    )


# ─────────────────────────────────────────────────────────────────────
# POSITIVE REALISM ANCHOR TEST  (operator-approved iter211 → iter212)
# Cross-cutting test: every major workflow family must contain at least
# one anchor phrase from the approved cultural-voice list. This makes
# the cultural voice load-bearing in the test suite, not just an
# editorial intent.
# ─────────────────────────────────────────────────────────────────────
WORKFLOW_FAMILIES = ["daily-report", "incident", "preop", "checkout"]

# Approved anchor phrases by category. Matching is case-insensitive
# substring; ANY one match in the family clears that family.
POSITIVE_REALISM_ANCHORS = [
    # trust / accountability
    "trust", "trusted",
    "your word",
    "good faith",
    "honest", "honestly",
    "accountab",
    # operator-before / operator-after / crew-reliance
    "operator before you",
    "operator after you",
    "next operator",
    "crew", "crews",
    "your name is on it",
    "return the favor",
    "credit",
    "ownership",
    "signature is",
    "signature on",
    # operational integrity
    "integrity", "professional",
    # MASCI-specific operational realism (anti-corporate)
    "field", "site",
    "shop", "dispatch",
]


def _family_tips(family: str) -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [
        t for t in all_tips()
        if t["form_key"] == family or t["form_key"].startswith(f"{family}.")
    ]


@pytest.mark.parametrize("family", WORKFLOW_FAMILIES)
def test_workflow_family_contains_positive_realism_anchor(family):
    """Each workflow family must have at least one anchor phrase. This
    is the cultural-voice load-bearing assertion."""
    tips = _family_tips(family)
    assert tips, f"No tips registered for family {family!r}"

    # Concatenate all EN+ES bodies for the family (one big haystack)
    haystack = " ".join(
        (t.get("body") or "") + " " + (t.get("body_es") or "")
        for t in tips
    ).lower()

    # Find which anchors hit (for a useful failure message)
    hits = [a for a in POSITIVE_REALISM_ANCHORS if a.lower() in haystack]
    assert hits, (
        f"Family {family!r} contains NO positive-realism anchor phrase. "
        f"Approved anchors include: trust/accountability/your word/good faith/"
        f"honest/operator before you/crew/ownership/integrity/professional/"
        f"signature is. Tone-discipline directive enforces voice consistency."
    )


def test_positive_realism_anchor_strength_at_least_three_distinct():
    """Across the platform, the cultural-voice surface area should be
    rich enough that at least 3 DIFFERENT anchor phrases appear (not
    one phrase repeated everywhere)."""
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    haystack = " ".join(
        (t.get("body") or "") + " " + (t.get("body_es") or "")
        for t in all_tips()
    ).lower()
    distinct_hits = {a for a in POSITIVE_REALISM_ANCHORS if a.lower() in haystack}
    assert len(distinct_hits) >= 3, (
        f"Only {len(distinct_hits)} distinct cultural-voice anchors land "
        f"across the registry: {distinct_hits}. The voice should be diverse."
    )


# Sanity: the anchor list itself must contain at least one phrase per
# operator-stated category — guards against the list silently shrinking.
def test_anchor_list_covers_all_approved_categories():
    categories_present = {
        "trust": any("trust" in a for a in POSITIVE_REALISM_ANCHORS),
        "accountability": any("accountab" in a for a in POSITIVE_REALISM_ANCHORS),
        "good-faith": any("good faith" in a for a in POSITIVE_REALISM_ANCHORS),
        "crew-reliance": any(re.search(r"\bcrew", a) for a in POSITIVE_REALISM_ANCHORS),
        "integrity": any("integrity" in a for a in POSITIVE_REALISM_ANCHORS),
    }
    missing = [k for k, v in categories_present.items() if not v]
    assert not missing, f"Anchor list missing operator-stated categories: {missing}"
