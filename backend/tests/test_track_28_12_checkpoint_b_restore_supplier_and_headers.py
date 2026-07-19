from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


sys.path.insert(0, "/app/backend")


def test_restore_replace_mode_guard_contract_present():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert 'confirm: str = Form("")' in src
    assert 'backup_ack: bool = Form(False)' in src
    assert 'dry_run: bool = Form(False)' in src
    assert 'RESTORE_REPLACE_ALL_COLLECTIONS' in src
    assert 'require_non_empty_destructive_scope(' in src
    assert '"status": "partial_failure" if total_failed else "success"' in src
    assert '"accepted" if total_failed == 0 else "partial_failure"' in src


def test_supplier_replace_all_guard_contract_present():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert 'replace_all: bool = Form(False)' in src
    assert 'REPLACE_ALL_SUPPLIERS' in src
    assert '"mode": "preflight"' in src
    assert '"mode": "replace_all"' in src
    assert 'current_suppliers' in src
    assert 'duplicates_filtered' in src


def test_operator_safety_non_empty_scope_refuses_empty():
    from lib.operator_safety import require_non_empty_destructive_scope

    with pytest.raises(HTTPException):
        require_non_empty_destructive_scope([], detail="empty")
    require_non_empty_destructive_scope(["suppliers"], detail="empty")


def test_governance_self_protection_runtime_image_honesty():
    src = Path("/app/backend/routes/governance_self_protection.py").read_text(encoding="utf-8")
    assert 'test_reports_not_shipped' in src
    assert 'backend/static/runtime-data/TRUST_SURFACES.json' in src
    assert 'memory/TRUST_SURFACES.json' not in src


def test_canonical_security_headers_present_and_ordered():
    src = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert 'X-Content-Type-Options' in src
    assert 'Referrer-Policy' in src
    assert 'X-Frame-Options' in src
    assert 'frame-ancestors' in src
