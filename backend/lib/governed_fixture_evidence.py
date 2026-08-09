from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, List, Optional

from lib.governed_record_classification import (
    PREVIEW_CERTIFICATION_CLASSIFICATION,
    SYNTHETIC_TEST_CLASSIFICATION,
    governed_hidden_markers,
    is_hidden_from_live_operations,
)


FixtureRule = Dict[str, Any]


def _rule(
    *,
    evidence_source: str,
    match_all: List[Dict[str, Any]],
    classification: str = SYNTHETIC_TEST_CLASSIFICATION,
    reason: str = "source_controlled_fixture_evidence",
    source_kind: str = "synthetic_test",
) -> FixtureRule:
    return {
        "evidence_source": evidence_source,
        "match_all": match_all,
        "classification": classification,
        "reason": reason,
        "source_kind": source_kind,
    }


FIXTURE_EVIDENCE_RULES: Dict[str, List[FixtureRule]] = {
    "employees": [
        _rule(
            evidence_source="backend/tests/test_iter152_employee_lifecycle.py",
            match_all=[{"field": "name", "op": "startswith", "value": "TEST_iter152_"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter316_rehire_eligibility_reactivate.py",
            match_all=[{"field": "name", "op": "startswith", "value": "iter316_pytest_"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter353b_availability_tile.py",
            match_all=[{"field": "name", "op": "startswith", "value": "iter353b avail "}],
        ),
        _rule(
            evidence_source="backend/tests/test_employees_and_dr_number_iter19.py",
            match_all=[{"field": "name", "op": "in", "values": ["TEST_Bob Builder", "TEST_John Doe", "TEST_Jane Smith"]}],
        ),
        _rule(
            evidence_source="backend/tests/test_field_leadership_iter42.py",
            match_all=[{"field": "name", "op": "eq", "value": "TEST_FL_Employee_iter42"}],
        ),
        _rule(
            evidence_source="backend/tests/test_track_15_40_directory_resolution.py",
            match_all=[{"field": "name", "op": "eq", "value": "Track 15.40 TestEmployee"}],
        ),
        _rule(
            evidence_source="backend/tests/test_track_19_03_hr_roster_source_of_truth.py",
            match_all=[{"field": "name", "op": "startswith", "value": "ZZ_TEST_19_03_"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter153_po_requests.py",
            match_all=[{"field": "name", "op": "startswith", "value": "TEST_iter153_"}],
        ),
        _rule(
            evidence_source="backend/tests/test_data_hygiene_sweep.py",
            match_all=[{"field": "name", "op": "eq", "value": "Approval Test User"}],
            reason="historical_fixture_literal_evidence",
        ),
        _rule(
            evidence_source="historical_runtime_signature:hr_queue_approval_test_employee",
            match_all=[
                {"field": "name", "op": "startswith", "value": "TEST_QA_HRApproved_"},
                {"field": "added_via", "op": "eq", "value": "hr-queue-approval"},
            ],
            reason="historical_composite_fixture_signature",
        ),
    ],
    "field_leadership_records": [
        _rule(
            evidence_source="backend/tests/test_field_leadership_iter42.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-FL-001"},
                {"field": "employee_name", "op": "in", "values": ["TEST_FL_Sub_Employee", "TEST_DEL_target", "TEST_DEL_admin"]},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_field_leadership_equipment_return_iter45.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-FL-RTN"},
                {"field": "employee_name", "op": "eq", "value": "TEST_FL_Return_Employee"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_field_leadership_equipment_iter44.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-FL-001"},
                {"field": "employee_name", "op": "eq", "value": "TEST_FL_Equip_Employee"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_iter54_doc_ids_e2e.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "0000-TEST"},
                {"field": "employee_name", "op": "eq", "value": "TEST_Doc Employee"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_iter70_termination.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "ITER70-TEST"},
                {"field": "employee_name", "op": "eq", "value": "Iter70 Employee"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_iter107_bilingual_audit.py",
            match_all=[{"field": "employee_name", "op": "startswith", "value": "TEST_iter107_"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter106_deployment_audit.py",
            match_all=[{"field": "employee_name", "op": "startswith", "value": "TEST_iter106 "}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter107_bilingual_audit.py",
            match_all=[{"field": "employee_name", "op": "eq", "value": "TEST Juan Perez"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter165_phase_j_idempotency.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-J-1"},
                {"field": "project_name", "op": "in", "values": ["iter165 fl test", "TEST_iter165_fl_test"]},
                {"field": "kind", "op": "eq", "value": "training_deficiency"},
            ],
            reason="composite_fixture_signature",
        ),
    ],
    "daily_reports": [
        _rule(
            evidence_source="backend/tests/test_daily_reports.py",
            match_all=[
                {"field": "project_name", "op": "in", "values": ["TEST_DR_Project A1A", "TEST_DR_DEL_Project A1A"]},
                {"field": "project_number", "op": "eq", "value": "TEST-25-23"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_daily_reports.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_COORD_CLASSIFY"},
                {"field": "project_number", "op": "eq", "value": "TEST-1"},
                {"field": "photos", "op": "contains", "value": "data:image/png;base64,FAKE0"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_track_22_4b_followup_dr_b03.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "TRACK 22.4b-followup-DR"}],
        ),
        _rule(
            evidence_source="backend/tests/test_dr_fix_1_constitutional_remediation.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "DR-FIX-1 · Pytest Project"}],
        ),
        _rule(
            evidence_source="backend/tests/test_dr_fix_2_trust_remediation.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "DR-FIX-2 · R7 fixture"}],
        ),
        _rule(
            evidence_source="backend/tests/test_mm_001b_material_movement_visibility.py",
            match_all=[{"field": "project_name", "op": "in", "values": ["MM-001B · E-5 fixture", "MM-001B-F1 · false-outgoing fixture", "MM-001B-F1 · production-retention fixture"]}],
        ),
        _rule(
            evidence_source="backend/tests/test_mm_entry_002_outbound_capture.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "MM-ENTRY-002 fixture"}],
        ),
        _rule(
            evidence_source="backend/tests/test_track_23_10_e_project_join.py",
            match_all=[
                {"field": "prepared_by", "op": "eq", "value": "Track 23.10-E pytest"},
                {"field": "general_notes", "op": "eq", "value": "pytest E2E"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_daily_report_submit_latency.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "TEST Submit Speed Project"}],
        ),
        _rule(
            evidence_source="backend/tests/test_dr_cutover_002_http_integration.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "DR Cutover 002 Test"}],
        ),
        _rule(
            evidence_source="backend/tests/test_employees_and_dr_number_iter19.py",
            match_all=[
                {"field": "prepared_by", "op": "eq", "value": "TEST_QA"},
                {"field": "project_name", "op": "in", "values": ["TEST_Numbering", "TEST_E2E_Project"]},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/odr/test_wave_1a.py",
            match_all=[
                {"field": "project_name", "op": "in", "values": ["TEST_M1_Wave1A_regression", "Wave-1A Test", "TEST_Wave_1A_Test"]},
                {"field": "prepared_by", "op": "in", "values": ["M1 regression", "Pytest Foreman"]},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/odr/test_wave_1bc.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Wave_1BC_Test"},
                {"field": "prepared_by", "op": "eq", "value": "Pytest Foreman"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/pw_suite/test_critical_flows_pw_phase2.py",
            match_all=[
                {"field": "prepared_by", "op": "eq", "value": "Phase Sigma-II Test"},
                {"field": "general_notes", "op": "startswith", "value": "playwright-pw-"},
            ],
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            reason="preview_certification_fixture_evidence",
            source_kind="preview_certification",
        ),
        _rule(
            evidence_source="backend/tests/pw_suite/test_critical_flows_pw_phase3.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "ZZ-RUNTIME-CERT-2026"},
                {"field": "prepared_by", "op": "eq", "value": "cert.foreman@example.com"},
            ],
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            reason="preview_certification_fixture_evidence",
            source_kind="preview_certification",
        ),
        _rule(
            evidence_source="backend/tests/test_iteration_571_photo_intel_summary.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "Test Project 571"},
                {"field": "project_number", "op": "eq", "value": "TEST-571"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_track_24_3_api_e2e.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Regression Project"},
                {"field": "project_number", "op": "eq", "value": "TEST-24-3-REG"},
            ],
        ),
        _rule(
            evidence_source="/app/daily_report_canonical_workflow_test.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "Test Project for Daily Report Verification"},
                {"field": "project_number", "op": "eq", "value": "TEST-2026-001"},
            ],
            reason="source_controlled_fixture_evidence",
        ),
        _rule(
            evidence_source="historical_runtime_signature:test_dr_001_daily_report",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "Test Project"},
                {"field": "project_number", "op": "eq", "value": "TEST-DR-001"},
                {"field": "prepared_by", "op": "eq", "value": "Test Supervisor"},
            ],
            reason="historical_composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter165_phase_j_idempotency.py",
            match_all=[
                {"field": "project_name", "op": "startswith", "value": "iter165 test "},
                {"field": "project_number", "op": "eq", "value": "TEST-J-1"},
                {"field": "prepared_by", "op": "eq", "value": "iter165 prepper"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_track_27_10_api_e2e.py",
            match_all=[
                {"field": "project_name", "op": "regex", "value": r"^TEST_Track27_10_(ValidAI|ValidManual|ValidEdited|ValidFallback|Parity)_[a-f0-9]*$"},
                {"field": "project_number", "op": "regex", "value": r"^TEST-27-10-(AI|MAN|EDT|FB|PAR)-[a-f0-9]*$"},
                {"field": "prepared_by", "op": "eq", "value": "Test Supervisor"},
            ],
            reason="source_controlled_fixture_evidence",
        ),
        _rule(
            evidence_source="historical_runtime_signature:track_27_10_gate_preview",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_TRACK_27_10_GATE"},
                {"field": "project_number", "op": "eq", "value": "TEST_2710"},
                {"field": "prepared_by", "op": "eq", "value": "Preview Supervisor"},
            ],
            reason="historical_composite_fixture_signature",
        ),
        _rule(
            evidence_source="historical_runtime_signature:test_coord_matrix_daily_report",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_COORD_MATRIX"},
                {"field": "project_number", "op": "eq", "value": "TEST-2"},
                {"field": "prepared_by", "op": "eq", "value": "Tester"},
                {"field": "photos", "op": "contains", "value": "data:image/png;base64,FAKE0"},
            ],
            reason="historical_composite_fixture_signature",
        ),
    ],
    "incidents": [
        _rule(
            evidence_source="backend/tests/test_incidents.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-INC-01"},
                {"field": "project_name", "op": "in", "values": ["TEST_INC_Lift_NearMiss", "TEST_INC_NearMiss"]},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_iter_phase5d_p2.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_phase5d"},
                {"field": "project_number", "op": "eq", "value": "TEST-0000"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_iter165_phase_j_idempotency.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-J-1"},
                {"field": "project_name", "op": "startswith", "value": "iter165 test "},
                {"field": "reported_by", "op": "eq", "value": "iter165"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter363_employee_linkage_persistence.py",
            match_all=[
                {"field": "project_name", "op": "startswith", "value": "iter363-"},
                {"field": "reported_by", "op": "eq", "value": "iter363 Auto-Test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter368_incident_capa_reverse_link.py",
            match_all=[
                {"field": "project_name", "op": "startswith", "value": "iter368-"},
                {"field": "reported_by", "op": "eq", "value": "iter368 Auto-Test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_team_snapshot_embedding.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2A_Test"},
                {"field": "reported_by", "op": "eq", "value": "snapshot-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_ownership_producer_routing.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2B_Test"},
                {"field": "reported_by", "op": "eq", "value": "producer-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter153E_phaseE_fanout.py",
            match_all=[
                {"field": "project_name", "op": "regex", "value": r"^PhaseE_[a-f0-9]+-PROJ$"},
                {"field": "project_number", "op": "regex", "value": r"^PhaseE_[a-f0-9]+-NUM$"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter451_incident_lifecycle.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "TEST-451-CURL"},
                {"field": "project_name", "op": "eq", "value": "iter451 curl test"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/pw_suite/test_critical_flows_pw_phase3.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase_Sigma_III_Public_Form_Cert"},
                {"field": "project_number", "op": "eq", "value": "T-SIGMA3"},
                {"field": "reported_by", "op": "eq", "value": "Phase Sigma-III Foreman"},
            ],
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            reason="preview_certification_fixture_evidence",
            source_kind="preview_certification",
        ),
    ],
    "meetings": [
        _rule(
            evidence_source="backend/tests/test_meeting_iter260.py",
            match_all=[
                {"field": "project_name", "op": "in", "values": ["TEST_iter260_project", "TEST_iter260_minimal"]},
                {"field": "conducted_by", "op": "eq", "value": "TEST Foreman"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/pw_suite/test_critical_flows_pw_phase3.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase_Sigma_III_Public_Form_Cert"},
                {"field": "project_number", "op": "eq", "value": "T-SIGMA3"},
            ],
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            reason="preview_certification_fixture_evidence",
            source_kind="preview_certification",
        ),
        _rule(
            evidence_source="historical_runtime_signature:track_15_73_slice_2_delete",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TRACK_15_73_SLICE_2_DELETE-project"},
                {"field": "conducted_by", "op": "eq", "value": "TRACK_15_73_SLICE_2_DELETE Tester"},
            ],
            reason="historical_composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter363_employee_linkage_persistence.py",
            match_all=[
                {"field": "project_name", "op": "startswith", "value": "iter363-MTG-"},
                {"field": "conducted_by", "op": "eq", "value": "iter363 Auto-Test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_team_snapshot_embedding.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2A_Test"},
                {"field": "conducted_by", "op": "eq", "value": "snapshot-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_ownership_producer_routing.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2B_Test"},
                {"field": "conducted_by", "op": "eq", "value": "producer-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="historical_runtime_signature:phase_b_fanout_validation",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "PHASE-B-TEST"},
                {"field": "project_number", "op": "eq", "value": "TEST-001"},
                {"field": "conducted_by", "op": "eq", "value": "Phase B Validator"},
            ],
            reason="historical_composite_fixture_signature",
        ),
    ],
    "jhas": [
        _rule(
            evidence_source="backend/tests/test_jhas.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_JHA_Trench Excavation"},
                {"field": "project_number", "op": "eq", "value": "TEST-J-01"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_team_snapshot_embedding.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2A_Test"},
                {"field": "crew_lead", "op": "eq", "value": "snapshot-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_ownership_producer_routing.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2B_Test"},
                {"field": "crew_lead", "op": "eq", "value": "producer-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="historical_runtime_signature:phase_b_jha_validation",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "PHASE-B-TEST"},
                {"field": "project_number", "op": "eq", "value": "TEST-001"},
                {"field": "crew_lead", "op": "eq", "value": "Phase B Validator"},
            ],
            reason="historical_composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_track_28_02b_field_ops_e2e.py",
            match_all=[
                {"field": "project_name", "op": "startswith", "value": "TEST_28_02_jha_"},
                {"field": "project_number", "op": "eq", "value": "TEST28"},
                {"field": "job_title", "op": "eq", "value": "TRACK 28.02B Cert JHA"},
            ],
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            reason="preview_certification_fixture_evidence",
            source_kind="preview_certification",
        ),
    ],
    "inspections": [
        _rule(
            evidence_source="backend/tests/test_admin_auth.py",
            match_all=[{"field": "project_name", "op": "eq", "value": "TEST_AUTH_OPEN_INSP"}],
        ),
        _rule(
            evidence_source="backend/tests/test_inspections.py",
            match_all=[{"field": "project_name", "op": "in", "values": ["TEST_I-95 Resurfacing", "TEST_GRADE_PASS_85", "TEST_GRADE_FAIL_AF", "TEST_GRADE_NONE"]}],
        ),
        _rule(
            evidence_source="backend/tests/test_team_snapshot_embedding.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2A_Test"},
                {"field": "inspector_name", "op": "eq", "value": "snapshot-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_ownership_producer_routing.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2B_Test"},
                {"field": "inspector_name", "op": "in", "values": ["producer-test", "snapshot-test"]},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter54_doc_ids_e2e.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_DocID Project"},
                {"field": "project_number", "op": "eq", "value": "0000-TEST"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/pw_suite/test_critical_flows_pw_phase3.py",
            match_all=[
                {"field": "project_number", "op": "eq", "value": "ZZ-RUNTIME-CERT-2026"},
                {"field": "inspector_name", "op": "eq", "value": "cert.pm@example.com"},
            ],
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            reason="preview_certification_fixture_evidence",
            source_kind="preview_certification",
        ),
        _rule(
            evidence_source="backend/tests/test_daily_reports.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_DR_REG_INSP"},
                {"field": "inspector_name", "op": "eq", "value": "Insp"},
            ],
            reason="composite_fixture_signature",
        ),
    ],
    "training_records": [
        _rule(
            evidence_source="backend/tests/test_iter363_employee_linkage_persistence.py",
            match_all=[
                {"field": "project_number", "op": "startswith", "value": "iter363-TRAIN-"},
                {"field": "instructor_name", "op": "eq", "value": "iter363 Auto-Test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter353c_employee_timeline_and_brief.py",
            match_all=[{"field": "training_name", "op": "startswith", "value": "iter353c-archived-"}],
        ),
    ],
    "safety_issuances": [
        _rule(
            evidence_source="backend/tests/test_safety_forms_iter37.py",
            match_all=[
                {"field": "employee_name", "op": "eq", "value": "TEST_Employee"},
                {"field": "project_number", "op": "eq", "value": "P-001"},
            ],
        ),
        _rule(
            evidence_source="git:adb32592:backend/tests/test_iter38_predeploy_qa.py",
            match_all=[
                {"field": "employee_name", "op": "eq", "value": "TEST_QA38_Email"},
                {"field": "issued_by", "op": "eq", "value": "QA Bot"},
                {"field": "project_name", "op": "eq", "value": "QA38"},
            ],
            reason="historical_source_controlled_fixture_evidence",
        ),
        _rule(
            evidence_source="git:44967564:backend/tests/test_predeploy_iter39.py",
            match_all=[
                {"field": "employee_name", "op": "eq", "value": "TEST_ITER39 Worker"},
                {"field": "issued_by", "op": "eq", "value": "QA Bot"},
                {"field": "project_name", "op": "eq", "value": "Iter39 PDF Test"},
            ],
            reason="historical_source_controlled_fixture_evidence",
        ),
        _rule(
            evidence_source="backend/tests/test_iter363_employee_linkage_persistence.py",
            match_all=[
                {"field": "project_name", "op": "startswith", "value": "iter363-PPE-"},
                {"field": "issued_by", "op": "eq", "value": "iter363 Auto-Test"},
            ],
            reason="composite_fixture_signature",
        ),
    ],
    "dispatch_assignments": [
        _rule(
            evidence_source="backend/tests/test_track_22_4b_followup_dispatch_idempotency.py",
            match_all=[
                {"field": "truck_id", "op": "eq", "value": "TRUCK-IDEMP-TEST"},
                {"field": "project_number", "op": "eq", "value": "IDEMP-DISP"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_iter392_dls_foundation.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter392"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter393_dispatch_project_card_sync.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter393"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter418_breakdown_proof.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter418"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter417_operational_attachments.py",
            match_all=[
                {"field": "truck_id", "op": "eq", "value": "T-IT417"},
                {"field": "driver_name", "op": "eq", "value": "Test Driver"},
                {"field": "project_number", "op": "eq", "value": "9999"},
            ],
            reason="historical_source_controlled_fixture_evidence",
        ),
        _rule(
            evidence_source="backend/tests/test_iter419_wait_reason.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter419"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter420_shop_recovery.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter420"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter423_project_status_board.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter423"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter424_assignment_timestamps.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter424"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter425_transport_hardening.py",
            match_all=[{"field": "truck_id", "op": "startswith", "value": "T-iter425"}],
        ),
        _rule(
            evidence_source="historical_runtime_signature:dispatch_override_test",
            match_all=[
                {"field": "truck_id", "op": "startswith", "value": "override-truck-"},
                {"field": "driver_name", "op": "eq", "value": "Override Test"},
                {"field": "project_number", "op": "eq", "value": "TEST"},
            ],
            reason="historical_composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter401_dispatch_driver_pinning.py",
            match_all=[
                {"field": "driver_name", "op": "eq", "value": "Dispatch Pinned Name"},
                {"field": "project_number", "op": "eq", "value": "iter401-PRJ"},
            ],
            reason="composite_fixture_signature",
        ),
    ],
    "equipment_inspections": [
        _rule(
            evidence_source="backend/tests/test_track_13_31b_d5_1_smart_preop_dvir_canonical_stamp.py",
            match_all=[
                {"field": "operator_name", "op": "eq", "value": "D5.1 Tester"},
                {"field": "project_name", "op": "eq", "value": "D5.1 test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_track_13_31b_d5_2_canonical_inspection_templates.py",
            match_all=[
                {"field": "operator_name", "op": "eq", "value": "D5.2 Tester"},
                {"field": "project_name", "op": "eq", "value": "D5.2"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_track_13_31b_d5_4_structured_section_capture.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "D5.4 test"},
                {"field": "project_number", "op": "eq", "value": "20-07"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter54_doc_ids_e2e.py",
            match_all=[
                {"field": "operator_name", "op": "eq", "value": "TEST_Operator"},
                {"field": "project_number", "op": "eq", "value": "0000-TEST"},
            ],
        ),
        _rule(
            evidence_source="backend/tests/test_equipment_inspections.py",
            match_all=[
                {"field": "operator_name", "op": "eq", "value": "TEST_Operator"},
                {"field": "equipment_unit", "op": "startswith", "value": "TEST_CAT320_INSP_"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_iter363_employee_linkage_persistence.py",
            match_all=[{"field": "project_name", "op": "startswith", "value": "iter363-EQ-"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter364_p1_linkage_persistence.py",
            match_all=[{"field": "project_name", "op": "startswith", "value": "iter364-PREOP-"}],
        ),
        _rule(
            evidence_source="backend/tests/test_iter79_preop_docid.py",
            match_all=[
                {"field": "operator_name", "op": "eq", "value": "Iter79 Tester"},
                {"field": "project_name", "op": "startswith", "value": "TEST_79 Project TEST-79-"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_team_snapshot_embedding.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2A_Test"},
                {"field": "operator_name", "op": "eq", "value": "snapshot-test"},
            ],
            reason="composite_fixture_signature",
        ),
        _rule(
            evidence_source="backend/tests/test_ownership_producer_routing.py",
            match_all=[
                {"field": "project_name", "op": "eq", "value": "TEST_Phase2B_2B_Test"},
                {"field": "operator_name", "op": "eq", "value": "producer-test"},
            ],
            reason="composite_fixture_signature",
        ),
    ],
}


def _string_value(doc: Dict[str, Any], field: str) -> str:
    value = doc.get(field)
    return value.strip() if isinstance(value, str) else ""


def _matches_condition(doc: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    field = condition["field"]
    op = condition["op"]
    value = doc.get(field)
    if op == "eq":
        return value == condition["value"]
    if op == "in":
        return value in set(condition["values"])
    if op == "startswith":
        return isinstance(value, str) and value.startswith(condition["value"])
    if op == "regex":
        return isinstance(value, str) and bool(re.match(condition["value"], value))
    if op == "contains":
        if isinstance(value, str):
            return condition["value"] in value
        if isinstance(value, list):
            return any(isinstance(item, str) and condition["value"] in item for item in value)
        return False
    raise ValueError(f"Unsupported fixture match op: {op}")


def find_fixture_evidence(doc: Optional[Dict[str, Any]], family: str) -> Optional[FixtureRule]:
    if not doc:
        return None
    for rule in FIXTURE_EVIDENCE_RULES.get(family, []):
        if all(_matches_condition(doc, cond) for cond in rule.get("match_all", [])):
            return deepcopy(rule)
    return None


def governed_fixture_markers(doc: Optional[Dict[str, Any]], family: str) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    evidence = find_fixture_evidence(doc, family)
    if not evidence:
        return None
    fields = [cond["field"] for cond in evidence.get("match_all", [])]
    classification = evidence.get("classification") or SYNTHETIC_TEST_CLASSIFICATION
    return governed_hidden_markers(
        classification=classification,
        evidence_source=evidence["evidence_source"],
        reason=evidence.get("reason") or "fixture_evidence",
        evidence_fields=fields,
        source_kind=evidence.get("source_kind") or (
            "preview_certification"
            if classification == PREVIEW_CERTIFICATION_CLASSIFICATION
            else "synthetic_test"
        ),
        certification_record=classification == PREVIEW_CERTIFICATION_CLASSIFICATION,
    )


def normalize_explicit_governed_markers(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    if doc.get("hidden_from_operations") is True and doc.get("truth_visibility_scope") == "technical_audit_only":
        return None
    if doc.get("certification_record") is True:
        return governed_hidden_markers(
            classification=PREVIEW_CERTIFICATION_CLASSIFICATION,
            evidence_source="explicit_payload_marker:certification_record",
            reason="explicit_certification_payload_marker",
            evidence_fields=["certification_record"],
            source_kind="preview_certification",
            certification_record=True,
        )
    if doc.get("synthetic_record") is True:
        return governed_hidden_markers(
            classification=SYNTHETIC_TEST_CLASSIFICATION,
            evidence_source="explicit_payload_marker:synthetic_record",
            reason="explicit_synthetic_payload_marker",
            evidence_fields=["synthetic_record"],
            source_kind="synthetic_test",
        )
    return None


def apply_governed_fixture_markers(doc: Optional[Dict[str, Any]], family: str) -> Dict[str, Any]:
    payload = deepcopy(doc or {})
    if is_hidden_from_live_operations(payload):
        return payload
    normalized = normalize_explicit_governed_markers(payload)
    if normalized:
        payload.update(normalized)
        return payload
    markers = governed_fixture_markers(payload, family)
    if markers:
        payload.update(markers)
    return payload


def is_governed_fixture(doc: Optional[Dict[str, Any]], family: str) -> bool:
    if is_hidden_from_live_operations(doc):
        return True
    return find_fixture_evidence(doc, family) is not None


__all__ = [
    "FIXTURE_EVIDENCE_RULES",
    "find_fixture_evidence",
    "governed_fixture_markers",
    "normalize_explicit_governed_markers",
    "apply_governed_fixture_markers",
    "is_governed_fixture",
]