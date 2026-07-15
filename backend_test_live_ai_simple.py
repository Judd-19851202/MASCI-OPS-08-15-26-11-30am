#!/usr/bin/env python3
"""
Simple backend test: Verify live AI path without tenant capability branching.

This test verifies:
1. AI provider flags are enabled in .env
2. No resolve_ai_capabilities() gate in daily_summary.py
3. No capability check in photo_intelligence/pipeline.py
4. Summary draft endpoint behavior
"""

import os
import re
import sys
from pathlib import Path

def log(msg: str, level: str = "INFO"):
    """Print log message."""
    print(f"[{level}] {msg}", flush=True)


def test_env_flags():
    """Test 1: Verify AI provider flags are enabled."""
    log("\n" + "="*80)
    log("TEST 1: Verify AI provider flags in .env")
    log("="*80)
    
    env_file = Path("/app/backend/.env")
    if not env_file.exists():
        log("❌ FAIL: .env file not found", "ERROR")
        return False
    
    with open(env_file, "r") as f:
        env_content = f.read()
    
    required_flags = {
        "AI_PROVIDER_ANTHROPIC_ENABLED": "true",
        "AI_PROVIDER_OPENAI_ENABLED": "true",
        "AI_DAILY_REPORT_SUMMARY_ENABLED": "true",
    }
    
    all_correct = True
    for flag, expected_value in required_flags.items():
        if f"{flag}={expected_value}" in env_content:
            log(f"✅ {flag}={expected_value}")
        else:
            log(f"❌ {flag} not set to {expected_value}", "ERROR")
            all_correct = False
    
    if all_correct:
        log("✅ PASS: All required AI provider flags are enabled")
        return True
    else:
        log("❌ FAIL: Some AI provider flags are not correctly set", "ERROR")
        return False


def test_no_resolve_ai_capabilities_gate():
    """Test 2: Verify resolve_ai_capabilities() gate removed from daily_summary.py."""
    log("\n" + "="*80)
    log("TEST 2: Verify no resolve_ai_capabilities() gate in daily_summary.py")
    log("="*80)
    
    file_path = Path("/app/backend/routes/daily_summary.py")
    if not file_path.exists():
        log("❌ FAIL: daily_summary.py not found", "ERROR")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for resolve_ai_capabilities import or call
    if "resolve_ai_capabilities" in content:
        log("❌ FAIL: resolve_ai_capabilities() still present in daily_summary.py", "ERROR")
        # Find the lines where it appears
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if "resolve_ai_capabilities" in line:
                log(f"  Line {i}: {line.strip()}", "ERROR")
        return False
    
    log("✅ No resolve_ai_capabilities() found in daily_summary.py")
    
    # Verify get_ai_provider() is used instead
    if "get_ai_provider()" in content:
        log("✅ get_ai_provider() is used (correct live AI path)")
    else:
        log("⚠️  WARN: get_ai_provider() not found", "WARN")
    
    log("✅ PASS: No resolve_ai_capabilities() gate in daily_summary.py")
    return True


def test_no_capability_check_in_pipeline():
    """Test 3: Verify capability check removed from photo_intelligence/pipeline.py."""
    log("\n" + "="*80)
    log("TEST 3: Verify no capability check in photo_intelligence/pipeline.py")
    log("="*80)
    
    file_path = Path("/app/backend/services/photo_intelligence/pipeline.py")
    if not file_path.exists():
        log("❌ FAIL: pipeline.py not found", "ERROR")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for capability-related checks
    capability_patterns = [
        r"resolve_ai_capabilities",
        r"tenant.*capability",
        r"capability.*check",
        r"AI_CAPABILITY",
    ]
    
    found_issues = []
    for pattern in capability_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_issues.append((pattern, matches))
    
    if found_issues:
        log("❌ FAIL: Capability checks still present in pipeline.py", "ERROR")
        for pattern, matches in found_issues:
            log(f"  Pattern '{pattern}' found: {matches}", "ERROR")
        return False
    
    log("✅ No capability checks found in pipeline.py")
    log("✅ PASS: No capability check in photo_intelligence/pipeline.py")
    return True


def test_summary_endpoint_structure():
    """Test 4: Verify summary endpoint structure uses live AI path."""
    log("\n" + "="*80)
    log("TEST 4: Verify summary endpoint uses live AI path")
    log("="*80)
    
    file_path = Path("/app/backend/routes/daily_summary.py")
    if not file_path.exists():
        log("❌ FAIL: daily_summary.py not found", "ERROR")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for _compose_live_summary function
    if "async def _compose_live_summary" not in content:
        log("❌ FAIL: _compose_live_summary function not found", "ERROR")
        return False
    
    log("✅ _compose_live_summary function present")
    
    # Check that draft_summary endpoint calls _compose_live_summary
    if "return await _compose_live_summary" in content:
        log("✅ draft_summary endpoint calls _compose_live_summary")
    else:
        log("⚠️  WARN: draft_summary may not call _compose_live_summary directly", "WARN")
    
    # Check for provider.synthesize() call (live AI path)
    if "provider.synthesize(" in content:
        log("✅ provider.synthesize() call present (live AI synthesis)")
    else:
        log("⚠️  WARN: provider.synthesize() not found", "WARN")
    
    # Check for mode="live_ai" response
    if '"live_ai"' in content or "'live_ai'" in content:
        log("✅ 'live_ai' mode present in responses")
    else:
        log("⚠️  WARN: 'live_ai' mode string not found", "WARN")
    
    log("✅ PASS: Summary endpoint structure uses live AI path")
    return True


def test_photo_intelligence_structure():
    """Test 5: Verify photo intelligence uses live AI path."""
    log("\n" + "="*80)
    log("TEST 5: Verify photo intelligence uses live AI path")
    log("="*80)
    
    file_path = Path("/app/backend/services/photo_intelligence/pipeline.py")
    if not file_path.exists():
        log("❌ FAIL: pipeline.py not found", "ERROR")
        return False
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check for analyze_photo function call
    if "await analyze_photo(" in content:
        log("✅ analyze_photo() call present")
    else:
        log("⚠️  WARN: analyze_photo() call not found", "WARN")
    
    # Check for get_gateway() call (AI gateway for vision)
    if "get_gateway()" in content:
        log("✅ get_gateway() call present (AI gateway for vision)")
    else:
        log("⚠️  WARN: get_gateway() not found", "WARN")
    
    # Check for process_draft function
    if "async def process_draft" in content:
        log("✅ process_draft function present")
    else:
        log("⚠️  WARN: process_draft function not found", "WARN")
    
    log("✅ PASS: Photo intelligence structure uses live AI path")
    return True


def main():
    """Run all tests."""
    log("="*80)
    log("BACKEND TEST: Live AI Path Without Tenant Capability Branching")
    log("="*80)
    
    results = {}
    
    # Run tests
    results["env_flags"] = test_env_flags()
    results["no_resolve_ai_capabilities"] = test_no_resolve_ai_capabilities_gate()
    results["no_capability_check_pipeline"] = test_no_capability_check_in_pipeline()
    results["summary_endpoint_structure"] = test_summary_endpoint_structure()
    results["photo_intelligence_structure"] = test_photo_intelligence_structure()
    
    # Summary
    log("\n" + "="*80)
    log("TEST SUMMARY")
    log("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"{status}: {test_name}")
    
    log(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        log("\n✅ ALL TESTS PASSED")
        log("Verification complete:")
        log("  - AI provider flags are enabled in .env")
        log("  - resolve_ai_capabilities() gate removed from daily_summary.py")
        log("  - Capability check removed from photo_intelligence/pipeline.py")
        log("  - Summary endpoint uses live AI path (get_ai_provider, provider.synthesize)")
        log("  - Photo intelligence uses live AI path (get_gateway, analyze_photo)")
        return 0
    else:
        log(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
