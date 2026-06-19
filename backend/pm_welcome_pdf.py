"""
pm_welcome_pdf.py — Per-PM welcome / onboarding letter.

Single-page WeasyPrint PDF the admin hands to each PM along with their
temp password. Walks them through:
  1. The new login flow (email + temp pw → forced password rotation).
  2. What they'll see on the portal (tiles scoped to their assigned jobs).
  3. How auto-email routing works (compliance vs operational, co-PMs).
  4. What to do if they forget their password.

The temp password is rendered ONCE in a tear-off block at the bottom so
the admin can hand it to the PM in person and shred the rest.

Usage:
    from pm_welcome_pdf import render_pm_welcome_pdf
    pdf = render_pm_welcome_pdf(pm_doc, temp_password="abc123", portal_url="https://mascidocs.com")
"""
from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from weasyprint import HTML


# ──────────────────────────────────────────────────────────────────────
# Logo loaded from /app/frontend/public so the PDF embeds the same red-M
# mark + full lockup the rest of the app uses.
# ──────────────────────────────────────────────────────────────────────
_PUBLIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public"


def _b64_data_uri(filename: str, mime: str = "image/png") -> str:
    p = _PUBLIC_DIR / filename
    if not p.exists():
        return ""
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def render_pm_welcome_pdf(
    pm: dict,
    *,
    temp_password: Optional[str] = None,
    portal_url: Optional[str] = None,
) -> bytes:
    """Render the welcome PDF for one PM. ``pm`` is the public PM doc
    (must include ``name`` and ``email``). ``temp_password`` is the plain
    text temp pw the admin just generated. ``portal_url`` defaults to
    PORTAL_URL env (which the deploy already sets to https://mascidocs.com).
    """
    name = (pm.get("name") or "").strip() or "Project Manager"
    email = (pm.get("email") or "").strip().lower()
    portal = (portal_url or os.environ.get("PORTAL_URL", "https://mascidocs.com")).rstrip("/")
    today = _today_iso()

    m_mark = _b64_data_uri("masci-mark.png")
    mark = _b64_data_uri("masci-mark.png")

    # If no temp password is provided (e.g. admin reusing this PDF),
    # blank the tear-off so paper isn't wasted on a credential field.
    pw_block = ""
    if temp_password:
        pw_block = f"""
        <div class="tearoff">
          <div class="tearoff-line"></div>
          <div class="tearoff-body">
            <div class="tearoff-tag">Hand-deliver only · Tear &amp; shred after PM logs in</div>
            <div class="tearoff-grid">
              <div>
                <div class="tearoff-label">Account</div>
                <div class="tearoff-value mono">{email}</div>
              </div>
              <div>
                <div class="tearoff-label">Temporary password</div>
                <div class="tearoff-value mono pw">{temp_password}</div>
              </div>
            </div>
            <div class="tearoff-note">
              First login will force you to choose your own 6+ character password.
              The temporary one above stops working the moment you do.
            </div>
          </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Welcome — MASCI PM Portal</title>
<style>
  @page {{ size: Letter; margin: 0.5in; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; font-family: 'Helvetica', 'Arial', sans-serif; color: #1e293b; font-size: 10.5pt; line-height: 1.4; }}
  body {{ background: #fff; }}
  /* Header */
  .header {{ display: flex; align-items: center; justify-content: space-between; border-bottom: 4px solid #b91c1c; padding-bottom: 10px; margin-bottom: 18px; }}
  .lockup {{ height: 38px; }}
  .header-meta {{ text-align: right; font-family: 'Courier New', monospace; font-size: 8pt; color: #64748b; line-height: 1.3; }}
  .header-meta .tag {{ color: #b91c1c; font-weight: bold; letter-spacing: 0.18em; text-transform: uppercase; }}

  h1 {{ font-size: 22pt; font-weight: 900; margin: 6px 0 4px; color: #0f172a; letter-spacing: -0.01em; }}
  h1 .name {{ color: #b91c1c; }}
  .lede {{ font-size: 10pt; color: #475569; margin: 0 0 14px; max-width: 92%; }}

  /* Step list */
  ol.steps {{ list-style: none; counter-reset: step; padding: 0; margin: 0 0 14px; }}
  ol.steps > li {{ counter-increment: step; position: relative; padding: 8px 0 8px 38px; border-top: 1px solid #e2e8f0; }}
  ol.steps > li:first-child {{ border-top: none; }}
  ol.steps > li::before {{
    content: counter(step);
    position: absolute; left: 0; top: 8px;
    width: 26px; height: 26px; border-radius: 50%;
    background: #b91c1c; color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 11pt; font-family: 'Courier New', monospace;
  }}
  ol.steps .step-title {{ font-weight: 800; font-size: 11pt; color: #0f172a; margin-bottom: 1px; }}
  ol.steps .step-body {{ color: #475569; font-size: 9.5pt; }}
  ol.steps code {{ background: #fef3c7; color: #92400e; padding: 1px 5px; border-radius: 2px; font-size: 9pt; }}

  /* Two-column splits */
  .split {{ display: flex; gap: 14px; margin-bottom: 14px; }}
  .col {{ flex: 1; border: 1px solid #cbd5e1; border-radius: 4px; padding: 10px 12px; }}
  .col h3 {{ margin: 0 0 6px; font-size: 9pt; font-family: 'Courier New', monospace; letter-spacing: 0.18em; text-transform: uppercase; color: #b91c1c; font-weight: 800; }}
  .col p {{ margin: 0 0 4px; font-size: 9pt; color: #334155; line-height: 1.45; }}
  .col strong {{ color: #0f172a; }}
  .col ul {{ margin: 4px 0 0; padding-left: 16px; font-size: 9pt; color: #334155; }}
  .col ul li {{ margin-bottom: 2px; }}

  /* Tear-off credential block */
  .tearoff {{ margin-top: 12px; }}
  .tearoff-line {{ border-top: 2px dashed #cbd5e1; margin-bottom: 6px; position: relative; }}
  .tearoff-line::after {{
    content: '✂'; position: absolute; left: 50%; top: -10px;
    transform: translateX(-50%);
    background: #fff; padding: 0 8px;
    font-size: 12pt; color: #94a3b8;
  }}
  .tearoff-body {{ background: #0f172a; color: #f1f5f9; border-radius: 4px; padding: 14px 16px; }}
  .tearoff-tag {{ font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 0.22em; text-transform: uppercase; color: #fbbf24; font-weight: 700; }}
  .tearoff-grid {{ display: flex; gap: 18px; margin-top: 10px; }}
  .tearoff-grid > div {{ flex: 1; }}
  .tearoff-label {{ font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 0.18em; text-transform: uppercase; color: #94a3b8; margin-bottom: 3px; }}
  .tearoff-value {{ font-size: 12pt; font-weight: 800; }}
  .tearoff-value.pw {{ color: #34d399; letter-spacing: 0.05em; }}
  .mono {{ font-family: 'Courier New', monospace; }}
  .tearoff-note {{ margin-top: 10px; font-size: 8.5pt; color: #cbd5e1; line-height: 1.5; }}

  /* Footer */
  .footer {{ margin-top: 14px; display: flex; align-items: center; justify-content: space-between; padding-top: 8px; border-top: 1px solid #e2e8f0; font-family: 'Courier New', monospace; font-size: 7.5pt; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase; }}
  .footer .mark {{ height: 18px; opacity: 0.85; }}
</style>
</head>
<body>

  <div class="header">
    <img class="lockup" src="{m_mark}" alt="MASCI" style="width: 64px; height: auto;" />
    <div class="header-meta">
      <div class="tag">PM Portal · Welcome</div>
      <div>Issued: {today}</div>
      <div>{portal}</div>
    </div>
  </div>

  <h1>Welcome to the new portal, <span class="name">{name}</span>.</h1>
  <p class="lede">
    The shared PM password is going away. From today, you sign in with <strong>your own work email and password</strong> — only the jobs you're assigned to (primary or co-PM) show up on your dashboard, and every report that gets filed against those jobs auto-emails you.
  </p>

  <ol class="steps">
    <li>
      <div class="step-title">Open the portal &amp; sign in</div>
      <div class="step-body">
        Go to <code>{portal}/pm/login</code>. Your username is your work email — <strong>{email}</strong>. Use the temporary password the office handed you (see tear-off below).
      </div>
    </li>
    <li>
      <div class="step-title">Pick your own password</div>
      <div class="step-body">
        First login will force you to <code>/pm/change-password</code>. Pick anything 6+ characters that you'll remember. The temporary password stops working the second you save the new one. <strong>Don't share it with anyone</strong> — admin can reset it for you any time.
      </div>
    </li>
    <li>
      <div class="step-title">Land on your dashboard</div>
      <div class="step-body">
        You'll only see the jobs you're assigned to (primary OR co-PM). Same for Daily Reports, Site Inspections, Safety Meetings, Incidents, JHAs, Equipment Pre-Op, QA/QC, and the P&amp;L snapshot. Other PMs' work is invisible to you.
      </div>
    </li>
    <li>
      <div class="step-title">Watch your inbox</div>
      <div class="step-body">
        Every Daily Report and Equipment Pre-Op filed against your jobs auto-emails you. Compliance forms (Inspections, Meetings, Incidents, JHAs, QA/QC) email you <em>and</em> the office. Co-PMs assigned to a job get the same emails CC'd — so the whole team's in the loop.
      </div>
    </li>
  </ol>

  <div class="split">
    <div class="col">
      <h3>What you'll see</h3>
      <ul>
        <li><strong>Records &amp; Forms</strong> — every safety form filed on your jobs</li>
        <li><strong>Project P&amp;L Snapshot</strong> — labor hours, sub hours, materials per job</li>
        <li><strong>Daily Reports</strong>, <strong>Equipment Pre-Op</strong>, <strong>QA/QC</strong></li>
        <li><strong>Active Jobs Master</strong> — your assigned jobs only</li>
      </ul>
    </div>
    <div class="col">
      <h3>If you forget your password</h3>
      <p>Text or call the office. An admin can issue a fresh temporary password from the console in under 30 seconds. Old password is killed instantly when the new one is issued.</p>
      <p style="margin-top:6px;"><strong>Locked out?</strong> Same fix — just call. Don't keep retyping; the system will lock the account after several wrong tries.</p>
    </div>
  </div>

  {pw_block}

  <div class="footer">
    <span>MASCI · Project Management Portal</span>
    <img class="mark" src="{mark}" alt="MASCI" />
    <span>{today}</span>
  </div>
  {_t1541_audit("pm_welcome", pm)}
</body>
</html>"""

    return HTML(string=html, base_url=str(_PUBLIC_DIR)).write_pdf()


def _t1541_audit(source_module: str, pm: dict) -> str:
    """TRACK 15.42 · audit block append helper. Additive — last in body."""
    try:
        from pdf_branding import build_audit_block_html
        return build_audit_block_html(
            record_id=(pm.get("id") or pm.get("email") or "—"),
            source_module=source_module,
            project=None,
            generated_by="admin",
        )
    except Exception:
        return ""
