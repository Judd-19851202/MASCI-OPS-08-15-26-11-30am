"""TRACK 15.10 — Project Team Management Recovery certification.

These tests assert the 6 non-deferrable operational recovery items:
1. No `(unnamed)` rendering anywhere in the panel.
2. Back navigation + breadcrumb on both PM and Admin job-team pages.
3. PM / Co-PM / Executive Oversight surfaced from project record
   (JIT-lifted from jobs_master when project_team_assignments rows
   are missing).
4. Display-name fallback hierarchy (full_name → display_name → name →
   first+last → email → Employee #id → Unknown person — Admin review).
5. Login/access status surfaced from existing user_directory.
6. PM directory picker pulls from existing user_directory (no new
   roster system, no silent account creation).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "routes" / "project_team_assignments.py"
PANEL = ROOT / "frontend" / "src" / "components" / "team" / "JobTeamRosterPanel.jsx"
API_LIB = ROOT / "frontend" / "src" / "lib" / "teamRosterApi.js"
PM_PAGE = ROOT / "frontend" / "src" / "pages" / "pm" / "PmJobTeam.jsx"
ADMIN_PAGE = ROOT / "frontend" / "src" / "pages" / "admin" / "AdminJobTeam.jsx"


# ─────────────────────────────────────── 1. NO "(unnamed)" RENDERING
class TestNoUnnamedDisplay:
    def test_panel_does_not_emit_literal_unnamed(self):
        src = PANEL.read_text(encoding="utf-8")
        # JSX must never render the string "(unnamed)".
        assert '"(unnamed)"' not in src
        assert "'(unnamed)'" not in src
        # Also no `(unnamed)` template-literal fallback.
        assert "(unnamed)" not in src.replace("// ", "")  # tolerate comments

    def test_panel_uses_display_name_helper(self):
        src = PANEL.read_text(encoding="utf-8")
        assert "function displayNameOf" in src
        assert "displayNameOf(it)" in src

    def test_helper_implements_full_fallback_hierarchy(self):
        src = PANEL.read_text(encoding="utf-8")
        helper = re.search(
            r"function displayNameOf\(it\)\s*\{.*?\n\}",
            src, re.DOTALL,
        ).group(0)
        for needle in (
            "it.full_name", "it.display_name", "it.name",
            "it.first_name", "it.last_name", "it.email",
            "it.employee_id", "Unknown person",
        ):
            assert needle in helper, f"Fallback hierarchy missing: {needle}"


# ─────────────────────────────────────── 2. BACK NAV + BREADCRUMB
class TestBackNavigation:
    def test_pm_job_team_has_breadcrumb(self):
        src = PM_PAGE.read_text(encoding="utf-8")
        assert 'data-testid="pm-job-team-breadcrumb"' in src
        assert 'data-testid="pm-job-team-crumb-portal"' in src
        assert 'data-testid="pm-job-team-crumb-staffing"' in src
        assert 'data-testid="pm-job-team-crumb-current"' in src

    def test_pm_job_team_has_back_button(self):
        src = PM_PAGE.read_text(encoding="utf-8")
        assert 'data-testid="pm-job-team-back"' in src
        assert 'to="/pm/project-staffing"' in src

    def test_admin_job_team_has_breadcrumb(self):
        src = ADMIN_PAGE.read_text(encoding="utf-8")
        assert 'data-testid="admin-job-team-breadcrumb"' in src
        assert 'data-testid="admin-job-team-crumb-portal"' in src
        assert 'data-testid="admin-job-team-crumb-staffing"' in src
        assert 'data-testid="admin-job-team-crumb-current"' in src

    def test_admin_job_team_has_back_button(self):
        src = ADMIN_PAGE.read_text(encoding="utf-8")
        assert 'data-testid="admin-job-team-back"' in src
        assert 'to="/admin/project-staffing"' in src


# ───────────── 3. KNOWN PM / CO-PM JIT-LIFTED FROM JOBS_MASTER
class TestKnownLeadershipSurfacing:
    def test_jit_lift_helper_exists(self):
        src = BACKEND.read_text(encoding="utf-8")
        assert "async def _jit_lift_known_leadership" in src

    def test_resolve_team_invokes_jit_lift(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def resolve_team_for_project.*?return rows",
            src, re.DOTALL,
        ).group(0)
        assert "_jit_lift_known_leadership" in block

    def test_jit_lift_reads_jobs_master_pm_fields(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def _jit_lift_known_leadership.*?return existing_rows \+ synth",
            src, re.DOTALL,
        ).group(0)
        assert "jobs_master.find_one" in block
        assert '"pm_email"' in block
        assert '"co_pm_emails"' in block

    def test_synthetic_rows_are_marked_for_ui(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def _jit_lift_known_leadership.*?return existing_rows \+ synth",
            src, re.DOTALL,
        ).group(0)
        # Synthetic rows must be tagged so the UI hides destructive
        # actions (no remove/transfer/star until materialised).
        assert '"synthetic": True' in block
        assert '"synthetic_source"' in block

    def test_panel_renders_synthetic_badge(self):
        src = PANEL.read_text(encoding="utf-8")
        assert "from project record" in src
        assert "job-team-synthetic-" in src

    def test_panel_hides_destructive_actions_on_synthetic_rows(self):
        src = PANEL.read_text(encoding="utf-8")
        # `isSynthetic` must gate remove/transfer/primary buttons.
        assert "const isSynthetic = !!it.synthetic" in src
        # `!isSynthetic` check must appear at least twice (remove + admin
        # toggle/transfer).
        assert src.count("!isSynthetic") >= 2


# ─────────────────────── 4. DISPLAY-NAME FALLBACK HIERARCHY (BACKEND)
class TestBackendFallbackHierarchy:
    def test_resolve_display_name_helper_exists(self):
        src = BACKEND.read_text(encoding="utf-8")
        assert "def _resolve_display_name" in src

    def test_resolve_display_name_covers_all_sources(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"def _resolve_display_name\(.*?\nreturn ",
            src, re.DOTALL,
        )
        if block is None:
            block = re.search(
                r"def _resolve_display_name\(.*?return \"Unknown person",
                src, re.DOTALL,
            )
        text = block.group(0)
        for needle in ('"full_name"', '"display_name"', '"name"',
                       '"first_name"', '"last_name"', '"email"',
                       '"employee_id"'):
            assert needle in text, f"Backend fallback missing: {needle}"

    def test_unknown_person_is_terminal_fallback(self):
        src = BACKEND.read_text(encoding="utf-8")
        assert 'return "Unknown person — Admin review required"' in src

    def test_enrich_attaches_resolved_display_name(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def _enrich_row_with_directory.*?return row",
            src, re.DOTALL,
        ).group(0)
        assert "_resolve_display_name(row" in block


# ─────────────────────────────────────── 5. LOGIN/ACCESS STATUS
class TestLoginStatusVisibility:
    def test_backend_helper_returns_canonical_statuses(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"def _login_status_from_directory.*?return \"invite_pending\"",
            src, re.DOTALL,
        ).group(0)
        for status in ("active", "invite_pending", "no_login",
                       "disabled", "unknown"):
            assert f'"{status}"' in block, f"Missing status: {status}"

    def test_backend_uses_existing_user_directory_fields(self):
        """No new auth system — must read EXISTING fields only."""
        src = BACKEND.read_text(encoding="utf-8")
        # Slice from the function definition to the next top-level def.
        start = src.index("def _login_status_from_directory")
        rest = src[start:]
        end = rest.index("\nasync def ") if "\nasync def " in rest else len(rest)
        block = rest[:end]
        for fld in ('"disabled"', '"must_change_password"',
                    '"password_hash"', '"last_login_at"'):
            assert fld in block, f"Login-status field not consulted: {fld}"

    def test_enrich_attaches_login_status(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def _enrich_row_with_directory.*?return row",
            src, re.DOTALL,
        ).group(0)
        assert 'row["login_status"]' in block

    def test_frontend_renders_login_status_badge(self):
        src = PANEL.read_text(encoding="utf-8")
        assert "function LoginStatusBadge" in src
        assert "LoginStatusBadge status=" in src
        assert "it.login_status" in src

    def test_frontend_covers_all_five_status_states(self):
        src = PANEL.read_text(encoding="utf-8")
        for st in ("active", "invite_pending", "no_login",
                   "disabled", "unknown"):
            assert f'"{st}"' in src, f"UI missing status: {st}"


# ─────────────────────────── 6. PM DIRECTORY PICKER (NO NEW ROSTER)
class TestPmDirectoryPicker:
    def test_backend_route_exists(self):
        src = BACKEND.read_text(encoding="utf-8")
        assert '@router.get("/api/pm/directory/users")' in src
        assert "async def pm_directory_users" in src

    def test_backend_route_is_portal_token_gated(self):
        """Any portal token may read — not just admin. PM, Shop, HR,
        Safety, Dispatch, FL all benefit from the picker."""
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def pm_directory_users\((.*?)\):",
            src, re.DOTALL,
        ).group(1)
        assert "require_any_portal_token" in block

    def test_backend_route_reads_existing_user_directory(self):
        """No new collection — must read existing user_directory."""
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def pm_directory_users.*?return \{",
            src, re.DOTALL,
        ).group(0)
        assert "db.user_directory.find" in block
        # No silent creation, no new collection.
        assert "user_directory.insert" not in block
        assert "user_directory.update" not in block

    def test_backend_excludes_disabled_accounts_by_default(self):
        src = BACKEND.read_text(encoding="utf-8")
        block = re.search(
            r"async def pm_directory_users.*?return \{",
            src, re.DOTALL,
        ).group(0)
        assert '"disabled"' in block

    def test_frontend_client_exposes_pm_directory_call(self):
        src = API_LIB.read_text(encoding="utf-8")
        assert "fetchPmDirectoryUsers" in src
        assert "/api/pm/directory/users" in src

    def test_panel_uses_pm_directory_in_pm_scope(self):
        src = PANEL.read_text(encoding="utf-8")
        # Both adminScope and PM scope load a directory (PM via the
        # new picker, no free-text email field).
        assert "fetchPmDirectoryUsers()" in src
        assert 'data-testid="job-team-user-select-pm"' in src
        # The OLD free-text PM email Input must be gone.
        assert 'data-testid="job-team-user-email"' not in src

    def test_panel_shows_no_candidates_calm_state(self):
        """Must not silently fail — operator-actionable message when
        the directory has no candidates for a role/portal."""
        src = PANEL.read_text(encoding="utf-8")
        assert "No active candidates found" in src


# ─────────────────────── 7. SAFETY GUARDS (NO REGRESSIONS)
class TestSafetyGuards:
    def test_no_silent_account_creation_in_panel(self):
        src = PANEL.read_text(encoding="utf-8")
        # The Add-Member flow must not call any auth/account-creation
        # endpoints. Whitelist: addTeamMember (assignment only).
        assert "/api/auth/create" not in src
        assert "createUser" not in src
        assert "issuePassword" not in src
        assert "setPassword" not in src

    def test_pm_assignable_roles_still_excludes_admin_only(self):
        """The admin-only role set (pm, co_pm, executive_oversight)
        must remain admin-only — Track 15.10 only added visibility,
        not assignment authority."""
        src = BACKEND.read_text(encoding="utf-8")
        assert 'ADMIN_ONLY_ROLES: Set[str] = {"pm", "co_pm", "executive_oversight"}' in src
        assert "PM_ASSIGNABLE_ROLES: Set[str] = ALL_ROLES - ADMIN_ONLY_ROLES" in src

    def test_no_new_collections_introduced(self):
        """Track 15.10 must NOT create new identity / login / roster
        collections. Whitelist: project_team_assignments (pre-existing),
        user_directory (pre-existing), employees (pre-existing),
        jobs_master (pre-existing), audit_events (pre-existing)."""
        src = BACKEND.read_text(encoding="utf-8")
        # Scan for `db.<collection>` references.
        cols = set(re.findall(r"db\.([a-z_][a-z0-9_]*)", src))
        allowed = {
            "project_team_assignments", "user_directory", "employees",
            "jobs_master", "audit_events", "task_notifications",
            "notifications", "directory_invites",
            # Pre-existing references already in this file:
            "team_roster_assignments_audit",
        }
        unknown = cols - allowed
        assert not unknown, (
            f"Track 15.10 introduced unexpected collections: {sorted(unknown)}"
        )
