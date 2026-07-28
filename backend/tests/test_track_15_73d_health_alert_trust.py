"""TRACK 15.73D · Health Monitor + Backup Card Trust — pytest gate.

Static + DB invariant tests for the alert-spam + backup-card-stale fixes.

1. health_monitor.py defines the Mongo-persisted cooldown helpers
   (`_load_cooldown` and `_persist_cooldown`) — the in-memory dict is
   gone.
2. admin_ops.py backup card calls `_r2_backup_age_seconds_cached` so
   the alert source-of-truth matches `/api/health/full`.
3. `db.health_alert_cooldowns` schema is correct when an upsert lands.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv(Path("/app/backend/.env"))


@pytest.fixture(scope="module")
def db():
    client = MongoClient(os.environ["MONGO_URL"])
    yield client[os.environ["DB_NAME"]]
    client.close()


def test_health_monitor_uses_mongo_persisted_cooldown():
    src = Path("/app/backend/health_monitor.py").read_text()
    # In-memory tracker must be GONE.
    assert "last_alerted: Dict[str, datetime] = {}" not in src, (
        "health_monitor.py still uses an in-memory cooldown dict — "
        "this is the Track 15.73D alert-spam root cause."
    )
    # Mongo-persisted helpers must be PRESENT.
    assert "_load_cooldown" in src, "Missing _load_cooldown helper."
    assert "_persist_cooldown" in src, "Missing _persist_cooldown helper."
    assert "health_alert_cooldowns" in src, (
        "Cooldown must be persisted to db.health_alert_cooldowns collection."
    )
    assert 'run_with_singleton_lock(db, "synthetic_health_monitor"' in src, (
        "Health monitor must run under singleton lock to avoid multi-worker duplicate polls/emails."
    )


def test_admin_ops_backup_card_consults_r2():
    src = Path("/app/backend/routes/admin_ops.py").read_text()
    assert "build_canonical_archive_lineage" in src, (
        "admin_ops.py backup card must consult canonical archive lineage "
        "before falling back — otherwise alerts can drift from real R2 truth."
    )


def test_complete_archive_includes_disk_backed_files_and_object_storage_notice():
    src = Path("/app/backend/server.py").read_text()
    assert 'disk_files/' in src, "Complete archive must include disk-backed files in disk_files/."
    assert 'disk-backed' in src and 'object storage' in src, (
        "Complete archive notice must truthfully describe disk-backed and object-storage coverage."
    )
    assert 'photos_rehydrated' in src and 'documents_rehydrated' in src, (
        "Restore path must rehydrate both photo:// and doc:// embedded object payloads."
    )


def test_health_alert_cooldowns_collection_shape(db):
    """If the cooldown collection has any docs, each must carry the
    expected schema."""
    cur = db.health_alert_cooldowns.find({}, {"_id": 0}).limit(10)
    for doc in cur:
        assert "subsystem" in doc, "cooldown row missing `subsystem` key"
        assert "last_alerted_at" in doc, "cooldown row missing `last_alerted_at`"
        sub = (doc.get("subsystem") or "").strip()
        assert sub, "cooldown subsystem key must be non-empty"
