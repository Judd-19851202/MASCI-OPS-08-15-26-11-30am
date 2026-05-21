"""
iter317-B · Field Leadership guidance article convergence.

Locks the surgical refresh delivered in iter317-B:

  • 4 stale FL articles refreshed with "Which door do I use?"
    disambiguation at the top:
        portal-leadership
        onboard-leadership-first-week
        tshoot-leadership-login
        portal-leadership-identity

  • 1 new article added:
        portal-field-leadership-portal-accounts

  • Every refreshed/new article references the per-user portal URL
    `/field-leadership/portal/login` (operational door) AND the
    legacy shared-password gate `/field-leadership/login` (read-only
    crew documents door) — the explicit two-doors disambiguation is
    the iter317-B operational goal.

  • Bilingual parity — every refreshed/new article carries EN body
    blocks AND ES body_es blocks; ES blocks carry the equivalent
    "¿Cuál puerta uso?" / "dos puertas" disambiguation.

  • iter317-A `field-leadership.portal-login` coaching family remains
    intact (no drift introduced by iter317-B's article refresh).

  • No new article IDs collide with the legacy article IDs; no
    duplicate article IDs anywhere in `content.py`.

Static-code invariants only; pulls articles via the same
`guidance` module the live FastAPI route uses, so the lock matches
what users actually receive at runtime.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT = REPO_ROOT / "backend/guidance/content.py"
TRANS_ES = REPO_ROOT / "backend/guidance/translations_es.py"
TRANS_ES_279 = REPO_ROOT / "backend/guidance/translations_es_iter279.py"


REFRESHED_IDS = (
    "portal-leadership",
    "onboard-leadership-first-week",
    "tshoot-leadership-login",
    "portal-leadership-identity",
)
NEW_ID = "portal-field-leadership-portal-accounts"
ALL_IDS = REFRESHED_IDS + (NEW_ID,)


def _load_articles():
    """Same merged dict the FastAPI route serves."""
    import sys
    backend_dir = str(REPO_ROOT / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from guidance import _articles_by_id
    return _articles_by_id


def _body_text(blocks):
    parts = []
    for b in blocks or []:
        if isinstance(b, dict):
            if b.get("text"):
                parts.append(str(b["text"]))
            for it in (b.get("items") or []):
                parts.append(str(it))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Existence + ID hygiene.
# ---------------------------------------------------------------------------


def test_iter317b_all_five_articles_present():
    articles = _load_articles()
    for aid in ALL_IDS:
        assert aid in articles, f"iter317-B article missing: {aid}"


def test_iter317b_no_duplicate_article_ids_in_content_module():
    src = CONTENT.read_text()
    # Count unique-quoted "id": "<id>" appearances per id.
    for aid in ALL_IDS:
        marker = f'"id": "{aid}"'
        count = src.count(marker)
        assert count == 1, (
            f"article id {aid!r} appears {count} times in content.py — "
            "iter317-B must not introduce duplicates"
        )


# ---------------------------------------------------------------------------
# Two-doors disambiguation — operational goal of iter317-B.
# ---------------------------------------------------------------------------


def test_iter317b_articles_carry_two_doors_disambiguation_en():
    articles = _load_articles()
    for aid in ALL_IDS:
        text = _body_text(articles[aid].get("body"))
        # Each refreshed/new article must mention BOTH the per-user
        # portal URL and the legacy gate URL.
        assert "/field-leadership/portal/login" in text, (
            f"{aid}: EN body must reference the per-user portal URL"
        )
        assert "/field-leadership/login" in text, (
            f"{aid}: EN body must still acknowledge the legacy gate URL "
            "for door disambiguation"
        )
        # And carry an explicit "which door" / "two doors" phrasing.
        has_marker = (
            "Which door do I use" in text
            or "two Field Leadership doors" in text
            or "Two valid doors" in text
            or "Which door am I at" in text
        )
        assert has_marker, (
            f"{aid}: EN body missing the iter317-B two-doors "
            "disambiguation marker"
        )


def test_iter317b_articles_carry_two_doors_disambiguation_es():
    articles = _load_articles()
    for aid in ALL_IDS:
        text_es = _body_text(articles[aid].get("body_es"))
        assert text_es, f"{aid}: missing body_es — bilingual parity gap"
        assert "/field-leadership/portal/login" in text_es, (
            f"{aid}: ES body must reference the per-user portal URL"
        )
        assert "/field-leadership/login" in text_es, (
            f"{aid}: ES body must still acknowledge the legacy gate URL"
        )
        has_marker_es = (
            "¿Cuál puerta uso" in text_es
            or "dos puertas" in text_es.lower()
            or "¿En cuál puerta" in text_es
            or "dos puertas válidas" in text_es.lower()
        )
        assert has_marker_es, (
            f"{aid}: ES body missing the iter317-B two-doors "
            "disambiguation marker"
        )


# ---------------------------------------------------------------------------
# Tone discipline — operator-mandated banned phrasing.
# ---------------------------------------------------------------------------


BANNED_PHRASES = (
    "best practices",
    "empower",
    "journey",
    "stakeholders",
    "culture of",
    "training module",
    "compliance posture",
    "learning experience",
)


def test_iter317b_articles_pass_tone_discipline_scan():
    """No LMS/corporate-training/compliance-suite drift in the
    refreshed or new articles."""
    articles = _load_articles()
    hits = []
    for aid in ALL_IDS:
        body_en = _body_text(articles[aid].get("body")).lower()
        body_es = _body_text(articles[aid].get("body_es")).lower()
        for banned in BANNED_PHRASES:
            if banned in body_en:
                hits.append((aid, "EN", banned))
            if banned in body_es:
                hits.append((aid, "ES", banned))
    assert not hits, f"iter317-B tone discipline failure: {hits}"


# ---------------------------------------------------------------------------
# Stale-reference scan — every remaining `/leadership/login` mention
# in the refreshed articles must now appear NEAR a clarification.
# ---------------------------------------------------------------------------


def test_iter317b_no_orphaned_legacy_url_in_refreshed_articles():
    """The legacy `/field-leadership/login` URL may still appear (it
    is a real, supported door), but it must NEVER appear in an
    article that does not ALSO mention the per-user portal URL.
    That's the whole iter317-B disambiguation contract."""
    articles = _load_articles()
    for aid in ALL_IDS:
        body_en = _body_text(articles[aid].get("body"))
        if "/field-leadership/login" in body_en:
            assert "/field-leadership/portal/login" in body_en, (
                f"{aid}: EN body mentions legacy gate without also "
                "mentioning the per-user portal"
            )
        body_es = _body_text(articles[aid].get("body_es"))
        if "/field-leadership/login" in body_es:
            assert "/field-leadership/portal/login" in body_es, (
                f"{aid}: ES body mentions legacy gate without also "
                "mentioning the per-user portal"
            )


# ---------------------------------------------------------------------------
# Related-article wiring.
# ---------------------------------------------------------------------------


def test_iter317b_new_article_linked_from_refreshed_articles():
    """The new `portal-field-leadership-portal-accounts` article
    must be reachable from each of the refreshed articles via the
    `related` list — so users following the Guidance Center can
    discover it."""
    articles = _load_articles()
    new_art = articles[NEW_ID]
    # The new article itself must `related`-link to all four
    # refreshed articles.
    new_related = set(new_art.get("related") or [])
    for aid in REFRESHED_IDS:
        assert aid in new_related, (
            f"{NEW_ID}: must `related`-link to {aid}"
        )
    # And each of the refreshed articles must `related`-link to
    # the new article so the navigation works the other direction
    # too. Iter317-B explicitly edited the `related` lists.
    for aid in REFRESHED_IDS:
        related = set(articles[aid].get("related") or [])
        assert NEW_ID in related, (
            f"{aid}: `related` must include {NEW_ID} so users can "
            "find the per-user portal walkthrough"
        )


# ---------------------------------------------------------------------------
# Scope discipline — the new article must be public (readable BEFORE
# login), matching the operator-mandate that confused Supers/Foremen
# should be able to find the answer before they sign in.
# ---------------------------------------------------------------------------


def test_iter317b_new_article_is_public_scope():
    articles = _load_articles()
    scopes = articles[NEW_ID].get("scopes") or []
    assert "public" in scopes, (
        "portal-field-leadership-portal-accounts must be `public` "
        "scope so confused users can read it before they sign in"
    )


# ---------------------------------------------------------------------------
# Coaching-family non-regression — iter317-A families must remain
# intact; the article refresh must not have disturbed them.
# ---------------------------------------------------------------------------


def test_iter317b_does_not_touch_iter317a_coaching_families():
    """iter317-A added 5 coaching families; iter317-B is articles-only.
    Confirm the coaching block is still present in tips.py."""
    src = (REPO_ROOT / "backend/guidance/tips.py").read_text()
    for fk in (
        "field-leadership.portal-login",
        "field-leadership.portal-dashboard",
        "field-leadership.change-password",
        "field-leadership.user-management",
        "field-leadership.dispatch-visibility",
    ):
        assert f'"form_key": "{fk}"' in src, (
            f"iter317-A family {fk} appears to have been disturbed"
        )


# ---------------------------------------------------------------------------
# Block-marker for grep discoverability.
# ---------------------------------------------------------------------------


def test_iter317b_marker_comments_present():
    en_src = CONTENT.read_text()
    es_src = TRANS_ES.read_text()
    es_iter279_src = TRANS_ES_279.read_text()
    assert "iter317-B" in en_src, "content.py must keep an iter317-B marker"
    assert "iter317-B" in es_src, "translations_es.py must keep an iter317-B marker"
    assert "iter317-B" in es_iter279_src, (
        "translations_es_iter279.py must keep an iter317-B marker"
    )
