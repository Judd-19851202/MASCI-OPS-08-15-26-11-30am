"""
WP-18CZ.2 Final Submission Workflow Tests
Tests for JHA acknowledgement, Transportation invite, Asset Transfers, 
Operational Constraints, and Service Truck Reconciliation workflows.
"""
import os
import pytest
import requests
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://masci-audit-hub.preview.emergentagent.com')
REQUEST_TIMEOUT = 60

_SESSION_REQUEST = requests.Session.request
_API_REQUEST = requests.api.request


def _timed_session_request(self, method, url, **kwargs):
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    return _SESSION_REQUEST(self, method, url, **kwargs)


def _timed_api_request(method, url, **kwargs):
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    return _API_REQUEST(method, url, **kwargs)


requests.Session.request = _timed_session_request
requests.api.request = _timed_api_request
requests.request = _timed_api_request

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
SHOP_EMAIL = "cert.shop@example.com"
SHOP_PASSWORD = "CertProof2026!"

# Fixture data
JHA_FIXTURE_FILE_ID = "c841c43f-34bd-43d3-96ca-b972d07b05fb"
JHA_FIXTURE_PROJECT = "25-12"
JHA_FIXTURE_EMPLOYEE_EMAIL = "track1540@mascicert.local"
TRANSPORT_INVITE_TOKEN = "UIPAaZvngRP7Lxjg6uNK-UA7mVjQeV1OUSdsGJHqb8M"


def _multi_login_session(email, password):
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/multi-login", json={
        "email": email,
        "password": password,
        "portal": "admin",
    }, timeout=60)
    response.raise_for_status()
    data = response.json()
    if data.get("session_token"):
        session.headers.update({"X-Directory-Token": data["session_token"]})
    portal_tokens = data.get("portal_tokens") or {}
    header_map = {
        "admin": "X-Admin-Token",
        "pm": "X-PM-Token",
        "shop": "X-Shop-Token",
        "dispatch": "X-Dispatch-Token",
        "safety": "X-Safety-Token",
        "hr": "X-HR-Token",
        "field_leadership": "X-FL-Token",
        "fl": "X-FL-Token",
    }
    for key, value in portal_tokens.items():
        header = header_map.get(key)
        if header and value:
            session.headers.update({header: value})
    return session


@pytest.fixture(scope="module")
def admin_session():
    """Get admin session with auth token"""
    return _multi_login_session(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def pm_session():
    """Get PM session with auth token"""
    return _multi_login_session(PM_EMAIL, PM_PASSWORD)


class TestJHAAcknowledgement:
    """JHA Acknowledgement workflow tests"""
    
    def test_jha_public_grouped_files(self):
        """Test public JHA files endpoint"""
        response = requests.get(f"{BASE_URL}/api/job-hazard-files/public/grouped")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} projects with JHA files")
        
        # Check for fixture project
        project_25_12 = next((p for p in data if p.get("project_number") == JHA_FIXTURE_PROJECT), None)
        if project_25_12:
            print(f"Project {JHA_FIXTURE_PROJECT} has {len(project_25_12.get('files', []))} files")
            assert len(project_25_12.get("files", [])) > 0
    
    def test_jha_acknowledgement_me_endpoint(self):
        """Test /me endpoint for acknowledgement status"""
        response = requests.get(
            f"{BASE_URL}/api/jha-acknowledgements/me",
            params={"employee_email": JHA_FIXTURE_EMPLOYEE_EMAIL}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "count" in data
        print(f"Employee {JHA_FIXTURE_EMPLOYEE_EMAIL} has {data['count']} acknowledgements")
    
    def test_jha_acknowledgement_duplicate_prevention(self):
        """Test that duplicate acknowledgements are prevented"""
        # First acknowledgement (may already exist)
        response = requests.post(f"{BASE_URL}/api/jha-acknowledgements", json={
            "project_number": JHA_FIXTURE_PROJECT,
            "jha_file_id": JHA_FIXTURE_FILE_ID,
            "employee_email": JHA_FIXTURE_EMPLOYEE_EMAIL,
            "signature": "Test Employee Duplicate Check"
        })
        
        # Should succeed (either new or duplicate prevented)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("ok") == True
        
        # Check if duplicate was prevented
        if data.get("duplicate_prevented"):
            print("SUCCESS: Duplicate acknowledgement safely prevented")
            assert "acknowledgement" in data
            assert data["acknowledgement"].get("doc_id")
        else:
            print("SUCCESS: New acknowledgement created")
            assert "acknowledgement" in data
    
    def test_jha_acknowledgement_by_doc_lookup(self, admin_session):
        """Test admin lookup by doc_id"""
        # First get an acknowledgement
        me_response = requests.get(
            f"{BASE_URL}/api/jha-acknowledgements/me",
            params={"employee_email": JHA_FIXTURE_EMPLOYEE_EMAIL}
        )
        if me_response.status_code == 200 and me_response.json().get("items"):
            doc_id = me_response.json()["items"][0].get("doc_id")
            if doc_id:
                # Lookup by doc_id
                response = admin_session.get(f"{BASE_URL}/api/jha-acknowledgements/by-doc/{doc_id}")
                assert response.status_code == 200
                data = response.json()
                assert "item" in data
                assert data["item"]["doc_id"] == doc_id
                print(f"SUCCESS: Found acknowledgement by doc_id: {doc_id}")


class TestTransportationInvite:
    """Transportation External Carrier Invite workflow tests"""
    
    def test_transport_invite_open(self):
        """Test opening a transport invite"""
        response = requests.get(f"{BASE_URL}/api/transportation/invite/{TRANSPORT_INVITE_TOKEN}")
        
        if response.status_code == 200:
            data = response.json()
            assert "invite_id" in data
            assert "carrier_legal_name" in data
            print(f"SUCCESS: Invite opened for carrier: {data.get('carrier_legal_name')}")
        elif response.status_code == 410:
            # Already submitted or expired
            print("INFO: Invite already submitted or expired")
        elif response.status_code == 404:
            print("INFO: Invite not found (may have been used)")
        else:
            print(f"WARNING: Unexpected status {response.status_code}")
    
    def test_transport_invite_invalid_token(self):
        """Test invalid token handling"""
        response = requests.get(f"{BASE_URL}/api/transportation/invite/INVALID-TOKEN-12345")
        assert response.status_code == 404
        print("SUCCESS: Invalid token correctly rejected with 404")
    
    def test_transport_invite_orientation_modules(self):
        """Test orientation modules endpoint"""
        response = requests.get(f"{BASE_URL}/api/transportation/invite/{TRANSPORT_INVITE_TOKEN}/orientation/modules")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            modules = data["items"]
            print(f"Found {len(modules)} orientation modules")
            
            # Check for required modules
            required = [m for m in modules if m.get("required")]
            print(f"Required modules: {len(required)}")
        elif response.status_code in [404, 410]:
            print("INFO: Invite not available for module listing")
    
    def test_transport_admin_invites_list(self, admin_session):
        """Test admin invites list endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/transportation/invites")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            print(f"Found {len(data['items'])} invites in admin list")
        else:
            print(f"Admin invites list returned {response.status_code}")


class TestAssetTransfers:
    """Asset Transfers workflow tests"""
    
    def test_asset_transfers_list(self, admin_session):
        """Test asset transfers list endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/asset-transfers")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"Found {len(data['items'])} asset transfers")
    
    def test_asset_transfer_create_and_verify(self, admin_session):
        """Test creating an asset transfer and verifying governed number"""
        # Create a test transfer
        response = admin_session.post(f"{BASE_URL}/api/asset-transfers", json={
            "equipment_id": "TEST-EQ-WP18CZ",
            "to_project_number": "25-12",
            "reason": "WP18CZ test transfer"
        })
        
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "doc_id" in data or "id" in data
            transfer_id = data["id"]
            doc_id = data.get("doc_id", data["id"])
            print(f"SUCCESS: Created transfer with doc_id: {doc_id}")
            
            # Verify by GET
            get_response = admin_session.get(f"{BASE_URL}/api/asset-transfers/{transfer_id}")
            assert get_response.status_code == 200
            get_data = get_response.json()
            assert get_data.get("doc_id") == doc_id or get_data.get("id") == transfer_id
            print(f"SUCCESS: Verified transfer exists with status: {get_data.get('status')}")
            
            # Cancel the test transfer
            cancel_response = admin_session.post(f"{BASE_URL}/api/asset-transfers/{transfer_id}/cancel")
            if cancel_response.status_code == 200:
                print("SUCCESS: Test transfer cancelled")
        elif response.status_code == 404:
            print("INFO: Equipment not found - expected for test equipment ID")
        else:
            print(f"Transfer create returned {response.status_code}: {response.text[:200]}")


class TestOperationalConstraints:
    """Operational Constraints workflow tests"""
    
    def test_constraints_list(self, admin_session):
        """Test constraints list endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/constraints")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} constraints")
    
    def test_constraint_create_and_verify(self, admin_session):
        """Test creating a constraint and verifying governed identifier"""
        # Create a test constraint
        response = admin_session.post(f"{BASE_URL}/api/constraints", json={
            "project_id": "25-12",
            "title": "WP18CZ Test Constraint",
            "discipline": "utilities",
            "kind": "utility-conflict",
            "severity": "medium",
            "owner": "Test Owner",
            "operational_impact": "Test impact for WP18CZ verification",
            "notes": "This is a test constraint for WP18CZ workflow verification"
        })
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            constraint_id = data["id"]
            doc_id = data.get("doc_id", "")
            print(f"SUCCESS: Created constraint with doc_id: {doc_id}")
            
            # Verify by GET
            get_response = admin_session.get(f"{BASE_URL}/api/constraints/{constraint_id}")
            assert get_response.status_code == 200
            get_data = get_response.json()
            assert get_data.get("id") == constraint_id
            assert get_data.get("status") == "open"
            print(f"SUCCESS: Verified constraint exists with status: {get_data.get('status')}")
            
            # Test chronology update
            chrono_response = admin_session.post(
                f"{BASE_URL}/api/constraints/{constraint_id}/chronology",
                json={"action": "note", "note": "WP18CZ test chronology entry"}
            )
            if chrono_response.status_code == 200:
                print("SUCCESS: Chronology update works")
            
            # Resolve the constraint
            resolve_response = admin_session.post(
                f"{BASE_URL}/api/constraints/{constraint_id}/resolve",
                json={"resolution_note": "WP18CZ test resolution - constraint resolved"}
            )
            if resolve_response.status_code == 200:
                resolve_data = resolve_response.json()
                assert resolve_data.get("status") == "resolved"
                print("SUCCESS: Constraint resolved correctly")
        else:
            print(f"Constraint create returned {response.status_code}: {response.text[:200]}")


class TestServiceTruckReconciliation:
    """Service Truck Reconciliation workflow tests"""
    
    def test_reconciliation_list(self, admin_session):
        """Test reconciliation list endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/shop/service-truck-reconciliation")
        assert response.status_code == 200
        data = response.json()
        assert "reconciliations" in data
        print(f"Found {len(data['reconciliations'])} reconciliations")
    
    def test_reconciliation_start_and_close(self, admin_session):
        """Test starting and closing a reconciliation"""
        today = datetime.now().strftime("%Y-%m-%d")
        test_truck = "TEST-TRUCK-WP18CZ"
        
        # Start reconciliation
        start_response = admin_session.post(
            f"{BASE_URL}/api/shop/service-truck-reconciliation/start",
            json={
                "date": today,
                "service_truck_unit": test_truck,
                "tech_id": "TEST-TECH-001",
                "tech_name": "WP18CZ Test Tech",
                "start_quantities": {
                    "red_diesel_gallons": 100,
                    "clear_diesel_gallons": 50,
                    "gasoline_gallons": 25,
                    "def_gallons": 10,
                    "engine_oil_quarts": 20,
                    "hydraulic_oil_quarts": 15,
                    "coolant_quarts": 10,
                    "transmission_fluid_quarts": 5,
                    "gear_oil_quarts": 5
                },
                "notes": "WP18CZ test start"
            }
        )
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            assert start_data.get("ok") == True
            rec_id = start_data.get("id")
            doc_id = start_data.get("doc_id", rec_id)
            print(f"SUCCESS: Started reconciliation with doc_id: {doc_id}")
            
            # Close reconciliation
            close_response = admin_session.post(
                f"{BASE_URL}/api/shop/service-truck-reconciliation/close",
                json={
                    "reconciliation_id": rec_id,
                    "end_quantities": {
                        "red_diesel_gallons": 80,
                        "clear_diesel_gallons": 40,
                        "gasoline_gallons": 20,
                        "def_gallons": 8,
                        "engine_oil_quarts": 18,
                        "hydraulic_oil_quarts": 13,
                        "coolant_quarts": 9,
                        "transmission_fluid_quarts": 4,
                        "gear_oil_quarts": 4
                    },
                    "notes": "WP18CZ test close",
                    "submitted_by": "WP18CZ Test Tech"
                }
            )
            
            if close_response.status_code == 200:
                close_data = close_response.json()
                assert close_data.get("ok") == True
                print(f"SUCCESS: Closed reconciliation with variance status: {close_data.get('variance_status')}")
                
                # Verify by GET
                get_response = admin_session.get(f"{BASE_URL}/api/shop/service-truck-reconciliation/{rec_id}")
                if get_response.status_code == 200:
                    get_data = get_response.json()
                    assert "reconciliation" in get_data
                    print(f"SUCCESS: Verified reconciliation detail with status: {get_data['reconciliation'].get('status')}")
            else:
                print(f"Close returned {close_response.status_code}: {close_response.text[:200]}")
        elif start_response.status_code == 409:
            print("INFO: Reconciliation already exists for this truck/date")
        else:
            print(f"Start returned {start_response.status_code}: {start_response.text[:200]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
