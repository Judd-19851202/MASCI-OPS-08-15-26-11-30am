"""TRACK 23.2 · V3 PDF / Email court-ready output alignment · lock envelope.

Enforces the V3 field-completeness expansion on the Daily Report PDF
+ email path shipped by TRACK 22.9C-through-23.4C. The audit target is
"if a V3 field has legal/operational value, it MUST render in the PDF".

Locked contracts:

  A. Crew table (Section 04)
     - Renders columns: Name, Employee ID, Trade/Role, Start, Stop,
       Lunch, Hours, Cost Code, Work Performed.
     - HR meta chip (`Crew: … · Sup: …`) renders inline when snapshots
       populated — never invents supervision context.
     - Total Hours row preserved.

  B. Materials · Inbound (Section 08)
     - Renders columns: Material, Qty, Unit, **Carrier** (single field,
       replaces legacy Supplier column), Ticket #, Cost Code, Notes.
     - Prefers `carrier` → `carrier_name_snapshot` → legacy `supplier`
       so historical V1 rows still show a hauler name.
     - Prefers `unit_snapshot` over raw `unit` for human-readable display.

  C. Materials · Outbound (Section 09d)
     - Renders columns: Material, Qty, Unit, **Carrier**, Destination,
       Ticket/Manifest, Cost Code, Notes.
     - Accepts `hauler` / `hauler_name_snapshot` / `carrier` / `carrier_name_snapshot`.

  D. Historical parity
     - PDF renders as valid `%PDF` bytes for V1-shaped records with no
       V3 fields.

  E. Provider / raw-meta safety
     - Rendered HTML never leaks provider names or raw metadata keys
       (already locked by 22.9C — extended check here for the new
       columns).
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _pdf():
    import pdf_render  # noqa: WPS433
    return pdf_render


V3_FIXTURE = {
    "project_name": "20-07",
    "report_date": "2026-02-06",
    "prepared_by": "Foreman X",
    "doc_id": "DR-2026-100",
    "report_number": "DR-2026-100",
    "masci_crews": [
        {
            "name": "Jane Smith", "employee_id": "EMP-1",
            "trade": "Operator", "crew_snapshot": "Crew B",
            "supervisor_snapshot": "R. Diaz",
            "start_time": "07:00", "stop_time": "17:00",
            "lunch_minutes": 30, "hours": 9.5, "cost_code": "PAV-100",
            "work_performed": "Paving Sta 12+00",
        },
        {
            "name": "John Doe", "employee_id": "EMP-2",
            "trade": "Carpenter", "crew_snapshot": "Crew A",
            "start_time": "07:00", "stop_time": "15:30",
            "lunch_minutes": 30, "hours": 8.0,
            "work_performed": "Curb forms",
        },
    ],
    "materials": [
        {
            "description": "Lime rock", "quantity": 125,
            "unit_snapshot": "Tons",
            "carrier": "Acme Hauling", "carrier_id": "SUP-77",
            "carrier_name_snapshot": "Acme Hauling",
            "ticket_number": "T-48372", "cost_code": "PAV-100",
        }
    ],
    "outbound_materials": [
        {
            "material": "Demo debris", "quantity": 6,
            "unit_snapshot": "Loads",
            "hauler": "Green Waste", "hauler_id": "SUP-88",
            "hauler_name_snapshot": "Green Waste",
            "destination": "Landfill A", "ticket_number": "M-77",
            "cost_code": "DEM-200",
        }
    ],
    "photos": [],
    "ai_accepted_summary": "Placed 125 tons of lime rock; hauled off 6 loads of demo debris.",
    "ai_accepted_summary_meta": {"edited_by_user": False},
}

LEGACY_FIXTURE = {
    "project_name": "20-99",
    "report_date": "2020-06-15",
    "prepared_by": "Legacy",
    "doc_id": "DR-2020-1",
    "report_number": "DR-2020-1",
    "masci_crews": [{"name": "Legacy Guy", "trade": "Laborer", "hours": 8}],
    "materials": [
        {"description": "Rock", "quantity": 50, "unit": "TN",
         "supplier": "Old Vendor", "ticket_number": "X-1"}
    ],
    "photos": [],
}


# ── A · Crew table ──────────────────────────────────────────────
def test_pdf_crew_table_has_new_v3_columns():
    html = _pdf()._render_daily(V3_FIXTURE)
    for col in ("Employee ID", "Trade / Role", "Cost Code"):
        assert col in html, f"Crew table missing `{col}` header."
    # HR meta chip renders when snapshots populated.
    assert "Crew: Crew B" in html
    assert "Sup: R. Diaz" in html
    # Total Hours row preserved.
    assert "Total Hours" in html


def test_pdf_crew_hr_meta_hidden_when_absent():
    """Legacy crew rows without HR snapshots must NOT sprout an empty
    'Crew: · Sup:' chip — the code path must gate on presence."""
    html = _pdf()._render_daily(LEGACY_FIXTURE)
    assert "Crew: " not in html
    assert "Sup: " not in html


# ── B · Inbound materials ──────────────────────────────────────
def test_pdf_inbound_materials_carrier_only():
    """Inbound Materials header must be Carrier — never Supplier."""
    html = _pdf()._render_daily(V3_FIXTURE)
    # New Carrier column present.
    assert ">Carrier<" in html
    # Old Supplier column header must not return for V3 rows.
    assert ">Supplier<" not in html
    # Values render.
    assert "Acme Hauling" in html
    assert "Tons" in html
    assert "PAV-100" in html


def test_pdf_inbound_legacy_supplier_fallback():
    """Legacy V1 rows carried only `supplier`. The Carrier column must
    fall back to it so historical PDFs still show a hauler name."""
    html = _pdf()._render_daily(LEGACY_FIXTURE)
    assert ">Carrier<" in html
    assert "Old Vendor" in html


# ── C · Outbound materials ─────────────────────────────────────
def test_pdf_outbound_carrier_and_snapshots():
    html = _pdf()._render_daily(V3_FIXTURE)
    assert "Green Waste" in html
    assert "Landfill A" in html
    assert "Loads" in html
    # Carrier header for outbound table (avoid matching inbound's).
    assert html.count(">Carrier<") >= 2


# ── D · PDF byte-parity across shapes ──────────────────────────
def test_pdf_bytes_valid_for_v3_and_legacy():
    pdf = _pdf().render_record_pdf("daily-report", V3_FIXTURE)
    assert pdf[:4] == b"%PDF"
    legacy = _pdf().render_record_pdf("daily-report", LEGACY_FIXTURE)
    assert legacy[:4] == b"%PDF"


# ── E · Provider / raw-meta must never leak into rendered HTML ─
def test_pdf_never_leaks_ai_provider_or_raw_meta():
    html = _pdf()._render_daily(V3_FIXTURE)
    lower = html.lower()
    for banned in ("openai", "anthropic", "claude", "gemini",
                   "gpt-", "sonnet", "opus", "haiku",
                   "nano banana", "llm", "latency_ms",
                   "provider_masked", "model_masked", "deterministic",
                   "edited_by_user"):
        assert banned not in lower, (
            f"TRACK 23.2 · Banned token `{banned}` leaked into PDF."
        )


# ── F · Email safety (surface-level regression guard) ──────────
def test_email_still_renders_daily_report_kind():
    html = _pdf().render_email_html("daily-report", V3_FIXTURE)
    assert "Operational Intelligence Summary" in html
    assert "Placed 125 tons" in html


def test_email_legacy_report_unchanged():
    html = _pdf().render_email_html("daily-report", LEGACY_FIXTURE)
    # No AI block for legacy records.
    assert "Operational Intelligence Summary" not in html
    assert "attached as a PDF" in html
