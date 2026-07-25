from __future__ import annotations

from types import SimpleNamespace

import pytest


class _FakeCollection:
    def __init__(self, *, count_returns=None):
        self.count_returns = list(count_returns or [])

    async def count_documents(self, query):
        if self.count_returns:
            value = self.count_returns.pop(0)
            if isinstance(value, Exception):
                raise value
            return value
        return 0


class _FakeDb:
    def __init__(self, *, audit_returns=None, spine_returns=None):
        self.email_routing_audit_v2 = _FakeCollection(count_returns=audit_returns)
        self.trust_spine_events = _FakeCollection(count_returns=spine_returns)


def _route_handler(router, path: str):
    return next(r.endpoint for r in router.routes if getattr(r, "path", "") == path)


def _owner_payload(*, claim="VALIDATED", truth_evaluation="VERIFIED", evidence_state="validated", audit_reference="OTS-C6-TRUST-SPINE"):
    return {
        "canonical_status": truth_evaluation,
        "platform_band": "green",
        "workflow_count": 1,
        "total_events_24h": 3,
        "total_failed_24h": 0,
        "workflows": [{
            "workflow": "meeting",
            "band": "green",
            "events_24h": 3,
            "failed_24h": 0,
            "success_rate_24h": 1.0,
            "expected_stages": ["record_created", "completed"],
            "last_success": {"ts": "2026-07-25T00:00:00+00:00"},
            "last_failure": None,
        }],
        "ots_truth": {
            "permitted_claim": claim,
            "truth_evaluation": truth_evaluation,
            "evidence_state": evidence_state,
            "audit_reference": audit_reference,
            "unknowns": [],
            "contradictory_evidence": [],
            "evidence_timestamp": "2026-07-25T00:00:00+00:00",
        },
    }


def _categorized_score(*, score=94, band="green"):
    return {
        "trust_score": score,
        "score_band": band,
        "score_band_label": "legacy-label",
        "score_reason": "derived-score",
        "score_inputs": [],
        "categories": {
            "workflow_health": {"score": score, "band": band, "inputs": []},
            "routing_integrity": {"score": score, "band": band, "inputs": []},
            "notification_delivery": {"score": score, "band": band, "inputs": []},
            "master_data": {"score": score, "band": band, "inputs": []},
            "audit_integrity": {"score": score, "band": band, "inputs": []},
            "infrastructure": {"score": score, "band": band, "inputs": []},
            "security": {"score": score, "band": band, "inputs": []},
        },
    }


@pytest.mark.asyncio
async def test_otc_preserves_legacy_fields_and_adds_ots(monkeypatch):
    import routes.admin_operations_trust_center as otc_module

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(otc_module, "_hist_ensure", _noop)
    monkeypatch.setattr(otc_module, "write_snapshot", _noop)
    monkeypatch.setattr(otc_module, "read_trend", lambda *args, **kwargs: [])

    async def _findings(db):
        return []

    monkeypatch.setattr(otc_module, "collect_findings", _findings)
    monkeypatch.setattr(otc_module, "overall_band", lambda findings: "green")
    monkeypatch.setattr(otc_module, "compute_categorized_score", lambda **kwargs: _categorized_score())
    monkeypatch.setattr(otc_module, "compute_score", lambda **kwargs: {"trust_score": 94})
    monkeypatch.setattr(otc_module, "_load_trust_spine_payload", lambda db: (lambda _=None: _owner_payload()))

    async def _alert(*args, **kwargs):
        return {"result": "disabled"}

    monkeypatch.setattr(otc_module.red_alert, "maybe_send", _alert)

    db = _FakeDb(audit_returns=[0, 0, 0], spine_returns=[0])

    async def _pass():
        return None

    router = otc_module.make_router(db, _pass)
    payload = await _route_handler(router, "/api/admin/operations-trust-center")(_=None)

    assert payload["ots_truth"]["truth_subject"] == "shared_operational_trust_score"
    assert payload["ots_truth"]["truth_surface"]["surface_id"] == "operations_trust_center"
    assert payload["ots_truth"]["canonical_owner"] == "trust_spine"
    assert payload["ots_truth"]["claim_ceiling"] == "CORRELATED"
    assert payload["ots_truth"]["permitted_claim"] == "CORRELATED"
    assert payload["ots_truth"]["audit_reference"] == "C2-R1-OPERATIONS-TRUST-CENTER"
    assert payload["truth_relationship"]["canonical_owner_id"] == "trust_spine"
    assert payload["truth_relationship"]["canonical_owner_route"] == "/api/admin/trust-spine"
    assert payload["compatibility"]["breaking_api_changes"] == 0
    assert payload["compatibility"]["new_additive_fields"] == 2
    assert payload["score_band_label"] == "Green score band"


@pytest.mark.asyncio
async def test_otc_high_score_cannot_exceed_low_owner_claim(monkeypatch):
    import routes.admin_operations_trust_center as otc_module

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(otc_module, "_hist_ensure", _noop)
    monkeypatch.setattr(otc_module, "write_snapshot", _noop)
    monkeypatch.setattr(otc_module, "read_trend", lambda *args, **kwargs: [{"ts": "2026-07-25T00:00:00+00:00", "score": 98, "band": "green"}])

    async def _findings(db):
        return []

    monkeypatch.setattr(otc_module, "collect_findings", _findings)
    monkeypatch.setattr(otc_module, "overall_band", lambda findings: "green")
    monkeypatch.setattr(otc_module, "compute_categorized_score", lambda **kwargs: _categorized_score(score=98, band="green"))
    monkeypatch.setattr(otc_module, "compute_score", lambda **kwargs: {"trust_score": 98})
    monkeypatch.setattr(otc_module, "_load_trust_spine_payload", lambda db: (lambda _=None: _owner_payload(claim="OBSERVED", truth_evaluation="DEGRADED", evidence_state="stale")))

    async def _alert(*args, **kwargs):
        return {"result": "disabled"}

    monkeypatch.setattr(otc_module.red_alert, "maybe_send", _alert)

    db = _FakeDb(audit_returns=[0, 0, 0], spine_returns=[0])

    async def _pass():
        return None

    router = otc_module.make_router(db, _pass)
    payload = await _route_handler(router, "/api/admin/operations-trust-center")(_=None)

    assert payload["trust_score"] == 98
    assert payload["score_band"] == "green"
    assert payload["ots_truth"]["permitted_claim"] == "OBSERVED"
    assert payload["ots_truth"]["contradictory_evidence"]
    assert any("Trust Spine supports only OBSERVED" in item for item in payload["ots_truth"]["contradictory_evidence"])


@pytest.mark.asyncio
async def test_otc_owner_unavailable_produces_unknown_claim(monkeypatch):
    import routes.admin_operations_trust_center as otc_module

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(otc_module, "_hist_ensure", _noop)
    monkeypatch.setattr(otc_module, "write_snapshot", _noop)
    monkeypatch.setattr(otc_module, "read_trend", lambda *args, **kwargs: [])

    async def _findings(db):
        return []

    monkeypatch.setattr(otc_module, "collect_findings", _findings)
    monkeypatch.setattr(otc_module, "overall_band", lambda findings: "green")
    monkeypatch.setattr(otc_module, "compute_categorized_score", lambda **kwargs: _categorized_score(score=95, band="green"))
    monkeypatch.setattr(otc_module, "compute_score", lambda **kwargs: {"trust_score": 95})

    def _boom(db):
        raise RuntimeError("spine unavailable")

    monkeypatch.setattr(otc_module, "_load_trust_spine_payload", _boom)

    async def _alert(*args, **kwargs):
        return {"result": "disabled"}

    monkeypatch.setattr(otc_module.red_alert, "maybe_send", _alert)

    db = _FakeDb(audit_returns=[0, 0, 0], spine_returns=[0])

    async def _pass():
        return None

    router = otc_module.make_router(db, _pass)
    payload = await _route_handler(router, "/api/admin/operations-trust-center")(_=None)

    assert payload["ots_truth"]["permitted_claim"] == "UNKNOWN"
    assert payload["ots_truth"]["evidence_state"] == "owner_unavailable"
    assert payload["ots_truth"]["unknowns"]
