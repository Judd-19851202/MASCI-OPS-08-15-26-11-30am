PRE-DEPLOYMENT DESIGN / LANGUAGE / VISUAL CHECK
================================================

DATE: 2026-02-15
SCOPE: Confirm Tracks 18.01 → 18.07 + 18.10 + 18.11 design system,
       naming, and language locks hold across the release surface.

────────────────────────────────────────────────────────────────────────────
CANONICAL NAMING (must appear · banned variants must not)
────────────────────────────────────────────────────────────────────────────
| Canonical                       | Status   | Banned variant                            | Status |
|---------------------------------|----------|-------------------------------------------|--------|
| MASCI Operations Platform       | ✅ used  | MASCI Hub (except allowed carve-outs)     | ✅ banned |
| Transportation Operations       | ✅ used  | Dispatch Portal (where banned), Office Portal | ✅ banned |
| Project Management              | ✅ used  | PM Portal                                  | ✅ banned |
| Human Resources                 | ✅ used  | HR Portal                                  | ✅ banned |
| Safety Operations               | ✅ used  | Safety Portal                              | ✅ banned |
| Shop Operations                 | ✅ used  | Shop Portal                                | ✅ banned |
| Administration                  | ✅ used  | Admin Portal, Admin Console (where banned) | ✅ banned |
| Field Leadership                | ✅ used  | FL Portal                                  | ✅ banned |
| Operational Guidance Center     | ✅ used  | —                                          | —      |

Allowed carve-out: the platform "Hub" word remains acceptable as the
internal codename for the multi-login surface helper module and the
R2 bucket name only — never user-facing copy.

────────────────────────────────────────────────────────────────────────────
CASE-STYLE LOCK (Track 18.07)
────────────────────────────────────────────────────────────────────────────
- Page headers / hero: Title Case ("Mission Control", "Drivers")
- Sub-tabs: Title Case
- Body / descriptive copy: Sentence case
- Empty / restricted state copy: Sentence case
- CTA buttons: Title Case
- Status badges: ALL CAPS or Title Case (consistent within a page)
- Code identifiers (testids): kebab-case
Status: ✅ pass — Track 18.07 lock tests green.

────────────────────────────────────────────────────────────────────────────
HOMEPAGE / FOOTER
────────────────────────────────────────────────────────────────────────────
- Homepage hero reads "MASCI Operations Platform" with platform tagline.
- No "MASCI Hub" / "Office Portals" rendered to anonymous users.
- Footer carries MASCI General Contractors copyright + Operational
  Guidance Center link + Sign-in surface.
Status: ✅ pass.

────────────────────────────────────────────────────────────────────────────
EMAIL TEMPLATES (Track 18.05)
────────────────────────────────────────────────────────────────────────────
- All emails use canonical names: "Transportation Operations",
  "Operational Guidance Center", "MASCI Operations Platform".
- Driver invite emails reference "Transportation Operations" not
  "Dispatch Portal" externally.
Status: ✅ pass — Track 18.05 lock test green.

────────────────────────────────────────────────────────────────────────────
PDF GENERATORS (Track 18.05)
────────────────────────────────────────────────────────────────────────────
- PDF headers / footers use canonical names.
- No legacy "MASCI Hub" branding in PDF metadata.
Status: ✅ pass.

────────────────────────────────────────────────────────────────────────────
OPERATIONAL DESIGN SYSTEM (Track 18.02)
────────────────────────────────────────────────────────────────────────────
- Color tokens (slate / amber / rose / emerald) consistent.
- Empty states follow the Track 18.02 calm-empty pattern.
- Restricted states use `<TxOpsRestrictedData />` branded component.
- Loading states use the canonical Loading… text or spinner.
- No raw "Failed" / "Error" / developer stack traces rendered.

────────────────────────────────────────────────────────────────────────────
DESIGN-SYSTEM LINTER R1–R8 (Tracks 18.03 / 18.04 / 18.11)
────────────────────────────────────────────────────────────────────────────
| Rule | Description                                                 | Status |
|------|-------------------------------------------------------------|--------|
| R1   | One H1 per page · semantic hierarchy                         | ✅     |
| R2   | Canonical color tokens only · no ad-hoc hex                  | ✅     |
| R3   | Spacing scale tokens · no arbitrary px                       | ✅     |
| R4   | Font size hierarchy                                          | ✅     |
| R5   | Border-radius tokens                                         | ✅     |
| R6   | Shadow / elevation tokens                                    | ✅     |
| R7   | Icon size + alignment                                        | ✅     |
| R8   | One primary CTA per card                                     | ✅ (calibrated by Track 18.11) |

────────────────────────────────────────────────────────────────────────────
GOVERNANCE BOUNDARY LINTER (Track 18.10)
────────────────────────────────────────────────────────────────────────────
- No operational execution logic in `/pages/admin/`.
- No admin-only chrome rendered inside `/transportation-operations/*`.
- Cross-portal calls only via documented helpers (api.js bus +
  cross-portal readiness endpoint).
Status: ✅ pass.

────────────────────────────────────────────────────────────────────────────
MISSION CONTROL LAYOUT (Track 18.12)
────────────────────────────────────────────────────────────────────────────
- Workspace strip · 8 chips · prefix-aware links.
- 8 KPI tiles + Cleanup card + Recent activity.
- Mobile / tablet / desktop responsive verified.
Status: ✅ pass.

────────────────────────────────────────────────────────────────────────────
DEVICE / BROWSER POLISH (Track 18.08)
────────────────────────────────────────────────────────────────────────────
- Mobile portrait (Track 18.08 audit) — no layout breaks.
- Tablet landscape — no layout breaks.
- Desktop 1280–1920 — Mission Control + tables render correctly.
Status: ✅ pass (visual baseline locked in 18.08).

────────────────────────────────────────────────────────────────────────────
OVERALL DESIGN / LANGUAGE / VISUAL STATUS
────────────────────────────────────────────────────────────────────────────
✅ PASS — every linter green, every canonical name in place, no banned
copy bleed, no raw developer errors in UI, ODS patterns applied
consistently across the release surface.
