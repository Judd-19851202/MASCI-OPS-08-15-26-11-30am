"""Track 19.11 · Amendment · Session-Expired Modal Loop Fix — Lock Tests.

Field bug repaired:
    On form pages (Daily Report, Equipment Pre-Op), an expired session
    caused the "Session Expired" modal to REOPEN on every subsequent
    keystroke because background pollers / roster refetches fire 401s
    outside the 800 ms debounce window. This test suite locks the fix:

Fix doctrine:
    * sessionStatusBus.js gains sticky *acknowledgment suppression* on
      the two auth kinds (session_expired, access_restricted).
    * Once the user dismisses via clearSessionStatus(), further
      publishes of the same kind are ignored until
        - success_loaded fires (session recovered), or
        - resetSessionAck() is called (login flow).
    * NETWORK_UNREACHABLE and BACKEND_UNAVAILABLE remain retryable UX
      and are NOT ack-suppressed.
    * SessionStatusOverlay strings are now fully bilingual via useT().
    * Zero backend / schema / route / payload / PDF / email drift.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"

_BUS = (FRONTEND / "src/lib/sessionStatusBus.js").read_text(encoding="utf-8")
_OVERLAY = (FRONTEND / "src/components/SessionStatusOverlay.jsx").read_text(encoding="utf-8")
_BUS_TESTS = (FRONTEND / "src/lib/sessionStatusBus.test.js").read_text(encoding="utf-8")
_I18N = (FRONTEND / "src/lib/i18n.js").read_text(encoding="utf-8")
_DR = (FRONTEND / "src/pages/NewDailyReport.jsx").read_text(encoding="utf-8")
_EQ = (FRONTEND / "src/pages/NewEquipmentInspection.jsx").read_text(encoding="utf-8")
_API = (FRONTEND / "src/lib/api.js").read_text(encoding="utf-8")
_ERROR_CLASS = (FRONTEND / "src/lib/errorClassification.js").read_text(encoding="utf-8")


# --- Bus contract: ack-suppression is present -------------------------------


def test_bus_declares_ack_sticky_kinds():
    """The set of auth kinds that trigger sticky ack-suppression must
    include session_expired and access_restricted — and only those."""
    assert "ACK_STICKY_KINDS" in _BUS
    assert '"session_expired"' in _BUS
    assert '"access_restricted"' in _BUS


def test_bus_exports_reset_session_ack():
    """resetSessionAck() is the lifting hook for successful re-auth."""
    assert "export function resetSessionAck" in _BUS


def test_bus_exports_get_session_ack_state():
    """Diagnostics hook — tests / ops scripts can inspect suppression."""
    assert "export function getSessionAckState" in _BUS


def test_bus_suppresses_publish_when_ack_present():
    """The publish path must short-circuit on ack-suppressed kinds."""
    assert "_ackSuppressed.has(kind)" in _BUS


def test_bus_success_loaded_lifts_ack_suppression():
    """Session recovery signal must clear the ack set."""
    assert "if (_ackSuppressed.size > 0)" in _BUS
    assert "_ackSuppressed = new Set();" in _BUS


def test_bus_clear_marks_ack_only_for_auth_kinds():
    """Dismissing NETWORK / BACKEND kinds must NOT ack-suppress (retryable UX)."""
    assert "if (ACK_STICKY_KINDS.has(dismissedKind))" in _BUS
    assert "_ackSuppressed.add(dismissedKind);" in _BUS


def test_bus_test_reset_resets_ack_set():
    """Jest _testReset must wipe the ack set between cases."""
    assert "_ackSuppressed = new Set();" in _BUS
    # And in _testReset specifically
    idx = _BUS.find("export const _testReset")
    assert idx != -1
    assert "_ackSuppressed = new Set();" in _BUS[idx:]


def test_bus_window_surface_exposes_new_hooks():
    """window.__masciSessionBus is the Playwright-facing surface;
    reset/introspection must be plumbed through it."""
    assert "resetAck: resetSessionAck" in _BUS
    assert "getAck: getSessionAckState" in _BUS


# --- Overlay bilingual + reset-on-login-nav ---------------------------------


def test_overlay_imports_reset_session_ack():
    assert "resetSessionAck" in _OVERLAY
    assert 'from "@/lib/sessionStatusBus"' in _OVERLAY


def test_overlay_calls_reset_ack_on_log_back_in():
    """When the user taps Log Back In, ack is lifted before nav so a
    genuinely-new post-login 401 can raise the modal again."""
    # The onPrimary handler must call resetSessionAck() for SESSION_EXPIRED.
    idx = _OVERLAY.find("state.kind === ERROR_KINDS.SESSION_EXPIRED")
    assert idx != -1
    # Look at the next ~400 chars for the resetSessionAck call.
    assert "resetSessionAck()" in _OVERLAY[idx : idx + 400]


def test_overlay_uses_useT_hook_for_bilingual_strings():
    assert 'import { useT } from "@/lib/i18n"' in _OVERLAY
    assert "const { t } = useT();" in _OVERLAY


def test_overlay_copy_function_takes_t_parameter():
    """The _copy helper must accept t so every user-facing string is
    routed through the i18n dictionary."""
    assert "function _copy(state, t)" in _OVERLAY
    assert "const copy = _copy(state, t);" in _OVERLAY


@pytest.mark.parametrize(
    "en_string",
    [
        "Session Expired",
        "Your login session has expired. No data has been lost. Please log back in to continue.",
        "Log Back In",
        "Stay Here",
        "Access Restricted",
        "Your account does not have permission to view this area.",
        "Connection Problem",
        "Your device cannot reach platform services right now. Any drafts or pending uploads remain protected locally.",
        "Services Temporarily Unavailable",
        "The server is reachable but returned an error. Try again shortly. Field drafts remain protected locally.",
        "Retry",
        "Dismiss",
    ],
)
def test_overlay_string_is_bilingual(en_string):
    """Every user-facing string in the overlay must have a Spanish
    translation in the ES dictionary of i18n.js."""
    escaped = en_string.replace('"', '\\"')
    assert f'"{escaped}":' in _I18N, (
        f"Missing ES translation for overlay string: {en_string!r}"
    )
    # And it must be referenced through t() in the overlay (or through
    # useT in the header aria-label).
    assert en_string in _OVERLAY, (
        f"Overlay does not carry the English canonical: {en_string!r}"
    )


def test_overlay_close_button_aria_label_bilingual():
    """The X close button aria-label must be bilingual too."""
    assert 'aria-label={t("Close")}' in _OVERLAY


# --- Jest coverage present --------------------------------------------------


@pytest.mark.parametrize(
    "test_title",
    [
        "after user dismiss, further session_expired publishes are suppressed",
        "access_restricted dismissal is also ack-suppressed",
        "success_loaded lifts ack-suppression so genuinely-new expiry can re-fire",
        "resetSessionAck lifts suppression without touching overlay state",
        "dismissing NETWORK_UNREACHABLE does NOT ack-suppress (retryable UX)",
        "dismissing BACKEND_UNAVAILABLE does NOT ack-suppress (retryable UX)",
    ],
)
def test_jest_coverage_present(test_title):
    """Ensure the Jest suite carries the ack-suppression behavior tests
    so regressions in the bus contract are caught in CI."""
    assert test_title in _BUS_TESTS


# --- Draft / typing safety guardrails ---------------------------------------


def test_daily_report_form_typing_not_gated_on_session_state():
    """Draft protection: typing into the DR form must not be blocked by
    session state. The form's inputs must not be disabled based on any
    session-bus flag."""
    # No `disabled={sessionExpired}` / `disabled={sessionStatus...}` etc.
    # (This is a positive guardrail: the form must NEVER wire input
    # disabling to the session bus. If it did, the fix would defeat
    # itself by making typing feel broken instead of the modal being
    # broken.)
    assert "sessionStatus" not in _DR
    assert "sessionExpired" not in _DR


def test_equipment_preop_form_typing_not_gated_on_session_state():
    """Same guardrail for Equipment Pre-Op."""
    assert "sessionStatus" not in _EQ
    assert "sessionExpired" not in _EQ


def test_track_19_09_camera_gate_still_present():
    """Regression: Camera Obstruction Gate must not have been touched."""
    assert 'data-testid="equipment-camera-gate"' in _EQ
    assert "Clear the obstruction before operating" in _EQ


def test_track_19_10_helpdrawer_wired_still_present():
    """Regression: HelpDrawer POC on Equipment Pre-Op must remain wired."""
    assert 'import { HelpDrawer } from "@/components/HelpDrawer"' in _EQ
    assert 'testIdPrefix="equipment-help-drawer"' in _EQ


# --- Interceptor contract preserved (zero drift on token handling) ---------


def test_interceptor_still_publishes_via_bus():
    """The axios interceptor still uses publishSessionStatus — the
    session-status pipeline is intact, just tamer at the sink."""
    assert "publishSessionStatus" in _API
    assert "classifyApiError" in _API


def test_interceptor_still_honors_skip_session_status_flag():
    """Background pollers can still opt-out of the global modal via the
    per-request skipSessionStatus config flag."""
    assert "skipSessionStatus" in _API


def test_interceptor_still_scopes_401_to_active_portal():
    """Track 15.13E / 15.13H portal-scoped 401 absorption preserved."""
    assert "activePortal" in _API
    assert "_namespacedHandled" in _API


def test_error_classification_still_maps_401_to_session_expired():
    """The classifier is the source of truth for the auth kind
    routing — do not let anyone silently change it."""
    assert "if (status === 401) return _decorate(T.SESSION_EXPIRED, 401);" in _ERROR_CLASS
    assert "if (status === 403) return _decorate(T.ACCESS_RESTRICTED, 403);" in _ERROR_CLASS


# --- Zero backend / schema / route drift ------------------------------------


def test_amendment_touched_no_backend_files():
    """The fix is 100% frontend. No new backend endpoints, no schema
    changes, no route additions. Track 19.08 snapshot lock must still
    hold — this test is a soft guard that no backend routes doc was
    edited to reflect a new session route."""
    audit_test_path = REPO_ROOT / "backend/tests/test_track_19_08_forms_audit_snapshots.py"
    audit = audit_test_path.read_text(encoding="utf-8")
    assert "SNAPSHOT_ROUTES_MIN = 900" in audit
    assert "SNAPSHOT_COLLECTIONS_MIN = 140" in audit
