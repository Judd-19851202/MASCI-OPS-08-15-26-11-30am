"""Track 22.1C · Scheduler + Startup Inventory Harness.

Boots the FastAPI app in-process (no uvicorn, no live services), enumerates
every `@app.on_event(...)` handler with full metadata, and writes:

- `memory/track_22_1c/STARTUP_ORDER_{stage}.json` — deterministic ordered
  list of startup + shutdown handler qualnames, modules, source lines,
  and a side-effect classification based on function-body substring
  heuristics (email / mongo / r2 / trust_spine / scheduler / external_api).

- `memory/track_22_1c/SCHEDULER_INVENTORY_{stage}.json` — a filtered slice
  of the same data covering only handlers that touch schedulers, mongo
  writes, or external side effects.

Deterministic + safe to `diff` byte-for-byte between snapshots.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import sys
from pathlib import Path

# --- Env guardrails ---------------------------------------------------------
os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
os.environ.setdefault("BACKUP_ON_STARTUP", "false")
os.environ.setdefault("RATE_LIMITING", "off")

sys.path.insert(0, "/app/backend")


SIDE_EFFECT_KEYWORDS = {
    "email": (r"\bresend\b", r"\bschedule_auto_email\b", r"send_email", r"digest_email"),
    "mongo_write": (r"\.insert_one\b", r"\.update_one\b", r"\.delete_one\b",
                    r"\.insert_many\b", r"\.update_many\b", r"\.replace_one\b"),
    "r2_storage": (r"\br2_\w+\b", r"\bboto3\b", r"\bs3_client\b"),
    "trust_spine": (r"emit_workflow_stage", r"trust_spine_events"),
    "scheduler": (r"asyncio\.create_task", r"run_with_singleton_lock",
                  r"AsyncIOScheduler", r"add_job", r"cron", r"interval"),
    "external_api": (r"requests\.(get|post|put|delete)", r"httpx\.",
                     r"aiohttp\."),
    "backup": (r"\bbackup_", r"BACKUP_"),
    "digest": (r"\bdigest_\w+\b", r"_digest\("),
    "index": (r"create_index", r"ensure_index"),
}


def _classify_side_effects(source: str) -> list[str]:
    hits = []
    for label, patterns in SIDE_EFFECT_KEYWORDS.items():
        for p in patterns:
            if re.search(p, source):
                hits.append(label)
                break
    return sorted(set(hits))


def _handler_row(fn, index: int) -> dict:
    try:
        src = inspect.getsource(fn)
    except Exception:
        src = ""
    try:
        lineno = inspect.getsourcelines(fn)[1]
    except Exception:
        lineno = None
    try:
        code_hash = hashlib.sha256(fn.__code__.co_code).hexdigest()
    except Exception:
        code_hash = None

    return {
        "index": index,
        "qualname": getattr(fn, "__qualname__", getattr(fn, "__name__", repr(fn))),
        "name": getattr(fn, "__name__", None),
        "module": getattr(fn, "__module__", None),
        "sourcefile": inspect.getsourcefile(fn) if hasattr(fn, "__code__") else None,
        "lineno": lineno,
        "is_coroutine": inspect.iscoroutinefunction(fn),
        "arg_count": (fn.__code__.co_argcount if hasattr(fn, "__code__") else None),
        "bytecode_sha256": code_hash,
        "side_effects": _classify_side_effects(src),
        "docstring_first_line": (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else None,
    }


def enumerate_lifecycle(app) -> dict:
    startups = list(getattr(app.router, "on_startup", []) or [])
    shutdowns = list(getattr(app.router, "on_shutdown", []) or [])
    startup_rows = [_handler_row(f, i) for i, f in enumerate(startups)]
    shutdown_rows = [_handler_row(f, i) for i, f in enumerate(shutdowns)]

    # Aggregate counts
    side_effect_totals: dict[str, int] = {}
    for r in startup_rows:
        for label in r["side_effects"]:
            side_effect_totals[label] = side_effect_totals.get(label, 0) + 1

    return {
        "startup_handler_count": len(startup_rows),
        "shutdown_handler_count": len(shutdown_rows),
        "startup_handlers": startup_rows,
        "shutdown_handlers": shutdown_rows,
        "side_effect_totals": side_effect_totals,
    }


def main(stage: str) -> None:
    from server import app  # type: ignore
    inv = enumerate_lifecycle(app)

    out_dir = Path("/app/memory/track_22_1c")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Full startup order file
    (out_dir / f"STARTUP_ORDER_{stage}.json").write_text(
        json.dumps(inv, indent=2, sort_keys=True), encoding="utf-8",
    )

    # Filtered scheduler inventory
    interesting = {"scheduler", "email", "external_api", "backup",
                   "digest", "r2_storage", "trust_spine", "mongo_write"}
    scheduler_rows = [r for r in inv["startup_handlers"] if set(r["side_effects"]) & interesting]
    (out_dir / f"SCHEDULER_INVENTORY_{stage}.json").write_text(
        json.dumps({
            "count": len(scheduler_rows),
            "handlers": scheduler_rows,
        }, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"[track 22.1c/{stage}] startups={inv['startup_handler_count']} shutdowns={inv['shutdown_handler_count']} scheduler_capable={len(scheduler_rows)}")
    for k, v in inv["side_effect_totals"].items():
        print(f"  side_effect: {k:14s} {v}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "current"
    main(stage)
