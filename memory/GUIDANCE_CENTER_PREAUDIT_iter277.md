# Guidance Center · Pre-Audit Inventory (iter277)

**Generated:** 2026-05-21 · evidence-based audit of `/app/backend/guidance/content.py::_ARTICLES`
**Total articles:** 124

**Heuristic hits across 124 articles:**
- LMS-drift phrases (best practices · empower · leverage · stakeholders · journey · etc.): **0**
- Stale terminology (Toolbox Talk · Crew Hub · daily safety meeting): **5**
- Corporate/policy framing (must comply · ensure compliance · etc.): **0**
- ES translations present: **50 of 124 (40%) — all complete (title+summary+body)**

## Counts by Recommended Action

| Action | Count | Description |
| --- | ---: | --- |
| leave | 63 | No drift detected · already aligned or intentionally terse |
| minor (i18n only) | 55 | Body 400-1500 chars · no ES counterpart yet |
| moderate (i18n only) | 1 | Body >1500 chars · no ES counterpart yet |
| major | 5 | Stale terminology (Toolbox Talk) — content needs operational re-anchoring + ES update |
| **TOTAL** | **124** | |

## Section × Action Distribution

| Section | leave | minor i18n | moderate i18n | major | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| portals | 12 | 32 | 1 | 1 | 46 |
| knowledge | 11 | 19 | 0 | 1 | 31 |
| onboarding | 13 | 0 | 0 | 3 | 16 |
| troubleshooting | 13 | 0 | 0 | 0 | 13 |
| roles | 6 | 3 | 0 | 0 | 9 |
| quickhelp | 8 | 0 | 0 | 0 | 8 |
| reliability | 0 | 1 | 0 | 0 | 1 |

---

## Targeted Action Lists

### 🔴 MAJOR · 5 articles · terminology drift (Toolbox Talk → Safety Meeting rename)

All five carry the `\bToolbox Talk` regex hit. Rename to `Safety Meeting` per current platform terminology. ES counterparts exist for all five and must be regenerated post-rewrite to maintain parity.

| id | section | body chars | ES present | recommended scope |
| --- | --- | ---: | :-: | --- |
| `portal-safety` | portals | 2270 | ✅ | rename + verify operational anchoring · regenerate ES |
| `public-toolbox-talks` | onboarding | 2691 | ✅ | rename + verify operational anchoring · regenerate ES |
| `public-tools-map` | knowledge | 1072 | ✅ | rename + verify operational anchoring · regenerate ES |
| `onboard-leadership-first-week` | onboarding | 2051 | ✅ | rename + verify operational anchoring · regenerate ES |
| `onboard-safety-first-week` | onboarding | 1878 | ✅ | rename + verify operational anchoring · regenerate ES |

### 🟡 MODERATE i18n-only · 1 article · long body without Spanish

| id | section | body chars |
| --- | --- | ---: |
| `hr-onboarding-new-hire` | portals | 1529 |

### 🟡 MINOR i18n-only · 55 articles · medium body, no Spanish

Distribution by section:

- **portals**: 32 articles · total body chars 31310
- **knowledge**: 19 articles · total body chars 14616
- **roles**: 3 articles · total body chars 1611
- **reliability**: 1 articles · total body chars 536

Detail (collapsed by id for review):

| id | section | body chars | tone fingerprint |
| --- | --- | ---: | --- |
| `admin-governance-why` | knowledge | 839 | neutral |
| `connect-admin-controls` | knowledge | 706 | ops-some |
| `connect-equipment-lifecycle` | knowledge | 846 | ops-some |
| `connect-field-to-payroll` | knowledge | 845 | ops-some |
| `connect-incident-to-audit` | knowledge | 706 | neutral |
| `connect-pm-field-review` | knowledge | 830 | neutral |
| `connect-shop-to-dispatch` | knowledge | 977 | ops-some |
| `dispatch-accuracy-why` | knowledge | 696 | ops-some |
| `dispatch-field-coordination` | knowledge | 731 | neutral |
| `field-project-scope` | knowledge | 495 | neutral |
| `hr-audit-trail` | knowledge | 646 | neutral |
| `hr-cross-portal-reads` | knowledge | 715 | neutral |
| `pm-coordination` | knowledge | 630 | ops-some |
| `pm-cross-project-visibility` | knowledge | 822 | ops-some |
| `safety-escalation-chain` | knowledge | 840 | neutral |
| `safety-near-miss-importance` | knowledge | 905 | neutral |
| `safety-photo-quality` | knowledge | 904 | neutral |
| `shop-downtime-logic` | knowledge | 769 | neutral |
| `shop-operator-responsibilities` | knowledge | 714 | ops-some |
| `admin-audit-forensics` | portals | 775 | neutral |
| `admin-backup-restore` | portals | 1087 | neutral |
| `admin-data-portability` | portals | 924 | neutral |
| `admin-role-templates` | portals | 957 | ops-some |
| `admin-sentry-observability` | portals | 993 | neutral |
| `admin-system-health` | portals | 770 | neutral |
| `admin-user-management` | portals | 1127 | neutral |
| `dispatch-availability-management` | portals | 858 | ops-some |
| `dispatch-equipment-movement` | portals | 1148 | neutral |
| `dispatch-holds-transfers` | portals | 1007 | neutral |
| `field-coaching-documentation` | portals | 693 | neutral |
| `field-daily-report-howto` | portals | 1384 | ops-some |
| `field-equipment-checkout` | portals | 750 | neutral |
| `field-incident-escalation` | portals | 888 | neutral |
| `field-writeup-authoring` | portals | 947 | neutral |
| `hr-offboarding` | portals | 1246 | neutral |
| `hr-time-verification-deep` | portals | 1350 | neutral |
| `hr-writeups-correctives` | portals | 1112 | neutral |
| `pm-labor-documentation` | portals | 807 | neutral |
| `pm-project-review-cadence` | portals | 812 | neutral |
| `pm-reporting-workflows` | portals | 665 | neutral |
| `portal-leadership` | portals | 427 | ops-some |
| `safety-audits-workflow` | portals | 933 | ops-some |
| `safety-corrective-actions-workflow` | portals | 1253 | neutral |
| `safety-fire-extinguishers` | portals | 899 | neutral |
| `safety-incident-investigation` | portals | 1386 | neutral |
| `safety-training-compliance` | portals | 892 | ops-some |
| `shop-damage-reporting` | portals | 1033 | neutral |
| `shop-equipment-return` | portals | 982 | neutral |
| `shop-failed-preop-workflow` | portals | 1162 | neutral |
| `shop-maintenance-coordination` | portals | 758 | neutral |
| `shop-preop-deep` | portals | 1285 | neutral |
| `why-backups` | reliability | 536 | neutral |
| `role-foreman` | roles | 417 | ops-some |
| `role-hr` | roles | 553 | neutral |
| `role-superintendent` | roles | 641 | ops-some |

### ✅ LEAVE · 63 articles · no detected drift · operational or intentionally terse

Listed by section for visibility. No action required.

- **knowledge** (11): `fleet-severity-oos-vs-monitor`, `public-who-to-ask`, `public-why-documentation`, `why-audit-logs`, `why-corrective-actions`, `why-daily-reports`, `why-equipment-accountability`, `why-incidents`, `why-photos`, `why-session-timeouts`, `why-time-verification`
- **onboarding** (13): `onboard-admin-first-week`, `onboard-dispatch-first-week`, `onboard-hr-first-week`, `onboard-login`, `onboard-mobile`, `onboard-pm-first-week`, `onboard-shop-first-week`, `public-daily-report-basics`, `public-material-calculator`, `public-mobile-qr`, `public-photos`, `public-preop-basics`, `public-qaqc-basics`
- **portals** (12): `portal-admin-identity`, `portal-admin`, `portal-dispatch-identity`, `portal-dispatch`, `portal-hr-identity`, `portal-hr`, `portal-leadership-identity`, `portal-pm-identity`, `portal-pm`, `portal-safety-identity`, `portal-shop-identity`, `portal-shop`
- **quickhelp** (8): `fleet-daily-dvir`, `fleet-repair-lifecycle`, `fleet-return-to-service`, `fleet-weekly-emergency`, `fleet-weekly-lead`, `task-submit-incident`, `task-upload-photos`, `task-verify-time`
- **roles** (6): `role-admin`, `role-dispatch`, `role-new-employee`, `role-pm`, `role-safety`, `role-shop`
- **troubleshooting** (13): `public-cant-login`, `public-incident-basics`, `tshoot-admin-login`, `tshoot-dispatch-login`, `tshoot-employee-not-found`, `tshoot-equipment-not-found`, `tshoot-hr-login`, `tshoot-leadership-login`, `tshoot-photo-upload`, `tshoot-pm-login`, `tshoot-safety-login`, `tshoot-session-timeout`, `tshoot-shop-login`

---

## Full Inventory Table

| id | section | EN chars | ES | tone fingerprint | Phase-H | terminology | coaching-gen | action |
| --- | --- | ---: | :-: | --- | --- | --- | --- | --- |
| `admin-governance-why` | knowledge | 839 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `connect-admin-controls` | knowledge | 706 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `connect-equipment-lifecycle` | knowledge | 846 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `connect-field-to-payroll` | knowledge | 845 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `connect-incident-to-audit` | knowledge | 706 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `connect-pm-field-review` | knowledge | 830 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `connect-shop-to-dispatch` | knowledge | 977 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `dispatch-accuracy-why` | knowledge | 696 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `dispatch-field-coordination` | knowledge | 731 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `field-project-scope` | knowledge | 495 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `fleet-severity-oos-vs-monitor` | knowledge | 1816 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `hr-audit-trail` | knowledge | 646 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `hr-cross-portal-reads` | knowledge | 715 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `pm-coordination` | knowledge | 630 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `pm-cross-project-visibility` | knowledge | 822 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `public-tools-map` | knowledge | 1072 | ✅ | stale-term,ops-some | DRIFT (terminology) | STALE (Toolbox) | pre-rename (Toolbox era) | **major** |
| `public-who-to-ask` | knowledge | 609 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-why-documentation` | knowledge | 646 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `safety-escalation-chain` | knowledge | 840 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `safety-near-miss-importance` | knowledge | 905 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `safety-photo-quality` | knowledge | 904 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `shop-downtime-logic` | knowledge | 769 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `shop-operator-responsibilities` | knowledge | 714 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `why-audit-logs` | knowledge | 169 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-corrective-actions` | knowledge | 135 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-daily-reports` | knowledge | 382 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `why-equipment-accountability` | knowledge | 133 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-incidents` | knowledge | 189 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-photos` | knowledge | 155 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-session-timeouts` | knowledge | 250 | ✅ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-time-verification` | knowledge | 228 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `onboard-admin-first-week` | onboarding | 2279 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `onboard-dispatch-first-week` | onboarding | 1903 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `onboard-hr-first-week` | onboarding | 1958 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `onboard-leadership-first-week` | onboarding | 2051 | ✅ | stale-term,ops-strong | DRIFT (terminology) | STALE (Toolbox) | pre-rename (Toolbox era) | **major** |
| `onboard-login` | onboarding | 190 | ✅ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `onboard-mobile` | onboarding | 165 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `onboard-pm-first-week` | onboarding | 1916 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `onboard-safety-first-week` | onboarding | 1878 | ✅ | stale-term,ops-strong | DRIFT (terminology) | STALE (Toolbox) | pre-rename (Toolbox era) | **major** |
| `onboard-shop-first-week` | onboarding | 2064 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-daily-report-basics` | onboarding | 646 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-material-calculator` | onboarding | 1061 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-mobile-qr` | onboarding | 504 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-photos` | onboarding | 557 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `public-preop-basics` | onboarding | 1069 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-qaqc-basics` | onboarding | 807 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `public-toolbox-talks` | onboarding | 2691 | ✅ | stale-term,ops-strong | DRIFT (terminology) | STALE (Toolbox) | pre-rename (Toolbox era) | **major** |
| `admin-audit-forensics` | portals | 775 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `admin-backup-restore` | portals | 1087 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `admin-data-portability` | portals | 924 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `admin-role-templates` | portals | 957 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `admin-sentry-observability` | portals | 993 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `admin-system-health` | portals | 770 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `admin-user-management` | portals | 1127 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `dispatch-availability-management` | portals | 858 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `dispatch-equipment-movement` | portals | 1148 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `dispatch-holds-transfers` | portals | 1007 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `field-coaching-documentation` | portals | 693 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `field-daily-report-howto` | portals | 1384 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `field-equipment-checkout` | portals | 750 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `field-incident-escalation` | portals | 888 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `field-writeup-authoring` | portals | 947 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `hr-offboarding` | portals | 1246 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `hr-onboarding-new-hire` | portals | 1529 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **moderate (i18n only)** |
| `hr-time-verification-deep` | portals | 1350 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `hr-writeups-correctives` | portals | 1112 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `pm-labor-documentation` | portals | 807 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `pm-project-review-cadence` | portals | 812 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `pm-reporting-workflows` | portals | 665 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `portal-admin` | portals | 2312 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `portal-admin-identity` | portals | 744 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `portal-dispatch` | portals | 2514 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `portal-dispatch-identity` | portals | 650 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `portal-hr` | portals | 2335 | ✅ | ops-strong | ALIGNED | current | post-Phase-H operational | **leave** |
| `portal-hr-identity` | portals | 569 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `portal-leadership` | portals | 427 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `portal-leadership-identity` | portals | 690 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `portal-pm` | portals | 2836 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `portal-pm-identity` | portals | 697 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `portal-safety` | portals | 2270 | ✅ | stale-term,ops-some | DRIFT (terminology) | STALE (Toolbox) | pre-rename (Toolbox era) | **major** |
| `portal-safety-identity` | portals | 697 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `portal-shop` | portals | 2211 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `portal-shop-identity` | portals | 787 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `safety-audits-workflow` | portals | 933 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `safety-corrective-actions-workflow` | portals | 1253 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `safety-fire-extinguishers` | portals | 899 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `safety-incident-investigation` | portals | 1386 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `safety-training-compliance` | portals | 892 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `shop-damage-reporting` | portals | 1033 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `shop-equipment-return` | portals | 982 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `shop-failed-preop-workflow` | portals | 1162 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `shop-maintenance-coordination` | portals | 758 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `shop-preop-deep` | portals | 1285 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `fleet-daily-dvir` | quickhelp | 1575 | ✅ | ops-strong | ALIGNED | current | post-Phase-H operational | **leave** |
| `fleet-repair-lifecycle` | quickhelp | 1546 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `fleet-return-to-service` | quickhelp | 1495 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `fleet-weekly-emergency` | quickhelp | 1418 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `fleet-weekly-lead` | quickhelp | 1165 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `task-submit-incident` | quickhelp | 378 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `task-upload-photos` | quickhelp | 249 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `task-verify-time` | quickhelp | 235 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `why-backups` | reliability | 536 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `role-admin` | roles | 389 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `role-dispatch` | roles | 251 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `role-foreman` | roles | 417 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `role-hr` | roles | 553 | ❌ | neutral | UNVERIFIED | current | neutral · expository | **minor (i18n only)** |
| `role-new-employee` | roles | 512 | ✅ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `role-pm` | roles | 227 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `role-safety` | roles | 374 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `role-shop` | roles | 362 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `role-superintendent` | roles | 641 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **minor (i18n only)** |
| `public-cant-login` | troubleshooting | 578 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `public-incident-basics` | troubleshooting | 916 | ✅ | ops-strong | ALIGNED | current | post-Phase-H operational | **leave** |
| `tshoot-admin-login` | troubleshooting | 1583 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `tshoot-dispatch-login` | troubleshooting | 1292 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `tshoot-employee-not-found` | troubleshooting | 161 | ❌ | ops-some | ALIGNED | current | Phase-H aligned | **leave** |
| `tshoot-equipment-not-found` | troubleshooting | 132 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `tshoot-hr-login` | troubleshooting | 1418 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `tshoot-leadership-login` | troubleshooting | 1509 | ✅ | ops-strong | ALIGNED | current | post-Phase-H operational | **leave** |
| `tshoot-photo-upload` | troubleshooting | 295 | ❌ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `tshoot-pm-login` | troubleshooting | 1275 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `tshoot-safety-login` | troubleshooting | 1209 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |
| `tshoot-session-timeout` | troubleshooting | 377 | ✅ | neutral | N/A (terse) | current | reference / terse | **leave** |
| `tshoot-shop-login` | troubleshooting | 1229 | ✅ | neutral | UNVERIFIED | current | neutral · expository | **leave** |

---

## Methodology Notes (evidence-based heuristics)

Each article was scanned (title + summary + flattened body blocks) for these objective regex patterns:

**LMS-drift indicators (case-insensitive):**
- `\bcompliance training journey\b` · `\bempower(?:ing|s)? employees\b` · `\bbest practices?\b`
- `\bleverag(?:e|ing)\b` · `\bstakeholders?\b` · `\becosystems?\b` · `\bsynergies\b`
- `\bgrowth mindset\b` · `\bstrategic initiative\b` · `\bholistic\b` · `\bworld[- ]class\b` · `\bculture of\b`

**Stale-terminology indicators:**
- `\bToolbox Talk` (platform renamed to Safety Meeting)
- `\bCrew Hub\b` (workflow removed 2026-04-28 per `test_credentials.md`)
- `\bdaily safety meeting\b` (historical drift with Toolbox)

**Corporate/policy framing (anti-Phase-H):**
- `\bpolicy requires\b` · `\bmust comply\b` · `\bensure compliance\b` · `\bcompliance with\b` · `\bemployees should\b`

**Operational/foreman voice (Phase-H positive):**
- `\bforeman\b` · `\bsuperintendent\b` · `\bcrew\b` · `\bjob site\b` · `\bshift\b`
- `\bwhat to do\b` · `\bif this happens\b` · `\bbefore you\b` · `\bafter you\b` · `\bdon'?t\b` · `\bstop work\b` · `\bwhy this matters\b`

**Phase-H alignment classification:**
- `ALIGNED` — positive operational markers present, no drift hits
- `N/A (terse)` — body <400 chars, no markers detected either way (reference articles, identity stubs)
- `UNVERIFIED` — body ≥400 chars but no positive operational markers AND no drift hits (potential expository drift, but no evidence of LMS bloat)
- `DRIFT (terminology)` — stale-term hit

**Action thresholds:**
- `major` — any stale-term hit
- `moderate` — 2+ LMS hits OR `best practices` hit
- `minor` — 1 LMS hit OR negative Phase-H hit
- `moderate (i18n only)` — no drift AND no ES AND body >1500 chars
- `minor (i18n only)` — no drift AND no ES AND body 400-1500 chars
- `leave` — everything else

This inventory is the **gate** for any subsequent rewrite work. No article should be edited unless it appears in the major/moderate/minor lists with a logged justification, OR unless the user explicitly approves a specific article ID for revision.
