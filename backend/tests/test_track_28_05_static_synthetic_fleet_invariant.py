"""TRACK 28.05 · Session 1 · Static invariant.

Lock the Session 1 filter-application decisions in place so they
cannot silently regress. Session 2 will expand this to a full
AST-scanner across every ``db.{equipment_master, dispatch_assignments,
fleet_defects, equipment_inspections}`` read callsite (mirrors the
28.02B / 28.03 / 28.04 doctrine).

Session 1 scope — verify these six SPECIFIC endpoints import + apply
the canonical synthetic filter:

  * ``server.py::list_equipment_master``            → equipment
  * ``routes/fleet_ops.py::list_fleet_units``       → equipment
  * ``routes/fleet_ops.py::dispatch_fleet_status``  → equipment
  * ``routes/fleet_ops.py::shop_defects``           → fleet_defect
  * ``routes/dispatch_lifecycle.py::get_board``     → dispatch
  * ``routes/dispatch_lifecycle.py::list_assignments`` → dispatch
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Set

import pytest


BACKEND_ROOT = Path("/app/backend")

# (rel_path, function_name, expected_filter_helper)
SESSION_1_LOCKS = [
    ("server.py", "list_equipment_master", "apply_synthetic_equipment_exclusion"),
    ("routes/fleet_ops.py", "list_fleet_units", "apply_synthetic_equipment_exclusion"),
    ("routes/fleet_ops.py", "dispatch_fleet_status", "apply_synthetic_equipment_exclusion"),
    ("routes/fleet_ops.py", "shop_defects", "apply_synthetic_fleet_defect_exclusion"),
    ("routes/dispatch_lifecycle.py", "get_board", "apply_synthetic_dispatch_exclusion"),
    ("routes/dispatch_lifecycle.py", "list_assignments", "apply_synthetic_dispatch_exclusion"),
]


def _function_names_calling(fn_node: ast.AST) -> Set[str]:
    names: Set[str] = set()
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names.add(f.id)
            elif isinstance(f, ast.Attribute):
                names.add(f.attr)
    return names


def _find_function(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    return None


@pytest.mark.parametrize("rel_path,fn_name,expected_helper", SESSION_1_LOCKS)
def test_session1_endpoint_applies_synthetic_filter(rel_path, fn_name, expected_helper):
    """The specific Session 1 endpoints must call the canonical
    synthetic filter helper. If someone removes the call the test
    fails, forcing a review."""
    p = BACKEND_ROOT / rel_path
    assert p.exists(), f"expected file missing: {rel_path}"
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    fn = _find_function(tree, fn_name)
    assert fn is not None, (
        f"TRACK 28.05 Session 1 lock: function {fn_name} not found in {rel_path}"
    )
    names = _function_names_calling(fn)
    assert expected_helper in names, (
        f"TRACK 28.05 regression: {rel_path}::{fn_name} does not call "
        f"{expected_helper}. This endpoint must apply the canonical "
        f"synthetic Fleet/Dispatch filter (see lib/synthetic_fleet_filter.py). "
        f"Do not remove the filter — synthetic TEST_28_05_* rows will "
        f"leak to operator screens."
    )


def test_synthetic_fleet_filter_module_exists():
    """The canonical filter module must be present + expose the four
    documented helpers."""
    p = BACKEND_ROOT / "lib" / "synthetic_fleet_filter.py"
    assert p.exists(), "TRACK 28.05: lib/synthetic_fleet_filter.py missing"
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    funcs = {
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for expected in (
        "apply_synthetic_equipment_exclusion",
        "apply_synthetic_inspection_exclusion",
        "apply_synthetic_dispatch_exclusion",
        "apply_synthetic_fleet_defect_exclusion",
        "is_synthetic_fleet_doc",
    ):
        assert expected in funcs, f"missing helper: {expected}"
