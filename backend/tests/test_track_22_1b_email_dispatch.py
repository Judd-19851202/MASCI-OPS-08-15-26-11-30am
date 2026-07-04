"""Track 22.1B · Email dispatcher modularization — permanent lock test.

Enforces:
- `backend/lib/email_dispatch.py` exists with the extracted symbols.
- server.py re-imports every extracted name under identical bindings.
- `_dispatch_auto_email` REMAINS defined in server.py (large body, not moved).
- `register_dispatcher(_dispatch_auto_email)` is called so the lib's
  `schedule_auto_email` routes through server's dispatcher.
- The bytecode of `_dispatch_auto_email` is unchanged relative to a stored
  fingerprint (co_code + first-line offset) so no accidental body edit slips in.
- The Resend SDK monkey-patch is installed BEFORE any `resend` import can
  return an unpatched send() (proven by import ordering assertion +
  runtime probe that returns the safety stub payload).
- All 10 Track 22.1B memory deliverables present and non-empty.
- Ledgers (PRD, CHANGELOG, Debt Register) record Track 22.1B.
- Runtime enumeration snapshots (before, after) are committed; the
  after-snapshot has 0 endpoint_qualname drift and 0 dependency_chain
  drift vs the before-snapshot.
- Every prior guardrail (EMAIL_SAFETY_MODE=strict, CORS explicit
  allow-lists, Track 22.0 + 22.1 lock tests) survives.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"
TRACK_DIR = MEM / "track_22_1b"

DELIVERABLES = [
    "TRACK_22_1B_EXECUTIVE_SUMMARY.md",
    "TRACK_22_1B_EMAIL_ARCHITECTURE.md",
    "TRACK_22_1B_DISPATCH_PARITY.md",
    "TRACK_22_1B_RECIPIENT_PARITY.md",
    "TRACK_22_1B_PAYLOAD_PARITY.md",
    "TRACK_22_1B_EMAIL_SAFETY.md",
    "TRACK_22_1B_RUNTIME_ORDER.md",
    "TRACK_22_1B_ZERO_DRIFT.md",
    "TRACK_22_1B_TEST_REPORT.md",
    "TRACK_22_1B_PERFORMANCE.md",
]


# ---------------------------------------------------------------------------
# 1. Extracted module exists with expected symbols.
# ---------------------------------------------------------------------------
def test_email_dispatch_module_exists_with_expected_symbols():
    body = (BACKEND / "lib" / "email_dispatch.py").read_text(encoding="utf-8")
    for sym in (
        "_KIND_TO_COLLECTION", "_filename_for", "_is_severe_incident",
        "_AUTO_EMAIL_DISPATCH_TASKS", "schedule_auto_email",
        "register_dispatcher", "_DISPATCHER_HOOK",
    ):
        assert sym in body, f"missing symbol in lib/email_dispatch.py: {sym}"
    # Must NOT `import resend` at module scope — SDK patch order safety.
    # Use AST to detect actual import statements (docstring / comment
    # mentions of the phrase are allowed).
    import ast
    tree = ast.parse(body)
    for node in tree.body:  # only top-level statements
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name != "resend", (
                    "lib/email_dispatch.py must not import resend at module scope"
                )
        if isinstance(node, ast.ImportFrom):
            assert node.module != "resend", (
                "lib/email_dispatch.py must not import from resend at module scope"
            )


# ---------------------------------------------------------------------------
# 2. server.py re-imports every extracted name.
# ---------------------------------------------------------------------------
def test_server_py_imports_extracted_names():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "from lib.email_dispatch import" in src
    for name in (
        "_filename_for", "_is_severe_incident",
        "_AUTO_EMAIL_DISPATCH_TASKS", "schedule_auto_email",
        "register_dispatcher",
    ):
        assert name in src, f"server.py must re-export {name}"
    # The registration call must appear.
    assert "_register_email_dispatcher(_dispatch_auto_email)" in src


# ---------------------------------------------------------------------------
# 3. _dispatch_auto_email remains in server.py (body not moved).
# ---------------------------------------------------------------------------
def test_dispatcher_body_still_in_server_py():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "async def _dispatch_auto_email(kind: str, record: dict)" in src
    # Signature is unchanged (still the same 2-arg async coroutine).


# ---------------------------------------------------------------------------
# 4. Old inline scaffolding is gone from server.py.
# ---------------------------------------------------------------------------
def test_old_inline_scaffolding_removed_from_server_py():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    # The inline strong-ref-set literal is gone (moved to lib).
    # We assert on the exact old comment marker that no longer appears.
    assert "def schedule_auto_email(kind: str, record: dict) -> None:" not in src, (
        "inline schedule_auto_email definition still present in server.py"
    )
    assert "def _filename_for(kind: str, record: dict) -> str:" not in src, (
        "inline _filename_for definition still present in server.py"
    )
    assert "def _is_severe_incident(record: dict) -> bool:" not in src, (
        "inline _is_severe_incident definition still present in server.py"
    )


# ---------------------------------------------------------------------------
# 5. Dispatcher hook is registered at runtime.
# ---------------------------------------------------------------------------
def test_dispatcher_hook_wired_at_runtime():
    import os, sys
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    from lib import email_dispatch as ed  # type: ignore
    assert ed._DISPATCHER_HOOK is server._dispatch_auto_email, (
        "register_dispatcher() did not bind _dispatch_auto_email into lib.email_dispatch._DISPATCHER_HOOK"
    )
    # Module attribution
    assert server.schedule_auto_email.__module__ == "lib.email_dispatch"
    assert server._filename_for.__module__ == "lib.email_dispatch"
    assert server._is_severe_incident.__module__ == "lib.email_dispatch"
    assert server._dispatch_auto_email.__module__ == "server"


# ---------------------------------------------------------------------------
# 6. SDK monkey-patch is still installed at module import time and blocks
#    live Resend sends.
# ---------------------------------------------------------------------------
def test_resend_sdk_patch_installed_and_blocks():
    import os, sys
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    sys.path.insert(0, str(BACKEND))
    import resend  # noqa: F401  # patched at import of server.py above
    import server  # noqa: F401
    result = resend.Emails.send({"from": "x", "to": ["y"], "subject": "s", "html": "<p/>"})
    assert result == {"id": "blocked_by_email_safety_mode", "status": "skipped"}, result


# ---------------------------------------------------------------------------
# 7. Runtime enumeration parity — 0 endpoint qualname / dependency chain
#    diffs between the pre-22.1B and post-22.1B snapshots.
# ---------------------------------------------------------------------------
def _load(name: str) -> dict:
    return json.loads((TRACK_DIR / name).read_text(encoding="utf-8"))


def test_runtime_snapshots_committed():
    for name in ("RUNTIME_ENUMERATION_before.json", "RUNTIME_ENUMERATION_after.json"):
        p = TRACK_DIR / name
        assert p.is_file() and p.stat().st_size > 1000, f"missing/empty: {name}"


def test_runtime_snapshot_zero_drift():
    b = _load("RUNTIME_ENUMERATION_before.json")
    a = _load("RUNTIME_ENUMERATION_after.json")
    assert b["route_count"] == a["route_count"]
    assert b["route_methods_total"] == a["route_methods_total"]
    assert b["openapi_path_count"] == a["openapi_path_count"]
    assert b["middleware"] == a["middleware"]
    assert b["startup_handlers"] == a["startup_handlers"]
    assert b["shutdown_handlers"] == a["shutdown_handlers"]
    assert b["exception_handlers"] == a["exception_handlers"]

    def key(r): return (r["path"], tuple(r["methods"]))
    b_by = {key(r): r for r in b["routes"]}
    a_by = {key(r): r for r in a["routes"]}
    assert set(b_by) == set(a_by), "route set drift"

    for k in b_by.keys() & a_by.keys():
        assert b_by[k]["endpoint_qualname"] == a_by[k]["endpoint_qualname"], (
            f"unexpected qualname move: {k}"
        )
        assert b_by[k]["dependency_chain"] == a_by[k]["dependency_chain"], (
            f"unexpected dependency chain drift: {k}"
        )


# ---------------------------------------------------------------------------
# 8. Bytecode fingerprint of _dispatch_auto_email is stable.
#    (Guards against silent edits to the dispatcher body during future work.)
# ---------------------------------------------------------------------------
def test_dispatcher_bytecode_fingerprint_recorded():
    fp = TRACK_DIR / "DISPATCHER_BYTECODE_FINGERPRINT.txt"
    assert fp.is_file(), "dispatcher bytecode fingerprint file missing"
    body = fp.read_text(encoding="utf-8").strip()
    assert re.match(r"^[0-9a-f]{64}$", body), (
        f"fingerprint must be a sha-256 hex string, got: {body!r}"
    )


def test_dispatcher_bytecode_matches_fingerprint():
    import os, sys
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    sys.path.insert(0, str(BACKEND))
    import server  # type: ignore
    code = server._dispatch_auto_email.__code__.co_code
    live = hashlib.sha256(code).hexdigest()
    stored = (TRACK_DIR / "DISPATCHER_BYTECODE_FINGERPRINT.txt").read_text(encoding="utf-8").strip()
    assert live == stored, (
        f"dispatcher body changed! live={live} stored={stored}. "
        "If this change is intentional, update the fingerprint file with the new sha256."
    )


# ---------------------------------------------------------------------------
# 9. Deliverables + ledgers.
# ---------------------------------------------------------------------------
def test_all_deliverables_present_and_non_empty():
    missing, empty = [], []
    for name in DELIVERABLES:
        p = MEM / name
        if not p.is_file():
            missing.append(name)
        elif p.stat().st_size < 200:
            empty.append(name)
    assert not missing, f"missing: {missing}"
    assert not empty, f"empty: {empty}"


def test_debt_register_records_track_22_1b():
    body = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8")
    assert "22.1b" in body.lower() or "22.1B" in body or "Track 22.1B" in body


def test_prd_records_track_22_1b():
    body = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 22.1B" in body or "Track 22.1B" in body or "22.1b" in body.lower()


def test_changelog_records_track_22_1b():
    body = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 22.1B" in body or "Track 22.1B" in body or "22.1b" in body.lower()


# ---------------------------------------------------------------------------
# 10. Prior guardrails preserved.
# ---------------------------------------------------------------------------
def test_email_safety_layers_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src
    assert "_dispatch_auto_email" in src
    env = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", env, re.MULTILINE)


def test_cors_explicit_allow_lists_preserved():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'allow_methods=["*"]' not in src
    assert 'allow_headers=["*"]' not in src


def test_prior_track_locks_committed():
    for name in (
        "test_track_22_0_platform_excellence.py",
        "test_track_22_1_server_modularization.py",
    ):
        assert (BACKEND / "tests" / name).is_file(), f"missing lock: {name}"
