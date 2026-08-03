#!/usr/bin/env python3
"""
WP-16 Wave 6 Backend API Inspection
Dispatch & Transportation backend/API verification

Base URL: https://masci-audit-hub.preview.emergentagent.com
Authoritative inventory: /app/memory/WP16_WAVE6_INVENTORY_AND_RECONCILIATION.md
Credentials: /app/memory/test_credentials.md
"""

import requests
import json
import sys
from typing import Dict, Any, List, Optional, Tuple

BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
DISPATCH_EMAIL = "cert.dispatch@example.com"
DISPATCH_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

class Wave6Inspector:
    def __init__(self):
        self.dispatch_token = None
        self.admin_token = None
        self.directory_token = None
        self.findings = []
        self.live_fixtures = {}
        self.defects = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log inspection messages"""
        prefix = {
            "INFO": "ℹ️",
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️",
            "FIXTURE": "🔑"
        }.get(level, "•")
        print(f"{prefix} {message}")
        
    def record_defect(self, defect_id: str, severity: str, description: str, evidence: str):
        """Record a verified defect"""
        self.defects.append({
            "id": defect_id,
            "severity": severity,
            "description": description,
            "evidence": evidence
        })
        self.log(f"DEFECT {defect_id} ({severity}): {description}", "FAIL")
        
    def record_fixture(self, fixture_type: str, value: Any):
        """Record live fixture IDs for frontend inspection"""
        self.live_fixtures[fixture_type] = value
        self.log(f"Found {fixture_type}: {value}", "FIXTURE")
        
    def login_dispatch(self) -> bool:
        """Login as dispatch user"""
        self.log("Logging in as Dispatch user...")
        try:
            response = requests.post(
                f"{API_BASE}/dispatch/login",
                json={"email": DISPATCH_EMAIL, "password": DISPATCH_PASSWORD},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.dispatch_token = data.get("token")
                self.log(f"Dispatch login successful", "PASS")
                return True
            else:
                self.log(f"Dispatch login failed: {response.status_code} - {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"Dispatch login error: {e}", "FAIL")
            return False
            
    def login_admin(self) -> bool:
        """Login as admin user via multi-login"""
        self.log("Logging in as Admin user...")
        try:
            response = requests.post(
                f"{API_BASE}/auth/multi-login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("portal_tokens", {}).get("admin")
                self.directory_token = data.get("session_token")
                self.log(f"Admin login successful", "PASS")
                return True
            else:
                self.log(f"Admin login failed: {response.status_code} - {response.text}", "FAIL")
                return False
        except Exception as e:
            self.log(f"Admin login error: {e}", "FAIL")
            return False
            
    def get_dispatch_headers(self) -> Dict[str, str]:
        """Get headers for dispatch API calls"""
        return {
            "X-Dispatch-Token": self.dispatch_token,
            "Content-Type": "application/json"
        }
        
    def get_admin_headers(self) -> Dict[str, str]:
        """Get headers for admin API calls"""
        return {
            "X-Admin-Token": self.admin_token,
            "X-Directory-Token": self.directory_token,
            "Content-Type": "application/json"
        }
        
    def get_mixed_headers(self) -> Dict[str, str]:
        """Get headers for mixed dispatch/admin API calls"""
        return {
            "X-Dispatch-Token": self.dispatch_token,
            "X-Admin-Token": self.admin_token,
            "X-Directory-Token": self.directory_token,
            "Content-Type": "application/json"
        }
        
    def test_api(self, wave_id: str, method: str, endpoint: str, headers: Dict[str, str], 
                 expected_status: int = 200, data: Optional[Dict] = None, 
                 description: str = "") -> Tuple[bool, Any]:
        """Test an API endpoint"""
        url = f"{API_BASE}{endpoint}"
        self.log(f"Testing {wave_id}: {method} {endpoint} - {description}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=10)
            else:
                self.log(f"Unsupported method: {method}", "FAIL")
                return False, None
                
            if response.status_code == expected_status:
                self.log(f"{wave_id} API returned {response.status_code} as expected", "PASS")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"{wave_id} API returned {response.status_code}, expected {expected_status}", "FAIL")
                self.log(f"Response: {response.text[:500]}", "FAIL")
                return False, None
                
        except Exception as e:
            self.log(f"{wave_id} API error: {e}", "FAIL")
            return False, None
            
    def inspect_w6_001_dispatch_board(self):
        """W6-001: Dispatch Board - assignments, state-events, exports"""
        self.log("\n=== W6-001: Dispatch Board ===")
        
        # Test board endpoint
        success, data = self.test_api(
            "W6-001",
            "GET",
            "/dispatch/assignments/board",
            self.get_dispatch_headers(),
            description="Dispatch board view"
        )
        
        if success and data:
            assignments = data.get("assignments", [])
            if assignments:
                assignment_id = assignments[0].get("id")
                if assignment_id:
                    self.record_fixture("assignment_id", assignment_id)
                    
        # Test assignments list
        success, data = self.test_api(
            "W6-001",
            "GET",
            "/dispatch/assignments",
            self.get_dispatch_headers(),
            description="Assignments list"
        )
        
        # Test state events
        success, data = self.test_api(
            "W6-001",
            "GET",
            "/dispatch/state-events",
            self.get_dispatch_headers(),
            description="State events"
        )
        
        # Test CSV exports
        for export_type in ["assignments", "state-events", "haul-cycles"]:
            success, data = self.test_api(
                "W6-001",
                "GET",
                f"/dispatch/exports/{export_type}.csv",
                self.get_dispatch_headers(),
                description=f"CSV export: {export_type}"
            )
            
    def inspect_w6_002_command_center(self):
        """W6-002: Dispatch Command Center - 7-tab operational command surface"""
        self.log("\n=== W6-002: Dispatch Command Center ===")
        
        # Test command summary
        success, data = self.test_api(
            "W6-002",
            "GET",
            "/dispatch/command/summary",
            self.get_dispatch_headers(),
            description="Command center summary"
        )
        
        # Test fleet tab
        success, data = self.test_api(
            "W6-002",
            "GET",
            "/dispatch/command/fleet",
            self.get_dispatch_headers(),
            description="Command center fleet"
        )
        
        # Test drivers tab
        success, data = self.test_api(
            "W6-002",
            "GET",
            "/dispatch/command/drivers",
            self.get_dispatch_headers(),
            description="Command center drivers"
        )
        
        # Test jobs tab
        success, data = self.test_api(
            "W6-002",
            "GET",
            "/dispatch/command/jobs",
            self.get_dispatch_headers(),
            description="Command center jobs"
        )
        
        # Test haul tab
        success, data = self.test_api(
            "W6-002",
            "GET",
            "/dispatch/command/haul",
            self.get_dispatch_headers(),
            description="Command center haul"
        )
        
        # Test broadcasts
        success, data = self.test_api(
            "W6-002",
            "GET",
            "/dispatch/command/broadcasts",
            self.get_dispatch_headers(),
            description="SMS broadcasts"
        )
        
    def inspect_w6_003_fleet_visibility(self):
        """W6-003: Dispatch Fleet Visibility - verify WP16-DEF-011 degradation"""
        self.log("\n=== W6-003: Dispatch Fleet Visibility ===")
        
        # Test fleet visibility endpoint
        success, data = self.test_api(
            "W6-003",
            "GET",
            "/api/fleet/visibility",
            self.get_dispatch_headers(),
            description="Fleet visibility main endpoint"
        )
        
        if not success:
            self.record_defect(
                "WP16-W6-003-001",
                "P1",
                "Fleet visibility endpoint failed",
                f"GET /api/fleet/visibility returned non-200 status with dispatch token"
            )
            
        # Test MaintainX integration (WP16-DEF-011 reference)
        success, data = self.test_api(
            "W6-003",
            "GET",
            "/api/integrations/maintainx/defect-coverage",
            self.get_dispatch_headers(),
            description="MaintainX defect coverage (WP16-DEF-011 check)"
        )
        
        if not success:
            self.log("⚠️  WP16-DEF-011: MaintainX defect coverage endpoint failed - prior evidence may still be valid", "WARN")
            
    def inspect_w6_004_operations_map(self):
        """W6-004: Dispatch Operations Map"""
        self.log("\n=== W6-004: Dispatch Operations Map ===")
        
        # Test operations map endpoint
        success, data = self.test_api(
            "W6-004",
            "GET",
            "/api/operations-map",
            self.get_dispatch_headers(),
            description="Operations map data"
        )
        
        # Test Motive posture
        success, data = self.test_api(
            "W6-004",
            "GET",
            "/api/dispatch/motive-posture",
            self.get_dispatch_headers(),
            description="Motive GPS posture"
        )
        
    def inspect_w6_005_haul_ledger(self):
        """W6-005: Dispatch Haul Ledger"""
        self.log("\n=== W6-005: Dispatch Haul Ledger ===")
        
        success, data = self.test_api(
            "W6-005",
            "GET",
            "/dispatch/haul-ledger",
            self.get_dispatch_headers(),
            description="Haul ledger view"
        )
        
    def inspect_w6_006_driver_qualification(self):
        """W6-006: Dispatch Driver Qualification"""
        self.log("\n=== W6-006: Dispatch Driver Qualification ===")
        
        success, data = self.test_api(
            "W6-006",
            "GET",
            "/dispatch/driver-qualification",
            self.get_dispatch_headers(),
            description="Driver qualification dashboard"
        )
        
    def inspect_w6_007_driver_profile(self):
        """W6-007: Dispatch Driver Command Profile (hidden detail route)"""
        self.log("\n=== W6-007: Dispatch Driver Command Profile ===")
        
        # First, try to get a driver key from command center drivers
        success, data = self.test_api(
            "W6-007",
            "GET",
            "/dispatch/command/drivers",
            self.get_dispatch_headers(),
            description="Get drivers list for fixture"
        )
        
        driver_key = None
        if success and data:
            drivers = data.get("drivers", [])
            if drivers:
                driver_key = drivers[0].get("driver_key") or drivers[0].get("driverKey")
                if driver_key:
                    self.record_fixture("driver_key", driver_key)
                    
                    # Test driver profile with live key
                    success, profile_data = self.test_api(
                        "W6-007",
                        "GET",
                        f"/api/operations/drivers/{driver_key}/profile",
                        self.get_dispatch_headers(),
                        description=f"Driver profile for {driver_key}"
                    )
                    
        if not driver_key:
            self.log("⚠️  No driver key found for W6-007 detail route testing", "WARN")
            
    def inspect_w6_008_transportation_wrapper(self):
        """W6-008: Transportation Operations Wrapper (mixed admin/dispatch)"""
        self.log("\n=== W6-008: Transportation Operations Wrapper ===")
        
        # Test dashboard (mission control)
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/dashboard",
            self.get_admin_headers(),
            description="Transportation dashboard (admin)"
        )
        
        # Test with dispatch token
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/dashboard",
            self.get_dispatch_headers(),
            expected_status=401,
            description="Transportation dashboard (dispatch - should fail)"
        )
        
        # Test carriers list
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/carriers",
            self.get_admin_headers(),
            description="Carriers list"
        )
        
        if success and data:
            carriers = data.get("carriers", [])
            if carriers:
                carrier_id = carriers[0].get("id")
                if carrier_id:
                    self.record_fixture("carrier_id", carrier_id)
                    
        # Test drivers list
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/persons",
            self.get_admin_headers(),
            description="Drivers/persons list"
        )
        
        if success and data:
            persons = data.get("persons", [])
            if persons:
                person_id = persons[0].get("id")
                if person_id:
                    self.record_fixture("person_id", person_id)
                    
        # Test trucks list
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/trucks",
            self.get_admin_headers(),
            description="Trucks list"
        )
        
        if success and data:
            trucks = data.get("trucks", [])
            if trucks:
                truck_id = trucks[0].get("id")
                if truck_id:
                    self.record_fixture("truck_id", truck_id)
                    
        # Test compliance dashboard
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/documents/queue",
            self.get_admin_headers(),
            description="Compliance documents queue"
        )
        
        # Test orientation dashboard
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/orientation/dashboard",
            self.get_admin_headers(),
            description="Orientation dashboard"
        )
        
        # Test orientation modules
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/orientation/modules",
            self.get_admin_headers(),
            description="Orientation modules"
        )
        
        # Test academy modules
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/academy/modules",
            self.get_admin_headers(),
            description="Academy modules"
        )
        
        # Test intelligence dashboard
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/intelligence/dashboard",
            self.get_admin_headers(),
            description="Intelligence dashboard"
        )
        
        # Test automation health
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/automation/health",
            self.get_admin_headers(),
            description="Automation health"
        )
        
        # Test audit timeline
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/audit-timeline",
            self.get_admin_headers(),
            description="Audit timeline"
        )
        
        # Test rate schedules
        success, data = self.test_api(
            "W6-008",
            "GET",
            "/admin/transportation/rate-schedules",
            self.get_admin_headers(),
            description="Rate schedules"
        )
        
    def inspect_w6_009_external_invite(self):
        """W6-009: External Carrier Invite (public tokenized)"""
        self.log("\n=== W6-009: External Carrier Invite ===")
        
        # First, try to create an invite to get a token
        success, data = self.test_api(
            "W6-009",
            "POST",
            "/admin/transportation/invites",
            self.get_admin_headers(),
            data={
                "carrier_name": "Test Carrier W6-009",
                "contact_email": "test-w6-009@example.com",
                "contact_name": "Test Contact"
            },
            description="Create invite to get token"
        )
        
        invite_token = None
        if success and data:
            invite_token = data.get("token") or data.get("invite_token")
            if invite_token:
                self.record_fixture("invite_token", invite_token)
                
                # Test public invite endpoint
                success, invite_data = self.test_api(
                    "W6-009",
                    "GET",
                    f"/transportation/invite/{invite_token}",
                    {},  # No auth headers for public endpoint
                    description=f"Public invite view for token {invite_token}"
                )
                
                # Test orientation modules for invite
                success, modules_data = self.test_api(
                    "W6-009",
                    "GET",
                    f"/transportation/invite/{invite_token}/orientation/modules",
                    {},
                    description="Orientation modules for invite"
                )
                
        if not invite_token:
            self.log("⚠️  Could not create invite token for W6-009 testing", "WARN")
            
    def inspect_w6_010_certificate_verify(self):
        """W6-010: Transportation Certificate Verify (public tokenized)"""
        self.log("\n=== W6-010: Transportation Certificate Verify ===")
        
        # First, try to get a certificate number from orientation certificates
        success, data = self.test_api(
            "W6-010",
            "GET",
            "/admin/transportation/orientation/certificates",
            self.get_admin_headers(),
            description="Get certificates list for fixture"
        )
        
        cert_number = None
        if success and data:
            certificates = data.get("certificates", [])
            if certificates:
                cert_number = certificates[0].get("certificate_number") or certificates[0].get("cnum")
                if cert_number:
                    self.record_fixture("certificate_number", cert_number)
                    
                    # Test public certificate verification
                    success, cert_data = self.test_api(
                        "W6-010",
                        "GET",
                        f"/transportation/orientation/certificates/verify/{cert_number}",
                        {},  # No auth headers for public endpoint
                        description=f"Public certificate verify for {cert_number}"
                    )
                    
        if not cert_number:
            self.log("⚠️  No certificate number found for W6-010 testing", "WARN")
            
    def test_permission_boundaries(self):
        """Test permission boundaries between dispatch and admin"""
        self.log("\n=== Permission Boundary Testing ===")
        
        # Test dispatch token on admin-only endpoint (should fail)
        success, data = self.test_api(
            "PERM-001",
            "GET",
            "/admin/transportation/carriers",
            self.get_dispatch_headers(),
            expected_status=401,
            description="Dispatch token on admin-only endpoint (should fail)"
        )
        
        if not success:
            self.log("Permission boundary correct: dispatch token rejected on admin-only endpoint", "PASS")
        else:
            self.record_defect(
                "WP16-W6-PERM-001",
                "P0",
                "Permission boundary violation: dispatch token accepted on admin-only endpoint",
                "GET /admin/transportation/carriers accepted X-Dispatch-Token"
            )
            
        # Test admin token on dispatch endpoint (should succeed for mixed access)
        success, data = self.test_api(
            "PERM-002",
            "GET",
            "/dispatch/assignments/board",
            self.get_admin_headers(),
            description="Admin token on dispatch endpoint (mixed access)"
        )
        
    def run_inspection(self):
        """Run full Wave 6 backend inspection"""
        self.log("=" * 80)
        self.log("WP-16 Wave 6 Backend API Inspection")
        self.log("Dispatch & Transportation")
        self.log("=" * 80)
        
        # Login
        if not self.login_dispatch():
            self.log("Failed to login as dispatch user - aborting", "FAIL")
            return False
            
        if not self.login_admin():
            self.log("Failed to login as admin user - aborting", "FAIL")
            return False
            
        # Run inspections in canonical order W6-001 to W6-010
        self.inspect_w6_001_dispatch_board()
        self.inspect_w6_002_command_center()
        self.inspect_w6_003_fleet_visibility()
        self.inspect_w6_004_operations_map()
        self.inspect_w6_005_haul_ledger()
        self.inspect_w6_006_driver_qualification()
        self.inspect_w6_007_driver_profile()
        self.inspect_w6_008_transportation_wrapper()
        self.inspect_w6_009_external_invite()
        self.inspect_w6_010_certificate_verify()
        
        # Test permission boundaries
        self.test_permission_boundaries()
        
        # Generate report
        self.generate_report()
        
        return True
        
    def generate_report(self):
        """Generate inspection report"""
        self.log("\n" + "=" * 80)
        self.log("WAVE 6 BACKEND INSPECTION REPORT")
        self.log("=" * 80)
        
        self.log(f"\n📊 SUMMARY:")
        self.log(f"   Total defects found: {len(self.defects)}")
        self.log(f"   Live fixtures discovered: {len(self.live_fixtures)}")
        
        if self.live_fixtures:
            self.log(f"\n🔑 LIVE FIXTURES FOR FRONTEND INSPECTION:")
            for fixture_type, value in self.live_fixtures.items():
                self.log(f"   {fixture_type}: {value}")
                
        if self.defects:
            self.log(f"\n❌ VERIFIED DEFECTS:")
            for defect in self.defects:
                self.log(f"\n   {defect['id']} ({defect['severity']}):")
                self.log(f"   Description: {defect['description']}")
                self.log(f"   Evidence: {defect['evidence']}")
        else:
            self.log(f"\n✅ NO CRITICAL DEFECTS FOUND")
            
        self.log("\n" + "=" * 80)
        self.log("INSPECTION COMPLETE")
        self.log("=" * 80)

if __name__ == "__main__":
    inspector = Wave6Inspector()
    success = inspector.run_inspection()
    sys.exit(0 if success else 1)
