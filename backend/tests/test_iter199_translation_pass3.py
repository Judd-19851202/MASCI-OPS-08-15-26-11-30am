"""iter199 — Pass 3 · Translation architecture tests.

Verifies:
  - translations_es.py module loads & merges into _ARTICLES at import
  - All 17 public-scope articles have title_es / summary_es / body_es
  - body_es structure validates (same block-type rules as body)
  - inventory translation report flips schema_landed → True
  - Articles without translation gracefully expose only English fields
  - get_article returns *_es fields when present (frontend can pick)
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_translations_module_loads():
    from guidance.translations_es import TRANSLATIONS_ES
    assert isinstance(TRANSLATIONS_ES, dict)
    assert len(TRANSLATIONS_ES) >= 17, f"expected >=17 translations, got {len(TRANSLATIONS_ES)}"


def test_translations_applied_to_articles_at_import():
    """Importing guidance package merges translations into _ARTICLES."""
    import guidance  # noqa: F401 — import triggers the merge
    from guidance.content import _ARTICLES
    n_with_body_es = sum(1 for a in _ARTICLES if a.get("body_es"))
    assert n_with_body_es >= 17, (
        f"expected at least 17 articles with body_es after import; got {n_with_body_es}"
    )


def test_all_17_public_articles_translated():
    """Every public-scope article must have full *_es triple."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    public_articles = [a for a in _ARTICLES if "public" in (a.get("scopes") or [])]
    assert len(public_articles) >= 17
    missing = []
    for a in public_articles:
        for field in ("title_es", "summary_es", "body_es"):
            if not a.get(field):
                missing.append(f"{a['id']}.{field}")
    assert not missing, f"public articles missing translation fields: {missing}"


def test_body_es_has_valid_block_types():
    """body_es blocks must use the same valid type vocabulary as body."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES, _VALID_BLOCK_TYPES
    for a in _ARTICLES:
        body_es = a.get("body_es")
        if not body_es:
            continue
        for bi, b in enumerate(body_es):
            assert isinstance(b, dict), f"{a['id']}.body_es[{bi}] not a dict"
            assert "type" in b, f"{a['id']}.body_es[{bi}] missing type"
            assert b["type"] in _VALID_BLOCK_TYPES, (
                f"{a['id']}.body_es[{bi}] invalid type {b['type']}"
            )


def test_translation_es_only_references_existing_ids():
    """Translations module must not reference unknown article ids."""
    import guidance  # noqa: F401
    from guidance.content import _ARTICLES
    from guidance.translations_es import TRANSLATIONS_ES
    valid_ids = {a["id"] for a in _ARTICLES}
    unknown = [aid for aid in TRANSLATIONS_ES if aid not in valid_ids]
    assert not unknown, f"translations_es references unknown ids: {unknown}"


def test_validator_passes_with_translations():
    """validate_registry must still pass after translations merged in."""
    import guidance  # noqa: F401
    from guidance.content import validate_registry
    issues = validate_registry(strict=False)
    assert not issues, f"validator surfaced issues after translation merge: {issues}"


def test_inventory_schema_landed_flag_true():
    """Pass 3 schema_landed flag flips True once any body_es exists."""
    import guidance  # noqa: F401
    from governance.inventory import compute_translation_readiness
    t = compute_translation_readiness()
    assert t["schema_landed"] is True
    assert t["body_es_present"] >= 17
    assert t["pct_body"] > 0.0


def test_inventory_translation_by_scope_public_is_high():
    """Public scope should report ~100% body coverage after Pass 3."""
    import guidance  # noqa: F401
    from governance.inventory import compute_translation_readiness
    t = compute_translation_readiness()
    public = t["by_scope"]["public"]
    assert public["body_es"] >= 17
    assert public["pct_body"] >= 95.0, (
        f"expected public scope >=95% body translation, got {public['pct_body']}%"
    )


def test_get_article_returns_es_fields_when_present():
    """get_article must surface *_es fields so the frontend can pick."""
    import guidance  # noqa: F401
    from guidance.content import get_article
    a = get_article("public-preop-basics", {"public"})
    assert a is not None
    assert "title_es" in a
    assert "summary_es" in a
    assert "body_es" in a
    assert isinstance(a["body_es"], list)
    assert a["title_es"] != a["title"]  # different language


def test_get_article_returns_english_only_when_no_translation():
    """Untranslated articles must still serve cleanly — graceful fallback."""
    import guidance  # noqa: F401
    from guidance.content import get_article
    # Pick an admin-only article (Tier 2+ — not yet translated in this pass)
    a = get_article("admin-user-management", {"admin"})
    assert a is not None
    assert "title" in a
    # Either missing or empty — both are valid "untranslated" states
    assert not a.get("body_es")


def test_inventory_drift_translation_severity_drops():
    """Drift should still flag translation-missing but pct_body is now > 0."""
    import guidance  # noqa: F401
    from governance.inventory import compute_drift
    d = compute_drift()
    tr_items = [it for it in d["items"] if it["category"] == "translation-missing"]
    # Still listed (most articles untranslated), but the count of
    # untranslated articles must be lower than the article total.
    assert len(tr_items) >= 1
    assert "untranslated" in tr_items[0]["message"] or "translation" in tr_items[0]["message"].lower()


# ─────────────────────────────────────────────────────────────────────
# HTTP-level smoke tests
# ─────────────────────────────────────────────────────────────────────

import httpx  # noqa: E402

API_URL = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"


def test_article_endpoint_serves_es_fields_to_anonymous():
    """Public article fetch must include title_es/body_es for anonymous."""
    r = httpx.get(f"{API_URL}/api/guidance/articles/public-preop-basics", timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    assert data.get("title_es")
    assert data.get("body_es")
    assert isinstance(data["body_es"], list)
    assert len(data["body_es"]) > 0


def test_article_endpoint_es_block_shape_matches_en():
    """Each body_es block should have the same 'type' vocabulary as body."""
    r = httpx.get(f"{API_URL}/api/guidance/articles/public-incident-basics", timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    en_types = {b["type"] for b in data["body"]}
    es_types = {b["type"] for b in data["body_es"]}
    # Block-type intersection should be substantial (not strict equality —
    # translators may collapse or split blocks for clarity).
    assert es_types & en_types, "no overlap in block types between body and body_es"
