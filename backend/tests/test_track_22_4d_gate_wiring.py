"""TRACK 22.4D · Mobile Regression Gate wiring lock.

Static regression that certifies the Track 22.4c Playwright mobile
responsiveness suite is included in the canonical deployment gate's
`REGRESSION_FILES` list, so any future mobile-layout regression blocks
production deploy.

Also locks that the Track 22.4b-followup family (idempotency, safety
lifecycle, DR / HR identity drift, driver certification) is present in
the gate — so a future refactor cannot silently drop them from the
gate list.
"""
from __future__ import annotations

import importlib.util
import os

import pytest


GATE_PATH = "/app/scripts/deployment_gate.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("deployment_gate", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_deployment_gate_module_loads():
    """Deployment gate script must remain a runnable Python module."""
    mod = _load_gate_module()
    assert hasattr(mod, "REGRESSION_FILES"), "REGRESSION_FILES missing"
    assert isinstance(mod.REGRESSION_FILES, list)
    assert len(mod.REGRESSION_FILES) > 0


def test_track_22_4c_mobile_sweep_in_gate():
    """Track 22.4c Playwright mobile sweep MUST be in the gate list."""
    mod = _load_gate_module()
    needle = (
        "/app/backend/tests/test_track_22_4c_mobile_responsiveness_sweep.py"
    )
    assert needle in mod.REGRESSION_FILES, (
        "Track 22.4c Playwright mobile responsiveness suite must be "
        "wired into `REGRESSION_FILES` in deployment_gate.py. Without "
        "it, mobile layout regressions do not block deploy."
    )
    # File must exist on disk too (dropped-file regression).
    assert os.path.exists(needle), f"gate references missing file: {needle}"


@pytest.mark.parametrize("suffix", [
    "test_track_22_4b_followup_safety_seam.py",
    "test_track_22_4b_followup_safety_b02.py",
    "test_track_22_4b_followup_safety_b04.py",
    "test_track_22_4b_followup_dr_b03.py",
    "test_track_22_4b_followup_idempotency_spine.py",
    "test_track_22_4b_followup_idempotency_spine_phase_2.py",
    "test_track_22_4b_followup_dispatch_idempotency.py",
    "test_track_22_4b_followup_hr.py",
    "test_track_22_4b_followup_trench_writes_idempotency.py",
    "test_track_22_4b_followup_shop_defects_idempotency.py",
    "test_track_22_4b_followup_driver.py",
])
def test_track_22_4b_followup_family_in_gate(suffix):
    """Every Track 22.4b-followup regression file must be gate-wired."""
    mod = _load_gate_module()
    full = f"/app/backend/tests/{suffix}"
    assert full in mod.REGRESSION_FILES, (
        f"{suffix} must be in the deployment gate's REGRESSION_FILES "
        f"so future refactors cannot silently drop it."
    )
    assert os.path.exists(full), f"gate references missing file: {full}"


def test_gate_timeout_accommodates_mobile_sweep():
    """Per-test timeout must be ≥60s so the mobile Playwright suite
    (which round-trips a real browser per assertion) never gets
    prematurely killed by pytest-timeout.
    """
    mod = _load_gate_module()
    src = open(GATE_PATH).read()
    # Look for the `--timeout` argument to pytest inside run_regression().
    import re
    m = re.search(r'"--timeout",\s*"(\d+)"', src)
    assert m, "deployment_gate.py must call pytest with --timeout"
    per_test_timeout = int(m.group(1))
    assert per_test_timeout >= 60, (
        f"per-test timeout ({per_test_timeout}s) is too aggressive for "
        f"Playwright mobile assertions. Bump to at least 60s."
    )


def test_gate_subprocess_timeout_accommodates_mobile_sweep():
    """Subprocess-level timeout must be ≥900s so 77 Playwright mobile
    assertions do not force a spurious deploy-block on cold-start."""
    src = open(GATE_PATH).read()
    import re
    # Match `timeout=NNN,` inside subprocess.run() calls (allow multiline).
    matches = [int(x) for x in re.findall(r"timeout\s*=\s*(\d{3,5})\s*,", src)]
    assert matches, "deployment_gate.py subprocess.run must specify timeout"
    assert max(matches) >= 900, (
        f"subprocess timeouts {matches} are all below 900s — mobile "
        f"sweep runtime (~250s worst-case) leaves too little headroom."
    )
