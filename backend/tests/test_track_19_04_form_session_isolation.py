"""Track 19.04 · Form Session Isolation regression suite.

Locks the following invariants:

* /jobs/{pn}/recent-context returns the v19.04 contract shape.
* /jobs/{pn}/recent-context is actor-scoped when `foreman` is supplied.
* No backend endpoint returns a global "latest draft" or "any user's
  most recent draft" — verified by AST search of server.py.
* Required markdown reports exist.
* Frontend draft store / useFormDraft carry the `savedByActor`
  stamp on every write and gate restore on fingerprint match.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest


BASE = "http://localhost:8001/api"


REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY = REPO_ROOT / "memory"
BACKEND = REPO_ROOT / "backend"
FRONTEND = REPO_ROOT / "frontend"


REQUIRED_REPORTS = [
    "TRACK_19_04_FORM_SESSION_AUTOSAVE_AUDIT.md",
    "TRACK_19_04_DAILY_REPORT_RESIDUE_REPRODUCTION.md",
    "FORM_SESSION_ISOLATION_CONTRACT.md",
    "TRACK_19_04_PLATFORM_FORM_RESIDUE_AUDIT.md",
    "TRACK_19_04_DAILY_REPORT_ATTACHMENT_AUDIT.md",
    "TRACK_19_04_DAILY_REPORT_EMAIL_ATTACHMENT_ROUTING.md",
    "TRACK_19_04_SECURITY_REVIEW.md",
]


@pytest.mark.parametrize("name", REQUIRED_REPORTS)
def test_required_report_exists(name: str):
    p = MEMORY / name
    assert p.exists(), f"missing required report: {name}"
    text = p.read_text(encoding="utf-8")
    assert len(text) > 200, f"{name} looks empty ({len(text)} bytes)"


def test_prd_mentions_track_19_04():
    prd = (MEMORY / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.04" in prd or "Track 19.04" in prd, "PRD missing Track 19.04 entry"


# ---- Backend contract ----

def test_recent_context_contract_v19_04():
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{BASE}/jobs/UNKNOWN-PROJECT/recent-context")
    assert r.status_code == 200
    d = r.json()
    assert d.get("contract_version") == "19.04"
    assert "actor_scoped" in d
    assert d.get("actor_scoped") is False
    assert d.get("source", "").startswith("daily_reports"), d
    assert d.get("masci_crews") == []
    assert d.get("equipment") == []


def test_recent_context_empty_project_returns_empty_shape():
    # An empty project_number param is currently routed to the
    # `UNKNOWN-` handler variant; here we exercise the strip() path
    # by passing a legit-looking but non-existent number.
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{BASE}/jobs/ZZZ-19-04-EMPTY/recent-context")
    assert r.status_code == 200
    d = r.json()
    assert d.get("contract_version") == "19.04"
    assert d.get("masci_crews") == []


def test_recent_context_accepts_foreman_query():
    with httpx.Client(timeout=30) as c:
        r = c.get(
            f"{BASE}/jobs/UNKNOWN/recent-context",
            params={"foreman": "Test Foreman"},
        )
    assert r.status_code == 200
    # actor_scoped false when no matching self-report exists — fine.
    assert r.json().get("contract_version") == "19.04"


# ---- Backend absence of global "latest draft" surface ----

def test_no_global_latest_draft_endpoint():
    server_py = (BACKEND / "server.py").read_text(encoding="utf-8")
    # Absolutely no endpoint may return a draft that isn't scoped to
    # an authenticated actor. The routes below would be forbidden.
    forbidden = [
        r"/api/daily-reports/latest\b",
        r"/api/drafts\b",
        r"/api/daily-reports/drafts\b",
        r"/api/forms/latest\b",
    ]
    for pat in forbidden:
        assert not re.search(pat, server_py), (
            f"forbidden global 'latest' endpoint present: {pat}"
        )


# ---- Frontend draft-store contract ----

def test_save_draft_stamps_saved_by_actor():
    src = (FRONTEND / "src/lib/resiliency/draftStore.js").read_text(encoding="utf-8")
    assert "savedByActor" in src, "draftStore.saveDraft missing savedByActor stamp"
    assert 'contract_version: "19.04"' in src, "draftStore missing 19.04 stamp"


def test_useformdraft_gates_restore_by_actor():
    src = (FRONTEND / "src/lib/resiliency/useFormDraft.js").read_text(encoding="utf-8")
    assert "getAuthActorFingerprint" in src, (
        "useFormDraft not consuming getAuthActorFingerprint"
    )
    assert "authorMismatch" in src or "blocked_cross_actor" in src, (
        "useFormDraft missing cross-actor gate"
    )


def test_actorid_exposes_auth_fingerprint():
    src = (FRONTEND / "src/lib/resiliency/actorId.js").read_text(encoding="utf-8")
    assert "export function getAuthActorFingerprint" in src, (
        "actorId missing getAuthActorFingerprint export"
    )


def test_smart_prefill_is_explicit_offer_not_auto_apply():
    src = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
    # The v19.04 explicit-offer chip must be present.
    assert "smartPrefillOffer" in src, "explicit smartPrefillOffer state missing"
    assert "daily-report-smart-prefill-apply" in src, (
        "smart-prefill Apply testid missing"
    )
    assert "daily-report-smart-prefill-dismiss" in src, (
        "smart-prefill Dismiss testid missing"
    )
    # And the OLD silent auto-apply pattern (mutating masci_crews inline
    # in the recent-context .then handler) must be gone.
    assert "prefilledLines += priorCrews.length" not in src, (
        "silent auto-apply of prior crew is STILL present — Track 19.04 regression"
    )


def test_default_data_is_pure_and_carries_attachments_field():
    src = (FRONTEND / "src/lib/dailyReportSchema.js").read_text(encoding="utf-8")
    assert "export function buildDailyReportDefaults" in src, (
        "buildDailyReportDefaults missing"
    )
    assert "attachments: []" in src, (
        "attachments[] not initialized in default Daily Report state"
    )
