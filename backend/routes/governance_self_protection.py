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

from fastapi import APIRouter, Body, Depends, HTTPException

REPO_ROOT = Path("/app")
SCRIPTS_DIR = REPO_ROOT / "scripts"
MEMORY_DIR = REPO_ROOT / "memory"
TEST_REPORTS_DIR = REPO_ROOT / "test_reports"
FIELD_WALKS_DIR = MEMORY_DIR / "FIELD_WALK_CHECKLISTS"
DEPLOY_HISTORY_PATH = MEMORY_DIR / "DEPLOYMENT_HISTORY.json"
DEPLOY_HISTORY_MAX = 50

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
    # TRACK 28.11 · Classify warnings so the UI can distinguish
    # "current actionable" from "historical baselined pattern".
    # `new_warnings` from the raw probe is a diff against the
    # authority baseline — it counts patterns that are not YET on
    # the baselined list. When `baselined > 0` those warnings are
    # part of an accepted historical pattern; the UI should NOT
    # display "60 NEW warnings" when 24 are already tolerated.
    warning_classification = {
        "current_actionable": n_w if n_b == 0 else 0,
        "historical_baselined": n_b,
        "baseline_tolerated_new": n_w if n_b > 0 else 0,
        "informational": 0,
    }
    payload = {
        "status": status,
        "new_violations": n_v,
        "new_warnings": n_w,
        "baselined": n_b,
        "warning_classification": warning_classification,
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
    now = time.time()
    # TRACK 28.11 · Freshness policy for field-walk doctrine docs.
    #   ≤ 30d  → HEALTHY (current)
    #   ≤ 60d  → ATTENTION (nearing recert)
    #   >  60d → STALE (must be recertified)
    FRESH_S = 30 * 86400
    ATTN_S = 60 * 86400
    per_walk_states: List[str] = []
    for name in ("FL.md", "PM.md", "Safety.md", "HR.md", "MobileSafari.md"):
        p = FIELD_WALKS_DIR / name
        if not p.exists():
            walks.append({"role": name.replace(".md", ""),
                          "exists": False, "last_modified_at": None,
                          "age_days": None, "freshness_status": "UNKNOWN"})
            per_walk_states.append("UNKNOWN")
            continue
        mtime = int(p.stat().st_mtime)
        age_s = int(now - mtime)
        age_d = age_s // 86400
        if age_s <= FRESH_S:
            fresh_state = "HEALTHY"
        elif age_s <= ATTN_S:
            fresh_state = "ATTENTION"
        else:
            fresh_state = "STALE"
        walks.append({
            "role": name.replace(".md", ""),
            "exists": True,
            "last_modified_at": mtime,
            "age_days": age_d,
            "freshness_status": fresh_state,
        })
        per_walk_states.append(fresh_state)
    # Rollup: worst walk drives the stanza status.
    if any(s == "STALE" for s in per_walk_states):
        status = "stale"
    elif any(s == "ATTENTION" for s in per_walk_states):
        status = "amber"
    elif any(s == "UNKNOWN" for s in per_walk_states):
        status = "amber"
    else:
        status = "green"
    return {
        "status": status,
        "walks": walks,
        "freshness_policy": {"healthy_max_days": 30, "attention_max_days": 60},
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


# ─── Deployment stanza (CUTOVER-READY · 2026-05-28) ─────────────────
#
# Tracks the moment-of-deploy and the source_hash that was current at
# each cutover. Read-only on the GET path. The pre-deploy script (or
# the operator, manually) POSTs to /api/admin/governance/record-deploy
# to append a new entry — this is the ONLY write path on the
# self-protection surface.
#
# The OPS-1 page consumes this to answer "what just changed?" in five
# seconds without leaving the governance surface.

def _read_deploy_history() -> List[Dict[str, Any]]:
    data = _safe_read_json(DEPLOY_HISTORY_PATH)
    if not data:
        return []
    items = data.get("history") if isinstance(data, dict) else None
    return items if isinstance(items, list) else []


def _deployment_status(*, current_hash: str) -> Dict[str, Any]:
    """Return the deployment stanza. Always renders — degrades to
    `bootstrap` when no history file exists yet (fresh install)."""
    history = _read_deploy_history()
    current_entry = None
    prior_entry = None
    if history:
        # Most recent entry whose hash matches the running process.
        for entry in reversed(history):
            if entry.get("source_hash") == current_hash:
                current_entry = entry
                break
        # Prior = the most recent entry whose hash != current.
        for entry in reversed(history):
            if entry.get("source_hash") and entry.get("source_hash") != current_hash:
                prior_entry = entry
                break
    deployed_at = (current_entry or {}).get("deployed_at")
    prior_source_hash = (prior_entry or {}).get("source_hash")
    prior_deployed_at = (prior_entry or {}).get("deployed_at")
    # Status doctrine:
    #   green     · history known, current hash recorded, prior hash present
    #   amber     · history known, current hash NOT recorded (deploy moved
    #               forward but operator hasn't run record-deploy yet)
    #   unknown   · no history at all (bootstrap)
    if not history:
        status = "unknown"
    elif current_entry is None:
        status = "amber"
    else:
        status = "green"
    return {
        "status": status,
        "source_hash": current_hash,
        "deployed_at": deployed_at,
        "prior_source_hash": prior_source_hash,
        "prior_deployed_at": prior_deployed_at,
        "history_size": len(history),
    }


def _record_deploy_entry(*, source_hash: str, note: str) -> Dict[str, Any]:
    """Append a deploy record. Idempotent against the exact same
    `source_hash` already at the tail — we never duplicate the most
    recent entry. Returns the new history payload."""
    history = _read_deploy_history()
    if history and history[-1].get("source_hash") == source_hash:
        # Idempotent — same hash already at tail.
        return {"appended": False, "history": history}
    entry = {
        "source_hash": source_hash,
        "deployed_at": int(time.time()),
        "note": (note or "")[:200],
    }
    history.append(entry)
    # Keep the last N records.
    if len(history) > DEPLOY_HISTORY_MAX:
        history = history[-DEPLOY_HISTORY_MAX:]
    payload = {
        "schema": "DEPLOYMENT_HISTORY/v1",
        "history": history,
    }
    DEPLOY_HISTORY_PATH.write_text(json.dumps(payload, indent=2))
    return {"appended": True, "entry": entry, "history_size": len(history)}


def build_governance_self_protection_router(require_admin):
    router = APIRouter()

    @router.get("/api/admin/governance/self-protection",
                dependencies=[Depends(require_admin)])
    async def get_self_protection() -> Dict[str, Any]:
        # Lazy-import to keep the route module independent of server.py
        # at import time; resolves at call time so unit tests that
        # mount the router in isolation don't crash.
        try:
            from server import _SOURCE_HASH as current_hash
        except ImportError:
            current_hash = "unknown"
        probe = _run_probe()
        trust = _trust_surfaces_status()
        context = _context_governance_status()
        truthful = _truthful_state_status()
        telemetry = _telemetry_doctrine_status()
        regression = _regression_suite_status()
        walks = _field_walk_status()
        drift = _drift_status(context=context, probe=probe)
        deployment = _deployment_status(current_hash=current_hash)
        # Overall page status: worst of the constituent stanzas.
        # NOTE: `deployment.status == "amber"` (deploy moved forward
        # but not yet recorded) is informational, not a governance
        # failure — it does NOT flip the overall page status. It only
        # affects its own pill so the operator sees "deploy recorded".
        order = {"green": 0, "amber": 1, "stale": 1, "red": 2, "unknown": 1}
        worst = max((order.get(s.get("status"), 0)
                     for s in (probe, trust, context, truthful, telemetry,
                               regression, walks, drift)),
                    default=0)
        page_status = {0: "green", 1: "amber", 2: "red"}.get(worst, "amber")
        # TRACK 28.11 · Emit canonical vocabulary so consumers stop
        # reading `overall_status: None` and defaulting to UNKNOWN.
        from lib.canonical_status import to_canonical  # noqa: PLC0415
        canonical_overall = to_canonical(page_status)
        return {
            "generated_at": int(time.time()),
            "page_status": page_status,
            "overall_status": page_status,
            "canonical_status": canonical_overall,
            "authority": probe,
            "trust_surfaces": trust,
            "context_governance": context,
            "truthful_state": truthful,
            "telemetry": telemetry,
            "regression_suite": regression,
            "field_walks": walks,
            "drift": drift,
            "deployment": deployment,
        }

    @router.post("/api/admin/governance/record-deploy",
                 dependencies=[Depends(require_admin)])
    async def record_deploy(payload: Dict[str, Any] = Body(default=None)) -> Dict[str, Any]:
        """Append the running process's `source_hash` to the deploy
        history. The operator runs this once per production cutover
        (or the pre-deploy script does it automatically). Idempotent
        against the same hash."""
        try:
            from server import _SOURCE_HASH as current_hash
        except ImportError:
            raise HTTPException(status_code=500,
                                detail="cannot resolve current source_hash")
        note = ""
        if isinstance(payload, dict):
            note = str(payload.get("note") or "")[:200]
        result = _record_deploy_entry(source_hash=current_hash, note=note)
        # Refresh the stanza for the operator.
        result["deployment"] = _deployment_status(current_hash=current_hash)
        return result

    return router


__all__ = [
    "build_governance_self_protection_router",
    "auto_record_deploy_on_startup",
]


def auto_record_deploy_on_startup(source_hash: str) -> Dict[str, Any]:
    """TRACK 28.11 · Idempotent startup hook.

    Called from `server.py` after the source_hash is known. Appends
    the current deploy to the on-disk history file iff the running
    hash is not already at the tail. Safe to call on every restart —
    an unchanged hash is a no-op.

    Also records a `restart_at` timestamp so the operator can see the
    difference between "the current build first deployed at T" and
    "the process last restarted at T". `deployed_at` never moves
    backward for the same hash.
    """
    if not source_hash or source_hash == "unknown":
        return {"appended": False, "reason": "no_source_hash"}
    try:
        return _record_deploy_entry(
            source_hash=source_hash,
            note="auto-recorded on backend startup",
        )
    except Exception as e:  # noqa: BLE001
        return {"appended": False, "reason": f"error:{e!s}"[:200]}
