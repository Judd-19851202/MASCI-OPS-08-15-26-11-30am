"""Operational Intelligence Product registry — the ONE contract every
intelligence product declares itself through.

A product is:
- a stable ID (``product_id`` / ``digest_type``)
- a locked permission contract (``permission_role`` string)
- a locked recipient contract (uses the shared registry)
- a locked schedule contract (freq · disabled default)
- a locked template contract (``template_key`` in the shared renderer)
- a locked data contract (``aggregator`` callable · may raise
  ``NotImplementedError`` if the domain data source is not yet wired)
- a locked audit contract (writes to the shared audit collection)
- a locked history contract (writes to the shared history collection)
- a locked trend contract (produced by the shared trend engine)
- a locked routing contract (deep-link builder callable)

Every product is registered at import time and every registration is
locked by pytest. This is what makes the engine "one truth."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


class ProductStatus:
    IMPLEMENTED = "implemented"          # aggregator produces real data
    CONTRACT_REGISTERED = "contract_registered"  # aggregator raises NotImplementedError


@dataclass(frozen=True)
class OperationalIntelligenceProduct:
    product_id: str                      # stable ID · e.g. "safety_morning_digest"
    display_name: str
    summary: str                         # one-line description
    permission_role: str                 # "safety_or_admin" · "admin_only" · etc.
    template_key: str                    # renderer template selector
    schedule_freq: str                   # "weekly" · "daily" · "monthly" · "manual"
    schedule_iso_day: Optional[int] = None  # 1=Mon..7=Sun (weekly)
    schedule_hour_utc: Optional[int] = None
    status: str = ProductStatus.CONTRACT_REGISTERED
    aggregator: Optional[Callable[..., Awaitable[Dict[str, Any]]]] = None
    deep_link_builder: Optional[Callable[[Dict[str, Any]], str]] = None
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry state
# ---------------------------------------------------------------------------
_REGISTRY: Dict[str, OperationalIntelligenceProduct] = {}


def register_product(p: OperationalIntelligenceProduct) -> None:
    """Register a product. Idempotent — a re-registration with the same
    product_id replaces the entry (used during test isolation)."""
    if not p.product_id:
        raise ValueError("product_id required")
    _REGISTRY[p.product_id] = p


def get_product(product_id: str) -> Optional[OperationalIntelligenceProduct]:
    return _REGISTRY.get(product_id)


def require_product(product_id: str) -> OperationalIntelligenceProduct:
    p = _REGISTRY.get(product_id)
    if not p:
        raise LookupError(f"Operational Intelligence product {product_id!r} is not registered")
    return p


def list_products() -> List[OperationalIntelligenceProduct]:
    return list(_REGISTRY.values())


__all__ = [
    "OperationalIntelligenceProduct", "ProductStatus",
    "register_product", "get_product", "require_product", "list_products",
]
