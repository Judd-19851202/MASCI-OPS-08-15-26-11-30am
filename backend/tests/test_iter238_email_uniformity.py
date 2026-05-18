"""iter238 · Auto-email uniform subject prefix + Pre-Op shop-manager routing.

Operator directive (2026-05-18):
  1. Color-code the [MASCI] tag by record type so Gmail/Outlook filter
     rules can match a stable per-record-type prefix.
  2. Format every job-related email subject as:
       [MASCI · {TAG}] {job_name} · {job_number} · {short_title} · {doc_id}
  3. Equipment Pre-Op auto-emails go to the Shop Manager only — no PM,
     no co-PMs, no office CC, no FAIL fan-out to mechanics/parts.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from pdf_render import (  # noqa: E402
    build_email_subject,
    build_email_subject_for_kind,
    SUBJECT_TYPE_TAGS,
)


# ─────────────────────────────────────────────────────────────────────────
# 1 · build_email_subject — type tags land + iter237 ordering preserved
# ─────────────────────────────────────────────────────────────────────────
class TestTypeTagsInSubject:
    """Every job-related kind gets its own stable [MASCI · TAG] prefix
    so PMs can filter by record type without opening the email."""

    def _record(self, doc_id):
        return {
            "project_name": "Spruce Creek",
            "project_number": "25-21",
            "doc_id": doc_id,
        }

    def test_inspection_tag(self):
        subj = build_email_subject("inspection", self._record("INSP-2026-00007"))
        assert subj == "[MASCI · INSP] Spruce Creek · 25-21 · Site Inspection · INSP-2026-00007"

    def test_meeting_tag(self):
        subj = build_email_subject("meeting", self._record("MTG-2026-00016"))
        assert subj == "[MASCI · SAFETY] Spruce Creek · 25-21 · Safety Meeting · MTG-2026-00016"

    def test_jha_tag(self):
        subj = build_email_subject("jha", self._record("JHA-2026-00003"))
        assert subj == "[MASCI · JHA] Spruce Creek · 25-21 · JHP · JHA-2026-00003"

    def test_incident_tag(self):
        subj = build_email_subject("incident", self._record("INC-2026-00001"))
        assert subj == "[MASCI · INC] Spruce Creek · 25-21 · Incident · INC-2026-00001"

    def test_daily_report_tag(self):
        subj = build_email_subject("daily-report", self._record("DR-2026-0042"))
        assert subj == "[MASCI · DAILY] Spruce Creek · 25-21 · Daily Report · DR-2026-0042"

    def test_equipment_inspection_tag(self):
        subj = build_email_subject("equipment-inspection", self._record("EQI-2026-00001"))
        assert subj == "[MASCI · EQUIP] Spruce Creek · 25-21 · Pre-Op · EQI-2026-00001"

    def test_qaqc_tag(self):
        subj = build_email_subject("qaqc", self._record("QA-2026-0014"))
        # short_title for "qaqc" comes from SHORT_KIND_TITLES; assert
        # prefix + project + job# + doc_id rather than the title string
        # (which may evolve in copy without breaking the contract).
        assert subj.startswith("[MASCI · QA/QC] Spruce Creek · 25-21 · ")
        assert subj.endswith(" · QA-2026-0014")

    def test_unknown_kind_falls_back_to_bare_masci_prefix(self):
        """Kinds without a registered tag must still produce a valid
        subject — the bare [MASCI] prefix from iter237 is preserved."""
        subj = build_email_subject("totally-new-kind", self._record("XYZ-2026-0001"))
        assert subj.startswith("[MASCI] Spruce Creek · 25-21 · ")
        assert subj.endswith(" · XYZ-2026-0001")
        assert "· · " not in subj


# ─────────────────────────────────────────────────────────────────────────
# 2 · Severe-incident / equipment-fail keep warning prefix (operator-stated)
# ─────────────────────────────────────────────────────────────────────────
class TestWarningPrefixesPreserved:
    """The 🚨/⚠ attention-grabbing prefixes win over the type tag —
    operators are scanning for those at-a-glance signals first."""

    def test_severe_incident_keeps_warning_prefix(self):
        subj = build_email_subject(
            "incident",
            {"project_name": "Spruce Creek", "project_number": "25-21", "doc_id": "INC-2026-0003"},
            severe_incident=True,
        )
        assert subj == "🚨 SEVERE INCIDENT · Spruce Creek · 25-21 · INC-2026-0003"
        assert "[MASCI · INC]" not in subj

    def test_equipment_fail_keeps_warning_prefix(self):
        subj = build_email_subject(
            "equipment-inspection",
            {
                "project_name": "Spruce Creek",
                "project_number": "25-21",
                "doc_id": "EQI-2026-0001",
                "equipment_type": "CAT",
                "equipment_unit": "320E",
            },
            equipment_fail=True,
        )
        assert subj == "⚠ EQUIPMENT FAIL · Spruce Creek · 25-21 · CAT 320E · EQI-2026-0001"
        assert "[MASCI · EQUIP]" not in subj


# ─────────────────────────────────────────────────────────────────────────
# 3 · build_email_subject_for_kind — used by safety_forms + field_leadership
# ─────────────────────────────────────────────────────────────────────────
class TestUniformBuilderForSafetyAndFieldLeadership:
    """Safety-office forms and Field Leadership records use the same
    builder so the prefix format is uniform across every email type."""

    def test_safety_equipment_issuance(self):
        subj = build_email_subject_for_kind(
            type_tag_key="issuance",
            project_name="Spruce Creek",
            project_number="25-21",
            short_title="Safety Equipment Issuance · Juan Perez",
            doc_id="EQI-2026-0001",
        )
        assert subj == (
            "[MASCI · ISSUANCE] Spruce Creek · 25-21 · "
            "Safety Equipment Issuance · Juan Perez · EQI-2026-0001"
        )

    def test_safety_equipment_return(self):
        subj = build_email_subject_for_kind(
            type_tag_key="return",
            project_name="Spruce Creek",
            project_number="25-21",
            short_title="Equipment Check-In & Return · Juan Perez",
            doc_id="EQI-2026-0001",
        )
        assert subj.startswith("[MASCI · RETURN] Spruce Creek · 25-21 · ")
        assert subj.endswith(" · EQI-2026-0001")

    def test_safety_equipment_training(self):
        subj = build_email_subject_for_kind(
            type_tag_key="training",
            project_name="Spruce Creek",
            project_number="25-21",
            short_title="Equipment Use & Care Training · Juan Perez",
            doc_id="EQT-2026-0001",
        )
        assert subj.startswith("[MASCI · TRAINING] Spruce Creek · 25-21 · ")

    def test_field_leadership_writeup(self):
        subj = build_email_subject_for_kind(
            type_tag_key="write_up",
            project_name="Spruce Creek",
            project_number="25-21",
            short_title="Field Leadership: Write-Up · Juan Perez",
            doc_id="FLN-2026-00042",
        )
        assert subj.startswith("[MASCI · LEADERSHIP] Spruce Creek · 25-21 · ")
        assert subj.endswith(" · FLN-2026-00042")

    def test_field_leadership_employee_termination(self):
        subj = build_email_subject_for_kind(
            type_tag_key="employee_termination",
            project_name="Spruce Creek",
            project_number="25-21",
            short_title="Field Leadership: Employee Termination · Juan Perez",
            doc_id="FLN-2026-00043",
        )
        assert subj.startswith("[MASCI · TERMINATION] Spruce Creek · 25-21 · ")

    def test_field_leadership_time_off(self):
        subj = build_email_subject_for_kind(
            type_tag_key="time_off_request",
            project_name="Spruce Creek",
            project_number="25-21",
            short_title="Field Leadership: Time Off Request · Juan Perez",
            doc_id="FLN-2026-00044",
        )
        assert subj.startswith("[MASCI · TIME OFF] Spruce Creek · 25-21 · ")

    def test_no_project_number_no_double_separator(self):
        subj = build_email_subject_for_kind(
            type_tag_key="write_up",
            project_name="Spruce Creek",
            project_number="",
            short_title="Field Leadership: Write-Up · Juan Perez",
            doc_id="FLN-2026-00042",
        )
        # Project still appears, job number quietly omitted, no "· ·".
        assert "· · " not in subj
        assert "[MASCI · LEADERSHIP] Spruce Creek · " in subj

    def test_no_project_at_all_still_renders(self):
        """Defensive — Field Leadership records without project info
        (rare edge case) still produce a non-broken subject."""
        subj = build_email_subject_for_kind(
            type_tag_key="write_up",
            project_name="",
            project_number="",
            short_title="Field Leadership: Write-Up · Juan Perez",
            doc_id="FLN-2026-00042",
        )
        assert subj.startswith("[MASCI · LEADERSHIP] ")
        assert "· · " not in subj


# ─────────────────────────────────────────────────────────────────────────
# 4 · Tag registry coverage — every kind we want filter-rule support for
# ─────────────────────────────────────────────────────────────────────────
class TestTagRegistry:
    """Lock down the SUBJECT_TYPE_TAGS mapping. If someone removes a
    kind here without an explicit operator decision, the test catches
    it so we don't silently drop a Gmail filter rule the operator
    already configured."""

    REQUIRED_KINDS = {
        # Main pipeline
        "inspection": "INSP",
        "meeting": "SAFETY",
        "jha": "JHA",
        "incident": "INC",
        "daily-report": "DAILY",
        "equipment-inspection": "EQUIP",
        "qaqc": "QA/QC",
        # Safety-office forms
        "issuance": "ISSUANCE",
        "return": "RETURN",
        "training": "TRAINING",
        # Field-leadership: routine
        "write_up": "LEADERSHIP",
        "verbal_coaching": "LEADERSHIP",
        "attendance": "LEADERSHIP",
        "recognition": "LEADERSHIP",
        "equipment_checkout": "LEADERSHIP",
        "new_employee_eval": "LEADERSHIP",
        "crew_eval": "LEADERSHIP",
        "promotion_recommendation": "LEADERSHIP",
        "training_deficiency": "LEADERSHIP",
        "supervisor_notes": "LEADERSHIP",
        # Field-leadership: special-case (operator-distinguished)
        "employee_termination": "TERMINATION",
        "time_off_request": "TIME OFF",
    }

    @pytest.mark.parametrize("kind,tag", list(REQUIRED_KINDS.items()))
    def test_kind_has_registered_tag(self, kind, tag):
        assert SUBJECT_TYPE_TAGS.get(kind) == tag, (
            f"kind={kind!r} expected tag={tag!r}, got "
            f"{SUBJECT_TYPE_TAGS.get(kind)!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5 · Backward-compat — iter78c + iter237 invariants still hold
# ─────────────────────────────────────────────────────────────────────────
class TestBackCompatInvariants:
    def test_iter78c_project_before_doc_id(self):
        """Project name must appear before doc_id in the subject so
        mobile preview truncation never hides the project."""
        subj = build_email_subject(
            "daily-report",
            {"doc_id": "DR-2026-0001", "project_name": "MASCI Hwy 45 Reconstruction Phase II"},
        )
        idx_proj = subj.find("Hwy")
        idx_dr = subj.find("DR-2026")
        assert idx_proj >= 0 and idx_dr >= 0 and idx_proj < idx_dr

    def test_iter237_project_number_after_project(self):
        """Job number must sit between project name and short_title."""
        subj = build_email_subject(
            "meeting",
            {"project_name": "Spruce Creek", "project_number": "25-21", "doc_id": "MTG-2026-0001"},
        )
        idx_proj = subj.find("Spruce Creek")
        idx_num = subj.find("25-21")
        idx_title = subj.find("Safety Meeting")
        assert idx_proj < idx_num < idx_title, f"ordering wrong: {subj}"
