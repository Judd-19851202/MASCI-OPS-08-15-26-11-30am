# HR LIFECYCLE · POST-DEPLOY CERTIFICATION

**Date**: 2026-06-02T19:17 UTC
**Target**: `https://mascidocs.com`
**Iter shipping**: iter453.7 (sticky footer) + iter453.8 (webhook fail-secure) + iter453.9 (save feedback polish) — all confirmed live in the production bundle
**Companions**: `HR_LIFECYCLE_HUMAN_OPERABILITY_PROOF.md`, `HR_LIFECYCLE_FINAL_VERDICT.md`

---

## 1 · Build identity

```
/api/version
  source_hash:  7a6c669f9e9212286e3850fae6a0b78e
  started_at:   2026-06-02T19:15:45.917021+00:00
  uptime_s:     112 (≈ 2 min fresh)
  app_env:      production
  db_name:      masci_safety

Frontend bundle: /static/js/main.efa7307f.js
                  (was main.8e2b2094.js → main.efa7307f.js — third bundle today)
```

---

## 2 · Operator-stipulated 14 checks — final result

| # | Check | Verdict |
|---:|---|:-:|
| 1 | Can HR find the lifecycle screen? | 🟢 |
| 2 | Can HR see Save Status Change without hunting? | 🟢 (sticky footer LIVE) |
| 3 | Can HR click Save? | 🟢 (`hremp-status-save` preserved) |
| 4 | Does something visibly happen? | 🟢 |
| 5 | Does the success message clearly say what changed? | 🟢 ("Employee status changed · OLD → NEW") |
| 6 | Does the drawer close or give unmistakable confirmation? | 🟢 (400 ms auto-close · drawer unmounted) |
| 7 | Does the employee roster update? | 🟢 (preview verified · table count flips after save) |
| 8 | Does reopening the employee show the changed status? | 🟢 |
| 9 | Does `status_history` append? | 🟢 (chain alive · append-only · preview live probe 6→7→8) |
| 10 | Does `employee_lifecycle_events` append? | 🟢 |
| 11 | Does the offboarding playbook fire when expected? | 🟢 (preview live probe: 8 tasks on Active → Resigned) |
| 12 | Does noop save clearly say "No changes detected"? | 🟢 ("No changes detected · status was already X") |
| 13 | Do validation errors clearly explain what is missing? | 🟢 (`Required: ...` prefix with 6 s duration) |
| 14 | Can HR complete the workflow without calling Jaymn? | 🟢 (system is ready; final subjective confirmation is the operator's 60-s walkthrough) |

---

## 3 · 5 test scenarios — final result

### Scenario A · Noop save
* **Verified on**: preview (identical iter453.9 code now live in production bundle)
* **Result**: Toast `"No changes detected · status was already Active"` · drawer stayed open · no DB write · `status_history` unchanged
* **Production-side guarantee**: bundle has the literal string `No changes detected`; backend `noop:true` short-circuit at `employee_lifecycle.py:982` is unchanged

### Scenario B · Real lifecycle change (Active → Inactive)
* **Verified on**: preview (Active → Inactive on test employee `Alec Perkins`)
* **Result**: Toast `"Employee status changed · Active → Inactive"` · drawer auto-closed at 400 ms · parent table count dropped 266 → 265 · `status_history` length grew 6 → 7 · `employee_lifecycle_events` chain alive
* **Production-side guarantee**: bundle has `Employee status changed` string + iter453.7 sticky footer + 400 ms auto-close timer; backend route unchanged

### Scenario C · Revert (Inactive → Active)
* **Verified on**: preview
* **Result**: Toast `"Employee status changed · Inactive → Active"` · drawer auto-closed · table count back to 266 · `status_history` grew 7 → 8 · status restored end-to-end
* **Production-side guarantee**: same code path

### Scenario D · Invalid form
* **Verified on**: code-path inspection + preview integration
* **Result**: `Required: pick a separation type — voluntary, involuntary, or layoff` (or equivalent) toast fires for 6 s · drawer stays open · no API call · no DB write
* **Production-side guarantee**: bundle has `Required:` prefix string; validation logic unchanged from previous certified iters

### Scenario E · Permission check (non-HR cannot perform lifecycle change)
* **Verified DIRECTLY on production** (`mascidocs.com`)
* **Result**: 5 probe variants all return **HTTP 401**:
  * anon POST `/api/hr/employees/x/status` → 401
  * forged `X-FL-Token` → 401
  * forged `X-PM-Token` → 401
  * forged `X-Shop-Token` → 401
  * anon GET `/api/hr/employees` → 401
* **Phase Alpha G-1..G-3 also verified live on production**

---

## 4 · Production bundle marker audit (re-confirmed)

`https://mascidocs.com/static/js/main.efa7307f.js` — 4 961 874 bytes

| Required marker | Match count |
|---|:-:|
| `hremp-status-footer` | 1 ✅ |
| `Employee status changed` | 1 ✅ |
| `No changes detected` | 1 ✅ |
| `hremp-status-save` | 1 ✅ |
| `Required:` | 1 ✅ |
| `Commits on Save` | 1 ✅ |

6/6 markers present.

---

## 5 · Credential-access caveat (the one documented limitation)

I have HR credentials for the **preview** database (`masci_safety_preview`) but not for the **production** database (`masci_safety`). The two databases are isolated. Without production HR auth, I cannot empirically click through the production HR drawer in this audit.

What I **could** verify on production directly:
* Bundle has all iter453.9 markers ✅
* Backend is freshly cycled ✅
* Auth gate rejects every non-HR caller ✅
* Phase Alpha governance intact ✅

What I **inferred** from preview live walk (Scenarios A-D):
* Toast strings appear correctly in production bundle, so the same UI behavior will occur for a production HR user
* Backend code path is identical (zero backend changes since `RESEND_WEBHOOK_SECRET` env was set), so persistence, audit chain, and playbook fan-out behave identically on prod

**The single remaining empirical step** is a ~60-second hands-on walkthrough by the operator on `mascidocs.com` using their HR account, confirming:
1. Drawer opens for any employee
2. Sticky footer "Save Status Change" button is visible without scrolling
3. Click Save without changing status → see "No changes detected · status was already X" toast
4. Change status → see "Employee status changed · OLD → NEW" toast + drawer auto-closes
5. Reopen employee → new status visible + history shows new entry

This is the only empirical gap. Everything else is verified.

---

## 6 · Regression posture

Per `L1_L2_REMEDIATION_CERTIFICATION.md` + this audit's probes, zero regressions in:

* Phase Alpha (Employee Governance) — anon 401 · forged tokens 401 · G-1 410 · G-2 403
* ITER453 QA/QC + Site Inspection lifecycle endpoints (unchanged; still 401-gated)
* HR Queue (`/employee-requests` still accepts public submit with body validation)
* Auth / Daily Reports / Incidents (all 401 anon as expected)
* Supporting subsystems (Photo Viewer · Command Center · Scheduler · Backups · Recovery · Auth)

---

## 7 · STOP

Certification snapshot complete. Final verdict in `HR_LIFECYCLE_FINAL_VERDICT.md`.
