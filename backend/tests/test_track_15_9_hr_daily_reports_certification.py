"""TRACK 15.9 — HR Daily Reports read-only certification.

These tests enforce the Five-Pillar contract for the HR Daily Reports
read-only surface delivered in iter332/iter336 and hardened in
Track 15.9:

  POWERFUL — list + detail endpoints, 6 filters, employee search,
             workforce-intel cross-link.
  SIMPLE   — single namespace `/api/hr/daily-reports`, single page
             component, no shadow report system.
  BEAUTIFUL— HR portal visual primitives (PortalShell, HrSideNavV2,
             paletteFor("hr")) reused; no custom-color drift.
  TRUSTED  — HR-token-only gate, no write verbs, no PDF/export
             affordances, least-privilege projection on detail
             (distribution_list excluded).
  PROVEN   — pre-existing 23 iter332/iter339 tests still green;
             this file adds 18 more.

Run:
    MONGO_URL=$URL DB_NAME=masci_safety_preview \
      python -m pytest tests/test_track_15_9_hr_daily_reports_certification.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_HR = ROOT / "backend" / "routes" / "hr_portal.py"
HR_PAGE = ROOT / "frontend" / "src" / "pages" / "HrDailyReports.jsx"
HR_HUB = ROOT / "frontend" / "src" / "pages" / "HrHub.jsx"
HR_NAV = ROOT / "frontend" / "src" / "components" / "hr" / "sidebar" / "HrSideNavV2.jsx"
HR_DEPS = ROOT / "backend" / "routes" / "hr_portal_deps.py"
APP_JS = ROOT / "frontend" / "src" / "App.js"


# ─────────────────────────────────────────────────────────── POWERFUL
def test_list_endpoint_supports_six_filters_and_keyword_search():
    """List route exposes the six operator-mandated filters plus the
    employee-name keyword search."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    block = re.search(r"async def hr_list_daily_reports\((.*?)\):",
                      src, re.DOTALL).group(1)
    for f in ("date_from", "date_to", "project", "employee",
              "subcontractor", "vendor", "report_number"):
        assert f in block, f"Missing filter: {f}"


def test_employee_filter_searches_nested_crew_members():
    """Employee search must look INSIDE masci_crews[].members[].name —
    not just at the top level — so HR can find any crew member."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    assert "masci_crews.members.name" in src


def test_subcontractor_and_vendor_filters_are_nested_regex():
    src = BACKEND_HR.read_text(encoding="utf-8")
    assert "subcontractors.name" in src
    assert "visitors.name" in src


def test_employee_accountability_endpoint_exists():
    """Phase 6 — workforce intelligence cross-link."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    assert "/hr/employee-accountability" in src
    assert "employee_name" in src


# ─────────────────────────────────────────────────────────── SIMPLE
def test_no_shadow_hr_daily_report_collection():
    """No separate HR-specific daily-report collection. HR reads from
    the canonical `daily_reports` collection. One source of truth."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    # The only collection name pattern for daily reports must be
    # `db.daily_reports`. No `db.hr_daily_reports` or similar.
    assert "db.hr_daily_reports" not in src
    assert "db.daily_reports_hr" not in src
    # Positive: must read from the canonical collection.
    assert "db.daily_reports.aggregate" in src
    assert "db.daily_reports.find_one" in src


def test_single_hr_daily_report_page_component():
    """One page file. No duplicate HR-DR pages."""
    assert HR_PAGE.exists()
    page_count = sum(1 for p in (ROOT / "frontend" / "src" / "pages").iterdir()
                     if p.is_file() and "DailyReport" in p.name and "Hr" in p.name)
    assert page_count == 1, f"Expected 1 HR-DR page, found {page_count}"


# ────────────────────────────────────────────────────────── BEAUTIFUL
def test_hr_dr_page_uses_portal_shell():
    src = HR_PAGE.read_text(encoding="utf-8")
    assert "PortalShell" in src
    assert "HrSideNavV2" in src


def test_hr_dr_page_uses_canonical_hr_palette():
    """No custom colors — uses paletteFor('hr') like every other HR page."""
    src = HR_PAGE.read_text(encoding="utf-8")
    assert 'paletteFor("hr")' in src


def test_hr_dr_page_kpi_strip_matches_hr_portal_pattern():
    """KPI strip must use the same `border-l-4 stripe` pattern as
    other HR cards — no custom card geometry."""
    src = HR_PAGE.read_text(encoding="utf-8")
    assert "border-l-4" in src
    assert "border-l-purple-700" in src  # HR brand stripe


def test_hr_dr_detail_uses_same_section_primitive():
    src = HR_PAGE.read_text(encoding="utf-8")
    # The Section helper is reused across panes — one visual primitive.
    assert "function Section(" in src


def test_hr_sidenav_includes_daily_reports_link():
    src = HR_NAV.read_text(encoding="utf-8")
    assert "/hr/daily-reports" in src
    assert "Daily Reports" in src


def test_hr_hub_tile_uses_canonical_clipboardlist_icon():
    """HR hub tile uses the same icon family (lucide-react ClipboardList)
    as the other HR cards (Employee Records, Training, Compliance)."""
    src = HR_HUB.read_text(encoding="utf-8")
    assert "ClipboardList" in src


# ─────────────────────────────────────────────────────────── TRUSTED
def test_hr_dr_routes_gated_by_require_hr_user_only():
    """Both endpoints depend ONLY on require_hr_user — no admin/PM/
    safety/dispatch fallback."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    for fn in ("hr_list_daily_reports", "hr_get_daily_report"):
        sig = re.search(rf"async def {fn}\((.*?)\):", src, re.DOTALL).group(1)
        assert "require_hr_user" in sig, fn
        for forbidden in ("require_admin", "require_pm", "require_safety",
                          "require_dispatch", "require_field_leadership",
                          "require_any_portal_token"):
            assert forbidden not in sig, f"{fn} uses {forbidden}"


def test_require_hr_user_rejects_all_other_tokens():
    """The HR-token resolver only inspects X-HR-Token. PM/Admin/Safety/
    Dispatch tokens are never even read."""
    src = HR_DEPS.read_text(encoding="utf-8")
    block = re.search(r"def make_require_hr_user\(.*?return _require_hr_user",
                      src, re.DOTALL).group(0)
    # Must only inspect X-HR-Token.
    assert 'alias="X-HR-Token"' in block
    # Must NOT fall back to other headers.
    for hdr in ("X-Admin-Token", "X-PM-Token", "X-Safety-Token",
                "X-Dispatch-Token", "X-Field-Leadership-Token",
                "Authorization"):
        assert hdr not in block, f"HR resolver leaks {hdr} fallback"


def test_no_hr_write_endpoints_on_daily_reports():
    """No POST/PUT/PATCH/DELETE under /api/hr/daily-reports."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    for verb in ("post", "put", "patch", "delete"):
        bad = f'@router.{verb}("/hr/daily-reports'
        assert bad not in src, f"Forbidden HR-DR write verb: {verb}"


def test_least_privilege_projection_strips_distribution_list():
    """Track 15.9 hardening — HR detail endpoint MUST project out
    `distribution_list` (PM's email CC list). HR has no rendering use
    case for outbound-comms recipients."""
    src = BACKEND_HR.read_text(encoding="utf-8")
    block = re.search(
        r"async def hr_get_daily_report\(.*?return doc",
        src, re.DOTALL,
    ).group(0)
    assert '"distribution_list": 0' in block, (
        "TRACK 15.9 detail projection must exclude distribution_list"
    )


def test_no_pdf_or_export_affordance_in_hr_dr_ui():
    """Phase 5 — HR DR detail page must NOT render PDF/export/email/
    approve/reject/edit/delete/submit/route buttons."""
    src = HR_PAGE.read_text(encoding="utf-8")
    for forbidden in ("Generate PDF", "Export PDF", "Send Email",
                      "EmailReport", "Approve Report", "Reject Report",
                      "Reopen Report", "Edit Report", "Delete Report",
                      "Submit Report", "Route Report"):
        assert forbidden not in src, (
            f"HR-DR page rendered forbidden control: {forbidden!r}"
        )


def test_no_pm_workflow_endpoints_under_hr_namespace():
    src = BACKEND_HR.read_text(encoding="utf-8")
    for forbidden in ("/hr/daily-reports/{report_id}/route",
                      "/hr/daily-reports/{report_id}/approve",
                      "/hr/daily-reports/{report_id}/reopen",
                      "/hr/daily-reports/{report_id}/pdf",
                      "/hr/daily-reports/{report_id}/email"):
        assert forbidden not in src, f"Forbidden HR workflow route: {forbidden}"


# ─────────────────────────────────────────────────────────── PROVEN
def test_app_registers_both_hr_daily_report_routes():
    src = APP_JS.read_text(encoding="utf-8")
    assert '/hr/daily-reports"' in src
    assert '/hr/daily-reports/:id"' in src
    assert "HrDailyReports" in src
    assert "HrDailyReportDetail" in src


def test_es_translations_present_for_hr_dr_strings():
    src = (ROOT / "frontend" / "src" / "lib" / "i18n.js").read_text(encoding="utf-8")
    for k in ('"Daily Reports Review":', '"Date from":', '"Date to":',
              '"Report number":', '"Subcontractor":', '"Vendor / Visitor":'):
        assert k in src, f"Missing ES translation for: {k}"


# ═══════════════════════════════════════════════════════════════════════════
# TRACK 15.9A · OPERATIONAL HARDENING — PM identity surfacing + new filters
# ═══════════════════════════════════════════════════════════════════════════
# These tests certify the Track 15.9A additions that take HR Daily Reports
# from "viewable" to "operationally complete":
#   • PM-of-record (name + email) surfaced via $lookup on `projects`.
#   • Superintendent surfaced from DR doc.
#   • 3 new filters: pm, superintendent, foreman.
#   • Company-wide visibility (no PM scope bleed-through from session).
#
# Run alongside the Track 15.9 tests above — same file, same fixture.


def _extract_function_body(src: str, fn_name: str) -> str:
    """Slice the source from `async def <fn_name>(` up to the next
    `@router.` decorator or `async def` definition. Reliable than
    non-greedy regex against multi-`return` bodies."""
    start = src.index(f"async def {fn_name}(")
    rest = src[start + 1:]
    # Find the next route definition or another async def.
    next_decorator = rest.find("    @router.")
    next_async = rest.find("    async def ")
    cuts = [c for c in (next_decorator, next_async) if c >= 0]
    end = min(cuts) if cuts else len(rest)
    return src[start:start + 1 + end]


class TestTrack15_9A_PmIdentitySurfacing:
    """PM identity must appear in BOTH list and detail responses."""

    def test_list_endpoint_projects_pm_name_and_pm_email(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        block = _extract_function_body(src, "hr_list_daily_reports")
        assert '"pm_name":' in block
        assert '"pm_email":' in block

    def test_list_endpoint_uses_projects_collection_lookup(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        block = _extract_function_body(src, "hr_list_daily_reports")
        # $lookup against `projects` collection on project_number.
        assert '"from": "projects"' in block
        assert '"localField": "project_number"' in block
        assert '"foreignField": "project_number"' in block

    def test_list_endpoint_projects_superintendent(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        block = _extract_function_body(src, "hr_list_daily_reports")
        # superintendent must be in the projection (top-level DR field).
        assert '"superintendent": 1' in block

    def test_detail_endpoint_enriches_with_pm_identity(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        block = _extract_function_body(src, "hr_get_daily_report")
        assert "db.projects.find_one" in block
        assert '"pm_name": 1, "pm_email": 1' in block
        assert 'doc["pm_name"]' in block
        assert 'doc["pm_email"]' in block


class TestTrack15_9A_NewFilters:
    """3 new filters: pm, superintendent, foreman."""

    def test_pm_filter_param_present(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        sig = re.search(
            r"async def hr_list_daily_reports\((.*?)\):",
            src, re.DOTALL,
        ).group(1)
        assert "pm: Optional[str]" in sig

    def test_superintendent_filter_param_present(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        sig = re.search(
            r"async def hr_list_daily_reports\((.*?)\):",
            src, re.DOTALL,
        ).group(1)
        assert "superintendent: Optional[str]" in sig

    def test_foreman_filter_param_present(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        sig = re.search(
            r"async def hr_list_daily_reports\((.*?)\):",
            src, re.DOTALL,
        ).group(1)
        assert "foreman: Optional[str]" in sig

    def test_pm_filter_searches_pm_name_or_pm_email_on_projects(self):
        """PM filter MUST resolve via the `projects` collection (PM is a
        property of the project, not the DR). Anti-pattern: searching
        `prepared_by` (which can be a foreman submitting on PM's behalf)."""
        src = BACKEND_HR.read_text(encoding="utf-8")
        block = _extract_function_body(src, "hr_list_daily_reports")
        # Find the PM-filter sub-block.
        pm_block = re.search(r"if pm:.*?match\.setdefault", block, re.DOTALL)
        if pm_block is None:
            pm_block = re.search(r"if pm:.*", block, re.DOTALL)
        text = pm_block.group(0)
        assert "db.projects.find" in text
        assert '"pm_name"' in text
        assert '"pm_email"' in text

    def test_pm_filter_no_pm_scope_bleed_through(self):
        """The PM filter must NOT use the HR actor's identity — it must
        be a search needle typed by the operator. HR must see EVERY PM's
        reports, just filtered by whomever they're investigating."""
        src = BACKEND_HR.read_text(encoding="utf-8")
        block = _extract_function_body(src, "hr_list_daily_reports")
        pm_block = re.search(r"if pm:.*?(?=        pipeline)", block, re.DOTALL)
        text = pm_block.group(0)
        # Must NOT pull PM identity from `actor` (the HR session).
        assert "actor.get" not in text
        assert "actor[" not in text
        assert "actor.pm_" not in text

    def test_superintendent_filter_searches_dr_top_level(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        assert (
            'match["superintendent"] = {\n                "$regex"' in src
            or 'match["superintendent"] = {"$regex"' in src
        )

    def test_foreman_filter_searches_nested_masci_crews(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        assert "masci_crews.foreman" in src


class TestTrack15_9A_CompanyWideGuarantee:
    """HR sees ALL DRs across ALL projects — no implicit scoping."""

    def test_list_endpoint_does_not_filter_by_actor(self):
        """The DR list pipeline's `match` dict must never be populated
        from the HR actor (no PM scope, no project ownership filter).
        HR is read-only company-wide."""
        src = BACKEND_HR.read_text(encoding="utf-8")
        body = _extract_function_body(src, "hr_list_daily_reports")
        body_after_sig = body.split("    ):", 1)[1]
        # Word-boundary so we don't false-positive on "subcontractor."
        assert re.search(r"\bactor\.", body_after_sig) is None, (
            "HR list endpoint must not scope by HR actor — it's company-wide."
        )
        assert re.search(r"\bactor\[", body_after_sig) is None

    def test_detail_endpoint_does_not_filter_by_actor(self):
        src = BACKEND_HR.read_text(encoding="utf-8")
        body = _extract_function_body(src, "hr_get_daily_report")
        body_after_sig = body.split("):", 1)[1]
        assert re.search(r"\bactor\.", body_after_sig) is None
        assert re.search(r"\bactor\[", body_after_sig) is None

    def test_no_session_pm_scope_helpers_invoked(self):
        """The HR DR endpoints must not call any of the PM-scope helpers
        used by the PM portal (assigned_projects, owned_projects, etc.)."""
        src = BACKEND_HR.read_text(encoding="utf-8")
        # Limit search to the two HR DR functions.
        block = (
            _extract_function_body(src, "hr_list_daily_reports")
            + _extract_function_body(src, "hr_get_daily_report")
        )
        for forbidden in ("assigned_projects", "owned_projects",
                          "pm_scope", "scoped_to_pm",
                          "pm_assigned_project_numbers"):
            assert forbidden not in block, (
                f"HR DR endpoint must not invoke {forbidden}"
            )


class TestTrack15_9A_FrontendFiltersAndColumns:
    """Frontend page exposes 3 new filters + 2 new columns."""

    def test_page_has_pm_filter_input(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert 'testId="hr-dr-pm"' in src
        assert 'setF("pm")' in src

    def test_page_has_superintendent_filter_input(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert 'testId="hr-dr-superintendent"' in src
        assert 'setF("superintendent")' in src

    def test_page_has_foreman_filter_input(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert 'testId="hr-dr-foreman"' in src
        assert 'setF("foreman")' in src

    def test_page_sends_three_new_filters_to_api(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert "params.pm = s.pm" in src
        assert "params.superintendent = s.superintendent" in src
        assert "params.foreman = s.foreman" in src

    def test_table_has_pm_column(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert "hr-dr-row-${idx}-pm" in src
        assert "r.pm_name" in src
        assert "r.pm_email" in src

    def test_table_has_superintendent_column(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert "hr-dr-row-${idx}-superintendent" in src
        assert "r.superintendent" in src

    def test_detail_header_shows_pm_strip(self):
        src = HR_PAGE.read_text(encoding="utf-8")
        assert 'data-testid="hr-dr-detail-pm-strip"' in src
        assert "doc.pm_name" in src
        assert "doc.superintendent" in src

    def test_clear_button_resets_all_filters(self):
        """onClear must reset every filter to its empty value AND
        explicitly pass EMPTY_FILTERS to fetchList to avoid stale-state."""
        src = HR_PAGE.read_text(encoding="utf-8")
        block = re.search(r"const onClear = \(\) => \{.*?\};", src, re.DOTALL).group(0)
        assert "setFilters(EMPTY_FILTERS)" in block
        assert "fetchList(EMPTY_FILTERS)" in block
        # The EMPTY_FILTERS object must cover all 10 keys.
        empty = re.search(r"const EMPTY_FILTERS = \{[^}]+\};", src, re.DOTALL).group(0)
        for k in ("dateFrom", "dateTo", "project", "pm",
                  "superintendent", "foreman", "employee",
                  "subcontractor", "vendor", "reportNumber"):
            assert f'{k}: ""' in empty, f"EMPTY_FILTERS missing {k}"


class TestTrack15_9A_EsTranslations:
    """New i18n strings must have ES translations."""

    def test_new_placeholders_have_es_translations(self):
        src = (ROOT / "frontend" / "src" / "lib" / "i18n.js").read_text(encoding="utf-8")
        for k in ('"Project manager name or email":',
                  '"Superintendent name":',
                  '"Foreman name":'):
            assert k in src, f"Missing ES translation for: {k}"

    def test_canonical_pm_and_super_es_present(self):
        src = (ROOT / "frontend" / "src" / "lib" / "i18n.js").read_text(encoding="utf-8")
        # These were pre-existing — verify still present.
        assert '"PM":' in src
        assert '"Superintendent":' in src
        assert '"Foreman":' in src
        assert '"Project Manager":' in src
