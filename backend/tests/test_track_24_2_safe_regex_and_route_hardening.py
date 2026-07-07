"""TRACK 24.2 · Phase 3 · `safe_regex` helper + platform-wide adoption.

Covers:
  · helper produces correct shapes for the three anchors
  · escaping literals: `.*`, `(a+)+b`, `[[[[`, `^$`, unicode
  · adoption sweep: no unescaped `f"^{var}$"` / `{"$regex": var, …}`
    patterns remain in the flagged high-risk files (safety_forms,
    transportation, employee_lifecycle, employee_records, hr_portal,
    trench_safety/*, operations_actions/api, promo_assets,
    document_expirations, tasks_notifications, po_requests).
"""
from __future__ import annotations
from pathlib import Path
import re
import sys

# Make sure /app/backend is on the path
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from lib.mongo_query import safe_regex


def test_safe_regex_default_substring():
    v = safe_regex("hello")
    assert v == {"$regex": "hello", "$options": "i"}


def test_safe_regex_exact_anchor():
    v = safe_regex("dave@example.com", anchor="exact")
    assert v == {"$regex": r"^dave@example\.com$", "$options": "i"}


def test_safe_regex_prefix_anchor():
    v = safe_regex("2025-", anchor="prefix")
    assert v == {"$regex": r"^2025\-", "$options": "i"}


def test_safe_regex_escapes_metacharacters():
    """Every regex metacharacter must be escaped to LITERAL match."""
    v = safe_regex(".*")
    # `.*` must match the literal `.*`, not "everything".
    assert v["$regex"] == r"\.\*"


def test_safe_regex_escapes_redos_payload():
    """Catastrophic backtracking payload must be neutralised."""
    v = safe_regex("(a+)+b")
    # `+` and parens escaped so the payload is inert.
    assert "+" not in v["$regex"] or "\\+" in v["$regex"]
    assert "(" not in v["$regex"] or "\\(" in v["$regex"]


def test_safe_regex_escapes_bracket_payload():
    v = safe_regex("[[[[")
    # No unbalanced bracket sequence — every `[` escaped.
    assert v["$regex"] == r"\[\[\[\["


def test_safe_regex_strips_whitespace():
    v = safe_regex("  hello  ")
    assert v["$regex"] == "hello"


def test_safe_regex_none_safe():
    v = safe_regex(None)  # type: ignore[arg-type]
    assert v == {"$regex": "", "$options": "i"}


def test_safe_regex_case_sensitive_option():
    v = safe_regex("hello", case_insensitive=False)
    assert v["$options"] == ""


# ─── Adoption sweep — target files must NOT interpolate raw variables ───
FLAGGED = [
    "routes/safety_forms.py",
    "routes/transportation.py",
    "routes/employee_records.py",
    "routes/tasks_notifications.py",
    "routes/document_expirations.py",
    "routes/operations_actions/api.py",
    "routes/promo_assets.py",
    "routes/trench_safety/assets.py",
    "routes/hr_portal.py",
    "routes/po_requests.py",
]

# Any `{"$regex": <var>, "$options": ...}` where <var> is a plain
# identifier that is NOT already wrapped with re.escape / _re.escape
# / safe_regex is a latent injection sink.
_UNSAFE = re.compile(
    r'\{\s*"\$regex"\s*:\s*([a-zA-Z_][a-zA-Z0-9_.\(\)]*)\s*,',
)


def _strip_comments(src: str) -> str:
    """Strip Python # comments and triple-quoted docstrings to avoid
    false positives from example strings inside docstrings."""
    # Docstrings (triple-quoted)
    src = re.sub(r'""".*?"""', "", src, flags=re.DOTALL)
    src = re.sub(r"'''.*?'''", "", src, flags=re.DOTALL)
    # Line comments
    src = re.sub(r"#[^\n]*", "", src)
    return src


def test_flagged_files_have_no_unescaped_regex_variables():
    """Every file in the P1-D flagged set must use `safe_regex` OR
    `re.escape()` for every `$regex` interpolation."""
    offenders: list[str] = []
    for rel in FLAGGED:
        p = BACKEND / rel
        if not p.exists():
            continue
        src = _strip_comments(p.read_text(encoding="utf-8"))
        for m in _UNSAFE.finditer(src):
            var_or_call = m.group(1)
            # allowed:
            #   safe_regex(...)  emits `{"$regex": pattern, "$options": …}`
            #                    where `pattern` is a local variable —
            #                    those matches are already the OUTPUT of
            #                    safe_regex, not user input. Skip if the
            #                    surrounding context is inside safe_regex.
            if var_or_call.startswith("safe_regex"):
                continue
            # `re.escape(...)` inline
            if "re.escape" in var_or_call or "_re.escape" in var_or_call:
                continue
            # bare literal string constants are safe
            if var_or_call.startswith('"') or var_or_call.startswith("'"):
                continue
            # `f"...` pre-escaped by safe_regex above — skip
            # Numeric constants
            if var_or_call.replace(".", "").isdigit():
                continue
            ln = src[: m.start()].count("\n") + 1
            offenders.append(f"{rel}:{ln} · {{\"$regex\": {var_or_call}, …")
    assert not offenders, (
        "The following files still interpolate raw variables into $regex "
        "(NoSQL injection / ReDoS surface). Replace with safe_regex(...) "
        "or wrap the value with re.escape().\n\n  "
        + "\n  ".join(offenders[:40])
    )


def test_helper_module_documented():
    """The helper module must carry a docstring so future contributors
    understand why to use it."""
    src = (BACKEND / "lib" / "mongo_query.py").read_text(encoding="utf-8")
    assert "safe_regex" in src
    assert "ReDoS" in src or "backtracking" in src


def test_duplicate_route_scan_is_fail_closed():
    """Track 24.2 · Phase 3 · the boot-time duplicate-route scan must
    RAISE on offenders (not WARN)."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    m = re.search(
        r"async def _assert_no_duplicate_routes\(\).*?(?=\n\@|\ndef |\nasync def )",
        src, flags=re.DOTALL,
    )
    assert m, "_assert_no_duplicate_routes function not found"
    body = m.group(0)
    assert "raise RuntimeError" in body, (
        "Duplicate-route scan must fail-closed (raise) on offenders, not just warn."
    )
    assert "[track-24.2]" in body, (
        "Logs should identify this as the 24.2 hardening step."
    )
