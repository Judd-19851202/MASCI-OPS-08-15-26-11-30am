"""
training_center.py — Iter134. System-wide Operator Training & Guides.

Distinct from the field-worker Training Hub (/training) which teaches
labor crews. This Training Center is for operators of the platform:
- Per-portal "how to use this portal" guides (Admin, Safety, HR, Dispatch, Shop, PM)
- Integration guides (Motive, MaintainX, R2, Resend)
- Backup / reliability / deploy-recovery education

Endpoints (mounted under /api):
  GET    /training-center/guides              — list (filterable by portal)
  GET    /training-center/guide/{slug}        — single guide (full content)
  GET    /training-center/guide/{slug}/pdf    — PDF download (weasyprint)
  POST   /training-center/seed                — admin: reset to defaults
  POST   /training-center/guide               — admin: create
  PATCH  /training-center/guide/{slug}        — admin: update
  DELETE /training-center/guide/{slug}        — admin: remove

Content model:
  {
    slug, portal, title, kicker, summary, audience,
    sections: [ { heading, body_md, callouts: [...] } ],
    updated_at, version
  }
"""
from __future__ import annotations

import io
import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


PORTALS = [
    {"key": "admin",      "label": "Admin Console"},
    {"key": "safety",     "label": "Safety Portal"},
    {"key": "hr",         "label": "HR Portal"},
    {"key": "dispatch",   "label": "Dispatch Portal"},
    {"key": "shop",       "label": "Shop Portal"},
    {"key": "pm",         "label": "PM Portal"},
    {"key": "field",      "label": "Field Leadership"},
    {"key": "integration","label": "Integrations"},
    {"key": "reliability","label": "Backup & Reliability"},
]


# ─── DEFAULT GUIDE CONTENT (pre-seeded, admin-editable) ─────────────
def _g(slug, portal, title, kicker, summary, audience, sections, version="1.0"):
    return {
        "slug": slug, "portal": portal, "title": title, "kicker": kicker,
        "summary": summary, "audience": audience, "sections": sections,
        "version": version,
    }


def _s(heading, body_md, callouts=None):
    return {"heading": heading, "body_md": body_md, "callouts": callouts or []}


DEFAULT_GUIDES: List[Dict[str, Any]] = [
    # ─── ADMIN ─────────────────────────────────────────────────────
    _g(
        "admin-getting-started", "admin",
        "Admin Console — Getting Started",
        "ADMIN · ESSENTIALS",
        "Every administrative tool on the platform lives one click away in the AdminShell sidebar. This guide walks through the daily Admin workflow.",
        "Admins only.",
        [
            _s("Signing In", "Navigate to **/admin/sign-in** and enter your Admin credentials. After the first sign-in you will be redirected to **/admin/change-password** — the new password becomes your daily password."),
            _s("The Dashboard", "AdminHub shows a KPI strip with at-a-glance counts (employees, jobs, suppliers, equipment) plus a global **Doc-ID search**. Type any document ID (form record, training record, equipment ID) and jump directly to it."),
            _s("Portal Management", "Use **Admin → People** to create/edit users for HR, Safety, Dispatch, Shop, PM. Each user gets a temp password; the user is forced to set their own on first sign-in.", [
                {"kind": "tip", "text": "Resetting a user's password from the Admin Console clears their session — they must use the new temp password to sign back in."},
            ]),
            _s("System Health", "**Admin → System Health** shows backend/Mongo/R2 reachability and the most recent integration sync events. Check this first when something feels off."),
            _s("Audit Logs", "Every privileged action (password resets, role changes, data exports) is logged to the audit trail. **Admin → Audit Logs** provides search by actor, target, action, and date range."),
            _s("Deploy Recovery", "If the deployed app drifts from the preview build, run **Admin → Deploy Recovery → Resync**. This re-applies the latest configuration without losing data.", [
                {"kind": "warn", "text": "Deploy Recovery does not roll back code. For a code rollback use Emergent's chat-input 'rollback' feature."},
            ]),
        ],
    ),
    _g(
        "admin-global-search", "admin",
        "Using Global Search",
        "ADMIN · QUICK FIND",
        "Global Search is the fastest way to locate any record across the entire platform. Trains users to use it instead of hunting through portals.",
        "Admins.",
        [
            _s("Where", "Top-bar in the Admin Console, **Admin → Global Search**, or keyboard shortcut **Cmd/Ctrl + K** anywhere in /admin."),
            _s("What It Searches", "Employees, suppliers, equipment, jobs, fire extinguishers, training records, incidents, audits, and PM activity. Type any partial match — the search ranks across all collections."),
            _s("Result Cards", "Each result shows the collection, the canonical ID, a snippet of the matched fields, and a **Jump** link that deep-links to the record in the appropriate portal."),
        ],
    ),
    # ─── SAFETY ────────────────────────────────────────────────────
    _g(
        "safety-getting-started", "safety",
        "Safety Portal — Getting Started",
        "SAFETY · ESSENTIALS",
        "The Safety Portal is the close-out side of every safety form filed from the field. Read-only on intake, write-enabled on resolution.",
        "Safety Managers, Safety Coordinators.",
        [
            _s("Signing In", "Navigate to **/safety-portal/login** and enter your Safety credentials. Forgot-password is a self-serve link — clicking it emails a reset token to the email on file."),
            _s("The Dashboard", "SafetyHub shows KPIs for incidents (7d), meetings, inspections (30d), open + overdue Corrective Actions, training deficiencies, and PPE issuances."),
            _s("Corrective Actions Flow", "**Safety → Corrective Actions** is the heart of the portal. Every deficiency from incidents, audits, inspections, or training feeds in. Move tickets through **Open → In Progress → Pending Review → Closed**.", [
                {"kind": "tip", "text": "Link every CA to its source record (incident, audit, fire-extinguisher unit) so the chain of evidence is preserved."},
            ]),
            _s("Incidents & Near-Misses", "**Safety → Incidents** is a read-only roll-up of every incident submitted via the field forms (Safety Forms Portal). Filter by severity, project, employee, or date."),
            _s("Fire Extinguishers", "Each unit has its own row with last/next inspection and status. Use **Bulk Import** for legacy inventory; use **Add Extinguisher** for one-offs."),
            _s("Weekly Digest", "Every Monday at 06:00 local, the digest is emailed to safety leadership. Preview anytime from **Safety → Weekly Digest**, or send manually if you missed the auto-send."),
        ],
    ),
    _g(
        "safety-fire-ext-bulk-import", "safety",
        "Fire Extinguisher Bulk Import",
        "SAFETY · IMPORT WIZARD",
        "Migrate legacy extinguisher inventory from a spreadsheet without retyping every unit by hand.",
        "Safety Managers.",
        [
            _s("Get the Template", "Open **Safety → Fire Extinguishers → Bulk Import** and click **Download Template**. The CSV has all supported columns and an example row."),
            _s("Supported Columns", "Extinguisher ID, Serial Number, Type, Size, Location, Assigned Truck, Project Number, Inspection Date, Next Due Date, Status (Pass/Fail/Needs Service/Out of Service), Deficiencies, Corrective Action Required, Notes. Headers are case-insensitive and several aliases are accepted."),
            _s("Match Logic", "The importer matches in priority order: (1) Extinguisher ID, (2) Serial Number, (3) Truck + Location composite. Matched rows **update** the existing record; unmatched rows **create**.", [
                {"kind": "tip", "text": "If you re-upload the same file twice, the second run is all 'updates' — never duplicates."},
            ]),
            _s("Preview Before Commit", "Uploading runs a parse + validation. **Nothing is written.** Review the row-by-row plan and any errors. Click **Apply** to commit. Errors skip; valid rows go through."),
            _s("Common Errors", "Bad date formats (use YYYY-MM-DD or MM/DD/YYYY), unknown status strings, or missing both Extinguisher ID and Serial Number on the same row."),
        ],
    ),
    # ─── HR ────────────────────────────────────────────────────────
    _g(
        "hr-getting-started", "hr",
        "HR Portal — Getting Started",
        "HR · ESSENTIALS",
        "Manage employee onboarding, role assignments, certifications, and the safety-records cross-portal view.",
        "HR Managers, HR Coordinators.",
        [
            _s("Signing In", "Navigate to **/hr-portal/login**. First sign-in forces a password change."),
            _s("Adding Employees", "**HR → Employees → Add** opens the onboarding form. Required fields: legal name, email, role, primary phone. The system auto-generates the employee ID."),
            _s("Cross-Portal Safety Records", "Use **HR → Safety Records** (read-only) to see every incident, training, and PPE issuance for any employee. This is the same view Safety sees, scoped to HR-allowed fields."),
            _s("Document Management", "Onboarding PDFs, ID copies, and signed agreements live in R2 storage — uploaded via the employee detail screen. Files are private and signed-URL gated."),
        ],
    ),
    # ─── DISPATCH ──────────────────────────────────────────────────
    _g(
        "dispatch-getting-started", "dispatch",
        "Dispatch Portal — Getting Started",
        "DISPATCH · ESSENTIALS",
        "Coordinate equipment movement, manage trucking holds, and consume Motive / MaintainX integration events.",
        "Dispatch Coordinators.",
        [
            _s("Signing In", "Navigate to **/dispatch-portal/login**. Mobile-friendly — designed for tablet use in the yard."),
            _s("Equipment Board", "Each piece of equipment shows its current job, location, and last-known driver. Drag-and-drop reassignment writes to the equipment_assignments collection."),
            _s("Pending Holds", "When the Shop flags a piece as 'do not dispatch' (PM hold, repair hold, certificate-expired hold), it surfaces here. Resolve the hold before the unit can return to active rotation."),
            _s("Integration Cards", "**Motive** shows real-time driver-safety events and HOS status. **MaintainX** shows open work orders against your fleet. Both are read-only until the user supplies API tokens.", [
                {"kind": "warn", "text": "Until tokens are configured, integration cards show 'Connection not configured' — not an error."},
            ]),
        ],
    ),
    # ─── SHOP ──────────────────────────────────────────────────────
    _g(
        "shop-getting-started", "shop",
        "Shop Portal — Getting Started",
        "SHOP · ESSENTIALS",
        "Manage parts inventory, PM schedules, work orders, and fleet readiness.",
        "Shop Manager, Shop Foreman.",
        [
            _s("Signing In", "Navigate to **/shop-portal/login**. Shop users can also impersonate Dispatch in read-only mode for cross-team visibility."),
            _s("Parts Inventory", "**Shop → Parts** tracks part-on-hand, reorder thresholds, supplier links, and last-used date. Low-stock parts surface to the AdminHub KPIs."),
            _s("PM Schedules", "Each piece of equipment has a PM interval (engine-hours or calendar). When threshold hits, the unit auto-creates a 'PM Due' work order."),
            _s("Work Orders", "Open → Parts Pulled → In Repair → QA → Closed. Each step writes to the equipment service history that PMs and Dispatch can see."),
        ],
    ),
    # ─── PM ────────────────────────────────────────────────────────
    _g(
        "pm-getting-started", "pm",
        "PM Portal — Getting Started",
        "PM · ESSENTIALS",
        "Project Managers oversee jobs, JHA plans, crew assignments, daily reports, and customer billing milestones.",
        "Project Managers, PM Coordinators.",
        [
            _s("Signing In", "Navigate to **/pm-portal/login**. PMs have read-access across all other portals (Safety incidents, Shop equipment, Dispatch assignments) — scoped to their assigned jobs."),
            _s("Job Detail", "Every job lists: assigned crew, equipment on-site, open safety items, billing milestones. Use the **Daily Log** tab to review what the field submitted."),
            _s("JHA Plans", "**PM → JHA Plans** lets you draft, version, and approve Job Hazard Analysis plans. Once approved, field crews can sign-in against the plan from the public Safety Forms portal."),
        ],
    ),
    # ─── FIELD ─────────────────────────────────────────────────────
    _g(
        "field-getting-started", "field",
        "Field Leadership — Getting Started",
        "FIELD · ESSENTIALS",
        "Field Foremen / Superintendents track training, retraining, and field-level safety deficiencies.",
        "Foremen, Superintendents.",
        [
            _s("Signing In", "Navigate to **/leadership/sign-in**. After first login you'll be prompted to change your password."),
            _s("Training Records", "**Leadership → Training** tracks every cert, the date issued, the expiration, and whether retraining is due. Filter by employee, cert type, or expiration window."),
            _s("Retraining Workflow", "Mark an employee as 'needs retraining' to surface them on the Safety Portal's training deficiencies KPI. Issue retraining records and the deficiency clears automatically."),
        ],
    ),
    # ─── INTEGRATIONS ──────────────────────────────────────────────
    _g(
        "integration-motive", "integration",
        "Motive Integration",
        "INTEGRATION · MOTIVE",
        "Motive (formerly KeepTruckin) provides driver-safety events, HOS, and ELD data. The integration is read-only.",
        "Admin (setup), Dispatch (consume).",
        [
            _s("Getting an API Token", "Sign in to your Motive Fleet account → **Settings → API → Create Token**. Copy the token; it is shown once."),
            _s("Configure", "**Admin → Integrations → Motive → Configure**. Paste the token + your Motive Company ID. The next health-check sync will flip the card to 'Connected'."),
            _s("What Syncs", "Vehicles, drivers, last-known location, HOS status, safety events (hard-brake, distracted driving, speed). Stored under the `motive_events` collection with a 30-day TTL.", [
                {"kind": "tip", "text": "Safety events feed the Safety Portal's Integration Events card so Safety leadership can correlate field incidents with telematics."},
            ]),
            _s("Troubleshooting", "If the card shows 'Degraded', open **Admin → System Health** and inspect the last sync error. Most often this is an expired token — regenerate in Motive and re-save."),
        ],
    ),
    _g(
        "integration-maintainx", "integration",
        "MaintainX Integration",
        "INTEGRATION · MAINTAINX",
        "MaintainX is the CMMS for work orders, PMs, and asset history. Integration surfaces work-order status into Dispatch + Shop.",
        "Admin (setup), Shop / Dispatch (consume).",
        [
            _s("Getting an API Token", "MaintainX → **Settings → Integrations → API Tokens → New**. Scope to read-only unless you plan to write WOs back."),
            _s("Configure", "**Admin → Integrations → MaintainX → Configure**. Paste token + your MaintainX Org ID."),
            _s("What Syncs", "Work orders (open + recent), asset list, PM schedules. Cached locally for fast UI — refresh button forces re-sync."),
        ],
    ),
    _g(
        "integration-r2", "integration",
        "Cloudflare R2 (File Storage)",
        "INTEGRATION · R2",
        "R2 is the object store for every uploaded file: onboarding PDFs, JHA attachments, inspection photos.",
        "Admin only.",
        [
            _s("Why R2", "Egress-free, S3-compatible, no per-GB transfer charges. Files live in your Cloudflare account — not on the app server's disk."),
            _s("Configuration", "**Admin → Integrations → R2 → Configure**. You need: R2 endpoint URL, access key ID, secret key, bucket name. Cloudflare → R2 → Manage API Tokens to mint a key."),
            _s("Degraded Mode", "If R2 becomes unreachable, the app enters **degraded mode**: new uploads buffer locally and replay when R2 returns. Events are logged in `r2_degraded_events` with a 30-day TTL.", [
                {"kind": "warn", "text": "Buffered uploads survive a server restart, but only for 30 days. Keep R2 healthy."},
            ]),
        ],
    ),
    _g(
        "integration-resend", "integration",
        "Resend (Transactional Email)",
        "INTEGRATION · RESEND",
        "Resend powers password-reset emails, the Weekly Safety Digest, and CA assignment notifications.",
        "Admin only.",
        [
            _s("Getting an API Key", "Resend → **API Keys → Create**. Scope: sending domain restricted to your verified domain."),
            _s("Configure", "**Admin → Integrations → Resend → Configure**. Paste API key + verified 'from' address."),
            _s("Failure Behavior", "If Resend is down, password-reset tokens are still generated and logged to **Admin → Audit Logs**. An admin can copy the reset URL out of the audit log and send it manually."),
        ],
    ),
    # ─── BACKUP & RELIABILITY ──────────────────────────────────────
    _g(
        "reliability-backups", "reliability",
        "MongoDB Backups",
        "RELIABILITY · BACKUPS",
        "MASCI's operational data lives in MongoDB. This guide describes the backup strategy and recovery drill.",
        "Admin, Ops.",
        [
            _s("What Is Backed Up", "All collections via daily `mongodump` to R2 (separate bucket from app uploads). Retention: 30 daily, 12 weekly, 12 monthly snapshots."),
            _s("Restore Drill", "Quarterly: spin a staging app, restore the most-recent snapshot, verify counts match production within 1%. Document the drill in **Admin → Audit Logs → Manual Entry**."),
            _s("TTL Collections", "These collections **self-prune** at 30 days and need not be backed up: `r2_degraded_events`, `digest_runs`, `system_health_events`, `motive_events`. They are operational telemetry, not records of record.", [
                {"kind": "tip", "text": "If you need long-term retention of these events, change the TTL index expireAfterSeconds before relying on the data."},
            ]),
        ],
    ),
    _g(
        "reliability-deploy-recovery", "reliability",
        "Deploy Recovery",
        "RELIABILITY · DEPLOY",
        "If the deployed app and the preview environment drift apart — different KPI counts, missing portals, stale config — Deploy Recovery is the first line of defense.",
        "Admin only.",
        [
            _s("Diagnose First", "**Admin → System Health → Recent**. Look for: backend reachable but reporting old version, R2 unreachable, Mongo connection slow. Each of these has a distinct fix."),
            _s("Recovery Steps", "**Admin → Deploy Recovery → Resync**. Re-applies environment variables, refreshes integration tokens, rebuilds the static frontend cache. Non-destructive — no data is touched."),
            _s("When To Roll Back", "If Resync doesn't help and System Health shows a recent failed deploy, use the Emergent **rollback** feature in the chat input. This is free and reverts to the previous working checkpoint."),
        ],
    ),
    _g(
        "reliability-incident-response", "reliability",
        "Incident Response Playbook",
        "RELIABILITY · ON-CALL",
        "What to do when the platform is down or degraded during business hours.",
        "Admin, Ops.",
        [
            _s("Triage", "1. Reproduce the issue from a different device + network. 2. Check **System Health** — is backend reachable? Mongo? R2? 3. Check **Audit Logs** for a recent privileged action that could have broken state."),
            _s("Common Causes", "**Expired R2 token** → re-save in Integrations. **Mongo TTL backlog** → wait 60s, TTL prune runs every minute. **Email not sending** → check Resend dashboard for paused sending domain."),
            _s("Communicate", "Post a one-line update to the team chat as soon as you have a hypothesis. Update again on confirmed cause and ETA. Document the full timeline in **Admin → Audit Logs → Manual Entry** after resolution."),
        ],
    ),
]


# ─── MODELS ────────────────────────────────────────────────────────
class GuideSection(BaseModel):
    heading: str = Field(..., min_length=1, max_length=200)
    body_md: str = Field(..., min_length=1)
    callouts: List[Dict[str, Any]] = Field(default_factory=list)


class GuideUpsert(BaseModel):
    slug: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-z0-9-]+$")
    portal: str = Field(..., min_length=2, max_length=40)
    title: str = Field(..., min_length=1, max_length=200)
    kicker: Optional[str] = Field(default="", max_length=120)
    summary: Optional[str] = Field(default="", max_length=2000)
    audience: Optional[str] = Field(default="", max_length=400)
    sections: List[GuideSection] = Field(default_factory=list)
    version: Optional[str] = Field(default="1.0", max_length=20)


class GuidePatch(BaseModel):
    portal: Optional[str] = None
    title: Optional[str] = None
    kicker: Optional[str] = None
    summary: Optional[str] = None
    audience: Optional[str] = None
    sections: Optional[List[GuideSection]] = None
    version: Optional[str] = None


# ─── PDF RENDERING ─────────────────────────────────────────────────
def _md_to_html(text: str) -> str:
    """Tiny markdown subset — **bold**, *italic*, `code`, line breaks.
    Enough for the seeded content; admin-edited content uses the same."""
    if not text:
        return ""
    # Escape HTML first
    out = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    # bold, italic, code (do bold before italic since ** subsumes *)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*(.+?)\*", r"<em>\1</em>", out)
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out)
    # paragraphs split by blank lines, single newlines become <br/>
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", out) if p.strip()]
    return "".join(f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in paragraphs)


def _render_guide_html(guide: Dict[str, Any]) -> str:
    sections_html = []
    for s in guide.get("sections", []):
        callouts_html = ""
        for c in (s.get("callouts") or []):
            kind = (c.get("kind") or "tip").lower()
            cls = {"tip": "callout-tip", "warn": "callout-warn"}.get(kind, "callout-tip")
            callouts_html += f'<div class="{cls}"><strong>{kind.upper()}:</strong> {_md_to_html(c.get("text", ""))}</div>'
        sections_html.append(
            f'<h2>{s.get("heading", "")}</h2>{_md_to_html(s.get("body_md", ""))}{callouts_html}',
        )
    return f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8" />
<style>
  @page {{ size: letter; margin: 0.75in; }}
  body {{ font-family: 'Helvetica', Arial, sans-serif; color: #0f172a; font-size: 11pt; line-height: 1.5; }}
  .kicker {{ font-family: 'Courier New', monospace; letter-spacing: 0.18em; font-size: 9pt; color: #475569; text-transform: uppercase; }}
  h1 {{ font-size: 22pt; margin: 4pt 0 6pt 0; color: #0f172a; }}
  h2 {{ font-size: 14pt; margin: 18pt 0 4pt 0; color: #0c4a6e; border-bottom: 2px solid #e2e8f0; padding-bottom: 3pt; }}
  .summary {{ font-style: italic; color: #334155; margin-bottom: 4pt; }}
  .meta {{ color: #64748b; font-size: 9pt; margin-bottom: 18pt; }}
  p {{ margin: 6pt 0; }}
  code {{ background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }}
  .callout-tip  {{ background: #ecfeff; border-left: 4px solid #0e7490; padding: 8pt 10pt; margin: 8pt 0; font-size: 10pt; }}
  .callout-warn {{ background: #fef3c7; border-left: 4px solid #b45309; padding: 8pt 10pt; margin: 8pt 0; font-size: 10pt; }}
  .footer {{ position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8pt; color: #94a3b8; }}
</style></head>
<body>
  <div class="kicker">{guide.get("kicker", "")}</div>
  <h1>{guide.get("title", "")}</h1>
  <p class="summary">{_md_to_html(guide.get("summary", ""))}</p>
  <p class="meta">Audience: {guide.get("audience", "—")} &nbsp;·&nbsp; Version {guide.get("version", "1.0")} &nbsp;·&nbsp; Updated {guide.get("updated_at", "")}</p>
  {''.join(sections_html)}
  <div class="footer">MASCI Operations Platform · Training Center</div>
</body></html>
"""


# ─── ROUTER ────────────────────────────────────────────────────────
def build_training_center_router(db, require_admin: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/training-center", tags=["training-center"])

    async def _seed_if_empty():
        """Idempotent seed: upsert any DEFAULT_GUIDES slug that is missing
        from the collection. Preserves admin-edited content because we use
        $setOnInsert — existing docs are never overwritten."""
        now = datetime.now(timezone.utc).isoformat()
        existing_slugs = set()
        async for d in db.training_guides.find({}, {"_id": 0, "slug": 1}):
            existing_slugs.add(d.get("slug"))
        missing = [g for g in DEFAULT_GUIDES if g["slug"] not in existing_slugs]
        if not missing:
            return False
        docs = [{**g, "updated_at": now, "is_default": True} for g in missing]
        await db.training_guides.insert_many(docs)
        logger.info("[training-center] seeded %d new default guide(s)", len(docs))
        return True

    @router.get("/portals")
    async def list_portals():
        await _seed_if_empty()
        counts = {}
        async for d in db.training_guides.find({}, {"_id": 0, "portal": 1}):
            counts[d["portal"]] = counts.get(d["portal"], 0) + 1
        return {
            "portals": [
                {**p, "count": counts.get(p["key"], 0)}
                for p in PORTALS
            ],
        }

    @router.get("/guides")
    async def list_guides(portal: Optional[str] = Query(default=None)):
        await _seed_if_empty()
        q: Dict[str, Any] = {}
        if portal:
            q["portal"] = portal
        cursor = db.training_guides.find(
            q, {"_id": 0, "sections": 0},  # exclude heavy section blob from list
        ).sort([("portal", 1), ("title", 1)])
        out = []
        async for d in cursor:
            out.append(d)
        return {"guides": out, "total": len(out)}

    @router.get("/guide/{slug}")
    async def get_guide(slug: str):
        await _seed_if_empty()
        g = await db.training_guides.find_one({"slug": slug}, {"_id": 0})
        if not g:
            raise HTTPException(status_code=404, detail="Guide not found")
        return g

    @router.get("/guide/{slug}/pdf")
    async def get_guide_pdf(slug: str):
        await _seed_if_empty()
        g = await db.training_guides.find_one({"slug": slug}, {"_id": 0})
        if not g:
            raise HTTPException(status_code=404, detail="Guide not found")
        try:
            from weasyprint import HTML  # noqa: PLC0415
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"weasyprint missing: {e}") from e
        html = _render_guide_html(g)
        pdf_bytes = HTML(string=html).write_pdf()
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{slug}.pdf"'},
        )

    @router.post("/seed", dependencies=[Depends(require_admin)])
    async def seed_defaults(reset: bool = False):
        if reset:
            await db.training_guides.delete_many({"is_default": True})
        await _seed_if_empty()
        count = await db.training_guides.count_documents({})
        return {"ok": True, "total": count, "reset": reset}

    @router.post("/guide", dependencies=[Depends(require_admin)])
    async def create_guide(body: GuideUpsert):
        existing = await db.training_guides.find_one({"slug": body.slug}, {"_id": 1})
        if existing:
            raise HTTPException(status_code=409, detail="Slug already exists")
        now = datetime.now(timezone.utc).isoformat()
        doc = body.model_dump()
        doc["updated_at"] = now
        doc["is_default"] = False
        await db.training_guides.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @router.patch("/guide/{slug}", dependencies=[Depends(require_admin)])
    async def update_guide(slug: str, body: GuidePatch):
        patch = {k: v for k, v in body.model_dump(exclude_none=True).items()}
        if not patch:
            raise HTTPException(status_code=400, detail="No fields to update")
        patch["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.training_guides.update_one({"slug": slug}, {"$set": patch})
        if not res.matched_count:
            raise HTTPException(status_code=404, detail="Guide not found")
        g = await db.training_guides.find_one({"slug": slug}, {"_id": 0})
        return g

    @router.delete("/guide/{slug}", dependencies=[Depends(require_admin)])
    async def delete_guide(slug: str):
        res = await db.training_guides.delete_one({"slug": slug})
        if not res.deleted_count:
            raise HTTPException(status_code=404, detail="Guide not found")
        return {"ok": True, "deleted": slug}

    return router


__all__ = ["build_training_center_router", "PORTALS", "DEFAULT_GUIDES"]
