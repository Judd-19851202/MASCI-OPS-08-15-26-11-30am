"""
TRACK 27.07B · Reference registry + conservative-fall-through regression contract.

Locks the five proven defects fixed by this track, so a regression
cannot reintroduce a false-orphan mechanism. Every test in this file
proves one specific defect stays fixed. Do not weaken assertions.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest

from services.r2_lifecycle.references import (
    REFERENCE_SOURCES,
    _extract_key,
    _walk_path,
    scan_mongo_references,
)
from services.r2_lifecycle.classification import (
    classify_object,
    classify_all,
    _HISTORICAL_PREFIXES,
)


# ─── Repair A · Missing collections ──────────────────────────────────
def test_registry_covers_safety_documents_collection():
    names = [s.collection for s in REFERENCE_SOURCES]
    assert "safety_documents" in names, (
        "TRACK 27.07B repair A regression: `safety_documents` must "
        "be a registered reference source (doc:// refs live there)."
    )
    src = next(s for s in REFERENCE_SOURCES if s.collection == "safety_documents")
    assert src.ref_scheme == "doc://"
    assert "file_data" in src.paths


def test_registry_covers_fire_extinguishers_attachments():
    names = [s.collection for s in REFERENCE_SOURCES]
    assert "fire_extinguishers" in names, (
        "TRACK 27.07B repair A regression: `fire_extinguishers` "
        "attachments carry doc:// refs and must be registered."
    )
    src = next(s for s in REFERENCE_SOURCES if s.collection == "fire_extinguishers")
    assert src.ref_scheme == "doc://"
    assert "attachments.*.file_data" in src.paths


# ─── Repair B · doc:// normalization ────────────────────────────────
def test_doc_scheme_extracts_key():
    key = _extract_key("doc://masci-hub/safety-docs/2026/07/abc/file.pdf", "doc://")
    assert key == "safety-docs/2026/07/abc/file.pdf"


def test_doc_scheme_handles_percent_encoded_key():
    # Uses %20 in place of space
    key = _extract_key("doc://masci-hub/safety-docs/2026/some%20file.pdf", "doc://")
    assert key == "safety-docs/2026/some file.pdf"


def test_doc_scheme_rejects_missing_key_segment():
    assert _extract_key("doc://bucket/", "doc://") is None
    assert _extract_key("doc://bucket", "doc://") is None
    assert _extract_key("", "doc://") is None
    assert _extract_key(None, "doc://") is None
    assert _extract_key({"not": "a string"}, "doc://") is None


def test_doc_scheme_rejects_other_scheme_input():
    # Wrong scheme must not silently be accepted.
    assert _extract_key("data:application/pdf;base64,AAAA", "doc://") is None
    assert _extract_key("photo://bucket/key.pdf", "doc://") is None


def test_http_r2_url_extraction():
    # Full HTTPS R2 URL → key extracted regardless of source's declared scheme.
    url = "https://46400762d3.r2.cloudflarestorage.com/masci-hub/photos/2026/07/x.jpg"
    assert _extract_key(url, "photo://") == "photos/2026/07/x.jpg"


def test_http_r2_url_strips_query_string():
    url = "https://acct.r2.cloudflarestorage.com/masci-hub/documents/x.pdf?sig=abc"
    assert _extract_key(url, "doc://") == "documents/x.pdf"


def test_photo_scheme_still_works_backcompat():
    key = _extract_key("photo://masci-hub/photos/2026/07/x.jpg", "photo://")
    assert key == "photos/2026/07/x.jpg"


def test_raw_key_still_works_backcompat():
    assert _extract_key("backups/auto-90d/x.zip", "raw_key") == "backups/auto-90d/x.zip"
    assert _extract_key("/backups/x.zip", "raw_key") == "backups/x.zip"
    # scheme prefixes must still be rejected on raw_key
    assert _extract_key("doc://bucket/x.zip", "raw_key") is None


# ─── Repair C · Nested traversal ────────────────────────────────────
def test_walker_yields_dicts_at_star_terminal():
    """When path ends in `*`, walker yields array elements (may be dicts)."""
    doc = {"attachments": [{"attachment_ref": "photo://b/k1.jpg"},
                           {"attachment_ref": "photo://b/k2.jpg"}]}
    yielded = list(_walk_path(doc, "attachments.*"))
    assert len(yielded) == 2
    assert all(isinstance(v, dict) for v in yielded)


def test_walker_descends_into_dict_field_after_star():
    """TRACK 27.07B repair C — `attachments.*.attachment_ref` must
    yield the *string* inside the dict, not the dict."""
    doc = {"attachments": [
        {"attachment_ref": "photo://b/k1.jpg"},
        {"attachment_ref": "photo://b/k2.jpg"},
        {"filename": "no-ref.pdf"},  # no attachment_ref key → silent
    ]}
    yielded = list(_walk_path(doc, "attachments.*.attachment_ref"))
    assert sorted(yielded) == ["photo://b/k1.jpg", "photo://b/k2.jpg"]


def test_walker_arrays_of_strings_still_work():
    doc = {"photos": ["photo://b/a.jpg", "photo://b/b.jpg"]}
    yielded = list(_walk_path(doc, "photos.*"))
    assert sorted(yielded) == ["photo://b/a.jpg", "photo://b/b.jpg"]


def test_walker_missing_path_silent():
    assert list(_walk_path({}, "attachments.*.attachment_ref")) == []
    assert list(_walk_path({"attachments": None}, "attachments.*.attachment_ref")) == []


# ─── Repair D · Conservative fall-through ───────────────────────────
def _mk_inv(key, hours_old=48, size=100):
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_old)
    return {"key": key, "size": size, "prefix": key.split("/")[0],
            "last_modified": ts.isoformat()}


def test_incomplete_reference_scan_forces_unknown_not_orphan():
    inv = _mk_inv("photos/2026/07/orphaned.jpg")
    r = classify_object(inv, refs=[], reference_scan_complete=False,
                        unresolved_refs_present=False)
    assert r.classification == "UNKNOWN"
    assert "reference_scan_incomplete" in r.protective_flags


def test_unresolved_refs_present_forces_ambiguous_not_orphan():
    inv = _mk_inv("photos/2026/07/orphaned.jpg")
    r = classify_object(inv, refs=[], reference_scan_complete=True,
                        unresolved_refs_present=True)
    assert r.classification == "AMBIGUOUS"
    assert "unresolved_refs" in r.protective_flags


def test_clean_orphan_only_when_complete_scan_and_zero_unresolved():
    inv = _mk_inv("photos/2026/07/orphaned.jpg")
    r = classify_object(inv, refs=[], reference_scan_complete=True,
                        unresolved_refs_present=False)
    assert r.classification == "VERIFIED_ORPHAN"


def test_pending_window_still_beats_orphan():
    inv = _mk_inv("photos/2026/07/recent.jpg", hours_old=0.5)
    r = classify_object(inv, refs=[], reference_scan_complete=True,
                        unresolved_refs_present=False)
    assert r.classification == "PENDING"


def test_verified_owner_when_at_least_one_ref():
    inv = _mk_inv("photos/2026/07/x.jpg")
    refs = [{"r2_key": "photos/2026/07/x.jpg", "collection": "daily_reports",
             "owner": "Daily Report", "feature": "daily_reports",
             "doc_id": "dr-1", "field_path": "photos.*"}]
    r = classify_object(inv, refs=refs, reference_scan_complete=True,
                        unresolved_refs_present=False)
    assert r.classification == "VERIFIED_OWNER"


def test_drill_photos_prefix_maps_to_historical():
    """TRACK 27.07B repair · `drill-photos/` is a legacy prefix with
    no live writer — objects there must never be classified ORPHAN."""
    assert any("drill-photos" in p for p in _HISTORICAL_PREFIXES)
    inv = _mk_inv("drill-photos/be35f16fd8c3/photos/2026/05/x.jpg")
    r = classify_object(inv, refs=[], reference_scan_complete=True,
                        unresolved_refs_present=False)
    assert r.classification == "HISTORICAL"


def test_system_reserved_prefix_wins_over_completeness_gate():
    """Even when scan is incomplete, protected prefixes stay protected."""
    inv = _mk_inv("system/x.blob")
    r = classify_object(inv, refs=[], reference_scan_complete=False,
                        unresolved_refs_present=False)
    assert r.classification == "SYSTEM_RESERVED"


def test_backup_prefix_wins_over_completeness_gate():
    inv = _mk_inv("backups/auto-90d/MASCI_complete_backup_2026-07-11.zip")
    r = classify_object(inv, refs=[], reference_scan_complete=False,
                        unresolved_refs_present=True)
    assert r.classification == "BACKUP_PROTECTED"


# ─── Repair E · Full-run integration test ──────────────────────────
class _FakeCol:
    def __init__(self, docs=None):
        self._docs = list(docs or [])
        self._inserted = []

    def find(self, *_a, **_kw):
        docs = self._docs

        class _Cur:
            def __aiter__(self_inner):
                return self_inner

            async def __anext__(self_inner):
                if not hasattr(self_inner, "_i"):
                    self_inner._i = 0
                if self_inner._i >= len(docs):
                    raise StopAsyncIteration
                d = docs[self_inner._i]
                self_inner._i += 1
                return dict(d)
        return _Cur()

    async def insert_many(self, ops, **_):
        self._inserted.extend(ops)

    async def insert_one(self, op):
        self._inserted.append(op)

    async def delete_many(self, *_a, **_kw):
        pass

    async def find_one(self, *_a, **_kw):
        return dict(self._docs[0]) if self._docs else None

    async def bulk_write(self, ops, **_):
        pass


class _FakeDB:
    def __init__(self):
        # Register the collections we care about with fake owners.
        self._cols = {
            "safety_documents": _FakeCol([
                {"id": "sd-1", "file_data": "doc://masci-hub/safety-docs/2026/07/x.pdf",
                 "storage_backend": "r2"},
            ]),
            "fire_extinguishers": _FakeCol([
                {"id": "fe-1", "attachments": [
                    {"id": "att-1", "file_data": "doc://masci-hub/safety-docs/2026/07/fe-1/y.pdf"},
                ]},
            ]),
            "daily_reports": _FakeCol([
                {"id": "dr-1",
                 "photos": ["photo://masci-hub/photos/2026/07/dr-1/p.jpg"],
                 "attachments": [{"attachment_ref": "photo://masci-hub/documents/2026/07/dr-1/a.xlsm"}]},
            ]),
            "r2_references": _FakeCol(),
            "r2_lifecycle_runs": _FakeCol(),
        }
        # Fill in every other registered source with empty collections
        for s in REFERENCE_SOURCES:
            if s.collection not in self._cols:
                self._cols[s.collection] = _FakeCol()

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._cols.setdefault(name, _FakeCol())

    def __getitem__(self, name):
        return self._cols.setdefault(name, _FakeCol())


def test_full_reference_scan_resolves_safety_and_fire_ext_and_dr_attachments():
    db = _FakeDB()
    summary = asyncio.get_event_loop().run_until_complete(
        scan_mongo_references(db, now=datetime.now(timezone.utc))
    )
    assert summary["complete"] is True
    keys = [op["r2_key"] for op in db._cols["r2_references"]._inserted]
    assert "safety-docs/2026/07/x.pdf" in keys, \
        "safety_documents.file_data must resolve"
    assert "safety-docs/2026/07/fe-1/y.pdf" in keys, \
        "fire_extinguishers.attachments[*].file_data must resolve"
    assert "documents/2026/07/dr-1/a.xlsm" in keys, \
        "daily_reports.attachments[*].attachment_ref must resolve"
    assert "photos/2026/07/dr-1/p.jpg" in keys, \
        "daily_reports.photos.* backward-compat must still resolve"


def test_unresolved_reference_is_counted_not_dropped():
    """A malformed ref goes into unresolved_by_source rather than
    disappearing silently."""
    db = _FakeDB()
    db._cols["safety_documents"] = _FakeCol([
        {"id": "sd-2", "file_data": "not-a-valid-ref"},
    ])
    summary = asyncio.get_event_loop().run_until_complete(
        scan_mongo_references(db, now=datetime.now(timezone.utc))
    )
    assert summary["unresolved_refs"] >= 1
    assert summary["unresolved_by_source"]["safety_documents"] >= 1
    # And no ref for that source was persisted
    keys = [op["r2_key"] for op in db._cols["r2_references"]._inserted]
    assert not any(k.endswith("not-a-valid-ref") for k in keys)


def test_no_verified_orphan_when_reference_scan_incomplete():
    """One source failure → zero VERIFIED_ORPHAN in classify_all."""
    db = _FakeDB()
    # Force one source to fail by making its find() raise.
    class _BoomCol(_FakeCol):
        def find(self, *_a, **_kw):
            raise RuntimeError("simulated source failure")
    db._cols["safety_documents"] = _BoomCol()
    summary = asyncio.get_event_loop().run_until_complete(
        scan_mongo_references(db, now=datetime.now(timezone.utc))
    )
    assert summary["complete"] is False
    assert summary["failed_sources"], summary
    # Now feed an inventory row into classify_all — object must NOT be VERIFIED_ORPHAN.
    db._cols["r2_inventory"] = _FakeCol([
        {"key": "photos/2026/07/x.jpg", "size": 100,
         "prefix": "photos", "last_modified":
             (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()},
    ])
    db._cols["r2_classifications"] = _FakeCol()
    cls_summary = asyncio.get_event_loop().run_until_complete(
        classify_all(db, now=datetime.now(timezone.utc))
    )
    assert cls_summary["counts"]["VERIFIED_ORPHAN"] == 0, cls_summary["counts"]
    assert cls_summary["counts"]["UNKNOWN"] >= 1, cls_summary["counts"]
    assert cls_summary["reference_scan_complete"] is False
