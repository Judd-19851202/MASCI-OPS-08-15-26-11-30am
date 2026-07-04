"""
routes/verification.py · VER-1 · Operational Verification Layer.

Convert operational signals (M-2 routed events, M-3 verified locations,
M-1 asset mappings) into trust states. **Compute-on-read only**.
Stores nothing. Mutates nothing. Authors nothing.

Doctrine: VER-1 brief §"CONSTITUTIONAL RULES" + MOTIVE_001 §G.

Trust states (VER-1-1):
  • CONFIRMED              — expected activity + Motive evidence agrees
  • PENDING_CONFIRMATION   — expected activity but insufficient evidence yet
  • MISMATCH               — expected vs observed conflict
  • QUIET                  — no expectation, no evidence
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query

logger = logging.getLogger(__name__)

TRUST_STATES = {"CONFIRMED", "PENDING_CONFIRMATION", "MISMATCH", "QUIET"}

ACTIVE_DISPATCH_STATES = {
    "ASSIGNED", "EN_ROUTE_TO_LOAD", "AT_LOAD_SITE",
    "LOADED", "EN_ROUTE_TO_DUMP", "AT_DUMP_SITE", "IN_TRANSIT",
}

TERMINAL_DISPATCH_STATES = {"COMPLETE", "CANCELLED", "CANCELED"}


def _parse_iso(ts: Any) -> Optional[datetime]:
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Trust-state compute primitives ────────────────────────────────────
def compute_trust_state(
    has_expectation: bool,
    observed_at_expected: bool,
    observed_elsewhere: bool,
) -> Tuple[str, str]:
    """The single source of trust truth.
    Returns (state, reason)."""
    if not has_expectation and not observed_at_expected and not observed_elsewhere:
        return ("QUIET", "no expectation and no evidence")
    if has_expectation and observed_at_expected and not observed_elsewhere:
        return ("CONFIRMED", "Motive evidence supports the expected activity")
    if has_expectation and observed_elsewhere and not observed_at_expected:
        return ("MISMATCH", "asset observed at a different verified location")
    if has_expectation and not observed_at_expected and not observed_elsewhere:
        return ("PENDING_CONFIRMATION", "expected but no Motive evidence yet")
    # Has expectation AND observed at expected AND observed elsewhere — mixed,
    # still CONFIRMED because the at-expected evidence dominates the question.
    if has_expectation and observed_at_expected and observed_elsewhere:
        return ("CONFIRMED", "asset visited expected location plus others (still confirmed)")
    # No expectation but observed somewhere — call it QUIET (we have nothing
    # to verify against). This protects against accidentally promoting
    # "stuff is happening" into a Confirmed-against-nothing positive.
    return ("QUIET", "evidence present but no expectation to verify against")


# ── Router builder ────────────────────────────────────────────────────
def build_verification_router(db, require_admin_dep: Callable) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["verification"])

    # ── shared lookups ────────────────────────────────────────────────
    async def _verified_geofences_for(project_number: str) -> List[str]:
        """Return motive_geofence_ids for the project's Verified op_locations."""
        out: List[str] = []
        async for loc in db.operational_locations.find({
            "project_number": project_number,
            "geocode_status": "Verified",
            "motive_geofence_id": {"$nin": [None, ""]},
        }):
            out.append(str(loc["motive_geofence_id"]))
        return out

    async def _events_today_at_locations(
        gids: List[str], date: str,
    ) -> List[Dict[str, Any]]:
        try:
            day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise HTTPException(400, f"Bad date: {e}") from e
        day_start = day.isoformat()
        day_end = (day + timedelta(days=1)).isoformat()
        out: List[Dict[str, Any]] = []
        async for ev in db.operational_events.find({
            "occurred_at": {"$gte": day_start, "$lt": day_end},
        }):
            ev.pop("_id", None)
            if not gids:
                continue
            if str(ev.get("location_id") or "") in gids \
               or any(str(s) == str(ev.get("location_id"))
                      for s in gids):
                # location_id is the op_location id, NOT motive_geofence_id.
                # Will be re-checked below — but we accept candidates and
                # filter by project_number directly.
                pass
            out.append(ev)
        return out

    async def _asset_key_for_dispatch(d: Dict[str, Any]) -> Optional[str]:
        """Resolve dispatch.truck_id (or equipment_id) → asset_key."""
        truck = (d.get("truck_id") or "").strip()
        equip = (d.get("equipment_id") or "").strip()
        if truck:
            # Look up by MASCI equipment id
            m = await db.asset_mappings.find_one({
                "masci_equipment_id": truck, "provider": "motive"
            })
            if m:
                mm = m.get("motive") or {}
                if m.get("asset_kind") == "vehicle" and mm.get("vehicle_id"):
                    return f"vehicle:{mm['vehicle_id']}"
                if m.get("asset_kind") == "equipment" and mm.get("asset_id"):
                    return f"equipment:{mm['asset_id']}"
        if equip:
            m = await db.asset_mappings.find_one({
                "masci_equipment_id": equip, "provider": "motive"
            })
            if m:
                mm = m.get("motive") or {}
                if m.get("asset_kind") == "vehicle" and mm.get("vehicle_id"):
                    return f"vehicle:{mm['vehicle_id']}"
                if m.get("asset_kind") == "equipment" and mm.get("asset_id"):
                    return f"equipment:{mm['asset_id']}"
        return None

    # ── VER-1-2 · Dispatch verification (per-assignment) ──────────────
    @router.get("/verification/dispatch/{dispatch_id}")
    async def verify_dispatch(dispatch_id: str = Path(...)):
        d = await db.dispatch_assignments.find_one({"id": dispatch_id}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Dispatch not found")
        state = (d.get("current_state") or "").upper()
        proj = d.get("project_number") or ""
        actor_key = await _asset_key_for_dispatch(d)

        # If the assignment is terminal, just report QUIET (no expectation to verify against).
        if state in TERMINAL_DISPATCH_STATES:
            return {"ok": True, "dispatch_id": dispatch_id,
                    "trust_state": "QUIET", "reason": "dispatch is terminal",
                    "expected_project": proj, "asset_key": actor_key,
                    "current_state": state}

        if not actor_key:
            return {"ok": True, "dispatch_id": dispatch_id,
                    "trust_state": "PENDING_CONFIRMATION",
                    "reason": "no Motive asset_mappings link for this dispatch's truck/equipment",
                    "expected_project": proj, "asset_key": None,
                    "current_state": state}

        # Gather today's operational_events for this actor
        date = _today_iso()
        day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        day_s = day.isoformat()
        day_e = (day + timedelta(days=1)).isoformat()
        observed_at_expected = False
        observed_elsewhere = False
        other_projects: List[str] = []
        async for ev in db.operational_events.find({
            "asset_key": actor_key,
            "occurred_at": {"$gte": day_s, "$lt": day_e},
        }):
            ev_proj = ev.get("project_number")
            if ev.get("location_type") == "JOB" and ev_proj == proj:
                observed_at_expected = True
            elif ev.get("location_type") == "JOB" and ev_proj:
                observed_elsewhere = True
                if ev_proj not in other_projects:
                    other_projects.append(ev_proj)

        trust_state, reason = compute_trust_state(
            has_expectation=bool(proj),
            observed_at_expected=observed_at_expected,
            observed_elsewhere=observed_elsewhere,
        )
        return {"ok": True, "dispatch_id": dispatch_id,
                "trust_state": trust_state, "reason": reason,
                "expected_project": proj, "asset_key": actor_key,
                "observed_other_projects": other_projects,
                "current_state": state}

    # ── VER-1-7 · Daily Report verification surface ───────────────────
    @router.get("/verification/daily-report/{report_id}",
                dependencies=[Depends(require_admin_dep)])
    async def verify_daily_report(report_id: str = Path(...)):
        dr = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not dr:
            raise HTTPException(404, "Daily Report not found")
        proj = dr.get("project_number") or ""
        date = dr.get("report_date") or _today_iso()

        # Equipment subject (VER-1-3)
        eq_rows = dr.get("equipment") or []
        eq_descriptions = [
            (r.get("description") or "").lower().strip() for r in eq_rows
            if (r.get("description") or "").strip()
        ]
        # Motive-detected equipment for project+date
        detections: List[Dict[str, Any]] = []
        day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        day_s = day.isoformat()
        day_e = (day + timedelta(days=1)).isoformat()
        async for ev in db.operational_events.find({
            "project_number": proj, "location_type": "JOB",
            "event_type": {"$in": ["PROJECT_ARRIVAL", "PROJECT_DEPARTURE"]},
            "occurred_at": {"$gte": day_s, "$lt": day_e},
        }):
            detections.append(ev)
        observed_labels = list({(ev.get("asset_label") or "").lower().strip()
                                for ev in detections})

        eq_has_exp = bool(eq_descriptions)
        eq_observed_at = any(
            any(part and part in label or label in part for part in obs.split())
            for obs in observed_labels for label in eq_descriptions
        ) if observed_labels and eq_descriptions else (
            bool(eq_descriptions) and bool(observed_labels)
        )
        eq_state, eq_reason = compute_trust_state(
            has_expectation=eq_has_exp,
            observed_at_expected=eq_observed_at,
            observed_elsewhere=False,
        )

        # Dispatch subject (VER-1-2 batch-roll-up)
        dispatch_count = await db.dispatch_assignments.count_documents({
            "project_number": proj,
            "current_state": {"$nin": list(TERMINAL_DISPATCH_STATES)},
        })
        # If any assignment-level Motive observation aligns with the project,
        # mark CONFIRMED. Otherwise PENDING.
        any_obs = any(ev.get("project_number") == proj for ev in detections)
        di_state, di_reason = compute_trust_state(
            has_expectation=bool(dispatch_count),
            observed_at_expected=any_obs,
            observed_elsewhere=False,
        )

        # Material movement subject (VER-1-4) — read-only visibility.
        # Expected: project has outbound or inbound material on the DR
        # OR has dispatch_assignments today.
        has_material_expectation = (
            bool(dr.get("materials")) or bool(dr.get("outbound_materials"))
            or dispatch_count > 0
        )
        # Observed: any non-JOB destination/source event tied to assets on
        # the project (plant/yard/disposal) on the same day.
        mm_observed = False
        if any_obs:
            async for ev in db.operational_events.find({
                "asset_key": {"$in": [d["asset_key"] for d in detections]},
                "occurred_at": {"$gte": day_s, "$lt": day_e},
                "location_type": {"$in": ["ASPHALT_PLANT", "CONCRETE_PLANT",
                                          "PIT", "DISPOSAL_SITE", "YARD"]},
            }).limit(1):
                mm_observed = True
                break
        mm_state, mm_reason = compute_trust_state(
            has_expectation=has_material_expectation,
            observed_at_expected=mm_observed,
            observed_elsewhere=False,
        )

        # Project presence (VER-1-5)
        pp_state, pp_reason = compute_trust_state(
            has_expectation=True,  # the DR itself implies presence is expected
            observed_at_expected=any_obs,
            observed_elsewhere=False,
        )

        # Overall
        if "MISMATCH" in (eq_state, di_state, mm_state, pp_state):
            overall = "MISMATCH"
        else:
            overall = max(
                ["CONFIRMED", "PENDING_CONFIRMATION"],
                key=lambda s: sum(1 for x in [eq_state, di_state, mm_state, pp_state] if x == s),
            )

        return {
            "ok": True, "report_id": report_id,
            "project_number": proj, "date": date,
            "subjects": {
                "equipment":          {"state": eq_state, "reason": eq_reason,
                                       "expected_count": len(eq_descriptions),
                                       "observed_count": len(observed_labels)},
                "dispatch":           {"state": di_state, "reason": di_reason,
                                       "active_assignments": dispatch_count},
                "material_movement":  {"state": mm_state, "reason": mm_reason},
                "project_presence":   {"state": pp_state, "reason": pp_reason},
            },
            "overall_state": overall,
            "evidence": {
                "operational_events_today": len(detections),
                "observed_labels": observed_labels[:10],
            },
        }

    # ── VER-1-5 · Project presence ────────────────────────────────────
    @router.get("/verification/project-presence/{project_number}/{date}",
                dependencies=[Depends(require_admin_dep)])
    async def verify_project_presence(
        project_number: str = Path(..., min_length=1),
        date: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        day_s = day.isoformat()
        day_e = (day + timedelta(days=1)).isoformat()
        active_dispatch = await db.dispatch_assignments.count_documents({
            "project_number": project_number,
            "current_state": {"$nin": list(TERMINAL_DISPATCH_STATES)},
        })
        observed_at = await db.operational_events.count_documents({
            "project_number": project_number,
            "location_type": "JOB",
            "occurred_at": {"$gte": day_s, "$lt": day_e},
        })
        # Cross-project observations (asset on this project's dispatch but
        # detected at a different project) — sample
        my_actors: List[str] = []
        async for d in db.dispatch_assignments.find({
            "project_number": project_number,
            "current_state": {"$nin": list(TERMINAL_DISPATCH_STATES)},
        }):
            key = await _asset_key_for_dispatch(d)
            if key:
                my_actors.append(key)
        observed_elsewhere = 0
        if my_actors:
            observed_elsewhere = await db.operational_events.count_documents({
                "asset_key": {"$in": my_actors},
                "location_type": "JOB",
                "project_number": {"$ne": project_number, "$nin": [None, ""]},
                "occurred_at": {"$gte": day_s, "$lt": day_e},
            })
        state, reason = compute_trust_state(
            has_expectation=bool(active_dispatch),
            observed_at_expected=observed_at > 0,
            observed_elsewhere=observed_elsewhere > 0,
        )
        return {"ok": True, "project_number": project_number, "date": date,
                "trust_state": state, "reason": reason,
                "active_dispatch": active_dispatch,
                "events_at_project": observed_at,
                "events_elsewhere_by_project_assets": observed_elsewhere}

    # ── VER-1-6 · Dashboard verification summary ──────────────────────
    @router.get("/admin/verification/dashboard",
                dependencies=[Depends(require_admin_dep)])
    async def verification_dashboard():
        """Roll-up: count of active dispatches by trust state."""
        counts = {s: 0 for s in TRUST_STATES}
        n = 0
        async for d in db.dispatch_assignments.find({
            "current_state": {"$nin": list(TERMINAL_DISPATCH_STATES)},
        }).limit(500):
            n += 1
            # Inline verification
            proj = d.get("project_number") or ""
            actor_key = await _asset_key_for_dispatch(d)
            if not actor_key:
                counts["PENDING_CONFIRMATION"] += 1
                continue
            day = datetime.now(timezone.utc)
            day_s = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            day_e = (day + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0).isoformat()
            obs_at = False
            obs_else = False
            async for ev in db.operational_events.find({
                "asset_key": actor_key,
                "occurred_at": {"$gte": day_s, "$lt": day_e},
            }):
                if ev.get("location_type") == "JOB" and ev.get("project_number") == proj:
                    obs_at = True
                elif ev.get("location_type") == "JOB" and ev.get("project_number"):
                    obs_else = True
            state, _ = compute_trust_state(bool(proj), obs_at, obs_else)
            counts[state] += 1
        return {"ok": True, "dispatch_counts_by_trust": counts,
                "active_dispatch_total": n}

    # ── VER-1 · Required Audit (10 questions) ─────────────────────────
    @router.get("/admin/verification/audit",
                dependencies=[Depends(require_admin_dep)])
    async def verification_audit():
        # Run a dashboard-style scan
        verified_count = 0
        pending_count = 0
        mismatch_count = 0
        quiet_count = 0
        mismatch_causes: Dict[str, int] = {}
        missing_evidence: Dict[str, int] = {}
        considered = 0

        async for d in db.dispatch_assignments.find({
            "current_state": {"$nin": list(TERMINAL_DISPATCH_STATES)},
        }).limit(1000):
            considered += 1
            proj = d.get("project_number") or ""
            actor_key = await _asset_key_for_dispatch(d)
            if not actor_key:
                pending_count += 1
                missing_evidence["no_asset_mapping"] = \
                    missing_evidence.get("no_asset_mapping", 0) + 1
                continue
            day = datetime.now(timezone.utc)
            day_s = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            day_e = (day + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0).isoformat()
            obs_at = False
            obs_else_pn: Optional[str] = None
            async for ev in db.operational_events.find({
                "asset_key": actor_key,
                "occurred_at": {"$gte": day_s, "$lt": day_e},
            }):
                if ev.get("location_type") == "JOB" and ev.get("project_number") == proj:
                    obs_at = True
                elif ev.get("location_type") == "JOB" and ev.get("project_number"):
                    obs_else_pn = ev.get("project_number")
            state, _ = compute_trust_state(bool(proj), obs_at, bool(obs_else_pn))
            if state == "CONFIRMED":
                verified_count += 1
            elif state == "PENDING_CONFIRMATION":
                pending_count += 1
                missing_evidence["no_events_yet"] = \
                    missing_evidence.get("no_events_yet", 0) + 1
            elif state == "MISMATCH":
                mismatch_count += 1
                cause = f"asset observed on {obs_else_pn}"
                mismatch_causes[cause] = mismatch_causes.get(cause, 0) + 1
            else:
                quiet_count += 1

        # Quiet assets — assets with no expectation AND no events
        total_assets = await db.asset_mappings.count_documents({})
        assets_with_events: set = set()
        async for ev in db.operational_events.find({}, {"asset_key": 1}):
            assets_with_events.add(ev.get("asset_key"))
        quiet_assets = total_assets - len(assets_with_events)

        denom = max(1, considered)
        accuracy = round(100.0 * verified_count / denom, 1)
        # False-positive: dispatches we marked CONFIRMED but where Motive
        # observed cross-project visits (we don't have ground truth to
        # compute FP/FN — leave honest 'not directly observable' nulls).
        # Operator trust score: blends accuracy with mismatch share.
        mismatch_share = round(100.0 * mismatch_count / denom, 1)
        trust_score = max(0.0, round(accuracy - (mismatch_share * 1.5), 1))

        return {"ok": True, "answers": {
            "q1_total_verified_assignments": verified_count,
            "q2_total_pending_assignments":  pending_count,
            "q3_total_mismatches":           mismatch_count,
            "q4_total_quiet_assets":         quiet_assets,
            "q5_top_mismatch_causes": sorted(mismatch_causes.items(),
                                              key=lambda x: -x[1])[:5],
            "q6_most_common_missing_evidence":
                sorted(missing_evidence.items(), key=lambda x: -x[1])[:5],
            "q7_verification_accuracy_pct": accuracy,
            "q8_false_positive_rate":
                "not directly observable without ground truth",
            "q9_false_negative_rate":
                "not directly observable without ground truth",
            "q10_operator_trust_score":      trust_score,
            "considered_active_dispatches":  considered,
        }}

    return router


__all__ = ["build_verification_router", "compute_trust_state",
           "TRUST_STATES", "ACTIVE_DISPATCH_STATES",
           "TERMINAL_DISPATCH_STATES"]
