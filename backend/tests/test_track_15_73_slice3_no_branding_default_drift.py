"""TRACK 15.73 SLICE 4 · No-Branding-Default-Drift · CI Guardrail.

Static analysis test that blocks the Track 15.68C regression pattern
from re-appearing. Greps the frontend source tree for ANY callsite of
``brandCompanyName("Customer")`` (the unsafe generic default).

If found, the test FAILS with the exact file:line citations so the
developer who re-introduced the pattern can fix it before merge.

Allowed patterns:

* ``brandCompanyName("MASCI")`` — tenant-canonical default for OurCo.
* ``brandCompanyName("Project")`` — display-only context (e.g. email subject).
* ``brandCompanyName()`` — no default; caller is responsible.

Banned pattern (the regression):
* ``brandCompanyName("Customer")`` — silent identity drift.
"""
from __future__ import annotations

import re
from pathlib import Path


FRONTEND_SRC = Path("/app/frontend/src")
BANNED = re.compile(r'brandCompanyName\(\s*"Customer"\s*\)')


def _walk_files() -> list[Path]:
    files: list[Path] = []
    for ext in ("*.jsx", "*.js", "*.tsx", "*.ts"):
        files.extend(FRONTEND_SRC.rglob(ext))
    return files


def test_no_branding_default_drift():
    offenders: list[str] = []
    for path in _walk_files():
        # Skip the helper definition file itself (defaultName="Customer"
        # is the function signature default, not a callsite).
        if path.name == "brandFilename.js":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if BANNED.search(line):
                rel = path.relative_to(FRONTEND_SRC.parent)
                offenders.append(f'  {rel}:{lineno}  {line.strip()}')

    if offenders:
        msg = (
            "TRACK 15.73 SLICE 4 · BANNED PATTERN DETECTED.\n"
            'Re-introducing `brandCompanyName("Customer")` is forbidden — it was the '
            "root cause of the Track 15.68C employee identity regression. Use "
            '`brandCompanyName("MASCI")` for tenant-canonical defaults or pass an '
            "explicit tenant name from BrandingProvider.\n\n"
            "Offending callsite(s):\n"
            + "\n".join(offenders)
        )
        raise AssertionError(msg)
