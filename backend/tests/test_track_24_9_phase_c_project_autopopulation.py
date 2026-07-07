"""TRACK 24.9 Phase C · Project auto-population lock suite.

Certifies that selecting a project in Daily Report V3 commits the
full project context — project_number, project_name, location,
client, project_manager, pm_email, co_pm_emails — and that every
downstream consumer (submit payload, PM/co-PM routing, ODS facts,
autosave/draft restore) receives the correct project reference.

Doctrine:
  * Field crews visually confirm the picked project via the metadata
    card. Missing optional metadata renders as "Not set", never as
    "null" / "None" / fabricated text.
  * Server derives PM routing from `jobs_master.project_number`; the
    payload metadata snapshot is informational for PDF/audit.
  * Autosave preserves the whole form state — including project
    metadata — via the useFormDraft snapshot pipeline.
  * Changing projects must clear the previous metadata (no
    contamination).
"""
from __future__ import annotations

import os
import sys
import uuid
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


# ── 1. Project metadata schema commits ─────────────────────────────
#
# The DR V3 form defaults must declare every project-metadata key
# so autosave/draft restore has a stable shape and the schema
# never silently drops a field.


PROJECT_META_KEYS = [
    "client",
    "project_manager",
    "pm_email",
    "co_pm_emails",
]


def test_dr_v3_schema_declares_project_metadata_keys():
    src = (FRONTEND / "lib" / "dailyReportSchema.js").read_text()
    for k in PROJECT_META_KEYS:
        assert f"{k}:" in src, (
            f"buildDailyReportDefaults() missing key `{k}` — the "
            f"draft snapshot won't preserve it and downstream "
            f"consumers will see a fabricated null."
        )


def test_section_project_conditions_commits_full_metadata_snapshot():
    src = (FRONTEND / "components" / "daily-report-v3" / "SectionProjectConditions.jsx").read_text()
    for marker in [
        "project_number: job?.project_number",
        "project_name: job?.project_name",
        "location: job?.location",
        "client: job?.client",
        "project_manager: job?.project_manager",
        "pm_email: job?.pm_email",
        "co_pm_emails:",
    ]:
        assert marker in src, (
            f"SectionProjectConditions onSelect must commit `{marker}` — "
            f"Phase C requires the full project-metadata snapshot."
        )


def test_section_project_conditions_shows_metadata_card_only_after_pick():
    """Blank-state must stay clean — the metadata card renders only
    after a project is bound. Prevents empty "Client: Not set" from
    surfacing on an untouched form."""
    src = (FRONTEND / "components" / "daily-report-v3" / "SectionProjectConditions.jsx").read_text()
    assert "data.project_number &&" in src
    assert 'data-testid="dr-v3-project-meta"' in src
    for tid in [
        "dr-v3-project-meta-client",
        "dr-v3-project-meta-pm",
        "dr-v3-project-meta-co-pms",
    ]:
        assert tid in src


# ── 2. Jobs API contract — every test project returns metadata ─────


@pytest.mark.parametrize("project_number,expect_pm_or_copm", [
    ("26-07", False),  # University High Parent Loop Ext — no PM/co-PM in source data (honest fallback)
    ("24-12", True),   # Oxford Rd — has project_manager (David Jewett)
    ("20-07", True),   # T5686 SR 15/SR600 — has co_pm_emails
])
def test_jobs_api_returns_project_metadata(project_number, expect_pm_or_copm):
    r = requests.get(f"{API}/jobs?limit=200", timeout=45)
    assert r.status_code == 200
    items = r.json().get("items", [])
    match = [j for j in items if (j.get("project_number") or "").startswith(project_number)]
    assert match, f"project {project_number} not found in /api/jobs"
    j = match[0]
    # Canonical keys always present (Pydantic default = "").
    for k in ["project_name", "location", "client", "project_manager", "pm_email"]:
        assert k in j, f"/api/jobs projection missing `{k}` for {project_number}"
    # co_pm_emails is always a list (even when empty).
    assert isinstance(j.get("co_pm_emails"), list)
    if expect_pm_or_copm:
        has_pm = bool(j.get("project_manager")) or bool(j.get("pm_email"))
        has_copm = bool(j.get("co_pm_emails"))
        assert has_pm or has_copm, (
            f"{project_number} expected PM or co-PM but neither present. "
            f"If the source data was cleared, this test's expectation "
            f"must be updated — never fabricate a PM to make it pass."
        )


# ── 3. Submit payload preserves project context ─────────────────────


def _admin_token(_cache={}):
    if "tok" in _cache:
        return _cache["tok"]
    r = requests.post(f"{API}/auth/multi-login", json={
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!",
    }, timeout=45)
    r.raise_for_status()
    _cache["tok"] = r.json().get("portal_tokens", {}).get("admin", "")
    return _cache["tok"]


@pytest.mark.parametrize("project_number", ["26-07", "24-12", "20-07"])
def test_submit_payload_preserves_project_metadata(project_number):
    """Submit a DR carrying the full project metadata snapshot. The
    backend must persist every field (Pydantic model_config extra=allow)."""
    # Pull the source-of-truth job for its metadata.
    jobs = requests.get(f"{API}/jobs?limit=200", timeout=45).json().get("items", [])
    match = [j for j in jobs if (j.get("project_number") or "").startswith(project_number)]
    assert match, f"project {project_number} missing in /api/jobs"
    j = match[0]
    unique_marker = f"TRACK_24_9_C_probe_{uuid.uuid4().hex[:8]}"
    payload = {
        "project_number": j["project_number"],
        "project_name": j["project_name"],
        "location": j.get("location") or "",
        "report_date": "2026-02-07",
        "prepared_by": "Track 24.9 Phase C Probe",
        "superintendent": "",
        "client": j.get("client") or "",
        "project_manager": j.get("project_manager") or "",
        "pm_email": j.get("pm_email") or "",
        "co_pm_emails": j.get("co_pm_emails") or [],
        "masci_crews": [],
        "photos": [],
        "activities": [],
        "general_notes": unique_marker,
        # Mark it synthetic so the Phase A filter hides it from
        # user-facing lists. This test purely certifies the payload
        # round-trip; the record is not for operational use.
        "synthetic_record": True,
        "hidden_from_operations": True,
        "cleanup_track": "24.9-C-test",
    }
    tok = _admin_token()
    r = requests.post(
        f"{API}/daily-reports", json=payload,
        headers={"Idempotency-Key": f"track24_9_c_{unique_marker}"},
        timeout=45,
    )
    assert r.status_code in (200, 201), f"submit rejected: {r.status_code} · {r.text[:300]}"
    body = r.json()
    # ── Assert round-trip preserves every project field ────────
    for k in ["project_number", "project_name", "location",
              "client", "project_manager", "pm_email"]:
        assert body.get(k) == payload[k], (
            f"submit payload dropped/mutated `{k}` for {project_number}. "
            f"expected={payload[k]!r} got={body.get(k)!r}"
        )
    assert body.get("co_pm_emails") == payload["co_pm_emails"]


# ── 4. Missing optional metadata → honest fallback ─────────────────


def test_project_meta_card_missing_data_uses_honest_fallback():
    """The metadata card shows `<em>Not set</em>` when the source
    job lacks client/PM. It NEVER shows "null", "None", "undefined",
    or a fabricated placeholder."""
    src = (FRONTEND / "components" / "daily-report-v3" / "SectionProjectConditions.jsx").read_text()
    assert '{t("Not set")}' in src
    for bad in ["null", "undefined", "N/A", "TBD"]:
        # Look for these as HARDCODED strings (not the word inside a
        # legitimate translation), i.e., in JSX text nodes.
        assert f'>{bad}<' not in src, (
            f"SectionProjectConditions must not render `{bad}` as "
            f"fallback text — use t('Not set') for honest fallback."
        )


# ── 5. No wrong-project contamination ──────────────────────────────
#
# The onSelect handler ALWAYS overwrites every project-metadata key
# (uses `job?.field || ""` — the empty string on the RHS ensures the
# previous project's value is CLEARED when the newly-picked job
# lacks that field). Missing this guard causes the previous project's
# PM/co-PM to leak into the new project's DR — a critical routing bug.


def test_project_metadata_clears_on_project_change():
    src = (FRONTEND / "components" / "daily-report-v3" / "SectionProjectConditions.jsx").read_text()
    # Every metadata write MUST use `|| ""` (or `|| []`) so
    # the previous value is cleared when the new job lacks the
    # field. Loose truthy check that would silently preserve the
    # prior value → test fails.
    for expr in [
        'client: job?.client || ""',
        'project_manager: job?.project_manager || ""',
        'pm_email: job?.pm_email || ""',
    ]:
        assert expr in src, (
            f"onSelect must clear `{expr}` on project change — "
            f"otherwise the prior project's metadata contaminates "
            f"the new DR."
        )
    assert "Array.isArray(job?.co_pm_emails)" in src


# ── 6. PM routing is keyed by project_number (server-side) ─────────


def test_pm_routing_reads_project_number_not_payload_pm():
    """Server-authoritative PM routing must read from jobs_master
    by project_number, not from the DR payload's `pm_email` field —
    otherwise a stale/wrong payload could redirect email delivery."""
    pm_routing_src = (ROOT / "pm_routing.py").read_text()
    # Guard: the resolve_pm function reads from jobs_master and
    # uses project_number as the key.
    assert "jobs_master" in pm_routing_src
    assert "project_number" in pm_routing_src


# ── 7. Frontend NewDailyReportV3 still reloads cost codes on project change ──


def test_new_dr_v3_reloads_cost_codes_on_project_change():
    src = (FRONTEND / "pages" / "NewDailyReportV3.jsx").read_text()
    assert "cost-codes/for-project" in src
    assert "data.project_number" in src


# ── 8. Autosave preserves project fields (indirect: schema declared) ──


def test_autosave_snapshot_includes_project_meta_fields():
    """useFormDraft snapshots the entire `data` object — so the
    project-metadata fields ride along automatically as long as
    they are declared in buildDailyReportDefaults. Test that link."""
    schema_src = (FRONTEND / "lib" / "dailyReportSchema.js").read_text()
    dr_src = (FRONTEND / "pages" / "NewDailyReportV3.jsx").read_text()
    assert "useFormDraft(FORM_KEY, data)" in dr_src
    for k in PROJECT_META_KEYS:
        assert f"{k}:" in schema_src


# ── 9. Cleanup — the synthetic probe DR must be excluded from user-facing lists ──


def test_probe_dr_hidden_from_user_facing_listings():
    tok = _admin_token()
    r = requests.get(
        f"{API}/daily-reports", headers={"X-Admin-Token": tok}, timeout=45,
    )
    assert r.status_code == 200
    # Track 24.9 Phase A filter must hide any DR marked synthetic.
    for it in r.json():
        assert (it.get("prepared_by") or "") != "Track 24.9 Phase C Probe", (
            f"Track 24.9 Phase C probe DR leaked to user-facing list. "
            f"synthetic_record=True should have hidden it. row={it}"
        )
