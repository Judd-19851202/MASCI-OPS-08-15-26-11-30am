"""
backend/guidance — Operational Guidance Center content + RBAC routes.

Phase A scope (preview only):
  • RBAC-aware content registry (in-code Python modules)
  • Server endpoints: catalog · article-by-id · search
  • Visibility computed server-side per request, based on the caller's
    portal tokens. Search and article-fetch refuse anything the caller
    cannot see; titles of restricted articles are NEVER leaked.

Pass 3 — Translation architecture
  • Spanish translations live in guidance/translations_es.py as a
    side-companion map (one entry per article id). At import time we
    merge title_es / summary_es / body_es into the matching article
    dict in _ARTICLES. Missing translations → graceful English fallback.
  • English remains canonical. Article IDs, scopes, tags, block types
    stay English. Only the human-readable strings get translated.

The frontend mirrors a static skeleton (cards / shell / section names)
but trusts THIS module as the source of truth for which articles
actually exist for the caller's tier set.
"""
from . import content as _content
from . import translations_es as _translations_es

# Merge Spanish translations into _ARTICLES at import time. Each entry
# in TRANSLATIONS_ES adds title_es / summary_es / body_es onto the
# matching article dict. Articles without translations remain English-
# only and will render with English text on either language toggle
# (graceful fallback policy — see translations_es.py header).
_articles_by_id = {a["id"]: a for a in _content._ARTICLES}
_translation_apply_count = 0
for _aid, _trans in _translations_es.TRANSLATIONS_ES.items():
    _article = _articles_by_id.get(_aid)
    if _article is None:
        # Unknown id in translations map — ignore silently. The inventory
        # dashboard surfaces this as drift if it becomes relevant.
        continue
    if "title_es" in _trans:
        _article["title_es"] = _trans["title_es"]
    if "summary_es" in _trans:
        _article["summary_es"] = _trans["summary_es"]
    if "body_es" in _trans:
        _article["body_es"] = _trans["body_es"]
    _translation_apply_count += 1

