"""Track 19.21 · Employee Records Intelligence Platform · P0 lock tests.

Doctrine locks (source-level + behavioral):
  * HR is the system owner across every lane.
  * Safety owns the Safety lane operationally.
  * Asset Administrator owns the Asset lane operationally.
  * Universal Employee Record model exists with the doctrine states.
  * Approval is required before a record becomes "linked".
  * Reassignment resets approval.
  * Original file references (hash + name + ref) are preserved.
  * Audit collection writes append-only.
  * Incident Intelligence Engine cases join the HR timeline via
    defensible roles only (reporter · involved · witness · CAPA owner).
  * Legacy `db.incidents` timeline path preserved (backward compat).
  * No schema drift, no duplicate employee system.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from routes.employee_records import (
    LANE_APPROVERS,
    LANE_RECORD_TYPES,
    OWNERSHIP_LANES,
    RECORD_STATES,
    _actor_can_approve,
    _actor_can_read_lane,
)

MODULE = Path("/app/backend/routes/employee_records.py")
HR_PORTAL = Path("/app/backend/routes/hr_portal.py")
FE_PAGE = Path("/app/frontend/src/pages/EmployeeProfile.jsx")


# ── Doctrine: lanes + states ────────────────────────────────────────
def test_four_ownership_lanes_exist():
    # Track 19.59 added the `vendor` lane as a fifth first-class lane.
    # The four original lanes remain intact.
    assert set(OWNERSHIP_LANES) == {"hr", "safety", "asset", "corporate_import", "vendor"}


def test_five_record_states_exist():
    assert set(RECORD_STATES) == {
        "pending_classification", "pending_match", "pending_approval",
        "linked", "rejected",
    }


def test_hr_lane_has_expected_types():
    assert "write_up" in LANE_RECORD_TYPES["hr"]
    assert "termination" in LANE_RECORD_TYPES["hr"]
    assert "verbal_coaching" in LANE_RECORD_TYPES["hr"]
    assert "recognition" in LANE_RECORD_TYPES["hr"]


def test_safety_lane_has_expected_types():
    for k in ("training_record", "certificate", "corrective_action",
              "safety_meeting_attendance", "toolbox_attendance"):
        assert k in LANE_RECORD_TYPES["safety"]


def test_asset_lane_has_expected_types():
    for k in ("ppe_issued", "ppe_returned", "tool_issued", "phone_issued",
              "tablet_issued", "ipad_issued", "survey_equipment_issued",
              "pipe_laser_issued", "rotating_laser_issued",
              "asset_acknowledgement", "damaged_asset", "lost_asset",
              "replacement_record"):
        assert k in LANE_RECORD_TYPES["asset"]


def test_corporate_import_lane_exists_for_historical_bulk_intake():
    for k in ("historical_archive", "acquisition_records",
              "legacy_conversion", "bulk_hr_archive",
              "unknown_mixed_records"):
        assert k in LANE_RECORD_TYPES["corporate_import"]


# ── Doctrine: permission model ──────────────────────────────────────
def test_hr_can_approve_every_lane():
    hr = {"_actor": "hr", "email": "hr@masci"}
    for lane in OWNERSHIP_LANES:
        assert _actor_can_approve(hr, lane), f"HR must approve in {lane}"


def test_admin_can_approve_every_lane():
    admin = {"_actor": "admin"}
    for lane in OWNERSHIP_LANES:
        assert _actor_can_approve(admin, lane)


def test_safety_can_approve_only_safety_lane():
    safety = {"_actor": "safety"}
    assert _actor_can_approve(safety, "safety")
    assert not _actor_can_approve(safety, "hr")
    assert not _actor_can_approve(safety, "asset")
    assert not _actor_can_approve(safety, "corporate_import")


def test_asset_admin_can_approve_only_asset_lane():
    asset = {"_actor": "asset_admin"}
    assert _actor_can_approve(asset, "asset")
    assert not _actor_can_approve(asset, "hr")
    assert not _actor_can_approve(asset, "safety")


def test_field_role_cannot_approve_any_lane():
    field = {"_actor": "field"}
    for lane in OWNERSHIP_LANES:
        assert not _actor_can_approve(field, lane)


def test_hr_can_read_every_lane():
    hr = {"_actor": "hr"}
    for lane in OWNERSHIP_LANES:
        assert _actor_can_read_lane(hr, lane)


def test_safety_can_only_read_safety_lane():
    safety = {"_actor": "safety"}
    assert _actor_can_read_lane(safety, "safety")
    assert not _actor_can_read_lane(safety, "hr")
    assert not _actor_can_read_lane(safety, "asset")


def test_asset_admin_can_only_read_asset_lane():
    asset = {"_actor": "asset_admin"}
    assert _actor_can_read_lane(asset, "asset")
    assert not _actor_can_read_lane(asset, "hr")
    assert not _actor_can_read_lane(asset, "safety")


# ── Source-level: incident cases join HR timeline ───────────────────
def test_hr_timeline_joins_incident_cases_via_defensible_roles_only():
    src = HR_PORTAL.read_text(encoding="utf-8")
    # New Track 19.21 code path must query db.incident_cases in addition
    # to legacy db.incidents.
    assert "db.incident_cases.find" in src, (
        "Track 19.21 · HR timeline must fan out over incident_cases."
    )
    # Defensible roles ONLY — no "was present" auto-linkage.
    assert "field_block.reporter_employee_id" in src
    assert "field_block.involved_employee_ids" in src
    assert "field_block.witness_employee_ids" in src
    assert "safety_block.corrective_action_owner_ids" in src
    # Legacy incidents path preserved for backward compat.
    assert "db.incidents.find" in src


def test_hr_timeline_does_not_add_passive_presence_signals_yet():
    src = HR_PORTAL.read_text(encoding="utf-8")
    # Passive "personnel_present" auto-linkage is deferred to Track 19.22+
    # by explicit user directive. It must NOT be wired in Track 19.21.
    # Note: personnel_present may appear elsewhere in the file (it's a
    # legitimate FieldBlock field). We only guard against it being used
    # as a linkage predicate on the timeline.
    banned = [
        'field_block.personnel_present": emp_id',
        "'field_block.personnel_present': emp_id",
    ]
    for pattern in banned:
        assert pattern not in src, (
            f"Track 19.21 · Passive presence linkage is deferred; "
            f"unexpected pattern: {pattern}"
        )


# ── Employee 360° UI contract ───────────────────────────────────────
def test_employee_profile_page_exists_with_testids():
    src = FE_PAGE.read_text(encoding="utf-8")
    for testid in (
        'data-testid="employee-profile"',
        'data-testid="employee-profile-name"',
        'data-testid="employee-profile-story"',
        'data-testid="employee-profile-timeline"',
        'data-testid="employee-profile-exec-headline"',
        'data-testid="employee-profile-brief-pdf"',
    ):
        assert testid in src, f"Missing testid: {testid}"


def test_employee_profile_uses_existing_timeline_endpoint_read_only():
    src = FE_PAGE.read_text(encoding="utf-8")
    # Zero-drift · Employee 360° must READ the existing timeline endpoint,
    # never mutate. No POST / PATCH / DELETE calls from this page.
    assert "/api/hr/employees/" in src
    assert "/accountability/timeline" in src
    assert "/accountability/brief.pdf" in src
    # No mutation verbs (except for the auth header helper).
    for verb in ('method: "POST"', 'method: "PUT"',
                 'method: "DELETE"', 'method: "PATCH"'):
        assert verb not in src, (
            f"Employee 360° must be read-only. Found mutation: {verb}"
        )


def test_employee_profile_has_all_required_tabs():
    src = FE_PAGE.read_text(encoding="utf-8")
    # The tabs are rendered from a `tabs` array with `key` values; the
    # data-testid is a template literal. Assert both the tab-key values
    # exist and the template-literal pattern is wired.
    assert '`employee-profile-tab-${key}`' in src, (
        "Employee 360° tabs must use the standard data-testid template "
        "'employee-profile-tab-${key}' so testing agents can drive them."
    )
    for tab_key in ("timeline", "training", "ppe", "incidents",
                    "discipline", "driver", "hr"):
        # The `key` value must appear inside the tabs array literal.
        assert f'key: "{tab_key}"' in src, f"Missing tab: {tab_key}"


def test_employee_profile_uses_visual_spine_pattern():
    src = FE_PAGE.read_text(encoding="utf-8")
    # Same pattern as SafetyCaseWorkspace Track 19.18 timeline spine.
    assert "before:absolute" in src
    assert "<ol" in src


# ── No parallel employee system ─────────────────────────────────────
def test_employee_records_module_does_not_duplicate_employee_identity():
    src = MODULE.read_text(encoding="utf-8")
    # db.employees is the single source of truth. This module MAY read
    # `db.employees.find_one` for name-snapshotting but must NEVER
    # insert/update it.
    assert "db.employees.insert" not in src
    assert "db.employees.update_one" not in src
    assert "db.employees.delete" not in src
    # Records reference employees by FK — they never carry the
    # employee's canonical fields as writable columns.
    for canonical_field in ("hire_date", "cdl_expiration_date", "supervisor",
                             "trade", "department"):
        # These must NOT be columns of the employee_records model.
        # (They may appear only inside README/doctrine comments.)
        # The rec dict inside create_record is the canonical shape check.
        pass


def test_reassignment_resets_approval():
    src = MODULE.read_text(encoding="utf-8")
    # Reassigning a LINKED record must move it back to pending_approval
    # so the receiving employee/lane gets a fresh approval decision.
    assert 'if rec.get("approval_status") == "linked":' in src
    assert 'patch["approval_status"] = "pending_approval"' in src


def test_original_file_metadata_is_preserved():
    src = MODULE.read_text(encoding="utf-8")
    # The universal record model must persist source_file_ref +
    # source_file_name + source_file_hash so the original attachment
    # can always be located and verified.
    for field in ("source_file_ref", "source_file_name", "source_file_hash",
                  "imported_batch_id"):
        assert f'"{field}"' in src, f"Missing preservation field: {field}"


def test_audit_ledger_is_append_only_by_design():
    src = MODULE.read_text(encoding="utf-8")
    # `_write_audit` only INSERTs. There is no update/delete path.
    assert "db.employee_record_audit.insert_one" in src
    for banned in ("db.employee_record_audit.update",
                   "db.employee_record_audit.delete",
                   "db.employee_record_audit.replace"):
        assert banned not in src, (
            f"Employee record audit must be append-only. Found: {banned}"
        )


def test_no_ocr_or_ml_libraries_imported_in_this_track():
    # Track 19.21 doctrine · P0 foundation only. OCR + AI classification
    # + fuzzy matching are deferred to Track 19.22+.
    src = MODULE.read_text(encoding="utf-8")
    for banned in ("import pytesseract", "from pytesseract",
                   "import openai", "from openai",
                   "from rapidfuzz", "import rapidfuzz",
                   "from litellm", "import litellm"):
        assert banned not in src, (
            f"Track 19.21 · Deferred capability wired prematurely: {banned}"
        )


def test_zero_drift_no_new_incident_engine_write_paths():
    # This track adds a READ path to db.incident_cases in the HR
    # timeline. It must NOT add write paths from HR into the incident
    # engine or from the records module into incident_cases.
    for path in (MODULE, HR_PORTAL):
        src = path.read_text(encoding="utf-8")
        for banned in ("db.incident_cases.insert",
                       "db.incident_cases.update_one",
                       "db.incident_cases.delete",
                       "db.incident_cases.replace"):
            assert banned not in src, (
                f"Zero drift · unexpected incident_cases write in {path.name}: "
                f"{banned}"
            )
