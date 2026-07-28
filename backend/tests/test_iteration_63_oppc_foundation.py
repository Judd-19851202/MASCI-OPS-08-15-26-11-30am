"""
OPPC Foundation Testing — Iteration 63

Tests for WP-OPPC-01, WP-OPPC-02, WP-OPPC-03:
- WP-OPPC-01: Documentation artifacts in /app/memory
- WP-OPPC-02: Cost-code foundation hardening with planning_readiness
- WP-OPPC-03: Rolling two-week planning lifecycle foundation

Endpoints tested:
- GET /api/cost-codes/projects/{project_number}/assignments
- GET /api/cost-codes/projects/{project_number}/schedule
- PUT /api/cost-codes/projects/{project_number}/assignments
- PUT /api/cost-codes/projects/{project_number}/schedule
- POST /api/cost-codes/projects/{project_number}/planning-lifecycle/publish
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Admin credentials from test_credentials.md (PM has no assigned projects)
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project number
TEST_PROJECT = "20-07"


class TestOPPCDocumentationArtifacts:
    """WP-OPPC-01: Verify documentation artifacts exist and are internally consistent."""

    def test_canonical_architecture_inventory_exists(self):
        """OPPC_CANONICAL_ARCHITECTURE_INVENTORY.md must exist with executive summary."""
        path = "/app/memory/OPPC_CANONICAL_ARCHITECTURE_INVENTORY.md"
        assert os.path.exists(path), f"Missing {path}"
        with open(path) as f:
            content = f.read()
        assert "## Executive Summary" in content
        assert "REUSE_EXISTING" in content or "EXTEND_EXISTING" in content
        # Verify no secondary engine recommendation
        assert "No secondary schedule engine" in content or "do not add a new planning registry" in content.lower()

    def test_gap_register_exists(self):
        """OPPC_GAP_REGISTER.md must exist with gap classifications."""
        path = "/app/memory/OPPC_GAP_REGISTER.md"
        assert os.path.exists(path), f"Missing {path}"
        with open(path) as f:
            content = f.read()
        assert "## Executive Summary" in content
        assert "GAP-01" in content
        assert "EXTEND_EXISTING" in content or "NEW_CANONICAL_COMPONENT_REQUIRED" in content

    def test_canonical_data_ownership_exists(self):
        """OPPC_CANONICAL_DATA_OWNERSHIP.md must exist with ownership rules."""
        path = "/app/memory/OPPC_CANONICAL_DATA_OWNERSHIP.md"
        assert os.path.exists(path), f"Missing {path}"
        with open(path) as f:
            content = f.read()
        assert "## Executive Summary" in content
        assert "jobs_master.assigned_cost_codes" in content
        # Verify no duplicate engine proposed
        assert "No business fact in this register has more than one proposed owner" in content

    def test_trust_spine_event_map_exists(self):
        """OPPC_TRUST_SPINE_EVENT_MAP.md must exist with workflow mappings."""
        path = "/app/memory/OPPC_TRUST_SPINE_EVENT_MAP.md"
        assert os.path.exists(path), f"Missing {path}"
        with open(path) as f:
            content = f.read()
        assert "## Executive Summary" in content
        assert "oppc-cost-code-plan" in content
        # Verify Trust Spine integration
        assert "trust_spine_events" in content or "Trust Spine" in content


class TestOPPCBackendAPI:
    """WP-OPPC-02 & WP-OPPC-03: Backend API tests for OPPC foundation."""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Authenticate as admin user and return session with tokens."""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login via multi-login
        login_resp = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if login_resp.status_code != 200:
            pytest.skip(f"Admin login failed: {login_resp.status_code} - {login_resp.text[:200]}")
        
        data = login_resp.json()
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        session_token = data.get("session_token")
        
        if admin_token:
            session.headers["X-Admin-Token"] = admin_token
        if session_token:
            session.headers["X-Directory-Token"] = session_token
        
        return session

    def test_get_assignments_returns_planning_readiness(self, admin_session):
        """GET /api/cost-codes/projects/{project_number}/assignments returns planning_readiness."""
        resp = admin_session.get(f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/assignments")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        assert "planning_readiness" in data, "Response must include planning_readiness"
        
        pr = data["planning_readiness"]
        assert "status" in pr, "planning_readiness must have status"
        assert pr["status"] in ("ready", "needs_attention", "unconfigured")
        assert "assignment_count" in pr
        assert "ready_assignments" in pr
        assert "supports_weekly_rollover" in pr
        assert "supports_monday_look_behind" in pr

    def test_each_assignment_includes_planning_readiness(self, admin_session):
        """Each assignment in the response must include its own planning_readiness."""
        resp = admin_session.get(f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/assignments")
        assert resp.status_code == 200
        
        data = resp.json()
        assignments = data.get("assignments", [])
        
        # If no assignments, this test passes (unconfigured state is valid)
        for assignment in assignments:
            assert "planning_readiness" in assignment, f"Assignment {assignment.get('code')} missing planning_readiness"
            pr = assignment["planning_readiness"]
            assert "status" in pr
            assert pr["status"] in ("ready", "needs_attention")

    def test_get_schedule_returns_planning_readiness_and_lifecycle(self, admin_session):
        """GET /api/cost-codes/projects/{project_number}/schedule returns planning_readiness and planning_lifecycle."""
        resp = admin_session.get(f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/schedule")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        
        # Verify planning_readiness
        assert "planning_readiness" in data, "Response must include planning_readiness"
        pr = data["planning_readiness"]
        assert "status" in pr
        assert "supports_weekly_rollover" in pr
        assert "supports_monday_look_behind" in pr
        
        # Verify planning_lifecycle
        assert "planning_lifecycle" in data, "Response must include planning_lifecycle"
        pl = data["planning_lifecycle"]
        assert "status" in pl
        assert pl["status"] in ("unconfigured", "needs_attention", "ready_to_publish", "published")
        assert "supports_publish" in pl
        assert "has_unpublished_changes" in pl

    def test_schedule_monday_look_behind_ready_derived_from_readiness(self, admin_session):
        """schedule.monday_look_behind_ready must be derived from actual readiness, not hardcoded."""
        resp = admin_session.get(f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/schedule")
        assert resp.status_code == 200
        
        data = resp.json()
        schedule = data.get("schedule", {})
        planning_readiness = data.get("planning_readiness", {})
        
        # monday_look_behind_ready should match planning_readiness.supports_monday_look_behind
        expected = bool(planning_readiness.get("supports_monday_look_behind"))
        actual = bool(schedule.get("monday_look_behind_ready"))
        
        assert actual == expected, f"schedule.monday_look_behind_ready ({actual}) should match planning_readiness.supports_monday_look_behind ({expected})"

    def test_put_assignments_preserves_canonical_owner_behavior(self, admin_session):
        """PUT /api/cost-codes/projects/{project_number}/assignments preserves canonical owner behavior."""
        # First get current assignments
        get_resp = admin_session.get(f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/assignments")
        if get_resp.status_code != 200:
            pytest.skip("Cannot read assignments for PUT test")
        
        current = get_resp.json()
        assignments = current.get("assignments", [])
        
        if not assignments:
            # Create a test assignment
            update_payload = {
                "assignments": [
                    {
                        "code": "TEST-OPPC-001",
                        "item_name": "OPPC Test Item",
                        "unit_of_measure": "LF",
                        "authorized_quantity": 100,
                        "schedule_start_date": "2026-07-28",
                        "duration_days": 5,
                        "schedule_phase": "Phase 1",
                        "planned_performer": "Test Crew",
                    }
                ]
            }
        else:
            # Prepare minimal update payload
            update_payload = {
                "assignments": [
                    {
                        "code": a["code"],
                        "item_name": a.get("item_name", ""),
                        "unit_of_measure": a.get("unit_of_measure", "LF"),
                        "authorized_quantity": a.get("authorized_quantity", 0),
                        "schedule_start_date": a.get("schedule_start_date", ""),
                        "duration_days": a.get("duration_days", 1),
                        "schedule_phase": a.get("schedule_phase", ""),
                        "planned_performer": a.get("planned_performer", ""),
                    }
                    for a in assignments[:3]  # Limit to first 3 for safety
                ]
            }
        
        put_resp = admin_session.put(
            f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/assignments",
            json=update_payload
        )
        
        # Should succeed or return 403/404 if project doesn't exist
        assert put_resp.status_code in (200, 403, 404), f"Unexpected status: {put_resp.status_code}: {put_resp.text[:300]}"
        
        if put_resp.status_code == 200:
            data = put_resp.json()
            assert "assignments" in data
            assert "progress" in data
            assert "planning_readiness" in data
            assert "planning_lifecycle" in data

    def test_put_schedule_sets_has_unpublished_changes(self, admin_session):
        """PUT /api/cost-codes/projects/{project_number}/schedule sets has_unpublished_changes=true."""
        # First get current schedule
        get_resp = admin_session.get(f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/schedule")
        if get_resp.status_code != 200:
            pytest.skip("Cannot read schedule for PUT test")
        
        current = get_resp.json()
        tasks = current.get("schedule", {}).get("tasks", [])
        
        if not tasks:
            pytest.skip("No tasks to test PUT schedule behavior")
        
        # Prepare minimal update payload
        update_payload = {
            "tasks": [
                {
                    "code": t["code"],
                    "schedule_start_date": t.get("baseline_start_date", ""),
                    "duration_days": t.get("duration_days", 1),
                    "predecessor_codes": t.get("predecessor_codes", []),
                }
                for t in tasks[:2]  # Limit to first 2 for safety
            ]
        }
        
        put_resp = admin_session.put(
            f"{BASE_URL}/api/cost-codes/projects/{TEST_PROJECT}/schedule",
            json=update_payload
        )
        
        assert put_resp.status_code in (200, 403, 404), f"Unexpected status: {put_resp.status_code}: {put_resp.text[:300]}"
        
        if put_resp.status_code == 200:
            data = put_resp.json()
            pl = data.get("planning_lifecycle", {})
            assert pl.get("has_unpublished_changes") is True, "PUT schedule should set has_unpublished_changes=true"


class TestOPPCTrustSpineIntegration:
    """Verify Trust Spine workflow registration for oppc-cost-code-plan."""

    def test_trust_spine_has_oppc_workflow(self):
        """Trust Spine must have oppc-cost-code-plan in WORKFLOW_EXPECTED_STAGES."""
        from lib.trust_spine import WORKFLOW_EXPECTED_STAGES
        
        assert "oppc-cost-code-plan" in WORKFLOW_EXPECTED_STAGES, "oppc-cost-code-plan must be registered in Trust Spine"
        
        stages = WORKFLOW_EXPECTED_STAGES["oppc-cost-code-plan"]
        assert "record_created" in stages
        assert "validation_complete" in stages
        assert "audit_written" in stages
        assert "completed" in stages


class TestOPPCFoundationModule:
    """Unit tests for services/cost_codes/foundation.py OPPC functions."""

    def test_build_assignment_planning_readiness_ready(self):
        """build_assignment_planning_readiness returns ready when all required fields present."""
        from services.cost_codes.foundation import build_assignment_planning_readiness
        
        row = {
            "code": "CC-1",
            "item_name": "Test Item",
            "unit_of_measure": "LF",
            "authorized_quantity": 100,
            "schedule_start_date": "2026-07-18",
            "duration_days": 5,
            "schedule_phase": "Phase 1",
            "planned_performer": "Crew A",
        }
        
        result = build_assignment_planning_readiness(row)
        assert result["status"] == "ready"
        assert result["missing_required"] == []
        assert result["supports_weekly_rollover"] is True
        assert result["supports_monday_look_behind"] is True

    def test_build_assignment_planning_readiness_needs_attention(self):
        """build_assignment_planning_readiness returns needs_attention when required fields missing."""
        from services.cost_codes.foundation import build_assignment_planning_readiness
        
        row = {
            "code": "CC-1",
            "item_name": "Test Item",
            "unit_of_measure": "LF",
            "authorized_quantity": 100,
            "schedule_start_date": "",  # Missing
            "duration_days": 5,
            "schedule_phase": "",  # Missing
            "planned_performer": "",  # Missing
        }
        
        result = build_assignment_planning_readiness(row)
        assert result["status"] == "needs_attention"
        assert "schedule_start_date" in result["missing_required"]
        assert "schedule_phase" in result["missing_required"]
        assert "planned_performer" in result["missing_required"]
        assert result["supports_weekly_rollover"] is False

    def test_build_planning_readiness_aggregates_assignments(self):
        """build_planning_readiness aggregates readiness across all assignments."""
        from services.cost_codes.foundation import build_planning_readiness
        
        assignments = [
            {
                "code": "CC-1",
                "item_name": "Item 1",
                "unit_of_measure": "LF",
                "authorized_quantity": 100,
                "schedule_start_date": "2026-07-18",
                "duration_days": 5,
                "schedule_phase": "Phase 1",
                "planned_performer": "Crew A",
            },
            {
                "code": "CC-2",
                "item_name": "Item 2",
                "unit_of_measure": "CY",
                "authorized_quantity": 50,
                "schedule_start_date": "",  # Missing
                "duration_days": 3,
                "schedule_phase": "",  # Missing
                "planned_performer": "",  # Missing
            },
        ]
        
        result = build_planning_readiness(assignments)
        assert result["assignment_count"] == 2
        assert result["ready_assignments"] == 1
        assert result["needs_attention_assignments"] == 1
        assert result["status"] == "needs_attention"
        assert result["missing_required_counts"]["schedule_start_date"] == 1
        assert result["missing_required_counts"]["schedule_phase"] == 1
        assert result["missing_required_counts"]["planned_performer"] == 1

    def test_build_planning_lifecycle_snapshot_ready_to_publish(self):
        """build_planning_lifecycle_snapshot returns ready_to_publish when foundation is ready."""
        from services.cost_codes.foundation import build_planning_lifecycle_snapshot
        
        planning_readiness = {
            "status": "ready",
            "assignment_count": 2,
            "supports_weekly_rollover": True,
            "supports_monday_look_behind": True,
        }
        
        result = build_planning_lifecycle_snapshot(
            planning_readiness=planning_readiness,
            stored={"has_unpublished_changes": True},
            schedule_window={"anchor_date": "2026-07-18", "start_date": "2026-07-11", "end_date": "2026-07-25"},
        )
        
        assert result["status"] == "ready_to_publish"
        assert result["supports_publish"] is True
        assert result["has_unpublished_changes"] is True

    def test_build_planning_lifecycle_snapshot_published(self):
        """build_planning_lifecycle_snapshot returns published when published_at is set and no changes."""
        from services.cost_codes.foundation import build_planning_lifecycle_snapshot
        
        planning_readiness = {
            "status": "ready",
            "assignment_count": 2,
            "supports_weekly_rollover": True,
            "supports_monday_look_behind": True,
        }
        
        result = build_planning_lifecycle_snapshot(
            planning_readiness=planning_readiness,
            stored={
                "published_at": "2026-07-18T10:00:00Z",
                "has_unpublished_changes": False,
            },
            schedule_window={},
        )
        
        assert result["status"] == "published"
        assert result["has_unpublished_changes"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
