"""GD-0031 — Final-acceptance REPAIR-CYCLE guards (TD-0014, TD-0015, OPPC read-scope).

Falsifiable regression for the defects found at Independent Acceptance:
  TD-0014: trench compliance/utilization per-row surfaces emit a governed value+state
           (subset=0 -> NOT_APPLICABLE, never a fake 0%); frontend renders via governed cell.
  TD-0015: equipment master panel renders an error/UNAVAILABLE state on load failure,
           never a false "0 units / fleet empty".
  OPPC:    a system_administrator / global-scope actor gets global PROJECT READ, ordinary
           scope preserved, and the READ bypass never applies to write endpoints.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FE = os.path.join(REPO, "..", "frontend", "src")


# ---- TD-0014: trench compliance/utilization N/A-as-0 ----

def test_trench_utilization_row_emits_governed_state_backend():
    src = open(os.path.join(REPO, "routes", "trench_safety", "reports.py")).read()
    # utilization by_type routes through the governed rate (subset=0 -> N/A), not _safe_pct(...,max(,1))
    assert "compliance_rate(sub_used, len(subset))" in src
    assert '"utilization_state": _ustate' in src
    assert "_safe_pct(sub_used, max(len(subset), 1))" not in src  # old masking gone


def test_trench_frontend_renders_rows_via_governed_cell():
    src = open(os.path.join(FE, "pages", "trench_safety", "TrenchSafetyReports.jsx")).read()
    # no raw ${...pct}% row interpolation remains for the three MiniTables
    assert "${v.compliance_pct}%" not in src
    assert "${r.compliance_pct}%" not in src
    assert "${v.utilization_pct}%" not in src
    # rows go through the governed pctCell(value, state) which shows N/A / UNKNOWN
    assert "pctCell(v.compliance_pct, v.compliance_state)" in src
    assert "pctCell(v.utilization_pct, v.utilization_state)" in src
    assert 'data-testid="pct-cell-na"' in src


def test_compliance_rate_zero_eligible_is_not_applicable_not_zero():
    from lib.kpi_percent_complete import compliance_rate
    val, state = compliance_rate(0, 0)
    assert val is None and state == "NOT_APPLICABLE"   # zero eligible -> N/A, never 0%
    val2, state2 = compliance_rate(0, 5)
    assert val2 == 0.0 and state2 == "OK"              # measured zero with eligible>0 -> genuine 0%


# ---- TD-0015: equipment master false-empty ----

def test_equipment_panel_renders_error_state_not_zero():
    src = open(os.path.join(FE, "components", "EquipmentMasterPanel.jsx")).read()
    assert "loadError" in src
    assert "setLoadError(operationalError(e" in src
    # on load failure the total shows UNAVAILABLE and an explicit error, not 0 / empty fleet
    assert "UNAVAILABLE" in src
    assert 'data-testid="equipment-master-load-error"' in src


# ---- OPPC read-scope: system_administrator global READ, no write bypass ----

def test_oppc_read_scope_global_bypass_is_read_only():
    src = open(os.path.join(REPO, "routes", "oppc_execution.py")).read()
    # bypass gated on read_only + global scope only
    assert "read_only: bool = False" in src
    assert "if read_only:" in src
    assert "scope.is_admin" in src
    # GET (read) endpoints pass read_only=True; the write endpoints must NOT
    get_readonly = src.count("_ensure_project_access(db, project_number, actor, read_only=True)")
    assert get_readonly == 4, f"expected 4 read-only GET sites, found {get_readonly}"


def test_governance_global_scope_is_admin_semantics():
    # the canonical scope owner treats global (project_numbers is None) as admin (allows any project)
    from lib.enterprise_governance import GovernanceProjectScope
    glob = GovernanceProjectScope(is_admin=True, project_numbers=None)
    scoped = GovernanceProjectScope(is_admin=False, project_numbers=["20-07"])
    assert glob.allows("20-07") and glob.allows("99-99")       # global reads any project
    assert scoped.allows("20-07") and not scoped.allows("99-99")  # ordinary PM stays scoped
