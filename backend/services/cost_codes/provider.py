"""TRACK 23.1 · Cost Code Provider Abstraction.

Doctrine
--------
The V3 Daily Report needs cost-code selection without hardcoding *where*
those codes come from. Today the source of truth is
`jobs_master.cost_codes[]` (an additive optional field). Tomorrow the
same UI must transparently read from Vista, Foundation, HCSS, Spectrum,
Sage, an ERP CSV import, or a new dedicated collection — without a
single line of UI or business-logic change.

This module owns that swap point.

Contract
--------
```
class CostCodeProvider:
    async def list_for_project(project_number: str) -> List[CostCode]
    async def get(project_number: str, code: str) -> Optional[CostCode]
```

Every downstream consumer (V3 UI, PM aggregations, future scheduling)
resolves its cost codes through `get_provider()` which returns a
singleton that dispatches to the concrete backend named by
``COST_CODE_PROVIDER`` in the environment. Defaults to
``jobs_master``.

Never returns raw MongoDB ObjectIds. Never fabricates codes.
Missing/empty ⇒ empty list (UI hides selector — never shows a warning
or empty dropdown).
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


# ── Data shape ───────────────────────────────────────────────────────
# Kept as a plain dict for JSON serialization; validated at boundaries.

CostCode = Dict[str, Any]  # {code:str, description:str, active:bool}


def _normalize_code(row: Any) -> Optional[CostCode]:
    """Coerce arbitrary input to the canonical cost code shape.

    Skips rows that lack a non-empty `code`. Silently drops anything
    that would violate the invariant ``code ∈ str`` — never raises.
    """
    if not isinstance(row, dict):
        return None
    code = str(row.get("code") or "").strip()
    if not code:
        return None
    return {
        "code": code,
        "description": str(row.get("description") or "").strip(),
        "active": bool(row.get("active", True)),
    }


# ── Provider interface ──────────────────────────────────────────────

class CostCodeProvider(ABC):
    """Read-only cost-code source. Implementations MUST be idempotent."""

    name: str = "base"

    @abstractmethod
    async def list_for_project(self, project_number: str) -> List[CostCode]:
        """Return only active cost codes for the given project.
        Empty list ⇒ the project has no cost-code configuration.
        """
        raise NotImplementedError

    async def get(self, project_number: str, code: str) -> Optional[CostCode]:
        """Convenience default — most providers override for efficiency."""
        for cc in await self.list_for_project(project_number):
            if cc["code"].lower() == (code or "").strip().lower():
                return cc
        return None


# ── Concrete: jobs_master ──────────────────────────────────────────

class JobsMasterCostCodeProvider(CostCodeProvider):
    """Reads cost codes from ``jobs_master.cost_codes[]``.

    This is the launch provider for Track 23.1. Any code that has
    ``active is False`` is filtered out so PMs can archive without
    admin help.
    """

    name = "jobs_master"

    def __init__(self, db):
        self._db = db

    async def list_for_project(self, project_number: str) -> List[CostCode]:
        if not project_number:
            return []
        try:
            doc = await self._db.jobs_master.find_one(
                {"project_number": project_number},
                {"_id": 0, "cost_codes": 1},
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("[cost-codes] jobs_master read failed: %s", exc)
            return []
        raw = (doc or {}).get("cost_codes") or []
        out: List[CostCode] = []
        seen: set = set()
        for row in raw:
            norm = _normalize_code(row)
            if norm is None or not norm["active"]:
                continue
            key = norm["code"].lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(norm)
        out.sort(key=lambda c: c["code"])
        return out


# ── Registry & singleton ─────────────────────────────────────────

_REGISTRY: Dict[str, type] = {
    "jobs_master": JobsMasterCostCodeProvider,
    # Future: "vista", "foundation", "hcss", "spectrum", "sage",
    # "csv_import" — register here without touching UI or DR logic.
}

_singleton: Optional[CostCodeProvider] = None


def get_provider(db) -> CostCodeProvider:
    """Return the process-wide singleton for the configured provider.

    Reads ``COST_CODE_PROVIDER`` from the environment; unknown or
    missing values fall back to the safe default ``jobs_master``.
    """
    global _singleton  # noqa: PLW0603
    if _singleton is not None:
        return _singleton
    name = (os.environ.get("COST_CODE_PROVIDER") or "jobs_master").strip().lower()
    cls = _REGISTRY.get(name) or JobsMasterCostCodeProvider
    _singleton = cls(db)
    return _singleton


def register_provider(name: str, cls: type) -> None:
    """Public seam for future ERP adapters. Adapters must subclass
    :class:`CostCodeProvider` and MUST NOT block the event loop.
    """
    if not issubclass(cls, CostCodeProvider):
        raise TypeError("provider must subclass CostCodeProvider")
    _REGISTRY[name.strip().lower()] = cls


def _reset_singleton_for_tests() -> None:
    """Test hook — pytest fixtures may swap providers per test."""
    global _singleton  # noqa: PLW0603
    _singleton = None


__all__ = [
    "CostCode",
    "CostCodeProvider",
    "JobsMasterCostCodeProvider",
    "get_provider",
    "register_provider",
    "_reset_singleton_for_tests",
]
