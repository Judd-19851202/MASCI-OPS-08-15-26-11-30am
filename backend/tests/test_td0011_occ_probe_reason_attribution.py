"""SO-08b / TD-0011 — OCC probe UNVERIFIABLE reason attribution.

The operations_registry card rendered "Check admin auth." for EVERY failure,
even when the real cause was a probe timeout on the heavy 16-op overview
aggregation (auth passthrough is correct). Misattributing a timeout to auth is
a truth defect. The reason must reflect the actual error class; a real hang is
an honest UNKNOWN, never a fake green.
"""
from backend.routes.occ_health_aggregator import _unreachable_reason, _eval_operations_overview


def test_timeout_is_not_attributed_to_auth():
    r = _unreachable_reason("ReadTimeout: timed out after 6s")
    assert "timed out" in r.lower()
    assert "auth" not in r.lower()


def test_auth_rejection_is_attributed_to_auth():
    assert "authorization" in _unreachable_reason("HTTP 401").lower()
    assert "authorization" in _unreachable_reason("HTTP 403").lower()


def test_connection_failure_attribution():
    assert "unreachable" in _unreachable_reason("ConnectError: connection refused").lower()


def test_operations_overview_unverifiable_on_timeout_reason():
    ev = _eval_operations_overview(None, "ReadTimeout: deadline exceeded", "2026-06-01T00:00:00Z")
    assert ev["status"] == "UNVERIFIABLE"  # honest UNKNOWN, never fake green
    assert "timed out" in (ev.get("recommended_action") or "").lower()


def test_operations_overview_success_still_evaluates_ops():
    body = {"operations": [
        {"id": "a", "status_snapshot": {"status": "healthy"}},
        {"id": "b", "status_snapshot": {"status": "critical"}},
    ]}
    ev = _eval_operations_overview(body, None, "2026-06-01T00:00:00Z")
    assert ev["status"] in ("MISMATCH", "DEGRADED", "VERIFIED")
