from __future__ import annotations

import os
from dataclasses import dataclass

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


def _db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]]


def _route_handler(router, path: str):
    return next(r.endpoint for r in router.routes if getattr(r, "path", "") == path)


@dataclass
class _FakeIdentity:
    app_env: str = "preview"
    db_name: str = "masci_safety_preview"

    def to_safe_dict(self):
        return {
            "app_env": self.app_env,
            "db_name": self.db_name,
        }


@dataclass
class _FakeValidation:
    status: str = "VERIFIED"
    valid: bool = True
    mismatch_category: str | None = None

    def to_safe_dict(self):
        return {
            "status": self.status,
            "valid": self.valid,
            "mismatch_category": self.mismatch_category,
            "detail": "test-bundle",
            "errors": [],
            "warnings": [],
            "remediation_owner": "tests",
            "remediation_action": "none",
        }


def _runtime_bundle(status: str = "VERIFIED"):
    return {
        "identity": _FakeIdentity(),
        "validation": _FakeValidation(status=status),
    }


async def _call_validator(db, *, runtime_status: str = "VERIFIED"):
    from routes.admin_platform_trust import make_router  # noqa: PLC0415

    async def _passthrough_dep():
        return None

    router = make_router(
        db,
        _passthrough_dep,
        get_runtime_identity=lambda: _runtime_bundle(runtime_status),
    )
    handler = _route_handler(router, "/api/admin/platform-trust/validate")
    return await handler(_=None)


@pytest.mark.asyncio
async def test_checkpoint7_validator_adds_bounded_ots_truth_and_compatibility():
    payload = await _call_validator(_db())

    for field in [
        "track",
        "generated_at",
        "canonical_truth",
        "truth_relationship",
        "system",
        "email_routing",
        "audit_status_integrity",
        "workflow_delivery_health",
        "pm_email_coverage",
        "dead_letter_health",
        "final_band",
        "red_reasons",
        "amber_reasons",
        "ots_truth",
        "compatibility",
    ]:
        assert field in payload

    ots = payload["ots_truth"]
    assert ots["truth_subject"] == "platform_validation_truth"
    assert ots["canonical_owner"] == "platform_attestation"
    assert ots["claim_ceiling"] == "VALIDATED"
    assert ots["permitted_claim"] in {"OBSERVED", "CORRELATED", "VERIFIED", "VALIDATED"}
    assert ots["permitted_claim"] != "CERTIFIED"
    assert "platform certification" in ots["prohibited_claims"]
    assert payload["compatibility"]["breaking_api_changes"] == 0
    assert payload["compatibility"]["new_additive_fields"] == 2
    assert payload["truth_relationship"]["role"] == "VALIDATOR"
    assert payload["truth_relationship"]["canonical_owner_id"] == "platform_attestation"


@pytest.mark.asyncio
async def test_checkpoint7_validator_never_exceeds_upstream_owner_claim():
    payload = await _call_validator(_db(), runtime_status="DEGRADED")
    ots = payload["ots_truth"]
    assert ots["claim_ceiling"] == "VALIDATED"
    assert ots["permitted_claim"] in {"OBSERVED", "CORRELATED", "VERIFIED"}
    assert ots["permitted_claim"] != "VALIDATED"
    assert payload["truth_relationship"]["canonical_status"] == payload["ots_truth"]["truth_evaluation"]


@pytest.mark.asyncio
async def test_checkpoint7_validator_unknown_and_contradiction_projection_is_visible():
    db = _db()
    payload = await _call_validator(db)
    ots = payload["ots_truth"]

    assert isinstance(ots["unknowns"], list)
    assert isinstance(ots["contradictory_evidence"], list)

    if payload["final_band"] == "red":
        assert ots["contradictory_evidence"], "red validation must project contradictions"
        assert payload["truth_relationship"]["has_conflict"] is True

    if payload["final_band"] in {"amber", "red"}:
        assert ots["degradation_reasons"], "degraded validation must explain why the claim was bounded"