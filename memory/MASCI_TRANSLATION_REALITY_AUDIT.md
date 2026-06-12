# MASCI Platform — Translation Reality Audit (Track 13.4B · Phase 3)

**Mode:** Discovery + classification only. No remediation plan.  
**Generated:** 2026-02 (Track 13.4B Phase 3).

> **The headline "20.5 % untranslated" is NOT the metric we report.**  
> The metric that matters is **operational translation readiness** — graded by who reads the surface and what they're trying to do.

---

## A. Methodology

1. Extracted **all distinct `t("…")` keys** invoked anywhere in the
   frontend source: **3,932** keys.
2. Extracted **all keys present in the Spanish `const ES = { … }`
   dictionary** in `i18n.js`: **4,272** keys.
3. **Orphan set** = called-by-code but no Spanish entry = `3,932 − ES ∩ t() = 806`.
4. **Dead set** = in dictionary but never called = `4,272 − ES ∩ t() = 1,146`.
5. Classified every called key into 6 audience-driven buckets via
   keyword heuristics (Safety / Field / Workflow / Public / Admin / Technical),
   plus an "Unclassified" residual.

Heuristic patterns (regex over the string content):
- **Safety**: safety · hazard · jha · jhp · incident · trench · excav · capa · ppe · osha · fall · electrocut · asphyx · fire · extinguish · silica · certif · toolbox · near miss · first aid · emergency · injury
- **Field**: daily · crew · foreman · field · truck · driver · pre-op · dvir · inspect · equipment · asset · photo · gps · odr · log out · sign in · forgot · reset password · submit · saved · reload · restore · discard · draft · language · mobile · tablet
- **Workflow**: open · close · approve · reject · review · submit · cancel · sign-off · edit · delete · save · update · create · new · complete · next · previous · due · expired · overdue · workflow · status · step · attach · upload · download · export · pdf · email
- **Public**: public · qr · poster · cheatsheet · landing · share · link · contact · address · hotline · after-hours
- **Admin**: admin · impersonate · backup · restore · database · cluster · cohort · stripe · migration · seed · sync · reconcile · persistence · production health · cluster capacity · stability · deploy · integration · webhook · directory · sso · mfa · passkey · audit · governance · compliance · legacy · payroll variance · po digest · operator digest
- **Technical**: api · endpoint · http · json · payload · token · jwt · webhook · bcrypt · hash · cache · index · collection · mongodb · docker · kubernetes · supervisor · environment · env · preview · prod · debug · trace · stack · error code

Heuristics are not perfect. Strings matching multiple buckets are
assigned to the highest-priority bucket (Safety > Field > Public >
Workflow > Admin > Technical). Strings matching none drop into
"Unclassified".

---

## B. Operational Readiness Scores

| Bucket | Audience | Total t() keys | With ES | Orphan | **Readiness %** |
|---|---|---|---|---|---|
| **Safety-Critical** | Field / Safety / Crew | 413 | 313 | **100** | **75.8 %** |
| **Field-Critical** | Crew / Foreman / Driver | 719 | 593 | **126** | **82.5 %** |
| **Workflow-Critical** | All operators completing a task | 439 | 362 | **77** | **82.5 %** |
| **Public-Facing** | Anyone (public forms, posters, QR landings, cheatsheet) | 91 | 67 | **24** | **73.6 %** |
| **Administrative / Office** | Admin / PM / Office staff | 73 | 54 | **19** | **74.0 %** |
| **Technical / Internal** | Engineers / Admins | 48 | 33 | **15** | **68.8 %** |
| Unclassified (mixed) | mixed | 2,149 | 1,704 | **445** | **79.3 %** |
| **All frontend UI** | mixed | 3,932 | 3,126 | **806** | 79.5 % |
| **Outbound emails** | Spanish-speaking crew sometimes | 0 templates have ES path | 0 | n/a | **0 %** |
| **Server-rendered PDFs** | Field crew, FL records, training certs | 0 PDF templates have ES path | 0 | n/a | **0 %** |
| **Excel / CSV exports** | Office | not applicable (data) | n/a | n/a | **0 %** |
| **Backend `HTTPException` details** | Spanish-speaking crew when validation fails | not wrapped | n/a | n/a | **0 %** |
| **Status verbs (engine literals)** | All operators | not wrapped in `t()` | n/a | n/a | **0 %** |

---

## C. Critical Spanish Gaps — examples (Safety-Critical bucket)

100 Safety-Critical orphan strings. Representative sample (verbatim from `/tmp/orphans.txt`):

```
1 year (OSHA 300)
A trench that looks 'mostly okay' has killed people. Anything that
  feels off — soil, water, the box, the spoil pile, the spotter —
  is a reason to stop. Safety beats schedule. Every time.
Acknowledge the trench-box rated-depth gap with a reason before
  submitting.
Action Required · Trench Box Rated Depth
Active JHPs / JHAs across your projects.
Asset IDs are permanent once created. Safety and Admin can both
  create, edit, and retire.
Bilingual wallet-sized safety cards — English and Español, front
  and back. Print on letter paper or email the PDF straight to the
  crew.
CAPA lifecycle
Cannot delete — linked corrective actions still reference this
  incident.
Certifications, training records, expirations, sign-in sheets,
  renewal reminders.
```

**Direct observation:** the *content of these strings* is exactly the
material a Spanish-speaking foreman or crew member needs in their first
language — trench-box safety guidance, CAPA workflow language, OSHA
training reminders. Yet **the Spanish path falls through to English**
today for all 100.

---

## D. Field-Critical Spanish Gaps — examples

126 Field-Critical orphan strings. Sample:

```
Active assignments, waiting trucks, breakdowns, haul movement.
Add photo (camera or gallery, required for FAIL)
All equipment returned at termination
All fields marked * are required
All submitted dailies, filterable by project.
Apply Driver Updates
Approved driver
Asset
Asset deleted
Asset updated
```

These are crew-facing labels that show up while a foreman is on a
phone or iPad in the field. Each one is a tiny barrier for a
Spanish-first crew member.

---

## E. Public-Facing Spanish Gaps — examples

24 Public-Facing orphan strings (lowest Spanish readiness rate at
73.6 %). The public forms (`/inspect/new`, `/meetings/new`,
`/incidents/new`, `/daily/new`, `/equipment/new`, `/jha/new`,
`/odr/new`, `/constraints/new`) and public posters all share this
audience. Examples (heuristically classified):

```
e.g., MASCI Yard
After-hours contact
Public Trench Safety
Asset Lookup
Field Tile
```

Public forms have the highest "stranger walks up cold" risk — a
language gap here is the most public-visible.

---

## F. Outbound Email / PDF / Excel — 0 % Spanish

Phase 2B §H.2 noted, and Phase 3 reconfirms:

- `branded_portal_emails.py`, `outage_alerts.py`, `pm_routes.py`,
  `pm_admin.py`, `safety_forms.py` outbound emails, etc. — **no
  Spanish variant exists.**
- `pm_welcome_pdf.py`, `field_leadership_pdf.py`, `training_pdf.py`,
  `hub_banners_pdf.py`, `safety_forms.py` PDF builders, ODR PDF
  builders, Trench Safety PDF report distribution — **no Spanish
  variant exists.**
- Excel exports (`MASCI_jobs.xlsx`, `MASCI_pms.xlsx`,
  `MASCI_Inspection_*.xlsx`) — sheet headers and labels are English.

The *only* form family with bilingual EN + ES inline acknowledgement
text is Safety Equipment Issuance / Training (Phase 2B §H.1).

---

## G. Dead Spanish Translation Weight — 1,146 keys

1,146 Spanish entries are in the dictionary but **never called by any
`t()` site**. These are not necessarily wrong — they may exist from
previous code that was refactored — but they're maintenance overhead
that doesn't currently improve any surface.

Representative sample (verbatim):

```
"Almacenamiento de archivos"
"Avisar al equipo de mantenimiento"
"Causa raíz"
"Conducción defensiva"
"Estado del extinguidor"
"Permiso de trabajo en altura"
"Recordatorio de capacitación"
"Reporte de cuasi-accidente"
"Verificación de hora extra"
"Verificación de hora regular"
```

(High likelihood several of these match strings that are now phrased
slightly differently in the frontend — they failed the exact-match
`t()` join. Phase 4 would diff them.)

---

## H. Status verbs are not wrapped in `t()` at all

Status engine literals (`active`, `closed`, `open`, `submitted`,
`signed_off`, `green`, `amber`, `red`, `gray`, `live`, `idle`,
`offline`, `working`, etc.) are rendered straight from the document
field. They are **not** wrapped in `t()`, so even when an ES
translation exists for the verb, it would not fire.

**Effective status-verb Spanish coverage: 0 %.**

---

## I. Translation Readiness Index (Phase-3 headline)

| Index | Value | Lens |
|---|---|---|
| Field-Critical Translation Readiness | **82.5 %** | crew / foreman / driver UI |
| Safety-Critical Translation Readiness | **75.8 %** | safety workflows, JHA, trench, CAPA, OSHA |
| Workflow-Critical Translation Readiness | **82.5 %** | form submit / approve / close labels |
| Public-Facing Translation Readiness | **73.6 %** | public forms, QR landings, cheatsheet |
| Administrative Translation Readiness | **74.0 %** | admin / office surfaces |
| Technical Translation Readiness | **68.8 %** | engineer / debug surfaces |
| **Outbound Email Readiness** | **0 %** | every Spanish-speaking recipient gets English |
| **Server-Rendered PDF Readiness** | **0 %** | Safety equipment issuance PDF is the lone partial exception (inline ES legal text) |
| **Status Verb Readiness** | **0 %** | engine literals never reach `t()` |

---

## J. Cross-mapping into the Master Findings Registry

Each row above is the prioritisable form of:
- T-01 — Safety-Critical UI gap
- T-02 — Field-Critical UI gap
- T-03 — Workflow-Critical UI gap
- T-04 — Public-Facing UI gap
- T-05 — Admin / Office UI gap
- T-06 — Technical UI gap
- T-07 — Unclassified UI gap
- T-08 — Outbound email translation = 0 %
- T-09 — Server-rendered PDF translation = 0 %
- T-10 — Excel / CSV export translation = 0 %
- T-11 — Backend `HTTPException` detail translation = 0 %
- T-12 — Status verb translation = 0 %

See `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md` §F and
`MASCI_PLATFORM_PRIORITY_MATRIX.md` for the tier assignments.

---

## K. What this audit did NOT do
- Did not auto-translate any string.
- Did not propose which orphan to fix first.
- Did not propose a translation pipeline.
- Did not validate machine-generated translations.
- Did not crawl the Mongo-backed guidance content for ES coverage.
- Did not crawl backend templates beyond identifying the language gap.
