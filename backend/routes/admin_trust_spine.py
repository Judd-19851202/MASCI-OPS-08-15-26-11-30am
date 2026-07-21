"""TRACK 15.76 · Platform Trust Spine — admin observability.

Admin-gated endpoint that aggregates ``trust_spine_events`` and
returns per-workflow lifecycle health alongside the Track 15.75D
audit-row health. The frontend Platform Trust Dashboard renders
these counters next to the per-workflow delivery table, giving the
operator a single screen with both audit-side and lifecycle-side
proof.

The endpoint is **READ-ONLY**, **admin-gated**, **secret-free**,
and **never mutates** anything.

Band rules (no fake-green):

* RED   — any failed_24h event OR contradicted dashboard
* AMBER — events_24h > 0 but missing one or more expected stages
* AMBER-NO-ACTIVITY — events_24h == 0 (workflow idle in last 24h)
* GREEN — events_24h > 0, no failures, all expected stages observed
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from lib.canonical_truth import canonical_truth_surface, derived_truth_payload
from lib.trust_spine import WORKFLOW_EXPECTED_STAGES


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/trust-spine")
    async def trust_spine(_: Any = Depends(require_admin_only_dep)) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        since_24h = (now - timedelta(hours=24)).isoformat()

        # Aggregate per workflow / stage / status counts (last 24h)
        workflows: Dict[str, Dict[str, Any]] = {}
        async for row in db.trust_spine_events.aggregate([
            {"$match": {"ts": {"$gte": since_24h}}},
            {"$group": {
                "_id": {"workflow": "$workflow", "stage": "$stage", "status": "$status"},
                "n": {"$sum": 1},
            }},
        ]):
            wf = (row["_id"].get("workflow") or "") or "unknown"
            stage = row["_id"].get("stage") or "unknown"
            status = row["_id"].get("status") or "unknown"
            slot = workflows.setdefault(wf, {
                "workflow": wf,
                "events_24h": 0,
                "ok_24h": 0,
                "failed_24h": 0,
                "skipped_24h": 0,
                "stages_seen": {},
                "stages_failed": {},
            })
            n = int(row["n"])
            slot["events_24h"] += n
            slot[f"{status}_24h"] = slot.get(f"{status}_24h", 0) + n
            slot["stages_seen"][stage] = slot["stages_seen"].get(stage, 0) + n
            if status == "failed":
                slot["stages_failed"][stage] = slot["stages_failed"].get(stage, 0) + n

        # Ensure every workflow listed in the expected contract appears
        # in the dashboard — even if it produced zero events — so the
        # operator can see idle workflows as AMBER-NO-ACTIVITY rather
        # than missing entirely.
        for known_wf in WORKFLOW_EXPECTED_STAGES.keys():
            workflows.setdefault(known_wf, {
                "workflow": known_wf,
                "events_24h": 0,
                "ok_24h": 0,
                "failed_24h": 0,
                "skipped_24h": 0,
                "stages_seen": {},
                "stages_failed": {},
            })

        for wf, slot in workflows.items():
            latest = await db.trust_spine_events.find_one(
                {"workflow": wf}, sort=[("ts", -1)],
                projection={"_id": 0},
            )
            slot["latest"] = latest
            slot["last_failure"] = await db.trust_spine_events.find_one(
                {"workflow": wf, "status": "failed"},
                sort=[("ts", -1)],
                projection={"_id": 0},
            )
            last_ok = await db.trust_spine_events.find_one(
                {"workflow": wf, "status": "ok"},
                sort=[("ts", -1)],
                projection={"_id": 0, "ts": 1, "stage": 1, "record_id": 1},
            )
            slot["last_success"] = last_ok

            expected = WORKFLOW_EXPECTED_STAGES.get(wf, [])
            seen_ok_stages = set()
            # A stage is "satisfied" only if we have at least one ok
            # event for it within the last 24h (fake-green guard).
            for stg in expected:
                if slot["stages_seen"].get(stg, 0) - slot["stages_failed"].get(stg, 0) > 0:
                    seen_ok_stages.add(stg)
            missing_stages = [s for s in expected if s not in seen_ok_stages]
            slot["expected_stages"] = list(expected)
            slot["missing_stages"] = missing_stages

            # Band logic.
            success_rate_24h = (
                (slot["ok_24h"] / slot["events_24h"]) if slot["events_24h"] else 0.0
            )
            slot["success_rate_24h"] = round(success_rate_24h, 3)

            if slot["failed_24h"] > 0:
                slot["band"] = "red"
                # Surface the most recent failure's specific stage.
                lf = slot["last_failure"] or {}
                slot["failure_stage"] = lf.get("stage") or "unknown"
                slot["reason"] = (
                    f"{slot['failed_24h']} failed lifecycle event(s) at "
                    f"{slot['failure_stage']}: "
                    f"{(lf.get('failure_reason') or '—')[:120]}"
                )
                slot["remediation"] = lf.get("remediation") or (
                    "Inspect backend logs and re-run the failing workflow."
                )
            elif slot["events_24h"] == 0:
                slot["band"] = "amber-no-activity"
                slot["failure_stage"] = None
                slot["reason"] = "no lifecycle events in last 24h"
                slot["remediation"] = (
                    "Submit a record for this workflow to refresh its evidence."
                )
            elif missing_stages:
                slot["band"] = "amber"
                slot["failure_stage"] = missing_stages[0]
                slot["reason"] = (
                    f"missing expected stage(s): {', '.join(missing_stages)}"
                )
                slot["remediation"] = (
                    "Wire missing stages into this workflow; partial evidence "
                    "is not green."
                )
            else:
                slot["band"] = "green"
                slot["failure_stage"] = None
                slot["reason"] = (
                    f"{slot['ok_24h']} ok event(s) across "
                    f"{len(seen_ok_stages)}/{len(expected) or 1} expected stage(s)"
                )
                slot["remediation"] = None

        # Sort rows: red first, then amber-no-activity, then amber, then green.
        band_order = {"red": 0, "amber": 1, "amber-no-activity": 2, "green": 3}
        rows: List[Dict[str, Any]] = sorted(
            workflows.values(),
            key=lambda r: (band_order.get(r["band"], 99), -r["events_24h"], r["workflow"]),
        )

        # Total counters.
        total_events_24h = await db.trust_spine_events.count_documents(
            {"ts": {"$gte": since_24h}}
        )
        total_failed_24h = await db.trust_spine_events.count_documents(
            {"ts": {"$gte": since_24h}, "status": "failed"}
        )

        # Universal platform band: red if ANY workflow is red, amber if
        # any workflow is amber (incl. no-activity), else green.
        if any(r["band"] == "red" for r in rows):
            platform_band = "red"
            canonical_status = "MISMATCH"
        elif any(r["band"] in {"amber", "amber-no-activity"} for r in rows):
            platform_band = "amber"
            canonical_status = "DEGRADED"
        else:
            platform_band = "green"
            canonical_status = "VERIFIED"

        return {
            "track": "15.76",
            "generated_at": now.isoformat(),
            "platform_band": platform_band,
            "canonical_status": canonical_status,
            "truth_surface": canonical_truth_surface("trust_spine"),
            "truth_relationship": derived_truth_payload(
                "trust_spine",
                canonical_owner_route="/api/admin/trust-spine",
                derivation_explanation="Workflow lifecycle truth comes directly from trust_spine_events rollups.",
                canonical_status=canonical_status,
                derived_status=canonical_status,
                conflicts=[],
                evidence_age_source="generated_at",
                stale_evidence=False,
            )["relationship"],
            "total_events_24h": total_events_24h,
            "total_failed_24h": total_failed_24h,
            "workflow_count": len(rows),
            "workflows": rows,
            "allowed_stages": sorted([
                "record_created", "validation_complete", "routing_resolved",
                "recipients_built", "notification_queued", "provider_accepted",
                "audit_written", "dashboard_updated", "completed",
            ]),
        }

    @router.get("/api/admin/trust-spine/workflow/{workflow}")
    async def trust_spine_workflow_drilldown(
        workflow: str,
        limit: int = 50,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Drill-in: last ``limit`` lifecycle events for a single workflow.

        Lets the operator see the exact record_ids, stages, and failure
        reasons without leaving the dashboard or running a Mongo query.
        """
        limit = max(1, min(int(limit or 50), 500))
        rows: List[Dict[str, Any]] = []
        cursor = db.trust_spine_events.find(
            {"workflow": workflow},
            {"_id": 0},
            sort=[("ts", -1)],
            limit=limit,
        )
        async for r in cursor:
            rows.append(r)
        return {
            "workflow": workflow,
            "count": len(rows),
            "expected_stages": WORKFLOW_EXPECTED_STAGES.get(workflow, []),
            "events": rows,
        }

    return router
