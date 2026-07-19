from __future__ import annotations

from pathlib import Path
import json


def test_restore_route_partial_failure_semantics_are_honest():
    src = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert '"status": "partial_failure" if total_failed else "success"' in src
    assert '"ok": total_failed == 0' in src
    assert 'failed_docs' in src


def test_security_header_middleware_exists_once_canonically():
    src = Path('/app/backend/server.py').read_text(encoding='utf-8')
    assert src.count('@app.middleware("http")') >= 1
    assert 'X-Content-Type-Options' in src
    assert 'Referrer-Policy' in src
    assert 'X-Frame-Options' in src
    assert 'frame-ancestors' in src


def test_governance_self_protection_runtime_unavailable_is_honest():
    src = Path('/app/backend/routes/governance_self_protection.py').read_text(encoding='utf-8')
    assert 'unavailable_in_runtime_image' in src
    assert 'test_reports_not_shipped' in src


def test_exception_inventory_json_exists_and_has_stable_records():
    path = Path('/app/docs/governance/critical_exception_inventory.json')
    obj = json.loads(path.read_text(encoding='utf-8'))
    assert obj['total_occurrences'] >= 2000
    assert 'occurrences' in obj and obj['occurrences']
    first = obj['occurrences'][0]
    for key in ['id', 'file', 'line', 'critical_family', 'exception_syntax', 'behavior_after_catch', 'initial_static_risk_classification', 'owner', 'status']:
        assert key in first
