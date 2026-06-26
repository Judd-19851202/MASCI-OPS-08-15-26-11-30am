"""TRACK 15.93 · Zero-Touch Production Deployment Hardening regression.

Locks the contract:

* ``lib.system_bootstrap.run_system_bootstrap(db)`` exists and is
  the ONE canonical entry point for first-time system
  initialization.
* Idempotent. Safe to call unlimited times.
* Create-if-missing on ``db.email_routes`` — NEVER overwrites
  existing rows. NEVER deletes.
* Preserves admin-customized rows (``source in {"admin","manual"}``
  or ``admin_customized=True``) — operator edits are sacred.
* Persists state to ``db.system_bootstrap_status`` (``_id="latest"``)
  and appends ``db.system_bootstrap_history``.
* Critical-route safety — refuses to insert a critical route with
  an empty TO list.
* Server boot wires the bootstrap as an ``@app.on_event("startup")``
  hook that runs BEFORE the readiness flag flips.
* ``GET /api/admin/deployment-readiness`` exposes the ``bootstrap``
  block and blocks deploy if bootstrap never ran or did not
  complete OK.
"""
from __future__ import annotations

import os
import uuid

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


class _NamespacedDB:
    """Tiny shim that rewrites the four collection names the
    bootstrap touches into unique-per-test names on the existing
    preview DB. The Atlas user attached to this pod does not have
    ``createDatabase`` permission, so we cannot use a throwaway
    DB per test — instead we sandbox via collection-name prefix.
    """

    _MAPPED = {
        "email_routes",
        "system_bootstrap_status",
        "system_bootstrap_history",
        "email_routing_audit_v2",
    }

    def __init__(self, real_db, prefix: str):
        self._db = real_db
        self._prefix = prefix

    def __getattr__(self, name):
        if name in self._MAPPED:
            return self._db[f"{self._prefix}_{name}"]
        return getattr(self._db, name)

    def __getitem__(self, name):
        if name in self._MAPPED:
            return self._db[f"{self._prefix}_{name}"]
        return self._db[name]


def _sandboxed_db():
    """Return a (cli, ns_db, prefix) triple. Caller MUST call
    ``_cleanup(cli, prefix)`` at teardown."""
    prefix = f"t1593_{uuid.uuid4().hex[:10]}"
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    real = cli[os.environ["DB_NAME"]]
    return cli, _NamespacedDB(real, prefix), prefix


async def _cleanup(cli: AsyncIOMotorClient, prefix: str) -> None:
    real = cli[os.environ["DB_NAME"]]
    for coll in _NamespacedDB._MAPPED:
        try:
            await real.drop_collection(f"{prefix}_{coll}")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Static contract tests — fast, no DB.
# ---------------------------------------------------------------------------

def test_module_exists_and_exports_canonical_entry_point():
    from lib import system_bootstrap as sb  # noqa: PLC0415
    assert hasattr(sb, "run_system_bootstrap"), \
        "canonical run_system_bootstrap entry point must exist"
    assert hasattr(sb, "read_latest_bootstrap_status"), \
        "canonical read_latest_bootstrap_status must exist"
    assert hasattr(sb, "BOOTSTRAP_VERSION"), \
        "BOOTSTRAP_VERSION must be exported"
    assert isinstance(sb.BOOTSTRAP_VERSION, int) and sb.BOOTSTRAP_VERSION >= 1


def test_module_reuses_canonical_seed_catalog():
    """No duplicate catalog — single source of truth is the seed
    script's build_catalog(). The bootstrap MUST import it."""
    src = open("/app/backend/lib/system_bootstrap.py").read()
    assert "from track_15_65_seed_email_routes import build_catalog" in src, \
        "system_bootstrap must re-use build_catalog() — no duplicate catalog"


def test_server_registers_bootstrap_before_ready_flip():
    """Startup ordering invariant: bootstrap MUST register before
    the readiness flag handler. FastAPI runs startup events in
    registration order, so the bootstrap source position in
    server.py is the contract."""
    src = open("/app/backend/server.py").read()
    bs_pos = src.find("_track_15_93_run_system_bootstrap")
    flip_pos = src.find("_iter453_6_flip_ready_flag")
    assert bs_pos != -1, "_track_15_93_run_system_bootstrap hook missing"
    assert flip_pos != -1, "_iter453_6_flip_ready_flag hook missing"
    assert bs_pos < flip_pos, \
        "bootstrap startup hook must register BEFORE the readiness flip"


def test_readiness_endpoint_wires_bootstrap_block():
    """Deployment-readiness must publish the bootstrap status block
    AND add bootstrap_incomplete / bootstrap_never_ran to its
    blocking-gate vocabulary."""
    src = open("/app/backend/routes/admin_deployment_readiness.py").read()
    assert "bootstrap" in src
    assert "bootstrap_incomplete" in src
    assert "bootstrap_never_ran" in src
    assert "read_latest_bootstrap_status" in src


def test_deployment_gate_includes_track_15_93():
    """The new regression file MUST be in the permanent gate list."""
    src = open("/app/scripts/deployment_gate.py").read()
    assert "test_track_15_93_zero_touch_bootstrap.py" in src, \
        "deployment_gate.py must include the 15.93 regression file"


# ---------------------------------------------------------------------------
# Behaviour tests — run against a sandboxed namespace on the preview DB.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fresh_empty_database_initializes_all_routes():
    """Fresh DB → bootstrap creates all 19 routes; readiness state
    is OK; critical routes have non-empty TO."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        result = await run_system_bootstrap(db)
        assert result["ok"] is True, result
        assert result["missing_items"] == [], result["missing_items"]
        assert result["version"] >= 1
        assert result["started_at"] and result["completed_at"]

        # 19 docs present
        count = await db.email_routes.count_documents({})
        assert count == 19, f"expected 19 routes, got {count}"

        # Every critical route has at least one recipient
        async for r in db.email_routes.find({"critical": True}):
            assert (r.get("to") or [])[0], \
                f"critical route {r['route_key']} has empty TO"

        # All seeded rows are marked source=bootstrap
        async for r in db.email_routes.find({}):
            assert r.get("source") == "bootstrap", r
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_critical_routes_all_present_after_bootstrap():
    """The 3 routes that the trust-gate explicitly checks for must
    all exist with non-empty TO after bootstrap."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        await run_system_bootstrap(db)
        for key in ("COMPLIANCE_ALWAYS_CC", "SAFETY_FORMS_TO",
                    "PRE_OP_FAIL_FALLBACK"):
            row = await db.email_routes.find_one(
                {"route_key": key, "enabled": True}
            )
            assert row is not None, f"{key} missing after bootstrap"
            to_list = [a for a in (row.get("to") or []) if a]
            assert to_list, f"{key} TO list empty after bootstrap"
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_repeated_bootstrap_is_idempotent():
    """Run bootstrap N times; second run creates zero new docs.
    No churn. No duplicates."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        first = await run_system_bootstrap(db)
        first_step = next(s for s in first["steps"] if s["name"] == "email_routes")
        assert len(first_step["created"]) == 19

        second = await run_system_bootstrap(db)
        second_step = next(s for s in second["steps"] if s["name"] == "email_routes")
        assert second_step["created"] == [], \
            f"second run created routes: {second_step['created']}"
        assert len(second_step["skipped_existing"]) == 19, second_step

        third = await run_system_bootstrap(db)
        third_step = next(s for s in third["steps"] if s["name"] == "email_routes")
        assert third_step["created"] == []
        assert await db.email_routes.count_documents({}) == 19
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_partially_configured_database_only_fills_gaps():
    """Pre-insert 2 routes; bootstrap creates the remaining 17.
    Pre-existing rows are untouched."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        await db.email_routes.insert_one({
            "_id": "masci::SAFETY_FORMS_TO",
            "tenant_key": "masci",
            "route_key": "SAFETY_FORMS_TO",
            "to": ["pre.existing@example.com"],
            "cc": [], "bcc": [],
            "enabled": True,
            "critical": False,
            "source": "seed",
            "version": 1,
        })
        await db.email_routes.insert_one({
            "_id": "masci::SUPER_ADMIN_TO",
            "tenant_key": "masci",
            "route_key": "SUPER_ADMIN_TO",
            "to": ["pre.existing.super@example.com"],
            "cc": [], "bcc": [],
            "enabled": True,
            "critical": True,
            "source": "seed",
            "version": 1,
        })

        result = await run_system_bootstrap(db)
        step = next(s for s in result["steps"] if s["name"] == "email_routes")
        assert len(step["created"]) == 17, step["created"]
        assert "SAFETY_FORMS_TO" in step["skipped_existing"]
        assert "SUPER_ADMIN_TO" in step["skipped_existing"]
        assert await db.email_routes.count_documents({}) == 19

        sft = await db.email_routes.find_one({"_id": "masci::SAFETY_FORMS_TO"})
        assert sft["to"] == ["pre.existing@example.com"]
        sa = await db.email_routes.find_one({"_id": "masci::SUPER_ADMIN_TO"})
        assert sa["to"] == ["pre.existing.super@example.com"]
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_admin_customized_rows_are_never_overwritten():
    """Admin-customized rows must survive bootstrap untouched."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        await db.email_routes.insert_one({
            "_id": "masci::PRE_OP_FAIL_FALLBACK",
            "tenant_key": "masci",
            "route_key": "PRE_OP_FAIL_FALLBACK",
            "to": ["admin.edited@example.com"],
            "cc": ["cc.edited@example.com"],
            "bcc": [],
            "enabled": True,
            "critical": False,
            "source": "admin",
            "version": 7,
            "updated_by": "admin",
        })
        await db.email_routes.insert_one({
            "_id": "masci::COMPLIANCE_ALWAYS_CC",
            "tenant_key": "masci",
            "route_key": "COMPLIANCE_ALWAYS_CC",
            "to": ["compliance.custom@example.com"],
            "cc": [], "bcc": [],
            "enabled": True,
            "critical": False,
            "source": "seed",
            "admin_customized": True,
            "version": 3,
        })

        result = await run_system_bootstrap(db)
        step = next(s for s in result["steps"] if s["name"] == "email_routes")
        assert "PRE_OP_FAIL_FALLBACK" in step["skipped_admin_customized"]
        assert "COMPLIANCE_ALWAYS_CC" in step["skipped_admin_customized"]

        pof = await db.email_routes.find_one(
            {"_id": "masci::PRE_OP_FAIL_FALLBACK"}
        )
        assert pof["to"] == ["admin.edited@example.com"]
        assert pof["cc"] == ["cc.edited@example.com"]
        assert pof["source"] == "admin"
        assert pof["version"] == 7

        cac = await db.email_routes.find_one(
            {"_id": "masci::COMPLIANCE_ALWAYS_CC"}
        )
        assert cac["to"] == ["compliance.custom@example.com"]
        assert cac["admin_customized"] is True
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_bootstrap_never_deletes_existing_documents():
    """A pre-existing row that is NOT in the catalog must still
    survive bootstrap (no destructive cleanup)."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        await db.email_routes.insert_one({
            "_id": "masci::LEGACY_CUSTOMER_X_ONLY",
            "tenant_key": "masci",
            "route_key": "LEGACY_CUSTOMER_X_ONLY",
            "to": ["legacy@example.com"],
            "cc": [], "bcc": [],
            "enabled": True,
            "critical": False,
            "source": "manual",
            "version": 1,
        })

        await run_system_bootstrap(db)
        legacy = await db.email_routes.find_one(
            {"_id": "masci::LEGACY_CUSTOMER_X_ONLY"}
        )
        assert legacy is not None, "bootstrap deleted a row it didn't own"
        assert legacy["to"] == ["legacy@example.com"]
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_bootstrap_status_and_history_persisted():
    """Latest pointer must exist and history must accrue across
    runs."""
    from lib.system_bootstrap import (  # noqa: PLC0415
        read_latest_bootstrap_status,
        run_system_bootstrap,
    )

    cli, db, prefix = _sandboxed_db()
    try:
        await run_system_bootstrap(db)
        await run_system_bootstrap(db)
        await run_system_bootstrap(db)

        latest = await read_latest_bootstrap_status(db)
        assert latest is not None, "latest pointer missing"
        assert latest["ok"] is True
        assert latest["version"] >= 1

        hist_n = await db.system_bootstrap_history.count_documents({})
        assert hist_n == 3, f"expected 3 history rows, got {hist_n}"
    finally:
        await _cleanup(cli, prefix)


@pytest.mark.asyncio
async def test_critical_route_with_empty_to_is_refused():
    """If env vars are unset such that a critical route resolves
    to empty TO, bootstrap must refuse to insert it AND surface
    a missing_item rather than crashing."""
    from lib.system_bootstrap import run_system_bootstrap  # noqa: PLC0415

    cli, db, prefix = _sandboxed_db()
    try:
        from track_15_65_seed_email_routes import build_catalog  # noqa: PLC0415
        original_catalog = build_catalog()
        from lib import system_bootstrap as sb  # noqa: PLC0415

        def _bad_catalog():
            cat = []
            for r in original_catalog:
                if r["route_key"] == "SUPER_ADMIN_TO":
                    r = {**r, "to": []}
                cat.append(r)
            return cat

        original_fn = sb.build_catalog
        sb.build_catalog = _bad_catalog
        try:
            result = await run_system_bootstrap(db)
        finally:
            sb.build_catalog = original_fn

        step = next(s for s in result["steps"] if s["name"] == "email_routes")
        assert "SUPER_ADMIN_TO" in step["skipped_critical_empty"]
        sa = await db.email_routes.find_one({"_id": "masci::SUPER_ADMIN_TO"})
        assert sa is None, "critical-empty route must NOT be inserted"
        assert any("SUPER_ADMIN_TO" in m or "critical" in m
                   for m in step["missing_items"]), step["missing_items"]
        assert result["ok"] is False
    finally:
        await _cleanup(cli, prefix)
