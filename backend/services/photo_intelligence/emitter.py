"""DR-ROI-001D · Photo evidence emitter → ODS spine.

Emit `photo_evidence_fact` records into `operational_facts` whenever a
supervisor accepts a suggested link OR when photo intelligence
completes with high confidence and unambiguous observations.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from services.ods_spine.model import now_iso
from services.ods_spine.store import (
    COLL_FACTS, supersede_facts, write_facts, record_ingestion_run,
)
from services.ods_spine.kpi import compute_kpi_snapshot


async def emit_photo_evidence_fact(
    db, *,
    tenant_id: str,
    project_id: str,
    date: str,
    report_id: str,
    photo_id: str,
    intel: Dict[str, Any],
    accepted_link: Dict[str, Any] = None,
    actor: str = "supervisor",
) -> Dict[str, Any]:
    """Emit or supersede the photo_evidence_fact for a photo.

    Idempotent: uses (source_type, source_id, source_item_id) dedupe.
    source_item_id = f'photo:{photo_id}'.
    """
    started = now_iso()
    src_id = report_id
    src_item = f"photo:{photo_id}"
    fact = {
        "fact_id": uuid.uuid4().hex,
        "fact_type": "photo_evidence_fact",
        "tenant_id": tenant_id, "project_id": project_id, "date": date,
        "source_type": "daily_report_v2",
        "source_id": src_id, "source_item_id": src_item,
        "source_version": 0,
        "source_status": "full",
        "is_current": True,
        "submitted_by": actor,
        "verified_identity": False,
        "confidence": float(intel.get("confidence") or 0.5),
        "trace_id": uuid.uuid4().hex,
        "created_at": started,
        "payload": {
            "photo_ref": photo_id,
            "linked_activity": (accepted_link or {}).get("target_id") if (accepted_link or {}).get("target_type") == "activity_card" else None,
            "linked_delay":    (accepted_link or {}).get("target_id") if (accepted_link or {}).get("target_type") == "constraint_card" else None,
            "linked_equipment":(accepted_link or {}).get("target_id") if (accepted_link or {}).get("target_type") == "equipment" else None,
            "linked_safety":   (accepted_link or {}).get("target_id") if (accepted_link or {}).get("target_type") == "safety" else None,
            "linked_quality":  (accepted_link or {}).get("target_id") if (accepted_link or {}).get("target_type") == "quality" else None,
            "ai_tags": [o.get("label", "") for o in (intel.get("observations") or []) if o.get("label")][:16],
            "caption": intel.get("narrative", "")[:500],
        },
    }
    await supersede_facts(db, source_type="daily_report_v2",
                         source_id=src_id, source_item_ids=[src_item])
    run_id = uuid.uuid4().hex
    fact["ingestion_run_id"] = run_id
    result = await write_facts(db, [fact], ingestion_run_id=run_id)
    await record_ingestion_run(
        db, source_type="daily_report_v2", source_id=src_id,
        source_version=0, actor=actor, trigger="photo_evidence",
        ok=True, facts_inserted=result["inserted"],
        facts_superseded=1, started_at=started,
    )
    # Snapshot recompute for the touched (project, date) pair.
    if project_id and date:
        await compute_kpi_snapshot(
            db, tenant_id=tenant_id, project_id=project_id, date=date,
        )
    return {"ok": True, "fact_id": fact["fact_id"], "run_id": run_id}
