# Platform Case Style Guide

> Source of truth for capitalization across every user-facing surface in the
> MASCI Operations Platform. Companion to the Platform Language Constitution
> (Track 18.03) and the Platform Language Migration (Track 18.04).

---

## Rule 1 — Official workspace + feature names use **Title Case**

Always Title Case when naming a workspace, product area, or named feature:

- **MASCI Operations Platform**
- **Transportation Operations**
- **Project Management**
- **Human Resources**
- **Safety Operations**
- **Shop Operations**
- **Administration**
- **Field Leadership**
- **Operational Guidance Center**
- **Mission Control**
- **Dispatch Board**
- **Live Map**
- **Haul Ledger**
- **Driver Qualification**
- **Right Rail**
- **Audit Timeline**

## Rule 2 — Generic operational categories in prose use **sentence case / lowercase**

When listing broad categories in a descriptive sentence:

> *Field reporting, safety, quality, equipment, workforce accountability, transportation, and project operations…*

Do not mix Title-Case workspace identities with lowercase generic categories in the same sentence.

## Rule 3 — Headings and cards use Title Case when naming a destination

- Section headers: **Today in the Field**, **Leadership Tools**, **Operations**, **Your Workspaces**, **Reference**.
- Card titles: **Transportation Operations**, **Shop Operations**, **Project Management**, etc.
- Page titles: **Mission Control**, **First Week on the Platform**, **Cheat Sheet**.

## Rule 4 — Descriptive body copy uses sentence case

> *Dispatch, fleet, drivers, carriers, compliance, orientation, cleanup, and transportation coordination.*

> *Fleet maintenance, inspections, repairs, parts, and equipment readiness.*

> *Employee records, onboarding, compliance, training, and workforce management.*

## Rule 5 — CTAs and buttons

Source text uses normal Title Case; CSS handles uppercase tracking where the visual design calls for it.

Approved CTA source strings:
- **Open Workspace**
- **Sign In**
- **Sign Out**
- **Start Here**
- **View Guide**
- **Open Mission Control**
- **View Related Records**
- **Open in Dispatch**
- **Review Documents**
- **Check Readiness**

Avoid writing raw `SIGN IN`, `sign in`, or `Sign in` inconsistently across sibling buttons. Pick one (default: Title Case source).

**Exception (documented):** `SafetyHub.jsx` uses `ctaLabel={t("OPEN")}` as source text where the card component intentionally styles the label uppercase via CSS for a deliberate tone. Treat as a card-system convention, not a precedent for ad-hoc all-caps source text.

## Rule 6 — Browser titles · PDFs · Emails · Notifications

Same rules apply everywhere user-facing:
- Subject lines: `[MASCI] {Sentence-case action} {Workspace Title Case}` — e.g. `[MASCI] Reset your Human Resources password`.
- PDF titles: `Welcome — MASCI {Workspace Title Case}`.
- Notification titles: short Title Case.
- Notification body: sentence case.

## Rule 7 — Spanish translations

Spanish strings use Spanish Title Case conventions (only first word + proper nouns are capitalized in headings). Workspace names translate as named entities:

- *Operaciones de Transporte*
- *Recursos Humanos*
- *Operaciones de Seguridad*
- *Operaciones de Taller*
- *Gestión de Proyectos*
- *Administración*

---

## Quick reference table

| Where it appears | Case style |
|---|---|
| Hero kicker / brand strip | Title Case (canonical platform name) |
| Hero subtext / descriptive prose | sentence case |
| Workspace card title | Title Case (workspace name) |
| Workspace card description | sentence case |
| Section header | Title Case |
| Page title (`<h1>`) | Title Case |
| Page subtitle / kicker | sentence case OR all-caps tracking (CSS) |
| Card body | sentence case |
| CTA button source | Title Case |
| CTA button display | Title Case OR uppercase via CSS |
| Email subject | `[MASCI] Sentence-case action Workspace Title Case` |
| Email headline | sentence case |
| PDF title | Title Case |
| Notification title | Title Case |
| Notification body | sentence case |
| Empty state | sentence case |
| Restricted state | `Restricted for your role` (canonical Title-Case-and-sentence-case hybrid per Constitution) |

---

## Enforcement

- `backend/tests/test_track_18_05_operational_excellence.py` locks the
  hero subtext + kicker case decisions.
- `backend/tests/test_track_18_04_platform_language_migration.py` locks
  the vocabulary itself.
- Deployment gate runs both on every commit.

If you find a new place where case is drifting, file it as part of
Track 18.06 and update this guide.
