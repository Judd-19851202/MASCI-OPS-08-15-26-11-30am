"""
WP-OPPC-14F Operational Case Management Backend Verification

This script verifies the new WP-OPPC-14F Operational Case Management backend
against https://backup-forensics.preview.emergentagent.com using super admin credentials.

Test flows:
1. Obtain admin + directory session
2. GET /api/admin/operations-control/cases (returns persisted cases and summary counts)
3. POST /api/admin/operations-control/certifications/preview-daily-report (creates fresh preview Daily Report and one governed case)
4. POST /api/admin/operations-control/certifications/run (returns OPERATIONS CONTROL PLANE v1 — VERIFIED COMPLETE)
5. GET case detail/assembly/timeline/graph endpoints for a returned case id
6. POST task/evidence/baseline/export endpoints
7. POST transition endpoints including invalid closure case to confirm server validation
8. POST communication acknowledgement
9. Confirm duplicate handling and no duplicate governed outcomes for same source record/policy

Backend files of interest:
- /app/backend/services/operations_control/case_management.py
- /app/backend/services/operations_control/control_plane.py
- /app/backend/routes/operations_control.py
- /app/backend/routes/daily_reports.py
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results
test_results: List[Dict[str, Any]] = []


def log_test(test_name: str, passed: bool, details: str = "", response_data: Optional[Dict[str, Any]] = None):
    """Log test result."""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if response_data:
        result["response_data"] = response_data
    test_results.append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"  {details}")


def test_1_obtain_admin_directory_session():
    """Test 1: Obtain admin + directory session via multi-login."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 1: Obtain admin + directory session",
                False,
                f"Multi-login failed with status {response.status_code}: {response.text[:200]}",
            )
            return None, None
        
        data = response.json()
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        if not session_token or not admin_token:
            log_test(
                "Test 1: Obtain admin + directory session",
                False,
                f"Missing tokens - session_token: {bool(session_token)}, admin_token: {bool(admin_token)}",
            )
            return None, None
        
        log_test(
            "Test 1: Obtain admin + directory session",
            True,
            f"Successfully obtained session_token and admin_token. Portal tokens: {list(portal_tokens.keys())}",
            {"session_token_present": True, "admin_token_present": True, "portals": list(portal_tokens.keys())},
        )
        return session_token, admin_token
    
    except Exception as e:
        log_test("Test 1: Obtain admin + directory session", False, f"Exception: {str(e)}")
        return None, None


def test_2_get_cases(session_token: str, admin_token: str):
    """Test 2: GET /api/admin/operations-control/cases returns persisted cases and summary counts."""
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 2: GET /api/admin/operations-control/cases",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
            return None
        
        data = response.json()
        
        # Verify response structure
        if "cases" not in data or "summary" not in data:
            log_test(
                "Test 2: GET /api/admin/operations-control/cases",
                False,
                f"Missing required fields. Keys: {list(data.keys())}",
            )
            return None
        
        cases = data.get("cases", [])
        summary = data.get("summary", {})
        
        log_test(
            "Test 2: GET /api/admin/operations-control/cases",
            True,
            f"Retrieved {len(cases)} cases. Summary: total={summary.get('total')}, open={summary.get('open')}, escalated={summary.get('escalated')}, pending_verification={summary.get('pending_verification')}, critical={summary.get('critical')}",
            {"case_count": len(cases), "summary": summary, "sample_case": cases[0] if cases else None},
        )
        return data
    
    except Exception as e:
        log_test("Test 2: GET /api/admin/operations-control/cases", False, f"Exception: {str(e)}")
        return None


def test_3_create_preview_daily_report(session_token: str, admin_token: str):
    """Test 3: POST /api/admin/operations-control/certifications/preview-daily-report creates fresh preview Daily Report and one governed case."""
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/preview-daily-report",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 3: POST preview-daily-report",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
            return None
        
        data = response.json()
        
        # Verify response structure - API returns certification, daily_report, case
        daily_report = data.get("daily_report")
        case = data.get("case")
        certification = data.get("certification")
        
        if not daily_report or not case:
            log_test(
                "Test 3: POST preview-daily-report",
                False,
                f"Missing daily_report or case. Keys: {list(data.keys())}",
            )
            return None
        
        log_test(
            "Test 3: POST preview-daily-report",
            True,
            f"Created preview Daily Report (id={daily_report.get('id')}) and governed case (id={case.get('id')}, case_number={case.get('case_number')}, status={case.get('status')})",
            {"daily_report_id": daily_report.get("id"), "case_id": case.get("id"), "case_number": case.get("case_number"), "case_status": case.get("status")},
        )
        return data
    
    except Exception as e:
        log_test("Test 3: POST preview-daily-report", False, f"Exception: {str(e)}")
        return None


def test_4_run_certification(session_token: str, admin_token: str):
    """Test 4: POST /api/admin/operations-control/certifications/run returns OPERATIONS CONTROL PLANE v1 — VERIFIED COMPLETE."""
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/run",
            headers=headers,
            timeout=60,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 4: POST certifications/run",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
            return None
        
        data = response.json()
        
        # Verify response structure - API returns release_determination
        release_determination = data.get("release_determination", "")
        primary_case = data.get("primary_case")
        
        # Check for expected message
        expected_message = "OPERATIONS CONTROL PLANE v1 — VERIFIED COMPLETE"
        if expected_message not in release_determination:
            log_test(
                "Test 4: POST certifications/run",
                False,
                f"Expected message '{expected_message}' not found. Release determination: {release_determination}",
            )
            return None
        
        log_test(
            "Test 4: POST certifications/run",
            True,
            f"Certification run successful. Release determination: {release_determination}. Primary case: {primary_case.get('case_number') if primary_case else 'N/A'}",
            {"release_determination": release_determination, "primary_case_id": primary_case.get("id") if primary_case else None},
        )
        return data
    
    except Exception as e:
        log_test("Test 4: POST certifications/run", False, f"Exception: {str(e)}")
        return None


def test_5_case_detail_endpoints(session_token: str, admin_token: str, case_id: str):
    """Test 5: GET case detail/assembly/timeline/graph endpoints for a returned case id."""
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token,
    }
    
    # Test 5a: GET case detail
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 5a: GET case detail",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            log_test(
                "Test 5a: GET case detail",
                True,
                f"Retrieved case detail. Case number: {data.get('case_number')}, Status: {data.get('status')}, Severity: {data.get('severity')}",
                {"case_number": data.get("case_number"), "status": data.get("status"), "severity": data.get("severity")},
            )
    except Exception as e:
        log_test("Test 5a: GET case detail", False, f"Exception: {str(e)}")
    
    # Test 5b: GET case assembly
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/assembly",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 5b: GET case assembly",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            proof_chain = data.get("proof_chain", [])
            log_test(
                "Test 5b: GET case assembly",
                True,
                f"Retrieved case assembly. Proof chain items: {len(proof_chain)}",
                {"proof_chain_count": len(proof_chain), "proof_chain_sample": proof_chain[:3] if proof_chain else []},
            )
    except Exception as e:
        log_test("Test 5b: GET case assembly", False, f"Exception: {str(e)}")
    
    # Test 5c: GET case timeline
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/timeline",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 5c: GET case timeline",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            timeline = data.get("timeline", [])
            log_test(
                "Test 5c: GET case timeline",
                True,
                f"Retrieved case timeline. Timeline items: {data.get('count', 0)}",
                {"timeline_count": data.get("count", 0), "timeline_sample": timeline[:3] if timeline else []},
            )
    except Exception as e:
        log_test("Test 5c: GET case timeline", False, f"Exception: {str(e)}")
    
    # Test 5d: GET case graph
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/graph",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 5d: GET case graph",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            log_test(
                "Test 5d: GET case graph",
                True,
                f"Retrieved case graph. Nodes: {len(nodes)}, Edges: {len(edges)}",
                {"node_count": len(nodes), "edge_count": len(edges)},
            )
    except Exception as e:
        log_test("Test 5d: GET case graph", False, f"Exception: {str(e)}")


def test_6_case_action_endpoints(session_token: str, admin_token: str, case_id: str):
    """Test 6: POST task/evidence/baseline/export endpoints."""
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token,
    }
    
    # Test 6a: POST create task
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/tasks",
            headers=headers,
            json={
                "title": "WP-OPPC-14F Test Task",
                "description": "Test task created during backend verification",
                "assignee_role": "pm",
                "priority": "High",
                "due_minutes": 1440,
            },
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 6a: POST create task",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            task = data.get("task")
            log_test(
                "Test 6a: POST create task",
                True,
                f"Created task. Task ID: {task.get('id') if task else 'N/A'}",
                {"task_id": task.get("id") if task else None},
            )
    except Exception as e:
        log_test("Test 6a: POST create task", False, f"Exception: {str(e)}")
    
    # Test 6b: POST capture evidence
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/evidence",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 6b: POST capture evidence",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            evidence = data.get("evidence")
            log_test(
                "Test 6b: POST capture evidence",
                True,
                f"Captured evidence. Evidence ID: {evidence.get('id') if evidence else 'N/A'}",
                {"evidence_id": evidence.get("id") if evidence else None},
            )
    except Exception as e:
        log_test("Test 6b: POST capture evidence", False, f"Exception: {str(e)}")
    
    # Test 6c: POST include baseline
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/baseline",
            headers=headers,
            json={"baseline_name": "WP-OPPC-14F Test Baseline"},
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 6c: POST include baseline",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            baseline = data.get("baseline")
            log_test(
                "Test 6c: POST include baseline",
                True,
                f"Included in baseline. Baseline ID: {baseline.get('id') if baseline else 'N/A'}",
                {"baseline_id": baseline.get("id") if baseline else None},
            )
    except Exception as e:
        log_test("Test 6c: POST include baseline", False, f"Exception: {str(e)}")
    
    # Test 6d: POST export evidence package
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/export",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 6d: POST export evidence package",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            export_row = data.get("export")
            log_test(
                "Test 6d: POST export evidence package",
                True,
                f"Exported evidence package. Export ID: {export_row.get('id') if export_row else 'N/A'}",
                {"export_id": export_row.get("id") if export_row else None},
            )
    except Exception as e:
        log_test("Test 6d: POST export evidence package", False, f"Exception: {str(e)}")


def test_7_case_transitions(session_token: str, admin_token: str, case_id: str):
    """Test 7: POST transition endpoints including invalid closure case to confirm server validation."""
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token,
    }
    
    # First, get the case to check its current status
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 7: Case transitions",
                False,
                f"Failed to get case status: {response.status_code}",
            )
            return
        
        case_data = response.json()
        current_status = case_data.get("status")
        
        # Test 7a: Valid transition based on current status
        # If case is CLOSED, try to reopen it first
        if current_status == "CLOSED":
            # Try REOPENED transition
            response = requests.post(
                f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
                headers=headers,
                json={
                    "to_status": "REOPENED",
                    "reason": "WP-OPPC-14F backend verification - reopening closed case",
                },
                timeout=30,
            )
            
            if response.status_code != 200:
                log_test(
                    "Test 7a: Valid transition (REOPENED)",
                    False,
                    f"Request failed with status {response.status_code}: {response.text[:200]}",
                )
            else:
                data = response.json()
                case = data.get("case")
                log_test(
                    "Test 7a: Valid transition (REOPENED)",
                    True,
                    f"Transitioned case from CLOSED to REOPENED. New status: {case.get('status') if case else 'N/A'}",
                    {"old_status": current_status, "new_status": case.get("status") if case else None},
                )
        else:
            # Try UNDER_REVIEW transition for non-closed cases
            response = requests.post(
                f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
                headers=headers,
                json={
                    "to_status": "UNDER_REVIEW",
                    "reason": "WP-OPPC-14F backend verification - valid transition test",
                },
                timeout=30,
            )
            
            if response.status_code != 200:
                log_test(
                    "Test 7a: Valid transition to UNDER_REVIEW",
                    False,
                    f"Request failed with status {response.status_code}: {response.text[:200]}",
                )
            else:
                data = response.json()
                case = data.get("case")
                log_test(
                    "Test 7a: Valid transition to UNDER_REVIEW",
                    True,
                    f"Transitioned case to UNDER_REVIEW. New status: {case.get('status') if case else 'N/A'}",
                    {"old_status": current_status, "new_status": case.get("status") if case else None},
                )
    
    except Exception as e:
        log_test("Test 7a: Valid transition", False, f"Exception: {str(e)}")
    
    # Test 7b: Invalid transition to CLOSED without required fields (should fail with 422)
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
            headers=headers,
            json={
                "to_status": "CLOSED",
                "reason": "",  # Missing required fields for closure
            },
            timeout=30,
        )
        
        # Expect 422 Unprocessable Entity for invalid closure
        if response.status_code == 422:
            log_test(
                "Test 7b: Invalid transition to CLOSED (validation)",
                True,
                f"Server correctly rejected invalid closure with 422: {response.text[:200]}",
                {"status_code": 422, "error": response.text[:200]},
            )
        elif response.status_code == 200:
            log_test(
                "Test 7b: Invalid transition to CLOSED (validation)",
                False,
                "Server accepted invalid closure (should have rejected with 422)",
            )
        else:
            log_test(
                "Test 7b: Invalid transition to CLOSED (validation)",
                False,
                f"Unexpected status code {response.status_code}: {response.text[:200]}",
            )
    except Exception as e:
        log_test("Test 7b: Invalid transition to CLOSED (validation)", False, f"Exception: {str(e)}")


def test_8_communication_acknowledgement(session_token: str, admin_token: str, case_id: str):
    """Test 8: POST communication acknowledgement."""
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token,
    }
    
    # First, get case detail to find communications
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}",
            headers=headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 8: POST communication acknowledgement",
                False,
                f"Failed to get case detail: {response.status_code}",
            )
            return
        
        data = response.json()
        linked_record_ids = data.get("linked_record_ids", {})
        communication_ids = linked_record_ids.get("communication_ids", [])
        
        if not communication_ids:
            log_test(
                "Test 8: POST communication acknowledgement",
                False,
                "No communication_ids found in case linked_record_ids",
            )
            return
        
        # Use first communication
        communication_id = communication_ids[0]
        
        # Acknowledge the communication
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/communications/{communication_id}/ack",
            headers=headers,
            json={"note": "WP-OPPC-14F backend verification - communication acknowledgement test"},
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 8: POST communication acknowledgement",
                False,
                f"Request failed with status {response.status_code}: {response.text[:200]}",
            )
        else:
            data = response.json()
            log_test(
                "Test 8: POST communication acknowledgement",
                True,
                f"Acknowledged communication {communication_id}",
                {"communication_id": communication_id, "ok": data.get("ok")},
            )
    
    except Exception as e:
        log_test("Test 8: POST communication acknowledgement", False, f"Exception: {str(e)}")


def test_9_duplicate_handling(session_token: str, admin_token: str):
    """Test 9: Confirm duplicate handling and no duplicate governed outcomes for same source record/policy."""
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
        }
        
        # Create first preview daily report and case
        response1 = requests.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/preview-daily-report",
            headers=headers,
            timeout=30,
        )
        
        if response1.status_code != 200:
            log_test(
                "Test 9: Duplicate handling",
                False,
                f"First preview-daily-report failed with status {response1.status_code}",
            )
            return
        
        data1 = response1.json()
        case1_id = data1.get("case", {}).get("id")
        daily_report1_id = data1.get("daily_report", {}).get("id")
        
        # Try to create another case from the same daily report (should detect duplicate)
        # This is done by running the certification again
        response2 = requests.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/preview-daily-report",
            headers=headers,
            timeout=30,
        )
        
        if response2.status_code != 200:
            log_test(
                "Test 9: Duplicate handling",
                False,
                f"Second preview-daily-report failed with status {response2.status_code}",
            )
            return
        
        data2 = response2.json()
        case2_id = data2.get("case", {}).get("id")
        daily_report2_id = data2.get("daily_report", {}).get("id")
        
        # Check if duplicate detection is working
        # The system should either:
        # 1. Return the same case (case1_id == case2_id)
        # 2. Create a new daily report but link to existing case
        # 3. Mark the second case as DUPLICATE
        
        # Get both cases to check their status
        response_case1 = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case1_id}",
            headers=headers,
            timeout=30,
        )
        
        response_case2 = requests.get(
            f"{BASE_URL}/api/admin/operations-control/cases/{case2_id}",
            headers=headers,
            timeout=30,
        )
        
        if response_case1.status_code == 200 and response_case2.status_code == 200:
            case1_data = response_case1.json()
            case2_data = response_case2.json()
            
            case1_status = case1_data.get("status")
            case2_status = case2_data.get("status")
            
            # Check if duplicate handling is working
            if case1_id == case2_id:
                log_test(
                    "Test 9: Duplicate handling",
                    True,
                    f"Duplicate detection working - same case returned for both requests (case_id={case1_id})",
                    {"case1_id": case1_id, "case2_id": case2_id, "same_case": True},
                )
            elif case2_status == "DUPLICATE":
                log_test(
                    "Test 9: Duplicate handling",
                    True,
                    f"Duplicate detection working - second case marked as DUPLICATE (case1_id={case1_id}, case2_id={case2_id})",
                    {"case1_id": case1_id, "case2_id": case2_id, "case2_status": case2_status},
                )
            else:
                # Check if they have the same originating event
                case1_origin = case1_data.get("origin", {})
                case2_origin = case2_data.get("origin", {})
                
                if case1_origin.get("originating_event_id") == case2_origin.get("originating_event_id"):
                    log_test(
                        "Test 9: Duplicate handling",
                        False,
                        f"Duplicate NOT detected - two separate cases created for same originating event (case1_id={case1_id}, case2_id={case2_id})",
                        {"case1_id": case1_id, "case2_id": case2_id, "case1_status": case1_status, "case2_status": case2_status},
                    )
                else:
                    log_test(
                        "Test 9: Duplicate handling",
                        True,
                        f"Different originating events - two separate cases expected (case1_id={case1_id}, case2_id={case2_id})",
                        {"case1_id": case1_id, "case2_id": case2_id, "different_origins": True},
                    )
        else:
            log_test(
                "Test 9: Duplicate handling",
                False,
                f"Failed to retrieve cases for duplicate check (case1: {response_case1.status_code}, case2: {response_case2.status_code})",
            )
    
    except Exception as e:
        log_test("Test 9: Duplicate handling", False, f"Exception: {str(e)}")


def main():
    """Run all WP-OPPC-14F backend verification tests."""
    print("=" * 80)
    print("WP-OPPC-14F Operational Case Management Backend Verification")
    print("=" * 80)
    print()
    
    # Test 1: Obtain admin + directory session
    session_token, admin_token = test_1_obtain_admin_directory_session()
    if not session_token or not admin_token:
        print("\n❌ CRITICAL: Failed to obtain authentication tokens. Cannot proceed with tests.")
        sys.exit(1)
    
    print()
    
    # Test 2: GET /api/admin/operations-control/cases
    cases_data = test_2_get_cases(session_token, admin_token)
    
    print()
    
    # Test 3: POST /api/admin/operations-control/certifications/preview-daily-report
    preview_data = test_3_create_preview_daily_report(session_token, admin_token)
    case_id = preview_data.get("case", {}).get("id") if preview_data else None
    
    print()
    
    # Test 4: POST /api/admin/operations-control/certifications/run
    test_4_run_certification(session_token, admin_token)
    
    print()
    
    # Test 5: GET case detail/assembly/timeline/graph endpoints
    if case_id:
        test_5_case_detail_endpoints(session_token, admin_token, case_id)
    else:
        # Try to get a case from the list
        if cases_data and cases_data.get("cases"):
            case_id = cases_data["cases"][0].get("id")
            if case_id:
                test_5_case_detail_endpoints(session_token, admin_token, case_id)
            else:
                print("⚠️  WARNING: No case_id available for Test 5")
        else:
            print("⚠️  WARNING: No case_id available for Test 5")
    
    print()
    
    # Test 6: POST task/evidence/baseline/export endpoints
    if case_id:
        test_6_case_action_endpoints(session_token, admin_token, case_id)
    else:
        print("⚠️  WARNING: No case_id available for Test 6")
    
    print()
    
    # Test 7: POST transition endpoints
    if case_id:
        test_7_case_transitions(session_token, admin_token, case_id)
    else:
        print("⚠️  WARNING: No case_id available for Test 7")
    
    print()
    
    # Test 8: POST communication acknowledgement
    if case_id:
        test_8_communication_acknowledgement(session_token, admin_token, case_id)
    else:
        print("⚠️  WARNING: No case_id available for Test 8")
    
    print()
    
    # Test 9: Duplicate handling
    test_9_duplicate_handling(session_token, admin_token)
    
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass rate: {pass_rate:.1f}%")
    print()
    
    # Save results to file
    with open("/app/wp_oppc_14f_backend_test_results.json", "w") as f:
        json.dump(
            {
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "pass_rate": pass_rate,
                },
                "tests": test_results,
            },
            f,
            indent=2,
        )
    
    print(f"Results saved to /app/wp_oppc_14f_backend_test_results.json")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
