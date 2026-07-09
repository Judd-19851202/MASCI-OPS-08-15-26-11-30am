"""TRACK 26.12 — Elite AI Daily Report Summary fix verification.

Covers:
  1. Draft save with real photos (data URLs)
  2. Synthesize with photos (>800 chars, cites photo + full field coverage)
  3. Regenerate → faster via vision cache
  4. Synthesize without photos → still ai_available=true
  5. GET /api/dr-v2/meta → ai_available & feature_flag true
  6. V1 deterministic path regression (no 5xx)
"""
import base64
import io
import os
import time

import httpx
import pytest
from PIL import Image

def _api_base():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if not v:
        for line in open("/app/frontend/.env"):
            if line.startswith("REACT_APP_BACKEND_URL="):
                v = line.strip().split("=", 1)[1]
                break
    return v.rstrip("/") + "/api"

BASE = _api_base()
IMG_URL = (
    "https://static.prod-images.emergentagent.com/jobs/436a87e2-f67d-4058-b777-9aca7c698514/"
    "images/96c688e4080a946a44cc36d13a777ff4faad4eee3d64673ab9b023ab8af0249d.png"
)


def _to_jpeg_data_url(img: Image.Image) -> str:
    img = img.convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=78)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture(scope="module")
def real_photos():
    with httpx.Client(timeout=60) as c:
        raw = c.get(IMG_URL).content
    base_img = Image.open(io.BytesIO(raw))
    w, h = base_img.size
    return [
        _to_jpeg_data_url(base_img),
        _to_jpeg_data_url(base_img.crop((0, 0, w // 2 + 80, h))),
        _to_jpeg_data_url(base_img.crop((w // 2 - 80, 0, w, h))),
    ]


def _full_draft(report_id, photos):
    return {
        "report_id": report_id,
        "project_number": "26-07",
        "project_name": "University High Parent Loop Ext",
        "client": "Volusia County Schools",
        "project_manager": "Mike Masci",
        "location": "Orange City, Florida",
        "report_date": "2026-07-08",
        "supervisor_name": "Jaymn Judd",
        "weather_summary": "Overcast, 75-93F",
        "masci_crews": [{"name": "Jaymn Judd", "trade": "Superintendent", "hours_worked": 9}],
        "subcontractors": [
            {"company": "TOPCON Paving", "trade": "Tech", "contact": "Dane"},
            {"company": "C & F Hyatt", "headcount": 8, "hours": 11,
             "notes": "Formed & poured flatwork sidewalk along parent loop"},
        ],
        "equipment_used": [{"description": "Bobcat S650 skid steer", "hours": 6}],
        "materials": [{"material": "3000psi Concrete", "quantity": 18, "unit": "CY",
                       "carrier": "Maschmeyer Concrete", "ticket": "MC-88231"}],
        "production": [{"description": "Sidewalk flatwork", "quantity": 240, "unit": "LF",
                        "sta_from": "12+00", "sta_to": "14+40", "percent_complete": 65}],
        "constraints": [{"constraint_type": "utility_conflict",
                         "description": "Irrigation line hit near sta 13+10, repaired by crew, 45 min impact"}],
        "day_impacts": {"schedule_delays": "Yes",
                        "schedule_delays_notes": "45 min lost to irrigation repair",
                        "weather_impact": "No", "weather_impact_notes": ""},
        "visitors": [{"name": "R. Ortiz", "company": "Volusia County", "purpose": "sidewalk inspection"}],
        "narrative_sections": {
            "tomorrow_plan": "Continue sidewalk pours sta 14+40 to 16+00, strip forms from today's pour",
            "follow_ups": "Need approved mix design submittal back from PM before Friday curb pour",
        },
        "general_notes": "School zone traffic control in place all day.",
        "photos": photos,
        "photo_captions": ["Sidewalk pour in progress", "", ""],
    }


# --- Meta endpoint ---
def test_meta_ai_available():
    r = httpx.get(f"{BASE}/dr-v2/meta", timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j.get("ai_available") is True, j
    assert j.get("feature_flag") is True, j


# --- Draft save + synthesize with photos ---
_STATE = {}

def test_draft_save_with_photos(real_photos):
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{BASE}/dr-v2/drafts",
                   json=_full_draft("t2612-testagent-1", real_photos))
    assert r.status_code == 200, r.text
    _STATE["photos"] = real_photos


def test_synth_full_draft_with_photos():
    t0 = time.time()
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{BASE}/dr-v2/ai/synthesize",
                   json={"report_id": "t2612-testagent-1",
                         "agents": ["day_narrative"], "force": True})
    el = time.time() - t0
    _STATE["first_elapsed"] = el
    assert r.status_code == 200, r.text
    j = r.json()
    out = (j.get("outputs") or {}).get("day_narrative") or {}
    assert out.get("ai_available") is True, out
    narr = out.get("narrative") or ""
    assert len(narr) > 800, f"narrative too short ({len(narr)}): {narr[:400]}"
    obs = j.get("photo_observations_used") or 0
    assert obs >= 3, f"photo_observations_used={obs}"

    # deterministic fallback pattern must NOT be present
    assert not ("Crew reported" in narr and "entries" in narr), \
        f"Detected deterministic template: {narr[:400]}"

    low = narr.lower()
    missing = []
    for token in [
        "topcon", "hyatt",              # sub company names
        "maschmeyer",                    # material carrier
        "mc-88231",                      # ticket
        "12+00",                         # station range
        "65",                            # percent complete
        "irrigation",                    # delay/constraint
        "ortiz",                         # visitor
        "14+40",                         # tomorrow plan sta
        "mix design",                    # PM follow-ups
    ]:
        if token not in low:
            missing.append(token)
    assert not missing, f"Narrative missing required tokens: {missing}\n--- narrative ---\n{narr}"


def test_regenerate_faster_via_cache():
    t0 = time.time()
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{BASE}/dr-v2/ai/synthesize",
                   json={"report_id": "t2612-testagent-1",
                         "agents": ["day_narrative"], "force": True})
    el = time.time() - t0
    assert r.status_code == 200, r.text
    j = r.json()
    out = (j.get("outputs") or {}).get("day_narrative") or {}
    assert out.get("ai_available") is True, out
    assert (j.get("photo_observations_used") or 0) >= 3
    # Cache should save vision time; allow small overhead for LLM variance
    first = _STATE.get("first_elapsed", 999)
    assert el < first + 5, f"regen elapsed={el:.1f}s not ~< first={first:.1f}s (cache expected to help)"


# --- Synthesize with no photos ---
def test_synth_no_photos_still_ai_available():
    draft = _full_draft("t2612-testagent-nophoto-1", [])
    draft["photos"] = []
    draft["photo_captions"] = []
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{BASE}/dr-v2/drafts", json=draft)
        assert r.status_code == 200, r.text
        r = c.post(f"{BASE}/dr-v2/ai/synthesize",
                   json={"report_id": "t2612-testagent-nophoto-1",
                         "agents": ["day_narrative"], "force": True})
    assert r.status_code == 200, r.text
    j = r.json()
    out = (j.get("outputs") or {}).get("day_narrative") or {}
    assert out.get("ai_available") is True, out
    narr = out.get("narrative") or ""
    assert len(narr) > 400, f"narrative too short: {narr!r}"
    assert not ("Crew reported" in narr and "entries" in narr), \
        f"Deterministic template in no-photo path: {narr[:400]}"


# --- V1 regression ---
def test_v1_deterministic_summary_no_5xx():
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{BASE}/daily-reports/summary/draft",
                   json={"project_number": "26-07",
                         "report_date": "2026-07-08",
                         "supervisor_name": "Jaymn Judd"})
    assert r.status_code < 500, f"V1 returned 5xx: {r.status_code} {r.text[:400]}"
    j = r.json()
    assert j.get("ok") is True, j
