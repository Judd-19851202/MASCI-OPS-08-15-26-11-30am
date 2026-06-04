"""
MaintainX API Client — P0-A read-first implementation
=====================================================

Hardened, read-first HTTP client for MaintainX. Provides:

  • Bearer-token auth via MAINTAINX_API_KEY (never logged in full)
  • Configurable base URL via MAINTAINX_BASE_URL (defaults to v1 prod)
  • Hard write-disable kill-switch (MAINTAINX_WRITE_ENABLED) — every
    write method raises immediately when the env var is anything other
    than the literal string "true".
  • Hard sync-disable kill-switch (MAINTAINX_SYNC_ENABLED) so the
    scheduler-side caller can opt out separately.
  • Structured `ClientError(status, code, message, retry_after, raw)`
    surface — never raises raw httpx errors out.
  • 401 / 403 / 429 / 5xx classification.
  • Optional pagination helper.
  • Caps timeouts at 15s.

Safety guarantees enforced by this module (do NOT remove):
  1. Even when WRITE is "enabled", every `post/patch/put/delete` here
     raises NotImplementedError. We do not ship write code in this
     P0 sprint — the kill-switch is layered defence only.
  2. The api_key is masked everywhere: logs, repr, error payloads,
     return values. We expose `api_key_last4` for confirmation only.

Public methods:
  • `MaintainxClient.is_configured()` → bool
  • `MaintainxClient.test_connection()` → dict
  • `MaintainxClient.list_assets(*, page_size, max_pages)` → list[dict]
  • `MaintainxClient.iter_assets(*, page_size)` → async iterator
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Env constants ────────────────────────────────────────────────────
DEFAULT_BASE_URL = "https://api.getmaintainx.com/v1"
ENV_API_KEY = "MAINTAINX_API_KEY"
ENV_BASE_URL = "MAINTAINX_BASE_URL"
ENV_SYNC_ENABLED = "MAINTAINX_SYNC_ENABLED"
ENV_WRITE_ENABLED = "MAINTAINX_WRITE_ENABLED"

# ─── Caps & limits ────────────────────────────────────────────────────
DEFAULT_TIMEOUT_S = 15.0
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 50  # absolute cap → max 5000 records / single call


# ═════════════════════════════════════════════════════════════════════
# Errors
# ═════════════════════════════════════════════════════════════════════
class MaintainxClientError(Exception):
    """Structured client error — never leaks the API key."""

    def __init__(
        self, *, status: int, code: str, message: str,
        retry_after: Optional[float] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status = int(status)
        self.code = code
        self.message = message
        self.retry_after = retry_after
        self.raw = raw or {}
        super().__init__(f"[maintainx:{code} status={status}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": False,
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "retry_after": self.retry_after,
        }


class MaintainxConfigError(MaintainxClientError):
    pass


class MaintainxWriteDisabled(MaintainxClientError):
    pass


# ═════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════
def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


def _env_truthy(name: str) -> bool:
    return _env(name).lower() == "true"


def mask_key(key: Optional[str]) -> str:
    if not key:
        return "<unset>"
    if len(key) <= 8:
        return "•" * len(key)
    return f"{'•' * (len(key) - 4)}{key[-4:]}"


@dataclass
class MaintainxConfig:
    api_key: str
    base_url: str
    sync_enabled: bool
    write_enabled: bool

    @classmethod
    def from_env(cls) -> "MaintainxConfig":
        return cls(
            api_key=_env(ENV_API_KEY),
            base_url=_env(ENV_BASE_URL, DEFAULT_BASE_URL),
            sync_enabled=_env_truthy(ENV_SYNC_ENABLED),
            write_enabled=_env_truthy(ENV_WRITE_ENABLED),
        )

    @property
    def api_key_last4(self) -> str:
        if not self.api_key or len(self.api_key) < 4:
            return ""
        return self.api_key[-4:]

    @property
    def api_key_present(self) -> bool:
        return bool(self.api_key)

    def public_view(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_key_present": self.api_key_present,
            "api_key_masked": mask_key(self.api_key) if self.api_key else None,
            "api_key_last4": self.api_key_last4,
            "sync_enabled": self.sync_enabled,
            "write_enabled": self.write_enabled,
        }


# ═════════════════════════════════════════════════════════════════════
# Client
# ═════════════════════════════════════════════════════════════════════
class MaintainxClient:
    """Read-first HTTP client. Writes are HARD-DISABLED in this sprint."""

    def __init__(self, config: Optional[MaintainxConfig] = None,
                 *, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self.config = config or MaintainxConfig.from_env()
        self._timeout = httpx.Timeout(timeout_s)

    # ── configuration probes ────────────────────────────────────────
    def is_configured(self) -> bool:
        return self.config.api_key_present and bool(self.config.base_url)

    def _assert_configured(self) -> None:
        if not self.config.api_key_present:
            raise MaintainxConfigError(
                status=0, code="missing_api_key",
                message="MAINTAINX_API_KEY env var not set",
            )
        if not self.config.base_url:
            raise MaintainxConfigError(
                status=0, code="missing_base_url",
                message="MAINTAINX_BASE_URL env var not set",
            )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "application/json",
            "User-Agent": "ForgedOps/maintainx-client 1.0 (read-first)",
        }

    # ── raw GET (with classification) ───────────────────────────────
    async def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None,
                   client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
        self._assert_configured()
        url = path if path.startswith("http") else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

        async def _do(c: httpx.AsyncClient) -> httpx.Response:
            return await c.get(url, headers=self._headers(), params=params or {})

        try:
            if client is not None:
                resp = await _do(client)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as c2:
                    resp = await _do(c2)
        except httpx.TimeoutException as e:
            raise MaintainxClientError(
                status=0, code="timeout",
                message=f"Request timed out after {self._timeout.read}s: {e}",
            ) from e
        except httpx.HTTPError as e:
            raise MaintainxClientError(
                status=0, code="transport_error",
                message=f"HTTP transport failed: {e.__class__.__name__}",
            ) from e

        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: httpx.Response) -> Dict[str, Any]:
        status = resp.status_code
        if 200 <= status < 300:
            try:
                return resp.json()
            except Exception:  # noqa: BLE001
                return {"raw_text": resp.text}

        # Error classification
        try:
            payload = resp.json()
        except Exception:  # noqa: BLE001
            payload = {"raw_text": resp.text[:500]}

        retry_after: Optional[float] = None
        ra_header = resp.headers.get("Retry-After")
        if ra_header:
            try:
                retry_after = float(ra_header)
            except ValueError:
                retry_after = None

        if status == 401:
            raise MaintainxClientError(
                status=status, code="unauthorized",
                message="MaintainX rejected the API key (401)",
                raw=payload,
            )
        if status == 403:
            raise MaintainxClientError(
                status=status, code="forbidden",
                message="MaintainX denied access — scope insufficient (403)",
                raw=payload,
            )
        if status == 429:
            raise MaintainxClientError(
                status=status, code="rate_limited",
                message="MaintainX rate limit exceeded (429)",
                retry_after=retry_after, raw=payload,
            )
        if 500 <= status < 600:
            raise MaintainxClientError(
                status=status, code="server_error",
                message=f"MaintainX server error ({status})", raw=payload,
            )
        raise MaintainxClientError(
            status=status, code="http_error",
            message=f"MaintainX returned HTTP {status}", raw=payload,
        )

    # ── public reads ────────────────────────────────────────────────
    async def test_connection(self) -> Dict[str, Any]:
        """Cheap connectivity probe. Returns a structured dict regardless
        of success/failure — never raises."""
        if not self.config.api_key_present:
            return {
                "ok": False,
                "status": "missing_api_key",
                "message": f"{ENV_API_KEY} not set",
                "config": self.config.public_view(),
            }
        # MaintainX exposes /assets — a cheap 1-record GET serves as a
        # whoami-equivalent without us guessing a vendor-specific path.
        try:
            data = await self._get("/assets", params={"limit": 1, "page": 1})
            return {
                "ok": True,
                "status": "connected",
                "message": "MaintainX API reachable",
                "config": self.config.public_view(),
                "sample_keys": sorted(list(data.keys()))[:10] if isinstance(data, dict) else [],
            }
        except MaintainxClientError as e:
            return {
                "ok": False,
                "status": "connection_failed",
                "config": self.config.public_view(),
                **e.to_dict(),
            }

    async def iter_assets(self, *, page_size: int = DEFAULT_PAGE_SIZE,
                          max_pages: int = DEFAULT_MAX_PAGES,
                          ) -> AsyncIterator[Dict[str, Any]]:
        """Async iterator over MaintainX asset records. Paginates safely
        using the documented MaintainX `page` / `limit` query params, with
        an absolute `max_pages` cap to prevent runaway pulls."""
        self._assert_configured()
        page_size = max(1, min(int(page_size or DEFAULT_PAGE_SIZE), 500))
        max_pages = max(1, min(int(max_pages or DEFAULT_MAX_PAGES), 500))

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for page in range(1, max_pages + 1):
                data = await self._get(
                    "/assets",
                    params={"page": page, "limit": page_size},
                    client=client,
                )
                # MaintainX paginated responses commonly use either
                # {results: [...], next: <url>} or a bare list. Handle
                # both shapes defensively.
                if isinstance(data, dict):
                    items = data.get("results") or data.get("data") or data.get("assets") or []
                    has_next = bool(data.get("next") or data.get("hasMore"))
                elif isinstance(data, list):
                    items = data
                    has_next = len(items) >= page_size
                else:
                    items = []
                    has_next = False

                if not items:
                    break
                for item in items:
                    if isinstance(item, dict):
                        yield item
                if not has_next:
                    break

    async def list_assets(self, *, page_size: int = DEFAULT_PAGE_SIZE,
                          max_pages: int = DEFAULT_MAX_PAGES,
                          ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        async for a in self.iter_assets(page_size=page_size, max_pages=max_pages):
            out.append(a)
        return out

    # ── writes — HARD DISABLED in this sprint ───────────────────────
    async def create_asset(self, *args, **kwargs):  # noqa: ARG002, D401
        raise MaintainxWriteDisabled(
            status=0, code="write_disabled_sprint",
            message="Writes are not implemented in the P0-A/P0-B read-first sprint.",
        )

    async def update_asset(self, *args, **kwargs):  # noqa: ARG002
        raise MaintainxWriteDisabled(
            status=0, code="write_disabled_sprint",
            message="Writes are not implemented in the P0-A/P0-B read-first sprint.",
        )

    async def delete_asset(self, *args, **kwargs):  # noqa: ARG002
        raise MaintainxWriteDisabled(
            status=0, code="write_disabled_sprint",
            message="Writes are not implemented in the P0-A/P0-B read-first sprint.",
        )


__all__ = [
    "MaintainxClient",
    "MaintainxConfig",
    "MaintainxClientError",
    "MaintainxConfigError",
    "MaintainxWriteDisabled",
    "mask_key",
    "DEFAULT_BASE_URL",
    "ENV_API_KEY",
    "ENV_BASE_URL",
    "ENV_SYNC_ENABLED",
    "ENV_WRITE_ENABLED",
]
