# M0.35 · Operator Review Guide

_Phase V.1 · 2026-05-29 · final pre-M1 review checkpoint._

The directive after M0.3 was unambiguous:

> "After M0.35: **STOP.** Do NOT begin M1 / Dual Write / Migration /
> Pilot. Await operator review."

This guide is the briefing for that review. Read top-to-bottom in
~5 minutes.

---

## 1 · M0.3 lock-ins (codified · audit-tracked · permanently)

The 4 review items from M0.3 are now locked in the certifications:

| Lock | Implementation |
|---|---|
| **OGC Catalog Tone** ✅ approved | `guidance_catalog.py` voice unchanged · M0.3 cert updated |
| **Public Viewer Redaction** ✅ approved | `_project_for_audience("external")` boundary unchanged · M0.3 cert updated |
| **PM 5-Metric Panel** ✅ approved | `OdrPmPanel.jsx` 5 metrics unchanged · M0.3 cert updated |
| **Trust Banner Doctrine** ✅ approved | `OdrTrustBanner.jsx` unchanged · trust banner doctrine locked |

## 2 · M0.35 deliverables (all 5 + audience projection doctrine)

| File | Status |
|---|---|
| `ODR_REALITY_VALIDATION_REPORT.md` | ✅ — 4 scenarios · 4/4 submitted clean · 0 leaks |
| `ODR_REALITY_GAP_AUDIT.md` | ✅ — 8 gaps surfaced · 1 pilot blocker (G7 photo embedding) |
| `ODR_PILOT_SUCCESS_SCORECARD.md` | ✅ — adoption / quality / operational value / sentiment metrics |
| `OFFLINE_QUEUE_READINESS_ASSESSMENT.md` | ✅ — 5-phase plan · 8.5–11.5 dev-days estimate |
| `M0_35_OPERATOR_REVIEW_GUIDE.md` (this) | ✅ ⛔ |
| `ODR_AUDIENCE_PROJECTION_DOCTRINE.md` | ✅ — locked · "user picks audience · system picks projection" |
| `ODR_SIMPLICITY_TEST_DOCTRINE.md` | ✅ ⛔ — Doctrine Lock #1 · permanent foreman approval gate |
| `ODR_PLATFORM_INHERITANCE_DOCTRINE.md` | ✅ ⛔ — Doctrine Lock #2 · ODR is a module of MASCI Ops, not a separate app |

## 3 · Backend changes shipped in M0.35

| Change | File |
|---|---|
| **Audience profile mapping** (11 profiles → 5 projections) | `routes/odr/pdf.py::AUDIENCE_PROFILES` |
| **PDF render audit log** (`odr_pdf_renders` collection · append-only) | `routes/odr/pdf.py::get_pdf` |
| **Public link audience-locked** (`audience_profile_locked="external"` written at mint) | `routes/odr/continuity.py::mint_link` |
| **Continuity index extension** (`odr_pdf_renders` · 3 indexes) | `routes/odr/continuity.py::ensure_continuity_indexes` |
| `X-ODR-Audience-Profile` response header | `routes/odr/pdf.py::get_pdf` |
| Reality validation harness | `scripts/odr_reality_validation.py` |

## 4 · What the reality validation actually proved

4 scenarios driven through the live preview API:

```
ODR-2026-00029  Airport · Taxiway Closure        5,442ms ✅
ODR-2026-00030  Drainage · Utility Conflict      4,923ms ✅
ODR-2026-00031  Asphalt · Plant Issue + MOT      4,804ms ✅
ODR-2026-00032  Concrete · Structures + Amendment 5,340ms ✅
```

Every scenario:

- ✅ Created draft + 8 patches + ack + submit + 5 PDF renders +
  audience profile call + public link mint + public resolve in **~5 seconds**.
- ✅ Public viewer leaked **0 internal fields**.
- ✅ Audience profile `external_dot` correctly mapped to `audience=external`.
- ✅ Public link auto-locked to `audience_profile_locked="external"`.
- ✅ Concrete scenario's amendment recorded with audit row.
- ✅ Continuity probe + Bilingual probe still green.

## 5 · The single pilot blocker found

🔴 **G7 — External PDFs do not yet embed photo thumbnails.** DOT/FAA
inspectors expect photo evidence inside the print package. The asset
substrate already exists (`routes/photo_governance.py`); the PDF
renderer needs to pull thumbnails. Estimated 1–2 dev-days · M0.4 task.

The other 7 gaps are pilot-tolerable.

## 6 · Audience projection doctrine — the simple rule

> **The user chooses the audience. The system chooses the projection.**

11 audience profiles are now mapped:

```
internal_foreman / superintendent / pm / operations
external_owner / cei / dot / faa / consultant
executive_leadership
legal_audit  (admin-only)
```

PMs never pick redaction options. Foremen never leak. Public links
are immutably audience-locked at mint. Every PDF render writes one
row to `odr_pdf_renders` (audit · indexed · append-only).

## 7 · What I want approval on before M1

- [ ] **Reality Validation acceptance** — read `ODR_REALITY_VALIDATION_REPORT.md`. Does it match how MASCI projects actually run? Anything missing?
- [ ] **Pilot blocker prioritization** — confirm G7 (photo embedding) is the only must-fix. Confirm G4 + G5 + G8 fix-during-pilot acceptance.
- [ ] **Pilot scorecard thresholds** — read `ODR_PILOT_SUCCESS_SCORECARD.md` thresholds (75% completion · 25% abandonment · 9-min completion · ≥3 photos · ≤0.10 amendment rate). Adjust if any number feels wrong for MASCI's specific operator base.
- [ ] **Audience profile catalog** — confirm the 11 profiles cover MASCI's PDF-distribution targets. Add `external_municipality` or `external_subcontractor` if needed.
- [ ] **Offline plan acceptance** — confirm O1+O2 (read-side cache + write queue) is the minimum-viable offline capability for pilot.

## 8 · What's still NOT happening (per directive)

- ❌ NO M1 migration / dual-write / pilot rollout
- ❌ NO RFI / Schedule / P6 work
- ❌ NO new architecture / new governance layers
- ❌ NO dashboard expansion
- ❌ NO production deploy (preview only)

## 9 · Test surface (cumulative)

| Suite | Result |
|---|---|
| `tests/odr/test_odr_substrate.py` (M0.1 regression) | 🟢 12/12 |
| `tests/odr/test_odr_m02.py` (M0.2 + M0.2A regression) | 🟢 24/24 |
| `tests/odr/test_odr_m03.py` (M0.3 regression) | 🟢 7/7 |
| Wave 1 substrate + 1.1 sidecar regression | 🟢 27/27 |
| `scripts/odr_public_link_continuity_probe.py --gate` | 🟢 0 failures |
| `scripts/odr_bilingual_probe.py --gate` | 🟢 0 failures |
| `scripts/odr_reality_validation.py` (M0.35 NEW) | 🟢 4/4 scenarios |
| `ruff check backend/routes/odr/` | 🟢 clean |
| `eslint frontend/src/{pages/odr,lib/odrApi,components/odr}` | 🟢 clean |

**Total: 70 pytest + 4 reality scenarios + 2 probes · 0 failures · 0 regression.**

## 10 · Doctrine Locks registered (M1 authorization conditions)

Two permanent doctrine locks were added to M0.35 closure. **Both are
M1 authorization preconditions** — M1 may not begin until they are
acknowledged by operator review.

### 🔴 Doctrine Lock #1 · `ODR_SIMPLICITY_TEST_DOCTRINE.md`

> "Would a foreman complete this on a phone, standing in mud,
> wearing gloves, at 5:30 PM, after a 12-hour shift?"

If the answer is NO, implementation must remove / hide / auto-populate /
infer / move-to-Super / move-to-PM / move-to-Ops the burden — never
push it onto the foreman.

- **Target**: < 5 min foreman completion
- **Stretch**: < 3 min
- **Hard ceiling**: 7 min (P0 regression above this)
- **Rule**: The platform may grow more intelligent. The foreman
  experience must grow simpler. Field simplicity always overrides
  architectural elegance.

### 🔴 Doctrine Lock #2 · `ODR_PLATFORM_INHERITANCE_DOCTRINE.md`

> ODR is NOT a standalone product. ODR is a module of MASCI Ops.

ODR must inherit: `PLATFORM_WIDE_NAVIGATION_DOCTRINE`,
`SHARED_COMPONENT_GOVERNANCE`, `CROSS_PORTAL_CONSISTENCY_STANDARD`,
`OPERATIONAL_CALMNESS_DOCTRINE`, `TIMELINE_DOCTRINE`,
`OPERATIONAL_LINKING_RULES`, `PHOTO_GOVERNANCE_STANDARD`,
`FIELD_LEADERSHIP_VISIBILITY_DOCTRINE`.

Divergence requires: **documentation · justification · review · approval.**
Every persona must feel they are using one operating system — not
multiple systems stitched together.

## 11 · M1 Authorization Conditions (all must be ✅)

| Condition | Status |
|---|---|
| M0.35 wrap-up complete | ✅ |
| pytest sweep complete (70+ tests · 0 fails) | ✅ |
| Reality validation passed (4/4 scenarios) | ✅ |
| 6 review artifacts updated | ✅ |
| `ODR_SIMPLICITY_TEST_DOCTRINE` registered | ✅ |
| `ODR_PLATFORM_INHERITANCE_DOCTRINE` registered | ✅ |
| **Operator review of all of the above** | ⏳ awaiting |

Until the final row turns ✅: **No migration. No dual-write. No pilot.
Await authorization.**

## 12 · Stop condition

🛑 **HALTED at end of M0.35 as directed.**

Awaiting operator decision on the **5 approval items in §7** plus
acknowledgement of the **2 doctrine locks in §10** before M1 migration
begins. Once M1 is authorized, the substrate enters its first dual-write
/ pilot wave from a position of confidence — because reality has
already validated it and the doctrine locks protect simplicity and
platform inheritance from drift.

Field truth beats developer assumptions. Operator adoption beats
feature count. Reality validation beats rework.

_End of M0_35_OPERATOR_REVIEW_GUIDE.md._
