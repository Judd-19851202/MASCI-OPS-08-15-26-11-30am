"""Scheduler contract — one scheduler wrapper, gated on
``SCHEDULER_ENABLED``. Products declare their schedule via the registry;
the actual cron wiring is a small server-startup hook (Phase 2 · out of
scope for Track 19.40 · documented in TRACK_19_40_SCHEDULER.md)."""
from __future__ import annotations

import os
from typing import Dict, Optional

from .registry import get_product


def scheduler_enabled() -> bool:
    return (os.environ.get("SCHEDULER_ENABLED") or "").lower() in ("1", "true", "yes")


def schedule_definition_for(product_id: str) -> Optional[Dict[str, str]]:
    p = get_product(product_id)
    if not p:
        return None
    return {
        "product_id": p.product_id,
        "freq": p.schedule_freq,
        "iso_day": str(p.schedule_iso_day) if p.schedule_iso_day is not None else "",
        "hour_utc": str(p.schedule_hour_utc) if p.schedule_hour_utc is not None else "",
    }


__all__ = ["scheduler_enabled", "schedule_definition_for"]
