"""TRACK 28.03 · Static invariant — every read on
``field_leadership_records`` must either apply
``apply_synthetic_flr_exclusion`` OR be explicitly allowlisted with a
documented admin-audit / internal-only reason.

Mirrors ``test_track_28_02b_static_synthetic_invariant.py`` but for the
Field Leadership collection. See that file's docstring for full
context on the AST scanner + allowlist doctrine.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


BACKEND_ROOT = Path("/app/backend")
READ_VERBS = {"find", "aggregate", "count_documents", "distinct"}
FILTER_HELPER = "apply_synthetic_flr_exclusion"


INTERNAL_ALLOWLIST: Dict[Tuple[str, str], str] = {
    # ─── Write-time linker: needs full visibility to correlate ─────
    # equipment_return records against their originating checkout,
    # even when the checkout is a synthetic training fixture.
    ("legacy_imports_equipment_checkout.py", "detect_duplicate"): (
        "Legacy CSV-import duplicate detector — write-side; must "
        "see every existing FL record to prevent double-imports "
        "including synthetic ones from previous certification runs."
    ),
    ("legacy_imports_equipment_checkout.py", "compute_pilot_debrief"): (
        "Legacy CSV-import pilot debrief — internal one-shot rollup "
        "that reports how many synthetic vs real rows were imported."
    ),
    # ─── FL admin equipment lookup — write-time. ────────────────────
    ("routes/field_leadership.py", "lookup_equipment_by_serial"): (
        "Equipment-return write-time serial resolver — needs to find "
        "the original checkout even when that checkout is a "
        "synthetic training fixture, so that a return is linked to "
        "the correct history record."
    ),
}


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


def _find_read_callsites(tree: ast.AST) -> List[Tuple[ast.FunctionDef, ast.Call]]:
    hits: List[Tuple[ast.FunctionDef, ast.Call]] = []

    def visit(node: ast.AST, enc: ast.FunctionDef | None) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enc = node
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr in READ_VERBS:
                receiver = fn.value
                if (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "field_leadership_records"
                    and enc is not None
                ):
                    hits.append((enc, node))
        for child in ast.iter_child_nodes(node):
            visit(child, enc)

    visit(tree, None)
    return hits


def _function_uses_filter(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == FILTER_HELPER:
                return True
            if isinstance(f, ast.Attribute) and f.attr == FILTER_HELPER:
                return True
    return False


def _is_identity_scoped_find(call: ast.Call) -> bool:
    if not call.args:
        return False
    first = call.args[0]
    if not isinstance(first, ast.Dict):
        return False
    if len(first.keys) != 1:
        return False
    k = first.keys[0]
    return isinstance(k, ast.Constant) and k.value in {"id", "doc_id"}


def _collect_violations() -> List[str]:
    violations: List[str] = []
    for path in _iter_backend_files():
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:  # pragma: no cover
            violations.append(f"{rel}: syntax error — {e}")
            continue
        for fn, call in _find_read_callsites(tree):
            verb = call.func.attr  # type: ignore[attr-defined]
            if verb == "find" and _is_identity_scoped_find(call):
                continue
            if _function_uses_filter(fn):
                continue
            if (rel, fn.name) in INTERNAL_ALLOWLIST:
                continue
            violations.append(
                f"{rel}:{call.lineno} in {fn.name}() calls "
                f"db.field_leadership_records.{verb}(...) without "
                f"applying {FILTER_HELPER}. Either wrap the query "
                f"or add ({rel!r}, {fn.name!r}) to INTERNAL_ALLOWLIST."
            )
    return violations


def test_no_new_flr_read_omits_synthetic_exclusion() -> None:
    violations = _collect_violations()
    if violations:
        joined = "\n  • " + "\n  • ".join(violations)
        pytest.fail(
            "TRACK 28.03 invariant: unfiltered read on "
            f"field_leadership_records discovered ({len(violations)}):"
            f"{joined}\n\nFix the callsite or extend "
            "INTERNAL_ALLOWLIST with a documented reason."
        )


def test_flr_allowlist_entries_still_exist() -> None:
    stale: List[str] = []
    for (rel, fn_name), reason in INTERNAL_ALLOWLIST.items():
        assert isinstance(reason, str) and reason.strip(), (
            f"Allowlist entry ({rel!r}, {fn_name!r}) has empty reason."
        )
        p = BACKEND_ROOT / rel
        if not p.exists():
            stale.append(f"{rel} (file missing) · fn={fn_name}")
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
        pytest.fail(f"Stale FLR allowlist entries:{joined}")
