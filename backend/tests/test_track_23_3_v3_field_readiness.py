"""TRACK 23.3 · V3 admin pilot control + resiliency wiring lock envelope.

Locks:
- Admin endpoints exist and are guarded by `require_admin`.
- Adding/removing pilot users is idempotent ($addToSet / $pull).
- Adding to pilot_users also removes from denied_users (prevents split-brain).
- Tenant-default POST accepts an explicit bool.
- Frontend V3 shell wires `useFormDraft`, `enqueueUpload`, `mintIdempotencyKey`,
  `saveCrewSetup`, `loadCrewSetup`, `useOnlineStatus`, `DraftStatusPill`,
  `DraftRestorePrompt`.
- Frontend flag hook persists the URL admin override in sessionStorage.
- Frontend shares the V1 form key `daily-report` so a mid-flight draft
  survives pilot flag flips in either direction.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from routes.ui_flags import COLL_UI_FLAGS, FLAG_KEY, register_dr_v3_flag_routes


class _Coll:
    def __init__(self, rows: Optional[List[Dict[str, Any]]] = None):
        self.rows = rows or []

    async def find_one(self, q, projection=None):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items()):
                return dict(r)
        return None

    async def update_one(self, q, update, upsert=False):
        matched = next((r for r in self.rows if all(r.get(k) == v for k, v in q.items())), None)

        class _R:
            matched_count = 1 if matched else 0
            upserted_id = None
            modified_count = 0

        if matched is None and upsert:
            new = {k: v for k, v in q.items() if not isinstance(v, dict)}
            if "$setOnInsert" in update:
                new.update(update["$setOnInsert"])
            self.rows.append(new)
            matched = new
        if matched is None:
            return _R()
        if "$set" in update:
            matched.update(update["$set"])
        if "$addToSet" in update:
            for k, v in update["$addToSet"].items():
                lst = matched.setdefault(k, [])
                if v not in lst:
                    lst.append(v)
        if "$pull" in update:
            for k, v in update["$pull"].items():
                lst = matched.get(k) or []
                matched[k] = [x for x in lst if x != v]
        return _R()


class _DB:
    def __init__(self):
        self._c = _Coll()

    def __getitem__(self, name):
        assert name == COLL_UI_FLAGS
        return self._c


# ── Endpoint surface: capture registered routes for direct call ──

class _Router:
    def __init__(self):
        self.routes = {}
    def get(self, path):
        def _wrap(fn):
            self.routes[("GET", path)] = fn
            return fn
        return _wrap
    def post(self, path):
        def _wrap(fn):
            self.routes[("POST", path)] = fn
            return fn
        return _wrap
    def delete(self, path):
        def _wrap(fn):
            self.routes[("DELETE", path)] = fn
            return fn
        return _wrap


async def _fake_admin():
    return {"email": "admin@masci.com"}


def _register(db):
    r = _Router()
    register_dr_v3_flag_routes(r, db, require_admin=_fake_admin)
    return r


# ── Backend behaviors ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_endpoints_registered_only_when_dep_supplied():
    db = _DB()
    r_without = _Router()
    register_dr_v3_flag_routes(r_without, db)  # no require_admin dep
    # Only the public read endpoint is registered.
    paths = {p for _, p in r_without.routes}
    assert "/feature-flags/dr-v3" in paths
    assert "/admin/dr-v3-flag" not in paths

    r_with = _register(db)
    paths_with = {p for _, p in r_with.routes}
    for expected in [
        "/feature-flags/dr-v3",
        "/admin/dr-v3-flag",
        "/admin/dr-v3-flag/pilot-user",
        "/admin/dr-v3-flag/pilot-project",
        "/admin/dr-v3-flag/tenant-default",
    ]:
        assert expected in paths_with, f"missing {expected}"


@pytest.mark.asyncio
async def test_add_pilot_user_is_idempotent_and_lowercases():
    db = _DB()
    r = _register(db)
    add = r.routes[("POST", "/admin/dr-v3-flag/pilot-user")]
    actor = await _fake_admin()
    out1 = await add({"email": "Chris@MASCI.com"}, actor=actor)
    out2 = await add({"email": "chris@masci.com"}, actor=actor)
    assert out1["ok"] and out1["email"] == "chris@masci.com"
    assert out2["ok"]  # idempotent
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert doc["pilot_users"] == ["chris@masci.com"]


@pytest.mark.asyncio
async def test_adding_pilot_user_removes_from_denied():
    db = _DB()
    # Seed with the user already denied.
    await db[COLL_UI_FLAGS].update_one(
        {"_id": FLAG_KEY},
        {"$setOnInsert": {"_id": FLAG_KEY, "pilot_users": [], "denied_users": ["chris@masci.com"]}},
        upsert=True,
    )
    r = _register(db)
    add = r.routes[("POST", "/admin/dr-v3-flag/pilot-user")]
    await add({"email": "chris@masci.com"}, actor=await _fake_admin())
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert "chris@masci.com" in doc["pilot_users"]
    assert "chris@masci.com" not in (doc.get("denied_users") or [])


@pytest.mark.asyncio
async def test_remove_pilot_user_is_idempotent():
    db = _DB()
    r = _register(db)
    add = r.routes[("POST", "/admin/dr-v3-flag/pilot-user")]
    remove = r.routes[("DELETE", "/admin/dr-v3-flag/pilot-user")]
    await add({"email": "chris@masci.com"}, actor=await _fake_admin())
    await remove("chris@masci.com", actor=await _fake_admin())
    await remove("chris@masci.com", actor=await _fake_admin())  # idempotent
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert doc["pilot_users"] == []


@pytest.mark.asyncio
async def test_add_and_remove_pilot_project_is_idempotent():
    db = _DB()
    r = _register(db)
    add = r.routes[("POST", "/admin/dr-v3-flag/pilot-project")]
    remove = r.routes[("DELETE", "/admin/dr-v3-flag/pilot-project")]
    await add({"project_number": "25-21"}, actor=await _fake_admin())
    await add({"project_number": "25-21"}, actor=await _fake_admin())
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert doc["pilot_projects"] == ["25-21"]
    await remove("25-21", actor=await _fake_admin())
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert doc["pilot_projects"] == []


@pytest.mark.asyncio
async def test_tenant_default_flip_persists():
    db = _DB()
    r = _register(db)
    flip = r.routes[("POST", "/admin/dr-v3-flag/tenant-default")]
    await flip({"enabled": True}, actor=await _fake_admin())
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert doc["tenant_default"] is True
    await flip({"enabled": False}, actor=await _fake_admin())
    doc = await db[COLL_UI_FLAGS].find_one({"_id": FLAG_KEY})
    assert doc["tenant_default"] is False


@pytest.mark.asyncio
async def test_empty_email_or_project_returns_ok_false():
    db = _DB()
    r = _register(db)
    add_u = r.routes[("POST", "/admin/dr-v3-flag/pilot-user")]
    add_p = r.routes[("POST", "/admin/dr-v3-flag/pilot-project")]
    out_u = await add_u({"email": ""}, actor=await _fake_admin())
    out_p = await add_p({"project_number": ""}, actor=await _fake_admin())
    assert out_u["ok"] is False and out_u["reason"] == "email_required"
    assert out_p["ok"] is False and out_p["reason"] == "project_number_required"


# ── Frontend wiring locks (static file inspection) ──────────────

V3_SHELL = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")
LEGACY_ROUTER = Path("/app/frontend/src/pages/DailyReportRouter.jsx")
LEGACY_V1 = Path("/app/frontend/src/pages/NewDailyReport.jsx")
LEGACY_FLAG = Path("/app/frontend/src/lib/dailyReportV3Flag.js")


def _src(p): return p.read_text(encoding="utf-8")


def test_v3_wires_useformdraft():
    src = _src(V3_SHELL)
    assert "useFormDraft" in src, "V3 must compose the shared useFormDraft hook"
    assert "DraftRestorePrompt" in src, "V3 must show DraftRestorePrompt when a pending draft exists"
    assert "DraftStatusPill" in src, "V3 must show DraftStatusPill in the header"


def test_v3_wires_offline_queue_and_idempotency():
    src = _src(V3_SHELL)
    assert "enqueueUpload" in src, "V3 must fall through to enqueueUpload when offline"
    assert "useOnlineStatus" in src, "V3 must react to online/offline"
    assert "mintIdempotencyKey" in src, "V3 must mint idempotency keys"
    assert "persistIdempotencyKey" in src, "V3 must persist idempotency keys across reload"
    assert "loadIdempotencyKey" in src, "V3 must load the persisted idempotency key on mount"
    assert '"Idempotency-Key"' in src, "V3 online submit must send Idempotency-Key header"


def test_v3_shares_form_key_with_v1():
    src = _src(V3_SHELL)
    assert "DAILY_REPORT_FORM_BASE" in src, \
        "V3 must keep the shared Daily Report draft base key"
    assert "useFormDraft(DAILY_REPORT_FORM_BASE" in src, \
        "V3 must use the shared Daily Report draft base key in the draft hook"


def test_v3_wires_crew_setup_memory_and_restore_yesterday():
    src = _src(V3_SHELL)
    for sym in [
        "extractSetupSnapshot",
        "saveCrewSetup",
        "loadCrewSetup",
        "applySetupSnapshotToData",
        "isProjectChange",
    ]:
        assert sym in src, f"V3 must wire {sym}"
    assert "dr-v3-crew-setup-offer" in src, "restore-yesterday prompt must be present"
    assert "dr-v3-crew-setup-use" in src
    assert "dr-v3-crew-setup-dismiss" in src


def test_v3_never_restores_dangerous_fields_from_yesterday():
    """applySetupSnapshotToData only restores masci_crews + equipment
    (verified by opening the crewMemory implementation) — locks this."""
    memory_src = Path("/app/frontend/src/lib/crewMemory.js").read_text()
    # Ensure the snapshot extractor doesn't grab safety/production/photos.
    for banned in ["safety_incidents", "photos:", "production:", "ai_accepted_summary"]:
        # `extractSetupSnapshot` is the only path used by V3; ensure it
        # never includes these keys in the setup snapshot payload.
        # The current implementation only extracts masci_crews +
        # equipment + subs skeleton; this lock prevents accidental
        # widening of the snapshot in future edits.
        assert banned not in memory_src, \
            f"crewMemory.js must never surface {banned} in setup snapshots"


def test_legacy_flag_and_shell_switching_removed():
    assert not LEGACY_FLAG.exists()
    assert not LEGACY_ROUTER.exists()
    assert not LEGACY_V1.exists()


def test_v3_no_longer_depends_on_runtime_flag_endpoint():
    src = _src(V3_SHELL)
    assert "/feature-flags/dr-v3" not in src
    assert "useDailyReportV3Flag" not in src


def test_v3_shows_offline_chip():
    src = _src(V3_SHELL)
    assert "dr-v3-offline-chip" in src, "V3 must show an offline chip when navigator is offline"
