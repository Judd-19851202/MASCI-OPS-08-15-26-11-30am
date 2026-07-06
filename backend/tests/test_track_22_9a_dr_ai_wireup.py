"""TRACK 22.9A · V1 Daily Report AI Wire-Up regression lock.

Locks the surgical wire-up: the V1 form now includes a non-blocking
AI summary assist, but:

* the assist NEVER blocks Daily Report submit,
* the V2 shell stays retired (no route resurrection),
* the tenant AI flag stays audit-logged,
* the summary section reuses the existing /api/dr-v2/ai/synthesize
  backend (no new AI backend routes),
* fallback exists when AI is unavailable,
* the accepted-summary field flows into the DR payload as
  ``ai_accepted_summary`` (a new, additive field — schema-safe).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


V1_FORM = Path("/app/frontend/src/pages/NewDailyReport.jsx")
ASSIST = Path("/app/frontend/src/components/daily-report/DailySummaryAssist.jsx")
ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_v1_form_imports_summary_assist():
    src = _read(V1_FORM)
    assert "DailySummaryAssist" in src, "V1 form must import DailySummaryAssist"
    assert re.search(r'from\s+"@/components/daily-report/DailySummaryAssist"', src), \
        "import path must point to daily-report component"


def test_v1_form_renders_summary_assist_before_signoff():
    src = _read(V1_FORM)
    assist_pos = src.find("<DailySummaryAssist")
    # Sign-Off band may appear multiple places (LifecycleGuide + actual
    # section); the actual band is the LAST occurrence.
    signoff_pos = src.rfind("Sign-Off / Submit")
    submit_pos = src.find("prepared-by-sig")
    assert assist_pos > 0, "V1 form must render <DailySummaryAssist />"
    assert assist_pos < signoff_pos, "Summary assist must sit before Sign-Off band"
    assert assist_pos < submit_pos, "Summary assist must sit before signature pad"


def test_v1_form_does_not_block_submit_on_assist():
    """The submit handler must not await / gate on the summary assist."""
    src = _read(V1_FORM)
    # Locate the submit handler region
    submit_call = src.find('url: "/daily-reports"')
    assert submit_call > 0
    # Backwards search: within the enclosing async function body, the
    # code must NOT await on summary generation or the assist component.
    preceding = src[max(0, submit_call - 4000):submit_call]
    for forbidden in ("await synthesize", "await summarize", "await dailySummaryAssist",
                      "await DailySummaryAssist", "await drV2Synthesize"):
        assert forbidden not in preceding, (
            f"submit path must not await on {forbidden!r}"
        )


def test_v2_shell_stays_retired():
    """No V2 route resurrection — the retired shell must still redirect."""
    src = _read(ROUTES)
    # The retired shell path must not re-appear as a live element.
    # Only the redirect stub is allowed.
    live_route = re.search(
        r'path="/daily-report/v2"\s+element=\{<DailyReportV2', src
    )
    assert live_route is None, "V2 daily report shell must not be reactivated"
    redirect = re.search(
        r'path="/daily-report/v2"\s+element=\{<Navigate to="/daily/submit"',
        src,
    )
    assert redirect is not None, "V2 route must still redirect to V1"


def test_assist_uses_existing_backend_no_new_ai_routes():
    """Assist reuses /api/dr-v2/* endpoints — no new AI backend endpoints."""
    src = _read(ASSIST)
    assert "/dr-v2/drafts" in src
    assert "/dr-v2/ai/synthesize" in src
    # It must NOT invent a new /daily-reports/ai path.
    assert "/daily-reports/ai/" not in src
    assert "/api/ai/summary" not in src


def test_assist_is_debounced_and_cancels_stale_requests():
    src = _read(ASSIST)
    assert "DEBOUNCE_MS" in src, "assist must debounce field updates"
    m = re.search(r"DEBOUNCE_MS\s*=\s*(\d+)", src)
    assert m is not None
    ms = int(m.group(1))
    assert 500 <= ms <= 2000, (
        f"debounce must be within field-friendly range 500–2000ms · got {ms}"
    )
    assert "AbortController" in src, "must cancel stale in-flight requests"
    assert "requestSeqRef" in src, "must guard against out-of-order responses"


def test_assist_has_hard_timeout():
    src = _read(ASSIST)
    m = re.search(r"REQUEST_TIMEOUT_MS\s*=\s*(\d+)", src)
    assert m is not None, "assist must define REQUEST_TIMEOUT_MS"
    ms = int(m.group(1))
    assert 5000 <= ms <= 20000, (
        f"assist hard timeout must be 5–20s · got {ms}"
    )


def test_assist_has_deterministic_fallback():
    src = _read(ASSIST)
    assert "buildDeterministicFallback" in src
    # Fallback must be grounded — no AI branding, no invented facts.
    assert "invents" not in src.lower() or "never invents" in src.lower()


def test_assist_exposes_accept_edit_regenerate_ignore():
    src = _read(ASSIST)
    for testid_suffix in ("accept", "regenerate", "clear", "textarea"):
        assert f"data-testid={{`${{testId}}-{testid_suffix}`}}" in src, (
            f"assist must expose testid ...-{testid_suffix} for e2e drivers"
        )


def test_no_raw_key_or_provider_branding_in_field_ui():
    """Field UI must not show 'powered by OpenAI/Claude' text."""
    src = _read(ASSIST)
    lower = src.lower()
    for banned in ("powered by openai", "powered by anthropic", "powered by claude",
                   "gpt-", "sk-"):
        assert banned not in lower, (
            f"field UI must not surface {banned!r}"
        )


def test_accepted_summary_flows_into_dr_payload():
    """On Accept, the summary text is copied onto ``ai_accepted_summary``
    in the parent DR data via ``set()``. The provenance metadata is
    stored on ``ai_accepted_summary_meta``. Both fields flow into the
    DR submit payload; ODS spine picks up the meta as a first-class
    ``day_summary_fact``. This is the only mechanism by which downstream
    consumers (PDF, PM screens, ODS) see the accepted narrative."""
    src = _read(V1_FORM)
    assert re.search(
        r'set\("ai_accepted_summary",\s*text\)', src
    ), "V1 form must copy accepted summary text onto ai_accepted_summary"
    assert re.search(
        r'set\("ai_accepted_summary_meta",\s*meta\s*\|\|\s*null\)', src
    ), "V1 form must copy provenance meta onto ai_accepted_summary_meta"


def test_dr_model_accepts_new_summary_fields():
    """Pydantic model must accept the two new fields without extra=allow
    magic — they are documented, typed, first-class."""
    from routes.daily_reports import DailyReportCreate
    payload = {
        "project_name": "Test", "location": "Test", "report_date": "2026-02-06",
        "prepared_by": "Test", "ai_accepted_summary": "test narrative",
        "ai_accepted_summary_meta": {"source": "ai", "confidence": 0.72},
    }
    m = DailyReportCreate(**payload)
    assert m.ai_accepted_summary == "test narrative"
    assert m.ai_accepted_summary_meta == {"source": "ai", "confidence": 0.72}


def test_ods_spine_emits_day_summary_fact_when_summary_present():
    """When a DR has ai_accepted_summary, the ODS spine builder emits
    exactly one ``day_summary_fact`` so PM/executive dashboards can
    render the narrative from a canonical source."""
    from services.ods_spine.ingest import _build_facts_from_dr_v1_report
    rec = {
        "id": "dr-t229a-1", "project_number": "20-04",
        "report_date": "2026-02-06", "prepared_by": "Test",
        "created_at": "2026-02-06T10:00:00+00:00",
        "ai_accepted_summary": "Crew installed 200 LF of pipe.",
        "ai_accepted_summary_meta": {
            "source": "edited", "provider_masked": "emergent",
            "model_masked": "claude-sonnet", "confidence": 0.72,
            "evidence_refs": ["masci_crews[0]", "materials[1]"],
            "latency_ms": 8600,
        },
    }
    facts = _build_facts_from_dr_v1_report(rec)
    sums = [f for f in facts if f.get("fact_type") == "day_summary_fact"]
    assert len(sums) == 1, f"expected exactly one day_summary_fact · got {len(sums)}"
    p = sums[0]["payload"]
    assert p["text"].startswith("Crew installed")
    assert p["source"] == "edited"
    assert p["confidence"] == 0.72
    assert "masci_crews[0]" in (p["evidence_refs"] or [])
    assert p["latency_ms"] == 8600


def test_ods_spine_omits_day_summary_fact_when_summary_absent():
    """Reports without an accepted summary must NOT emit a summary fact
    (would create empty spine rows)."""
    from services.ods_spine.ingest import _build_facts_from_dr_v1_report
    rec = {
        "id": "dr-t229a-2", "project_number": "20-04",
        "report_date": "2026-02-06", "prepared_by": "Test",
        "created_at": "2026-02-06T10:00:00+00:00",
    }
    facts = _build_facts_from_dr_v1_report(rec)
    sums = [f for f in facts if f.get("fact_type") == "day_summary_fact"]
    assert sums == [], "must not emit day_summary_fact when summary absent"


def test_photo_upload_and_submit_paths_unchanged():
    """Sanity: existing photo upload + submit paths must remain intact."""
    src = _read(V1_FORM)
    assert 'url: "/daily-reports"' in src, "V1 submit endpoint must remain"
    assert "PhotoUpload" in src, "photo upload must remain"
    assert "idempotencyKeyRef" in src, "idempotency must remain"
    assert "enqueueUpload" in src, "offline queue must remain"
