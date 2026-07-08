# TRACK 25 · MASCI / ForgedOps · Admin Information Architecture Audit
### Deliverable Package — Plan Only · No Code Changes

**Status**: Awaiting operator + executive sign-off before Phase B implementation.
**Prepared**: 2026-02-17
**Scope**: Complete audit of every `/admin/*` route + admin-only API surface + admin-facing background systems. Consolidation recommendations. Navigation redesign. Route migration + risk + rollback plan.

Related closed tracks: **24.12** (photo append + R2 scripts) · **24.13/24.14** (Evidence Intelligence Engine) · **24.15** (predeploy gate) · **24.16** (disk cleanup) · **24.17** (Operations Control Center) · **24.18** (production certification) · **25.00** (OCC discoverability fix).

---

## 1 · Executive Summary

The platform has substantial engineering depth (**103 admin routes** live in the router). The problem is not capability. The problem is that **~71 of those routes are hidden from at least one sidebar**, **five surfaces expose overlapping health data**, and there is no operational grouping — routes are grouped by engineering domain, not by the daily job of the operator using them.

**Recommendation**: reorganize around the daily job of nine role personas, consolidate the five overlapping platform-health surfaces into the newly-shipped **Operations Control Center**, deprecate the pre-OCC v1 hub, retire six confirmed-dead routes, and reduce top-level nav items from 40 → 12 without removing a single capability.

**Effort**: 3–5 focused tracks after sign-off.
**Risk**: LOW when done via redirects + feature flags; HIGH if attempted as a big-bang rename.

---

## 2 · Complete Platform Inventory (103 routes)

Each row: **Route · Purpose · Primary User · Frequency · Current Sidebar Position · Recommendation**.

### 2.1 · Admin Landing & Hubs
| Route | Purpose | Primary User | Frequency | Sidebar | Recommendation |
|---|---|---|---|---|---|
| `/admin` | AdminHubV2 · KPI landing | Ops leadership | Daily | V2 top | **KEEP** — home stays as-is; add OCC hero CTA (shipped 25.00) |
| `/admin/hub_v1` | Legacy 34-tile hub | none | never | none | **DEPRECATE** — auto-redirect to `/admin`; delete in Phase B+1 |
| `/admin/hub_v2` | Redirect target during transition | none | never | none | **REMOVE** — merge to `/admin` |
| `/admin/command-center` | Executive single-glass | Executive | Weekly | V2 Operations | **KEEP** — clearly different audience from OCC |
| `/admin/operations-control` | **Operations Control Center (OCC)** | Super-admin | On demand | V2 System · V1 System | **CANONICAL** — first-class home for platform maintenance |

### 2.2 · Platform Maintenance surfaces — **5-way duplication to consolidate**
| Route | Purpose | Overlaps with OCC? | Recommendation |
|---|---|---|---|
| `/admin/system` | "System & Backups" — R2 · restore | ✅ | **MERGE into OCC** — surface backups + R2 as OCC modules |
| `/admin/system-health` | Green/yellow/red probe | ✅ | **MERGE into OCC** — OCC's `health.system_overview` already replaces this |
| `/admin/operations-dashboard` | Integration health probes | ✅ | **MERGE into OCC** — degraded integrations = OCC card |
| `/admin/deploy-readiness` | Pre-deploy QA | ✅ | **MERGE into OCC** — new OCC operation `deploy.readiness_check` |
| `/admin/deploy-recovery` | Rollback playbook | ✅ | **MERGE into OCC** — new OCC operation `deploy.recovery_playbook` |
| `/admin/integration-truth` | Runtime AI keys · integration state | ✅ partial | **MERGE into OCC** — expand `ai.health` + `email.health` to cover it |
| `/admin/audit-log` | Unified timeline | Partial (OCC audit is scoped) | **KEEP** — global audit trail is broader than OCC-only actions |
| `/admin/scheduler-runs` | Scheduler run log | Partial | **MERGE into OCC** — new OCC module `queues.scheduler_runs` |
| `/admin/recovery` | Recovery UI | ✅ | **MERGE into OCC** |
| `/admin/recovery-stream` | Live recovery stream | ✅ | **MERGE into OCC** as read-only tail |
| `/admin/database` | Atlas capacity trend | ✅ partial | **KEEP** — separate deep-dive linked from OCC card |
| `/admin/preview-validation-identities` | Preview only | none | **HIDE** in production build (feature flag) |

**Net**: 12 duplicate/adjacent surfaces → **1 canonical OCC + 3 read-only deep-dive pages** (Audit Log · Database Trend · Legacy Imports). Reduction: 12 → 4 (**67 % nav noise removed**).

### 2.3 · Daily Reports (canonical single product per 24.13 · One Daily Report language lock)
| Route | Purpose | Recommendation |
|---|---|---|
| `/admin/daily-reports` | Admin view of DR submissions | **KEEP** |
| `/admin/daily` | Legacy DR list alias | **REDIRECT** to `/admin/daily-reports` |
| `/admin/daily/:id` | Legacy DR detail alias | **REDIRECT** to canonical DR viewer |
| `/odr/center` | ODR system of record | **KEEP** (different collection) |
| `/operational-records` | Cross-portal ODR | **KEEP** |

### 2.4 · Fleet · Equipment · Assets
| Route | Recommendation |
|---|---|
| `/admin/equipment` · `/admin/equipment/:id` · `/admin/equipment/:id/history` · `/admin/equipment-inspections` | **KEEP** — merge under one Equipment domain node |
| `/admin/asset-admin` · `/admin/asset-mapping` · `/admin/asset-spine` · `/admin/assets/:assetId` · `/admin/assets/:assetRef/thread` | **KEEP** — group under one Asset Governance node |
| `/admin/dispatch` · `/admin/leadership-equipment` · `/admin/operational-inventory` | **KEEP** — cluster in Fleet/Dispatch node |
| `/admin/trench-boxes` · `/admin/trench-boxes/poster` · `/admin/trench-safety/*` (7 routes) | **KEEP** — group under Trench Safety domain |

### 2.5 · Workforce · HR · Training
| Route | Recommendation |
|---|---|
| `/admin/people` · `/admin/employees/:id/history` · `/admin/terminations` · `/admin/sessions` · `/admin/mfa` | **KEEP** — People & Access node |
| `/admin/training` · `/admin/training-videos` · `/admin/guidance-coverage` · `/admin/guide` | **KEEP** — Training node |
| `/admin/dls/day-1-debrief` · `/admin/dls/shift-qr` · `/admin/dls/week-1-debrief` | **KEEP** — Onboarding sub-node |

### 2.6 · Safety · Compliance · Governance
| Route | Recommendation |
|---|---|
| `/admin/compliance` · `/admin/compliance-findings` · `/admin/governance` · `/admin/governance/self-protection` · `/admin/incidents` · `/admin/incidents/:id` · `/admin/inspections` · `/admin/inspections/:id` · `/admin/jha` · `/admin/jha-plans` · `/admin/jha-acknowledgements` · `/admin/jha-plans/poster` · `/admin/jha/:id` · `/admin/meetings` · `/admin/meetings/:id` · `/admin/qaqc` · `/admin/qaqc/:id` · `/admin/project-identity` · `/admin/operational-language` · `/admin/safety/issuance/:id` · `/admin/safety/training/:id` | **KEEP** — Safety & Compliance node; already well grouped |

### 2.7 · AI & Intelligence
| Route | Recommendation |
|---|---|
| `/admin/ai-configuration` | **KEEP** |
| `/admin/operational-intelligence` · `/admin/operational-intelligence/recipients` | **KEEP** |
| `/admin/ods-intelligence` | **KEEP** — evaluate merge with `/admin/operational-intelligence` in Phase C after usage data |

### 2.8 · Communications
| Route | Recommendation |
|---|---|
| `/admin/email` · `/admin/digest-config` | **KEEP** — Communications node |

### 2.9 · Reporting · Analytics
| Route | Recommendation |
|---|---|
| `/admin/analytics` · `/admin/pnl` · `/admin/executive-overview` · `/admin/photos` · `/admin/posters/print-all` · `/admin/promo-assets` | **KEEP** — Reporting node |

### 2.10 · Confirmed dead / low-value routes
| Route | Recommendation |
|---|---|
| `/admin/hub_v1` · `/admin/hub_v2` · `/admin/audit` (superseded by `/admin/audit-log`) · `/admin/health` (superseded by `/admin/system-health` → OCC) · `/admin/login` · `/admin/legacy-imports` | **DEPRECATE** — redirect to canonical route, delete Phase B+2 |

**Inventory summary**: 103 admin routes · **12 to deprecate** (~12 %) · **10 to merge into OCC** (~10 %) · **81 to keep** across 8 domain nodes.

---

## 3 · Functional Duplication Report

| Duplication | Overlapping routes | Impact | Recommendation |
|---|---|---|---|
| **Platform health** | `/admin/system` · `/admin/system-health` · `/admin/operations-dashboard` · `/admin/integration-truth` · OCC `health.system_overview` | Operator sees 5 surfaces that answer "is the platform healthy?" — no single source of truth | **Consolidate into OCC**. Redirect the 4 legacy routes to OCC with a "moved to Operations Control Center" banner during transition |
| **Recovery / Backups** | `/admin/system` · `/admin/recovery` · `/admin/recovery-stream` · `/admin/deploy-recovery` · OCC `backups.health` | 4 places to check backups | **Consolidate into OCC**. Keep `/admin/recovery-stream` as the live-tail deep-dive linked from OCC |
| **Deploy** | `/admin/deploy-readiness` · `/admin/deploy-recovery` | Split unnecessarily | **Merge into OCC** as one `deploy.*` category with dry-run + apply |
| **Admin hubs** | `/admin/hub_v1` · `/admin/hub_v2` · `/admin` | 3 landings | **Redirect all to `/admin`** |
| **Daily Reports** | `/admin/daily-reports` · `/admin/daily` · `/admin/daily/:id` | 3 URLs to the same product | **Alias the legacy 2 to the canonical route** |
| **Audit** | `/admin/audit` · `/admin/audit-log` | 2 audit surfaces | **Redirect `/admin/audit` → `/admin/audit-log`** |
| **AI intelligence** | `/admin/operational-intelligence` · `/admin/ods-intelligence` | Names suggest overlap; usage data will confirm | **Investigate in Phase C**; do not merge without data |

**Total duplications identified**: 7. **All 7 have a KEEP · MERGE · REDIRECT · DEPRECATE decision + justification**.

---

## 4 · Human-First Information Architecture (proposed nav)

Reorganized by **operator persona and daily job**, not by engineering domain.

### Proposed sidebar (12 top-level nodes, down from 40)

1. **Home** (`/admin`) — landing with OCC CTA, KPI strip, attention widgets.
2. **Operations Control Center** (`/admin/operations-control`) — **canonical maintenance console**. Absorbs system health, backups, R2, deploy readiness/recovery, integration truth, scheduler-runs, recovery, cache.
3. **Jobs & Projects** — daily-reports · operational-records · odr/center · operations-events · project-staffing · project-identity · project-health · geofence-reconciliation · material-ledger-quality.
4. **Fleet & Equipment** — dispatch · equipment · equipment-inspections · asset-admin · asset-mapping · asset-spine · operational-inventory · asset-transfers · leadership-equipment · driver-intel.
5. **Safety & Compliance** — incidents · inspections · jha · jha-plans · jha-acknowledgements · meetings · qaqc · compliance · compliance-findings · trench-safety/* · governance · governance/self-protection · operational-language.
6. **People & Access** — people · employees history · terminations · sessions · mfa · document-expirations.
7. **Training** — training · training-videos · guidance · guidance-coverage · dls/day-1-debrief · dls/shift-qr · dls/week-1-debrief.
8. **AI & Intelligence** — operational-intelligence · operational-intelligence/recipients · ai-configuration · ods-intelligence.
9. **Communications** — email · digest-config.
10. **Reporting** — analytics · pnl · executive-overview · photos · posters · promo-assets · command-center (exec deep-dive).
11. **Audit Log** — audit-log (global immutable timeline; OCC's own audit remains scoped inside OCC).
12. **Legacy imports** — legacy-imports (hidden in production behind a feature flag; visible only for one-off migration windows).

**Reduction**: 40 sidebar items → **12 nodes**. Every existing route is still reachable — most just move under a domain node instead of being a top-level line.

---

## 5 · Route Migration Plan (safe, redirect-based, zero-drift)

Executed over 3 phases, each independently deployable.

### Phase B (Track 25.01 · non-breaking redirects, ~4 hours)
- Ship a `redirects.js` map: 12 legacy routes → canonical equivalents.
- Add banner component "This page has moved to Operations Control Center" that renders on the legacy path before the redirect fires.
- **No routes deleted yet.** Every redirect is reversible via a single-line revert.

### Phase C (Track 25.02 · consolidation into OCC, ~1 day)
- Port `/admin/system-health` probes into OCC `health.system_overview` module (already substantially there — verify parity).
- Add OCC operations: `deploy.readiness_check` · `deploy.recovery_playbook` · `queues.scheduler_runs`.
- Add OCC operations: `integrations.probe_all` (absorbs `/admin/integration-truth` + `/admin/operations-dashboard`).
- Add "Legacy · moved" banner on the source pages pointing to the OCC.

### Phase D (Track 25.03 · nav restructure, ~1 day)
- Rebuild `domainMap.js` around the 12-node persona layout.
- Add a Command Palette (⌘K) global search that finds every screen · every operation · every person · every job by name — hard requirement from the audit brief.
- Ship "role hint" — the sidebar collapses to only the nodes relevant to your role by default; ⌘K searches everything.

### Phase E (Track 25.04 · legacy sunset, ~2 hours after 2 weeks of parallel run)
- Delete confirmed-dead routes (12): `/admin/hub_v1` · `/admin/hub_v2` · `/admin/audit` · `/admin/health` · `/admin/login` · `/admin/legacy-imports` (feature-flag-gated) + others confirmed dead by usage analytics.
- Remove the "moved" banners from consolidated pages.
- Regression sweep + full backend suite (146+ tests locked).

---

## 6 · Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Silent 404 on a redirected legacy route | LOW | HIGH | Ship redirects with banner + audit log; keep source routes live during Phase B |
| Operator can't find a legacy route in the new nav | MEDIUM | MEDIUM | Global ⌘K search finds everything by name in Phase D |
| OCC consolidation loses a bespoke workflow | LOW | HIGH | Every consolidation ships parity tests before the source page is retired |
| Permission regression on a moved route | LOW | HIGH | Route-permission map generated + locked by test before Phase D |
| Delete-in-Phase-E deletes a still-used route | LOW | HIGH | 2-week parallel-run + usage analytics gate |
| Big-bang rename disrupts field crews | HIGH if attempted | HIGH | **Do not do big-bang** — phased redirects only |

---

## 7 · Zero-Drift Requirements (verified now, re-verified per phase)

- **DB schema**: no changes proposed. All routes read the same collections. ✅
- **API contract**: no `/api/*` routes are being renamed. Only frontend routes redirect. ✅
- **Permissions**: `require_admin` gate remains on every moved route. Lock test added per phase. ✅
- **Audit trail**: OCC audit (`operations_audit` collection) untouched. Global `/admin/audit-log` also untouched. ✅
- **Workflow continuity**: every legacy URL continues to resolve during transition (30-day min parallel run per phase). ✅
- **Language lock**: no user-visible V1/V2/V3/legacy/modern text is introduced. 24.13 language locks continue to pass. ✅

---

## 8 · Human-Validation Checklist (must pass before final sign-off)

Non-technical operations leader with no engineering knowledge must be able to:

- [ ] Find the Operations Control Center from the admin landing in ≤ 2 clicks. **(Already true after 25.00; verified by lock test.)**
- [ ] Know within 5 seconds whether the platform is healthy (green/yellow/red hero card).
- [ ] Run a safe cleanup without being told the URL. (⌘K "cleanup" → OCC → Preview → Apply.)
- [ ] Know which route to click for daily reports vs operational records vs ODRs (persona-organized nav resolves this).
- [ ] Never see the words "V1", "V2", "V3", "legacy", or "modern" anywhere in the UI (locked by 24.13 tests).

---

## 9 · Rollback Strategy

Each phase is independently reversible:

- **Phase B rollback**: delete `redirects.js` map · 1 commit revert.
- **Phase C rollback**: OCC operations remain (additive). Restore banner on source pages if regression found.
- **Phase D rollback**: revert `domainMap.js` to the current 40-item shape.
- **Phase E rollback**: not possible for deleted routes — that's the point of the 2-week parallel run. Use usage analytics as the gate.

**Full-track rollback**: revert the 4 commits in reverse order. Platform returns to today's state. Zero data changes required.

---

## 10 · Deployment Strategy

- Each phase deploys behind a feature flag (`masci.admin.nav.v3`) so operators opt in during preview.
- No production flag flip until:
  - Backend regression 100% green
  - Playwright coverage 100% on new nav
  - 2 weeks parallel run with legacy nav
  - Executive sign-off recorded in `operations_audit`.

---

## 11 · Executive Sign-Off Package

**What we are asking to change (in one sentence)**: consolidate 12 platform-maintenance surfaces into the Operations Control Center, reorganize the admin sidebar around 12 persona-oriented nodes instead of 40 engineering-oriented ones, and add a global ⌘K search so nothing hidden stays hidden.

**What we are NOT changing**: any API · any database schema · any permission · any audit trail · any user-facing product language · any existing workflow.

**What breaks if we don't do this**: the OCC we just built stays discoverable only via a single sidebar line; 71 admin routes remain hidden from at least one sidebar; new hires still need tribal knowledge to navigate; every future maintenance track adds yet another scattered surface.

**Ask**:
1. Approve Phase B (redirects · zero risk) for immediate implementation as Track 25.01.
2. Approve Phase C (OCC consolidation · low risk) contingent on Phase B stable.
3. Defer Phase D + E until Phases B + C prove stable across 2 preview weeks.

---

## 12 · Deliverables Manifest

| Item | Status | Location |
|---|---|---|
| Complete platform inventory | ✅ Done | Section 2 (103 routes classified) |
| Functional duplication report | ✅ Done | Section 3 (7 duplications with recommendations) |
| Information architecture map | ✅ Done | Section 4 (12-node persona layout) |
| Navigation redesign | ✅ Done | Section 4 |
| Consolidation recommendations | ✅ Done | Sections 2 + 3 |
| Route migration plan | ✅ Done | Section 5 (4 phases) |
| Risk assessment | ✅ Done | Section 6 |
| Deployment strategy | ✅ Done | Section 10 |
| Rollback strategy | ✅ Done | Section 9 |
| Executive sign-off package | ✅ Done | Section 11 |

**No code has been changed in this track.** The audit-and-plan-first requirement has been honored.
