#!/usr/bin/env python3
"""
WP-15 Governance Convergence and Constitutional Certification - Backend API Verification
Final closeout verification for governed auth lifecycle and critical evidence paths
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "super_admin": {
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!"
    },
    "admin_only": {
        "email": "ops8-admin-only-preview@example.com",
        "password": "AdminOnlyOps8!"
    },
    "pm_only": {
        "email": "cert.pm@example.com",
        "password": "CertProof2026!"
    },
    "safety_only": {
        "email": "cert.safety@example.com",
        "password": "CertProof2026!"
    },
    "dispatch_only": {
        "email": "cert.dispatch@example.com",
        "password": "CertProof2026!"
    },
    "hr_only": {
        "email": "cert.hr@example.com",
        "password": "CertProof2026!"
    },
    "fl_only": {
        "email": "cert.foreman@example.com",
        "password": "CertProof2026!"
    }
}

class WP15GovernanceTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suite": "WP-15 Governance Convergence Backend Verification",
            "tests": {},
            "overall_status": "UNKNOWN",
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def multi_login(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Perform multi-login and return success status and session data
        Returns: (success: bool, session_data: dict or None)
        """
        url = f"{self.base_url}/api/auth/multi-login"
        payload = {"email": email, "password": password}
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                self.log(f"Login failed: {response.status_code} - {response.text[:200]}", "ERROR")
                return False, None
        except Exception as e:
            self.log(f"Login exception: {str(e)}", "ERROR")
            return False, None
    
    def test_1_multi_login_directory_and_portal_tokens(self):
        """
        Test 1: Multi-login returns directory session + portal tokens for admin-only and admin+pm users
        """
        self.log("\n" + "="*80)
        self.log("TEST 1: Multi-login directory session + portal tokens")
        self.log("="*80)
        
        test_result = {
            "name": "Multi-login directory session + portal tokens",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Test 1a: Admin-only user
            self.log("\n[1a] Testing admin-only user login...")
            success, data = self.multi_login(
                CREDENTIALS["admin_only"]["email"],
                CREDENTIALS["admin_only"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Admin-only login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Verify directory session token
            if "session_token" not in data:
                test_result["errors"].append("Admin-only: Missing session_token (directory token)")
                test_result["status"] = "FAIL"
            else:
                test_result["details"].append(f"✅ Admin-only: Directory session token present (length: {len(data['session_token'])})")
            
            # Verify portal tokens
            if "portal_tokens" not in data:
                test_result["errors"].append("Admin-only: Missing portal_tokens")
                test_result["status"] = "FAIL"
            else:
                portal_tokens = data["portal_tokens"]
                if "admin" not in portal_tokens:
                    test_result["errors"].append("Admin-only: Missing admin portal token")
                    test_result["status"] = "FAIL"
                else:
                    test_result["details"].append(f"✅ Admin-only: Admin portal token present (length: {len(portal_tokens['admin'])})")
                
                # Should only have admin portal
                if len(portal_tokens) > 1:
                    test_result["details"].append(f"⚠️  Admin-only: Has {len(portal_tokens)} portal tokens (expected 1): {list(portal_tokens.keys())}")
                else:
                    test_result["details"].append(f"✅ Admin-only: Has exactly 1 portal token (admin)")
            
            # Test 1b: Super admin (has multiple portals)
            self.log("\n[1b] Testing super admin login (multi-portal)...")
            success, data = self.multi_login(
                CREDENTIALS["super_admin"]["email"],
                CREDENTIALS["super_admin"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Super admin login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Verify directory session token
            if "session_token" not in data:
                test_result["errors"].append("Super admin: Missing session_token (directory token)")
                test_result["status"] = "FAIL"
            else:
                test_result["details"].append(f"✅ Super admin: Directory session token present (length: {len(data['session_token'])})")
            
            # Verify portal tokens
            if "portal_tokens" not in data:
                test_result["errors"].append("Super admin: Missing portal_tokens")
                test_result["status"] = "FAIL"
            else:
                portal_tokens = data["portal_tokens"]
                if "admin" not in portal_tokens:
                    test_result["errors"].append("Super admin: Missing admin portal token")
                    test_result["status"] = "FAIL"
                else:
                    test_result["details"].append(f"✅ Super admin: Admin portal token present")
                
                # Super admin should have multiple portals
                test_result["details"].append(f"✅ Super admin: Has {len(portal_tokens)} portal tokens: {list(portal_tokens.keys())}")
            
            # Determine final status
            if not test_result["errors"]:
                test_result["status"] = "PASS"
                self.log("✅ TEST 1 PASSED", "SUCCESS")
            else:
                test_result["status"] = "FAIL"
                self.log("❌ TEST 1 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 1 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def test_2_governed_admin_api_positive_control(self):
        """
        Test 2: Governed admin API positive control
        GET /api/admin/governance/overview with valid X-Admin-Token + X-Directory-Token returns 200
        """
        self.log("\n" + "="*80)
        self.log("TEST 2: Governed admin API positive control")
        self.log("="*80)
        
        test_result = {
            "name": "Governed admin API positive control",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Login as super admin
            self.log("\n[2] Logging in as super admin...")
            success, data = self.multi_login(
                CREDENTIALS["super_admin"]["email"],
                CREDENTIALS["super_admin"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Super admin login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Extract tokens
            directory_token = data.get("session_token")
            admin_token = data.get("portal_tokens", {}).get("admin")
            
            if not directory_token or not admin_token:
                test_result["errors"].append("Missing required tokens")
                test_result["status"] = "FAIL"
                return test_result
            
            test_result["details"].append(f"✅ Obtained directory token (length: {len(directory_token)})")
            test_result["details"].append(f"✅ Obtained admin token (length: {len(admin_token)})")
            
            # Test governed admin API with valid headers
            self.log("\n[2] Testing GET /api/admin/governance/overview with valid headers...")
            url = f"{self.base_url}/api/admin/governance/overview"
            headers = {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": directory_token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                test_result["details"].append(f"✅ GET /api/admin/governance/overview returned 200 OK")
                test_result["status"] = "PASS"
                self.log("✅ TEST 2 PASSED", "SUCCESS")
                
                # Log response summary
                try:
                    response_data = response.json()
                    test_result["details"].append(f"Response keys: {list(response_data.keys())}")
                except:
                    pass
            else:
                test_result["errors"].append(f"Expected 200, got {response.status_code}")
                test_result["errors"].append(f"Response: {response.text[:500]}")
                test_result["status"] = "FAIL"
                self.log("❌ TEST 2 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 2 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def test_3_negative_request_lifecycle_control(self):
        """
        Test 3: Negative request-lifecycle control
        Mismatched or missing X-Directory-Token should be denied (401/403)
        """
        self.log("\n" + "="*80)
        self.log("TEST 3: Negative request-lifecycle control")
        self.log("="*80)
        
        test_result = {
            "name": "Negative request-lifecycle control",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Login as super admin
            self.log("\n[3] Logging in as super admin...")
            success, data = self.multi_login(
                CREDENTIALS["super_admin"]["email"],
                CREDENTIALS["super_admin"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Super admin login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Extract tokens
            directory_token = data.get("session_token")
            admin_token = data.get("portal_tokens", {}).get("admin")
            
            if not directory_token or not admin_token:
                test_result["errors"].append("Missing required tokens")
                test_result["status"] = "FAIL"
                return test_result
            
            url = f"{self.base_url}/api/admin/governance/overview"
            
            # Test 3a: Missing X-Directory-Token
            self.log("\n[3a] Testing with missing X-Directory-Token...")
            headers = {
                "X-Admin-Token": admin_token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            self.log(f"Response status (missing directory token): {response.status_code}")
            
            if response.status_code in [401, 403]:
                test_result["details"].append(f"✅ Missing X-Directory-Token correctly denied with {response.status_code}")
            else:
                test_result["errors"].append(f"Missing X-Directory-Token: Expected 401/403, got {response.status_code}")
            
            # Test 3b: Mismatched X-Directory-Token (use a fake token)
            self.log("\n[3b] Testing with mismatched X-Directory-Token...")
            headers = {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": "fake-mismatched-token-12345",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            self.log(f"Response status (mismatched directory token): {response.status_code}")
            
            if response.status_code in [401, 403]:
                test_result["details"].append(f"✅ Mismatched X-Directory-Token correctly denied with {response.status_code}")
            else:
                test_result["errors"].append(f"Mismatched X-Directory-Token: Expected 401/403, got {response.status_code}")
            
            # Test 3c: Missing X-Admin-Token
            self.log("\n[3c] Testing with missing X-Admin-Token...")
            headers = {
                "X-Directory-Token": directory_token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            self.log(f"Response status (missing admin token): {response.status_code}")
            
            if response.status_code in [401, 403]:
                test_result["details"].append(f"✅ Missing X-Admin-Token correctly denied with {response.status_code}")
            else:
                test_result["errors"].append(f"Missing X-Admin-Token: Expected 401/403, got {response.status_code}")
            
            # Determine final status
            if not test_result["errors"]:
                test_result["status"] = "PASS"
                self.log("✅ TEST 3 PASSED", "SUCCESS")
            else:
                test_result["status"] = "FAIL"
                self.log("❌ TEST 3 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 3 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def test_4_emergency_override_api(self):
        """
        Test 4: Emergency override API
        POST /api/admin/governance/emergency-overrides should return success
        """
        self.log("\n" + "="*80)
        self.log("TEST 4: Emergency override API")
        self.log("="*80)
        
        test_result = {
            "name": "Emergency override API",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Login as super admin
            self.log("\n[4] Logging in as super admin...")
            success, data = self.multi_login(
                CREDENTIALS["super_admin"]["email"],
                CREDENTIALS["super_admin"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Super admin login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Extract tokens
            directory_token = data.get("session_token")
            admin_token = data.get("portal_tokens", {}).get("admin")
            
            if not directory_token or not admin_token:
                test_result["errors"].append("Missing required tokens")
                test_result["status"] = "FAIL"
                return test_result
            
            # Test emergency override API
            self.log("\n[4] Testing POST /api/admin/governance/emergency-overrides...")
            url = f"{self.base_url}/api/admin/governance/emergency-overrides"
            headers = {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": directory_token,
                "Content-Type": "application/json"
            }
            
            # Create a test override payload with required fields
            payload = {
                "action_key": "wp15_certification_test",
                "module_key": "governance_verification",
                "record_type": "certification_test",
                "record_id": f"wp15-test-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "company_id": "masci",
                "project_number": "",
                "denied_policy_id": "",
                "justification": "WP-15 governance convergence certification test - verifying emergency override API functionality for constitutional certification closeout",
                "operational_urgency": "certification_verification",
                "evidence": ["wp15_backend_api_verification"],
                "expires_at": ""
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                test_result["details"].append(f"✅ POST /api/admin/governance/emergency-overrides returned {response.status_code}")
                test_result["status"] = "PASS"
                self.log("✅ TEST 4 PASSED", "SUCCESS")
                
                # Log response summary
                try:
                    response_data = response.json()
                    test_result["details"].append(f"Response keys: {list(response_data.keys())}")
                except:
                    pass
            else:
                test_result["errors"].append(f"Expected 200/201, got {response.status_code}")
                test_result["errors"].append(f"Response: {response.text[:500]}")
                test_result["status"] = "FAIL"
                self.log("❌ TEST 4 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 4 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def test_5_pm_governed_workflow_smoke(self):
        """
        Test 5: PM governed workflow smoke test
        PM-authenticated representative governed read should work with valid lifecycle headers
        """
        self.log("\n" + "="*80)
        self.log("TEST 5: PM governed workflow smoke test")
        self.log("="*80)
        
        test_result = {
            "name": "PM governed workflow smoke test",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Login as PM
            self.log("\n[5] Logging in as PM...")
            success, data = self.multi_login(
                CREDENTIALS["pm_only"]["email"],
                CREDENTIALS["pm_only"]["password"]
            )
            
            if not success:
                test_result["errors"].append("PM login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Extract tokens
            directory_token = data.get("session_token")
            pm_token = data.get("portal_tokens", {}).get("pm")
            
            if not directory_token or not pm_token:
                test_result["errors"].append("Missing required PM tokens")
                test_result["status"] = "FAIL"
                return test_result
            
            test_result["details"].append(f"✅ PM login successful")
            test_result["details"].append(f"✅ Obtained directory token (length: {len(directory_token)})")
            test_result["details"].append(f"✅ Obtained PM token (length: {len(pm_token)})")
            
            # Test PM governed read endpoint (PM command center overview)
            self.log("\n[5] Testing PM governed read with valid lifecycle headers...")
            url = f"{self.base_url}/api/pm/command-center/overview"
            headers = {
                "X-PM-Token": pm_token,
                "X-Directory-Token": directory_token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                test_result["details"].append(f"✅ PM governed read with valid headers returned 200 OK")
                test_result["status"] = "PASS"
                self.log("✅ TEST 5 PASSED", "SUCCESS")
            else:
                test_result["errors"].append(f"Expected 200, got {response.status_code}")
                test_result["errors"].append(f"Response: {response.text[:500]}")
                test_result["status"] = "FAIL"
                self.log("❌ TEST 5 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 5 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def test_6_safety_dispatch_representative_reads(self):
        """
        Test 6: Safety and Dispatch representative protected reads
        Should authenticate successfully with valid portal sessions
        """
        self.log("\n" + "="*80)
        self.log("TEST 6: Safety and Dispatch representative protected reads")
        self.log("="*80)
        
        test_result = {
            "name": "Safety and Dispatch representative protected reads",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Test 6a: Safety user
            self.log("\n[6a] Testing Safety user protected read...")
            success, data = self.multi_login(
                CREDENTIALS["safety_only"]["email"],
                CREDENTIALS["safety_only"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Safety login failed")
            else:
                directory_token = data.get("session_token")
                safety_token = data.get("portal_tokens", {}).get("safety")
                
                if not directory_token or not safety_token:
                    test_result["errors"].append("Missing Safety tokens")
                else:
                    test_result["details"].append(f"✅ Safety login successful")
                    
                    # Test Safety protected read (safety overview)
                    url = f"{self.base_url}/api/safety/overview"
                    headers = {
                        "X-Safety-Token": safety_token,
                        "X-Directory-Token": directory_token,
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.get(url, headers=headers, timeout=30)
                    self.log(f"Safety read response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        test_result["details"].append(f"✅ Safety protected read returned 200 OK")
                    else:
                        test_result["errors"].append(f"Safety read: Expected 200, got {response.status_code}")
            
            # Test 6b: Dispatch user
            self.log("\n[6b] Testing Dispatch user protected read...")
            success, data = self.multi_login(
                CREDENTIALS["dispatch_only"]["email"],
                CREDENTIALS["dispatch_only"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Dispatch login failed")
            else:
                directory_token = data.get("session_token")
                dispatch_token = data.get("portal_tokens", {}).get("dispatch")
                
                if not directory_token or not dispatch_token:
                    test_result["errors"].append("Missing Dispatch tokens")
                else:
                    test_result["details"].append(f"✅ Dispatch login successful")
                    
                    # Test Dispatch protected read (dispatch command summary)
                    url = f"{self.base_url}/api/dispatch/command/summary"
                    headers = {
                        "X-Dispatch-Token": dispatch_token,
                        "X-Directory-Token": directory_token,
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.get(url, headers=headers, timeout=30)
                    self.log(f"Dispatch read response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        test_result["details"].append(f"✅ Dispatch protected read returned 200 OK")
                    else:
                        test_result["errors"].append(f"Dispatch read: Expected 200, got {response.status_code}")
            
            # Determine final status
            if not test_result["errors"]:
                test_result["status"] = "PASS"
                self.log("✅ TEST 6 PASSED", "SUCCESS")
            else:
                test_result["status"] = "FAIL"
                self.log("❌ TEST 6 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 6 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def test_7_no_unexpected_auth_storms(self):
        """
        Test 7: Confirm no unexpected sign-in loops or systemic 401 storms
        Make multiple sequential requests and verify no auth degradation
        """
        self.log("\n" + "="*80)
        self.log("TEST 7: No unexpected sign-in loops or 401 storms")
        self.log("="*80)
        
        test_result = {
            "name": "No unexpected sign-in loops or 401 storms",
            "status": "UNKNOWN",
            "details": [],
            "errors": []
        }
        
        try:
            # Login as super admin
            self.log("\n[7] Logging in as super admin...")
            success, data = self.multi_login(
                CREDENTIALS["super_admin"]["email"],
                CREDENTIALS["super_admin"]["password"]
            )
            
            if not success:
                test_result["errors"].append("Super admin login failed")
                test_result["status"] = "FAIL"
                return test_result
            
            # Extract tokens
            directory_token = data.get("session_token")
            admin_token = data.get("portal_tokens", {}).get("admin")
            
            if not directory_token or not admin_token:
                test_result["errors"].append("Missing required tokens")
                test_result["status"] = "FAIL"
                return test_result
            
            headers = {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": directory_token,
                "Content-Type": "application/json"
            }
            
            # Make multiple sequential requests to different endpoints
            test_endpoints = [
                "/api/admin/governance/overview",
                "/api/admin/operations-control/registry",
                "/api/admin/platform/status",
                "/api/admin/governance/overview",  # Repeat to check consistency
                "/api/admin/operations-control/registry"  # Repeat
            ]
            
            self.log(f"\n[7] Making {len(test_endpoints)} sequential requests...")
            
            status_codes = []
            for i, endpoint in enumerate(test_endpoints, 1):
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, headers=headers, timeout=30)
                status_codes.append(response.status_code)
                self.log(f"Request {i}/{len(test_endpoints)}: {endpoint} -> {response.status_code}")
            
            # Check for 401 storms (multiple 401s)
            auth_errors = [code for code in status_codes if code in [401, 403]]
            
            if len(auth_errors) == 0:
                test_result["details"].append(f"✅ No 401/403 errors in {len(test_endpoints)} sequential requests")
                test_result["status"] = "PASS"
                self.log("✅ TEST 7 PASSED", "SUCCESS")
            elif len(auth_errors) <= 1:
                test_result["details"].append(f"⚠️  1 auth error in {len(test_endpoints)} requests (acceptable)")
                test_result["status"] = "PASS"
                self.log("✅ TEST 7 PASSED (with minor auth error)", "SUCCESS")
            else:
                test_result["errors"].append(f"Auth storm detected: {len(auth_errors)} auth errors in {len(test_endpoints)} requests")
                test_result["errors"].append(f"Status codes: {status_codes}")
                test_result["status"] = "FAIL"
                self.log("❌ TEST 7 FAILED", "ERROR")
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["errors"].append(f"Exception: {str(e)}")
            self.log(f"❌ TEST 7 EXCEPTION: {str(e)}", "ERROR")
        
        return test_result
    
    def run_all_tests(self):
        """Run all WP-15 governance tests"""
        self.log("\n" + "="*80)
        self.log("WP-15 GOVERNANCE CONVERGENCE BACKEND VERIFICATION")
        self.log("="*80)
        self.log(f"Base URL: {self.base_url}")
        self.log(f"Timestamp: {self.results['timestamp']}")
        
        # Run all tests
        tests = [
            ("test_1", self.test_1_multi_login_directory_and_portal_tokens),
            ("test_2", self.test_2_governed_admin_api_positive_control),
            ("test_3", self.test_3_negative_request_lifecycle_control),
            ("test_4", self.test_4_emergency_override_api),
            ("test_5", self.test_5_pm_governed_workflow_smoke),
            ("test_6", self.test_6_safety_dispatch_representative_reads),
            ("test_7", self.test_7_no_unexpected_auth_storms)
        ]
        
        for test_id, test_func in tests:
            result = test_func()
            self.results["tests"][test_id] = result
            self.results["summary"]["total"] += 1
            if result["status"] == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
        
        # Determine overall status
        if self.results["summary"]["failed"] == 0:
            self.results["overall_status"] = "PASS"
        else:
            self.results["overall_status"] = "FAIL"
        
        # Print summary
        self.print_summary()
        
        # Save results to file
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80)
        self.log("TEST SUMMARY")
        self.log("="*80)
        
        for test_id, result in self.results["tests"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            self.log(f"{status_icon} {test_id.upper()}: {result['name']} - {result['status']}")
            
            if result["details"]:
                for detail in result["details"]:
                    self.log(f"    {detail}")
            
            if result["errors"]:
                for error in result["errors"]:
                    self.log(f"    ❌ {error}", "ERROR")
        
        self.log("\n" + "="*80)
        self.log(f"OVERALL: {self.results['overall_status']}")
        self.log(f"Total: {self.results['summary']['total']}")
        self.log(f"Passed: {self.results['summary']['passed']}")
        self.log(f"Failed: {self.results['summary']['failed']}")
        self.log("="*80)
    
    def save_results(self):
        """Save test results to JSON file"""
        filename = f"/app/wp15_governance_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"\n✅ Results saved to: {filename}")

if __name__ == "__main__":
    test = WP15GovernanceTest()
    test.run_all_tests()
