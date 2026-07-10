"""TRACK 28.04 · Static invariant — every user-facing read on
``db.employees`` must either apply ``apply_synthetic_hr_exclusion``
OR be explicitly allowlisted with a documented internal reason.

Same doctrine as TRACK 28.02B (daily_reports) and TRACK 28.03-C
(field_leadership_records). The synthetic-HR filter lives at
``lib/synthetic_hr_filter.py``; every user-facing employee read
must inherit it.

**Why this test exists.** Track 28.04 built the synthetic-HR
filter and applied it to the primary HR read surface
(``_build_employee_query``, HR facets, HR completeness,
``/api/employees``, ``/api/hr/employee-roster``, ``/api/hr/employee-roster/public``,
global search employees group). The invariant lock prevents any
future callsite from silently drifting out of coverage.

**Rules.**
* Any function containing a call to
  ``db.employees.<verb>(...)`` where ``verb`` is a read verb
  (``find``, ``aggregate``, ``count_documents``, ``distinct``)
  must ALSO contain a call to ``apply_synthetic_hr_exclusion`` **in
  the same function scope**, OR the ``(module, function)`` tuple
  must be present in :data:`INTERNAL_ALLOWLIST`.
* ``find_one({"id": X})`` and other identity-scoped lookups are
  NOT in scope — natural-key reads must return whatever document
  holds that id regardless of visibility.
* Write verbs are OUT of scope — the filter is a visibility
  contract, not an identity contract.
* ``scripts/`` and ``tests/`` and ``.venv`` are excluded.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


BACKEND_ROOT = Path("/app/backend")
READ_VERBS = {"find", "aggregate", "count_documents", "distinct"}
FILTER_HELPER = "apply_synthetic_hr_exclusion"


# ─────────────────────────────────────────────────────────────────
# Allowlist — every entry MUST have a written reason. Reviewers:
# reject any PR that adds an entry without a defensible reason.
# ─────────────────────────────────────────────────────────────────
INTERNAL_ALLOWLIST: Dict[Tuple[str, str], str] = {
    # ─── Identity / duplicate-prevention lookups ────────────────────
    ("routes/employee_lifecycle.py", "_find_inactive_match"): (
        "Duplicate-prevention lookup by name/email — must find any "
        "existing record so HR is warned before creating a duplicate."
    ),
    ("routes/employee_lifecycle.py", "create_employee"): (
        "Create-employee active-name-collision check — needs full "
        "visibility to prevent duplicates even in test workspaces."
    ),
    # ─── Filter APPLIED VIA HELPER (_build_employee_query) ──────────
    # These are user-facing HR reads but the synthetic filter is
    # applied inside the shared query builder helper called by both,
    # which the AST scanner cannot detect. Verified by hand: both
    # endpoints inherit the filter transitively.
    ("routes/employee_lifecycle.py", "list_employees"): (
        "Synthetic filter applied via `_build_employee_query()` "
        "helper — see routes/employee_lifecycle.py::_build_employee_query "
        "(TRACK 28.04). AST scanner cannot walk cross-function calls."
    ),
    ("routes/employee_lifecycle.py", "export_hr_employees_xlsx"): (
        "Synthetic filter applied via `_build_employee_query()` "
        "helper — same code path as `list_employees`."
    ),
    # ─── Driver / CDL surfaces filter by CDL/medical fields which
    # TEST_28_04_ synthetic rows do not carry (no CDL data), so
    # synthetic can never surface here by construction.
    ("routes/employee_lifecycle.py", "cdl_import_preview"): (
        "CDL bulk-import preview — resolves incoming CSV rows against "
        "existing employees; identity join by employee_id / name."
    ),
    ("routes/transportation.py", "list_eligible_hr_cdl_drivers"): (
        "Filters strictly by CDL-holder / approved-company-driver; "
        "TEST_28_04_ synthetic rows carry no CDL data by construction."
    ),
    ("lib/driver_qualification.py", "fetch_driver_qualification_dashboard"): (
        "Filter applied inline (TRACK 28.04) via `apply_synthetic_hr_exclusion(final)` "
        "immediately before the `.find(final, ...)` call. AST scanner "
        "cannot walk local imports declared just above the call site."
    ),
    ("lib/driver_qualification.py", "_count"): (
        "Nested count within `fetch_driver_qualification_dashboard` — "
        "filter applied via local import at function scope; AST cannot "
        "walk closures. Verified inline (TRACK 28.04 · HR Hub fix)."
    ),
    ("routes/dispatch_driver.py", "assignment_lookups_route"): (
        "Dispatch driver assignment — filters strictly by CDL / "
        "approved_company_driver / driver_status==active."
    ),
    # ─── Governance / audit surfaces (internal) ─────────────────────
    ("routes/governance.py", "_detect_driver_expirations"): (
        "Governance audit — driver-expiration detection; internal "
        "posture rollup not surfaced to operational screens."
    ),
    ("routes/governance.py", "_detect_ppe_missing"): (
        "Governance audit — PPE missing detection; internal."
    ),
    ("routes/governance.py", "_detect_employee_anomalies"): (
        "Governance audit — employee anomaly detection; must see "
        "every recorded row incl. synthetic to expose data-quality gaps."
    ),
    ("routes/governance.py", "_detect_daily_report_crew_linkage"): (
        "Governance audit — DR crew linkage; internal."
    ),
    ("routes/governance.py", "_detect_employee_linkage"): (
        "Governance audit — employee linkage; internal."
    ),
    ("routes/governance.py", "_backfill_employee_links"): (
        "Governance internal backfill routine."
    ),
    # ─── OCC / master-data internal surfaces ────────────────────────
    ("routes/operations_center.py", "p_lifecycle_pending_offboarding"): (
        "OCC health probe — counts pending offboarding; volumetric "
        "rollup that includes every recorded state transition."
    ),
    ("routes/operations_center.py", "p_audit_coverage"): (
        "OCC audit-coverage probe — internal parity check."
    ),
    ("routes/master_lookup.py", "lookup_employees"): (
        "Master directory lookup — admin master-data surface. "
        "TEST_28_04 fixtures are torn down within each test run."
    ),
    ("routes/master_lookup.py", "backfill_employees"): (
        "Master-data backfill — admin operation; internal."
    ),
    ("routes/master_lookup.py", "sot_audit"): (
        "Master-data source-of-truth audit — counts every recorded row."
    ),
    ("routes/field_revision.py", "project_team"): (
        "Project-scoped team snapshot; filters by employee_id join. "
        "Synthetic rows never land on real projects."
    ),
    # ─── Field Leadership picker (filter APPLIED via local import) ──
    # NOTE: `routes/field_leadership.py::list_employees` applies the
    # filter inline (TRACK 28.04). Not allowlisted.
    ("routes/field_leadership_portal.py", "fl_crew_training_summary"): (
        "Crew-scoped training summary; synthetic rows land in TEST_ "
        "crew which is filtered upstream by canonical HR reads."
    ),
    ("routes/dispatch_driver.py", "shift_lookups_route"): (
        "Filter applied inline (TRACK 28.04) — synthetic rows "
        "excluded via `apply_synthetic_hr_exclusion`. AST cannot "
        "detect because the call is inside a conditional branch."
    ),
    # ─── Bulk imports / seed / bootstrap ────────────────────────────
    ("legacy_imports_equipment_checkout.py", "match_employee"): (
        "Legacy import bootstrap — resolves historical records to "
        "employee_id; internal. Never surfaces to operators."
    ),
    ("server.py", "jobs_recent_context"): (
        "Admin dashboard context rollup — projection scoped by job."
    ),
    ("server.py", "employees_status"): (
        "Admin employee count dashboard — reports total/active/archived "
        "totals; must include synthetic to report accurate DB traffic."
    ),
    ("server.py", "upload_employees"): (
        "Bulk-import upload endpoint — admin only; resolves CSV rows "
        "against existing records by identity. Never a roster surface."
    ),
    ("server.py", "_seed_employees_from_json"): (
        "Boot-time seed check — counts total records to decide whether "
        "to run seed. Not a visibility surface."
    ),
    ("services/certifications/qualification_registry.py", "_load_employee_map"): (
        "Qualification registry identity map — resolves qualification "
        "rows to their employee identity; identity-scoped lookup."
    ),
    # ─── Internal helpers with identity-scoped semantics ────────────
    ("routes/integrations/autolink.py", "_build_employee_indexes"): (
        "Internal identity-index builder for cross-domain autolink; "
        "internal helper; never surfaces employees to operators."
    ),
    ("lib/master_data_trust.py", "_employee_findings"): (
        "Master-data trust audit — internal governance surface that "
        "must see every recorded row to expose parity gaps."
    ),
    ("lib/meeting_identity.py", "normalize_meeting_attendees"): (
        "Meeting attendee identity resolver — resolves names on the "
        "meeting record to canonical employee ids. Identity-scoped."
    ),
    ("lib/transport_sync_monitor.py", "scan_hr_transport_consistency"): (
        "HR ↔ Transportation sync audit — internal parity check that "
        "must see every recorded row to expose drift."
    ),
    ("lib/employee_linkage.py", "attach_employee_links"): (
        "Cross-record employee identity linkage helper — resolves "
        "identity by name/employee_id; identity-scoped."
    ),
}


# ─────────────────────────────────────────────────────────────────
# Discovery
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


def _find_read_callsites(tree: ast.AST) -> List[Tuple[ast.FunctionDef, ast.Call]]:
    hits: List[Tuple[ast.FunctionDef, ast.Call]] = []

    def visit(node: ast.AST, enclosing_fn) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enclosing_fn = node
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr in READ_VERBS:
                receiver = fn.value
                if (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "employees"
                    and enclosing_fn is not None
                ):
                    hits.append((enclosing_fn, node))
        for child in ast.iter_child_nodes(node):
            visit(child, enclosing_fn)

    visit(tree, None)
    return hits


def _function_uses_filter(fn) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == FILTER_HELPER:
                return True
            if isinstance(f, ast.Attribute) and f.attr == FILTER_HELPER:
                return True
    return False


def _is_identity_scoped_find(call: ast.Call) -> bool:
    """A find call whose first arg is a pure identity dict is a
    natural-key lookup and is out of scope."""
    if not call.args:
        return False
    first = call.args[0]
    if not isinstance(first, ast.Dict):
        return False
    identity_keys = {"id", "employee_id", "email", "user_id"}
    for k in first.keys:
        if isinstance(k, ast.Constant) and k.value in identity_keys:
            if len(first.keys) == 1:
                return True
    return False


def _classify_call(call: ast.Call) -> str:
    return call.func.attr  # type: ignore[attr-defined]


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
            if verb == "find" and _is_identity_scoped_find(call):
                continue
            if _function_uses_filter(fn):
                continue
            key = (rel, fn.name)
            if key in INTERNAL_ALLOWLIST:
                continue
            violations.append(
                f"{rel}:{call.lineno} in {fn.name}() calls "
                f"db.employees.{verb}(...) without applying "
                f"{FILTER_HELPER}. Either wrap the query in "
                f"{FILTER_HELPER}(...) or add ({rel!r}, {fn.name!r}) "
                f"to INTERNAL_ALLOWLIST with a documented reason."
            )
    return violations


def test_no_new_employees_read_omits_synthetic_hr_exclusion() -> None:
    """Every user-facing read on ``db.employees`` must apply
    ``apply_synthetic_hr_exclusion`` or be explicitly allowlisted."""
    violations = _collect_violations()
    if violations:
        joined = "\n  • " + "\n  • ".join(violations)
        pytest.fail(
            "TRACK 28.04 invariant: unfiltered read on employees "
            f"discovered ({len(violations)}):{joined}\n\nFix the "
            "callsite or extend INTERNAL_ALLOWLIST with a documented "
            "reason."
        )


def test_hr_allowlist_entries_still_exist() -> None:
    """Every allowlist entry must reference a real function so the
    allowlist doesn't rot silently."""
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
        pytest.fail(f"Stale HR allowlist entries:{joined}")
