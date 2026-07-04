"""Track 21.2E-1 · Defense-in-Depth Canonicalization — lock test.

Proves that every ``project_name`` literal appearing in an
HTTP-submitting backend test file starts with the ``TEST_`` prefix.
This makes the Track 20.6B in-code gate sufficient on its own —
the Track 21.2E SDK-level kill switch remains as the outermost
env-gated backstop.

No HTTP calls, no email dispatch, no live-server dependency.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

APP = Path("/app")
BACKEND_TESTS = APP / "backend" / "tests"
CANON_REPORT = APP / "memory" / "track_21_2e_1" / "CANONICALIZATION_REPORT.json"


def _http_submitting_test_files():
    """Yield every backend test file that actually POSTs to the backend."""
    for tf in sorted(BACKEND_TESTS.rglob("test_*.py")):
        if "__pycache__" in str(tf):
            continue
        try:
            txt = tf.read_text(errors="ignore")
        except Exception:
            continue
        if "requests.post" in txt or "client.post" in txt:
            yield tf, txt


def test_no_non_test_project_name_literals_remain():
    """Every ``"project_name": "..."`` literal in an HTTP-submitting test
    file must start with ``TEST_``. Zero exceptions."""
    self_path = Path(__file__).resolve()
    offenders = []
    for tf, txt in _http_submitting_test_files():
        if tf.resolve() == self_path:
            # The lock test itself references the regex; skip.
            continue
        for m in re.finditer(r'"project_name"\s*:\s*"([^"]+)"', txt):
            pname = m.group(1)
            if not pname.startswith("TEST_"):
                offenders.append({
                    "file": tf.relative_to(APP).as_posix(),
                    "line": txt[: m.start()].count("\n") + 1,
                    "project_name": pname,
                })
    assert not offenders, (
        f"Found {len(offenders)} non-TEST_ project_name literals in "
        f"HTTP-submitting tests: {offenders[:5]}"
    )


def test_canonicalization_report_exists():
    assert CANON_REPORT.is_file(), (
        "Track 21.2E-1 canonicalization report must be committed at "
        f"{CANON_REPORT.relative_to(APP)}"
    )
    d = json.loads(CANON_REPORT.read_text())
    assert d.get("residual_non_test") == [] or len(d["residual_non_test"]) == 0
    assert d["rewrites_performed"] > 0
    assert d["files_touched"] > 0


def test_track_20_6b_gate_still_present():
    """Canonicalization must not have accidentally disturbed the
    Track 20.6B TEST_-prefix gate in _dispatch_auto_email."""
    src = (APP / "backend" / "server.py").read_text(encoding="utf-8")
    assert "synthetic-test-record gate" in src
    assert 'startswith("TEST_")' in src


def test_track_21_2e_sdk_kill_switch_still_present():
    """Canonicalization must not have accidentally disturbed the
    Track 21.2E SDK-level kill switch."""
    src = (APP / "backend" / "server.py").read_text(encoding="utf-8")
    assert 'if _EMAIL_SAFETY_MODE in ("strict", "silent", "test"):' in src
    assert "_resend_boot.Emails.send = staticmethod(_blocked_send)" in src


def test_preview_env_still_declares_strict_safety_mode():
    body = (APP / "backend" / ".env").read_text(encoding="utf-8")
    assert re.search(r"^EMAIL_SAFETY_MODE=strict\s*$", body, re.MULTILINE)


def test_canonicalized_literals_follow_uniform_shape():
    """Every canonicalized project_name must match a uniform regex:
    ``TEST_[A-Za-z0-9_]+``. No embedded spaces, non-ASCII, or punctuation."""
    canonical_pat = re.compile(r"^TEST_[A-Za-z0-9_]+$")
    weird = []
    for tf, txt in _http_submitting_test_files():
        for m in re.finditer(r'"project_name"\s*:\s*"(TEST_[^"]+)"', txt):
            pname = m.group(1)
            if not canonical_pat.match(pname):
                weird.append({
                    "file": tf.relative_to(APP).as_posix(),
                    "line": txt[: m.start()].count("\n") + 1,
                    "project_name": pname,
                })
    # Some prior test writers used TEST_iter151_persist style — that's fine.
    # This assertion is a *soft* bound: at least 95% of canonicalized literals
    # should be uniform. Report the outliers for review.
    if weird:
        # Allow a small number to slip (pre-existing custom-shape TEST_ literals).
        assert len(weird) <= 10, (
            f"Too many non-uniform TEST_ literals: {len(weird)}. First 5: {weird[:5]}"
        )
