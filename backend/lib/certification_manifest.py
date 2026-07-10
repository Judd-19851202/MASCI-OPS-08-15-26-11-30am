"""Platform Certification Manifest — TRACK 28.07 · Phase 17.

Single source-controlled truth for "what workflows are certified, by
whom, when, against which regression suites."

## Design principles

* **Source-controlled** — this is a Python module, not a database
  row. Every change is a diff reviewers can inspect.
* **Machine-enforceable** — `test_certification_manifest_freshness.py`
  reads this file and asserts each PASS entry is coherent (owner,
  domain, regression tests exist and pass).
* **Dependency-aware** — every entry declares upstream dependencies
  (e.g. Fleet cert depends on Employees identity, HR lifecycle).
  Future CI can flag entries whose deps changed.
* **Deterministic** — no timestamps written by CI; only by humans.
  The last-certified date is embedded in the entry.

## Status semantics

* ``PASS``                    — certified, evidence current
* ``RE_CERTIFICATION_REQUIRED``— touched by later change, needs re-run
* ``IN_PROGRESS``             — actively being certified this session
* ``FAIL``                    — a regression opened this entry
* ``NOT_CERTIFIED``           — declared but never certified

## Future-development doctrine

When you touch a certified workflow:

1. Find the manifest entry that names the touched file/route/collection.
2. Flip its status to ``RE_CERTIFICATION_REQUIRED``.
3. Run the declared regression suites.
4. Only when they pass may the status return to ``PASS`` with a new
   ``last_certified_at`` + ``last_certified_commit``.

CI enforcement (Phase 17 v1):
* ``test_certification_manifest_freshness.py`` validates:
   - every entry has an owner, domain, and non-empty regression_tests
   - every regression_tests path exists on disk
   - every PASS entry has a last_certified_at + last_certified_commit
   - no two entries share the same workflow_id

Future CI enforcement (deferred to Session 2 / post-28.09):
   - git-diff-driven auto-flag of RE_CERTIFICATION_REQUIRED
   - release-gate integration
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal


CertStatus = Literal[
    "PASS", "RE_CERTIFICATION_REQUIRED", "IN_PROGRESS", "FAIL", "NOT_CERTIFIED",
]


@dataclass(frozen=True)
class CertEntry:
    workflow_id: str                    # unique
    domain: str                         # HR / Fleet / Dispatch / Safety / Training / Admin / Exec
    owner: str                          # role or squad
    routes: List[str]                   # frontend paths + backend api paths
    apis: List[str]                     # api endpoints
    collections: List[str]              # canonical mongo collections
    regression_tests: List[str]         # backend/tests/*.py — MUST EXIST
    cross_domain_deps: List[str]        # workflow_id references (upstream)
    last_certified_at: str              # ISO-8601 UTC, human-set
    last_certified_commit: str          # git sha OR "session-<n>"
    evidence_location: str              # register / changelog / test report
    status: CertStatus


# The manifest itself — every certified workflow lands here.
MANIFEST: List[CertEntry] = [
    # ─────────────────────── HR ───────────────────────
    CertEntry(
        workflow_id="hr.employee_lifecycle",
        domain="HR",
        owner="HR Ops",
        routes=["/hr/employees"],
        apis=[
            "/api/hr/employees", "/api/hr/employees/{id}",
            "/api/hr/employees/{id}/status", "/api/hr/employees/{id}/reactivate",
            "/api/hr/employees/facets", "/api/hr/employees/export.xlsx",
        ],
        collections=["employees", "hr_audit"],
        regression_tests=[
            "backend/tests/test_track_28_04_hr_e2e.py",
            "backend/tests/test_track_28_04_static_synthetic_hr_invariant.py",
            "backend/tests/test_track_28_04_cross_portal_auth.py",
        ],
        cross_domain_deps=[],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.04",
        evidence_location="memory/TRACK_28_CERTIFICATION_REGISTER.md · Track 28.04 · HR",
        status="PASS",
    ),
    # ───────────────── Field Operations ─────────────────
    CertEntry(
        workflow_id="field_ops.daily_report",
        domain="Field Ops",
        owner="Field Operations",
        routes=["/daily-reports", "/daily-report-v3"],
        apis=[
            "/api/daily-reports", "/api/daily-reports/{id}",
            "/api/daily-reports.csv", "/api/inspections", "/api/incidents",
            "/api/meetings", "/api/jhas",
        ],
        collections=["daily_reports", "inspections", "incidents", "meetings", "jhas"],
        regression_tests=[
            "backend/tests/test_track_28_02b_field_ops_e2e.py",
            "backend/tests/test_track_28_02b_static_synthetic_invariant.py",
        ],
        cross_domain_deps=["hr.employee_lifecycle"],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.02b",
        evidence_location="memory/TRACK_28_CERTIFICATION_REGISTER.md · Track 28.02B",
        status="PASS",
    ),
    # ───────────────── Field Leadership ─────────────────
    CertEntry(
        workflow_id="field_leadership.records",
        domain="Field Leadership",
        owner="Field Leadership",
        routes=["/fl", "/fl/records"],
        apis=["/api/fl/records", "/api/field-leadership/employees"],
        collections=["field_leadership_records"],
        regression_tests=[
            "backend/tests/test_track_28_03_field_leadership_e2e.py",
            "backend/tests/test_track_28_03_static_flr_invariant.py",
        ],
        cross_domain_deps=["hr.employee_lifecycle"],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.03",
        evidence_location="memory/TRACK_28_CERTIFICATION_REGISTER.md · Track 28.03",
        status="PASS",
    ),
    # ─────────────── Fleet / Dispatch ───────────────
    CertEntry(
        workflow_id="fleet.equipment_and_dispatch",
        domain="Fleet / Dispatch",
        owner="Operations",
        routes=["/fleet", "/dispatch-portal", "/shop"],
        apis=[
            "/api/equipment-master", "/api/fleet/units",
            "/api/dispatch/assignments", "/api/dispatch/assignments/board",
            "/api/shop/fleet/defects", "/api/equipment-inspections",
        ],
        collections=[
            "equipment_master", "dispatch_assignments",
            "equipment_inspections", "fleet_defects",
        ],
        regression_tests=[
            "backend/tests/test_track_28_05_fleet_dispatch_e2e.py",
            "backend/tests/test_track_28_05_static_synthetic_fleet_invariant.py",
            "backend/tests/test_track_28_05_session2_phases_10_16.py",
            "backend/tests/test_track_28_05f_shop_manager_queue_mobile.py",
        ],
        cross_domain_deps=["hr.employee_lifecycle"],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.05f",
        evidence_location="memory/TRACK_28_CERTIFICATION_REGISTER.md · Track 28.05 / 28.05F",
        status="PASS",
    ),
    # ───────────────── Safety ─────────────────
    CertEntry(
        workflow_id="safety.incidents_and_forms",
        domain="Safety",
        owner="Safety",
        routes=["/safety", "/incidents", "/inspections", "/meetings", "/jhas"],
        apis=[
            "/api/incidents", "/api/incidents.csv",
            "/api/jhas", "/api/inspections", "/api/meetings",
        ],
        collections=["incidents", "jhas", "inspections", "meetings"],
        regression_tests=[
            "backend/tests/test_track_28_06_safety_e2e.py",
            "backend/tests/test_track_28_06_api_employees_import_regression.py",
        ],
        cross_domain_deps=["hr.employee_lifecycle"],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.06",
        evidence_location="memory/TRACK_28_CERTIFICATION_REGISTER.md · Track 28.06",
        status="PASS",
    ),
    # ───────────────── Training / Qualifications ─────────────────
    CertEntry(
        workflow_id="training.qualifications_and_credentials",
        domain="Training",
        owner="Training / Safety Ops",
        routes=[
            "/hr/qualifications", "/hr/training-records",
            "/verify",  # public QR verification
        ],
        apis=[
            "/api/hr/qualifications",
            "/api/hr/qualifications/{id}/renew",
            "/api/hr/qualifications/{id}/revoke",
            "/api/hr/qualifications/{id}/suspend",
            "/api/hr/qualifications/{id}/reinstate",
            "/api/employees/qualifications",
            "/api/employees/competent-persons",
            "/api/employees/competent-persons/public",
        ],
        collections=["safety_training_records", "qualification_attachments"],
        regression_tests=[
            "backend/tests/test_track_28_07_training_e2e.py",
        ],
        cross_domain_deps=[
            "hr.employee_lifecycle", "safety.incidents_and_forms",
            "fleet.equipment_and_dispatch",
        ],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.07-s1",
        evidence_location=(
            "memory/TRACK_28_CERTIFICATION_REGISTER.md · Track 28.07 Session 1"
        ),
        status="PASS",
    ),
    # ─────────── Platform-wide auth invariants ───────────
    CertEntry(
        workflow_id="platform.admin_auth_invariant",
        domain="Platform",
        owner="Platform Trust",
        routes=[],
        apis=[],
        collections=[],
        regression_tests=[
            "backend/tests/test_no_retired_sync_admin_validator_alone.py",
            "backend/tests/test_no_portal_token_gate_missing_canonical_validator.py",
        ],
        cross_domain_deps=[],
        last_certified_at="2026-07-11",
        last_certified_commit="track-28.03e+28.04-p1",
        evidence_location="memory/TRACK_28_CERTIFICATION_REGISTER.md · Tracks 28.03E, 28.04-P1",
        status="PASS",
    ),
    # ─── Session 2 pending — placeholders declared, not certified ───
    CertEntry(
        workflow_id="admin_os.landing_and_deep_pages",
        domain="Admin OS",
        owner="Platform Ops",
        routes=["/admin", "/admin-portal"],
        apis=[],
        collections=[],
        regression_tests=[],
        cross_domain_deps=["platform.admin_auth_invariant"],
        last_certified_at="",
        last_certified_commit="",
        evidence_location="",
        status="NOT_CERTIFIED",
    ),
    CertEntry(
        workflow_id="occ.trust_center",
        domain="Admin OS",
        owner="Platform Ops",
        routes=["/admin/occ"],
        apis=["/api/admin/occ/*"],
        collections=[],
        regression_tests=[],
        cross_domain_deps=["platform.admin_auth_invariant"],
        last_certified_at="",
        last_certified_commit="",
        evidence_location="",
        status="NOT_CERTIFIED",
    ),
    CertEntry(
        workflow_id="ai.operations",
        domain="AI Ops",
        owner="Platform Ops",
        routes=["/admin/ai"],
        apis=["/api/integrations/health", "/api/admin/ai/*"],
        collections=[],
        regression_tests=[],
        cross_domain_deps=["platform.admin_auth_invariant"],
        last_certified_at="",
        last_certified_commit="",
        evidence_location="",
        status="NOT_CERTIFIED",
    ),
    CertEntry(
        workflow_id="communications.email_routing",
        domain="Communications",
        owner="Platform Ops",
        routes=["/admin/communications"],
        apis=["/api/admin/email/*", "/api/admin/digest/*"],
        collections=["email_routes", "resend_webhook_events"],
        regression_tests=[],
        cross_domain_deps=["platform.admin_auth_invariant"],
        last_certified_at="",
        last_certified_commit="",
        evidence_location="",
        status="NOT_CERTIFIED",
    ),
    CertEntry(
        workflow_id="storage.recovery_and_r2",
        domain="Storage",
        owner="Platform Ops",
        routes=["/admin/storage"],
        apis=["/api/admin/storage/*", "/api/admin/backup/*"],
        collections=[],
        regression_tests=[],
        cross_domain_deps=["platform.admin_auth_invariant"],
        last_certified_at="",
        last_certified_commit="",
        evidence_location="",
        status="NOT_CERTIFIED",
    ),
    CertEntry(
        workflow_id="executive.dashboards_and_reports",
        domain="Executive",
        owner="Executive Intelligence",
        routes=["/executive", "/executive-portal"],
        apis=["/api/executive/*"],
        collections=[],
        regression_tests=[],
        cross_domain_deps=[
            "hr.employee_lifecycle", "field_ops.daily_report",
            "safety.incidents_and_forms", "fleet.equipment_and_dispatch",
            "training.qualifications_and_credentials",
        ],
        last_certified_at="",
        last_certified_commit="",
        evidence_location="",
        status="NOT_CERTIFIED",
    ),
]


def by_workflow(workflow_id: str) -> CertEntry:
    for e in MANIFEST:
        if e.workflow_id == workflow_id:
            return e
    raise KeyError(workflow_id)


def workflows_touching_file(rel_path: str) -> List[str]:
    """Given a repo-relative path, return workflow_ids whose regression
    tests or routes reference it. Foundation for future CI dep-tracking."""
    hits: List[str] = []
    for e in MANIFEST:
        if any(rel_path in t for t in e.regression_tests):
            hits.append(e.workflow_id)
            continue
        if any(rel_path in r for r in e.routes):
            hits.append(e.workflow_id)
    return hits


def pass_entries() -> List[CertEntry]:
    return [e for e in MANIFEST if e.status == "PASS"]


def needs_recert() -> List[CertEntry]:
    return [e for e in MANIFEST if e.status == "RE_CERTIFICATION_REQUIRED"]


__all__ = [
    "CertEntry", "CertStatus", "MANIFEST",
    "by_workflow", "workflows_touching_file", "pass_entries", "needs_recert",
]
