#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
FAIL_REGISTER = REPO_ROOT / "memory" / "WP18_OPERATOR_LANGUAGE_HARD_FAIL_REGISTER.csv"


def _run_gate() -> dict:
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "operator_language_gate.py"), "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    payload = {}
    stdout = (completed.stdout or "").strip()
    if stdout:
        payload = json.loads(stdout)
    fail_rows = 0
    if FAIL_REGISTER.exists():
        with FAIL_REGISTER.open(newline="", encoding="utf-8") as handle:
            fail_rows = sum(1 for row in csv.DictReader(handle) if str(row.get("status") or "").upper() == "FAIL")
    return {
        "returncode": completed.returncode,
        "operator_facing_banned_findings": payload.get("operator_facing_banned_findings"),
        "technical_admin_exceptions": payload.get("technical_admin_exceptions"),
        "scanned_files": payload.get("scanned_files"),
        "csv_path": str(FAIL_REGISTER),
        "fail_rows": fail_rows,
    }


def main() -> int:
    result = _run_gate()
    ok = result["returncode"] == 0 and result["fail_rows"] == 0 and int(result.get("operator_facing_banned_findings") or 0) == 0
    print(json.dumps({**result, "decision": "pass" if ok else "fail"}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())