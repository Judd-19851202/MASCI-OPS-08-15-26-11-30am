"""
test_iter172_phase_k1_identity_mirror.py — Phase K1 verification.

Pure-database tests for the silent unified-identity mirror. Phase K1
is explicitly a zero-UX, zero-auth-flow change; we only verify the
mirror engine here.

Properties verified:
  1. Indexes are created.
  2. Backfill creates one row per distinct email across portal collections.
  3. Multi-portal users → portals list is unioned.
  4. Mirrored rows are tagged `mirrored=True` and carry an unguessable hash.
  5. Pre-existing managed rows are NOT overwritten.
  6. Backfill is idempotent.
  7. New portal users picked up on next run.
  8. Portals list grows when a mirrored user appears in a new portal.
  9. Email uniqueness enforced at DB index level.
 10. Empty + malformed inputs handled safely.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

sys.path.insert(0, "/app/backend")


def _load_env(p: str) -> None:
    txt = Path(p).read_text()
    for line in txt.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env("/app/backend/.env")
from lib.identity_mirror import backfill_mirror, ensure_indexes  # noqa: E402


def _run(coro_factory):
    """Run an async test body in a fresh event loop with its own
    motor client + test database. Drops the DB on exit no matter what.

    coro_factory: async function that takes a `db` handle and returns
    whatever the test asserts on.
    """
    name = f"masci_test_iter172_{uuid.uuid4().hex[:10]}"

    async def body():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[name]
        try:
            return await coro_factory(db)
        finally:
            await client.drop_database(name)
            client.close()

    return asyncio.run(body())


async def _seed_portal(db, coll: str, email: str, name: str = ""):
    await db[coll].insert_one({
        "id": str(uuid.uuid4()),
        "email": email,
        "name": name or email.split("@")[0],
        "role": "Mechanic",
        "is_active": True,
        "password_hash": bcrypt.hashpw(b"seedpw", bcrypt.gensalt(rounds=4)).decode("ascii"),
    })


def test_indexes_created():
    async def body(db):
        await ensure_indexes(db)
        return await db.user_directory.index_information()
    info = _run(body)
    assert "email_unique" in info
    assert "id_unique" in info
    assert "mirrored_flag" in info
    assert "portals_arr" in info


def test_backfill_creates_one_row_per_email():
    async def body(db):
        await _seed_portal(db, "hr_users", "alice@mascigc.com")
        await _seed_portal(db, "shop_users", "bob@mascigc.com")
        await _seed_portal(db, "safety_users", "charlie@mascigc.com")
        stats = await backfill_mirror(db)
        count = await db.user_directory.count_documents({})
        return stats, count
    stats, count = _run(body)
    assert stats["scanned_emails"] == 3
    assert stats["created"] == 3
    assert count == 3


def test_multi_portal_union():
    email = "multi@mascigc.com"

    async def body(db):
        await _seed_portal(db, "hr_users", email)
        await _seed_portal(db, "shop_users", email)
        await _seed_portal(db, "safety_users", email)
        await backfill_mirror(db)
        return await db.user_directory.find_one({"email": email}, {"_id": 0})

    row = _run(body)
    assert row is not None
    assert sorted(row["portals"]) == ["hr", "safety", "shop"]
    assert row["mirrored"] is True


def test_mirrored_rows_have_random_unguessable_hash():
    async def body(db):
        await _seed_portal(db, "hr_users", "hash-test@mascigc.com")
        await backfill_mirror(db)
        return await db.user_directory.find_one({"email": "hash-test@mascigc.com"}, {"_id": 0})

    row = _run(body)
    assert row["password_hash"]
    for guess in ("", "password", "seedpw", "Maddix123!", "MASCI1982!"):
        assert not bcrypt.checkpw(guess.encode(), row["password_hash"].encode("ascii"))


def test_managed_row_is_not_overwritten():
    email = "managed@mascigc.com"
    managed_hash = bcrypt.hashpw(b"realmasterpw", bcrypt.gensalt(rounds=4)).decode("ascii")

    async def body(db):
        now = datetime.now(timezone.utc).isoformat()
        await db.user_directory.insert_one({
            "id": str(uuid.uuid4()),
            "email": email,
            "name": "Managed User",
            "portals": ["admin", "hr", "pm"],
            "password_hash": managed_hash,
            "is_super_admin": False,
            "disabled": False,
            "must_change_password": False,
            "created_at": now,
            "updated_at": now,
        })
        await _seed_portal(db, "shop_users", email)
        await backfill_mirror(db)
        return await db.user_directory.find_one({"email": email}, {"_id": 0})

    row = _run(body)
    assert sorted(row["portals"]) == ["admin", "hr", "pm"]
    assert row["password_hash"] == managed_hash
    assert "shop" in (row.get("mirror_sources") or {})


def test_backfill_is_idempotent():
    async def body(db):
        await _seed_portal(db, "hr_users", "idem-a@mascigc.com")
        await _seed_portal(db, "shop_users", "idem-b@mascigc.com")
        s1 = await backfill_mirror(db)
        s2 = await backfill_mirror(db)
        s3 = await backfill_mirror(db)
        count = await db.user_directory.count_documents({})
        return s1, s2, s3, count

    s1, s2, s3, count = _run(body)
    assert s1["created"] == 2
    assert s2["created"] == 0
    assert s3["created"] == 0
    assert s2["updated_mirrored"] == 2
    assert s3["updated_mirrored"] == 2
    assert count == 2


def test_new_portal_user_picked_up_on_rerun():
    async def body(db):
        await _seed_portal(db, "hr_users", "first@mascigc.com")
        s1 = await backfill_mirror(db)
        await _seed_portal(db, "shop_users", "second@mascigc.com")
        s2 = await backfill_mirror(db)
        count = await db.user_directory.count_documents({})
        return s1, s2, count

    s1, s2, count = _run(body)
    assert s1["created"] == 1
    assert s2["created"] == 1
    assert count == 2


def test_portals_list_grows_when_user_added_to_new_portal():
    email = "growing@mascigc.com"

    async def body(db):
        await _seed_portal(db, "hr_users", email)
        s1 = await backfill_mirror(db)
        row1 = await db.user_directory.find_one({"email": email}, {"_id": 0})
        await _seed_portal(db, "shop_users", email)
        s2 = await backfill_mirror(db)
        row2 = await db.user_directory.find_one({"email": email}, {"_id": 0})
        return s1, row1, s2, row2

    s1, row1, s2, row2 = _run(body)
    assert s1["created"] == 1
    assert sorted(row1["portals"]) == ["hr"]
    assert s2["created"] == 0
    assert s2["updated_mirrored"] == 1
    assert sorted(row2["portals"]) == ["hr", "shop"]


def test_email_uniqueness_enforced():
    async def body(db):
        await ensure_indexes(db)
        email = "dup@mascigc.com"
        await db.user_directory.insert_one({"id": str(uuid.uuid4()), "email": email})
        try:
            await db.user_directory.insert_one({"id": str(uuid.uuid4()), "email": email})
            return False
        except DuplicateKeyError:
            return True

    assert _run(body) is True


def test_empty_portal_collections_are_safe():
    async def body(db):
        return await backfill_mirror(db)

    stats = _run(body)
    assert stats["scanned_emails"] == 0
    assert stats["created"] == 0


def test_malformed_emails_are_skipped():
    async def body(db):
        await db.hr_users.insert_one({"id": str(uuid.uuid4()), "email": None})
        await db.hr_users.insert_one({"id": str(uuid.uuid4())})
        await db.hr_users.insert_one({"id": str(uuid.uuid4()), "email": "not-an-email"})
        await db.hr_users.insert_one({"id": str(uuid.uuid4()), "email": "valid@mascigc.com"})
        return await backfill_mirror(db)

    stats = _run(body)
    assert stats["scanned_emails"] == 1
    assert stats["created"] == 1
