"""TRACK 15.73 SLICE 1 · Equipment Resolver — pytest gate.

Wraps the live regression script as a pytest module so CI can block any
future change that re-introduces equipment identity drift.
"""
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "track_15_73_slice1_resolver_regression.py"


def test_equipment_resolver_regression_passes():
    assert SCRIPT.exists(), f"Resolver regression script missing: {SCRIPT}"
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, timeout=300, env=env,
    )
    assert proc.returncode == 0, (
        "Slice 1 equipment resolver regression FAILED.\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    assert "OVERALL: PASS" in proc.stdout, "Expected PASS marker not found in regression output."
