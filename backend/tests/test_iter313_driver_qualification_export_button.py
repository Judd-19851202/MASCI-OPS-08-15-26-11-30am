"""
iter313 · Driver Qualification "Export Current View → CSV" button invariants.

Bounded UI closure of iter312 — adds a single download button to the
existing dashboard. NOT a new endpoint, NOT new infrastructure, NOT a
reporting framework. The button:

  1. Calls the iter312 CSV endpoint ONLY (`/hr/driver-qualification/dashboard.csv`).
  2. Passes the SAME `filters` state the dashboard JSON fetch uses, so the
     downloaded CSV represents EXACTLY what HR is currently viewing.
  3. Triggers a browser download via `Blob` + anchor click (no new
     backend route for "downloads", no new collection, no new
     permissions).

These tests lock the contract via static-code invariants so the button
can't accidentally drift to a different endpoint or stop sharing
filter state with the dashboard.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_JSX = REPO_ROOT / "frontend/src/pages/HrDriverQualificationDashboard.jsx"
I18N_JS = REPO_ROOT / "frontend/src/lib/i18n.js"


def _read_jsx():
    assert DASHBOARD_JSX.exists(), f"missing: {DASHBOARD_JSX}"
    return DASHBOARD_JSX.read_text()


def test_iter313_export_button_present():
    """The export button must exist with its canonical testid."""
    jsx = _read_jsx()
    assert 'data-testid="dq-export-csv"' in jsx, (
        "iter313 export button missing — `data-testid=\"dq-export-csv\"` not found"
    )


def test_iter313_export_calls_csv_endpoint():
    """The export handler must call the iter312 endpoint — no new path."""
    jsx = _read_jsx()
    assert '"/hr/driver-qualification/dashboard.csv"' in jsx, (
        "iter313 export handler not calling iter312 endpoint "
        "`/hr/driver-qualification/dashboard.csv` — endpoint drift detected"
    )


def test_iter313_export_uses_blob_response_type():
    """Browser-side download must use responseType=blob so the file is
    properly handled as binary and the browser triggers a download."""
    jsx = _read_jsx()
    # The blob responseType must be set on the CSV fetch.
    pattern = re.compile(
        r"\"/hr/driver-qualification/dashboard\.csv\"[\s\S]{0,400}responseType:\s*\"blob\"",
    )
    assert pattern.search(jsx), (
        "iter313 export not setting responseType: \"blob\" on the CSV fetch — "
        "browser may render CSV inline instead of triggering download"
    )


def test_iter313_export_shares_filter_state_with_dashboard():
    """The export handler must pass the SAME `filters` keys to the
    backend as the dashboard JSON fetch — otherwise the CSV slice
    would diverge from the visible table (operator's zero-query-drift
    contract from iter312 would break)."""
    jsx = _read_jsx()
    # Locate the export handler.
    handler_idx = jsx.find("exportCurrentView")
    assert handler_idx > 0, "exportCurrentView handler not found"
    # The handler is a multi-line async arrow function. Scan a window
    # generous enough to include the params construction (before the
    # api.get call) AND the catch/finally tail. The handler body has
    # nested `} catch { ... } finally { ... }` so we can't use `};`
    # as a delimiter — just take a 3000-char window from the def.
    handler = jsx[handler_idx:handler_idx + 3000]
    # Same filter keys as fetchRows.
    REQUIRED_FILTER_KEYS = [
        "cdl_holder", "approved", "driver_status", "endorsement",
        "expiring_cdl_30d", "expiring_medical_30d", "q",
    ]
    for key in REQUIRED_FILTER_KEYS:
        assert f"filters.{key}" in handler, (
            f"iter313 export handler missing filters.{key} — CSV slice "
            f"would diverge from the dashboard view. Zero-query-drift "
            f"contract broken."
        )


def test_iter313_export_button_disabled_during_export_or_empty():
    """Button must be disabled while a download is in flight, while
    the dashboard is loading, OR when there's nothing to export
    (`items.length === 0`)."""
    jsx = _read_jsx()
    # Find the button JSX block.
    idx = jsx.find('data-testid="dq-export-csv"')
    block_start = jsx.rfind("<Button", 0, idx)
    block_end = jsx.find(">", idx) + 1
    block = jsx[block_start:block_end]
    assert "disabled=" in block, "iter313 export button has no `disabled` prop"
    # Verify the disabled expression references exporting + items
    assert "exporting" in block, (
        "iter313 export button's disabled guard missing `exporting` — "
        "double-click during fetch could trigger duplicate downloads"
    )
    assert "items.length" in block or "items.length === 0" in block, (
        "iter313 export button doesn't disable on empty items — "
        "HR could download a 0-row CSV by accident"
    )


def test_iter313_filename_extracted_from_content_disposition():
    """The handler must respect the server-side Content-Disposition
    filename (which carries the iter312 canonical
    `MASCI_driver_qualification_YYYY-MM-DD.csv` pattern). Client-side
    fallback only kicks in if the header is missing."""
    jsx = _read_jsx()
    handler_idx = jsx.find("exportCurrentView")
    handler = jsx[handler_idx:handler_idx + 3500]
    assert "content-disposition" in handler.lower() or "Content-Disposition" in handler, (
        "iter313 export handler ignores server Content-Disposition — filename drift"
    )
    assert "filename" in handler, "iter313 handler not extracting filename"
    # Sensible fallback pattern present.
    assert "MASCI_driver_qualification_" in handler, (
        "iter313 handler missing client-side fallback filename pattern"
    )


def test_iter313_es_translations_present():
    """The two new EN strings must have ES translations so the button
    renders correctly in Spanish locale."""
    i18n = I18N_JS.read_text()
    REQUIRED_ES = [
        '"Export Current View \u2192 CSV": "Exportar Vista Actual \u2192 CSV"',
        '"Export the current filtered view to CSV": "Exportar la vista filtrada actual a CSV"',
        '"Driver qualification CSV downloaded":',
        '"Could not export driver qualification CSV":',
    ]
    for needle in REQUIRED_ES:
        assert needle in i18n, (
            f"iter313 ES translation missing: {needle!r}"
        )


def test_iter313_no_new_backend_endpoint_introduced():
    """iter313 must NOT introduce a new backend endpoint — it
    must reuse the iter312 dashboard.csv route only."""
    # Scan the JSX for any csv-looking endpoint that is NOT iter312's.
    jsx = _read_jsx()
    csv_refs = re.findall(r'"(/[a-z0-9/_-]+\.csv)"', jsx)
    for ref in csv_refs:
        assert ref == "/hr/driver-qualification/dashboard.csv", (
            f"iter313 scope violation: unexpected CSV endpoint {ref!r} — "
            f"only iter312 endpoint is allowed"
        )


def test_iter313_button_failure_visible_to_hr():
    """Failed exports must surface to HR via toast — admin surfaces
    fail loudly per iter308 stabilization principles."""
    jsx = _read_jsx()
    handler_idx = jsx.find("exportCurrentView")
    handler = jsx[handler_idx:handler_idx + 3500]
    assert "toast.error" in handler, (
        "iter313 export failure does not surface to HR via toast — "
        "violates iter308 'admin surfaces fail loudly' principle"
    )
    assert "console.error" in handler, (
        "iter313 export failure does not log to console for debugging"
    )
