from __future__ import annotations

import pytest

from services.photo_intelligence.pipeline import list_draft_intelligence, _extract_draft_photo_batches


class _Cursor:
    def __init__(self, rows):
        self.rows = rows

    async def to_list(self, length=200):
        return list(self.rows)[:length]


class _Collection:
    def __init__(self, rows=None):
        self.rows = rows or []

    def find(self, query, projection=None):
        def _match(doc):
            for k, v in query.items():
                if doc.get(k) != v:
                    return False
            return True
        return _Cursor([d for d in self.rows if _match(d)])


class _DB:
    def __init__(self):
        self.collections = {
            "dr_v2_photo_intelligence": _Collection(),
            "dr_v1_photo_intel_jobs": _Collection(),
        }

    def __getitem__(self, name):
        return self.collections[name]


@pytest.mark.asyncio
async def test_all_photos_are_accounted_for_with_duplicates_and_terminal_failures():
    db = _DB()
    draft_identity = "dr03-operator-proof"
    draft = {"photos": [f"photo://{i}.jpg" for i in range(9)]}
    photo_ids = [row["photo_id"] for row in _extract_draft_photo_batches(draft)]
    db["dr_v2_photo_intelligence"].rows = [
        {"report_id": draft_identity, "photo_id": photo_ids[0], "analysis_status": "complete", "observations": [{"description": "fresh curb alignment visible"}]},
        {"report_id": draft_identity, "photo_id": photo_ids[1], "analysis_status": "complete", "observations": []},
        {"report_id": draft_identity, "photo_id": photo_ids[2], "analysis_status": "complete", "observations": [{"description": "concrete placement visible"}]},
        {"report_id": draft_identity, "photo_id": photo_ids[3], "analysis_status": "complete", "observations": [{"description": "equipment staged near curb work"}]},
        {"report_id": draft_identity, "photo_id": photo_ids[4], "analysis_status": "complete", "observations": [{"description": "traffic control devices present"}]},
        {"report_id": draft_identity, "photo_id": photo_ids[5], "analysis_status": "complete", "observations": [{"description": "duplicate reused"}]},
        {"report_id": draft_identity, "photo_id": photo_ids[6], "analysis_status": "unavailable", "observations": []},
    ]
    db["dr_v1_photo_intel_jobs"].rows = [
        {"report_id": draft_identity, "photo_id": photo_ids[0], "status": "complete"},
        {"report_id": draft_identity, "photo_id": photo_ids[1], "status": "complete"},
        {"report_id": draft_identity, "photo_id": photo_ids[2], "status": "complete"},
        {"report_id": draft_identity, "photo_id": photo_ids[3], "status": "complete"},
        {"report_id": draft_identity, "photo_id": photo_ids[4], "status": "complete"},
        {"report_id": draft_identity, "photo_id": photo_ids[5], "status": "duplicate_reused"},
        {"report_id": draft_identity, "photo_id": photo_ids[6], "status": "terminal"},
        {"report_id": draft_identity, "photo_id": photo_ids[7], "status": "pending"},
        {"report_id": draft_identity, "photo_id": photo_ids[8], "status": "in_progress"},
    ]

    out = await list_draft_intelligence(db, draft_identity=draft_identity, draft=draft)
    assert out["photo_count"] == 9
    assert out["reviewed"] == 6
    assert out["duplicates_reused"] == 1
    assert out["terminal_failures"] == 1
    assert out["queued"] == 1
    assert out["processing"] == 1
    assert out["status"] == "partially_analyzed"
    assert "Analyzed 6 of 9 photos" in out["status_message"]
