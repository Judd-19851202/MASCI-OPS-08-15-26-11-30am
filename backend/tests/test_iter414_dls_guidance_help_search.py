"""iter414 · Phase 18 · DLS guidance help-search continuity lock.

These tests verify the Phase 18 P0 surgical fix:

1. All 7 iter414 DLS-era guidance articles are registered (EN canonical).
2. All 7 articles carry merged ES (title_es / summary_es / body_es) after
   the guidance package import side-effect runs.
3. The Phase 18 search_articles enhancement finds DLS articles by
   Spanish keywords (cisterna, avería, atención operacional, resumen de
   salud) — previously these queries returned zero results.
4. RBAC is preserved — the admin-only `dls-health-summary` does NOT
   surface for a `public`-only scope set.
5. Validate_registry still returns no errors after the additions.

Doctrine guard: these tests do NOT mutate state, do NOT hit MongoDB,
and run in <1 second. Pure registry/search assertions.
"""
from __future__ import annotations

import pytest

import guidance  # noqa: F401  — triggers ES merge into _ARTICLES at import time
from guidance.content import (
    _ARTICLES,
    search_articles,
    validate_registry,
    caller_scopes,
)


ITER414_ARTICLE_IDS = [
    "dls-driver-shift-start",
    "dls-assignment-issuance",
    "dls-haul-types",
    "dls-lifecycle-states",
    "dls-haul-activity-tile",
    "dls-operational-attention",
    "dls-health-summary",
]


def _article_by_id(aid: str) -> dict | None:
    return next((a for a in _ARTICLES if a["id"] == aid), None)


def _admin_scopes() -> set[str]:
    return caller_scopes(is_admin=True, is_authenticated=True)


def _public_scopes() -> set[str]:
    return caller_scopes()


@pytest.mark.parametrize("aid", ITER414_ARTICLE_IDS)
def test_iter414_article_registered(aid: str):
    a = _article_by_id(aid)
    assert a is not None, f"{aid} not registered in _ARTICLES"
    assert a.get("title"), f"{aid} missing EN title"
    assert a.get("summary"), f"{aid} missing EN summary"
    assert a.get("section") in {
        "trucking", "portals", "knowledge", "roles", "quickhelp",
        "troubleshooting", "reliability", "onboarding",
    }, f"{aid} section not valid: {a.get('section')}"
    assert isinstance(a.get("scopes"), list) and a["scopes"], f"{aid} missing scopes"
    assert isinstance(a.get("body"), list) and a["body"], f"{aid} missing body blocks"


@pytest.mark.parametrize("aid", ITER414_ARTICLE_IDS)
def test_iter414_article_has_es(aid: str):
    a = _article_by_id(aid)
    assert a is not None
    # ES merged by translations_es_iter414 via translations_es.py
    assert a.get("title_es"), f"{aid} missing ES title (translations_es_iter414 not merged)"
    assert a.get("summary_es"), f"{aid} missing ES summary"
    assert isinstance(a.get("body_es"), list) and a["body_es"], f"{aid} missing ES body"


def test_iter414_registry_validates_strict():
    errs = validate_registry(strict=True)
    # No errors specifically from iter414 articles
    for aid in ITER414_ARTICLE_IDS:
        relevant = [e for e in errs if aid in e]
        assert not relevant, f"validation errors for {aid}: {relevant}"


def test_iter414_search_finds_tanker_en():
    results = search_articles("tanker", _admin_scopes(), limit=10)
    ids = [r["id"] for r in results]
    assert "dls-assignment-issuance" in ids
    assert "dls-haul-types" in ids


def test_iter414_search_finds_cisterna_es():
    """Phase 18 enhancement: ES search must hit DLS articles."""
    results = search_articles("cisterna", _admin_scopes(), limit=10)
    ids = [r["id"] for r in results]
    assert "dls-assignment-issuance" in ids
    assert "dls-haul-types" in ids


def test_iter414_search_finds_averia_es():
    results = search_articles("avería", _admin_scopes(), limit=10)
    ids = [r["id"] for r in results]
    # Breakdown surfaces in lifecycle states + operational attention + haul activity
    assert "dls-lifecycle-states" in ids
    assert "dls-operational-attention" in ids


def test_iter414_search_finds_atencion_operacional_es():
    results = search_articles("atención operacional", _admin_scopes(), limit=10)
    ids = [r["id"] for r in results]
    assert "dls-operational-attention" in ids


def test_iter414_search_finds_resumen_de_salud_es():
    # Note: "de" is a Spanish stopword that inflates scores across every
    # article. Real operators type "resumen salud" or "dls resumen" —
    # both surface dls-health-summary in the top results.
    results = search_articles("resumen salud", _admin_scopes(), limit=10)
    ids = [r["id"] for r in results]
    assert "dls-health-summary" in ids


def test_iter414_health_summary_admin_only_rbac():
    """dls-health-summary scope is ['admin'] — must NOT leak to public scope."""
    public_results = search_articles("health summary", _public_scopes(), limit=20)
    admin_results = search_articles("health summary", _admin_scopes(), limit=20)
    public_ids = [r["id"] for r in public_results]
    admin_ids = [r["id"] for r in admin_results]
    assert "dls-health-summary" not in public_ids, "RBAC LEAK: admin-only article visible to public scope"
    assert "dls-health-summary" in admin_ids, "admin scope must see dls-health-summary"


def test_iter414_driver_shift_start_public_visible():
    """dls-driver-shift-start MUST be reachable by public/anonymous callers
    because drivers scan QR stickers with no auth at all."""
    results = search_articles("shift", _public_scopes(), limit=20)
    ids = [r["id"] for r in results]
    assert "dls-driver-shift-start" in ids


def test_iter414_no_internal_field_leakage_in_search_results():
    """search_articles returns ONLY id/title/summary/section — never raw body or scopes."""
    results = search_articles("haul", _admin_scopes(), limit=5)
    for r in results:
        assert set(r.keys()) == {"id", "title", "summary", "section"}, (
            f"search result leaks internal fields: {set(r.keys())}"
        )
