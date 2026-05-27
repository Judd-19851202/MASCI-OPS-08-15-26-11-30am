"""Unit tests for the iter437 idempotency strip patch.

Run with: cd /app/backend && python3 -m pytest tests/test_iter437_idempotency_strip.py -v
"""
from __future__ import annotations

from lib.idempotency import _strip_for_cache, _LARGE_STRING_PLACEHOLDER, _LARGE_STRING_BYTES


def test_strips_image_base64():
    payload = {"id": "x", "ok": True, "image_base64": "A" * 200_000}
    out = _strip_for_cache(payload)
    assert "image_base64" not in out
    assert out["id"] == "x" and out["ok"] is True


def test_strips_photos_array():
    payload = {"id": "y", "photos": [{"image_base64": "A" * 100}], "name": "report"}
    out = _strip_for_cache(payload)
    assert "photos" not in out
    assert out == {"id": "y", "name": "report"}


def test_strips_nested_attachments():
    payload = {
        "id": "z",
        "sections": [
            {"name": "crew", "attachments": [{"file_base64": "X"}]},
            {"name": "visitors", "data": "ok"},
        ],
    }
    out = _strip_for_cache(payload)
    assert "attachments" not in out["sections"][0]
    assert out["sections"][1]["data"] == "ok"


def test_strips_large_string_outside_known_keys():
    big = "Q" * (_LARGE_STRING_BYTES + 10)
    payload = {"id": "a", "freeform_note": big, "title": "small"}
    out = _strip_for_cache(payload)
    assert out["freeform_note"] == _LARGE_STRING_PLACEHOLDER
    assert out["title"] == "small"


def test_preserves_operational_fields():
    payload = {
        "id": "rep-1",
        "ok": True,
        "status": "created",
        "report_date": "2026-05-26",
        "created_at": "2026-05-26T12:00:00Z",
        "error": None,
        "message": "Report saved",
        "photos": ["A" * 100_000],  # would explode
    }
    out = _strip_for_cache(payload)
    for k in ("id", "ok", "status", "report_date", "created_at", "error", "message"):
        assert k in out, f"lost operational field: {k}"
    assert "photos" not in out


def test_handles_non_dict_root():
    # Some routes return lists or primitives.
    assert _strip_for_cache([{"image_base64": "x"}, {"id": 1}]) == [{}, {"id": 1}]
    assert _strip_for_cache("hello") == "hello"
    assert _strip_for_cache(None) is None
    assert _strip_for_cache(42) == 42


def test_handles_deeply_nested():
    payload = {"a": {"b": {"c": {"d": {"image_base64": "X" * 500, "keep": True}}}}}
    out = _strip_for_cache(payload)
    assert out["a"]["b"]["c"]["d"]["keep"] is True
    assert "image_base64" not in out["a"]["b"]["c"]["d"]


def test_strip_is_idempotent():
    """Stripping a stripped response must be a no-op."""
    payload = {"id": "x", "photos": ["A" * 100], "title": "t"}
    once = _strip_for_cache(payload)
    twice = _strip_for_cache(once)
    assert once == twice


def test_size_reduction_realistic():
    """Round-trip size assertion on a realistic daily-report shape."""
    payload = {
        "id": "dr-1",
        "ok": True,
        "report_date": "2026-05-26",
        "photos": [{"image_base64": "A" * 1_000_000} for _ in range(3)],  # ~3 MB
        "activities": "scope of work text",
    }
    import json
    before = len(json.dumps(payload))
    after = len(json.dumps(_strip_for_cache(payload)))
    assert before > 3_000_000, before
    assert after < 1_000, after  # post-strip should be tiny
    assert (before - after) / before > 0.99
