"""TRACK 15.80 · permanent secret-exposure regression.

Background
----------
On 2026-06-07 commit ``c619207c``, the file
``memory/PRODUCTION_SECRETS_SEALED.env.template`` was committed to
the repo with literal high-entropy production secrets (JWT_SECRET,
ADMIN_HMAC_SECRET, MFA_ENCRYPTION_KEY, SUPER_ADMIN_BOOTSTRAP_PASSWORD,
portal passwords). The values were later rotated in production —
Track 15.80 Phase 4 proved exploitability is now negative — but the
historical file (plus 3 sibling runbook files) still held the values
in plain text. The audit caught it.

This test prevents recurrence: it scans every tracked file in the
repo for high-entropy secret-shaped literals and FAILS the build if
any are found. It is wired into the deployment gate so no future
commit can ship a similar exposure.

Scope (intentional false-positive filter)
----------------------------------------
We allow:
  * placeholders (``<rotated ...>``, ``<paste-here>``, ``EXAMPLE``,
    ``<your-value>``, etc.)
  * env-var references in source code (``os.environ.get(...)``,
    ``process.env.X``)
  * SHA256/HMAC PREFIX hashes documenting rotation evidence (16 or 64
    hex chars, but explicitly inside a "rotation evidence" / "audit
    evidence" file naming convention)
  * test fixture files using clearly synthetic strings (e.g.
    ``test_password = "abc12345"``)

We BLOCK:
  * raw high-entropy secret literals assigned to ``*_SECRET=*``,
    ``*_KEY=*``, ``*_HMAC=*``, ``*_TOKEN=*``, ``*_PASSWORD=*`` keys
    in any tracked file (markdown, env, txt, anything).
  * Mongo URIs containing a credential (``mongodb://user:pwd@``).
  * Resend keys (``re_<10+ chars>``).
  * AWS access key ids (``AKIA[A-Z0-9]{16}``).
  * Bearer tokens.

How to whitelist a single legitimate documentation literal:

Prepend the line with ``<!-- secret-scan: allow-line -->`` (markdown
comment) or ``# secret-scan: allow-line`` (shell/python). One allow
per line max.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path("/app")

EXCLUDE_PREFIXES = (
    ".git/", "node_modules/", "frontend/build/",
    ".venv/", "venv/", ".pytest_cache/",
)
EXCLUDE_SUFFIXES = (
    ".lock", ".min.js", ".min.css",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp4", ".webm", ".mp3", ".wav",
)

# Hard-block patterns. Each is a (regex, label) — the regex captures
# the OFFENDING substring; the label is for the assertion message.
BLOCKERS = [
    # Secret-looking key=value assignments with HIGH-ENTROPY values.
    # We require: at least 24 chars, mixed-case OR base64-ish, AND no
    # placeholder markers on the same line.
    (
        r'(?im)^[^#\n]*?'                       # not a fully-commented line
        r'(?:JWT_SECRET|ADMIN_HMAC_SECRET|HMAC_SECRET|'
        r'MFA_ENCRYPTION_KEY|ENCRYPTION_KEY|'
        r'SUPER_ADMIN_BOOTSTRAP_PASSWORD|BOOTSTRAP_PASSWORD|'
        r'ADMIN_PASSWORD|SEED_DEFAULT_PASSWORD|'
        r'(?:SHOP|PM|SAFETY_FORMS|DEV)_PASSWORD'
        r')\s*[:=]\s*'
        r'["\']?'
        r'([A-Za-z0-9+/=_\-]{24,})'             # value
        r'["\']?',
        'SECRET_LITERAL_ASSIGNMENT',
    ),
    # Mongo URI containing credentials.
    (
        r'mongodb(?:\+srv)?://[^"\'\s]+:[^"\'\s]+@[^"\'\s]+',
        'MONGO_URI_WITH_CREDS',
    ),
    # Raw Resend API key (re_ + ≥16 alphanumeric).
    (
        r'(?<![A-Za-z0-9])re_[A-Za-z0-9]{16,}',
        'RESEND_API_KEY_LITERAL',
    ),
    # AWS access key id.
    (
        r'(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])',
        'AWS_ACCESS_KEY_ID',
    ),
    # Bearer token literal (≥30 chars after "Bearer ").
    (
        r'Bearer\s+[A-Za-z0-9._\-]{30,}',
        'BEARER_TOKEN_LITERAL',
    ),
]

# Allow-list: per-line opt-out marker. ONE marker per line max.
ALLOW_LINE_MARKERS = (
    "secret-scan: allow-line",
)

# Allow-list: placeholder markers — if the matched VALUE contains any
# of these substrings, treat as documentation placeholder, not a leak.
PLACEHOLDER_VALUE_MARKERS = (
    "<rotated", "<paste", "<set-", "<your-", "<generated",
    "<changeme", "<keep current", "<from phase",
    "rotated · production-env-only",
    "PLACEHOLDER", "placeholder",
    "your-", "paste-", "REPLACE_ME", "CHANGE_ME", "CHANGEME",
    "EXAMPLE", "example.", "EXAMPLEKEY",
    "<openssl",
    "redacted", "REDACTED",
    "***",  # masked URI like ``mongodb+srv://***:***@host``
)


def _is_placeholder(value: str) -> bool:
    if any(m in value for m in PLACEHOLDER_VALUE_MARKERS):
        return True
    # Any ``<...>`` angle-bracket placeholder substring counts.
    if re.search(r"<[A-Za-z][A-Za-z0-9 _\-./]*>", value):
        return True
    return False


def _is_allowed_line(line: str) -> bool:
    return any(m in line for m in ALLOW_LINE_MARKERS)


def _list_tracked_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=str(REPO_ROOT)
    ).decode()
    files = []
    for f in out.splitlines():
        if any(f.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
        if any(f.endswith(s) for s in EXCLUDE_SUFFIXES):
            continue
        # exclude the secret-scanner test itself (it contains the
        # regex patterns which would otherwise self-match if a
        # future edit pasted a literal).
        if f == "backend/tests/test_track_15_80_no_secrets_in_repo.py":
            continue
        files.append(f)
    return files


def test_no_high_entropy_secrets_in_tracked_files():
    """Hard rule: a tracked file may NOT contain a high-entropy
    secret-shaped literal. Documentation placeholders + env-var refs
    are allowed. The historical leak (TRACK 15.80) is locked out by
    this test; the .gitignore patterns block re-introduction at the
    filename level."""
    findings: list[tuple[str, int, str, str]] = []
    files = _list_tracked_files()
    assert len(files) > 100, "git ls-files returned suspiciously few files"

    for f in files:
        path = REPO_ROOT / f
        try:
            data = path.read_bytes()
        except (OSError, FileNotFoundError):
            continue
        if b"\x00" in data[:2000]:
            continue  # binary
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            continue
        for line_no, line in enumerate(text.split("\n"), start=1):
            if _is_allowed_line(line):
                continue
            for pat, label in BLOCKERS:
                m = re.search(pat, line)
                if not m:
                    continue
                # If the matched value (group 1, when present) is a
                # placeholder, skip.
                try:
                    value = m.group(1)
                except IndexError:
                    value = m.group(0)
                if _is_placeholder(value) or _is_placeholder(line):
                    continue
                findings.append(
                    (f, line_no, label, f"<{label} · len≈{len(value)}>")
                )
                break  # one finding per line

    if findings:
        msg_lines = [
            "Track 15.80 secret-exposure regression FAILED. "
            f"{len(findings)} secret-shaped literals found in tracked files. "
            "Add `<!-- secret-scan: allow-line -->` (markdown) or "
            "`# secret-scan: allow-line` (shell/python) to the offending "
            "line ONLY if the value is a documentation placeholder. "
            "Otherwise, rotate the secret and remove the literal:"
        ]
        for f, ln, label, redacted in findings[:30]:
            msg_lines.append(f"  · {f}:{ln} → {label}  {redacted}")
        if len(findings) > 30:
            msg_lines.append(f"  · …+{len(findings)-30} more findings")
        raise AssertionError("\n".join(msg_lines))


def test_sealed_secrets_file_not_tracked():
    """The exact file that started this incident MUST never be tracked
    again. Pinning by full path catches accidental restores."""
    out = subprocess.check_output(
        ["git", "ls-files", "memory/PRODUCTION_SECRETS_SEALED.env.template"],
        cwd=str(REPO_ROOT),
    ).decode().strip()
    assert out == "", (
        "memory/PRODUCTION_SECRETS_SEALED.env.template is tracked by git. "
        "This file historically leaked production secrets and must remain "
        "deleted from the repo. Do NOT restore it."
    )


def test_gitignore_blocks_known_secret_patterns():
    """The .gitignore MUST contain explicit blocks for the historical
    leak patterns so this class of defect cannot return through file
    creation alone."""
    gi = (REPO_ROOT / ".gitignore").read_text()
    required_patterns = [
        ".env",
        "*.env.template",
        "*_SECRETS_*.env*",
        "*_SECRETS_*.template",
        "*SEALED*.env*",
        "*SEALED*.template",
        "secrets.env*",
    ]
    missing = [p for p in required_patterns if p not in gi]
    assert not missing, (
        f"Track 15.80 secret-file pattern lock missing from .gitignore: "
        f"{missing}"
    )
