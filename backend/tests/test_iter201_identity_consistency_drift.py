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
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    cats = {it["category"] for it in d["items"]}
    assert "portal-identity-incomplete" in cats


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
    """HR / Safety / Dispatch / Shop / PM / Admin all need the triple."""
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    flagged = {it["subject"] for it in d["items"]
               if it["category"] == "portal-identity-incomplete"}
    for portal in ("hr", "safety", "shop", "dispatch", "pm", "admin"):
        assert portal in flagged, (
            f"Portal '{portal}' must be flagged for identity drift "
            f"until Pass 5 builds its triple; currently flagged: {flagged}"
        )


def test_admin_drift_is_p2_others_p1():
    """Admin gets softer P2 severity — its 'first-week' is internal,
    less field-driven. All other operational portals are P1."""
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    by_subject = {
        it["subject"]: it for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    }
    assert by_subject["admin"]["severity"] == "p2"
    for portal in ("hr", "safety", "shop", "dispatch", "pm"):
        assert by_subject[portal]["severity"] == "p1", (
            f"{portal} should be P1; got {by_subject[portal]['severity']}"
        )


def test_drift_message_names_missing_articles():
    """The drift message must tell the operator exactly which articles
    to create — otherwise it's noise, not signal.

    iter205 update: portal-<persona>-identity articles were authored as
    part of the Tiered Guidance RBAC pass, so they are no longer
    missing. The triple still surfaces drift for the remaining two
    pieces (onboard-* and tshoot-*) until Pass 5a/5b/5c land them.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    hr_drift = next(
        (it for it in d["items"]
         if it["category"] == "portal-identity-incomplete"
         and it["subject"] == "hr"),
        None,
    )
    assert hr_drift is not None
    assert "onboard-hr-first-week" in hr_drift["message"]
    assert "tshoot-hr-login" in hr_drift["message"]
    # iter205 — identity article landed; message must NOT name it as missing
    assert "portal-hr-identity" not in hr_drift["message"]


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
