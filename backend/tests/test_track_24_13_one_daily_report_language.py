"""TRACK 24.13 · Product-facing Daily Report Language Lock.

There is ONE Daily Report. Internal legacy filenames / routes / test
IDs may reference version tags for backwards compatibility, but ALL
product-facing surfaces (PDF templates, email templates, AI prompt
labels, viewer strings, sidebar labels) must refer to it simply as
"Daily Report".

This suite scans the rendered/printed strings — not code comments —
so a stray "Daily Report V3" showing up in a PDF header or a PM
email would fail the build.
"""
from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path("/app/backend")

# ── Utility ─────────────────────────────────────────────────────────

_BANNED_PHRASES = (
    "Daily Report V1",
    "Daily Report V2",
    "Daily Report V3",
    "V1 Daily Report",
    "V2 Daily Report",
    "V3 Daily Report",
    "Daily Job Report V1",
    "Daily Job Report V2",
    "Daily Job Report V3",
    "Legacy Daily Report",
    "Modern Daily Report",
    "Old Daily Report",
    "New Daily Report V",  # covers "New Daily Report V2/V3"
)


def _visible_strings(py_src: str) -> list[str]:
    """Extract the string literals that are likely rendered to a user.

    Heuristic: any triple-quoted docstring is treated as an internal
    comment and stripped. Regular string/f-string literals ARE scanned —
    the tests below only look at content that would be interpolated
    into an HTML/PDF/email body.
    """
    # Strip triple-quoted docstrings (internal comments).
    src = re.sub(r'"""[\s\S]*?"""', "", py_src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    return re.findall(r'"([^"\\]{0,4000})"|\'([^\'\\]{0,4000})\'', src)


def _flatten(matches):
    for m in matches:
        for g in m:
            if g:
                yield g


# ── PDF rendered strings ────────────────────────────────────────────

def test_pdf_render_carries_no_versioned_daily_report_label():
    src = (BACKEND / "pdf_render.py").read_text(encoding="utf-8")
    strings = list(_flatten(_visible_strings(src)))
    hits: list[tuple[str, str]] = []
    for s in strings:
        for phrase in _BANNED_PHRASES:
            if phrase in s:
                hits.append((phrase, s[:120]))
    assert not hits, (
        "TRACK 24.13 · pdf_render.py contains user-visible versioned "
        f"'Daily Report' labels: {hits}. There is ONE Daily Report."
    )


# ── AI prompt-facing labels ────────────────────────────────────────

def test_ai_agent_prompts_do_not_reference_versioned_daily_report():
    src = (BACKEND / "services" / "dr_ai" / "agents.py").read_text(
        encoding="utf-8",
    )
    strings = list(_flatten(_visible_strings(src)))
    hits: list[tuple[str, str]] = []
    for s in strings:
        for phrase in _BANNED_PHRASES:
            if phrase in s:
                hits.append((phrase, s[:120]))
    assert not hits, (
        "TRACK 24.13 · dr_ai agent prompts must reference the single "
        f"'Daily Report' product. Found: {hits}"
    )


# ── Email rendered strings ─────────────────────────────────────────

def test_email_body_daily_report_labels_are_unversioned():
    """Scan the render_email_html / daily-report branch of pdf_render.py
    for versioned product labels. This test also lightly touches the
    lib/email* modules if they exist."""
    scanned: list[Path] = []
    for cand in ("pdf_render.py",):
        p = BACKEND / cand
        if p.exists():
            scanned.append(p)
    email_dir = BACKEND / "lib"
    if email_dir.exists():
        for p in email_dir.glob("email*.py"):
            scanned.append(p)
    hits: list[tuple[str, str, str]] = []
    for p in scanned:
        src = p.read_text(encoding="utf-8")
        strings = list(_flatten(_visible_strings(src)))
        for s in strings:
            for phrase in _BANNED_PHRASES:
                if phrase in s:
                    hits.append((str(p), phrase, s[:120]))
    assert not hits, (
        f"TRACK 24.13 · email body carries versioned Daily Report "
        f"labels: {hits}"
    )


# ── DR evidence engine emits only 'Daily Report' language ──────────

def test_dr_evidence_service_uses_unified_daily_report_language():
    root = BACKEND / "services" / "dr_evidence"
    hits: list[tuple[str, str]] = []
    for p in root.rglob("*.py"):
        src = p.read_text(encoding="utf-8")
        # Docstrings can mention "V1 legacy shape" internally to
        # describe compat adapters — that's fine. Only scan runtime
        # string literals (i.e., non-docstring strings).
        strings = list(_flatten(_visible_strings(src)))
        for s in strings:
            for phrase in _BANNED_PHRASES:
                if phrase in s:
                    hits.append((str(p), s[:120]))
    assert not hits, (
        "TRACK 24.13 · dr_evidence service must not carry versioned "
        f"Daily Report labels in runtime strings: {hits}"
    )
