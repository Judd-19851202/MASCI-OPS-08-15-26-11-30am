# MASCI Layer Audit · Phase 10 · Document 1 of 5

**Date:** 2026-05-24
**Mode:** Audit only · zero code changes
**Goal:** Identify everything that is MASCI-specific and would need swapping for a different contractor.

This is the **inventory of company-specific surface area** across the codebase. Each item is categorized by what kind of swap it would require.

---

## Headline metric

- **473** hits of `@mascigc.com` or `@mascidocs.com` across `backend/` + `frontend/src/`
- **108** MASCI literal hits in `backend/server.py` alone
- **134** MASCI hits in `frontend/src/lib/i18n.js` (translations — EN + ES bilingual copy)
- **128** MASCI hits in `backend/data/equipment_master.json` (real fleet roster)
- **8** hardcoded `MASCI_HUB_*` Content-Disposition filenames in `server.py`
- **1** FastAPI title literal (`server.py:34`)
- **1** HTML `<title>` literal (`index.html:75`)

These are **inventory metrics, not bug counts.** Each category below has its own swap strategy.

---

## Category 1 · Brand & identity surfaces

### 1A. App titles / window titles
| Location | Literal |
|---|---|
| `backend/server.py:34` | `FastAPI(title="MASCI Job Site Safety Inspection API")` |
| `frontend/public/index.html:75` | `<title>MASCI Operations Platform</title>` |

### 1B. Logo asset
| Location | Asset |
|---|---|
| `frontend/src/components/MasciLogo.jsx` | Three SVG variants (mark, wordmark, lockup) imported and rendered across all portal landings |
| `frontend/src/assets/forgedops-logo.png` | ForgedOps attribution mark (separate platform-vendor brand, not MASCI) |

### 1C. Brand footer / attribution
| Location | Literal |
|---|---|
| `backend/pdf_render.py:1484` | `MASCI General Contractors Inc. · 386-322-4500 · mascidocs.com` |
| `backend/backup_verification.py:454` | (same) |
| `backend/branded_portal_emails.py:80` | (same) |
| `frontend/src/components/JhaPlansPosterCard.jsx:62` | `386-322-4500` (phone literal) |

### 1D. Company info source of truth (the right pattern — already has localStorage swap)
| Location | Default values |
|---|---|
| `frontend/src/lib/companyInfo.js:6-17` | `DEFAULT_COMPANY_INFO = { company_name: "MASCI General Contractors Inc.", address: "5752 South Ridgewood Avenue", city_state_zip: "Port Orange, FL 32127-6442", phone: "386-322-4500", email: "safety@mascigc.com", website: "mascigc.com" }` |

**Note:** The frontend already supports per-device override via localStorage. The backend has no equivalent.

---

## Category 2 · PDF / export filename literals

All in `backend/server.py`:

| Line | Filename literal |
|---|---|
| 924 | `MASCI_HUB_Operations_Manual.pdf` |
| 938 | `MASCI_HUB_Operations_Manual.docx` |
| 961 | `MASCI_HUB_Operations_Manual.pdf` (variant) |
| 975 | `MASCI_HUB_Operations_Manual.docx` (variant) |
| 1057 | `MASCI_HUB_Operations_Manual_{stamp}.pdf` |
| 1078 | `MASCI_HUB_Operations_Manual_{stamp}.docx` |
| 1199 | `MASCI_HUB_Source_Bundle_{stamp}.zip` |
| 1335 | `MASCI_employees_{stamp}.xlsx` |
| 1347 | `MASCI_suppliers_{stamp}.xlsx` |
| 1374 | `MASCI_equipment_{stamp}.xlsx` |

Plus:
| Location | Filename |
|---|---|
| `backend/routes/safety_topic_library.py:468` | `MASCI_Safety_Topic_Pack.pdf` |
| `CSV/MASCI_{kind}_{stamp}.csv` (filesystem path) | Various |

**Total: ~15 PDF/export filename literals. All bake MASCI into the file the user downloads.**

---

## Category 3 · Email & notification copy

All in backend Python templates:

| Location | Sample copy |
|---|---|
| `backend/branded_portal_emails.py` | `Your MASCI HR Portal account has been created.` |
| (same) | `Your MASCI Safety Portal account has been created.` |
| (same) | `Your MASCI Field Leadership Portal account has been created.` |
| (same) | `We received a request to reset your MASCI HR Portal password.` |
| (server.py auto-email) | `<h2>MASCI Field Safety Card</h2>` |
| (server.py auto-email) | `Sent from MASCI Hub · Safety` |
| (server.py auto-email) | `<p>MASCI Operations Platform · Safety Forms · Auto-email</p>` |
| (backup_verification.py) | `The MASCI Hub backup scheduler has not produced a successful…` |
| (server.py admin emails) | `This message was sent from the MASCI HUB Admin Console…` |
| `backend/email_routing.py:14-72` | Hardcoded recipient lists: `["jaymn.judd@mascigc.com", "safety@mascigc.com"]`, `["shopmanager@mascigc.com"]` |

**All ~20+ email templates assume the customer is MASCI.**

---

## Category 4 · Legal documents (intentionally specific)

| Location | MASCI hit count | Treatment |
|---|---|---|
| `frontend/src/pages/legal/TermsOfService.jsx` | 45 | **KEEP MASCI-specific** — legal documents must name the contracting party |
| `frontend/src/pages/legal/PrivacyPolicy.jsx` | 30 | (same) |

These are **not productization blockers**; legal docs are tenant-specific by definition and will always need per-tenant authoring.

---

## Category 5 · Training & guidance content

| Location | MASCI hit count |
|---|---|
| `backend/guidance/content.py` | 52 |
| `backend/guidance/translations_es.py` | 47 |
| `backend/guidance/tips.py` | 24 |
| `backend/guidance/tips_es.py` | 23 |
| `backend/training_pdf.py` | 34 |
| `frontend/src/data/training.js` | 23 |

Sample copy (EN): `"A guided first-day checklist for every new MASCI hire: watch the core Field lessons, take a short quiz, sign an acknowledgement…"`

Sample copy (ES): `"Cada trabajo MASCI activo. Su propio PDF del Plan de Peligros. Un escaneo."`

These are **customer-authored operational content** rather than platform code. In a SaaS model they would become per-tenant content collections (CMS) or per-tenant copies of starter content.

---

## Category 6 · Real operational data

| Location | Content |
|---|---|
| `backend/data/equipment_master.json` (+ 8 backups) | 128 MASCI references each — actual fleet inventory |
| `backend/data/jobs_master.json` | Real MASCI project numbers (e.g., `25-21 SJR2C - Loop Trail - Spruce Creek`) + client names (City of Port Orange) + project managers (Ramon Rodriguez) |
| `frontend/src/components/AdminJobMasterPanel.jsx:672` | Hardcoded project sample data |

These are **data**, not code. In a SaaS deployment they would be tenant-scoped collections (or seeded per-tenant from a starter pack).

---

## Category 7 · Bilingual UI copy

`frontend/src/lib/i18n.js` — **134 MASCI hits.** Examples:

| EN | ES |
|---|---|
| `Capacitación MASCI` (Spanish key) | (translation paired in same file) |
| `Centro MASCI` | (Spanish key) |
| `Active MASCI jobs` | `Trabajos MASCI activos` |
| `Active MASCI maintenance holds.` | (paired) |
| `Admin Console · MASCI` | (paired) |

These are translation pairs that hardcode the company name in user-facing UI strings.

---

## Category 8 · Environment-file company assumptions

| Env var | Value |
|---|---|
| `ADMIN_PASSWORD` | `MASCI1982!` (year of MASCI founding embedded in default) |
| `SENDER_EMAIL` | `noreply@mascidocs.com` |
| `REPLY_TO_EMAIL` | `jaymn.judd@mascigc.com` |
| `BACKUP_EMAIL_TO` | `jaymn.judd@mascigc.com` |
| `OUTAGE_ALERT_TO` | `jaymn.judd@mascigc.com` |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `Maddix123!` |

All 7 env vars carry MASCI identity into the platform's operational behavior.

---

## Category 9 · Holiday / observance content

Sample literals (typically in `i18n.js` or content files):

- `"Christmas — From the MASCI Family"`
- `"To every veteran on our crews and every veteran in our families — thank you. The discipline, professionalism, and accountability you bring to this work makes MASCI better."`
- `"A serious incident has occurred on a MASCI project. All crews stop work immediately…"`

Holiday banners + safety stand-down messages name MASCI directly. They are **operationally meaningful but tenant-specific** — would need per-tenant CMS in a SaaS model.

---

## Category 10 · Test fixtures (acceptable as-is)

`backend/tests/` references MASCI in ~20 files. These are test fixtures and would **stay MASCI-named** in any productization path — tests assert MASCI-named seed data flows through correctly. Not a blocker.

---

## Volume summary by category

| Category | MASCI hits | Productization treatment |
|---|---|---|
| 1. Brand & identity | ~12 | Env-driven defaults; per-tenant override |
| 2. PDF / export filenames | ~15 | Env-driven defaults (`TENANT_NAME` placeholder) |
| 3. Email & notification copy | ~20 templates | Env-driven brand name; per-tenant template overrides |
| 4. Legal documents | ~75 | KEEP per-tenant (intentional) |
| 5. Training & guidance content | ~200 | Per-tenant CMS / starter content |
| 6. Real operational data | ~400 (data) | Per-tenant collections; not code |
| 7. Bilingual UI copy | 134 | Env-driven brand name token in `t()` |
| 8. Env vars | 7 | Already env-vars; just need per-tenant `.env` |
| 9. Holiday / observance | ~10 | Per-tenant CMS |
| 10. Test fixtures | ~20 files | KEEP MASCI-named (test artifacts) |

**Approximate total MASCI-specific surface area: ~890 references across ~50 files.**

**Productization treatment is straightforward but volumetric.** No single surface is a blocker; the work is volume sweeping with disciplined env-var + content-collection patterns.

---

## What is NOT MASCI-specific (the product core)

The rest of the codebase — RBAC matrix, lifecycle continuity, governance findings, CAPA pipeline, signal discipline, glossary terms, mobile compression patterns, audit trail mechanics — is platform infrastructure that would carry to any general contractor unchanged.

Detailed in `PRODUCT_CORE_BOUNDARY_MAP.md` (next document).

---

## Conclusion

The MASCI layer is **large but well-bounded**. Every category has a clear productization treatment. The work is:
- Plumbing (env vars + content collections + per-tenant overrides)
- Not architectural redesign

The platform's intellectual property — the operational discipline encoded in 9 prior phases — is **separate from the MASCI layer**. Productization is a sweeping exercise, not a rebuild.
