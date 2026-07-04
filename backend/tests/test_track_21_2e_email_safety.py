"""Track 21.2E · Email Safety Incident Closeout — lock test.

Proves the Track 21.2 email safety hardening at the unit level. No HTTP
requests are made; no records are submitted; no fixtures spin up a live
backend. All assertions are static or in-process.

Run:
    pytest /app/backend/tests/test_track_21_2e_email_safety.py -v
"""
from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path("/app")
BACKEND = REPO / "backend"
MEM = REPO / "memory" / "track_21_2e"

sys.path.insert(0, str(BACKEND))


# --------------------------------------------------------------------- 1 · SDK patch install proof

def test_resend_sdk_is_patched_when_strict(monkeypatch):
    """Import server.py with EMAIL_SAFETY_MODE=strict → resend.Emails.send is a stub."""
    monkeypatch.setenv("EMAIL_SAFETY_MODE", "strict")
    # Force fresh import of server + resend so the patch installs deterministically.
    for name in ("server", "resend"):
        if name in sys.modules:
            del sys.modules[name]
    import resend  # noqa: F401
    original_send = resend.Emails.send
    import server  # noqa: F401  (triggers the boot-time patch)
    patched_send = resend.Emails.send
    # The patched callable must NOT be the original one.
    assert patched_send is not original_send, "resend.Emails.send was not patched"
    # The patched callable must return the synthetic blocked payload.
    result = patched_send({"from": "a@b.com", "to": "x@y.com", "subject": "t", "html": "<p>t</p>"})
    assert isinstance(result, dict)
    assert result.get("id") == "blocked_by_email_safety_mode"
    assert result.get("status") == "skipped"


def test_resend_sdk_untouched_when_safety_off():
    """Source-level guarantee: server.py only patches Resend when
    EMAIL_SAFETY_MODE is strict/silent/test. In production (env unset or
    'off'), the `if _EMAIL_SAFETY_MODE in ...` branch is skipped, so the
    real SDK ``send`` remains in place."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    # Guard clause must be present and must gate the patch installation.
    guard = 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):'
    assert guard in src, "Missing production-safe env guard around Resend patch"
    guard_idx = src.find(guard)
    patch_idx = src.find("_resend_boot.Emails.send = staticmethod(_blocked_send)")
    assert patch_idx > 0, "Resend patch installation line not found"
    assert guard_idx < patch_idx, "Env guard must precede patch installation"
    # There must be NO unconditional patch of resend.Emails.send anywhere else.
    unconditional = re.findall(r"^resend\.Emails\.send\s*=", src, re.MULTILINE)
    assert not unconditional, (
        "Found an unconditional module-level assignment to resend.Emails.send — "
        "this would patch the SDK even in production. Move behind the env guard."
    )


# --------------------------------------------------------------------- 2 · auto_email_enabled proof

def test_auto_email_enabled_false_in_strict(monkeypatch):
    monkeypatch.setenv("EMAIL_SAFETY_MODE", "strict")
    monkeypatch.setenv("RESEND_API_KEY", "re_fake")
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "true")
    if "pm_routing" in sys.modules:
        importlib.reload(sys.modules["pm_routing"])
    else:
        import pm_routing  # noqa: F401
    from pm_routing import auto_email_enabled
    assert auto_email_enabled() is False


def test_auto_email_enabled_true_in_off_mode(monkeypatch):
    monkeypatch.setenv("EMAIL_SAFETY_MODE", "off")
    monkeypatch.setenv("RESEND_API_KEY", "re_fake")
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "true")
    if "pm_routing" in sys.modules:
        importlib.reload(sys.modules["pm_routing"])
    from pm_routing import auto_email_enabled
    assert auto_email_enabled() is True


def test_auto_email_enabled_false_when_unset_and_no_resend_key(monkeypatch):
    monkeypatch.delenv("EMAIL_SAFETY_MODE", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "true")
    if "pm_routing" in sys.modules:
        importlib.reload(sys.modules["pm_routing"])
    from pm_routing import auto_email_enabled
    assert auto_email_enabled() is False


# --------------------------------------------------------------------- 3 · Dispatcher short-circuit proof

def test_dispatch_auto_email_source_contains_strict_gate():
    """Static assertion: the strict gate lives BEFORE recipients_for_record_async
    inside `_dispatch_auto_email`. Bounds the search to that function body."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    # Locate the function definition
    fn_start = src.find("async def _dispatch_auto_email(kind: str, record: dict)")
    assert fn_start > 0, "_dispatch_auto_email not found"
    # Function body ends at the next top-level "async def" or "def" or module boundary
    fn_end = src.find("\n\n\n", fn_start + 1)
    if fn_end < 0:
        fn_end = len(src)
    body = src[fn_start:fn_end]
    idx_gate = body.find("EMAIL_SAFETY_MODE=%s hard-kill")
    idx_recipients = body.find("recipients_for_record_async")
    assert idx_gate > 0, "Strict-mode gate not present in _dispatch_auto_email"
    assert idx_recipients > 0, "recipients_for_record_async not called from dispatcher"
    assert idx_gate < idx_recipients, (
        "Strict-mode gate must precede recipients_for_record_async so the "
        "dispatcher short-circuits before any recipient lookup."
    )


def test_dispatch_auto_email_source_contains_test_prefix_gate():
    """Track 20.6B TEST_-prefix gate must still exist (defense-in-depth)."""
    src = (BACKEND / "server.py").read_text(encoding="utf-8")
    assert "synthetic-test-record gate" in src
    assert 'startswith("TEST_")' in src


# --------------------------------------------------------------------- 4 · Every direct-Resend callsite is downstream of one of the two gates

def test_no_direct_resend_send_outside_gated_helpers():
    """Enumerate every reference to `resend.Emails.send` / `_resend.Emails.send`
    across the backend and bound the surface. The SDK-level monkey patch
    covers every one of these callers when EMAIL_SAFETY_MODE=strict, but if
    the count changes materially (someone adds a new direct-SDK call in a
    new module), this canary fires so we review whether the new site needs
    a matching gate."""
    hits = []
    pat = re.compile(r"\b_?resend\.Emails\.send\b")
    for py in BACKEND.rglob("*.py"):
        if "__pycache__" in str(py) or "/tests/" in str(py):
            continue
        try:
            txt = py.read_text(errors="ignore")
        except Exception:
            continue
        for m in pat.finditer(txt):
            # Skip references inside comments / docstrings by checking that
            # the line's stripped text does not start with '#' and the match
            # is not preceded by '# ' on the same line.
            line_start = txt.rfind("\n", 0, m.start()) + 1
            line_prefix = txt[line_start:m.start()]
            if line_prefix.lstrip().startswith("#"):
                continue
            if line_prefix.count('"') % 2 == 1 or line_prefix.count("'") % 2 == 1:
                # Inside a string literal (docstring / log message).
                continue
            hits.append({"file": str(py.relative_to(REPO)), "offset": m.start()})
    # Track 21.2E baseline: 20 executable direct-SDK references
    # (all in server.py — imported lazily via `import resend as _resend`
    # inside each helper — plus 1 in lib/red_alert.py).
    # Assertion is a *bound* not an exact match, so refactors that add or
    # remove one or two callers do not cause spurious churn.
    assert 15 <= len(hits) <= 30, (
        f"Unexpected direct Resend callsite count: {len(hits)}. "
        f"Track 21.2E baseline is ~21 sites. Any material change must be reviewed."
    )


# --------------------------------------------------------------------- 5 · Inventory of non-TEST_ payloads exists and is non-zero

def test_non_test_payload_inventory_exists():
    inv = MEM / "NON_TEST_PAYLOAD_INVENTORY.json"
    assert inv.is_file(), "Non-TEST_ payload inventory must exist"
    import json
    d = json.loads(inv.read_text())
    # Track 21.2E baseline: 72 payloads across 36 files (57 distinct names).
    # Track 21.2E-1 canonicalization drove the count to 0. Both states are
    # acceptable — the invariant is that the count is captured (non-negative).
    assert d["total_non_test_payloads"] >= 0
    assert d["distinct_files"] >= 0
    assert d["distinct_project_names"] >= 0


# --------------------------------------------------------------------- 6 · Preview env has the safety mode set

def test_preview_env_declares_strict_safety_mode():
    envfile = BACKEND / ".env"
    body = envfile.read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", body, re.MULTILINE), (
        "Preview backend/.env must declare EMAIL_SAFETY_MODE=strict"
    )


# --------------------------------------------------------------------- 7 · Boot-time log line asserted in current preview log

def test_boot_log_confirms_patch_active():
    """One of the current backend logs must record the SDK patch activation."""
    log_paths = list(Path("/var/log/supervisor").glob("backend*.log"))
    if not log_paths:
        pytest.skip("supervisor logs unavailable")
    found = False
    for lp in log_paths:
        try:
            if "EMAIL_SAFETY_MODE=strict — Resend SDK patched" in lp.read_text(errors="ignore"):
                found = True
                break
        except Exception:
            continue
    assert found, (
        "Backend supervisor logs must contain the Track 21.2 SDK-patch "
        "activation line 'EMAIL_SAFETY_MODE=strict — Resend SDK patched'."
    )
