"""TRACK RC1-PREDEPLOY-ADDENDUM · Preview→Production Isolation regression lock.

Locks the boot-time guarantees that prevent the preview pod from
writing to or reading the production MongoDB namespace.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load the backend .env so the env-variable tests see the same values
# the running pod sees.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


# ─── Boot guard contract — server.py refuses to start on misalignment ─

def test_env_db_alignment_guard_present_in_server():
    src = Path("/app/backend/server.py").read_text()
    assert "_verify_env_db_alignment" in src
    assert "RuntimeError" in src
    assert "_preview" in src, (
        "Guard must reference the '_preview' DB suffix discriminator"
    )


def test_failsafe_module_exists():
    p = Path("/app/backend/db_isolation_failsafe.py")
    assert p.exists()
    src = p.read_text()
    assert "PREVIEW_DB" in src and "PROD_DB" in src
    assert "ENFORCE_DB_ISOLATION" in src
    assert "sys.exit(99)" in src, (
        "Must fail-fast (non-zero exit) when isolation flag is on and probe fails"
    )


# ─── Live environment identity ───────────────────────────────────────

def test_app_env_is_preview():
    assert os.environ.get("APP_ENV", "").strip().lower() == "preview", (
        "Preview pod must report APP_ENV=preview"
    )


def test_db_name_uses_preview_suffix():
    db_name = os.environ.get("DB_NAME", "")
    assert db_name.endswith("_preview"), (
        f"Preview pod must use a DB ending in '_preview'; got {db_name!r}"
    )


def test_enforce_db_isolation_enabled():
    flag = (os.environ.get("ENFORCE_DB_ISOLATION") or "").strip().lower()
    assert flag in ("1", "true", "yes", "on"), (
        "ENFORCE_DB_ISOLATION must be active in preview to fail-fast on credential drift"
    )


def test_auto_email_reports_disabled_in_preview():
    """Preview must NOT auto-email real users. AUTO_EMAIL_REPORTS guards every send path."""
    flag = (os.environ.get("AUTO_EMAIL_REPORTS") or "").strip().lower()
    assert flag in ("false", "0", "no", "off", ""), (
        f"Preview must not auto-email production users; AUTO_EMAIL_REPORTS={flag!r}"
    )


# ─── Cross-env probe (read-only) — preview credential MUST be blocked ─

@pytest.mark.asyncio
async def test_preview_credential_cannot_access_production_db():
    """The preview pod's MongoDB credential must NOT have visibility on
    the production DB namespace. This is the core isolation invariant.
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "")
    assert mongo_url, "MONGO_URL must be set"
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
    try:
        # Try to list collections in production DB. MUST raise.
        from pymongo.errors import OperationFailure
        try:
            cols = await client["masci_safety"].list_collection_names()
            pytest.fail(
                "🔴 ISOLATION VIOLATION · preview credential can list collections "
                f"in production DB 'masci_safety' ({len(cols)} collections visible)"
            )
        except OperationFailure:
            pass  # GOOD — access denied as expected
    finally:
        client.close()
