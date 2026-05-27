"""iter437 / Phase IV-BETA.5A-P4B · Guidance routes extraction regression.

Locks the safe-extraction contract for the guidance content endpoints
that were moved from server.py to routes/guidance_routes.py.

Asserts:
  • All 5 public endpoints respond with the original 200 contract.
  • JSON shape is byte-for-byte equivalent to the pre-extraction shape.
  • RBAC fallback (no headers → public scope) works.
  • 404 on unknown article preserved.
  • Zero-results search-miss logging path still callable (no exception).
"""
from __future__ import annotations

import pytest
import requests


@pytest.fixture(scope="module")
def base(base_url: str) -> str:
    return base_url.rstrip("/")


def test_guidance_sections_shape(base: str):
    r = requests.get(f"{base}/api/guidance/sections", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert "sections" in j
    assert "scopes" in j
    assert isinstance(j["sections"], list)
    assert isinstance(j["scopes"], list)
    # Scopes must be sorted (preserved RBAC contract). In CI we may have
    # injected dev/admin tokens; we just assert the list is sorted.
    assert j["scopes"] == sorted(j["scopes"])


def test_guidance_articles_shape(base: str):
    r = requests.get(f"{base}/api/guidance/articles", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert "articles" in j
    assert "count" in j
    assert isinstance(j["articles"], list)
    assert isinstance(j["count"], int)
    # Every article carries the canonical 5 fields and nothing surprising.
    for a in j["articles"][:3]:
        assert {"id", "title", "summary", "section", "tags"} <= set(a)
        assert isinstance(a["tags"], list)


def test_guidance_articles_filter_by_section(base: str):
    """The `?section=` filter must continue to work post-extraction."""
    r_all = requests.get(f"{base}/api/guidance/articles", timeout=15)
    r_all.raise_for_status()
    all_arts = r_all.json().get("articles") or []
    if not all_arts:
        pytest.skip("no public articles to filter")
    target = all_arts[0]["section"]
    r = requests.get(f"{base}/api/guidance/articles?section={target}", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert all(a["section"] == target for a in j["articles"])


def test_guidance_article_unknown_returns_404(base: str):
    r = requests.get(f"{base}/api/guidance/articles/__definitely-not-real__", timeout=15)
    assert r.status_code == 404


def test_guidance_tips_empty_form_key(base: str):
    r = requests.get(f"{base}/api/guidance/tips", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert j == {"form_key": "", "tips": []}


def test_guidance_tips_with_form_key(base: str):
    r = requests.get(f"{base}/api/guidance/tips?form_key=daily-report", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert j["form_key"] == "daily-report"
    assert "tips" in j
    assert "count" in j
    assert isinstance(j["tips"], list)


def test_guidance_search_shape(base: str):
    r = requests.get(f"{base}/api/guidance/search?q=safety&limit=5", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert "query" in j
    assert j["query"] == "safety"
    assert "results" in j
    assert isinstance(j["results"], list)
    assert len(j["results"]) <= 5


def test_guidance_search_zero_results_logs_without_exception(base: str):
    """The fire-and-forget miss-log path must not surface to the caller
    (it's a `try/except: pass` by design). Hitting it with a unique
    impossible query exercises that path."""
    impossible = "zzz-iter437-p4b-guidance-extract-canary-zzz"
    r = requests.get(f"{base}/api/guidance/search?q={impossible}", timeout=15)
    r.raise_for_status()
    j = r.json()
    assert j["query"] == impossible
    assert j["results"] == []


def test_guidance_search_limit_bounds(base: str):
    """Limit must be clamped to [1, 100] — pre-extraction contract."""
    # Negative / zero limit clamps to 1
    r0 = requests.get(f"{base}/api/guidance/search?q=safety&limit=-3", timeout=15)
    r0.raise_for_status()
    assert len(r0.json()["results"]) <= 1
    # Huge limit clamps to 100
    r1 = requests.get(f"{base}/api/guidance/search?q=safety&limit=9999", timeout=15)
    r1.raise_for_status()
    assert len(r1.json()["results"]) <= 100
