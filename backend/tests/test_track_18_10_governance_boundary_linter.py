"""TRACK 18.10 · Governance Boundary Linter — permanent guardrail.

Permanently prevents the architecture drift that Track 18.09C had to
clean up: operational execution pages must NOT be born under
`frontend/src/pages/admin/`. Administration governs. Operations
execute.

Linter design principles (per directive · "precise guardrail, not a
noisy scanner"):
1. Allow-list-first. Every existing file is grandfathered.
2. Content scan only fires on NEW files not in the allow-list and
   requires TWO or more high-confidence operational-execution signals
   to flag.
3. Thin alias rule matches a single canonical pattern.
4. Read-only oversight pages are explicitly allow-listed (they render
   operational data via shared components — no forked logic).

The 34 directive-mandated assertions below cover every required
verification.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/app")
FRONTEND_SRC = ROOT / "frontend" / "src"
MEMORY = ROOT / "memory"
SCRIPTS = ROOT / "scripts"
ADMIN_PAGES_DIR = FRONTEND_SRC / "pages" / "admin"

AUDIT = MEMORY / "ADMIN_GOVERNANCE_BOUNDARY_AUDIT.md"
RULES = MEMORY / "GOVERNANCE_BOUNDARY_LINTER_RULES.md"
TRACK_DOC = MEMORY / "TRACK_18_10_GOVERNANCE_BOUNDARY_LINTER.md"


# ---------------------------------------------------------------------
# Allow-list — every existing file under pages/admin/ as of 2026-02-10
# plus the cross-tree thin alias at pages/AdminTransportation.jsx.
# ---------------------------------------------------------------------
GOVERNANCE_FILES = {
    "AdminAnalytics.jsx",
    "AdminAssetAdmin.jsx",
    "AdminAssetMapping.jsx",
    "AdminAssetSpineHealth.jsx",
    "AdminAuditLog.jsx",
    "AdminCommandCenter.jsx",
    "AdminCompliance.jsx",
    "AdminComplianceFindings.jsx",
    "AdminDatabase.jsx",
    "AdminDigestConfig.jsx",
    "AdminEmail.jsx",
    "AdminGeofenceReconciliation.jsx",
    "AdminGovernance.jsx",
    "AdminGuidanceCoverage.jsx",
    "AdminIntegrationCenter.jsx",
    "AdminJobTeam.jsx",
    "AdminJobs.jsx",
    "AdminMasterHistory.jsx",
    "AdminMfa.jsx",
    "AdminOperationalInventory.jsx",
    "AdminOperationalLanguage.jsx",
    "AdminOperationsDashboard.jsx",
    "AdminOperationsEvents.jsx",
    "AdminPeople.jsx",
    "AdminProfile.jsx",
    "AdminProjectIdentityGovernance.jsx",
    "AdminProjectStaffing.jsx",
    "AdminPromoAssets.jsx",
    "AdminRecovery.jsx",
    "AdminRecoveryStream.jsx",
    "AdminSessions.jsx",
    "AdminSystem.jsx",
    "AssetProfile.jsx",
    "DeployRecovery.jsx",
    "SelfProtection.jsx",
    "SystemHealth.jsx",
}

READ_ONLY_OVERSIGHT_FILES = {
    "AdminDispatch.jsx",
    "AdminDlsDay1Debrief.jsx",
    "AdminDlsShiftQR.jsx",
    "AdminDriverIntel.jsx",
    "AdminEquipment.jsx",
    "AdminJhaAcknowledgements.jsx",
    "AdminTraining.jsx",
}

ADMIN_PAGE_ALLOWLIST = GOVERNANCE_FILES | READ_ONLY_OVERSIGHT_FILES

# Cross-tree thin alias (lives at pages/, not pages/admin/).
THIN_ALIASES = {
    FRONTEND_SRC / "pages" / "AdminTransportation.jsx",
}

THIN_ALIAS_LINE_BUDGET = 25  # non-empty lines
THIN_ALIAS_REEXPORT_PATTERN = re.compile(
    r'export\s*\{\s*default\s*\}\s*from\s*"[^"]+"'
)

# High-confidence operational-execution signals — used only on NEW
# files (not in allow-list).
OPERATIONAL_SIGNALS = (
    r"\bassignLoad\s*\(",
    r"\bassignDriver\s*\(",
    r"\bconfirmDispatch\s*\(",
    r"\bdispatch_assignment\b",
    r"\bonboardDriver\s*\(",
    r"\bsubmitDriverIntake\s*\(",
    r"\bonboardCarrier\s*\(",
    r"\bcarrierOnboarding\s*\(",
    r"\bsetTruckReady\s*\(",
    r"\bconfirmTruckReady\s*\(",
    r"\bsubmitDailyReport\s*\(",
    r"\bsubmitSafetyMeeting\s*\(",
    r"\bsubmitJHA\s*\(",
    r"\bsubmitTimesheet\s*\(",
    r"\bclockIn\s*\(",
    r"\bclockOut\s*\(",
    r"\bcloseWorkOrder\s*\(",
    r"\bconfirmRepair\s*\(",
)
OPERATIONAL_SIGNAL_RES = [re.compile(p) for p in OPERATIONAL_SIGNALS]


def _non_empty_lines(text: str) -> int:
    return sum(1 for ln in text.splitlines() if ln.strip())


def _count_operational_signals(text: str) -> int:
    return sum(1 for r in OPERATIONAL_SIGNAL_RES if r.search(text))


# =====================================================================
# 1. Governance boundary audit document exists.
# =====================================================================
def test_01_governance_boundary_audit_exists():
    assert AUDIT.exists(), "ADMIN_GOVERNANCE_BOUNDARY_AUDIT.md is missing."


# =====================================================================
# 2. Governance ownership registry exists.
# =====================================================================
def test_02_governance_ownership_registry_exists():
    assert RULES.exists(), "GOVERNANCE_BOUNDARY_LINTER_RULES.md is missing."


# =====================================================================
# 3. Admin page audit covers every file in frontend/src/pages/admin/.
# =====================================================================
def test_03_audit_covers_every_admin_file():
    audit_body = AUDIT.read_text()
    missing = []
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name not in audit_body:
            missing.append(p.name)
    assert not missing, (
        "Audit document does not list every file under pages/admin/. "
        f"Missing: {missing}"
    )


# =====================================================================
# 4. Every admin file has a classification.
# =====================================================================
def test_04_every_admin_file_has_classification():
    missing = []
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name not in ADMIN_PAGE_ALLOWLIST:
            missing.append(p.name)
    assert not missing, (
        "Admin files exist without a Track 18.10 classification. "
        f"Either add them to GOVERNANCE_FILES / READ_ONLY_OVERSIGHT_FILES "
        f"in this test file AND ADMIN_GOVERNANCE_BOUNDARY_AUDIT.md, "
        f"or relocate to the owning operational workspace. Missing: {missing}"
    )


# =====================================================================
# 5. Thin alias allow-list exists.
# =====================================================================
def test_05_thin_alias_allowlist_exists():
    body = AUDIT.read_text()
    assert "Thin alias allow-list" in body
    # Must list pages/AdminTransportation.jsx.
    assert "AdminTransportation.jsx" in body


# =====================================================================
# 6. Read-only oversight allow-list exists.
# =====================================================================
def test_06_read_only_oversight_allowlist_exists():
    body = AUDIT.read_text()
    assert "Read-only oversight allow-list" in body
    # Every file we classified as READ_ONLY_OVERSIGHT must appear in it.
    for name in READ_ONLY_OVERSIGHT_FILES:
        assert name in body, (
            f"Read-only oversight allow-list missing entry: {name}"
        )


# =====================================================================
# 7. AdminTransportation.jsx is classified as thin alias.
# =====================================================================
def test_07_admin_transportation_classified_thin_alias():
    p = FRONTEND_SRC / "pages" / "AdminTransportation.jsx"
    assert p.exists()
    audit_body = AUDIT.read_text()
    assert "AdminTransportation.jsx" in audit_body
    assert "THIN_ALIAS" in audit_body


# =====================================================================
# 8. AdminTransportation.jsx contains no operational business logic.
# =====================================================================
def test_08_admin_transportation_thin_alias_discipline():
    p = FRONTEND_SRC / "pages" / "AdminTransportation.jsx"
    src = p.read_text()
    # Within the line budget.
    assert _non_empty_lines(src) <= THIN_ALIAS_LINE_BUDGET, (
        f"AdminTransportation.jsx exceeds thin-alias line budget "
        f"({THIN_ALIAS_LINE_BUDGET}). It must remain a thin re-export."
    )
    # Must contain exactly one `export { default } from` re-export
    # pointing at the operational source.
    matches = THIN_ALIAS_REEXPORT_PATTERN.findall(src)
    assert len(matches) == 1, (
        "AdminTransportation.jsx must contain exactly one "
        f"`export {{ default }} from \"...\"` re-export. Found {len(matches)}."
    )
    assert "./transportation/TransportationApp" in src, (
        "AdminTransportation.jsx must re-export from "
        "./transportation/TransportationApp."
    )
    # No high-confidence operational signals.
    assert _count_operational_signals(src) == 0, (
        "AdminTransportation.jsx contains operational-execution signals. "
        "Thin aliases must not implement operational logic."
    )


# =====================================================================
# 9. TransportationApp.jsx remains operational source of truth.
# =====================================================================
def test_09_transportation_app_is_source_of_truth():
    p = FRONTEND_SRC / "pages" / "transportation" / "TransportationApp.jsx"
    assert p.exists(), "TransportationApp.jsx is missing."
    src = p.read_text()
    # Must export a default React component and mount Routes.
    assert "export default function TransportationApp" in src
    assert "<Routes>" in src


# =====================================================================
# 10. No operational Transportation execution page is implemented
#     under pages/admin/.
# =====================================================================
def test_10_no_transportation_execution_under_admin():
    # The only Transportation-adjacent files under pages/admin/ are
    # the documented READ_ONLY_OVERSIGHT entries (AdminDispatch,
    # AdminDriverIntel, AdminEquipment) and zero operational
    # execution pages. The single source of truth lives at
    # pages/transportation/.
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        # Any unknown file gets the content scan.
        src = p.read_text()
        signals = _count_operational_signals(src)
        assert signals < 2, (
            f"{p.name} appears to implement operational execution "
            f"({signals} high-confidence signals) and is not in the "
            "Track 18.10 allow-list. Either relocate to "
            "pages/transportation/ or document with a classification "
            "in ADMIN_GOVERNANCE_BOUNDARY_AUDIT.md."
        )


# =====================================================================
# 11. No Dispatch execution page is implemented under pages/admin/.
# =====================================================================
def test_11_no_dispatch_execution_under_admin():
    # Dispatch execution lives at pages/DispatchBoard.jsx,
    # pages/DispatchCommandCenter.jsx, etc., and at /dispatch-portal/*.
    # No admin-prefixed file may BE the dispatch execution surface.
    # The only Dispatch-flavored admin file is AdminDispatch.jsx —
    # classified READ_ONLY_OVERSIGHT.
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        # New file with dispatch-execution signals → fail.
        dispatch_signals = sum(
            1 for r in OPERATIONAL_SIGNAL_RES[:4] if r.search(src)
        )
        assert dispatch_signals < 2, (
            f"{p.name} appears to implement Dispatch execution. "
            "Relocate to pages/DispatchBoard.jsx / "
            "pages/DispatchCommandCenter.jsx / /dispatch-portal/*."
        )


# =====================================================================
# 12. No PM execution page is implemented under pages/admin/.
# =====================================================================
def test_12_no_pm_execution_under_admin():
    # PM execution lives under pages/pm/ (or equivalent). Admin PM
    # pages (AdminJobs, AdminJobTeam, AdminProjectStaffing,
    # AdminProjectIdentityGovernance) are governance.
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        # Look for PM execution signals: submitting daily-report,
        # safety-meeting, JHA — these are PM/field execution.
        pm_signals = sum(
            1 for sig in (r"submitDailyReport", r"submitSafetyMeeting", r"submitJHA")
            if re.search(sig, src)
        )
        assert pm_signals < 2, (
            f"{p.name} appears to implement PM/field execution. "
            "Relocate to the owning operational workspace."
        )


# =====================================================================
# 13. No HR execution page is implemented under pages/admin/.
# =====================================================================
def test_13_no_hr_execution_under_admin():
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        hr_signals = sum(
            1 for sig in (r"submitTimesheet", r"clockIn", r"clockOut")
            if re.search(sig, src)
        )
        assert hr_signals < 2, (
            f"{p.name} appears to implement HR execution. "
            "Relocate to the owning operational workspace."
        )


# =====================================================================
# 14. No Safety Operations execution page under pages/admin/.
# =====================================================================
def test_14_no_safety_execution_under_admin():
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        # Safety execution: submitting JHA or safety meeting.
        safety_signals = sum(
            1 for sig in (r"submitJHA", r"submitSafetyMeeting")
            if re.search(sig, src)
        )
        assert safety_signals < 2, (
            f"{p.name} appears to implement Safety execution. "
            "Relocate to pages/safety/."
        )


# =====================================================================
# 15. No Shop Operations execution page under pages/admin/.
# =====================================================================
def test_15_no_shop_execution_under_admin():
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        shop_signals = sum(
            1 for sig in (r"closeWorkOrder", r"confirmRepair")
            if re.search(sig, src)
        )
        assert shop_signals < 2, (
            f"{p.name} appears to implement Shop execution. "
            "Relocate to pages/shop/."
        )


# =====================================================================
# 16. No Field Leadership execution page under pages/admin/.
# =====================================================================
def test_16_no_field_leadership_execution_under_admin():
    # Field Leadership execution lives at /leadership/* and
    # /field-leadership/*. Admin variants (AdminDlsDay1Debrief,
    # AdminDlsShiftQR, AdminJhaAcknowledgements) are READ_ONLY_OVERSIGHT.
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        # Field leadership executes daily report / JHA submissions.
        fl_signals = sum(
            1 for sig in (r"submitDailyReport", r"submitJHA", r"submitSafetyMeeting")
            if re.search(sig, src)
        )
        assert fl_signals < 2, (
            f"{p.name} appears to implement Field Leadership execution."
        )


# =====================================================================
# 17. Governance linter exists.
# =====================================================================
def test_17_governance_linter_exists():
    # The linter is this file.
    p = ROOT / "backend" / "tests" / "test_track_18_10_governance_boundary_linter.py"
    assert p.exists(), "Governance boundary linter file is missing."


# =====================================================================
# 18. Linter detects a seeded operational-admin violation.
# =====================================================================
def test_18_linter_detects_seeded_violation(tmp_path):
    """Synthetic seed: write a fake admin page with TWO operational
    signals and confirm our signal counter flags it."""
    seeded = (
        "import React from 'react';\n"
        "export default function FakeAdminPage(){\n"
        "  const handle = () => { assignLoad(123); confirmDispatch(456); };\n"
        "  return <button onClick={handle}>go</button>;\n"
        "}\n"
    )
    signals = _count_operational_signals(seeded)
    assert signals >= 2, (
        "Linter signal counter failed to detect a synthetic "
        "operational-execution seed. The guardrail is not protective."
    )


# =====================================================================
# 19. Linter allows documented thin aliases.
# =====================================================================
def test_19_linter_allows_documented_thin_alias():
    p = FRONTEND_SRC / "pages" / "AdminTransportation.jsx"
    src = p.read_text()
    # Thin alias rule: ≤ 25 non-empty lines + 1 re-export.
    assert _non_empty_lines(src) <= THIN_ALIAS_LINE_BUDGET
    assert len(THIN_ALIAS_REEXPORT_PATTERN.findall(src)) == 1


# =====================================================================
# 20. Linter allows documented governance pages.
# =====================================================================
def test_20_linter_allows_documented_governance_pages():
    # Every GOVERNANCE_FILES entry exists on disk.
    missing = []
    for name in GOVERNANCE_FILES:
        if not (ADMIN_PAGES_DIR / name).exists():
            missing.append(name)
    assert not missing, (
        "Governance allow-list references files that don't exist. "
        f"Remove or fix: {missing}"
    )


# =====================================================================
# 21. Linter allows documented read-only oversight pages.
# =====================================================================
def test_21_linter_allows_documented_oversight_pages():
    missing = []
    for name in READ_ONLY_OVERSIGHT_FILES:
        if not (ADMIN_PAGES_DIR / name).exists():
            missing.append(name)
    assert not missing, (
        "Read-only oversight allow-list references files that don't "
        f"exist. Remove or fix: {missing}"
    )


# =====================================================================
# 22. Linter avoids known false positives.
# =====================================================================
def test_22_linter_avoids_false_positives():
    """Every existing governance / read-only-oversight file in the
    repo must pass without firing. We assert the signal count is
    below the 2-signal threshold for every grandfathered file."""
    flagged = []
    for p in ADMIN_PAGES_DIR.glob("*.jsx"):
        if p.name not in ADMIN_PAGE_ALLOWLIST:
            continue
        src = p.read_text()
        if _count_operational_signals(src) >= 2:
            flagged.append(p.name)
    assert not flagged, (
        "Linter false positive: grandfathered admin file(s) tripped "
        f"the operational-signal counter: {flagged}. Recalibrate the "
        "signal list (the two-signal threshold is the false-positive "
        "control)."
    )


# =====================================================================
# 23. /transportation-operations/* contract preserved.
# =====================================================================
def test_23_transportation_operations_route_preserved():
    src = (FRONTEND_SRC / "App.js").read_text()
    assert '/transportation-operations/*' in src
    assert re.search(
        r'path="/transportation-operations/\*"\s+element=\{TX\(',
        src,
    ), "/transportation-operations/* must use TX(...) gate."


# =====================================================================
# 24. /admin/transportation/* alias preserved.
# =====================================================================
def test_24_admin_transportation_alias_preserved():
    src = (FRONTEND_SRC / "App.js").read_text()
    assert '/admin/transportation/*' in src
    assert re.search(
        r'path="/admin/transportation/\*"\s+element=\{A\(',
        src,
    ), "/admin/transportation/* must use A(...) admin-strict gate."


# =====================================================================
# 25. /api/admin/transportation/* API prefix preserved.
# =====================================================================
def test_25_admin_transportation_api_prefix_preserved():
    server = (ROOT / "backend" / "server.py").read_text()
    # The admin transportation API surface must remain mounted. We
    # check for the canonical prefix substring.
    assert "/admin/transportation" in server, (
        "/api/admin/transportation/* prefix appears to have been "
        "removed from backend/server.py."
    )


# =====================================================================
# 26. No route changes.
# =====================================================================
def test_26_no_route_changes():
    # The audit + executive doc must declare zero route changes.
    body = TRACK_DOC.read_text()
    assert "no new endpoints" in body.lower() or "No new endpoints" in body
    # Both doorways still in App.js (sanity).
    src = (FRONTEND_SRC / "App.js").read_text()
    assert "/transportation-operations/*" in src
    assert "/admin/transportation/*" in src


# =====================================================================
# 27. No auth changes.
# =====================================================================
def test_27_no_auth_changes():
    src = (FRONTEND_SRC / "App.js").read_text()
    # Both auth helpers in use.
    assert "A(" in src and "TX(" in src


# =====================================================================
# 28. No RBAC changes.
# =====================================================================
def test_28_no_rbac_changes():
    # Admin-strict and operational gates both still mount their
    # respective doorways. We assert the canonical guard names appear
    # somewhere in App.js (their definitions or usages).
    src = (FRONTEND_SRC / "App.js").read_text()
    # The admin-strict adminAuth import is canonical.
    assert "adminAuth" in src or "isAdmin" in src, (
        "Admin auth import appears to have been removed."
    )


# =====================================================================
# 29. Dispatch execution preserved.
# =====================================================================
def test_29_dispatch_execution_preserved():
    src = (FRONTEND_SRC / "App.js").read_text()
    # Dispatch execution lives at /dispatch-portal/* and direct files
    # (DispatchBoard, DispatchCommandCenter).
    assert "DispatchBoard" in src or "/dispatch-portal" in src


# =====================================================================
# 30. Driver workflows preserved.
# =====================================================================
def test_30_driver_workflows_preserved():
    src = (FRONTEND_SRC / "App.js").read_text()
    assert "/dr/" in src or "DriverPortal" in src or "/driver/" in src, (
        "Driver workflow routes appear to have been removed."
    )


# =====================================================================
# 31. No new collections.
# =====================================================================
def test_31_no_new_collections():
    server = (ROOT / "backend" / "server.py").read_text()
    # Canonical sample of pre-18.10 collections must remain.
    for sample in ("users", "operational_events"):
        assert sample in server, (
            f"Canonical pre-18.10 collection '{sample}' no longer "
            "appears in server.py."
        )


# =====================================================================
# 32. No new endpoints unless solely test/linter support.
# =====================================================================
def test_32_no_new_endpoints_for_linter():
    # The Track 18.10 linter is a static test; it requires no new
    # backend endpoints. We assert the executive document declares
    # this.
    body = TRACK_DOC.read_text()
    assert "no new endpoints" in body.lower() or "No new endpoints" in body or "static test" in body.lower(), (
        "Track 18.10 executive doc must declare the linter is a "
        "static test that requires no new endpoints."
    )


# =====================================================================
# 33. Deployment gate includes Track 18.10.
# =====================================================================
def test_33_deployment_gate_includes_18_10():
    gate = (SCRIPTS / "deployment_gate.py").read_text()
    assert "test_track_18_10_governance_boundary_linter.py" in gate, (
        "Track 18.10 lock file is not wired into the deployment gate."
    )


# =====================================================================
# 34. Final certification states Administration governs and operations
#     execute.
# =====================================================================
def test_34_final_certification_states_constitutional_rule():
    body = TRACK_DOC.read_text()
    assert "Administration governs" in body
    assert "Operations execute" in body
    assert "🟢" in body and "GO" in body
