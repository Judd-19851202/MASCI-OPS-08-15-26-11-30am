"""Track 19.45A · Operational Intelligence Governance & Value
Certification · lock test.

Locks:
- Universal recipient management CRUD functions exist and are exported.
- Admin recipient add / list / update / deactivate / bulk-import routes
  are registered under /api/operational-intelligence/recipients.
- Group create + add-member routes registered.
- Deactivation is preferred over deletion (audit fields updated).
- Invalid email rejected.
- Bulk import dedupes by (email, product_id).
- 8 governance docs + PRD + CHANGELOG updated.
- No new email provider · no new scheduler.

Run isolated:
    pytest backend/tests/test_track_19_45a_governance_and_recipients.py -q
"""
from __future__ import annotations

import asyncio
from pathlib import Path

APP = Path("/app")
BE = APP / "backend"
MEM = APP / "memory"


# --------------------------------------------------- fake DB harness


class _Coll:
    def __init__(self):
        self.docs: list = []

    async def insert_one(self, d):
        self.docs.append(dict(d))
        return type("R", (), {"inserted_id": d.get("id")})()

    async def find_one(self, q, proj=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    async def update_one(self, q, upd):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update(upd.get("$set", {}))
                for k, v in (upd.get("$push", {}) or {}).items():
                    d.setdefault(k, []).append(v)
                return type("R", (), {"modified_count": 1})()
        return type("R", (), {"modified_count": 0})()

    def find(self, q=None, proj=None):
        rows = [d for d in self.docs
                if all(d.get(k) == v
                       for k, v in (q or {}).items()
                       if not isinstance(v, dict))]

        class _Cur:
            def __init__(self, r): self.r = list(r)

            def limit(self, n):
                self.r = self.r[:n]
                return self

            def sort(self, *a, **k): return self

            def __aiter__(self):
                self._it = iter(self.r)
                return self

            async def __anext__(self):
                try:
                    return next(self._it)
                except StopIteration:
                    raise StopAsyncIteration
        return _Cur(rows)


class _Db:
    def __init__(self):
        self._c = {}

    def __getitem__(self, name):
        return self._c.setdefault(name, _Coll())


# --------------------------------------------------- exports


def test_recipient_management_functions_exist():
    from operational_intelligence import (
        list_recipients, add_recipient, update_recipient,
        deactivate_recipient, bulk_import_recipients,
        list_groups, add_group, add_group_member,
    )
    for f in (list_recipients, add_recipient, update_recipient,
              deactivate_recipient, bulk_import_recipients,
              list_groups, add_group, add_group_member):
        assert callable(f)


# --------------------------------------------------- add / update / deactivate


def test_add_recipient_stamps_created_and_updated():
    from operational_intelligence import add_recipient

    async def _go():
        db = _Db()
        d = await add_recipient(
            db, email="Test@Masci.local ",
            product_id="safety_morning_digest",
            display_name="Test User",
            role_label="Safety",
            added_by="admin@masci",
        )
        assert d["email"] == "test@masci.local"    # normalised
        assert d["display_name"] == "Test User"
        assert d["digest_type"] == "safety_morning_digest"
        assert d["active"] is True
        assert d["created_at"]
        assert d["updated_at"]
        assert d["added_by"] == "admin@masci"
        assert d["updated_by"] == "admin@masci"

    asyncio.run(_go())


def test_add_recipient_rejects_invalid_email():
    from operational_intelligence import add_recipient
    import pytest

    async def _go():
        db = _Db()
        with pytest.raises(ValueError):
            await add_recipient(db, email="not-an-email",
                                product_id="safety_morning_digest")

    asyncio.run(_go())


def test_update_recipient_stamps_updated_only():
    from operational_intelligence import add_recipient, update_recipient

    async def _go():
        db = _Db()
        d = await add_recipient(
            db, email="u@m.co", product_id="fleet_intelligence",
            display_name="A",
        )
        rid = d["id"]
        orig_created = d["created_at"]
        upd = await update_recipient(
            db, recipient_id=rid, updated_by="mgr@masci",
            display_name="B", role_label="Fleet",
        )
        assert upd["display_name"] == "B"
        assert upd["role_label"] == "Fleet"
        assert upd["updated_by"] == "mgr@masci"
        # created_* untouched
        assert upd["created_at"] == orig_created

    asyncio.run(_go())


def test_deactivate_recipient_flips_active_flag():
    from operational_intelligence import add_recipient, deactivate_recipient

    async def _go():
        db = _Db()
        d = await add_recipient(db, email="x@m.co",
                                product_id="hr_intelligence")
        upd = await deactivate_recipient(
            db, recipient_id=d["id"], updated_by="admin@masci")
        assert upd["active"] is False
        assert upd["updated_by"] == "admin@masci"

    asyncio.run(_go())


# --------------------------------------------------- bulk import


def test_bulk_import_dedupes_by_email_and_product():
    from operational_intelligence import bulk_import_recipients

    async def _go():
        db = _Db()
        res = await bulk_import_recipients(
            db,
            rows=[
                {"email": "a@m.co", "product_id": "fleet_intelligence"},
                {"email": "a@m.co", "product_id": "fleet_intelligence"},  # dup
                {"email": "a@m.co", "product_id": "hr_intelligence"},     # ok
                {"email": "not-an-email", "product_id": "fleet_intelligence"},
                {"email": "b@m.co"},  # missing product & no default
            ],
        )
        assert res["inserted"] == 2
        assert res["duplicate"] == 1
        assert res["skipped"] == 2

    asyncio.run(_go())


def test_bulk_import_uses_default_product_id():
    from operational_intelligence import bulk_import_recipients

    async def _go():
        db = _Db()
        res = await bulk_import_recipients(
            db,
            rows=[{"email": "c@m.co"}, {"email": "d@m.co"}],
            default_product_id="training_intelligence",
        )
        assert res["inserted"] == 2

    asyncio.run(_go())


# --------------------------------------------------- routes registered


def test_admin_recipient_routes_are_registered():
    """The route module must register at least the CRUD + bulk + groups
    endpoint paths under /api/operational-intelligence/recipients + /groups."""
    src = (BE / "operational_intelligence" / "routes.py").read_text(encoding="utf-8")
    for path in (
        '/operational-intelligence/recipients"',
        '/operational-intelligence/recipients/for/{product_id}"',
        '/operational-intelligence/recipients/{recipient_id}"',
        '/operational-intelligence/recipients/bulk-import"',
        '/operational-intelligence/groups"',
        '/operational-intelligence/groups/{group_id}/members"',
    ):
        assert path in src, f"missing route: {path}"


def test_no_new_email_provider_or_scheduler_in_track_19_45a():
    engine_dir = BE / "operational_intelligence"
    banned = ("resend.emails.send", "sendgrid", "smtplib", "postmark",
              "APScheduler", "BackgroundScheduler", "AsyncIOScheduler",
              "CronTrigger")
    for f in engine_dir.glob("*.py"):
        t = f.read_text(encoding="utf-8")
        for b in banned:
            assert b not in t, f"drift in {f.name}: {b}"


# --------------------------------------------------- documentation locks


REQUIRED_DOCS = [
    "TRACK_19_45A_GOVERNANCE_AUDIT.md",
    "TRACK_19_45A_RECIPIENT_GOVERNANCE.md",
    "TRACK_19_45A_EMAIL_INVENTORY.md",
    "TRACK_19_45A_SIGNAL_TO_NOISE_AUDIT.md",
    "TRACK_19_45A_VALUE_CERTIFICATION.md",
    "TRACK_19_45A_SCORE_AND_TREND_CERTIFICATION.md",
    "TRACK_19_45A_DEPARTMENT_VALUE_AUDIT.md",
    "TRACK_19_45A_INDUSTRY_COMPARISON.md",
    "TRACK_19_45A_COCKPIT_READINESS.md",
    "TRACK_19_45A_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_45A_TEST_REPORT.md",
]


def test_all_track_19_45a_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_prd_updated():
    assert "TRACK 19.45A" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.45A" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
