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
    # iter317-C · Driver Qualification / trucking operational articles
    # (CDL vs Approved, medical card cadence, tanker endorsements,
    # dashboard interpretation, restrictions & escalation). Scoped to
    # hr+safety+dispatch+admin via per-article `scopes`.
    {"id": "trucking",    "title": "Driver Qualification & Trucking", "icon": "truck"},
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
        "related": ["why-daily-reports", "task-submit-incident", "why-photos",
                    "field-daily-report-howto", "field-coaching-documentation",
                    "field-writeup-authoring", "field-incident-escalation"],
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
        "related": ["why-time-verification", "task-verify-time", "tshoot-employee-not-found",
                    "hr-onboarding-new-hire", "hr-time-verification-deep",
                    "hr-writeups-correctives", "hr-offboarding",
                    "hr-cross-portal-reads", "hr-audit-trail"],
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
        "related": ["why-incidents", "why-corrective-actions", "task-submit-incident",
                    "safety-incident-investigation", "safety-corrective-actions-workflow",
                    "safety-audits-workflow", "safety-fire-extinguishers",
                    "safety-training-compliance", "safety-near-miss-importance",
                    "safety-escalation-chain"],
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
        "related": ["why-equipment-accountability", "tshoot-equipment-not-found",
                    "shop-preop-deep", "shop-failed-preop-workflow", "shop-damage-reporting",
                    "shop-maintenance-coordination", "shop-equipment-return",
                    "shop-operator-responsibilities", "shop-downtime-logic",
                    "connect-shop-to-dispatch"],
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
        "related": ["why-equipment-accountability", "portal-dispatch",
                    "dispatch-equipment-movement", "dispatch-availability-management",
                    "dispatch-holds-transfers", "dispatch-field-coordination",
                    "dispatch-accuracy-why", "connect-shop-to-dispatch"],
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
        "related": ["why-daily-reports", "portal-pm", "pm-project-review-cadence",
                    "pm-labor-documentation", "pm-cross-project-visibility",
                    "pm-reporting-workflows", "pm-coordination",
                    "connect-pm-field-review"],
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
        "related": ["why-audit-logs", "why-backups", "tshoot-session-timeout",
                    "admin-user-management", "admin-audit-forensics", "admin-system-health",
                    "admin-backup-restore", "admin-data-portability",
                    "admin-sentry-observability", "admin-role-templates",
                    "admin-governance-why", "connect-admin-controls"],
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

    # ── PORTAL GUIDES (iter205 — rebuilt to Field Leadership standard) ───
    # Each portal training landing must include: what it is · who uses
    # it · workflows it owns · why it matters · what happens after
    # records land · common mistakes · what to do first · related
    # deeper guidance. Public scope so the /guidance training card
    # action lands on real content for anonymous users.
    {
        "id": "portal-hr",
        "section": "portals",
        "title": "HR Portal Training",
        "summary": "What HR owns, who uses it, and how the work connects to every other portal.",
        "scopes": ["hr", "admin"],
        "tags": ["hr portal", "human resources", "onboarding", "time", "payroll"],
        "body": [
            {"type": "p", "text":
                "HR is the people-and-time portal. It owns the records that prove who worked, "
                "what hours were paid, who was hired, who left, and what training is current. "
                "It is one of the most cross-connected portals on the platform — every other portal "
                "feeds it data, and HR feeds payroll + compliance + every audit conversation."},
            {"type": "p", "text":
                "Who uses it: HR Staff, HR Managers, and Operations support roles. Cross-portal "
                "reads from PM (project labor) and Field Leadership (write-ups, recognition)."},
            {"type": "bullets", "items": [
                "Time verification — comparing crew Daily Reports against payroll",
                "New-hire onboarding — paperwork, credentials, equipment, training",
                "Employee accountability — write-ups, coaching docs, recognition",
                "Training records — OSHA, equipment-certified, internal courses",
                "Document expirations — driver's licenses, medical cards, certifications",
                "Time-off requests — vacation, sick, PTO, public confirmation",
                "Payroll variance — when reported hours don't match the field record",
                "Offboarding / termination — final-pay calculations, asset returns",
            ]},
            {"type": "why", "text":
                "HR is where the field's documentation becomes the company's source of truth. "
                "A Daily Report submitted from the field by a foreman becomes an hours total in HR. "
                "A write-up authored by a superintendent in Field Leadership becomes an accountability "
                "record in HR. A QA/QC inspection signed off in PM becomes a training-pattern signal "
                "for HR. If HR records are wrong, payroll is wrong — and payroll is wrong is the "
                "fastest way to lose a crew."},
            {"type": "next", "items": [
                "If you're new — read the role guide for HR Staff",
                "First task usually: time verification for the current pay period",
                "Walk one new-hire onboarding end-to-end before you do one alone",
                "Bookmark Document Expirations — it never stops needing attention",
            ]},
            {"type": "mistakes", "items": [
                "Approving time without comparing the Daily Report (the field record is the truth)",
                "Closing an onboarding before equipment-issuance is signed",
                "Filing a write-up without the supervisor's signature attached",
                "Letting a license/medical/certification expiration slip past its date",
            ]},
            {"type": "tip", "text":
                "HR records are read by PM and Field Leadership constantly. Treat every HR record "
                "as if the project manager and superintendent will read it tomorrow — because they will."},
            {"type": "warn", "text":
                "If you can't sign in to HR, do not type your HR password into another portal's "
                "login form (Safety, Shop, etc.). Each portal has its own login — pasting the "
                "wrong password elsewhere can temporarily lock your account."},
        ],
        "related": [
            "role-hr",
            "task-verify-time",
            "hr-onboarding-new-hire",
            "hr-time-verification-deep",
            "hr-writeups-correctives",
            "hr-offboarding",
            "tshoot-employee-not-found",
            "public-cant-login",
        ],
    },
    {
        "id": "portal-safety",
        "section": "portals",
        "title": "Safety Portal Training",
        "summary": "Incidents, corrective actions, audits, training compliance — and why none of it is paperwork.",
        "scopes": ["safety", "admin"],
        "tags": ["safety portal", "incidents", "audits", "compliance"],
        "body": [
            {"type": "p", "text":
                "Safety is the portal that turns events into accountability. Every incident, "
                "near-miss, corrective action, audit finding, fire-extinguisher inspection, and "
                "training-compliance check lives here. It is not a paperwork portal — every record "
                "in Safety either prevented an injury, recovered from one, or built the defense for "
                "an OSHA conversation that hasn't happened yet."},
            {"type": "p", "text":
                "Who uses it: Safety Managers, Safety Coordinators, Safety Officers. Cross-portal "
                "reads from Field Leadership (incident context), HR (training records), and Admin."},
            {"type": "bullets", "items": [
                "Incidents — injuries, property damage, near-misses, third-party events",
                "Corrective actions — what gets fixed, by whom, by when, signed off",
                "Audits — site walks, jobsite safety audits, sub-contractor audits",
                "Fire extinguishers — inventory, monthly inspections, recharge tracking",
                "Training compliance — who's current on OSHA-10, OSHA-30, equipment, first-aid",
                "Safety Meetings — meeting topics, attendance, signatures",
                "JHA plans — Job Hazard Analyses authored and approved",
            ]},
            {"type": "why", "text":
                "Safety records are the single most important defensive documentation MASCI produces. "
                "An OSHA inspector showing up tomorrow asks two questions: 'Show me your training "
                "compliance' and 'Show me your last incident.' Safety is where the answers live. "
                "Vague safety records = exposure; specific safety records = defensible operations."},
            {"type": "next", "items": [
                "If you're new — read the role guide for Safety Manager",
                "Walk one open incident end-to-end (report → investigation → corrective → close)",
                "Pull the current training-compliance report for your most active project",
                "Bookmark Fire Extinguishers — monthly cadence catches you fast",
            ]},
            {"type": "mistakes", "items": [
                "Closing an incident without a documented root cause + corrective action",
                "Logging a corrective action without a signed-off completion date",
                "Letting OSHA-10 expirations slip on the active crew (project shutdown risk)",
                "Filing a toolbox-talk without the attendance signatures",
                "Speculating about cause in an incident report — record only observed facts",
            ]},
            {"type": "tip", "text":
                "Near-misses are the cheapest lessons MASCI ever gets. Encourage crews to report "
                "them and document them the same way as injuries — they're the early-warning system."},
            {"type": "warn", "text":
                "Never close an incident before the corrective action is verified complete. "
                "An 'incident closed' record with an open corrective action is the worst possible "
                "audit trail."},
        ],
        "related": [
            "role-safety",
            "safety-incident-investigation",
            "safety-corrective-actions-workflow",
            "safety-audits-workflow",
            "safety-fire-extinguishers",
            "safety-training-compliance",
            "safety-near-miss-importance",
            "public-incident-basics",
        ],
    },
    {
        "id": "portal-shop",
        "section": "portals",
        "title": "Shop / Fleet Portal Training",
        "summary": "Equipment health, Pre-Op review, damage workflow, maintenance coordination — the back-end of fleet operations.",
        "scopes": ["shop", "admin"],
        "tags": ["shop portal", "fleet", "mechanic", "maintenance"],
        "body": [
            {"type": "p", "text":
                "Shop is the portal that keeps the fleet running. Every Pre-Op a field operator "
                "submits flows here. Every damage report, every maintenance task, every parts order, "
                "every equipment return — all of it lives in Shop. The portal exists to make sure "
                "the right gear is operational on the right job at the right time, and to document "
                "what happened to it along the way."},
            {"type": "p", "text":
                "Who uses it: Mechanics, Shop Foreman, Fleet Coordinator. Cross-portal "
                "reads from Dispatch (where equipment is going) and Field Leadership (who has it now)."},
            {"type": "bullets", "items": [
                "Pre-Op review — every field Pre-Op lands here; failed Pre-Ops need action",
                "Fleet DVIR + Weekly Lead + Weekly Emergency — driver/lead inspections route to Shop with severity already attached (OOS / Monitor); repairs flow through the Phase 4 lifecycle to Dispatch Return-to-Service",
                "Damage reporting — what got bent, scraped, broken, by whom, when",
                "Maintenance coordination — scheduled, preventive, emergency",
                "Parts catalog & ordering — what's in stock, what's on order, lead times",
                "Equipment issuance & return — Safety + Shop joint sign-offs",
                "Sign-offs — releasing equipment back to the field after repair",
            ]},
            {"type": "why", "text":
                "Shop records protect everyone. A field operator's Pre-Op signature shows they "
                "did the walk; the shop's repair record shows what was found and fixed; the return "
                "sign-off shows the unit is cleared back to service. If a piece of equipment causes "
                "an incident, the chain of Pre-Op → Damage → Repair → Sign-Off is the entire defense. "
                "Missing records mean missing answers."},
            {"type": "next", "items": [
                "If you're new — read the role guide for Shop / Mechanic",
                "Walk one failed Pre-Op end-to-end from field report to shop sign-off",
                "Open Parts Catalog and learn the ordering lead times by category",
                "Bookmark the equipment-return form — it's joint with Safety",
            ]},
            {"type": "mistakes", "items": [
                "Signing off a unit back to service before the corrective action is verified",
                "Ordering parts without confirming the equipment ID + serial number",
                "Closing damage reports without photos before AND after repair",
                "Skipping the Safety joint sign-off on equipment return",
            ]},
            {"type": "tip", "text":
                "When a failed Pre-Op lands, the goal isn't to win the argument with the field — "
                "it's to determine whether the unit is operationally safe right now. Field operators "
                "who feel heard report problems faster the next time."},
        ],
        "related": [
            "role-shop",
            "shop-preop-deep",
            "shop-failed-preop-workflow",
            "shop-damage-reporting",
            "shop-maintenance-coordination",
            "shop-equipment-return",
            "connect-shop-to-dispatch",
            "connect-equipment-lifecycle",
            "public-preop-basics",
            "fleet-daily-dvir",
            "fleet-repair-lifecycle",
        ],
    },
    {
        "id": "portal-admin",
        "section": "portals",
        "title": "Admin Console Guidance",
        "summary": "The control plane — people, roles, system health, backups, governance.",
        "scopes": ["admin"],
        "tags": ["admin portal", "operator", "control plane"],
        "body": [
            {"type": "p", "text":
                "Admin is the operator-level control plane of the platform. It is intentionally "
                "narrow in audience — typically the platform owner and one or two trusted operators. "
                "Admin owns the surfaces no other portal can see: every user, every role template, "
                "every audit-log entry, every active session, every backup, and the governance signals "
                "that tell you when something is drifting."},
            {"type": "p", "text":
                "Who uses it: the platform Owner and designated Operator(s). Not for general staff."},
            {"type": "bullets", "items": [
                "User management — invite, role-assign, suspend, restore",
                "Role templates — define what each portal token grants",
                "Audit log — every privileged action, who/when/what",
                "System health — backend metrics, queue depths, error rates",
                "Sessions — who is signed in right now, force-revoke if needed",
                "Backups & restore — manual triggers, schedule, point-in-time recovery",
                "Data portability — compliance-grade export per record family",
                "Operational inventory & governance — drift detection across portals",
                "Sentry observability — error tracking, release tagging",
            ]},
            {"type": "why", "text":
                "Admin work has the deepest blast radius on the platform. A single role-template "
                "change ripples to every user who has that role. A force-revoked session locks "
                "someone out mid-task. The audit log is the only place where 'who changed what when' "
                "is permanently recorded — and the only safeguard against assumptions in disputes. "
                "Admin is intentionally English-only because operators need precise terminology, "
                "not translated approximations."},
            {"type": "next", "items": [
                "If you're new to operator role — read Admin User Management first",
                "Run a manual backup and walk the restore process in a safe context",
                "Open the Operational Inventory dashboard and read every drift item",
                "Bookmark the Audit Log — every operator action you take lands there",
            ]},
            {"type": "mistakes", "items": [
                "Modifying a role template without checking who currently holds that role",
                "Force-revoking a session without telling the user first",
                "Editing user records without an audit-log-friendly reason in the notes",
                "Skipping the operational-inventory drift review during weekly checks",
            ]},
            {"type": "tip", "text":
                "When Admin work touches multiple users (role changes, bulk suspend), pair it with "
                "a Slack/email notice. The audit log records the action; communication records the "
                "operational intent."},
            {"type": "warn", "text":
                "Admin tokens grant access to every other portal automatically. Never share an "
                "admin token. If an admin password needs rotation, rotate the role-token grants too."},
        ],
        "related": [
            "role-admin",
            "admin-user-management",
            "admin-audit-forensics",
            "admin-system-health",
            "admin-backup-restore",
            "admin-data-portability",
            "admin-sentry-observability",
            "admin-role-templates",
            "admin-governance-why",
        ],
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
        "related": ["role-superintendent", "role-foreman", "connect-field-to-payroll",
                    "field-daily-report-howto"],
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

    # ═════════════════════════════════════════════════════════════════
    # PHASE 3 · PUBLIC FIELD CREW TRAINING (iter196 · preview only)
    # Operator directive: field crews and new employees may not have
    # portal logins but still need useful, safe public training. Public
    # articles must NEVER expose restricted operational intelligence —
    # they teach the WHAT and the WHY, not the HOW for restricted roles.
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "public-mobile-qr",
        "section": "onboarding",
        "title": "Scan-and-Go: Using the QR code at your job site",
        "summary": "Open the MASCI Operations Platform on your phone in seconds.",
        "scopes": ["public"],
        "tags": ["public", "mobile", "qr", "field crew", "job site"],
        "body": [
            {"type": "p", "text":
                "Most job-site signs and time-card posters carry a MASCI QR code. "
                "Scanning it opens the platform on your phone — no app to install, "
                "no URL to remember."},
            {"type": "steps", "items": [
                "Open your phone's camera",
                "Point it at the QR code on the job-site sign or poster",
                "Tap the link that appears at the top of the screen",
                "Bookmark the page or add it to your home screen so you don't need the QR next time",
            ]},
            {"type": "tip", "text":
                "If the QR doesn't open the platform, the link expired or the sign is "
                "out of date. Tell your supervisor — they'll get a fresh sign printed."},
        ],
        "related": ["onboard-login", "onboard-mobile", "public-photos"],
    },
    {
        "id": "public-photos",
        "section": "onboarding",
        "title": "Photos that actually help",
        "summary": "What to photograph in the field — and how.",
        "scopes": ["public"],
        "tags": ["public", "photos", "documentation", "field crew"],
        "body": [
            {"type": "p", "text":
                "Whenever you take a photo for MASCI, you're creating a record someone "
                "may rely on later. A clear photo can answer a question; a blurry one "
                "creates a new one."},
            {"type": "bullets", "items": [
                "Wide shot first (the whole area)",
                "Then close-up shots (the specific item or issue)",
                "Include a hand or tape measure if size matters",
                "Re-take if the photo is blurry",
                "More is better — delete is cheap, returning to the site isn't",
            ]},
            {"type": "why", "text":
                "Photos protect you. If anyone later asks 'what did it look like?', a good "
                "photo answers it. If only words exist, the answer depends on memory — and "
                "memory loses every argument."},
        ],
        "related": ["public-daily-report-basics", "public-incident-basics"],
    },
    {
        "id": "public-daily-report-basics",
        "section": "onboarding",
        "title": "What a daily report is (and why yours matters)",
        "summary": "The 60-second explanation for field crew.",
        "scopes": ["public"],
        "tags": ["public", "daily report", "field crew", "why"],
        "body": [
            {"type": "p", "text":
                "Every workday gets a Daily Report. Your supervisor or foreman submits "
                "it before the crew leaves the site. It records: who was there, what was "
                "done, what was used, and anything that came up."},
            {"type": "why", "text":
                "That report is what the office reads to know how the job is going. It "
                "feeds payroll, project status, and any after-the-fact question about the "
                "day. Your work shows up there — accurately reporting hours and conditions "
                "is how your day gets fairly documented."},
            {"type": "bullets", "items": [
                "Tell your supervisor if hours were missed or recorded wrong",
                "Flag issues out loud at the end of the day so they make it into the report",
                "Photos you took on the phone may get included — keep them clear",
            ]},
        ],
        "related": ["public-photos", "public-who-to-ask", "public-why-documentation"],
    },
    {
        "id": "public-incident-basics",
        "section": "troubleshooting",
        "title": "If something happens on a job site",
        "summary": "First steps after any injury, near-miss, or damage.",
        "scopes": ["public"],
        "tags": ["public", "incident", "field crew", "safety"],
        "body": [
            {"type": "p", "text":
                "Things happen. What matters is what you do in the next few minutes."},
            {"type": "steps", "items": [
                "Make the area safe first — that always comes first, before paperwork",
                "Tell the supervisor or foreman immediately — in person, not by text",
                "If someone is hurt, get medical help — call 911 if it's serious",
                "Take photos of the scene if it's safe to do so",
                "Do not move equipment or clean up until told to (it preserves the evidence)",
            ]},
            {"type": "why", "text":
                "Quick honest reporting protects everyone — the person hurt, the crew, the "
                "supervisor, and the company. Late or vague reporting protects nobody."},
            {"type": "warn", "text":
                "Do not guess about cause or assign blame. Just describe what you saw. "
                "Safety will investigate from there."},
            {"type": "tip", "text":
                "A near-miss (something almost happened — almost fell, almost dropped, "
                "almost hit) is worth reporting. Report it the same way: facts, time, "
                "place, photos if relevant. Near-misses are the cheapest lessons the "
                "crew gets — speak up and you may have just prevented the real one."},
        ],
        "related": ["public-who-to-ask", "public-photos", "public-why-documentation",
                    "public-toolbox-talks"],
    },
    {
        "id": "public-cant-login",
        "section": "troubleshooting",
        "title": "I can't log in",
        "summary": "Most-common login problems and what to try.",
        "scopes": ["public"],
        "tags": ["public", "troubleshooting", "login"],
        "body": [
            {"type": "p", "text":
                "Login problems are usually one of three things. Try in this order."},
            {"type": "steps", "items": [
                "Double-check the email or username — typos are #1",
                "Make sure caps lock isn't on for the password",
                "If you got temp credentials, the first login forces a password change — finish that step",
                "If you keep getting 'invalid credentials' after several tries, the account may be locked — wait 15 minutes and try again",
                "If still stuck, ask HR (for HR/Field/Shop logins) or your IT contact (for Admin)",
            ]},
            {"type": "tip", "text":
                "Bookmark the login page after your first successful login. Re-typing the "
                "URL on a phone every time is where typos sneak in."},
        ],
        "related": ["public-who-to-ask", "onboard-login", "tshoot-session-timeout"],
    },
    {
        "id": "public-who-to-ask",
        "section": "knowledge",
        "title": "Who do I ask for help?",
        "summary": "A quick map of who handles what.",
        "scopes": ["public"],
        "tags": ["public", "help", "directory"],
        "body": [
            {"type": "p", "text":
                "MASCI Operations Platform is run by different teams for different things. "
                "Knowing who to ask saves a lot of back-and-forth."},
            {"type": "bullets", "items": [
                "Wrong hours / paycheck question → talk to your supervisor first, then HR",
                "Equipment broken or unsafe → tell your supervisor and Shop",
                "Got hurt or saw something unsafe → supervisor + Safety",
                "Can't log in or account locked → HR (for most portals) or your IT contact (Admin)",
                "Forgot a password → HR can reset it; do NOT share passwords",
                "Question about a job-site assignment → your supervisor or PM",
            ]},
            {"type": "tip", "text":
                "If you don't know who to ask, ask your direct supervisor. They'll route "
                "it to the right place."},
        ],
        "related": ["public-cant-login", "public-incident-basics", "public-why-documentation"],
    },
    {
        "id": "public-why-documentation",
        "section": "knowledge",
        "title": "Why this paperwork matters",
        "summary": "The field crew's version of 'why the platform exists'.",
        "scopes": ["public"],
        "tags": ["public", "why", "documentation", "field crew"],
        "body": [
            {"type": "p", "text":
                "MASCI's documentation isn't busywork. Every form, every photo, every "
                "report exists to answer a question that comes up later — sometimes weeks "
                "later, sometimes years."},
            {"type": "bullets", "items": [
                "Daily reports → answer 'what got built today?'",
                "Time records → answer 'did the paycheck match the work?'",
                "Incident reports → answer 'what happened?' for insurance, doctors, lawyers",
                "Equipment records → answer 'who had what and was it working?'",
                "Photos → answer 'what did it look like?'",
            ]},
            {"type": "why", "text":
                "Most disputes — over hours, over damage, over what was agreed — get "
                "settled by whatever was written down at the time. People who document well "
                "get the benefit of the doubt. People who don't, don't."},
        ],
        "related": ["public-daily-report-basics", "public-incident-basics",
                    "public-photos", "public-who-to-ask"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE 3 · PUBLIC FIELD TOOLS — REAL ROUTE COVERAGE (iter197)
    # ─────────────────────────────────────────────────────────────────
    # Operator directive: every public/no-login surface in the actual
    # platform must have a public guidance article. The routes covered
    # here come from a code-level audit of /app/frontend/src/App.js:
    #   /equipment/submit      → public-preop-basics
    #   /meetings/submit       → public-toolbox-talks
    #   /qaqc, /qaqc/:slug/new → public-qaqc-basics
    #   /field/calculators     → public-material-calculator
    #   /submit, /inspections/submit, /jha, /trench-boxes, /cheatsheet,
    #   /daily/submit, /incidents/submit, /meetings/submit, /equipment/submit
    #                          → public-tools-map (overview index)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "public-preop-basics",
        "section": "onboarding",
        "title": "Equipment Pre-Op Checks (Field Basics)",
        "summary": "Daily check before you operate. Sign your name. Flag what's broken.",
        "scopes": ["public"],
        "tags": ["public", "pre-op", "equipment", "field crew", "inspection"],
        "body": [
            {"type": "p", "text":
                "Before you run any piece of equipment, you walk it. A Pre-Op is the "
                "record of that walk-around: fluids, tires, lights, safety devices, "
                "obvious damage. You sign your name and submit before you start work."},
            {"type": "steps", "items": [
                "Open the Pre-Op form (scan the QR on the asset, or use the public submit link)",
                "Walk the machine — actually look, don't box-tick from the seat",
                "Check fluids, tires/tracks, lights, alarms, seatbelt, guards, controls",
                "Photograph anything wrong before you submit",
                "Submit. The form locks in the time and your name",
            ]},
            {"type": "why", "text":
                "Pre-Op protects you. If the equipment was damaged before you used it, "
                "your signed Pre-Op shows you flagged it. If you didn't sign, the question "
                "becomes whether you caused the damage. Five minutes of walking around is "
                "the cheapest insurance on the job."},
            {"type": "warn", "text":
                "If something fails inspection, do NOT use the equipment. Tell your "
                "supervisor. The shop has to clear it before it goes back into service."},
            {"type": "bullets", "items": [
                "Brakes feel weak → stop, don't operate",
                "Hydraulic leak → stop, don't operate",
                "Missing/cracked guards → stop, don't operate",
                "Anything you wouldn't trust your kid in → stop",
            ]},
        ],
        "related": ["public-photos", "public-who-to-ask", "public-tools-map"],
    },
    {
        "id": "public-toolbox-talks",
        "section": "onboarding",
        "title": "Safety Meetings",
        "summary": "Real-world incident pattern first. Then the action drill. Sign the roster — that's your acknowledgement.",
        "scopes": ["public"],
        "tags": ["public", "safety meeting", "field crew", "incident pattern"],
        "body": [
            {"type": "p", "text":
                "A MASCI Safety Meeting is not a generic safety briefing. It runs from a "
                "curated library of 130+ heavy-civil and highway topics — each one "
                "written around a real-world incident pattern that has actually killed "
                "or seriously hurt construction workers. The foreman picks the topic, "
                "reads the WHAT HAPPENS paragraph to the crew, then walks through the "
                "action drill. That's the format. Same in English. Same in Spanish."},
            {"type": "p", "text":
                "If you've been to a MASCI Safety Meeting before, you've already "
                "noticed it doesn't sound like compliance training. That's intentional. "
                "The topics are written in the voice of experienced superintendents "
                "and foremen describing what actually happens on jobsites — not what a "
                "policy says should happen."},
            {"type": "steps", "items": [
                "Show up on time — most meetings run 5–15 minutes",
                "Listen to the WHAT HAPPENS / PATRÓN REAL paragraph first — that's the real incident pattern the topic is built around",
                "Then the bullets — those are the action steps for today's work",
                "If anything's unclear, ask before the crew breaks. The foreman would rather answer now than read about it later",
                "Sign the attendance form (paper or digital) — that's the record you were there",
                "If you spotted a hazard during the talk, speak up. Stop Work Authority belongs to every person on the crew",
            ]},
            {"type": "why", "text":
                "The incident-pattern format exists because compliance language doesn't "
                "stick. A worker hearing \"maintain situational awareness during backing \"\n                \"operations\" forgets it by lunch. A worker hearing \"the spotter was on his "
                "phone for four seconds — the dump truck rolled over the laborer behind "
                "it — that's the pattern\" remembers it for a career. The signature on "
                "the roster says you heard the pattern AND the action drill."},
            {"type": "bullets", "items": [
                "Every English topic has a 1:1 Spanish version, written in field Spanish — not Google-translated. Field voice in both languages.",
                "Topics are organized into 21 operational domains: Concrete · Paving · Milling · MOT · Trucking · Excavation · Dewatering · Shop · Plant · Fall Protection · Confined Space · Electrical · Wellness · and more",
                "Wellness topics (heat, fatigue, mental health) are written operationally — judgment-degradation framing, not corporate wellness language",
                "Severity classification is internal Safety/Admin metadata — it does not appear on the crew-facing meeting",
            ]},
            {"type": "tip", "text":
                "If you can't make a meeting (medical, late shift, off-site task), "
                "tell your supervisor. Acknowledgement can sometimes be captured "
                "separately — but it has to be captured. Missing the meeting is fine; "
                "skipping the acknowledgement is not."},
            {"type": "warn", "text":
                "If the foreman ever shortcuts the WHAT HAPPENS paragraph to save time "
                "and jumps straight to the bullets — speak up. The incident pattern IS "
                "the lesson. The bullets are how you avoid becoming the next one."},
        ],
        "related": ["public-incident-basics", "public-why-documentation", "public-tools-map"],
    },
    {
        "id": "public-qaqc-basics",
        "section": "onboarding",
        "title": "QA/QC for Field Crews",
        "summary": "Quality checks while you work — photos, measurements, sign-offs.",
        "scopes": ["public"],
        "tags": ["public", "qaqc", "quality", "field crew", "inspection"],
        "body": [
            {"type": "p", "text":
                "QA/QC means Quality Assurance / Quality Control. In the field, it's "
                "the records you create that prove the work was done to spec — photos of "
                "rebar before pour, dimensions, materials used, sign-offs at each stage."},
            {"type": "bullets", "items": [
                "Photo BEFORE you cover it (concrete pour, backfill, sheetrock, etc.)",
                "Photo AFTER if condition matters",
                "Record measurements / counts when asked — guesses don't help anybody",
                "Note who inspected and when, if you're the one doing it",
            ]},
            {"type": "why", "text":
                "QA/QC documentation protects the project. If the owner or inspector "
                "ever asks 'is this to spec?', the answer is whatever the photos and "
                "records say. Good records = no rework arguments. Missing records = "
                "rework or worse."},
            {"type": "warn", "text":
                "Do not pour, cover, or close out work that was supposed to be inspected "
                "first. Wait for the sign-off, or capture the inspection record on the spot."},
        ],
        "related": ["public-photos", "public-why-documentation", "public-tools-map"],
    },
    {
        "id": "public-material-calculator",
        "section": "onboarding",
        "title": "Material Calculator & Field Tools",
        "summary": "Quick math for concrete, gravel, asphalt, and more.",
        "scopes": ["public"],
        "tags": ["public", "calculator", "material", "field crew", "tool"],
        "body": [
            {"type": "p", "text":
                "The Material Calculator is a no-login tool on the MASCI platform that "
                "estimates quantities for common materials — concrete (yards), gravel "
                "(tons), asphalt (tons), pipe trench backfill, and similar. It's a "
                "ball-park: useful for ordering and double-checking, NOT a substitute for "
                "engineered drawings."},
            {"type": "steps", "items": [
                "Pick the material type",
                "Enter the dimensions (length × width × depth, or whatever the tool asks)",
                "Check the calculated quantity",
                "Compare to your plan or the supervisor's number — if they don't agree, ask before ordering",
            ]},
            {"type": "why", "text":
                "Over-ordering material wastes money; under-ordering stops the crew. The "
                "calculator catches obvious errors before the truck shows up. A 30-second "
                "check is cheaper than half a day of waiting."},
            {"type": "mistakes", "items": [
                "Mixing units (feet vs inches, yards vs tons) — read the labels carefully",
                "Forgetting waste/compaction factors — supervisor knows the right multiplier",
                "Trusting the calculator over the plan when they disagree — verify",
            ]},
            {"type": "tip", "text":
                "When in doubt, send the supervisor a screenshot of the calculator result "
                "before placing an order. Two-minute confirmation, zero re-orders."},
        ],
        "related": ["public-who-to-ask", "public-tools-map"],
    },
    {
        "id": "public-tools-map",
        "section": "knowledge",
        "title": "Public Field Tools — What's Available Without Login",
        "summary": "Every no-login tool on the MASCI platform and what each is for.",
        "scopes": ["public"],
        "tags": ["public", "tools", "field crew", "directory", "overview"],
        "body": [
            {"type": "p", "text":
                "Many MASCI tools work without a portal login — you can use them from "
                "any phone, on any job site, by scanning the QR or following a link. Here "
                "is what's available and what each is for."},
            {"type": "bullets", "items": [
                "Daily Report submit — record the workday before leaving the site",
                "Equipment Pre-Op submit — sign off that equipment is safe to run",
                "Incident submit — report an injury / near-miss / damage",
                "Site Inspection submit — public safety walk inspection",
                "Safety Meeting submit — sign attendance, log the topic",
                "QA/QC checklists — quality records by trade / stage",
                "Material Calculator — quick quantity math",
                "JHA / Trench Box reference — printable hazard reference",
                "Cheat Sheet — quick reference card for the most-used forms",
            ]},
            {"type": "tip", "text":
                "Bookmark the platform URL on your phone after the first scan — you "
                "won't need the QR every time. Add it to your phone's home screen for "
                "one-tap access."},
            {"type": "next", "items": [
                "Submitted forms are picked up by the office team for review",
                "Most flow into payroll / safety / project records the next business day",
                "Anything urgent (incident, equipment failure) — also tell the supervisor in person",
            ]},
        ],
        "related": ["public-daily-report-basics", "public-preop-basics",
                    "public-incident-basics", "public-toolbox-talks",
                    "public-qaqc-basics", "public-material-calculator",
                    "public-mobile-qr", "public-who-to-ask"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B · HR PORTAL DEEP CONTENT (iter191 · preview only)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "hr-onboarding-new-hire",
        "section": "portals",
        "title": "HR · Onboarding a New Hire",
        "summary": "Account setup, equipment issuance, training assignment, paper trail.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "onboarding", "new hire", "setup", "account", "equipment"],
        "body": [
            {"type": "p", "text":
                "Onboarding a new hire creates the operational record that follows them "
                "for their entire tenure. The goal is one clean trail: account exists, "
                "equipment is signed for, training is assigned, supervisor knows."},
            {"type": "steps", "items": [
                "Confirm the hire packet is complete (offer accepted, I-9, W-4) — outside the platform",
                "In Admin → People & Access, create the employee's portal account (field / shop / dispatch as appropriate)",
                "Set must_change_password=true and deliver the temp credentials via the channel HR uses (email / in person)",
                "Open Safety Forms → Equipment Issuance for any PPE / tools / phone / tablet assigned on day one",
                "Open Safety Forms → Equipment Training for required first-day training (extinguisher, lift, etc.)",
                "Tell the supervisor in writing — the audit log records you did this",
            ]},
            {"type": "why", "text":
                "Day-one documentation prevents the two most expensive HR problems: "
                "an employee disputing what they were given, and an employee using equipment "
                "they weren't trained on. Both come back to whether the paper trail exists."},
            {"type": "next", "items": [
                "Equipment issuance auto-emails Safety + HR (audit-tracked)",
                "The supervisor sees the new hire in their crew roster the next time they open Field Leadership",
                "Training records are searchable by Safety for audits",
                "Time entries become possible on the first work day",
            ]},
            {"type": "mistakes", "items": [
                "Skipping the equipment issuance form because 'it's just a hard hat'",
                "Not setting must_change_password — temp credentials live forever",
                "Issuing equipment without recording the training that authorizes its use",
                "Forgetting to tell the supervisor (they will not know the person is starting)",
            ]},
        ],
        "related": ["hr-offboarding", "hr-audit-trail", "task-verify-time", "role-hr"],
    },
    {
        "id": "hr-time-verification-deep",
        "section": "portals",
        "title": "HR · Time Verification Deep Dive",
        "summary": "Regular / Overtime / Lunch invariant, payroll cross-check, defensible record.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "time verification", "payroll", "overtime", "flsa", "lunch"],
        "body": [
            {"type": "p", "text":
                "Time Verification compares supervisor-entered hours against the payroll system. "
                "The platform does the FLSA Regular/Overtime split at the weekly rollup, not "
                "per day. Lunch is unpaid and tracked separately."},
            {"type": "bullets", "items": [
                "Total paid hours = Regular + Overtime (invariant — never breaks)",
                "Lunch is tracked but is NOT included in paid totals",
                "OT is the weekly portion above 40 hours of regular work",
                "Daily rows show 0.00 for Reg/OT — that is by design; the rollup is weekly",
            ]},
            {"type": "steps", "items": [
                "Open HR → Time Verification",
                "Pick the pay period (week ending)",
                "Scan the summary cards: Total Hours / Regular / Overtime / Lunch",
                "Drill into any employee whose totals look wrong",
                "Flag discrepancies to the supervisor — do NOT silently edit",
                "Export CSV with the WEEKLY ROLLUP section for payroll cross-check",
            ]},
            {"type": "why", "text":
                "Time Verification is the most-questioned record we keep. If a paycheck is "
                "ever disputed, this is the record that answers it. A clean weekly rollup "
                "with a signed CSV is a defensible record. A guessed or backfilled entry is not."},
            {"type": "next", "items": [
                "Verified totals feed payroll cross-check (outside the platform)",
                "CSV export with WEEKLY ROLLUP totals can be archived per pay period",
                "Discrepancies become Field Leadership follow-ups — supervisor edits the source, not HR",
            ]},
            {"type": "warn", "text":
                "HR does not edit supervisor-entered hours. If a number is wrong, the "
                "supervisor fixes it in the source record — that preserves the chain of custody."},
        ],
        "related": ["task-verify-time", "why-time-verification", "connect-field-to-payroll", "role-hr"],
    },
    {
        "id": "hr-writeups-correctives",
        "section": "portals",
        "title": "HR · Write-Ups & Corrective Action Follow-Through",
        "summary": "What makes a defensible HR write-up and how it travels through the platform.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "write-up", "corrective action", "discipline", "documentation"],
        "body": [
            {"type": "p", "text":
                "Write-Ups originate in Field Leadership (supervisor authors). HR reviews, "
                "files, and follows up. A write-up is operational documentation, not a "
                "punishment — its job is to record that a conversation happened, what was "
                "agreed, and what the next step is."},
            {"type": "bullets", "items": [
                "Supervisor authors the write-up in Field Leadership",
                "HR reviews via HR → Field Leadership Records",
                "Corrective Actions (if any) are tracked separately by Safety",
                "Every write-up is timestamped, attributed, and audit-logged",
            ]},
            {"type": "why", "text":
                "A defensible write-up protects everyone. It protects the employee from "
                "vague accusations, the supervisor from selective memory, and the company "
                "from disputes. Vague write-ups protect nobody."},
            {"type": "mistakes", "items": [
                "Editing the supervisor's original record — HR reviews, doesn't rewrite",
                "Closing the loop verbally without recording it",
                "Treating a write-up as the end of the story — it's usually the start of one",
                "Skipping the conversation and just filing the form",
            ]},
            {"type": "next", "items": [
                "Write-up becomes visible to HR, Admin, and the authoring supervisor",
                "If a Corrective Action is opened, Safety owns the follow-through",
                "Repeated write-ups for the same employee surface in HR review patterns",
            ]},
        ],
        "related": ["field-writeup-authoring", "why-corrective-actions", "hr-audit-trail", "role-hr"],
    },
    {
        "id": "hr-offboarding",
        "section": "portals",
        "title": "HR · Employee Offboarding",
        "summary": "Equipment return, account disable, final pay, audit closure.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "offboarding", "termination", "final pay", "equipment return"],
        "body": [
            {"type": "p", "text":
                "Offboarding is the reverse of onboarding — and just as important. The goal "
                "is no loose ends: every assigned item is returned or accounted for, every "
                "account is disabled, and the last paycheck reflects verified hours."},
            {"type": "steps", "items": [
                "Pull the employee's equipment-issuance history (HR → Employee Accountability)",
                "Confirm each item is returned, transferred, or written off — record which",
                "Run a final Time Verification through their last work day",
                "Disable the employee's portal account in Admin → People & Access (do NOT delete)",
                "Note the offboarding date in their record",
                "Inform payroll of the final pay window (outside the platform)",
            ]},
            {"type": "why", "text":
                "Offboarding documentation answers two questions that come back later: "
                "'Did we get our stuff back?' and 'Was the last paycheck right?'. A clean "
                "offboarding closes both before they become a dispute."},
            {"type": "warn", "text":
                "Disable accounts, do NOT delete them. Deleting an account breaks every audit "
                "trail that references that user. Disable preserves history; delete erases it."},
            {"type": "next", "items": [
                "Disabled account stops working immediately on next page load",
                "Equipment records show the asset is unassigned (Shop / Dispatch can re-issue)",
                "Final Time Verification CSV is the auditable record for the last paycheck",
                "Audit log preserves the disable action with the actor and timestamp",
            ]},
        ],
        "related": ["hr-onboarding-new-hire", "why-equipment-accountability", "hr-audit-trail"],
    },
    {
        "id": "hr-cross-portal-reads",
        "section": "knowledge",
        "title": "HR · What You Can Read in Other Portals",
        "summary": "HR's cross-portal read scope — what is and isn't visible.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "cross-portal", "read access", "rbac", "safety records"],
        "body": [
            {"type": "p", "text":
                "HR has read access into adjacent portals when the data ties back to an "
                "employee. That visibility is intentionally narrow — HR reviews, it does "
                "not edit other portals."},
            {"type": "bullets", "items": [
                "Safety records (incidents tied to an employee) — read-only",
                "Equipment issuance / training records — read-only",
                "Field Leadership write-ups & coaching — read-only review",
                "Time Verification for any project supervisor enters hours on",
            ]},
            {"type": "warn", "text":
                "HR does NOT see admin audit logs, system health, backups, or other HR "
                "users' password resets. Those stay with Admin."},
            {"type": "why", "text":
                "Cross-portal reads let HR build a complete picture of an employee without "
                "needing admin escalation for routine review work. Writes stay locked to "
                "the originating portal — that preserves chain of custody."},
        ],
        "related": ["role-hr", "hr-audit-trail", "role-safety"],
    },
    {
        "id": "hr-audit-trail",
        "section": "knowledge",
        "title": "HR · Audit Trail — What Gets Logged",
        "summary": "What HR actions are recorded and where to find them.",
        "scopes": ["hr", "admin"],
        "tags": ["hr", "audit", "log", "compliance"],
        "body": [
            {"type": "p", "text":
                "Every HR action that touches an account or a record is logged. The audit "
                "trail answers 'who did what, and when' for HR-significant actions."},
            {"type": "bullets", "items": [
                "Login / logout events (with IP)",
                "Account create / disable / password reset (admin actions)",
                "Time Verification CSV exports",
                "Cross-portal record views are NOT individually logged (volume too high) — but the access scope is enforced server-side",
            ]},
            {"type": "p", "text":
                "Admins can review the full audit log in Admin → Audit Log. HR users see "
                "their own action history through HR review surfaces."},
            {"type": "why", "text":
                "The audit trail is a regression detector. If a record looks wrong, the "
                "trail shows whether it was always wrong or whether someone changed it."},
        ],
        "related": ["why-audit-logs", "role-hr"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B · FIELD LEADERSHIP DEEP CONTENT (iter191 · preview only)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "portal-leadership",
        "section": "portals",
        "title": "Field Leadership Portal Quick-Start",
        "summary": "Daily ops surface for supers, foremen, and crew leads.",
        "scopes": ["leadership", "admin"],
        "tags": ["field leadership", "portal", "supervisor"],
        "body": [
            {"type": "p", "text":
                "Field Leadership is the daily-operations surface for supers, foremen, and "
                "crew leads. Everything you document here flows into HR, Safety, and PM review."},
            # iter317-B · "Which door do I use?" disambiguation. Two
            # operational doors exist side-by-side; both are valid;
            # they do different jobs. Surface the answer at the top
            # so a new Super/Foreman never bounces between them.
            {"type": "tip", "text":
                "Which door do I use? There are two Field Leadership "
                "doors: (1) /field-leadership/portal/login — your "
                "per-user account, where everything you submit is "
                "signed under your name; (2) /field-leadership/login "
                "— the shared-password gate for read-only crew "
                "documents. Day-to-day operations work happens in "
                "(1). The shared gate stays in place for crew "
                "document access; it does not unlock the workflows "
                "below."},
            {"type": "bullets", "items": [
                "Daily Reports",
                "Write-Ups / Verbal Coaching / Attendance",
                "Recognition",
                "Equipment Checkout",
                "New Employee / Crew Evaluations",
                "Training Deficiency notes",
            ]},
            {"type": "tip", "text":
                "Use the mobile home-screen shortcut. The portal is built mobile-first because "
                "most documentation happens on a phone in the field."},
        ],
        "related": ["field-daily-report-howto", "field-coaching-documentation", "role-foreman",
                    "portal-field-leadership-portal-accounts"],
    },
    # ── Pass 4 — Field Leadership Operational Identity (iter200) ─────────
    # New articles supporting the first-class /leadership/login URL + the
    # operational-identity messaging on the login page. Onboarding and
    # troubleshooting use `public` scope so they're readable BEFORE login.
    # The identity article uses leadership scope (assumes you're already in).
    {
        "id": "onboard-leadership-first-week",
        "section": "onboarding",
        "title": "Field Leadership — First Week",
        "summary": "What a new Superintendent or Foreman does in their first week on MASCI.",
        "scopes": ["public"],
        "tags": ["onboarding", "leadership", "first week", "supervisor", "foreman", "superintendent"],
        "body": [
            {"type": "p", "text":
                "Welcome to Field Leadership. This portal is the daily operations surface "
                "for Superintendents, Foremen, Field Leaders, and Operations Oversight. "
                "Here is what to do your first week."},
            # iter317-B · "Which door do I use?" disambiguation at the
            # top so the rest of the article isn't ambiguous. The
            # per-user portal (iter314) is the operational door; the
            # shared-password gate stays in place for read-only crew
            # documents only.
            {"type": "tip", "text":
                "Which door do I use? Two valid doors exist. The "
                "operational one — where your Daily Reports, "
                "write-ups, equipment sign-outs, and crew "
                "evaluations live — is /field-leadership/portal/"
                "login (your per-user company email + password, "
                "issued by HR or Admin). The legacy shared-"
                "password door at /field-leadership/login is read-"
                "only for crew documents. If HR or Admin has "
                "given you a per-user account, that is the door "
                "you use day-to-day."},
            {"type": "steps", "items": [
                "Day 1 — Find out which door HR/Admin set you up with. If you have a per-user account, sign in at /field-leadership/portal/login with your company email and the temporary password you were issued; the portal will force you to change it on first sign-in. If you only have the shared crew password, the office can issue you a per-user account in a few minutes.",
                "Day 1 — Read the 'What does Field Leadership do?' article (linked at the bottom of the login page).",
                "Day 2 — Submit your first Daily Report on the actual job (not a test). Photos. Crews. Hours. Conditions.",
                "Day 2-3 — Walk the lifecycle of one equipment Pre-Op from operator → shop → back to field. Understand what your sign-off triggers.",
                "Day 3-4 — Issue one piece of PPE / equipment using Equipment Checkout. The record is the proof.",
                "Day 4-5 — Run a Safety Meeting and submit the attendance form.",
                "End of Week 1 — If you have any documentation event (verbal coaching, write-up, recognition), enter it the same day. Late documentation is weaker documentation.",
            ]},
            {"type": "why", "text":
                "Field Leadership is the most operationally connected portal in MASCI — your "
                "Daily Reports feed payroll (HR), your write-ups feed accountability (HR + Safety), "
                "your equipment sign-outs feed Shop + Dispatch, and your project notes feed PM. "
                "The first week is about understanding that everything you document touches "
                "another team. Get the rhythm right and the rest of the platform works around you."},
            {"type": "tip", "text":
                "Add the per-user portal to your phone home screen on Day 1. Almost every Field "
                "Leadership task is done on a phone in the field — installing the shortcut early "
                "saves you 5-10 taps per submission for the rest of your career here."},
            # iter317-B · the original article said "Field Leadership
            # uses a SHARED leadership password." That is no longer
            # universally true after iter314; replace the warning
            # with the per-user accountability message that fits the
            # current operational model.
            {"type": "warn", "text":
                "Your per-user portal password is yours alone — not "
                "the crew's. Every action you submit is signed in "
                "your name in the audit trail. Don't text the "
                "password to a foreman or share it 'just so they "
                "can pull a report.' If a teammate needs access, "
                "that's an HR/Admin account-issuance conversation, "
                "not a password-sharing workaround."},
            {"type": "next", "items": [
                "Bookmark this article — it's also the answer to 'what do I do next' for the first month",
                "Read 'Submitting a Defensible Daily Report' — referenced more than any other guide here",
                "Read 'Field Leadership Portal Accounts' (the per-user identity overview)",
                "Talk to your PM about which projects you'll be assigned",
            ]},
        ],
        "related": [
            "portal-leadership-identity",
            "portal-field-leadership-portal-accounts",
            "tshoot-leadership-login",
            "field-daily-report-howto",
            "role-superintendent",
            "role-foreman",
        ],
    },
    {
        "id": "tshoot-leadership-login",
        "section": "troubleshooting",
        "title": "Can't sign in to Field Leadership",
        "summary": "Quick fixes for both Field Leadership doors — per-user portal and legacy shared-password gate.",
        "scopes": ["public"],
        "tags": ["troubleshooting", "leadership", "login", "supervisor", "portal"],
        "body": [
            # iter317-B · two-doors guidance at the top so users
            # don't troubleshoot the wrong door for ten minutes.
            {"type": "p", "text":
                "There are two Field Leadership doors and they need "
                "different things at sign-in. Figure out which one "
                "you're at, then follow the matching checklist."},
            {"type": "tip", "text":
                "Which door am I at? If the form asks for an EMAIL "
                "and a password, you're at the per-user portal "
                "(/field-leadership/portal/login). If it asks for "
                "only a password, you're at the legacy shared-"
                "password gate (/field-leadership/login)."},
            {"type": "p", "text":
                "Per-user Portal — /field-leadership/portal/login "
                "(your company email + your individual password):"},
            {"type": "steps", "items": [
                "Confirm you're at /field-leadership/portal/login (not /field-leadership/login).",
                "Use the company email HR or Admin issued you — not a coworker's, not a personal email.",
                "If you were issued a temporary password and never signed in, the portal will force you to change it on first sign-in.",
                "Forgot the password? Use the Forgot Password link on the login page, or ask HR/Admin to reset it. The reset issues a fresh temporary password and invalidates the old one immediately.",
                "Still rejected? Ask HR/Admin to confirm your account is active. Deactivated accounts cannot sign in.",
            ]},
            {"type": "p", "text":
                "Legacy Shared-Password Gate — /field-leadership/login "
                "(crew-wide password for read-only crew documents only):"},
            {"type": "steps", "items": [
                "Confirm you're at /field-leadership/login (the shared-password door).",
                "Verify spelling and caps-lock state — the shared password is case-sensitive.",
                "If you already have an Admin or PM token (you've signed in to /admin/login or /pm/login earlier in this session), the legacy gate accepts those automatically.",
                "Close the browser tab and reopen if a previous token is interfering.",
                "Ask your direct supervisor or the office for the current shared password if it has been rotated.",
            ]},
            {"type": "why", "text":
                "Both doors exist on purpose. The per-user portal "
                "carries operational accountability — every action "
                "is signed in your name. The shared-password gate "
                "exists for crew read-only document access where "
                "individual identity isn't needed. Most "
                "operational work belongs at the per-user door."},
            {"type": "warn", "text":
                "Do NOT type the shared crew password into the "
                "per-user portal (or vice versa). Wrong door + "
                "wrong password is what causes most repeat sign-in "
                "failures. Look at the form first; if it asks for "
                "an email, you need your per-user credentials."},
            {"type": "tip", "text":
                "Once you sign in successfully at either door, "
                "your browser holds a session token. You don't need "
                "to re-enter credentials again that same shift "
                "unless you close the tab or the session expires."},
        ],
        "related": [
            "onboard-leadership-first-week",
            "portal-leadership-identity",
            "portal-field-leadership-portal-accounts",
            "tshoot-session-timeout",
            "public-cant-login",
        ],
    },
    {
        "id": "portal-leadership-identity",
        "section": "portals",
        "title": "Field Leadership Portal — Overview",
        "summary": "What Field Leadership is for, who uses it, and which of the two doors to use.",
        "scopes": ["public"],
        "tags": ["leadership", "identity", "portal", "supervisor"],
        "body": [
            {"type": "p", "text":
                "The Field Leadership Portal is the daily-operations surface for Superintendents, "
                "Foremen, Field Leaders, and Operations Oversight — the people running crews on "
                "the ground."},
            {"type": "p", "text":
                "Who uses it: Superintendents, Foremen, Truck Bosses, Working Supervisors, "
                "Field Supervisors. Operations Oversight (HR/Admin) issues and manages the "
                "accounts but works inside their own portals."},
            # iter317-B · disambiguate the two doors at the top of
            # the overview. The per-user portal is the operational
            # door; the shared-password gate is a read-only crew
            # document surface.
            {"type": "tip", "text":
                "Which door do I use? Two valid doors exist. "
                "(1) /field-leadership/portal/login — per-user "
                "accounts (your company email + individual "
                "password). This is the operational door; "
                "everything you submit is signed in your name. "
                "(2) /field-leadership/login — legacy shared-"
                "password gate for read-only crew documents. Both "
                "work; they do different jobs."},
            {"type": "p", "text":
                "How to get a per-user account: HR or Admin issues "
                "Field Leadership Portal accounts. You receive a "
                "company email account and a temporary password; "
                "the portal forces you to change it on first sign-"
                "in. After that, your email and your individual "
                "password sign you in."},
            {"type": "warn", "text":
                "Operational Field Leadership training (procedures, workflows, internal SOPs) "
                "is restricted to authenticated leadership users. Workflow-level content is "
                "not visible to anonymous users."},
            {"type": "next", "items": [
                "Read 'Field Leadership Portal Accounts' for the full per-user identity walkthrough",
                "If you can't sign in — read 'Can't sign in to Field Leadership' (public)",
            ]},
        ],
        "related": [
            "onboard-leadership-first-week",
            "portal-field-leadership-portal-accounts",
            "tshoot-leadership-login",
            "public-cant-login",
        ],
    },

    # ── iter317-B · NEW per-user FL Portal accounts article ──────────
    # Operational disambiguation deliverable for iter317-B. Public
    # scope (readable BEFORE login) so a Super/Foreman who doesn't
    # yet know which door to use can find this answer first.
    {
        "id": "portal-field-leadership-portal-accounts",
        "section": "portals",
        "title": "Field Leadership Portal Accounts (per-user)",
        "summary": "Per-user Field Leadership Portal accounts — what they are, who issues them, and when the legacy shared-password gate still applies.",
        "scopes": ["public"],
        "tags": ["leadership", "identity", "portal", "accounts", "per-user", "fl portal"],
        "body": [
            {"type": "p", "text":
                "A Field Leadership Portal account is your individual "
                "operational identity inside MASCI. It is a company "
                "email + an individual password — not a shared crew "
                "code. Every Daily Report, write-up, equipment "
                "sign-out, and crew evaluation you submit is signed "
                "in your name in the audit trail."},
            {"type": "tip", "text":
                "Which door do I use? Two valid doors exist. The "
                "per-user portal at /field-leadership/portal/login "
                "is the operational door — your day-to-day "
                "workflows live there. The legacy shared-password "
                "gate at /field-leadership/login still exists for "
                "read-only crew documents; it does not unlock "
                "operational workflows. Most leadership work "
                "happens at the per-user door."},
            {"type": "p", "text":
                "Who issues accounts: HR or Admin. They create your "
                "account, set a temporary password, and hand the "
                "temporary password to you through the channel HR "
                "uses for credentials. The portal forces you to "
                "change the temporary password the first time you "
                "sign in — that is the handoff from 'issued' to "
                "'in use'."},
            {"type": "p", "text":
                "Who gets accounts: Superintendents, Foremen, Truck "
                "Bosses, Working Supervisors, Field Supervisors. "
                "Accounts are issued to people who actually need "
                "them — not 'just in case' accounts, not training "
                "accounts that never get cleaned up."},
            {"type": "p", "text":
                "Password resets: HR or Admin resets the password "
                "if you forget it, or you can use the Forgot "
                "Password link on the login page. Either path "
                "issues a fresh temporary password and invalidates "
                "the prior password immediately. Old sessions die "
                "at the same moment."},
            {"type": "why", "text":
                "Per-user accounts exist because operational "
                "actions need operational accountability. A signed "
                "Daily Report carries your name into payroll and "
                "Safety review; a write-up carries your name into "
                "the employee record HR keeps. A shared crew "
                "password cannot deliver that — everyone signed in "
                "looks the same. The per-user portal is how the "
                "platform connects what happens in the field to "
                "who actually did it."},
            {"type": "warn", "text":
                "Your password is yours — not the crew's. Don't "
                "text it to a foreman, write it on a clipboard, or "
                "share it 'just so they can pull a report.' Every "
                "action signed under your name is yours "
                "operationally — including the ones you didn't "
                "actually do because someone borrowed your login. "
                "If a teammate needs access, that's an HR/Admin "
                "account-issuance conversation."},
            {"type": "p", "text":
                "When does the legacy shared-password gate still "
                "apply? Read-only crew document access at "
                "/field-leadership/login — drawings, plan sets, "
                "and similar documents the whole crew needs to "
                "see. The shared gate does NOT unlock Daily "
                "Reports, write-ups, equipment checkout, "
                "evaluations, or any other per-user workflow. Both "
                "doors are intentional; they do different jobs."},
            {"type": "next", "items": [
                "Don't have an account yet? Ask HR or Admin — they issue Field Leadership Portal accounts.",
                "Got a temporary password? Sign in at /field-leadership/portal/login and change it on first sign-in.",
                "Can't sign in? Read 'Can't sign in to Field Leadership' (public).",
                "Already in? Read 'Field Leadership — First Week' for the operational rhythm.",
                "Not sure which door you should be using? Ask HR or Admin. The answer is fast (usually 'whichever account we set you up with'). Don't bounce between the two doors troubleshooting on your own.",
            ]},
        ],
        "related": [
            "onboard-leadership-first-week",
            "portal-leadership-identity",
            "tshoot-leadership-login",
            "portal-leadership",
            "role-superintendent",
            "role-foreman",
        ],
    },



    # ═════════════════════════════════════════════════════════════════
    # iter317-C · Driver Qualification operational articles. Five
    # bounded articles covering the operational distinctions Dispatch,
    # Safety, HR, and Shop have been holding in tribal knowledge:
    #   driver-cdl-vs-approved-company-driver
    #   driver-medical-card-and-expirations
    #   driver-tanker-and-endorsements
    #   driver-qualification-dashboard-understanding
    #   driver-restrictions-and-escalation
    # Scoped to hr+safety+dispatch+admin (the readers who actually use
    # the dashboard daily). Bilingual parity in translations_es.py.
    # ═════════════════════════════════════════════════════════════════

    {
        "id": "driver-cdl-vs-approved-company-driver",
        "section": "trucking",
        "title": "CDL Holder vs Approved Company Driver",
        "summary": "Why MASCI tracks the two flags separately and why a CDL alone does not put a driver behind the wheel of a MASCI truck.",
        "scopes": ["hr", "safety", "dispatch", "admin"],
        "tags": ["driver-qualification", "cdl", "insurance", "dispatch"],
        "body": [
            {"type": "p", "text":
                "Two flags. Two separate decisions. CDL Holder "
                "means the state has licensed the driver to operate "
                "a commercial vehicle in that license class. "
                "Approved Company Driver means MASCI's insurance "
                "roster, MVR review, medical card scan, drug screen "
                "results, and supervisor sign-off are all on file "
                "and the driver is cleared to operate a MASCI "
                "truck. The two answers almost never land on the "
                "same day."},
            {"type": "why", "text":
                "Conflating them is the most common dispatch error "
                "in this space. 'He has a CDL' is not the same as "
                "'he can drive today.' The dashboard surfaces them "
                "as separate columns so the answer is unambiguous "
                "before the truck moves."},
            {"type": "bullets", "items": [
                "CDL Holder — state-issued license, class + endorsements + restrictions on file",
                "Approved Company Driver — MASCI runway complete (insurance · MVR · medical · drug screen · supervisor)",
                "Driver Status — operational rollup (Active · Pending · Suspended · Off-roster)",
                "Tanker-Capable filter — separate operational filter for dewatering hauls",
            ]},
            {"type": "tip", "text":
                "When a CDL holder is sitting at not-yet-approved, "
                "the runway is usually missing one piece. Pull the "
                "drawer; the missing field is right there."},
            {"type": "warn", "text":
                "Never assign a load on CDL alone. The CDL "
                "satisfies state law. The approved-driver flag "
                "satisfies MASCI's insurance and process. Both "
                "have to be green before dispatch."},
            {"type": "next", "items": [
                "Read 'Medical Card Cadence and Expirations' — the date that lapses most quietly",
                "Read 'Driver Restrictions and Escalation' — when state-licensing limits change dispatch options",
            ]},
        ],
        "related": [
            "driver-medical-card-and-expirations",
            "driver-restrictions-and-escalation",
            "driver-qualification-dashboard-understanding",
        ],
    },

    {
        "id": "driver-medical-card-and-expirations",
        "section": "trucking",
        "title": "Medical Card Cadence and Expirations",
        "summary": "Medical card lapse means the driver does not operate a CMV that day. How the dashboard surfaces the date and how Safety, HR, and Dispatch escalate when it slips.",
        "scopes": ["hr", "safety", "dispatch", "admin"],
        "tags": ["driver-qualification", "medical-card", "expirations", "fmcsa"],
        "body": [
            {"type": "p", "text":
                "The DOT medical card (FMCSA 391.45) runs on its "
                "own clock — typically 24 months, sometimes shorter "
                "if the examiner flagged a condition. It is NOT "
                "tied to CDL expiration. A driver can have three "
                "years of CDL runway and a medical card that "
                "lapses tomorrow. The day the card lapses, that "
                "driver legally cannot operate a CMV in interstate "
                "commerce."},
            {"type": "why", "text":
                "The two dates almost never line up. Treating "
                "medical-card and CDL as one renewal window is the "
                "single most common way a card lapses silently. "
                "The dashboard shows them in two separate columns "
                "for that reason."},
            {"type": "tip", "text":
                "Use the 60-day expiration view, not the day-of-"
                "dispatch view. Most renewals take 1–2 weeks once "
                "the DOT exam is scheduled — and getting the exam "
                "scheduled takes its own time."},
            {"type": "warn", "text":
                "Card lapsed = driver does not run a CMV that "
                "day. Notify Safety + HR + Dispatch the same "
                "shift. Renewal path is a DOT-certified medical "
                "examiner, exam current, certificate on file with "
                "MASCI. Until all three are true, the driver runs "
                "supporting work only — this is not a one-day "
                "exception field."},
            {"type": "next", "items": [
                "If the card has already lapsed: pull the driver from the route, get the DOT exam scheduled, document the conversation.",
                "If 30 days out: pre-schedule the exam now — renewals take time.",
                "Read 'CDL Holder vs Approved Company Driver' for how the medical card fits the broader approval runway.",
            ]},
        ],
        "related": [
            "driver-cdl-vs-approved-company-driver",
            "driver-qualification-dashboard-understanding",
            "driver-restrictions-and-escalation",
        ],
    },

    {
        "id": "driver-tanker-and-endorsements",
        "section": "trucking",
        "title": "Tanker Endorsement and Endorsement Codes at MASCI",
        "summary": "Why the tanker (N) endorsement matters for MASCI dewatering work, and how X / H combinations open the routes the basic CDL cannot.",
        "scopes": ["hr", "safety", "dispatch", "admin"],
        "tags": ["driver-qualification", "endorsements", "tanker", "hazmat", "dewatering"],
        "body": [
            {"type": "p", "text":
                "MASCI dewatering work moves real volumes of "
                "liquid. The tanker endorsement (N) is not a "
                "paperwork checkbox — it covers the physics of "
                "hauling a partially-loaded liquid trailer: "
                "surge, rollover risk on a curve, brake fade on "
                "a downgrade. Drivers without N do not run "
                "dewatering loads. Period."},
            {"type": "bullets", "items": [
                "N — Tanker. Required for any liquid-bulk haul above the threshold; central to MASCI dewatering routes.",
                "H — Hazmat. Required for placarded hazardous cargo. Carries its own TSA background check.",
                "X — Tanker AND Hazmat combined. Required when liquid hazmat moves on a tanker — the only single endorsement that satisfies the inspection.",
                "T — Double/Triple trailers. Specific equipment use, less common at MASCI.",
                "P — Passenger. Rarely applicable to MASCI work.",
                "S — School bus. Not applicable.",
            ]},
            {"type": "tip", "text":
                "When dispatch is matching a driver to a liquid "
                "hazmat load (vac trucks pulling contaminated "
                "water is the common case), look at the "
                "endorsements column. The answer is either X is "
                "present or the load goes to a different driver."},
            {"type": "why", "text":
                "The dashboard surfaces tanker-capable drivers as "
                "a separate filter because that filter actually "
                "matters for assignment. 'He has a CDL' is not "
                "enough; 'he has N' is the operational answer for "
                "dewatering."},
            {"type": "next", "items": [
                "Read 'Driver Restrictions and Escalation' — restrictions can disqualify drivers even when endorsements look right",
                "Read 'CDL Holder vs Approved Company Driver' — endorsements live inside the CDL; approval is a separate runway",
            ]},
        ],
        "related": [
            "driver-cdl-vs-approved-company-driver",
            "driver-restrictions-and-escalation",
            "driver-qualification-dashboard-understanding",
        ],
    },

    {
        "id": "driver-qualification-dashboard-understanding",
        "section": "trucking",
        "title": "Reading the Driver Qualification Dashboard",
        "summary": "What each column on the Driver Qualification dashboard means, when to act on it, and what it deliberately does not do.",
        "scopes": ["hr", "safety", "dispatch", "admin"],
        "tags": ["driver-qualification", "dashboard", "interpretation"],
        "body": [
            {"type": "p", "text":
                "The Driver Qualification dashboard is the "
                "operational rollup of every driver-relevant field "
                "on the employee record — CDL holder, approved "
                "company driver, driver status, CDL expiration, "
                "medical card expiration, endorsements, "
                "restrictions, tanker-capable. It is the surface "
                "Dispatch, Safety, and HR look at before a load "
                "moves."},
            {"type": "bullets", "items": [
                "Name + Employee ID — sortable, searchable",
                "CDL Holder — yes/no flag from the employee record",
                "Approved Company Driver — yes/no flag, separate from CDL",
                "Driver Status — operational rollup (Active · Pending · Suspended · Off-roster)",
                "CDL Expiration — state CDL renewal date",
                "Medical Card Expiration — FMCSA 391.45 cadence, INDEPENDENT of CDL",
                "Endorsements — N · H · X · T · P · S codes on the CDL",
                "Restrictions — L · E · Z codes on the CDL that limit equipment",
            ]},
            {"type": "tip", "text":
                "Filter views — use the 30 / 60 / 90 day "
                "expiration filters to plan ahead. Use the "
                "tanker-capable filter when matching dewatering "
                "loads. The dashboard is a planning surface, not "
                "a dispatch-day refusal surface."},
            {"type": "warn", "text":
                "What this dashboard is NOT. It is not a dispatch "
                "system. It does not assign loads. It does not "
                "auto-revoke approved-driver status when something "
                "expires — that decision stays human on purpose. "
                "It does not enforce qualification at the moment "
                "of assignment. Building any of those would mean "
                "MASCI now owns a trucking-management product, "
                "which is exactly what we said no to."},
            {"type": "next", "items": [
                "Export Current View — pull the filtered list as CSV for offline review",
                "Read each column's deep article: CDL vs Approved · Medical Card · Tanker · Restrictions",
            ]},
        ],
        "related": [
            "driver-cdl-vs-approved-company-driver",
            "driver-medical-card-and-expirations",
            "driver-tanker-and-endorsements",
            "driver-restrictions-and-escalation",
        ],
    },

    {
        "id": "driver-restrictions-and-escalation",
        "section": "trucking",
        "title": "Driver Restrictions and Escalation",
        "summary": "What CDL restriction codes mean for MASCI dispatch and how Safety + HR handle a driver who shows up to operate equipment their CDL restricts.",
        "scopes": ["hr", "safety", "dispatch", "admin"],
        "tags": ["driver-qualification", "restrictions", "escalation", "safety-stop"],
        "body": [
            {"type": "p", "text":
                "CDL restriction codes are state-licensing "
                "decisions — written onto the CDL because the "
                "driver demonstrated proficiency on a narrower "
                "class of equipment than the full class allows. "
                "MASCI does not override them with a willing-"
                "supervisor signature; they are not optional "
                "information."},
            {"type": "bullets", "items": [
                "L — No air brake equipped CMV (the most operationally consequential at MASCI; most heavy fleet has air brakes)",
                "E — No manual transmission (eliminates stick-shift assignments)",
                "Z — No full air brake system (similar operational impact to L; treat the same)",
                "K — Intrastate only (cannot cross state lines)",
                "M — No Class A passenger vehicle",
                "N — No Class A or B passenger vehicle",
                "O — No tractor-trailer",
            ]},
            {"type": "tip", "text":
                "Dispatch reads the restrictions column before "
                "assigning. It is the same workflow as reading "
                "endorsements — the column tells you what the "
                "driver can and cannot legally operate, not what "
                "the office wishes they could."},
            {"type": "warn", "text":
                "If a driver shows up to operate equipment their "
                "CDL restricts, that's a Safety stop — not a "
                "dispatch reroute. Pull them off the truck, "
                "document the mismatch, bring it to HR/Safety the "
                "same day. Two paths forward: (1) the driver gets "
                "the restriction removed at the DMV, (2) dispatch "
                "matches them to a truck they're actually "
                "licensed for. Workarounds are not a third path."},
            {"type": "next", "items": [
                "Read 'CDL Holder vs Approved Company Driver' — restrictions ride inside the CDL; approval is separate",
                "Read 'Tanker Endorsement' — endorsements + restrictions together define the equipment match",
            ]},
        ],
        "related": [
            "driver-cdl-vs-approved-company-driver",
            "driver-tanker-and-endorsements",
            "driver-qualification-dashboard-understanding",
            "driver-medical-card-and-expirations",
        ],
    },



    # ═════════════════════════════════════════════════════════════════
    # PASS 5a · HR + SAFETY + PM ONBOARDING + LOGIN TROUBLESHOOTING
    # ─────────────────────────────────────────────────────────────────
    # Public-scope, mirrors leadership pattern from Pass 4. These are
    # FIRST-WEEK orientation + LOGIN recovery articles — not workflow
    # SOPs. Anyone needing operational workflow depth signs in to the
    # matching portal-scoped article (Tier 2).
    # ═════════════════════════════════════════════════════════════════

    # ── HR — onboarding + login-troubleshoot ─────────────────────────
    {
        "id": "onboard-hr-first-week",
        "section": "onboarding",
        "title": "HR Staff — First Week",
        "summary": "What a new HR staffer or HR manager does in their first week at MASCI.",
        "scopes": ["public"],
        "tags": ["hr", "onboarding", "first week", "new staff"],
        "body": [
            {"type": "p", "text":
                "Welcome to HR. The HR portal is people-and-time at MASCI. Your first week is "
                "mostly setup, shadowing, and reading — not solo work. Take the time. HR records "
                "are referenced by payroll, audits, and project reviews for years."},
            {"type": "steps", "items": [
                "Day 1 — Receive your HR credentials from an admin. Sign in at /hr/login and complete your forced password change.",
                "Day 1 — Read the public Guidance Center landing once, end to end (15 minutes). You'll see what every portal does.",
                "Day 2 — Sit with your HR Manager for an hour. Ask them to walk you through their inbox: what arrives daily, what arrives weekly, what's seasonal.",
                "Day 2-3 — Shadow one full time-verification cycle with your manager before doing one yourself. The cadence matters more than the screen.",
                "Day 3-4 — Shadow one full new-hire onboarding, paperwork to first-day. Take notes on what feels slow — that's where mistakes happen.",
                "Day 4-5 — Read the deep HR training articles once. They're long on purpose; skim, bookmark, return when needed.",
                "End of week 1 — Make a list of every question you didn't ask yet. Ask them. HR is forgiving of 'too many questions early' — much less forgiving of 'pretended to know'.",
            ]},
            {"type": "why", "text":
                "HR records flow into payroll the same week they're created. A first-week "
                "mistake on a time entry is corrected with a 30-second conversation; the same "
                "mistake discovered three months later requires a paycheck adjustment, an audit "
                "note, and a difficult conversation. Mistakes are cheap in week one. They get "
                "expensive fast."},
            {"type": "tip", "text":
                "Keep a notebook (paper or app) for the first month. Write down every term, "
                "every acronym, every workflow you encounter. Re-read it weekly. By week four "
                "you'll have authored your own private HR cheatsheet — and that's worth more "
                "than any document we could write for you."},
            {"type": "next", "items": [
                "By week 2 you should be doing time-verification independently with manager spot-checks",
                "By week 4 you should own one onboarding cycle end-to-end",
                "Bookmark 'Can't sign in?' (public) — you'll need to point new staff at it",
            ]},
        ],
        "related": [
            "portal-hr-identity",
            "tshoot-hr-login",
            "public-cant-login",
        ],
    },
    {
        "id": "tshoot-hr-login",
        "section": "troubleshooting",
        "title": "Can't sign in to HR",
        "summary": "Quick fixes when /hr/login isn't working.",
        "scopes": ["public"],
        "tags": ["hr", "login", "troubleshooting", "password"],
        "body": [
            {"type": "p", "text":
                "HR uses per-user email + password. If you can't get in, walk through these in order."},
            {"type": "steps", "items": [
                "Confirm you're at /hr/login (NOT /admin/login, NOT /pm/login — those expect different accounts and will lock you out after several attempts).",
                "Check caps lock and your spelling. Passwords are case-sensitive.",
                "If this is your first login, use the temporary password an admin gave you. You'll be forced to change it.",
                "If you forgot your password, click 'Forgot password?' on /hr/login. You'll receive a reset link by email — single-use, 30-minute expiry.",
                "If the reset email never arrives, check spam. If it's still missing after 10 minutes, the email on file may be wrong — contact your admin.",
                "If you see 'account disabled', an admin has locked your account. Contact your operator.",
            ]},
            {"type": "why", "text":
                "HR is its own isolated scope — admin tokens do NOT satisfy HR endpoints. That's "
                "intentional: HR's records (personnel, payroll variance, write-ups) are "
                "sensitive enough that 'admin can see everything' is not the right posture for "
                "HR reads. Each HR user has their own audit trail."},
            {"type": "warn", "text":
                "Do NOT type your HR password into any other portal's login form (Safety, PM, "
                "Shop, Dispatch, Admin). Each portal has its own login. Pasting the wrong "
                "password elsewhere can temporarily lock that account after a few attempts."},
            {"type": "tip", "text":
                "If you're locked out after multiple bad attempts, wait 15 minutes — the "
                "lockout is per-IP and self-clears. Or contact your operator to clear it sooner."},
        ],
        "related": [
            "portal-hr-identity",
            "onboard-hr-first-week",
            "public-cant-login",
        ],
    },

    # ── Safety — onboarding + login-troubleshoot ─────────────────────
    {
        "id": "onboard-safety-first-week",
        "section": "onboarding",
        "title": "Safety Staff — First Week",
        "summary": "What a new Safety Manager, Coordinator, or Officer does in their first week.",
        "scopes": ["public"],
        "tags": ["safety", "onboarding", "first week", "new staff"],
        "body": [
            {"type": "p", "text":
                "Welcome to Safety. The Safety portal is how MASCI proves compliance, documents "
                "incidents, and defends operations during an OSHA visit. Your first week is "
                "mostly site visits, shadowing, and reading. The depth matters more than the speed."},
            {"type": "steps", "items": [
                "Day 1 — Receive your Safety credentials from an admin. Sign in at /safety-portal/login and complete your forced password change.",
                "Day 1 — Walk one active jobsite with a current Safety staffer. Don't take notes for compliance yet — just observe what they observe.",
                "Day 2 — Sit with your manager and review the last 30 days of incidents, near-misses, and corrective actions. Patterns matter more than individual events.",
                "Day 2-3 — Shadow one full incident from report → investigation → corrective action → close. Don't lead it. Watch the cadence.",
                "Day 3-4 — Read the deep Safety training articles once. Bookmark them. They're authored to be re-read every quarter.",
                "Day 4-5 — Lead one Safety Meeting under your manager's supervision. Get comfortable with the rhythm of running a meeting.",
                "End of week 1 — Identify the one project that worries you most. That's where your attention belongs in week 2.",
            ]},
            {"type": "why", "text":
                "Safety is the portal that gets cited most often in disputes — OSHA visits, "
                "insurance claims, after-action reviews. First-week mistakes are forgiven; "
                "the goal is to build the muscle memory of 'document specifically, close "
                "completely, follow up always' before you're operating alone."},
            {"type": "tip", "text":
                "Field crews respond to safety staff who LISTEN before correcting. Spend your "
                "first week asking 'what's been frustrating you?' instead of 'are you following "
                "the procedure?'. The trust you build early multiplies for years."},
            {"type": "next", "items": [
                "By week 2 you should be authoring routine incident reports independently",
                "By week 4 you should own one project's safety oversight end-to-end",
                "Bookmark 'If something happens on a job site' (public) — that's the field-side surface you'll be supporting",
            ]},
        ],
        "related": [
            "portal-safety-identity",
            "tshoot-safety-login",
            "public-incident-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "tshoot-safety-login",
        "section": "troubleshooting",
        "title": "Can't sign in to Safety",
        "summary": "Quick fixes when /safety-portal/login isn't working.",
        "scopes": ["public"],
        "tags": ["safety", "login", "troubleshooting", "password"],
        "body": [
            {"type": "p", "text":
                "Safety uses per-user email + password. If you can't get in, walk through these in order."},
            {"type": "steps", "items": [
                "Confirm you're at /safety-portal/login (NOT /admin/login or any other portal door).",
                "Check caps lock and spelling. Passwords are case-sensitive.",
                "If this is your first login, use the temporary password an admin gave you. You'll be forced to change it.",
                "Use 'Forgot password?' for a reset link by email (single-use, 30-minute expiry).",
                "Check spam if the reset email doesn't arrive. If it's still missing, your operator may have the wrong email on file.",
                "If you see 'account disabled', contact your operator.",
            ]},
            {"type": "why", "text":
                "Safety is its own isolated scope. Admin tokens do NOT satisfy Safety endpoints "
                "automatically — that's intentional, because Safety records are referenced "
                "during OSHA conversations and need a clean audit trail of 'who read what when'."},
            {"type": "warn", "text":
                "Do NOT type your Safety password into another portal's login form. Each portal "
                "has its own login. Repeated bad attempts on the wrong portal can lock that "
                "account temporarily."},
            {"type": "tip", "text":
                "If you're locked out, wait 15 minutes — the lockout self-clears — or contact "
                "your operator. Safety lockouts are rare; if it happens twice in a week, the "
                "issue is probably the wrong login URL, not the password."},
        ],
        "related": [
            "portal-safety-identity",
            "onboard-safety-first-week",
            "public-cant-login",
        ],
    },

    # ── PM — onboarding + login-troubleshoot ─────────────────────────
    {
        "id": "onboard-pm-first-week",
        "section": "onboarding",
        "title": "PM — First Week",
        "summary": "What a new Project Manager or Co-PM does in their first week at MASCI.",
        "scopes": ["public"],
        "tags": ["pm", "onboarding", "first week", "project manager"],
        "body": [
            {"type": "p", "text":
                "Welcome to PM. The PM portal is the project-level lens at MASCI. Your first "
                "week is mostly listening, reading the project history, and building rapport "
                "with the field. PMs who try to start by changing things in week one almost "
                "always regret it."},
            {"type": "steps", "items": [
                "Day 1 — Receive your PM credentials from an admin. Sign in at /pm/login and complete your forced password change.",
                "Day 1 — Read every project you'll be assigned. Last 30 days of Daily Reports, last 90 days of incidents, last quarter's labor totals. Don't act yet. Just read.",
                "Day 2 — Visit at least one active jobsite for each project you're assigned. Meet the foreman in person. They are your most important relationship.",
                "Day 2-3 — Sit with your outgoing PM (if there is one) for a half-day handoff. Ask: 'What's brittle here? What did the last PM not write down?'",
                "Day 3-4 — Walk one weekly review cycle with another PM. Don't lead it — just watch what they look at and in what order.",
                "Day 4-5 — Read the deep PM training articles once. They're long; skim and bookmark.",
                "End of week 1 — Identify the one project that needs the most attention. Schedule a site visit for week 2.",
            ]},
            {"type": "why", "text":
                "PMs are the bridge between field operations and project finance. The first "
                "week's job isn't to demonstrate command — it's to build a clear mental model "
                "of where the field is, what's working, and what the previous PM was nervous "
                "about. That model is what every later decision depends on."},
            {"type": "tip", "text":
                "Send a short note to each foreman in your first week: 'I'm your new PM, my "
                "phone is X, my email is Y, call me before noon for fastest reply.' Most "
                "communication friction in PM work comes from the field not knowing how to "
                "reach you. Close that gap on day three."},
            {"type": "next", "items": [
                "By week 2 you should be running weekly project reviews independently",
                "By week 4 you should be reconciling labor and answering owner questions on your own",
                "Bookmark 'Daily Report Basics' (public) — that's the field-side surface feeding your dashboard",
            ]},
        ],
        "related": [
            "portal-pm-identity",
            "tshoot-pm-login",
            "public-daily-report-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "tshoot-pm-login",
        "section": "troubleshooting",
        "title": "Can't sign in to PM",
        "summary": "Quick fixes when /pm/login isn't working.",
        "scopes": ["public"],
        "tags": ["pm", "login", "troubleshooting", "password"],
        "body": [
            {"type": "p", "text":
                "PM uses per-user email + password. Each PM has their own account scoped to "
                "the projects they manage. If you can't get in, walk through these in order."},
            {"type": "steps", "items": [
                "Confirm you're at /pm/login (NOT /admin/login or any other portal door).",
                "Check caps lock and spelling. Passwords are case-sensitive.",
                "If this is your first login, use the temporary password an admin gave you. You'll be forced to change it.",
                "Use 'Forgot password?' for a reset link by email (single-use, 30-minute expiry).",
                "Check spam if the reset email doesn't arrive. If it's still missing, your operator may have the wrong email on file.",
                "If you see 'account disabled' or 'locked', contact your operator.",
            ]},
            {"type": "why", "text":
                "PM scope is project-based, not portal-based. Each PM signs in with their own "
                "account so the audit log can attribute every action to the right person. "
                "Sharing PM credentials defeats the audit trail and makes disputes harder to "
                "resolve later."},
            {"type": "warn", "text":
                "Do NOT use another PM's credentials, even temporarily. The audit log will "
                "attribute every action to them — including any approval, edit, or close-out "
                "you perform. If you need cross-PM access, ask your operator for proper "
                "delegation."},
            {"type": "tip", "text":
                "PM lockouts auto-clear after 15 minutes. If you're locked out twice in a "
                "week, the issue is almost always the wrong portal door, not the password."},
        ],
        "related": [
            "portal-pm-identity",
            "onboard-pm-first-week",
            "public-cant-login",
        ],
    },

    # ── Shop — onboarding + login-troubleshoot ───────────────────────
    {
        "id": "onboard-shop-first-week",
        "section": "onboarding",
        "title": "Shop / Fleet Staff — First Week",
        "summary": "What a new Mechanic, Shop Foreman, or Fleet Coordinator does in their first week.",
        "scopes": ["public"],
        "tags": ["shop", "fleet", "onboarding", "first week", "new staff"],
        "body": [
            {"type": "p", "text":
                "Welcome to Shop. The Shop / Fleet portal is how MASCI keeps equipment "
                "operational and documented. Your first week is mostly hands-on time in the "
                "yard, shadowing the people who already do the work, and learning the rhythm "
                "of how the field talks to the shop."},
            {"type": "steps", "items": [
                "Day 1 — Receive your Shop credentials from an admin. Sign in at /shop/login and complete your forced password change.",
                "Day 1 — Walk the yard with the Shop Foreman. Touch every active piece of equipment. The platform names mean nothing until you've put hands on the actual unit.",
                "Day 2 — Sit with the Fleet Coordinator for an hour. Ask them to walk you through their day: what arrives first thing, what's mid-day, what's end-of-day reconciliation.",
                "Day 2-3 — Shadow one full Pre-Op review cycle from incoming submission to follow-up call with the field. Don't act yet — watch the cadence.",
                "Day 3-4 — Shadow one full damage triage from field report to repair-sign-off. Note where the field operator was wrong, where they were right, and how the conversation went.",
                "Day 4-5 — Read the deep Shop training articles once. Bookmark them; they're built to be re-read every quarter.",
                "End of week 1 — Identify the one piece of equipment everyone in the yard worries about. That's where your attention belongs in week 2.",
            ]},
            {"type": "why", "text":
                "Shop sits at the intersection of safety, money, and field morale. A unit "
                "released too early causes an incident; a unit held too long stalls a "
                "project. The shop's documentation is the only thing that proves which call "
                "was made and why. First-week mistakes are expected — first-week shortcuts "
                "in documentation are not."},
            {"type": "tip", "text":
                "Field operators trust mechanics who LISTEN. Spend your first week asking "
                "operators 'what's been giving you trouble?' instead of telling them their "
                "Pre-Op was wrong. The trust you build early shows up as honest damage "
                "reports for years."},
            {"type": "next", "items": [
                "By week 2 you should be reviewing routine Pre-Ops independently",
                "By week 4 you should own one equipment-return joint sign-off with Safety",
                "Bookmark 'Equipment Pre-Op Checks (Field Basics)' (public) — that's the field-side surface you'll be supporting",
            ]},
        ],
        "related": [
            "portal-shop-identity",
            "tshoot-shop-login",
            "public-preop-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "tshoot-shop-login",
        "section": "troubleshooting",
        "title": "Can't sign in to Shop",
        "summary": "Quick fixes when /shop/login isn't working.",
        "scopes": ["public"],
        "tags": ["shop", "fleet", "login", "troubleshooting", "password"],
        "body": [
            {"type": "p", "text":
                "Shop uses per-user email + password. If you can't get in, walk through these in order."},
            {"type": "steps", "items": [
                "Confirm you're at /shop/login (NOT /admin/login or any other portal door).",
                "Check caps lock and spelling. Passwords are case-sensitive.",
                "If this is your first login, use the temporary password an admin gave you. You'll be forced to change it.",
                "Use 'Forgot password?' for a reset link by email (single-use, 30-minute expiry).",
                "Check spam if the reset email doesn't arrive. If it's still missing, your operator may have the wrong email on file.",
                "If you see 'account disabled' or 'locked', contact your operator.",
            ]},
            {"type": "why", "text":
                "Shop is its own isolated scope. Admin tokens do NOT satisfy Shop endpoints "
                "automatically — that's intentional, because shop sign-offs are referenced "
                "during insurance disputes and need a clean per-user audit trail."},
            {"type": "warn", "text":
                "Do NOT type your Shop password into another portal's login form (Safety, HR, "
                "PM, Dispatch, Admin). Each portal has its own login. Repeated bad attempts "
                "on the wrong portal can temporarily lock that account."},
            {"type": "tip", "text":
                "If you're locked out, wait 15 minutes — the lockout self-clears — or "
                "contact your operator. Shop lockouts usually mean the wrong login URL, not "
                "the wrong password. Bookmark /shop/login on day one to avoid the issue."},
        ],
        "related": [
            "portal-shop-identity",
            "onboard-shop-first-week",
            "public-cant-login",
        ],
    },

    # ── Dispatch — onboarding + login-troubleshoot ───────────────────
    {
        "id": "onboard-dispatch-first-week",
        "section": "onboarding",
        "title": "Dispatch Staff — First Week",
        "summary": "What a new Dispatcher, Fleet Coordinator, or Operations Oversight staffer does in their first week.",
        "scopes": ["public"],
        "tags": ["dispatch", "onboarding", "first week", "new staff"],
        "body": [
            {"type": "p", "text":
                "Welcome to Dispatch. The Dispatch portal is how MASCI coordinates equipment "
                "across active projects. Your first week is mostly listening, mapping mental "
                "models to physical units, and learning the rhythm of how the field, the shop, "
                "and the office disagree about where equipment is."},
            {"type": "steps", "items": [
                "Day 1 — Receive your Dispatch credentials from an admin. Sign in at /dispatch-portal/login and complete your forced password change.",
                "Day 1 — Sit beside the current dispatcher for the morning push. Don't speak. Just watch how they decide which call to take first.",
                "Day 2 — Visit at least two active jobsites. See the equipment with your own eyes before trusting any system report. Memory of the physical units pays off for months.",
                "Day 2-3 — Shadow one full job-to-job movement event from release through arrival. Note where the system view and the reality diverged.",
                "Day 3-4 — Read the last 30 days of discrepancy reports between field and dispatch. Patterns matter more than individual incidents.",
                "Day 4-5 — Read the deep Dispatch training articles once. They're long; skim and bookmark.",
                "End of week 1 — Identify the one project that keeps generating reconciliation issues. Plan a site visit for week 2.",
            ]},
            {"type": "why", "text":
                "Dispatch is upstream of every asset decision the rest of the platform makes. "
                "A first-week dispatcher who reconciles honestly is worth more than a "
                "ten-year veteran who hides discrepancies to keep numbers clean. Build the "
                "habit early: write what's true, even when it's messy."},
            {"type": "tip", "text":
                "Field crews trust dispatchers who answer the phone. Spend your first week "
                "answering every call within two rings, even if you can't solve it yet. "
                "'I don't know, let me find out' beats 'I'll call you back' every time."},
            {"type": "next", "items": [
                "By week 2 you should be running routine movement events independently",
                "By week 4 you should be reconciling field discrepancies on your own",
                "Bookmark 'Daily Report Basics' (public) — that's the field-side surface feeding what you see",
            ]},
        ],
        "related": [
            "portal-dispatch-identity",
            "tshoot-dispatch-login",
            "public-daily-report-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "tshoot-dispatch-login",
        "section": "troubleshooting",
        "title": "Can't sign in to Dispatch",
        "summary": "Quick fixes when /dispatch-portal/login isn't working.",
        "scopes": ["public"],
        "tags": ["dispatch", "login", "troubleshooting", "password"],
        "body": [
            {"type": "p", "text":
                "Dispatch uses per-user email + password. If you can't get in, walk through these in order."},
            {"type": "steps", "items": [
                "Confirm you're at /dispatch-portal/login (NOT /admin/login or any other portal door — Dispatch's URL is longer than most).",
                "Check caps lock and spelling. Passwords are case-sensitive.",
                "If this is your first login, use the temporary password an admin gave you. You'll be forced to change it.",
                "Use 'Forgot password?' for a reset link by email (single-use, 30-minute expiry).",
                "Check spam if the reset email doesn't arrive. If it's still missing, your operator may have the wrong email on file.",
                "If you see 'account disabled' or 'locked', contact your operator.",
            ]},
            {"type": "why", "text":
                "Dispatch is its own isolated scope. Admin tokens do NOT satisfy Dispatch "
                "endpoints automatically — that's intentional, because dispatch records are "
                "referenced during utilisation reviews and need clean per-user attribution."},
            {"type": "warn", "text":
                "Do NOT type your Dispatch password into another portal's login form. Each "
                "portal has its own login. The Dispatch URL is /dispatch-portal/login — "
                "longer than HR's or Shop's — and confusing it with another portal door is "
                "the single most common first-week login mistake."},
            {"type": "tip", "text":
                "Bookmark /dispatch-portal/login on day one. It's the longest portal URL "
                "and the easiest to misremember. Lockouts self-clear in 15 minutes if you "
                "do hit one."},
        ],
        "related": [
            "portal-dispatch-identity",
            "onboard-dispatch-first-week",
            "public-cant-login",
        ],
    },

    # ── Admin — onboarding + login-troubleshoot ──────────────────────
    {
        "id": "onboard-admin-first-week",
        "section": "onboarding",
        "title": "Admin / Operator — First Week",
        "summary": "What a new platform Operator does in their first week. Deliberate, slow, audit-first.",
        "scopes": ["public"],
        "tags": ["admin", "operator", "onboarding", "first week", "new staff"],
        "body": [
            {"type": "p", "text":
                "Welcome. Operator is the most trusted role on the platform — and the one "
                "with the deepest blast radius. Your first week is deliberately slow. Read, "
                "watch, ask, and resist the urge to change things. Every operator who got "
                "this seriously wrong got there by acting fast in week one."},
            {"type": "steps", "items": [
                "Day 1 — Receive your operator credentials from the platform Owner directly. Sign in at /admin/login and complete your forced password change. Change it again at end of week 1 — by then you'll have learned what a strong password feels like in this environment.",
                "Day 1 — Read the deep Admin Console guidance once, end to end. Don't act on any of it yet.",
                "Day 2 — Sit beside the current operator for the full day. Watch what they do, not what they say they do. The gap between those two is where most mistakes hide.",
                "Day 2-3 — Read every audit-log entry from the last 30 days. Patterns matter more than individual events. If something looks weird, ask before assuming.",
                "Day 3-4 — Pick one low-risk maintenance task (e.g., reviewing the operational-inventory drift dashboard) and walk it under supervision. Do not perform any user-management or backup operation alone yet.",
                "Day 4-5 — Read the platform's last two incident post-mortems if any exist. Operator work is judged by what didn't happen — knowing past near-misses is how you stay there.",
                "End of week 1 — Make a list of every system surface you don't yet understand. Bring that list to your weekly check-in with the Owner.",
            ]},
            {"type": "why", "text":
                "Admin work is high-trust and high-impact. A first-week mistake on a user "
                "record creates a paper trail. A first-week mistake on a role template "
                "creates a security gap. A first-week mistake on a backup creates a "
                "recovery problem. The cost of going slowly in week one is zero; the cost "
                "of going fast can be permanent."},
            {"type": "tip", "text":
                "Operator work is a relationship with the Owner, not just a technical job. "
                "In your first week, send a short end-of-day summary every day: 'today I "
                "did X, Y, Z; tomorrow I plan to do A, B, C; questions I have are 1, 2.' "
                "Most operator-onboarding friction comes from gaps in communication, not "
                "gaps in skill."},
            {"type": "next", "items": [
                "By week 2 you should be performing routine read-only operations independently",
                "By week 4 you should own one user-management cycle end-to-end with Owner sign-off",
                "Bookmark the audit log — you'll be living in it",
            ]},
        ],
        "related": [
            "portal-admin-identity",
            "tshoot-admin-login",
            "public-cant-login",
        ],
    },
    {
        "id": "tshoot-admin-login",
        "section": "troubleshooting",
        "title": "Can't sign in to Admin",
        "summary": "Quick fixes when /admin/login isn't working.",
        "scopes": ["public"],
        "tags": ["admin", "operator", "login", "troubleshooting", "password"],
        "body": [
            {"type": "p", "text":
                "Admin uses a password issued directly by the platform Owner. If you can't get "
                "in, walk through these in order."},
            {"type": "steps", "items": [
                "Confirm you're at /admin/login (NOT /hr/login or any other portal door — admin has its own surface).",
                "Check caps lock and spelling. Passwords are case-sensitive.",
                "If this is your first login, use the temporary password the Owner gave you. You'll be forced to change it.",
                "If you forgot your password, contact the platform Owner directly. Admin password resets are not self-serve by design.",
                "If you see 'account disabled' or 'locked', contact the Owner. Admin lockouts are rare and intentional.",
                "Do not request an admin password reset through any other channel (chat, email forwarding, screenshots). The Owner is the only authorized reset path.",
            ]},
            {"type": "why", "text":
                "Admin password resets are deliberately not automated. A self-serve reset "
                "for the most-privileged account on the platform would be a structural "
                "weakness. The Owner-only reset path is a feature, not a friction — it "
                "makes a phishing attack on an operator account meaningfully harder."},
            {"type": "warn", "text":
                "Never paste your admin password into another portal's login form. Never "
                "share an admin password — not with another operator, not with the Owner "
                "over chat, never. If you suspect your admin password has been seen by "
                "anyone, request a rotation through the Owner immediately."},
            {"type": "tip", "text":
                "Admin lockouts auto-clear in 15 minutes for IP-based lockouts. Account-level "
                "lockouts require Owner action. Bookmark /admin/login and use it from a "
                "known device — the most common admin-login failure is typing /admin in "
                "a phone browser that auto-completes to a previous portal URL."},
        ],
        "related": [
            "portal-admin-identity",
            "onboard-admin-first-week",
            "public-cant-login",
        ],
    },

    {
        "id": "field-daily-report-howto",
        "section": "portals",
        "title": "Field · Submitting a Defensible Daily Report",
        "summary": "What goes in, what to skip, why it matters.",
        "scopes": ["leadership", "admin"],
        "tags": ["field", "daily report", "documentation", "supervisor"],
        "body": [
            {"type": "p", "text":
                "A Daily Report is the operational record of the workday. It is referenced "
                "by HR for time, by PM for project status, by Safety for incidents, and by "
                "leadership for after-the-fact review. Build it like someone will read it "
                "six months from now — because someone will."},
            {"type": "steps", "items": [
                "Pick the correct project (the most common mistake is the wrong project)",
                "Enter crew on site, hours worked, lunch",
                "Document work performed in plain language — what was built / completed / blocked",
                "Photograph progress, deliveries, conditions, and any issue",
                "Record equipment used and any failures",
                "Note conditions: weather, delays, safety concerns",
                "Submit BEFORE leaving the job site",
            ]},
            {"type": "why", "text":
                "The daily report is the single most-cited document we keep. It supports "
                "payroll, project schedule disputes, change orders, insurance claims, and "
                "safety investigations. Field leadership is the only role that can produce it."},
            {"type": "mistakes", "items": [
                "Wrong project selected (everything downstream is wrong)",
                "No photos (a note without a photo is harder to defend)",
                "Submitting from home the next day (timestamp is wrong; details are colder)",
                "Skipping the 'issues' field because nothing felt big enough to mention",
                "Copy-pasting yesterday's narrative",
            ]},
            {"type": "next", "items": [
                "Report becomes visible to PM, HR, Admin, and authorized leadership",
                "Time entries on the report feed HR Time Verification",
                "Photos become part of the project's archive — searchable by date",
                "Issues flagged become PM follow-up items",
            ]},
        ],
        "related": ["why-daily-reports", "connect-field-to-payroll", "why-photos", "role-foreman"],
    },
    {
        "id": "field-equipment-checkout",
        "section": "portals",
        "title": "Field · Equipment Checkout & Return",
        "summary": "The handoff between supervisor, Shop, and HR.",
        "scopes": ["leadership", "admin"],
        "tags": ["field", "equipment", "checkout", "return", "accountability"],
        "body": [
            {"type": "p", "text":
                "Equipment Checkout is how field leadership records who has what. It is the "
                "feeder for both Shop accountability (the asset's whereabouts) and HR "
                "accountability (the employee's responsibility)."},
            {"type": "steps", "items": [
                "Open Field Leadership → Equipment Checkout",
                "Pick the employee and the asset(s)",
                "Note condition at issuance (photos count)",
                "Submit",
            ]},
            {"type": "why", "text":
                "If equipment is lost, damaged, or unreturned at offboarding, the checkout "
                "record answers who had it last. No checkout record = no accountability."},
            {"type": "next", "items": [
                "Shop sees the asset is now assigned (no longer 'available')",
                "HR sees the employee's accountability list grow",
                "At offboarding, HR walks the list and confirms each item back",
            ]},
            {"type": "tip", "text":
                "Photograph the asset condition at checkout AND at return. The two photos "
                "are the cleanest possible damage record."},
        ],
        "related": ["why-equipment-accountability", "hr-offboarding", "role-shop"],
    },
    {
        "id": "field-coaching-documentation",
        "section": "portals",
        "title": "Field · Documenting Coaching & Verbal Conversations",
        "summary": "Why a 5-minute conversation deserves a 30-second record.",
        "scopes": ["leadership", "admin"],
        "tags": ["field", "coaching", "verbal", "documentation"],
        "body": [
            {"type": "p", "text":
                "Verbal coaching is the most common form of leadership and the most under-"
                "documented. Recording it briefly creates the pattern HR needs if the same "
                "conversation keeps happening."},
            {"type": "bullets", "items": [
                "Date, employee, what was discussed, what was agreed",
                "Keep it factual — no opinions, no labels",
                "Note any follow-up action (training, re-check next week, etc.)",
            ]},
            {"type": "why", "text":
                "A coaching record is a small thing the first time. The fourth time it "
                "becomes the basis for a write-up. The tenth time it becomes the basis "
                "for a corrective action. None of that is possible without record #1."},
            {"type": "mistakes", "items": [
                "Waiting until the conversation 'feels formal enough' to document it",
                "Recording opinions instead of facts",
                "Skipping the follow-up note (what was agreed)",
            ]},
        ],
        "related": ["field-writeup-authoring", "hr-writeups-correctives"],
    },
    {
        "id": "field-incident-escalation",
        "section": "portals",
        "title": "Field · Incident Escalation Chain",
        "summary": "Field → Safety → Admin: who sees what, when.",
        "scopes": ["leadership", "admin"],
        "tags": ["field", "incident", "escalation", "safety"],
        "body": [
            {"type": "p", "text":
                "An incident in the field travels through a defined chain. Knowing the "
                "chain helps the right people respond at the right time."},
            {"type": "steps", "items": [
                "Make the scene safe — that is always step one",
                "Document the incident with photos and a written account",
                "Submit through Field or Safety portal before leaving the site",
                "Safety reviews and may open a Corrective Action",
                "Severe incidents escalate to Admin and the assigned PM",
            ]},
            {"type": "why", "text":
                "Quick, factual incident documentation supports investigation, protects "
                "the people involved, and prevents repeat events. Late or vague documentation "
                "does the opposite."},
            {"type": "warn", "text":
                "Do not speculate about cause in the incident report. Record what you "
                "observed. Cause analysis is the investigation's job, not the field report's."},
            {"type": "next", "items": [
                "Safety reviews within their normal cadence",
                "Corrective Actions (if any) are tracked separately",
                "Audit trail preserves the submission chain",
                "Severe incidents trigger admin notification",
            ]},
        ],
        "related": ["task-submit-incident", "connect-incident-to-audit", "why-incidents", "role-safety"],
    },
    {
        "id": "field-writeup-authoring",
        "section": "portals",
        "title": "Field · Authoring a Defensible Write-Up",
        "summary": "Facts, conversation, agreed next step.",
        "scopes": ["leadership", "admin"],
        "tags": ["field", "write-up", "discipline", "documentation"],
        "body": [
            {"type": "p", "text":
                "A write-up records that a conversation happened, what was agreed, and what "
                "the next step is. It is not a complaint form — it is a follow-up structure."},
            {"type": "bullets", "items": [
                "What happened (facts, no labels)",
                "What was discussed (the conversation summary)",
                "What was agreed (next step, deadline, check-in)",
                "Employee acknowledgement (where applicable)",
            ]},
            {"type": "why", "text":
                "Defensible write-ups protect everyone in the chain — the employee from "
                "vague accusations, the supervisor from selective memory, the company from "
                "disputes. The pattern is more important than the harshness of the wording."},
            {"type": "mistakes", "items": [
                "Writing only about the incident, with no agreed next step",
                "Using opinion words ('lazy', 'careless') instead of describing behavior",
                "Authoring without having had the conversation first",
                "Filing and forgetting — the check-in is the point",
            ]},
            {"type": "next", "items": [
                "HR reviews via HR → Field Leadership Records",
                "Repeated write-ups for the same employee surface in review",
                "If escalation is needed, Safety / HR / Admin pick it up from there",
            ]},
        ],
        "related": ["field-coaching-documentation", "hr-writeups-correctives", "role-foreman"],
    },
    {
        "id": "field-project-scope",
        "section": "knowledge",
        "title": "Field · What You See on Other Projects",
        "summary": "Project assignment, PM scope, and why you might not see something.",
        "scopes": ["leadership", "admin"],
        "tags": ["field", "scope", "project", "visibility"],
        "body": [
            {"type": "p", "text":
                "Field Leadership sees records tied to the projects they're assigned to. "
                "PMs see records tied to projects they manage. Admin sees everything."},
            {"type": "bullets", "items": [
                "If a record is missing, the most likely cause is project assignment",
                "If a project changed PMs, older records still belong to the old PM's scope",
                "Cross-project reporting (when needed) goes through Admin",
            ]},
            {"type": "why", "text":
                "Scope-based visibility keeps every supervisor's home screen focused on the "
                "work that's actually theirs. It is not a security wall — it is a noise filter."},
        ],
        "related": ["tshoot-equipment-not-found"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B · CROSS-WORKFLOW CONNECTIONS (iter191 · preview only)
    # ─────────────────────────────────────────────────────────────────
    # Operator-emphasized: "how everything connects" is one of the
    # highest-value teaching opportunities in the platform.
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "connect-field-to-payroll",
        "section": "knowledge",
        "title": "How Field Reports Become Payroll",
        "summary": "Daily Report → HR Time Verification → Payroll cross-check.",
        "scopes": ["field", "leadership", "hr", "pm", "admin"],
        "tags": ["workflow", "field", "hr", "payroll", "time", "connection"],
        "body": [
            {"type": "p", "text":
                "A daily report doesn't sit in one portal. Once submitted, the time entries "
                "feed HR's Time Verification, where they are rolled up weekly into "
                "Regular / Overtime / Lunch and cross-checked against payroll."},
            {"type": "steps", "items": [
                "Supervisor submits a Daily Report from the field",
                "Hours per employee land in HR Time Verification under the matching pay period",
                "HR rolls up the week and flags discrepancies",
                "Verified totals support the payroll cross-check",
                "Audit trail preserves every step — supervisor entry, HR review, export",
            ]},
            {"type": "why", "text":
                "Understanding this connection is what makes a field supervisor careful about "
                "hours and projects in the daily report. The number on a paycheck two weeks "
                "later started life in their phone on the job site."},
            {"type": "tip", "text":
                "Wrong project on the daily report = wrong project on the paycheck cost-code. "
                "It is the cheapest mistake to make and the most expensive to untangle."},
        ],
        "related": ["why-daily-reports", "why-time-verification", "hr-time-verification-deep", "field-daily-report-howto"],
    },
    {
        "id": "connect-incident-to-audit",
        "section": "knowledge",
        "title": "How an Incident Becomes a Corrective Action",
        "summary": "Field incident → Safety review → Corrective Action → Audit trail.",
        "scopes": ["field", "leadership", "safety", "admin"],
        "tags": ["workflow", "incident", "safety", "corrective", "audit", "connection"],
        "body": [
            {"type": "p", "text":
                "An incident submitted in the field doesn't end with submission. It opens a "
                "review chain that may produce a Corrective Action — the follow-up record "
                "that proves the issue was actually addressed."},
            {"type": "steps", "items": [
                "Incident submitted (field, supervisor, or Safety)",
                "Safety reviews the report and decides whether a Corrective Action is needed",
                "Corrective Action is opened with an owner and a deadline",
                "Owner completes the action and records what changed",
                "Safety closes the action — the audit trail now shows the full lifecycle",
            ]},
            {"type": "why", "text":
                "The Corrective Action is what turns an incident from a record of a problem "
                "into a record of a solution. Without it, the same near-miss can happen again "
                "and nobody can say what was done about it last time."},
        ],
        "related": ["why-incidents", "why-corrective-actions", "field-incident-escalation", "role-safety"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 2 · SAFETY PORTAL DEEP CONTENT (iter192 · preview only)
    # Operator directive: "Safety should become one of the deepest and
    # strongest operational guidance areas in the platform."
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "safety-incident-investigation",
        "section": "portals",
        "title": "Safety · Investigating an Incident After Submission",
        "summary": "Triage, root-cause, photographic evidence, witness statements.",
        "scopes": ["safety", "admin"],
        "tags": ["safety", "incident", "investigation", "root cause", "evidence"],
        "body": [
            {"type": "p", "text":
                "Once a field incident is submitted, Safety owns the investigation. The "
                "investigation's job is not to assign blame — it is to reconstruct what "
                "happened factually enough that the same event can be prevented next time."},
            {"type": "steps", "items": [
                "Read the field report in full — do not skim",
                "Verify scene was made safe (the report should say so explicitly)",
                "Review every photo; request additional photos if the scene wasn't captured",
                "Collect statements from witnesses while memory is fresh — within 24h ideally",
                "Identify contributing factors (equipment, training, procedure, environment)",
                "Decide whether a Corrective Action is warranted",
                "Document the investigation findings in the incident record",
            ]},
            {"type": "why", "text":
                "A thorough investigation protects everyone — the injured party, witnesses, "
                "supervisor, and the company. A rushed or skipped investigation creates a "
                "record that proves nothing, which is worse than no record at all."},
            {"type": "mistakes", "items": [
                "Speculating about cause before facts are in",
                "Letting investigation drift past 72h (memory degrades fast)",
                "Closing without a written finding — even 'no further action needed' is a finding",
                "Skipping the witness interview because 'it seems minor'",
            ]},
            {"type": "next", "items": [
                "Corrective Action opened (if warranted) — see safety-corrective-actions-workflow",
                "Severe incidents escalate to Admin + insurance review",
                "Audit trail records every step of the investigation",
                "Patterns surface in monthly Safety review (multiple similar incidents = systemic)",
            ]},
        ],
        "related": ["safety-corrective-actions-workflow", "safety-near-miss-importance",
                    "connect-incident-to-audit", "safety-photo-quality", "role-safety"],
    },
    {
        "id": "safety-corrective-actions-workflow",
        "section": "portals",
        "title": "Safety · Corrective Actions Deep Workflow",
        "summary": "Owner, deadline, follow-up, closure, verification.",
        "scopes": ["safety", "admin"],
        "tags": ["safety", "corrective action", "follow-up", "closure", "workflow"],
        "body": [
            {"type": "p", "text":
                "A Corrective Action is a tracked follow-up to an incident, audit finding, "
                "or near-miss. Its job is to make sure the issue was actually fixed — not "
                "just discussed."},
            {"type": "steps", "items": [
                "Open the Corrective Action from the source record (incident, audit, or near-miss)",
                "Assign an owner — must be a specific person, not a department",
                "Set a deadline — short enough to keep momentum, realistic enough to honor",
                "Define what 'done' looks like (training completed, equipment replaced, procedure updated, etc.)",
                "Owner executes and records what changed (photos, signed acknowledgements, training records)",
                "Safety verifies and closes — never close without verifying",
            ]},
            {"type": "why", "text":
                "Without Corrective Actions, the same problem happens again and nobody can "
                "say what was done last time. Corrective Actions are the difference between "
                "documenting failure and documenting improvement."},
            {"type": "mistakes", "items": [
                "Assigning to a department ('Shop will handle it') — assign to a person",
                "Vague 'done' criteria ('improve training') — be specific",
                "Closing on the owner's word alone — verify with the artifact",
                "Letting actions age past deadline without re-engaging the owner",
            ]},
            {"type": "next", "items": [
                "Closed action shows in the audit trail of the source incident",
                "Open actions surface in Safety's weekly digest",
                "Repeated actions for the same root cause flag a systemic issue",
            ]},
        ],
        "related": ["safety-incident-investigation", "why-corrective-actions",
                    "connect-incident-to-audit", "role-safety"],
    },
    {
        "id": "safety-audits-workflow",
        "section": "portals",
        "title": "Safety · Conducting an Audit",
        "summary": "Cadence, scope, findings, corrective actions, documentation.",
        "scopes": ["safety", "admin"],
        "tags": ["safety", "audit", "findings", "compliance"],
        "body": [
            {"type": "p", "text":
                "Safety audits are scheduled, scope-limited reviews of an area, crew, or "
                "process. The output is a list of findings — each becomes either a closed "
                "observation or an open Corrective Action."},
            {"type": "bullets", "items": [
                "Scope: project, crew, equipment class, or process",
                "Cadence: as established by Safety leadership — typically monthly per active project",
                "Output: findings list with severity, owner, and follow-up",
                "Follow-up: each non-trivial finding becomes a Corrective Action",
            ]},
            {"type": "why", "text":
                "Audits catch issues before they become incidents. A clean audit is not the "
                "goal — a thorough audit is. Findings are the audit's value, not its failure."},
            {"type": "mistakes", "items": [
                "Auditing only when something is wrong — the cadence is the point",
                "Listing findings without owners or deadlines",
                "Recording 'all clear' without describing what was actually inspected",
            ]},
            {"type": "next", "items": [
                "Findings flow into Corrective Actions when warranted",
                "Audit history is searchable by project, crew, and date",
                "Audit patterns inform safety training priorities",
            ]},
        ],
        "related": ["safety-corrective-actions-workflow", "safety-near-miss-importance", "role-safety"],
    },
    {
        "id": "safety-fire-extinguishers",
        "section": "portals",
        "title": "Safety · Fire Extinguisher Inspections",
        "summary": "Monthly inspection cadence, unit history, deficiencies, replacement.",
        "scopes": ["safety", "admin"],
        "tags": ["safety", "fire extinguisher", "inspection", "compliance"],
        "body": [
            {"type": "p", "text":
                "Fire extinguishers carry an explicit inspection cadence — by code and by "
                "company policy. Each unit has a history: inspections, deficiencies, "
                "recharges, replacements."},
            {"type": "steps", "items": [
                "Open Safety → Fire Extinguishers",
                "Pick the unit (by serial or tag)",
                "Record inspection: pressure / seal / pin / hose / signage / clearance",
                "Note any deficiencies — open a follow-up for repair or replacement",
                "Submit — the unit's history updates with the timestamp + inspector",
            ]},
            {"type": "why", "text":
                "Extinguisher records are inspected by code authorities and insurers. A "
                "missing month is a finding; a missing year is a problem. The history is "
                "the unit's defense."},
            {"type": "warn", "text":
                "A failed extinguisher is out of service until replaced — do not return "
                "it to its mount with a deficiency open."},
            {"type": "next", "items": [
                "Unit history is searchable by serial / project / inspector",
                "Deficient units flagged on the Safety dashboard until resolved",
                "Annual recharge / replacement cycles tracked from the same record",
            ]},
        ],
        "related": ["safety-audits-workflow", "role-safety"],
    },
    {
        "id": "safety-training-compliance",
        "section": "portals",
        "title": "Safety · Training & Compliance Tracking",
        "summary": "Who is trained on what, when it expires, what to do when it does.",
        "scopes": ["safety", "admin"],
        "tags": ["safety", "training", "compliance", "expiration"],
        "body": [
            {"type": "p", "text":
                "Training records prove who is qualified to operate what. They are also "
                "what protects the company when a question arises about whether someone "
                "should have been operating equipment they weren't trained on."},
            {"type": "bullets", "items": [
                "Each training record ties to an employee + a competency + a date",
                "Competencies with expirations carry a renewal date",
                "Equipment Issuance can be cross-checked against training records",
                "Expired or missing training surfaces in the Safety dashboard",
            ]},
            {"type": "why", "text":
                "Training records are the documented answer to 'should they have been "
                "doing that?'. Untracked training is undefendable training."},
            {"type": "mistakes", "items": [
                "Issuing equipment to someone whose training expired",
                "Filing training certificates outside the platform ('I'll add it later')",
                "Treating renewal dates as suggestions",
            ]},
            {"type": "next", "items": [
                "Records flow into HR's employee accountability view",
                "Expiring training surfaces in the weekly digest",
                "Audit trail records who entered the training and when",
            ]},
        ],
        "related": ["safety-audits-workflow", "hr-onboarding-new-hire", "role-safety"],
    },
    {
        "id": "safety-near-miss-importance",
        "section": "knowledge",
        "title": "Safety · Why Near-Misses Are the Cheapest Lessons",
        "summary": "What a near-miss is, why it matters more than people think.",
        "scopes": ["field", "leadership", "safety", "admin"],
        "tags": ["safety", "near miss", "why", "documentation"],
        "body": [
            {"type": "p", "text":
                "A near-miss is an event that could have caused harm but didn't — the trip "
                "that didn't become a fall, the swing that didn't connect, the loose chain "
                "that was caught in time. Most companies under-document near-misses because "
                "'nothing happened.' That's exactly backwards."},
            {"type": "why", "text":
                "Near-misses are the cheapest possible lessons. They tell you about a risk "
                "without the cost of an injury. A field that documents near-misses well "
                "produces fewer real incidents over time — because the contributing factors "
                "were caught early."},
            {"type": "bullets", "items": [
                "Document factually — what almost happened, what stopped it",
                "Photograph the setup if it still exists",
                "Submit through the same incident form (mark as near-miss)",
                "Safety reviews like any other incident",
            ]},
            {"type": "tip", "text":
                "Crews that submit near-misses are not bad crews — they are honest crews. "
                "Crews that submit zero near-misses for a year are not safer; they're "
                "quieter. Treat near-miss volume as a signal, not a stigma."},
        ],
        "related": ["safety-incident-investigation", "why-incidents",
                    "connect-incident-to-audit", "role-safety"],
    },
    {
        "id": "safety-escalation-chain",
        "section": "knowledge",
        "title": "Safety · Escalation Chain & Who Sees What",
        "summary": "Field → Safety → Admin → Insurance: when each step engages.",
        "scopes": ["field", "leadership", "safety", "admin"],
        "tags": ["safety", "escalation", "chain", "workflow"],
        "body": [
            {"type": "p", "text":
                "Different severities trigger different responses. Knowing which level "
                "engages when prevents either over-escalation (everyone called for a paper "
                "cut) or under-escalation (admin learns about a serious event from rumor)."},
            {"type": "bullets", "items": [
                "Routine — Safety reviews and closes through normal cadence",
                "Significant — Safety + assigned PM are notified; Corrective Action likely",
                "Severe (injury, property damage, public exposure) — Admin + Safety + PM same-day",
                "Catastrophic — Admin + insurance carrier engagement; legal-hold posture",
            ]},
            {"type": "warn", "text":
                "When in doubt, escalate. The cost of over-engaging Admin once is much "
                "lower than the cost of under-engaging them when it mattered."},
            {"type": "why", "text":
                "The chain protects everyone: the injured party gets prompt response, "
                "the supervisor isn't left holding a serious decision alone, and Admin "
                "has the context to engage insurance / legal when actually needed."},
        ],
        "related": ["field-incident-escalation", "safety-incident-investigation", "role-safety"],
    },
    {
        "id": "safety-photo-quality",
        "section": "knowledge",
        "title": "Safety · Photo & Documentation Quality Standards",
        "summary": "What makes a photograph evidence vs noise.",
        "scopes": ["field", "leadership", "safety", "shop", "admin"],
        "tags": ["safety", "photo", "documentation", "quality", "evidence"],
        "body": [
            {"type": "p", "text":
                "A photo turns a note into evidence. A bad photo turns it back into a note. "
                "The difference is what's in the frame, what's in focus, and whether "
                "anyone six months later can tell what they're looking at."},
            {"type": "bullets", "items": [
                "Capture context first (wide shot showing the surroundings)",
                "Then capture the detail (close-up of the specific item / damage / hazard)",
                "Include a size reference where it matters (a hand, a tape, anything known)",
                "Avoid blur — re-take if motion or focus is off",
                "Take more than you think you need; deleting is cheap, re-visiting the scene isn't",
            ]},
            {"type": "why", "text":
                "Photos are the first thing reviewers reach for. They survive memory, "
                "personnel changes, and disputes. A clear photo set is worth more than a "
                "long written description."},
            {"type": "mistakes", "items": [
                "Only one photo of a complex scene",
                "Close-up with no context (where is this?)",
                "Wide shot with no detail (what's the issue?)",
                "Forgetting to photograph the surroundings (witnesses, equipment, conditions)",
            ]},
        ],
        "related": ["why-photos", "task-upload-photos", "safety-incident-investigation"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 2 · SHOP / FLEET DEEP CONTENT (iter192 · preview only)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "shop-preop-deep",
        "section": "portals",
        "title": "Shop · Pre-Op Inspections Deep Dive",
        "summary": "What every pre-op should catch, what 'pass' really means.",
        "scopes": ["shop", "admin"],
        "tags": ["shop", "pre-op", "inspection", "equipment", "operator"],
        "body": [
            {"type": "p", "text":
                "A Pre-Op is the operator's check before using equipment. It's a daily "
                "promise that the equipment is safe to run — and a daily protection if it "
                "turns out it wasn't."},
            {"type": "bullets", "items": [
                "Fluids — engine, hydraulic, coolant levels and leaks",
                "Tires / tracks — pressure, wear, damage",
                "Lights & signals — turn / brake / backup / strobe",
                "Safety devices — seatbelt, horn, alarms, guards",
                "Operating controls — full range, no binding",
                "Visible damage — frame cracks, bent components, missing bolts",
            ]},
            {"type": "why", "text":
                "Pre-Op records protect the operator from being blamed for a defect that "
                "was there before they started, and protect the company from running "
                "equipment that should have been pulled. A signed Pre-Op is a record of "
                "operational accountability."},
            {"type": "warn", "text":
                "Pre-Op is not paperwork. If you skip the inspection and 'just check the "
                "box,' you have signed a document saying the equipment was safe when you "
                "didn't actually look."},
            {"type": "mistakes", "items": [
                "Box-ticking without walking the asset",
                "Missing the underside / blind sides (where most damage hides)",
                "Skipping the brakes / safety devices because 'they worked yesterday'",
                "Recording 'pass' on an issue you mean to flag verbally",
            ]},
            {"type": "next", "items": [
                "Submitted Pre-Op becomes part of the asset's daily record",
                "Failed Pre-Op kicks the failed-pre-op workflow (Shop + Dispatch alerted)",
                "Pattern of failures on the same asset surfaces in Shop trends",
            ]},
        ],
        "related": ["shop-failed-preop-workflow", "shop-operator-responsibilities",
                    "shop-damage-reporting", "role-shop"],
    },
    {
        "id": "shop-failed-preop-workflow",
        "section": "portals",
        "title": "Shop · Failed Pre-Op Workflow",
        "summary": "What happens after a pre-op fails — and who's involved.",
        "scopes": ["shop", "admin"],
        "tags": ["shop", "failed pre-op", "out of service", "workflow"],
        "body": [
            {"type": "p", "text":
                "When a Pre-Op fails — or the operator flags an Out-of-Service condition — "
                "a defined chain kicks in. The asset is tagged, Shop is notified, Dispatch "
                "knows it's unavailable, and the field has documented why."},
            {"type": "steps", "items": [
                "Operator marks the Pre-Op as failed (or out-of-service) and documents what",
                "Auto-email fans out to every active Shop user + the supervisor",
                "Shop reviews, schedules repair, or pulls the asset",
                "Dispatch is updated — the asset stops appearing as available",
                "When repaired, Shop signs off — the asset re-enters availability",
            ]},
            {"type": "why", "text":
                "Without this chain, a failed asset can keep getting handed to the next "
                "operator. The failure record + the dispatch hold are the two things that "
                "stop the loop. Both need to land or the system breaks."},
            {"type": "mistakes", "items": [
                "Marking 'fail' without describing the failure",
                "Verbal handoff to Shop without filing the form (no record exists)",
                "Returning to service without a Shop sign-off",
                "Skipping the Dispatch update — asset shows available but isn't",
            ]},
            {"type": "next", "items": [
                "Shop receives the alert email and opens the inspection record",
                "Dispatch sees the asset on the Out-of-Service list",
                "Shop sign-off closes the loop and clears the asset",
                "Audit trail preserves the full lifecycle of the failure",
            ]},
        ],
        "related": ["shop-preop-deep", "shop-damage-reporting", "connect-shop-to-dispatch",
                    "role-shop", "role-dispatch"],
    },
    {
        "id": "shop-damage-reporting",
        "section": "portals",
        "title": "Shop · Damage Reporting",
        "summary": "From discovery to cost recovery — the full damage paper trail.",
        "scopes": ["shop", "admin"],
        "tags": ["shop", "damage", "equipment", "reporting"],
        "body": [
            {"type": "p", "text":
                "Damage reports document equipment damage with enough detail to support "
                "repair planning, warranty / insurance claims, and (if applicable) operator "
                "accountability conversations."},
            {"type": "steps", "items": [
                "Photograph the damage — wide shot for context, close-ups for detail",
                "Record the asset (serial / tag), the date, the discovering party",
                "Describe what happened factually — when known, by whom; when not, say so",
                "Tie to the operator's name if the damage is associated with a specific use",
                "Submit — Shop, Admin, and (where applicable) HR can review",
            ]},
            {"type": "why", "text":
                "Damage records support three downstream conversations: how much to "
                "repair / replace, whether insurance or warranty applies, and whether the "
                "damage points to a training or process problem."},
            {"type": "warn", "text":
                "Damage reports are factual records, not blame attributions. Describe what "
                "you observed; let HR / Safety handle accountability discussions separately."},
            {"type": "next", "items": [
                "Shop schedules repair or write-off",
                "If associated with an operator, the record is visible to HR for review",
                "Asset history grows — patterns surface (some assets / operators repeat)",
            ]},
        ],
        "related": ["shop-preop-deep", "field-equipment-checkout",
                    "connect-equipment-lifecycle", "role-shop"],
    },
    {
        "id": "shop-maintenance-coordination",
        "section": "portals",
        "title": "Shop · Maintenance Coordination",
        "summary": "Scheduled service, asset history, and the Dispatch handoff.",
        "scopes": ["shop", "admin"],
        "tags": ["shop", "maintenance", "service", "scheduled"],
        "body": [
            {"type": "p", "text":
                "Maintenance work — scheduled or reactive — flows through Shop. The point "
                "is to keep equipment running while preserving a clean per-asset service "
                "history."},
            {"type": "bullets", "items": [
                "Scheduled service: based on hours / mileage / calendar per asset",
                "Reactive service: from a failed Pre-Op, damage report, or operator note",
                "Service record: what was done, by whom, parts used, time on asset",
                "Dispatch handoff: asset is unavailable during service, available again after sign-off",
            ]},
            {"type": "why", "text":
                "A clean maintenance history reduces unexpected downtime, supports "
                "warranty / resale value, and answers questions when an asset fails ('was "
                "it serviced on schedule?')."},
            {"type": "next", "items": [
                "Service log is searchable per asset",
                "Dispatch updated when asset enters / leaves service",
                "Recurring service patterns flag candidates for replacement",
            ]},
        ],
        "related": ["shop-failed-preop-workflow", "shop-downtime-logic",
                    "connect-shop-to-dispatch", "role-shop"],
    },
    {
        "id": "shop-equipment-return",
        "section": "portals",
        "title": "Shop · Equipment Return & Reconciliation",
        "summary": "Receiving equipment back — condition check, history, accountability.",
        "scopes": ["shop", "admin"],
        "tags": ["shop", "return", "reconciliation", "accountability"],
        "body": [
            {"type": "p", "text":
                "Equipment returns are where accountability lands. Whether the return is "
                "routine (end-of-job) or part of an offboarding, Shop's job is to verify "
                "what came back, in what condition, with what history."},
            {"type": "steps", "items": [
                "Inspect on return — photograph condition (matches checkout photos if available)",
                "Note any damage discovered at return that wasn't recorded earlier",
                "Update the asset's status: available / in-service / damaged / lost",
                "Tie back to the Field Leadership checkout record if applicable",
                "If associated with an offboarding, confirm HR sees the asset as returned",
            ]},
            {"type": "why", "text":
                "Returns close the accountability loop opened at checkout. Without a clean "
                "return record, an asset can be 'returned' verbally but still flagged as "
                "assigned in the system — the kind of mismatch that surfaces only at year-end."},
            {"type": "mistakes", "items": [
                "Accepting a return without inspecting condition",
                "Skipping the photo at return ('it looks fine')",
                "Not updating the asset status — record shows it still assigned",
                "Returning offboarded equipment without notifying HR",
            ]},
        ],
        "related": ["field-equipment-checkout", "hr-offboarding",
                    "connect-equipment-lifecycle", "role-shop"],
    },
    {
        "id": "shop-operator-responsibilities",
        "section": "knowledge",
        "title": "Shop · Operator Responsibilities",
        "summary": "What the operator owns — and what Shop owns.",
        "scopes": ["field", "leadership", "shop", "admin"],
        "tags": ["shop", "operator", "responsibility", "field"],
        "body": [
            {"type": "p", "text":
                "The operator and Shop split equipment responsibility. Understanding the "
                "split prevents the most common conflict ('Shop should have caught that' / "
                "'the operator should have flagged it')."},
            {"type": "bullets", "items": [
                "Operator owns: daily Pre-Op, in-shift checks, immediate damage / failure reporting, end-of-shift condition note",
                "Shop owns: scheduled service, repair after a documented failure, fleet condition over time, sign-off on return-to-service",
                "Shared: damage discovery (whoever finds it documents it), training compliance (operator's record but Shop verifies before issuing)",
            ]},
            {"type": "why", "text":
                "Clear ownership prevents the gap where 'someone else was supposed to "
                "catch that.' Both halves carry weight — the system only works when both "
                "sides own their half."},
        ],
        "related": ["shop-preop-deep", "field-equipment-checkout", "role-shop"],
    },
    {
        "id": "shop-downtime-logic",
        "section": "knowledge",
        "title": "Shop · Downtime & Escalation Logic",
        "summary": "When downtime becomes an escalation, not just a repair.",
        "scopes": ["shop", "dispatch", "admin"],
        "tags": ["shop", "downtime", "escalation", "dispatch"],
        "body": [
            {"type": "p", "text":
                "Not every repair is an escalation. But certain downtime patterns are — and "
                "they need to engage Dispatch, PM, and sometimes Admin so the field doesn't "
                "find out about availability gaps the day they need the asset."},
            {"type": "bullets", "items": [
                "Routine — same-day or next-day repair, no field impact",
                "Significant — multi-day repair OR critical asset; Dispatch must know",
                "Escalation — repair pulls a project-critical asset; PM + Dispatch + Admin engage",
                "Replacement decision — repeat failures or repair-cost threshold; Admin decision required",
            ]},
            {"type": "why", "text":
                "The field can absorb a routine repair without warning. It cannot absorb a "
                "project-critical asset disappearing without coordination. The escalation "
                "rules are not bureaucracy — they are how Dispatch / PM / Admin get the "
                "context they need to keep the field running."},
        ],
        "related": ["shop-maintenance-coordination", "shop-failed-preop-workflow",
                    "connect-shop-to-dispatch", "role-shop", "role-dispatch"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 2 · CROSS-WORKFLOW CONNECTIONS (iter192)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "connect-shop-to-dispatch",
        "section": "knowledge",
        "title": "How Shop & Dispatch Stay in Sync",
        "summary": "Failed Pre-Op → Shop → Dispatch hold → Field availability.",
        "scopes": ["shop", "dispatch", "leadership", "pm", "admin"],
        "tags": ["workflow", "shop", "dispatch", "equipment", "connection"],
        "body": [
            {"type": "p", "text":
                "Equipment availability is a Dispatch concern. Equipment health is a Shop "
                "concern. They have to stay in sync or the field gets handed assets that "
                "shouldn't be in service — or can't find assets that actually are."},
            {"type": "steps", "items": [
                "Pre-Op failure / damage / scheduled service kicks an asset out of service",
                "Shop records the status — that update flows to Dispatch's view of availability",
                "Dispatch holds the asset; it stops appearing in field-assignment lists",
                "Shop completes the work and signs off — Dispatch picks up the new status",
                "Asset is back in field rotation — with a clean record of the gap",
            ]},
            {"type": "why", "text":
                "When this loop is clean, the field sees only assets that are actually "
                "ready. When it breaks, supervisors waste a morning chasing equipment that "
                "isn't where the system says it is. The integrity of every asset list "
                "downstream rides on this loop."},
            {"type": "tip", "text":
                "If Dispatch sees an asset listed as available but Shop has it on the bench, "
                "that's a sync bug — usually a missing status update. Flag it; don't work around it."},
        ],
        "related": ["shop-failed-preop-workflow", "shop-maintenance-coordination",
                    "shop-downtime-logic", "role-shop", "role-dispatch"],
    },
    {
        "id": "connect-equipment-lifecycle",
        "section": "knowledge",
        "title": "Equipment Lifecycle — End to End",
        "summary": "Issuance → Use → Damage → Return → Offboarding.",
        "scopes": ["shop", "dispatch", "hr", "leadership", "admin"],
        "tags": ["workflow", "equipment", "lifecycle", "shop", "hr", "connection"],
        "body": [
            {"type": "p", "text":
                "An asset's life in the system spans multiple portals. Knowing the "
                "lifecycle helps every portal recognize their piece — and helps everyone "
                "spot where a record is missing."},
            {"type": "steps", "items": [
                "Asset created / received — Shop or Admin records the master record",
                "Issued to an employee — Field Leadership or Safety Forms equipment-issuance form",
                "In use — daily Pre-Op, in-shift checks, end-of-shift condition note",
                "Damage / failure (if any) — operator or Shop records",
                "Returned — Shop inspects, updates status, ties to checkout record",
                "Offboarding (when applicable) — HR confirms each assigned asset is back, transferred, or written off",
                "Retired / sold — Admin records final disposition",
            ]},
            {"type": "why", "text":
                "Every gap in this chain is a future dispute waiting to happen — 'was "
                "this returned?', 'who damaged it?', 'why is HR's list different from "
                "Shop's list?'. The lifecycle view is the answer key."},
        ],
        "related": ["field-equipment-checkout", "shop-equipment-return", "shop-damage-reporting",
                    "hr-offboarding", "why-equipment-accountability"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 3 · DISPATCH PORTAL DEEP CONTENT (iter193 · preview only)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "portal-dispatch",
        "section": "portals",
        "title": "Dispatch Portal Training",
        "summary": "Equipment movement, availability, holds, transfers, and field coordination — the upstream of every asset decision.",
        "scopes": ["dispatch", "admin"],
        "tags": ["dispatch", "portal", "equipment", "coordination"],
        "body": [
            {"type": "p", "text":
                "Dispatch is the portal that coordinates equipment across the fleet. Its job is to "
                "make sure the right asset is in the right place, on the right job, in a known "
                "state — and that everyone downstream (Shop, Field Leadership, PM) sees the same "
                "truth about where things are and what they're doing."},
            {"type": "p", "text":
                "Who uses it: Dispatchers, Fleet Coordinators, and Operations Oversight. Cross-portal "
                "reads from Shop (equipment health), Field Leadership (operator-level checkout), "
                "and PM (project assignments)."},
            {"type": "bullets", "items": [
                "Equipment availability — Available / Assigned / In-Transit / Hold / In Service / OOS",
                "Movement events — job-to-job transfers with source · destination · arrival",
                "Holds & transfers — temporary restriction vs permanent reassignment",
                "Utilisation reports — over- and under-deployed assets surfaced",
                "Operational events log — assignments, holds, returns, reason codes",
                "Field coordination — reconciling system view with physical reality",
                "Cross-portal status broadcasting — Shop / Field / PM sync",
            ]},
            {"type": "why", "text":
                "Dispatch is upstream of every asset-related decision the rest of the platform makes. "
                "When dispatch is accurate, the field doesn't waste mornings hunting for equipment, "
                "Shop schedules service against the right project, PMs see real utilisation, and "
                "executives make fleet decisions with honest data. When dispatch is wrong, every "
                "downstream view is wrong — and the people relying on them often don't know it."},
            {"type": "next", "items": [
                "If you're new — read the role guide for Dispatch",
                "Walk one job-to-job movement event end-to-end (release → in-transit → arrival)",
                "Learn the difference between a HOLD and a TRANSFER — picking the wrong one quietly corrupts utilisation",
                "Bookmark Availability — your single most-referenced surface",
            ]},
            {"type": "mistakes", "items": [
                "Reassigning to a new project without releasing from the old one",
                "Skipping the in-transit state (jumps A→B with no gap, hides delays)",
                "Using a HOLD when a TRANSFER is correct (or vice versa) — corrupts utilisation",
                "Forgetting to confirm arrival (asset shows in-transit indefinitely)",
                "Arguing with field discrepancy reports instead of recording the reconciliation",
            ]},
            {"type": "tip", "text":
                "Most disputes about 'where is X equipment?' end at Dispatch. The cleaner the "
                "dispatch record, the shorter the conversation. If a supervisor finds equipment "
                "in the field that Dispatch doesn't show there, record the discrepancy and "
                "reconcile — the record is more valuable than the question of who was right."},
            {"type": "warn", "text":
                "A held asset still counts against the original project's utilisation; a "
                "transferred asset does not. Picking the right operation is how project "
                "reporting downstream stays honest."},
        ],
        "related": [
            "role-dispatch",
            "dispatch-equipment-movement",
            "dispatch-availability-management",
            "dispatch-holds-transfers",
            "dispatch-field-coordination",
            "dispatch-accuracy-why",
            "connect-shop-to-dispatch",
            "connect-equipment-lifecycle",
        ],
    },
    {
        "id": "dispatch-equipment-movement",
        "section": "portals",
        "title": "Dispatch · Equipment Movement Lifecycle",
        "summary": "Job-to-job transfers, in-transit status, arrival confirmation.",
        "scopes": ["dispatch", "admin"],
        "tags": ["dispatch", "movement", "transfer", "lifecycle"],
        "body": [
            {"type": "p", "text":
                "Equipment doesn't teleport between jobs. The movement is a tracked event "
                "with a source, a destination, an in-transit state, and an arrival "
                "confirmation. Each of those states is visible to the people who need it."},
            {"type": "steps", "items": [
                "Originating PM / supervisor releases the asset (or Dispatch reclaims it)",
                "Dispatch creates the movement event with source / destination / timing",
                "Asset enters `in-transit` — invisible to either job's active asset list",
                "Receiving project confirms arrival; asset re-enters `assigned` on the new job",
                "Movement event closes — visible in the asset's history",
            ]},
            {"type": "why", "text":
                "Without a tracked movement, equipment can show as 'still on job A' while it "
                "is physically on job B. That breaks both project asset reports and Shop's "
                "ability to know where to dispatch a technician for service."},
            {"type": "mistakes", "items": [
                "Reassigning to the new project without releasing from the old one",
                "Skipping the in-transit state (jumps from A to B with no gap, hides delays)",
                "Forgetting to confirm arrival (asset shows in-transit indefinitely)",
            ]},
            {"type": "next", "items": [
                "Both projects' asset lists update automatically",
                "Asset history shows the full path — useful for utilisation analysis",
                "PMs see project-level changes in their dashboard",
            ]},
        ],
        "related": ["dispatch-availability-management", "dispatch-holds-transfers",
                    "connect-equipment-lifecycle", "role-dispatch"],
    },
    {
        "id": "dispatch-availability-management",
        "section": "portals",
        "title": "Dispatch · Availability & Utilisation",
        "summary": "What 'available' really means, and the cost of stale data.",
        "scopes": ["dispatch", "admin"],
        "tags": ["dispatch", "availability", "utilisation", "asset"],
        "body": [
            {"type": "p", "text":
                "'Available' has a precise meaning: assigned to no project, not on hold, not "
                "in service, condition-cleared. Anything less is something else — and the "
                "system records the difference so Dispatch can decide accurately."},
            {"type": "bullets", "items": [
                "Available — ready to be assigned",
                "Assigned — currently on a project",
                "In-transit — moving between jobs",
                "On hold — temporarily restricted (operator certification, project pause, etc.)",
                "In service — Shop has the asset",
                "Out of service — failed pre-op or damage pending repair",
            ]},
            {"type": "why", "text":
                "Stale availability is the source of more daily wasted effort than any other "
                "kind of bad data. A foreman driving to a yard for an asset that isn't there "
                "is the most expensive five minutes in dispatch."},
            {"type": "next", "items": [
                "Availability changes flow to the field-assignment lists in real time",
                "Utilisation reports surface assets that are over- or under-deployed",
                "Patterns inform fleet sizing decisions",
            ]},
        ],
        "related": ["dispatch-holds-transfers", "shop-failed-preop-workflow",
                    "connect-shop-to-dispatch", "role-dispatch"],
    },
    {
        "id": "dispatch-holds-transfers",
        "section": "portals",
        "title": "Dispatch · Holds & Transfers",
        "summary": "Pausing, releasing, and routing assets without losing accountability.",
        "scopes": ["dispatch", "admin"],
        "tags": ["dispatch", "hold", "transfer", "release"],
        "body": [
            {"type": "p", "text":
                "A hold is a temporary restriction. A transfer is a permanent change of "
                "assignment. They're different operations because they have different "
                "downstream effects — a hold is reversible without retracing accountability; "
                "a transfer is not."},
            {"type": "bullets", "items": [
                "Hold reasons: operator certification, project pause, weather, inspection",
                "Transfer reasons: project completion, reassignment, off-rent",
                "Each carries a reason code that surfaces in the asset's history",
            ]},
            {"type": "why", "text":
                "Hold vs transfer is one of the most-confused operations in dispatch — "
                "and one where the wrong choice quietly poisons downstream reports. Picking "
                "the right one is how project utilisation numbers stay honest."},
            {"type": "warn", "text":
                "Do not use a hold when a transfer is the right operation, or vice versa. "
                "A held asset still counts against the original project's utilisation; a "
                "transferred asset does not. The reporting downstream depends on the "
                "correct choice."},
            {"type": "next", "items": [
                "Held assets reappear when the hold is cleared",
                "Transferred assets close out the original project's record",
                "PM views update with the change",
            ]},
        ],
        "related": ["dispatch-availability-management", "dispatch-equipment-movement",
                    "role-dispatch"],
    },
    {
        "id": "dispatch-field-coordination",
        "section": "knowledge",
        "title": "Dispatch · How Dispatch & Field Stay in Sync",
        "summary": "The handoff that prevents 'asset isn't where the system says it is'.",
        "scopes": ["dispatch", "leadership", "pm", "admin"],
        "tags": ["dispatch", "field", "coordination", "workflow"],
        "body": [
            {"type": "p", "text":
                "Dispatch sees the system view; field sees the physical view. When those "
                "drift, the field wastes morning hours looking for equipment. The handoff "
                "is what keeps the two views aligned."},
            {"type": "bullets", "items": [
                "Field-leadership equipment checkout records WHO has WHAT (operator-level)",
                "Dispatch records WHERE that WHAT is (project-level)",
                "Both update on movement events; both surface to PM",
            ]},
            {"type": "why", "text":
                "Dispatch alone can't see the operator-level reality; field alone can't see "
                "the project-level allocation. The handoff is the only place both views meet."},
            {"type": "tip", "text":
                "If a supervisor finds equipment in the field that Dispatch doesn't show "
                "there, the supervisor records the discrepancy — Dispatch reconciles, "
                "doesn't argue. The record is more valuable than the question of who was right."},
        ],
        "related": ["dispatch-equipment-movement", "dispatch-availability-management",
                    "field-equipment-checkout", "connect-shop-to-dispatch"],
    },
    {
        "id": "dispatch-accuracy-why",
        "section": "knowledge",
        "title": "Dispatch · Why Accuracy Matters",
        "summary": "Every downstream report depends on the dispatch record being right.",
        "scopes": ["dispatch", "shop", "leadership", "pm", "admin"],
        "tags": ["dispatch", "accuracy", "why", "data quality"],
        "body": [
            {"type": "p", "text":
                "Dispatch is upstream of everything: project utilisation reports, Shop's "
                "view of who has what, the field's available-asset list, executive fleet "
                "decisions. When dispatch is wrong, every downstream view is wrong — but "
                "the people relying on them often don't know it."},
            {"type": "bullets", "items": [
                "Field sees a stale 'available' list → wasted trips",
                "Shop schedules service on assets that have moved → wasted technician time",
                "PMs see wrong utilisation → wrong project cost estimates",
                "Executives see wrong fleet utilisation → wrong purchase / sell decisions",
            ]},
            {"type": "why", "text":
                "Dispatch accuracy isn't a Dispatch-team concern — it's an operational "
                "concern for every team downstream. Treat each entry like the report it'll "
                "be cited in, because it will be."},
        ],
        "related": ["dispatch-availability-management", "dispatch-field-coordination",
                    "connect-shop-to-dispatch", "role-dispatch"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 3 · PM PORTAL DEEP CONTENT (iter193 · preview only)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "portal-pm",
        "section": "portals",
        "title": "PM Portal Training",
        "summary": "Project oversight, report review, labor documentation, and cross-portal coordination — the project-level lens.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "project manager", "portal"],
        "body": [
            {"type": "p", "text":
                "The PM portal is the project-level lens. PMs see only the records tied to "
                "projects they manage — daily reports, inspections, JHAs, incidents, "
                "field-leadership records, equipment assignments, labor documentation, and "
                "cross-portal status. It is intentionally scope-filtered: each PM focuses on "
                "their own projects without wading through everyone else's."},
            {"type": "p", "text":
                "Who uses it: Project Managers and Co-PMs. Cross-portal reads from Field "
                "Leadership (Daily Reports), HR (labor totals), Safety (incidents), Shop "
                "(equipment health), and Dispatch (assignments)."},
            {"type": "bullets", "items": [
                "Project dashboard — scope-filtered to PM's assigned projects only",
                "Daily Report review — operational truth of each day on the project",
                "Inspections / meetings / JHAs — safety and quality records",
                "Incidents — anything that happened on the project, full chain",
                "Field Leadership records — write-ups, recognition, attendance",
                "Equipment-allocation visibility — what's on the project, in what state",
                "Labor documentation — hours → cost-code → payroll connection",
                "Cross-project visibility — only what scope grants; admin can see all",
                "Reporting workflows — dashboards, drill-downs, exports for owners",
                "Cadence reviews — daily / weekly / monthly review loops",
            ]},
            {"type": "why", "text":
                "PM work is the bridge between field operations and project finance. A Daily "
                "Report from the field becomes a labor cost in the PM dashboard. An incident "
                "becomes a project risk. An equipment allocation becomes a utilisation number. "
                "PMs are the only role with a project-wide view that's both wide enough to spot "
                "drift and narrow enough to act on it. If PM oversight is sloppy, projects "
                "discover problems at month-end instead of mid-week — and month-end is too late."},
            {"type": "next", "items": [
                "If you're new — read the role guide for PM",
                "Walk one project's last 7 days of Daily Reports end-to-end (the cadence anchor)",
                "Open the labor-documentation report and reconcile against one weekly payroll",
                "Bookmark Cross-Project Visibility — understand what your scope does/doesn't show",
            ]},
            {"type": "mistakes", "items": [
                "Approving a Daily Report without verifying the labor totals match the field",
                "Letting an incident close without confirming the corrective action was verified",
                "Skipping the weekly review cadence (drift compounds when no one's watching)",
                "Assuming admin sees the same scope-filtered view (admin sees everything)",
                "Reviewing reports a week late — the field needs feedback while details are warm",
            ]},
            {"type": "tip", "text":
                "PM scope is project-based, not portal-based. Records from projects you don't "
                "manage are intentionally hidden — that's a noise filter, not a security wall. "
                "If you need to see a different PM's project, ask admin for read access; don't "
                "go around the scope by signing in with shared credentials."},
            {"type": "warn", "text":
                "Don't sign in to /pm/login with someone else's email. Per-PM scope is enforced "
                "by token — using another PM's account makes the audit log point at them for "
                "every action you take. Ask admin for proper cross-PM access if you need it."},
        ],
        "related": [
            "role-pm",
            "pm-project-review-cadence",
            "pm-labor-documentation",
            "pm-cross-project-visibility",
            "pm-coordination",
            "pm-reporting-workflows",
            "connect-pm-field-review",
        ],
    },
    {
        "id": "pm-project-review-cadence",
        "section": "portals",
        "title": "PM · Project Review Cadence",
        "summary": "What to review, how often, what to escalate.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "review", "cadence", "project"],
        "body": [
            {"type": "p", "text":
                "PM review is the early-warning system for a project. Daily checks catch "
                "small issues; weekly rollups catch trends; monthly reviews drive direction. "
                "Skipping a level breaks the warning system."},
            {"type": "steps", "items": [
                "Daily: scan daily reports for issues, missing entries, schedule slip",
                "Weekly: rollup of hours, incident count, equipment status, open items",
                "Monthly: project trend review with leadership, scope alignment",
                "Quarterly: cross-project lessons-learned",
            ]},
            {"type": "why", "text":
                "Most project problems show up in the daily / weekly window as small "
                "signals. The cost of catching them there is hours; the cost of catching "
                "them at the monthly review is weeks; the cost of catching them at closeout "
                "is the change order."},
            {"type": "next", "items": [
                "Issues flagged in review become PM follow-up items",
                "Patterns inform supervisor coaching",
                "Cross-project trends surface to admin and leadership",
            ]},
        ],
        "related": ["pm-labor-documentation", "pm-reporting-workflows",
                    "connect-pm-field-review", "role-pm"],
    },
    {
        "id": "pm-labor-documentation",
        "section": "portals",
        "title": "PM · Labor & Documentation Relationships",
        "summary": "How field labor entries become project cost reality.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "labor", "documentation", "cost", "payroll"],
        "body": [
            {"type": "p", "text":
                "Hours entered on field reports become the project's labor cost. The PM is "
                "the person who knows whether those hours make sense for the work performed "
                "— nobody else has both the field view and the cost view."},
            {"type": "bullets", "items": [
                "Daily report hours → HR time verification → payroll cost-code",
                "Wrong project on a daily report = wrong cost-code on payroll",
                "Time discrepancies are typically caught in weekly PM review",
            ]},
            {"type": "why", "text":
                "Labor is usually the biggest line on a project. Bad labor data isn't a "
                "small problem — it's a multi-thousand-dollar problem repeating every week. "
                "PM review is where it gets caught before it accumulates."},
            {"type": "mistakes", "items": [
                "Assuming HR will catch project mis-codes (HR catches totals, PM catches projects)",
                "Reviewing labor only at month-end (the mistake compounds for 4 weeks)",
                "Not requesting a re-entry when the report is materially wrong",
            ]},
        ],
        "related": ["connect-field-to-payroll", "hr-time-verification-deep",
                    "pm-project-review-cadence", "role-pm"],
    },
    {
        "id": "pm-cross-project-visibility",
        "section": "knowledge",
        "title": "PM · What You Can and Cannot See",
        "summary": "Project assignment, scope filtering, when to ask Admin.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "scope", "visibility", "rbac"],
        "body": [
            {"type": "p", "text":
                "PM visibility is project-scoped. Records tied to projects you manage are "
                "fully visible; records on other projects are intentionally hidden. This is "
                "not a permissions limitation — it's a noise filter."},
            {"type": "bullets", "items": [
                "Visible: daily reports, inspections, JHAs, incidents, FL records on your projects",
                "Visible: equipment assignments on your projects",
                "Hidden: any record tied to a project you don't manage",
                "Cross-project reporting: routed through Admin",
            ]},
            {"type": "warn", "text":
                "If a record you expect to see is missing, first check the project "
                "assignment. The most common cause is the wrong project on the originating "
                "record — fix at the source, don't work around it."},
            {"type": "why", "text":
                "Scope-based visibility keeps each PM's view focused on the work that's "
                "actually theirs. Admin sees everything; that's why cross-project questions "
                "route through Admin, not through PM-to-PM data sharing."},
        ],
        "related": ["field-project-scope", "pm-project-review-cadence", "role-pm"],
    },
    {
        "id": "pm-reporting-workflows",
        "section": "portals",
        "title": "PM · Reporting Workflows",
        "summary": "Surface-level views, drill-downs, and what to export.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "reporting", "workflow", "export"],
        "body": [
            {"type": "p", "text":
                "PM reporting is layered. The PM dashboard is the surface scan; drill-downs "
                "answer specific questions; exports support conversations outside the platform."},
            {"type": "bullets", "items": [
                "Dashboard: per-project rollup of recent activity, open items, alerts",
                "Drill-down: per-record detail (daily report, inspection, etc.)",
                "Export: CSV / PDF for owner / client / executive review",
            ]},
            {"type": "why", "text":
                "Layered reporting matches the kind of question being asked. Dashboard "
                "answers 'how is the project doing'; drill-downs answer 'what specifically "
                "happened'; exports answer 'show me the record'. Each has its place."},
            {"type": "next", "items": [
                "Audit trail records who exported what and when",
                "Repeated drill-downs into the same area surface as PM patterns",
            ]},
        ],
        "related": ["pm-project-review-cadence", "pm-labor-documentation", "role-pm"],
    },
    {
        "id": "pm-coordination",
        "section": "knowledge",
        "title": "PM · Coordination Across Crews & Trades",
        "summary": "How PMs use the platform to keep multiple crews aligned.",
        "scopes": ["pm", "admin"],
        "tags": ["pm", "coordination", "crews"],
        "body": [
            {"type": "p", "text":
                "Multi-crew projects live or die on coordination. The platform doesn't run "
                "coordination — humans do — but the platform creates the shared record that "
                "keeps every crew working from the same facts."},
            {"type": "bullets", "items": [
                "Daily reports across crews tell a single project story",
                "Field-leadership coaching / write-ups surface friction early",
                "Equipment assignments per crew are visible across the project",
                "Incident escalation engages PM the same day for severe events",
            ]},
            {"type": "why", "text":
                "Without shared records, coordination depends on memory and phone calls — "
                "both of which fail when something is being disputed. With shared records, "
                "the conversation starts from a common baseline."},
        ],
        "related": ["pm-project-review-cadence", "field-incident-escalation", "role-pm"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 3 · ADMIN PORTAL DEEP CONTENT (iter193 · preview only)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "admin-user-management",
        "section": "portals",
        "title": "Admin · User Management",
        "summary": "Create, disable, transfer, reset — the directory's day-to-day.",
        "scopes": ["admin"],
        "tags": ["admin", "user", "directory", "access"],
        "body": [
            {"type": "p", "text":
                "User management is the daily heart of admin work. Most of it is creating "
                "and disabling accounts, resetting passwords, and assigning role templates. "
                "Each one is small; the discipline is in doing it consistently."},
            {"type": "steps", "items": [
                "Create: enter email + portal(s) + role template; set must_change_password=true",
                "Disable (preferred over delete): preserves audit history",
                "Reset password: admin-issued temp credential, force change on next login",
                "Convert mirrored → managed (K4b, when wired): explicit password handoff",
            ]},
            {"type": "why", "text":
                "User management is the platform's access perimeter. A disabled-not-deleted "
                "account preserves the audit chain; a forced password change at first login "
                "preserves the secret. Both small disciplines add up to the platform's "
                "answer when access is later questioned."},
            {"type": "warn", "text":
                "Never delete an account that has audit history — disable it. Deleting "
                "breaks every audit-trail reference that points to that user. Disable "
                "preserves history; delete erases the chain of custody."},
            {"type": "next", "items": [
                "Created users appear in the directory on next page load",
                "Disabled accounts stop working immediately on next request",
                "Audit log records every create / disable / password-reset action",
            ]},
        ],
        "related": ["admin-audit-forensics", "admin-role-templates", "admin-governance-why",
                    "role-admin"],
    },
    {
        "id": "admin-audit-forensics",
        "section": "portals",
        "title": "Admin · Audit Trail Forensics",
        "summary": "Reading the audit log to reconstruct what actually happened.",
        "scopes": ["admin"],
        "tags": ["admin", "audit", "forensics", "investigation"],
        "body": [
            {"type": "p", "text":
                "The audit log is the platform's memory. When a question comes up — 'who "
                "disabled that account?', 'who exported the backup?', 'when did this "
                "permission change?' — the audit log is where you get a defensible answer."},
            {"type": "bullets", "items": [
                "Login / logout events with IP",
                "Account create / disable / password reset",
                "Backup downloads (chain-of-custody)",
                "Permission and role-template changes",
                "Sensitive admin actions (denials logged for step-up enforcement)",
            ]},
            {"type": "steps", "items": [
                "Filter by actor (email) or by action type",
                "Narrow by time window",
                "Read the chain end-to-end before concluding — single rows can mislead",
                "Export the relevant rows for the investigation record",
            ]},
            {"type": "why", "text":
                "The audit log is the answer to questions of trust. Without it, every "
                "dispute is one person's recollection against another. With it, the system "
                "speaks for itself."},
        ],
        "related": ["why-audit-logs", "admin-user-management", "admin-governance-why",
                    "role-admin"],
    },
    {
        "id": "admin-system-health",
        "section": "portals",
        "title": "Admin · System Health & Sessions",
        "summary": "What 'healthy' looks like and how to spot when it isn't.",
        "scopes": ["admin"],
        "tags": ["admin", "system health", "sessions", "operations"],
        "body": [
            {"type": "p", "text":
                "Admin → System exposes the platform's vital signs: Mongo health, scheduler, "
                "recent backups, active sessions. Most of the time this page is boring — "
                "that's the point. Pay attention when it isn't."},
            {"type": "bullets", "items": [
                "Mongo + scheduler = both green at all times",
                "Backup recency: most-recent backup timestamp must be within the auto-cadence",
                "Last 5 Sessions panel: spot stale or anomalous active sessions",
                "/api/health/full: deep-health probe (used by UptimeRobot)",
            ]},
            {"type": "why", "text":
                "Boring is the goal. Most days the system-health page tells you nothing new. "
                "The discipline is in checking it anyway — because the day it has something "
                "to say, you want to learn about it from this page and not from a user."},
            {"type": "next", "items": [
                "Backup-recency miss → check the scheduler log; usually transient",
                "Session anomaly → cross-check with audit log",
            ]},
        ],
        "related": ["admin-backup-restore", "admin-sentry-observability", "role-admin"],
    },
    {
        "id": "admin-backup-restore",
        "section": "portals",
        "title": "Admin · Backups & Restore Posture",
        "summary": "What backs up, when, where it lives, and proving it works.",
        "scopes": ["admin"],
        "tags": ["admin", "backup", "restore", "r2", "drill"],
        "body": [
            {"type": "p", "text":
                "MASCI keeps two parallel preservation systems: technical backups (used to "
                "restore the live database) and human-readable exports (used to read records "
                "outside the platform). A backup that's never been restored isn't yet a "
                "backup — it's an assumption."},
            {"type": "bullets", "items": [
                "Hourly + nightly snapshots → Cloudflare R2 → 90-day lifecycle expiration",
                "Side-DB restore drill: validates a backup can actually be read into Mongo",
                "Quarterly drill cadence; logged in `RESTORE_DRILL.md`",
                "Human-readable export: separate tool, storage-neutral, on-demand",
            ]},
            {"type": "why", "text":
                "A backup that's never been restored is an assumption, not a backup. "
                "The drill cadence converts that assumption into a verified capability — "
                "and the side-DB target ensures verification never risks the live database."},
            {"type": "warn", "text":
                "Never restore a backup over the live DB. The restore-drill script refuses "
                "any target_db that doesn't start with `masci_restore_drill_`. That refusal "
                "is intentional."},
            {"type": "next", "items": [
                "Drill failure = backup is suspect; investigate immediately",
                "Drill success = drill row appended to the runbook",
                "Restore decisions over live data engage Admin + insurance / legal as appropriate",
            ]},
        ],
        "related": ["why-backups", "admin-data-portability", "admin-governance-why",
                    "role-admin"],
    },
    {
        "id": "admin-data-portability",
        "section": "portals",
        "title": "Admin · Data Portability & Human-Readable Exports",
        "summary": "When customers, auditors, or attorneys need readable records.",
        "scopes": ["admin"],
        "tags": ["admin", "export", "portability", "audit"],
        "body": [
            {"type": "p", "text":
                "Human-readable exports turn the database into something a non-technical "
                "reader can open. Used for customer leave-the-platform scenarios, auditor / "
                "attorney requests, or just internal record-pulls."},
            {"type": "bullets", "items": [
                "Per-record PDF (platform layout where available, fallback elsewhere)",
                "Per-record CSV / JSON / RAW",
                "Photos resolved offline (no R2 dependency at read time)",
                "Manifest + verification report included in every export"
            ]},
            {"type": "why", "text":
                "Data portability isn't a marketing feature — it's an operational "
                "obligation. When a customer, auditor, or attorney needs records, "
                "human-readable exports are the answer that doesn't require a developer "
                "or a platform login."},
            {"type": "tip", "text":
                "Exports are storage-neutral by design. The export tool never auto-uploads "
                "to R2 — that decision belongs to whoever runs the export, for the case "
                "they're running it for."},
            {"type": "next", "items": [
                "Export audit-logged with actor, scope, timestamp",
                "Output zip / folder delivered through the chosen channel (manual, by design)",
            ]},
        ],
        "related": ["admin-backup-restore", "why-backups", "role-admin"],
    },
    {
        "id": "admin-sentry-observability",
        "section": "portals",
        "title": "Admin · Sentry & Observability Posture",
        "summary": "Errors, releases, and PII discipline.",
        "scopes": ["admin"],
        "tags": ["admin", "sentry", "observability", "errors"],
        "body": [
            {"type": "p", "text":
                "Sentry is active in preview and production for backend and frontend. Its "
                "job is to surface errors the team didn't see — silently failing requests, "
                "broken frontends in environments not actively being used."},
            {"type": "bullets", "items": [
                "Release identifier = source hash (BE + FE share the same release tag)",
                "PII scrubber strips password*/token*/secret*/api_key* + auth headers + hex blobs",
                "Auto-session-tracking enabled for release-health",
                "Init is no-op if DSN is unset — app safe without Sentry configured",
            ]},
            {"type": "why", "text":
                "Most production bugs aren't reported by users — they're silent failures "
                "the team doesn't know to look for. Sentry's job is to surface those "
                "automatically, with enough release context to know which deploy introduced "
                "them and which one fixed them."},
            {"type": "warn", "text":
                "Do NOT log raw request bodies or response payloads to Sentry. The scrubber "
                "catches common keys; assume any non-scrubbed surface is logged in clear."},
            {"type": "next", "items": [
                "New errors surface in Sentry issues — triage same-day",
                "Release health drops after a deploy → roll back fast, investigate after",
            ]},
        ],
        "related": ["admin-system-health", "admin-governance-why", "role-admin"],
    },
    {
        "id": "admin-role-templates",
        "section": "portals",
        "title": "Admin · Role Templates",
        "summary": "Why templates exist, how to assign them, and what's still hand-rolled.",
        "scopes": ["admin"],
        "tags": ["admin", "role template", "rbac", "permissions"],
        "body": [
            {"type": "p", "text":
                "Role templates capture the standard permissions for each portal-role "
                "combination (HR Manager, Mechanic, Foreman, Superintendent, etc.). They "
                "exist so every account doesn't have to be permissioned from scratch."},
            {"type": "bullets", "items": [
                "31 built-in templates across all 7 portals (Phase K3)",
                "Hierarchy supported (PM Read-Only ⊆ Coordinator ⊆ PM)",
                "Custom templates survive system-seed (system != True flag)",
                "Enforcement is deferred to Phase K6 — templates exist, are surfaced read-only today",
            ]},
            {"type": "why", "text":
                "Role templates are the staging ground for replacing scattered "
                "`role == \"...\"` checks with a single permission catalog. Surfacing them "
                "read-only first lets the team verify the catalog before flipping the "
                "enforcement gate — a deliberate slow rollout to avoid breaking valid users."},
            {"type": "warn", "text":
                "Today, role templates are visible in the Unified Directory but are not "
                "yet enforced by the auth gates. Routes still use per-portal token checks. "
                "The enforcement cutover is staged (Phase K6) and intentionally gradual."},
        ],
        "related": ["admin-user-management", "admin-governance-why", "role-admin"],
    },
    {
        "id": "admin-governance-why",
        "section": "knowledge",
        "title": "Admin · Why Controls & Restrictions Exist",
        "summary": "The reasoning behind RBAC, audit, lockouts, and rate limits.",
        "scopes": ["admin"],
        "tags": ["admin", "governance", "rbac", "security", "why"],
        "body": [
            {"type": "p", "text":
                "Admin controls aren't a tax on speed — they're how the platform survives "
                "the eventual day something goes wrong. Each control answers a specific "
                "real-world risk."},
            {"type": "bullets", "items": [
                "RBAC: prevents one portal's mistake from spreading across other portals",
                "Audit log: answers 'who did what' when a record is disputed",
                "Session timeouts: limit the cost of a lost / unattended device",
                "Rate limits: prevent a single buggy client (or attacker) from overwhelming the API",
                "Backup + restore drill: ensures recovery is possible when needed",
                "Step-up auth (when enabled): re-confirms identity for sensitive actions",
            ]},
            {"type": "why", "text":
                "Each control is small; together they form the difference between a "
                "platform that holds up under real-world friction and one that quietly "
                "fails when it matters. None of them are paranoia — all of them are "
                "responses to events that have happened to other platforms."},
        ],
        "related": ["admin-audit-forensics", "admin-user-management",
                    "admin-backup-restore", "why-session-timeouts", "role-admin"],
    },

    # ═════════════════════════════════════════════════════════════════
    # PHASE B ITER 3 · CROSS-WORKFLOW CONNECTIONS (iter193)
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "connect-pm-field-review",
        "section": "knowledge",
        "title": "How Field Reports Reach PM Review",
        "summary": "Field submit → PM scope → review → action.",
        "scopes": ["field", "leadership", "pm", "admin"],
        "tags": ["workflow", "field", "pm", "review", "connection"],
        "body": [
            {"type": "p", "text":
                "A field report doesn't just sit in the field's record store. It surfaces "
                "automatically to the PMs assigned to the project, who use it as their "
                "early-warning system."},
            {"type": "steps", "items": [
                "Supervisor submits a daily report / inspection / incident with the correct project",
                "Record enters PM's project-scoped view on next page load",
                "PM reviews in their cadence (daily / weekly / monthly)",
                "Issues become follow-ups; severe items escalate same-day",
                "Audit trail records who reviewed what, when",
            ]},
            {"type": "why", "text":
                "Without this loop, the PM only learns about field issues when they "
                "escalate verbally. With it, the PM has a chance to catch a small issue "
                "while it's still small — which is also when it's cheapest to fix."},
            {"type": "tip", "text":
                "Wrong project on the field record = record never reaches PM review. Of "
                "all the data-quality issues in the system, this is the highest-cost one "
                "to leave uncorrected."},
        ],
        "related": ["pm-project-review-cadence", "pm-labor-documentation",
                    "connect-field-to-payroll", "field-daily-report-howto"],
    },
    {
        "id": "connect-admin-controls",
        "section": "knowledge",
        "title": "How Admin Controls Protect Each Portal",
        "summary": "RBAC, audit, session boundaries — what each portal inherits.",
        "scopes": ["admin"],
        "tags": ["workflow", "admin", "rbac", "audit", "connection"],
        "body": [
            {"type": "p", "text":
                "Each portal benefits from admin-level controls it doesn't see directly. "
                "Understanding the inherited posture helps when designing new features or "
                "deciding whether a request requires step-up."},
            {"type": "bullets", "items": [
                "Every portal inherits the audit log (login, logout, sensitive actions)",
                "Every portal inherits session timeouts (tier-specific)",
                "Every portal inherits rate limits on public POST surfaces",
                "Every portal inherits scope-based RBAC at the API gate",
                "Step-up auth (env-gated) applies to admin-sensitive mutations only",
            ]},
            {"type": "why", "text":
                "The admin controls aren't admin-only protections — they're platform-level "
                "protections that make every portal safer. The portals don't have to "
                "implement these themselves; admin owns the posture for all of them."},
        ],
        "related": ["admin-governance-why", "admin-audit-forensics",
                    "why-session-timeouts", "why-audit-logs"],
    },

    # ═════════════════════════════════════════════════════════════════
    # ITER205 · TIERED GUIDANCE RBAC · PUBLIC IDENTITY ARTICLES
    # ─────────────────────────────────────────────────────────────────
    # Operator directive (iter205-correction): public identity articles
    # must be STRICTLY LIMITED to:
    #   • what this portal is (one paragraph)
    #   • who uses it (one line)
    #   • basic purpose / why it exists (one sentence)
    #   • how to access it (sign-in URL)
    #   • pointer to login-troubleshooting (public)
    # They MUST NOT expose:
    #   • internal workflows
    #   • HR procedures
    #   • admin operations
    #   • dispatch logic
    #   • PM management details
    #   • protected training / SOPs
    # Anyone wanting workflow-level depth must sign in to the matching
    # portal-scoped article (404'd to anonymous — no title leak).
    # ═════════════════════════════════════════════════════════════════
    {
        "id": "portal-hr-identity",
        "section": "portals",
        "title": "HR Portal — Overview",
        "summary": "What HR is for and how to access it. Operational HR training requires HR sign-in.",
        "scopes": ["public"],
        "tags": ["hr", "identity", "portal"],
        "body": [
            {"type": "p", "text":
                "The HR portal is MASCI's people-and-time portal. It exists so HR staff have "
                "one place to manage employee records and time."},
            {"type": "p", "text":
                "Who uses it: HR staff and HR managers."},
            {"type": "p", "text":
                "How to access it: sign in at /hr/login with the email and password issued to "
                "you by an admin. If you do not have an account, contact your operator."},
            {"type": "warn", "text":
                "Operational HR training (procedures, workflows, internal SOPs) is restricted "
                "to HR staff. The public Guidance Center does not surface those articles. If "
                "you are HR staff, sign in to read them. If you are not, this material is "
                "intentionally not visible to you."},
        ],
        "related": [
            "public-cant-login",
        ],
    },
    {
        "id": "portal-safety-identity",
        "section": "portals",
        "title": "Safety Portal — Overview",
        "summary": "What the Safety Portal is for and how to access it. Operational Safety training requires Safety sign-in.",
        "scopes": ["public"],
        "tags": ["safety", "identity", "portal"],
        "body": [
            {"type": "p", "text":
                "The Safety Portal is the system Safety staff use to manage compliance, "
                "incidents, and audits at MASCI."},
            {"type": "p", "text":
                "Who uses it: Safety Managers, Coordinators, and Officers."},
            {"type": "p", "text":
                "How to access it: sign in at /safety-portal/login with the email and password "
                "issued to you by an admin. If you do not have an account, contact your operator."},
            {"type": "warn", "text":
                "Operational Safety training (procedures, workflows, internal SOPs) is "
                "restricted to Safety staff. Field crews can read basic safety guidance "
                "(public) elsewhere in the Guidance Center. Workflow-level Safety content is "
                "not visible to anonymous users."},
            {"type": "next", "items": [
                "If you're field crew — read 'If something happens on a job site' (public)",
                "If you can't sign in — read 'Can't sign in?' (public)",
            ]},
        ],
        "related": [
            "public-incident-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "portal-shop-identity",
        "section": "portals",
        "title": "Shop / Fleet Portal — Overview",
        "summary": "What the Shop Portal is for and how to access it. Operational Shop training requires Shop sign-in.",
        "scopes": ["public"],
        "tags": ["shop", "fleet", "identity", "portal"],
        "body": [
            {"type": "p", "text":
                "The Shop / Fleet Portal is the system Shop staff use to keep MASCI's fleet "
                "running. It exists so mechanics and fleet coordinators have a single place "
                "to manage equipment health."},
            {"type": "p", "text":
                "Who uses it: Mechanics, Shop Foreman, and Fleet Coordinator."},
            {"type": "p", "text":
                "How to access it: sign in at /shop/login with the email and password issued "
                "to you by an admin. If you do not have an account, contact your operator."},
            {"type": "warn", "text":
                "Operational Shop training (procedures, workflows, internal SOPs) is "
                "restricted to Shop staff. Field operators can read 'Equipment Pre-Op Checks "
                "(Field Basics)' (public) for the field-side surface. Workflow-level Shop "
                "content is not visible to anonymous users."},
            {"type": "next", "items": [
                "If you're a field operator — read 'Equipment Pre-Op Checks (Field Basics)' (public)",
                "If you can't sign in — read 'Can't sign in?' (public)",
            ]},
        ],
        "related": [
            "public-preop-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "portal-dispatch-identity",
        "section": "portals",
        "title": "Dispatch Portal — Overview",
        "summary": "What the Dispatch Portal is for and how to access it. Operational Dispatch training requires Dispatch sign-in.",
        "scopes": ["public"],
        "tags": ["dispatch", "identity", "portal"],
        "body": [
            {"type": "p", "text":
                "The Dispatch Portal is the system Dispatch staff use to coordinate equipment "
                "across MASCI projects. It exists so dispatchers and fleet coordinators have "
                "a single place to know where assets are."},
            {"type": "p", "text":
                "Who uses it: Dispatchers, Fleet Coordinators, and Operations Oversight."},
            {"type": "p", "text":
                "How to access it: sign in at /dispatch-portal/login with the email and "
                "password issued to you by an admin. If you do not have an account, contact "
                "your operator."},
            {"type": "warn", "text":
                "Operational Dispatch training (procedures, workflows, internal SOPs) is "
                "restricted to Dispatch staff. Workflow-level Dispatch content is not visible "
                "to anonymous users."},
            {"type": "next", "items": [
                "If you can't sign in — read 'Can't sign in?' (public)",
            ]},
        ],
        "related": [
            "public-cant-login",
        ],
    },
    {
        "id": "portal-pm-identity",
        "section": "portals",
        "title": "PM Portal — Overview",
        "summary": "What the PM Portal is for and how to access it. Operational PM training requires PM sign-in.",
        "scopes": ["public"],
        "tags": ["pm", "identity", "portal", "project manager"],
        "body": [
            {"type": "p", "text":
                "The PM (Project Management) Portal is the system Project Managers use to "
                "oversee their assigned projects. It exists so each PM has a single place "
                "scoped to the projects they manage."},
            {"type": "p", "text":
                "Who uses it: Project Managers and Co-PMs."},
            {"type": "p", "text":
                "How to access it: sign in at /pm/login with the email and password issued to "
                "you by an admin. If you do not have an account, contact your operator."},
            {"type": "warn", "text":
                "Operational PM training (procedures, workflows, internal SOPs) is restricted "
                "to PMs. Field crews can read public guidance on Daily Reports. Workflow-level "
                "PM management content is not visible to anonymous users."},
            {"type": "next", "items": [
                "If you're field crew — read 'Daily Report Basics' (public)",
                "If you can't sign in — read 'Can't sign in?' (public)",
            ]},
        ],
        "related": [
            "public-daily-report-basics",
            "public-cant-login",
        ],
    },
    {
        "id": "portal-admin-identity",
        "section": "portals",
        "title": "Admin Console — Overview",
        "summary": "What the Admin Console is for and how to access it. Operational Admin training is admin-only.",
        "scopes": ["public"],
        "tags": ["admin", "identity", "console", "operator"],
        "body": [
            {"type": "p", "text":
                "The Admin Console is the operator-level control surface of the platform. It "
                "exists so the platform owner and trusted operators have one place to administer "
                "the system."},
            {"type": "p", "text":
                "Who uses it: the platform Owner and designated Operator(s). Not for general staff."},
            {"type": "p", "text":
                "How to access it: sign in at /admin/login. Admin accounts are issued by the "
                "platform Owner directly."},
            {"type": "warn", "text":
                "Operational Admin training is the most-restricted tier on the platform. Its "
                "procedures, workflows, and internal SOPs are deliberately not surfaced to "
                "anonymous users. If you don't have an admin account, this material is "
                "intentionally not for you — that's by design."},
            {"type": "next", "items": [
                "If you need an admin to take an action — contact your operator directly",
                "If you can't sign in — read 'Can't sign in?' (public)",
            ]},
        ],
        "related": [
            "public-cant-login",
        ],
    },

    # ─────────────────────────────────────────────────────────────────
    # FLEET / TRUCKING DVIR · iter251 · Phase 1-5 integration
    # ─────────────────────────────────────────────────────────────────
    # Operator directive (2026-05-19): connect Fleet operational
    # workflows into the Operations Guidance Center. Tone: experienced
    # transportation/fleet leadership coaching crews — NOT a compliance
    # vendor product. Short, operational, field-readable. No LMS drift.
    {
        "id": "fleet-daily-dvir",
        "section": "quickhelp",
        "title": "Daily Driver Vehicle Inspection (DVIR)",
        "summary": "Walk the truck before you roll. PASS / FAIL / N/A each item. The system handles severity.",
        "scopes": ["public", "field", "leadership", "shop", "dispatch", "safety", "admin"],
        "tags": ["fleet", "dvir", "driver", "truck", "trailer", "pre-trip"],
        "body": [
            {"type": "p", "text":
                "The Daily DVIR is the driver's pre-trip walk-around. It exists so the driver, "
                "Shop, and Dispatch are working from the same picture of the truck before it leaves "
                "the yard. It is not paperwork — it is the moment the driver says 'this is what I see' "
                "and the Shop hears it the same minute."},
            {"type": "steps", "items": [
                "Open Field · tap 'Trucking · Daily DVIR'",
                "Type or pick your name · roster autocompletes after your first inspection",
                "Pick your truck unit · plate / VIN / odometer / hour meter prefill",
                "Walk the truck — front, driver side, rear, passenger side. Mark each item PASS, FAIL, or N/A",
                "If you have a trailer, tap 'Add trailer' and walk that too",
                "Anything you marked FAIL needs a short note (10+ characters) and a photo if you have one",
                "Sign and submit",
            ]},
            {"type": "why", "text":
                "An honest DVIR keeps the crew safe and keeps the truck on the road. A real defect "
                "caught at 6:30 a.m. is a Shop ticket. The same defect caught at 50 mph is a tow bill, "
                "a lost day, or worse."},
            {"type": "next", "items": [
                "Shop sees your defects grouped by truck within seconds",
                "Severity is set automatically — drivers don't classify · the system does",
                "If anything is Out of Service, Dispatch reassigns the load",
                "If it's a Monitor item, Shop schedules a repair window",
                "Your name stays on the inspection · accountability, not blame",
            ]},
            {"type": "mistakes", "items": [
                "Marking N/A on items the truck actually has (axle without spare, missing triangle)",
                "Skipping the trailer walk-around when pulling one",
                "FAIL with no note · Shop can't act on 'something is wrong'",
                "Holding the inspection until you're already on the road",
            ]},
            {"type": "tip", "text":
                "Use the 'Why this matters' tip inside the form for each section — short coaching, no "
                "compliance language."},
        ],
        "related": ["fleet-severity-oos-vs-monitor", "fleet-repair-lifecycle", "portal-shop"],
    },
    {
        "id": "fleet-weekly-lead",
        "section": "quickhelp",
        "title": "Weekly Lead Inspection",
        "summary": "Lead-driver / fleet-lead / superintendent quick weekly review. High-signal items only.",
        "scopes": ["public", "field", "leadership", "shop", "dispatch", "safety", "admin"],
        "tags": ["fleet", "weekly", "lead", "superintendent", "fleet-lead"],
        "body": [
            {"type": "p", "text":
                "The Weekly Lead is a quick second-set-of-eyes pass by a lead driver, fleet lead, or "
                "superintendent. It's not a re-do of the daily DVIR. It's the operational hygiene "
                "check — recurring complaints, items the lead wants Shop to look at, the things a "
                "driver who runs the same truck every day stops noticing."},
            {"type": "steps", "items": [
                "Open Field · tap 'Weekly · Lead Inspection'",
                "Pick the truck and enter your name as the lead inspector",
                "Walk it · 9 high-signal items (brakes, mirrors, lights, fluids, seat belts, emergency kit, fire extinguisher, triangles, body / paint)",
                "Sign and submit",
            ]},
            {"type": "why", "text":
                "Leads see patterns drivers miss because they swap trucks. A weekly lead pass catches "
                "the slow leak, the gradual mirror crack, the door seal that's been letting in dust "
                "for three weeks. Small problems · before they become OOS."},
            {"type": "next", "items": [
                "Defects route through the same Shop queue as the daily DVIR",
                "Severity governance is identical · OOS / Monitor decided by the system",
                "Shop sees the lead's note alongside the driver's note from the same morning",
            ]},
            {"type": "mistakes", "items": [
                "Treating the weekly lead as a 'gotcha' on the driver — it's a partnership",
                "Skipping the week because 'nothing's changed'",
                "Reusing last week's signature instead of signing fresh",
            ]},
        ],
        "related": ["fleet-daily-dvir", "fleet-severity-oos-vs-monitor", "fleet-repair-lifecycle"],
    },
    {
        "id": "fleet-weekly-emergency",
        "section": "quickhelp",
        "title": "Weekly Emergency Equipment Check",
        "summary": "Fire extinguisher · triangles · first aid · PPE · backup alarm. Present · charged · within date.",
        "scopes": ["public", "field", "leadership", "shop", "dispatch", "safety", "admin"],
        "tags": ["fleet", "weekly", "emergency", "fire extinguisher", "triangles", "ppe", "first aid"],
        "body": [
            {"type": "p", "text":
                "The Weekly Emergency Equipment Check is the inspector's confirmation that everything "
                "the truck carries for a roadside emergency is actually there, charged, and not expired. "
                "It's quick — 17 items — and it matters more than its size suggests. The fire "
                "extinguisher you don't notice missing in the yard is the one you reach for at 2 a.m. "
                "in a work zone."},
            {"type": "steps", "items": [
                "Open Field · tap 'Weekly · Emergency Equipment'",
                "Pick the truck",
                "Verify each item: fire extinguisher (charged · sealed · tag current) · reflective triangles · first aid · spill kit · backup alarm · emergency lighting · PPE on board",
                "Mark each PASS / FAIL / N/A",
                "FAIL items need a short note · the item routes to Shop the same way a DVIR defect does",
                "Sign and submit",
            ]},
            {"type": "why", "text":
                "This is one of the few checks where missing equipment automatically classifies as "
                "Out of Service — you can't run a job-site truck without a working extinguisher or "
                "triangles. The check protects the crew, the public, and the company's ability to "
                "respond to an incident professionally."},
            {"type": "next", "items": [
                "Failed items appear in the Shop queue with the right severity already attached",
                "Dispatch sees the unit's status update instantly",
                "Safety can review the audit trail for any DOT or work-zone documentation"
            ]},
            {"type": "mistakes", "items": [
                "Marking 'present' without actually checking the extinguisher tag date",
                "Skipping the spill kit on a truck that hauls hydraulic equipment",
                "Treating an expired tag as a Monitor — system will classify correctly automatically",
            ]},
        ],
        "related": ["fleet-daily-dvir", "fleet-severity-oos-vs-monitor", "fleet-repair-lifecycle"],
    },
    {
        "id": "fleet-severity-oos-vs-monitor",
        "section": "knowledge",
        "title": "Out of Service vs Monitor · how severity works",
        "summary": "Drivers do not assign severity. The system does. Honest reporting is what matters.",
        "scopes": ["public", "field", "leadership", "shop", "dispatch", "safety", "admin"],
        "tags": ["fleet", "severity", "oos", "monitor", "governance", "fmcsa", "dot"],
        "body": [
            {"type": "p", "text":
                "Every defect on a DVIR, Weekly Lead, or Emergency Equipment check is automatically "
                "classified as either Out of Service or Monitor. Drivers and inspectors don't make "
                "that call — they just report what they saw. The classification comes from a fixed "
                "severity table reviewed against FMCSA and DOT commercial-vehicle baselines and "
                "approved by operations leadership."},
            {"type": "p", "text":
                "Out of Service means the truck does not roll until Shop verifies the repair and "
                "Dispatch confirms Return-to-Service. Monitor means the truck is safe to operate but "
                "Shop owns the repair on a planned cadence — no rush, no panic, but it is being tracked."},
            {"type": "why", "text":
                "Separating reporting from severity is intentional. It removes the pressure on a "
                "driver to under-report ('it's probably fine') or over-report ('better safe…') and it "
                "removes the temptation for anyone in the chain to argue severity after the fact. The "
                "driver reports. The system classifies. The Shop acts."},
            {"type": "bullets", "items": [
                "Drivers and leads · honest reporting · short note · photo if you have one",
                "System · severity based on the item and the description · published table",
                "Shop · sees the truck grouped by unit · driver note + photo + severity in one place",
                "Dispatch · sees availability (OOS / Repair-in-progress / Available)",
                "Safety · reads the audit trail · repair record · regulatory ref where applicable",
            ]},
            {"type": "tip", "text":
                "Monitor is not punishment. Monitor is 'we know about it · it's tracked · it's "
                "scheduled.' A truck with three Monitor items can roll all day. A truck with one OOS "
                "item parks until Shop says otherwise."},
            {"type": "mistakes", "items": [
                "Calling a defect Monitor 'because we need the truck today' · the system classifies, not the operator",
                "Hiding a defect to avoid an OOS · puts the crew at risk and shows up later as a bigger repair",
                "Arguing severity with Shop · severity is a published table · the conversation is about the repair, not the classification",
            ]},
        ],
        "related": ["fleet-daily-dvir", "fleet-repair-lifecycle", "fleet-return-to-service"],
    },
    {
        "id": "fleet-repair-lifecycle",
        "section": "quickhelp",
        "title": "Fleet Repair Lifecycle · Shop · Dispatch · Safety",
        "summary": "Defect → Shop acknowledged → Repaired → Dispatch Return-to-Service. One trail · three scopes.",
        "scopes": ["public", "field", "leadership", "shop", "dispatch", "safety", "admin"],
        "tags": ["fleet", "repair", "lifecycle", "shop", "dispatch", "safety", "rts"],
        "body": [
            {"type": "p", "text":
                "Every Fleet defect — DVIR, Weekly Lead, or Weekly Emergency — flows through the same "
                "four-step lifecycle. Shop, Dispatch, and Safety see the same record at every step, "
                "scoped to what each role actually does."},
            {"type": "steps", "items": [
                "Open · the defect is fresh from the driver/inspector. Shop sees it in the unit's queue.",
                "Shop acknowledged · the mechanic opened the card. Optional — most shops skip this and go straight to repair.",
                "Repaired · Shop logged the repair drawer (mechanic name · repair notes · photos if applicable · timestamp).",
                "Returned to service · Dispatch confirmed the unit is safe to roll. Intentional · checkbox-confirmed.",
            ]},
            {"type": "why", "text":
                "The four steps are deliberate. Shop owns the wrench. Dispatch owns the operational "
                "decision to put the truck back in rotation. Safety reads the trail. No one person "
                "closes the loop alone."},
            {"type": "bullets", "items": [
                "Shop · uses the driver's note and photo to know exactly what to look at",
                "Dispatch · sees Available / OOS / Repair-in-progress without scanning a list",
                "Safety · reads the full audit trail · who · when · what changed · before/after status",
            ]},
            {"type": "next", "items": [
                "After Shop marks repaired · unit status becomes 'Repair in progress' (awaiting RTS)",
                "Dispatch sees the unit on their visibility page with a 'Return to Service' button",
                "After RTS · unit status returns to Available · audit log stamped with both names",
            ]},
            {"type": "mistakes", "items": [
                "Shop marks repaired but Dispatch never confirms — unit sits in 'awaiting RTS' indefinitely",
                "Repair note shorter than 'replaced part' — Safety has no record of what was inspected",
                "Skipping the Shop drawer and editing the defect directly · breaks the audit trail",
            ]},
        ],
        "related": ["fleet-daily-dvir", "fleet-severity-oos-vs-monitor", "fleet-return-to-service", "portal-shop"],
    },
    {
        "id": "fleet-return-to-service",
        "section": "quickhelp",
        "title": "Return-to-Service · Dispatch confirmation",
        "summary": "Shop fixed the truck. Dispatch confirms it can roll. Intentional · timestamped · audit-logged.",
        "scopes": ["public", "field", "leadership", "shop", "dispatch", "safety", "admin"],
        "tags": ["fleet", "rts", "return to service", "dispatch", "repair"],
        "body": [
            {"type": "p", "text":
                "Return-to-Service is the moment Dispatch tells the system 'this truck is back in "
                "rotation.' It happens only after Shop has logged a repair · never automatically · "
                "never as a side effect of closing something else."},
            {"type": "steps", "items": [
                "Open the Fleet view from the Dispatch portal",
                "Find the unit · it shows 'Awaiting RTS' alongside the Shop's repair record",
                "Tap 'Return to Service' on the defect",
                "Review the Shop repair note (and photos, if Shop attached any)",
                "Enter your name · add an optional Dispatch note",
                "Check the confirmation box — 'I have reviewed the Shop repair record and confirm this unit is safe to return to service'",
                "Tap Return to Service",
            ]},
            {"type": "why", "text":
                "The Shop owns the wrench but Dispatch owns the operational decision. Dispatch is the "
                "role that knows whether the load is realistic, whether the route makes sense for a "
                "freshly repaired unit, and whether anyone needs a heads-up. The intentional checkbox "
                "is not red tape · it is the moment the platform records that a human made a decision, "
                "not that a button got tapped on the way to somewhere else."},
            {"type": "next", "items": [
                "Unit status flips to Available · drivers can pick it up",
                "Audit log captures: who · when · status_before · status_after · Shop note · Dispatch note",
                "Safety can read the full trail · DVIR → Shop repair → Dispatch RTS",
            ]},
            {"type": "mistakes", "items": [
                "Confirming RTS without reading the Shop note · you lose the operational context",
                "Skipping the confirmation note when something is unusual · brief context helps Safety later",
                "Trying to RTS a unit Shop hasn't repaired yet · system blocks this · for good reason",
            ]},
        ],
        "related": ["fleet-repair-lifecycle", "fleet-severity-oos-vs-monitor", "fleet-daily-dvir"],
    },
    # ─────────────────────────────────────────────────────────────────
    # iter414 · Phase 18 · DLS operational unification — Help-Search closure
    # ─────────────────────────────────────────────────────────────────
    # Operator directive: every new DLS surface introduced by Phase 14-17
    # must be reachable through Help Search in BOTH EN and ES. Without
    # these articles, a Spanish-preferring dispatcher / driver typing
    # "cisterna" or "movimiento de equipo" finds nothing — a real
    # operational dead-end. Seven articles, each ≤6 blocks, calm voice.
    # ES translations live in guidance/translations_es_iter414.py.
    {
        "id": "dls-driver-shift-start",
        "section": "trucking",
        "title": "DLS · Driver Shift Start (QR Sticker → /shift)",
        "summary": "How a truck driver self-starts a shift in seconds — no password, no app, no enrollment.",
        "scopes": ["dispatch", "admin", "leadership", "field", "hr", "shop", "public"],
        "tags": ["dls", "shift", "qr", "driver", "self-start", "shift-start", "magic-link"],
        "body": [
            {"type": "p", "text":
                "Every truck cab carries a printed QR sticker. The driver scans it with their phone "
                "camera, lands on /shift, picks their name + the truck + (optionally) trailer and "
                "carrier, taps START SHIFT, and they are operationally live. No password, no app, "
                "no enrollment. The platform follows the truck, not the user account."},
            {"type": "steps", "items": [
                "Driver opens phone camera and scans the sticker on the truck door",
                "Phone opens /shift in the browser — already on the right tenant",
                "Driver picks their name (or types it if they're a sub), picks the truck, optional trailer + carrier",
                "Driver taps START SHIFT",
                "Truck appears on the dispatch board · driver can now receive lifecycle taps",
            ]},
            {"type": "why", "text":
                "Truck identity is the operational continuity key, not the user account. The "
                "platform must not require enterprise auth from a driver who's about to wear "
                "gloves. The QR is the physical bridge from a parked truck to live operations."},
            {"type": "next", "items": [
                "Drive the assignment — tap ENROUTE_TO_LOAD when leaving",
                "If dispatch hasn't issued one yet, the truck simply sits ready",
                "End of day · tap Sign out — leaves the truck clean for the next driver",
            ]},
            {"type": "tip", "text":
                "Admins print the sticker at /admin/dls/shift-qr — one tenant, one URL, one QR. "
                "Stickers go on cab doors. A worn sticker is reprintable in 30 seconds."},
        ],
        "related": ["dls-assignment-issuance", "dls-lifecycle-states", "portal-dispatch"],
    },
    {
        "id": "dls-assignment-issuance",
        "section": "trucking",
        "title": "DLS · Assignment Issuance (Issue Work Drawer)",
        "summary": "How dispatch issues a haul to a truck — Material · Equipment Move · Tanker · Spoils · Support — through one calm drawer.",
        "scopes": ["dispatch", "admin", "leadership"],
        "tags": ["dls", "assignment", "issuance", "drawer", "haul-type", "material", "equipment-move", "tanker", "spoils", "support"],
        "body": [
            {"type": "p", "text":
                "Dispatch opens the Issue Work drawer from the Dispatch Command portal and the "
                "Issue Work section preselects the haul type. The drawer asks for the truck "
                "(required), driver (optional · self-start can claim later), and 4-6 conditional "
                "fields depending on haul type. Submit lands the assignment on the board "
                "immediately."},
            {"type": "bullets", "items": [
                "Material — source / load point · destination · material (catalog dropdown)",
                "Equipment Move — equipment · pickup location · drop-off location",
                "Tanker / Liquid Asphalt — tanker source · destination plant · liquid product (27-item catalog)",
                "Spoils / Dump — uses Material fields with spoils-typical defaults",
                "Support / Misc — minimal fields · free-text in material slot",
            ]},
            {"type": "why", "text":
                "ONE drawer · ONE Dispatch Lifecycle System · five haul types. Lowboys ride the "
                "same DLS as material trucks. Tankers ride the same DLS as lowboys. The platform "
                "is one operational operating system, not five separate dispatch modules."},
            {"type": "next", "items": [
                "Truck appears on the board as ASSIGNED",
                "Driver lifecycle taps drive state forward (ENROUTE → AT_LOAD → ENROUTE_TO_DUMP → COMPLETE)",
                "On COMPLETE, a cycle is materialized · PM tile updates · top materials chips update",
            ]},
            {"type": "tip", "text":
                "Every typed-once 'Add temporary' value (carrier, material, source, destination) "
                "surfaces in the next drawer as a 'history' option. Operational memory feeds itself."},
        ],
        "related": ["dls-driver-shift-start", "dls-haul-types", "dls-lifecycle-states", "dls-operational-attention"],
    },
    {
        "id": "dls-haul-types",
        "section": "trucking",
        "title": "DLS · Five Haul Types (Material · Equipment Move · Tanker · Spoils · Support)",
        "summary": "How the DLS handles every kind of truck work through ONE lifecycle.",
        "scopes": ["dispatch", "admin", "leadership", "pm"],
        "tags": ["dls", "haul-type", "material", "equipment-move", "tanker", "liquid-asphalt", "spoils", "support"],
        "body": [
            {"type": "p", "text":
                "MASCI dispatch handles five haul types through the SAME lifecycle. Same board. "
                "Same governance. Same cycle materialization. No separate portals, no separate "
                "modules — just different conditional fields on the assignment drawer."},
            {"type": "bullets", "items": [
                "Material — asphalt, aggregate, concrete, earthwork, utility, job support (66-item catalog)",
                "Equipment Move — lowboy hauls with pickup/dropoff + equipment master record",
                "Tanker / Liquid Asphalt — 27-product catalog (binders · emulsions · fuel) · 9 terminals · 9 plant destinations",
                "Spoils / Dump — spoils material to a dump destination",
                "Support / Misc — any other operationally valid haul",
            ]},
            {"type": "why", "text":
                "Operations think in trucks moving stuff, not in software modules. Forcing the "
                "system to mirror operational language (instead of forcing operations to mirror "
                "software taxonomy) is what makes this platform feel calm rather than corporate."},
            {"type": "next", "items": [
                "PM tile splits material loads from equipment moves in the count",
                "Health summary surfaces all 5 haul types in `haul_types_today`",
                "Future plant continuity work has `liquid_product` already on the wire",
            ]},
        ],
        "related": ["dls-assignment-issuance", "dls-lifecycle-states", "dls-haul-activity-tile"],
    },
    {
        "id": "dls-lifecycle-states",
        "section": "trucking",
        "title": "DLS · Lifecycle States & Wait Reasons",
        "summary": "ASSIGNED → ENROUTE → AT_LOAD → WAITING → ENROUTE_TO_DUMP → COMPLETE — and what each transition signals downstream.",
        "scopes": ["dispatch", "admin", "leadership", "pm", "shop", "field"],
        "tags": ["dls", "lifecycle", "state-machine", "wait-state", "waiting", "breakdown", "complete"],
        "body": [
            {"type": "p", "text":
                "Every assignment moves through a canonical state machine driven by driver taps. "
                "There is no auto-state — drivers are the sole authors of every transition. This "
                "preserves operational honesty (the platform never invents activity that didn't "
                "happen) and protects against false GPS-driven state changes."},
            {"type": "bullets", "items": [
                "ASSIGNED — issued by dispatch · waiting for driver claim",
                "ENROUTE_TO_LOAD — driver is moving toward the source",
                "AT_LOAD — driver arrived at source",
                "WAITING — driver tapped a canonical wait reason (WAIT_ON_PLANT / WAIT_ON_DUMP / BREAKDOWN / WAITING_OTHER)",
                "ENROUTE_TO_DUMP — driver loaded and rolling to destination",
                "AT_DUMP — driver arrived at destination",
                "COMPLETE — driver finished the haul · cycle materialized",
            ]},
            {"type": "why", "text":
                "Canonical states + canonical wait reasons (not free-text) keep operational data "
                "clean for governance, PM reporting, and post-deploy review. WAIT_ON_PLANT means "
                "the SAME thing every time, in every report, regardless of which driver typed it."},
            {"type": "next", "items": [
                "Governance fires findings on stuck > 30 min or wait > 45 min",
                "Shop sees BREAKDOWN immediately via the cross-portal tile",
                "PM sees waiting_on_plant / waiting_on_dump counts in the haul activity tile",
            ]},
            {"type": "warn", "text":
                "Drivers DO NOT use free-text wait reasons. Free-text destroys operational "
                "intelligence. The WAITING_OTHER picker (deferred until live ops surfaces real "
                "patterns) will be a canonical sub-category list, not a notes box."},
        ],
        "related": ["dls-driver-shift-start", "dls-operational-attention", "dls-haul-activity-tile"],
    },
    {
        "id": "dls-haul-activity-tile",
        "section": "portals",
        "title": "DLS · PM Haul Activity Tile (Production Awareness)",
        "summary": "How PMs see live haul activity for their projects — without becoming a dispatcher.",
        "scopes": ["pm", "admin", "leadership"],
        "tags": ["dls", "pm", "production-awareness", "haul-activity", "tile", "read-only"],
        "body": [
            {"type": "p", "text":
                "The PM Haul Activity tile sits on the PM hub and refreshes every 60 seconds. It "
                "shows production awareness — loads completed today, active hauls, equipment "
                "moves, waits on plant/site, breakdown impacts — scoped to the PM's assigned "
                "projects. It is read-only by design. PMs cannot issue, cancel, or transition."},
            {"type": "bullets", "items": [
                "Loads completed today — split into material loads and equipment moves",
                "Active hauls — anything not yet COMPLETE",
                "Equipment moves active — lowboys in flight to or from a job",
                "Waiting on plant / Waiting on dump — exception counts",
                "Breakdown impacts — trucks down on the PM's projects",
                "Top materials — top-5 by load count today (Equipment Move filtered out)",
            ]},
            {"type": "why", "text":
                "PMs need production-awareness, not dispatch controls. Knowing how much work "
                "completed today and what's waiting is enough — the dispatcher remains the "
                "single decision-maker on every reassignment. This restraint is what keeps "
                "operations from accumulating five overlapping coordinators."},
            {"type": "next", "items": [
                "Tile refreshes every 60 seconds automatically",
                "Empty state explicit: 'Nothing to report — your jobs are quiet right now'",
                "If a breakdown occurs, the tile reflects it within a minute · Shop sees it instantly",
            ]},
        ],
        "related": ["dls-lifecycle-states", "dls-operational-attention", "portal-pm"],
    },
    {
        "id": "dls-operational-attention",
        "section": "portals",
        "title": "DLS · Operational Attention (What Matters NOW)",
        "summary": "The Dispatch Command surface that surfaces stuck trucks, long waits, and breakdowns — without becoming a dashboard.",
        "scopes": ["dispatch", "admin", "leadership"],
        "tags": ["dls", "operational-attention", "governance", "stuck", "breakdown", "wait", "findings", "dispatch"],
        "body": [
            {"type": "p", "text":
                "Operational Attention is the rose-accented section at the top of the Dispatch "
                "Command portal. It reads from /api/dispatch/governance/findings and surfaces "
                "three exception families: breakdowns, trucks stuck more than 30 minutes, and "
                "extended waits. Each card carries action-oriented hint text — not a metric."},
            {"type": "bullets", "items": [
                "Breakdown — Shop sees these too. Decide reassign vs hold.",
                "Stuck > 30 min — driver hasn't tapped in a while. Call them.",
                "Extended wait — plant or dump bottleneck. Reassign or absorb.",
            ]},
            {"type": "why", "text":
                "Calm operations require ONE place where exceptions surface. Dashboards split "
                "attention across charts; Operational Attention concentrates it into 3 cards "
                "with a clear next action. When the cards are empty, dispatch can breathe — "
                "the platform is signalling 'nothing needs your eyes right now'."},
            {"type": "next", "items": [
                "Each card carries an action hint, not a number",
                "Empty state says exactly that — empty",
                "Findings update live via /api/dispatch/governance/findings polling",
            ]},
        ],
        "related": ["dls-lifecycle-states", "dls-health-summary", "portal-dispatch"],
    },
    {
        "id": "dls-health-summary",
        "section": "knowledge",
        "title": "DLS · Day-1 Health Summary (Quiet · Flowing · Attention)",
        "summary": "The read-only admin endpoint that gives operations leadership one calm signal of platform health.",
        "scopes": ["admin"],
        "tags": ["dls", "health-summary", "observability", "day-1", "quiet", "flowing", "attention", "admin"],
        "body": [
            {"type": "p", "text":
                "GET /api/admin/dls/health-summary is the entire Day-1 monitoring story. Three "
                "calm hits — morning, mid-morning, end-of-day — answer 'is the platform healthy?' "
                "Three operational words, no scoring, no charts."},
            {"type": "bullets", "items": [
                "quiet — zero active assignments · zero shifts · zero exceptions",
                "flowing — active work present · no exceptions",
                "attention — breakdown present · OR longest wait ≥ 45 min · OR oldest stuck ≥ 60 min · OR findings > 0",
            ]},
            {"type": "why", "text":
                "Minimum observability beats monitoring suites for operations leadership. A "
                "single endpoint, hit three times a day, is the entire platform-health story "
                "for Day-1. Notes carry up to 3 small operational reasons. There is no KPI, "
                "no scoring, no graph. Just one word and an honest reason."},
            {"type": "next", "items": [
                "Pre-flight (30 min before drivers arrive) — expect status: quiet",
                "Mid-morning (~11 AM) — expect status: flowing · transitions_today > 0",
                "End-of-day — capture completed_cycles_today · transitions_today as closing numbers",
            ]},
            {"type": "tip", "text":
                "File the Day-1 debrief same day at /app/memory/DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md. "
                "Operational memory fades fast — and the debrief is what tells the next iteration "
                "what to actually build versus what to leave alone."},
        ],
        "related": ["dls-operational-attention", "dls-lifecycle-states", "portal-dispatch"],
    },
    # ─────────────────────────────────────────────────────────────────
    # iter417 · Phase 20.0 · Operational Attachments Foundation
    # ─────────────────────────────────────────────────────────────────
    {
        "id": "dls-attachments-load-proof",
        "section": "trucking",
        "title": "DLS · Operational Attachments (Load Proof · Tickets · Photos)",
        "summary": "How operational proof flows with the haul — tickets, BOLs, scale receipts, breakdown photos — without becoming document management.",
        "scopes": ["dispatch", "admin", "leadership", "pm", "shop", "field"],
        "tags": [
            "dls", "attachments", "load-proof", "asphalt-ticket", "scale-ticket",
            "tanker-bol", "bol", "fuel-receipt", "dump-receipt", "delivery-receipt",
            "breakdown-photo", "damage-photo", "load-photo", "operational-proof",
        ],
        "body": [
            {"type": "p", "text":
                "Operational attachments are NOT files. They are operational proof "
                "that travels with the haul itself. A scale ticket attached to a "
                "Material assignment becomes part of that assignment's truth — "
                "downstream consumers (PM, Shop, governance, post-deploy review) "
                "all see the same proof tied to the same operational event."},
            {"type": "bullets", "items": [
                "Asphalt ticket / Scale ticket — material load proof from the plant or scale",
                "Tanker BOL — bill of lading for tanker / liquid asphalt hauls",
                "Fuel receipt / Dump receipt / Delivery receipt — operational proof points",
                "Load photo / Damage photo / Breakdown photo — operational visual continuity",
                "Inspection photo — pre-op or DVIR follow-up visual",
                "Transfer document — equipment-move chain-of-custody",
                "Operational note photo — anything else operations needs to remember",
            ]},
            {"type": "why", "text":
                "Operational truth fades fast in the field — and paper tickets get "
                "lost or damaged. Tying every photo and receipt to the assignment "
                "(not to a folder, not to a project, not to a user account) keeps "
                "the proof permanently glued to the operational truth that created "
                "it. Dispatch, PM, Shop, and governance all read the same proof "
                "from the same assignment record."},
            {"type": "next", "items": [
                "Driver or dispatcher attaches via the assignment context drawer · camera-first",
                "Attachment becomes operational proof for that assignment forever",
                "Mistake recovery: original uploader can delete within 5 minutes · then permanent",
                "Each attachment carries: type · uploader · time · optional operational note",
            ]},
            {"type": "tip", "text":
                "Take photos AT THE LOAD POINT or AT THE DUMP — not from memory in "
                "the truck cab afterwards. The closer the proof is captured to the "
                "operational moment, the more operational truth it carries."},
            {"type": "warn", "text":
                "Attachments are operational proof. Don't use them as a general "
                "photo album · don't attach unrelated company documents · don't "
                "attach personnel records. The 12 canonical types exist to keep "
                "operational truth tight — anything that doesn't fit is doctrine "
                "drift and belongs somewhere else."},
        ],
        "related": [
            "dls-assignment-issuance", "dls-haul-types", "dls-lifecycle-states",
            "dls-driver-shift-start", "portal-dispatch",
        ],
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
            # Filter `related` to only show visible related articles.
            # iter200 polish — include title_es alongside English title
            # so the frontend can render related-link labels in the
            # caller's language with graceful EN fallback.
            allowed_ids = {x["id"] for x in visible_articles(granted_scopes)}
            articles_by_id = {x["id"]: x for x in _ARTICLES}
            out = dict(a)
            out["related"] = [
                {
                    "id": r,
                    "title": (articles_by_id.get(r, {}).get("title") or r),
                    "title_es": articles_by_id.get(r, {}).get("title_es"),
                }
                for r in (a.get("related") or [])
                if r in allowed_ids
            ]
            return out
    return None


def search_articles(query: str, granted_scopes: set[str], limit: int = 25) -> list[dict]:
    """Title + body keyword match, RBAC-aware, no fuzzy (Phase A spec).

    iter414 · Phase 18: include ES title/summary/body in the haystack so
    Spanish-preferring callers can find articles by Spanish keywords
    (e.g. 'cisterna', 'movimiento de equipo', 'avería'). EN remains the
    canonical source; ES is additive search fuel only.
    """
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
            # iter414 · ES fuel (graceful: keys may be absent)
            a.get("title_es", "") or "",
            a.get("summary_es", "") or "",
            _flatten_body(a.get("body_es") or []),
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



# ─────────────────────────────────────────────────────────────────────
# Coverage Dashboard — admin governance read-only view (iter193)
# ─────────────────────────────────────────────────────────────────────
#
# Lightweight, structural coverage analyzer. NOT analytics — just a
# snapshot of what content exists per portal × section. Admins use this
# to spot gaps as the platform grows. Pairs with search-zero-results
# logging (demand-signal) to inform Phase B/C/D content prioritization.

# The 7 operational portals the operator has identified for full coverage.
COVERAGE_PORTALS = ["hr", "safety", "shop", "dispatch", "pm", "leadership", "admin"]

# The sections every portal should have at least one article in to be
# considered "mature". Aligned with the operator's checklist:
#   - roles            (role-based training)
#   - portals          (deep portal-specific workflows)
#   - troubleshooting  (problem-solving guidance)
#   - knowledge        ("why it matters" / cross-workflow)
COVERAGE_REQUIRED_SECTIONS = ["roles", "portals", "troubleshooting", "knowledge"]


def coverage_report() -> dict:
    """Structural coverage matrix: per-portal × per-section article counts.

    Returns a dict with:
      - portals: list of {portal, sections: {section_id: count}, gaps: [section_id]}
      - totals: per-section totals across all articles
      - article_count: total articles in registry

    Read-only; never raises; never reads from DB. Pure registry inspection.
    """
    # Per-portal counts: an article counts toward a portal if its scopes
    # include that portal OR if it is admin-scoped (admins see everything).
    # We intentionally do NOT credit the cross-cutting "field" / "public"
    # scopes here — those don't represent portal-specific coverage.
    per_portal: list[dict] = []
    for portal in COVERAGE_PORTALS:
        section_counts: dict[str, int] = {s["id"]: 0 for s in SECTIONS}
        for a in _ARTICLES:
            scopes = _normalize_scopes(a.get("scopes") or [])
            if portal in scopes:
                section_counts[a["section"]] = section_counts.get(a["section"], 0) + 1
        gaps = [s for s in COVERAGE_REQUIRED_SECTIONS if section_counts.get(s, 0) == 0]
        per_portal.append({
            "portal": portal,
            "sections": section_counts,
            "total": sum(section_counts.values()),
            "gaps": gaps,
            "mature": len(gaps) == 0,
        })

    # Per-section totals across the whole registry
    totals: dict[str, int] = {s["id"]: 0 for s in SECTIONS}
    for a in _ARTICLES:
        totals[a["section"]] = totals.get(a["section"], 0) + 1

    return {
        "portals": per_portal,
        "totals": totals,
        "article_count": len(_ARTICLES),
        "required_sections": list(COVERAGE_REQUIRED_SECTIONS),
        "covered_portals": COVERAGE_PORTALS,
    }


# ─────────────────────────────────────────────────────────────────────
# Workflow Registry — "Has Guidance" indicator (iter194)
# ─────────────────────────────────────────────────────────────────────
#
# Lightweight registry mapping operational workflows / forms to the
# guidance article(s) that cover them. Operator-directive: this is
# maintenance tooling for admins, NOT analytics — it answers the single
# question "which workflows in the platform are documented, and which
# aren't yet?".
#
# Adding a workflow here is the lightweight commitment that says
# "this surface exists; it should have guidance." A new workflow added
# without a `primary_article` shows up as a gap on the admin map.

_WORKFLOWS: list[dict] = [
    # ── Field Leadership ─────────────────────────────────────────────
    {"id": "daily-report", "label": "Daily Report",
     "portal": "leadership", "primary_article": "field-daily-report-howto",
     "alt_articles": ["why-daily-reports", "connect-field-to-payroll"]},
    {"id": "equipment-checkout", "label": "Equipment Checkout",
     "portal": "leadership", "primary_article": "field-equipment-checkout",
     "alt_articles": ["connect-equipment-lifecycle", "why-equipment-accountability"]},
    {"id": "verbal-coaching", "label": "Verbal Coaching",
     "portal": "leadership", "primary_article": "field-coaching-documentation",
     "alt_articles": ["field-writeup-authoring"]},
    {"id": "write-up", "label": "Employee Write-Up",
     "portal": "leadership", "primary_article": "field-writeup-authoring",
     "alt_articles": ["hr-writeups-correctives"]},
    {"id": "field-incident", "label": "Field Incident Report",
     "portal": "leadership", "primary_article": "task-submit-incident",
     "alt_articles": ["field-incident-escalation", "connect-incident-to-audit"]},
    # ── Safety ───────────────────────────────────────────────────────
    {"id": "safety-incident", "label": "Safety Incident Investigation",
     "portal": "safety", "primary_article": "safety-incident-investigation",
     "alt_articles": ["why-incidents", "safety-near-miss-importance"]},
    {"id": "corrective-action", "label": "Corrective Action",
     "portal": "safety", "primary_article": "safety-corrective-actions-workflow",
     "alt_articles": ["why-corrective-actions"]},
    {"id": "safety-audit", "label": "Safety Audit",
     "portal": "safety", "primary_article": "safety-audits-workflow",
     "alt_articles": []},
    {"id": "fire-extinguisher", "label": "Fire Extinguisher Inspection",
     "portal": "safety", "primary_article": "safety-fire-extinguishers",
     "alt_articles": []},
    {"id": "safety-training", "label": "Safety Training Records",
     "portal": "safety", "primary_article": "safety-training-compliance",
     "alt_articles": []},
    # ── HR ───────────────────────────────────────────────────────────
    {"id": "time-verification", "label": "Time Verification",
     "portal": "hr", "primary_article": "hr-time-verification-deep",
     "alt_articles": ["task-verify-time", "why-time-verification", "connect-field-to-payroll"]},
    {"id": "hr-onboarding", "label": "Employee Onboarding",
     "portal": "hr", "primary_article": "hr-onboarding-new-hire",
     "alt_articles": []},
    {"id": "hr-offboarding", "label": "Employee Offboarding",
     "portal": "hr", "primary_article": "hr-offboarding",
     "alt_articles": ["connect-equipment-lifecycle"]},
    # ── Shop / Fleet ─────────────────────────────────────────────────
    {"id": "pre-op", "label": "Equipment Pre-Op Inspection",
     "portal": "shop", "primary_article": "shop-preop-deep",
     "alt_articles": ["shop-operator-responsibilities"]},
    {"id": "failed-preop", "label": "Failed Pre-Op Workflow",
     "portal": "shop", "primary_article": "shop-failed-preop-workflow",
     "alt_articles": ["connect-shop-to-dispatch"]},
    {"id": "damage-report", "label": "Equipment Damage Report",
     "portal": "shop", "primary_article": "shop-damage-reporting",
     "alt_articles": []},
    {"id": "maintenance-coordination", "label": "Maintenance Coordination",
     "portal": "shop", "primary_article": "shop-maintenance-coordination",
     "alt_articles": []},
    {"id": "equipment-return", "label": "Equipment Return",
     "portal": "shop", "primary_article": "shop-equipment-return",
     "alt_articles": ["connect-equipment-lifecycle"]},
    # ── Dispatch ─────────────────────────────────────────────────────
    {"id": "equipment-movement", "label": "Equipment Movement / Transfer",
     "portal": "dispatch", "primary_article": "dispatch-equipment-movement",
     "alt_articles": ["connect-equipment-lifecycle"]},
    {"id": "holds-transfers", "label": "Holds & Transfers",
     "portal": "dispatch", "primary_article": "dispatch-holds-transfers",
     "alt_articles": []},
    # ── PM ───────────────────────────────────────────────────────────
    {"id": "pm-project-review", "label": "PM Project Review",
     "portal": "pm", "primary_article": "pm-project-review-cadence",
     "alt_articles": ["connect-pm-field-review"]},
    # ── Admin ────────────────────────────────────────────────────────
    {"id": "admin-user-mgmt", "label": "User Management",
     "portal": "admin", "primary_article": "admin-user-management",
     "alt_articles": []},
    {"id": "admin-backup-restore", "label": "Backups & Restore",
     "portal": "admin", "primary_article": "admin-backup-restore",
     "alt_articles": ["why-backups"]},
    {"id": "admin-role-templates", "label": "Role Templates",
     "portal": "admin", "primary_article": "admin-role-templates",
     "alt_articles": []},

    # ── Known operational surfaces that do NOT yet have guidance ─────
    # These are real gaps — registered here so the admin map shows them
    # as outstanding work, not so they're hidden.
    {"id": "toolbox-meeting", "label": "Toolbox Meeting / JHA Discussion",
     "portal": "leadership", "primary_article": None, "alt_articles": []},
    {"id": "jha", "label": "Job Hazard Analysis",
     "portal": "safety", "primary_article": None, "alt_articles": []},
    {"id": "trench-box", "label": "Trench Box Reference",
     "portal": "safety", "primary_article": None, "alt_articles": []},
    {"id": "po-request", "label": "PO Request / Approval",
     "portal": "pm", "primary_article": None, "alt_articles": []},
    {"id": "document-expirations", "label": "Document Expirations Tracking",
     "portal": "hr", "primary_article": None, "alt_articles": []},
    {"id": "tasks-actions", "label": "Cross-Portal Tasks & Actions",
     "portal": "admin", "primary_article": None, "alt_articles": []},
]


def workflow_coverage_report() -> dict:
    """Per-workflow guidance-link map. Used by admin maintenance UI.

    Returns:
      {
        workflows: [
          {id, label, portal, primary_article: {id,title}|None, alt_articles: [{id,title}], has_guidance: bool}
        ],
        totals: {total, covered, gaps},
        per_portal: {portal: {total, covered, gaps}}
      }
    """
    # Build a lookup of article id → title for fast resolution
    title_by_id = {a["id"]: a["title"] for a in _ARTICLES}

    rows: list[dict] = []
    per_portal: dict[str, dict] = {}
    covered = 0
    gaps = 0

    for w in _WORKFLOWS:
        primary_id = w.get("primary_article")
        primary = None
        if primary_id and primary_id in title_by_id:
            primary = {"id": primary_id, "title": title_by_id[primary_id]}
        alts = []
        for aid in (w.get("alt_articles") or []):
            if aid in title_by_id:
                alts.append({"id": aid, "title": title_by_id[aid]})
        has = primary is not None
        if has:
            covered += 1
        else:
            gaps += 1
        portal = w.get("portal", "unknown")
        bucket = per_portal.setdefault(portal, {"total": 0, "covered": 0, "gaps": 0})
        bucket["total"] += 1
        if has:
            bucket["covered"] += 1
        else:
            bucket["gaps"] += 1
        rows.append({
            "id": w["id"],
            "label": w["label"],
            "portal": portal,
            "primary_article": primary,
            "alt_articles": alts,
            "has_guidance": has,
        })

    return {
        "workflows": rows,
        "totals": {
            "total": len(_WORKFLOWS),
            "covered": covered,
            "gaps": gaps,
        },
        "per_portal": per_portal,
    }


# ─────────────────────────────────────────────────────────────────────
# Registry integrity validation (iter195)
# ─────────────────────────────────────────────────────────────────────
#
# Lightweight content safety net. Runs at import time and asserts the
# registry has no structurally-bad entries. Operator-directive: one
# malformed article must not be able to take down all guidance and
# search endpoints — Sentry already catches runtime errors, but a
# defensive structural check at import-time catches editorial issues
# before they reach a deploy.
#
# Validation is intentionally lenient: missing/invalid blocks raise a
# clear AssertionError naming the offending article id. Use this in
# tests for fast-fail; production import always runs it once.

_VALID_BLOCK_TYPES = {"p", "steps", "bullets", "why", "next", "warn", "tip", "mistakes"}
_REQUIRED_ARTICLE_KEYS = {"id", "section", "title", "summary", "scopes", "body"}
_KNOWN_SECTIONS = {s["id"] for s in SECTIONS}


def validate_registry(strict: bool = True) -> list[str]:
    """Return a list of integrity issues. With strict=True, also raises
    AssertionError on the first issue (used at import time).

    Issues detected:
      • Article missing required keys
      • Article id duplicate
      • Article section not in SECTIONS
      • Scopes must be a non-empty list of strings
      • Body must be a list of dicts with valid `type`
      • Tags / related must be lists when present
      • All `related` ids must exist in the registry
      • All `alt_articles` / `primary_article` in workflows must exist
    """
    issues: list[str] = []
    seen_ids: set[str] = set()
    article_ids: set[str] = {a.get("id") for a in _ARTICLES if isinstance(a.get("id"), str)}

    for idx, a in enumerate(_ARTICLES):
        prefix = f"_ARTICLES[{idx}] id={a.get('id', '<missing>')}"
        missing = _REQUIRED_ARTICLE_KEYS - set(a.keys())
        if missing:
            issues.append(f"{prefix}: missing keys {missing}")
            continue
        aid = a["id"]
        if aid in seen_ids:
            issues.append(f"{prefix}: duplicate id")
        seen_ids.add(aid)
        if a["section"] not in _KNOWN_SECTIONS:
            issues.append(f"{prefix}: section '{a['section']}' is not a registered section")
        scopes = a.get("scopes")
        if not isinstance(scopes, list) or not scopes or not all(isinstance(s, str) for s in scopes):
            issues.append(f"{prefix}: scopes must be a non-empty list of strings")
        body = a.get("body")
        if not isinstance(body, list):
            issues.append(f"{prefix}: body must be a list")
        else:
            for bi, b in enumerate(body):
                if not isinstance(b, dict) or "type" not in b:
                    issues.append(f"{prefix}: body[{bi}] must be a dict with `type`")
                    continue
                if b["type"] not in _VALID_BLOCK_TYPES:
                    issues.append(f"{prefix}: body[{bi}] has unknown type '{b['type']}'")
        # Optional fields shape check
        for opt in ("tags", "related"):
            if opt in a and not isinstance(a[opt], list):
                issues.append(f"{prefix}: '{opt}' must be a list when present")
        for rel in a.get("related") or []:
            if rel not in article_ids:
                issues.append(f"{prefix}: related id '{rel}' does not exist")
        # iter199 — translation fields: title_es/summary_es must be strings
        # when present; body_es must be a valid block-list with known types.
        for opt in ("title_es", "summary_es"):
            if opt in a and not isinstance(a[opt], str):
                issues.append(f"{prefix}: '{opt}' must be a string when present")
        if "body_es" in a:
            body_es = a["body_es"]
            if not isinstance(body_es, list):
                issues.append(f"{prefix}: body_es must be a list when present")
            else:
                for bi, b in enumerate(body_es):
                    if not isinstance(b, dict) or "type" not in b:
                        issues.append(f"{prefix}: body_es[{bi}] must be a dict with `type`")
                        continue
                    if b["type"] not in _VALID_BLOCK_TYPES:
                        issues.append(f"{prefix}: body_es[{bi}] has unknown type '{b['type']}'")

    # Workflow registry cross-check
    for wi, w in enumerate(_WORKFLOWS):
        prefix = f"_WORKFLOWS[{wi}] id={w.get('id', '<missing>')}"
        if not isinstance(w, dict) or "id" not in w or "label" not in w or "portal" not in w:
            issues.append(f"{prefix}: missing required keys (id/label/portal)")
            continue
        primary = w.get("primary_article")
        if primary is not None and primary not in article_ids:
            issues.append(f"{prefix}: primary_article '{primary}' does not exist")
        for alt in w.get("alt_articles") or []:
            if alt not in article_ids:
                issues.append(f"{prefix}: alt_article '{alt}' does not exist")

    if strict and issues:
        raise AssertionError(
            "guidance registry integrity check failed:\n  - " + "\n  - ".join(issues)
        )
    return issues


# Run at import time so a malformed registry is caught before the app
# accepts a single request. The strict mode raises on first issue;
# we wrap in a log-and-allow guard for production so the app can still
# serve OTHER healthy endpoints even if a content-only mistake slips in.
try:
    validate_registry(strict=True)
except AssertionError as _e:  # pragma: no cover — defensive
    import logging as _logging
    _logging.getLogger(__name__).error("[guidance] %s", _e)
    # We do NOT re-raise. The endpoints will continue to serve whatever
    # articles ARE valid; a malformed article only affects itself.

