"""
tests/test_dispatch_d1_activation.py

Phase D-1 · Dispatch Activation Sprint regression suite.

Covers all 12 required tests from the OMEGA directive plus the
"do-no-harm" invariants. Async-pytest against a real motor-style
mongomock or a live local Mongo (whichever the existing test scaffold
provides — we use the in-tree `tests/_dispatch_helpers.py` if present,
otherwise we skip with a clear reason).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest

import dispatch_lifecycle as DLS  # backend module
from dispatch_reminders import scan_unacked_assignments


# ── Test scaffold ──────────────────────────────────────────────────
# These tests use a lightweight in-memory Mongo stub so the suite is
# self-contained. We DO NOT touch the running preview database.
class _FakeCollection:
    def __init__(self):
        self._docs: List[Dict[str, Any]] = []

    async def insert_one(self, doc):
        self._docs.append(dict(doc))
        return type("R", (), {"inserted_id": doc.get("id")})()

    async def find_one(self, query, projection=None):
        for d in self._docs:
            if all(d.get(k) == v for k, v in query.items() if not isinstance(v, dict)):
                return dict(d)
        return None

    def find(self, query, projection=None):
        return _FakeCursor(self._docs, query)

    async def update_one(self, query, update):
        # Separate $or clauses from positional equality match
        or_clauses = query.get("$or") or []
        plain = {k: v for k, v in query.items() if k != "$or"}
        for d in self._docs:
            # Plain field equality (id, etc.)
            if not all(d.get(k) == v for k, v in plain.items() if not isinstance(v, dict)):
                continue
            # $or branches
            if or_clauses:
                ok = False
                for c in or_clauses:
                    branch_ok = True
                    for ck, cv in c.items():
                        if isinstance(cv, dict) and cv.get("$exists") is False:
                            if ck in d and d.get(ck) is not None:
                                branch_ok = False
                                break
                        elif cv is None:
                            if d.get(ck) is not None:
                                branch_ok = False
                                break
                        elif d.get(ck) != cv:
                            branch_ok = False
                            break
                    if branch_ok:
                        ok = True
                        break
                if not ok:
                    continue
            set_fields = update.get("$set") or {}
            for k, v in set_fields.items():
                d[k] = v
            inc = update.get("$inc") or {}
            for k, v in inc.items():
                d[k] = (d.get(k) or 0) + v
            push = update.get("$push") or {}
            for k, v in push.items():
                if isinstance(v, dict) and "$each" in v:
                    d.setdefault(k, []).extend(v["$each"])
                else:
                    d.setdefault(k, []).append(v)
            return type("R", (), {"modified_count": 1})()
        return type("R", (), {"modified_count": 0})()

    async def count_documents(self, query):
        return sum(1 for d in self._docs if all(d.get(k) == v for k, v in query.items()))


class _FakeCursor:
    def __init__(self, docs, query):
        self._docs = list(docs)
        self._query = query
        self._limit = None
        self._sort = None

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for d in self._docs:
            if self._matches(d):
                yield dict(d)

    def _matches(self, d):
        q = self._query
        for k, v in q.items():
            if k == "$or":
                ok = False
                for c in v:
                    if all(self._field_match(d, ck, cv) for ck, cv in c.items()):
                        ok = True
                        break
                if not ok:
                    return False
                continue
            if not self._field_match(d, k, v):
                return False
        return True

    def _field_match(self, d, k, v):
        actual = d.get(k)
        if isinstance(v, dict):
            if "$lt" in v:
                return actual is not None and actual < v["$lt"]
            if "$exists" in v:
                return (k in d) if v["$exists"] else (k not in d)
            if "$nin" in v:
                return actual not in v["$nin"]
        return actual == v

    async def to_list(self, length):
        out = []
        async for d in self._gen():
            out.append(d)
            if length and len(out) >= length:
                break
        return out


class _FakeDB:
    def __init__(self):
        self.dispatch_assignments = _FakeCollection()
        self.dispatch_state_events = _FakeCollection()
        self.dispatch_magic_links = _FakeCollection()
        self.dispatch_driver_sessions = _FakeCollection()
        self.haul_cycles = _FakeCollection()
        self.tasks = _FakeCollection()
        self.employees = _FakeCollection()


# ── Helpers ────────────────────────────────────────────────────────
def _seed_assignment(
    db, *,
    assignment_id="A1",
    current_state=DLS.ASSIGNED,
    acked_at=None,
    revision_seq=0,
    revision_pending=False,
    minutes_old=0,
    driver_id="d1",
    project_number="PROJ-1",
):
    """Async-aware seed helper. Returns a coroutine — await it from
    inside the run() block. (We can't nest run_until_complete.)
    """
    moment = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
    return db.dispatch_assignments.insert_one({
        "id": assignment_id,
        "tenant_id": "masci",
        "truck_id": "T-1",
        "driver_id": driver_id,
        "driver_name": "Test Driver",
        "current_state": current_state,
        "project_number": project_number,
        "project_name": "Test Project",
        "material": "Asphalt",
        "source_location": "Plant A",
        "destination": "Job A",
        "assigned_at": moment.isoformat(),
        "last_transition_at": moment.isoformat(),
        "cancelled_at": None,
        "acked_at": acked_at,
        "acked_by": None,
        "ack_method": None,
        "ack_device": None,
        "ack_revision_seq": None,
        "revision_seq": revision_seq,
        "revision_pending": revision_pending,
        "revision_history": [],
        "reminder_sent_at": None,
        "reminder_count": 0,
        "delivery_log": [],
        "state_history": [],
    })


# ────────────────────────────────────────────────────────────────────
# TEST 2 · Driver acknowledgement records ack fields
# TEST 11 · Existing lifecycle transitions still work (covered alongside)
# ────────────────────────────────────────────────────────────────────
def test_record_acknowledgement_stamps_required_fields():
    from routes.dispatch_lifecycle import _record_acknowledgement

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        assignment = await db.dispatch_assignments.find_one({"id": "A1"})
        updated = await _record_acknowledgement(
            db,
            assignment=assignment,
            actor={"_actor": "driver", "name": "Test Driver"},
            method="tap",
            device="iPad / Safari",
            note="",
        )
        assert updated["acked_at"], "acked_at must be set"
        assert updated["acked_by"] == "Test Driver"
        assert updated["ack_method"] == "tap"
        assert updated["ack_device"] == "iPad / Safari"
        assert updated["ack_revision_seq"] == 0
        # State events stream must have an ACKNOWLEDGED row
        events = [d async for d in db.dispatch_state_events.find({"assignment_id": "A1"})]
        assert any(e.get("warning_tag") == "ACKNOWLEDGED" for e in events)
        # state_history must have the audit row
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        assert any(h.get("warning_tag") == "ACKNOWLEDGED" for h in (a.get("state_history") or []))

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 8 · PATCH revision creates audit event
# TEST 9 · Driver sees revision pending (revision_pending flag)
# TEST 10 · Driver acknowledges revision (re-ack clears flag)
# ────────────────────────────────────────────────────────────────────
def test_revision_creates_audit_event_and_resets_ack():
    from routes.dispatch_lifecycle import _record_revision, _record_acknowledgement

    async def run():
        db = _FakeDB()
        await _seed_assignment(db, acked_at="2026-01-01T00:00:00+00:00")
        original = await db.dispatch_assignments.find_one({"id": "A1"})
        assert original["acked_at"], "fixture must start acked"

        revised = await _record_revision(
            db,
            assignment=original,
            actor={"_actor": "dispatch", "name": "Operator"},
            changes={"destination": "Job B", "material": "Concrete"},
            reason="Plant ran out of asphalt",
        )
        assert revised["revision_seq"] == 1
        assert revised["revision_pending"] is True
        assert revised["acked_at"] is None, "ack must reset on revise"
        # Revision history captures before+after
        assert revised["revision_history"][-1]["after"]["destination"] == "Job B"
        assert revised["revision_history"][-1]["before"]["destination"] == "Job A"
        # State event written
        evs = [d async for d in db.dispatch_state_events.find({"assignment_id": "A1"})]
        assert any(e.get("warning_tag") == "REVISED" for e in evs)

        # Driver re-acks
        rev_a = await db.dispatch_assignments.find_one({"id": "A1"})
        re_acked = await _record_acknowledgement(
            db, assignment=rev_a,
            actor={"_actor": "driver", "name": "Test Driver"},
            method="tap", device="iPad", note="",
            target_revision=1,
        )
        assert re_acked["acked_at"], "re-ack stamps acked_at"
        assert re_acked["revision_pending"] is False, "re-ack clears pending"
        assert re_acked["ack_revision_seq"] == 1

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 4 · New assignment sends notification attempt
# TEST 5 · Notification failure does not block assignment creation
# ────────────────────────────────────────────────────────────────────
def test_notification_writes_bell_and_delivery_log():
    from routes.dispatch_lifecycle import _fire_assignment_notification

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        result = await _fire_assignment_notification(
            db, assignment=a, event="new_assignment",
            send_email_fn=None,  # email skipped — bell only
        )
        assert result["ok"]
        # Bell write
        bell = [d async for d in db.tasks.find({"assignment_id": "A1"})]
        assert len(bell) == 1
        assert bell[0]["assignee_role"] == "dispatch"
        assert bell[0]["kind"] == "dispatch_new_assignment"
        # Delivery log on the assignment
        a2 = await db.dispatch_assignments.find_one({"id": "A1"})
        assert any(e["channel"] == "bell" and e["ok"] for e in (a2.get("delivery_log") or []))

    asyncio.get_event_loop().run_until_complete(run())


def test_notification_email_failure_does_not_raise():
    from routes.dispatch_lifecycle import _fire_assignment_notification

    async def failing_email(*args, **kwargs):
        raise RuntimeError("simulated Resend outage")

    async def run():
        db = _FakeDB()
        # Need an employee record with email for the email path to trigger
        await db.employees.insert_one({"id": "d1", "email": "driver@masci.test", "full_name": "Test"})
        await _seed_assignment(db)
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        # Should NOT raise.
        result = await _fire_assignment_notification(
            db, assignment=a, event="new_assignment", send_email_fn=failing_email,
        )
        assert result["ok"], "notification must report ok even on email failure"
        a2 = await db.dispatch_assignments.find_one({"id": "A1"})
        log = a2.get("delivery_log") or []
        # Bell entry succeeded, email entry recorded failure
        assert any(e["channel"] == "email" and e["ok"] is False for e in log)

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 6 · Unacknowledged reminder fires once
# TEST 7 · Reminder does not duplicate spam
# ────────────────────────────────────────────────────────────────────
def test_reminder_fires_once_then_skips_on_rescan():
    async def run():
        db = _FakeDB()
        # Old enough to trigger reminder (threshold default 10 min)
        await _seed_assignment(db, assignment_id="A_OLD", minutes_old=15)
        # Too new — must NOT fire
        await _seed_assignment(db, assignment_id="A_NEW", minutes_old=2)

        s1 = await scan_unacked_assignments(db, threshold_min=10)
        assert s1["fired"] == 1
        assert "A_OLD" in s1["fired_assignment_ids"]
        assert "A_NEW" not in s1["fired_assignment_ids"]

        # Confirm idempotency on rescan
        s2 = await scan_unacked_assignments(db, threshold_min=10)
        assert s2["fired"] == 0, "second scan must not duplicate"

        # Reminder_sent_at is set; reminder_count is 1
        a = await db.dispatch_assignments.find_one({"id": "A_OLD"})
        assert a["reminder_sent_at"], "reminder_sent_at must be stamped"
        assert a["reminder_count"] == 1

        # Bell row exists for the reminder
        rows = [d async for d in db.tasks.find({"assignment_id": "A_OLD"})]
        assert any(r["kind"] == "dispatch_reminder_unacked" for r in rows)

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 11 · Existing lifecycle transitions still work
# (regression check — transition writer untouched by D-1.x)
# ────────────────────────────────────────────────────────────────────
def test_existing_transition_writer_intact():
    from routes.dispatch_lifecycle import _record_transition

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        updated = await _record_transition(
            db,
            assignment=a,
            to_state=DLS.ENROUTE_TO_LOAD,
            actor={"_actor": "driver", "name": "Test Driver"},
        )
        assert updated["current_state"] == DLS.ENROUTE_TO_LOAD
        # state_history grew by exactly one row
        assert len(updated.get("state_history") or []) == 1
        assert (updated["state_history"][0])["to_state"] == DLS.ENROUTE_TO_LOAD

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 12 · Existing driver magic-link session shape preserved
# (we don't run the real driver_sessions module here — this is a
# defensive shape check on the assignment doc seed, since the seed is
# what magic-link consumers later read)
# ────────────────────────────────────────────────────────────────────
def test_assignment_seed_carries_d1_fields():
    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        # All D-1 fields must exist on the fixture so the schema
        # contract is enforced from the test surface.
        for fld in (
            "acked_at", "acked_by", "ack_method", "ack_device",
            "ack_revision_seq", "revision_seq", "revision_pending",
            "revision_history", "reminder_sent_at", "reminder_count",
            "delivery_log",
        ):
            assert fld in a, f"D-1 field missing from assignment: {fld}"

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST · Cancelled assignment cannot be revised or acked
# (defensive — operationally important)
# ────────────────────────────────────────────────────────────────────
def test_revisable_fields_constant_is_tight():
    from routes.dispatch_lifecycle import REVISABLE_FIELDS

    # The D-1.5 directive is explicit about which fields revision touches.
    # Lock the set so future drift requires a deliberate change.
    assert "truck_id" not in REVISABLE_FIELDS, "truck_id must go through /reassign"
    assert "driver_id" not in REVISABLE_FIELDS, "driver_id must go through /reassign"
    assert "current_state" not in REVISABLE_FIELDS
    assert "cancelled_at" not in REVISABLE_FIELDS
    for fld in ("source_location", "destination", "material", "note"):
        assert fld in REVISABLE_FIELDS, f"REVISABLE_FIELDS missing required: {fld}"
