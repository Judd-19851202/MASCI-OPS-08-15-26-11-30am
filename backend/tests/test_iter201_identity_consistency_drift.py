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
    """HR / Safety / Dispatch / Shop / PM / Admin all need the triple.

    iter205 update: identity articles landed for all six.
    Pass 5a (2026-05-18) update: HR / Safety / PM cleared the full
    triple (identity + onboard-first-week + tshoot-login). Only Shop /
    Dispatch / Admin remain as drift until Pass 5b/5c land their
    onboard + tshoot articles.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    flagged = {it["subject"] for it in d["items"]
               if it["category"] == "portal-identity-incomplete"}
    for portal in ("shop", "dispatch", "admin"):
        assert portal in flagged, (
            f"Portal '{portal}' must still be flagged for identity drift "
            f"until Pass 5b/5c builds its triple; currently flagged: {flagged}"
        )
    for portal in ("hr", "safety", "pm"):
        assert portal not in flagged, (
            f"Portal '{portal}' cleared in Pass 5a — must NOT be in drift; "
            f"currently flagged: {flagged}"
        )


def test_admin_drift_is_p2_others_p1():
    """Admin gets softer P2 severity. Shop / Dispatch remain P1.

    HR / Safety / PM cleared the triple in Pass 5a and are no longer
    in the identity-drift set.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    by_subject = {
        it["subject"]: it for it in d["items"]
        if it["category"] == "portal-identity-incomplete"
    }
    assert by_subject["admin"]["severity"] == "p2"
    for portal in ("shop", "dispatch"):
        assert by_subject[portal]["severity"] == "p1", (
            f"{portal} should be P1; got {by_subject[portal]['severity']}"
        )


def test_drift_message_names_missing_articles():
    """The drift message must tell the operator exactly which articles
    to create — otherwise it's noise, not signal.

    iter205 update: identity articles landed; message no longer names them.
    Pass 5a update: HR / Safety / PM cleared. The check now pivots to
    Shop (still incomplete) to validate the drift-message contract.
    """
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    shop_drift = next(
        (it for it in d["items"]
         if it["category"] == "portal-identity-incomplete"
         and it["subject"] == "shop"),
        None,
    )
    assert shop_drift is not None
    assert "onboard-shop-first-week" in shop_drift["message"]
    assert "tshoot-shop-login" in shop_drift["message"]
    assert "portal-shop-identity" not in shop_drift["message"]


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
