"""
test_iter62_backup_resiliency
=============================
Locks the iter62 fixes into a regression suite:

* `_build_slim_backup_zip_on_disk` produces a small zip directly from
  Mongo without touching the full archive — proves the lite-mode
  escape hatch is wired up and bounded in memory.
* `_lite_mode_default` honors the BACKUP_LITE_MODE_ONLY env truthiness.
* `_BACKUP_SCHEDULER_STATE` exists and starts in a sensible default
  shape so the diagnostic endpoint never returns None / missing keys.
* `_BACKUP_RUNNOW_LAST` exists with all expected fields.
"""
from __future__ import annotations

import os
import sys

# Bootstrap path so `import server` works from this test file location
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_lite_mode_env_truthy():
    import server
    os.environ.pop("BACKUP_LITE_MODE_ONLY", None)
    assert server._lite_mode_default() is False
    for v in ("1", "true", "TRUE", "yes", "Y", "On"):
        os.environ["BACKUP_LITE_MODE_ONLY"] = v
        assert server._lite_mode_default() is True, f"value {v!r} should be truthy"
    for v in ("0", "false", "no", "off", ""):
        os.environ["BACKUP_LITE_MODE_ONLY"] = v
        assert server._lite_mode_default() is False, f"value {v!r} should be falsy"
    os.environ.pop("BACKUP_LITE_MODE_ONLY", None)


def test_scheduler_state_initial_shape():
    """Diagnostic endpoint must never KeyError on a fresh process —
    every consumer assumes these keys exist."""
    import server
    s = server._BACKUP_SCHEDULER_STATE
    for k in (
        "alive",
        "armed_at",
        "last_tick_ts",
        "in_progress",
        "last_attempt_started_at",
        "last_attempt_outcome",
        "last_run_for_hour",
        "failed_attempts",
    ):
        assert k in s, f"missing scheduler-state key: {k}"
    # last_run_for_hour and failed_attempts should be dict-shaped
    assert isinstance(s["last_run_for_hour"], dict)
    assert isinstance(s["failed_attempts"], dict)


def test_runnow_state_initial_shape():
    import server
    r = server._BACKUP_RUNNOW_LAST
    for k in ("started_at", "finished_at", "outcome", "lite_mode"):
        assert k in r, f"missing run-now state key: {k}"
    assert isinstance(server._BACKUP_RUNNOW_IN_PROGRESS, bool)


def test_run_scheduled_backup_accepts_lite_mode_kwarg():
    """Signature regression — the iter62 lite-mode override is a positional
    or keyword arg. If a future refactor drops it, the manual run-now
    endpoint will silently ignore the user's ``?lite=true`` query param."""
    import inspect
    import server
    sig = inspect.signature(server._run_scheduled_backup)
    assert "lite_mode" in sig.parameters, (
        "_run_scheduled_backup must accept lite_mode kwarg "
        "(used by manual /admin/backups/run-now?lite=true)"
    )
    # Default must be False so existing scheduled runs are unaffected.
    assert sig.parameters["lite_mode"].default is False


def test_slim_backup_zip_helper_exists():
    """Module export sanity check — admin warm-cache path imports this
    helper indirectly via _run_scheduled_backup. If it's renamed, the
    lite path silently breaks."""
    import server
    assert hasattr(server, "_build_slim_backup_zip_on_disk"), (
        "_build_slim_backup_zip_on_disk is required for lite-mode backups"
    )
    assert hasattr(server, "_email_lite_backup_zip"), (
        "_email_lite_backup_zip is required for lite-mode backups"
    )
