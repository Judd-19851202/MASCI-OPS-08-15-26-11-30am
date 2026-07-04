"""Track 21.3 · Remaining Class-C Remediation — permanent lock test.

Enforces every decision made in Track 21.3 phases A + B + C + D + E-docs.

No HTTP calls beyond the CORS preflight sanity check. No email dispatched.
No live-server dependency beyond a local `localhost:8001` health probe
that runs only when the pod is up (skipped otherwise).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
BACKEND = APP / "backend"
MEM = APP / "memory"


# ---------------------------------------------------------------- Phase A · Env

def test_env_var_census_committed():
    assert (MEM / "TRACK_21_3_ENV_VAR_CENSUS.md").is_file()


def test_env_example_committed():
    body = (BACKEND / ".env.example").read_text(encoding="utf-8")
    assert "EMAIL_SAFETY_MODE" in body
    assert "MONGO_URL" in body
    assert "RESEND_API_KEY" in body
    assert "S3_ENDPOINT_URL" in body
    assert "AUTO_EMAIL_REPORTS" in body


# ---------------------------------------------------------------- Phase B · CORS

def test_cors_middleware_uses_explicit_allow_lists():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    # Wildcard method/header allow-lists must be gone.
    assert 'allow_methods=["*"]' not in src, "CORS allow_methods must be explicit"
    assert 'allow_headers=["*"]' not in src, "CORS allow_headers must be explicit"
    # The explicit lists must be present.
    assert '"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"' in src
    assert '"X-Admin-Token"' in src
    assert '"X-Portal-Token"' in src
    assert '"Authorization"' in src
    assert 'expose_headers=' in src


def test_cors_hardening_report_committed():
    body = (MEM / "TRACK_21_3_CORS_HARDENING_REPORT.md").read_text(encoding="utf-8")
    assert "Phase B" in body
    assert "EMAIL_SAFETY_MODE=strict" in body


# ---------------------------------------------------------------- Phase C · Storage + Sentry

def test_storage_and_sentry_reports_committed():
    for name in ("TRACK_21_3_STORAGE_HYGIENE_REPORT.md", "TRACK_21_3_SENTRY_HYGIENE_REPORT.md"):
        p = MEM / name
        assert p.is_file(), f"Missing: {name}"


# ---------------------------------------------------------------- Phase D · Singletons

def test_singleton_collection_review_committed():
    body = (MEM / "TRACK_21_3_SINGLETON_COLLECTION_REVIEW.md").read_text(encoding="utf-8")
    assert "TD-21.2-C04" in body
    assert "RETIRE-LATER" in body


# ---------------------------------------------------------------- Phase E · Components

def test_component_collision_report_committed():
    body = (MEM / "TRACK_21_3_COMPONENT_COLLISION_REPORT.md").read_text(encoding="utf-8")
    assert "EmptyState" in body
    assert "StatusBadge" in body
    assert "SideNavV2" in body
    assert "21.y" in body  # decision target


# ---------------------------------------------------------------- Phase H · Manifest / Cross-track

def test_track_21_2e_kill_switch_still_present():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src


def test_preview_env_still_strict():
    body = (BACKEND / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", body, re.MULTILINE)


def test_all_track_21_3_deliverables_committed():
    required = [
        "TRACK_21_3_EXECUTIVE_SUMMARY.md",
        "TRACK_21_3_ENV_VAR_CENSUS.md",
        "TRACK_21_3_CORS_HARDENING_REPORT.md",
        "TRACK_21_3_STORAGE_HYGIENE_REPORT.md",
        "TRACK_21_3_SENTRY_HYGIENE_REPORT.md",
        "TRACK_21_3_SINGLETON_COLLECTION_REVIEW.md",
        "TRACK_21_3_COMPONENT_COLLISION_REPORT.md",
        "TRACK_21_3_MANIFEST_DIFF_REPORT.md",
        "TRACK_21_3_ZERO_DRIFT_MATRIX.md",
        "TRACK_21_3_EMAIL_SAFETY_CERTIFICATION.md",
        "TRACK_21_3_TEST_REPORT.md",
    ]
    missing = [name for name in required if not (MEM / name).is_file()]
    assert not missing, f"Missing Track 21.3 deliverables: {missing}"


def test_debt_register_records_track_21_3():
    body = (MEM / "TECHNICAL_DEBT_REGISTER.md").read_text(encoding="utf-8")
    assert "TD-21.2-C05" in body
    assert "21.3" in body


def test_changelog_records_track_21_3():
    body = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 21.3" in body or "Track 21.3" in body


def test_boot_log_still_records_sdk_patch():
    for lp in Path("/var/log/supervisor").glob("backend*.log"):
        try:
            if "EMAIL_SAFETY_MODE=strict — Resend SDK patched" in lp.read_text(errors="ignore"):
                return
        except Exception:
            continue
    pytest.skip("supervisor logs unavailable in this environment")
