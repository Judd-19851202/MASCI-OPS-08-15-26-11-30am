# ITER500 · WHITE LABEL READINESS REPORT

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY

Determine whether workflows are operationally complete, understandable, discoverable, and supportable by a **non-MASCI organization** under a white-label deployment.

---

## Architectural readiness

| Dimension | Status | Notes |
|---|:-:|---|
| Multi-tenancy | 🔴 NOT BUILT | App is single-tenant; MongoDB DB name `masci_safety` is per-deployment, not per-tenant |
| Branding / logo / color theme | 🟡 partial | `/app/frontend/src/components/` has theme tokens but org-name is hard-coded in several titles ("MASCI Safety Hub", "MASCI Documents") |
| Email-from address / Resend "from" domain | 🟡 | `safety@mascigc.com` referenced in code as the dead-letter / digest sender |
| Onboarding journey | 🔴 NOT BUILT | No self-onboarding flow |
| Per-org governance customization | 🔴 | Phase Alpha "HR is the sole authoritative owner" is a hardcoded principle, not configurable |
| Per-org workflow toggles | 🔴 | Cannot turn off JHA · QA/QC · Daily Reports for orgs that don't need them |
| Per-org status taxonomy | 🔴 | Status strings hardcoded throughout the codebase |
| Per-org locale / language | 🟡 | i18n wrapper `t()` exists but no real translation files |

## White-label workflow gaps

| Domain | Gap | Severity |
|---|---|:-:|
| HR Lifecycle | Constitutional principle hard-coded · cannot relax for orgs where HR is decentralized | 🔴 |
| Safety | Incident closure-action contract is opinionated · won't suit orgs with simpler safety frameworks | 🟡 |
| Operations | Dispatch board assumes MASCI-specific crew structures | 🟡 |
| Payroll | Pay-period boundaries hardcoded | 🟡 |
| QA/QC | Closure-action triplet (re-inspection / corrective_action / exception) is MASCI doctrine; other orgs may use different vocab | 🟡 |

---

## White Label Readiness score

* **Architectural readiness**: 🔴 ~ 25 % (single-tenant · hardcoded org name · no multi-org governance) 
* **Workflow readiness**: 🟢 ~ 70 % (most workflows are universally applicable construction-services patterns)
* **Branding readiness**: 🟡 ~ 50 % (theme tokens exist but org strings hardcoded)
* **Onboarding readiness**: 🔴 ~ 20 %

**Overall White Label Readiness %** ≈ **40 %**

Production-ready for additional MASCI-aligned customers (Customer #2) is possible at ~ 60 %. Production-ready for true white-label (non-construction-services or non-MASCI-doctrine orgs) requires substantial multi-tenancy and configurability work that is OUT OF SCOPE of this audit.

---

## STOP
