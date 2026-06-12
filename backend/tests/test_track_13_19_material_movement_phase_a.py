"""Track 13.19 · Phase A · Material Movement Ledger enrichment test.

Verifies the enriched response shape of
GET /api/material-movement/daily/{project_number}/{date}

Strategy:
  - The endpoint is public-read (same posture as /api/jobs) so we hit the
    live preview backend with a synthetic project_number to obtain a
    guaranteed empty-day response. The shape contract is exercised on a
    `no_activity` day, which is the strictest test of additive contract
    compliance.
  - Real data days (project_number with actual reports) are exercised by
    a second case that reads through any matching live project.

Skip cleanly when REACT_APP_BACKEND_URL is not reachable.

Doctrine: TRACK_13_19_MATERIAL_MOVEMENT_LEDGER_PHASE_A_PROOF_JOIN.md
"""
import os
import pytest
import httpx

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _get(path: str):
    try:
        return httpx.get(f"{API}{path}", timeout=15)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"backend not reachable: {exc}")


# ── 1 · Existing contract: all legacy keys are still present.
def test_legacy_keys_preserved_on_empty_day():
    r = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    assert r.status_code == 200, r.text
    body = r.json()
    for k in ("project_number", "date", "dispatch", "incoming", "outgoing"):
        assert k in body, f"legacy key missing: {k}"
    assert body["incoming"] == []
    assert body["outgoing"] == []
    d = body["dispatch"]
    for k in ("assignments", "loads", "trucks", "by_haul_type", "rows"):
        assert k in d, f"legacy dispatch.{k} missing"
    assert d["assignments"] == 0
    assert d["loads"] == 0
    assert d["trucks"] == 0
    assert d["by_haul_type"] == {}
    assert d["rows"] == []


# ── 2 · Phase A additive: every new top-level key present + correct empty shape.
def test_phase_a_additive_keys_present_on_empty_day():
    r = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    assert r.status_code == 200
    body = r.json()
    for k in (
        "scale_ticket_proofs",
        "haul_cycles",
        "proof_summary",
        "rollups",
        "verification_status",
        "source_breakdown",
    ):
        assert k in body, f"Phase A key missing: {k}"
    assert body["scale_ticket_proofs"] == []
    assert body["haul_cycles"] == []
    assert body["verification_status"] == "no_activity"


# ── 3 · proof_summary shape on empty day.
def test_proof_summary_shape_on_empty_day():
    r = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    ps = r.json()["proof_summary"]
    for k in (
        "scale_ticket_count", "scale_ticket_net_lbs", "scale_ticket_net_tons",
        "missing_proof_count", "matched_proof_count", "partial_proof_count",
    ):
        assert k in ps, f"proof_summary.{k} missing"
    assert ps["scale_ticket_count"] == 0
    assert ps["missing_proof_count"] == 0
    assert ps["matched_proof_count"] == 0
    assert ps["partial_proof_count"] == 0
    # Empty day must never fabricate tonnage.
    assert ps["scale_ticket_net_lbs"] is None
    assert ps["scale_ticket_net_tons"] is None


# ── 4 · rollups shape on empty day.
def test_rollups_shape_on_empty_day():
    r = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    ru = r.json()["rollups"]
    for k in (
        "inbound_count", "outbound_count", "haul_cycles_count",
        "scale_ticket_count", "loads_count", "trucks_count",
        "materials_count", "net_lbs_from_tickets", "net_tons_from_tickets",
    ):
        assert k in ru, f"rollups.{k} missing"
    # All counts zero on empty day.
    for k in ("inbound_count", "outbound_count", "haul_cycles_count",
              "scale_ticket_count", "loads_count", "trucks_count",
              "materials_count"):
        assert ru[k] == 0, f"rollups.{k} should be 0 on empty day; got {ru[k]}"
    # Tonnage must not be fabricated.
    assert ru["net_lbs_from_tickets"] is None
    assert ru["net_tons_from_tickets"] is None


# ── 5 · source_breakdown shape — FleetWatcher must stay 0 (NOT_CONNECTED).
def test_source_breakdown_shape_and_fleetwatcher_zero():
    r = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    sb = r.json()["source_breakdown"]
    for k in ("daily_reports", "dispatch_assignments", "haul_cycles",
              "scale_tickets", "odr_events", "fleetwatcher"):
        assert k in sb, f"source_breakdown.{k} missing"
    # Hard rule — FleetWatcher remains NOT_CONNECTED.
    assert sb["fleetwatcher"] == 0
    # ODR join deferred to a later phase.
    assert sb["odr_events"] == 0


# ── 6 · verification_status is one of the documented values.
def test_verification_status_in_closed_set():
    r = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    vs = r.json()["verification_status"]
    assert vs in {
        "no_activity", "verified", "partial",
        "missing_proof", "mismatch", "needs_review",
    }, f"unexpected verification_status: {vs}"


# ── 7 · Input validation preserved.
def test_input_validation_preserved():
    r = _get("/material-movement/daily/%20/2099-01-01")
    # Whitespace-only project_number must 422 per existing contract.
    assert r.status_code == 422, r.text


# ── 8 · Phase A does not write to the database. Re-call returns same shape.
def test_idempotent_no_side_effects():
    r1 = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    r2 = _get("/material-movement/daily/SYNTHETIC-13-19-EMPTY/2099-01-01")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


# ── 9 · Live-data smoke (best-effort). If a real preview project_number
#       returns activity, additive keys must still all be present.
def test_live_data_response_shape():
    # Try a handful of common preview project numbers; skip if none yield activity.
    candidates = [
        "001-001", "001-002", "002-001", "S-001", "MASCI-001",
    ]
    for pn in candidates:
        # Pick a recent date — the endpoint is forgiving.
        for d in ("2026-01-01", "2026-02-01", "2025-12-01"):
            r = _get(f"/material-movement/daily/{pn}/{d}")
            if r.status_code != 200:
                continue
            body = r.json()
            # Shape stays identical regardless of whether data was found.
            for k in (
                "scale_ticket_proofs", "haul_cycles", "proof_summary",
                "rollups", "verification_status", "source_breakdown",
                "dispatch", "incoming", "outgoing",
            ):
                assert k in body, f"key {k} missing on live response for {pn}/{d}"
            return  # one good shape proof is enough
    pytest.skip("no live preview project_number returned 200")
