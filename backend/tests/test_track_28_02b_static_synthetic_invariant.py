"""TRACK 28.02B · Static invariant — every read on ``daily_reports`` must
either apply ``apply_synthetic_dr_exclusion`` OR be explicitly allowlisted
with a documented admin-audit / internal-only reason.

**Why this test exists.** Track 28.02B discovered three P1 leaks
(``list_daily_reports_csv``, ``global_search.run_daily_reports``,
``operations_center_command`` + ``dispatch_command_center`` +
``shop_intel``) where an operational read path silently drifted out
of the TRACK 24.9 synthetic-exclusion coverage. The single JSON list
correctly filtered; the CSV twin did not. That class of defect is
now impossible to reintroduce without an explicit code-review
decision — this test fails CI if any *new* read path on
``daily_reports`` omits the filter and is not on the allowlist.

**Rules.**
* Any function containing a call to
  ``db.daily_reports.<verb>(...)`` where ``verb`` is a read verb
  (``find``, ``aggregate``, ``count_documents``, ``distinct``)
  must ALSO contain a call to ``apply_synthetic_dr_exclusion`` **in
  the same function scope**, OR the ``(module, function)`` tuple must
  be present in :data:`INTERNAL_ALLOWLIST`.
* ``find_one({"id": X})`` and other identity-scoped lookups are NOT
  in scope — they are natural-key reads that must return whatever
  document holds that id regardless of visibility.
* Write verbs (``insert_one``, ``update_*``, ``delete_*``) are OUT
  of scope — the filter is a visibility contract, not an identity
  contract.
* ``scripts/`` and ``tests/`` and ``.venv`` are excluded — CLI +
  test harnesses legitimately need full visibility.

**Adding a new callsite.**
1. Prefer applying ``apply_synthetic_dr_exclusion`` — that is 99% of
   the time the correct behaviour.
2. If you *genuinely* need to see synthetic rows (admin forensics,
   audit reports, sync scripts, health probes that count everything
   deliberately), add ``(rel_path, function_name)`` to
   :data:`INTERNAL_ALLOWLIST` with a one-line reason describing why
   the invariant should not apply here.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


BACKEND_ROOT = Path("/app/backend")
READ_VERBS = {"find", "aggregate", "count_documents", "distinct"}
FILTER_HELPER = "apply_synthetic_dr_exclusion"


# ─────────────────────────────────────────────────────────────────
# Allowlist — every entry MUST have a written reason. Reviewers:
# reject PRs that add an entry without a defensible reason.
# ─────────────────────────────────────────────────────────────────
INTERNAL_ALLOWLIST: Dict[Tuple[str, str], str] = {
    # ─── Admin forensics / audit ─────────────────────────────────
    ("routes/admin_dr_delivery_forensics.py", "dr_delivery_forensics"): (
        "Admin delivery-pipeline forensics — needs full visibility "
        "including synthetic rows to trace routing decisions."
    ),
    ("routes/admin_pm_coverage.py", "pm_email_coverage"): (
        "Admin PM coverage audit — enumerates every project_number "
        "ever recorded to expose PM-assignment gaps."
    ),
    ("routes/payroll_variance.py", "build_variance_rows"): (
        "Payroll audit — cross-checks every recorded DR against "
        "payroll; project scope is applied one layer above."
    ),
    ("routes/governance.py", "_detect_daily_report_crew_linkage"): (
        "Governance audit — internal employee_id linkage rollup that "
        "must see synthetic rows to expose them on legacy dashboards."
    ),
    # ─── Health probes (must count real DB traffic incl. synthetic) ─
    ("services/operations_control/health.py", "_dr_recent"): (
        "OCC health probe — counts total recent writes to detect a "
        "back-end outage; synthetic writes are still real DB traffic."
    ),
    ("services/operations_control/daily_reports.py", "_dr_health"): (
        "Internal DR volumetric counters for OCC platform-runtime "
        "cards — measures backend traffic, not operator visibility."
    ),
    # ─── Rollup libraries — caller supplies scope, filter applied "
    # one level up in every caller (pm_command_center, safety_portal,
    # admin dashboards). Keeping this file scope-agnostic is by design.
    ("lib/daily_report_rollup.py", "rollup_window"): (
        "Rollup helper — accepts caller-supplied query; the caller is "
        "responsible for adding the synthetic filter. Every real "
        "caller (pm_command_center + hr_portal + safety_portal) does."
    ),
    # ─── Excavation write-time link resolver — the submitting "
    # foreman needs their exact DR (real or synthetic training) to link.
    ("routes/trench_safety/excavations.py", "public_submit"): (
        "Excavation → DR write-time linker; needs to resolve the "
        "foreman's own DR (which may be synthetic during a training "
        "run) to link the excavation to. Never surfaces DRs to a "
        "user; the link is one-directional."
    ),
    # ─── Dispatch scope is per-driver / per-project, not per-visibility. ─
    ("routes/dispatch_driver.py", "assignment_lookups_route"): (
        "Dispatch driver assignment lookups — internal rollup scoped "
        "to a specific driver; synthetic DRs carry no driver "
        "assignments so they cannot cross-contaminate naturally."
    ),
    ("routes/dispatch_haul_ledger.py", "haul_ledger"): (
        "Dispatch haul ledger — scoped to per-project haul cycles; "
        "synthetic DRs carry no haul cycles."
    ),
    ("routes/dispatch_portal_auth.py", "dispatch_daily_reports"): (
        "Dispatch portal DR — driver-scoped read; synthetic DRs "
        "carry no driver linkage and never surface here."
    ),
    # ─── Operational records archive is an HR read-only audit. ────
    ("routes/operational_records.py", "list_records"): (
        "Operational records HR archive — audit surface that must "
        "reflect every recorded operational transaction."
    ),
    # ─── Non-visibility identity/write helpers. ───────────────────
    ("routes/daily_reports.py", "get_daily_report"): (
        "Identity-scoped GET-by-id; the caller has a specific id."
    ),
    ("routes/daily_reports.py", "next_daily_report_number"): (
        "Doc-id preview — reads doc_id_counters; DR read is a "
        "counter sanity-check that must count every row."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Discovery
# ─────────────────────────────────────────────────────────────────
def _iter_backend_files() -> List[Path]:
    """Yield every backend .py file except tests, scripts, migrations."""
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
    """Return (containing_function, call) pairs where the call matches
    ``<something>.daily_reports.<read_verb>(...)``.

    We climb the AST recording the nearest enclosing function so we
    can check for the filter helper in the same scope.
    """
    hits: List[Tuple[ast.FunctionDef, ast.Call]] = []

    def visit(node: ast.AST, enclosing_fn: ast.FunctionDef | None) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enclosing_fn = node
        if isinstance(node, ast.Call):
            fn = node.func
            # Match `<expr>.daily_reports.<read_verb>(...)`
            if isinstance(fn, ast.Attribute) and fn.attr in READ_VERBS:
                receiver = fn.value  # <expr>.daily_reports
                if (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "daily_reports"
                    and enclosing_fn is not None
                ):
                    hits.append((enclosing_fn, node))
        for child in ast.iter_child_nodes(node):
            visit(child, enclosing_fn)

    visit(tree, None)
    return hits


def _function_uses_filter(fn: ast.FunctionDef) -> bool:
    """True if ``apply_synthetic_dr_exclusion`` is CALLED anywhere in
    this function's body (including nested calls)."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == FILTER_HELPER:
                return True
            if isinstance(f, ast.Attribute) and f.attr == FILTER_HELPER:
                return True
    return False


def _classify_call(call: ast.Call) -> str:
    """Give the read verb + a heuristic 'identity-scoped' flag.

    ``find_one({"id": X})`` / ``find_one({"doc_id": X})`` — natural
    key by id — are excluded from the invariant since the caller is
    resolving a specific record.
    """
    verb = call.func.attr  # type: ignore[attr-defined]
    # Note: we already filtered READ_VERBS above, so verb is one of
    # find, aggregate, count_documents, distinct.
    return verb


def _is_identity_scoped_find(call: ast.Call) -> bool:
    """A ``find`` call whose first positional arg is an ``id``/``doc_id``
    equality dict is an identity-scoped lookup — the caller already
    has the primary key and needs whichever record holds it.
    """
    if not call.args:
        return False
    first = call.args[0]
    if not isinstance(first, ast.Dict):
        return False
    for k in first.keys:
        if isinstance(k, ast.Constant) and k.value in {"id", "doc_id"}:
            # Only if the dict is a *pure* id filter (no other keys
            # that would be scope filters).
            if len(first.keys) == 1:
                return True
    return False


# ─────────────────────────────────────────────────────────────────
# Test surface
# ─────────────────────────────────────────────────────────────────
def _collect_violations() -> List[str]:
    violations: List[str] = []
    for path in _iter_backend_files():
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:  # pragma: no cover
            violations.append(f"{rel}: syntax error — {e}")
            continue
        hits = _find_read_callsites(tree)
        for fn, call in hits:
            verb = _classify_call(call)
            # find_one({"id": X}) is a natural-key lookup — skip.
            if verb == "find" and _is_identity_scoped_find(call):
                continue
            if _function_uses_filter(fn):
                continue
            key = (rel, fn.name)
            if key in INTERNAL_ALLOWLIST:
                continue
            violations.append(
                f"{rel}:{call.lineno} in {fn.name}() calls "
                f"db.daily_reports.{verb}(...) without applying "
                f"{FILTER_HELPER}. Either wrap the query in "
                f"{FILTER_HELPER}(...) or add ({rel!r}, {fn.name!r}) "
                f"to INTERNAL_ALLOWLIST with a documented reason."
            )
    return violations


def test_no_new_daily_reports_read_omits_synthetic_exclusion() -> None:
    """Every read path on ``daily_reports`` must apply
    ``apply_synthetic_dr_exclusion`` or be explicitly allowlisted."""
    violations = _collect_violations()
    if violations:
        joined = "\n  • " + "\n  • ".join(violations)
        pytest.fail(
            "TRACK 28.02B invariant: unfiltered read on daily_reports "
            f"discovered ({len(violations)}):{joined}\n\nFix the "
            "callsite or extend INTERNAL_ALLOWLIST with a documented "
            "reason."
        )


def test_allowlist_entries_still_exist() -> None:
    """Every allowlist entry must reference a real function so the
    allowlist doesn't rot silently. If a file is renamed or a function
    deleted, force an update to the allowlist rather than let a stale
    exemption drift."""
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
        pytest.fail(f"Stale allowlist entries:{joined}")
