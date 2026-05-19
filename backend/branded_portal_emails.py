"""
branded_portal_emails.py — shared chrome for portal onboarding/reset emails.

Iter81: unifies PM + Shop + HR welcome/reset emails so all three portals
arrive in employees' inboxes with brand-consistent chrome. The OUTER
chrome (MASCI Operations Platform eyebrow → portal sub-eyebrow → bold
h1 → divider → Inc. + phone + ForgedOps™ footer) is identical across
portals; only the per-portal accent color and sub-eyebrow text varies.

The INNER body content (greeting, credentials block, "what to do next"
list) is whatever the caller provides — the helper is just the wrapper.

Usage:
    from branded_portal_emails import render_portal_email
    html = render_portal_email(
        portal="PM",                  # "PM" | "Shop" | "HR"
        headline="Welcome to the MASCI PM Portal",
        body_inner_html="<p>Hi Chris,</p>... <table>credentials</table>...",
    )
"""
from __future__ import annotations

from html import escape as _esc
from typing import Dict


_PORTAL_THEMES: Dict[str, Dict[str, str]] = {
    "PM": {
        "sub_eyebrow": "PM Portal · Account",
        "accent": "#c8102e",         # red — matches the PM accent in the UI
    },
    "Shop": {
        "sub_eyebrow": "Shop Portal · Account",
        "accent": "#ea580c",         # amber-red — matches Shop accent
    },
    "HR": {
        "sub_eyebrow": "HR Portal · Account",
        "accent": "#7e22ce",         # purple — matches HR accent
    },
    "Safety": {
        "sub_eyebrow": "Safety Portal · Account",
        "accent": "#0e7490",         # cyan-700 — matches Safety accent in the UI
    },
    "Dispatch": {
        "sub_eyebrow": "Dispatch Portal · Account",
        "accent": "#0891b2",         # cyan-600 — matches Dispatch accent
    },
}


def render_portal_email(*, portal: str, headline: str, body_inner_html: str) -> str:
    """Wrap any portal onboarding/reset body content in the standard
    MASCI Operations Platform chrome.

    Args:
        portal: "PM" | "Shop" | "HR" — drives sub-eyebrow + accent color
        headline: bold h1 line (e.g. "Welcome to the MASCI PM Portal",
                  "Reset your password", "Your password has been reset")
        body_inner_html: pre-rendered HTML for the message body (the
                         caller is responsible for escaping its own
                         user-supplied substitutions)

    Returns:
        Full HTML document ready to pass to Resend.
    """
    theme = _PORTAL_THEMES.get(portal, _PORTAL_THEMES["PM"])
    sub_eyebrow = _esc(theme["sub_eyebrow"])
    accent = theme["accent"]

    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f8fafc;font-family:Helvetica,Arial,sans-serif;color:#0f172a;">
  <table style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:24px;">
    <tr><td>
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.25em;text-transform:uppercase;color:#c8102e;font-weight:700;">MASCI Operations Platform</div>
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:{accent};font-weight:600;margin-top:4px;">{sub_eyebrow}</div>
      <h1 style="margin:8px 0 14px;font-size:22px;font-weight:900;letter-spacing:-0.02em;line-height:1.15;">{_esc(headline)}</h1>
      <div style="font-size:14px;line-height:1.55;color:#0f172a;">{body_inner_html}</div>
      <hr style="border:0;border-top:1px solid #e2e8f0;margin:22px 0 16px 0" />
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#475569;font-weight:bold;">
        MASCI General Contractors Inc. · 386-322-4500 · mascidocs.com
      </div>
      <div style="font-family:'Courier New',monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#94a3b8;font-weight:normal;margin-top:6px;">
        Generated through MASCI Operations Platform &mdash; Powered by ForgedOps&trade; | &copy; 2026 ForgedOps&trade;
      </div>
    </td></tr>
  </table>
</body></html>"""
