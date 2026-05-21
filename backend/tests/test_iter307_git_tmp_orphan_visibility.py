"""
iter307 · Ops-hygiene git tmp orphan visibility lock.

Bounded follow-up to the iter306 disk-audit closure: the audit found
~1 GB of orphan `tmp_pack_*` / `tmp_obj_*` files in `.git/objects/`
from a single interrupted git pack operation. Those orphans never
surfaced operationally because git never references them and the
`[ops-hygiene]` log didn't watch them.

This iteration adds ONE conditional log line (signal-not-noise — emits
ONLY when orphans exist) so any future accumulation surfaces on the
next backend startup or backup completion. No autonomous cleanup, no
new endpoint, no daemon, no new collection.

Scope discipline:
  - Logging-only addition inside the existing `_log_operational_hygiene`
    helper (iter299's bounded-closure infrastructure).
  - Emits `[ops-hygiene] git_tmp_orphans: count=N size_mb=X.Y` ONLY when
    at least one orphan tmp file exists.
  - Matches the three globbed patterns git uses for transient files
    during pack/index operations: `tmp_pack_*`, `tmp_idx_*`, and
    `??/tmp_obj_*` (the two-char shard dirs in `.git/objects/`).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PY = REPO_ROOT / "backend/server.py"


def test_iter307_git_tmp_orphan_logging_present():
    """The `_log_operational_hygiene` helper must emit a
    `git_tmp_orphans` log line. This is the one-line visibility add
    that surfaces interrupted git pack operations the same way iter299
    surfaced lite-backup tail accumulation."""
    text = SERVER_PY.read_text()
    assert "git_tmp_orphans" in text, (
        "iter307 logging missing — `[ops-hygiene] git_tmp_orphans` log "
        "line removed from server.py. Future orphan accumulation would "
        "become invisible operationally."
    )


def test_iter307_globs_all_three_tmp_patterns():
    """The orphan-detection glob must cover all three git tmp file
    patterns: tmp_pack_* (interrupted packs), tmp_idx_* (interrupted
    indexes), and tmp_obj_* (interrupted loose objects). Missing any
    one leaves a blind spot."""
    text = SERVER_PY.read_text()
    # Extract the orphan-detection block.
    idx = text.find("git_tmp_orphans")
    assert idx > 0, "iter307 block not located"
    block = text[max(0, idx - 800): idx + 800]
    for pat in ("tmp_pack_*", "tmp_idx_*", "tmp_obj_*"):
        assert pat in block, (
            f"iter307 orphan-detection glob missing pattern {pat!r} — "
            f"orphans of that kind would not be visible in [ops-hygiene] log."
        )


def test_iter307_signal_not_noise_only_logs_when_orphans_present():
    """The log line must be inside an `if tmp_paths:` guard so it only
    emits when orphans actually exist. Without the guard, the log line
    would print `count=0 size_mb=0.0` on every startup — noise that
    would erode operator attention to real signals (same lesson as
    iter306's stuck TEST banner)."""
    text = SERVER_PY.read_text()
    idx = text.find("git_tmp_orphans")
    block = text[max(0, idx - 400): idx + 200]
    assert "if tmp_paths" in block, (
        "iter307 missing `if tmp_paths:` guard — log would emit "
        "noise on every startup. Signal-not-noise discipline broken."
    )


def test_iter307_no_autonomous_cleanup_introduced():
    """The visibility addition must NOT delete or modify the orphan
    files. Operator explicitly forbade autonomous cleanup of any
    accumulated artifacts. This test asserts no `os.remove` / `os.unlink`
    / `shutil.rmtree` near the git_tmp_orphans logging."""
    text = SERVER_PY.read_text()
    idx = text.find("git_tmp_orphans")
    block = text[max(0, idx - 800): idx + 800]
    BANNED = ["os.remove", "os.unlink", "shutil.rmtree", "Path.unlink", ".unlink("]
    for bad in BANNED:
        assert bad not in block, (
            f"iter307 scope violation: {bad!r} found near git_tmp_orphans "
            f"logging — autonomous cleanup of orphans was NOT approved."
        )


def test_iter307_glob_scoped_to_app_git_objects_only():
    """The orphan search must be scoped to `/app/.git/objects/` — never
    `/.git`, never `/tmp`, never anywhere else. Wide-scope globs would
    introduce filesystem-traversal risk."""
    text = SERVER_PY.read_text()
    idx = text.find("git_tmp_orphans")
    block = text[max(0, idx - 800): idx + 800]
    # All three globs must be rooted in /app/.git/objects/
    glob_calls = re.findall(r'_g\.glob\(["\']([^"\']+)["\']\)', block)
    assert len(glob_calls) >= 3, f"expected ≥3 glob calls, got {glob_calls}"
    for g in glob_calls:
        assert g.startswith("/app/.git/objects/"), (
            f"iter307 glob {g!r} is not scoped to /app/.git/objects/ — "
            f"scope violation."
        )
