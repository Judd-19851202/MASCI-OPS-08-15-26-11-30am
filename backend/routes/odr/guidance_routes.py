"""
routes/odr/guidance_routes.py — Guidance Intelligence Foundation (deterministic).

Doctrine:
  /app/memory/ODR_COACHING_GUIDANCE_ADDENDUM.md (O36–O50)
  /app/memory/GUIDANCE_INTELLIGENCE_FOUNDATION.md (M0.2A)

Resolution path (NOT AI · fully deterministic):
  Crew Type → ODR Section → Prompt Key → Guidance Catalog → EN/ES output

API:
  GET  /api/odr/guidance/prompts                          list all prompt_keys
  GET  /api/odr/guidance/resolve                          resolve one (prompt_key,crew_type,lang)
  GET  /api/odr/guidance/catalog-health                   coverage stats
  GET  /api/odr/guidance/crew-readiness/{crew_type}       crew readiness matrix
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from .crew_readiness_matrix import CREW_READINESS_MATRIX
from .guidance_catalog import (
    CATALOG, CATALOG_CREW_TYPES, catalog_health,
    list_prompt_keys, resolve_prompt,
)


def build_odr_guidance_router(
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:

    router = APIRouter(prefix="/api/odr/guidance", tags=["odr-guidance"])

    @router.get("/prompts")
    async def get_prompts(
        _actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        keys = list_prompt_keys()
        return {
            "count": len(keys),
            "prompt_keys": keys,
            "sections": sorted({CATALOG[k].get("section", "") for k in keys}),
        }

    @router.get("/resolve")
    async def get_resolve(
        prompt_key: str = Query(...),
        crew_type: Optional[str] = Query(default=None),
        lang: str = Query(default="en", pattern="^(en|es)$"),
        _actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        if prompt_key not in CATALOG:
            raise HTTPException(404, f"Unknown prompt_key: {prompt_key}")
        bullets = resolve_prompt(prompt_key, crew_type=crew_type, lang=lang)
        entry = CATALOG[prompt_key]
        return {
            "prompt_key": prompt_key,
            "crew_type": crew_type,
            "lang": lang,
            "section": entry.get("section"),
            "severity": entry.get("severity"),
            "bullets": bullets,
            "applied_crew_overlay": bool(
                crew_type and (entry.get("crew_overrides") or {}).get(crew_type)
            ),
        }

    @router.get("/catalog-health")
    async def get_catalog_health(
        _actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        return catalog_health()

    @router.get("/crew-readiness/{crew_type}")
    async def get_crew_readiness(
        crew_type: str,
        _actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        if crew_type not in CREW_READINESS_MATRIX:
            raise HTTPException(404, f"No readiness matrix for crew_type={crew_type}")
        matrix = CREW_READINESS_MATRIX[crew_type]
        return {
            "crew_type": crew_type,
            "required": list(matrix.get("required", [])),
            "recommended": list(matrix.get("recommended", [])),
            "advanced": list(matrix.get("advanced", [])),
            "required_topic_count": len(matrix.get("required", [])),
        }

    @router.get("/crew-readiness")
    async def get_all_crew_readiness(
        _actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        return {
            "crews": sorted(CREW_READINESS_MATRIX.keys()),
            "universe": CATALOG_CREW_TYPES,
            "matrix": CREW_READINESS_MATRIX,
        }

    return router


__all__ = ["build_odr_guidance_router"]
