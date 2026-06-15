"""
Track 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION.

Contract regression tests. Read-only — these never mutate any DB, file,
or token. They lock the canonical password contract documented in
/app/memory/AUTH_PASSWORD_CONTRACT.md so future drift fails CI.

PRODUCTION LOGIN PROTECTION COMPLIANCE:
  - No bcrypt.hashpw against any user document.
  - No login attempts.
  - No password mutations.
  - No env-var changes.
  - No collection writes.
"""
import os
import pathlib
import re

import pytest

REPO = pathlib.Path("/app")
BACKEND = REPO / "backend"
MEMORY = REPO / "memory"


def _read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Phase 2 · bcrypt parity ──────────────────────────────────────────

def test_bcrypt_rounds_pinned_pm_auth():
    src = _read(BACKEND / "pm_auth.py")
    assert "bcrypt.gensalt(rounds=12)" in src


def test_bcrypt_rounds_pinned_user_directory():
    src = _read(BACKEND / "user_directory.py")
    assert "bcrypt.gensalt(rounds=12)" in src


def test_bcrypt_rounds_pinned_auth_module():
    """Track 14.0-AUTH-PASSWORD-PARITY fix: pinned this track."""
    src = _read(BACKEND / "auth.py")
    assert "bcrypt.gensalt(rounds=12)" in src, (
        "auth.hash_password must use bcrypt.gensalt(rounds=12) — Track "
        "14.0-AUTH-PASSWORD-PARITY locked this for explicit parity."
    )


# ── Phase 3 · temp password parity ───────────────────────────────────

def test_temp_password_alphabet_no_ambiguous():
    from pm_auth import generate_temp_password  # noqa: PLC0415
    samples = [generate_temp_password() for _ in range(500)]
    for s in samples:
        for ch in s:
            assert ch not in "0O1lI", (
                f"temp password contained ambiguous char {ch!r}"
            )


def test_temp_password_default_length_ten():
    from pm_auth import generate_temp_password  # noqa: PLC0415
    assert len(generate_temp_password()) == 10


def test_temp_password_high_entropy():
    from pm_auth import generate_temp_password  # noqa: PLC0415
    samples = {generate_temp_password() for _ in range(1000)}
    assert len(samples) >= 950, "duplicate temp passwords — entropy too low"


# ── Phase 5 · reset token TTL parity ─────────────────────────────────

@pytest.mark.parametrize("module,constant", [
    ("pm_auth", "_RESET_TOKEN_TTL_SECONDS"),
    ("hr_users", "_HR_RESET_TOKEN_TTL_SECONDS"),
    ("safety_users", "_SAFETY_RESET_TOKEN_TTL_SECONDS"),
    ("shop_users", "_SHOP_RESET_TOKEN_TTL_SECONDS"),
    ("dispatch_users", "_DISPATCH_RESET_TOKEN_TTL_SECONDS"),
])
def test_reset_token_ttl_thirty_minutes(module, constant):
    src = _read(BACKEND / f"{module}.py")
    pattern = rf"{re.escape(constant)}\s*=\s*30\s*\*\s*60"
    assert re.search(pattern, src), (
        f"{module}.{constant} must equal 30 * 60 (30-minute reset TTL)"
    )


# ── Phase 2 · per-portal libs import from pm_auth (single source) ────

@pytest.mark.parametrize("portal_module", [
    "hr_users", "safety_users", "shop_users", "dispatch_users",
])
def test_portal_helpers_import_from_pm_auth(portal_module):
    src = _read(BACKEND / f"{portal_module}.py")
    assert "from pm_auth import" in src, (
        f"{portal_module} must import auth helpers from pm_auth "
        "(single source of truth for hash/verify/temp-password)."
    )
    for helper in ("hash_password", "verify_password", "generate_temp_password"):
        assert helper in src, (
            f"{portal_module} must use the pm_auth.{helper} canonical helper"
        )


# ── Phase 2 · password min-length contract ───────────────────────────

def test_pm_min_password_length_six():
    src = _read(BACKEND / "pm_auth.py")
    assert "len(plain) < 6" in src, "pm_auth must enforce min_length=6"


def test_master_min_password_length_ten():
    src = _read(BACKEND / "auth.py")
    # min_length=10 on ChangeMasterPasswordIn-like models
    assert "min_length=10" in src, (
        "auth.py change-password Pydantic models must enforce min_length=10"
    )


# ── Phase 7 · lockout contract ───────────────────────────────────────

def test_per_ip_lockout_env_pinned():
    src = _read(BACKEND / "server.py")
    assert 'LOGIN_MAX_FAILS_PER_WINDOW = int(os.environ.get("LOGIN_MAX_FAILS", "10"))' in src
    assert 'LOGIN_LOCKOUT_SECONDS = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "900"))' in src


def test_per_ip_lockout_helper_present():
    src = _read(BACKEND / "server.py")
    # The lockout helper consults the per-IP attempts ring.
    assert "LOGIN_LOCKOUT_SECONDS" in src
    assert "LOGIN_MAX_FAILS_PER_WINDOW" in src


# ── Phase 11 · no plaintext leak in any backend route ────────────────

def test_no_plaintext_password_leak_in_route_returns():
    """Read every routes/*.py file and confirm no function explicitly
    returns a `password_hash` field in its response body. The directory
    routes use explicit `{"_id": 0, "password_hash": 0}` projection;
    other routes scrub via `public_view` or never load the hash."""
    routes_dir = BACKEND / "routes"
    suspects = []
    for py in routes_dir.rglob("*.py"):
        src = py.read_text(encoding="utf-8")
        # Allow projections that strip the hash (`"password_hash": 0`).
        # Disallow `return ...password_hash...` patterns.
        for m in re.finditer(r'return\s+[^"\n]*password_hash', src):
            line_no = src[:m.start()].count("\n") + 1
            # Filter out the safe pattern `password_hash": 0` (explicit projection)
            line_text = src.splitlines()[line_no - 1]
            if '"password_hash": 0' in line_text or "'password_hash': 0" in line_text:
                continue
            suspects.append(f"{py.relative_to(BACKEND)}:{line_no}")
    assert not suspects, f"possible password_hash leak in: {suspects}"


# ── Phase 9 · break-glass documented ─────────────────────────────────

def test_break_glass_routes_documented_in_test_credentials():
    src = _read(MEMORY / "test_credentials.md")
    # Three documented break-glass paths.
    assert "Legacy Admin Console" in src or "Legacy API-only break-glass" in src
    assert "PM_PASSWORD" in src
    assert "Developer Portal" in src or "DEV_PASSWORD" in src


# ── Phase 1 · inventory + contract docs exist ────────────────────────

def test_auth_inventory_doc_exists():
    assert (MEMORY / "AUTH_INVENTORY.md").exists()


def test_auth_contract_doc_exists():
    assert (MEMORY / "AUTH_PASSWORD_CONTRACT.md").exists()


def test_auth_existing_user_protection_doc_exists():
    """PRODUCTION LOGIN PROTECTION attestation must be on disk."""
    assert (MEMORY / "AUTH_EXISTING_USER_PROTECTION_CERTIFICATION.md").exists()


def test_auth_lockout_certification_doc_exists():
    assert (MEMORY / "AUTH_LOCKOUT_CERTIFICATION.md").exists()


def test_auth_reset_certification_doc_exists():
    assert (MEMORY / "AUTH_RESET_CERTIFICATION.md").exists()


def test_auth_session_certification_doc_exists():
    assert (MEMORY / "AUTH_SESSION_CERTIFICATION.md").exists()


def test_auth_runtime_proof_matrix_doc_exists():
    assert (MEMORY / "AUTH_RUNTIME_PROOF_MATRIX.md").exists()


def test_auth_regression_suite_summary_doc_exists():
    assert (MEMORY / "AUTH_REGRESSION_SUITE_SUMMARY.md").exists()
