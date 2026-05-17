"""guidance.content — Phase A in-code content registry.

Each article is a plain dict. Visibility is declared per-article as a
set of "scopes" — the caller has access to an article iff their portal
tier set intersects ``scopes``.

Scope vocabulary (mirrors the platform's portal tokens, plus a special
"public" scope for general/anonymous-safe content):

    public      — anyone, including anonymous (login help, general)
    field       — any authenticated user (incl. PM/HR/Shop/Safety/Dispatch/Admin)
    admin       — admin-strict only
    hr          — HR portal users
    safety      — Safety portal users
    shop        — Shop portal users
    dispatch    — Dispatch portal users
    pm          — PM portal users
    leadership  — Field Leadership users

Sections (top-level menu families) are declared in SECTIONS below.

Style note: write content in plain English, declarative voice, no
marketing language. Use "supports / helps / improves" not "guarantees".
Every article should declare WHY it matters and WHAT happens next where
applicable.
"""
from __future__ import annotations

from typing import Iterable

# ─────────────────────────────────────────────────────────────────────
# Top-level sections (mirror the directive's 10 content families)
# ─────────────────────────────────────────────────────────────────────
SECTIONS = [
    {"id": "roles",       "title": "Role-Based Training",        "icon": "user-cog"},
    {"id": "quickhelp",   "title": "Task-Based Quick Help",      "icon": "zap"},
    {"id": "portals",     "title": "Portal Guides",              "icon": "layout-grid"},
    {"id": "troubleshooting", "title": "Troubleshooting",        "icon": "life-buoy"},
    {"id": "knowledge",   "title": "Why It Matters",             "icon": "lightbulb"},
    {"id": "reliability", "title": "Backups & Data Portability", "icon": "shield"},
    {"id": "onboarding",  "title": "New User Onboarding",        "icon": "user-plus"},
]


# ─────────────────────────────────────────────────────────────────────
# Article registry
# ─────────────────────────────────────────────────────────────────────
#
# Each article schema:
#
#   id            stable kebab-case slug (used in URLs, search index)
#   section       one of SECTIONS[].id
#   title         human title (shown in lists, used in search)
#   summary       one-line subhead
#   scopes        list of scope strings (see header) — controls visibility
#   tags          freeform keywords for search
#   body          structured content blocks (see _block helpers below)
#   related       list of related article ids (filtered by RBAC at serve)
#
# Blocks supported in `body`:
#
#   {"type": "p",        "text": "..."}                  paragraph
#   {"type": "steps",    "items": ["...", "...", ...]}   numbered list
#   {"type": "bullets",  "items": ["...", "...", ...]}   bullet list
#   {"type": "why",      "text": "..."}                  callout: why it matters
#   {"type": "next",     "items": ["...", "...", ...]}   callout: what happens next
#   {"type": "warn",     "text": "..."}                  callout: caution
#   {"type": "tip",      "text": "..."}                  callout: helpful tip
#   {"type": "mistakes", "items": ["...", "...", ...]}   callout: common mistakes
#
# This list is intentionally seed content — Phase B fills in the long
# tail. Each section here has at least one example so the UI is never
# empty for a given scope.

_ARTICLES: list[dict] = [
    # ── ROLES ────────────────────────────────────────────────────────
    {
        "id": "role-superintendent",
        "section": "roles",
        "title": "Superintendent",
        "summary": "Daily ops, crew, equipment, incidents, coaching.",
        "scopes": ["leadership", "admin"],
        "tags": ["superintendent", "field", "supervisor", "crew", "daily"],
        "body": [
            {"type": "p", "text":
                "Superintendents document daily operations, crew activity, equipment use, "
                "incidents, coaching, and project conditions."},
            {"type": "why", "text":
                "Clean field documentation supports MASCI, helps payroll and project review, "
                "improves accountability, and gives leadership real-time visibility."},
            {"type": "bullets", "items": [
                "Daily Reports",
                "Incident Reporting",
                "Equipment Checkout",
                "Employee Coaching",
                "Corrective Actions",
                "Safety Documentation",
            ]},
            {"type": "mistakes", "items": [
                "Missing photos",
                "Incomplete notes",
                "Wrong project selected",
                "Not submitting before end of day",
                "Failing to document equipment issues",
            ]},
            {"type": "next", "items": [
                "Records become visible to authorized leadership",
                "HR / Safety / Admin may review depending on workflow",
                "Audit trails preserve submission history",
            ]},
        ],
        "related": ["why-daily-reports", "why-photos", "task-submit-incident"],
    },
    {
        "id": "role-foreman",
        "section": "roles",
        "title": "Foreman",
        "summary": "Crew leadership and daily field documentation.",
        "scopes": ["leadership", "admin"],
        "tags": ["foreman", "field", "supervisor", "crew"],
        "body": [
            {"type": "p", "text":
                "Foremen lead crews in the field and own most of the day-to-day "
                "documentation: daily reports, photos, equipment status, time entries."},
            {"type": "why", "text":
                "Foreman documentation is the most accurate operational record we have. "
                "It improves payroll accuracy and supports field decisions."},
            {"type": "bullets", "items": [
                "Submit a Daily Report every workday",
                "Document equipment issues immediately",
                "Coach employees and record significant conversations",
                "Escalate incidents quickly",
            ]},
        ],
        "related": ["why-daily-reports", "task-submit-incident", "why-photos"],
    },
    {
        "id": "role-hr",
        "section": "roles",
        "title": "HR",
        "summary": "Time, employees, write-ups, offboarding.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "human resources", "payroll", "time", "write-up"],
        "body": [
            {"type": "p", "text":
                "HR uses the platform to verify time, manage employee records, review "
                "write-ups, track equipment checkout for offboarding, and document "
                "personnel actions."},
            {"type": "why", "text":
                "HR documentation supports payroll accuracy, helps protect both MASCI "
                "and employees, and creates a clear paper trail for personnel decisions."},
            {"type": "bullets", "items": [
                "Time Verification",
                "Employee Records",
                "Write-Ups / Corrective Action follow-through",
                "Offboarding (equipment return, final pay)",
            ]},
            {"type": "next", "items": [
                "Verified time goes to payroll cross-check",
                "Write-ups are visible to HR, Admin, and field leadership",
                "Audit log records who reviewed what",
            ]},
        ],
        "related": ["why-time-verification", "task-verify-time", "tshoot-employee-not-found"],
    },
    {
        "id": "role-safety",
        "section": "roles",
        "title": "Safety",
        "summary": "Incidents, near-misses, corrective actions, audits.",
        "scopes": ["safety", "admin"],
        "tags": ["safety", "incident", "audit", "corrective", "near miss"],
        "body": [
            {"type": "p", "text":
                "Safety reviews incidents and near-misses, drives corrective actions, "
                "manages audits and fire extinguisher records, and owns the safety training log."},
            {"type": "why", "text":
                "Safety documentation supports investigations, helps prevent repeat events, "
                "and improves the company's overall safety posture."},
            {"type": "bullets", "items": [
                "Incidents and Near-Misses",
                "Corrective Actions",
                "Audits",
                "Fire Extinguisher inspections",
                "Training Records",
            ]},
        ],
        "related": ["why-incidents", "why-corrective-actions", "task-submit-incident"],
    },
    {
        "id": "role-shop",
        "section": "roles",
        "title": "Shop / Fleet",
        "summary": "Inspections, failed pre-ops, damage, maintenance.",
        "scopes": ["shop", "admin"],
        "tags": ["shop", "fleet", "equipment", "maintenance"],
        "body": [
            {"type": "p", "text":
                "Shop owns equipment health: inspections, failed pre-ops, damage "
                "reports, maintenance coordination, and equipment accountability."},
            {"type": "why", "text":
                "Clean equipment records reduce downtime, support warranty and insurance "
                "claims, and help dispatch know what is actually available."},
            {"type": "bullets", "items": [
                "Equipment Inspections",
                "Failed Pre-Ops",
                "Damage Reports",
                "Maintenance Coordination",
                "Equipment Accountability",
            ]},
        ],
        "related": ["why-equipment-accountability", "tshoot-equipment-not-found"],
    },
    {
        "id": "role-dispatch",
        "section": "roles",
        "title": "Dispatch",
        "summary": "Equipment movement, availability, holds, transfers.",
        "scopes": ["dispatch", "admin"],
        "tags": ["dispatch", "equipment", "transfer", "hold"],
        "body": [
            {"type": "p", "text":
                "Dispatch coordinates equipment movement: availability, holds, transfers, "
                "and the relationship between shop status and field readiness."},
            {"type": "why", "text":
                "Accurate dispatch records prevent equipment from being double-booked or "
                "sent to a job in a state it shouldn't be in."},
        ],
        "related": ["why-equipment-accountability"],
    },
    {
        "id": "role-pm",
        "section": "roles",
        "title": "Project Manager",
        "summary": "Project oversight, report review, coordination.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "project manager", "project", "coordination"],
        "body": [
            {"type": "p", "text":
                "PMs review project-level reports, coordinate across crews and trades, "
                "and provide oversight of field execution."},
            {"type": "why", "text":
                "PM review catches issues before they grow and keeps project records "
                "aligned with what the field is actually seeing."},
        ],
        "related": ["why-daily-reports"],
    },
    {
        "id": "role-admin",
        "section": "roles",
        "title": "Admin",
        "summary": "Users, audits, system health, backups.",
        "scopes": ["admin"],
        "tags": ["admin", "audit log", "backup", "restore", "system"],
        "body": [
            {"type": "p", "text":
                "Admin manages users, audit logs, system health, deployments, backups, "
                "restore drills, data portability, and role templates."},
            {"type": "why", "text":
                "Admin controls are the platform's last line of defense. They ensure "
                "only the right people have access and that operational data is recoverable."},
            {"type": "bullets", "items": [
                "User & directory management",
                "Audit logs",
                "System health & sessions",
                "Backups, restore drills, data portability",
                "Role templates",
            ]},
        ],
        "related": ["why-audit-logs", "why-backups", "tshoot-session-timeout"],
    },
    {
        "id": "role-new-employee",
        "section": "roles",
        "title": "New Employee",
        "summary": "What to do in your first week using MASCI.",
        "scopes": ["public"],
        "tags": ["new", "onboarding", "first day", "getting started"],
        "body": [
            {"type": "p", "text":
                "Welcome to MASCI. This platform is how the company tracks daily work, "
                "equipment, safety, time, and personnel records. You will likely use it "
                "on a phone in the field."},
            {"type": "steps", "items": [
                "Log in with the credentials your supervisor or HR gave you",
                "Find your portal (Field, PM, Shop, etc.) on the home page",
                "Use the daily report template if you're in the field",
                "Take photos — they're part of the record",
                "Ask your supervisor if you can't see something you expect to",
            ]},
            {"type": "tip", "text":
                "If you get signed out unexpectedly, it's a routine timeout — log back in."},
        ],
        "related": ["onboard-login", "onboard-mobile", "tshoot-session-timeout"],
    },

    # ── QUICK HELP (task-based) ──────────────────────────────────────
    {
        "id": "task-submit-incident",
        "section": "quickhelp",
        "title": "How do I submit an incident?",
        "summary": "Quick steps for incident reporting.",
        "scopes": ["field", "leadership", "safety", "admin"],
        "tags": ["incident", "submit", "report", "safety"],
        "body": [
            {"type": "steps", "items": [
                "Open the Safety portal (or your field landing page)",
                "Tap 'Submit Incident'",
                "Fill in the date, time, location, and what happened",
                "Take photos of the scene if safe to do so",
                "Submit before leaving the job site",
            ]},
            {"type": "why", "text":
                "Timely incident reports help Safety investigate quickly and protect everyone involved."},
            {"type": "next", "items": [
                "Safety reviews the report",
                "Corrective Actions may be created",
                "Audit history is preserved",
            ]},
        ],
        "related": ["role-safety", "why-incidents"],
    },
    {
        "id": "task-upload-photos",
        "section": "quickhelp",
        "title": "How do I upload photos?",
        "summary": "Adding photos to a record.",
        "scopes": ["field", "leadership", "shop", "safety", "pm", "hr", "admin"],
        "tags": ["photo", "upload", "image", "attachment"],
        "body": [
            {"type": "steps", "items": [
                "Tap the photo button on the form",
                "Pick an existing photo or take a new one",
                "Wait for the upload to finish before submitting",
                "Confirm the thumbnail appears in the form",
            ]},
            {"type": "tip", "text":
                "If you have spotty service, upload one photo at a time and wait for the green check."},
        ],
        "related": ["tshoot-photo-upload"],
    },
    {
        "id": "task-verify-time",
        "section": "quickhelp",
        "title": "How do I verify time?",
        "summary": "HR / payroll time verification flow.",
        "scopes": ["hr", "admin"],
        "tags": ["time", "payroll", "overtime", "lunch", "verify"],
        "body": [
            {"type": "steps", "items": [
                "Open the HR portal",
                "Select the pay period",
                "Compare supervisor-entered hours against payroll",
                "Flag any discrepancies for follow-up",
            ]},
            {"type": "why", "text":
                "Time verification supports payroll accuracy and gives a clear audit trail "
                "if a paycheck is ever questioned."},
        ],
        "related": ["why-time-verification", "role-hr"],
    },

    # ── PORTAL GUIDES ────────────────────────────────────────────────
    {
        "id": "portal-hr",
        "section": "portals",
        "title": "HR Portal Quick-Start",
        "summary": "What the HR portal does and how to use it.",
        "scopes": ["hr", "admin"],
        "tags": ["hr portal", "human resources"],
        "body": [
            {"type": "p", "text":
                "The HR portal is the entry point for time verification, employee records, "
                "write-ups, equipment-checkout visibility, and offboarding support."},
            {"type": "why", "text":
                "Centralising HR work here means everything is searchable, audited, and "
                "reviewable by authorized leadership."},
        ],
        "related": ["role-hr", "task-verify-time"],
    },
    {
        "id": "portal-safety",
        "section": "portals",
        "title": "Safety Portal Quick-Start",
        "summary": "How Safety manages incidents and audits.",
        "scopes": ["safety", "admin"],
        "tags": ["safety portal"],
        "body": [
            {"type": "p", "text":
                "The Safety portal is where incidents, near-misses, corrective actions, "
                "fire extinguisher records, and audit work happen."},
        ],
        "related": ["role-safety"],
    },
    {
        "id": "portal-shop",
        "section": "portals",
        "title": "Shop / Fleet Portal Quick-Start",
        "summary": "Equipment health, inspections, and maintenance.",
        "scopes": ["shop", "admin"],
        "tags": ["shop portal", "fleet"],
        "body": [{"type": "p", "text":
            "The Shop portal owns equipment health and maintenance coordination."}],
        "related": ["role-shop"],
    },
    {
        "id": "portal-admin",
        "section": "portals",
        "title": "Admin Portal Quick-Start",
        "summary": "Users, audits, system health, backups.",
        "scopes": ["admin"],
        "tags": ["admin portal"],
        "body": [
            {"type": "p", "text":
                "Admin covers the platform's control plane: users, role templates, audit "
                "logs, system health, sessions, and backup/restore tools."},
            {"type": "tip", "text":
                "Most operational visibility lives under Admin → System. Sessions, "
                "audit log, and backups are all there."},
        ],
        "related": ["role-admin"],
    },

    # ── TROUBLESHOOTING ──────────────────────────────────────────────
    {
        "id": "tshoot-photo-upload",
        "section": "troubleshooting",
        "title": "Photo upload failed",
        "summary": "Common causes and recovery steps.",
        "scopes": ["field", "leadership", "shop", "safety", "pm", "hr", "admin"],
        "tags": ["photo", "upload", "failed", "troubleshoot"],
        "body": [
            {"type": "bullets", "items": [
                "Check service / data connection",
                "Try one photo first, not a batch",
                "Confirm the file type is supported (JPG / PNG / HEIC)",
            ]},
            {"type": "warn", "text":
                "Do NOT submit duplicate forms unless instructed — that creates duplicate records."},
            {"type": "p", "text":
                "If the upload still fails, contact your supervisor or admin with the form name and timestamp."},
        ],
        "related": ["task-upload-photos"],
    },
    {
        "id": "tshoot-session-timeout",
        "section": "troubleshooting",
        "title": "Why did my session time out?",
        "summary": "Session timeouts are deliberate and protective.",
        "scopes": ["public"],
        "tags": ["session", "timeout", "signed out", "login"],
        "body": [
            {"type": "p", "text":
                "MASCI signs users out after a period of inactivity to protect access. "
                "Different roles have different limits — admins have the shortest window, "
                "field users the longest."},
            {"type": "why", "text":
                "If a device is left unattended or lost, automatic sign-out limits how long "
                "an unauthorized person could use it."},
            {"type": "steps", "items": [
                "Sign back in with your normal credentials",
                "If you can't sign in, contact your supervisor or admin",
            ]},
        ],
        "related": ["why-session-timeouts"],
    },
    {
        "id": "tshoot-employee-not-found",
        "section": "troubleshooting",
        "title": "Employee not found in search",
        "summary": "Why an employee might not appear and what to do.",
        "scopes": ["hr", "leadership", "admin"],
        "tags": ["employee", "not found", "search"],
        "body": [
            {"type": "bullets", "items": [
                "The employee may not be active yet — check with HR",
                "The name spelling may differ from the search term",
                "The portal may not have visibility into that employee group",
            ]},
        ],
        "related": [],
    },
    {
        "id": "tshoot-equipment-not-found",
        "section": "troubleshooting",
        "title": "Equipment not found",
        "summary": "What to check when equipment doesn't appear.",
        "scopes": ["shop", "dispatch", "field", "leadership", "admin"],
        "tags": ["equipment", "not found"],
        "body": [
            {"type": "bullets", "items": [
                "Equipment may be on hold — check Dispatch",
                "Equipment may be retired or transferred — check Shop",
                "Search by asset number, not nickname",
            ]},
        ],
        "related": [],
    },

    # ── WHY IT MATTERS ───────────────────────────────────────────────
    {
        "id": "why-daily-reports",
        "section": "knowledge",
        "title": "Why Daily Reports Matter",
        "summary": "The operational backbone of field documentation.",
        "scopes": ["field", "leadership", "pm", "admin"],
        "tags": ["daily report", "why", "field"],
        "body": [
            {"type": "p", "text":
                "Daily Reports are the most-referenced operational record we have. "
                "They support payroll cross-check, project review, dispute resolution, "
                "and after-the-fact investigations."},
            {"type": "why", "text":
                "A complete Daily Report protects the crew and the company. It improves "
                "communication between field and office, helps catch issues early, and "
                "creates a defensible record of what actually happened on the job site."},
        ],
        "related": ["role-superintendent", "role-foreman"],
    },
    {
        "id": "why-photos",
        "section": "knowledge",
        "title": "Why Photos Matter",
        "summary": "Photos turn notes into evidence.",
        "scopes": ["field", "leadership", "shop", "safety", "admin"],
        "tags": ["photos", "why"],
        "body": [
            {"type": "p", "text":
                "Photos turn a written note into a verifiable record. They support "
                "investigations, insurance / warranty claims, equipment status, and "
                "project documentation."},
        ],
        "related": ["task-upload-photos"],
    },
    {
        "id": "why-incidents",
        "section": "knowledge",
        "title": "Why Safety Incidents Must Be Documented",
        "summary": "Documentation supports investigation and protection.",
        "scopes": ["field", "leadership", "safety", "admin"],
        "tags": ["incident", "safety", "why"],
        "body": [
            {"type": "p", "text":
                "Documented incidents support investigation, help prevent repeat events, "
                "and protect both the company and the people involved."},
            {"type": "tip", "text":
                "Document near-misses too — they're the cheapest lessons we get."},
        ],
        "related": ["task-submit-incident", "role-safety"],
    },
    {
        "id": "why-corrective-actions",
        "section": "knowledge",
        "title": "Why Corrective Actions Matter",
        "summary": "Closing the loop on issues raised.",
        "scopes": ["safety", "leadership", "admin"],
        "tags": ["corrective action", "why"],
        "body": [
            {"type": "p", "text":
                "Corrective Actions turn an incident or finding into a tracked follow-up. "
                "They make it visible whether the issue was actually addressed."},
        ],
        "related": ["why-incidents"],
    },
    {
        "id": "why-equipment-accountability",
        "section": "knowledge",
        "title": "Why Equipment Accountability Matters",
        "summary": "Assigned equipment has cost and responsibility.",
        "scopes": ["shop", "dispatch", "leadership", "hr", "admin"],
        "tags": ["equipment", "accountability", "why"],
        "body": [
            {"type": "p", "text":
                "Assigned equipment carries cost and responsibility. Clean checkout / "
                "return records help prevent loss and support offboarding review."},
        ],
        "related": ["role-shop", "role-hr"],
    },
    {
        "id": "why-time-verification",
        "section": "knowledge",
        "title": "Why Time Verification Matters",
        "summary": "Supports payroll accuracy and audit trail.",
        "scopes": ["hr", "leadership", "admin"],
        "tags": ["time", "payroll", "why"],
        "body": [
            {"type": "p", "text":
                "Verified time supports payroll accuracy and gives a clean audit trail "
                "if a paycheck is ever questioned."},
            {"type": "tip", "text":
                "Regular / OT / Lunch are tracked separately. Total paid hours = Regular + Overtime. "
                "Lunch is unpaid time tracked separately."},
        ],
        "related": ["task-verify-time", "role-hr"],
    },
    {
        "id": "why-audit-logs",
        "section": "knowledge",
        "title": "Why Audit Logs Matter",
        "summary": "Who did what, and when.",
        "scopes": ["admin"],
        "tags": ["audit", "log", "why"],
        "body": [
            {"type": "p", "text":
                "Audit logs answer 'who did what, and when' — for sensitive admin actions, "
                "for backup downloads, for permission changes. They're how we reconstruct "
                "events after the fact."},
        ],
        "related": [],
    },
    {
        "id": "why-session-timeouts",
        "section": "knowledge",
        "title": "Why Session Timeouts Exist",
        "summary": "Auto sign-out protects access if a device is left unattended.",
        "scopes": ["public"],
        "tags": ["session", "timeout", "why"],
        "body": [
            {"type": "p", "text":
                "Session timeouts sign users out after a period of inactivity. Different "
                "roles have different windows — admins shortest, field longest."},
            {"type": "why", "text":
                "If a phone or laptop is lost or left unattended, auto sign-out limits how "
                "long an unauthorized person could use it."},
        ],
        "related": ["tshoot-session-timeout"],
    },

    # ── RELIABILITY / DATA PORTABILITY ───────────────────────────────
    {
        "id": "why-backups",
        "section": "reliability",
        "title": "How MASCI's Backups Work",
        "summary": "Technical backups, human-readable exports, restore drills.",
        "scopes": ["admin"],
        "tags": ["backup", "restore", "r2", "data portability"],
        "body": [
            {"type": "p", "text":
                "MASCI maintains two parallel preservation systems."},
            {"type": "bullets", "items": [
                "Technical backups: nightly + hourly snapshots stored in Cloudflare R2. "
                "Used to restore the live database if something fails.",
                "Human-readable exports: PDF + CSV per-record archives. Used when a "
                "non-technical reader needs to see what was on file.",
            ]},
            {"type": "p", "text":
                "Restore drills periodically prove the technical backups are actually "
                "usable — a backup that has never been restored is not yet a backup."},
            {"type": "why", "text":
                "Together these support disaster recovery, customer/auditor record "
                "requests, and operational continuity."},
        ],
        "related": ["why-audit-logs"],
    },

    # ── ONBOARDING ───────────────────────────────────────────────────
    {
        "id": "onboard-login",
        "section": "onboarding",
        "title": "How to log in",
        "summary": "First-time login basics.",
        "scopes": ["public"],
        "tags": ["login", "onboarding"],
        "body": [
            {"type": "steps", "items": [
                "Open the MASCI URL given by your supervisor or HR",
                "Enter your credentials",
                "If you have multiple portals, pick the one for your role",
            ]},
            {"type": "tip", "text":
                "Bookmark the URL on your phone — there's no app to install."},
        ],
        "related": ["onboard-mobile", "tshoot-session-timeout"],
    },
    {
        "id": "onboard-mobile",
        "section": "onboarding",
        "title": "Using MASCI on a phone or tablet",
        "summary": "Field-friendly mobile usage tips.",
        "scopes": ["public"],
        "tags": ["mobile", "phone", "tablet", "onboarding"],
        "body": [
            {"type": "bullets", "items": [
                "Add the site to your phone's home screen for one-tap access",
                "Submit forms before leaving the job site — service can drop",
                "If a photo upload fails, retry one at a time",
            ]},
        ],
        "related": ["task-upload-photos", "onboard-login"],
    },
]


# ─────────────────────────────────────────────────────────────────────
# RBAC — scope vocabulary
# ─────────────────────────────────────────────────────────────────────
SCOPE_PUBLIC = "public"
SCOPE_FIELD = "field"
SCOPE_ADMIN = "admin"
SCOPE_HR = "hr"
SCOPE_SAFETY = "safety"
SCOPE_SHOP = "shop"
SCOPE_DISPATCH = "dispatch"
SCOPE_PM = "pm"
SCOPE_LEADERSHIP = "leadership"

ALL_SCOPES = {
    SCOPE_PUBLIC, SCOPE_FIELD, SCOPE_ADMIN, SCOPE_HR, SCOPE_SAFETY,
    SCOPE_SHOP, SCOPE_DISPATCH, SCOPE_PM, SCOPE_LEADERSHIP,
}


def _normalize_scopes(scopes: Iterable[str]) -> set[str]:
    return {s.strip().lower() for s in (scopes or []) if s}


def caller_scopes(
    *,
    is_admin: bool = False,
    is_hr: bool = False,
    is_safety: bool = False,
    is_shop: bool = False,
    is_dispatch: bool = False,
    is_pm: bool = False,
    is_leadership: bool = False,
    is_field: bool = False,
    is_authenticated: bool = False,
) -> set[str]:
    """Compute the scope set granted to a caller. Public scope is
    ALWAYS granted (anonymous can see public content). Field scope is
    granted to any authenticated portal (admin/hr/safety/etc are also
    field-eligible because they may need field-facing content)."""
    s: set[str] = {SCOPE_PUBLIC}
    if (
        is_admin or is_hr or is_safety or is_shop or is_dispatch or is_pm
        or is_leadership or is_field or is_authenticated
    ):
        s.add(SCOPE_FIELD)
    if is_admin:
        # Admin sees everything operational
        s.update({SCOPE_ADMIN, SCOPE_HR, SCOPE_SAFETY, SCOPE_SHOP,
                  SCOPE_DISPATCH, SCOPE_PM, SCOPE_LEADERSHIP})
    if is_hr:
        s.add(SCOPE_HR)
    if is_safety:
        s.add(SCOPE_SAFETY)
    if is_shop:
        s.add(SCOPE_SHOP)
    if is_dispatch:
        s.add(SCOPE_DISPATCH)
    if is_pm:
        s.add(SCOPE_PM)
    if is_leadership:
        s.add(SCOPE_LEADERSHIP)
    return s


def article_visible(article: dict, granted_scopes: set[str]) -> bool:
    """True iff the granted scope set intersects article['scopes']."""
    return bool(_normalize_scopes(article.get("scopes") or []) & granted_scopes)


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────
def all_articles() -> list[dict]:
    return list(_ARTICLES)


def visible_articles(granted_scopes: set[str]) -> list[dict]:
    return [a for a in _ARTICLES if article_visible(a, granted_scopes)]


def get_article(article_id: str, granted_scopes: set[str]) -> dict | None:
    for a in _ARTICLES:
        if a["id"] == article_id and article_visible(a, granted_scopes):
            # Filter `related` to only show visible related articles
            allowed_ids = {x["id"] for x in visible_articles(granted_scopes)}
            out = dict(a)
            out["related"] = [
                {"id": r, "title": next((x["title"] for x in _ARTICLES if x["id"] == r), r)}
                for r in (a.get("related") or [])
                if r in allowed_ids
            ]
            return out
    return None


def search_articles(query: str, granted_scopes: set[str], limit: int = 25) -> list[dict]:
    """Title + body keyword match, RBAC-aware, no fuzzy (Phase A spec)."""
    q = (query or "").strip().lower()
    if not q:
        return []
    terms = [t for t in q.split() if t]
    if not terms:
        return []
    results: list[tuple[int, dict]] = []
    for a in visible_articles(granted_scopes):
        haystack = " ".join([
            a.get("title", ""),
            a.get("summary", ""),
            " ".join(a.get("tags") or []),
            _flatten_body(a.get("body") or []),
        ]).lower()
        score = sum(haystack.count(t) for t in terms)
        if score > 0:
            results.append((score, a))
    results.sort(key=lambda x: -x[0])
    return [
        {
            "id": a["id"],
            "title": a["title"],
            "summary": a.get("summary"),
            "section": a["section"],
        }
        for _, a in results[:limit]
    ]


def _flatten_body(blocks: list[dict]) -> str:
    out: list[str] = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        if "text" in b:
            out.append(str(b["text"]))
        if "items" in b:
            out.extend(str(x) for x in (b["items"] or []))
    return " ".join(out)


def sections_for(granted_scopes: set[str]) -> list[dict]:
    """Return SECTIONS annotated with the count of visible articles per section."""
    visible = visible_articles(granted_scopes)
    counts: dict[str, int] = {}
    for a in visible:
        counts[a["section"]] = counts.get(a["section"], 0) + 1
    return [
        {**s, "count": counts.get(s["id"], 0)}
        for s in SECTIONS
        if counts.get(s["id"], 0) > 0
    ]
