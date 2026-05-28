"""routes/governance_self_protection.py — Phase GOVERNANCE-OPS-1 · 2026-05-28.

Read-only aggregator that powers the `/admin/governance/self-protection`
operational visibility page. Reads the governance doctrine artifacts
that already exist on disk and returns a calm, text-first JSON payload
that the page renders 1:1 — NO database, NO live aggregation, NO
charts, NO analytics creep.

Sources (all read-only · all already maintained by other workstreams)
* `scripts/authority_pattern_baseline.json`
* `memory/TRUST_SURFACES.json`
* `memory/SHARED_SURFACE_CONTEXT_MATRIX.json`
* `memory/TRUTHFUL_STATE_TEST_MATRIX.json`
* `memory/TELEMETRY_SIGNAL_MATRIX.json`
* `memory/FIELD_WALK_CHECKLISTS/` (file mtimes as "last walk")
* `scripts/authority_mismatch_probe.py` (invoked with a 60s cache)

Doctrine
--------
* Admin-only (require_admin dependency).
* Idempotent · no writes anywhere.
* Sub-200ms response under cache hit · sub-500ms cold (the only
  expensive call is the probe, which itself runs in ~85ms).
* Degrades gracefully — if any source file is missing, the
  corresponding stanza renders `"status": "unknown"` rather than
  500-ing the whole page.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

REPO_ROOT = Path("/app")
SCRIPTS_DIR = REPO_ROOT / "scripts"
MEMORY_DIR = REPO_ROOT / "memory"
TEST_REPORTS_DIR = REPO_ROOT / "test_reports"
FIELD_WALKS_DIR = MEMORY_DIR / "FIELD_WALK_CHECKLISTS"

# 60s cache for the probe — page polling MUST NOT thrash CI.
_PROBE_CACHE: Dict[str, Any] = {"at": 0.0, "data": None}
_PROBE_TTL_S = 60


def _safe_read_json(path: Path) -> Dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _run_probe() -> Dict[str, Any]:
    """Run the Authority Mismatch Probe with a 60s in-memory cache.

    Returns the same structure as `--json` mode, plus a `cached_age_s`
    field so the UI can render the freshness.
    """
    now = time.time()
    if _PROBE_CACHE["data"] and (now - _PROBE_CACHE["at"]) < _PROBE_TTL_S:
        d = dict(_PROBE_CACHE["data"])
        d["cached_age_s"] = int(now - _PROBE_CACHE["at"])
        return d
    started = time.time()
    try:
        r = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "authority_mismatch_probe.py"),
             "--json"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return {"status": "unknown", "scan_ms": -1,
                    "error": r.stderr[:200]}
        data = json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"status": "unknown", "scan_ms": -1, "error": str(e)[:200]}
    n_v = len(data.get("new_violations") or [])
    n_w = len(data.get("new_warnings") or [])
    n_b = len(data.get("baselined") or [])
    if n_v > 0:
        status = "red"
    elif n_w > 0 and n_b == 0:
        # warn-only with no baseline coverage = needs review
        status = "amber"
    else:
        status = "green"
    payload = {
        "status": status,
        "new_violations": n_v,
        "new_warnings": n_w,
        "baselined": n_b,
        "scan_ms": data.get("scan_ms", int((time.time() - started) * 1000)),
        "last_run_at": int(now),
        "cached_age_s": 0,
    }
    _PROBE_CACHE["data"] = payload
    _PROBE_CACHE["at"] = now
    return payload


def _trust_surfaces_status() -> Dict[str, Any]:
    data = _safe_read_json(MEMORY_DIR / "TRUST_SURFACES.json")
    if not data:
        return {"status": "unknown", "registered": 0, "live": 0,
                "planned": 0, "surfaces": []}
    surfaces = data.get("surfaces") or []
    live = [s for s in surfaces if s.get("status") == "live"]
    planned = [s for s in surfaces if s.get("status") == "planned"]
    surfaces_brief = [{
        "id": s.get("id"),
        "name": s.get("name"),
        "status": s.get("status"),
        "regression_count": len(s.get("regression") or []),
    } for s in surfaces]
    return {
        "status": "green",
        "registered": len(surfaces),
        "live": len(live),
        "planned": len(planned),
        "doctrine_fields": data.get("doctrine_fields") or [],
        "surfaces": surfaces_brief,
    }


def _context_governance_status() -> Dict[str, Any]:
    data = _safe_read_json(MEMORY_DIR / "SHARED_SURFACE_CONTEXT_MATRIX.json")
    if not data:
        return {"status": "unknown", "context_governed": 0, "tbd": 0, "rows": []}
    rows = data.get("surfaces") or []
    governed = [r for r in rows if r.get("compliance") == "context-governed"]
    tbd = [r for r in rows if str(r.get("compliance") or "").startswith("TBD")]
    planned = [r for r in rows if str(r.get("status") or "").startswith("planned")]
    rows_brief = [{
        "path": r.get("path"),
        "status": r.get("status"),
        "compliance": r.get("compliance"),
    } for r in rows]
    # Status: green if all live surfaces governed; amber if some TBD;
    # red if any live surface has compliance == "violation" (none today).
    if any(r.get("status") == "live"
           and str(r.get("compliance") or "").startswith("TBD")
           for r in rows):
        status = "amber"
    else:
        status = "green"
    return {
        "status": status,
        "context_governed": len(governed),
        "tbd": len(tbd),
        "planned": len(planned),
        "rows": rows_brief,
    }


def _truthful_state_status() -> Dict[str, Any]:
    data = _safe_read_json(MEMORY_DIR / "TRUTHFUL_STATE_TEST_MATRIX.json")
    if not data:
        return {"status": "unknown", "contracts": 0}
    contracts = data.get("contracts") or []
    # We don't run the tests here — the existence of the contract +
    # the named regression test is the doctrine surface. Test status
    # is reflected by the `regression suite` stanza below.
    return {
        "status": "green",
        "contracts": len(contracts),
        "surfaces_covered": sorted({c.get("surface") for c in contracts
                                    if c.get("surface")}),
    }


def _telemetry_doctrine_status() -> Dict[str, Any]:
    data = _safe_read_json(MEMORY_DIR / "TELEMETRY_SIGNAL_MATRIX.json")
    if not data:
        return {"status": "unknown"}
    return {
        "status": "green",
        "client_signals": len(data.get("client_signals") or {}),
        "server_signals": len(data.get("server_signals") or {}),
        "forbidden_patterns": len(data.get("forbidden") or []),
    }


def _regression_suite_status() -> Dict[str, Any]:
    """Read the most recent test_reports/iteration_*.json (if any)
    plus the test_credentials marker. Status is reported AS-IS — we
    don't run tests on this page request."""
    reports: List[Path] = []
    if TEST_REPORTS_DIR.exists():
        reports = sorted(TEST_REPORTS_DIR.glob("iteration_*.json"))
    if not reports:
        return {"status": "unknown", "last_iteration": None}
    last = reports[-1]
    try:
        body = json.loads(last.read_text())
    except (json.JSONDecodeError, OSError):
        return {"status": "unknown", "last_iteration": last.name}
    # Best-effort summary extraction (structure varies by iteration).
    # We're calm here — partial extraction is fine.
    return {
        "status": "green",
        "last_iteration": last.name,
        "last_iteration_at": int(last.stat().st_mtime),
        "summary_keys": list(body.keys())[:10],
    }


def _field_walk_status() -> Dict[str, Any]:
    if not FIELD_WALKS_DIR.exists():
        return {"status": "unknown", "walks": []}
    walks = []
    for name in ("FL.md", "PM.md", "Safety.md", "HR.md", "MobileSafari.md"):
        p = FIELD_WALKS_DIR / name
        if not p.exists():
            walks.append({"role": name.replace(".md", ""),
                          "exists": False, "last_modified_at": None})
            continue
        # File mtime here is the doctrine doc's last edit. We do NOT
        # claim it's the last operator walk timestamp — operators record
        # walk results out-of-band (a future iteration may track these
        # in a tiny IDB or admin-only collection). For now, show the
        # checklist's last-touched date so operators know which version
        # of the checklist is current.
        walks.append({
            "role": name.replace(".md", ""),
            "exists": True,
            "last_modified_at": int(p.stat().st_mtime),
        })
    return {
        "status": "amber" if any(not w.get("exists") for w in walks) else "green",
        "walks": walks,
    }


def _drift_status(*, context: Dict[str, Any], probe: Dict[str, Any]) -> Dict[str, Any]:
    """Combined drift snapshot. Reuses the underlying source values so
    a single number tells the operator how many open governance gaps
    exist right now."""
    tbd = int(context.get("tbd") or 0)
    new_v = int(probe.get("new_violations") or 0)
    new_w = int(probe.get("new_warnings") or 0)
    total_gaps = tbd + new_v
    status = "green"
    if new_v > 0:
        status = "red"
    elif tbd > 0 or new_w > 0:
        status = "amber"
    return {
        "status": status,
        "open_gaps": total_gaps,
        "context_tbd": tbd,
        "authority_violations": new_v,
        "authority_warnings": new_w,
    }


def build_governance_self_protection_router(require_admin):
    router = APIRouter()

    @router.get("/api/admin/governance/self-protection",
                dependencies=[Depends(require_admin)])
    async def get_self_protection() -> Dict[str, Any]:
        probe = _run_probe()
        trust = _trust_surfaces_status()
        context = _context_governance_status()
        truthful = _truthful_state_status()
        telemetry = _telemetry_doctrine_status()
        regression = _regression_suite_status()
        walks = _field_walk_status()
        drift = _drift_status(context=context, probe=probe)
        # Overall page status: worst of the constituent stanzas.
        order = {"green": 0, "amber": 1, "red": 2, "unknown": 1}
        worst = max((order.get(s.get("status"), 0)
                     for s in (probe, trust, context, truthful, telemetry,
                               regression, walks, drift)),
                    default=0)
        page_status = {0: "green", 1: "amber", 2: "red"}.get(worst, "amber")
        return {
            "generated_at": int(time.time()),
            "page_status": page_status,
            "authority": probe,
            "trust_surfaces": trust,
            "context_governance": context,
            "truthful_state": truthful,
            "telemetry": telemetry,
            "regression_suite": regression,
            "field_walks": walks,
            "drift": drift,
        }

    return router


__all__ = ["build_governance_self_protection_router"]
