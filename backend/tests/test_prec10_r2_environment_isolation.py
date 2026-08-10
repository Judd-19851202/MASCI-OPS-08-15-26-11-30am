from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "/app/backend")

from lib.storage_ownership import (  # noqa: E402
    build_env_owned_key,
    current_env_owns_key,
    describe_key_ownership,
)


def test_storage_ownership_parses_namespaced_and_legacy_keys():
    preview_key = "photos/preview/2026/08/example.jpg"
    owned = describe_key_ownership(preview_key)
    assert owned.namespaced is True
    assert owned.family == "photos"
    assert owned.owner_env == "preview"
    assert owned.relative_key == "2026/08/example.jpg"

    legacy = describe_key_ownership("photos/2026/08/example.jpg")
    assert legacy.namespaced is False
    assert legacy.owner_env is None
    assert legacy.family == "photos"


def test_build_env_owned_key_scopes_all_supported_families(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert build_env_owned_key("photos", "2026/08/x.jpg") == "photos/production/2026/08/x.jpg"
    assert build_env_owned_key("documents", "2026/08/x.pdf") == "documents/production/2026/08/x.pdf"
    assert build_env_owned_key("promo-assets", "hero/x.mp4") == "promo-assets/production/hero/x.mp4"


def test_current_env_owns_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    assert current_env_owns_key("documents/preview/2026/08/file.pdf") is True
    assert current_env_owns_key("documents/production/2026/08/file.pdf") is False
    assert current_env_owns_key("documents/2026/08/file.pdf") is False


def test_explicit_legacy_overwrite_is_blocked(monkeypatch):
    import photo_storage  # noqa: PLC0415

    class _Client:
        def head_object(self, Bucket, Key):
            return {"ContentLength": 3}

        def put_object(self, **_kwargs):
            raise AssertionError("put_object must not run for legacy overwrite")

    monkeypatch.setattr(photo_storage, "_client", lambda: _Client())
    monkeypatch.setattr(photo_storage, "is_configured", lambda: True)

    async def _go():
        await photo_storage.upload_bytes(b"abc", key="photos/2026/08/legacy.jpg", content_type="image/jpeg")

    try:
        asyncio.run(_go())
    except PermissionError as exc:
        assert "legacy unowned object key" in str(exc)
        return
    raise AssertionError("legacy overwrite should have been blocked")


def test_safety_doc_delete_refuses_cross_environment_keys(monkeypatch):
    import safety_doc_storage  # noqa: PLC0415

    class _Client:
        def __init__(self):
            self.deleted = []

        def delete_object(self, Bucket, Key):
            self.deleted.append({"Bucket": Bucket, "Key": Key})

    monkeypatch.setenv("APP_ENV", "preview")
    client = _Client()
    monkeypatch.setattr(safety_doc_storage, "_client", lambda: client)

    async def _go():
        return await safety_doc_storage.delete_doc("doc://bucket/safety-docs/production/2026/08/file.pdf")

    assert asyncio.run(_go()) is False
    assert client.deleted == []