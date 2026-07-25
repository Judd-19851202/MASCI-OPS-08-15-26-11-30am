"""TRACK 15.79 · Deployment ledger persistence.

Append-only Mongo collection (``deployment_decisions``) that records
every Trust Gate invocation. Designed so the operator can audit
*"on date X, was the platform deploy-ready? what blocked it?"*
without parsing CI logs.

Documents are **immutable** — there is no UPDATE/DELETE surface
exposed. The endpoint only writes via ``insert_one`` and a
``$setOnInsert``-only TTL index housekeeping path (year-old
records expire automatically).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from lib.ots_truth import CERTIFIED, canonical_truth_card, public_ots_projection


COLLECTION = "deployment_decisions"


async def ensure_indexes(db) -> None:
    try:
        await db[COLLECTION].create_index([("ts", -1)])
        await db[COLLECTION].create_index([("commit", 1), ("ts", -1)])
        await db[COLLECTION].create_index([("decision", 1), ("ts", -1)])
        await db[COLLECTION].create_index(
            [("verification_id", 1)], unique=True, sparse=True
        )
        # 365-day TTL on the ts_dt field (immutable for the operator's
        # forensic window; older entries auto-expire to keep the
        # collection small).
        await db[COLLECTION].create_index(
            "ts_dt", expireAfterSeconds=365 * 24 * 3600
        )
    except Exception:
        pass


async def write_snapshot_doc(db, body: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_indexes(db)
    decision = (body.get("decision") or "").lower()
    if decision not in {"pass", "fail"}:
        raise HTTPException(400, "decision must be exactly 'pass' or 'fail'")
    now = datetime.now(timezone.utc)
    verification_id = str(body.get("verification_id") or "")[:96] or None
    doc: Dict[str, Any] = {
        "ts": now.isoformat(),
        "ts_dt": now,
        "decision": decision,
        "exit_code": int(body.get("exit_code") or 0),
        "commit": str(body.get("commit") or body.get("backend_runtime_commit") or "")[:64],
        "branch": str(body.get("branch") or "")[:64],
        "environment": str(body.get("environment") or "")[:32],
        "operator": str(body.get("operator") or "")[:128],
        "duration_ms": int(body.get("duration_ms") or 0),
        "trust_score": int(body.get("trust_score") or 0),
        "trust_band": str(body.get("trust_band") or "")[:16],
        "blocking_count": int(body.get("blocking_count") or 0),
        "advisory_count": int(body.get("advisory_count") or 0),
        "regression_count": int(body.get("regression_count") or 0),
        "blocking_ids": (body.get("blocking_ids") or [])[:32],
        "frontend_build_commit": str(body.get("frontend_build_commit") or "")[:64],
        "backend_runtime_commit": str(body.get("backend_runtime_commit") or body.get("commit") or "")[:64],
        "intended_release_commit": str(body.get("intended_release_commit") or "")[:128],
        "build_version": str(body.get("build_version") or "")[:128],
        "build_timestamp": str(body.get("build_timestamp") or "")[:64],
        "parity_result": bool(body.get("parity_result")),
        "parity_reason": str(body.get("parity_reason") or "")[:256],
        "health_ok": bool(body.get("health_ok")),
        "health_status_code": int(body.get("health_status_code") or 0),
        "health_reason": str(body.get("health_reason") or "")[:256],
        "go_no_go": str(body.get("go_no_go") or decision.upper())[:16],
        "failure_reason": str(body.get("failure_reason") or "")[:512],
        "script_version": str(body.get("script_version") or "")[:64],
        "source_hash": str(body.get("source_hash") or "")[:64],
        "dependency_manifest_hash": str(body.get("dependency_manifest_hash") or "")[:128],
        "governance_hash": str(body.get("governance_hash") or body.get("release_gate_manifest_hash") or "")[:128],
        "verification_source": str(body.get("verification_source") or "")[:64],
        "runtime_identity_status": str(body.get("runtime_identity_status") or "")[:64],
    }
    truth_card = canonical_truth_card(
        truth_subject="bcss_recovery_certification",
        canonical_owner="bcss_recovery_certification",
        truth_surface_id="bcss_recovery_certification",
        evidence_state="historical",
        evidence_quality="DECISION_RECORDED",
        evidence_confidence="HIGH",
        truth_evaluation="VERIFIED" if decision == "pass" else "DEGRADED",
        permitted_claim=CERTIFIED,
        claim_ceiling=CERTIFIED,
        claim_basis=["deployment_decisions ledger"],
        prohibited_claims=["current recovery certification"],
        degradation_reasons=[] if decision == "pass" else [str(body.get("failure_reason") or "deployment decision failed")],
        unknowns=["Historical decision records do not prove current deployment or recovery state."],
        contradictory_evidence=[],
        evidence_timestamp=doc["ts"],
        evaluation_timestamp=doc["ts"],
        audit_reference="OTS-C5-DEPLOYMENT-HISTORY",
        evidence_required_to_raise_claim=["current decision context for present-tense claims"],
        notes=["Historical ledger is decision-recorded evidence only."],
    )
    doc["ots_truth"] = public_ots_projection(truth_card)
    if verification_id:
        doc["verification_id"] = verification_id
        await db[COLLECTION].update_one(
            {"verification_id": verification_id},
            {"$setOnInsert": doc},
            upsert=True,
        )
    else:
        await db[COLLECTION].insert_one(doc)
    return {
        "ok": True,
        "ts": doc["ts"],
        "verification_id": verification_id,
    }


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.post("/api/admin/deployment-readiness/snapshot")
    async def append_snapshot(
        request: Request,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Append one deployment decision to the immutable ledger.

        Body (all fields optional except ``decision``)::

            {
              "decision":  "pass" | "fail",
              "exit_code": int,
              "commit":    "abc1234",
              "branch":    "main",
              "environment": "preview" | "production",
              "operator":  "jaymn.judd@mascigc.com",
              "duration_ms": 38234,
              "trust_score": 40,
              "trust_band":  "red",
              "blocking_count": 0,
              "advisory_count": 3,
              "regression_count": 99,
              "blocking_ids": ["..."]
            }
        """
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "invalid JSON body")
        return await write_snapshot_doc(db, body)

    @router.get("/api/admin/deployment-readiness/history")
    async def history(
        limit: int = 50,
        _: Any = Depends(require_admin_only_dep),
    ) -> Dict[str, Any]:
        """Read-only view of the deployment ledger (newest first)."""
        limit = max(1, min(int(limit or 50), 500))
        rows = []
        cursor = db[COLLECTION].find(
            {}, {"_id": 0, "ts_dt": 0}, sort=[("ts", -1)], limit=limit,
        )
        async for r in cursor:
            if "ots_truth" not in r:
                truth_card = canonical_truth_card(
                    truth_subject="bcss_recovery_certification",
                    canonical_owner="bcss_recovery_certification",
                    truth_surface_id="bcss_recovery_certification",
                    evidence_state="historical",
                    evidence_quality="DECISION_RECORDED",
                    evidence_confidence="HIGH",
                    truth_evaluation="VERIFIED" if r.get("decision") == "pass" else "DEGRADED",
                    permitted_claim=CERTIFIED,
                    claim_ceiling=CERTIFIED,
                    claim_basis=["deployment_decisions ledger"],
                    prohibited_claims=["current recovery certification"],
                    degradation_reasons=[] if r.get("decision") == "pass" else [str(r.get("failure_reason") or "deployment decision failed")],
                    unknowns=["Historical decision records do not prove current deployment or recovery state."],
                    contradictory_evidence=[],
                    evidence_timestamp=r.get("ts"),
                    evaluation_timestamp=r.get("ts"),
                    audit_reference="OTS-C5-DEPLOYMENT-HISTORY",
                    evidence_required_to_raise_claim=["current decision context for present-tense claims"],
                    notes=["Historical ledger is decision-recorded evidence only."],
                )
                r["ots_truth"] = public_ots_projection(truth_card)
            rows.append(r)
        total = await db[COLLECTION].count_documents({})
        pass_count = await db[COLLECTION].count_documents({"decision": "pass"})
        fail_count = await db[COLLECTION].count_documents({"decision": "fail"})
        return {
            "count": len(rows),
            "total_ever": total,
            "pass_total": pass_count,
            "fail_total": fail_count,
            "events": rows,
        }

    return router
