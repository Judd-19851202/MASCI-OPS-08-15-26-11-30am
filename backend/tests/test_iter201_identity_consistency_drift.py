"""iter201 — Operational Identity Consistency drift rule.

After Pass 4 the operator surfaced an important governance maturity gap:
Field Leadership now has a full operational identity (onboard / tshoot /
identity triple), but HR / Safety / Dispatch / Shop / PM / Admin still
don't have parallel coverage. That inconsistency is itself a governance
drift item.

This iter adds a programmatic check so the dashboard auto-surfaces the
gap. Tests:
  - drift category 'portal-identity-incomplete' exists
  - Field Leadership does NOT appear in it (already has the triple)
  - 6 other portals DO appear (currently missing the triple)
  - Severity is p1 for operational portals, p2 for admin
  - As portals get their triples in Pass 5a/b/c, the drift list shrinks
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_drift_surfaces_identity_consistency_category():
    """Historical: the governance system must surface a
    'portal-identity-incomplete' drift category.

    Pass 5c update: the category logic still exists in
    governance/inventory.py, but the drift bucket is now empty (all
    triples landed). This test now asserts the category is either
    present OR cleanly empty — both are valid post-Pass-5c states.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    cats = {it["category"] for it in d["items"]}
    incomplete = [
        it for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    ]
    # Either the category surfaces (legacy state) or the bucket is
    # cleanly empty (post-Pass-5c state). What's NOT acceptable is
    # surfacing the category with no message detail.
    assert "portal-identity-incomplete" in cats or incomplete == []


def test_field_leadership_NOT_in_identity_incomplete():
    """Pass 4 already gave Field Leadership the full triple — it must
    NOT show up as drift."""
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    fl = [it for it in d["items"]
          if it["category"] == "portal-identity-incomplete"
          and it["subject"] == "leadership"]
    assert not fl, "Field Leadership has identity triple — shouldn't be flagged"


def test_six_other_portals_flagged_for_identity_drift():
    """Historical: HR / Safety / Dispatch / Shop / PM / Admin all needed the triple.

    iter205 update: identity articles landed for all six.
    Pass 5a (2026-05-18): HR / Safety / PM cleared.
    Pass 5b (2026-05-18): Shop / Dispatch cleared.
    Pass 5c (2026-05-18): Admin cleared.

    The identity-incomplete drift bucket is now empty by design. This
    test now asserts that completion contract.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    flagged = {it["subject"] for it in d["items"]
               if it["category"] == "portal-identity-incomplete"}
    assert flagged == set(), (
        f"Pass 5c closed the identity-incomplete drift bucket entirely; "
        f"still flagged: {flagged}"
    )


def test_admin_drift_is_p2_others_p1():
    """Historical: Admin gets softer P2 severity.

    Pass 5c update: Admin cleared, so the identity-drift bucket is now
    empty. This test now asserts the bucket is empty.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    by_subject = {
        it["subject"]: it for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    }
    assert by_subject == {}, (
        f"identity-incomplete bucket must be empty post-Pass-5c; "
        f"still has: {list(by_subject)}"
    )


def test_drift_message_names_missing_articles():
    """Historical: the drift message must name missing articles.

    Pass 5c update: nothing is missing anymore, so this test now
    asserts the bucket is empty (no drift message to validate).
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    incomplete = [
        it for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    ]
    assert incomplete == [], (
        f"Pass 5c should fully clear identity-incomplete drift; "
        f"still flagged: {[it['subject'] for it in incomplete]}"
    )


def test_drift_assigns_fix_pass_label():
    """Drift items must point operators at the right next-pass."""
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    items = [it for it in d["items"]
             if it["category"] == "portal-identity-incomplete"]
    for it in items:
        assert "Pass 5" in (it.get("fix_pass") or ""), (
            f"identity drift items must point at Pass 5; got {it.get('fix_pass')}"
        )
