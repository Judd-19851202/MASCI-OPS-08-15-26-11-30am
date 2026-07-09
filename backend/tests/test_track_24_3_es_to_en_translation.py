"""TRACK 24.3 · Backend tests for the ES → EN canonical translation
pipeline used by Daily Report V3 on submit.

These tests exercise both the pure Python service (`translate_es_to_en_bulk`)
and the FastAPI route (`POST /api/translate/dr-v3-freetext`). External LLM
calls are stubbed via monkeypatching `_call_openai` / `_call_anthropic` so
the tests are deterministic and offline.
"""
from __future__ import annotations

import asyncio
import os
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("EMERGENT_LLM_KEY", "test-key")

from services.translation import service as tr_service  # noqa: E402
from services.translation.service import translate_es_to_en_bulk, TranslationResult  # noqa: E402


class _MemDb:
    """Minimal in-memory Mongo stand-in used only by the audit writer."""

    def __init__(self):
        self.rows = []

    def __getitem__(self, name):
        parent = self

        class _Coll:
            async def insert_one(_self, doc):
                parent.rows.append({"_coll": name, **doc})
                return None
        return _Coll()


def _fake_openai(response_json: str):
    async def _fn(api_key, payload_text, preserve_list):  # noqa: ARG001
        return response_json
    return _fn


@pytest.mark.asyncio
async def test_empty_payload_short_circuits():
    db = _MemDb()
    r = await translate_es_to_en_bulk(db, {}, actor="unit", dr_id="dr-empty")
    assert r.ok is True
    assert r.translations == {}
    assert r.provider is None
    assert any(row["_coll"] == "translation_audit" and row["ok"] is True for row in db.rows)


@pytest.mark.asyncio
async def test_success_translates_and_preserves(monkeypatch):
    db = _MemDb()
    monkeypatch.setattr(
        tr_service, "_call_openai",
        _fake_openai('{"general_notes":"Crew working at Sta 12+50","excavation.soil_notes":"Type B soil"}'),
    )
    fields = {"general_notes": "Cuadrilla trabajando en Sta 12+50",
              "excavation.soil_notes": "Suelo tipo B"}
    r = await translate_es_to_en_bulk(
        db, fields, preserve_tokens={"Sta 12+50"}, actor="unit", dr_id="dr-ok",
    )
    assert r.ok is True, r.error
    assert r.translations["general_notes"] == "Crew working at Sta 12+50"
    assert r.translations["excavation.soil_notes"] == "Type B soil"
    assert r.provider == "openai"
    assert r.model == "gpt-5.2"


@pytest.mark.asyncio
async def test_fail_closed_on_invalid_json(monkeypatch):
    db = _MemDb()
    monkeypatch.setattr(tr_service, "_call_openai",
                        _fake_openai("this is not JSON at all"))
    monkeypatch.setattr(tr_service, "_call_anthropic",
                        _fake_openai("also not JSON"))
    r = await translate_es_to_en_bulk(db, {"a": "hola"})
    assert r.ok is False
    assert r.error in {"translation_no_json", "translation_invalid_json"}


@pytest.mark.asyncio
async def test_fail_closed_on_key_mismatch(monkeypatch):
    db = _MemDb()
    monkeypatch.setattr(tr_service, "_call_openai",
                        _fake_openai('{"different_key":"hello"}'))
    monkeypatch.setattr(tr_service, "_call_anthropic",
                        _fake_openai('{"different_key":"hello"}'))
    r = await translate_es_to_en_bulk(db, {"a": "hola"})
    assert r.ok is False
    assert r.error == "translation_key_mismatch"


@pytest.mark.asyncio
async def test_fail_closed_on_spanish_leak(monkeypatch):
    db = _MemDb()
    monkeypatch.setattr(tr_service, "_call_openai",
                        _fake_openai('{"a":"cañería with accents"}'))
    monkeypatch.setattr(tr_service, "_call_anthropic",
                        _fake_openai('{"a":"cañería"}'))
    r = await translate_es_to_en_bulk(db, {"a": "cañería rota"})
    assert r.ok is False
    assert r.error == "translation_spanish_leak"


@pytest.mark.asyncio
async def test_fail_closed_on_preserve_token_lost(monkeypatch):
    db = _MemDb()
    # Preserve-token "24-12" is in input but the output drops it.
    monkeypatch.setattr(
        tr_service, "_call_openai",
        _fake_openai('{"general_notes":"Truck working at station"}'),
    )
    monkeypatch.setattr(
        tr_service, "_call_anthropic",
        _fake_openai('{"general_notes":"Truck working at station"}'),
    )
    r = await translate_es_to_en_bulk(
        db, {"general_notes": "Camion 24-12 trabajando en la estacion"},
        preserve_tokens={"24-12"},
    )
    assert r.ok is False
    assert r.error == "translation_preserve_token_lost"


@pytest.mark.asyncio
async def test_fallback_to_anthropic_after_openai_error(monkeypatch):
    db = _MemDb()

    async def _openai_boom(*a, **kw):
        raise RuntimeError("openai outage")
    monkeypatch.setattr(tr_service, "_call_openai", _openai_boom)
    monkeypatch.setattr(
        tr_service, "_call_anthropic",
        _fake_openai('{"a":"hello"}'),
    )
    r = await translate_es_to_en_bulk(db, {"a": "hola"})
    assert r.ok is True
    assert r.provider == "anthropic"
    assert r.model == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_missing_llm_key_fails_closed(monkeypatch):
    db = _MemDb()
    monkeypatch.delenv("EMERGENT_LLM_KEY", raising=False)
    r = await translate_es_to_en_bulk(db, {"a": "hola"})
    assert r.ok is False
    assert r.error == "llm_key_missing"


@pytest.mark.asyncio
async def test_audit_row_always_written(monkeypatch):
    db = _MemDb()
    monkeypatch.setattr(tr_service, "_call_openai",
                        _fake_openai('{"a":"hello"}'))
    await translate_es_to_en_bulk(db, {"a": "hola"}, actor="qa")
    audit_rows = [r for r in db.rows if r["_coll"] == "translation_audit"]
    assert len(audit_rows) == 1
    assert audit_rows[0]["ok"] is True
    assert audit_rows[0]["actor"] == "qa"


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
