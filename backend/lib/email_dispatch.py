"""Email dispatch subsystem — extracted from server.py in Track 22.1B.

Contains the SAFE, self-contained pieces of the auto-email dispatcher:

- `_KIND_TO_COLLECTION` map (const)
- `_filename_for(kind, record)` — pure helper
- `_is_severe_incident(record)` — pure helper
- `_AUTO_EMAIL_DISPATCH_TASKS` — module-level strong-ref set (Track 15.79C)
- `schedule_auto_email(kind, record)` — fire-and-forget launcher
- `register_dispatcher(fn)` — indirection hook that lets server.py wire its
  large 473-line `_dispatch_auto_email` into `schedule_auto_email` without
  creating an import cycle.

WHAT WAS NOT MOVED (deliberate — Zero-Drift protection):

`_dispatch_auto_email` itself stays inline in `backend/server.py`. It
closes over ~8 server.py module-locals (`db`, `logger`, `_resolve_sender_email`,
`_resolve_reply_to_email`, `render_record_pdf`, `_maybe_enrich_for_pdf`,
`build_email_subject`, `render_email_html`, `_email_b64`). Extracting the
body would require either lazy back-imports (an import cycle) or a wide
dependency-injection factory that alters the closure mechanism. Both add
risk. The dispatcher is life-safety code — its body remains byte-identical
where it lives.

SDK IMPORT ORDER (safety-critical):

This module does NOT `import resend` at module scope. The Resend SDK
kill switch installed by `server.py` at line ~105 must remain installed
before any code obtains `resend.Emails.send`. Because this module imports
only stdlib + FastAPI, its import order relative to the SDK patch is
irrelevant. See `TRACK_22_1B_EMAIL_SAFETY.md` for the certification.

REGISTER PATTERN:

server.py imports `schedule_auto_email` from this module and, after
defining its `_dispatch_auto_email`, calls
`register_dispatcher(_dispatch_auto_email)`. From that moment onwards
every `schedule_auto_email(kind, record)` calls the registered
dispatcher via a strong-referenced `asyncio.create_task`. Before
registration, `schedule_auto_email` is a no-op — which is safe (the
lambda call sites in server.py cannot fire before the module finishes
importing anyway).
"""
from __future__ import annotations

import asyncio
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# _KIND_TO_COLLECTION — Mongo collection lookup by dispatch kind.
# Consumers: `_dispatch_auto_email`, `/api/auto-email-preview` (server.py
# ~L15234-L15236). Kept as a module-level dict; server.py re-imports the
# name so all references resolve identically.
# ---------------------------------------------------------------------------
_KIND_TO_COLLECTION = {
    "inspection": "inspections",
    "meeting": "meetings",
    "jha": "jhas",
    "incident": "incidents",
    "daily-report": "daily_reports",
    "equipment-inspection": "equipment_inspections",
}


# ---------------------------------------------------------------------------
# _filename_for — Composes a MASCI-<kind>-<project>-<date>.pdf filename.
# Pure function. Byte-identical to the pre-22.1B inline version.
# ---------------------------------------------------------------------------
def _filename_for(kind: str, record: dict) -> str:
    project = record.get("project_name") or "MASCI"
    date_part = (
        record.get("report_date")
        or record.get("inspection_date")
        or record.get("meeting_date")
        or record.get("jha_date")
        or record.get("incident_date")
        or ""
    )
    safe_proj = "".join(
        c if c.isalnum() else "_" for c in str(project)[:40]
    ).strip("_")
    return f"MASCI-{kind}-{safe_proj}-{date_part}.pdf".replace("--", "-")


# ---------------------------------------------------------------------------
# _is_severe_incident — Classifies an incident record as "severe" per the
# platform's OSHA + severity semantics. Pure function.
# ---------------------------------------------------------------------------
def _is_severe_incident(record: dict) -> bool:
    """Major/severe incident → always include OSHA-recordable + work-stopped flag."""
    sev = (record.get("severity") or "").strip().lower()
    severe = {"medical", "restricted", "lost_time", "fatality"}
    if sev in severe:
        return True
    if (record.get("osha_recordable") or "").strip().lower() == "yes":
        return True
    if (record.get("work_stopped") or "").strip().lower() == "yes":
        return True
    return False


# ---------------------------------------------------------------------------
# TRACK 15.79C · P0 fix — `asyncio.create_task()` only keeps a WEAK
# reference to the task. Under load the garbage collector can collect
# a pending task before it runs, which explains why production Daily
# Reports submitted post-deploy left ZERO email_routing_audit_v2 rows
# AND ZERO trust_spine_events: the dispatcher task was scheduled,
# the HTTP handler returned, and the GC freed the task before
# ``_dispatch_auto_email`` ever started.
#   Fix: retain a STRONG reference in a module-level set + clear it
#   when the task completes.
# ---------------------------------------------------------------------------
_AUTO_EMAIL_DISPATCH_TASKS: set = set()


# ---------------------------------------------------------------------------
# Dispatcher registration hook. server.py registers its
# `_dispatch_auto_email` here after it is defined.
# ---------------------------------------------------------------------------
_DISPATCHER_HOOK: Optional[Callable] = None


def register_dispatcher(fn: Callable) -> None:
    """Register the actual dispatcher coroutine function. Called once at
    server.py import time, after `_dispatch_auto_email` is defined.

    Multiple registrations are allowed (last write wins) — matches the
    pre-22.1B behavior where reloading the module re-binds the name.
    """
    global _DISPATCHER_HOOK
    _DISPATCHER_HOOK = fn


def schedule_auto_email(kind: str, record: dict) -> None:
    """Fire-and-forget wrapper (safe to call from any create endpoint).

    TRACK 15.79C — the returned task is now retained in a module-level
    set so the event loop's weak reference does not cause the GC to
    collect it before ``_dispatch_auto_email`` runs. ``add_done_callback``
    discards the task from the set when it completes (ok, failed, or
    cancelled), so the set never grows unbounded.

    TRACK 22.1B — This function was extracted from server.py; the
    concrete dispatcher is provided via `register_dispatcher(...)`.
    Body is byte-identical to the pre-22.1B version, with the single
    lookup change `_dispatch_auto_email` → `_DISPATCHER_HOOK`.
    """
    if _DISPATCHER_HOOK is None:
        # Pre-registration call — safe no-op. In normal boot this window
        # is closed before any HTTP handler can run (server.py registers
        # the dispatcher during module import).
        return
    try:
        task = asyncio.create_task(_DISPATCHER_HOOK(kind, dict(record)))
    except RuntimeError:
        # No running loop — skip silently (e.g. during sync tests)
        return
    _AUTO_EMAIL_DISPATCH_TASKS.add(task)
    task.add_done_callback(_AUTO_EMAIL_DISPATCH_TASKS.discard)
