#!/usr/bin/env python3
"""
MASCI OPS Checkpoint 7 Phase B - Backend Verification Script
Independently verify /api/admin/platform-trust/validate endpoint
"""
import os
import sys
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_pass(msg):
    print(f"{GREEN}✓ PASS{RESET}: {msg}")

def print_fail(msg):
    print(f"{RED}✗ FAIL{RESET}: {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ INFO{RESET}: {msg}")

def print_section(msg):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{msg}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

async def call_validator():
    """Call the validator endpoint directly (bypassing auth for testing)"""
    from routes.admin_platform_trust import make_router
    
    # Connect to DB
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    # Mock auth dependency
    async def _passthrough_dep():
        return None
    
    # Mock runtime identity with different statuses
    class FakeIdentity:
        def __init__(self):
            self.app_env = "preview"
            self.db_name = "masci_safety_preview"
        
        def to_safe_dict(self):
            return {
                "app_env": self.app_env,
                "db_name": self.db_name,
            }
    
    class FakeValidation:
        def __init__(self, status="VERIFIED"):
            self.status = status
            self.valid = True
            self.mismatch_category = None
        
        def to_safe_dict(self):
            return {
                "status": self.status,
                "valid": self.valid,
                "mismatch_category": self.mismatch_category,
                "detail": "test-bundle",
                "errors": [],
                "warnings": [],
                "remediation_owner": "tests",
                "remediation_action": "none",
            }
    
    def runtime_bundle(status="VERIFIED"):
        return {
            "identity": FakeIdentity(),
            "validation": FakeValidation(status=status),
        }
    
    # Create router with mock dependencies
    router = make_router(
        db,
        _passthrough_dep,
        get_runtime_identity=lambda: runtime_bundle("VERIFIED")
    )
    
    # Find the handler
    handler = None
    for route in router.routes:
        if getattr(route, "path", "") == "/api/admin/platform-trust/validate":
            handler = route.endpoint
            break
    
    if not handler:
        raise Exception("Handler not found")
    
    # Call the handler
    return await handler(_=None)

async def verify_legacy_contract(payload):
    """Verify legacy contract is preserved (13 existing fields)"""
    print_section("REQUIREMENT 1: Legacy Contract Preserved")
    
    required_fields = [
        "track",
        "generated_at",
        "canonical_truth",
        "truth_relationship",
        "system",
        "email_routing",
        "audit_status_integrity",
        "workflow_delivery_health",
        "pm_email_coverage",
        "dead_letter_health",
        "final_band",
        "red_reasons",
        "amber_reasons",
    ]
    
    all_pass = True
    for field in required_fields:
        if field in payload:
            print_pass(f"Field '{field}' present")
        else:
            print_fail(f"Field '{field}' MISSING")
            all_pass = False
    
    return all_pass

async def verify_ots_contract(payload):
    """Verify new additive OTS contract present"""
    print_section("REQUIREMENT 2: New Additive OTS Contract Present")
    
    all_pass = True
    
    # Check ots_truth exists
    if "ots_truth" not in payload:
        print_fail("Field 'ots_truth' MISSING")
        return False
    print_pass("Field 'ots_truth' present (additive)")
    
    # Check compatibility exists
    if "compatibility" not in payload:
        print_fail("Field 'compatibility' MISSING")
        return False
    print_pass("Field 'compatibility' present (additive)")
    
    # Check compatibility.breaking_api_changes is 0
    compat = payload.get("compatibility", {})
    breaking = compat.get("breaking_api_changes", -1)
    if breaking == 0:
        print_pass(f"compatibility.breaking_api_changes = {breaking} (no breaking changes)")
    else:
        print_fail(f"compatibility.breaking_api_changes = {breaking} (expected 0)")
        all_pass = False
    
    return all_pass

async def verify_constitutional_bounding(payload):
    """Verify constitutional bounding"""
    print_section("REQUIREMENT 3: Constitutional Bounding")
    
    all_pass = True
    ots = payload.get("ots_truth", {})
    
    # Check truth_subject
    truth_subject = ots.get("truth_subject")
    if truth_subject == "platform_validation_truth":
        print_pass(f"ots_truth.truth_subject = '{truth_subject}' (correct)")
    else:
        print_fail(f"ots_truth.truth_subject = '{truth_subject}' (expected 'platform_validation_truth')")
        all_pass = False
    
    # Check canonical_owner
    canonical_owner = ots.get("canonical_owner")
    if canonical_owner == "platform_attestation":
        print_pass(f"ots_truth.canonical_owner = '{canonical_owner}' (correct)")
    else:
        print_fail(f"ots_truth.canonical_owner = '{canonical_owner}' (expected 'platform_attestation')")
        all_pass = False
    
    # Check claim_ceiling
    claim_ceiling = ots.get("claim_ceiling")
    if claim_ceiling == "VALIDATED":
        print_pass(f"ots_truth.claim_ceiling = '{claim_ceiling}' (always VALIDATED)")
    else:
        print_fail(f"ots_truth.claim_ceiling = '{claim_ceiling}' (expected 'VALIDATED')")
        all_pass = False
    
    # Check permitted_claim never exceeds VALIDATED and MUST NEVER be CERTIFIED
    permitted_claim = ots.get("permitted_claim")
    valid_claims = ["OBSERVED", "CORRELATED", "VERIFIED", "VALIDATED"]
    if permitted_claim in valid_claims:
        print_pass(f"ots_truth.permitted_claim = '{permitted_claim}' (valid bounded claim)")
    else:
        print_fail(f"ots_truth.permitted_claim = '{permitted_claim}' (invalid claim)")
        all_pass = False
    
    if permitted_claim != "CERTIFIED":
        print_pass(f"ots_truth.permitted_claim = '{permitted_claim}' (MUST NEVER be CERTIFIED)")
    else:
        print_fail(f"ots_truth.permitted_claim = 'CERTIFIED' (VIOLATION: validator cannot certify)")
        all_pass = False
    
    # Check truth_relationship.role
    truth_rel = payload.get("truth_relationship", {})
    role = truth_rel.get("role")
    if role == "VALIDATOR":
        print_pass(f"truth_relationship.role = '{role}' (correct)")
    else:
        print_fail(f"truth_relationship.role = '{role}' (expected 'VALIDATOR')")
        all_pass = False
    
    # Check prohibited_claims includes platform certification
    prohibited = ots.get("prohibited_claims", [])
    if "platform certification" in prohibited or "CERTIFIED" in prohibited:
        print_pass(f"ots_truth.prohibited_claims includes platform certification/CERTIFIED")
    else:
        print_fail(f"ots_truth.prohibited_claims missing platform certification/CERTIFIED")
        all_pass = False
    
    return all_pass

async def verify_upstream_bounding():
    """Verify validator never exceeds upstream owner claim"""
    print_section("REQUIREMENT 3b: Validator Never Exceeds Upstream Owner Claim")
    
    from routes.admin_platform_trust import make_router
    
    # Connect to DB
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    
    async def _passthrough_dep():
        return None
    
    class FakeIdentity:
        def __init__(self):
            self.app_env = "preview"
            self.db_name = "masci_safety_preview"
        
        def to_safe_dict(self):
            return {
                "app_env": self.app_env,
                "db_name": self.db_name,
            }
    
    class FakeValidation:
        def __init__(self, status="VERIFIED"):
            self.status = status
            self.valid = True
            self.mismatch_category = None
        
        def to_safe_dict(self):
            return {
                "status": self.status,
                "valid": self.valid,
                "mismatch_category": self.mismatch_category,
                "detail": "test-bundle",
                "errors": [],
                "warnings": [],
                "remediation_owner": "tests",
                "remediation_action": "none",
            }
    
    def runtime_bundle(status="DEGRADED"):
        return {
            "identity": FakeIdentity(),
            "validation": FakeValidation(status=status),
        }
    
    # Test with DEGRADED upstream status
    router = make_router(
        db,
        _passthrough_dep,
        get_runtime_identity=lambda: runtime_bundle("DEGRADED")
    )
    
    handler = None
    for route in router.routes:
        if getattr(route, "path", "") == "/api/admin/platform-trust/validate":
            handler = route.endpoint
            break
    
    payload = await handler(_=None)
    ots = payload.get("ots_truth", {})
    
    all_pass = True
    
    # When upstream is DEGRADED, validator should not claim VALIDATED
    permitted_claim = ots.get("permitted_claim")
    claim_ceiling = ots.get("claim_ceiling")
    
    if claim_ceiling == "VALIDATED":
        print_pass(f"ots_truth.claim_ceiling = '{claim_ceiling}' (always VALIDATED)")
    else:
        print_fail(f"ots_truth.claim_ceiling = '{claim_ceiling}' (expected 'VALIDATED')")
        all_pass = False
    
    # Permitted claim should be downgraded when upstream is weaker
    if permitted_claim in ["OBSERVED", "CORRELATED", "VERIFIED"]:
        print_pass(f"ots_truth.permitted_claim = '{permitted_claim}' (correctly downgraded from upstream DEGRADED)")
    else:
        print_fail(f"ots_truth.permitted_claim = '{permitted_claim}' (should be downgraded when upstream is DEGRADED)")
        all_pass = False
    
    if permitted_claim != "VALIDATED":
        print_pass(f"ots_truth.permitted_claim != 'VALIDATED' (validator correctly bounded by weaker upstream)")
    else:
        print_fail(f"ots_truth.permitted_claim = 'VALIDATED' (should not exceed upstream DEGRADED)")
        all_pass = False
    
    return all_pass

async def verify_truthful_downgrade(payload):
    """Verify truthful downgrade semantics"""
    print_section("REQUIREMENT 4: Truthful Downgrade Semantics")
    
    all_pass = True
    ots = payload.get("ots_truth", {})
    
    # Check unknowns field exists
    if "unknowns" in ots:
        print_pass(f"ots_truth.unknowns present (count: {len(ots['unknowns'])})")
    else:
        print_fail("ots_truth.unknowns MISSING")
        all_pass = False
    
    # Check contradictory_evidence field exists
    if "contradictory_evidence" in ots:
        print_pass(f"ots_truth.contradictory_evidence present (count: {len(ots['contradictory_evidence'])})")
    else:
        print_fail("ots_truth.contradictory_evidence MISSING")
        all_pass = False
    
    # Check degradation_reasons field exists
    if "degradation_reasons" in ots:
        print_pass(f"ots_truth.degradation_reasons present (count: {len(ots['degradation_reasons'])})")
    else:
        print_fail("ots_truth.degradation_reasons MISSING")
        all_pass = False
    
    # Verify red/amber states carry bounded reasons
    final_band = payload.get("final_band")
    red_reasons = payload.get("red_reasons", [])
    amber_reasons = payload.get("amber_reasons", [])
    
    if final_band == "red":
        if red_reasons:
            print_pass(f"final_band = 'red' with {len(red_reasons)} red_reasons (truthful)")
        else:
            print_fail(f"final_band = 'red' but no red_reasons (should explain why)")
            all_pass = False
    elif final_band == "amber":
        if amber_reasons:
            print_pass(f"final_band = 'amber' with {len(amber_reasons)} amber_reasons (truthful)")
        else:
            print_fail(f"final_band = 'amber' but no amber_reasons (should explain why)")
            all_pass = False
    else:
        print_pass(f"final_band = '{final_band}' (green or other)")
    
    return all_pass

async def verify_auth_and_health():
    """Verify auth and health"""
    print_section("REQUIREMENT 5: Auth and Health")
    
    import urllib.request
    import urllib.error
    
    all_pass = True
    
    # Test anonymous access is rejected
    api_url = "https://masci-audit-hub.preview.emergentagent.com"
    try:
        urllib.request.urlopen(f"{api_url}/api/admin/platform-trust/validate", timeout=15)
        print_fail("Anonymous access NOT rejected (should return 401/403)")
        all_pass = False
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            print_pass(f"Anonymous access rejected with HTTP {exc.code}")
        else:
            print_fail(f"Anonymous access returned HTTP {exc.code} (expected 401/403)")
            all_pass = False
    except Exception as e:
        print_fail(f"Error testing anonymous access: {e}")
        all_pass = False
    
    # Test invalid token access is rejected
    try:
        req = urllib.request.Request(
            f"{api_url}/api/admin/platform-trust/validate",
            headers={"Cookie": "admin_token=invalid_token_12345"}
        )
        urllib.request.urlopen(req, timeout=15)
        print_fail("Invalid token access NOT rejected (should return 401/403)")
        all_pass = False
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            print_pass(f"Invalid token access rejected with HTTP {exc.code}")
        else:
            print_fail(f"Invalid token access returned HTTP {exc.code} (expected 401/403)")
            all_pass = False
    except Exception as e:
        print_fail(f"Error testing invalid token access: {e}")
        all_pass = False
    
    # Backend health check
    try:
        response = urllib.request.urlopen(f"{api_url}/api/health", timeout=15)
        if response.status == 200:
            print_pass("Backend health check passed (HTTP 200)")
        else:
            print_fail(f"Backend health check returned HTTP {response.status}")
            all_pass = False
    except Exception as e:
        print_fail(f"Backend health check failed: {e}")
        all_pass = False
    
    return all_pass

async def verify_upstream_owner_reference():
    """Verify upstream owner reference endpoint is accessible"""
    print_section("ADDITIONAL: Upstream Owner Reference")
    
    import urllib.request
    
    all_pass = True
    api_url = "https://masci-audit-hub.preview.emergentagent.com"
    
    # Test /api/admin/platform/status endpoint exists (upstream owner)
    try:
        urllib.request.urlopen(f"{api_url}/api/admin/platform/status", timeout=15)
        print_fail("Upstream owner endpoint /api/admin/platform/status should require auth but returned 200")
        all_pass = False
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            print_pass(f"Upstream owner endpoint /api/admin/platform/status exists and requires auth (HTTP {exc.code})")
        else:
            print_fail(f"Upstream owner endpoint returned unexpected HTTP {exc.code}")
            all_pass = False
    except Exception as e:
        print_fail(f"Error checking upstream owner endpoint: {e}")
        all_pass = False
    
    return all_pass

async def main():
    print_section("MASCI OPS Checkpoint 7 Phase B - Backend Verification")
    print_info("Target endpoint: /api/admin/platform-trust/validate")
    print_info("Upstream owner: /api/admin/platform/status")
    print_info("Runtime file: /app/backend/routes/admin_platform_trust.py")
    
    try:
        # Call the validator to get payload
        print_info("Calling validator endpoint...")
        payload = await call_validator()
        print_pass("Validator endpoint called successfully")
        
        # Save payload for inspection
        with open("/tmp/checkpoint7_payload.json", "w") as f:
            json.dump(payload, f, indent=2, default=str)
        print_info("Payload saved to /tmp/checkpoint7_payload.json")
        
        # Run all verifications
        results = []
        
        results.append(("Legacy Contract", await verify_legacy_contract(payload)))
        results.append(("OTS Contract", await verify_ots_contract(payload)))
        results.append(("Constitutional Bounding", await verify_constitutional_bounding(payload)))
        results.append(("Upstream Bounding", await verify_upstream_bounding()))
        results.append(("Truthful Downgrade", await verify_truthful_downgrade(payload)))
        results.append(("Auth and Health", await verify_auth_and_health()))
        results.append(("Upstream Owner", await verify_upstream_owner_reference()))
        
        # Summary
        print_section("VERIFICATION SUMMARY")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
            print(f"  {name}: {status}")
        
        print(f"\n{BLUE}Total: {passed}/{total} requirements passed{RESET}")
        
        if passed == total:
            print(f"\n{GREEN}{'='*80}{RESET}")
            print(f"{GREEN}✓ ALL REQUIREMENTS PASSED - CHECKPOINT 7 PHASE B VERIFIED{RESET}")
            print(f"{GREEN}{'='*80}{RESET}\n")
            return 0
        else:
            print(f"\n{RED}{'='*80}{RESET}")
            print(f"{RED}✗ SOME REQUIREMENTS FAILED - SEE DETAILS ABOVE{RESET}")
            print(f"{RED}{'='*80}{RESET}\n")
            return 1
            
    except Exception as e:
        print_fail(f"Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
