"""
TRACK 15.47 · Incident PDF enrichment.

Universal-PDF-foundation-compliant helper that loads the state-event
timeline (`incident_state_events`) and the linked CAPA records
(`corrective_actions` with `source_kind='incident'`) for a given
incident, then attaches them to the record dict under reserved keys
`_state_timeline` and `_linked_capas`. The dedicated PDF renderer
blocks (added in Track 15.47 to `pdf_render._render_generic`) pick
these up automatically — no V2 PDF system created.

Calling pattern:

    inc = await db.incidents.find_one({"id": ...})
    inc = await enrich_incident_for_pdf(db, inc)
    pdf = render_record_pdf("incident", inc)

Both reads are best-effort; if either collection is missing or empty
the enrichment falls through silently and the PDF still renders the
incident body without those sections.
"""
from __future__ import annotations

from typing import Any, Dict, List


async def enrich_incident_for_pdf(db, record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        return record
    incident_id = record.get("id") or record.get("doc_id") or ""
    if not incident_id:
        return record

    out = dict(record)  # shallow copy — never mutate caller's record

    # ---------- G8 · State timeline ----------
    # Track 15.47-aligned source. The lifecycle module writes events
    # to `incident_state_events`; if a different collection name is
    # used in older deployments we fall back gracefully.
    timeline: List[Dict[str, Any]] = []
    for coll_name in ("incident_state_events", "state_events"):
        try:
            cur = db[coll_name].find(
                {"incident_id": incident_id},
                {"_id": 0},
            ).sort("created_at", 1)
            async for ev in cur:
                timeline.append({
                    "from_state": ev.get("from_state") or ev.get("from") or "",
                    "to_state": ev.get("to_state") or ev.get("to") or "",
                    "actor": ev.get("actor_name") or ev.get("actor_email") or ev.get("actor") or "system",
                    "at": ev.get("created_at") or ev.get("at") or "",
                    "reason": ev.get("reason") or ev.get("note") or "",
                })
            if timeline:
                break  # only one collection should ever yield results
        except Exception:
            timeline = []
    if timeline:
        out["_state_timeline"] = timeline

    # ---------- G9 · Linked CAPAs ----------
    capas: List[Dict[str, Any]] = []
    try:
        cur = db.corrective_actions.find(
            {"source_kind": "incident", "source_id": incident_id},
            {"_id": 0},
        ).sort("created_at", 1)
        async for ca in cur:
            capas.append({
                "id": ca.get("id") or "",
                "title": ca.get("title") or "",
                "assigned_to_name": ca.get("assigned_to_name") or ca.get("assigned_to_email") or "",
                "due_date": ca.get("due_date") or "",
                "status": ca.get("status") or "Open",
                "completed_at": ca.get("completed_at") or "",
            })
    except Exception:
        capas = []
    if capas:
        out["_linked_capas"] = capas

    # ---------- TRACK 15.49 · Aftercare task chain ----------
    # Pulls the 24h/72h/7d follow-up tasks created by the aftercare
    # fan-out (and any manually-added incident follow-up tasks) so the
    # PDF can SHOW that the company followed through, not just
    # responded.
    followups: List[Dict[str, Any]] = []
    try:
        cur = db.tasks.find(
            {"source_module": "safety.incidents", "source_record_id": incident_id},
            {"_id": 0},
        ).sort("due_date", 1)
        async for tk in cur:
            followups.append({
                "task_key": tk.get("task_key") or "",
                "title": tk.get("title") or "",
                "assignee_role": tk.get("assignee_role") or "",
                "assignee_name": tk.get("assigned_to_name") or tk.get("assigned_to_email") or "",
                "due_date": tk.get("due_at") or tk.get("due_date") or "",
                "status": tk.get("status") or "Open",
                "completed_at": tk.get("closed_at") or tk.get("completed_at") or "",
                "priority": tk.get("priority") or "",
            })
    except Exception:
        followups = []
    if followups:
        out["_aftercare_tasks"] = followups

    return out
