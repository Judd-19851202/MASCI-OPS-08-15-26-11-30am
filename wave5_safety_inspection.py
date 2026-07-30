#!/usr/bin/env python3
"""
WP-16 Wave 5 Safety Certification - Backend API Inspection
Inspection-only. No code changes. No data writes.

Base URL: https://backup-forensics.preview.emergentagent.com
Scope: Verify Safety login, token-backed API access, permissions, operational workflows,
       life-safety/compliance integrity for W5-001 to W5-052.
"""

import requests
import json
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Base configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "safety": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
    "hr": {"email": "cert.hr@example.com", "password": "CertProof2026!"},
    "pm": {"email": "cert.pm@example.com", "password": "CertProof2026!"},
    "shop": {"email": "cert.shop@example.com", "password": "CertProof2026!"},
    "admin_only": {"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
    "super_admin": {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
}

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "critical": [],
    "high": [],
    "medium": [],
    "low": []
}

# Token storage
tokens = {}

def log_result(test_name: str, status: str, details: str, severity: str = "low"):
    """Log test result with severity classification"""
    result = {
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    if status == "PASS":
        test_results["passed"].append(result)
    elif status == "FAIL":
        test_results["failed"].append(result)
        test_results[severity].append(result)
    elif status == "WARN":
        test_results["warnings"].append(result)
    
    # Print to console
    severity_prefix = f"[{severity.upper()}]" if status == "FAIL" else ""
    print(f"{severity_prefix} {status}: {test_name}")
    print(f"  {details}\n")

def safety_login() -> Tuple[bool, Optional[str]]:
    """Test Safety portal login and return token"""
    try:
        response = requests.post(
            f"{API_BASE}/safety/login",
            json=CREDENTIALS["safety"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            if token:
                tokens["safety"] = token
                log_result(
                    "Safety Login",
                    "PASS",
                    f"Safety login successful. Token received. Response keys: {list(data.keys())}"
                )
                return True, token
            else:
                log_result(
                    "Safety Login",
                    "FAIL",
                    f"Login returned 200 but no token found. Response: {json.dumps(data, indent=2)}",
                    "critical"
                )
                return False, None
        else:
            log_result(
                "Safety Login",
                "FAIL",
                f"Login failed with status {response.status_code}. Response: {response.text}",
                "critical"
            )
            return False, None
    except Exception as e:
        log_result(
            "Safety Login",
            "FAIL",
            f"Login exception: {str(e)}",
            "critical"
        )
        return False, None

def multi_portal_login(portal: str) -> Tuple[bool, Optional[Dict]]:
    """Test multi-portal login for non-Safety portals"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/multi-login",
            json=CREDENTIALS[portal],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            portal_tokens = data.get("portal_tokens", {})
            session_token = data.get("session_token")
            
            tokens[portal] = {
                "portal_tokens": portal_tokens,
                "session_token": session_token
            }
            
            log_result(
                f"{portal.upper()} Multi-Portal Login",
                "PASS",
                f"Login successful. Portals: {list(portal_tokens.keys())}"
            )
            return True, tokens[portal]
        else:
            log_result(
                f"{portal.upper()} Multi-Portal Login",
                "FAIL",
                f"Login failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
            return False, None
    except Exception as e:
        log_result(
            f"{portal.upper()} Multi-Portal Login",
            "FAIL",
            f"Login exception: {str(e)}",
            "high"
        )
        return False, None

def test_safety_me():
    """Test /api/safety/me endpoint"""
    if "safety" not in tokens:
        log_result("Safety /me", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/safety/me",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_result(
                "Safety /me",
                "PASS",
                f"Safety /me returned user data. Keys: {list(data.keys())}"
            )
        else:
            log_result(
                "Safety /me",
                "FAIL",
                f"Safety /me failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Safety /me", "FAIL", f"Exception: {str(e)}", "high")

def test_safety_overview():
    """Test /api/safety/overview endpoint"""
    if "safety" not in tokens:
        log_result("Safety Overview", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/safety/overview",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_result(
                "Safety Overview",
                "PASS",
                f"Safety overview returned data. Keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
        else:
            log_result(
                "Safety Overview",
                "FAIL",
                f"Safety overview failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Safety Overview", "FAIL", f"Exception: {str(e)}", "high")

def test_corrective_actions():
    """Test /api/safety/corrective-actions endpoints"""
    if "safety" not in tokens:
        log_result("Corrective Actions List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        # Test list endpoint
        response = requests.get(
            f"{API_BASE}/safety/corrective-actions",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Corrective Actions List",
                "PASS",
                f"Corrective actions list returned {count} items"
            )
            
            # If we have items, test detail endpoint
            if isinstance(data, list) and len(data) > 0:
                first_id = data[0].get("id") or data[0].get("_id")
                if first_id:
                    detail_response = requests.get(
                        f"{API_BASE}/safety/corrective-actions/{first_id}",
                        headers={"X-Safety-Token": tokens["safety"]},
                        timeout=10
                    )
                    if detail_response.status_code == 200:
                        log_result(
                            "Corrective Actions Detail",
                            "PASS",
                            f"Corrective action detail retrieved for ID {first_id}"
                        )
                    else:
                        log_result(
                            "Corrective Actions Detail",
                            "FAIL",
                            f"Detail failed with status {detail_response.status_code}",
                            "medium"
                        )
        else:
            log_result(
                "Corrective Actions List",
                "FAIL",
                f"Corrective actions list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Corrective Actions", "FAIL", f"Exception: {str(e)}", "high")

def test_fire_extinguishers():
    """Test /api/safety/fire-extinguishers endpoints"""
    if "safety" not in tokens:
        log_result("Fire Extinguishers List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/safety/fire-extinguishers",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Fire Extinguishers List",
                "PASS",
                f"Fire extinguishers list returned {count} items"
            )
        else:
            log_result(
                "Fire Extinguishers List",
                "FAIL",
                f"Fire extinguishers list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Fire Extinguishers", "FAIL", f"Exception: {str(e)}", "high")

def test_safety_documents():
    """Test /api/safety/documents endpoints"""
    if "safety" not in tokens:
        log_result("Safety Documents List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/safety/documents",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Safety Documents List",
                "PASS",
                f"Safety documents list returned {count} items"
            )
        else:
            log_result(
                "Safety Documents List",
                "FAIL",
                f"Safety documents list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Safety Documents", "FAIL", f"Exception: {str(e)}", "high")

def test_training_records():
    """Test /api/safety/training-records endpoints"""
    if "safety" not in tokens:
        log_result("Training Records List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/safety/training-records",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Training Records List",
                "PASS",
                f"Training records list returned {count} items"
            )
        else:
            log_result(
                "Training Records List",
                "FAIL",
                f"Training records list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Training Records", "FAIL", f"Exception: {str(e)}", "high")

def test_safety_digest():
    """Test /api/safety/digest endpoints"""
    if "safety" not in tokens:
        log_result("Safety Digest Preview", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/safety/digest/preview",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_result(
                "Safety Digest Preview",
                "PASS",
                f"Safety digest preview returned data. Keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
        else:
            log_result(
                "Safety Digest Preview",
                "FAIL",
                f"Safety digest preview failed with status {response.status_code}. Response: {response.text}",
                "medium"
            )
    except Exception as e:
        log_result("Safety Digest", "FAIL", f"Exception: {str(e)}", "medium")

def test_safety_exports():
    """Test /api/safety/exports endpoints"""
    if "safety" not in tokens:
        log_result("Safety Exports", "FAIL", "No Safety token available", "critical")
        return
    
    export_endpoints = [
        "incidents",
        "corrective-actions",
        "inspections",
        "training-records",
        "fire-extinguishers",
        "documents"
    ]
    
    for endpoint in export_endpoints:
        try:
            response = requests.get(
                f"{API_BASE}/safety/exports/{endpoint}",
                headers={"X-Safety-Token": tokens["safety"]},
                timeout=10
            )
            
            if response.status_code == 200:
                log_result(
                    f"Safety Export - {endpoint}",
                    "PASS",
                    f"Export endpoint returned data (length: {len(response.content)} bytes)"
                )
            else:
                log_result(
                    f"Safety Export - {endpoint}",
                    "FAIL",
                    f"Export failed with status {response.status_code}",
                    "medium"
                )
        except Exception as e:
            log_result(f"Safety Export - {endpoint}", "FAIL", f"Exception: {str(e)}", "medium")

def test_safety_forms_login():
    """Test /api/safety-forms/login endpoint"""
    try:
        # Safety forms uses password-only authentication
        response = requests.post(
            f"{API_BASE}/safety-forms/login",
            json={"password": "safety_forms_password"},  # This is a placeholder
            timeout=10
        )
        
        # We expect this to fail with wrong password, but should return proper error
        if response.status_code in [200, 401]:
            log_result(
                "Safety Forms Login",
                "PASS",
                f"Safety forms login endpoint responding correctly (status {response.status_code})"
            )
        else:
            log_result(
                "Safety Forms Login",
                "FAIL",
                f"Safety forms login returned unexpected status {response.status_code}. Response: {response.text}",
                "medium"
            )
    except Exception as e:
        log_result("Safety Forms Login", "FAIL", f"Exception: {str(e)}", "medium")

def test_safety_forms_check():
    """Test /api/safety-forms/check endpoint"""
    try:
        response = requests.get(
            f"{API_BASE}/safety-forms/check",
            timeout=10
        )
        
        if response.status_code in [200, 401]:
            log_result(
                "Safety Forms Check",
                "PASS",
                f"Safety forms check endpoint responding (status {response.status_code})"
            )
        else:
            log_result(
                "Safety Forms Check",
                "FAIL",
                f"Safety forms check returned unexpected status {response.status_code}",
                "medium"
            )
    except Exception as e:
        log_result("Safety Forms Check", "FAIL", f"Exception: {str(e)}", "medium")

def test_inspections():
    """Test /api/inspections endpoints"""
    if "safety" not in tokens:
        log_result("Inspections List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/inspections",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Inspections List",
                "PASS",
                f"Inspections list returned {count} items"
            )
            
            # Test detail if we have items
            if isinstance(data, list) and len(data) > 0:
                first_id = data[0].get("id") or data[0].get("_id")
                if first_id:
                    detail_response = requests.get(
                        f"{API_BASE}/inspections/{first_id}",
                        headers={"X-Safety-Token": tokens["safety"]},
                        timeout=10
                    )
                    if detail_response.status_code == 200:
                        log_result(
                            "Inspections Detail",
                            "PASS",
                            f"Inspection detail retrieved for ID {first_id}"
                        )
                    else:
                        log_result(
                            "Inspections Detail",
                            "FAIL",
                            f"Detail failed with status {detail_response.status_code}",
                            "medium"
                        )
        else:
            log_result(
                "Inspections List",
                "FAIL",
                f"Inspections list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Inspections", "FAIL", f"Exception: {str(e)}", "high")

def test_meetings():
    """Test /api/meetings endpoints"""
    if "safety" not in tokens:
        log_result("Meetings List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/meetings",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Meetings List",
                "PASS",
                f"Meetings list returned {count} items"
            )
        else:
            log_result(
                "Meetings List",
                "FAIL",
                f"Meetings list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Meetings", "FAIL", f"Exception: {str(e)}", "high")

def test_jhas():
    """Test /api/jhas endpoints"""
    if "safety" not in tokens:
        log_result("JHAs List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/jhas",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "JHAs List",
                "PASS",
                f"JHAs list returned {count} items"
            )
        else:
            log_result(
                "JHAs List",
                "FAIL",
                f"JHAs list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("JHAs", "FAIL", f"Exception: {str(e)}", "high")

def test_incidents():
    """Test /api/incidents endpoints"""
    if "safety" not in tokens:
        log_result("Incidents List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/incidents",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Incidents List",
                "PASS",
                f"Incidents list returned {count} items"
            )
            
            # Test detail and lifecycle if we have items
            if isinstance(data, list) and len(data) > 0:
                first_id = data[0].get("id") or data[0].get("_id")
                if first_id:
                    # Test detail
                    detail_response = requests.get(
                        f"{API_BASE}/incidents/{first_id}",
                        headers={"X-Safety-Token": tokens["safety"]},
                        timeout=10
                    )
                    if detail_response.status_code == 200:
                        log_result(
                            "Incidents Detail",
                            "PASS",
                            f"Incident detail retrieved for ID {first_id}"
                        )
                    else:
                        log_result(
                            "Incidents Detail",
                            "FAIL",
                            f"Detail failed with status {detail_response.status_code}",
                            "high"
                        )
                    
                    # Test lifecycle
                    lifecycle_response = requests.get(
                        f"{API_BASE}/incidents/{first_id}/lifecycle",
                        headers={"X-Safety-Token": tokens["safety"]},
                        timeout=10
                    )
                    if lifecycle_response.status_code == 200:
                        log_result(
                            "Incidents Lifecycle",
                            "PASS",
                            f"Incident lifecycle retrieved for ID {first_id}"
                        )
                    else:
                        log_result(
                            "Incidents Lifecycle",
                            "FAIL",
                            f"Lifecycle failed with status {lifecycle_response.status_code}",
                            "high"
                        )
                    
                    # Test state events
                    state_response = requests.get(
                        f"{API_BASE}/incidents/{first_id}/state-events",
                        headers={"X-Safety-Token": tokens["safety"]},
                        timeout=10
                    )
                    if state_response.status_code == 200:
                        log_result(
                            "Incidents State Events",
                            "PASS",
                            f"Incident state events retrieved for ID {first_id}"
                        )
                    else:
                        log_result(
                            "Incidents State Events",
                            "FAIL",
                            f"State events failed with status {state_response.status_code}",
                            "high"
                        )
        else:
            log_result(
                "Incidents List",
                "FAIL",
                f"Incidents list failed with status {response.status_code}. Response: {response.text}",
                "critical"
            )
    except Exception as e:
        log_result("Incidents", "FAIL", f"Exception: {str(e)}", "critical")

def test_incident_cases():
    """Test /api/incident-cases endpoints"""
    if "safety" not in tokens:
        log_result("Incident Cases List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/incident-cases",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Incident Cases List",
                "PASS",
                f"Incident cases list returned {count} items"
            )
        else:
            log_result(
                "Incident Cases List",
                "FAIL",
                f"Incident cases list failed with status {response.status_code}. Response: {response.text}",
                "critical"
            )
    except Exception as e:
        log_result("Incident Cases", "FAIL", f"Exception: {str(e)}", "critical")

def test_trench_boxes():
    """Test /api/trench-boxes endpoints"""
    try:
        # Trench boxes are public read
        response = requests.get(
            f"{API_BASE}/trench-boxes",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Boxes List",
                "PASS",
                f"Trench boxes list returned {count} items (public read)"
            )
        else:
            log_result(
                "Trench Boxes List",
                "FAIL",
                f"Trench boxes list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Boxes", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_box_files():
    """Test /api/trench-box-files endpoints"""
    try:
        response = requests.get(
            f"{API_BASE}/trench-box-files",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Box Files List",
                "PASS",
                f"Trench box files list returned {count} items (public read)"
            )
        else:
            log_result(
                "Trench Box Files List",
                "FAIL",
                f"Trench box files list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Box Files", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_safety_dashboard():
    """Test /api/trench-safety/dashboard endpoint"""
    if "safety" not in tokens:
        log_result("Trench Safety Dashboard", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/dashboard",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_result(
                "Trench Safety Dashboard",
                "PASS",
                f"Trench safety dashboard returned data. Keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
        else:
            log_result(
                "Trench Safety Dashboard",
                "FAIL",
                f"Trench safety dashboard failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Safety Dashboard", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_safety_alerts():
    """Test /api/trench-safety/alerts endpoint"""
    if "safety" not in tokens:
        log_result("Trench Safety Alerts", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/alerts",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Safety Alerts",
                "PASS",
                f"Trench safety alerts returned {count} items"
            )
        else:
            log_result(
                "Trench Safety Alerts",
                "FAIL",
                f"Trench safety alerts failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Safety Alerts", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_safety_assets():
    """Test /api/trench-safety/assets endpoints"""
    if "safety" not in tokens:
        log_result("Trench Safety Assets List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/assets",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Safety Assets List",
                "PASS",
                f"Trench safety assets list returned {count} items"
            )
        else:
            log_result(
                "Trench Safety Assets List",
                "FAIL",
                f"Trench safety assets list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Safety Assets", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_safety_excavations():
    """Test /api/trench-safety/excavations endpoints"""
    if "safety" not in tokens:
        log_result("Trench Safety Excavations List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/excavations",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Safety Excavations List",
                "PASS",
                f"Trench safety excavations list returned {count} items"
            )
        else:
            log_result(
                "Trench Safety Excavations List",
                "FAIL",
                f"Trench safety excavations list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Safety Excavations", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_safety_inspections():
    """Test /api/trench-safety/inspections endpoints"""
    if "safety" not in tokens:
        log_result("Trench Safety Inspections List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/inspections",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Safety Inspections List",
                "PASS",
                f"Trench safety inspections list returned {count} items"
            )
        else:
            log_result(
                "Trench Safety Inspections List",
                "FAIL",
                f"Trench safety inspections list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Safety Inspections", "FAIL", f"Exception: {str(e)}", "high")

def test_trench_safety_repairs():
    """Test /api/trench-safety/repairs endpoints"""
    if "safety" not in tokens:
        log_result("Trench Safety Repairs List", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/repairs",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Trench Safety Repairs List",
                "PASS",
                f"Trench safety repairs list returned {count} items"
            )
        else:
            log_result(
                "Trench Safety Repairs List",
                "FAIL",
                f"Trench safety repairs list failed with status {response.status_code}. Response: {response.text}",
                "high"
            )
    except Exception as e:
        log_result("Trench Safety Repairs", "FAIL", f"Exception: {str(e)}", "high")

def test_negative_access():
    """Test that non-Safety tokens cannot access Safety-protected endpoints"""
    # Login as admin-only user
    success, admin_tokens = multi_portal_login("admin_only")
    if not success:
        log_result("Negative Access Test", "FAIL", "Could not login as admin-only user", "high")
        return
    
    # Try to access Safety overview with admin token
    try:
        admin_token = admin_tokens["portal_tokens"].get("admin")
        if not admin_token:
            log_result("Negative Access Test", "FAIL", "No admin token available", "high")
            return
        
        response = requests.get(
            f"{API_BASE}/safety/overview",
            headers={"X-Admin-Token": admin_token},
            timeout=10
        )
        
        if response.status_code in [401, 403]:
            log_result(
                "Negative Access - Admin to Safety",
                "PASS",
                f"Admin token correctly rejected from Safety endpoint (status {response.status_code})"
            )
        elif response.status_code == 200:
            log_result(
                "Negative Access - Admin to Safety",
                "FAIL",
                "Admin token incorrectly allowed access to Safety endpoint",
                "critical"
            )
        else:
            log_result(
                "Negative Access - Admin to Safety",
                "WARN",
                f"Unexpected status {response.status_code} for negative access test"
            )
    except Exception as e:
        log_result("Negative Access Test", "FAIL", f"Exception: {str(e)}", "high")

def test_signatures():
    """Test /api/signatures endpoint"""
    if "safety" not in tokens:
        log_result("Signatures GET", "FAIL", "No Safety token available", "critical")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/signatures",
            headers={"X-Safety-Token": tokens["safety"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            log_result(
                "Signatures GET",
                "PASS",
                f"Signatures endpoint returned {count} items"
            )
        else:
            log_result(
                "Signatures GET",
                "FAIL",
                f"Signatures endpoint failed with status {response.status_code}. Response: {response.text}",
                "medium"
            )
    except Exception as e:
        log_result("Signatures", "FAIL", f"Exception: {str(e)}", "medium")

def print_summary():
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("WP-16 WAVE 5 SAFETY CERTIFICATION - BACKEND API INSPECTION SUMMARY")
    print("="*80 + "\n")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
    pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {len(test_results['passed'])} ({pass_rate:.1f}%)")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Warnings: {len(test_results['warnings'])}\n")
    
    print("SEVERITY BREAKDOWN:")
    print(f"  Critical: {len(test_results['critical'])}")
    print(f"  High: {len(test_results['high'])}")
    print(f"  Medium: {len(test_results['medium'])}")
    print(f"  Low: {len(test_results['low'])}\n")
    
    if test_results["critical"]:
        print("CRITICAL FAILURES:")
        for result in test_results["critical"]:
            print(f"  ❌ {result['test']}: {result['details']}")
        print()
    
    if test_results["high"]:
        print("HIGH PRIORITY FAILURES:")
        for result in test_results["high"]:
            print(f"  ❌ {result['test']}: {result['details']}")
        print()
    
    if test_results["medium"]:
        print("MEDIUM PRIORITY FAILURES:")
        for result in test_results["medium"]:
            print(f"  ⚠️  {result['test']}: {result['details']}")
        print()
    
    print("="*80)
    
    # Return exit code based on critical/high failures
    if test_results["critical"] or test_results["high"]:
        return 1
    return 0

def main():
    """Main test execution"""
    print("WP-16 Wave 5 Safety Certification - Backend API Inspection")
    print("Base URL:", BASE_URL)
    print("="*80 + "\n")
    
    # Phase 1: Authentication
    print("PHASE 1: AUTHENTICATION\n")
    safety_success, safety_token = safety_login()
    if not safety_success:
        print("\n❌ CRITICAL: Safety login failed. Cannot proceed with Safety API tests.\n")
        print_summary()
        sys.exit(1)
    
    # Test Safety /me
    test_safety_me()
    
    # Phase 2: Safety Portal Core APIs
    print("\nPHASE 2: SAFETY PORTAL CORE APIs\n")
    test_safety_overview()
    test_corrective_actions()
    test_fire_extinguishers()
    test_safety_documents()
    test_training_records()
    test_safety_digest()
    
    # Phase 3: Safety Exports
    print("\nPHASE 3: SAFETY EXPORTS\n")
    test_safety_exports()
    
    # Phase 4: Safety Forms
    print("\nPHASE 4: SAFETY FORMS\n")
    test_safety_forms_login()
    test_safety_forms_check()
    
    # Phase 5: Core Safety Reporting (Inspections, Meetings, JHAs, Incidents)
    print("\nPHASE 5: CORE SAFETY REPORTING\n")
    test_inspections()
    test_meetings()
    test_jhas()
    test_incidents()
    
    # Phase 6: Incident Cases & Intelligence
    print("\nPHASE 6: INCIDENT CASES & INTELLIGENCE\n")
    test_incident_cases()
    
    # Phase 7: Trench Safety
    print("\nPHASE 7: TRENCH SAFETY\n")
    test_trench_boxes()
    test_trench_box_files()
    test_trench_safety_dashboard()
    test_trench_safety_alerts()
    test_trench_safety_assets()
    test_trench_safety_excavations()
    test_trench_safety_inspections()
    test_trench_safety_repairs()
    
    # Phase 8: Shared APIs
    print("\nPHASE 8: SHARED APIs\n")
    test_signatures()
    
    # Phase 9: Security & Permissions
    print("\nPHASE 9: SECURITY & PERMISSIONS\n")
    test_negative_access()
    
    # Print summary and exit
    exit_code = print_summary()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
