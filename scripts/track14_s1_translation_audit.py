"""
Track 14.0-S1 Spanish Translation Coverage Audit · static scan.

Extracts every t("…") call from the frontend source, normalizes the
strings, cross-checks against the i18n.js dictionary, and prints a
coverage report.

Usage:
    cd /app && python3 scripts/track14_s1_translation_audit.py

Notes:
- t(...) only catches the canonical `t("string")` pattern. Strings built
  by interpolation (`t(\\`...\\`)` or t(variable)) are out of scope by
  design — those are runtime-dynamic strings that can't be statically
  asserted.
- Files under /node_modules/, /build/, /coverage/, /.git/ are skipped.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path("/app/frontend/src")
DICT_PATH = ROOT / "lib" / "i18n.js"

# t("…") with EITHER double or single quotes. Escaped quotes inside are
# rare in this codebase so we keep the matcher simple and high-signal.
T_CALL = re.compile(r"""\bt\(\s*"([^"\\]+(?:\\.[^"\\]*)*)"\s*[,)]""", re.M)
T_CALL_SINGLE = re.compile(r"""\bt\(\s*'([^'\\]+(?:\\.[^'\\]*)*)'\s*[,)]""", re.M)

# Dictionary entry — "english key": "spanish value" (inside i18n.js)
DICT_ENTRY = re.compile(r'^\s*"((?:[^"\\]|\\.)+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', re.M)

# Files we never extract from.
EXCLUDE_DIRS = {"node_modules", "build", "coverage", ".git", "__pycache__"}
INCLUDE_EXTS = {".js", ".jsx", ".ts", ".tsx"}


def iter_source_files() -> List[Path]:
    out: List[Path] = []
    for p in ROOT.rglob("*"):
        if p.is_dir():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.suffix not in INCLUDE_EXTS:
            continue
        if p == DICT_PATH:
            continue
        out.append(p)
    return out


def extract_used_strings() -> Dict[str, List[str]]:
    """Returns {english_key: [file_paths_referencing_it]}."""
    used: Dict[str, List[str]] = {}
    for p in iter_source_files():
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for rx in (T_CALL, T_CALL_SINGLE):
            for m in rx.finditer(text):
                key = m.group(1)
                # Skip empty / single-char artifacts.
                if not key or len(key.strip()) == 0:
                    continue
                used.setdefault(key, []).append(str(p.relative_to(ROOT)))
    return used


def extract_dictionary() -> Dict[str, str]:
    """Returns {english_key: spanish_value}."""
    out: Dict[str, str] = {}
    text = DICT_PATH.read_text(encoding="utf-8")
    for m in DICT_ENTRY.finditer(text):
        en, es = m.group(1), m.group(2)
        if en in out:
            # Last definition wins — same as JS.
            pass
        out[en] = es
    return out


def per_portal_breakdown(used: Dict[str, List[str]]) -> Dict[str, Tuple[int, int]]:
    """Group untranslated strings by portal directory.
    Returns {portal_label: (total_strings, untranslated_count)}.
    """
    portals = {
        "Admin": ["admin", "Admin"],
        "PM": ["pm", "Pm", "PM"],
        "HR": ["hr", "Hr"],
        "Safety": ["safety", "Safety"],
        "Shop": ["shop", "Shop"],
        "Dispatch": ["dispatch", "Dispatch"],
        "Field Leadership": ["field", "FieldLeadership", "leadership"],
        "Public Forms": ["forms", "Public", "incidents/new", "daily/new", "meetings/new"],
        "Notifications/Tasks": ["Notification", "Task", "notifications"],
        "Other / Shared": [],
    }
    return portals  # Stub — caller computes from `used`.


def main() -> int:
    used = extract_used_strings()
    dictionary = extract_dictionary()

    used_keys: Set[str] = set(used.keys())
    dict_keys: Set[str] = set(dictionary.keys())

    translated = used_keys & dict_keys
    untranslated = used_keys - dict_keys
    unused_dict = dict_keys - used_keys

    total = len(used_keys)
    coverage = (len(translated) / total * 100.0) if total else 100.0

    print("=" * 72)
    print(" Track 14.0-S1 · Spanish Translation Coverage Audit")
    print("=" * 72)
    print(f"Dictionary entries (i18n.js):   {len(dict_keys):>6}")
    print(f"Distinct t() call sites:        {total:>6}")
    print(f"Translated:                     {len(translated):>6}  ({coverage:5.1f}%)")
    print(f"Untranslated:                   {len(untranslated):>6}")
    print(f"Unused dictionary entries:      {len(unused_dict):>6}")
    print()

    # Sample untranslated
    print("SAMPLE OF UNTRANSLATED (first 30 alphabetically):")
    for k in sorted(untranslated)[:30]:
        files = used[k][:3]
        flist = ", ".join(files)
        if len(used[k]) > 3:
            flist += f", +{len(used[k]) - 3} more"
        print(f"  · {k!r}  ({flist})")

    # Per-portal heat map
    print()
    print("PER-PORTAL UNTRANSLATED HEAT MAP (top 10 portals by file path):")
    portal_counts: Dict[str, int] = {}
    for k in untranslated:
        for f in used[k]:
            # Top-level directory after src/
            parts = f.split("/", 2)
            top = parts[0] if parts else "root"
            portal_counts.setdefault(top, 0)
            portal_counts[top] += 1
            break
    for portal, cnt in sorted(portal_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {portal:24} {cnt:>5}")

    # Write JSON for downstream tooling
    out_path = Path("/app/test_reports/track14_s1_audit.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "dictionary_entries": len(dict_keys),
        "used_strings": total,
        "translated": len(translated),
        "untranslated": len(untranslated),
        "unused_dict_entries": len(unused_dict),
        "coverage_pct": round(coverage, 2),
        "untranslated_samples": sorted(untranslated)[:200],
        "portal_breakdown": portal_counts,
    }, indent=2))
    print()
    print(f"JSON report → {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
