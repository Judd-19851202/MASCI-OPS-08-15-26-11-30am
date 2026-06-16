# ADMIN V1 vs V2 — GAP MATRIX

**Phase 16 deliverable (Track 15.0). Audit-only. No migration. No default flip.**

## Default

- **V1** is currently the production default (`AdminShell.jsx` SECTIONS array).
- **V2** lives at `/admin-v2-preview` (or is mounted via the V2 feature flag) and reads from `/app/frontend/src/components/admin/sidebar/domainMap.js`. Per platform memory, V2 is feature-flagged off in production.

## Route Coverage Matrix

| Route | Section | V1 | V2 | Notes |
|-------|---------|----|----|-------|
| `/admin` | Overview | ✅ | ❌ implicit | V2 lands on overview but has no explicit nav row |
| `/admin/command-center` | Command Center | ✅ | ❌ MISSING | **Gap G1** — V2 audit-only sidebar lacks executive single-glass |
| `/admin/people` | People & Access | ✅ | ✅ | parity |
| `/admin/jobs` | Jobs & Field | ✅ | ✅ | parity |
| `/admin/equipment` | Equipment & Suppliers | ✅ | ✅ | parity |
| `/admin/asset-admin` | Asset Administration | ✅ | ❌ MISSING | **Gap G2** — canonical taxonomy review queue absent from V2 |
| `/admin/email` | Email & Routing | ✅ | ✅ | parity |
| `/admin/training` | Training & Forms | ✅ | ✅ | parity |
| `/admin/compliance` | Compliance & Audits | ✅ | ✅ | parity |
| `/tasks` | Tasks & Actions | ✅ | ✅ (footer) | parity |
| `/document-expirations` | Document Expirations | ✅ | ✅ | parity (D-A20 closed) |
| `/po-requests` | PO Requests | ✅ | ✅ (footer) | parity |
| `/project-health` | Project Health | ✅ | ✅ | parity |
| `/asset-transfers` | Asset Transfers | ✅ | ✅ | parity |
| `/admin/dispatch` | Dispatch Portal | ✅ | ✅ | parity |
| `/admin/operations-events` | Operations Events | ✅ | ✅ | parity |
| `/operational-records` | Operational Records | ✅ (D-A15 fix) | ❌ MISSING | **Gap G3** — V2 has `/odr/center` (Operational Daily Records, different model) but not `/operational-records` (Phase V.1 cross-portal records) |
| `/odr/center` | Operational Daily Records | ❌ MISSING | ✅ | **Gap G4** — V1 lacks the FLL-aware ODR center |
| `/operations-actions` | Operations Actions | ✅ (D-A15 fix) | ✅ | parity (both updated this session) |
| `/admin/integrations` | Integrations | ✅ | ✅ | parity |
| `/admin/system` | System & Backups | ✅ | ✅ | parity |
| `/admin/system-health` | System Health | ✅ | ✅ | parity |
| `/admin/database` | Database | ✅ | ✅ | parity |
| `/admin/digest-config` | Weekly Digest | ✅ | ✅ | parity |
| `/admin/audit-log` | Audit Log | ✅ | ✅ | parity |
| `/admin/sessions` | Sessions | ✅ | ✅ | parity |
| `/admin/deploy-recovery` | Deploy Recovery | ✅ | ✅ | parity |
| `/admin/deploy-readiness` | Deploy Readiness | ✅ | ✅ | parity |
| `/admin/analytics` | Usage Analytics | ✅ | ✅ | parity |
| `/guidance` | Operational Guidance Center | ✅ | ✅ (footer) | parity |
| `/admin/operational-inventory` | Operational Inventory | ❌ MISSING | ✅ | **Gap G5** — V2-only coverage matrix |
| `/admin/governance` | Governance Health | ❌ MISSING | ✅ | **Gap G6** — V2-only cross-portal contradiction score |
| `/admin/operational-language` | Operational Language | ❌ MISSING | ✅ | **Gap G7** — V2-only shared EN/ES glossary |
| `/admin/promo-assets` | Promo Assets | ❌ MISSING | ✅ | **Gap G8** — V2-only cinematic clip library |

## Numeric summary

- **V1**: 32 sections, all reachable, production default.
- **V2**: 36 routes covered, feature-flagged off in production.
- **Routes in V1 but not V2**: 3 critical (Command Center · Asset Administration · Operational Records).
- **Routes in V2 but not V1**: 5 (ODR Center · Operational Inventory · Governance Health · Operational Language · Promo Assets).

## Friction comparison

| Dimension | V1 | V2 | Verdict |
|-----------|----|----|---------|
| Flat vs grouped nav | Flat 32-section list | 5-domain accordion (Operations · People & Compliance · Equipment · Communications · Compliance & Governance · Infrastructure) | V2 is more navigable as count grows; V1 wins on raw discoverability (no clicks to reveal). |
| Mobile / iPad behavior | Mobile sheet drawer with all 32 entries scrollable | Same drawer + accordion collapsing | V2 better on small screens once accordion state persists. |
| Onboarding new admins | Steep — 32 items visible at once | Easier — domains reveal context | V2 wins. |
| Power-user speed | Faster — 1 click anywhere | 2 clicks (open domain → click) | V1 wins. |
| Maintenance discipline | Anyone adding a route to V1 must touch the flat SECTIONS array (visible diff) | Adding a route to V2 requires picking a domain (intentional thought) | V2 wins. |

## Gap conclusions

- **G1 (V2 missing Command Center)** — DEFER. Adding Command Center to V2 is a 1-line config change but only matters when V2 becomes default. **Recommended action**: when V2 promotion track opens, add it.
- **G2 (V2 missing Asset Administration)** — same as G1. Tracked.
- **G3 (V2 missing Operational Records)** — same. Note V2 chose `/odr/center` which is a *different* concept (FLL-aware ODR rollups vs cross-portal Phase V.1 records). Both should live in V2.
- **G4 (V1 missing ODR Center)** — **Could be safely added to V1 today.** Adding 1 sidebar entry — safe, additive, no permission change. Recommend adding to V1 as part of this fix-as-you-go pass.
- **G5–G8 (V2-only features)** — DEFER. These were intentionally piloted in V2. Promoting them to V1 means promoting the workflow itself; not in this track's scope.

## Recommendation

- **DO NOT migrate** V1 → V2 in this track. The user explicitly forbids architecture work here.
- **SAFE FIX-AS-YOU-GO**: add `/odr/center` to V1 sidebar (closes G4 — 1-line additive change · no permission change · no migration).
- **DEFER everything else** to a future "V2 promotion track" when (a) V2 has feature parity for G1/G2/G3 and (b) the user authorizes the default flip.

## Risk if promoted prematurely

- Admins who depend on Command Center, Asset Administration, or Operational Records would lose 1-click access if V2 became default without G1/G2/G3 closed first.
- G5-G8 routes are powerful tools but never validated by daily operations — they would catch admins off-guard if surfaced as primary nav without onboarding.

## Status

🟡 **DOCUMENT-ONLY AUDIT COMPLETE.** No migration. No default flip. One safe fix-as-you-go applied (G4 closed inline in Track 15).
