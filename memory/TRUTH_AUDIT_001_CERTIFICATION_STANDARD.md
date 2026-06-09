# TRUTH-AUDIT-001 · Mandatory Certification Standard

**Effective:** Immediately, for all future MASCI Operations Platform certifications.
**Authority:** ForgedOps doctrine · OMEGA directive TRUTH-AUDIT-001
**Replaces:** All prior ad-hoc certification headers (inconsistent across reports).

---

## Section 1 · The Four Required Fields

Every certification document MUST open with the following block, exactly:

```
Environment    : <preview | production | both | other-named-environment>
Access Level   : <see §2 enumeration>
Evidence Source: <see §3 enumeration>
Confidence     : VERIFIED | INFERRED | ASSUMED
```

A certification document that does NOT contain all four fields, with values drawn from the enumerations below, **automatically fails certification.** Operators must reject it on sight.

This is the entire doctrine. The rest of this document is its enumeration and rationale.

---

## Section 2 · Access Level enumeration

| Token | Meaning | Examples of operations enabled |
|---|---|---|
| `public-only` | HTTPS probes against publicly-routable endpoints with no authentication. | `curl https://mascidocs.com/api/health`; landing-page screenshots. |
| `preview-runtime+preview-DB` | Full root inside the preview fork pod + read/write on `masci_safety_preview` only. | Code edits to `/app`; `motor` client against preview DB; jest/pytest; supervisor restarts. |
| `prod-DB-read` | Read-only Mongo access to `masci_safety` via the shared Atlas credential. | `motor.find_one` on prod collections; row counts; index inspection. |
| `prod-DB-read+write` | Read AND write Mongo access to `masci_safety`. | `motor.update_one` on prod rows. **Requires explicit operator authorization in the certification body.** |
| `prod-admin-UI` | Authenticated session as admin in the production frontend. | Login → admin panels → cross-portal navigation. **Requires operator-supplied session token OR confirmed-shared credential from `test_credentials.md`.** |
| `prod-super-admin-UI` | Authenticated session as super-admin (MFA-stepped if enabled). | Bootstrap-level identity actions, directory CRUD, audit log inspection in UI. **Requires operator confirmation.** |
| `mixed` | The certification used multiple access levels for different sections — MUST enumerate which level was used per section in the body. | A typical post-deploy audit will use public-only + prod-DB-read + preview-runtime in different sections. |

If your access level is not in this list, write a custom one and explain it — but do NOT omit the field.

---

## Section 3 · Evidence Source enumeration

| Token | Meaning |
|---|---|
| `external-probe` | curl / wget / browser request against an externally-routable URL. |
| `preview-runtime` | bash / python / supervisor / log files inside the preview pod's `/app`. |
| `preview-DB` | direct Mongo queries against `masci_safety_preview`. |
| `prod-DB (read-only)` | direct Mongo queries against `masci_safety`, restricted to `find`, `count_documents`, `aggregate`, `index_information`. |
| `prod-DB (read/write)` | direct Mongo `insert`, `update`, `delete`, `bulk_write` against `masci_safety`. **Requires operator authorization, recorded inline.** |
| `operator-attested` | The certification's underlying fact was provided by the operator (e.g., a screenshot of the admin dashboard); the agent did not directly observe it. |
| `static-analysis` | Source code review; route / contract inspection; no runtime probe. |
| `existing-test-suite` | Running pre-existing jest / pytest tests and reporting their pass/fail signal. |
| `mixed` | Multiple — MUST enumerate sources used per section in the body. |

---

## Section 4 · Confidence enumeration

| Token | Meaning |
|---|---|
| `VERIFIED` | A primary-source observation captured in this audit directly demonstrates the claim. (e.g., direct Mongo read returned the value; curl returned the status code.) |
| `INFERRED` | The claim is derived from indirect evidence: behavior is consistent with the claim but the claim itself was not directly observed. (e.g., webhook returns 401 → secret IS configured.) |
| `ASSUMED` | The claim is held to be true but no observation in this audit demonstrates it. (e.g., "production deploys take less than 60 seconds" — true by historical experience but not measured here.) |

If you write something the operator must rely on, you MUST class it. A document with mixed confidence levels MUST class each section.

---

## Section 5 · Example header (correct)

```
# MOTIVE-PROD-INCIDENT-002 · Post-Remediation Health Audit

Environment    : production
Access Level   : prod-DB-read
Evidence Source: mixed (external-probe + prod-DB-read + preview-DB)
Confidence     : VERIFIED for §1-§3; INFERRED for §4 (Motive API call success); ASSUMED for §5 (operator email delivery)
```

## Section 6 · Example header (incorrect — fails certification)

```
# Some-Sprint Final Certification

Verdict: PASS
Date: 2026-06-09
```

This header is **rejected** because:
- No `Environment` field.
- No `Access Level` field.
- No `Evidence Source` field.
- No `Confidence` field.

---

## Section 7 · What this doctrine FIXES

| Prior failure mode | How the four fields fix it |
|---|---|
| Conflating "backend default DB binding" with "credential capability" (AUDIT-ACCESS-VERIFY-001 Q6) | `Access Level` field must be set from §2 enumeration — there is no token for "preview DB only" if the credential is cluster-level. The author is forced to confront the truth. |
| Claiming verdicts without disclosing whether prod was touched (POST-DEPLOY-002 §1 verdict) | `Evidence Source` field forces explicit disclosure of `prod-DB (read-only)` or `prod-DB (read/write)`. |
| Inferring credential state from webhook behavior and reporting it as fact (PROD-STABILIZE-001 § Phase 1 #1-2) | `Confidence` field forces author to mark INFERRED instead of VERIFIED when the evidence is indirect. |
| Mixing certification modes within one document silently | `Confidence` and `Evidence Source` allow `mixed` with a requirement to enumerate per section. |

## Section 8 · What this doctrine deliberately does NOT do

- It does NOT prescribe what verdicts certifications must reach. It only requires honesty about the evidence supporting them.
- It does NOT restrict access. The capability to read prod DB exists today; this doctrine just requires disclosure when that access is used.
- It does NOT replace the OMEGA constitution. The five filters (POWERFUL · SIMPLE · BEAUTIFUL · TRUSTED · PROVEN) still apply. This doctrine is *how* certifications satisfy TRUSTED + PROVEN.

---

## Section 9 · Audit standard for past reports

This doctrine is **forward-looking.** Prior certifications are not retroactively invalidated by missing headers; they are reconciled in `TRUTH_AUDIT_001_REPORT_RECONCILIATION.md`. Going forward, any new certification that does not include the four-field header is rejected.
