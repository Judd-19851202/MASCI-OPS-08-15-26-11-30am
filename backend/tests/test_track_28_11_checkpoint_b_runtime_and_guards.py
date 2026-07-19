from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


sys.path.insert(0, "/app/backend")


def test_runtime_routes_no_longer_point_to_memory_paths():
    checks = {
        "/app/backend/routes/dispatch_day1_debrief.py": ["\"storage\": \"operator_workspace_memory\"", '"path": f"/app/memory/'],
        "/app/backend/routes/platform_data_truth.py": ["docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md", "/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md"],
        "/app/backend/routes/asset_mapping_recon.py": ["runbook_ref", '"runbook_path":     "/app/memory/'],
        "/app/backend/db_isolation_failsafe.py": ["docs/recovery/LIVE_VS_RECOVERY_RECONCILIATION.md", "/app/memory/PHASE1_ATLAS_SEPARATION_REPORT.md"],
    }
    for path, (must_have, must_not_have) in checks.items():
        src = Path(path).read_text(encoding="utf-8")
        assert must_have in src
        assert must_not_have not in src


def test_governance_runtime_paths_use_shipped_static_runtime_data():
    src = Path("/app/backend/routes/governance_health.py").read_text(encoding="utf-8")
    assert '/app/backend/static/runtime-data/HUB_VISUAL_BASELINE.json' in src
    assert '/app/backend/static/runtime-data/DOCTRINE_TRENDLINE.json' in src
    assert '/app/memory/HUB_VISUAL_BASELINE.json' not in src


def test_operator_safety_requires_confirmation_and_backup_ack(monkeypatch):
    from lib.operator_safety import require_destructive_confirmation, require_destructive_runtime_guard

    monkeypatch.setenv("DB_NAME", "masci_safety")
    with pytest.raises(HTTPException):
        require_destructive_confirmation({"confirm": "WRONG"}, expected_confirm="RIGHT")
    with pytest.raises(HTTPException):
        require_destructive_confirmation({"confirm": "RIGHT"}, expected_confirm="RIGHT")
    require_destructive_confirmation({"confirm": "RIGHT", "backup_ack": True}, expected_confirm="RIGHT")
    require_destructive_runtime_guard(expected_db_name="masci_safety")
    monkeypatch.setenv("DB_NAME", "other_db")
    with pytest.raises(HTTPException):
        require_destructive_runtime_guard(expected_db_name="masci_safety")


def test_destructive_routes_use_shared_guard_tokens():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert 'REPLACE_ALL_JOBS_MASTER' in src
    assert 'FORCE_RESEED_CREW_COLLECTIONS' in src
    assert 'SCRAP_CREW_HUB' in src
    assert 'require_destructive_confirmation' in src
    assert 'require_destructive_runtime_guard' in src


def test_cost_code_bulk_replace_guarded():
    src = Path("/app/backend/routes/cost_codes.py").read_text(encoding="utf-8")
    assert 'REPLACE_COST_CODE_REGISTRY' in src
    assert 'require_destructive_confirmation' in src
    assert 'require_destructive_runtime_guard' in src


def test_jobs_bulk_replace_refuses_empty_rows():
    from jobs_master import bulk_replace

    class _DummyDB:
        pass

    with pytest.raises(ValueError):
        import asyncio
        asyncio.run(bulk_replace(_DummyDB(), []))
