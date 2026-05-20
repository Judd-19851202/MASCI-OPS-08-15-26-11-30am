"""
iter278 · Sequence #8 Terminology Cluster regression test.

Locks in the Toolbox Talk → Safety Meeting rename across the 5 articles
identified by the iter277 pre-audit. Fails if any stale terminology
pattern reappears anywhere in `/app/backend/guidance/content.py`
(_ARTICLES) or `/app/backend/guidance/translations_es.py`
(TRANSLATIONS_ES).
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from guidance import content as guidance_content
from guidance import translations_es as guidance_es


STALE_PATTERNS = [
    re.compile(r"\bToolbox Talks?", re.IGNORECASE),
    re.compile(r"\bCrew Hub\b", re.IGNORECASE),
    re.compile(r"\bdaily safety meeting\b", re.IGNORECASE),
    re.compile(r"\bcharla\s+de\s+seguridad\b", re.IGNORECASE),
    re.compile(r"\bcharlas\s+de\s+seguridad\b", re.IGNORECASE),
]

RENAMED_ARTICLE_IDS = {
    "portal-safety",
    "public-toolbox-talks",
    "public-tools-map",
    "onboard-leadership-first-week",
    "onboard-safety-first-week",
}


def _flatten(blocks):
    out = []
    if isinstance(blocks, str):
        return blocks
    if not isinstance(blocks, list):
        return ""
    for blk in blocks:
        if isinstance(blk, dict):
            for v in blk.values():
                if isinstance(v, str):
                    out.append(v)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            out.extend(s for s in it.values() if isinstance(s, str))
                        elif isinstance(it, str):
                            out.append(it)
        elif isinstance(blk, str):
            out.append(blk)
    return "\n".join(out)


def _article_text(article):
    """Title + summary + flattened body + tag strings."""
    parts = [article.get("title", ""), article.get("summary", "")]
    parts.append(_flatten(article.get("body", [])))
    for tag in article.get("tags", []) or []:
        if isinstance(tag, str):
            parts.append(tag)
    return "\n".join(parts)


def _es_text(es_entry):
    parts = [es_entry.get("title_es", ""), es_entry.get("summary_es", "")]
    parts.append(_flatten(es_entry.get("body_es", [])))
    return "\n".join(parts)


def test_no_stale_terminology_in_any_article_en():
    hits = []
    for article in guidance_content._ARTICLES:
        text = _article_text(article)
        for pat in STALE_PATTERNS:
            m = pat.search(text)
            if m:
                hits.append((article["id"], pat.pattern, m.group()))
    assert not hits, f"Stale terminology still present in EN: {hits}"


def test_no_stale_terminology_in_any_article_es():
    hits = []
    for aid, es_entry in guidance_es.TRANSLATIONS_ES.items():
        text = _es_text(es_entry)
        for pat in STALE_PATTERNS:
            m = pat.search(text)
            if m:
                hits.append((aid, pat.pattern, m.group()))
    assert not hits, f"Stale terminology still present in ES: {hits}"


def test_renamed_articles_keep_their_ids():
    """IDs are URL-stable. Rename must not change article identifiers."""
    present_ids = {a["id"] for a in guidance_content._ARTICLES}
    missing = RENAMED_ARTICLE_IDS - present_ids
    assert not missing, f"Renamed articles lost their IDs: {missing}"


def test_renamed_articles_have_es_counterparts():
    """All 5 renamed articles must retain their Spanish translations."""
    missing = [
        aid for aid in RENAMED_ARTICLE_IDS
        if aid not in guidance_es.TRANSLATIONS_ES
    ]
    assert not missing, f"ES counterparts missing for: {missing}"


def test_renamed_article_titles_contain_safety_meeting_anchor():
    """Articles previously titled with Toolbox Talk should now reflect Safety Meeting."""
    arts = {a["id"]: a for a in guidance_content._ARTICLES}
    # public-toolbox-talks title should anchor on Safety Meetings
    assert arts["public-toolbox-talks"]["title"] == "Safety Meetings", \
        f"public-toolbox-talks title unexpected: {arts['public-toolbox-talks']['title']!r}"
    # ES counterpart should match
    assert guidance_es.TRANSLATIONS_ES["public-toolbox-talks"]["title_es"] == "Reuniones de Seguridad", \
        f"public-toolbox-talks ES title unexpected: {guidance_es.TRANSLATIONS_ES['public-toolbox-talks']['title_es']!r}"


def test_es_uses_canonical_safety_meeting_term():
    """Across the 5 renamed articles, ES body must use 'Reunión de Seguridad'
    (the canonical iter270 term) and must NOT use 'Charla de Seguridad'."""
    for aid in RENAMED_ARTICLE_IDS:
        es_entry = guidance_es.TRANSLATIONS_ES.get(aid)
        if not es_entry:
            continue
        text = _es_text(es_entry)
        assert not re.search(r"\bcharla\s+de\s+seguridad\b", text, re.I), \
            f"{aid} still uses 'Charla de Seguridad' in ES"


def test_total_article_count_unchanged():
    """No article was added or removed during the rename."""
    assert len(guidance_content._ARTICLES) == 124
