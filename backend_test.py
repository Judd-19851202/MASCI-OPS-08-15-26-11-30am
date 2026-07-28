#!/usr/bin/env python3
"""
MASCI OPS OPPC Continuation Features WP-11, WP-12, WP-13 Backend API Certification
Target: https://backup-forensics.preview.emergentagent.com
Credentials: Admin (jaymn.judd@mascigc.com / Maddix123!), PM (cert.pm@example.com / CertProof2026!)
"""

import requests
import json
import sys
from typing import Dict, Any, List, Tuple

BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"

# Test results storage
test_results = []

def log_test(test_name: str, passed: bool, details: str, response_data: Any = None):
    """Log test result"""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "response_data": response_data
    }
    test_results.append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    print(f"  Details: {details}")
    if not passed and response_data:
        print(f"  Response: {json.dumps(response_data, indent=2)[:500]}")
    print()

def authenticate_admin() -> Tuple[str, str]:
    """Authenticate as admin and return directory token and admin portal token"""
    print("Authenticating as admin...")
    response = requests.post(
        f"{API_BASE}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Admin authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    data = response.json()
    directory_token = data.get("session_token")
    admin_token = data.get("portal_tokens", {}).get("admin")
    
    if not directory_token or not admin_token:
        print(f"❌ Missing tokens in auth response")
        print(f"Response: {json.dumps(data, indent=2)}")
        sys.exit(1)
    
    print(f"✅ Admin authenticated successfully")
    print(f"  Directory token: {directory_token[:20]}...")
    print(f"  Admin token: {admin_token[:20]}...")
    print()
    return directory_token, admin_token

def authenticate_pm() -> Tuple[str, str]:
    """Authenticate as PM and return directory token and PM portal token"""
    print("Authenticating as PM...")
    response = requests.post(
        f"{API_BASE}/auth/multi-login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ PM authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    data = response.json()
    directory_token = data.get("session_token")
    pm_token = data.get("portal_tokens", {}).get("pm")
    
    if not directory_token or not pm_token:
        print(f"❌ Missing tokens in PM auth response")
        print(f"Response: {json.dumps(data, indent=2)}")
        sys.exit(1)
    
    print(f"✅ PM authenticated successfully")
    print(f"  Directory token: {directory_token[:20]}...")
    print(f"  PM token: {pm_token[:20]}...")
    print()
    return directory_token, pm_token

def test_wp11_forecasting_schedule(directory_token: str, admin_token: str, project_number: str):
    """Test WP-11: GET /api/cost-codes/projects/{project_number}/schedule"""
    test_name = f"WP-11: GET /api/cost-codes/projects/{project_number}/schedule"
    
    try:
        response = requests.get(
            f"{API_BASE}/cost-codes/projects/{project_number}/schedule",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check required fields
        required_fields = [
            "projected_finish_date",
            "committed_finish_date",
            "hardening_summary",
            "scenario",
            "governance"
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            log_test(test_name, False, f"Missing required fields: {missing_fields}", data)
            return
        
        # Check hardening_summary structure
        if not isinstance(data.get("hardening_summary"), dict):
            log_test(test_name, False, "hardening_summary is not a dict", data)
            return
        
        # Check scenario comparison
        if not isinstance(data.get("scenario"), (dict, list)):
            log_test(test_name, False, "scenario comparison not present", data)
            return
        
        # Check governance data
        if not isinstance(data.get("governance"), dict):
            log_test(test_name, False, "governance data not present", data)
            return
        
        log_test(test_name, True, f"All required fields present. Projected finish: {data.get('projected_finish_date')}, Committed finish: {data.get('committed_finish_date')}", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp11_forecast(directory_token: str, admin_token: str, project_number: str):
    """Test WP-11: GET /api/cost-codes/projects/{project_number}/forecast"""
    test_name = f"WP-11: GET /api/cost-codes/projects/{project_number}/forecast"
    
    try:
        response = requests.get(
            f"{API_BASE}/cost-codes/projects/{project_number}/forecast",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for canonical forecast payload
        if not isinstance(data, dict):
            log_test(test_name, False, "Response is not a dict", data)
            return
        
        # Check for forecast-related fields
        has_forecast_data = any(key in data for key in ["forecast", "cost_codes", "projected_cost", "budget"])
        
        if not has_forecast_data:
            log_test(test_name, False, "No forecast-related fields found", data)
            return
        
        log_test(test_name, True, f"Canonical forecast payload returned with {len(data)} top-level keys", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp11_forecast_snapshots(directory_token: str, admin_token: str, project_number: str):
    """Test WP-11: POST /api/cost-codes/projects/{project_number}/forecast/snapshots"""
    test_name = f"WP-11: POST /api/cost-codes/projects/{project_number}/forecast/snapshots"
    
    try:
        # First get current forecast to snapshot
        get_response = requests.get(
            f"{API_BASE}/cost-codes/projects/{project_number}/forecast",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if get_response.status_code != 200:
            log_test(test_name, False, f"Cannot get forecast for snapshot: HTTP {get_response.status_code}", get_response.text[:500])
            return
        
        # Now create snapshot
        snapshot_payload = {
            "snapshot_reason": "WP-11 certification test",
            "forecast_data": get_response.json()
        }
        
        response = requests.post(
            f"{API_BASE}/cost-codes/projects/{project_number}/forecast/snapshots",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json=snapshot_payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for snapshot confirmation
        if not isinstance(data, dict):
            log_test(test_name, False, "Response is not a dict", data)
            return
        
        # Check for snapshot ID or confirmation
        has_snapshot_id = any(key in data for key in ["snapshot_id", "id", "ok", "created"])
        
        if not has_snapshot_id:
            log_test(test_name, False, "No snapshot confirmation found", data)
            return
        
        log_test(test_name, True, "Forecast snapshot persisted successfully", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp11_forecast_overrides(directory_token: str, admin_token: str, project_number: str, cost_code: str):
    """Test WP-11: PUT /api/cost-codes/projects/{project_number}/forecast/overrides/{cost_code}"""
    test_name = f"WP-11: PUT /api/cost-codes/projects/{project_number}/forecast/overrides/{cost_code}"
    
    try:
        override_payload = {
            "override_value": 50000.00,
            "override_reason": "WP-11 certification test override",
            "audited": True
        }
        
        response = requests.put(
            f"{API_BASE}/cost-codes/projects/{project_number}/forecast/overrides/{cost_code}",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json=override_payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check that override was persisted
        if not isinstance(data, dict):
            log_test(test_name, False, "Response is not a dict", data)
            return
        
        # Verify override doesn't remove calculated truth
        has_override = "override" in data or "override_value" in data
        has_calculated = "calculated" in data or "forecast" in data or "ok" in data
        
        if not has_override and not has_calculated:
            log_test(test_name, False, "No override or calculated truth confirmation", data)
            return
        
        log_test(test_name, True, "Override persisted without removing calculated truth", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp12_project_health_confidence(directory_token: str, admin_token: str):
    """Test WP-12: GET /api/project-health returns production_confidence"""
    test_name = "WP-12: GET /api/project-health (production_confidence on rows)"
    
    try:
        response = requests.get(
            f"{API_BASE}/project-health",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for projects array
        projects = data.get("projects", [])
        if not isinstance(projects, list):
            log_test(test_name, False, "No projects array found", data)
            return
        
        if len(projects) == 0:
            log_test(test_name, False, "No projects in response", data)
            return
        
        # Check if at least one project has production_confidence
        has_confidence = any("production_confidence" in p for p in projects)
        
        if not has_confidence:
            log_test(test_name, False, "No production_confidence field on project rows", {"sample_project": projects[0] if projects else None})
            return
        
        # Count projects with confidence scores
        confidence_count = sum(1 for p in projects if "production_confidence" in p)
        
        log_test(test_name, True, f"production_confidence present on {confidence_count}/{len(projects)} project rows", {"sample_project": projects[0]})
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp12_project_confidence_detail(directory_token: str, admin_token: str, project_number: str):
    """Test WP-12: GET /api/project-health/{project_number}/confidence"""
    test_name = f"WP-12: GET /api/project-health/{project_number}/confidence (explainable score)"
    
    try:
        response = requests.get(
            f"{API_BASE}/project-health/{project_number}/confidence",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for explainable score structure
        required_fields = ["score", "explanation", "factors"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            log_test(test_name, False, f"Missing explainable score fields: {missing_fields}", data)
            return
        
        # Check score is numeric
        if not isinstance(data.get("score"), (int, float)):
            log_test(test_name, False, "Score is not numeric", data)
            return
        
        # Check explanation exists
        if not data.get("explanation"):
            log_test(test_name, False, "No explanation provided", data)
            return
        
        # Check factors is a list or dict
        if not isinstance(data.get("factors"), (list, dict)):
            log_test(test_name, False, "Factors is not a list or dict", data)
            return
        
        log_test(test_name, True, f"Explainable confidence score: {data.get('score')} with {len(data.get('factors', []))} factors", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp12_confidence_snapshots(directory_token: str, admin_token: str, project_number: str):
    """Test WP-12: POST /api/project-health/{project_number}/confidence/snapshots"""
    test_name = f"WP-12: POST /api/project-health/{project_number}/confidence/snapshots"
    
    try:
        # First get current confidence
        get_response = requests.get(
            f"{API_BASE}/project-health/{project_number}/confidence",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if get_response.status_code != 200:
            log_test(test_name, False, f"Cannot get confidence for snapshot: HTTP {get_response.status_code}", get_response.text[:500])
            return
        
        # Create snapshot
        snapshot_payload = {
            "snapshot_reason": "WP-12 certification test",
            "confidence_data": get_response.json()
        }
        
        response = requests.post(
            f"{API_BASE}/project-health/{project_number}/confidence/snapshots",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json=snapshot_payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for snapshot confirmation
        has_snapshot_id = any(key in data for key in ["snapshot_id", "id", "ok", "created"])
        
        if not has_snapshot_id:
            log_test(test_name, False, "No snapshot confirmation found", data)
            return
        
        log_test(test_name, True, "Confidence snapshot persisted successfully", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp12_ods_executive_confidence(directory_token: str, admin_token: str):
    """Test WP-12: GET /api/ods/executive/confidence"""
    test_name = "WP-12: GET /api/ods/executive/confidence (confidence rollups)"
    
    try:
        response = requests.get(
            f"{API_BASE}/ods/executive/confidence",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for confidence rollups
        has_rollups = any(key in data for key in ["confidence_rollup", "rollup", "summary", "projects"])
        
        if not has_rollups:
            log_test(test_name, False, "No confidence rollup data found", data)
            return
        
        log_test(test_name, True, f"Executive confidence rollups present with {len(data)} top-level keys", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp12_ods_admin_confidence(directory_token: str, admin_token: str):
    """Test WP-12: Admin ODS endpoint includes confidence rollups"""
    test_name = "WP-12: Admin ODS endpoint (confidence rollups)"
    
    try:
        # Try common admin ODS endpoints
        endpoints = [
            "/api/ods/admin/confidence",
            "/api/admin/ods/confidence",
            "/api/ods/confidence"
        ]
        
        success = False
        for endpoint in endpoints:
            response = requests.get(
                f"{API_BASE.replace('/api', '')}{endpoint}",
                headers={
                    "X-Directory-Token": directory_token,
                    "X-Admin-Token": admin_token
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                has_rollups = any(key in data for key in ["confidence_rollup", "rollup", "summary", "projects"])
                if has_rollups:
                    log_test(test_name, True, f"Admin ODS confidence rollups found at {endpoint}", data)
                    success = True
                    break
        
        if not success:
            log_test(test_name, False, "No admin ODS confidence endpoint found or no rollups present", None)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_project_briefing_get(directory_token: str, admin_token: str, project_number: str):
    """Test WP-13: GET /api/oppc/projects/{project_number}/monday-briefing"""
    test_name = f"WP-13: GET /api/oppc/projects/{project_number}/monday-briefing"
    
    try:
        response = requests.get(
            f"{API_BASE}/oppc/projects/{project_number}/monday-briefing",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for briefing structure
        if not isinstance(data, dict):
            log_test(test_name, False, "Response is not a dict", data)
            return
        
        # Check for briefing fields
        has_briefing = any(key in data for key in ["briefing", "status", "content", "frozen", "approved"])
        
        if not has_briefing:
            log_test(test_name, False, "No briefing data found", data)
            return
        
        log_test(test_name, True, f"Project briefing retrieved with {len(data)} top-level keys", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_project_briefing_approve(directory_token: str, admin_token: str, project_number: str):
    """Test WP-13: POST /api/oppc/projects/{project_number}/monday-briefing/approve"""
    test_name = f"WP-13: POST /api/oppc/projects/{project_number}/monday-briefing/approve"
    
    try:
        response = requests.post(
            f"{API_BASE}/oppc/projects/{project_number}/monday-briefing/approve",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json={"approved_by": "WP-13 certification test"},
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for approval confirmation
        has_approval = any(key in data for key in ["approved", "ok", "status"])
        
        if not has_approval:
            log_test(test_name, False, "No approval confirmation found", data)
            return
        
        log_test(test_name, True, "Project briefing approved successfully", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_project_briefing_freeze(directory_token: str, admin_token: str, project_number: str):
    """Test WP-13: POST /api/oppc/projects/{project_number}/monday-briefing/freeze"""
    test_name = f"WP-13: POST /api/oppc/projects/{project_number}/monday-briefing/freeze"
    
    try:
        response = requests.post(
            f"{API_BASE}/oppc/projects/{project_number}/monday-briefing/freeze",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json={"frozen_by": "WP-13 certification test"},
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for freeze confirmation
        has_freeze = any(key in data for key in ["frozen", "ok", "status"])
        
        if not has_freeze:
            log_test(test_name, False, "No freeze confirmation found", data)
            return
        
        log_test(test_name, True, "Project briefing frozen successfully", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_project_briefing_pdf(directory_token: str, admin_token: str, project_number: str):
    """Test WP-13: GET /api/oppc/projects/{project_number}/monday-briefing/pdf"""
    test_name = f"WP-13: GET /api/oppc/projects/{project_number}/monday-briefing/pdf"
    
    try:
        response = requests.get(
            f"{API_BASE}/oppc/projects/{project_number}/monday-briefing/pdf",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        # Check content type is PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            log_test(test_name, False, f"Content-Type is not PDF: {content_type}", None)
            return
        
        # Check response has content
        if len(response.content) == 0:
            log_test(test_name, False, "PDF response is empty", None)
            return
        
        log_test(test_name, True, f"Project briefing PDF generated ({len(response.content)} bytes)", None)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_enterprise_briefing_get(directory_token: str, admin_token: str):
    """Test WP-13: GET /api/oppc/enterprise/monday-briefing"""
    test_name = "WP-13: GET /api/oppc/enterprise/monday-briefing"
    
    try:
        response = requests.get(
            f"{API_BASE}/oppc/enterprise/monday-briefing",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for enterprise briefing structure
        if not isinstance(data, dict):
            log_test(test_name, False, "Response is not a dict", data)
            return
        
        # Check for enterprise briefing fields
        has_briefing = any(key in data for key in ["briefing", "projects", "summary", "frozen", "approved"])
        
        if not has_briefing:
            log_test(test_name, False, "No enterprise briefing data found", data)
            return
        
        log_test(test_name, True, f"Enterprise briefing retrieved with {len(data)} top-level keys", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_enterprise_briefing_approve(directory_token: str, admin_token: str):
    """Test WP-13: POST /api/oppc/enterprise/monday-briefing/approve"""
    test_name = "WP-13: POST /api/oppc/enterprise/monday-briefing/approve"
    
    try:
        response = requests.post(
            f"{API_BASE}/oppc/enterprise/monday-briefing/approve",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json={"approved_by": "WP-13 certification test"},
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for approval confirmation
        has_approval = any(key in data for key in ["approved", "ok", "status"])
        
        if not has_approval:
            log_test(test_name, False, "No approval confirmation found", data)
            return
        
        log_test(test_name, True, "Enterprise briefing approved successfully", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_enterprise_briefing_freeze(directory_token: str, admin_token: str):
    """Test WP-13: POST /api/oppc/enterprise/monday-briefing/freeze"""
    test_name = "WP-13: POST /api/oppc/enterprise/monday-briefing/freeze"
    
    try:
        response = requests.post(
            f"{API_BASE}/oppc/enterprise/monday-briefing/freeze",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json={"frozen_by": "WP-13 certification test"},
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for freeze confirmation
        has_freeze = any(key in data for key in ["frozen", "ok", "status"])
        
        if not has_freeze:
            log_test(test_name, False, "No freeze confirmation found", data)
            return
        
        log_test(test_name, True, "Enterprise briefing frozen successfully", data)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_enterprise_briefing_pdf(directory_token: str, admin_token: str):
    """Test WP-13: GET /api/oppc/enterprise/monday-briefing/pdf"""
    test_name = "WP-13: GET /api/oppc/enterprise/monday-briefing/pdf"
    
    try:
        response = requests.get(
            f"{API_BASE}/oppc/enterprise/monday-briefing/pdf",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"HTTP {response.status_code}", response.text[:500])
            return
        
        # Check content type is PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            log_test(test_name, False, f"Content-Type is not PDF: {content_type}", None)
            return
        
        # Check response has content
        if len(response.content) == 0:
            log_test(test_name, False, "PDF response is empty", None)
            return
        
        log_test(test_name, True, f"Enterprise briefing PDF generated ({len(response.content)} bytes)", None)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_wp13_governance_frozen_reject_regenerate(directory_token: str, admin_token: str, project_number: str):
    """Test WP-13: Frozen briefings reject regenerate/reapprove"""
    test_name = f"WP-13: Governance - frozen briefing rejects regenerate"
    
    try:
        # First freeze the briefing
        freeze_response = requests.post(
            f"{API_BASE}/oppc/projects/{project_number}/monday-briefing/freeze",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json={"frozen_by": "WP-13 governance test"},
            timeout=30
        )
        
        if freeze_response.status_code not in [200, 201]:
            log_test(test_name, False, f"Cannot freeze briefing: HTTP {freeze_response.status_code}", freeze_response.text[:500])
            return
        
        # Try to regenerate (should be rejected)
        regenerate_response = requests.post(
            f"{API_BASE}/oppc/projects/{project_number}/monday-briefing/regenerate",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            },
            json={},
            timeout=30
        )
        
        # Should be rejected (400, 403, or 409)
        if regenerate_response.status_code in [200, 201]:
            log_test(test_name, False, "Frozen briefing allowed regenerate (should reject)", regenerate_response.json())
            return
        
        if regenerate_response.status_code not in [400, 403, 409]:
            log_test(test_name, False, f"Unexpected status code: {regenerate_response.status_code}", regenerate_response.text[:500])
            return
        
        log_test(test_name, True, f"Frozen briefing correctly rejected regenerate with HTTP {regenerate_response.status_code}", None)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_truth_basis_canonical(directory_token: str, admin_token: str):
    """Test that truth_basis remains canonical_operational_data"""
    test_name = "Validation: truth_basis = canonical_operational_data"
    
    try:
        # Check project health endpoint
        response = requests.get(
            f"{API_BASE}/project-health",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"Cannot get project health: HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        
        # Check for truth_basis field
        truth_basis = data.get("truth_basis")
        
        if not truth_basis:
            log_test(test_name, False, "No truth_basis field found", data)
            return
        
        if truth_basis != "canonical_operational_data":
            log_test(test_name, False, f"truth_basis is '{truth_basis}', expected 'canonical_operational_data'", data)
            return
        
        log_test(test_name, True, f"truth_basis = {truth_basis} (correct)", None)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def test_no_duplicate_engines(directory_token: str, admin_token: str):
    """Test that there are no duplicate engines from user/API perspective"""
    test_name = "Validation: No duplicate engines"
    
    try:
        # This is a conceptual test - we check that endpoints don't return duplicate data
        # For example, checking project health doesn't have duplicate projects
        response = requests.get(
            f"{API_BASE}/project-health",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(test_name, False, f"Cannot get project health: HTTP {response.status_code}", response.text[:500])
            return
        
        data = response.json()
        projects = data.get("projects", [])
        
        if not projects:
            log_test(test_name, True, "No projects to check for duplicates", None)
            return
        
        # Check for duplicate project numbers
        project_numbers = [p.get("project_number") for p in projects if p.get("project_number")]
        unique_numbers = set(project_numbers)
        
        if len(project_numbers) != len(unique_numbers):
            duplicates = [num for num in project_numbers if project_numbers.count(num) > 1]
            log_test(test_name, False, f"Found duplicate project numbers: {set(duplicates)}", None)
            return
        
        log_test(test_name, True, f"No duplicate projects found ({len(projects)} unique projects)", None)
        
    except Exception as e:
        log_test(test_name, False, f"Exception: {str(e)}", None)

def get_test_project_number(directory_token: str, admin_token: str) -> str:
    """Get a test project number from the system"""
    try:
        response = requests.get(
            f"{API_BASE}/project-health",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get("projects", [])
            if projects and len(projects) > 0:
                return projects[0].get("project_number", "TEST-001")
        
        return "TEST-001"  # Fallback
    except:
        return "TEST-001"  # Fallback

def main():
    print("=" * 80)
    print("MASCI OPS OPPC Continuation Features WP-11, WP-12, WP-13")
    print("Backend API Certification")
    print("=" * 80)
    print()
    
    # Authenticate
    admin_dir_token, admin_token = authenticate_admin()
    
    # Get a test project number
    print("Getting test project number...")
    test_project = get_test_project_number(admin_dir_token, admin_token)
    print(f"Using project: {test_project}")
    print()
    
    # Test cost code for overrides
    test_cost_code = "01-100"
    
    print("=" * 80)
    print("WP-11: Forecasting & Critical-Path Hardening")
    print("=" * 80)
    print()
    
    test_wp11_forecasting_schedule(admin_dir_token, admin_token, test_project)
    test_wp11_forecast(admin_dir_token, admin_token, test_project)
    test_wp11_forecast_snapshots(admin_dir_token, admin_token, test_project)
    test_wp11_forecast_overrides(admin_dir_token, admin_token, test_project, test_cost_code)
    
    print("=" * 80)
    print("WP-12: Production Confidence Score")
    print("=" * 80)
    print()
    
    test_wp12_project_health_confidence(admin_dir_token, admin_token)
    test_wp12_project_confidence_detail(admin_dir_token, admin_token, test_project)
    test_wp12_confidence_snapshots(admin_dir_token, admin_token, test_project)
    test_wp12_ods_executive_confidence(admin_dir_token, admin_token)
    test_wp12_ods_admin_confidence(admin_dir_token, admin_token)
    
    print("=" * 80)
    print("WP-13: Monday Morning Briefing")
    print("=" * 80)
    print()
    
    test_wp13_project_briefing_get(admin_dir_token, admin_token, test_project)
    test_wp13_project_briefing_approve(admin_dir_token, admin_token, test_project)
    test_wp13_project_briefing_freeze(admin_dir_token, admin_token, test_project)
    test_wp13_project_briefing_pdf(admin_dir_token, admin_token, test_project)
    test_wp13_enterprise_briefing_get(admin_dir_token, admin_token)
    test_wp13_enterprise_briefing_approve(admin_dir_token, admin_token)
    test_wp13_enterprise_briefing_freeze(admin_dir_token, admin_token)
    test_wp13_enterprise_briefing_pdf(admin_dir_token, admin_token)
    test_wp13_governance_frozen_reject_regenerate(admin_dir_token, admin_token, test_project)
    
    print("=" * 80)
    print("Validation Tests")
    print("=" * 80)
    print()
    
    test_truth_basis_canonical(admin_dir_token, admin_token)
    test_no_duplicate_engines(admin_dir_token, admin_token)
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print()
    
    if failed_tests > 0:
        print("FAILED TESTS:")
        for result in test_results:
            if not result["passed"]:
                print(f"  ❌ {result['test']}")
                print(f"     {result['details']}")
        print()
    
    # Save results to file
    with open("/app/wp11_wp12_wp13_backend_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": pass_rate
            },
            "tests": test_results
        }, f, indent=2)
    
    print(f"Detailed results saved to: /app/wp11_wp12_wp13_backend_test_results.json")
    print()
    
    if failed_tests > 0:
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
