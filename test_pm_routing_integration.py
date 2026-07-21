#!/usr/bin/env python3
"""
Integration test for pm_routing.py with governed certification lane routing_override.

Validates that pm_routing.py properly honors the routing_override from governed certification lane.
"""
import sys
sys.path.insert(0, "/app/backend")

import asyncio
from backend.tests.test_dr03_governed_certification_lane import _FakeDB
from pm_routing import recipients_for_record_async
from lib.governed_certification_lane import GOVERNED_CERTIFICATION_CO_PM_EMAILS


async def test_pm_routing_honors_governed_override():
    """Test that pm_routing.py honors routing_override from governed certification lane."""
    print("\n=== PM ROUTING INTEGRATION TEST ===")
    
    # Test case from test_dr03_governed_certification_lane.py line 130-150
    record = {
        "project_number": "ZZ-RUNTIME-CERT-2026",
        "routing_override": {
            "enabled": True,
            "pm_name": "Certification PM",
            "to": ["cert.pm@example.com"],
            "cc": GOVERNED_CERTIFICATION_CO_PM_EMAILS,
        },
    }
    
    dist = await recipients_for_record_async(_FakeDB(), record, kind="daily-report")
    
    all_passed = True
    
    # Validate pm_email
    if dist["pm_email"] == "cert.pm@example.com":
        print(f"  ✅ PASS: pm_email matches: {dist['pm_email']}")
    else:
        print(f"  ❌ FAIL: pm_email mismatch: {dist['pm_email']}")
        all_passed = False
    
    # Validate to
    if dist["to"] == ["cert.pm@example.com"]:
        print(f"  ✅ PASS: to matches: {dist['to']}")
    else:
        print(f"  ❌ FAIL: to mismatch: {dist['to']}")
        all_passed = False
    
    # Validate cc
    if dist["cc"] == GOVERNED_CERTIFICATION_CO_PM_EMAILS:
        print(f"  ✅ PASS: cc matches: {dist['cc']}")
    else:
        print(f"  ❌ FAIL: cc mismatch: {dist['cc']}")
        all_passed = False
    
    # Validate all
    expected_all = ["cert.pm@example.com", *GOVERNED_CERTIFICATION_CO_PM_EMAILS]
    if dist["all"] == expected_all:
        print(f"  ✅ PASS: all matches: {dist['all']}")
    else:
        print(f"  ❌ FAIL: all mismatch: {dist['all']}")
        all_passed = False
    
    return all_passed


async def test_pm_routing_with_valid_governed_override():
    """Test pm_routing with valid (non-placeholder) governed override."""
    print("\n=== PM ROUTING WITH VALID GOVERNED OVERRIDE ===")
    
    record = {
        "project_number": "ZZ-RUNTIME-CERT-2026",
        "routing_override": {
            "enabled": True,
            "pm_name": "Jaymn Judd",
            "pm_email": "jaymn.judd@mascigc.com",
            "to": ["jaymn.judd@mascigc.com"],
            "cc": ["david.jewett@mascigc.com"],
        },
    }
    
    dist = await recipients_for_record_async(_FakeDB(), record, kind="daily-report")
    
    all_passed = True
    
    # Validate no example.com in recipients
    has_example_com = any("example.com" in email for email in dist["all"])
    if not has_example_com:
        print(f"  ✅ PASS: No example.com in recipients: {dist['all']}")
    else:
        print(f"  ❌ FAIL: example.com found in recipients: {dist['all']}")
        all_passed = False
    
    # Validate valid recipients are present
    if "jaymn.judd@mascigc.com" in dist["to"]:
        print(f"  ✅ PASS: Valid PM in to: {dist['to']}")
    else:
        print(f"  ❌ FAIL: Valid PM NOT in to: {dist['to']}")
        all_passed = False
    
    if "david.jewett@mascigc.com" in dist["cc"]:
        print(f"  ✅ PASS: Valid co-PM in cc: {dist['cc']}")
    else:
        print(f"  ❌ FAIL: Valid co-PM NOT in cc: {dist['cc']}")
        all_passed = False
    
    return all_passed


async def main():
    """Run all integration tests."""
    print("=" * 80)
    print("PM ROUTING INTEGRATION TEST - GOVERNED CERTIFICATION LANE")
    print("=" * 80)
    
    results = {
        "PM Routing honors governed override": await test_pm_routing_honors_governed_override(),
        "PM Routing with valid governed override": await test_pm_routing_with_valid_governed_override(),
    }
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED")
        return 0
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
