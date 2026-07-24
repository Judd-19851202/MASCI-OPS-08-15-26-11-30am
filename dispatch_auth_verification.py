"""
Focused backend/auth verification for Dispatch portal sign-in contract.

Verifies:
1) POST /api/dispatch/login with cert.dispatch@example.com / CertProof2026! succeeds
2) Response contract remains valid for frontend dispatch login
3) Must-change-password behavior compatible with frontend redirect
4) No backend regression introduced by frontend fix
"""
import requests
import json
from datetime import datetime, timezone

# Backend URL from frontend/.env
BASE_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
DISPATCH_EMAIL = "cert.dispatch@example.com"
DISPATCH_PASSWORD = "CertProof2026!"

def test_dispatch_login():
    """Test 1: POST /api/dispatch/login succeeds with correct credentials"""
    print("\n" + "="*80)
    print("TEST 1: Dispatch Login Authentication")
    print("="*80)
    
    url = f"{BASE_URL}/dispatch/login"
    payload = {
        "email": DISPATCH_EMAIL,
        "password": DISPATCH_PASSWORD
    }
    
    print(f"\nPOST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Body: {json.dumps(data, indent=2)}")
            
            # Verify response contract
            required_fields = ["token", "user", "must_change_password", "kind"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print(f"\n❌ FAIL: Missing required fields: {missing_fields}")
                return {
                    "test": "dispatch_login",
                    "status": "FAIL",
                    "reason": f"Missing required fields: {missing_fields}",
                    "response": data
                }
            
            # Verify token is present and non-empty
            if not data.get("token"):
                print(f"\n❌ FAIL: Token is empty or missing")
                return {
                    "test": "dispatch_login",
                    "status": "FAIL",
                    "reason": "Token is empty or missing",
                    "response": data
                }
            
            # Verify user object has expected fields
            user = data.get("user", {})
            user_required_fields = ["id", "email", "name"]
            missing_user_fields = [f for f in user_required_fields if f not in user]
            
            if missing_user_fields:
                print(f"\n❌ FAIL: User object missing fields: {missing_user_fields}")
                return {
                    "test": "dispatch_login",
                    "status": "FAIL",
                    "reason": f"User object missing fields: {missing_user_fields}",
                    "response": data
                }
            
            # Verify kind is "dispatch"
            if data.get("kind") != "dispatch":
                print(f"\n⚠️  WARNING: Expected kind='dispatch', got kind='{data.get('kind')}'")
            
            print(f"\n✅ PASS: Dispatch login successful")
            print(f"   - Token: {data['token'][:20]}... (truncated)")
            print(f"   - User ID: {user.get('id')}")
            print(f"   - User Email: {user.get('email')}")
            print(f"   - User Name: {user.get('name')}")
            print(f"   - Must Change Password: {data.get('must_change_password')}")
            print(f"   - Kind: {data.get('kind')}")
            
            return {
                "test": "dispatch_login",
                "status": "PASS",
                "token": data["token"],
                "user": user,
                "must_change_password": data.get("must_change_password"),
                "kind": data.get("kind"),
                "response": data
            }
        else:
            print(f"\n❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "test": "dispatch_login",
                "status": "FAIL",
                "reason": f"Expected 200, got {response.status_code}",
                "response_text": response.text
            }
    except Exception as e:
        print(f"\n❌ FAIL: Exception occurred: {str(e)}")
        return {
            "test": "dispatch_login",
            "status": "FAIL",
            "reason": f"Exception: {str(e)}"
        }


def test_response_contract_validity(login_result):
    """Test 2: Verify response contract is valid for frontend dispatch login"""
    print("\n" + "="*80)
    print("TEST 2: Response Contract Validity for Frontend")
    print("="*80)
    
    if login_result.get("status") != "PASS":
        print("\n⚠️  SKIP: Login test failed, cannot verify contract")
        return {
            "test": "response_contract",
            "status": "SKIP",
            "reason": "Login test failed"
        }
    
    response = login_result.get("response", {})
    
    # Check all fields frontend expects
    frontend_expected_fields = {
        "token": str,
        "user": dict,
        "must_change_password": bool,
        "kind": str
    }
    
    issues = []
    
    for field, expected_type in frontend_expected_fields.items():
        if field not in response:
            issues.append(f"Missing field: {field}")
        elif not isinstance(response[field], expected_type):
            issues.append(f"Field '{field}' has wrong type: expected {expected_type.__name__}, got {type(response[field]).__name__}")
    
    # Check user object structure
    user = response.get("user", {})
    user_expected_fields = ["id", "email", "name"]
    for field in user_expected_fields:
        if field not in user:
            issues.append(f"User object missing field: {field}")
    
    if issues:
        print(f"\n❌ FAIL: Contract validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return {
            "test": "response_contract",
            "status": "FAIL",
            "issues": issues
        }
    
    print(f"\n✅ PASS: Response contract is valid for frontend")
    print(f"   - All required fields present")
    print(f"   - All field types correct")
    print(f"   - User object structure valid")
    
    return {
        "test": "response_contract",
        "status": "PASS"
    }


def test_must_change_password_behavior(login_result):
    """Test 3: Verify must-change-password behavior is compatible with frontend redirect"""
    print("\n" + "="*80)
    print("TEST 3: Must-Change-Password Behavior")
    print("="*80)
    
    if login_result.get("status") != "PASS":
        print("\n⚠️  SKIP: Login test failed, cannot verify must-change-password")
        return {
            "test": "must_change_password",
            "status": "SKIP",
            "reason": "Login test failed"
        }
    
    must_change = login_result.get("must_change_password")
    
    # Verify must_change_password is a boolean
    if not isinstance(must_change, bool):
        print(f"\n❌ FAIL: must_change_password should be boolean, got {type(must_change).__name__}")
        return {
            "test": "must_change_password",
            "status": "FAIL",
            "reason": f"must_change_password is not boolean: {type(must_change).__name__}"
        }
    
    print(f"\n✅ PASS: must_change_password behavior is compatible")
    print(f"   - Field is boolean: {must_change}")
    print(f"   - Frontend can use this to redirect to /dispatch-portal/change-password")
    print(f"   - Current value: {must_change}")
    
    if must_change:
        print(f"   - ⚠️  Note: User is flagged for password change")
    else:
        print(f"   - User is not flagged for password change")
    
    return {
        "test": "must_change_password",
        "status": "PASS",
        "must_change_password": must_change
    }


def test_no_backend_regression(login_result):
    """Test 4: Verify no backend regression introduced by frontend fix"""
    print("\n" + "="*80)
    print("TEST 4: No Backend Regression")
    print("="*80)
    
    if login_result.get("status") != "PASS":
        print("\n⚠️  SKIP: Login test failed, cannot verify regression")
        return {
            "test": "no_regression",
            "status": "SKIP",
            "reason": "Login test failed"
        }
    
    token = login_result.get("token")
    
    # Test that token can be used to access dispatch endpoints
    print(f"\nVerifying token works with dispatch endpoints...")
    
    # Test /api/dispatch/me endpoint
    url = f"{BASE_URL}/dispatch/me"
    headers = {"X-Dispatch-Token": token}
    
    print(f"\nGET {url}")
    print(f"Headers: X-Dispatch-Token: {token[:20]}... (truncated)")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify user data is returned
            if "user" not in data:
                print(f"\n❌ FAIL: /dispatch/me response missing 'user' field")
                return {
                    "test": "no_regression",
                    "status": "FAIL",
                    "reason": "/dispatch/me response missing 'user' field"
                }
            
            print(f"\n✅ PASS: No backend regression detected")
            print(f"   - Login endpoint works correctly")
            print(f"   - Token is valid and accepted by backend")
            print(f"   - /dispatch/me endpoint accessible with token")
            print(f"   - Response contract unchanged")
            
            return {
                "test": "no_regression",
                "status": "PASS",
                "me_response": data
            }
        else:
            print(f"\n❌ FAIL: /dispatch/me returned {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "test": "no_regression",
                "status": "FAIL",
                "reason": f"/dispatch/me returned {response.status_code}",
                "response_text": response.text
            }
    except Exception as e:
        print(f"\n❌ FAIL: Exception occurred: {str(e)}")
        return {
            "test": "no_regression",
            "status": "FAIL",
            "reason": f"Exception: {str(e)}"
        }


def main():
    """Run all dispatch auth verification tests"""
    print("\n" + "="*80)
    print("DISPATCH PORTAL AUTH VERIFICATION")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print(f"Test User: {DISPATCH_EMAIL}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    results = {}
    
    # Test 1: Login
    login_result = test_dispatch_login()
    results["dispatch_login"] = login_result
    
    # Test 2: Response contract
    contract_result = test_response_contract_validity(login_result)
    results["response_contract"] = contract_result
    
    # Test 3: Must-change-password
    must_change_result = test_must_change_password_behavior(login_result)
    results["must_change_password"] = must_change_result
    
    # Test 4: No regression
    regression_result = test_no_backend_regression(login_result)
    results["no_regression"] = regression_result
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    failed = sum(1 for r in results.values() if r.get("status") == "FAIL")
    skipped = sum(1 for r in results.values() if r.get("status") == "SKIP")
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    print(f"\nTest Results:")
    for test_name, result in results.items():
        status = result.get("status", "UNKNOWN")
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"  {symbol} {test_name}: {status}")
        if result.get("reason"):
            print(f"     Reason: {result['reason']}")
    
    # Save results to file
    output_file = "/app/dispatch_auth_verification_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_url": BASE_URL,
            "test_user": DISPATCH_EMAIL,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Final verdict
    print("\n" + "="*80)
    if failed == 0 and passed == total:
        print("FINAL VERDICT: ✅ ALL TESTS PASSED")
        print("="*80)
        return 0
    elif failed > 0:
        print(f"FINAL VERDICT: ❌ {failed} TEST(S) FAILED")
        print("="*80)
        return 1
    else:
        print(f"FINAL VERDICT: ⚠️  {skipped} TEST(S) SKIPPED")
        print("="*80)
        return 2


if __name__ == "__main__":
    exit(main())
