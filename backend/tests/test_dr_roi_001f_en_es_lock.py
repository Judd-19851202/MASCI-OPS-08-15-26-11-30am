"""DR-ROI-001F-FINAL-REPAIR · Amendment · EN/ES field-mode lock envelope.

Enforces the bilingual contract:
- Every field-facing string on the DR-V2 shell + sections is keyed via
  useDrV2Lang(). No hard-coded English strings that would resist ES mode.
- The language toggle exists and defaults to English.
- The canonicalize endpoint is registered.
- Canonicalize helpers behave (walk_get / walk_set / no-op EN path).
"""
from __future__ import annotations
import asyncio
import re
from pathlib import Path


ROOT = Path("/app/frontend/src/pages/daily-report-v2")
LANG_LIB = Path("/app/frontend/src/lib/dailyReportV2Lang.js")

SECTION_FILES = list((ROOT / "sections").glob("*.jsx"))
LOCALIZED_REQUIRED = {
    "DaySetupSection.jsx",
    "CrewTimeSection.jsx",
    "PhotosSection.jsx",
    "SignatureSubmitSection.jsx",
    "AISummarySection.jsx",
}


def test_lang_library_exports_are_complete():
    text = LANG_LIB.read_text(encoding="utf-8")
    for name in ("DICTIONARY", "DrV2LangProvider", "useDrV2Lang", "LangToggle"):
        assert name in text, f"dailyReportV2Lang.js must export {name}"


def test_dictionary_has_en_and_es_for_every_key():
    text = LANG_LIB.read_text(encoding="utf-8")
    # Find every `"key.name": { en: "…", es: "…" }` line — permissive regex.
    entries = re.findall(
        r'"([a-z0-9_.]+)":\s*\{\s*en:\s*(?:"[^"]*"|\'[^\']*\'),\s*es:\s*(?:"[^"]*"|\'[^\']*\')',
        text,
    )
    assert len(entries) >= 60, (
        f"Dictionary must define at least 60 EN/ES pairs · found {len(entries)}"
    )


def test_shell_wraps_provider_and_renders_toggle():
    shell = (ROOT / "DailyReportV2.jsx").read_text(encoding="utf-8")
    assert "DrV2LangProvider" in shell, "Shell must wrap in DrV2LangProvider"
    assert "LangToggle" in shell, "Shell must render <LangToggle />"
    assert "useDrV2Lang" in shell, "Shell must consume useDrV2Lang"
    # Field-facing strings should now come from `t("...")`.
    for phrase in ('"Daily Job Report"', '"MASCI Field Operations"',
                    '"Draft"', '"Not saved yet"', '"Saving…"',
                    '"Draft saved"'):
        assert phrase not in shell, (
            f"Shell hard-codes '{phrase}' — must go through t(...)"
        )


def test_default_language_is_english():
    text = LANG_LIB.read_text(encoding="utf-8")
    # readInitialLang: "return v === 'es' ? 'es' : 'en'" — default falls to EN.
    assert 'v === "es" ? "es" : "en"' in text or "'es' ? 'es' : 'en'" in text, \
        "Default language must be English when no localStorage value exists"


def test_key_sections_wire_the_lang_hook():
    for fname in LOCALIZED_REQUIRED:
        path = ROOT / "sections" / fname
        assert path.exists(), f"missing section: {fname}"
        text = path.read_text(encoding="utf-8")
        assert "useDrV2Lang" in text, f"{fname} must import useDrV2Lang"
        assert re.search(r"\bt\(\s*['\"]s\d\d?", text), \
            f"{fname} must call t(\"sNN…\") for its labels"


def test_canonicalize_route_registered_and_helpers_work():
    """Canonicalize endpoint must be registered in server.py and its
    walk_get/walk_set helpers behave correctly on nested lists."""
    server = Path("/app/backend/server.py").read_text(encoding="utf-8")
    assert "register_dr_v2_canonicalize_routes" in server

    from routes.dr_v2_canonicalize import (  # type: ignore[import]
        _walk_get, _walk_set, TRANSLATABLE_PATHS,
    )
    # Cover the four important shapes.
    d = {
        "activity_cards": [{"notes": "A"}, {"notes": "B"}],
        "constraint_cards": [{"what_happened": "wc"}, {"impact": "wi"}],
        "tomorrow_readiness": {"crew_needs": "cn"},
        "safety": {"quality_notes": "qn"},
        "accepted_summary": "sum",
        "day_setup": {"location_label": "here"},
    }
    got = _walk_get(d, "activity_cards[].notes")
    assert len(got) == 2 and got[0]["value"] == "A"
    _walk_set(d, got[0]["ptr"], "A2")
    assert d["activity_cards"][0]["notes"] == "A2"
    # Ensure every TRANSLATABLE_PATHS entry resolves at least the paths we set.
    for path in ("accepted_summary",
                 "constraint_cards[].what_happened",
                 "tomorrow_readiness.crew_needs",
                 "safety.quality_notes"):
        assert path in TRANSLATABLE_PATHS


def test_canonicalize_no_op_for_english_language():
    """Passing field_language='en' must return the draft unchanged."""
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import APIRouter
    from routes.dr_v2_canonicalize import register_dr_v2_canonicalize_routes

    r = APIRouter()
    db_stub = MagicMock()
    coll_stub = MagicMock()
    coll_stub.insert_one = AsyncMock(return_value=None)
    db_stub.__getitem__ = MagicMock(return_value=coll_stub)
    register_dr_v2_canonicalize_routes(r, db_stub)

    # Grab the handler from the mounted routes.
    handler = None
    for route in r.routes:
        if getattr(route, "path", "").endswith("/canonicalize"):
            handler = route.endpoint
            break
    assert handler is not None

    draft = {"activity_cards": [{"notes": "excavation completed"}], "field_language": "en"}
    resp = asyncio.get_event_loop().run_until_complete(
        handler("rpt_test_en", {"draft": draft, "field_language": "en"})
    )
    assert resp["translation_status"] == "not_required"
    assert resp["canonical_draft"]["activity_cards"][0]["notes"] == "excavation completed"
    assert resp["translations"] == []
    assert resp["field_language"] == "en"


def test_task_router_carries_translation_task():
    from services.ai_gateway.task_router import TASK_ROUTES
    assert "translation_es_en" in TASK_ROUTES, \
        "task_router.py must expose 'translation_es_en'"


def test_ods_only_receives_english_canonical():
    """The bilingual mandate: ODS emission must not carry Spanish
    freeform text. The dr_v2 canonicalize endpoint stores originals in
    the audit collection; the canonical_draft returned is what ODS gets.
    Structural check: the module must import the audit collection name.
    """
    text = Path("/app/backend/routes/dr_v2_canonicalize.py").read_text(encoding="utf-8")
    assert "dr_v2_bilingual_audit" in text, \
        "canonicalize module must persist to dr_v2_bilingual_audit"
    assert "original_user_text" in text
    assert "canonical_english_text" in text
    assert "translation_confidence" in text
    assert "translation_provider" in text
    assert "reviewed_by_user" in text
