RELEASE NOTES · MASCI Operations Platform · Track 18 Production Cut
====================================================================

DATE   : 2026-02-15
OWNER  : MASCI Engineering
TARGET : Internal MASCI operations team + external partners using
         /transportation-operations and /dispatch-portal

────────────────────────────────────────────────────────────────────────────
WHAT'S NEW
────────────────────────────────────────────────────────────────────────────
This release is the Track 18 Production Cut — a platform-wide
consolidation that brings real operational access to dispatchers,
locks in the Operational Design System, and ships a calmer, more
consistent visual language across every portal.

────────────────────────────────────────────────────────────────────────────
MAJOR IMPROVEMENTS
────────────────────────────────────────────────────────────────────────────
• **MASCI Operations Platform language migration.** Every portal —
  Transportation Operations, Project Management, Human Resources,
  Safety Operations, Shop Operations, Administration, Field
  Leadership — now uses its canonical name across the UI, emails,
  and PDFs. No more "MASCI Hub / Office Portals" copy drift.

• **Operational Design System (ODS).** Color, spacing, type, radius,
  shadow, icon, and CTA hierarchy are now governed by linter rules
  R1–R8. Empty states, restricted states, and loading states share
  one calm pattern across the platform.

• **Mission Control access + layout repair.** The Transportation
  Operations Mission Control now opens to a real workspace strip
  with 8 chips, 8 KPI tiles, a top cleanup-opportunity card, and a
  recent-activity feed — all prefix-aware so dispatchers and
  admins both land in their own URL space.

• **Governance boundary linter.** Operational logic stays out of
  `/pages/admin/`; admin-only chrome no longer bleeds into
  `/transportation-operations/*`.

────────────────────────────────────────────────────────────────────────────
TRANSPORTATION OPERATIONS FIXES (highlight)
────────────────────────────────────────────────────────────────────────────
This was the highest-risk area of the release. The two fixes shipped:

• **Track 18.12B — Dispatcher functionality restore.** Replaces
  uncaught 401 React runtime overlays and raw "Admin login required"
  text with a single 401/403-safe data doorway (`txGet` + `txCatch`)
  and a Transportation-branded restricted state.

• **Track 18.12C — Real functionality fix + VISIBLE = USABLE.**
  Reclassified 23 core operational read endpoints from admin-only to
  dispatcher-operational at the backend gate level. A dispatcher
  now sees **real data** on Drivers, Carriers, Trucks, Orientation,
  Compliance, Documents queue, Inspections queue, Morning Queue,
  30-day Forecast, Cleanup signals, and per-entity timeline.
  Admin-only governance surfaces (Audit Timeline, Intelligence deep
  analytics, Automation Health, HR Sync, Email Routes, Module CMS
  writes, materialize-actions) remain admin-strict — AND are HIDDEN
  from the dispatch nav, not band-aided behind a banner.

────────────────────────────────────────────────────────────────────────────
ROLE-SPECIFIC NOTES
────────────────────────────────────────────────────────────────────────────
• **Dispatchers**: Mission Control + Drivers + Carriers + Trucks +
  Orientation + Compliance + Morning Queue + Forecast + Cleanup now
  work natively. Intelligence and Audit Timeline are hidden — those
  remain governance-only surfaces.

• **Super Admin / Administration**: nothing taken away. Every
  pre-Track-18 oversight surface is still accessible at
  `/admin/transportation/*` AND `/transportation-operations/*`.

• **Project Management / Human Resources / Safety Operations /
  Shop Operations / Field Leadership**: portal language updated to
  the canonical name. No workflow changes.

• **Drivers / external carriers (magic-link)**: tokenised links
  continue to work exactly as before. No Transportation TopBar
  chrome bleeds into the minimal driver routes.

────────────────────────────────────────────────────────────────────────────
KNOWN DEFERRALS (NOT IN THIS RELEASE)
────────────────────────────────────────────────────────────────────────────
- Request Access CTA on restricted states (deferred)
- Global Graph visualisation (backlog)
- Manual link/unlink relationship editor (backlog)
- AI relationship suggestions (backlog)
- Fuzzy search / saved searches (backlog)
- Cross-platform global relationship analytics outside Transportation (backlog)
- Cold-start cache for the admin Intelligence aggregations
  (known non-blocker — admin-only, slow on first load)

────────────────────────────────────────────────────────────────────────────
SUPPORT / CONTACT
────────────────────────────────────────────────────────────────────────────
Issues post-release: jaymn.judd@mascigc.com or the operations channel
on the operations mailing list. Outage alerts route automatically.

────────────────────────────────────────────────────────────────────────────
ROLLBACK
────────────────────────────────────────────────────────────────────────────
A point-in-time database snapshot is captured immediately before the
release. Rollback procedure documented in
`PRODUCTION_DEPLOYMENT_CHECKLIST.md` — git checkout of the previous
SHA + frontend artefact swap returns the platform to its pre-Track-18
state in minutes.
