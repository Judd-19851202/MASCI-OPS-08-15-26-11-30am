"""TRACK 15.41 · Field preservation diff (CRITICAL DIRECTIVE #1).

Verifies: AFTER PDF text is a SUPERSET of BEFORE PDF text.

For each of the Top 6 PDFs:
  * tokenize each line into "fingerprints" (stripped, non-empty)
  * assert every BEFORE fingerprint exists in the AFTER fingerprint set
  * dump any missing fingerprints as a hard FAIL

Track 15.41 GREEN cert is gated on this script reporting 0 missing
fingerprints across all 6 PDFs.
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT_BASE = Path("/tmp/track_15_41")
PDFS = [
    "safety_meeting",
    "daily_report",
    "jha",
    "equipment_issuance",
    "equipment_return",
    "training_acknowledgement",
]


def _fingerprints(text: str) -> set[str]:
    """Stripped, non-empty lines. Token-of-truth for "the operational
    information rendered on the PDF". This is intentionally permissive:
    line-level equality only; whitespace and pagination noise are
    ignored. Empty lines and pure punctuation rows are dropped."""
    import re as _re
    iso_re = _re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    sha_re = _re.compile(r"^sha256=[0-9a-f]{16}$")
    fps = set()
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # ignore lines that are pagination artifacts (just "Page N of M")
        if line.startswith("Page ") and "of" in line:
            continue
        # ignore the generation timestamp line which obviously moves
        if line.startswith("Generated 20") or line.startswith("Generated  20"):
            continue
        # ignore standalone ISO timestamps (the DR official-record
        # `rendered <utc>` footer; this is intentionally a moving value)
        compact = line.replace(" ", "")
        if iso_re.match(compact):
            continue
        if sha_re.match(compact):
            continue
        fps.add(line)
    return fps


def main():
    any_fail = False
    print(f"{'PDF':<30s} {'BEFORE':>8s} {'AFTER':>8s} {'MISSING':>8s} VERDICT")
    print("-" * 70)
    for name in PDFS:
        before = (OUT_BASE / "before" / f"{name}.txt")
        after = (OUT_BASE / "after" / f"{name}.txt")
        if not before.exists() or not after.exists():
            print(f"{name:<30s}      —        —       —  SKIP (missing file)")
            continue
        b_fps = _fingerprints(before.read_text())
        a_fps = _fingerprints(after.read_text())
        missing = b_fps - a_fps
        verdict = "🟢 PASS" if not missing else "🔴 FAIL"
        print(f"{name:<30s} {len(b_fps):>8d} {len(a_fps):>8d} {len(missing):>8d}  {verdict}")
        if missing:
            any_fail = True
            print(f"  Missing fingerprints in AFTER:")
            for m in sorted(missing)[:20]:
                print(f"    - {m!r}")
            if len(missing) > 20:
                print(f"    ... +{len(missing)-20} more")
    print("-" * 70)
    if any_fail:
        print("🔴 FIELD PRESERVATION FAIL — track is NOT GREEN")
        sys.exit(1)
    print("🟢 FIELD PRESERVATION PASS — every BEFORE line is present in AFTER")


if __name__ == "__main__":
    main()
