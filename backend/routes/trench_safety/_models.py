"""Pydantic models + status enums for trench-safety operations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
import uuid


# ────────────────────────────────────────────────────────────────────────
# Enums (string sets — not python Enum so they JSON-serialise cleanly)
# ────────────────────────────────────────────────────────────────────────

ASSET_TYPES = (
    "Trench Box",
    "End Panel",
    "Spreader Bar",
    "Hydraulic Shore",
    "Slide Rail System",
    "Trench Jack",
    "Ladder",
    "Accessory",
)

CONDITIONS = ("Excellent", "Good", "Fair", "Poor", "Out Of Service")

OPERATIONAL_STATUSES = (
    "Available",
    "Assigned",
    "In Transport",
    "Inspection Hold",
    "Repair",
    "Retired",
)

INSPECTION_TYPES = ("Daily Visual", "Monthly Competent Person", "Annual Review")
INSPECTION_RESULTS = ("Pass", "Fail", "Pending Review")

REPAIR_STATUSES = ("Open", "In Progress", "Completed")

DEPLOYMENT_SOURCES = (
    "Manual Assignment",
    "Daily Report",
    "Project Equipment List",
    "Dispatch / Transport Log",
    "Admin Adjustment",
)

PHOTO_CATEGORIES = (
    "Front", "Rear", "Side", "Serial Number", "Manufacturer Plate",
    "Inspection Photo", "Damage Photo", "Repair Photo", "QR Label Photo",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────────────────────────────────────────────────────
# Asset
# ────────────────────────────────────────────────────────────────────────

class TrenchSafetyAssetCreate(BaseModel):
    """Admin/Safety payload for creating a new physical asset.

    `asset_id` is REQUIRED and PERMANENT — once created it never changes.
    """
    model_config = ConfigDict(extra="ignore")

    asset_id: str = Field(min_length=1, max_length=64)
    asset_type: str = "Trench Box"

    # General
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    year_manufactured: Optional[int] = None
    owner: str = "MASCI"
    purchase_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    notes: str = ""

    # Physical
    size: str = ""
    length_ft: Optional[float] = None
    width_min_ft: Optional[float] = None
    width_max_ft: Optional[float] = None
    height_ft: Optional[float] = None
    weight_lbs: Optional[float] = None
    rated_depth_ft: Optional[float] = None
    rated_soil_type: str = ""
    adjustable_range: str = ""
    capacity: str = ""

    # Appearance
    color: str = ""
    paint_condition: str = ""
    corrosion_level: str = ""

    # Condition
    condition: str = "Good"
    operational_status: str = "Available"

    # Location
    current_location: str = "MASCI Yard"
    current_project_id: Optional[str] = None
    current_project_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_to_role: Optional[str] = None
    yard_location: str = "MASCI Yard"

    # Manufacturer reference link
    manufacturer_ref_id: Optional[str] = None

    # Data-quality flags (admin-set during seeding/import)
    missing_serial_number: bool = False
    missing_manufacturer: bool = False
    needs_review: bool = False


class TrenchSafetyAssetUpdate(BaseModel):
    """Edit payload — every field optional. asset_id NOT included
    (immutable). asset_type NOT included (immutable post-create)."""
    model_config = ConfigDict(extra="ignore")

    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    year_manufactured: Optional[int] = None
    owner: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    notes: Optional[str] = None

    size: Optional[str] = None
    length_ft: Optional[float] = None
    width_min_ft: Optional[float] = None
    width_max_ft: Optional[float] = None
    height_ft: Optional[float] = None
    weight_lbs: Optional[float] = None
    rated_depth_ft: Optional[float] = None
    rated_soil_type: Optional[str] = None
    adjustable_range: Optional[str] = None
    capacity: Optional[str] = None

    color: Optional[str] = None
    paint_condition: Optional[str] = None
    corrosion_level: Optional[str] = None

    condition: Optional[str] = None
    # operational_status changes go through /status (lifecycle gate)

    current_location: Optional[str] = None
    yard_location: Optional[str] = None

    manufacturer_ref_id: Optional[str] = None

    missing_serial_number: Optional[bool] = None
    missing_manufacturer: Optional[bool] = None
    needs_review: Optional[bool] = None


class RetireAssetBody(BaseModel):
    retired_reason: str = Field(min_length=1, max_length=500)


class StatusChangeBody(BaseModel):
    operational_status: str = Field(min_length=1)
    note: Optional[str] = None


# ────────────────────────────────────────────────────────────────────────
# Inspection
# ────────────────────────────────────────────────────────────────────────

class InspectionChecklistItem(BaseModel):
    key: str
    label: str
    result: str  # "Pass" | "Fail" | "N/A"
    note: Optional[str] = ""


class InspectionSubmit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    inspection_type: str = "Daily Visual"
    inspector_name: str = Field(min_length=1, max_length=200)
    inspector_role: str = ""
    competent_person_confirmed: bool = False
    checklist: List[InspectionChecklistItem] = Field(default_factory=list)
    findings: str = ""
    corrective_actions: str = ""
    result: str = "Pass"  # Pass | Fail | Pending Review
    photo_refs: List[str] = Field(default_factory=list)


# ────────────────────────────────────────────────────────────────────────
# Repair
# ────────────────────────────────────────────────────────────────────────

class RepairCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    issue_description: str = Field(min_length=1, max_length=2000)
    reported_by: Optional[str] = None
    photo_refs: List[str] = Field(default_factory=list)
    repair_vendor: Optional[str] = None
    repair_cost: Optional[float] = None
    requires_reinspection: bool = True


class RepairUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Optional[str] = None        # Open | In Progress | Completed
    completion_notes: Optional[str] = None
    repair_vendor: Optional[str] = None
    repair_cost: Optional[float] = None
    photo_refs: Optional[List[str]] = None
    requires_reinspection: Optional[bool] = None


# ────────────────────────────────────────────────────────────────────────
# Deployment
# ────────────────────────────────────────────────────────────────────────

class DeploymentAssign(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    assigned_by: Optional[str] = None
    source: str = "Manual Assignment"
    condition_at_assign: Optional[str] = None
    notes: Optional[str] = None


class DeploymentReturn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    returned_by: Optional[str] = None
    condition_at_return: Optional[str] = None
    notes: Optional[str] = None


# ────────────────────────────────────────────────────────────────────────
# Damage report (public intake)
# ────────────────────────────────────────────────────────────────────────

DAMAGE_REPORT_KINDS = ("Damage", "Unsafe Condition", "Missing Pins", "Missing Labels")


class DamageReportPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    asset_id: str = Field(min_length=1, max_length=64)
    kind: str = Field(default="Damage", max_length=64)
    description: str = Field(min_length=5, max_length=2000)
    reported_by_name: Optional[str] = Field(default=None, max_length=200)
    contact: Optional[str] = Field(default=None, max_length=200)
