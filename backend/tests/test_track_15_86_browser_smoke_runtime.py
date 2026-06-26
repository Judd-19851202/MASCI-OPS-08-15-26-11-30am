"""TRACK 15.86 · Browser smoke runtime probe.

This file invokes the actual headless Playwright runner in
``--gate`` mode. It is **skipped by default** because:

  * The deployment gate cycle must remain fast and 100 % deterministic.
  * Not every contributor's machine has chromium installed.
  * The static meta-gate in
    ``test_track_15_86_browser_smoke_gate.py`` already locks the
    runner's *shape* and is wired into the deployment gate.

To run this probe (locally or in a nightly CI tier), set::

    MASCI_SMOKE_BROWSER=1 pytest \
      backend/tests/test_track_15_86_browser_smoke_runtime.py -v

The probe is also auto-enabled when ``MASCI_SMOKE_BROWSER`` is
unset but a chromium binary is detected in the default Playwright
cache (``/root/.cache/ms-playwright``) — except in the pytest
``deployment_gate.py`` runner, which sets ``MASCI_SMOKE_BROWSER=0``
explicitly to keep the gate fast.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

RUNNER_PATH = Path(
    "/app/backend/tests/browser_smoke/run_browser_smoke.py"
)


def _chromium_headless_shell_available() -> bool:
    """Detect a chromium / chromium_headless_shell binary in the
    default Playwright cache."""
    candidates = [
        Path("/root/.cache/ms-playwright"),
        Path("/pw-browsers"),
        Path(os.path.expanduser("~/.cache/ms-playwright")),
    ]
    for root in candidates:
        if not root.exists():
            continue
        for sub in root.iterdir():
            name = sub.name.lower()
            if "chromium" in name or "headless_shell" in name:
                return True
    # Fallback: ``playwright`` CLI on PATH at least indicates the SDK
    # is installed even if browsers aren't.
    return False


def _should_run() -> bool:
    explicit = os.environ.get("MASCI_SMOKE_BROWSER")
    if explicit is not None:
        return explicit not in ("0", "false", "False", "")
    return _chromium_headless_shell_available()


@pytest.mark.skipif(not _should_run(),
                    reason="Track 15.86 runtime probe is opt-in. Set "
                           "MASCI_SMOKE_BROWSER=1 to enable.")
def test_browser_smoke_gate_passes_on_preview_environment():
    """Invokes the runner's ``run()`` entry point in the lightweight
    ``--gate`` mode (3 routes × 3 viewports = 9 checks)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "track_15_86_browser_smoke_runner", str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["track_15_86_browser_smoke_runner"] = module
    spec.loader.exec_module(module)

    exit_code = module.run(extended=False, json_out=False)
    assert exit_code == 0, (
        "Track 15.86 runtime probe FAILED — see the runner's human "
        "output above for the (route × viewport) breakdown."
    )
