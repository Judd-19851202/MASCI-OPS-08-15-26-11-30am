"""
iter295 · Fleet Visibility convergence closure test.

Bounded closure of the iter294-audit Fleet Visibility row. Audit
finding: every yellow marker was actually stale — the ES translations
were already in `i18n.js`, the coaching family already carried all 4
canonical kinds, the regression suite already had 87 tests, and the
desktop/tablet density was intentional.

iter295 ships ZERO code on the Fleet Visibility surface itself. The
work is governance-truth alignment: matrix amendments + this
defensive regression test that LOCKS the bilingual state so it can
never silently regress.

What this test locks:
  - Every Fleet Visibility status label has an ES translation entry
    in i18n.js
  - Every Fleet defect-status / audit-trail label has an ES entry
  - `fleet.*` coaching family stays intact (no namespace drift)
  - Fleet PDF surface stays scoped to the severity-reference-card
    (no accidental expansion into defect-history/repair-lifecycle
    PDF endpoints during future iterations)
  - No drift into banned fleet-platform namespaces (telematics, gps,
    inventory, maintenance-schedule, dispatch-automation,
    fuel-tracking, mechanic-workflow)
"""
import sys
import pathlib
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from guidance.tips import all_tips


def _i18n_text() -> str:
    return pathlib.Path("/app/frontend/src/lib/i18n.js").read_text()


# Strings rendered by Fleet Visibility components verified against the
# actual source: StatusPill · SeverityBadge · DefectStatusPill ·
# AuditTrailPanel · AuditExpand.
FLEET_ES_REQUIRED_KEYS = [
    # StatusPill (truck-level status)
    "Available",
    "Repair Required",
    "Out of Service",
    "Repair In Progress",
    "Returned to Service",
    "Unknown",
    # SeverityBadge
    "Monitor",
    # DefectStatusPill (defect-level)
    "Shop acknowledged",
    "Awaiting RTS",
    "Returned to service",
    # AuditTrailPanel
    "Loading audit trail…",
    "No audit events yet.",
    "Driver submitted",
    "Shop marked repaired",
    "Dispatch returned to service",
    "Manual OOS by Dispatch",
    # AuditExpand toggle
    "View audit trail",
    "Hide audit trail",
]


@pytest.mark.parametrize("key", FLEET_ES_REQUIRED_KEYS)
def test_each_fleet_visibility_key_has_es_translation(key):
    """Every visible label in Fleet Visibility status/badge/audit
    components must have an ES entry in i18n.js. Audit-discovered
    reality (iter294): all 18 were already present. This test locks
    that state."""
    text = _i18n_text()
    needle = f'"{key}":'
    assert needle in text, f"Fleet Visibility key missing ES entry: {key}"


def test_es_translations_render_as_spanish_not_english():
    """High-confidence pairs where EN != ES is structurally obvious.
    Lock against the common drift of an iteration copying the EN key
    as the ES value."""
    text = _i18n_text()
    pairs = [
        ('"Available"', 'Disponible'),
        ('"Repair Required"', 'Reparación Requerida'),
        ('"Out of Service"', 'Fuera de Servicio'),
        ('"Repair In Progress"', 'Reparación en Progreso'),
        ('"Returned to Service"', 'Regresado al Servicio'),
        ('"Unknown"', 'Desconocido'),
        ('"Awaiting RTS"', 'Esperando RTS'),
        ('"View audit trail"', 'Ver registro de auditoría'),
        ('"Hide audit trail"', 'Ocultar registro de auditoría'),
        ('"Loading audit trail…"', 'Cargando registro de auditoría…'),
        ('"Driver submitted"', 'Conductor envió'),
        ('"Shop marked repaired"', 'Taller marcó como reparado'),
        ('"Dispatch returned to service"', 'Despacho regresó al servicio'),
    ]
    failures = []
    for en_key, expected_es in pairs:
        idx = 0
        found_match = False
        while True:
            idx = text.find(en_key, idx)
            if idx < 0:
                break
            snippet = text[idx:idx + 200]
            if expected_es in snippet:
                found_match = True
                break
            idx += 1
        if not found_match:
            failures.append((en_key, expected_es))
    assert not failures, f"Fleet ES translations missing expected values: {failures}"


# ─── Fleet coaching family stability ─────────────────────────────


def _fleet_tips():
    return [
        t for t in all_tips()
        if (t.get("form_key") or "").startswith("fleet")
    ]


def test_fleet_coaching_family_carries_canonical_four_kinds():
    """iter274/iter276 closed the 4-Kinds gap. Lock the canonical
    coverage at the family-aggregate level so future iterations
    can't silently regress the escalate tip."""
    kinds_present = {t["kind"] for t in _fleet_tips()}
    missing = {"why", "who", "next", "escalate"} - kinds_present
    assert not missing, f"Fleet family aggregate missing kinds: {missing}"


def test_fleet_form_keys_remain_within_known_namespace():
    """Lock the fleet.* form_key shape. Audit (iter294) banned drift
    into telematics / gps / inventory / maintenance-schedule /
    dispatch-automation / fuel-tracking / mechanic-workflow. This
    test fails if any of those namespaces silently appears."""
    fleet_keys = {t["form_key"] for t in _fleet_tips()}
    banned_substrings = [
        "fleet.telematics",
        "fleet.gps",
        "fleet.inventory",
        "fleet.maintenance-schedule",
        "fleet.dispatch-automation",
        "fleet.fuel-tracking",
        "fleet.mechanic-workflow",
        "fleet.assignment",
        "fleet.scheduling",
    ]
    hits = [k for k in fleet_keys
            if any(b in k for b in banned_substrings)]
    assert not hits, \
        f"iter295/future scope drift — banned fleet form_keys appeared: {hits}"


def test_fleet_tip_count_at_least_ten():
    """Audit benchmark for a mature umbrella."""
    assert len(_fleet_tips()) >= 10


# ─── Fleet PDF surface protection ────────────────────────────────


def test_only_severity_reference_card_pdf_is_registered():
    """iter294 audit conclusion: the live audit trail panel already
    satisfies operational evidence needs. The only Fleet PDF that
    exists is the severity reference card (admin printable). This
    test fails if a future iteration silently adds defect-history,
    repair-lifecycle, or OOS-log PDF endpoints without a fresh
    audit that classifies the operational need."""
    from server import app
    fleet_pdf_paths = {
        r.path for r in app.routes
        if hasattr(r, "path")
        and "fleet" in (r.path or "")
        and r.path.endswith(".pdf")
    }
    expected = {"/api/admin/fleet/severity-reference-card.pdf"}
    extra = fleet_pdf_paths - expected
    assert not extra, \
        f"Unaudited Fleet PDF endpoint(s) appeared — re-audit before shipping: {extra}"
    assert "/api/admin/fleet/severity-reference-card.pdf" in fleet_pdf_paths, \
        "Severity reference card PDF route missing"


# ─── No-collision guards ─────────────────────────────────────────


def test_fleet_family_does_not_collide_with_dispatch_or_safety_families():
    fleet = {t["form_key"] for t in _fleet_tips()}
    dispatch = {t["form_key"] for t in all_tips()
                if (t.get("form_key") or "").startswith("dispatch")}
    safety = {t["form_key"] for t in all_tips()
              if (t.get("form_key") or "").startswith("safety-")}
    assert not (fleet & dispatch), f"Fleet collides with dispatch: {fleet & dispatch}"
    assert not (fleet & safety), f"Fleet collides with safety-*: {fleet & safety}"
