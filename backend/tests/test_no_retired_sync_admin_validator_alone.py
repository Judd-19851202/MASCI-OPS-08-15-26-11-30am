"""TRACK 28.03E · Platform-wide admin auth-gate invariant.

**Contract**

The retired synchronous ``_is_valid_admin_token`` in
``server.py`` was retired in TRACK 15.32 and unconditionally
returns ``False``. It survives only as a placeholder inside legacy
gate factory signatures.

Any code path that uses this function to authorize an admin
request must ALSO invoke ``_is_valid_directory_admin_token_async``
(or an equivalently-scoped async validator) so the actual per-user
admin token issued by ``/api/auth/multi-login`` unlocks the gate.

Failure to do so has already caused TWO production P0 regressions:

  * TRACK 28.02-A · Safety/Shop/Dispatch write factories
  * TRACK 28.03-A · Field Leadership gate

This invariant closes the class of defect permanently: CI fails
whenever a function references the retired sync validator without
the paired async fallback, unless the function is in the
:data:`INTERNAL_ALLOWLIST` with a documented, machine-internal,
non-authorizing reason.

**Rules**

The invariant scans every backend ``.py`` file (excluding tests,
scripts, migrations, backups). For each callsite it finds that
matches any of the following patterns:

  1. Direct call: ``_is_valid_admin_token(<expr>)``
  2. Positional-arg wiring inside a factory-call at import time:
     ``some_factory(db, _is_valid_admin_token, …)``

The scanner then locates the enclosing function (for direct
calls) or the enclosing module scope (for factory wiring). The
invariant asserts that either:

  (a) the enclosing function/module ALSO invokes / awaits
      ``_is_valid_directory_admin_token_async`` (or another
      known async admin-token validator symbol), OR

  (b) the ``(rel_path, function_name)`` tuple is in
      :data:`INTERNAL_ALLOWLIST` with a documented reason.

**Adding a new callsite**

1. PREFER wiring the async validator alongside the sync one. That
   is the correct answer 99% of the time.
2. If a machine-internal helper genuinely cannot authorize an
   operator request (e.g. a signature-verifier that only ever
   sees pre-authenticated headers, a scope-computer that returns
   an empty set on failure without any side-effect), add an
   allowlist entry with:
      • file (relative to /app/backend)
      • function name
      • exact purpose
      • why async directory validation is not required
      • risk owner

**Companion test**

``test_flr_allowlist_entries_still_exist`` — every allowlist
entry must reference a real function so the allowlist doesn't
rot silently.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


BACKEND_ROOT = Path("/app/backend")
SYNC_VALIDATOR = "_is_valid_admin_token"
ASYNC_VALIDATORS = {
    "_is_valid_directory_admin_token_async",
    "is_valid_admin_token_async",  # factory param name used inside gate factories
}


# ─────────────────────────────────────────────────────────────────
# Allowlist — every entry MUST have a written reason. Reviewers:
# reject PRs that add an entry without demonstrating that the
# helper is machine-internal and cannot authorize an operator
# request.
# ─────────────────────────────────────────────────────────────────
class Reason:
    """Structured allowlist reason. Keeps the invariant honest by
    requiring every field to be populated. Empty strings fail."""

    def __init__(self, purpose: str, why_no_async: str, risk_owner: str) -> None:
        assert purpose.strip(), "empty purpose"
        assert why_no_async.strip(), "empty why_no_async"
        assert risk_owner.strip(), "empty risk_owner"
        self.purpose = purpose
        self.why_no_async = why_no_async
        self.risk_owner = risk_owner


INTERNAL_ALLOWLIST: Dict[Tuple[str, str], Reason] = {
    # `server.py::_is_valid_admin_token` is the function DEFINITION
    # itself — obviously exempt from the "must also invoke async"
    # rule since it IS the sync helper.
    ("server.py", "_is_valid_admin_token"): Reason(
        purpose="Legacy sync HMAC validator — the retired sentinel itself.",
        why_no_async="This IS the sync helper; adding an async call inside "
                     "its own body would be circular. Callers must pair the "
                     "async validator, not the definition.",
        risk_owner="platform-core",
    ),

    # `lib/prepared_by_resolver.py::_is_valid_admin_token` is a
    # LOCAL RE-EXPORT that delegates to server.py's sync helper.
    # Same reasoning: it's the helper, not an authorization site.
    ("lib/prepared_by_resolver.py", "_is_valid_admin_token"): Reason(
        purpose="Local delegating wrapper to server.py::_is_valid_admin_token.",
        why_no_async="This is a naming shim, not an authorization site. The "
                     "real gate lives at prepared_by_resolver.resolve() where "
                     "admin identity is only used to select a DEFAULT "
                     "author label — the write path is already gated by an "
                     "async-validated dependency elsewhere.",
        risk_owner="platform-core",
    ),
}


# ─────────────────────────────────────────────────────────────────
# Scanner
# ─────────────────────────────────────────────────────────────────
def _iter_backend_files() -> List[Path]:
    out: List[Path] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        if rel.startswith(("tests/", "scripts/", "migrations/", "backups/")):
            continue
        if "__pycache__" in rel or ".venv" in rel:
            continue
        out.append(path)
    return out


def _iter_calls_with_enclosing_fn(tree: ast.AST) -> List[Tuple[ast.FunctionDef | None, ast.Call]]:
    hits: List[Tuple[ast.FunctionDef | None, ast.Call]] = []

    def visit(node: ast.AST, enc: ast.FunctionDef | None) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enc = node
        if isinstance(node, ast.Call):
            hits.append((enc, node))
        for child in ast.iter_child_nodes(node):
            visit(child, enc)

    visit(tree, None)
    return hits


def _call_uses_sync_validator(call: ast.Call) -> bool:
    """True if this call INVOKES the sync validator as a function."""
    fn = call.func
    if isinstance(fn, ast.Name) and fn.id == SYNC_VALIDATOR:
        return True
    if isinstance(fn, ast.Attribute) and fn.attr == SYNC_VALIDATOR:
        return True
    return False


def _call_passes_sync_validator_positionally(call: ast.Call) -> bool:
    """True if this call PASSES the sync validator as an argument
    (positional or keyword) — this is the gate-factory wiring pattern
    ``make_require_X(db, _is_valid_admin_token)``.
    """
    for a in call.args:
        if isinstance(a, ast.Name) and a.id == SYNC_VALIDATOR:
            return True
    for kw in call.keywords:
        if isinstance(kw.value, ast.Name) and kw.value.id == SYNC_VALIDATOR:
            return True
    return False


def _factory_call_also_passes_async_validator(call: ast.Call) -> bool:
    """For factory-wiring callsites: True if the SAME call ALSO
    threads a known async admin validator through its kwargs or
    positional args. This is the "correctly wired" shape.
    """
    for a in call.args:
        if isinstance(a, ast.Name) and a.id in ASYNC_VALIDATORS:
            return True
    for kw in call.keywords:
        if isinstance(kw.value, ast.Name) and kw.value.id in ASYNC_VALIDATORS:
            return True
    return False


def _function_references_async_validator(fn: ast.FunctionDef | None) -> bool:
    """True if the enclosing function body references any known
    async admin-token validator symbol."""
    if fn is None:
        return False
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and node.id in ASYNC_VALIDATORS:
            return True
        if isinstance(node, ast.Attribute) and node.attr in ASYNC_VALIDATORS:
            return True
    return False


def _collect_violations() -> List[str]:
    violations: List[str] = []
    for path in _iter_backend_files():
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:  # pragma: no cover
            violations.append(f"{rel}: syntax error — {e}")
            continue
        # Build a set of async-validator symbols the module can see,
        # via any import; keeps false positives low for wrappers that
        # re-export the async validator with a different local name.
        for fn, call in _iter_calls_with_enclosing_fn(tree):
            if _call_uses_sync_validator(call):
                # Case (1) — direct sync call.
                if fn is None:
                    # Module-scope direct call — should not happen; fail.
                    violations.append(
                        f"{rel}:{call.lineno} · module-scope call to "
                        f"{SYNC_VALIDATOR}(...) has no enclosing "
                        f"function; unable to prove async pairing."
                    )
                    continue
                if _function_references_async_validator(fn):
                    continue
                if (rel, fn.name) in INTERNAL_ALLOWLIST:
                    continue
                violations.append(
                    f"{rel}:{call.lineno} in {fn.name}() invokes "
                    f"{SYNC_VALIDATOR}(...) without an accompanying "
                    f"reference to any of {sorted(ASYNC_VALIDATORS)}. "
                    f"Either add an async check or allowlist "
                    f"({rel!r}, {fn.name!r}) with a documented reason."
                )
            elif _call_passes_sync_validator_positionally(call):
                # Case (2) — factory wiring. The factory must ALSO
                # receive the async validator so it can fall through.
                if _factory_call_also_passes_async_validator(call):
                    continue
                fn_name = fn.name if fn else "<module>"
                violations.append(
                    f"{rel}:{call.lineno} in {fn_name}() wires "
                    f"{SYNC_VALIDATOR} into a gate factory without "
                    f"also threading an async validator ({sorted(ASYNC_VALIDATORS)}). "
                    f"Update the factory call to pass the async "
                    f"validator too (e.g. "
                    f"`is_valid_admin_token_async=_is_valid_directory_admin_token_async`)."
                )
    return violations


def test_no_retired_sync_admin_validator_alone() -> None:
    """The retired sync ``_is_valid_admin_token`` must never
    authorize an admin request without an accompanying async
    validator. See module docstring for full doctrine."""
    violations = _collect_violations()
    if violations:
        joined = "\n  • " + "\n  • ".join(violations)
        pytest.fail(
            "TRACK 28.03E invariant: standalone retired sync admin "
            f"validator authorization paths discovered ({len(violations)}):"
            f"{joined}\n\nFix each callsite by adding the async "
            "validator OR extend INTERNAL_ALLOWLIST with a "
            "documented, machine-internal reason."
        )


def test_admin_gate_allowlist_entries_still_exist() -> None:
    """Every allowlist entry must reference a real function to
    prevent silent rot."""
    stale: List[str] = []
    for (rel, fn_name), reason in INTERNAL_ALLOWLIST.items():
        assert isinstance(reason, Reason), "malformed allowlist entry"
        p = BACKEND_ROOT / rel
        if not p.exists():
            stale.append(f"{rel} · file missing · fn={fn_name}")
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError:
            continue
        names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
        if fn_name not in names:
            stale.append(f"{rel} · fn={fn_name} not found in file")
    if stale:
        joined = "\n  • " + "\n  • ".join(stale)
        pytest.fail(f"Stale admin-gate allowlist entries:{joined}")
