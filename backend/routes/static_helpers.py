"""
routes/static_helpers.py — iter437 · Phase IV-BETA.5A-P6 · Safe route extraction (phase 2).

Lifts pure public utility helpers out of `server.py`. These endpoints
share three properties that make them the safest possible extraction
candidates:

  • Stateless — no DB reads, no DB writes, no scheduler dependency.
  • No authentication required — already public surfaces in production.
  • Bounded input — every parameter is length-clamped before use.

Extracted endpoints:

  GET /api/qr.svg
    Public QR-code generator. Returns an SVG-encoded QR for `data`.
    Used by the Training Scan-&-Go posters and any UI that wants to
    inline a QR without shipping a JS library. Cached 24h — the input
    is always a stable public URL so it's safe to cache hard.

The implementation is verbatim from server.py to keep external
behaviour byte-identical. Any future utility routes can land here too
(this is the safest landing zone for public read-only helpers).
"""
from __future__ import annotations

import io

import segno  # type: ignore
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response


def build_static_helpers_router() -> APIRouter:
    router = APIRouter(prefix="/api", tags=["static-helpers"])

    @router.get("/qr.svg")
    async def qr_svg(data: str, scale: int = 6):
        """Public QR-code generator. Returns an SVG-encoded QR for `data`.
        Used by the Training Scan-&-Go posters (and anywhere else the UI
        wants to inline a QR without shipping a JS library). Cached for
        24h — the input is always a stable public URL so it's safe to
        cache hard."""
        if not data or len(data) > 2048:
            raise HTTPException(400, "data query param required (1-2048 chars)")
        scale = max(2, min(int(scale or 6), 20))
        qr = segno.make(data, error="m")
        buf = io.BytesIO()
        qr.save(
            buf,
            kind="svg",
            scale=scale,
            dark="#0F172A",
            light=None,
            border=2,
            xmldecl=False,
        )
        return Response(
            content=buf.getvalue(),
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    return router


__all__ = ["build_static_helpers_router"]
