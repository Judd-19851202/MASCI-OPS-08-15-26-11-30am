#!/usr/bin/env python3
"""
Backend Release Gate Test for Project 24-06
Tests operational go-live readiness for cost codes, scheduling, daily reports, and Monday briefing
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PROJECT_NUMBER = "24-06"
COST_CODE = "ZZ-GATE-203758"
DAILY_REPORT_ID = "DR-2026-03558"

class ReleaseGateTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.directory_token = None
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "project": PROJECT_NUMBER,
            "objectives": {},
            "overall_status": "UNKNOWN"
        }
    
    def log(self, message, level="INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
    
    def authenticate(self):
        """Authenticate as Super Admin and get tokens"""
        self.log("Authenticating as Super Admin...")
        
        url = f"{self.base_url}/api/auth/multi-login"
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            self.log(f"Auth response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Auth response: {json.dumps(data, indent=2)}")
                
                # Extract tokens from response
                # session_token is the directory token
                if "session_token" in data:
                    self.directory_token = data["session_token"]
                # portal_tokens.admin is the admin token
                portal_tokens = data.get("portal_tokens", {})
                if "admin" in portal_tokens:
                    self.admin_token = portal_tokens["admin"]
                
                self.log(f"Admin token: {self.admin_token[:20] if self.admin_token else 'None'}...")
                self.log(f"Directory token: {self.directory_token[:20] if self.directory_token else 'None'}...")
                
                return True
            else:
                self.log(f"Auth failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Auth exception: {str(e)}", "ERROR")
            return False
    
    def get_headers(self):
        """Get headers with admin and directory tokens"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.admin_token:
            headers["X-Admin-Token"] = self.admin_token
        if self.directory_token:
            headers["X-Directory-Token"] = self.directory_token
        return headers
    
    def test_cost_code_assignment(self):
        """Test A: Cost code assignment + schedule canonical state for 24-06"""
        self.log("\n=== TEST A: Cost Code Assignment + Schedule State ===")
        
        result = {
            "status": "UNKNOWN",
            "details": {},
            "errors": []
        }
        
        try:
            # 1. Check cost code registry
            self.log("Checking cost code registry...")
            url = f"{self.base_url}/api/cost-codes/registry"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Cost code registry status: {response.status_code}")
            
            if response.status_code == 200:
                registry_data = response.json()
                cost_codes = registry_data.get("cost_codes", [])
                found_code = any(cc.get("code") == COST_CODE for cc in cost_codes)
                result["details"]["cost_code_in_registry"] = found_code
                self.log(f"Cost code {COST_CODE} in registry: {found_code}")
            else:
                result["errors"].append(f"Cost code registry failed: {response.status_code}")
            
            # 2. Check project cost code assignment
            self.log(f"Checking cost code assignment for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/cost-codes/projects/{PROJECT_NUMBER}"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Project cost code status: {response.status_code}")
            
            if response.status_code == 200:
                project_data = response.json()
                assigned_code = project_data.get("cost_code")
                result["details"]["assigned_cost_code"] = assigned_code
                result["details"]["cost_code_matches"] = (assigned_code == COST_CODE)
                self.log(f"Assigned cost code: {assigned_code}, matches expected: {assigned_code == COST_CODE}")
            else:
                result["errors"].append(f"Project cost code check failed: {response.status_code}")
            
            # 3. Check schedule canonical state
            self.log(f"Checking schedule state for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/cost-codes/projects/{PROJECT_NUMBER}/schedule"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Schedule state status: {response.status_code}")
            
            if response.status_code == 200:
                schedule_data = response.json()
                result["details"]["schedule_exists"] = True
                result["details"]["projected_finish"] = schedule_data.get("projected_finish_date")
                result["details"]["committed_finish"] = schedule_data.get("committed_finish_date")
                result["details"]["critical_path_count"] = schedule_data.get("critical_path_count", 0)
                self.log(f"Schedule data: {json.dumps(schedule_data, indent=2)}")
            else:
                result["errors"].append(f"Schedule state check failed: {response.status_code}")
            
            # Determine overall status
            if len(result["errors"]) == 0:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
        
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Exception: {str(e)}")
            self.log(f"Test A exception: {str(e)}", "ERROR")
        
        self.results["objectives"]["A_cost_code_schedule"] = result
        return result
    
    def test_weekly_rollover(self):
        """Test B: Weekly rollover readiness"""
        self.log("\n=== TEST B: Weekly Rollover Readiness ===")
        
        result = {
            "status": "UNKNOWN",
            "details": {},
            "errors": []
        }
        
        try:
            # Check rollover preview endpoint
            self.log(f"Checking rollover preview for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/oppc/projects/{PROJECT_NUMBER}/rollover/preview"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Rollover preview status: {response.status_code}")
            
            if response.status_code == 200:
                preview_data = response.json()
                result["details"]["preview_available"] = True
                result["details"]["preview_data"] = preview_data
                self.log(f"Rollover preview: {json.dumps(preview_data, indent=2)}")
                result["status"] = "PASS"
            else:
                result["errors"].append(f"Rollover preview failed: {response.status_code} - {response.text}")
                result["status"] = "FAIL"
        
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Exception: {str(e)}")
            self.log(f"Test B exception: {str(e)}", "ERROR")
        
        self.results["objectives"]["B_weekly_rollover"] = result
        return result
    
    def test_daily_report_actuals(self):
        """Test C: Daily report actuals propagated into project cost-code progress"""
        self.log("\n=== TEST C: Daily Report Actuals Propagation ===")
        
        result = {
            "status": "UNKNOWN",
            "details": {},
            "errors": []
        }
        
        try:
            # 1. Check if daily report exists
            self.log(f"Checking daily report {DAILY_REPORT_ID}...")
            url = f"{self.base_url}/api/daily-reports/{DAILY_REPORT_ID}"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Daily report status: {response.status_code}")
            
            if response.status_code == 200:
                report_data = response.json()
                result["details"]["daily_report_exists"] = True
                result["details"]["report_project"] = report_data.get("project_number")
                self.log(f"Daily report found for project: {report_data.get('project_number')}")
            else:
                result["errors"].append(f"Daily report check failed: {response.status_code}")
            
            # 2. Check OPPC daily actuals
            self.log(f"Checking OPPC daily actuals for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/oppc/projects/{PROJECT_NUMBER}/daily-actuals"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Daily actuals status: {response.status_code}")
            
            if response.status_code == 200:
                actuals_data = response.json()
                result["details"]["daily_actuals_available"] = True
                result["details"]["actuals_count"] = len(actuals_data.get("actuals", []))
                self.log(f"Daily actuals: {json.dumps(actuals_data, indent=2)}")
            else:
                result["errors"].append(f"Daily actuals check failed: {response.status_code}")
            
            # 3. Check cost code progress
            self.log(f"Checking cost code progress for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/cost-codes/projects/{PROJECT_NUMBER}/progress"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Cost code progress status: {response.status_code}")
            
            if response.status_code == 200:
                progress_data = response.json()
                result["details"]["progress_available"] = True
                result["details"]["progress_data"] = progress_data
                self.log(f"Cost code progress: {json.dumps(progress_data, indent=2)}")
            else:
                result["errors"].append(f"Cost code progress check failed: {response.status_code}")
            
            # Determine overall status
            if len(result["errors"]) == 0:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
        
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Exception: {str(e)}")
            self.log(f"Test C exception: {str(e)}", "ERROR")
        
        self.results["objectives"]["C_daily_report_actuals"] = result
        return result
    
    def test_monday_briefing(self):
        """Test D: Monday briefing freshness (suspected blocker)"""
        self.log("\n=== TEST D: Monday Briefing Freshness (SUSPECTED BLOCKER) ===")
        
        result = {
            "status": "UNKNOWN",
            "details": {},
            "errors": [],
            "blocker": False
        }
        
        try:
            # 1. Check current Monday briefing state
            self.log(f"Checking Monday briefing state for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/oppc/projects/{PROJECT_NUMBER}/monday-briefing"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Monday briefing GET status: {response.status_code}")
            
            if response.status_code == 200:
                briefing_data = response.json()
                result["details"]["briefing_exists"] = True
                result["details"]["briefing_status"] = briefing_data.get("status")
                result["details"]["is_frozen"] = briefing_data.get("frozen", False)
                result["details"]["last_generated"] = briefing_data.get("generated_at")
                self.log(f"Monday briefing: {json.dumps(briefing_data, indent=2)}")
                
                # Check if frozen
                if briefing_data.get("frozen"):
                    self.log("WARNING: Monday briefing is FROZEN", "WARN")
                    result["details"]["frozen_warning"] = "Briefing is frozen and may be stale"
            else:
                result["errors"].append(f"Monday briefing GET failed: {response.status_code}")
            
            # 2. Try to regenerate Monday briefing
            self.log(f"Attempting to regenerate Monday briefing for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/oppc/projects/{PROJECT_NUMBER}/monday-briefing/generate"
            response = requests.post(url, headers=self.get_headers(), json={}, timeout=30)
            self.log(f"Monday briefing generate status: {response.status_code}")
            self.log(f"Monday briefing generate response: {response.text}")
            
            if response.status_code == 200:
                result["details"]["regeneration_successful"] = True
                result["status"] = "PASS"
            elif response.status_code == 409:
                # This is the suspected blocker
                result["details"]["regeneration_blocked"] = True
                result["details"]["block_reason"] = response.text
                result["blocker"] = True
                result["status"] = "FAIL"
                result["errors"].append(f"BLOCKER: Monday briefing regeneration blocked with 409: {response.text}")
                self.log(f"BLOCKER CONFIRMED: {response.text}", "ERROR")
            else:
                result["errors"].append(f"Monday briefing generate failed: {response.status_code} - {response.text}")
                result["status"] = "FAIL"
        
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Exception: {str(e)}")
            self.log(f"Test D exception: {str(e)}", "ERROR")
        
        self.results["objectives"]["D_monday_briefing"] = result
        return result
    
    def test_project_health(self):
        """Test E: Project health / confidence freshness for 24-06"""
        self.log("\n=== TEST E: Project Health / Confidence Freshness ===")
        
        result = {
            "status": "UNKNOWN",
            "details": {},
            "errors": []
        }
        
        try:
            # 1. Check project health
            self.log(f"Checking project health for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/oppc/projects/{PROJECT_NUMBER}/health"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Project health status: {response.status_code}")
            
            if response.status_code == 200:
                health_data = response.json()
                result["details"]["health_available"] = True
                result["details"]["health_score"] = health_data.get("health_score")
                result["details"]["confidence_score"] = health_data.get("confidence_score")
                result["details"]["last_updated"] = health_data.get("last_updated")
                self.log(f"Project health: {json.dumps(health_data, indent=2)}")
            else:
                result["errors"].append(f"Project health check failed: {response.status_code}")
            
            # 2. Check production confidence score
            self.log(f"Checking production confidence for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/oppc/projects/{PROJECT_NUMBER}/confidence"
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            self.log(f"Production confidence status: {response.status_code}")
            
            if response.status_code == 200:
                confidence_data = response.json()
                result["details"]["confidence_available"] = True
                result["details"]["confidence_data"] = confidence_data
                self.log(f"Production confidence: {json.dumps(confidence_data, indent=2)}")
            else:
                result["errors"].append(f"Production confidence check failed: {response.status_code}")
            
            # Determine overall status
            if len(result["errors"]) == 0:
                result["status"] = "PASS"
            else:
                result["status"] = "FAIL"
        
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Exception: {str(e)}")
            self.log(f"Test E exception: {str(e)}", "ERROR")
        
        self.results["objectives"]["E_project_health"] = result
        return result
    
    def test_trust_spine(self):
        """Test F: Trust Spine audit trail completeness"""
        self.log("\n=== TEST F: Trust Spine Audit Trail ===")
        
        result = {
            "status": "UNKNOWN",
            "details": {},
            "errors": []
        }
        
        try:
            # Check trust spine events for project 24-06
            self.log(f"Checking trust spine events for project {PROJECT_NUMBER}...")
            url = f"{self.base_url}/api/trust-spine/events"
            params = {
                "project_number": PROJECT_NUMBER,
                "limit": 50
            }
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=30)
            self.log(f"Trust spine status: {response.status_code}")
            
            if response.status_code == 200:
                spine_data = response.json()
                events = spine_data.get("events", [])
                result["details"]["events_available"] = True
                result["details"]["event_count"] = len(events)
                
                # Check for specific event types
                event_types = [e.get("event_type") for e in events]
                result["details"]["event_types"] = list(set(event_types))
                
                # Look for expected events
                has_oppc_actuals = "oppc-daily-actuals" in event_types
                has_daily_report = "daily-report" in event_types
                
                result["details"]["has_oppc_actuals_event"] = has_oppc_actuals
                result["details"]["has_daily_report_event"] = has_daily_report
                
                self.log(f"Trust spine events: {len(events)} total")
                self.log(f"Event types: {result['details']['event_types']}")
                self.log(f"Has oppc-daily-actuals: {has_oppc_actuals}")
                self.log(f"Has daily-report: {has_daily_report}")
                
                if has_oppc_actuals and has_daily_report:
                    result["status"] = "PASS"
                else:
                    result["status"] = "PARTIAL"
                    result["errors"].append("Missing expected event types in trust spine")
            else:
                result["errors"].append(f"Trust spine check failed: {response.status_code}")
                result["status"] = "FAIL"
        
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Exception: {str(e)}")
            self.log(f"Test F exception: {str(e)}", "ERROR")
        
        self.results["objectives"]["F_trust_spine"] = result
        return result
    
    def run_all_tests(self):
        """Run all release gate tests"""
        self.log("=" * 80)
        self.log("OPERATIONAL GO-LIVE RELEASE GATE TEST - PROJECT 24-06")
        self.log("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            self.log("Authentication failed. Cannot proceed with tests.", "ERROR")
            self.results["overall_status"] = "BLOCKED"
            return self.results
        
        # Run all tests
        self.test_cost_code_assignment()
        self.test_weekly_rollover()
        self.test_daily_report_actuals()
        self.test_monday_briefing()
        self.test_project_health()
        self.test_trust_spine()
        
        # Determine overall status
        statuses = [obj["status"] for obj in self.results["objectives"].values()]
        has_blocker = any(obj.get("blocker", False) for obj in self.results["objectives"].values())
        
        if has_blocker:
            self.results["overall_status"] = "NOT READY - BLOCKER FOUND"
        elif all(s == "PASS" for s in statuses):
            self.results["overall_status"] = "RELEASE GATE READY"
        elif "FAIL" in statuses:
            self.results["overall_status"] = "NOT READY - FAILURES FOUND"
        else:
            self.results["overall_status"] = "PARTIAL - REVIEW REQUIRED"
        
        # Print summary
        self.log("\n" + "=" * 80)
        self.log("RELEASE GATE TEST SUMMARY")
        self.log("=" * 80)
        self.log(f"Overall Status: {self.results['overall_status']}")
        self.log("\nObjective Results:")
        for obj_name, obj_result in self.results["objectives"].items():
            status_icon = "✅" if obj_result["status"] == "PASS" else "❌" if obj_result["status"] == "FAIL" else "⚠️"
            blocker_flag = " [BLOCKER]" if obj_result.get("blocker") else ""
            self.log(f"  {status_icon} {obj_name}: {obj_result['status']}{blocker_flag}")
            if obj_result["errors"]:
                for error in obj_result["errors"]:
                    self.log(f"      - {error}")
        
        return self.results

if __name__ == "__main__":
    tester = ReleaseGateTest()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("/app/release_gate_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("Full results saved to: /app/release_gate_test_results.json")
    print("=" * 80)
