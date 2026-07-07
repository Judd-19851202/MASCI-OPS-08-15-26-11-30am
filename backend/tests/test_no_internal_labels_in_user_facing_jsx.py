"""TRACK 24.1 · P0-3 · repo-wide UI copy lock.

Fails CI if any user-facing JSX text node in `/app/frontend/src`
contains an internal engineering label:

  · TRACK N            · TRACK NN.MMx
  · Track 13.6B        · Track 23.10-D  (etc.)
  · Internal · … Preview
  · Safety / Admin · Internal Use
  · Pilot build, Internal audit, Debug mode
  · Feature flag <name>

Code comments (`//` or `{/* */}`) are exempt because they never
render. Files under `__tests__/` and any `.test.js*` files are
exempt because they exercise the labels intentionally.

This lock is the **only** thing that prevents the copy defect the
Track 24.0 audit found from silently drifting back in.  Do not
weaken it.  If a new label is genuinely operator-facing (e.g. a
policy citation like "OSHA 29 CFR 1926.32(f)"), it is not covered
by this regex — regulatory references are fine.
"""
from __future__ import annotations

import re
import os
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent / "frontend" / "src"

_STRIP_LINE_COMMENT = re.compile(r"//[^\n]*")
_STRIP_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_BAD = re.compile(
    r"("
    r"TRACK\s*\d+\.[0-9A-Z]+[a-z]?"           # TRACK 15.66
    r"|Track\s+\d+\.[0-9A-Z]+[a-z]?"          # Track 13.6B
    r"|Internal\s+·\s+.*?\s+Preview"          # Internal · PM V2 Preview
    r"|Safety\s*/\s*Admin\s+·\s+Internal\s+Use"
    r"|Internal\s+Use\s+only"
    r"|pilot\s+build"
    r"|internal\s+audit"
    r"|debug\s+mode"
    r"|feature[\s_-]*flag[\s_-]+[a-z0-9_-]+"
    r")",
    re.IGNORECASE,
)


def _strip(src: str) -> str:
    """Remove `//` line comments and `/* */` block comments.

    Both regular JS/TS comments and JSX-style `{/* */}` blocks are
    captured because the `{ }` outside `/* */` is not part of the
    comment content that would match the BAD regex."""
    src = _STRIP_LINE_COMMENT.sub("", src)
    src = _STRIP_BLOCK_COMMENT.sub("", src)
    return src


def _iter_frontend_files():
    for base, _, files in os.walk(ROOT):
        if "__tests__" in base or "/node_modules/" in base:
            continue
        for f in files:
            if f.endswith((".jsx", ".tsx", ".js", ".ts")):
                if f.endswith((".test.js", ".test.jsx", ".test.ts", ".test.tsx")):
                    continue
                yield Path(base) / f


def test_no_internal_labels_in_user_facing_jsx():
    """Repo-wide lock: no user-visible JSX text may contain internal
    engineering track labels or "Internal · … Preview" strings.

    Track 24.0 audit (2026-02-07) found 31 files leaking these
    strings — every one was scrubbed in Track 24.1 (2026-02-07).
    This test prevents any future regression."""
    offenders: list[str] = []
    for p in _iter_frontend_files():
        try:
            src = _strip(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for m in _BAD.finditer(src):
            ln = src[: m.start()].count("\n") + 1
            rel = str(p.relative_to(ROOT))
            offenders.append(f"{rel}:{ln} · {m.group()!r}")
    assert not offenders, (
        "Internal engineering labels leaked into user-facing JSX.\n"
        "Every offender below renders to a real user (comment blocks\n"
        "are excluded from this scan).  Scrub these before deploy:\n\n  "
        + "\n  ".join(offenders[:60])
        + (f"\n\n  … and {len(offenders) - 60} more." if len(offenders) > 60 else "")
    )
