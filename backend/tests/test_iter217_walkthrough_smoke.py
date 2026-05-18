"""iter217 · Walkthrough framework structural smoke test.

NOT a functional test of every persona — those are intentionally
runnable as standalone scripts (see /app/walkthroughs/README.md).
This file verifies the framework's structural invariants so that
breakage in the runner is caught before the next walkthrough pass.

To run an actual walkthrough:
    PLAYWRIGHT_BROWSERS_PATH=/pw-browsers python /app/walkthroughs/foreman.py
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

WALKTHROUGHS_DIR = Path("/app/walkthroughs")
sys.path.insert(0, str(WALKTHROUGHS_DIR))

PRIORITY_PERSONAS = [
    "foreman",
    "superintendent",
    "operator",
    "dispatcher",
    "hr",
    "safety",
    "pm",
    "laborer",
]


def test_walkthrough_runner_importable():
    """The shared runner module must import cleanly without side
    effects (it's imported at the top of every persona script)."""
    spec = importlib.util.spec_from_file_location(
        "_runner", WALKTHROUGHS_DIR / "_runner.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "Walkthrough")
    assert hasattr(mod, "run")
    assert hasattr(mod, "FIND_HELPTIPS_JS")
    assert hasattr(mod, "EXPAND_HELPTIPS_JS")


def test_finding_kinds_vocabulary_is_stable():
    """The finding vocabulary is operator-load-bearing — drift here
    means the editorial backlog stops being legible."""
    from _runner import FINDING_KINDS  # noqa: E402
    required = {
        "friction",
        "missing-coaching",
        "weak-tip",
        "unclear-wording",
        "discoverability-gap",
        "mobile-clipping",
        "workflow-confusion",
        "no-escalation-path",
        "voice-drift",
        "positive-observation",
    }
    assert FINDING_KINDS == required, (
        f"Finding-kind vocabulary drifted. "
        f"Added: {FINDING_KINDS - required}, "
        f"Removed: {required - FINDING_KINDS}"
    )


@pytest.mark.parametrize("persona", PRIORITY_PERSONAS)
def test_persona_script_exists(persona):
    """Every operator-priority persona must have a runnable script."""
    path = WALKTHROUGHS_DIR / f"{persona}.py"
    assert path.exists(), f"missing walkthrough: {path}"
    src = path.read_text()
    # Each script must define the canonical `<persona>_day(page, wt)` fn.
    assert f"def {persona}_day" in src, (
        f"{persona}.py must define a `{persona}_day(page, wt)` function"
    )
    # Each script must invoke run(...) when executed as __main__.
    assert "if __name__ ==" in src and "run(" in src, (
        f"{persona}.py must invoke run(...) when executed"
    )


def test_walkthrough_class_construction():
    """Walkthrough() constructs cleanly and validates persona slugs."""
    from _runner import Walkthrough  # noqa: E402

    wt = Walkthrough("test-persona", {"width": 414, "height": 896})
    assert wt.persona == "test-persona"
    assert wt.shots_dir.exists()

    # Invalid slugs must be rejected so report-file paths stay safe.
    with pytest.raises(ValueError):
        Walkthrough("Invalid Persona!", {"width": 1, "height": 1})


def test_finding_kind_validation():
    """note() must reject unknown finding kinds at write time."""
    from _runner import Walkthrough  # noqa: E402
    wt = Walkthrough("test-validation", {"width": 1, "height": 1})
    wt.begin_step("01-test", "test step")
    wt.note("friction", "ok", "ok")  # valid kind passes
    with pytest.raises(ValueError):
        wt.note("not-a-real-kind", "x", "x")


def test_aggregator_importable():
    """aggregate_findings must be importable and expose collect()."""
    spec = importlib.util.spec_from_file_location(
        "aggregate_findings", WALKTHROUGHS_DIR / "aggregate_findings.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "collect"), "aggregate_findings.collect() missing"
    backlog = mod.collect()
    assert "actionable_in_priority_order" in backlog
    assert "overall_tally" in backlog


def test_persona_priority_order_matches_operator_directive():
    """The aggregator's PRIORITY_ORDER MUST match the operator's
    explicit ordering directive (foreman → super → operator → dispatcher
    → HR → safety → PM → laborer)."""
    spec = importlib.util.spec_from_file_location(
        "aggregate_findings", WALKTHROUGHS_DIR / "aggregate_findings.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.PRIORITY_ORDER == PRIORITY_PERSONAS, (
        "Persona priority order drifted from the operator's "
        "iter217 directive."
    )


@pytest.mark.skipif(
    os.environ.get("RUN_WALKTHROUGHS") != "1",
    reason="Set RUN_WALKTHROUGHS=1 to actually drive Playwright in CI",
)
def test_foreman_walkthrough_runs():
    """Optional smoke run of the foreman walkthrough — only fires in
    full CI mode. Default test sweep stays fast."""
    import subprocess
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": "/pw-browsers"}
    proc = subprocess.run(
        ["python", str(WALKTHROUGHS_DIR / "foreman.py")],
        capture_output=True, env=env, timeout=180,
    )
    assert proc.returncode == 0, (
        f"foreman walkthrough crashed: {proc.stderr.decode()[-500:]}"
    )
    backlog_path = Path("/app/walkthrough_reports/foreman_findings.json")
    assert backlog_path.exists()
