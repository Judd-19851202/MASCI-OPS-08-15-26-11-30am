#!/usr/bin/env python3
"""
Backend test for governed certification lane repair.

Validates the PREVIEW-only bounded backend repair for Daily Report governed certification lane.
Focus: recipient selection and governed-lane invariants.

Required proof points:
1. Placeholder example.com certification recipients are no longer selected
2. Correct governed recipients are selected from live project routing when available
3. Normal non-certification behavior remains unchanged outside the certification lane
4. The focused proof tests pass
"""
import sys
sys.path.insert(0, "/app/backend")

from lib.governed_certification_lane import (
    _is_reserved_or_invalid_email,
    _select_governed_recipients,
    build_governed_routing_override,
    apply_governed_daily_report_lane,
)


def test_proof_point_1_placeholder_example_com_not_selected():
    """Proof Point 1: Placeholder example.com certification recipients are no longer selected."""
    print("\n=== PROOF POINT 1: Placeholder example.com recipients NOT selected ===")
    
    # Test 1a: Direct validation of _is_reserved_or_invalid_email
    test_cases = [
        ("cert.pm@example.com", True, "example.com domain"),
        ("cert.copm@example.com", True, "example.com domain"),
        ("test@subdomain.example.com", True, "subdomain of example.com"),
        ("user@example.org", True, "example.org domain"),
        ("user@example.net", True, "example.net domain"),
        ("jaymn.judd@mascigc.com", False, "valid real domain"),
        ("preview-cert@mascigc.com", False, "valid real domain"),
        ("", True, "empty email"),
        ("invalid", True, "no @ symbol"),
    ]
    
    all_passed = True
    for email, expected_invalid, description in test_cases:
        result = _is_reserved_or_invalid_email(email)
        status = "✅ PASS" if result == expected_invalid else "❌ FAIL"
        print(f"  {status}: {email:40s} -> invalid={result:5} (expected={expected_invalid:5}) [{description}]")
        if result != expected_invalid:
            all_passed = False
    
    # Test 1b: Validate that _select_governed_recipients filters out example.com
    print("\n  Testing _select_governed_recipients with placeholder emails:")
    project_doc_with_placeholders = {
        "pm_email": "cert.pm@example.com",
        "co_pm_emails": ["cert.copm@example.com", "cert.foreman@example.com"],
    }
    
    result = _select_governed_recipients(project_doc=project_doc_with_placeholders)
    has_example_com = any("example.com" in email for email in result["to"] + result["cc"])
    
    if has_example_com:
        print(f"  ❌ FAIL: example.com emails found in result: {result}")
        all_passed = False
    else:
        print(f"  ✅ PASS: No example.com emails in result (to={result['to']}, cc={result['cc']})")
    
    return all_passed


def test_proof_point_2_correct_recipients_from_live_project():
    """Proof Point 2: Correct governed recipients are selected from live project routing when available."""
    print("\n=== PROOF POINT 2: Correct recipients from live project routing ===")
    
    # Test with valid project routing
    project_doc_with_valid_routing = {
        "project_number": "ZZ-RUNTIME-CERT-2026",
        "project_name": "Runtime Certification — Internal Test Project",
        "pm_email": "jaymn.judd@mascigc.com",
        "co_pm_emails": ["david.jewett@mascigc.com", "chris.wright@mascigc.com"],
        "active": True,
    }
    
    result = build_governed_routing_override(project_doc=project_doc_with_valid_routing)
    
    all_passed = True
    
    # Validate primary PM is in 'to'
    if "jaymn.judd@mascigc.com" in result["to"]:
        print(f"  ✅ PASS: Primary PM in 'to': {result['to']}")
    else:
        print(f"  ❌ FAIL: Primary PM NOT in 'to': {result['to']}")
        all_passed = False
    
    # Validate co-PMs are in 'cc'
    expected_co_pms = {"david.jewett@mascigc.com", "chris.wright@mascigc.com"}
    actual_cc = set(result["cc"])
    if expected_co_pms.issubset(actual_cc):
        print(f"  ✅ PASS: Co-PMs in 'cc': {result['cc']}")
    else:
        print(f"  ❌ FAIL: Co-PMs NOT properly in 'cc': expected={expected_co_pms}, actual={actual_cc}")
        all_passed = False
    
    # Validate recipient_source is 'project_doc'
    if result.get("recipient_source") == "project_doc":
        print(f"  ✅ PASS: recipient_source is 'project_doc'")
    else:
        print(f"  ❌ FAIL: recipient_source is '{result.get('recipient_source')}', expected 'project_doc'")
        all_passed = False
    
    # Validate no example.com in final recipients
    has_example_com = any("example.com" in email for email in result["all"])
    if not has_example_com:
        print(f"  ✅ PASS: No example.com in final recipients")
    else:
        print(f"  ❌ FAIL: example.com found in final recipients: {result['all']}")
        all_passed = False
    
    return all_passed


def test_proof_point_3_normal_non_certification_unchanged():
    """Proof Point 3: Normal non-certification behavior remains unchanged outside the certification lane."""
    print("\n=== PROOF POINT 3: Normal non-certification behavior unchanged ===")
    
    # Test with a normal (non-certification) daily report
    normal_doc = {
        "id": "dr-normal-1",
        "project_number": "26-07",
        "project_name": "Normal Project",
        "prepared_by": "John Foreman",
        "prepared_by_identity": {
            "directory": "fl",
            "user_id": "john.foreman@mascigc.com",
            "name": "John Foreman",
            "email": "john.foreman@mascigc.com",
            "role": "Foreman",
        },
    }
    
    # Apply governed lane logic
    result_doc = apply_governed_daily_report_lane(normal_doc, project_doc=None)
    
    all_passed = True
    
    # Validate that certification flags are NOT set for normal reports
    if not result_doc.get("certification_record"):
        print(f"  ✅ PASS: certification_record is False for normal report")
    else:
        print(f"  ❌ FAIL: certification_record is True for normal report")
        all_passed = False
    
    if not result_doc.get("synthetic_record"):
        print(f"  ✅ PASS: synthetic_record is False for normal report")
    else:
        print(f"  ❌ FAIL: synthetic_record is True for normal report")
        all_passed = False
    
    if not result_doc.get("hidden_from_operations"):
        print(f"  ✅ PASS: hidden_from_operations is False for normal report")
    else:
        print(f"  ❌ FAIL: hidden_from_operations is True for normal report")
        all_passed = False
    
    if not result_doc.get("routing_override"):
        print(f"  ✅ PASS: routing_override is not set for normal report")
    else:
        print(f"  ❌ FAIL: routing_override is set for normal report: {result_doc.get('routing_override')}")
        all_passed = False
    
    return all_passed


def test_proof_point_4_focused_tests_pass():
    """Proof Point 4: The focused proof tests pass."""
    print("\n=== PROOF POINT 4: Focused proof tests pass ===")
    print("  Running pytest on test_dr03_governed_certification_lane.py...")
    
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_dr03_governed_certification_lane.py", "-v", "--tb=short"],
        cwd="/app/backend",
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        print(f"  ✅ PASS: All focused tests passed")
        # Extract test count from output
        for line in result.stdout.split("\n"):
            if "passed" in line:
                print(f"  {line.strip()}")
        return True
    else:
        print(f"  ❌ FAIL: Some focused tests failed")
        print(result.stdout)
        print(result.stderr)
        return False


def test_additional_edge_cases():
    """Additional edge case validation for robustness."""
    print("\n=== ADDITIONAL EDGE CASES ===")
    
    all_passed = True
    
    # Edge case 1: Mixed valid and invalid emails
    print("\n  Edge Case 1: Mixed valid and invalid emails in project_doc")
    mixed_project_doc = {
        "pm_email": "cert.pm@example.com",  # Invalid placeholder
        "co_pm_emails": [
            "valid.copm@mascigc.com",  # Valid
            "cert.copm@example.com",   # Invalid placeholder
        ],
    }
    
    result = _select_governed_recipients(project_doc=mixed_project_doc)
    
    # Should skip the invalid pm_email and use fallback
    if not result["to"] or "example.com" not in str(result["to"]):
        print(f"  ✅ PASS: Invalid pm_email skipped, fallback used: to={result['to']}")
    else:
        print(f"  ❌ FAIL: Invalid pm_email not properly skipped: to={result['to']}")
        all_passed = False
    
    # Should include valid co-PM but skip invalid one
    has_valid = "valid.copm@mascigc.com" in result["cc"]
    has_invalid = any("example.com" in email for email in result["cc"])
    
    if has_valid and not has_invalid:
        print(f"  ✅ PASS: Valid co-PM included, invalid skipped: cc={result['cc']}")
    else:
        print(f"  ❌ FAIL: Co-PM filtering incorrect: cc={result['cc']}")
        all_passed = False
    
    # Edge case 2: Empty project_doc
    print("\n  Edge Case 2: Empty project_doc (should use environment fallback)")
    result_empty = _select_governed_recipients(project_doc={})
    print(f"  Result with empty project_doc: to={result_empty['to']}, cc={result_empty['cc']}")
    print(f"  ✅ INFO: Empty project_doc handled (fallback behavior)")
    
    # Edge case 3: None project_doc
    print("\n  Edge Case 3: None project_doc (should use environment fallback)")
    result_none = _select_governed_recipients(project_doc=None)
    print(f"  Result with None project_doc: to={result_none['to']}, cc={result_none['cc']}")
    print(f"  ✅ INFO: None project_doc handled (fallback behavior)")
    
    return all_passed


def main():
    """Run all proof point tests."""
    print("=" * 80)
    print("GOVERNED CERTIFICATION LANE REPAIR - BACKEND TEST")
    print("=" * 80)
    
    results = {
        "Proof Point 1 (No example.com selected)": test_proof_point_1_placeholder_example_com_not_selected(),
        "Proof Point 2 (Correct recipients from live project)": test_proof_point_2_correct_recipients_from_live_project(),
        "Proof Point 3 (Normal non-cert unchanged)": test_proof_point_3_normal_non_certification_unchanged(),
        "Proof Point 4 (Focused tests pass)": test_proof_point_4_focused_tests_pass(),
        "Additional Edge Cases": test_additional_edge_cases(),
    }
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    if all_passed:
        print("✅ ALL PROOF POINTS VERIFIED - REPAIR IS WORKING CORRECTLY")
        return 0
    else:
        print("❌ SOME PROOF POINTS FAILED - REVIEW REQUIRED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
