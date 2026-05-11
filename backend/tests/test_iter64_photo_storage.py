"""
test_iter64_photo_storage
=========================
Regression tests for the iter64 photo storage abstraction + migration.

Coverage:
* `is_configured` returns False when env vars are missing → safety net
  for unconfigured deploys (which must fall back to base64 storage with
  no behaviour change).
* `is_storage_ref` correctly classifies `photo://` URLs as cloud-backed
  and `data:image/...` URLs as base64.
* `_parse_ref` rejects malformed refs (so callers can fall back).
* `_ext_from_data_url` maps common mime types correctly and falls back
  to `jpg` for unknown types.
* `read_photo_bytes` decodes a base64 `data:` URL correctly without
  needing the S3 client.
* `photo_migration` schema constants reference real collection names.
* `_migrate_one_array` in dry-run mode doesn't touch S3 and reports
  correct migrate/skip counts including for already-migrated refs.
"""
from __future__ import annotations

import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _png_b64() -> str:
    """1x1 transparent PNG, base64-encoded → useful for round-trip tests."""
    one_pixel_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return "data:image/png;base64," + base64.b64encode(one_pixel_png).decode()


def test_is_configured_false_when_env_missing():
    """Critical safety net — when env vars aren't set, the system MUST
    fall back to base64 storage. False is the safe default."""
    # Clear any test env that might pollute
    for k in ("S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY"):
        os.environ.pop(k, None)
    import importlib
    import photo_storage
    importlib.reload(photo_storage)
    assert photo_storage.is_configured() is False


def test_is_storage_ref_classification():
    import photo_storage
    assert photo_storage.is_storage_ref("photo://mybucket/photos/2026/05/abc.jpg") is True
    assert photo_storage.is_storage_ref("data:image/png;base64,abc=") is False
    assert photo_storage.is_storage_ref("") is False
    assert photo_storage.is_storage_ref(None) is False
    assert photo_storage.is_storage_ref("https://random.com/x.jpg") is False
    assert photo_storage.is_storage_ref("photo://") is False  # malformed (no bucket/key)


def test_parse_ref_rejects_malformed():
    import photo_storage
    with __import__("pytest").raises(ValueError):
        photo_storage._parse_ref("not-a-ref")
    with __import__("pytest").raises(ValueError):
        photo_storage._parse_ref("photo://bucket-only")
    # Valid ref parses cleanly
    b, k = photo_storage._parse_ref("photo://mybucket/photos/2026/05/abc.jpg")
    assert b == "mybucket"
    assert k == "photos/2026/05/abc.jpg"


def test_ext_from_data_url_mapping():
    import photo_storage
    cases = {
        "data:image/jpeg;base64,xxx": "jpg",
        "data:image/png;base64,xxx": "png",
        "data:image/webp;base64,xxx": "webp",
        "data:image/heic;base64,xxx": "heic",
        "data:image/avif;base64,xxx": "avif",
        "data:image/unknown;base64,xxx": "jpg",  # default fallback
        "garbage": "jpg",  # no mime info
    }
    for url, expected in cases.items():
        assert photo_storage._ext_from_data_url(url) == expected, f"failed for {url}"


def test_read_photo_bytes_handles_base64():
    """read_photo_bytes must transparently decode base64 data URLs even
    when the S3 client isn't initialized — this is the dual-read
    contract that lets the platform serve mid-migration."""
    import photo_storage

    async def _go():
        return await photo_storage.read_photo_bytes(_png_b64())

    raw = asyncio.run(_go())
    assert isinstance(raw, bytes)
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "decoded bytes should be a valid PNG signature"


def test_read_photo_bytes_rejects_garbage():
    import photo_storage

    async def _go(ref):
        return await photo_storage.read_photo_bytes(ref)

    import pytest
    with pytest.raises(ValueError):
        asyncio.run(_go(""))
    with pytest.raises(ValueError):
        asyncio.run(_go("not-a-photo-ref"))


def test_photo_collections_schema_is_sane():
    """The migration map must reference collections that actually exist
    in the schema (or at minimum, are plausibly named). Catches typos
    that would silently skip a whole collection's worth of photos."""
    import photo_migration
    # These are the canonical collection names from the codebase — drift
    # here means the migrator misses photos.
    expected = {
        "daily_reports",
        "inspections",
        "qaqc_inspections",
        "safety_incidents",
        "meetings",
        "jha_records",
        "equipment_inspections",
        "shop_signoffs",
        "safety_form_records",
        "safety_equipment_trainings",
        "safety_equipment_returns",
        "field_leadership_records",
    }
    actual = set(photo_migration.PHOTO_COLLECTIONS.keys())
    missing = expected - actual
    extra = actual - expected
    assert not missing, f"PHOTO_COLLECTIONS missing canonical collections: {missing}"
    # field_leadership_records must include both top-level photos AND items.*.photos
    fl = photo_migration.PHOTO_COLLECTIONS["field_leadership_records"]
    assert "photos" in fl
    assert "items.*.photos" in fl, (
        "field_leadership_records.items.*.photos missing — would orphan "
        "per-item equipment-checkout photos in MongoDB after migration"
    )


def test_migrate_one_array_dry_run_classification():
    """Dry-run must accurately count what WOULD be migrated/skipped/failed
    without writing anything anywhere."""
    import photo_migration

    photos = [
        _png_b64(),                                        # would migrate
        "photo://bucket/photos/2026/05/x.jpg",              # already migrated → skip
        "data:image/jpeg;base64,/9j/4AAQ",                  # would migrate
        "",                                                  # not a string-as-data-URL → skip
        42,                                                  # non-string → skip
    ]

    async def _go():
        return await photo_migration._migrate_one_array(
            photos, source_id="test:abc", dry_run=True
        )

    new_list, mig, skp, fail, bts = asyncio.run(_go())
    assert mig == 2, f"expected 2 to migrate, got {mig}"
    assert skp == 3, f"expected 3 to skip, got {skp}"
    assert fail == 0
    # Dry-run preserves the original list — nothing is uploaded or changed.
    assert new_list == photos


def test_migrate_one_array_dry_run_idempotent_on_migrated_refs():
    """Already-migrated photo:// refs must skip cleanly — re-running
    after a partial migration must not double-charge bytes."""
    import photo_migration

    photos = [
        "photo://b/photos/2026/05/x.jpg",
        "photo://b/photos/2026/05/y.png",
        "photo://b/photos/2026/05/z.webp",
    ]

    async def _go():
        return await photo_migration._migrate_one_array(
            photos, source_id="test:idempotent", dry_run=True
        )

    new_list, mig, skp, fail, bts = asyncio.run(_go())
    assert mig == 0
    assert skp == 3
    assert bts == 0
    assert new_list == photos


# ── Iter64 Phase 2: sync read + PDF dual-read integration ─────────────


def test_resolve_to_data_url_sync_passthrough_for_data_urls():
    """A data: URL must be returned untouched — no R2 round-trip, no
    base64 re-encode, no truncation. This is how PDFs continue to render
    legacy records identically while migration is in progress."""
    import photo_storage
    src = _png_b64()
    assert photo_storage.resolve_to_data_url_sync(src) == src


def test_resolve_to_data_url_sync_safe_on_garbage():
    """Empty/None/unrecognized refs must return '' so PDF render can
    just skip the image gracefully (we never want a corrupt DB entry
    to crash a whole PDF render)."""
    import photo_storage
    assert photo_storage.resolve_to_data_url_sync("") == ""
    assert photo_storage.resolve_to_data_url_sync(None) == ""
    assert photo_storage.resolve_to_data_url_sync("https://random.example.com/x.jpg") == ""
    assert photo_storage.resolve_to_data_url_sync("garbage-string") == ""


def test_indexer_accepts_photo_uri_refs_not_just_data_urls():
    """Critical regression for iter64 Phase 2: the job_photos indexer
    must index BOTH legacy base64 photos AND migrated photo:// refs.
    Skipping photo:// refs here was the bug that caused migrated photos
    to vanish from the gallery on production."""
    import inspect
    from routes import job_photos
    src = inspect.getsource(job_photos.index_record_photos)
    # The filter must accept BOTH schemes. We assert on the string form
    # because the check happens inside a `continue`-guarded for-loop —
    # the simplest signal that the photo:// branch is wired.
    assert "photo://" in src, (
        "index_record_photos no longer references photo:// — migrated "
        "photos would not be indexed and would disappear from the gallery"
    )
