"""TRACK 22.5A · legacy governance linter modernization lock.

Certifies that the Track 18.10 / 18.11 / 18.12 family of governance
linters read the *current* routing shell — not the pre-Track-19 App.js
that no longer contains any inline route definitions. The safety
intent of every legacy assertion is preserved by reading App.js AND
AppRoutes.jsx concatenated; where the strings physically live is an
implementation detail.

This lock exists so a future refactor of the tests cannot silently
drop the `_read_app_shell()` helper (or its inline equivalent) and
re-open the "gate is green because it looks at an empty file" trap.
"""
from __future__ import annotations

import pathlib


ROOT = pathlib.Path("/app")
BACKEND_TESTS = ROOT / "backend" / "tests"


LEGACY_FILES = [
    "test_track_18_10_governance_boundary_linter.py",
    "test_track_18_11_r8_duplicate_cta_linter.py",
    "test_track_18_12_mission_control_access_layout.py",
    "test_track_18_12b_transportation_dispatcher_functionality.py",
    "test_track_18_12c_transportation_role_permissions.py",
    "test_pre_deployment_release_safety.py",
]


def test_appjs_and_approutes_are_both_readable():
    """The routing shell physically consists of these two files."""
    assert (ROOT / "frontend" / "src" / "App.js").exists()
    assert (ROOT / "frontend" / "src" / "app" / "routing" / "AppRoutes.jsx").exists()


def test_legacy_linters_do_not_read_appjs_in_isolation_for_routes():
    """Every legacy linter that literally-substring-matches route
    or auth patterns MUST also read `app/routing/AppRoutes.jsx`.

    We enforce this by scanning each legacy file's source: if it
    references `App.js`, it must also reference `AppRoutes.jsx`.
    That's the exact structural pattern the Track 22.5a
    modernization installed.
    """
    for name in LEGACY_FILES:
        src = (BACKEND_TESTS / name).read_text()
        mentions_appjs = "App.js" in src
        mentions_approutes = "AppRoutes.jsx" in src
        if mentions_appjs:
            assert mentions_approutes, (
                f"{name} reads App.js but does NOT read "
                f"AppRoutes.jsx. Track 22.5a doctrine: route + auth "
                f"literal-substring assertions must read the "
                f"concatenated shell so drift into AppRoutes.jsx "
                f"cannot mask a real route removal."
            )


def test_track_18_10_allowlist_covers_new_admin_surfaces():
    """`ADMIN_PAGE_ALLOWLIST` must include the five admin surfaces
    added since the original Track 18.10 audit. Missing any of
    these would falsely fail `test_04_every_admin_file_has_classification`
    and would tempt an operator to bypass the gate — the exact
    trap Track 22.5a exists to prevent.
    """
    src = (BACKEND_TESTS / "test_track_18_10_governance_boundary_linter.py").read_text()
    for surface in (
        "AdminAIConfiguration.jsx",
        "AdminOperationalIntelligence.jsx",
        "AdminOperationalIntelligenceRecipients.jsx",
        "IntegrationTruth.jsx",
        "PreviewValidationIdentities.jsx",
    ):
        assert f'"{surface}"' in src, (
            f"Admin surface {surface} missing from Track 18.10 "
            f"ADMIN_PAGE_ALLOWLIST. This would falsely-fail the "
            f"classification lock and tempt a gate bypass."
        )
