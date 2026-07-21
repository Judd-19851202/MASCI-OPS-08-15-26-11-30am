from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from lib.canonical_truth import validate_truth_registry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def reconcile_shared_foundation(*, extra_findings: Optional[List[Dict]] = None) -> Dict:
    result = validate_truth_registry()
    findings = list(result.get("findings") or [])
    if extra_findings:
        findings.extend(extra_findings)
    p0_open = [f for f in findings if f.get("severity") == "P0" and f.get("blocking_status")]
    return {
        "executed_at": _now_iso(),
        "status": "PASS" if not p0_open else "FAIL",
        "finding_count": len(findings),
        "p0_open_count": len(p0_open),
        "findings": findings,
        "registry_summary": result.get("summary") or {},
    }


__all__ = ["reconcile_shared_foundation"]