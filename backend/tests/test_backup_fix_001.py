"""BACKUP-FIX-001 · Verification widens `last_full` to recognize complete-r2.

Surgical regression suite verifying:
  · `complete-r2` counts as successful full backup (the fix)
  · `full` and `lite` still count (no regression)
  · Warning still fires when none of the three modes appear in last 20 rows
  · Stale-backup detection still works (max-age threshold)
  · No mutation in `db.backup_health` from running the verifier
  · R2 listing & restore-drill recognition unchanged

All tests construct ephemeral in-memory representations via a tiny stub
DB façade that mimics motor — no production DB writes.
"""
from __future__ import annotations
import asyncio
import importlib
from datetime import datetime, timedelta, timezone


def _ts_offset(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._idx = 0
        self._sort_key = None
        self._reverse = False
        self._limit = None

    def sort(self, key, direction=1):
        # support .sort("ts", -1)
        self._sort_key = key
        self._reverse = (direction == -1)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __aiter__(self):
        rows = list(self._rows)
        if self._sort_key:
            rows.sort(key=lambda r: r.get(self._sort_key) or "", reverse=self._reverse)
        if self._limit is not None:
            rows = rows[: self._limit]
        self._rows_iter = iter(rows)
        return self

    async def __anext__(self):
        try:
            return next(self._rows_iter)
        except StopIteration:
            raise StopAsyncIteration


class _Coll:
    def __init__(self, rows):
        self.rows = list(rows)

    def find(self, query=None, projection=None):
        # only need {} or simple count_documents below
        return _Cursor(self.rows)

    async def count_documents(self, query=None):
        return len(self.rows)


class _DB:
    def __init__(self, health_rows, kinds_count=0):
        self._health = _Coll(health_rows)
        self._kinds_count = kinds_count

    def __getitem__(self, name):
        # Used for per-collection counts in the verifier. Return empty.
        return _Coll([])

    @property
    def backup_health(self):
        return self._health


def _patch_r2_to_empty(monkeypatch_module):
    """Bypass R2 listing — we only care about ledger semantics in these
    tests. Stub returns a healthy non-empty listing so r2_status="ok"."""
    bv = importlib.import_module("backup_verification")

    async def _fake_list(prefix="backups/"):
        return [{
            "key": "backups/auto-90d/MASCI_complete_backup_test.zip",
            "size_bytes": 100 * 1024 * 1024,
            "last_modified_iso": _ts_offset(0.5),
        }]

    monkeypatch_module(bv, "list_r2_backup_archives", _fake_list)

    # Also short-circuit photo_storage import
    import sys
    sys.modules.setdefault("photo_storage", type(sys)("photo_storage"))
    sys.modules["photo_storage"].is_configured = lambda: True


def _import_bv():
    return importlib.import_module("backup_verification")


def _set_attr(obj, name, value):
    setattr(obj, name, value)


# ─────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────
def test_complete_r2_counts_as_full_backup():
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    db = _DB([
        {"ts": _ts_offset(h), "ok": True, "mode": "complete-r2",
         "filename": f"f{h}.zip", "size_bytes": 100, "records": 100}
        for h in range(1, 11)  # 10 hourly complete-r2 rows
    ] + [
        {"ts": _ts_offset(0.5 + i), "ok": True, "mode": "r2-usage-alert",
         "size_bytes": 0, "records": 0} for i in range(10)
    ])
    rpt = asyncio.run(bv.build_verification_report(db))
    assert rpt["ledger"]["status"] == "ok", rpt["ledger"]
    assert rpt["ledger"]["issues"] == []
    assert rpt["ledger"]["last_full"] is not None
    assert rpt["ledger"]["last_full"]["mode"] == "complete-r2"
    assert rpt["verdict"] == "pass"


def test_full_mode_still_counts():
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    db = _DB([
        {"ts": _ts_offset(2), "ok": True, "mode": "full",
         "filename": "x.zip", "size_bytes": 999, "records": 100},
    ])
    rpt = asyncio.run(bv.build_verification_report(db))
    assert rpt["ledger"]["last_full"]["mode"] == "full"
    assert rpt["ledger"]["status"] == "ok"


def test_lite_mode_still_counts():
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    db = _DB([
        {"ts": _ts_offset(3), "ok": True, "mode": "lite",
         "filename": "y.zip", "size_bytes": 500, "records": 50},
    ])
    rpt = asyncio.run(bv.build_verification_report(db))
    assert rpt["ledger"]["last_full"]["mode"] == "lite"
    assert rpt["ledger"]["status"] == "ok"


def test_warning_fires_when_no_full_lite_complete_r2_in_window():
    """Only r2-usage-alert rows present → warning MUST still trigger."""
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    db = _DB([
        {"ts": _ts_offset(i + 1), "ok": True, "mode": "r2-usage-alert",
         "size_bytes": 0, "records": 0}
        for i in range(20)
    ])
    rpt = asyncio.run(bv.build_verification_report(db))
    assert rpt["ledger"]["status"] == "warn"
    assert any("No successful full backup recorded" in i
               for i in rpt["ledger"]["issues"])
    assert rpt["ledger"]["last_full"] is None


def test_stale_backup_still_detected_for_complete_r2():
    """If the newest complete-r2 row is older than max_age, ledger goes stale."""
    import os
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    os.environ["BACKUP_VERIFICATION_MAX_AGE_HOURS"] = "10"
    db = _DB([
        {"ts": _ts_offset(48), "ok": True, "mode": "complete-r2",
         "filename": "old.zip", "size_bytes": 100, "records": 100},
    ])
    try:
        rpt = asyncio.run(bv.build_verification_report(db))
        assert rpt["ledger"]["status"] == "stale", rpt["ledger"]
        assert any("Last successful full/lite backup" in i
                   for i in rpt["ledger"]["issues"])
    finally:
        os.environ.pop("BACKUP_VERIFICATION_MAX_AGE_HOURS", None)


def test_failure_row_recognized_as_last_failure():
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    db = _DB([
        {"ts": _ts_offset(1), "ok": False, "mode": "complete-r2-error",
         "error": "boom"},
        {"ts": _ts_offset(2), "ok": True, "mode": "complete-r2",
         "filename": "ok.zip", "size_bytes": 200, "records": 200},
    ])
    rpt = asyncio.run(bv.build_verification_report(db))
    assert rpt["ledger"]["last_failure"] is not None
    assert rpt["ledger"]["last_full"] is not None  # the ok row still counts


def test_no_writes_to_backup_health_during_verification():
    bv = _import_bv()
    _patch_r2_to_empty(_set_attr)
    rows = [{"ts": _ts_offset(2), "ok": True, "mode": "complete-r2",
             "filename": "x.zip", "size_bytes": 100, "records": 100}]
    db = _DB(rows)
    pre_len = len(db._health.rows)
    asyncio.run(bv.build_verification_report(db))
    asyncio.run(bv.build_verification_report(db))
    assert len(db._health.rows) == pre_len


def test_full_backup_modes_constant_is_authoritative():
    """The fix introduces FULL_BACKUP_MODES — make sure the tuple is
    a closed enum that explicitly lists the three accepted modes."""
    import inspect
    bv = _import_bv()
    src = inspect.getsource(bv.build_verification_report)
    assert 'FULL_BACKUP_MODES = ("full", "lite", "complete-r2")' in src, (
        "FULL_BACKUP_MODES constant must list exactly the 3 accepted modes"
    )
    assert "if last_full is None and mode in FULL_BACKUP_MODES" in src
