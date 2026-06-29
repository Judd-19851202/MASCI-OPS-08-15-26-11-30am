"""TRACK 19.02C · Disk Hygiene lock-file.

Locks in the audit + cleanup commitments so they cannot silently
regress. This test file does NOT mutate disk — it asserts that the
required reports exist and contain the mandatory clauses.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

MEM = Path("/app/memory")
TESTS_DIR = Path("/app/backend/tests")

BASELINE = MEM / "TRACK_19_02C_DISK_BASELINE.md"
SIZE_AUDIT = MEM / "TRACK_19_02C_DISK_SIZE_AUDIT.md"
CLASSIFICATION = MEM / "TRACK_19_02C_CLEANUP_CLASSIFICATION.md"
PLAN = MEM / "TRACK_19_02C_CLEANUP_PLAN.md"
BACKUP_AUDIT = MEM / "TRACK_19_02C_BACKUP_STORAGE_AUDIT.md"
LOG_AUDIT = MEM / "TRACK_19_02C_LOG_STORAGE_AUDIT.md"
ARTIFACT_AUDIT = MEM / "TRACK_19_02C_ARTIFACT_AUDIT.md"
CACHE_AUDIT = MEM / "TRACK_19_02C_CACHE_AUDIT.md"
POST_VALIDATION = MEM / "TRACK_19_02C_POST_CLEANUP_VALIDATION.md"
FINAL_REPORT = MEM / "TRACK_19_02C_FINAL_DISK_REPORT.md"
FUTURE_PLAN = MEM / "TRACK_19_02C_FUTURE_DISK_HYGIENE_PLAN.md"
PRD = MEM / "PRD.md"


def _read(p: Path) -> str:
    assert p.exists(), f"required report missing: {p}"
    return p.read_text(encoding="utf-8")


# ─────────── 1-11 · all required reports exist ───────────


def test_01_baseline_doc_exists(): assert BASELINE.exists()
def test_02_size_audit_doc_exists(): assert SIZE_AUDIT.exists()
def test_03_cleanup_classification_exists(): assert CLASSIFICATION.exists()
def test_04_cleanup_plan_exists(): assert PLAN.exists()
def test_05_backup_audit_exists(): assert BACKUP_AUDIT.exists()
def test_06_log_audit_exists(): assert LOG_AUDIT.exists()
def test_07_artifact_audit_exists(): assert ARTIFACT_AUDIT.exists()
def test_08_cache_audit_exists(): assert CACHE_AUDIT.exists()
def test_09_post_cleanup_validation_exists(): assert POST_VALIDATION.exists()
def test_10_final_disk_report_exists(): assert FINAL_REPORT.exists()
def test_11_future_hygiene_plan_exists(): assert FUTURE_PLAN.exists()


# ─────────── 12-16 · cleanup plan contains required clauses ───────────


def test_12_cleanup_plan_includes_protected_paths():
    text = _read(PLAN)
    for protected in (
        "/app/backend/storage/",
        "/app/backend/static/",
        "/app/backend/backups/",
        "/app/.git/",
        "/app/memory/",
    ):
        assert protected in text, f"plan must enumerate protected path {protected}"


def test_13_cleanup_plan_forbids_production_data_deletion():
    text = _read(PLAN).lower()
    assert ("no production data deletion" in text) \
        or ("never delete production data" in text)


def test_14_cleanup_plan_forbids_customer_upload_deletion():
    text = _read(PLAN).lower()
    assert "no customer upload deletion" in text \
        or "customer upload" in text and "protected" in text
    # Concrete protected path must be present.
    assert "/app/backend/storage/" in _read(PLAN)


def test_15_cleanup_plan_forbids_database_deletion():
    text = _read(PLAN).lower()
    assert "no database deletion" in text \
        or "mongodb is not on this filesystem" in text


def test_16_cleanup_plan_forbids_blind_rm_rf():
    text = _read(PLAN).lower()
    assert "no `rm -rf` against any path not in the safe-to-delete list" in text \
        or "no blind wildcards" in text


# ─────────── 17-18 · backup/log audits document retention ───────────


def test_17_backup_audit_documents_retention():
    text = _read(BACKUP_AUDIT)
    assert "BACKUP_KEEP_MAX" in text
    assert "retention" in text.lower()


def test_18_log_audit_documents_retention():
    text = _read(LOG_AUDIT)
    assert "retention" in text.lower() or "rotation" in text.lower()


# ─────────── 19-20 · final report shows before/after + reclaim ───────────


def test_19_final_report_includes_before_and_after_disk_usage():
    text = _read(FINAL_REPORT)
    assert re.search(r"BEFORE.*AFTER", text, re.I | re.S)
    # 74% before, 57% after.
    assert "74%" in text and "57%" in text


def test_20_final_report_includes_reclaimed_space():
    text = _read(FINAL_REPORT).lower()
    assert "reclaim" in text
    # Total reclaim figure must be present (1.6 G or 1.76 G).
    assert re.search(r"1\.[567]\s*g", text)


# ─────────── 21-25 · post-cleanup validation covers tracks ───────────


def test_21_validation_includes_app_health():
    text = _read(POST_VALIDATION)
    assert "/api/health" in text
    assert "RUNNING" in text


def test_22_validation_includes_track_19_02a_fleet_tests():
    text = _read(POST_VALIDATION)
    assert "test_track_19_02a_fleet_adoption_hardening" in text


def test_23_validation_includes_track_19_01_academy_tests():
    text = _read(POST_VALIDATION)
    assert "test_track_19_01_transportation_academy" in text


def test_24_validation_includes_track_19_00_driver_carrier_tests():
    text = _read(POST_VALIDATION)
    assert "test_track_19_00_transportation_driver_carrier_foundation" in text


def test_25_validation_includes_track_18_12c_visible_usable_tests():
    text = _read(POST_VALIDATION)
    assert "test_track_18_12c_transportation_role_permissions" in text


# ─────────── 26-27 · future plan covers monitoring + retention ───────────


def test_26_future_plan_includes_monitoring_threshold():
    text = _read(FUTURE_PLAN)
    assert "70%" in text and "80%" in text
    assert "threshold" in text.lower() or "alert" in text.lower()


def test_27_future_plan_includes_artifact_retention():
    text = _read(FUTURE_PLAN).lower()
    assert "retention" in text or "retain" in text
    assert "playwright" in text


# ─────────── 28 · no protected path appears in deleted-path list ───────────


def test_28_no_protected_path_in_deleted_list():
    """The plan's `# Action plan` table must not list any path under a
    protected root in its `Command` column."""
    text = _read(PLAN)
    forbidden_in_commands = (
        "rm -rf /app/backend/storage",
        "rm -rf /app/backend/static",
        "rm -rf /app/backend/backups",
        "rm -rf /app/.git",
        "rm -rf /app/backend/server.py",
        "rm -rf /app/memory/PRD.md",
        "rm -rf /app/memory/CHANGELOG.md",
        "rm -rf /app/memory/_INDEX.md",
        "rm -rf /app/memory/MASCI_RC_CERTIFICATION_LEDGER.md",
        "rm -f /app/backend/storage",
        "rm -f /app/backend/static",
        "rm -f /app/backend/backups",
        "rm -f /app/.git",
    )
    for token in forbidden_in_commands:
        assert token not in text, \
            f"forbidden destructive token present in plan: {token}"


# ─────────── 29 · final GO/NO-GO present ───────────


def test_29_final_status_go_or_nogo_exists():
    text = _read(FINAL_REPORT)
    assert re.search(r"^\s*\*\*GO\*\*\.|^\s*\*\*NO-GO\*\*\.|GO\s*/\s*NO-GO",
                     text, re.M | re.I)


# ─────────── 30 · PRD.md updated for Track 19.02C ───────────


def test_30_prd_updated_for_19_02c():
    text = _read(PRD).lower()
    assert "19.02c" in text or "track 19_02c" in text or "track_19_02c" in text
