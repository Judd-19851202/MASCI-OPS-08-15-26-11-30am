# DR-ROI-001 · Schema Plan

**Date:** 2026-02-05
**Constraint:** Additive-only. `DailyReportCreate.model_config = ConfigDict(extra="allow")` guarantees legacy clients continue submitting successfully. Every V2 field defaults to a safe null/empty.

## New backend fields (all optional, additive)

```python
# ── Track B (this session · UI-side scaffolding · backend fields NOT yet added) ──
# The following are planned; backend addition lands in DR-ROI-001C when
# AI wiring begins. `extra="allow"` in the existing model lets V2 clients
# POST these fields today without server-side change — they land in Mongo
# as extra keys and can be aggregated read-side.

activity_cards: List[Dict[str, Any]] = default_factory=list
constraint_cards: List[Dict[str, Any]] = default_factory=list
tomorrow_readiness: Optional[Dict[str, Any]] = None
ai_operational_summary: Optional[str] = None
ai_agent_outputs: Optional[Dict[str, Any]] = None
ai_questions: List[Dict[str, Any]] = default_factory=list
ai_confidence: Optional[float] = None
ai_source_trace: Optional[Dict[str, Any]] = None
pm_action_items: List[Dict[str, Any]] = default_factory=list
photo_ai_tags: List[Dict[str, Any]] = default_factory=list
photo_activity_links: List[Dict[str, Any]] = default_factory=list
final_approved_narrative: Optional[str] = None
supervisor_ai_approval_state: Optional[str] = None   # "unreviewed" | "accepted" | "edited" | "regenerated"
ai_approval_log: List[Dict[str, Any]] = default_factory=list
```

## New nested shapes

### `activity_cards[]`
```python
{
    "id": "uuid",
    "area": "Parent Loop East",
    "activity_type": "Base grading",
    "quantity": 240,
    "unit": "LF",
    "crew_ids": ["hr:12", "hr:44"],
    "equipment_ids": ["eq:motor-grader-3", "eq:roller-2"],
    "materials_placed": [{"material": "base", "loads": 12}],
    "materials_removed": [{"material": "trees", "loads": 6}],
    "trucks_loads": 12,
    "photo_ids": ["ph:abc", "ph:def", "ph:ghi", "ph:jkl"],
    "status": "on-track",          # on-track | ahead | delayed | blocked | complete
    "has_issue": False,
    "extra_work": False,
    "continues_tomorrow": False,
    "notes": "optional supervisor note ≤ 280 chars"
}
```

### `constraint_cards[]`
```python
{
    "id": "uuid",
    "category": "utility_conflict",  # closed-enum (see below)
    "what_happened": "found 8\" gas line at 2ft depth · not on plan",
    "started_at": "2026-02-05T09:15:00-05:00",
    "ended_at": "2026-02-05T11:30:00-05:00",   # optional
    "duration_minutes": 135,
    "impact": "stopped grading crew · rerouted grader to west side",
    "responsible_party": "owner",              # owner | ceo | pm | sub | crew | weather | vendor | dot | ceo/pm | other
    "responsible_party_name": "Duke Energy",
    "needed_by": "2026-02-06T07:00:00-05:00",
    "photo_ids": ["ph:mn1"],
    "cost_impact_potential": True,
    "time_impact_potential": True,
    "notes": "gas company called; ETA response 12:00 tomorrow"
}

# Closed-enum categories (matches directive):
CONSTRAINT_CATEGORIES = [
    "weather", "equipment", "utility_conflict", "inspection_delay",
    "material_delay", "survey_model_issue", "subcontractor_issue",
    "owner_ceo_decision", "traffic_control", "manpower",
    "extra_work", "safety_stop", "quality_rework", "other"
]
```

### `tomorrow_readiness{}`
```python
{
    "crew_needed": [{"trade": "pipe", "count": 4}],
    "equipment_needed": [{"description": "trench box 8ft", "count": 1}],
    "material_needed": [{"description": "12\" HDPE", "quantity": 500, "unit": "LF"}],
    "inspection_needed": [{"agency": "county", "activity": "compaction", "needed_by": "2026-02-06T09:00:00-05:00"}],
    "survey_needed": [{"scope": "grade shots east loop", "needed_by": "2026-02-06T07:30:00-05:00"}],
    "traffic_control_needed": True,
    "subcontractor_needed": [{"trade": "electrical", "activity": "conduit"}],
    "decision_needed": [{"topic": "8\" gas line reroute", "from": "owner", "needed_by": "2026-02-06T12:00:00-05:00"}],
    "safety_follow_ups": [],
    "quality_follow_ups": [],
    "blockers": [
        {"type": "utility_conflict", "description": "gas line reroute", "constraint_id": "uuid"}
    ]
}
```

### `ai_source_trace{}`
```python
{
    "sentences": [
        {
            "index": 0,
            "text": "Crew completed 240 LF of base grading on Parent Loop East.",
            "evidence_ids": ["activity_card:uuid1"],
            "agent": "OperationsAgent",
            "confidence": 0.98
        },
        {
            "index": 1,
            "text": "Utility conflict at 09:15 delayed grading for 2h 15m.",
            "evidence_ids": ["constraint_card:uuid2"],
            "agent": "DelayAgent",
            "confidence": 0.95
        }
    ],
    "generated_at": "2026-02-05T18:32:00Z",
    "model_versions": {
        "reasoning": "claude-sonnet-4.5-2026-01",
        "vision":    "gpt-5.2-vision-2026-01"
    }
}
```

### `pm_action_items[]`
```python
{
    "id": "uuid",
    "title": "Confirm gas-line reroute plan with Duke Energy",
    "owner": "pm@masci.com",
    "due": "2026-02-06T12:00:00-05:00",
    "source": {"type": "constraint_card", "id": "uuid2"},
    "priority": "high",           # high | medium | low
    "status": "open"              # open | in-progress | resolved
}
```

### `ai_approval_log[]`
```python
[
    {"at": "2026-02-05T18:32:00Z", "action": "draft_generated",  "agent": "NarrativeAgent"},
    {"at": "2026-02-05T18:35:00Z", "action": "supervisor_edit",  "diff": "…"},
    {"at": "2026-02-05T18:38:00Z", "action": "supervisor_accept", "final_hash": "sha256:…"}
]
```

## New analytics collection: `daily_report_kpis`

```python
{
    "_id": ObjectId,
    "report_id": "uuid",             # trace back to source doc
    "project_number": "23-045",
    "report_date": "2026-02-05",     # ISO date
    "shift": "day",
    "supervisor": "prepared_by field",

    # Production
    "production_by_activity": [{"activity_type": "base grading", "quantity": 240, "unit": "LF"}],
    "production_by_area":     [{"area": "Parent Loop East", "activities": [...] }],
    "material_loads_in": 12,
    "material_loads_out": 6,
    "truck_count": 18,

    # Time
    "crew_hours_by_activity": [{"activity_type": "base grading", "hours": 36.5}],
    "equip_hours_by_activity": [{"activity_type": "base grading", "hours": 24.0}],

    # Delays
    "weather_delay_hours": 0,
    "equip_delay_hours": 0.5,
    "delay_counts_by_category": {"utility_conflict": 1, "weather": 0},
    "extra_work_events": 0,

    # PM
    "open_pm_actions": 3,
    "tomorrow_readiness_risks": 1,

    # Safety/Quality
    "unresolved_safety_issues": 0,
    "unresolved_quality_issues": 0,

    # Meta
    "photo_compliance": True,   # ≥ 6 photos
    "ai_confidence_score": 0.94,
    "report_completeness_score": 0.98,

    # Traceability
    "generated_from_report_id": "uuid",
    "generated_at": "2026-02-05T18:40:00Z",
    "regeneration_count": 0
}
```

**Indexes:**
- `{project_number: 1, report_date: -1}` — PM project trend
- `{report_date: -1}` — global daily rollup
- `{"delay_counts_by_category.utility_conflict": 1}` — delay-cause queries
- `{report_id: 1}` — traceback

## Backward compatibility contract

| Guarantee | Mechanism |
|---|---|
| Legacy V1 POSTs still succeed | `extra="allow"` accepts current shape; no field made required |
| Legacy V1 reads still succeed | V2 fields default to `null`/`[]`/`{}` in dashboards |
| Existing tests still pass | No existing field renamed / removed / retyped |
| Existing PDF unchanged | PDF renderer reads only legacy fields until DR-ROI-001F |
| HR crew-time flow unchanged | `masci_crews[]` shape untouched |
| Safety gate unchanged | 8 safety-escalation fields untouched |
| Excavation gate unchanged | `excavation_activity_today` + `linked_excavation_ids[]` untouched |
| Photo minimum unchanged | `photos[]` min 6 still enforced |
| Job Photos mirror unchanged | Mirror indexes existing photo lists; new `photo_ai_tags[]` added later without changing mirror |
| Audit trail unchanged | Trust-spine events keep firing on existing verbs |
| CSV export unchanged | V2 fields excluded from CSV until explicitly opted-in |

## Migration plan

- **Track B (this session):** No backend field additions. V2 shell scaffolding uses client-side state only.
- **Track C:** Add optional backend fields as documented above. Deploy alongside AI wiring.
- **Track E:** Add `daily_report_kpis` collection + submit-time upsert. Backfill script for historic reports optional.
- **Rollback path:** All V2 fields are additive; rolling back is drop-column safe.
