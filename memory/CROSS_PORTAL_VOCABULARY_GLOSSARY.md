# Cross-Portal Vocabulary Glossary

*iter437 · Phase IV-BETA.5A-P3C · 2026-02-27*
*Status: 🟢 GLOSSARY ESTABLISHED · operator reference document*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Purpose

Establish a **single source of canonical operator vocabulary** for the
MASCI platform. Terms below are the **doctrine-correct** forms used in
UI copy, emails, coaching sublines, and operator-facing documentation.
The vocabulary is enforced by `scripts/verify_admin_copy.py` and
`scripts/verify_coaching_sublines.py` where applicable.

## II. Portal names (🟢 canonical)

| Canonical | Use in | Avoid |
|---|---|---|
| **Admin Console** | Header kicker · breadcrumbs · email signatures | "Admin Panel", "Admin Dashboard", "Backoffice" |
| **PM Portal** | Header kicker · email subjects · operator-facing labels | "PM Dashboard", "Project Portal" |
| **HR Portal** | Header kicker · email subjects | "HR Dashboard", "People Portal" |
| **Safety Portal** | Header kicker · email subjects | "Safety Dashboard", "EHS Console" |
| **Dispatch** | Future portal · cataloged but not yet built | "Logistics", "Dispatch Center" |

## III. Operator roles (🟢 canonical)

| Canonical | Notes |
|---|---|
| **Field Leadership** | Foremen, supers, project leads. Same UI as PM with role-gated surfaces. |
| **PM** / **Project Manager** | Owns jobs, daily reports, MoM, change orders. |
| **HR** | Read-mostly. Time verification + accountability. |
| **Safety** | Owns incidents / CA / inspections / training records. |
| **Admin** | Platform operator. Tier-broad access. |
| **Super Admin** | Bootstrap-only. Used for break-glass + integrity ops. |
| **Operator** (generic) | Used in this doc to mean *any* internal user with platform access. NOT to be used in UI copy. |

## IV. Operational surfaces (🟢 canonical)

| Canonical | Notes |
|---|---|
| **Hub** | Landing dashboard for each portal (PM Hub, HR Hub, Safety Hub, Admin Hub). |
| **Section** | A top-level page within a portal (e.g. Equipment & Suppliers, Time Verification). |
| **Tile** | A clickable card on a Hub. Always has a left-edge stripe + h3 + ≤14-word subline + single neutral CTA. |
| **Kicker** | The mono uppercase line above a page h1 (e.g. `SAFETY PORTAL · INCIDENTS`). |
| **Stripe** | The 4 px left-edge accent that identifies a tile's domain. |
| **Pill** | A small rounded label. May be `SEV_PILL` (data-bound severity) or `STATUS_PILL` (workflow state · neutral slate per iter437 IV-BETA.5A). |
| **Banner** | A full-width record-level alert. Severe-tier banners only — never decorative. |
| **Chip** | Tiny monochrome operator-facing readout. Currently only the governance health chip. |

## V. Severity / escalation lexicon (🟢 RESERVED)

| Canonical | When used | Visual treatment |
|---|---|---|
| **Critical** | True severe incident · OSHA-recordable risk | `SEV_PILL` red-700 bg-white text |
| **High** | High-severity, non-critical | `SEV_PILL` red-100 bg + red-300 border |
| **Medium** | Operational warning | `SEV_PILL` amber-100 bg |
| **Low** | Logged, no immediate action | `SEV_PILL` emerald-100 bg |
| **Severe incident** | Used in email subject prefix `🚨 SEVERE INCIDENT · …` | Reserved · never decorative |
| **OSHA Recordable** | Compliance flag · data-bound | Red-900 pill |
| **Open** / **Investigating** / **Closed** | Workflow state · NOT severity | Slate STATUS_PILL (calm) |

## VI. Coaching subline patterns (🟢)

Sentence-case, ≤14 words, period termination. Enforced by
`verify_coaching_sublines.py`.

| Pattern | Example |
|---|---|
| `<Action verb>. <Operational complement>.` | "Open, investigate, verify, close out." |
| `<Noun list of operational outputs>.` | "Issuance, returns, damages, chargebacks." |
| `<Concise observation/promise>.` | "Severity-tagged review of every field report." |

Avoid:

- ❌ Marketing language ("Empower your team to…")
- ❌ Imperatives with no object ("Manage your data.")
- ❌ Compound sublines split with `·` more than 3 times
- ❌ ALL-CAPS source text (Tailwind transforms presentation)

## VII. Communication footers (🟢)

The standardised footer (per `COMMUNICATION_FOOTER_STANDARDIZATION.md`)
uses **one canonical line** across every system-generated email:

> *This is an automated MASCI Safety platform notification.
> Reply directly to this email to reach your project team.*

Use that line verbatim. Do NOT reword. The footer is the **only**
consistent identifying line on every email — its parity is governance.

## VIII. Reserved punctuation (🟢)

| Glyph | Use |
|---|---|
| `·` (U+00B7) | Operational separator within a single mono kicker or label |
| `→` (U+2192) | "Open" CTA suffix on tiles |
| `🚨` | ONE use only — severe-incident email subject prefix |
| `⚠` | ONE use only — equipment-fail email subject prefix |
| All other emoji | Avoid in UI copy entirely |

## IX. Doctrine reaffirmed

- ✅ Vocabulary is **doctrine**, not style preference
- ✅ All future copy passes through this glossary
- ✅ Verbiage gates already enforce the harshest violations
- ✅ Updates to this glossary require an operator-blessed checkpoint
- ✅ Preview only · NO production deploy
