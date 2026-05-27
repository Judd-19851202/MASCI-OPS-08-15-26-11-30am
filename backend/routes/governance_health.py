"""
routes/governance_health.py — Phase IV-BETA.5A-P1A · Governance Health Chip backend.

Public read-only endpoint that surfaces the persisted doctrine baseline
(captured by tests/pw_suite/test_visual_doctrine_baseline.py) in a form
the tiny `GovernanceHealthChip.jsx` component can render. The chip is
mounted on all four Hub V2 surfaces (Admin · PM · HR · Safety) and is
intentionally restrained — monochrome, no animation, secondary
hierarchy.

Design:
  - Reads /app/memory/HUB_VISUAL_BASELINE.json on every call (small file,
    rare reads).
  - NO database I/O.
  - NO auth requirement — the chip surfaces on all four portals; gating
    by portal would force four parallel implementations. The data is
    operational telemetry (hue family count, loudness composite, hashes)
    with zero PII.
  - Endpoints:
      GET /api/governance/health            → all portals summary
      GET /api/governance/health/{portal}   → one portal (admin|pm|hr|safety)

Drift state thresholds are calibrated to the iter437 IV-BETA.5A baselines:
    pm   ≈ 27   ┐ stable band ≤ 45
    admin ≈ 36  │
    hr    ≈ 65  ┘ monitor band 45-75
    safety ≈ 67 ┘ drift band > 75
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

BASELINE_PATH = Path("/app/memory/HUB_VISUAL_BASELINE.json")

VALID_PORTALS = {"admin", "pm", "hr", "safety"}

# Calibrated to the iter437 IV-BETA.5A baseline. Warning-only — no deploy
# gate. Operator can tighten these once 3+ iterations of trend data exist.
STABLE_CEIL = 45.0
MONITOR_CEIL = 75.0


def _classify(loudness: float) -> Dict[str, str]:
    """Return {state, label, summary} for a loudness composite score."""
    if loudness <= STABLE_CEIL:
        return {
            "state": "stable",
            "label": "governance stable",
            "summary": "Doctrine baseline within calibrated calm band.",
        }
    if loudness <= MONITOR_CEIL:
        return {
            "state": "monitor",
            "label": "governance monitor",
            "summary": "Loudness elevated. Operator review optional.",
        }
    return {
        "state": "drift",
        "label": "governance drift",
        "summary": "Loudness above calibrated ceiling. Review recommended.",
    }


def _load_baseline() -> Optional[Dict[str, Any]]:
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _portal_health(baseline: Dict[str, Any], portal: str) -> Optional[Dict[str, Any]]:
    snapshots = baseline.get("snapshots") or {}
    cells = snapshots.get(portal)
    if not cells:
        return None

    # Pick desktop as the canonical chip cell; fall back gracefully.
    cell = cells.get("desktop") or cells.get("ipad") or cells.get("mobile")
    if not cell:
        return None

    loudness = float(cell.get("loudness_score") or 0.0)
    classification = _classify(loudness)

    return {
        "portal": portal,
        "loudness": round(loudness, 2),
        "hue_family_count": int(cell.get("hue_family_count") or 0),
        "badge_density": float(cell.get("badge_density") or 0.0),
        "elements_walked": int(cell.get("elements_walked") or 0),
        "dom_style_hash": cell.get("dom_style_hash") or "",
        "hierarchy_hash": cell.get("hierarchy_hash") or "",
        **classification,
        "baseline_version": (baseline.get("_meta") or {}).get("version") or "",
        "baseline_updated_at": (baseline.get("_meta") or {}).get("updated_at") or "",
    }


def build_governance_health_router() -> APIRouter:
    router = APIRouter(tags=["governance-health"])

    @router.get("/api/governance/health")
    async def governance_health_all():
        """All portals summary — tiny payload (<1 KB)."""
        baseline = _load_baseline()
        if not baseline:
            return {"ok": False, "reason": "baseline_not_captured", "portals": {}}
        portals = {}
        for p in sorted(VALID_PORTALS):
            cell = _portal_health(baseline, p)
            if cell:
                portals[p] = cell
        return {
            "ok": True,
            "thresholds": {
                "stable_ceiling": STABLE_CEIL,
                "monitor_ceiling": MONITOR_CEIL,
            },
            "portals": portals,
        }

    @router.get("/api/governance/health/{portal}")
    async def governance_health_one(portal: str):
        """Single-portal health — what the chip fetches."""
        portal = portal.lower().strip()
        if portal not in VALID_PORTALS:
            raise HTTPException(status_code=400, detail="unknown portal")
        baseline = _load_baseline()
        if not baseline:
            return {"ok": False, "reason": "baseline_not_captured", "portal": portal}
        cell = _portal_health(baseline, portal)
        if not cell:
            return {"ok": False, "reason": "portal_not_in_baseline", "portal": portal}
        return {"ok": True, **cell}

    return router


__all__ = ["build_governance_health_router", "_classify", "STABLE_CEIL", "MONITOR_CEIL"]
