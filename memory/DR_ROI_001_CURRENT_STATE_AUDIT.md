# DR-ROI-001 · Current State Audit

**Date:** 2026-02-05
**Method:** Read-only inventory of the entire Daily Report workflow.

## Frontend surface

| File | Lines | Role |
|---|---:|---|
| `frontend/src/pages/NewDailyReport.jsx` | **3,021** | The V1 mega-form used by supervisors in production |
| `frontend/src/pages/DailyReportsDashboard.jsx` | 243 | PM/admin listing dashboard |
| `frontend/src/lib/dailyReportSchema.js` | 112 | `buildDailyReportDefaults()` — frontend seed shape |
| `frontend/src/lib/dailyReportPayloadRepair.js` + `.test.js` | — | Payload normalization + tests |
| `frontend/src/lib/dailyReportScore.js` | — | Completeness scoring |
| `frontend/src/components/DailyReportLifecyclePanel.jsx` | — | Lifecycle panel embed |
| `frontend/src/components/CompletenessChip.jsx` | — | Completeness chip |
| `frontend/src/components/trench/DailyReportExcavationActivity.jsx` | — | JHA/JHP excavation gate |

## Backend surface

| File | Lines | Role |
|---|---:|---|
| `backend/routes/daily_reports.py` | **665** | `register_daily_reports_routes()` · full CRUD + audit endpoints |
| `backend/routes/daily_report_lifecycle.py` | — | Lifecycle status endpoints |
| `backend/routes/admin_dr_delivery_forensics.py` | — | Delivery forensics |
| `backend/routes/hr_portal.py` (392–529) | — | HR crew-time consumption |
| `backend/routes/dispatch_portal_auth.py` | — | Dispatch daily report reads |
| `backend/routes/field_leadership_portal.py` | — | Field Leadership reads |
| `backend/routes/safety_portal/daily_reports.py` | — | Safety portal linkage |
| `backend/routes/verification.py` | — | Public verification links |

## Backend Pydantic model — `DailyReportCreate`

Already Pydantic v2 idiomatic (Track 22.4A style):
```python
class DailyReportCreate(BaseModel):
    model_config = ConfigDict(extra="allow")  # ← V2 additive fields land safely
    project_name: str
    project_number: Optional[str] = ""
    location: str
    report_date: str
    report_number: Optional[str] = ""
    prepared_by: str
    superintendent: Optional[str] = ""

    # Weather
    weather_summary: Optional[str] = ""
    weather_snapshots: List[Dict[str, Any]] = Field(default_factory=list)

    # Gate flags
    schedule_delays: str = "No"
    schedule_delays_notes: str = ""
    weather_impact: str = "No"
    weather_impact_notes: str = ""
    safety_incidents_today: str = "No"
    injuries_reported: str = "No"
    incident_notes: str = ""
    safety_notified: str = ""
    safety_contact_person: str = ""
    safety_contact_time: str = ""
    incident_report_filled: str = ""
    incident_report_time: str = ""
    general_notes: str = ""

    # Repeating sections
    masci_crews: List[Dict[str, Any]] = default_factory=list  # HR-linked
    subcontractors: List[Dict[str, Any]]
    visitors: List[Dict[str, Any]]
    equipment: List[Dict[str, Any]]
    materials: List[Dict[str, Any]]         # inbound
    outbound_materials: List[Dict[str, Any]] # MM-ENTRY-002 · K-MM-1
    activities: List[Dict[str, Any]]

    # V.2 Wave-1A/B (already merged)
    production: List[ProductionRow]         # structured quantities
    constraints: List[ConstraintRow]        # structured delays

    # Narrative
    narrative_sections: Optional[Dict[str, str]]  # 6-prompt guided

    # Photos + attachments
    photos: List[str]                       # min 6 enforced
    attachments: List[Dict[str, Any]]

    # Signatures + gates
    prepared_by_signature: str
    superintendent_signature: str
    excavation_activity_today: str
    linked_excavation_ids: List[str]

    # Distribution
    distribution_list: List[str]
```

## Current API endpoints (from `daily_reports.py`)

| Method | Path | Role |
|---|---|---|
| POST | `/api/daily-reports` | Create (guarded by role check) |
| GET | `/api/daily-reports` | List (admin) |
| GET | `/api/daily-reports/next-number` | Auto-increment report number |
| GET | `/api/daily-reports/exposure-signals` | Public/CEI exposure flags |
| GET | `/api/daily-reports/audit-footer` | Audit-metadata footer |
| GET | `/api/daily-reports.csv` | CSV list (admin) |
| GET | `/api/daily-reports/{id}` | Read one |
| DELETE | `/api/daily-reports/{id}` | Delete (admin) |
| POST | `/api/daily-reports/attachments/upload` | Upload PDF/XLSX/CSV attachment (registered in `server.py:2895`) |

## Downstream consumers (must not break)

1. **HR Portal** (`hr_portal.py:392,529`) — reads `masci_crews[]` for HR-linked crew time
2. **Dispatch Portal** (`dispatch_portal_auth.py:421`)
3. **Field Leadership Portal** (`field_leadership_portal.py:691`)
4. **Safety Portal** (`safety_portal/daily_reports.py`)
5. **Verification API** (`verification.py:203`)
6. **Job Photos mirror** (Phase 1 read-only sync of `photos[]`) — `routes/job_photos.py.index_record_photos`
7. **Executive Overview** (`executive_overview.py`)
8. **Material Movement** (`material_movement.py:71`) — reads by `project_number` + `date`
9. **Admin DR Delivery Forensics** (`admin_dr_delivery_forensics.py:222`)
10. **Last Activity** (`last_activity.py`)
11. **Payroll Variance** (`payroll_variance.py`)
12. **Shop Intel** (`shop_intel.py`)
13. **Operations Actions API** (`operations_actions/api.py`)
14. **Admin Ops** (`admin_ops.py`)
15. **PM Routes** (`pm_routes.py`)

## Existing test coverage

| File | Coverage |
|---|---|
| `tests/test_daily_reports.py` | Core CRUD + validation |
| `tests/test_track_19_04_daily_report_attachments.py` | Attachment upload |
| `tests/test_track_19_05_daily_report_total_audit.py` | Audit trail |
| `tests/test_track_19_06_daily_report_progressive_disclosure.py` | Progressive-disclosure UX |
| `tests/test_track_19_07_daily_report_cognitive_ux.py` | Cognitive UX metrics |
| `frontend/src/lib/dailyReportPayloadRepair.test.js` | Payload normalization |
| `frontend/src/lib/__tests__/track_15_13h_session_classification.test.js` | Session classification |

## Critical workflows (MUST NOT BREAK)

- ✅ **HR-linked crew time** — `masci_crews[]` powers HR portal reads
- ✅ **Safety escalation gate** — `safety_incidents_today` / `injuries_reported` / `incident_notes` / `safety_notified` / `safety_contact_person` / `safety_contact_time` / `incident_report_filled` / `incident_report_time`
- ✅ **Excavation/JHA gate** — `excavation_activity_today=Yes` requires ≥ 1 linked excavation ID (backend 422)
- ✅ **Photo minimum** — 6 photos enforced (`photo_min: 6`)
- ✅ **Signature requirement** — `prepared_by_signature` + `superintendent_signature`
- ✅ **Job Photos mirror** — inline photos in `materials[].ticket_photos`, `subcontractors[].photos`, `photos[]` sync to Job Photos library
- ✅ **Audit trail** — trust-spine events emitted on create/update/delete
- ✅ **Report numbering** — auto-incremented via `/next-number`
- ✅ **Distribution list** — CC emails on PDF delivery
- ✅ **CSV export** — `/api/daily-reports.csv`
- ✅ **Delivery forensics** — admin DR delivery lookup

## Existing schema strengths (already V2-ready)

| Current schema field | DR-ROI-001 requirement | Status |
|---|---|---|
| `production[]` | Structured production quantities | 🟢 Present |
| `constraints[]` | Structured delays/constraints | 🟢 Present |
| `activities[]` | Activity narrative log | 🟡 Present but weak (needs Activity Cards) |
| `narrative_sections{}` | Structured 6-prompt narrative | 🟢 Present |
| `outbound_materials[]` | Materials leaving site | 🟢 Present |
| `equipment[]` | Equipment log | 🟢 Present |
| `weather_snapshots[]` | Multiple weather points | 🟢 Present |
| `photos[]` | Photo evidence | 🟢 Present (min 6) |
| `attachments[]` | Unified attachments | 🟢 Present |
| `excavation_activity_today` + `linked_excavation_ids[]` | Excavation gate | 🟢 Present |
| Safety gate fields | Safety escalation | 🟢 Present |
| `distribution_list[]` | Extra emails | 🟢 Present |

## Gap analysis (what DR-ROI-001 adds)

| New capability | Frontend | Backend | AI |
|---|---|---|---|
| **Activity Cards** (area/quantity/crew/equipment/photos linked) | 🔴 NEW | 🟡 Extend `activities[]` shape | — |
| **Constraint Chips** (structured taxonomy · click → follow-up) | 🔴 NEW | 🟡 Extend `constraints[]` shape | — |
| **Tomorrow Readiness** panel | 🔴 NEW | 🔴 New field `tomorrow_readiness{}` | Delay Agent |
| **AI Live Summary** UI + approval controls | 🔴 NEW | 🔴 New fields: `ai_operational_summary`, `final_approved_narrative`, `ai_confidence`, `ai_source_trace`, `ai_agent_outputs`, `ai_questions`, `supervisor_ai_approval_state` | Multi-agent |
| **PM Intelligence panel** | 🔴 NEW | 🔴 New collection `daily_report_kpis` (hybrid storage per user Q4) | PM Agent |
| **Photo Intelligence** (Vision tags · activity-link suggestions) | 🔴 NEW | 🔴 New field `photo_ai_tags[]` + `photo_activity_links[]` | GPT-5.2 Vision |
| **Confidence & Validation Agent** panel | 🔴 NEW | 🔴 Aggregated confidence + uncertainty flags | Confidence Agent |
| **Supervisor Approval panel** (accept/edit/regenerate + audit) | 🔴 NEW | 🔴 New field `ai_approval_log[]` | — |
| **PM Action Items** feed | 🔴 NEW | 🔴 New field `pm_action_items[]` | PM Agent |
| **V2 PDF layout** | — | 🔴 New PDF template (deferred per user Q5) | — |
| **V2 form shell (progressive)** | 🔴 NEW · this session | — | — |

## Duplicate workflows identified

1. Multiple narrative surfaces: `general_notes` + `narrative_sections{}` + `activities[].notes` + `constraints[]. notes` + freeform text scattered → **DR-ROI-001 consolidates into ONE approved AI narrative** with full source trace.
2. Two ways to express delays: `schedule_delays` + `schedule_delays_notes` (free text) vs `constraints[]` (structured) → **DR-ROI-001 makes structured chips authoritative**; free text becomes AI evidence only.
3. Two ways to express materials: `materials[]` + `outbound_materials[]` (already good) vs `activities[].material_placed` (buried) → **DR-ROI-001 links materials to Activity Cards explicitly**.

## Attestation

Zero code change in this audit. Baseline preserved verbatim. Ready for DR-ROI-001A + 001B execution per user directive.
