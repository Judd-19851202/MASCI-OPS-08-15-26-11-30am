"""
routes/odr/models.py — Pydantic envelope for Phase V.1 ODR.

Implements the full data model from ODR_DATA_MODEL.md + four
addenda (Delta D1–D8, Public-Link Device Continuity, Final
Governance, Coaching). Schema version = 2.

Implementation discipline:
  * `ConfigDict(extra="forbid")` everywhere — no silent field drift.
  * Optional fields default to None — never to mutable structures
    via class attributes (use Field(default_factory=...)).
  * Enum values match enums.py verbatim.
  * No business logic in models (validation only).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    AmendmentPortal, AmendmentRole, AttachmentKind, CoachingScope,
    CoachingSeverity, ConflictResolution, ConstraintType,
    ContinuityOutcome, CrewType, DelayType, ExtraWorkOrg,
    IssuedVia, LanguageAtEntry, MaterialEventKind, MaterialIssue,
    MaterialUom, PhotoTag, PipeMaterial, PreloadAttemptOutcome,
    PublicLinkScope, ReadinessScore, ReviewActionKind,
    ReviewActorRole, ReviewStatus, SafetyEventKind, SupportedLang,
    SyncState, TranslatedBy,
)


# ── Primitives ───────────────────────────────────────────────────────


class GeoFix(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float
    lng: float
    accuracy_m: Optional[float] = None


class WeatherFix(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = ""
    temp_f: Optional[float] = None
    wind_mph: Optional[float] = None
    precipitation_in: Optional[float] = None
    source: Optional[str] = None


class LocalizedString(BaseModel):
    """D6 · bilingual native. Stores canonical EN + original if non-EN."""
    model_config = ConfigDict(extra="forbid")
    text: str = ""
    original: Optional[str] = None
    original_lang: Optional[SupportedLang] = None
    translated_by: Optional[TranslatedBy] = None
    translated_at_utc: Optional[str] = None
    translation_model: Optional[str] = None
    translation_confidence: Optional[float] = None


class DeviceFingerprint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ua: str = ""
    os: str = ""
    os_version: str = ""
    app_version: str = ""
    is_pwa: bool = False
    is_secure_context: bool = True


# ── Section 1 · Project ──────────────────────────────────────────────


class ProjectSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str
    project_number: str
    project_name: str
    contract_number: Optional[str] = None
    report_date: str            # YYYY-MM-DD
    day_number: Optional[int] = None
    gps: Optional[GeoFix] = None
    gps_accuracy_m: Optional[float] = None
    time_created_local: str = ""
    time_created_utc: str = ""
    time_submitted_utc: Optional[str] = None
    foreman_uid: str = ""
    foreman_name: str = ""
    superintendent_uid: Optional[str] = None
    superintendent_name: Optional[str] = None
    pm_uid: Optional[str] = None
    pm_name: Optional[str] = None
    weather: WeatherFix = Field(default_factory=WeatherFix)
    weather_pulled_at_utc: Optional[str] = None


# ── Section 2 · Crew profile ─────────────────────────────────────────


class CrewProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    crew_id: str
    crew_name: str
    crew_type: CrewType
    primary_operation: str
    secondary_operations: List[str] = Field(default_factory=list)


# ── Section 2.5 · Work Areas (D2) ────────────────────────────────────


class WorkArea(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_area_id: str
    label: LocalizedString = Field(default_factory=LocalizedString)
    station_from: Optional[str] = None
    station_to: Optional[str] = None
    gps_centroid: Optional[GeoFix] = None
    timezone: Optional[str] = None
    notes: LocalizedString = Field(default_factory=LocalizedString)


# ── Section 3 · Manpower ─────────────────────────────────────────────


class ManpowerRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_uid: str
    name: str
    role: str
    classification: Optional[str] = None
    present: bool = True
    hours: float = 0.0
    overtime_hours: float = 0.0
    absent_reason: Optional[str] = None
    missing_personnel_flag: bool = False


class ManpowerBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: List[ManpowerRow] = Field(default_factory=list)
    total_hours: float = 0.0
    total_overtime: float = 0.0


# ── Section 4 · Equipment ────────────────────────────────────────────


class MaintenanceIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: str = "info"          # info | warn | critical
    description: str = ""
    photos: List[str] = Field(default_factory=list)
    auto_shop_ticket_id: Optional[str] = None


class EquipmentRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equipment_id: str
    asset_tag: str = ""
    description: str = ""
    hours: float = 0.0
    idle_hours: float = 0.0
    down_hours: float = 0.0
    utilization_pct: float = 0.0
    work_area_id: Optional[str] = None
    maintenance_issue: Optional[MaintenanceIssue] = None


class EquipmentBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: List[EquipmentRow] = Field(default_factory=list)


# ── Section 5 · Subcontractors ───────────────────────────────────────


class DeliveryNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: LocalizedString = Field(default_factory=LocalizedString)
    quantity: Optional[float] = None
    uom: Optional[str] = None
    ticket_number: Optional[str] = None


class IssueNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: LocalizedString = Field(default_factory=LocalizedString)
    severity: Optional[str] = None


class SubRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sub_id: Optional[str] = None
    name: str = ""
    present: bool = False
    work_performed: LocalizedString = Field(default_factory=LocalizedString)
    deliveries: List[DeliveryNote] = Field(default_factory=list)
    issues: List[IssueNote] = Field(default_factory=list)


class SubcontractorBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: List[SubRow] = Field(default_factory=list)


# ── Section 5.5 · Materials (D3) ─────────────────────────────────────


class MaterialEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_event_id: str
    work_area_id: Optional[str] = None
    kind: MaterialEventKind
    material_code: Optional[str] = None
    description: LocalizedString = Field(default_factory=LocalizedString)
    quantity: float = 0.0
    uom: MaterialUom = "other"
    vendor: Optional[str] = None
    ticket_numbers: List[str] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    issue: Optional[MaterialIssue] = None


# ── Section 6 · Production (polymorphic) ─────────────────────────────


class TestRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    value: Optional[float] = None
    unit: Optional[str] = None
    passed: Optional[bool] = None


class StructureSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    quantity: int = 1


class PipeRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pipe_size_in: float
    pipe_material: PipeMaterial
    lf_installed: float
    from_structure: Optional[str] = None
    to_structure: Optional[str] = None
    backfill_type: Optional[str] = None
    compaction_pct: Optional[float] = None
    testing: List[TestRecord] = Field(default_factory=list)


class PipeProduction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runs: List[PipeRun] = Field(default_factory=list)
    structures_set: List[StructureSet] = Field(default_factory=list)
    total_lf: float = 0.0
    total_structures: int = 0


class GenericProduction(BaseModel):
    """Catch-all for crew types whose sub-shapes are deferred to V.1.1."""
    model_config = ConfigDict(extra="forbid")
    notes: LocalizedString = Field(default_factory=LocalizedString)
    quantities: List[Dict[str, Any]] = Field(default_factory=list)


class ProductionBlock(BaseModel):
    """Polymorphic — exactly one sub-shape populated per CrewType."""
    model_config = ConfigDict(extra="forbid")
    pipe: Optional[PipeProduction] = None
    grading: Optional[GenericProduction] = None
    paving: Optional[GenericProduction] = None
    mot: Optional[GenericProduction] = None
    concrete: Optional[GenericProduction] = None
    structures: Optional[GenericProduction] = None
    milling: Optional[GenericProduction] = None
    survey: Optional[GenericProduction] = None
    electrical: Optional[GenericProduction] = None
    other: Optional[GenericProduction] = None


class ProductionSegment(BaseModel):
    """D1 · multiple operations per ODR."""
    model_config = ConfigDict(extra="forbid")
    segment_id: str
    crew_type: CrewType
    primary_operation: str
    work_area_id: Optional[str] = None
    started_at_utc: Optional[str] = None
    ended_at_utc: Optional[str] = None
    body: ProductionBlock = Field(default_factory=ProductionBlock)


# ── Section 7 · Delays ───────────────────────────────────────────────


class DelayEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delay_type: DelayType
    hours_lost: float = 0.0
    description: LocalizedString = Field(default_factory=LocalizedString)
    photos: List[str] = Field(default_factory=list)
    constraint_link_id: Optional[str] = None
    work_area_id: Optional[str] = None


class DelayBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    any_delays: bool = False
    entries: List[DelayEntry] = Field(default_factory=list)
    total_hours_lost: float = 0.0


# ── Section 8 · Extra work ───────────────────────────────────────────


class ExtraWorkEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requested_by: str = ""
    requested_by_org: Optional[ExtraWorkOrg] = None
    description: LocalizedString = Field(default_factory=LocalizedString)
    potential_cost_impact_usd: Optional[float] = None
    potential_schedule_impact_days: Optional[float] = None
    photos: List[str] = Field(default_factory=list)
    rfi_link_id: Optional[str] = None
    work_area_id: Optional[str] = None


class ExtraWorkBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    any_extra_work: bool = False
    entries: List[ExtraWorkEntry] = Field(default_factory=list)


# ── Section 9 · Constraints ──────────────────────────────────────────


class ConstraintEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    constraint_type: ConstraintType
    description: LocalizedString = Field(default_factory=LocalizedString)
    auto_operational_constraint_id: Optional[str] = None
    work_area_id: Optional[str] = None


class ConstraintBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entries: List[ConstraintEntry] = Field(default_factory=list)


# ── Section 10 · Safety (D7 per-event) ───────────────────────────────


class SafetyEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    event_kind: SafetyEventKind
    notified_safety: bool = False
    contact_name: Optional[str] = None
    contact_time_utc: Optional[str] = None
    incident_report_complete: bool = False
    incident_report_link_id: Optional[str] = None
    work_area_id: Optional[str] = None
    photos: List[str] = Field(default_factory=list)


class SafetyBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accident: bool = False
    incident: bool = False
    near_miss: bool = False
    property_damage: bool = False
    environmental_release: bool = False
    injury: bool = False
    any_event: bool = False
    events: List[SafetyEvent] = Field(default_factory=list)


# ── Section 11 · Weather impact ──────────────────────────────────────


class WeatherImpactBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weather_impacted_work: bool = False
    hours_lost: Optional[float] = None
    description: LocalizedString = Field(default_factory=LocalizedString)


# ── Section 12 · Photos ──────────────────────────────────────────────


class PhotoRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_id: str
    tag: PhotoTag = "general"
    voice_caption: Optional[LocalizedString] = None
    text_caption: Optional[LocalizedString] = None
    captured_at_utc: str = ""
    captured_at_local: str = ""
    gps: Optional[GeoFix] = None
    section_anchor: Optional[str] = None
    work_area_id: Optional[str] = None
    photo_governance_id: Optional[str] = None


# ── Section 13 · Tomorrow plan ───────────────────────────────────────


class TomorrowPlanBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    planned_work: LocalizedString = Field(default_factory=LocalizedString)
    required_resources: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)


# ── Section 14 · Plan vs actual ──────────────────────────────────────


class PlanVsActualBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    completed_planned_work: bool = True
    variance_reason: Optional[LocalizedString] = None
    schedule_impact_days: Optional[float] = None


# ── Section 15 · Readiness (coaching · O36–O50) ──────────────────────


class CoachingPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt_key: str
    text: LocalizedString = Field(default_factory=LocalizedString)
    section_anchor: str = ""
    severity: CoachingSeverity = "nudge"


class ReadinessSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluated_at_utc: str = ""
    missing_required: List[str] = Field(default_factory=list)
    coaching_prompts: List[CoachingPrompt] = Field(default_factory=list)
    hard_stops: List[str] = Field(default_factory=list)
    score: ReadinessScore = "draft"


# ── Section 16 · Review ──────────────────────────────────────────────


class ReviewEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_uid: str
    actor_role: ReviewActorRole
    action: ReviewActionKind
    note: Optional[str] = None
    at_utc: str


class ReviewBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pm_reviewer_uid: Optional[str] = None
    status_history: List[ReviewEvent] = Field(default_factory=list)


# ── D4 · Reliability envelope ────────────────────────────────────────


class SyncConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    section: str
    detected_at_utc: str
    server_value_hash: str
    client_value_hash: str
    resolution: ConflictResolution = "unresolved"
    resolved_at_utc: Optional[str] = None


class ReliabilityBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    autosave_enabled: bool = True
    autosave_interval_s: int = 5
    last_autosave_at_utc: Optional[str] = None
    autosave_count: int = 0
    last_known_good_section: Optional[str] = None
    recovery_token: Optional[str] = None
    offline_origin: bool = False
    offline_session_id: Optional[str] = None
    offline_photo_queue_size: int = 0
    offline_photo_queue_drained_at_utc: Optional[str] = None
    sync_state: SyncState = "clean"
    last_sync_at_utc: Optional[str] = None
    sync_conflicts: List[SyncConflict] = Field(default_factory=list)
    device_fingerprint: DeviceFingerprint = Field(default_factory=DeviceFingerprint)


# ── D5 · Completion telemetry ────────────────────────────────────────


class CompletionTelemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seconds_to_submit: Optional[float] = None
    section_visit_times: Dict[str, float] = Field(default_factory=dict)
    auto_fill_accept_rate: Dict[str, float] = Field(default_factory=dict)
    voice_caption_count: int = 0
    voice_caption_chars: int = 0
    autosave_count: int = 0
    language_at_entry: LanguageAtEntry = "en"


# ── Continuity (O11–O20) ─────────────────────────────────────────────


class DeviceToken(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token_id: str
    token_hash: str
    issued_at_utc: str
    last_seen_at_utc: str
    expires_at_utc: str
    issued_to_fingerprint: DeviceFingerprint
    issued_via: IssuedVia = "foreman_first_use"
    issuer_uid: Optional[str] = None
    note: Optional[str] = None
    revoked_at_utc: Optional[str] = None


class ContinuitySignals(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fingerprint_match: bool = False
    token_match: bool = False
    project_match: bool = False
    link_match: bool = False
    date_in_window: bool = False
    gps_proximity_ok: Optional[bool] = None
    prior_identity_match: Optional[bool] = None
    explicit_conflict: bool = False


class DeviceContinuityBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signals: ContinuitySignals = Field(default_factory=ContinuitySignals)
    outcome: ContinuityOutcome = "denied_no_prior"
    evaluated_at_utc: str = ""
    prior_odr_id: Optional[str] = None


class PublicAccessBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    link_id: str = ""
    link_scope: PublicLinkScope = "project_crew"
    link_created_at_utc: str = ""
    link_created_by_uid: str = ""
    link_revoked_at_utc: Optional[str] = None
    device_tokens: List[DeviceToken] = Field(default_factory=list)
    continuity: DeviceContinuityBlock = Field(default_factory=DeviceContinuityBlock)


# ── Final Governance (O21–O35) ───────────────────────────────────────


class ForemanAck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acknowledged: bool = False
    acknowledged_at_utc: Optional[str] = None
    acknowledged_by_uid: str = ""
    acknowledged_from_fingerprint: Optional[DeviceFingerprint] = None
    text: str = ""


class SignatureBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    foreman_acknowledgement: ForemanAck = Field(default_factory=ForemanAck)


class AttachmentRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attachment_id: str


# ── Top-level ODR envelope ───────────────────────────────────────────


class ODR(BaseModel):
    """The Operational Daily Record · schema_version=2 · M0.1."""
    model_config = ConfigDict(extra="forbid")

    id: str
    doc_id: str
    schema_version: int = 2
    legacy_daily_report_id: Optional[str] = None

    project: ProjectSnapshot
    crew_profile: CrewProfile
    work_areas: List[WorkArea] = Field(default_factory=list)
    manpower: ManpowerBlock = Field(default_factory=ManpowerBlock)
    equipment: EquipmentBlock = Field(default_factory=EquipmentBlock)
    subcontractors: SubcontractorBlock = Field(default_factory=SubcontractorBlock)
    materials: List[MaterialEvent] = Field(default_factory=list)
    production_segments: List[ProductionSegment] = Field(default_factory=list)
    delays: DelayBlock = Field(default_factory=DelayBlock)
    extra_work: ExtraWorkBlock = Field(default_factory=ExtraWorkBlock)
    constraints: ConstraintBlock = Field(default_factory=ConstraintBlock)
    safety: SafetyBlock = Field(default_factory=SafetyBlock)
    weather_impact: WeatherImpactBlock = Field(default_factory=WeatherImpactBlock)
    photos: List[PhotoRef] = Field(default_factory=list)
    tomorrow: TomorrowPlanBlock = Field(default_factory=TomorrowPlanBlock)
    plan_vs_actual: PlanVsActualBlock = Field(default_factory=PlanVsActualBlock)
    readiness: ReadinessSnapshot = Field(default_factory=ReadinessSnapshot)
    review: ReviewBlock = Field(default_factory=ReviewBlock)

    reliability: ReliabilityBlock = Field(default_factory=ReliabilityBlock)
    completion_telemetry: CompletionTelemetry = Field(default_factory=CompletionTelemetry)

    public_access: PublicAccessBlock = Field(default_factory=PublicAccessBlock)

    signature: SignatureBlock = Field(default_factory=SignatureBlock)
    attachments: List[AttachmentRef] = Field(default_factory=list)

    amend_allowed_until_utc: Optional[str] = None
    amendment_count: int = 0
    last_amended_at_utc: Optional[str] = None
    last_amended_by_uid: Optional[str] = None

    prior_report_preload_allowed: bool = False
    preload_denial_reason: Optional[str] = None

    status: ReviewStatus = "draft"
    created_at: str
    submitted_at: Optional[str] = None
    last_edited_at: str
    last_edited_by_uid: str
    submitted_by_uid: Optional[str] = None
    location_at_submit: Optional[GeoFix] = None
    location_accuracy_m: Optional[float] = None
    device_session_id: Optional[str] = None
    schema_violations: List[str] = Field(default_factory=list)
    consumer_dispatch: Dict[str, str] = Field(default_factory=dict)


# ── Input / output DTOs ──────────────────────────────────────────────


class ODRCreate(BaseModel):
    """Minimal input to start an ODR draft. Everything else is patched in."""
    model_config = ConfigDict(extra="forbid")
    project: ProjectSnapshot
    crew_profile: CrewProfile


class ODRPatch(BaseModel):
    """Partial update. All keys optional; only present keys are written."""
    model_config = ConfigDict(extra="forbid")
    project: Optional[ProjectSnapshot] = None
    crew_profile: Optional[CrewProfile] = None
    work_areas: Optional[List[WorkArea]] = None
    manpower: Optional[ManpowerBlock] = None
    equipment: Optional[EquipmentBlock] = None
    subcontractors: Optional[SubcontractorBlock] = None
    materials: Optional[List[MaterialEvent]] = None
    production_segments: Optional[List[ProductionSegment]] = None
    delays: Optional[DelayBlock] = None
    extra_work: Optional[ExtraWorkBlock] = None
    constraints: Optional[ConstraintBlock] = None
    safety: Optional[SafetyBlock] = None
    weather_impact: Optional[WeatherImpactBlock] = None
    photos: Optional[List[PhotoRef]] = None
    tomorrow: Optional[TomorrowPlanBlock] = None
    plan_vs_actual: Optional[PlanVsActualBlock] = None
    reliability: Optional[ReliabilityBlock] = None
    completion_telemetry: Optional[CompletionTelemetry] = None
    signature: Optional[SignatureBlock] = None


class ODRSubmit(BaseModel):
    """Submit transition body. May carry final reliability + signature."""
    model_config = ConfigDict(extra="forbid")
    location_at_submit: Optional[GeoFix] = None
    signature_text: Optional[str] = None
    device_fingerprint: Optional[DeviceFingerprint] = None


class SectionEventCreate(BaseModel):
    """Append-only telemetry row · `odr_section_events`."""
    model_config = ConfigDict(extra="forbid")
    section: str               # field path · e.g. "production_segments[0].body.pipe.runs[1].lf_installed"
    action: str                # e.g. "value_changed" · "added" · "removed"
    note: Optional[str] = None
    old_value_hash: Optional[str] = None
    new_value_hash: Optional[str] = None


# ── Amendment (post-24h-window · Super+) ─────────────────────────────


class AmendmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_path: str
    old_value: Any
    new_value: Any
    reason: LocalizedString
    triggers_pdf_rerender: bool = False


__all__ = [
    "ODR", "ODRCreate", "ODRPatch", "ODRSubmit",
    "SectionEventCreate", "AmendmentCreate",
    "ProjectSnapshot", "CrewProfile", "WorkArea",
    "ManpowerBlock", "ManpowerRow",
    "EquipmentBlock", "EquipmentRow", "MaintenanceIssue",
    "SubcontractorBlock", "SubRow", "DeliveryNote", "IssueNote",
    "MaterialEvent",
    "ProductionSegment", "ProductionBlock", "PipeProduction", "PipeRun",
    "GenericProduction", "TestRecord", "StructureSet",
    "DelayBlock", "DelayEntry",
    "ExtraWorkBlock", "ExtraWorkEntry",
    "ConstraintBlock", "ConstraintEntry",
    "SafetyBlock", "SafetyEvent",
    "WeatherImpactBlock",
    "PhotoRef",
    "TomorrowPlanBlock", "PlanVsActualBlock",
    "ReadinessSnapshot", "CoachingPrompt",
    "ReviewBlock", "ReviewEvent",
    "ReliabilityBlock", "SyncConflict",
    "CompletionTelemetry",
    "PublicAccessBlock", "DeviceContinuityBlock", "ContinuitySignals", "DeviceToken",
    "SignatureBlock", "ForemanAck", "AttachmentRef",
    "GeoFix", "WeatherFix", "LocalizedString", "DeviceFingerprint",
]
