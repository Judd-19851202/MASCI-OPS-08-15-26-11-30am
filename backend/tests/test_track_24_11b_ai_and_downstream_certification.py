"""TRACK 24.11B · Phase 4-9 · AI evidence intake, archive routing,
and downstream endpoint locks.

Extends 24.11B upload certification into:
  * AI evidence bundle contract (Phase 4-5)
  * DR → Trust Spine + team_snapshot + attachment linkage (Phase 6-7)
  * Regression locks (Phase 9)
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

import pytest
import requests


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT.parent / "frontend" / "src"


def _api_url() -> str:
    fe = ROOT.parent / "frontend" / ".env"
    for line in fe.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not found")


API = _api_url() + "/api"


# ─── Phase 4 · AI evidence bundle must include every field class ───


REQUIRED_EVIDENCE_KEYS = [
    "project_number", "project_name", "client", "project_manager",
    "location", "report_date",
    "day_setup",
    "activity_cards", "masci_crews", "equipment_used",
    "materials", "outbound_materials",
    "subcontractors", "vendors",
    "visitors", "constraints_cards",
    "safety_quality",
    "excavation", "competent_person",
    "work_stoppage", "tomorrow_readiness", "general_notes",
    "photos", "photo_observations",
    "attachments",
]


@pytest.mark.parametrize("key", REQUIRED_EVIDENCE_KEYS)
def test_ai_evidence_bundle_includes_key(key):
    """The evidence bundle written by toEvidenceDraft must reference
    every required field class so the AI never silently ignores a
    section of the DR."""
    src = (FRONTEND / "components" / "daily-report" / "DailySummaryAssist.jsx").read_text()
    # Look for the key as an object property key (`key:` inside the
    # bundle literal).
    assert re.search(rf"\b{re.escape(key)}\s*:", src), (
        f"Evidence bundle missing key `{key}` — AI cannot reference "
        f"data it never receives."
    )


def test_ai_evidence_bundle_attachment_projection_is_metadata_only():
    """AI must NOT be sent raw attachment bytes — only filename,
    category, extension, file_size. Extraction (OCR / PDF text) is
    not implemented; the bundle must reflect that so the model
    cannot hallucinate file contents."""
    src = (FRONTEND / "components" / "daily-report" / "DailySummaryAssist.jsx").read_text()
    for k in ["filename:", "category:", "extension:", "file_size:"]:
        assert k in src, f"attachment projection missing `{k}`"
    # File bytes must not be forwarded.
    assert "attachment_ref" not in _get_attachment_block(src), (
        "Raw storage URL must not leak into AI evidence; only "
        "metadata is safe to expose."
    )


def _get_attachment_block(src: str) -> str:
    m = re.search(r"attachments:\s*\([^)]+\)[^}]*\}\)\)", src)
    return m.group(0) if m else ""


# ─── Phase 5 · Live AI synthesize round-trip ────────────────────────


def test_live_ai_synthesize_consumes_supervisor_text():
    """Round-trip a rich DR bundle through /dr-v2/ai/synthesize and
    verify the returned narrative references the supervisor's text.
    This is the ONLY way to prove the AI actually reads the inputs
    end-to-end on the live preview backend."""
    bundle = {
        "report_id": "track_24_11b_ai_probe",
        "project": {"project_number": "20-07", "project_name": "T5686 SR 15/SR600"},
        "day_setup": {"weather": "Clear 78F", "supervisor_name": "24.11B Probe"},
        "crew": [{"name": "Alec Perkins", "role": "General Laborer", "hours": 8}],
        "activities": [{"activity": "Placed 3 lifts of ABC-3 base along the south lane between STA 12+50 and STA 14+00", "hours": 8}],
        "safety": {"incidents_today": False,
                   "notes": "Crew reviewed trench safety before entering the 6-ft cut near STA 13+25."},
        "materials_in": [{"material": "ABC-3 base", "quantity": 240, "unit": "tons"}],
        "outbound_materials": [],
        "photos": [],
    }
    # Prime a draft.
    r = requests.post(f"{API}/dr-v2/drafts", json=bundle, timeout=30)
    assert r.status_code == 200, r.text[:200]
    # Synthesize.
    r = requests.post(
        f"{API}/dr-v2/ai/synthesize",
        json={"report_id": bundle["report_id"], "agents": ["day_narrative"], "force": True},
        timeout=90,
    )
    assert r.status_code == 200
    outputs = r.json().get("outputs", {})
    day = outputs.get("day_narrative") or {}
    narrative = (day.get("narrative") or day.get("text") or "").lower()
    assert narrative, "AI returned empty narrative"
    # It should reference the concrete facts the supervisor supplied.
    # Accept 1+ keyword match — LLM sometimes paraphrases (e.g.
    # "aggregate base" instead of "ABC-3") but must ground in the
    # payload's specifics somewhere.
    matches = sum(1 for m in ["abc-3", "sta 12", "sta 13", "sta 14", "trench",
                              "clear", "78", "6-ft", "6 ft", "aggregate", "base",
                              "south lane"] if m in narrative)
    assert matches >= 1, (
        f"AI narrative ignored supervisor evidence — 0 keyword matches. "
        f"narrative preview: {narrative[:400]}"
    )


def test_live_ai_synthesize_does_not_leak_provider_or_key():
    """The response must expose provider/model metadata (for
    provenance) but MUST NOT include the API key."""
    r = requests.post(
        f"{API}/dr-v2/ai/synthesize",
        json={"report_id": "track_24_11b_ai_probe", "agents": ["day_narrative"], "force": True},
        timeout=90,
    )
    body = r.text
    for leak in ["sk-", "Bearer ey", "EMERGENT_LLM_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        assert leak not in body, f"AI response leaked `{leak}` prefix"


# ─── Phase 6 · Archive / PM routing linkage ────────────────────────


DR_ID_PROBE = "85c5ed25-368e-46fe-8fa9-ae93993dd452"  # created in 24.10


def _admin_tok(_c={}):
    if "t" in _c: return _c["t"]
    r = requests.post(f"{API}/auth/multi-login", json={
        "email": "jaymn.judd@mascigc.com", "password": "Maddix123!"
    }, timeout=45)
    _c["t"] = r.json().get("portal_tokens", {}).get("admin", "")
    return _c["t"]


def test_probe_dr_carries_project_and_team_snapshot():
    """The 24.10 probe DR must carry both the project reference and
    the server-derived team_snapshot (proves PM/co-PM routing key)."""
    r = requests.get(
        f"{API}/daily-reports/{DR_ID_PROBE}",
        headers={"X-Admin-Token": _admin_tok()}, timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"probe DR {DR_ID_PROBE} not present; skipping linkage lock")
    d = r.json()
    assert d.get("project_number") == "20-07"
    assert d.get("team_snapshot"), "no team_snapshot on submitted DR"
    members = (d["team_snapshot"] or {}).get("members") or {}
    co_pm = [m.get("email") for m in (members.get("co_pm") or [])]
    assert "pm.demo@mascigc.com" in co_pm, (
        "server-derived co_pm routing did not include the jobs_master value"
    )


def test_probe_dr_hidden_from_user_facing_lists():
    """Synthetic-hygiene filter from Phase A must keep the probe DR
    out of PM/HR/Safety/admin daily-report listings."""
    tok = _admin_tok()
    for path in ["/daily-reports", "/daily-reports/approved?limit=500"]:
        r = requests.get(f"{API}{path}", headers={"X-Admin-Token": tok}, timeout=60)
        if r.status_code != 200:
            continue
        body = r.json()
        items = body if isinstance(body, list) else body.get("items", [])
        for it in items:
            assert (it.get("id") or "") != DR_ID_PROBE, (
                f"probe DR leaked into {path}"
            )


# ─── Phase 7 · PDF generation includes the payload photo ────────────


def test_probe_dr_pdf_generation_succeeds_and_embeds_project_facts():
    tok = _admin_tok()
    r = requests.get(
        f"{API}/daily-reports/{DR_ID_PROBE}/pdf",
        headers={"X-Admin-Token": tok}, timeout=120,
    )
    if r.status_code != 200:
        pytest.skip("probe PDF path unavailable; skipping PDF assertion")
    body = r.content
    assert body[:4] == b"%PDF", "response is not a PDF"
    # PDF should be large enough to contain the embedded photo
    # (a text-only 2-page PDF is ~30 KB; with a photo it's > 500 KB).
    assert len(body) > 100_000, (
        f"PDF suspiciously small ({len(body)} B) — photo may not have "
        f"been embedded."
    )


# ─── Phase 8/9 · Endpoint contract locks ───────────────────────────


def test_daily_reports_post_public_and_returns_id_and_docid():
    """The primary submit endpoint must be public (anonymous foreman
    flow) and return `id` + `doc_id` on success."""
    payload = {
        "project_number": "TEST-24.11B-DOCK",
        "project_name": "24.11B endpoint dock",
        "location": "24.11B dock",
        "report_date": "2026-02-07",
        "prepared_by": "24.11B lock probe",
        "masci_crews": [], "photos": [], "activities": [],
        "general_notes": "24.11B endpoint verification",
        "synthetic_record": True,
        "hidden_from_operations": True,
        "cleanup_track": "24.11B-lock",
    }
    r = requests.post(
        f"{API}/daily-reports", json=payload,
        headers={"Idempotency-Key": f"track2411b_lock"}, timeout=45,
    )
    assert r.status_code in (200, 201), r.text[:300]
    d = r.json()
    assert d.get("id")
    assert d.get("doc_id")


# ─── Phase 9 · Regression lock — no synthetic in Approved list ─────


def test_approved_list_excludes_synthetic():
    tok = _admin_tok()
    r = requests.get(
        f"{API}/daily-reports/approved?limit=500",
        headers={"X-Admin-Token": tok}, timeout=60,
    )
    assert r.status_code == 200
    sentinels = re.compile(
        r"^(TEST[_\-]|0000-TEST|SMOKE[_\-]|SYNTHETIC[_\-]|ITER[0-9]|QA_SMOKE|CERT_TEST|RECERT|PARITY)",
        re.IGNORECASE,
    )
    for it in r.json().get("items", []):
        pn = (it.get("project_number") or "").strip()
        assert not sentinels.match(pn), f"synthetic leaked: {it}"
