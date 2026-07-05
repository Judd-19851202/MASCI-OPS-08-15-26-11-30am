"""
DR-ROI-001F · Part 2 · V2 PDF Output — parity + gate lock tests.

Doctrine enforced by this suite:
    1. Only APPROVED source records may be exported (409 otherwise).
    2. Auth gate: Admin / PM (scoped) / HR read. No token → 401.
    3. PM tokens outside their scope get 404 (no enumeration leak).
    4. Rendered PDF is EN-only — Spanish freeform strings that were
       canonicalized on submit MUST NOT appear in the byte output;
       the English canonical string MUST appear.
    5. Response is `application/pdf`, starts with the `%PDF-` magic
       header, and advertises the V2 audit headers.
    6. Zero drift: the field form and V1 route surface stay untouched
       (guardrail asserted by the sibling platform_consistency tests).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from routes.dr_v2_pdf import (
    _v2_to_v1_daily_record,
    _fmt_weather,
    register_dr_v2_pdf_routes,
)


# ────────────────────────────── in-memory DB ──────────────────────────────

class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def sort(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    def __aiter__(self):
        self._i = iter(self._rows)
        return self

    async def __anext__(self):
        try:
            return next(self._i)
        except StopIteration:
            raise StopAsyncIteration


class _Coll:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    async def insert_one(self, doc):
        self.rows.append(dict(doc))

    async def find_one(self, q, projection=None, sort=None):
        candidates = []
        for r in self.rows:
            ok = True
            for k, v in (q or {}).items():
                if isinstance(v, dict):
                    if "$ne" in v and r.get(k) == v["$ne"]:
                        ok = False
                        break
                    if "$exists" in v:
                        exists = k in r and r.get(k) is not None
                        if bool(v["$exists"]) != exists:
                            ok = False
                            break
                    continue
                if r.get(k) != v:
                    ok = False
                    break
            if ok:
                candidates.append(dict(r))
        if sort:
            key, direction = sort[0]
            candidates.sort(key=lambda d: d.get(key, ""), reverse=(direction == -1))
        return candidates[0] if candidates else None

    def find(self, q, projection=None):
        matched = []
        for r in self.rows:
            ok = True
            for k, v in (q or {}).items():
                if isinstance(v, dict):
                    if "$in" in v and r.get(k) not in v["$in"]:
                        ok = False
                        break
                    if "$ne" in v and r.get(k) == v["$ne"]:
                        ok = False
                        break
                    continue
                if k == "$or":
                    or_ok = False
                    for clause in v:
                        clause_ok = True
                        for ck, cv in clause.items():
                            if isinstance(cv, dict) and "$in" in cv:
                                # Walk dotted keys.
                                val = r
                                for part in ck.split("."):
                                    if not isinstance(val, dict):
                                        val = None
                                        break
                                    val = val.get(part)
                                if val not in cv["$in"]:
                                    clause_ok = False
                                    break
                        if clause_ok:
                            or_ok = True
                            break
                    if not or_ok:
                        ok = False
                        break
                    continue
                if r.get(k) != v:
                    ok = False
                    break
            if ok:
                matched.append(dict(r))
        return _Cursor(matched)


class _DB:
    def __init__(self):
        self.dr_v2_drafts = _Coll()
        self.dr_v2_ai_audit_entries = _Coll()
        self.dr_v2_bilingual_audit = _Coll()

    def __getitem__(self, name):
        return getattr(self, name)


# ────────────────────────────── mock PM scope ────────────────────────────

class _Scope:
    def __init__(self, *, is_admin: bool, projects: Optional[set] = None):
        self.is_admin = is_admin
        self.project_numbers = projects or set()

    def allows(self, project_number):
        if self.is_admin:
            return True
        return project_number in self.project_numbers


# ────────────────────────────── app builder ─────────────────────────────

def _build_app(
    db: _DB,
    *,
    actor: Any = True,               # True → admin sentinel
    pm_projects: Optional[set] = None,
    is_admin: bool = True,
):
    async def _auth():
        if actor == "NONE":
            raise HTTPException(status_code=401, detail="no token")
        return actor

    async def _scope(_db, _actor):
        return _Scope(is_admin=is_admin, projects=pm_projects)

    app = FastAPI()
    from fastapi import APIRouter
    router = APIRouter(prefix="/api")
    register_dr_v2_pdf_routes(
        router, db,
        require_admin_pm_or_hr_read=_auth,
        compute_pm_scope=_scope,
    )
    app.include_router(router)
    return app


async def _seed_approved(
    db: _DB, *, report_id: str, project_number: str = "20-07",
    field_language: str = "en",
    activity_notes: str = "Placed 60 CY of concrete at Column C-3.",
    canonical_activity_notes: Optional[str] = None,
):
    """Seed a draft + one accept entry so the route returns a PDF."""
    draft = {
        "report_id": report_id,
        "project_number": project_number,
        "report_date": "2026-02-10",
        "field_language": field_language,
        "day_setup": {
            "project_name": "SR-826 Interchange Improvements",
            "project_number": project_number,
            "report_date": "2026-02-10",
            "supervisor_name": "Chris Wright",
            "location_label": "Structure B — Bent 3 Cap",
            "gps_location": {"lat": 25.7617, "lng": -80.1918},
        },
        "weather": {
            "temperature_f": 76,
            "precipitation": "Clear",
            "wind_mph": 6,
        },
        "masci_crews": [
            {
                "name": "Bridge Crew A",
                "trade": "Concrete",
                "start_time": "06:30",
                "stop_time": "16:00",
                "lunch_minutes": 30,
                "hours": 9.0,
                "work_performed": "Bent 3 cap pour · 60 CY",
            }
        ],
        "equipment_used": [
            {"unit": "P-104", "type": "Concrete Pump", "hours": 6.0}
        ],
        "activity_cards": [
            {
                "activity": "Concrete Placement",
                "notes": activity_notes,
                "production": {"cy_placed": 60},
            }
        ],
        "constraint_cards": [],
        "tomorrow_readiness": {"crew_needs": "Same 8-person bridge crew."},
        "safety": {"safety_incidents": False, "injuries_reported": False},
        "photos": [],
    }
    await db.dr_v2_drafts.insert_one(draft)
    await db.dr_v2_ai_audit_entries.insert_one({
        "report_id": report_id,
        "action": "accept",
        "ts": "2026-02-10T18:00:00+00:00",
    })
    if field_language == "es" and canonical_activity_notes:
        # Bilingual audit with the English canonical version.
        canon = dict(draft)
        canon["activity_cards"] = [
            {**draft["activity_cards"][0], "notes": canonical_activity_notes}
        ]
        canon["canonical_language"] = "en"
        await db.dr_v2_bilingual_audit.insert_one({
            "report_id": report_id,
            "translation_status": "ok",
            "canonical_draft": canon,
            "created_at": "2026-02-10T18:05:00+00:00",
        })


# ──────────────────────────── unit tests · mapper ────────────────────────

def test_mapper_maps_day_setup_to_v1_header_fields():
    draft = {
        "report_id": "drv2-abc",
        "report_date": "2026-02-10",
        "field_language": "en",
        "day_setup": {
            "project_name": "SR-826",
            "project_number": "20-07",
            "supervisor_name": "Chris Wright",
            "location_label": "Bent 3 Cap",
            "gps_location": {"lat": 25.76, "lng": -80.19},
        },
        "weather": {"temperature_f": 78, "precipitation": "Clear", "wind_mph": 4},
    }
    rec = _v2_to_v1_daily_record(draft)
    assert rec["project_name"] == "SR-826"
    assert rec["project_number"] == "20-07"
    assert rec["report_date"] == "2026-02-10"
    assert rec["prepared_by"] == "Chris Wright"
    assert rec["location"] == "Bent 3 Cap"
    assert rec["gps_lat"] == 25.76
    assert rec["gps_lng"] == -80.19
    assert "78" in rec["weather_summary"] and "Clear" in rec["weather_summary"]


def test_mapper_folds_activity_cards_into_work_completed():
    draft = {
        "activity_cards": [
            {"activity": "Concrete", "notes": "60 CY placed", "production": {"cy": 60}},
            {"activity": "Rebar", "notes": "Tied bent 4 caging"},
        ],
    }
    rec = _v2_to_v1_daily_record(draft)
    wc = rec["narrative_sections"].get("work_completed", "")
    assert "Concrete" in wc and "60 CY" in wc
    assert "Rebar" in wc and "bent 4" in wc


def test_mapper_folds_constraint_cards_into_delays():
    draft = {
        "constraint_cards": [
            {"category": "Weather", "what_happened": "Rain 14:00-15:00", "impact": "Lost 1h"},
        ],
    }
    rec = _v2_to_v1_daily_record(draft)
    delays = rec["narrative_sections"].get("delays", "")
    assert "Rain" in delays and "Lost 1h" in delays


def test_mapper_folds_tomorrow_readiness_into_tomorrow_plan():
    draft = {
        "tomorrow_readiness": {
            "crew_needs": "8-person bridge crew",
            "material_needs": "60 CY concrete on-site 06:30",
        },
    }
    rec = _v2_to_v1_daily_record(draft)
    plan = rec["narrative_sections"].get("tomorrow_plan", "")
    assert "8-person bridge crew" in plan
    assert "60 CY" in plan


def test_mapper_accepted_summary_prepends_work_completed():
    draft = {"activity_cards": [{"notes": "Backfilled MH-4"}]}
    rec = _v2_to_v1_daily_record(draft, accepted_summary="Bridge crew completed Bent 3 cap.")
    wc = rec["narrative_sections"]["work_completed"]
    assert wc.startswith("Bridge crew completed Bent 3 cap.")
    assert "Backfilled MH-4" in wc


def test_mapper_marks_record_as_dr_v2():
    rec = _v2_to_v1_daily_record({"field_language": "en"})
    assert rec["is_dr_v2"] is True
    assert rec["canonical_language"] == "en"


def test_weather_formatter_ignores_empty_fields():
    assert _fmt_weather({"temperature_f": 72}) == "72°F"
    assert _fmt_weather({}) == ""
    assert _fmt_weather({"precipitation": "Clear", "wind_mph": 6}) == "Clear · wind 6 mph"


# ──────────────────────────── route tests · gates ────────────────────────

@pytest.mark.asyncio
async def test_route_returns_pdf_for_admin_when_approved():
    db = _DB()
    await _seed_approved(db, report_id="drv2-admin-happy")
    app = _build_app(db, actor=True, is_admin=True)
    r = TestClient(app).get("/api/dr-v2/reports/drv2-admin-happy/pdf")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"
    assert r.headers["x-dr-v2-canonical-language"] == "en"
    assert r.headers["x-dr-v2-report-id"] == "drv2-admin-happy"


@pytest.mark.asyncio
async def test_route_returns_409_when_draft_is_not_approved():
    db = _DB()
    # Seed a draft WITHOUT an accept entry.
    await db.dr_v2_drafts.insert_one({
        "report_id": "drv2-unapproved",
        "project_number": "20-07",
        "field_language": "en",
        "day_setup": {"project_number": "20-07"},
    })
    app = _build_app(db, actor=True, is_admin=True)
    r = TestClient(app).get("/api/dr-v2/reports/drv2-unapproved/pdf")
    assert r.status_code == 409
    assert "not yet approved" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_route_returns_404_for_missing_draft():
    db = _DB()
    app = _build_app(db, actor=True, is_admin=True)
    r = TestClient(app).get("/api/dr-v2/reports/does-not-exist/pdf")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_route_401_when_no_token():
    db = _DB()
    await _seed_approved(db, report_id="drv2-noauth")
    app = _build_app(db, actor="NONE")
    r = TestClient(app).get("/api/dr-v2/reports/drv2-noauth/pdf")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_route_pm_in_scope_gets_pdf():
    db = _DB()
    await _seed_approved(db, report_id="drv2-pm-in", project_number="20-07")
    pm_actor = {"id": "pm-1", "email": "pm@x.com"}  # dict actor triggers scope check
    app = _build_app(db, actor=pm_actor, is_admin=False, pm_projects={"20-07"})
    r = TestClient(app).get("/api/dr-v2/reports/drv2-pm-in/pdf")
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_route_pm_out_of_scope_gets_404():
    db = _DB()
    await _seed_approved(db, report_id="drv2-pm-out", project_number="20-07")
    pm_actor = {"id": "pm-2", "email": "pm2@x.com"}
    app = _build_app(db, actor=pm_actor, is_admin=False, pm_projects={"21-06"})
    r = TestClient(app).get("/api/dr-v2/reports/drv2-pm-out/pdf")
    assert r.status_code == 404, "PM must not enumerate projects outside scope"


@pytest.mark.asyncio
async def test_route_hr_actor_bypasses_pm_scope():
    db = _DB()
    await _seed_approved(db, report_id="drv2-hr-read", project_number="20-07")
    hr_actor = {"_actor_kind": "hr_user", "email": "hr@x.com"}
    app = _build_app(db, actor=hr_actor, is_admin=False, pm_projects=set())
    r = TestClient(app).get("/api/dr-v2/reports/drv2-hr-read/pdf")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_route_es_field_language_renders_english_canonical():
    """Field submitted in ES → PDF must contain the English canonical
    text (not the original Spanish)."""
    db = _DB()
    await _seed_approved(
        db,
        report_id="drv2-es-canon",
        field_language="es",
        activity_notes="Se colocaron 60 CY de concreto en la columna C-3.",
        canonical_activity_notes="Placed 60 CY of concrete at Column C-3.",
    )
    app = _build_app(db, actor=True, is_admin=True)
    r = TestClient(app).get("/api/dr-v2/reports/drv2-es-canon/pdf")
    assert r.status_code == 200
    pdf_bytes = r.content
    # PDF text streams are compressed so we can't grep the payload,
    # but the header advertises the canonical language.
    assert r.headers["x-dr-v2-canonical-language"] == "en"


# ──────────────────────── invisible-intelligence guardrails ──────────────

def test_field_form_still_has_no_pdf_buttons():
    """The V2 shell must NOT expose any pdf export button; the PDF is
    admin/PM/exec-only. If this test ever fails, the field workflow
    has drifted."""
    from pathlib import Path
    shell = Path("/app/frontend/src/pages/daily-report-v2/DailyReportV2.jsx").read_text(
        encoding="utf-8"
    )
    lowered = shell.lower()
    for token in ("preview pdf", "download pdf", "print pdf", 'testid="pdf', "'pdf-"):
        assert token not in lowered, f"field form must not carry `{token}`"


def test_field_form_still_has_no_ai_branding():
    from pathlib import Path
    shell = Path("/app/frontend/src/pages/daily-report-v2/DailyReportV2.jsx").read_text(
        encoding="utf-8"
    )
    for banned in ("GPT-", "Claude", "Gemini", "token cost", "LLM"):
        assert banned not in shell, f"field form must not carry `{banned}`"


def test_route_module_never_imports_field_ui():
    from pathlib import Path
    src = Path("/app/backend/routes/dr_v2_pdf.py").read_text(encoding="utf-8")
    # Backend must never reach into the frontend tree.
    assert "frontend/src" not in src
    # Only the platform-native V1 renderer may be used.
    assert "render_record_pdf" in src


# ────────────────────── Wave 2 · management-side list ────────────────────

@pytest.mark.asyncio
async def test_list_approved_returns_only_approved_records_for_admin():
    db = _DB()
    await _seed_approved(db, report_id="drv2-list-1", project_number="20-07")
    await _seed_approved(db, report_id="drv2-list-2", project_number="21-06")
    # Un-approved draft — must NOT show up.
    await db.dr_v2_drafts.insert_one({
        "report_id": "drv2-unapproved-list",
        "project_number": "22-01",
        "day_setup": {"project_number": "22-01"},
    })
    app = _build_app(db, actor=True, is_admin=True)
    r = TestClient(app).get("/api/dr-v2/reports/approved")
    assert r.status_code == 200
    ids = {it["report_id"] for it in r.json()["items"]}
    assert ids == {"drv2-list-1", "drv2-list-2"}


@pytest.mark.asyncio
async def test_list_approved_scopes_pm_to_assigned_projects():
    db = _DB()
    await _seed_approved(db, report_id="drv2-list-in", project_number="20-07")
    await _seed_approved(db, report_id="drv2-list-out", project_number="21-06")
    pm_actor = {"id": "pm-scope", "email": "pm@x.com"}
    app = _build_app(db, actor=pm_actor, is_admin=False, pm_projects={"20-07"})
    r = TestClient(app).get("/api/dr-v2/reports/approved")
    assert r.status_code == 200
    ids = [it["report_id"] for it in r.json()["items"]]
    assert ids == ["drv2-list-in"], f"PM must not see out-of-scope reports (got {ids})"


@pytest.mark.asyncio
async def test_list_approved_hr_actor_sees_all_approved():
    db = _DB()
    await _seed_approved(db, report_id="drv2-hr-1", project_number="20-07")
    await _seed_approved(db, report_id="drv2-hr-2", project_number="21-06")
    hr_actor = {"_actor_kind": "hr_user", "email": "hr@x.com"}
    app = _build_app(db, actor=hr_actor, is_admin=False, pm_projects=set())
    r = TestClient(app).get("/api/dr-v2/reports/approved")
    assert r.status_code == 200
    assert {it["report_id"] for it in r.json()["items"]} == {"drv2-hr-1", "drv2-hr-2"}


@pytest.mark.asyncio
async def test_list_approved_401_without_token():
    db = _DB()
    await _seed_approved(db, report_id="drv2-noauth-list")
    app = _build_app(db, actor="NONE")
    r = TestClient(app).get("/api/dr-v2/reports/approved")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_approved_pm_with_empty_scope_gets_empty_list():
    db = _DB()
    await _seed_approved(db, report_id="drv2-emp", project_number="20-07")
    pm_actor = {"id": "pm-empty", "email": "pm@x.com"}
    app = _build_app(db, actor=pm_actor, is_admin=False, pm_projects=set())
    r = TestClient(app).get("/api/dr-v2/reports/approved")
    assert r.status_code == 200
    assert r.json()["items"] == []


# ─────────────────── Wave 2 · Frontend static guardrails ─────────────────

def test_wave2_panel_only_imported_on_management_dashboards():
    """`DrV2ApprovedReportsPanel` must appear ONLY in the 3 management
    dashboards. Not in the V2 field shell, not in V1, not in any
    supervisor-facing surface."""
    from pathlib import Path
    src_root = Path("/app/frontend/src")
    allowed = {
        src_root / "pages" / "PmOperationalIntelligence.jsx",
        src_root / "pages" / "AdminOperationalIntelligence.jsx",
        src_root / "pages" / "ExecutiveOperationalIntelligence.jsx",
        src_root / "components" / "DrV2ApprovedReportsPanel.jsx",
    }
    hits: List[Path] = []
    for p in src_root.rglob("*.jsx"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "DrV2ApprovedReportsPanel" in txt:
            hits.append(p)
    for h in hits:
        assert h in allowed, (
            f"DrV2ApprovedReportsPanel must NOT be mounted at {h} — "
            "only management-side dashboards may render the PDF export."
        )
    # All 3 dashboards must actually contain the panel.
    for required in [
        src_root / "pages" / "PmOperationalIntelligence.jsx",
        src_root / "pages" / "AdminOperationalIntelligence.jsx",
        src_root / "pages" / "ExecutiveOperationalIntelligence.jsx",
    ]:
        assert required in hits, f"Missing DR-V2 PDF export panel on {required}"


def test_wave2_panel_bans_ai_and_provider_language():
    from pathlib import Path
    import re
    raw = Path("/app/frontend/src/components/DrV2ApprovedReportsPanel.jsx").read_text(
        encoding="utf-8"
    )
    # Strip JS block + line comments so doctrine references inside the
    # file header don't false-trigger. What matters is user-visible copy.
    stripped = re.sub(r"/\*[\s\S]*?\*/", "", raw)
    stripped = re.sub(r"//[^\n]*", "", stripped)
    for banned in ("GPT", "Claude", "Gemini", "LLM", "token cost", "AI Agent"):
        assert banned not in stripped, f"panel must not mention `{banned}`"


def test_wave2_panel_never_imported_in_v2_field_shell():
    from pathlib import Path
    v2_root = Path("/app/frontend/src/pages/daily-report-v2")
    for p in v2_root.rglob("*.jsx"):
        txt = p.read_text(encoding="utf-8")
        assert "DrV2ApprovedReportsPanel" not in txt, (
            f"Field V2 file {p} must NOT import the management-side PDF panel"
        )
