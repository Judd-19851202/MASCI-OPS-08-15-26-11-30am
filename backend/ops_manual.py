"""Internal System Owner & Operations Manual — MASCI HUB

Generates both PDF (WeasyPrint) and DOCX (python-docx) for The Judd Group LLC.
Not a customer-facing document. Admin-only download via /api/admin/ops-manual.{pdf,docx}.

Content is kept in structured Python data (SECTIONS) so both renderers emit the
same copy — single source of truth. Tables are rendered as real tables in both
formats (HTML `<table>` for PDF, `doc.add_table` for DOCX).

Re-generated on every request — the document is small (~15-20 pages) so we
don't bother caching.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import List, Tuple, Union

from weasyprint import HTML
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ---------------------------------------------------------------------------
# Content definition — single source of truth.
#
# Each section is (heading, body_blocks). A body_block is either:
#   • a paragraph string
#   • ("h3", "subheading text")
#   • ("list", [item1, item2, ...])
#   • ("table", [headers...], [[row1_cells], [row2_cells], ...])
# ---------------------------------------------------------------------------

# Type alias for clarity
Block = Union[str, tuple]

SECTIONS: List[Tuple[str, List[Block]]] = [
    ("1. System Overview", [
        "MASCI HUB is the field-operations and safety-documentation platform used by MASCI General Contractors Inc. and MASCI Corporation. It is delivered to end users at the customer-branded URL mascidocs.com. The platform captures, routes, and archives the paperwork that construction crews, mechanics, project managers, and office staff generate every day — Daily Reports, Equipment Pre-Op inspections, Site Safety Inspections, Safety Meetings, JHAs, Incident Reports, Training Packets, and the underlying master data (equipment, employees, suppliers, vendors, jobs, PM assignments).",
        ("h3", "Core Modules"),
        ("table",
            ["Module", "Primary Audience", "What It Does"],
            [
                ["Field Hub", "Foremen, crews, superintendents", "Daily Reports, Equipment Pre-Op, photos, signatures, crew hours, activities"],
                ["Safety Hub", "Safety officers, foremen", "Site inspections, toolbox talks, JHAs, incident reports, trench box tracking, safety cards"],
                ["Shop Hub", "Mechanics, shop supervisors", "Review failed pre-ops, sign off on repairs, parts + work orders"],
                ["PM Hub", "Project managers", "Scoped dashboards per assigned project — daily-report summaries, job-specific incidents, notifications"],
                ["Admin Hub", "Office / The Judd Group", "User roles, master lists (equipment, employees, subs, vendors), integrity checks, backups, training-video URL registry"],
                ["Training Hub", "All personnel (field public, shop/PM/admin gated)", "Step-by-step lessons, bilingual EN/ES content, PDF packets, scan-&-go QR posters"],
            ]),
        ("h3", "Primary Workflows"),
        ("list", [
            "Daily Report — foreman fills at end of shift → auto-routes to assigned PM via email → stored against the job.",
            "Equipment Pre-Op — operator fills at start of shift → FAIL items with photos route to Shop queue → shop signs off before unit returns to service.",
            "Safety Inspection / JHA / Incident — filed as it happens → PM + safety officer notified → archived for OSHA record-keeping.",
            "Training — crews scan a trailer QR code → open /training/field (no login) → watch/read/print the lesson → gated tracks (Shop/PM/Admin) require the matching portal password.",
        ]),
        ("h3", "User Tiers"),
        ("list", [
            "Public (field crews) — no login required for Field forms. Posters use QR codes to deep-link into specific forms.",
            "Shop — gated by SHOP_PASSWORD. Access to Shop Hub + Shop training.",
            "PM — gated by PM_PASSWORD. Scoped dashboards for assigned projects only.",
            "Admin — gated by ADMIN_PASSWORD. Full platform control including backups and user management.",
        ]),
    ]),

    ("2. Full System Architecture", [
        ("h3", "Frontend"),
        "React 18 single-page application, bundled with CRACO / Create React App. Tailwind CSS for styling. shadcn/ui component library. React Router for client-side routing. Built output is a ~1.6 MB minified main bundle + code-split chunks, served as static files from the hosting provider. Mobile-first: every form is designed for iPhone SE through desktop. Native HTML5 `<video>` for training videos, not iframes, so field crews on 4G get proper playback controls.",
        ("h3", "Backend"),
        "FastAPI (Python 3.11) running under uvicorn. Single API router at /api prefix. Async endpoints backed by Motor (async MongoDB driver). WeasyPrint for PDF generation. Resend SDK for email. bcrypt for password hashing. JWT for session tokens (signed with JWT_SECRET). Rate limiting and login lockout built in (configurable via env).",
        ("h3", "Database"),
        "MongoDB. Production runs on MongoDB Atlas (managed, free tier sufficient at current scale). Local development and preview environments may use an in-container MongoDB; that instance is ephemeral and wiped on every redeploy — this is why Atlas is mandatory in production.",
        ("h3", "Key Collections"),
        ("table",
            ["Collection", "Purpose"],
            [
                ["users", "Login/role records"],
                ["equipment_master", "Fleet registry"],
                ["employees", "Crew roster"],
                ["suppliers / vendors", "Master lists"],
                ["jobs / projects", "Active job registry + PM assignments"],
                ["daily_reports", "Daily report submissions"],
                ["equipment_inspections", "Pre-Op records + FAIL items"],
                ["shop_signoffs", "Shop clearance history"],
                ["incident_reports", "Accidents / near-misses"],
                ["safety_inspections / jhas / meetings", "Safety documentation"],
                ["training_videos", "Config doc: { slug → URL } map"],
                ["training_hits", "Analytics of who/when scanned a poster"],
                ["backup_runs", "Scheduled-backup audit log"],
                ["auth_events", "Login / lockout history"],
            ]),
        ("h3", "File Handling"),
        "User uploads (photos, signatures) are written to local disk at /app/backend/uploads. Static safety-card PDFs live at /app/backend/static/safety-cards. Generated PDFs (training packets, records) are rendered in-memory and streamed to the client — not persisted. Future Version 2 should migrate uploads to S3-compatible object storage so container restarts do not risk user content (see Section 11).",
        ("h3", "Email System"),
        "Resend (resend.com) handles all outbound mail — PM routing of daily reports, shop alerts on FAIL pre-ops, bulk safety-card distribution, twice-daily backup emails, and outage alerts. Sender/reply addresses are env-configured (SENDER_EMAIL / REPLY_TO_EMAIL). Emails carry attached PDFs rendered at request time.",
        ("h3", "PDF Generation"),
        "Two generators: (1) /app/backend/pdf_render.py for single records (inspections, reports, incidents); (2) /app/backend/training_pdf.py for multi-page training packets. Both use WeasyPrint with Letter size, custom @page CSS for per-page footer + page count, and a last-page ownership clarification block. Footer text is language-aware: _css_for_lang(lang) injects EN or ES attribution.",
    ]),

    ("3. Third-Party / Supporting Systems", [
        "Every external dependency is listed below. Critical Dependency = impact if the service is down or dropped.",
        ("table",
            ["Service", "Purpose", "Integration", "Criticality"],
            [
                ["Emergent (hosting)", "Native deployment platform — builds and hosts frontend + backend + MongoDB", "CI-style build on push, serves mascidocs.com + preview URLs", "HIGH — primary runtime"],
                ["MongoDB Atlas", "Production database (managed)", "Backend connects via MONGO_URL env var", "HIGH — all data lives here"],
                ["Resend", "Transactional email (PM routing, backups, bulk)", "Resend Python SDK, key RESEND_API_KEY", "HIGH — no email = no PM routing, no backups"],
                ["Cloudflare", "CDN + SSL in front of mascidocs.com", "DNS + automatic HTTPS certificate", "HIGH — TLS + caching"],
                ["Domain registrar", "Ownership of mascidocs.com", "Annual renewal, DNS records point at Emergent", "HIGH — losing it = losing the brand URL"],
                ["Emergent LLM Key", "Access to Gemini/OpenAI/Claude via a single key", "Used for AI-assisted content (translations, future features)", "MEDIUM — optional enrichment, fallback to no-AI path"],
                ["WeasyPrint", "Python PDF renderer (open-source, self-hosted)", "Pinned in requirements.txt", "MEDIUM — generates PDFs; replaceable with wkhtmltopdf if EOL"],
                ["python-docx", "DOCX generator for this manual + future exports", "Pinned in requirements.txt", "LOW — only used for operator docs"],
                ["GitHub (via Save-to-GitHub)", "Source control backup — captures every commit", "Triggered manually from Emergent deployment dashboard", "MEDIUM — recovery anchor if Emergent platform is ever abandoned"],
                ["Customer Assets CDN", "Asset hosting for training videos (current provider = Emergent asset storage)", "Video URLs registered in training_videos Mongo doc", "MEDIUM — videos are non-blocking; replaceable with any HTTPS MP4 host"],
            ]),
    ]),

    ("4. Cost Breakdown", [
        "All figures as of 2026-05. Usage-based costs may rise with crew growth.",
        ("h3", "Per-Service Monthly Cost"),
        ("table",
            ["System", "Purpose", "Monthly Cost (USD)", "Scaling Notes"],
            [
                ["Emergent Standard plan", "Build, host, deploy mascidocs.com + preview", "$20.00", "100 credits/mo included; heavy deploy days can consume 3-5 credits. Pro plan ($200) buys badge-removal + higher limits."],
                ["MongoDB Atlas (M0 Free tier)", "Production database", "$0.00", "M0 = 512 MB storage, shared CPU. Upgrade to M10 (~$57/mo) when storage exceeds 400 MB or crew > 50."],
                ["Resend", "Transactional email", "$0–$20", "Free tier = 3,000 emails/mo. $20/mo tier = 50,000 emails/mo. MASCI should stay under free tier unless bulk safety-card emails exceed 100 recipients weekly."],
                ["Cloudflare (Free)", "CDN, SSL, DNS protection", "$0.00", "Free tier fully covers current traffic. Pro ($20/mo) only needed if image hotlinking or DDoS becomes an issue."],
                ["Domain registrar (mascidocs.com)", "Annual domain renewal", "~$1.20 (annualised)", "$12-15/year typical (.com)."],
                ["Emergent LLM Key usage", "AI text via Universal Key", "$0-5", "Pay-per-use. Small model calls are $0.001-0.01 each. Top up via Profile → Universal Key."],
                ["Training video storage", "Customer-asset CDN (Emergent-hosted)", "$0.00", "Included in Emergent plan. If video library grows past ~20 videos (~500 MB) consider moving to dedicated S3 + CloudFront."],
                ["Operator time (The Judd Group)", "Admin / maintenance labor", "variable", "1-4 hours/mo at current scale. Rises to 8-10 hours/mo when Daily Reports > 100/week."],
            ]),
        ("h3", "Usage Tier Estimates"),
        ("table",
            ["Tier", "Users", "Jobs", "Reports/Month", "Storage", "Total Monthly"],
            [
                ["Low (current MASCI)", "10-25", "5-10 active", "200-400", "< 300 MB", "$20-40"],
                ["Medium", "25-75", "10-25 active", "500-1,500", "300 MB - 2 GB", "$60-120"],
                ["High", "75-200", "25-80 active", "2,000-6,000", "2-10 GB", "$200-450"],
            ]),
        "Notes: Moving from Low → Medium typically only requires upgrading MongoDB Atlas from M0 free to M10 ($57). Moving Medium → High adds Pro-tier Emergent + Resend paid tier + likely S3 migration.",
    ]),

    ("5. Deployment & Environments", [
        ("h3", "Three Environments"),
        ("table",
            ["Environment", "URL", "Purpose"],
            [
                ["Development", "Local container (in-session)", "Live-edit preview while the agent is working — hot-reload, ephemeral DB"],
                ["Preview", "*.preview.emergentagent.com", "Latest committed code, shared database state, visible Emergent badge"],
                ["Production", "https://mascidocs.com", "Live site for MASCI crews. Atlas-backed, no Emergent badge"],
            ]),
        ("h3", "How to Deploy"),
        ("list", [
            "Before any deploy — click 'Backup + email + download NOW' in Admin → System Recovery. Confirm green check.",
            "Run Integrity Check (Admin panel). Confirm ok: true.",
            "Click Save-to-GitHub in the Emergent chat input. This captures the current frontend + backend as a git commit.",
            "Verify production env vars are set: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD, ADMIN_HMAC_SECRET, JWT_SECRET, CORS_ORIGINS=https://mascidocs.com, MONGO_URL pointing at Atlas, BACKUP_EMAIL_TO, RESEND_API_KEY, SENDER_EMAIL, REPLY_TO_EMAIL, AUTO_EMAIL_REPORTS=true, RATE_LIMITING=on.",
            "Click Deploy in the Emergent deployment dashboard. Build takes 10-15 minutes.",
            "Post-deploy smoke test: curl https://mascidocs.com/api/health → 200. Log in as Admin / PM / Shop. Spot-check a dashboard. Confirm BackendVersionBadge in Admin Hub footer is GREEN with a new source_hash.",
            "Run post_deploy_check.py: python3 /app/scripts/post_deploy_check.py — one-command drift verification plus training-PDF audit.",
        ]),
        ("h3", "Rollback"),
        "Use the Rollback option in the Emergent deployment dashboard to return to the previous checkpoint. This reverts code ONLY — if data changed between deploy and rollback, restore the pre-deploy backup from Step 1 above.",
    ]),

    ("6. Backup & Recovery", [
        ("h3", "Automatic Backups"),
        "The platform runs scheduled backups twice daily (UTC hours configurable via BACKUP_HOURS_UTC). Each run zips every MongoDB collection into a single archive and emails it to BACKUP_EMAIL_TO. The audit trail lives in the backup_runs collection. This is the last line of defense — if the database is ever wiped, these email attachments reconstruct the entire operation.",
        ("h3", "Manual Backup"),
        ("list", [
            "Admin Hub → System Recovery panel → 'Backup + email + download NOW' button.",
            "A ZIP containing every collection is downloaded immediately AND emailed to BACKUP_EMAIL_TO.",
            "Integrity Check button verifies the current database state before you trust the backup.",
        ]),
        ("h3", "Recovery Procedure"),
        ("list", [
            "STEP 1 — Secure the most recent backup ZIP (download link or email attachment).",
            "STEP 2 — Spin up a fresh MongoDB Atlas cluster if the current one is compromised.",
            "STEP 3 — Use mongorestore against the archive: `mongorestore --uri=<new_atlas_uri> --archive=<backup.zip>`.",
            "STEP 4 — Update MONGO_URL in the Emergent deploy env vars to point at the new cluster.",
            "STEP 5 — Redeploy. Confirm BackendVersionBadge is GREEN and /api/health returns 200.",
            "STEP 6 — Spot-check a daily report, a pre-op, and an incident record. Confirm they load.",
            "STEP 7 — Run a fresh backup immediately to prove the new cluster is writable.",
        ]),
        ("h3", "Worst-Case Scenario"),
        "Emergent platform + Atlas BOTH simultaneously unavailable: bring up FastAPI on any Python-hosting provider (Render, Fly.io, Railway), point at a new Atlas cluster (or Docker Mongo), import backups via mongorestore, push frontend build to Cloudflare Pages / Vercel / Netlify. Repository is recoverable via GitHub (from Save-to-GitHub commits). Recovery window: 4-8 hours if backups are current.",
    ]),

    ("7. Performance & Scaling", [
        ("h3", "What Impacts Performance"),
        ("table",
            ["Factor", "Typical Cost", "Notes"],
            [
                ["PDF generation (WeasyPrint)", "300-900 ms per record, 2-4 s per training packet", "Synchronous — blocks that worker. Move to a background task queue if concurrent generates exceed 10/min."],
                ["Photo upload", "50-400 ms per image", "Local disk write. Migrating to S3 removes single-host risk but adds ~100 ms network."],
                ["MongoDB query", "1-50 ms", "Acceptable at current volume. Add indexes on (job_id, created_at) when daily_reports > 10k."],
                ["Email send", "300-800 ms", "Resend handles queuing. PM routing is synchronous to the submit request — may be worth offloading to a background task if daily reports > 50/day."],
                ["Cold backend start", "3-6 s", "On Emergent hibernation policy. First request after idle is slow; subsequent are fast."],
            ]),
        ("h3", "Scaling Behavior"),
        ("list", [
            "More users — no impact up to several hundred concurrent; login throttling (LOGIN_MAX_FAILS / LOGIN_LOCKOUT_SECONDS) is the only bottleneck and is per-IP.",
            "More jobs — MongoDB queries stay under 50 ms as long as indexes are kept. Admin integrity-check may slow down past 10,000 records per collection.",
            "More data (uploads) — local disk fills before anything else breaks. Migrate to S3 before 50 GB total upload volume.",
            "More PDF traffic — WeasyPrint is the chokepoint. Add horizontal workers or a dedicated PDF microservice if > 100 renders/hour.",
        ]),
    ]),

    ("8. Security", [
        ("h3", "Authentication"),
        "Tier passwords (ADMIN_PASSWORD / PM_PASSWORD / SHOP_PASSWORD) live only in server env vars — never in code, never in the client bundle. Login exchanges a password for a short-lived JWT (signed with JWT_SECRET). Tokens are stored in browser localStorage and sent via X-Admin-Token / X-PM-Token / X-Shop-Token headers. bcrypt is used for any hashed user passwords.",
        ("h3", "Role-Based Access Control"),
        ("list", [
            "Public — Field forms and Field training only.",
            "Shop — adds Shop Hub, Shop training, sign-off workflows.",
            "PM — adds scoped PM dashboards (only their assigned projects visible).",
            "Admin — full access. Also the only role that can mutate master lists, trigger backups, or change training video URLs.",
        ]),
        ("h3", "Data Protection"),
        ("list", [
            "TLS everywhere — Cloudflare handles automatic HTTPS for mascidocs.com.",
            "Atlas encrypts data at rest by default.",
            "Passwords hashed, never logged, never returned in API responses.",
            "JWT tokens time-boxed (ACCESS_TOKEN_MINUTES / REFRESH_TOKEN_DAYS configurable).",
            "Rate limiting on public POST endpoints (PUBLIC_POST_LIMIT_PER_HOUR) prevents brute force.",
            "Login lockout after N failures (LOGIN_MAX_FAILS / LOGIN_LOCKOUT_SECONDS).",
            "Admin-only endpoints verify X-Admin-Token HMAC (ADMIN_HMAC_SECRET).",
        ]),
        ("h3", "Client vs Server Exposure"),
        ("list", [
            "Server-only: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD, JWT_SECRET, ADMIN_HMAC_SECRET, RESEND_API_KEY, MONGO_URL, EMERGENT_LLM_KEY.",
            "Client-visible (intended): REACT_APP_BACKEND_URL (needed to call the API).",
            "Verified via audit: zero secrets in the minified JS bundle. Grep `sk-`, `re_`, `AWS_`, `MONGO_URL` against the live bundle returns nothing but env-var *names* in admin docs strings.",
        ]),
        ("h3", "Known Risks"),
        ("table",
            ["Risk", "Mitigation"],
            [
                ["Password sharing among crew", "Admin can rotate via ADMIN/PM/SHOP_PASSWORD env vars + redeploy; kicks all sessions."],
                ["JWT_SECRET leak", "Rotate JWT_SECRET + redeploy. All tokens instantly invalid."],
                ["Public endpoint abuse", "Rate limiting already on. Cloudflare adds DDoS absorption."],
                ["Atlas credentials leak", "Atlas IP allowlist + rotate DB user password."],
                ["Lost admin password", "Recoverable via Emergent deploy env vars — only The Judd Group LLC has access to those."],
            ]),
    ]),

    ("9. Failure Points", [
        ("table",
            ["Failure", "What Breaks", "Impact", "Detection", "Fix"],
            [
                ["Emergent hosting outage", "Entire platform unreachable", "TOTAL — no one can log in or submit", "Cloudflare 521/522 error, /api/health times out", "Check Emergent status page. If extended, trigger DR deploy on alt host per Section 6 worst-case."],
                ["MongoDB Atlas outage", "All reads/writes fail", "TOTAL — app loads but forms error on submit", "Backend logs show connection refused; /api/health 500", "Atlas status page. Atlas usually self-heals. If cluster corrupted, restore from backup ZIP."],
                ["Resend outage", "Emails stop sending (PM routing, backups, alerts)", "HIGH — data still saved; PMs don't get notifications", "No inbound emails for 30+ min; backend logs show Resend 5xx", "Resend status page. All queued data still saved — emails resume when Resend recovers."],
                ["PDF generation failure", "WeasyPrint throws on a specific record", "MEDIUM — one PDF broken; rest of platform fine", "User sees 500 on download; backend logs show WeasyPrint stack trace", "Usually a malformed image upload. Check uploads dir; delete offending file."],
                ["Cloudflare SSL issue", "HTTPS fails, browsers refuse to load", "TOTAL", "Browser 'not secure' warning; curl --insecure still works", "Cloudflare dashboard → SSL/TLS → re-issue cert. Typically auto-heals in <15 min."],
                ["Domain expiry", "mascidocs.com stops resolving", "TOTAL", "DNS lookup fails", "Renew at registrar. Set auto-renew + 60-day warning."],
                ["Local disk fills on backend", "Uploads fail with 500; eventually backend crashes", "HIGH", "Upload returns 'No space left on device'", "SSH into container, clear /app/backend/uploads oldest files. Long-term: migrate to S3."],
                ["ADMIN_PASSWORD forgotten", "No one can access Admin Hub", "HIGH — can't do master-list edits or backups", "Login returns 401 on valid admin page", "Change ADMIN_PASSWORD in Emergent deploy env vars → redeploy."],
                ["Stale backend after deploy (frontend current, backend old)", "New features silently missing from API / PDFs", "MEDIUM", "BackendVersionBadge goes RED or shows old source_hash", "Redeploy. Run post_deploy_check.py to verify."],
                ["User device offline (field crew on bad 4G)", "Can't submit forms", "LOCAL only", "User reports 'it's not saving'", "User retries when signal returns. Consider offline-capable PWA in V2."],
            ]),
    ]),

    ("10. Maintenance Checklist", [
        ("h3", "Daily"),
        ("list", [
            "BackendVersionBadge in Admin Hub footer is GREEN (source_hash matches current deploy, uptime sane).",
            "curl https://mascidocs.com/api/health returns 200.",
            "Spot-check one daily-report email arrived in the PM inbox.",
            "Spot-check one new form submission landed in MongoDB (anything from today).",
        ]),
        ("h3", "Weekly"),
        ("list", [
            "Verify both scheduled backup emails arrived (open one and confirm the ZIP is > 0 bytes and contains JSON for key collections).",
            "Review backend error logs for anything repeating (WeasyPrint warnings, Resend 429s, Atlas auth timeouts).",
            "Check Admin → System Recovery → 'Run Integrity Check' returns ok: true.",
            "Scan outage_alerts inbox for platform alerts.",
        ]),
        ("h3", "Monthly"),
        ("list", [
            "Review Emergent credit usage (Profile → Universal Key → Balance). Top up if < 50.",
            "Review Atlas storage usage. Upgrade cluster tier when > 70% of M0 quota.",
            "Review Resend volume. Upgrade tier if > 2,500 emails/mo (80% of free).",
            "Review mascidocs.com domain auto-renew status.",
            "Review new platform features or security advisories (FastAPI, MongoDB, WeasyPrint).",
            "Rotate ADMIN_HMAC_SECRET + JWT_SECRET if > 12 months old.",
        ]),
    ]),

    ("11. Future Scaling / Version 2 Notes", [
        ("h3", "What Should Be Rebuilt for Scale"),
        ("list", [
            "File uploads → S3-compatible object storage (AWS S3, Backblaze B2, Cloudflare R2). Removes container-disk fragility and enables CDN-backed image delivery.",
            "server.py → broken into routers (/routes/auth.py, /routes/training.py, /routes/equipment.py, etc.). Current file is ~5,000 lines — hard to navigate and slows agent-assisted changes.",
            "Static safety-card PDFs → regenerate via WeasyPrint (same pipeline as training packets) so future footer/logo changes auto-flow to those 4 cards.",
            "PDF generation → background task queue (Celery + Redis, or Arq). Currently blocks the worker; at scale this creates request-timeout risk.",
            "Offline-capable field forms → Progressive Web App with IndexedDB queue. Field crews on bad signal can fill forms offline, sync when online.",
            "Real-time notifications → WebSocket or Server-Sent Events so PMs see daily reports appear without a refresh.",
        ]),
        ("h3", "Dependencies That Could Become Issues"),
        ("list", [
            "Emergent platform lock-in — DR plan mitigates this but worth decoupling if MASCI ever grows to multiple customers.",
            "WeasyPrint — stable but requires GTK system libs; could be replaced with a headless Chrome PDF service (Gotenberg, Browserless) for better CSS support.",
            "Custom-asset CDN for training videos — moving to a dedicated S3 + CloudFront bucket gives The Judd Group LLC direct ownership of video storage."
        ]),
        ("h3", "Long-Term SaaS Recommendations"),
        ("list", [
            "Separate the MASCI-specific data from the platform code. Introduce a `tenant_id` column on every collection; customer-scope every query.",
            "White-label deployment pattern — each customer gets their own subdomain + isolated Atlas database + configurable branding (logo, lockup, footer text, safety card content).",
            "Per-tenant billing integration (Stripe) so onboarding a new customer doesn't require code changes.",
            "Centralized monitoring (Datadog, Axiom, Better Stack) once more than one customer is on the platform.",
        ]),
    ]),

    ("12. Owner Notes", [
        "This section is intentionally blank — The Judd Group LLC should use this space for ongoing observations, custom changes, and future-improvement ideas as they come up during daily operation of MASCI HUB.",
        ("h3", "Custom Notes"),
        "—",
        ("h3", "Future Improvements"),
        "—",
        ("h3", "Observations"),
        "—",
    ]),
]


COVER_TITLE = "MASCI HUB"
COVER_SUBTITLE = "Internal System Owner & Operations Manual"
COVER_OWNER = "The Judd Group LLC"
COVER_CLASSIFICATION = "CONFIDENTIAL — Not for Customer or Public Use"


# ---------------------------------------------------------------------------
# PDF renderer (WeasyPrint)
# ---------------------------------------------------------------------------

def _pdf_html() -> str:
    now = datetime.now(timezone.utc).strftime("%B %d, %Y")
    parts = []
    parts.append("""<!doctype html><html><head><meta charset="utf-8">
<style>
@page { size: Letter; margin: 0.75in 0.75in 0.95in 0.75in;
  @bottom-left  { content: "MASCI HUB · Internal Operations Manual"; font-family: 'Helvetica', sans-serif; font-size: 8pt; color: #6b7280; }
  @bottom-center { content: "CONFIDENTIAL — The Judd Group LLC"; font-family: 'Helvetica', sans-serif; font-size: 8pt; color: #b91c1c; letter-spacing: 0.1em; text-transform: uppercase; }
  @bottom-right { content: counter(page) " / " counter(pages); font-family: 'Helvetica', sans-serif; font-size: 8pt; color: #6b7280; }
}
@page :first { margin: 1.2in 0.75in 1in 0.75in;
  @bottom-left { content: ""; } @bottom-center { content: ""; } @bottom-right { content: ""; } }
body { font-family: 'Helvetica', Arial, sans-serif; font-size: 10.5pt; color: #1f2937; line-height: 1.5; }
.cover { text-align: center; padding-top: 2in; }
.cover .title { font-size: 32pt; font-weight: 900; letter-spacing: 0.02em; color: #111827; }
.cover .sub { font-size: 14pt; color: #374151; margin-top: 12pt; letter-spacing: 0.05em; }
.cover .owner { margin-top: 40pt; font-size: 11pt; color: #4b5563; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 0.18em; }
.cover .classification { margin-top: 60pt; color: #b91c1c; font-size: 10pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; border: 2px solid #b91c1c; padding: 8pt 16pt; display: inline-block; }
.cover .date { margin-top: 28pt; color: #6b7280; font-size: 9pt; font-family: 'Courier New', monospace; }
h1 { font-size: 16pt; font-weight: 900; color: #111827; margin-top: 28pt; margin-bottom: 10pt; padding-bottom: 6pt; border-bottom: 2px solid #111827; page-break-before: always; page-break-after: avoid; }
h3 { font-size: 11pt; font-weight: 700; color: #374151; margin-top: 14pt; margin-bottom: 5pt; text-transform: uppercase; letter-spacing: 0.04em; page-break-after: avoid; }
p { margin: 6pt 0; }
ul { margin: 6pt 0 10pt 18pt; padding: 0; }
li { margin: 3pt 0; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 9.5pt; }
th { background: #111827; color: white; text-align: left; padding: 6pt 8pt; font-weight: 700; font-size: 9pt; text-transform: uppercase; letter-spacing: 0.04em; }
td { padding: 5pt 8pt; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
tr:nth-child(even) td { background: #f9fafb; }
</style></head><body>""")

    # Cover
    parts.append(f"""<section class="cover">
<div class="title">{COVER_TITLE}</div>
<div class="sub">{COVER_SUBTITLE}</div>
<div class="owner">Prepared for {COVER_OWNER}</div>
<div class="classification">{COVER_CLASSIFICATION}</div>
<div class="date">Generated {now}</div>
</section>""")

    # Sections
    for heading, blocks in SECTIONS:
        parts.append(f"<h1>{_html_escape(heading)}</h1>")
        for b in blocks:
            if isinstance(b, str):
                parts.append(f"<p>{_html_escape(b)}</p>")
            elif b[0] == "h3":
                parts.append(f"<h3>{_html_escape(b[1])}</h3>")
            elif b[0] == "list":
                parts.append("<ul>")
                for item in b[1]:
                    parts.append(f"<li>{_html_escape(item)}</li>")
                parts.append("</ul>")
            elif b[0] == "table":
                headers, rows = b[1], b[2]
                parts.append("<table><thead><tr>")
                for h in headers:
                    parts.append(f"<th>{_html_escape(h)}</th>")
                parts.append("</tr></thead><tbody>")
                for row in rows:
                    parts.append("<tr>")
                    for cell in row:
                        parts.append(f"<td>{_html_escape(cell)}</td>")
                    parts.append("</tr>")
                parts.append("</tbody></table>")

    parts.append("</body></html>")
    return "".join(parts)


def _html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_ops_manual_pdf() -> bytes:
    return HTML(string=_pdf_html()).write_pdf()


# ---------------------------------------------------------------------------
# DOCX renderer (python-docx)
# ---------------------------------------------------------------------------

def render_ops_manual_docx() -> bytes:
    doc = Document()
    # Page margins — 8.5 × 11 is default Letter in python-docx
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Cover
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("\n\n\n" + COVER_TITLE)
    run.font.size = Pt(36)
    run.bold = True
    run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(COVER_SUBTITLE)
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("\n\nPrepared for " + COVER_OWNER)
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
    run.font.name = "Courier New"

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("\n\n" + COVER_CLASSIFICATION)
    run.font.size = Pt(11)
    run.bold = True
    run.font.color.rgb = RGBColor(0xB9, 0x1C, 0x1C)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    now = datetime.now(timezone.utc).strftime("%B %d, %Y")
    run = p.add_run("\nGenerated " + now)
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)
    run.font.name = "Courier New"

    doc.add_page_break()

    # Sections
    for heading, blocks in SECTIONS:
        h = doc.add_heading(heading, level=1)
        for run in h.runs:
            run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        for b in blocks:
            if isinstance(b, str):
                p = doc.add_paragraph(b)
                p.paragraph_format.space_after = Pt(6)
            elif b[0] == "h3":
                doc.add_heading(b[1], level=3)
            elif b[0] == "list":
                for item in b[1]:
                    doc.add_paragraph(item, style="List Bullet")
            elif b[0] == "table":
                headers, rows = b[1], b[2]
                tbl = doc.add_table(rows=1, cols=len(headers))
                tbl.style = "Light Grid Accent 1"
                hdr_cells = tbl.rows[0].cells
                for i, htext in enumerate(headers):
                    hdr_cells[i].text = htext
                    for paragraph in hdr_cells[i].paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
                for row in rows:
                    row_cells = tbl.add_row().cells
                    for i, cell in enumerate(row):
                        row_cells[i].text = str(cell)
                doc.add_paragraph("")  # spacing

    # Footer
    section = doc.sections[0]
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = "CONFIDENTIAL — The Judd Group LLC · MASCI HUB Operations Manual"
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in fp.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0xB9, 0x1C, 0x1C)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
