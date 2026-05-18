"""iter215 + iter216 — Material Requests + Dispatch Requests contextual coaching.

Two surfaces each:

* iter215 — Material Requests
  - daily-report.materials (deepening: mistake, next, escalate)
  - material-calculator   (new top-level: planning-stage coaching)

* iter216 — Dispatch Requests
  - daily-report.equipment (deepening: next, escalate)
  - dispatch.transfers     (new Tier-2 surface: dispatcher-side coaching)

Both follow the iter211-212 tone discipline: operational realism,
field-authentic voice, positive-realism anchors, no OSHA-robotic /
HR-legal / corporate-MBA-speak drift.
"""
import os
import re
import httpx
import pytest

API_URL = os.environ.get(
    "PUBLIC_API_URL",
    os.environ.get("API_URL", "http://localhost:8001"),
)


# Helper — direct registry access (some tips are Tier-2, anon HTTP won't see them).
def _tips_under(prefix: str) -> list[dict]:
    import guidance  # noqa: F401
    from guidance.tips import all_tips
    return [t for t in all_tips() if t["form_key"] == prefix or t["form_key"].startswith(prefix + ".")]


# ═════════════════════════════════════════════════════════════════════
# iter215 — Material Requests
# ═════════════════════════════════════════════════════════════════════

DR_MATERIALS_KEYS = ["daily-report.materials"]
MATCALC_KEYS = [
    "material-calculator",
    "material-calculator.waste",
    "material-calculator.lead-time",
    "material-calculator.field-verify",
]


# ── daily-report.materials — deepening assertions ────────────────────
def test_daily_report_materials_now_has_canonical_kinds():
    """After iter215 deepening, daily-report.materials covers
    why/example/mistake/next/escalate (5 of the 7 kinds — the four
    canonical operational moments + the example)."""
    rows = [t for t in _tips_under("daily-report.materials")
            if t["form_key"] == "daily-report.materials"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "example", "mistake", "next", "escalate"):
        assert required in kinds, f"daily-report.materials missing kind: {required}"


def test_daily_report_materials_escalate_warns_about_silent_substitutions():
    rows = [t for t in _tips_under("daily-report.materials")
            if t["form_key"] == "daily-report.materials" and t["kind"] == "escalate"]
    assert rows, "missing escalate tip"
    body = (rows[0].get("body") or "").lower()
    assert "subst" in body or "swapped" in body or "different" in body, (
        "escalate must address substitutions"
    )
    assert "dispute" in body or "billing" in body, (
        "escalate must connect quiet substitutions to billing disputes"
    )


# ── material-calculator — new top-level surface ──────────────────────
def test_material_calculator_seed_count():
    assert len(_tips_under("material-calculator")) >= 9, (
        "Expected ≥9 material-calculator tips (3 top-level + 2 waste + "
        "2 lead-time + 2 field-verify)"
    )


@pytest.mark.parametrize("form_key", MATCALC_KEYS)
def test_material_calculator_anon_readable(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    assert r.status_code == 200
    assert len(r.json()["tips"]) >= 1


@pytest.mark.parametrize("form_key", MATCALC_KEYS)
def test_material_calculator_tips_bilingual(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


@pytest.mark.parametrize("form_key", MATCALC_KEYS)
def test_material_calculator_tips_concise(form_key):
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key={form_key}", timeout=10.0,
    )
    for t in r.json()["tips"]:
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


def test_material_calculator_anchors_planning_not_truth():
    """The cultural anchor — calculator is for planning, not for truth.
    Field measurement is the ground truth."""
    rows = _tips_under("material-calculator.field-verify")
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "field" in haystack and ("measure" in haystack or "verify" in haystack), (
        "field-verify must coach physical measurement over calculator output"
    )


def test_material_calculator_waste_calls_out_zero_percent_mistake():
    rows = [t for t in _tips_under("material-calculator.waste")
            if t["kind"] == "mistake" or t["kind"] == "why"]
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "0%" in haystack or "0 %" in haystack or "zero" in haystack, (
        "waste coaching must explicitly call out the 0% mistake"
    )


def test_material_calculator_lead_time_addresses_supplier_calendar():
    rows = _tips_under("material-calculator.lead-time")
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "supplier" in haystack, "lead-time tip must reference the supplier"


# ═════════════════════════════════════════════════════════════════════
# iter216 — Dispatch Requests
# ═════════════════════════════════════════════════════════════════════

DR_EQUIPMENT_KEYS = ["daily-report.equipment"]
DISPATCH_KEYS = [
    "dispatch.transfers",
    "dispatch.transfers.lead-time",
    "dispatch.transfers.access",
    "dispatch.transfers.load-specs",
    "dispatch.transfers.utilization",
]


# ── daily-report.equipment — deepening assertions ────────────────────
def test_daily_report_equipment_now_has_next_and_escalate():
    rows = [t for t in _tips_under("daily-report.equipment")
            if t["form_key"] == "daily-report.equipment"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "mistake", "next", "escalate"):
        assert required in kinds, f"daily-report.equipment missing kind: {required}"


def test_daily_report_equipment_next_anchors_dispatch_visibility():
    rows = [t for t in _tips_under("daily-report.equipment")
            if t["form_key"] == "daily-report.equipment" and t["kind"] == "next"]
    assert rows, "missing next tip"
    body = (rows[0].get("body") or "").lower()
    assert "dispatch" in body, "next tip must reference Dispatch"


def test_daily_report_equipment_escalate_anchors_shop_heads_up():
    rows = [t for t in _tips_under("daily-report.equipment")
            if t["form_key"] == "daily-report.equipment" and t["kind"] == "escalate"]
    assert rows, "missing escalate tip"
    body = (rows[0].get("body") or "").lower()
    assert "shop" in body, "escalate must coach the verbal heads-up to Shop"


# ── dispatch.transfers — new Tier-2 surface ──────────────────────────
def test_dispatch_transfers_seed_count():
    assert len(_tips_under("dispatch.transfers")) >= 12, (
        "Expected ≥12 dispatch.transfers tips (4 canonical + 2 lead + "
        "2 access + 2 load + 2 utilization)"
    )


def test_dispatch_transfers_all_tier2_dispatch_scoped():
    """Every dispatch.transfers tip MUST be dispatch-or-admin scoped.
    No accidental public leaks of dispatcher-internal coaching."""
    for t in _tips_under("dispatch.transfers"):
        scopes = set(t.get("scopes") or [])
        assert "public" not in scopes, (
            f"{t['form_key']}/{t['kind']} accidentally has 'public' scope "
            f"— dispatcher coaching is Tier-2"
        )
        assert scopes & {"dispatch", "admin"}, (
            f"{t['form_key']}/{t['kind']} missing dispatch/admin scope: {scopes}"
        )


def test_anon_caller_sees_no_dispatch_transfers_tips():
    r = httpx.get(
        f"{API_URL}/api/guidance/tips?form_key=dispatch.transfers", timeout=10.0,
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("count", 0) == 0


def test_dispatch_transfers_canonical_four_tips_present():
    rows = [t for t in _tips_under("dispatch.transfers")
            if t["form_key"] == "dispatch.transfers"]
    kinds = {t["kind"] for t in rows}
    for required in ("why", "who", "next", "escalate"):
        assert required in kinds


def test_dispatch_transfers_bilingual():
    for t in _tips_under("dispatch.transfers"):
        assert t.get("title_es"), f"{t['form_key']}/{t['kind']}: missing title_es"
        assert t.get("body_es"),  f"{t['form_key']}/{t['kind']}: missing body_es"


def test_dispatch_transfers_concise():
    for t in _tips_under("dispatch.transfers"):
        wc_en = len((t.get("body") or "").split())
        wc_es = len((t.get("body_es") or "").split())
        assert wc_en <= 80, f"{t['form_key']}/{t['kind']} EN ({wc_en} words)"
        assert wc_es <= 90, f"{t['form_key']}/{t['kind']} ES ({wc_es} words)"


def test_dispatch_transfers_lead_time_coaches_24h_ideal():
    rows = _tips_under("dispatch.transfers.lead-time")
    haystack = " ".join((t.get("body") or "").lower() for t in rows)
    assert "24" in haystack or "day" in haystack, (
        "lead-time tip should reference 24h / one-work-day-ahead"
    )


def test_dispatch_transfers_access_example_has_concrete_details():
    """The access 'example' tip must demonstrate concreteness — gate
    code, phone number, address — not abstract advice."""
    ex = [t for t in _tips_under("dispatch.transfers.access") if t["kind"] == "example"]
    assert ex, "missing access example"
    body = ex[0].get("body") or ""
    # At minimum, must contain a phone number or a gate code or a
    # specific address indicator.
    has_phone = bool(re.search(r"\d{3}[-.]?\d{4}", body))
    has_code = "code" in body.lower() and bool(re.search(r"\d{3,5}", body))
    has_addr = "Pkwy" in body or "Industrial" in body
    assert any([has_phone, has_code, has_addr]), (
        "access example must show concrete details (phone, code, address)"
    )


# ── Tone discipline — banlists across both iter215/216 surfaces ──────
ROBOTIC_OSHA_PHRASES = [
    "in accordance with", "pursuant to", "in compliance with applicable",
    "OSHA-mandated", "regulatory requirement", "shall be required to",
    "the undersigned", "willful violation",
]

CORPORATE_MBA_PHRASES = [
    "synergize", "leverage synergies", "best-in-class",
    "value-add proposition", "right-size", "stakeholder alignment",
    "core competency", "deliverables-driven",
]


def test_no_robotic_osha_tone_across_all_new_tips():
    all_new = (
        _tips_under("daily-report.materials")
        + _tips_under("material-calculator")
        + _tips_under("daily-report.equipment")
        + _tips_under("dispatch.transfers")
    )
    for t in all_new:
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in ROBOTIC_OSHA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} uses OSHA tone: {bad}"


def test_no_corporate_mba_drift_across_all_new_tips():
    all_new = (
        _tips_under("material-calculator")
        + _tips_under("dispatch.transfers")
    )
    for t in all_new:
        full = " ".join([t.get("body") or "", t.get("body_es") or ""])
        bad = [p for p in CORPORATE_MBA_PHRASES if p.lower() in full.lower()]
        assert not bad, f"{t['form_key']}/{t['kind']} drifts MBA-speak: {bad}"


# ── Positive-realism anchor — both iter215 + iter216 surfaces ─────────
def test_iter215_iter216_anchor_field_realism():
    """At least one anchor phrase must surface across material-
    calculator and dispatch.transfers families. Anchors include:
    field, foreman, crew, schedule, operational, jobsite, supplier."""
    haystack_215 = " ".join(
        (t.get("body") or "").lower() for t in _tips_under("material-calculator")
    )
    haystack_216 = " ".join(
        (t.get("body") or "").lower() for t in _tips_under("dispatch.transfers")
    )
    for name, hs in [("material-calculator", haystack_215),
                     ("dispatch.transfers", haystack_216)]:
        anchors = ["field", "foreman", "crew", "schedule", "operational",
                   "jobsite", "supplier", "driver"]
        hits = [a for a in anchors if a in hs]
        assert hits, (
            f"{name} contains NO field-realism anchor phrase. Approved "
            f"anchors include: {anchors}. Tone-discipline directive."
        )
