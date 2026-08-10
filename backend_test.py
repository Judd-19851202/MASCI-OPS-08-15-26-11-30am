#!/usr/bin/env python3
"""
PRE-C10 Proof-Closure Batch Backend QA
Testing MASCI preview backend endpoints for PRE-C10 proof-closure batch.
"""

import requests
import json
from typing import Dict, Any, Optional, List

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.pm_token = None
        self.directory_token = None
        self.results = []
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin and get token."""
        print("\n" + "="*80)
        print("ADMIN AUTHENTICATION")
        print("="*80)
        
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/multi-login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("portal_tokens", {}).get("admin")
                self.directory_token = data.get("session_token")
                if self.admin_token:
                    print(f"✅ Admin authentication successful")
                    print(f"   Admin token: {self.admin_token[:20]}...")
                    if self.directory_token:
                        print(f"   Directory token: {self.directory_token[:20]}...")
                    return True
                else:
                    print(f"❌ Admin authentication failed: No admin token in response")
                    return False
            else:
                print(f"❌ Admin authentication failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Admin authentication error: {str(e)}")
            return False
    
    def authenticate_pm(self) -> bool:
        """Authenticate as PM and get token."""
        print("\n" + "="*80)
        print("PM AUTHENTICATION")
        print("="*80)
        
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/multi-login",
                json={
                    "email": PM_EMAIL,
                    "password": PM_PASSWORD
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.pm_token = data.get("portal_tokens", {}).get("pm")
                if self.pm_token:
                    print(f"✅ PM authentication successful")
                    print(f"   PM token: {self.pm_token[:20]}...")
                    return True
                else:
                    print(f"❌ PM authentication failed: No PM token in response")
                    return False
            else:
                print(f"❌ PM authentication failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ PM authentication error: {str(e)}")
            return False
    
    def test_endpoint(self, name: str, path: str, expected_status: int = 200, 
                     use_pm_token: bool = False, check_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Test a single endpoint."""
        full_url = f"{BASE_URL}{path}"
        
        try:
            # Build headers based on authentication type
            headers = {}
            if use_pm_token and self.pm_token:
                headers["X-PM-Token"] = self.pm_token
            elif self.admin_token:
                headers["X-Admin-Token"] = self.admin_token
                if self.directory_token:
                    headers["X-Directory-Token"] = self.directory_token
            
            response = self.session.get(full_url, headers=headers, timeout=30)
            
            result = {
                "name": name,
                "path": path,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "passed": response.status_code == expected_status,
                "response_size": len(response.content),
                "error": None,
                "data_sample": None,
                "auth_type": "PM" if use_pm_token else "Admin"
            }
            
            # Try to parse JSON response
            try:
                data = response.json()
                result["data_sample"] = self._get_data_sample(data)
                
                # Check for specific fields if requested
                if check_fields and response.status_code == 200:
                    missing_fields = [f for f in check_fields if f not in data]
                    if missing_fields:
                        result["passed"] = False
                        result["error"] = f"Missing fields: {missing_fields}"
                        
            except Exception:
                if response.status_code == 200:
                    result["data_sample"] = response.text[:200]
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                "name": name,
                "path": path,
                "status_code": None,
                "expected_status": expected_status,
                "passed": False,
                "response_size": 0,
                "error": str(e),
                "data_sample": None,
                "auth_type": "PM" if use_pm_token else "Admin"
            }
            self.results.append(result)
            return result
    
    def _get_data_sample(self, data: Any) -> str:
        """Get a sample of the response data for display."""
        if isinstance(data, dict):
            keys = list(data.keys())[:5]
            sample = {k: data[k] for k in keys if k in data}
            return json.dumps(sample, indent=2)[:300]
        elif isinstance(data, list):
            return f"Array with {len(data)} items"
        else:
            return str(data)[:200]
    
    def print_result(self, result: Dict[str, Any]):
        """Print a single test result."""
        status_icon = "✅" if result["passed"] else "❌"
        auth_label = f"[{result.get('auth_type', 'Unknown')}]"
        print(f"\n{status_icon} {result['name']} {auth_label}")
        print(f"   Path: {result['path']}")
        print(f"   Status: {result['status_code']} (expected: {result['expected_status']})")
        
        if result["error"]:
            print(f"   Error: {result['error']}")
        elif result["data_sample"]:
            print(f"   Response sample: {result['data_sample'][:150]}...")
    
    def run_kpi_tests(self):
        """Test KPI row source/runtime parity checks."""
        print("\n" + "="*80)
        print("SCOPE 1: KPI ROW SOURCE/RUNTIME PARITY CHECKS")
        print("="*80)
        
        tests = [
            ("Admin Governance Summary", "/admin/governance/summary", False),
            ("Cluster Capacity", "/cluster/capacity", False),
            ("Cluster Capacity History", "/cluster/capacity/history?days=30", False),
            ("HR Employee Requests", "/hr/employee-requests?status=pending&limit=1000", False),
            ("Field Leadership Time-Off Stats", "/field-leadership/time-off/stats", False),
            ("Operations Expirations Summary", "/operations/expirations/summary", False),
        ]
        
        for name, path, use_pm in tests:
            result = self.test_endpoint(name, path, use_pm_token=use_pm)
            self.print_result(result)
    
    def run_proof_chain_tests(self):
        """Test C1-C9 proof chain availability."""
        print("\n" + "="*80)
        print("SCOPE 2: C1-C9 PROOF CHAIN AVAILABILITY")
        print("="*80)
        
        project = "ZZ-RUNTIME-CERT-2026"
        tests = [
            ("PM Schedule Overview", f"/pm/project-controls/projects/{project}/schedule/overview", True),
            ("PM Schedule Lookahead", f"/pm/project-controls/projects/{project}/schedule/lookahead", True),
            ("PM Daily Work Plan", f"/pm/project-controls/projects/{project}/schedule/daily-work-plan?work_date=2026-08-08", True),
            ("PM Forecasting Workspace", f"/pm/project-controls/projects/{project}/forecasting/workspace", True),
            ("Admin Earned Value", f"/admin/governance/project-controls/projects/{project}/earned-value", False),
            ("Admin Portfolio Intelligence", "/admin/governance/project-controls/portfolio-intelligence", False),
        ]
        
        for name, path, use_pm in tests:
            result = self.test_endpoint(name, path, use_pm_token=use_pm)
            self.print_result(result)
    
    def run_production_cert_test(self):
        """Test production certification blocked-reason repair."""
        print("\n" + "="*80)
        print("SCOPE 3: PRODUCTION CERTIFICATION BLOCKED-REASON REPAIR")
        print("="*80)
        
        result = self.test_endpoint(
            "Production Certification",
            "/admin/production-certification",
            use_pm_token=False
        )
        self.print_result(result)
        
        # Additional validation for production certification
        if result["passed"] and result["status_code"] == 200:
            try:
                response = self.session.get(
                    f"{BASE_URL}/admin/production-certification",
                    headers={
                        "X-Admin-Token": self.admin_token,
                        "X-Directory-Token": self.directory_token
                    } if self.directory_token else {"X-Admin-Token": self.admin_token},
                    timeout=30
                )
                data = response.json()
                
                print("\n   📊 Production Certification Details:")
                if isinstance(data, dict):
                    # Check for stable counters/schema
                    if "overall_status" in data:
                        print(f"      Overall Status: {data.get('overall_status')}")
                    if "counters" in data:
                        counters = data.get("counters", {})
                        print(f"      Counters: verified={counters.get('verified')}, failed={counters.get('failed')}, blocked={counters.get('blocked')}")
                    if "workflows" in data:
                        workflows = data.get("workflows", [])
                        print(f"      Total Workflows: {len(workflows)}")
                        
                        # Check for blocked workflows with reason/remediation
                        blocked = [w for w in workflows if w.get("status") == "BLOCKED"]
                        if blocked:
                            print(f"      Blocked Workflows: {len(blocked)}")
                            for w in blocked[:3]:  # Show first 3
                                name = w.get("name", "Unknown")
                                reason = w.get("blocked_reason", "N/A")
                                remediation = w.get("remediation", "N/A")
                                print(f"         - {name}")
                                print(f"           Reason: {reason}")
                                if remediation != "N/A":
                                    print(f"           Remediation: {remediation[:80]}...")
                        else:
                            print(f"      ✅ No blocked workflows (all workflows passing)")
                else:
                    print(f"      Response type: {type(data)}")
                    
            except Exception as e:
                print(f"   ⚠️  Could not parse production certification details: {str(e)}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for r in self.results:
                if not r["passed"]:
                    print(f"   - {r['name']}: {r['path']}")
                    print(f"     Status: {r['status_code']} (expected: {r['expected_status']})")
                    if r["error"]:
                        print(f"     Error: {r['error']}")
        
        print("\n" + "="*80)
        print("SCOPE-BY-SCOPE RESULTS")
        print("="*80)
        
        # Scope 1: KPI endpoints (first 6)
        scope1_results = self.results[:6]
        scope1_passed = sum(1 for r in scope1_results if r["passed"])
        scope1_status = "✅ PASS" if scope1_passed == len(scope1_results) else "❌ FAIL"
        print(f"\n1. KPI Row Source/Runtime Parity Checks: {scope1_passed}/{len(scope1_results)} {scope1_status}")
        
        # Scope 2: Proof chain endpoints (next 6)
        scope2_results = self.results[6:12]
        scope2_passed = sum(1 for r in scope2_results if r["passed"])
        scope2_status = "✅ PASS" if scope2_passed == len(scope2_results) else "❌ FAIL"
        print(f"2. C1-C9 Proof Chain Availability: {scope2_passed}/{len(scope2_results)} {scope2_status}")
        
        # Scope 3: Production cert (last 1)
        if len(self.results) > 12:
            scope3_results = self.results[12:]
            scope3_passed = sum(1 for r in scope3_results if r["passed"])
            scope3_status = "✅ PASS" if scope3_passed == len(scope3_results) else "❌ FAIL"
            print(f"3. Production Certification: {scope3_passed}/{len(scope3_results)} {scope3_status}")
        
        return passed == total

def main():
    """Main test execution."""
    print("="*80)
    print("PRE-C10 PROOF-CLOSURE BATCH BACKEND QA")
    print("Preview Environment: https://masci-audit-hub.preview.emergentagent.com")
    print("="*80)
    
    tester = BackendTester()
    
    # Step 1: Authenticate as Admin
    if not tester.authenticate_admin():
        print("\n❌ CRITICAL: Admin authentication failed. Cannot proceed with admin tests.")
        return False
    
    # Step 2: Authenticate as PM
    if not tester.authenticate_pm():
        print("\n⚠️  WARNING: PM authentication failed. PM endpoints will be skipped.")
    
    # Step 3: Run KPI tests
    tester.run_kpi_tests()
    
    # Step 4: Run proof chain tests
    tester.run_proof_chain_tests()
    
    # Step 5: Run production cert test
    tester.run_production_cert_test()
    
    # Step 6: Print summary
    all_passed = tester.print_summary()
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
