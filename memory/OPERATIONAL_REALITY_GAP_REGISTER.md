# OMEGA · OPERATIONAL REALITY GAP REGISTER

**Date:** 2026-06-02 · Companion to `OPERATIONAL_REALITY_AUDIT.md`
**Mode:** READ-ONLY · zero code · zero design
**Definition of "gap":** A capability needed for MASCI to run a heavy-civil GC entirely inside ForgedOps that is either absent, partial, or in violation of the Constitution.

---

## §0 · Legend

| Severity | Meaning |
|---|---|
| **G0** | Blocks day-to-day operations · workaround is daily friction |
| **G1** | Limits scalability or executive visibility · workaround is weekly friction |
| **G2** | Reduces field adoption or operational clarity · workaround is monthly friction |
| **G3** | Cosmetic / convenience / nice-to-have |

| Cluster | Meaning |
|---|---|
| **ABSENT** | No primitive · greenfield build required |
| **PARTIAL** | Some primitive exists · needs completion |
| **EXTERNAL** | Externally fulfilled today; integration decision required |
| **CONSTITUTIONAL** | Would violate Constitution if built as currently scoped · re-scope required |
| **TRIBAL** | Currently runs on tribal knowledge · should be captured as data |

---

## §1 · Gap register · 48 entries

### G0 · Blocks day-to-day operations (12)

| # | Gap | Area | Cluster | Workaround today |
|---:|---|---|---|---|
| G0-1 | **Job costing not in ForgedOps** | Financial · Executive · PM | EXTERNAL | Accounting system + spreadsheets |
| G0-2 | **Master schedule not in ForgedOps** | Operations · PM | EXTERNAL | P6 / MS Project + spreadsheet rollups |
| G0-3 | **Submittal workflow absent** | PM | ABSENT | Spreadsheet log + email + tribal knowledge |
| G0-4 | **RFI workflow absent** | PM | ABSENT | Spreadsheet log + email |
| G0-5 | **Change-order workflow absent** | PM · Financial | ABSENT | Spreadsheet + accounting system |
| G0-6 | **Pay-application workflow absent** | PM · Financial | ABSENT | Spreadsheet + accounting system |
| G0-7 | **Field clock-in/out per employee absent** | Field Ops · HR | ABSENT | Paper time tickets + Time Verification CSV |
| G0-8 | **Production tracking by activity absent** | Field Ops · PM · Executive | ABSENT | Daily Report free-text + spreadsheets |
| G0-9 | **Subcontractor management absent** | Operations · PM | ABSENT | Email + spreadsheets + phone |
| G0-10 | **Three parallel Corrective-Action systems** | Safety · Operations | PARTIAL | Manual cross-reference per incident |
| G0-11 | **0 / 736 user-level task assignment** | All areas | PARTIAL | Role-level only · "everyone owns it = nobody owns it" |
| G0-12 | **iter445 "Has crew reviewed JHP?" Yes/No field exists with no consumer** | Field Ops · Safety | CONSTITUTIONAL (FAIL-1) | Self-attestation field tolerated |

### G1 · Limits scalability or executive visibility (14)

| # | Gap | Area | Cluster | Workaround today |
|---:|---|---|---|---|
| G1-1 | **No executive role · login · portfolio view** | Executive | ABSENT | Email / spreadsheets / board packets |
| G1-2 | **No per-PM accountability scorecard** | Executive · Operations | ABSENT | Tribal knowledge |
| G1-3 | **No portfolio rollup (open work · trend · forecast)** | Executive · Operations | ABSENT | Spreadsheets / weekly operations meeting |
| G1-4 | **No backlog / bid-pipeline tracker** | Executive | ABSENT | CRM / spreadsheet |
| G1-5 | **No WIP schedule / forecast-to-complete** | Executive · Financial | EXTERNAL | Accounting + spreadsheet |
| G1-6 | **No OSHA 300/301 generator** | Safety · Executive | ABSENT | Spreadsheet · manual |
| G1-7 | **No Driver Qualification File workflow** | Fleet · HR | ABSENT | Paper DQ file |
| G1-8 | **No DOT compliance dashboard** | Fleet | ABSENT | ELD vendor + spreadsheet |
| G1-9 | **No performance review workflow** | HR | ABSENT | Spreadsheet + paper |
| G1-10 | **No discipline tracking workflow** | HR | ABSENT | Paper / file system |
| G1-11 | **No `manager_employee_id` on employees** | HR · Ownership | ABSENT | Tribal knowledge of who reports to whom |
| G1-12 | **No tenant_id propagation across 141 collections** | Customer #2 | ABSENT | N/A (single-tenant today) |
| G1-13 | **No multi-tenant auth / SSO / SAML / OIDC** | Customer #2 | ABSENT | Single MASCI auth |
| G1-14 | **No "what's open across the platform that I own" view** | All areas | ABSENT | Hub-by-hub navigation |

### G2 · Reduces field adoption or operational clarity (15)

| # | Gap | Area | Cluster | Workaround today |
|---:|---|---|---|---|
| G2-1 | **OC-003 QA/QC follow-up absent** | Safety · PM | PARTIAL | Tribal + email |
| G2-2 | **OC-004 Site Inspection follow-up absent** | Safety | PARTIAL | Tribal + email |
| G2-3 | **OC-008 PPE Return absent** | Safety · HR | ABSENT | Paper tracking |
| G2-4 | **Maintenance work-order system absent** | Equipment | ABSENT | Spreadsheet / paper tickets |
| G2-5 | **Equipment utilization-by-job absent** | Equipment · PM · Financial | ABSENT | Spreadsheet from Time Verification |
| G2-6 | **Fuel-card integration absent** | Equipment · Fleet · Financial | EXTERNAL | Vendor portal + spreadsheet |
| G2-7 | **OC-013 Onboarding multi-step partial** | HR | CONSTITUTIONAL (REPLACE-6) | Single-record + paper checklist |
| G2-8 | **OC-014 Offboarding multi-step partial** | HR | CONSTITUTIONAL (REPLACE-5) | Status mutator + paper |
| G2-9 | **Benefits administration absent** | HR | EXTERNAL | Benefits carrier portal |
| G2-10 | **ATS / recruiting pipeline absent** | HR | EXTERNAL or ABSENT | LinkedIn / Indeed + spreadsheet |
| G2-11 | **MSDS / SDS library absent** | Safety | EXTERNAL | Velocity / KHA / 3E vendor |
| G2-12 | **Drug-test pool tracking absent** | Safety · Fleet · HR | EXTERNAL | Vendor portal |
| G2-13 | **Workers comp claim integration absent** | Safety · HR | EXTERNAL | Carrier portal + paper |
| G2-14 | **Lien-waiver tracking absent** | PM · Financial | ABSENT | Spreadsheet + paper |
| G2-15 | **Meeting-minutes capture absent** | PM · Operations · Executive | ABSENT | Word doc + email |

### G3 · Cosmetic / convenience (7)

| # | Gap | Area | Cluster | Workaround today |
|---:|---|---|---|---|
| G3-1 | **OC-006 Safety Meeting amend absent** | Safety | PARTIAL | Re-file |
| G3-2 | **OC-016 Continuity Events edit/close absent** | Operations · Executive | PARTIAL | Re-enter |
| G3-3 | **OC-017 Safety digest fire surface relocation** | Safety · HR | PARTIAL | Safety impersonates Admin |
| G3-4 | **OC-019 Casing inconsistency (Open vs open)** | All | TRIBAL | Tolerated |
| G3-5 | **OC-022 Reopen actions in 14 workflows** | All | PARTIAL | Admin DB write |
| G3-6 | **OC-009 Photo Janitor absent** | Operations · All | ABSENT | Tolerated; R2 governance ALERT |
| G3-7 | **Closure-attestation modal Constitutional review** | Safety · PM | CONSTITUTIONAL (review · most PASS) | Existing closure modal · likely keep |

---

## §2 · Cluster tally

| Cluster | Count | Notes |
|---|---:|---|
| **ABSENT** | 22 | Greenfield build required |
| **PARTIAL** | 11 | Existing primitive · needs completion or re-scope |
| **EXTERNAL** | 9 | Externally fulfilled · integration decision required |
| **CONSTITUTIONAL** | 4 | Re-scope required per Constitution / Amendment 001 |
| **TRIBAL** | 2 | Should be captured as data |
| **TOTAL** | **48** | |

By severity:

| Severity | Count |
|---|---:|
| G0 | 12 |
| G1 | 14 |
| G2 | 15 |
| G3 | 7 |
| **TOTAL** | **48** |

---

## §3 · Workaround cost summary (qualitative)

| Workaround source | Gap items relying on it | Operator friction signal |
|---|---:|---|
| **Accounting / ERP** (QuickBooks · Sage · Foundation · Vista) | 5 (G0-1, G0-5, G0-6, G1-5, G2-14) | Highest single dependency · integration is unavoidable |
| **Spreadsheets** | 19 | Largest operational friction · pervasive across PM · HR · Fleet · Safety |
| **Phone / text / email** | 12 | Coordination workflows that should be structured |
| **Tribal knowledge / memory** | 8 | Cannot survive employee turnover · Customer #2 cannot inherit |
| **Paper / file system** | 6 | OSHA / DOT / HR compliance · highest legal exposure |
| **External vendor portals** | 7 | Benefits · ELD · drug-test · workers comp · MSDS |

---

## §4 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| 48 gaps catalogued with severity + cluster + workaround | ✅ |
| Constitutional cluster cross-cites prior Amendment 001 findings | ✅ |
| Workaround-cost summary surfaced for operator decisioning | ✅ |

🛑 **STOPPED.**
