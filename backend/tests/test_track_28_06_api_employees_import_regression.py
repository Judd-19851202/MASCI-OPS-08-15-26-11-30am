"""TRACK 28.06 · Regression lock — /api/employees must not throw
NameError.

Root cause of the bug (discovered during Track 28.06 device walk):
`server.py::list_employees` at line 4841 CALLS
`apply_synthetic_hr_exclusion(...)` but does NOT import it. The
Track 28.04 static invariant only checks that the CALL is present;
it does not check that the name is bound in scope. So a missing
import produces a runtime `NameError` on every request to
`/api/employees` — a critical failure since every downstream form
(Daily Report, Safety, Incident, Meeting, JHA, Dispatch) hits
this endpoint for the employee/attendee picker.

This test hits the live endpoint and requires HTTP 200. If a
future edit removes the import, the test fails immediately.
"""
from __future__ import annotations

import re
import httpx
import pytest


def _backend() -> str:
    try:
        r = httpx.get("http://localhost:8001/api/health", timeout=5)
        if r.status_code == 200:
            return "http://localhost:8001"
    except Exception:
        pass
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("no backend")


BACKEND = _backend()


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    return r.json()["portal_tokens"]["admin"]


def test_api_employees_returns_200(admin_token: str) -> None:
    """/api/employees must not raise NameError. The endpoint is the
    canonical employee picker for every form on the platform (Daily
    Report, Safety, Incident, Meeting, JHA, Dispatch) — a 500 here
    breaks the entire operator workflow."""
    r = httpx.get(
        f"{BACKEND}/api/employees",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 200, (
        f"TRACK 28.06 regression: /api/employees returned {r.status_code}. "
        f"Body: {r.text[:300]}. "
        f"If NameError: confirm `from lib.synthetic_hr_filter import "
        f"apply_synthetic_hr_exclusion` is imported inside "
        f"server.py::list_employees function scope."
    )
    body = r.json()
    assert "items" in body
    assert isinstance(body["items"], list)


def test_server_list_employees_imports_filter_helper() -> None:
    """Structural regression: server.py::list_employees function body
    must contain the local import for apply_synthetic_hr_exclusion.
    Prevents the exact bug pattern that hit prod: the CALL is present
    but the IMPORT is missing."""
    import ast
    path = "/app/backend/server.py"
    with open(path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "list_employees":
                # Walk body — look for a `from lib.synthetic_hr_filter
                # import apply_synthetic_hr_exclusion` statement OR
                # verify the name is bound at module scope.
                found_local = False
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.ImportFrom):
                        if stmt.module == "lib.synthetic_hr_filter":
                            for alias in stmt.names:
                                if alias.name == "apply_synthetic_hr_exclusion":
                                    found_local = True
                                    break
                if not found_local:
                    # Check module-level
                    for stmt in tree.body:
                        if isinstance(stmt, ast.ImportFrom):
                            if stmt.module == "lib.synthetic_hr_filter":
                                for alias in stmt.names:
                                    if alias.name == "apply_synthetic_hr_exclusion":
                                        found_local = True
                                        break
                assert found_local, (
                    "TRACK 28.06 regression: server.py::list_employees "
                    "does not import `apply_synthetic_hr_exclusion`. "
                    "This causes a NameError at runtime on every "
                    "/api/employees request. Add:\n"
                    "  from lib.synthetic_hr_filter import "
                    "apply_synthetic_hr_exclusion  # noqa: PLC0415\n"
                    "inside the function body (or at module scope)."
                )
                return
    pytest.fail("server.py::list_employees function not found")
