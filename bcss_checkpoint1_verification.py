#!/usr/bin/env python3
"""
BCSS Checkpoint 1 Verification Script
Verifies canonical_truth_registry() contains 10 bcss_* surfaces
and validate_truth_registry() has zero BCSS-scoped findings.
"""

import sys
sys.path.insert(0, '/app/backend')

from lib.canonical_truth import canonical_truth_registry, validate_truth_registry

def main():
    print("=" * 80)
    print("BCSS CHECKPOINT 1 VERIFICATION")
    print("=" * 80)
    
    # 1. Get the registry
    registry = canonical_truth_registry()
    
    # 2. Filter BCSS surfaces
    bcss_surfaces = {k: v for k, v in registry.items() if k.startswith("bcss_")}
    
    print(f"\n1. BCSS SURFACES COUNT: {len(bcss_surfaces)}")
    print(f"   Expected: 10")
    print(f"   Result: {'✅ PASS' if len(bcss_surfaces) == 10 else '❌ FAIL'}")
    
    # 3. List all BCSS surfaces
    print(f"\n2. BCSS SURFACES REGISTERED:")
    for i, (surface_id, surface) in enumerate(sorted(bcss_surfaces.items()), 1):
        print(f"   {i:2d}. {surface_id}")
        print(f"       - truth_subject: {surface['truth_subject']}")
        print(f"       - role: {surface['role']}")
        print(f"       - owner_endpoint: {surface['owner_endpoint']}")
        print(f"       - owner_module: {surface['owner_module']}")
    
    # 4. Validate registry
    validation = validate_truth_registry()
    
    # 5. Filter BCSS-scoped findings
    bcss_findings = [
        f for f in validation["findings"]
        if str(f.get("surface_id", "")).startswith("bcss_")
        or str(f.get("subject", "")).startswith("bcss_")
    ]
    
    print(f"\n3. BCSS-SCOPED VALIDATION FINDINGS: {len(bcss_findings)}")
    print(f"   Expected: 0")
    print(f"   Result: {'✅ PASS' if len(bcss_findings) == 0 else '❌ FAIL'}")
    
    if bcss_findings:
        print("\n   FINDINGS DETAILS:")
        for finding in bcss_findings:
            print(f"   - {finding['finding_type']}: {finding['surface_id']}")
            print(f"     Severity: {finding['severity']}")
            print(f"     Evidence: {finding['evidence']}")
    
    # 6. Overall validation summary
    print(f"\n4. OVERALL VALIDATION SUMMARY:")
    print(f"   - Total surfaces in registry: {validation['summary']['surface_count']}")
    print(f"   - Registered surfaces: {validation['summary']['registered_surface_count']}")
    print(f"   - Total findings: {validation['summary']['finding_count']}")
    print(f"   - P0 open count: {validation['summary']['p0_open_count']}")
    print(f"   - Owner conflicts: {validation['summary']['owner_conflicts']}")
    print(f"   - Duplicate derivations: {validation['summary']['duplicate_derivations']}")
    
    # 7. Role counts
    print(f"\n5. ROLE COUNTS:")
    for role, count in validation['role_counts'].items():
        print(f"   - {role}: {count}")
    
    # 8. Final verdict
    print("\n" + "=" * 80)
    if len(bcss_surfaces) == 10 and len(bcss_findings) == 0:
        print("✅ BCSS CHECKPOINT 1 VERIFICATION: PASS")
        print("   - All 10 BCSS surfaces are registered")
        print("   - Zero BCSS-scoped validation findings")
        print("   - No runtime breakage detected")
        return 0
    else:
        print("❌ BCSS CHECKPOINT 1 VERIFICATION: FAIL")
        if len(bcss_surfaces) != 10:
            print(f"   - Expected 10 BCSS surfaces, found {len(bcss_surfaces)}")
        if len(bcss_findings) > 0:
            print(f"   - Found {len(bcss_findings)} BCSS-scoped validation findings")
        return 1
    print("=" * 80)

if __name__ == "__main__":
    sys.exit(main())
