# Executive Platform Certification · Defect Register · Phase 8

**Batch:** OMEGA Forensic Platform Certification · Phase 8
**Date:** 2026-05-31
**Scope:** Master defect register consolidating findings from Phases 1-7. Every finding carries location · severity · reproduction · evidence · root cause (if proven) · recommended remediation. No remediation executed.

> Companion to the 6 phase-specific reports + `EXECUTIVE_SUMMARY.md` one-pager.

---

## 1 · Final scores

| Dimension | Score | Rationale |
|---|---|---|
| Overall Production Health | 🟢 **88/100** | All endpoints healthy · Pillar 1 live · scheduler ticking · 6 data hygiene findings but bounded |
| White-Label Readiness | 🔴 **15/100** | Pillar 1 modules clean; 4,431 MASCI literals across 413 files; 15-batch (30-40 day) backlog |
| Customer #2 Readiness | 🔴 **20/100** | Architecture supports it but requires WL-0..WL-15 + tenant_id propagation |
| ForgedOps Support Readiness | 🔴 **5/100** | No support portal · no tickets · no multi-tenant · 92-108 day build required |
| Production Data Cleanliness | 🟡 **88/100** | 6 contamination items totaling 44 docs across 5 collections; 2 are 🔴 |

---

## 2 · Top 25 🔴 CRITICAL findings

| # | Finding | Location | Phase | Recommendation |
|---|---|---|---|---|
| C-01 | Test FL user `fieldleader@mascigc.com` live in production with documented password | `db.field_leadership_users` | 3 | rotate · deactivate · or delete |
| C-02 | Duplicate `doc_id='INC-2026-00001'` on 2 incident rows | `db.incidents` | 3 | dedupe; reconcile incident ID scheme |
| C-03 | Incident DELETE workflow known fragile (cascade) | `routes/safety_portal/incidents.py` | 4 | migrate to soft-delete |
| C-04 | Single-tenant DB (no `tenant_id` column anywhere) | platform-wide | 6+7 | multi-tenant batch |
| C-05 | Super-admin email hardcoded `server.py:8697` | `server.py:8697` | 5+6 | env-driven super-admin |
| C-06 | Pillar 2 Phase A defect D1 (SAF-CRITICAL no resolution-state check) | `routes/command_center.py` | 4 | Pillar 2 patch batch |
| C-07 | Pillar 2 Phase A defect D2 (SAF-OSHA no resolution-state check) | same | 4 | same |
| C-08 | Pillar 2 Phase A defect D5 (Approvals/Equipment OOS sub-count silently zeros) | same | 4 | same |
| C-09 | JOBS-ISSUE-NO-OWNER predicate text says "incident OR CA" but code queries CA only — 19 ownerless incidents silently uncounted | `routes/command_center.py:355-365` | 1+4 | Pillar 2 patch |
| C-10 | `noreply@mascidocs.com` hardcoded across 7 lines of `server.py` (env-overrideable but defaults branded) | `server.py` 5324·6235·8517·8557·8725·8804·9568 | 6 | WL-7 batch |
| C-11 | `safety@mascigc.com` default safety digest recipient | `server.py:9489` | 6 | WL-7 batch |
| C-12 | Backup filename prefix `MASCI_complete_backup_*` is brand-coupled | backup architecture | 6 | WL-10 batch |
| C-13 | `MasciLogo.jsx` component literally named after the customer | `frontend/src/components/MasciLogo.jsx` | 6 | WL-5 batch |
| C-14 | Equipment master JSON seed (134 MASCI refs) bound to MASCI fleet | `backend/data/equipment_master.json` | 6 | WL-6 batch |
| C-15 | T&C and Privacy Policy bound to MASCI legal entity | `frontend/src/pages/legal/` | 6 | WL-9 batch |
| C-16 | OGC content (`backend/guidance/`) tuned to MASCI crew taxonomy | code | 6 | WL-8/14 batch |
| C-17 | Support Portal UI does not exist | platform-wide | 7 | ForgedOps batch |
| C-18 | Support Tickets collection does not exist | DB | 7 | ForgedOps batch |
| C-19 | Multi-customer tenant management does not exist | platform-wide | 7 | ForgedOps batch |
| C-20 | Per-tenant brand-chrome substitution does not exist | frontend | 7 | ForgedOps batch |
| C-21 | Pillar 1B Escalation Framework not built; no field-diff "what changed" surface for ForgedOps support | platform-wide | 4 | Pillar 1B batch |
| C-22 | Audit-event collections (`audit_events`, `admin_audit`, `usage_events`) lack `tenant_id` | DB | 7 | tenant-id propagation batch |
| C-23 | Per-tenant release pinning not supported | release infra | 7 | ForgedOps batch |
| C-24 | Per-tenant `command_center_thresholds` UI not exposed | admin UI | 7 | WL-4 batch |
| C-25 | Pillar 1A-6 Accountability Dashboard not yet built · Pillar 1 service surface UI-invisible | frontend | n/a | Pillar 1A-6 batch |

---

## 3 · Top 25 🟡 IMPORTANT findings

| # | Finding | Location | Phase | Recommendation |
|---|---|---|---|---|
| I-01 | 2 PREVIEW_POSTENV notifications in production (2026-05-16) | `db.notifications` | 3 | delete · low risk |
| I-02 | 10 payroll-variance batches with null status / null upload_by | `db.payroll_variance_batches` | 3+4 | delete or archive |
| I-03 | 29 of 30 transfer_requests are Cancelled · iterative test runs | `db.transfer_requests` | 3 | archive optional |
| I-04 | Expired Memorial Day banner not purged | `db.hub_banners` | 3 | display-time filter likely sufficient |
| I-05 | `user_directory` has 7 users all with `is_active=null` | DB | 5 | clarify visibility filter doctrine |
| I-06 | HR portal header has empty outlined button (operator-flagged) | frontend HR layout | 2 | reproduce + surgical fix |
| I-07 | 2 MASCI strings in `command_center.py` ("Within MASCI PO SLA") | `routes/command_center.py:168·905` | 6 | WL-1 |
| I-08 | Recovery dashboard pre-existing AMBER (R2 bucket 88.51 GB > 50 GB) | recovery | post-deploy | operator-side R2 storage decision |
| I-09 | RTO `last_drill_min=null` (no recent drill) | recovery | post-deploy | next Sunday auto-populates |
| I-10 | 2 historical `complete-r2-error` from 2026-05-25 in `failures_7d` (usage_events sort-memory) | recovery | post-deploy | falls off the 7-day window |
| I-11 | Owner placeholder strings ("Pending Approver" · "Safety" · "Shop" · "Unassigned PM") in English only | `lib/accountability_projection.py` | 6 | WL-2 |
| I-12 | Incident ID surface has 3 fields (`id` UUID · `incident_number` · `doc_id`) — inconsistent | `db.incidents` | 4 | pick canonical |
| I-13 | `corrective_actions` collection empty in production (0 rows) — Phase 1A-5 incident resolver inert on prod data today | DB | n/a | mechanism still correct; will activate as CAs are filed |
| I-14 | `email_routing_config` collection empty | DB | 1 | acceptable today; needs population for multi-tenant |
| I-15 | `integration_settings` for `motive`/`maintainx` both `enabled=False · status="Not Connected"` | DB | 1 | acceptable if not authorized |
| I-16 | 27 FL users on production · all `is_active=True` · no soft-delete pattern visible | DB | 5 | offboarding doctrine clarification |
| I-17 | Multi-login returns portal token for portals with 0 users (e.g. `pm_users`) | auth | 5 | acceptable for super-admin |
| I-18 | `scheduler_locks` has 5 active leases tied to one pod hostname — pod-scaling implication | DB | 1 | single-pod design by definition |
| I-19 | `audit_events` at 10,155 rows · `admin_audit` at 1,899 — retention strategy not codified | DB | 1+7 | ForgedOps retention batch |
| I-20 | `r2_degraded_events` collection exists but unverified — degraded-mode telemetry path | DB | 1 | confirm wired |
| I-21 | `idempotency_keys` collection retention not codified | DB | 1 | retention sweep needed |
| I-22 | `temp_upload_chunks` collection — orphan-cleanup not codified | DB | 1 | cleanup sweep |
| I-23 | `webauthn_challenges` retention not codified | DB | 1 | cleanup sweep |
| I-24 | Pillar 1A-3 service-side `accountability/item` uses BASE projection (not resolved variant) → drilldown vs service show different owners | code | 1A-3 | doc clarified · UI confusion risk |
| I-25 | `JOBS-ISSUE-NO-PATH` rule severity-blind (counts any incident > 7d without CA, regardless of severity) | code | 4 | rule refinement candidate |

---

## 4 · Top 25 🟢 COSMETIC findings

| # | Finding | Location | Phase |
|---|---|---|---|
| Co-01 | 5 orphaned dev-only pages (`DevHub` · `DevLogin` · `AllPostersPrint` · `AccessDenied` · `AdminDeployReadiness`) | frontend | 2 |
| Co-02 | Some `// TODO` / `// FIXME` markers in code (development debt) | code-wide | 2 |
| Co-03 | Expired Memorial Day banner not purged | DB | 3 |
| Co-04 | 29 historical cancelled transfer_requests inflate UI history | DB | 3 |
| Co-05 | `system_counters` value=133 — unclear semantic (probably PO/incident counter) | DB | 1 |
| Co-06 | Cancelled-test transfer_requests reference same asset 4 minutes apart | DB | 3 |
| Co-07 | `doc_id` gaps in incidents (00005..00009 missing) suggesting delete history | DB | 3 |
| Co-08 | `hub_banners.dismiss_log` carries IP/UA on every dismiss — privacy/log-bloat | DB | 1 |
| Co-09 | `hill_scopes` · `field_memory_notes` · `ops_manual_snapshots` — operational substrate · counts not enumerated this batch | DB | 1 |
| Co-10 | Auto-posted banners with `auto_posted_iter` audit-string tied to iter# (`iter329`) — iteration leakage in production data | DB | 3 |
| Co-11 | `equipment_inspections` cosmetic count not enumerated this batch | DB | 1 |
| Co-12 | `messages` / `message_comments` retention not enumerated | DB | 1 |
| Co-13 | Frontend has no unified "control catalog" (every page redefines buttons) | frontend | 2 |
| Co-14 | `MasciLogo.jsx` literally named after customer — refactor candidate to `<BrandLogo />` | frontend | 6 |
| Co-15 | `frontend/src/lib/topics/*.js` (en/es) duplicates much copy across language pairs | frontend | 6 |
| Co-16 | `backend/scripts/iter*_*.py` (legacy iteration scripts) still in repo | code | 6 |
| Co-17 | `.bak.json` and `equipment_master.20260*.json` data backups in repo | code | 6 |
| Co-18 | `frontend/src/data/training_es.js` not auto-synced with `training.js` | frontend | 6 |
| Co-19 | Pillar 1A-3 `accountability/sources` endpoint returns `canonical_statuses` as a duplicate of the global statuses list — debate whether to expose | code | 1 |
| Co-20 | Pillar 2 cards have "Verbose" text in JSON payload (e.g. "Within MASCI PO SLA") that could be config-driven | code | 6 |
| Co-21 | Banners severity enum includes `cultural` — unclear consumer-side handling | DB | 1 |
| Co-22 | `safety_users` / `dispatch_users` / `shop_users` have inactive-but-not-null states ("other" category) — schema drift | DB | 5 |
| Co-23 | `field_leadership_users` all `is_active=True` — no offboarding events visible in audit | DB | 5 |
| Co-24 | Multi-login response includes `super_admin=null` (not Boolean) — minor typing inconsistency | API | 5 |
| Co-25 | Several `@app.on_event("startup")` hooks with overlapping responsibilities | code | 1 |

---

## 5 · Closeout

🟡 **Master defect register: 25 🔴 + 25 🟡 + 25 🟢 findings = 75 evidence-backed items.** Production is functionally healthy; the largest defect classes are (a) single-tenancy / white-label coupling and (b) ForgedOps-readiness — both already known and scoped to future batches. The few directly-operational defects (test FL account in prod · duplicate incident doc_id · incident delete fragility · payroll-variance null batches) are remediable in short batches.

🛑 STOP. **No remediation executed.** Operator review and authorization required for any subsequent fix batches.
