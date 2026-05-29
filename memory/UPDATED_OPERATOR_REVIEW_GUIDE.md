# UPDATED Operator Review Guide · M0.0 → M0.4

_Phase V.1 · 2026-05-29 · final pre-M1 review checkpoint._

This guide supersedes `M0_35_OPERATOR_REVIEW_GUIDE.md` for the
purposes of the **M1 authorization decision**. It folds in the M0.4
external-PDF photo embedding work and the doctrine locks acknowledged
in the M0.35 closeout.

> _Read top-to-bottom in ~6 minutes. By the end of §10 you have
> everything needed to authorize (or hold) M1._

---

## 1 · State of the substrate

| Wave | Scope | Status |
|---|---|---|
| **M0.0** | Hygiene closure (W1/W2/W3) | ✅ Closed |
| **M0.1** | Substrate sealed (8 collections, 25 indexes, 12 tests) | ✅ Sealed |
| **M0.2** | Continuity Engine + Amendment Engine + PDF v1 | ✅ Live |
| **M0.2A** | OGC Catalog (14 keys) + Crew Readiness Matrix + Probes | ✅ Live |
| **M0.3** | Foreman Entry · FL Center · PM Panel · Public Viewer | ✅ Live |
| **M0.35** | Audience Projection Doctrine + Reality Validation (4/4 scenarios) + 2 Doctrine Locks | ✅ Closed |
| **M0.4** | **External PDF photo thumbnail embedding** | ✅ **This wave** |

## 2 · M0.4 in 60 seconds

External ODR PDFs (DOT / FAA / CEI / owner / consultant) now carry
photo evidence with audience-projected redaction:

- **What ships:** 480 px JPEG thumbnails, 96 KB byte-capped, 24-photo
  per-doc cap, 2-column grid with caption + tag below each thumb.
- **What's redacted for external:** raw `photo_id` → ordinal slots
  `p1`, `p2`, …; section anchor; work area id; foreman/super/pm uids;
  email + 32+ hex token patterns in caption; GPS (never in projection).
- **What's audited:** `odr_pdf_renders` rows now carry
  `photo_count_referenced` + `photo_count_embedded`.
- **Continuity preserved:** same photo set → same SHA256. Public
  links remain audience-locked at mint.
- **Failure mode:** unresolvable photo refs render a
  `[photo unavailable]` placeholder; the PDF is never dropped.

## 3 · Doctrine locks (acknowledged at M0.35 · governing M0.4 forward)

| Lock | What it governs |
|---|---|
| **#1 · Simplicity Test** (`ODR_SIMPLICITY_TEST_DOCTRINE.md`) | Every ODR change must pass _"can a foreman complete this on a phone, in mud, in gloves, at 5:30 PM?"_ Target < 5 min · stretch < 3 min · ceiling 7 min. M0.4 imposes **zero new foreman steps** — photo embedding happens server-side. ✅ inherits |
| **#2 · Platform Inheritance** (`ODR_PLATFORM_INHERITANCE_DOCTRINE.md`) | ODR is a module of MASCI Ops. M0.4 introduces **no new ODR-only components** — photo rendering uses Pillow + the existing `_section_*` flowable shape. ✅ inherits |

## 4 · Cumulative test surface · 0 fails

| Suite | Result |
|---|---|
| `tests/odr/test_odr_substrate.py` (M0.1) | 🟢 12 / 12 |
| `tests/odr/test_odr_m02.py` (M0.2 + M0.2A) | 🟢 24 / 24 |
| `tests/odr/test_odr_m03.py` (M0.3) | 🟢 7 / 7 |
| `tests/odr/test_odr_m04.py` (**M0.4 · this wave**) | 🟢 9 / 9 |
| `scripts/odr_public_link_continuity_probe.py --gate` | 🟢 0 fail |
| `scripts/odr_bilingual_probe.py --gate` | 🟢 0 fail |
| `scripts/odr_reality_validation.py` (M0.35) | 🟢 4 / 4 scenarios |

**Total: 52 pytest + 4 reality scenarios + 2 governance probes · 0 failures · 0 regression.**

## 5 · Advisory probes wired for M1 (advisory only · never fail builds)

Per the M0.4 authorization, four heuristic probes are now installed.
Each writes a markdown report under `/app/memory/` and exits 0
unconditionally. Operators consume the reports during review; the
probes never gate a build.

| Probe | Doctrine source | Initial state |
|---|---|---|
| `scripts/odr_completion_time_drift_probe.py` | `ODR_SIMPLICITY_TEST_DOCTRINE.md` | 🟢 GREEN · mean 1.50 min · 8 sample |
| `scripts/odr_simplicity_drift_probe.py` | `ODR_SIMPLICITY_TEST_DOCTRINE.md` | 🟢 GREEN · 0 advisories |
| `scripts/odr_inheritance_drift_probe.py` | `ODR_PLATFORM_INHERITANCE_DOCTRINE.md` | 🟢 GREEN · 0 advisories |
| `scripts/cross_portal_consistency_drift_probe.py` | `CROSS_PORTAL_CONSISTENCY_STANDARD.md` + Lock #2 | 🟢 GREEN · ODR uses shared ui kit |

Output reports (auto-generated):
- `/app/memory/ODR_COMPLETION_TIME_DRIFT_REPORT.md`
- `/app/memory/ODR_SIMPLICITY_DRIFT_REPORT.md`
- `/app/memory/ODR_INHERITANCE_DRIFT_REPORT.md`
- `/app/memory/CROSS_PORTAL_CONSISTENCY_DRIFT_REPORT.md`

## 6 · External-PDF photo audit · what to spot-check before M1

Operators reviewing M0.4 should validate the following on at least
one real external PDF:

- [ ] **Footer line carries `audience=external`, `sha256=…`, `rendered <utc>`** on every page
- [ ] **No `foreman_uid`, `superintendent_uid`, or `pm_uid` strings** appear anywhere in the PDF text layer
- [ ] **No raw `photo_id` strings** appear anywhere in the PDF byte stream (use grep on the downloaded file; you should see ordinal slot patterns like `p1`, `p2` only)
- [ ] **Every photo carries a caption + tag**, no GPS, no section anchor, no work area
- [ ] **`X-ODR-Photo-Count` and `X-ODR-Photo-Embedded` response headers match** what the ODR record actually carries
- [ ] **Re-rendering the same external PDF yields the same `X-ODR-SHA256`** (continuity invariant)

## 7 · Approval items · what we want operator sign-off on before M1

- [ ] **M0.4 photo embedding acceptance** — read `M0_4_PHOTO_PDF_CERTIFICATION.md` + `EXTERNAL_PDF_PHOTO_GOVERNANCE_REPORT.md`. Confirm the redaction matrix matches MASCI's distribution policy.
- [ ] **Pilot blocker G7 cleared** — confirm M0.4 closes the only pre-pilot blocker surfaced in `ODR_REALITY_GAP_AUDIT.md`.
- [ ] **24-photo per-doc cap** — confirm this cap is acceptable for typical MASCI submittals. (Easy to relax if needed.)
- [ ] **96 KB per-thumb cap** — confirm this is acceptable for DOT/FAA mailing limits.
- [ ] **Advisory probe state** — confirm operator interpretation of the four advisory probe reports.
- [ ] **M1 authorization** — explicit go/no-go on Migration · Dual-Write · Pilot.

## 8 · M1 authorization gate (every row must be ✅)

| Condition | Status |
|---|---|
| M0.0 hygiene | ✅ |
| M0.1 substrate sealed | ✅ |
| M0.2 / M0.2A engines + probes | ✅ |
| M0.3 operator surfaces live | ✅ |
| M0.35 reality validation passed (4/4) | ✅ |
| Doctrine Lock #1 (Simplicity Test) acknowledged | ✅ |
| Doctrine Lock #2 (Platform Inheritance) acknowledged | ✅ |
| **M0.4 external PDF photo embedding** | ✅ |
| Pytest sweep complete | ✅ 52 / 52 |
| Continuity + bilingual probes green | ✅ |
| Advisory probes installed (M1-prep) | ✅ 4 / 4 GREEN at install |
| **Operator final review of all the above** | ⏳ awaiting |

Until the final row turns ✅: **No M1 migration. No dual-write.
No pilot. Await authorization.**

## 9 · What stays NOT happening (per directive)

- ❌ NO M1 migration / dual-write / pilot rollout
- ❌ NO RFI / Schedule / P6 work
- ❌ NO new architecture or governance layers added
- ❌ NO production deploy beyond the existing preview cutover

## 10 · Stop condition

🛑 **HALTED at end of M0.4 as directed.**

The substrate is now **field-ready for first crew pilot** the moment
operator authorization arrives. Reality validation has proved the
operational shape. Audience projection is locked. Photos travel
with the document. Doctrine locks protect simplicity and inheritance
from drift. The audit trail knows what was shipped to whom and when.

> _Field truth beats developer assumptions._
> _Operator adoption beats feature count._
> _Reality validation beats rework._
> _Photo evidence beats narrative dispute._

When you're ready, issue **M1 authorization**. Until then, the
system stays here — calmly, deterministically, and audit-defensibly
complete through M0.4.

---

_End of UPDATED_OPERATOR_REVIEW_GUIDE.md · supersedes M0_35 review guide for the M1 authorization decision._
