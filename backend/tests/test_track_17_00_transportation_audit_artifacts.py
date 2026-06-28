"""TRACK 17.00 · Platform-wide trucking / transportation audit artifacts.

Audit-only track. This regression locks the existence and
section-completeness of the five audit deliverables produced
during the platform-wide discovery scan.

No behavior is tested here — Track 17.00 is read-only by spec.
"""
from __future__ import annotations

from pathlib import Path

MEMORY = Path("/app/memory")

REQUIRED_FILES = {
    "TRACK_17_00_PLATFORM_WIDE_TRUCKING_TRANSPORTATION_AUDIT.md": (
        "Executive summary",
        "Portals scanned",
        "Total features found",
        "Total routes found",
        "Total backend endpoints",
        "Total collections",
        "Hidden / unreachable features",
        "Duplications / overlaps",
        "Dispatch preservation findings",
        "Transportation system findings",
        "Data model findings",
        "RBAC findings",
        "Workflow findings",
        "Recommended next track",
        "Files created",
        "Tests",
        "Final call",
    ),
    "TRUCKING_TRANSPORTATION_FEATURE_INVENTORY.md": (
        "Frontend route map",
        "Backend endpoint inventory",
        "Mongo collections",
        "Track-by-track inventory",
        "Visibility matrix",
    ),
    "TRUCKING_TRANSPORTATION_ROUTE_MAP.md": (
        "Frontend routes",
        "Public (no auth)",
        "Admin",
        "Dispatch portal",
        "Driver portal",
        "PM portal",
        "Operations portal",
        "Backend transportation endpoints",
        "Backend dispatch endpoints",
        "Backend fleet/equipment endpoints",
    ),
    "TRUCKING_TRANSPORTATION_RBAC_MATRIX.md": (
        "Frontend surface matrix",
        "Backend endpoint matrix",
        "Per-collection write-RBAC",
        "Read-only consumer pattern",
    ),
    "TRUCKING_TRANSPORTATION_DUPLICATION_AND_HIDDEN_FEATURES.md": (
        "Duplications & overlaps",
        "Hidden / unreachable features",
    ),
}


def test_01_audit_files_exist():
    for filename in REQUIRED_FILES:
        path = MEMORY / filename
        assert path.exists(), (
            f"Track 17.00 audit deliverable missing: {path}")


def test_02_required_sections_present():
    for filename, sections in REQUIRED_FILES.items():
        path = MEMORY / filename
        src = path.read_text()
        for section in sections:
            assert section in src, (
                f"Track 17.00 file {filename!r} missing required "
                f"section {section!r}")


def test_03_audit_files_are_non_trivial():
    # Audit deliverables should be substantial — at least 50 LOC each.
    for filename in REQUIRED_FILES:
        path = MEMORY / filename
        line_count = len(path.read_text().splitlines())
        assert line_count >= 50, (
            f"Track 17.00 audit deliverable too thin: {filename} "
            f"({line_count} lines, expected ≥50).")


def test_04_audit_references_real_endpoints():
    # The route map must reference real endpoints we know exist.
    route_map = (MEMORY / "TRUCKING_TRANSPORTATION_ROUTE_MAP.md").read_text()
    for endpoint in (
        "/api/admin/transportation/carriers",
        "/api/admin/transportation/intelligence/cleanup-signals",
        "/api/dispatch/transportation/check",
        "/api/operations/transportation/readiness",
        "/api/transportation/invite/{token}",
        "/api/dispatch/recommendation",
    ):
        assert endpoint in route_map, (
            f"Track 17.00 route map missing endpoint reference: "
            f"{endpoint}")


def test_05_audit_references_real_collections():
    inventory = (MEMORY / "TRUCKING_TRANSPORTATION_FEATURE_INVENTORY.md").read_text()
    for coll in (
        "carriers",
        "transport_persons",
        "transport_trucks",
        "transport_eligibility_state",
        "transport_action_items",
        "dispatch_assignments",
        "transport_dispatch_recommendation_audit",
        "audit_events",
    ):
        assert coll in inventory, (
            f"Track 17.00 inventory missing collection reference: "
            f"{coll}")


def test_06_dispatch_preservation_documented():
    audit = (MEMORY / "TRACK_17_00_PLATFORM_WIDE_TRUCKING_TRANSPORTATION_AUDIT.md").read_text()
    assert "Dispatch preservation findings" in audit
    # The audit MUST explicitly state Dispatch is not being replaced.
    assert "preserve" in audit.lower(), (
        "Track 17.00 audit must explicitly call out Dispatch "
        "preservation.")
