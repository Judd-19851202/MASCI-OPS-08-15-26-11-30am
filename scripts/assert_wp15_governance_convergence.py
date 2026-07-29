#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: assert_wp15_governance_convergence.py <scan-json-path>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ Scan file not found: {path}")
        return 2

    data = json.loads(path.read_text())
    legacy = int(data.get("legacy_but_migratable") or 0)
    candidates = int(data.get("governance_candidate_manual_review") or 0)
    manual_headers = int(data.get("manual_auth_header_construction") or 0)
    special_cases = int(data.get("special_case_infrastructure") or 0)
    findings = data.get("constitutional_decision_points") or []
    failing_findings = [
        row for row in findings
        if row.get("category") in {"legacy_migratable", "governance_candidate"}
        or row.get("reason") == "Manual governed-request header construction"
    ]

    print("WP15 Governance Convergence Gate")
    print(f"- scan_timestamp: {data.get('scan_timestamp')}")
    print(f"- legacy_but_migratable: {legacy}")
    print(f"- governance_candidate_manual_review: {candidates}")
    print(f"- manual_auth_header_construction: {manual_headers}")
    print(f"- special_case_infrastructure: {special_cases} (informational)")

    if legacy == 0 and candidates == 0 and manual_headers == 0:
        print("✅ Governance convergence gate passed.")
        return 0

    print("❌ Governance convergence gate failed. Exact findings:")
    for row in failing_findings[:25]:
        print(
            "  - "
            f"category={row.get('category')} "
            f"reason={row.get('reason')} "
            f"path={row.get('path')}"
        )
    if len(failing_findings) > 25:
        print(f"  … {len(failing_findings) - 25} more finding(s) omitted")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())