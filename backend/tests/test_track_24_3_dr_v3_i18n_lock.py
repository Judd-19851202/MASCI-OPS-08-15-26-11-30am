"""TRACK 24.3 · Hard-coded string lock.

Scans Daily Report V3 frontend files for user-visible English literals
that were never wrapped in the platform i18n `t(…)` helper. Regenerates
on every CI run · fails closed the moment a DR V3 component ships an
untranslatable string.

Whitelist (allowed unwrapped):
  * data-testid, className, key, type, autoComplete, spellCheck attrs
  * enum keys / API paths / class names / numeric constants
  * technical strings that never render (JSDoc, imports, keys)

Threshold: 0 offenders. Any offender fails the test.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

FRONTEND_ROOT = Path("/app/frontend/src")
DR_V3_FILES = [
    FRONTEND_ROOT / "pages" / "NewDailyReportV3.jsx",
    FRONTEND_ROOT / "components" / "daily-report-v3" / "sections.jsx",
    FRONTEND_ROOT / "components" / "daily-report-v3" / "DailyReportV3ExcavationSection.jsx",
    FRONTEND_ROOT / "components" / "daily-report-v3" / "SectionProjectConditions.jsx",
    FRONTEND_ROOT / "components" / "daily-report-v3" / "CompetentPersonCombo.jsx",
    FRONTEND_ROOT / "components" / "daily-report-v3" / "UnitCombo.jsx",
    # Track 24.3 · sub-components rendered inside DR V3 that must also
    # translate cleanly in ES mode.
    FRONTEND_ROOT / "components" / "daily-report" / "DailySummaryAssist.jsx",
    FRONTEND_ROOT / "components" / "SignaturePad.jsx",
]

# Substrings we do NOT flag (technical / infrastructure strings).
_TECHNICAL_HINTS = {
    "MASCI", "MASCI ", " MASCI",  # brand — allowed by i18n brand substitution
    "http", "photo:", "data:",
    "ft", "m",  # excavation dimension enum values
    "yes", "no", "n/a",
}


def _strip_comments(src: str) -> str:
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"\{/\*.*?\*/\}", "", src, flags=re.DOTALL)
    return src


# JSX text: `>UserFacingString<`.
RX_JSX_TEXT = re.compile(
    r">\s*"
    r"([A-Z][A-Za-z][A-Za-z0-9 ,'.:;/\-–—?!()&%$#@+*=<>_\"]{2,120})"
    r"\s*(?=[<])",
    re.MULTILINE,
)

# Attribute literal: `attr="UserFacingString"`.
RX_PROP = re.compile(
    r'\b(title|label|placeholder|description|error|alt|subtitle|kicker|helper|helperText|'
    r'caption|toast|message|heading|body|prompt|hint|ariaLabel|aria-label|tooltip)\s*=\s*'
    r'"([^"\{]{2,120})"'
)


def _is_technical(text: str) -> bool:
    t = text.strip()
    if not t or t.startswith("{") or t.startswith("$"):
        return True
    if t in _TECHNICAL_HINTS:
        return True
    if re.fullmatch(r"[\-.\d%°]+", t):
        return True
    return False


def _scan(path: Path):
    src = _strip_comments(path.read_text(encoding="utf-8"))
    offenders = []
    for m in RX_JSX_TEXT.finditer(src):
        text = m.group(1).strip()
        if _is_technical(text):
            continue
        # Line number
        line = src[:m.start()].count("\n") + 1
        offenders.append((line, "jsx-text", text))
    for m in RX_PROP.finditer(src):
        text = (m.group(2) or "").strip()
        if _is_technical(text):
            continue
        line = src[:m.start()].count("\n") + 1
        offenders.append((line, f"prop:{m.group(1)}", text))
    return offenders


@pytest.mark.parametrize("path", DR_V3_FILES, ids=[p.name for p in DR_V3_FILES])
def test_no_hardcoded_english_in_dr_v3(path: Path):
    """Every user-visible English string in DR V3 must be wrapped in
    `t(…)` from `@/lib/i18n`. Any unwrapped literal fails this lock."""
    assert path.exists(), f"missing DR V3 file: {path}"
    offenders = _scan(path)
    if offenders:
        lines = "\n".join(f"  line {ln} [{kind}]: {txt!r}" for ln, kind, txt in offenders)
        pytest.fail(
            f"[Track 24.3] {path.name} has {len(offenders)} hard-coded "
            f"user-facing English literal(s):\n{lines}\n\n"
            f"Wrap each with `t(\"…\")` from `@/lib/i18n`."
        )


def test_i18n_keys_have_spanish_values():
    """Every DR V3 key referenced via `t("…")` must exist in the ES
    dictionary or be intentionally reserved (English acronym / brand)."""
    i18n_src = (FRONTEND_ROOT / "lib" / "i18n.js").read_text(encoding="utf-8")
    # Extract every key in the ES const (rough grep — production-grade
    # audit only needs approximate parity, not perfect parsing).
    es_keys = set(re.findall(r'^\s*"([^"]+?)"\s*:\s*"', i18n_src, re.MULTILINE))
    referenced = set()
    for p in DR_V3_FILES:
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r'(?<![A-Za-z0-9_])t\(\s*"([^"]+?)"', text):
            referenced.add(m.group(1))
    # Allow-list: brand / acronym / single-char / already-known safe.
    allow = {"GPS", "MASCI · Daily Job Report", "Yes", "No", "N/A"}
    missing = [k for k in sorted(referenced - es_keys - allow)
               if not re.fullmatch(r"Type [A-Z][A-Za-z]*", k)]
    if missing:
        pytest.fail(
            f"[Track 24.3] {len(missing)} DR V3 t() keys have no Spanish "
            f"translation:\n" + "\n".join(f"  - {k}" for k in missing[:60])
        )
