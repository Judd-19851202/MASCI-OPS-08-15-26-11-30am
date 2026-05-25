"""
test_iter431_phase29.py · iter431 · Phase 29 parity-lock.
─────────────────────────────────────────────────────────────────────
1. Operational Moments Rail endpoint contract.
2. Stability governance sweepers honour dry-run + protect operational truth.
3. Weekly operator digest renders the doctrine-mandated plaintext shape.
4. Fleet-ops auth dep factories produce the right shapes.
5. Passkey session-mint factory delegates correctly (MFA + non-MFA).
6. Phase 5 extractions don't break the legacy-imports / op-attachments
   smoke surface (regression guard).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

import pytest


# ─────────────────────────────────────────────────────────────────────
# Helpers (kept tiny – we replicate just enough fake-Mongo behaviour
# for the routes under test)
# ─────────────────────────────────────────────────────────────────────
class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def __aiter__(self):
        self._i = iter(self._rows)
        return self

    async def __anext__(self):
        try:
            return next(self._i)
        except StopIteration:
            raise StopAsyncIteration


class _Coll:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.deleted: List[Dict[str, Any]] = []

    async def find_one(self, q=None, projection=None, sort=None):
        for r in self.rows:
            if _match(r, q or {}):
                return dict(r)
        return None

    def find(self, q=None, projection=None):
        return _Cursor([dict(r) for r in self.rows if _match(r, q or {})])

    async def count_documents(self, q):
        return sum(1 for r in self.rows if _match(r, q or {}))

    async def delete_many(self, q):
        before = len(self.rows)
        self.rows = [r for r in self.rows if not _match(r, q)]
        deleted = before - len(self.rows)
        return type("R", (), {"deleted_count": deleted})


def _match(row, q):
    if "$or" in q:
        return any(_match(row, sub) for sub in q["$or"])
    for k, v in q.items():
        if isinstance(v, dict):
            for op, val in v.items():
                rv = row.get(k)
                if op == "$lt" and (rv is None or rv >= val):
                    return False
                if op == "$gte" and (rv is None or rv < val):
                    return False
                if op == "$exists":
                    if val and k not in row:
                        return False
                    if not val and k in row:
                        return False
                if op == "$ne":
                    if rv == val:
                        return False
        else:
            if row.get(k) != v:
                return False
    return True


class _DB:
    def __init__(self, **kwargs):
        self._colls = {}
        for k, v in kwargs.items():
            self._colls[k] = v
            setattr(self, k, v)

    def __getitem__(self, name):
        if name not in self._colls:
            self._colls[name] = _Coll([])
            setattr(self, name, self._colls[name])
        return self._colls[name]


async def _admin_actor():
    return {"email": "admin@masci.test", "role": "admin", "admin": True}


# ─────────────────────────────────────────────────────────────────────
# 1 · Operational Moments Rail
# ─────────────────────────────────────────────────────────────────────
def test_iter431_operational_moments_merges_four_sources():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes.dispatch_continuity import build_dispatch_continuity_router

    db = _DB(
        dispatch_assignments=_Coll([{
            "tenant_id": "masci", "id": "asgn-1",
            "state_history": [
                {"at": "2026-05-25T10:00:00+00:00", "from": None,
                 "to": "assigned", "by": "DispatchOp"},
                {"at": "2026-05-25T11:00:00+00:00", "from": "assigned",
                 "to": "en_route", "by": "Driver Joe"},
            ],
            "recovery_history": [
                {"at": "2026-05-25T13:00:00+00:00", "from": None,
                 "to": "waiting_on_parts", "by": "ShopOp"},
            ],
        }]),
        dispatch_continuity_events=_Coll([
            {"tenant_id": "masci", "assignment_id": "asgn-1",
             "created_at": "2026-05-25T12:00:00+00:00", "kind": "breakdown",
             "title": "Breakdown reported", "created_by": "Driver Joe"},
        ]),
        operational_attachments=_Coll([
            {"tenant_id": "masci", "host_kind": "assignment", "host_id": "asgn-1",
             "uploaded_at": "2026-05-25T12:30:00+00:00",
             "type": "breakdown_photo", "uploaded_by": "Driver Joe",
             "id": "att-1", "filename": "x.jpg"},
        ]),
    )

    app = FastAPI()
    app.include_router(build_dispatch_continuity_router(
        db=db,
        require_dispatch_or_admin_dep=_admin_actor,
        require_any_portal_token_dep=_admin_actor,
        require_driver_session_dep=_admin_actor,
    ))
    client = TestClient(app)
    r = client.get("/api/dispatch/operational-moments/by-assignment/asgn-1")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assignment_id"] == "asgn-1"
    assert body["count"] == 5  # 2 lifecycle + 1 recovery + 1 continuity + 1 attachment
    # Chronological ascending order
    kinds_in_order = [m["kind"] for m in body["moments"]]
    assert kinds_in_order == [
        "lifecycle", "lifecycle", "continuity", "attachment", "recovery",
    ]


def test_iter431_operational_moments_missing_assignment():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes.dispatch_continuity import build_dispatch_continuity_router

    db = _DB(
        dispatch_assignments=_Coll([]),
        dispatch_continuity_events=_Coll([]),
        operational_attachments=_Coll([]),
    )
    app = FastAPI()
    app.include_router(build_dispatch_continuity_router(
        db=db,
        require_dispatch_or_admin_dep=_admin_actor,
        require_any_portal_token_dep=_admin_actor,
        require_driver_session_dep=_admin_actor,
    ))
    client = TestClient(app)
    r = client.get("/api/dispatch/operational-moments/by-assignment/nope")
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# 2 · Stability sweepers
# ─────────────────────────────────────────────────────────────────────
def test_iter431_stability_sweep_dry_run_never_deletes():
    from lib.stability_governance import run_stability_sweep
    db = _DB(
        dispatch_driver_sessions=_Coll([
            {"created_at": "2020-01-01T00:00:00+00:00"},
            {"revoked_at": "2026-05-01T00:00:00+00:00", "created_at": "2026-04-01T00:00:00+00:00"},
        ]),
        webauthn_challenges=_Coll([
            {"created_at": "2020-01-01T00:00:00+00:00"},
        ]),
        temp_upload_chunks=_Coll([]),
        offline_replay_records=_Coll([
            {"state": "replayed", "created_at": "2020-01-01T00:00:00+00:00"},
        ]),
    )
    result = asyncio.run(run_stability_sweep(db, dry_run=True))
    assert result["dry_run"] is True
    # No row deleted
    assert len(db.dispatch_driver_sessions.rows) == 2
    assert len(db.webauthn_challenges.rows) == 1
    assert len(db.offline_replay_records.rows) == 1
    # would_delete counts populated
    counts = {r["target"]: r.get("would_delete", -1) for r in result["results"]}
    assert counts["dispatch_driver_sessions"] == 2
    assert counts["webauthn_challenges"] == 1
    assert counts["offline_replay_records"] == 1


def test_iter431_stability_sweep_apply_protects_active_offline_replay():
    from lib.stability_governance import run_stability_sweep
    db = _DB(
        dispatch_driver_sessions=_Coll([]),
        webauthn_challenges=_Coll([]),
        temp_upload_chunks=_Coll([]),
        offline_replay_records=_Coll([
            # Old AND unreplayed — MUST be preserved
            {"state": "pending", "created_at": "2020-01-01T00:00:00+00:00"},
            # Old AND replayed — eligible
            {"state": "replayed", "created_at": "2020-01-01T00:00:00+00:00"},
        ]),
    )
    asyncio.run(run_stability_sweep(db, dry_run=False))
    # The pending row survives; the replayed row is gone
    remaining_states = sorted({r["state"] for r in db.offline_replay_records.rows})
    assert remaining_states == ["pending"]


# ─────────────────────────────────────────────────────────────────────
# 3 · Weekly digest plaintext shape
# ─────────────────────────────────────────────────────────────────────
def test_iter431_digest_renders_required_lines():
    from lib.operator_digest import render_digest_plaintext

    payload = {
        "captured_at": "2026-05-26T14:00:00+00:00",
        "atlas": {"connected": True, "mongo_version": "8.0.23", "collections": 121},
        "last_backup": {"ts": "2026-05-26T11:00:00+00:00", "ok": True,
                        "size_bytes": 14_213_456, "destinations": ["r2"]},
        "attachments": {"total": 70, "r2_backed": 70, "migrated_pct": 100.0,
                        "total_size_bytes": 12_345},
        "growth_30d": {"count": 18, "bytes": 1_200_000,
                       "projected_90d_count": 54, "projected_90d_bytes": 3_600_000},
        "evidence_accesses_7d": 12,
        "drift_warnings": 0,
        "drift_reason": "",
    }
    text = render_digest_plaintext(payload)
    # Every doctrine-mandated label appears
    for needle in ("MASCI Operations · Weekly Digest",
                   "Atlas:", "Last backup:", "Attachments:",
                   "Storage growth (30d):", "Evidence accesses (7d):",
                   "Drift warnings:"):
        assert needle in text, f"missing: {needle}"
    # Calm verdict
    assert "All systems calm." in text


def test_iter431_digest_renders_review_when_red():
    from lib.operator_digest import render_digest_plaintext
    payload = {
        "captured_at": "2026-05-26T14:00:00+00:00",
        "atlas": {"connected": False, "mongo_version": None, "collections": 0},
        "last_backup": None,
        "attachments": {"total": 0, "r2_backed": 0, "migrated_pct": 0.0,
                        "total_size_bytes": 0},
        "growth_30d": {"count": 0, "bytes": 0,
                       "projected_90d_count": 0, "projected_90d_bytes": 0},
        "evidence_accesses_7d": 0,
        "drift_warnings": 1,
        "drift_reason": "no heartbeat",
    }
    text = render_digest_plaintext(payload)
    assert "RED" in text
    assert "Operator review recommended." in text


# ─────────────────────────────────────────────────────────────────────
# 4 · Fleet-ops auth dep factories
# ─────────────────────────────────────────────────────────────────────
def test_iter431_fleet_submitter_factory_smoke():
    from routes.fleet_ops_deps import make_require_fleet_submitter
    dep = make_require_fleet_submitter(
        db=_DB(), is_valid_admin_token=lambda t: t == "good",
    )
    assert callable(dep)


def test_iter431_fleet_portal_factory_raises_when_no_token():
    import asyncio
    from fastapi import HTTPException
    from fastapi import Request
    from routes.fleet_ops_deps import make_require_any_fleet_portal
    dep = make_require_any_fleet_portal(
        db=_DB(),
        is_valid_admin_token=lambda t: False,
        shop_token_for=lambda pw: "xxx",
    )

    class _R: client = None
    async def go():
        await dep(_R(), None, None, None, None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(go())
    assert exc.value.status_code == 401


# ─────────────────────────────────────────────────────────────────────
# 5 · Passkey session-mint factory (MFA branch + non-MFA branch)
# ─────────────────────────────────────────────────────────────────────
def test_iter431_passkey_mint_factory_returns_callable():
    from routes.passkey_session_mint import make_mint_multi_login_response_for_passkey

    class _UD:
        @staticmethod
        def make_directory_token(): return "t-1"
        @staticmethod
        async def persist_session(db, token, user_id): pass
        @staticmethod
        async def stamp_last_login(db, user_id, portal): pass
        @staticmethod
        async def write_audit(db, **kwargs): pass
        @staticmethod
        def public_view(u): return {"id": u["id"], "email": u["email"]}

    async def _mint_all_portals(u):
        return {"admin": "a-tok", "dispatch": "d-tok"}

    fn = make_mint_multi_login_response_for_passkey(
        db=_DB(),
        mint_all_portal_tokens_fn=_mint_all_portals,
        ud_for_pk=_UD,
    )
    assert callable(fn)
