"""
Pydantic models for the Integration Center HTTP surface.

Hoisted to module scope (Pydantic 2.12 can't fully resolve closure
BaseModels at request time).
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ── Integration settings ─────────────────────────────────────────────
class IntegrationSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    demo_mode: Optional[bool] = None
    api_key: Optional[str] = None             # full secret — never echoed back
    webhook_secret: Optional[str] = None      # full secret — never echoed back
    settings: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


# ── Asset mapping ────────────────────────────────────────────────────
class AssetMappingCreate(BaseModel):
    masci_equipment_id: str = Field(..., min_length=1)
    motive_vehicle_id: Optional[str] = ""
    motive_asset_id: Optional[str] = ""
    motive_driver_id: Optional[str] = ""
    motive_device_id: Optional[str] = ""
    motive_gps_enabled: Optional[bool] = False
    motive_dashcam_enabled: Optional[bool] = False
    maintainx_asset_id: Optional[str] = ""
    maintainx_location_id: Optional[str] = ""
    maintainx_pm_schedule_id: Optional[str] = ""
    mapping_confidence: Optional[str] = "medium"   # low | medium | high
    mapping_notes: Optional[str] = ""


class AssetMappingUpdate(BaseModel):
    motive_vehicle_id: Optional[str] = None
    motive_asset_id: Optional[str] = None
    motive_driver_id: Optional[str] = None
    motive_device_id: Optional[str] = None
    motive_gps_enabled: Optional[bool] = None
    motive_dashcam_enabled: Optional[bool] = None
    maintainx_asset_id: Optional[str] = None
    maintainx_location_id: Optional[str] = None
    maintainx_pm_schedule_id: Optional[str] = None
    mapping_confidence: Optional[str] = None
    mapping_notes: Optional[str] = None
    active: Optional[bool] = None


# ── Employee / Driver mapping ────────────────────────────────────────
class EmployeeMappingCreate(BaseModel):
    masci_employee_id: str = Field(..., min_length=1)
    motive_driver_id: Optional[str] = ""
    motive_driver_name: Optional[str] = ""
    motive_email: Optional[str] = ""
    maintainx_user_id: Optional[str] = ""
    maintainx_name: Optional[str] = ""
    maintainx_email: Optional[str] = ""
    maintainx_role: Optional[str] = ""
    mapping_notes: Optional[str] = ""


class EmployeeMappingUpdate(BaseModel):
    motive_driver_id: Optional[str] = None
    motive_driver_name: Optional[str] = None
    motive_email: Optional[str] = None
    maintainx_user_id: Optional[str] = None
    maintainx_name: Optional[str] = None
    maintainx_email: Optional[str] = None
    maintainx_role: Optional[str] = None
    mapping_notes: Optional[str] = None
    active: Optional[bool] = None


# ── CSV import row schemas (lax — admin can match incomplete data) ──
class CsvImportPayload(BaseModel):
    kind: str = Field(...)                    # motive_vehicles | motive_drivers | maintainx_assets | maintainx_users
    rows: List[Dict[str, Any]] = Field(default_factory=list)


# ── Webhook test payload (only accepted when test_mode is enabled) ──
class WebhookTestPayload(BaseModel):
    event_type: Optional[str] = ""
    payload: Optional[Dict[str, Any]] = None


# ── Mappings Wizard ─────────────────────────────────────────────────
class WizardPreviewRow(BaseModel):
    """One pasted/uploaded row coming into the wizard. All fields are
    string-typed because the source is CSV/paste — we coerce later."""
    unit_number: Optional[str] = ""
    external_id: Optional[str] = ""
    external_name: Optional[str] = ""
    raw: Optional[Dict[str, Any]] = None        # keep original row for traceability


class WizardPreviewRequest(BaseModel):
    kind: str = Field(..., description="motive_vehicles | maintainx_assets")
    rows: List[WizardPreviewRow] = Field(default_factory=list)


class WizardDecision(BaseModel):
    """One reviewed-row commit instruction.

    action:
      - "create": create a new mapping for `masci_equipment_id`
      - "update": update existing mapping (`mapping_id`) for the provider
      - "skip":   record the row in the log as skipped (no DB write)
    force_overwrite must be true when overwriting a populated provider field.
    """
    action: str = Field(..., pattern="^(create|update|skip)$")
    masci_equipment_id: Optional[str] = None    # required for create/update
    mapping_id: Optional[str] = None            # required for update
    external_id: Optional[str] = ""             # the provider id pulled from CSV
    external_name: Optional[str] = ""
    force_overwrite: Optional[bool] = False
    notes: Optional[str] = ""


class WizardCommitRequest(BaseModel):
    kind: str = Field(..., description="motive_vehicles | maintainx_assets")
    source_label: Optional[str] = "paste"       # csv | paste | api — free-form
    decisions: List[WizardDecision] = Field(default_factory=list)
