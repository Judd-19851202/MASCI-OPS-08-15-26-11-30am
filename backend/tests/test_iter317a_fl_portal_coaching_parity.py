"""
iter317-A · Field Leadership Portal coaching parity.

Locks the convergence iter317-A delivered:
  • 5 coaching families:
       field-leadership.portal-login (canonical 4)
       field-leadership.portal-dashboard (canonical 4)
       field-leadership.change-password (why/mistake/next)
       field-leadership.user-management (canonical 4 · HR/Admin)
       field-leadership.dispatch-visibility (why/next/escalate)
  • Bilingual parity — every EN tip has its ES title+body
  • HelpTipBlock mounts on 5 frontend surfaces:
       FieldLeadershipPortalLogin / Dashboard / ChangePassword
       AdminFieldLeadershipUsersPanel / HrFieldLeadershipUsers
  • No drift into the legacy `field-leadership.records` (HR write-ups)
    coaching family; the new families share the `field-leadership`
    namespace but never collide with the records sub-families.

Static-code invariants only — no live preview state is mutated. The
audit_file lives at /app/memory/iter317_coaching_guidance_parity_audit.md
and is referenced here for traceability but not parsed.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TIPS_EN = REPO_ROOT / "backend/guidance/tips.py"
TIPS_ES = REPO_ROOT / "backend/guidance/tips_es.py"
FL_LOGIN = REPO_ROOT / "frontend/src/pages/FieldLeadershipPortalLogin.jsx"
FL_DASH = REPO_ROOT / "frontend/src/pages/FieldLeadershipPortalDashboard.jsx"
FL_CPW = REPO_ROOT / "frontend/src/pages/FieldLeadershipPortalChangePassword.jsx"
HR_FL_USERS = REPO_ROOT / "frontend/src/pages/HrFieldLeadershipUsers.jsx"
ADMIN_FL_PANEL = REPO_ROOT / "frontend/src/components/AdminFieldLeadershipUsersPanel.jsx"

EXPECTED_FAMILIES = {
    "field-leadership.portal-login":        {"why", "mistake", "next", "escalate"},
    "field-leadership.portal-dashboard":    {"why", "mistake", "next", "escalate"},
    "field-leadership.change-password":     {"why", "mistake", "next"},
    "field-leadership.user-management":     {"why", "mistake", "next", "escalate"},
    "field-leadership.dispatch-visibility": {"why", "next", "escalate"},
}
TOTAL_EXPECTED_TIPS = sum(len(v) for v in EXPECTED_FAMILIES.values())  # 18


def _load_en_tips():
    """Load all EN tips by importing the merge function directly.
    Returns list[dict] with form_key + kind keys."""
    import sys
    backend_dir = str(REPO_ROOT / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from guidance.tips import all_tips
    return all_tips()


# ---------------------------------------------------------------------------
# Coaching family invariants.
# ---------------------------------------------------------------------------


def test_iter317a_all_five_families_present_with_expected_kinds():
    tips = _load_en_tips()
    by_family: dict = {}
    for t in tips:
        by_family.setdefault(t["form_key"], set()).add(t["kind"])
    for fk, expected_kinds in EXPECTED_FAMILIES.items():
        assert fk in by_family, f"missing iter317-A family: {fk}"
        assert by_family[fk] == expected_kinds, (
            f"{fk}: expected kinds {sorted(expected_kinds)}, "
            f"got {sorted(by_family[fk])}"
        )


def test_iter317a_total_tip_count_is_eighteen():
    tips = _load_en_tips()
    total = sum(1 for t in tips if t["form_key"] in EXPECTED_FAMILIES)
    assert total == TOTAL_EXPECTED_TIPS, (
        f"expected {TOTAL_EXPECTED_TIPS} iter317-A tips, got {total}"
    )


def test_iter317a_bilingual_parity_every_tip_has_es():
    tips = _load_en_tips()
    missing = []
    for t in tips:
        if t["form_key"] not in EXPECTED_FAMILIES:
            continue
        title_es = (t.get("title_es") or "").strip()
        body_es = (t.get("body_es") or "").strip()
        if not (title_es and body_es):
            missing.append((t["form_key"], t["kind"]))
    assert not missing, f"iter317-A tips missing ES translation: {missing}"


def test_iter317a_tips_carry_operational_scopes():
    """Each family must restrict to operationally-appropriate roles.
    portal-login / change-password include leadership + hr + admin
    (anyone resetting / signing in could be any of the three);
    portal-dashboard / dispatch-visibility are leadership-only;
    user-management is hr + admin only."""
    tips = _load_en_tips()
    expectations = {
        "field-leadership.portal-login":        {"leadership", "hr", "admin"},
        "field-leadership.portal-dashboard":    {"leadership"},
        "field-leadership.change-password":     {"leadership", "hr", "admin"},
        "field-leadership.user-management":     {"hr", "admin"},
        "field-leadership.dispatch-visibility": {"leadership"},
    }
    for t in tips:
        fk = t["form_key"]
        if fk not in expectations:
            continue
        scopes = set(t.get("scopes") or [])
        assert scopes == expectations[fk], (
            f"{fk}/{t['kind']} has scopes {sorted(scopes)}; "
            f"expected {sorted(expectations[fk])}"
        )


# ---------------------------------------------------------------------------
# Frontend mount invariants — lock the HelpTipBlock placements.
# ---------------------------------------------------------------------------


def test_iter317a_portal_login_mounts_coaching():
    src = FL_LOGIN.read_text()
    assert 'import { HelpTipBlock }' in src or "HelpTipBlock" in src
    assert 'formKey="field-leadership.portal-login"' in src


def test_iter317a_portal_dashboard_mounts_coaching():
    src = FL_DASH.read_text()
    assert 'formKey="field-leadership.portal-dashboard"' in src
    # Dispatch-visibility coaching mounts at the dispatch card.
    assert 'formKey="field-leadership.dispatch-visibility"' in src


def test_iter317a_change_password_mounts_coaching():
    src = FL_CPW.read_text()
    assert 'formKey="field-leadership.change-password"' in src


def test_iter317a_admin_panel_mounts_coaching():
    src = ADMIN_FL_PANEL.read_text()
    assert 'formKey="field-leadership.user-management"' in src


def test_iter317a_hr_host_page_mounts_coaching():
    src = HR_FL_USERS.read_text()
    assert 'formKey="field-leadership.user-management"' in src


# ---------------------------------------------------------------------------
# Voice / tone discipline — guard against LMS/corporate drift.
# ---------------------------------------------------------------------------


BANNED_PHRASES = (
    "best practices",
    "empower",
    "journey",
    "stakeholders",
    "culture of",
    "training module",
    "learning experience",
    "certification path",
    "compliance posture",
)


def test_iter317a_no_lms_or_corporate_drift_in_tips():
    """Operator-mandate tone discipline — the new tips must not drift
    into LMS / corporate-training / compliance-suite language."""
    tips = _load_en_tips()
    hits = []
    for t in tips:
        if t["form_key"] not in EXPECTED_FAMILIES:
            continue
        body_lower = (t.get("body") or "").lower()
        title_lower = (t.get("title") or "").lower()
        for banned in BANNED_PHRASES:
            if banned in body_lower or banned in title_lower:
                hits.append((t["form_key"], t["kind"], banned))
    assert not hits, (
        f"iter317-A tips contain banned corporate/LMS phrasing: {hits}"
    )


# ---------------------------------------------------------------------------
# Legacy isolation — new portal coaching must not conflate with the
# legacy `field-leadership.records` (HR write-ups) family or the legacy
# shared-password gate URL.
# ---------------------------------------------------------------------------


def test_iter317a_does_not_redefine_legacy_records_family():
    """The 5 new families share the `field-leadership.*` namespace but
    must NEVER collide with the existing iter218 `field-leadership.records`
    sub-families."""
    tips = _load_en_tips()
    legacy_subfamilies = {
        "field-leadership.records",
        "field-leadership.records.review-tone",
        "field-leadership.records.follow-through",
        "field-leadership.records.documentation-discipline",
    }
    counts = {fk: 0 for fk in legacy_subfamilies}
    for t in tips:
        if t["form_key"] in legacy_subfamilies:
            counts[t["form_key"]] += 1
    # All four legacy sub-families must still be present and intact.
    assert counts["field-leadership.records"] >= 4, (
        "legacy field-leadership.records family must remain (>=4 tips)"
    )
    assert counts["field-leadership.records.review-tone"] >= 2
    assert counts["field-leadership.records.follow-through"] >= 2
    assert counts["field-leadership.records.documentation-discipline"] >= 2


def test_iter317a_portal_login_tips_distinguish_from_legacy_gate():
    """Portal-login coaching must reference the legacy shared-password
    gate URL so users at the wrong door get redirected — the explicit
    distinction is the whole point of the family."""
    tips = _load_en_tips()
    bodies = " ".join(
        (t.get("body") or "")
        for t in tips
        if t["form_key"] == "field-leadership.portal-login"
    )
    # The legacy gate path is mentioned at least once in the family.
    assert "/field-leadership/login" in bodies, (
        "portal-login tips must mention the legacy `/field-leadership/login` "
        "gate so users at the wrong door understand the distinction"
    )


# ---------------------------------------------------------------------------
# Companion file existence — audit doc + tips file structure.
# ---------------------------------------------------------------------------


def test_iter317a_audit_document_exists():
    audit = REPO_ROOT / "memory/iter317_coaching_guidance_parity_audit.md"
    assert audit.exists(), (
        "iter317-A audit deliverable must remain in /app/memory/ as the "
        "evidence trail for the closure sequence"
    )


def test_iter317a_tips_file_carries_iter317a_block_marker():
    """Future maintainers should be able to grep `iter317-A` to find
    the block. Lock a single marker comment so the block is locatable."""
    src = TIPS_EN.read_text()
    assert "iter317-A" in src, "tips.py must keep the iter317-A block marker"
    src_es = TIPS_ES.read_text()
    assert "iter317-A" in src_es, "tips_es.py must keep the iter317-A block marker"


def test_iter317a_es_translations_anchored_to_family_keys():
    """Every iter317-A (form_key, kind) tuple must appear as a key in
    tips_es.py so the merge logic can find its translation."""
    es_src = TIPS_ES.read_text()
    for fk, kinds in EXPECTED_FAMILIES.items():
        for kind in kinds:
            anchor = f'("{fk}", "{kind}")'
            assert anchor in es_src, (
                f"tips_es.py missing translation anchor {anchor}"
            )
            # Each anchor must also carry a non-empty title_es + body_es
            # right after it (sanity check that translation is filled in,
            # not just stubbed).
            # Find the surrounding dict and confirm both keys are present.
            idx = es_src.index(anchor)
            window = es_src[idx: idx + 1200]
            assert '"title_es":' in window
            assert '"body_es":' in window
            assert re.search(r'"title_es":\s*"[^"]+"', window), (
                f"{anchor} title_es appears empty"
            )
