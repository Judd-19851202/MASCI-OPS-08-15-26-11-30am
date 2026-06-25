"""TRACK 15.79C · P0 regression — schedule_auto_email task retention.

Locks the fix for the production incident where Daily Reports
submitted in production left ZERO audit rows AND ZERO Trust Spine
events. Root cause: ``asyncio.create_task()`` only keeps a WEAK
reference to the task; under load the GC could collect the pending
``_dispatch_auto_email`` coroutine before it executed.

These tests assert:
  1. ``schedule_auto_email`` retains a STRONG reference until done.
  2. The retained task completes (best-effort) without being GC'd
     even if the caller drops every other reference.
  3. The done-callback discards the task from the retention set on
     completion (no unbounded growth).
  4. Multiple concurrent dispatches all survive GC.
  5. The fix is byte-for-byte present in server.py — no future
     refactor can silently revert it.

Why these matter: every Daily Report, Meeting, Inspection, JHA,
Incident, Equipment Pre-Op, and QA/QC submission depends on
``schedule_auto_email`` to deliver the operational email. A
silently-disappearing background task is the worst possible failure
mode — operator sees a saved record, no error, no email, no log.
"""
from __future__ import annotations

import asyncio
import gc
from pathlib import Path

import pytest


SERVER_PY = Path("/app/backend/server.py")


# ── 1 · the strong-reference set exists + is named correctly ──────
def test_dispatch_retention_set_present_in_server_py():
    src = SERVER_PY.read_text()
    assert "_AUTO_EMAIL_DISPATCH_TASKS" in src, (
        "TRACK 15.79C fix removed: the strong-reference set "
        "`_AUTO_EMAIL_DISPATCH_TASKS` is missing from server.py — "
        "asyncio.create_task tasks will be GC'd mid-flight and "
        "Daily Report emails will silently disappear in production."
    )


# ── 2 · schedule_auto_email actually adds the task to the set ─────
def test_schedule_auto_email_retains_strong_reference():
    """Drop every external reference to the task — it should still be
    held by ``_AUTO_EMAIL_DISPATCH_TASKS`` until done."""
    import server as srv  # noqa: PLC0415

    async def _run():
        # Stub the dispatcher with a coroutine that we control so the
        # test does not actually touch Mongo or Resend.
        async def _stub_dispatcher(kind, record):
            await asyncio.sleep(0.05)
            record["_stub_ran"] = True

        original = srv._dispatch_auto_email
        srv._dispatch_auto_email = _stub_dispatcher  # type: ignore[assignment]
        try:
            srv._AUTO_EMAIL_DISPATCH_TASKS.clear()
            rec = {"id": "track1579c-strong-ref", "project_number": "X"}
            srv.schedule_auto_email("daily-report", rec)
            # 1 task retained
            assert len(srv._AUTO_EMAIL_DISPATCH_TASKS) == 1
            # Aggressively GC to prove the strong ref is what's
            # holding the task alive.
            gc.collect()
            assert len(srv._AUTO_EMAIL_DISPATCH_TASKS) == 1
            # Let it finish.
            while srv._AUTO_EMAIL_DISPATCH_TASKS:
                await asyncio.sleep(0.02)
            # Set is now empty (done-callback discarded it).
            assert len(srv._AUTO_EMAIL_DISPATCH_TASKS) == 0
        finally:
            srv._dispatch_auto_email = original  # type: ignore[assignment]

    asyncio.run(_run())


# ── 3 · multiple concurrent dispatches all survive GC ─────────────
def test_schedule_auto_email_handles_burst_without_loss():
    import server as srv  # noqa: PLC0415

    async def _run():
        done_ids: list = []

        async def _stub_dispatcher(kind, record):
            await asyncio.sleep(0.02)
            done_ids.append(record["id"])

        original = srv._dispatch_auto_email
        srv._dispatch_auto_email = _stub_dispatcher  # type: ignore[assignment]
        try:
            srv._AUTO_EMAIL_DISPATCH_TASKS.clear()
            # Submit 20 dispatches in a tight burst, then drop every
            # local reference and force GC.
            for i in range(20):
                srv.schedule_auto_email(
                    "daily-report",
                    {"id": f"burst-{i:02d}", "project_number": "BURST"},
                )
            gc.collect()
            # Wait for all to finish.
            for _ in range(200):
                if not srv._AUTO_EMAIL_DISPATCH_TASKS:
                    break
                await asyncio.sleep(0.02)
            assert len(done_ids) == 20, (
                f"only {len(done_ids)}/20 dispatches completed — "
                f"GC reclaimed pending tasks (TRACK 15.79C regression)"
            )
        finally:
            srv._dispatch_auto_email = original  # type: ignore[assignment]

    asyncio.run(_run())


# ── 4 · done-callback discards finished task (no unbounded growth) ─
def test_dispatch_retention_set_self_clears():
    import server as srv  # noqa: PLC0415

    async def _run():
        async def _stub_dispatcher(kind, record):
            return None  # finishes immediately

        original = srv._dispatch_auto_email
        srv._dispatch_auto_email = _stub_dispatcher  # type: ignore[assignment]
        try:
            srv._AUTO_EMAIL_DISPATCH_TASKS.clear()
            for i in range(5):
                srv.schedule_auto_email(
                    "daily-report", {"id": f"clear-{i}"}
                )
            # All should have completed and been removed.
            await asyncio.sleep(0.1)
            assert len(srv._AUTO_EMAIL_DISPATCH_TASKS) == 0
        finally:
            srv._dispatch_auto_email = original  # type: ignore[assignment]

    asyncio.run(_run())


# ── 5 · no-running-loop path stays silent (sync test compatibility) ─
def test_schedule_auto_email_no_running_loop_is_silent():
    """When called outside an async context, schedule_auto_email
    must not raise — sync test fixtures rely on this."""
    import server as srv  # noqa: PLC0415

    # Direct call from sync test scope: no running loop → must be a
    # silent no-op (no exception, no task registered).
    srv._AUTO_EMAIL_DISPATCH_TASKS.clear()
    srv.schedule_auto_email("daily-report", {"id": "no-loop"})
    assert len(srv._AUTO_EMAIL_DISPATCH_TASKS) == 0


# ── 6 · _wl render path still locked (companion regression check) ──
def test_render_email_html_no_wl_regression():
    """Track 15.76 fixed the original ``_wl`` NameError. This test
    pins the fix in place during the 15.79C audit so a future refactor
    cannot accidentally regress it while editing nearby code."""
    from pdf_render import render_email_html  # noqa: PLC0415
    for kind in (
        "daily-report", "meeting", "inspection", "incident",
        "jha", "qaqc", "equipment-inspection", "dvir",
    ):
        html = render_email_html(
            kind,
            {"id": f"15.79c-{kind}", "project_number": "20-07",
             "project_name": "Test", "report_date": "2026-06-25"},
            note="Routine.",
        )
        assert html and isinstance(html, str)


# ── 7 · server.py source contract — the create_task line is wrapped ─
def test_create_task_line_keeps_reference():
    """Lock the exact byte sequence so the strong-reference pattern
    cannot be silently removed by a future refactor."""
    src = SERVER_PY.read_text()
    assert "task = asyncio.create_task(_dispatch_auto_email" in src
    assert "_AUTO_EMAIL_DISPATCH_TASKS.add(task)" in src
    assert "task.add_done_callback(_AUTO_EMAIL_DISPATCH_TASKS.discard)" in src
