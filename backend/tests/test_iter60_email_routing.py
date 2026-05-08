"""
test_iter60_email_routing
=========================
Verifies the DB-backed email-routing override module behaves correctly:

* env defaults are returned when no DB doc exists
* PUT-style save persists the override and `load` reflects it
* ``invalidate()`` busts the per-process 60s cache
* Empty list is treated as a legitimate "silence this" override
  (NOT confused with absent → fall back to env)
* List inputs are stripped + de-duped (case-insensitive)
* `shop_manager_fallback` is treated as a single string
* Invalid keys passed to `save()` are silently dropped
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class _FakeColl:
    def __init__(self):
        self.docs = {}
    async def find_one(self, q, proj=None):
        return self.docs.get(q.get("_id"))
    async def update_one(self, q, update, upsert=False):
        key = q["_id"]
        existing = self.docs.get(key, {})
        new = dict(existing)
        for k, v in (update.get("$set") or {}).items():
            new[k] = v
        self.docs[key] = new


class _FakeDb:
    def __init__(self):
        self.email_routing_config = _FakeColl()


def test_env_defaults_when_no_db_doc():
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    cfg = asyncio.run(er.load(db))
    # When env vars unset for these in tests, the hardcoded fallbacks still
    # populate the config so the platform never has empty critical lists.
    assert cfg["always_cc"] == ["jaymn.judd@mascigc.com", "safety@mascigc.com"]
    assert cfg["safety_forms_to"] == ["safety@mascigc.com", "jaymn.judd@mascigc.com"]
    assert cfg["leadership_always_to"] == [
        "jaymn.judd@mascigc.com",
        "safety@mascigc.com",
    ]
    assert cfg["shop_manager_fallback"] == "shopmanager@mascigc.com"
    assert cfg["_meta"]["source"] == "env"


def test_save_persists_and_load_reflects_override():
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.save(db, {
        "safety_forms_to": ["a@x.com", "b@x.com"],
        "severe_incident_cc": ["risk@x.com"],
    }))
    cfg = asyncio.run(er.load(db))
    assert cfg["safety_forms_to"] == ["a@x.com", "b@x.com"]
    assert cfg["severe_incident_cc"] == ["risk@x.com"]
    # Untouched keys still match env defaults
    assert cfg["always_cc"] == ["jaymn.judd@mascigc.com", "safety@mascigc.com"]
    assert cfg["_meta"]["source"] == "db"


def test_save_invalidates_cache():
    """Without explicit invalidate the 60s cache would mask the new write.
    `save` must call `invalidate` internally."""
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.load(db))  # warms cache
    asyncio.run(er.save(db, {"always_cc": ["new@x.com"]}))
    cfg = asyncio.run(er.load(db))  # must reflect the update, not stale cache
    assert cfg["always_cc"] == ["new@x.com"]


def test_empty_list_silences_the_route():
    """Passing [] is a legitimate user action — they want to silence the
    route. Must NOT be confused with "missing → fall back to env"."""
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.save(db, {"severe_incident_cc": []}))
    cfg = asyncio.run(er.load(db))
    assert cfg["severe_incident_cc"] == []
    assert cfg["_meta"]["source"] == "db"


def test_list_dedup_and_strip():
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.save(db, {
        "safety_forms_to": ["  a@x.com  ", "B@X.com", "a@x.com", "", "  "],
    }))
    cfg = asyncio.run(er.load(db))
    # 'a@x.com' kept once (first occurrence), 'B@X.com' kept since lower-cased
    # version differs from the first; whitespace stripped; empties dropped
    assert cfg["safety_forms_to"] == ["a@x.com", "B@X.com"]


def test_string_input_for_list_field_is_split_on_commas():
    """The admin endpoint may receive a comma-string from the UI textarea —
    `_normalize_value` should split it into a list automatically."""
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.save(db, {"backup_email_to": "a@x.com, b@x.com,c@x.com"}))
    cfg = asyncio.run(er.load(db))
    assert cfg["backup_email_to"] == ["a@x.com", "b@x.com", "c@x.com"]


def test_shop_manager_fallback_is_single_string():
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.save(db, {"shop_manager_fallback": "  custom@shop.com  "}))
    cfg = asyncio.run(er.load(db))
    assert cfg["shop_manager_fallback"] == "custom@shop.com"


def test_save_drops_unknown_keys():
    """Caller-injected garbage keys must not pollute the config doc."""
    import email_routing as er
    er.invalidate()
    db = _FakeDb()
    asyncio.run(er.save(db, {
        "always_cc": ["x@y.com"],
        "rogue_key": "naughty",
        "drop_db": True,
    }))
    doc = db.email_routing_config.docs["default"]
    assert "rogue_key" not in doc
    assert "drop_db" not in doc
    assert doc["always_cc"] == ["x@y.com"]
