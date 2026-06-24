"""TRACK 15.73 SLICE 2 · Attendee Identity Normalization — pytest gate.

Wraps the live 7-case regression script as a pytest module.
"""
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "track_15_73_slice2_attendee_identity_regression.py"


def test_attendee_identity_regression_passes():
    assert SCRIPT.exists(), f"Identity regression script missing: {SCRIPT}"
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, timeout=300, env=env,
    )
    assert proc.returncode == 0, (
        "Slice 2 attendee identity regression FAILED.\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    assert "Overall: PASS" in proc.stdout, "Expected PASS marker missing."
