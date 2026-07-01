"""Track 19.16 · UX Hardening Batch 1 · LOCK TESTS.

Locks the routing + module contracts introduced by Batch 1:

  * Backend weather auto-fetch endpoint mounted
  * Backend project-context endpoint mounted
  * Weather module is pure I/O (no writes to any Mongo collection)
  * Frontend IncidentReport uses ProjectPicker + IdentityConfirm + Weather
  * Frontend schema no longer requests a raw text `job_number` field
  * FormShell renders the progress rail in a dedicated band (stable header)
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path("/app")
FE_ROOT = REPO_ROOT / "frontend/src"


# ── Backend contract ────────────────────────────────────────────────
def test_weather_module_exists_and_read_only():
    p = REPO_ROOT / "backend/incident_engine/weather.py"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert "fetch_current_weather" in src
    # Never writes to any Mongo collection.
    for forbidden in (".insert_one(", ".insert_many(",
                      ".update_one(", ".update_many(",
                      ".delete_one(", ".delete_many("):
        assert forbidden not in src


def test_report_routes_registers_weather_and_project_context():
    src = (REPO_ROOT / "backend/incident_engine/report_routes.py").read_text(
        encoding="utf-8")
    assert '"/incident-intelligence/weather"' in src
    assert '"/incident-intelligence/project-context/{project_number}"' in src
    assert "fetch_current_weather" in src


def test_project_context_route_is_read_only():
    """The project-context route must not mutate any Mongo collection."""
    src = (REPO_ROOT / "backend/incident_engine/report_routes.py").read_text(
        encoding="utf-8")
    idx = src.index("project_context")
    window = src[idx: idx + 2000]
    for forbidden in (".insert_one(", ".insert_many(",
                      ".update_one(", ".update_many(",
                      ".delete_one(", ".delete_many("):
        assert forbidden not in window


# ── Frontend contract ───────────────────────────────────────────────
def test_incident_schema_uses_project_picker_not_raw_text():
    src = (FE_ROOT / "lib/incidentReportSchema.js").read_text(encoding="utf-8")
    # Location step uses project_picker; reporter uses identity_confirm.
    assert 'type: "project_picker"' in src
    assert 'type: "identity_confirm"' in src
    assert 'type: "weather_auto"' in src
    # The prior plain-text job_number field is gone.
    assert 'key: "job_number", type: "text"' not in src


def test_incident_report_page_wires_autofill_helpers():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    assert "fetchDirectoryMe" in src
    assert "fetchProjectContext" in src
    assert "fetchWeather" in src
    # Field renderers exist.
    assert "ProjectPickerField" in src
    assert "IdentityConfirmField" in src
    assert "WeatherAutoField" in src
    # AutoMap plumbed through Review + StepPanel.
    assert "autoMap" in src


def test_incident_report_defaults_date_time_to_now():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    # Boot-time useEffect sets occurred_at_date + occurred_at_time.
    assert "occurred_at_date" in src
    assert "occurred_at_time" in src
    assert "new Date()" in src


def test_incident_report_review_shows_auto_vs_typed_counts():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    assert 'data-testid="incident-report-review-auto-count"' in src
    assert 'data-testid="incident-report-review-typed-count"' in src


def test_incident_report_project_picker_carries_manual_toggle():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    # Manual override for temporary / unlisted projects is available
    # but hidden behind an explicit toggle — no silent free-text field.
    assert "manual-toggle" in src


def test_incident_report_api_exports_batch_1_helpers():
    src = (FE_ROOT / "lib/incidentReportApi.js").read_text(encoding="utf-8")
    for fn in ("fetchDirectoryMe", "fetchProjectContext", "fetchWeather"):
        assert f"export async function {fn}" in src


# ── Header stability ────────────────────────────────────────────────
def test_form_shell_progress_band_is_below_header_row():
    """The ProgressRail is rendered in its OWN band below the header
    row — not inline with header actions. This kills layout jumps as
    the current step changes."""
    src = (FE_ROOT / "components/FormShell.jsx").read_text(encoding="utf-8")
    assert 'data-testid={`${containerTestId}-progress-band`}' in src
    # Header row has a fixed height so it never jumps.
    assert 'h-14' in src


def test_form_shell_still_renders_lang_toggle_and_draft_slot():
    """Header actions still include the language toggle + optional draft
    slot — the redesign is stability-only, not feature reduction."""
    src = (FE_ROOT / "components/FormShell.jsx").read_text(encoding="utf-8")
    assert "<LangToggle />" in src
    assert "{draftSlot}" in src


# ── Zero-Drift ──────────────────────────────────────────────────────
def test_batch1_did_not_mutate_phase_a_engine_or_reports():
    """Batch 1 must not have touched Phase A domain code or the reports
    engine — everything is additive."""
    reports_src = (REPO_ROOT / "backend/incident_engine/reports.py").read_text(
        encoding="utf-8")
    assert "fetch_current_weather" not in reports_src
    assert "project-context" not in reports_src


def test_incident_report_still_mounts_at_incidents_report():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert '<Route path="/incidents/report"' in txt
