"""iter426 · Phase 25.3 · Restore Continuity + Backup Drift tests.

Verifies:
  1. `_backup_drift_watch` logs a WARN line when a collection disappears.
  2. `backup_drift_history` collection retains last 30 snapshots (FIFO trim).
  3. Newly-inlined disk-backup root `/app/memory` is recognised.
  4. Restore-readiness simulation: a freshly-built archive contains every
     expected manifest field + every Phase 12-25 collection key.
  5. Operational-attachment binary round-trips through archive + decode.
"""
from __future__ import annotations

import base64
import json
import logging
import sys
import uuid
import zipfile
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def server_module():
    sys.path.insert(0, "/app/backend")
    import server  # noqa: PLC0415
    return server


@pytest.fixture
def tmp_zip(tmp_path) -> Path:
    return tmp_path / f"iter426-archive-{uuid.uuid4().hex[:6]}.zip"


@pytest.fixture(scope="module")
def seed_attachment(server_module):
    """Insert one operational_attachments row with a known binary so we can
    round-trip its data_b64 through the archive."""
    import os
    from pymongo import MongoClient
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    cli = MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
    try:
        db = cli[db_name]
        tag = f"iter426-{uuid.uuid4().hex[:6]}"
        # known bytes · base64 of "MASCI-RESTORE-DRILL"
        raw = b"MASCI-RESTORE-DRILL"
        db.operational_attachments.insert_one({
            "id": f"oa-iter426-{tag}",
            "tenant_id": tag,
            "type": "breakdown_photo",
            "filename": "drill.png",
            "content_type": "image/png",
            "data_b64": base64.b64encode(raw).decode("ascii"),
            "size_bytes": len(raw),
        })
    finally:
        cli.close()
    return {"raw": raw, "tag": tag}


# ──────────────────────────────────────────────────────────────
# 1. Drift watcher: WARN when a collection disappears
# ──────────────────────────────────────────────────────────────
def test_iter426_drift_watcher_logs_disappearance(server_module, caplog):
    """Simulate two consecutive runs · second run has a missing collection.
    Verify a calm WARN line surfaces."""
    import asyncio
    import os
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]

    async def _run():
        cli = AsyncIOMotorClient(mongo_url)
        try:
            db = cli[db_name]
            # Clear drift history for a clean test
            await db.backup_drift_history.delete_many(
                {"captured_collections": {"$in": [["iter426-drift-ghost"]]}},
            )
            # First "run" — record a known set
            await server_module._backup_drift_watch(db, {
                "captured_collections": [
                    "iter426-drift-a", "iter426-drift-b", "iter426-drift-ghost",
                ],
                "total_records": 100,
                "explicit_exclusions": [],
            })
            # Second "run" — ghost disappears
            with caplog.at_level(logging.WARNING, logger="server"):
                await server_module._backup_drift_watch(db, {
                    "captured_collections": ["iter426-drift-a", "iter426-drift-b"],
                    "total_records": 80,
                    "explicit_exclusions": [],
                })
            # Cleanup
            await db.backup_drift_history.delete_many(
                {"captured_collections": {"$elemMatch": {"$regex": "^iter426-drift"}}},
            )
        finally:
            cli.close()

    asyncio.new_event_loop().run_until_complete(_run())
    # Verify a WARN with "DRIFT" + "disappeared" + "iter426-drift-ghost"
    msgs = " ".join(r.message for r in caplog.records if r.levelno >= logging.WARNING)
    assert "DRIFT" in msgs, f"Expected DRIFT warn line; got: {msgs[:400]}"
    assert "iter426-drift-ghost" in msgs, f"Disappeared collection missing from log: {msgs[:400]}"


# ──────────────────────────────────────────────────────────────
# 2. Drift history is capped (FIFO trim to 30)
# ──────────────────────────────────────────────────────────────
def test_iter426_drift_history_capped(server_module):
    import asyncio
    import os
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]

    async def _run():
        cli = AsyncIOMotorClient(mongo_url)
        try:
            db = cli[db_name]
            # Clean slate for this scenario
            await db.backup_drift_history.delete_many({"_iter426_test": True})
            # Pre-seed 35 history entries with the marker
            from datetime import datetime, timezone
            docs = [{
                "id": str(uuid.uuid4()),
                "recorded_at": datetime.now(timezone.utc),
                "captured_collections": ["a", "b"],
                "total_records": i,
                "_iter426_test": True,
            } for i in range(35)]
            await db.backup_drift_history.insert_many(docs)
            # Run the watcher once — it should trim total back to 30
            await server_module._backup_drift_watch(db, {
                "captured_collections": ["a", "b"],
                "total_records": 999,
                "explicit_exclusions": [],
            })
            count = await db.backup_drift_history.count_documents({})
            # The new entry brings total to 36 pre-trim · trim leaves 30
            assert count <= 30, f"history not trimmed: {count}"
            # Cleanup
            await db.backup_drift_history.delete_many({"_iter426_test": True})
        finally:
            cli.close()

    asyncio.new_event_loop().run_until_complete(_run())


# ──────────────────────────────────────────────────────────────
# 3. /app/memory is in DISK_BACKUP_ROOTS · doc continuity
# ──────────────────────────────────────────────────────────────
def test_iter426_memory_in_disk_backup_roots():
    text = Path("/app/backend/server.py").read_text()
    assert '("/app/memory", "memory")' in text, (
        "/app/memory not registered in DISK_BACKUP_ROOTS — repo loss insurance missing"
    )


# ──────────────────────────────────────────────────────────────
# 4. Restore-readiness: archive manifest carries every iter425 audit field
# ──────────────────────────────────────────────────────────────
def test_iter426_archive_manifest_restore_ready(server_module, tmp_zip):
    server_module._build_complete_archive_on_disk(None, tmp_zip)
    with zipfile.ZipFile(str(tmp_zip)) as zf:
        manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))
    # iter425 audit fields all present
    for k in (
        "generated_at", "mode", "total_records", "per_kind",
        "captured_collections", "explicit_exclusions",
        "redaction_rules_applied", "inlined_photos",
    ):
        assert k in manifest, f"MANIFEST missing field: {k}"
    assert manifest["mode"] == "complete"
    # Phase 12-25 collections present (auto-discovery proof)
    captured = set(manifest["captured_collections"])
    for required in (
        "dispatch_assignments", "dispatch_continuity_events",
        "operational_attachments", "user_passkeys",
    ):
        assert required in captured, f"Restore archive missing {required}"
    # Notice is operator-friendly
    assert "MFA secrets" in manifest["notice"], "Manifest notice does not mention MFA redaction"


# ──────────────────────────────────────────────────────────────
# 5. Operational attachment binary round-trip · restore-readiness
# ──────────────────────────────────────────────────────────────
def test_iter426_attachment_binary_roundtrip(server_module, tmp_zip, seed_attachment):
    server_module._build_complete_archive_on_disk(None, tmp_zip)
    with zipfile.ZipFile(str(tmp_zip)) as zf:
        oa_files = [n for n in zf.namelist() if n.startswith("operational_attachments/json/")]
        assert oa_files, "operational_attachments missing from archive"
        # Walk every row · find the iter426 seeded one
        for name in oa_files:
            row = json.loads(zf.read(name).decode("utf-8"))
            if row.get("id", "").startswith("oa-iter426"):
                # Decode and compare
                decoded = base64.b64decode(row["data_b64"])
                assert decoded == seed_attachment["raw"], (
                    f"Restored attachment bytes drift: "
                    f"got {decoded[:40]!r} expected {seed_attachment['raw'][:40]!r}"
                )
                return
        pytest.fail("iter426 seed attachment not present in archive")
