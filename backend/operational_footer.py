"""iter437 / Phase IV-BETA.3-P1C · Communication footer standardization.

Renders the 3-line operational footer mandated by
COMMUNICATION_UNIFICATION_DOCTRINE.md §A.IV. The footer is intentionally
restrained — no oversized branding, no signature, no unsubscribe in
transactional context.

Contract (locked by tests/test_iter437_footer_standardization.py):

    MASCI
    automated operational notice
    do-not-reply

When a portal context is provided (e.g. `portal="HR"`, `portal="PM"`),
the second line becomes `automated operational notice · {Workspace}`,
where {Workspace} is the canonical Track 18.04 user-facing workspace
name resolved from the internal code (HR → Human Resources,
Dispatch → Transportation Operations, etc.) so an operator scanning a
long thread can identify which workspace produced the message.
Optional `doc_id` adds an inbox-Cmd-F target on line 3.

No frontend changes. No notification engine changes. Pure helper.
"""
from __future__ import annotations

from html import escape as _esc
from typing import Optional


# Track 18.04 · Internal portal codes → canonical user-facing workspace
# names. Unknown codes fall back to `{code} Workspace` so legacy callers
# don't break.
_WORKSPACE_NAME = {
    "PM": "Project Management",
    "HR": "Human Resources",
    "Shop": "Shop Operations",
    "Safety": "Safety Operations",
    "Dispatch": "Transportation Operations",
    "Admin": "Administration",
    "Leadership": "Field Leadership",
}


def _workspace_label(code: str) -> str:
    return _WORKSPACE_NAME.get(code, f"{code} Workspace")


def render_operational_footer_html(
    *,
    portal: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> str:
    """Return the canonical 3-line footer as restrained inline-styled HTML."""
    line2 = "automated operational notice"
    if portal:
        line2 = f"{line2} \u00b7 {_esc(_workspace_label(portal))}"
    line3 = "do-not-reply"
    if doc_id:
        line3 = f"{line3} \u00b7 {_esc(doc_id)}"

    return (
        '<table cellpadding="0" cellspacing="0" '
        'style="margin-top:18px;border-top:1px solid #e2e8f0;'
        'padding-top:10px;width:100%;">'
        '<tr><td style="font-family:Arial,sans-serif;'
        'font-size:11px;color:#64748b;line-height:1.5;text-align:left;">'
        '<div style="color:#0f172a;font-weight:700;letter-spacing:0.04em;">MASCI</div>'
        f'<div>{line2}</div>'
        f'<div>{line3}</div>'
        '</td></tr></table>'
    )


def render_operational_footer_text(
    *,
    portal: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> str:
    """Plain-text variant for log lines, plain-text email parts, and
    governance test assertions."""
    line2 = "automated operational notice"
    if portal:
        line2 = f"{line2} \u00b7 {_workspace_label(portal)}"
    line3 = "do-not-reply"
    if doc_id:
        line3 = f"{line3} \u00b7 {doc_id}"
    return f"MASCI\n{line2}\n{line3}"


__all__ = [
    "render_operational_footer_html",
    "render_operational_footer_text",
]
