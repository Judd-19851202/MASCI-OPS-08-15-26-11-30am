"""iter437 / Phase IV-BETA.5A-P6 · Static helpers safe-route extraction.

Locks the behavioural parity contract for `/api/qr.svg` after the
extraction from server.py to routes/static_helpers.py.

Doctrine:
  • Pure public utility · no DB · no auth · no scheduler state
  • Bounded input (1-2048 chars · scale clamped to 2-20)
  • SVG content-type + 24h cache header preserved verbatim
  • Server.py shrinks net · zero behavioural change at the API edge
"""
from __future__ import annotations

import requests


def test_qr_svg_default_scale_returns_svg(base_url: str):
    """Happy path · public URL data, default scale 6 → SVG response."""
    r = requests.get(
        f"{base_url}/api/qr.svg",
        params={"data": "https://mascidocs.com"},
        timeout=10,
    )
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/svg+xml")
    body = r.text
    assert body.startswith("<svg"), body[:80]
    assert "xmlns" in body


def test_qr_svg_cache_header_at_backend():
    """The route-owned cache-control header is `public, max-age=86400`.
    External proxies may override it (ingress/Cloudflare); the contract
    we lock here is the header value the FastAPI route sets, which is
    what we extracted verbatim from server.py."""
    r = requests.get(
        "http://localhost:8001/api/qr.svg",
        params={"data": "https://mascidocs.com"},
        timeout=10,
    )
    assert r.status_code == 200
    cc = r.headers.get("cache-control", "")
    assert "public" in cc and "max-age=86400" in cc, f"cache-control: {cc!r}"


def test_qr_svg_explicit_scale_within_bounds(base_url: str):
    r = requests.get(
        f"{base_url}/api/qr.svg",
        params={"data": "abc", "scale": 4},
        timeout=10,
    )
    assert r.status_code == 200
    assert r.text.startswith("<svg")


def test_qr_svg_oversized_data_rejected(base_url: str):
    """The route caps `data` at 2048 chars — anything larger is a 400."""
    big = "x" * 2100
    r = requests.get(
        f"{base_url}/api/qr.svg",
        params={"data": big},
        timeout=10,
    )
    assert r.status_code == 400


def test_qr_svg_missing_data_rejected(base_url: str):
    """Missing required `data` param is rejected (FastAPI 422 or app-level 400)."""
    r = requests.get(f"{base_url}/api/qr.svg", timeout=10)
    assert r.status_code in (400, 422), (
        f"expected 400/422 for missing data, got {r.status_code}"
    )
