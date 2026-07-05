# DR-ROI-001 · V2 Architecture

**Date:** 2026-02-05

## System-level shape

```
┌─────────────────────────────────────────────────────────────────┐
│  Field Device (iPad/phone/ToughBook)                            │
│                                                                 │
│  frontend/src/pages/daily-report-v2/                            │
│    DailyReportV2.jsx          # progressive shell               │
│    sections/DaySetup          # project, date, shift, weather   │
│    sections/CrewTime          # HR-linked (existing model)      │
│    sections/Equipment         # existing model, minor extend    │
│    sections/ActivityCards     # NEW · replaces activities[]     │
│    sections/ConstraintChips   # NEW · replaces constraints[]    │
│    sections/TomorrowReady     # NEW · readiness signals         │
│    sections/SafetyQuality     # existing gates, simplified UI   │
│    sections/PhotosSection     # existing min-6, linkable        │
│    sections/AISummary         # NEW · placeholder (Track C)     │
│    sections/SignatureSubmit   # existing signature flow         │
│    panels/PmIntelligencePanel # NEW · placeholder (Track E)     │
│    panels/PhotoIntelPanel     # NEW · placeholder (Track D)     │
│    panels/ConfidencePanel     # NEW · placeholder (Track C)     │
│    panels/SupervisorApproval  # NEW · placeholder (Track C)     │
│                                                                 │
│  Feature flag:  isV2Enabled(user, project)                      │
│                                                                 │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │  (V1 submit path unchanged)
               │  POST /api/daily-reports   {legacy schema}
               │
               │  (V2 submit path adds fields via extra=allow)
               │  POST /api/daily-reports   {legacy schema + V2 add}
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend · backend/routes/daily_reports.py                      │
│    DailyReportCreate(BaseModel)                                 │
│    model_config = ConfigDict(extra="allow")   ← key to V2       │
│    ...existing 30+ fields...                                    │
│    # V2 additive (Track A/B: docs only)                         │
│    activity_cards: List[Dict] = []                              │
│    constraint_cards: List[Dict] = []                            │
│    tomorrow_readiness: Optional[Dict] = None                    │
│    ai_operational_summary: Optional[str] = None                 │
│    ai_agent_outputs: Optional[Dict] = None                      │
│    ai_questions: List[Dict] = []                                │
│    ai_confidence: Optional[float] = None                        │
│    ai_source_trace: Optional[Dict] = None                       │
│    pm_action_items: List[Dict] = []                             │
│    photo_ai_tags: List[Dict] = []                               │
│    photo_activity_links: List[Dict] = []                        │
│    final_approved_narrative: Optional[str] = None               │
│    supervisor_ai_approval_state: Optional[str] = None           │
│    ai_approval_log: List[Dict] = []                             │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │  On submit (Track E hybrid write):
               │    1. Save whole doc → daily_reports (immutable)
               │    2. Extract & upsert normalized KPIs → daily_report_kpis
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Analytics Layer · daily_report_kpis (new)                      │
│    { report_id, project_number, date, shift,                    │
│      production_by_activity[], production_by_area[],            │
│      crew_hours_by_activity[], equip_hours_by_activity[],       │
│      material_loads_in, material_loads_out, truck_count,        │
│      weather_delay_hours, equip_delay_hours,                    │
│      delay_counts_by_category, extra_work_events,               │
│      open_pm_actions, unresolved_safety, unresolved_quality,    │
│      tomorrow_readiness_risks, photo_compliance,                │
│      ai_confidence_score, report_completeness_score,            │
│      generated_from_report_id, generated_at }                   │
└──────────────┬──────────────────────────────────────────────────┘
               │
               │  PM dashboards + trend cards + Executive Overview
               │  (Track E scope)
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI Layer · Multi-agent (Track C · not wired this session)      │
│                                                                 │
│    Structured facts + photos                                    │
│    │                                                            │
│    ├── Operations Agent      (Claude Sonnet 4.5)                │
│    ├── Equipment Agent       (Claude Sonnet 4.5)                │
│    ├── Delay Agent           (Claude Sonnet 4.5)                │
│    ├── Safety Agent          (Claude Sonnet 4.5)                │
│    ├── Quality Agent         (Claude Sonnet 4.5)                │
│    ├── Photo Vision Agent    (GPT-5.2 Vision)  ← evidence only  │
│    ├── PM Intelligence Agent (Claude Sonnet 4.5)                │
│    ├── Narrative Agent       (Claude Sonnet 4.5) ← final draft  │
│    └── Confidence Agent      (Claude Sonnet 4.5) ← scores all   │
│                                                                 │
│    Trigger model: hybrid+ event-driven (Track C)                │
│      - Debounced field-change events → light agents             │
│      - Explicit "Preview AI Summary" → Narrative + Vision       │
│      - Cached per-agent evidence hash                           │
│                                                                 │
│    Approval flow:                                               │
│      draft → confidence score → supervisor edits or accepts     │
│      → final_approved_narrative → submit                        │
└─────────────────────────────────────────────────────────────────┘
```

## Design principles

1. **Feature-flagged rollout** — V2 lives at `/daily-report/v2`; V1 remains at `/new-daily-report`. Zero disruption to production submitters.
2. **Additive backend schema only** — `extra="allow"` guarantees legacy clients keep working. V2 fields are all optional with safe defaults.
3. **Supervisor is the source of truth** — AI generates evidence-traceable narrative; supervisor accepts/edits before submit.
4. **Best-of-breed AI** — Claude Sonnet 4.5 for reasoning + narrative; GPT-5.2 Vision only for photo evidence; Confidence Agent flags uncertainty.
5. **Hybrid+ event-driven AI** — lightweight agents debounced on field changes; heavy agents (Narrative, Vision) explicit or pre-submit only.
6. **Hybrid storage** — immutable report doc + separate `daily_report_kpis` collection for analytics; every KPI traces to its report.
7. **PDF v2 architected but deferred** — current PDF stays byte-for-byte until V2 workflow is certified end-to-end.
8. **Zero AI invention** — every AI sentence must trace to an evidence node.

## Subtrack map

| Subtrack | Scope | Session |
|---|---|---|
| **DR-ROI-001A** | Current State Audit + Schema Plan + all 14 planning docs | 🟢 THIS SESSION |
| **DR-ROI-001B (expanded)** | V2 shell scaffolding · Activity Cards · Constraint Chips · Tomorrow Readiness · placeholders · feature flag · route wiring · zero V1 disruption · no AI wiring | 🟢 THIS SESSION |
| **DR-ROI-001C** | Multi-agent AI wiring (Claude Sonnet 4.5 for reasoning · Confidence Agent · Narrative Agent · Supervisor Approval flow · source trace + audit) | ⏳ next session |
| **DR-ROI-001D** | Photo Vision (GPT-5.2 Vision) · photo_ai_tags · photo_activity_links · evidence-back-to-agents | ⏳ next session |
| **DR-ROI-001E** | PM Intelligence KPI dashboard · `daily_report_kpis` collection · aggregation pipelines · trend cards | ⏳ next session |
| **DR-ROI-001F** | V2 PDF template · dual-render harness · cutover flag · executive layout | ⏳ next session |
| **DR-ROI-001G** | Full regression · Playwright per-portal · testing agent · deployment certification | ⏳ final session |
