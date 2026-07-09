"""TRACK 27.05 · P0-4 · Disk-space preflight helpers.

Small, self-contained module that upload / render / temp-write paths
consult before touching the local filesystem. If free disk space is
below the safe threshold, the caller raises HTTP 507 Insufficient
Storage rather than starting a write that will die halfway through
and leave a corrupt half-file behind.

Environment overrides:
    DISK_SAFE_MIN_BYTES         (default 512 MiB) — refuse below this
    DISK_SAFE_MIN_PERCENT_FREE  (default 5.0 %)   — same-thresh as pct
    DISK_PREFLIGHT_PATH         (default /app)    — mount point checked

Two thresholds because a 100 GB disk with 400 MB free is objectively
in trouble (percent-free triggers) and a 20 GB disk with 100 MB free
is objectively in trouble (byte-count triggers). Whichever hits first
wins.

Nothing here modifies disk state; the module is READ-ONLY.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiskStatus:
    path: str
    total_bytes: int
    free_bytes: int
    percent_free: float
    ok: bool
    reason: Optional[str]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or str(default))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or str(default))
    except ValueError:
        return default


def _thresholds() -> tuple[int, float]:
    return (
        _env_int("DISK_SAFE_MIN_BYTES", 512 * 1024 * 1024),   # 512 MiB
        _env_float("DISK_SAFE_MIN_PERCENT_FREE", 5.0),
    )


def _path() -> str:
    return os.environ.get("DISK_PREFLIGHT_PATH", "/app")


def check_disk(path: Optional[str] = None) -> DiskStatus:
    """Report current free-space state. Never raises."""
    p = path or _path()
    try:
        usage = shutil.disk_usage(p)
    except OSError as e:
        logger.warning(f"[disk-preflight] disk_usage({p!r}) failed: {e}")
        return DiskStatus(p, 0, 0, 0.0, True, None)  # fail-open on missing path
    min_bytes, min_pct = _thresholds()
    pct_free = 100.0 * usage.free / usage.total if usage.total else 0.0
    ok = usage.free >= min_bytes and pct_free >= min_pct
    reason = None
    if not ok:
        parts = []
        if usage.free < min_bytes:
            parts.append(
                f"free={usage.free / (1024*1024):.1f} MiB < min={min_bytes / (1024*1024):.0f} MiB"
            )
        if pct_free < min_pct:
            parts.append(f"free%={pct_free:.1f}% < min%={min_pct:.1f}%")
        reason = " · ".join(parts)
    return DiskStatus(p, usage.total, usage.free, round(pct_free, 2), ok, reason)


class DiskFullError(Exception):
    """Raised when a preflight fails. Callers translate to HTTP 507."""

    def __init__(self, status: DiskStatus):
        self.status = status
        super().__init__(
            f"Disk preflight failed at {status.path}: {status.reason}"
        )


def preflight_or_raise(path: Optional[str] = None) -> DiskStatus:
    """Call this BEFORE writing to local disk (temp render, upload
    staging, PDF cache, etc.). Raises `DiskFullError` if the disk is
    below the safe threshold — callers should translate the exception
    into HTTP 507 Insufficient Storage.

    Fail-open on OSError (e.g., path doesn't exist) — the check never
    blocks a workflow due to its own failure.
    """
    st = check_disk(path)
    if not st.ok:
        raise DiskFullError(st)
    return st


__all__ = ["DiskStatus", "DiskFullError", "check_disk", "preflight_or_raise"]
