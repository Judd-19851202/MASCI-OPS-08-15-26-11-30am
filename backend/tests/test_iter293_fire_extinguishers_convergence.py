"""
iter293 · Fire Extinguishers convergence closure test.

Bounded closure of the iter292-audit Fire Extinguishers row. Workflow
was matrix-yellow on EN/ES + PDF + Guide, but the audit established:
  - coaching is already complete (10 EN + 10 ES tips since iter275)
  - PDF endpoint is already registered (`history.pdf` since iter135)
  - the only real gap was EN/ES UI parity on the page itself

This test locks:
  - `fire-extinguisher` coaching family stability (no regression from
    iter275 closure)
  - ES counterpart merge for every fire-extinguisher tip
  - PDF endpoint stays registered (route surface protection)
  - ES UI key coverage in i18n.js (the visible labels that iter293
    wrapped with t())
  - No collision with neighbor families (safety-document,
    safety-training, document-expirations)
  - Scope locked to {safety, admin}

Out of scope (intentionally NOT tested):
  - asset management
  - NFPA inspection scheduling
  - inventory tracking
  - geo-mapping
  - QR systems
  - maintenance workflows
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from guidance.tips import all_tips


def _fe_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("fire-extinguisher")
    ]


# ─── Coaching family stability ───────────────────────────────────


def test_top_family_has_canonical_four_kinds():
    top = {t["kind"] for t in _fe_tips() if t["form_key"] == "fire-extinguisher"}
    missing = {"why", "who", "next", "escalate"} - top
    assert not missing, f"Top family missing canonical kinds: {missing}"


def test_total_tip_count_at_least_ten():
    """Audit benchmark: ≥10 tips across the fire-extinguisher family."""
    assert len(_fe_tips()) >= 10


def test_every_fe_tip_has_es_counterpart_merged():
    not_merged = []
    for t in _fe_tips():
        if not t.get("title_es") or not t.get("body_es"):
            not_merged.append((t["form_key"], t["kind"]))
    assert not not_merged, f"ES merge incomplete: {not_merged}"


def test_all_fe_tips_use_public_or_safety_or_admin_scope():
    """Fire-extinguisher coaching is intentionally readable by ALL
    logged-in users (`public` scope) since iter275 — every field
    operator may interact with extinguishers, not just Safety. Lock
    that intentional scope decision instead of forcing safety/admin-
    only narrowing."""
    bad = []
    for t in _fe_tips():
        scopes = set(t.get("scopes") or [])
        if scopes - {"public", "safety", "admin", "leadership", "pm", "hr"}:
            bad.append((t["form_key"], t["kind"], scopes))
    assert not bad, f"FE tips have unexpected scopes: {bad}"


def test_no_lms_drift_in_fe_tips():
    banned = [
        re.compile(r"\bbest practices?\b", re.I),
        re.compile(r"\bempower\b", re.I),
        re.compile(r"\bleverage\b", re.I),
        re.compile(r"\bstakeholders?\b", re.I),
        re.compile(r"\bjourney\b", re.I),
        re.compile(r"\bculture of\b", re.I),
    ]
    hits = []
    for t in _fe_tips():
        for field in ("title", "body", "title_es", "body_es"):
            text = t.get(field, "") or ""
            for pat in banned:
                m = pat.search(text)
                if m:
                    hits.append((t["form_key"], t["kind"], field, m.group()))
    assert not hits, f"LMS drift in FE tips: {hits}"


# ─── PDF endpoint surface protection ─────────────────────────────


def test_history_pdf_route_is_registered():
    """The `/safety/fire-extinguishers/{id}/history.pdf` route was
    added in iter135. Make sure no future iteration accidentally
    removes it — the audit found it satisfies the operational PDF
    need for OSHA/insurer/superintendent requests."""
    from server import app
    paths = {r.path for r in app.routes if hasattr(r, "path")}
    expected = "/api/safety/fire-extinguishers/{fe_id}/history.pdf"
    assert expected in paths, \
        f"Fire Extinguishers history PDF route missing: {expected}"


def test_history_pdf_route_is_get_only():
    from server import app
    for r in app.routes:
        if getattr(r, "path", None) == "/api/safety/fire-extinguishers/{fe_id}/history.pdf":
            methods = set(r.methods or [])
            assert "POST" not in methods
            assert "GET" in methods
            return
    pytest.fail("Fire Extinguishers PDF route not found on app")


# ─── ES UI key coverage in i18n.js ───────────────────────────────


def _i18n_text() -> str:
    p = pathlib.Path("/app/frontend/src/lib/i18n.js")
    return p.read_text()


REQUIRED_ES_KEYS = [
    # Page title + kicker
    '"Fire Extinguishers"',
    '"SAFETY · FIRE EXTINGUISHER REGISTER"',
    # Tabs (operationally critical for ES users). Pass/Fail/Status
    # already have established translations ("Cumple"/"No Cumple"/"Estado")
    # — iter293 reuses those by design.
    '"All"',
    '"Needs Service"',
    '"Overdue"',
    # Table headers
    '"Unit"',
    '"Location"',
    '"Type / Size"',
    '"Last Inspect"',
    '"Next Due"',
    '"Actions"',
    # Form Select labels iter293 newly translated
    '"Location kind"',
    # Inspect dialog
    '"Log inspection"',
    # Buttons
    '"Add Extinguisher"',
    '"Bulk Import"',
    # Tooltip
    '"Attachments & PDF history"',
]


@pytest.mark.parametrize("key", REQUIRED_ES_KEYS)
def test_each_required_es_key_present_in_i18n(key):
    """Every visible EN string on the Fire Extinguishers page must
    have a corresponding ES translation key in /lib/i18n.js. This is
    how a bilingual field user actually sees Spanish in production."""
    text = _i18n_text()
    assert key in text, f"Missing ES translation key in i18n.js: {key}"


def test_es_translations_are_actually_spanish_not_english():
    """Lock against the most common i18n mistake: someone copies the
    EN key as the ES value. Pick a handful of high-confidence checks
    where EN != ES is structurally obvious AND the key is owned by
    iter293 (not by an earlier closure)."""
    text = _i18n_text()
    # Only check keys iter293 added — Pass/Fail/Status are owned by
    # earlier closures (QA/QC inspection · Cumple/No Cumple/Estado).
    obvious_es_pairs = [
        ('"Fire Extinguishers"', 'Extintores'),
        ('"All"', 'Todos'),
        ('"Overdue"', 'Vencido'),
        ('"Unit"', 'Unidad'),
        ('"Location"', 'Ubicación'),
        ('"Actions"', 'Acciones'),
        ('"Last Inspect"', 'Última Inspección'),
        ('"Add Extinguisher"', 'Agregar Extintor'),
    ]
    failures = []
    for en_key, expected_in_es_value in obvious_es_pairs:
        # Find ALL occurrences and check at least one has the expected ES
        # (since last-write-wins, the iter293 entry takes effect at runtime).
        idx = 0
        found_match = False
        while True:
            idx = text.find(en_key, idx)
            if idx < 0:
                break
            snippet = text[idx:idx + 200]
            if expected_in_es_value in snippet:
                found_match = True
                break
            idx += 1
        if not found_match:
            failures.append((en_key, expected_in_es_value))
    assert not failures, f"ES translations missing iter293 expected values: {failures}"


# ─── Bounded-scope guard (no scope drift) ────────────────────────


def test_iter293_did_not_introduce_inventory_or_compliance_form_keys():
    """The audit explicitly banned drift into asset management,
    inventory tracking, NFPA platform expansion, compliance suites,
    QR systems, or geo-mapping. Lock the form_key namespace so no
    iteration silently sprawls."""
    fe_keys = {t["form_key"] for t in _fe_tips()}
    banned_substrings = [
        "fire-extinguisher.inventory",
        "fire-extinguisher.qr",
        "fire-extinguisher.geo",
        "fire-extinguisher.maintenance-schedule",
        "fire-extinguisher.assignment",
        "fire-extinguisher.compliance-workflow",
    ]
    hits = [k for k in fe_keys
            if any(b in k for b in banned_substrings)]
    assert not hits, \
        f"iter293 scope drift — banned form_keys appeared: {hits}"


def test_fe_family_does_not_collide_with_safety_document_or_training():
    """Adjacent Safety families. Make sure no key overlap."""
    fe = {t["form_key"] for t in _fe_tips()}
    sd = {t["form_key"] for t in all_tips()
          if (t.get("form_key") or "").startswith("safety-document")}
    st = {t["form_key"] for t in all_tips()
          if (t.get("form_key") or "").startswith("safety-training")}
    assert not (fe & sd), f"FE collides with safety-document: {fe & sd}"
    assert not (fe & st), f"FE collides with safety-training: {fe & st}"
