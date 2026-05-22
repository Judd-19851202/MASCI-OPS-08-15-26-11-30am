"""iter329 · Scheduled Cultural Banner Calendar — contract.

Locks down:
  • Each entry in CULTURAL_CALENDAR resolves to the correct UTC date
    for the current/next year (Memorial Day = last Monday of May,
    Thanksgiving = 4th Thursday of Nov, Labor Day = 1st Monday of
    Sept, etc.).
  • The activation window is `pre_hours` BEFORE → `post_hours` AFTER
    the anchor date (default 24 / 24; Christmas 48 / 48).
  • `ensure_cultural_banners(db, now=...)` is idempotent — calling
    twice on the same date never duplicates.
  • Cultural banners ship with severity='cultural' and `auto_posted=True`.
  • Banner copy is preserved bilingual at source (no LLM dependency).
  • Operational severity precedence is unchanged.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from cultural_banner_calendar import (
    CULTURAL_CALENDAR,
    ensure_cultural_banners,
    _memorial_day,
    _thanksgiving,
    _labor_day,
    _independence_day,
    _veterans_day,
    _christmas,
    _new_year,
)


# ─── Date resolvers ──────────────────────────────────────────────────


def test_iter329_memorial_day_2026_is_last_monday_of_may():
    d = _memorial_day(2026)
    # 2026 Memorial Day = Monday, May 25, 2026.
    assert d == datetime(2026, 5, 25, tzinfo=timezone.utc)


def test_iter329_thanksgiving_2026_is_fourth_thursday_of_nov():
    d = _thanksgiving(2026)
    # 2026 Thanksgiving = Thursday, Nov 26, 2026.
    assert d == datetime(2026, 11, 26, tzinfo=timezone.utc)


def test_iter329_labor_day_2026_is_first_monday_of_sept():
    d = _labor_day(2026)
    # 2026 Labor Day = Monday, Sep 7, 2026.
    assert d == datetime(2026, 9, 7, tzinfo=timezone.utc)


def test_iter329_fixed_date_holidays_are_correct():
    assert _independence_day(2026) == datetime(2026, 7, 4, tzinfo=timezone.utc)
    assert _veterans_day(2026) == datetime(2026, 11, 11, tzinfo=timezone.utc)
    assert _christmas(2026) == datetime(2026, 12, 25, tzinfo=timezone.utc)
    assert _new_year(2027) == datetime(2027, 1, 1, tzinfo=timezone.utc)


# ─── Activation window ──────────────────────────────────────────────


def test_iter329_activation_window_is_24h_before_and_24h_after():
    """Default entries activate 24h before, deactivate 24h after."""
    memorial = next(e for e in CULTURAL_CALENDAR if e.template_id == "memorial_day")
    start, end = memorial.window(2026)
    assert start == datetime(2026, 5, 24, tzinfo=timezone.utc)
    assert end == datetime(2026, 5, 26, tzinfo=timezone.utc)


def test_iter329_christmas_window_extended_to_48h():
    """Christmas runs longer per the entry config (covers Eve & Day 2)."""
    christmas = next(e for e in CULTURAL_CALENDAR if e.template_id == "christmas")
    start, end = christmas.window(2026)
    assert start == datetime(2026, 12, 23, tzinfo=timezone.utc)
    assert end == datetime(2026, 12, 27, tzinfo=timezone.utc)


# ─── Bilingual-at-source verification ───────────────────────────────


def test_iter329_every_entry_ships_bilingual_at_source():
    """No LLM dependency for cultural banners — EN + ES copy is
    curated in CULTURAL_CALENDAR and shipped at the source."""
    for entry in CULTURAL_CALENDAR:
        assert entry.title_en and entry.title_en.strip(), f"{entry.template_id} missing title_en"
        assert entry.title_es and entry.title_es.strip(), f"{entry.template_id} missing title_es"
        assert entry.body_en and entry.body_en.strip(), f"{entry.template_id} missing body_en"
        assert entry.body_es and entry.body_es.strip(), f"{entry.template_id} missing body_es"
        # ES copy must differ from EN (catches accidental copy-paste).
        assert entry.title_es != entry.title_en, f"{entry.template_id} title_es duplicates title_en"
        assert entry.body_es != entry.body_en, f"{entry.template_id} body_es duplicates body_en"


# ─── Calendar coverage ───────────────────────────────────────────────


def test_iter329_calendar_covers_all_approved_major_holidays():
    """The approved holidays in the iter329 spec must all ship in
    CULTURAL_CALENDAR (no silent omissions)."""
    expected = {
        "new_year", "memorial_day", "independence_day", "labor_day",
        "veterans_day", "thanksgiving", "christmas",
    }
    actual = {e.template_id for e in CULTURAL_CALENDAR}
    missing = expected - actual
    assert not missing, f"Cultural calendar missing approved holidays: {missing}"


# ─── ensure_cultural_banners idempotency + duplicate protection ─────


def _async_iter_mock(items):
    """Helper — turn a list into an async iterator for motor mocks."""
    async def _iter():
        for it in items:
            yield it
    return _iter()


def test_iter329_ensure_skips_when_outside_any_window():
    """No holiday today (Feb 14, 2026 = nothing in the calendar) →
    zero inserts."""
    db = MagicMock()
    db.hub_banners = MagicMock()
    db.hub_banners.find_one = AsyncMock(return_value=None)
    db.hub_banners.insert_one = AsyncMock()
    now = datetime(2026, 2, 14, 12, 0, tzinfo=timezone.utc)
    result = asyncio.run(ensure_cultural_banners(db, now=now))
    assert result == []
    db.hub_banners.insert_one.assert_not_called()


def test_iter329_ensure_posts_on_holiday_window_boundary():
    """Inside the 24h pre-Memorial-Day window → one insert."""
    db = MagicMock()
    db.hub_banners = MagicMock()
    db.hub_banners.find_one = AsyncMock(return_value=None)
    db.hub_banners.insert_one = AsyncMock()
    # Memorial Day 2026 = May 25. Window starts May 24 00:00 UTC.
    now = datetime(2026, 5, 24, 6, 0, tzinfo=timezone.utc)
    result = asyncio.run(ensure_cultural_banners(db, now=now))
    assert len(result) == 1
    posted = result[0]
    assert posted["template_id"] == "memorial_day"
    assert posted["severity"] == "cultural"
    assert posted["auto_posted"] is True
    assert posted["auto_posted_iter"] == "iter329"
    assert posted["created_by"] == "cultural-calendar"
    # Window end = May 26 00:00 UTC.
    assert posted["expires_at"] == datetime(2026, 5, 26, tzinfo=timezone.utc).isoformat()


def test_iter329_ensure_is_idempotent_no_duplicate_when_already_active():
    """If an active banner with matching template_id exists, no insert."""
    db = MagicMock()
    db.hub_banners = MagicMock()
    db.hub_banners.find_one = AsyncMock(return_value={
        "id": "existing",
        "template_id": "memorial_day",
        "expires_at": datetime(2026, 5, 26, tzinfo=timezone.utc).isoformat(),
    })
    db.hub_banners.insert_one = AsyncMock()
    now = datetime(2026, 5, 24, 6, 0, tzinfo=timezone.utc)
    result = asyncio.run(ensure_cultural_banners(db, now=now))
    assert result == []
    db.hub_banners.insert_one.assert_not_called()


def test_iter329_ensure_swallows_db_errors():
    """DB unavailable → returns []; never raises into the banner
    list endpoint."""
    db = MagicMock()
    db.hub_banners = MagicMock()
    db.hub_banners.find_one = AsyncMock(side_effect=RuntimeError("mongo down"))
    db.hub_banners.insert_one = AsyncMock()
    now = datetime(2026, 5, 24, 6, 0, tzinfo=timezone.utc)
    result = asyncio.run(ensure_cultural_banners(db, now=now))
    assert result == []
    db.hub_banners.insert_one.assert_not_called()


def test_iter329_ensure_double_call_inserts_only_once():
    """Real idempotency check — call the ensure twice with the same
    `now`. The second call must NOT insert (the first call's record
    is returned by find_one)."""
    db = MagicMock()
    db.hub_banners = MagicMock()
    inserted_record = {}

    async def fake_find_one(query):
        # Mirror the duplicate-protection lookup behavior.
        if not inserted_record:
            return None
        if inserted_record.get("template_id") == query.get("template_id"):
            return inserted_record
        return None

    async def fake_insert(doc):
        inserted_record.update(doc)
        return MagicMock()

    db.hub_banners.find_one = fake_find_one
    db.hub_banners.insert_one = fake_insert

    now = datetime(2026, 5, 24, 6, 0, tzinfo=timezone.utc)
    first = asyncio.run(ensure_cultural_banners(db, now=now))
    second = asyncio.run(ensure_cultural_banners(db, now=now))
    assert len(first) == 1
    assert second == []


# ─── Operational severity precedence (regression of iter328) ────────


def test_iter329_does_not_alter_severity_rank():
    """Reading the hub_banners route source confirms cultural still
    sorts at priority 9 (below every operational tier)."""
    src = open("/app/backend/routes/hub_banners.py").read()
    assert '"cultural": 9' in src, (
        "Cultural severity must remain at priority 9 — iter329 must "
        "not alter the iter328 hierarchy contract."
    )
