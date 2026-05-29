"""
routes/odr/enums.py — closed-set vocabulary for ODR.

Source of truth — mirrored client-side in `frontend/src/lib/odrEnums.js`
once the UI ships. Every value here MUST appear in
/app/memory/ODR_DATA_MODEL.md.
"""
from __future__ import annotations

from typing import Literal

# ── Section 2 · Crew profile ─────────────────────────────────────────
CrewType = Literal[
    "pipe", "utility", "grading", "fine_grade", "stabilization",
    "concrete", "structures", "curb", "sidewalk", "milling", "paving",
    "mot", "survey", "airfield", "electrical", "other",
]

# ── Section 7 · Delays ───────────────────────────────────────────────
DelayType = Literal[
    "weather", "utility", "survey", "cei", "owner", "faa", "mot",
    "material", "equipment", "staffing", "other",
]

# ── Section 8 · Extra work ───────────────────────────────────────────
ExtraWorkOrg = Literal["owner", "cei", "designer", "faa", "fdot", "other"]

# ── Section 9 · Constraints ──────────────────────────────────────────
ConstraintType = Literal[
    "utility", "survey", "design", "access",
    "staffing", "material", "equipment", "other",
]

# ── Section 12 · Photos ──────────────────────────────────────────────
PhotoTag = Literal[
    "production", "delay", "extra_work", "safety",
    "qc", "equipment", "mot", "weather", "general",
]

# ── Section 6 pipe sub-block ─────────────────────────────────────────
PipeMaterial = Literal["RCP", "HDPE", "PVC", "DI", "CMP", "other"]

# ── Section 16 · Review ──────────────────────────────────────────────
ReviewStatus = Literal["draft", "submitted", "returned", "approved"]

# ── Section 15 · Readiness ───────────────────────────────────────────
ReadinessScore = Literal["draft", "ready", "needs_attention", "blocked"]

# ── Section 10 · Safety ──────────────────────────────────────────────
SafetyEventKind = Literal[
    "accident", "incident", "near_miss",
    "property_damage", "environmental_release", "injury",
]

# ── D3 · Materials ───────────────────────────────────────────────────
MaterialEventKind = Literal[
    "delivered", "consumed", "staged", "returned",
    "wasted", "rejected", "short",
]
MaterialUom = Literal["ton", "cy", "lf", "sf", "ea", "gal", "other"]
MaterialIssue = Literal["shortage", "reject", "damage", "wrong_material"]

# ── D4 · Reliability ─────────────────────────────────────────────────
SyncState = Literal["clean", "pending", "conflict", "error"]
ConflictResolution = Literal["server_wins", "client_wins", "merged", "unresolved"]

# ── D5 · Telemetry ───────────────────────────────────────────────────
LanguageAtEntry = Literal["en", "es", "mixed"]

# ── D6 · Bilingual ───────────────────────────────────────────────────
SupportedLang = Literal["en", "es"]
TranslatedBy = Literal["model", "operator", "none"]

# ── Continuity (O11–O20) ─────────────────────────────────────────────
PublicLinkScope = Literal["project", "project_crew"]
IssuedVia = Literal["foreman_first_use", "admin_override", "pm_override"]
ContinuityOutcome = Literal[
    "allowed",
    "denied_device_mismatch",
    "denied_missing_token",
    "denied_expired_context",
    "denied_wrong_project",
    "denied_wrong_link",
    "denied_date_out_of_window",
    "denied_gps_conflict",
    "denied_no_prior",
]
PreloadAttemptOutcome = Literal[
    "allowed",
    "denied_device_mismatch",
    "denied_missing_token",
    "denied_expired_context",
    "denied_wrong_project",
    "denied_wrong_link",
    "denied_date_out_of_window",
    "denied_gps_conflict",
    "denied_no_prior",
    "override_used",
]

# ── Governance (O21–O35) ─────────────────────────────────────────────
AttachmentKind = Literal[
    "delivery_ticket", "haul_ticket", "density_report",
    "asphalt_ticket", "concrete_ticket",
    "cei_directive", "faa_notice", "fdot_directive",
    "rfi_attachment", "other_pdf", "other_image",
]
AmendmentRole = Literal[
    "foreman", "superintendent", "senior_superintendent", "admin",
]
AmendmentPortal = Literal["field_leadership", "admin"]
ReviewActionKind = Literal["submit", "return", "approve"]
ReviewActorRole = Literal["pm", "superintendent", "admin"]

# ── Coaching (O36–O50) ───────────────────────────────────────────────
CoachingSeverity = Literal["nudge", "suggest", "strong_suggest"]
CoachingScope = Literal["project", "region", "platform"]

# ── Field Leadership Levels (FLL-1..FLL-6) ───────────────────────────
FLL = Literal["FLL-1", "FLL-2", "FLL-3", "FLL-4", "FLL-5", "FLL-6"]
VisibilityVerb = Literal["FULL", "LIMITED", "SUMMARY", "NONE"]


__all__ = [
    "CrewType", "DelayType", "ExtraWorkOrg", "ConstraintType",
    "PhotoTag", "PipeMaterial", "ReviewStatus", "ReadinessScore",
    "SafetyEventKind", "MaterialEventKind", "MaterialUom", "MaterialIssue",
    "SyncState", "ConflictResolution", "LanguageAtEntry",
    "SupportedLang", "TranslatedBy",
    "PublicLinkScope", "IssuedVia", "ContinuityOutcome", "PreloadAttemptOutcome",
    "AttachmentKind", "AmendmentRole", "AmendmentPortal",
    "ReviewActionKind", "ReviewActorRole",
    "CoachingSeverity", "CoachingScope",
    "FLL", "VisibilityVerb",
]
