"""TRACK 28.03 · Static audit — no Field Leadership form silently
auto-restores an unsent draft.

The FL platform standardized in TRACK 27.08 established the
explicit-restore contract:
  1. `useDraftSync` LOADS an unsent draft into local state but does
     NOT auto-apply it — the caller must render an explicit
     "Restore / Start blank" prompt.
  2. A user's typed content only re-populates the form if they
     click the "Restore draft" button.
  3. Successful submit calls `commit()` which wipes the draft.

This test enforces that contract by asserting:
  • The single canonical entrypoint (`FieldLeadershipFormPage.jsx`)
    renders every FL form and uses `useDraftSync` with the
    `hasPendingDraft` + `restorePendingDraft` prompt UI.
  • The `useDraftSync` hook implementation has NOT reverted to a
    silent auto-apply pattern (no `onRecoverRef.current(draft)`
    call directly inside the mount effect).
  • The FL form entrypoint exposes the required data-testids
    (`fl-draft-restore-prompt`, `fl-draft-restore-apply`,
    `fl-draft-restore-discard`) so operator flows can be verified.
"""
from __future__ import annotations

from pathlib import Path
import re

import pytest


FRONTEND_ROOT = Path("/app/frontend/src")
HOOK_FILE = FRONTEND_ROOT / "lib" / "resiliency" / "useDraftSync.js"
FL_FORM_FILE = FRONTEND_ROOT / "pages" / "FieldLeadershipFormPage.jsx"


def test_use_draft_sync_hook_never_auto_applies_on_mount() -> None:
    """The hook's mount `useEffect` must NOT call the caller's
    `onRecover` — it must only stash the draft in `pendingDraft`.
    Regressing to auto-apply reintroduces the P0 that Track 27.08
    fixed: a user's stale draft leaking into a fresh form before
    they can see the blank state.
    """
    assert HOOK_FILE.exists(), f"missing {HOOK_FILE}"
    src = HOOK_FILE.read_text(encoding="utf-8")

    # Find the on-mount useEffect body.
    match = re.search(
        r"useEffect\(\s*\(\)\s*=>\s*\{(.*?)\n\s*\},\s*\[formKey,\s*actorId\]",
        src, re.DOTALL,
    )
    assert match, (
        "Could not locate the on-mount useEffect that reads the draft "
        "— the hook was refactored and this audit must be updated."
    )
    body = match.group(1)
    assert "setPendingDraft" in body, (
        "On-mount effect must stash the draft in `pendingDraft` state."
    )
    # onRecover must NOT be invoked inside the mount effect.
    assert "onRecover(" not in body and "onRecoverRef.current(" not in body, (
        "TRACK 27.08 explicit-restore contract violated — the "
        "on-mount effect invokes the caller's onRecover directly, "
        "which is a silent auto-apply. Restore must happen only "
        "through applyDraft() after the operator clicks Restore."
    )


def test_fl_form_page_uses_explicit_restore_prompt() -> None:
    """FL forms route through a single entrypoint; the prompt UI
    with 3 canonical data-testids must be present."""
    assert FL_FORM_FILE.exists(), f"missing {FL_FORM_FILE}"
    src = FL_FORM_FILE.read_text(encoding="utf-8")
    assert "useDraftSync" in src, "FL form page must consume useDraftSync"
    for testid in (
        "fl-draft-restore-prompt",
        "fl-draft-restore-apply",
        "fl-draft-restore-discard",
    ):
        assert testid in src, f"FL form page missing testid `{testid}` — the explicit-restore prompt UI has drifted"
    # Successful submit must call commit() so the draft is wiped.
    assert "await commit()" in src or "commit();" in src, (
        "FL form must call `commit()` on successful submit to wipe the draft."
    )


def test_no_fl_component_bypasses_useDraftSync_with_silent_restore() -> None:
    """No other FL page may reintroduce silent draft restore by
    directly calling `getDraft` and applying the result in a mount
    effect."""
    fl_files = list(FRONTEND_ROOT.rglob("Field*.jsx")) + list(FRONTEND_ROOT.rglob("Fl*.jsx"))
    violations = []
    for f in fl_files:
        src = f.read_text(encoding="utf-8")
        if "getDraft(" not in src:
            continue
        # Any file that calls getDraft(...) must also render the
        # explicit-restore prompt (identified by any of the canonical
        # testids OR consuming useDraftSync).
        if "useDraftSync" in src:
            continue
        if any(t in src for t in (
            "fl-draft-restore-prompt",
            "fl-draft-restore-apply",
            "fl-draft-restore-discard",
        )):
            continue
        rel = f.relative_to(FRONTEND_ROOT).as_posix()
        violations.append(f"{rel} calls getDraft() without routing through useDraftSync's explicit-restore prompt")
    if violations:
        raise AssertionError(
            "TRACK 27.08 explicit-restore contract violated:\n  • "
            + "\n  • ".join(violations)
        )
