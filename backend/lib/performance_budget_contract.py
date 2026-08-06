from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict

from lib.release_gate_governance import load_release_gate_manifest


def read_performance_budget_contract(repo_root: Path = Path("/app")) -> Dict[str, Any]:
    manifest = load_release_gate_manifest()
    perf = manifest.get("performance_prerequisites") or {}
    rel_path = str(perf.get("performance_budget_register") or "memory/WP18DA_PERFORMANCE_BUDGET_REGISTER.csv")
    path = repo_root / rel_path
    payload: Dict[str, Any] = {
        "ok": False,
        "path": str(path),
        "exists": path.exists(),
        "required_budget_keys": list(perf.get("required_budget_keys") or []),
    }
    if not path.exists():
        payload["summary"] = "Performance budget register is missing."
        return payload
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:  # pragma: no cover
        return {
            **payload,
            "summary": "Performance budget register could not be parsed.",
            "error": type(exc).__name__,
        }

    required_keys = list(perf.get("required_budget_keys") or [])
    rows_by_key = {
        str((row or {}).get("budget_key") or "").strip(): row
        for row in rows
        if str((row or {}).get("budget_key") or "").strip()
    }
    missing_keys = [key for key in required_keys if key not in rows_by_key]
    failing_rows = []
    for key, row in rows_by_key.items():
        status = str((row or {}).get("status") or "").strip().upper()
        if status != "PASS":
            failing_rows.append(
                {
                    "budget_key": key,
                    "status": status or "MISSING",
                    "measured": row.get("measured"),
                    "target": row.get("target"),
                }
            )
    payload.update(
        {
            "ok": not missing_keys and not failing_rows,
            "row_count": len(rows),
            "pass_count": sum(1 for row in rows if str((row or {}).get("status") or "").strip().upper() == "PASS"),
            "missing_keys": missing_keys,
            "failing_rows": failing_rows,
            "summary": (
                "Performance budget contract is currently satisfied."
                if not missing_keys and not failing_rows
                else "Performance budget contract is currently blocking release."
            ),
        }
    )
    return payload


__all__ = ["read_performance_budget_contract"]