"""
routes/guidance_routes.py — iter437 · Phase IV-BETA.5A-P4B · Safe route extraction.

Lifts the FIVE PUBLIC read-only guidance content endpoints out of
server.py so the file shrinks gradually without behavioural change:

  GET /api/guidance/sections
  GET /api/guidance/articles
  GET /api/guidance/articles/{article_id}
  GET /api/guidance/tips
  GET /api/guidance/search

Doctrine:
  • Identical JSON contract to the in-server.py originals (byte-for-byte
    payload shape).
  • Same RBAC contract — caller scopes are computed by an injected
    `caller_scopes` helper, mirroring the `build_training_center_router`
    pattern already in use.
  • No DB writes except the fire-and-forget zero-results log on
    `/guidance/search` (preserved verbatim).
  • Admin coverage routes (`/api/admin/guidance/*`) intentionally
    NOT moved — they belong to a different governance domain and are
    already lined up for a future admin-routes extraction.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)


def build_guidance_router(
    db,
    caller_scopes: Callable[[Request], Awaitable[set]],
) -> APIRouter:
    """Build the guidance router.

    Args:
        db: Motor AsyncIOMotorDatabase — used only for the fire-and-forget
            `guidance_search_misses` log.
        caller_scopes: Async function `(Request) -> set` returning the
            caller's RBAC scope set (see server.py::_guidance_caller_scopes).
    """
    router = APIRouter(prefix="/api", tags=["guidance"])

    @router.get("/guidance/sections")
    async def guidance_sections(request: Request):
        """Operational Guidance Center — list visible sections + counts.
        RBAC: open endpoint; visibility filtered by caller's portal tokens."""
        from guidance.content import sections_for
        scopes = await caller_scopes(request)
        return {"sections": sections_for(scopes), "scopes": sorted(scopes)}

    @router.get("/guidance/articles")
    async def guidance_articles(request: Request, section: Optional[str] = None):
        """List visible articles (optionally filtered by section)."""
        from guidance.content import visible_articles
        scopes = await caller_scopes(request)
        rows = visible_articles(scopes)
        if section:
            rows = [a for a in rows if a.get("section") == section]
        return {
            "articles": [
                {"id": a["id"], "title": a["title"], "summary": a.get("summary"),
                 "section": a["section"], "tags": a.get("tags") or []}
                for a in rows
            ],
            "count": len(rows),
        }

    @router.get("/guidance/articles/{article_id}")
    async def guidance_article(article_id: str, request: Request):
        """Fetch a single article. Returns 404 if not visible to caller —
        a restricted title is never leaked to an unauthorized caller."""
        from guidance.content import get_article
        scopes = await caller_scopes(request)
        art = get_article(article_id, scopes)
        if not art:
            raise HTTPException(status_code=404, detail="Not found")
        return art

    @router.get("/guidance/tips")
    async def guidance_tips(request: Request, form_key: str = ""):
        """Return RBAC-filtered HelpTips for a form_key.

        `form_key` follows a dotted hierarchy (e.g. "daily-report.crew").
        A query for a leaf returns tips bound to the leaf AND tips bound
        to parent contexts ("daily-report"), so callers always get the
        broad + narrow coaching in one fetch.
        """
        from guidance.tips import tips_for
        if not form_key:
            return {"form_key": "", "tips": []}
        scopes = await caller_scopes(request)
        rows = tips_for(form_key.strip()[:120], scopes)
        return {"form_key": form_key, "tips": rows, "count": len(rows)}

    @router.get("/guidance/search")
    async def guidance_search(request: Request, q: str = "", limit: int = 25):
        """Title + body keyword match, RBAC-aware, no fuzzy (Phase A spec).

        Zero-results logging (iter193, operator-approved):
          • Logs query text + UTC timestamp + scope set when a non-empty
            query returns zero results.
          • Operational gap-intelligence ONLY — used to identify content
            gaps, terminology mismatches, onboarding pain.
          • No sensitive payload, no user identification, no IP — strictly
            a content-demand signal.
        """
        from guidance.content import search_articles
        scopes = await caller_scopes(request)
        safe_limit = max(1, min(int(limit or 25), 100))
        results = search_articles(q, scopes, limit=safe_limit)
        # Fire-and-forget zero-results logging (preserved verbatim).
        if q and (q.strip()) and not results:
            try:
                await db.guidance_search_misses.insert_one({
                    "query": q.strip()[:200],
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "scopes": sorted(scopes),
                })
            except Exception as e:  # noqa: BLE001
                logger.debug("guidance_search_misses insert failed: %s", e)
        return {"query": q, "results": results}

    return router


__all__ = ["build_guidance_router"]
