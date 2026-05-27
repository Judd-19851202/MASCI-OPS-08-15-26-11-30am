# Navigation Re-Architecture Plan — Phase IV

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 PLAN COMPLETE · EXECUTION INCREMENTAL · ZERO BREAKING URLs
**Source map:** `/app/memory/ADMIN_DOMAIN_MAP.json`
**Companion:** `/app/memory/ADMIN_INFORMATION_ARCHITECTURE.md`

---

## Migration principles (non-negotiable)

1. **Zero URL deletion.** Every existing `/admin/*` URL keeps responding for at least 90 days post-migration via shim/redirect.
2. **Single nav surface.** `AdminShell.jsx` remains the only sidebar. No duplicate nav systems are introduced.
3. **One domain per PR.** Each domain migration is its own branch + PR, < 500 LOC of nav changes.
4. **Regression suite mandatory between domains.** `pre_deploy_check.sh` must pass green between every domain migration.
5. **Mobile + iPad smoke required.** Each domain migration is validated against a mobile viewport before merge.

---

## Migration sequence (10 domains · safest-first)

The sequence is ordered by impact-on-real-users (low-impact first):

| Step | Domain | Rationale for ordering | Routes touched |
|---|---|---|---|
| 1 | **Governance** | Super-admin only · zero field-user impact | governance, operational-language, guidance-coverage, audit-log |
| 2 | **System Health** | Super-admin / admin only | system-health, deploy-readiness |
| 3 | **Data & Storage** | Admin-only · pure observability | database, system, deploy-recovery, legacy-imports |
| 4 | **Communications** | Admin-only outbound mail surface | email, digest-config |
| 5 | **Identity & Access** | Admin daily work but no mid-shift impact | people, mfa, sessions |
| 6 | **Safety & Compliance** | Admin/Safety · weekly cadence | qaqc, compliance, compliance-findings |
| 7 | **HR & Workforce** | Daily but predictable · iPad-locked SLA preserved | training, terminations, document-expirations |
| 8 | **Fleet & Equipment** | Mid-shift critical · shop relies on this | equipment, assets, leadership-equipment, jha, trench-boxes |
| 9 | **Operations** | Real-time field surface | inspections, meetings, operations-events, project-health |
| 10 | **Dispatch & Logistics** | The most volatile · last to migrate | dispatch, dls/*, asset-transfers |

Why this order: a regression in Governance affects 1 super-admin. A regression in Dispatch affects 12 dispatchers + every driver. Lower-impact domains migrate first so the team builds confidence in the migration pattern before touching mid-shift-critical surfaces.

---

## Per-domain migration checklist (apply to each PR)

```
[ ] Add new nav entry for the domain in AdminShell.jsx
[ ] Move the existing entries into a `children` group under the domain
[ ] Confirm every old URL still responds (no removals)
[ ] Add a domain-scope page header using the canonical pattern (UX_GOVERNANCE_STANDARD § Section headers)
[ ] Mobile screenshot at 375 × 812 (iPhone SE 3rd gen)
[ ] iPad screenshot at 820 × 1180 (iPad Air)
[ ] Run `bash /app/scripts/pre_deploy_check.sh` — must be 8/8 green
[ ] Run Playwright Phase III suite — must be 12/12 green
[ ] Verify nav-key data-testid contract (kebab-case · stable across migrations)
[ ] Write an entry in /app/memory/NAV_MIGRATION_LOG.md with the PR # + screenshots
```

---

## Target nav structure (`AdminShell.jsx` shape after Phase IV)

Two-tier sidebar. Top tier = 10 domains. Tap a domain → expands its children. The current 29 flat entries become 10 collapsible groups containing 32-ish leaf entries.

```
[OVERVIEW]                    /admin                       (always pinned at top)

[1] IDENTITY & ACCESS         /admin/identity
    └─ Portal users           /admin/people
    └─ MFA                    /admin/mfa
    └─ Sessions               /admin/sessions

[2] OPERATIONS                /admin/operations
    └─ Inspections            /admin/inspections
    └─ Meetings               /admin/meetings
    └─ Operations events      /admin/operations-events
    └─ Operational inventory  /admin/operational-inventory
    └─ Project health         /project-health

[3] FLEET & EQUIPMENT         /admin/fleet
    └─ Equipment              /admin/equipment
    └─ Leadership equipment   /admin/leadership-equipment
    └─ JHA plans              /admin/jha-plans
    └─ Trench boxes           /admin/trench-boxes

[4] DISPATCH & LOGISTICS      /admin/dispatch
    └─ Dispatch portal        /admin/dispatch
    └─ Shift QR               /admin/dls/shift-qr
    └─ Day-1 debrief          /admin/dls/day-1-debrief
    └─ Week-1 debrief         /admin/dls/week-1-debrief
    └─ Asset transfers        /asset-transfers

[5] HR & WORKFORCE            /admin/hr
    └─ People (HR slice)      /admin/people#hr
    └─ Training & forms       /admin/training
    └─ Terminations           /admin/terminations
    └─ Document expirations   /document-expirations

[6] SAFETY & COMPLIANCE       /admin/safety
    └─ QA/QC                  /admin/qaqc
    └─ Compliance             /admin/compliance
    └─ Compliance findings    /admin/compliance-findings

[7] COMMUNICATIONS            /admin/communications
    └─ Email & routing        /admin/email
    └─ Weekly digest          /admin/digest-config

[8] DATA & STORAGE            /admin/data
    └─ Database               /admin/database
    └─ System & backups       /admin/system
    └─ Deploy recovery        /admin/deploy-recovery
    └─ Legacy imports         /admin/legacy-imports

[9] SYSTEM HEALTH             /admin/health
    └─ System health          /admin/system-health
    └─ Deploy readiness       /admin/deploy-readiness

[10] GOVERNANCE               /admin/governance
    └─ Governance health      /admin/governance
    └─ Operational language   /admin/operational-language
    └─ Guidance coverage      /admin/guidance-coverage
    └─ Audit log              /admin/audit-log

—— FOOTER ——
Tasks & Actions               /tasks                    (cross-portal pinned)
PO Requests                   /po-requests              (cross-portal pinned)
Operational Guidance Center   /guidance                 (open to all roles)
Profile                       /admin/profile
```

The two pinned cross-portal items at the footer stay accessible from admin but visually separated from the 10 domains. Promo Assets, Analytics, and Integrations move into Governance (Analytics) and Communications (Integrations) respectively.

---

## Backward compatibility

Every old top-level entry remains as a deep-link. Examples:

- `/admin/people` still resolves the same component (sits inside Identity & Access AND HR & Workforce as a deep-link from each).
- `/admin/system-health` still resolves (sits inside System Health).
- `/admin/operations-events` still resolves (sits inside Operations).

Bookmarks, email deep-links, training docs, and operator muscle memory remain valid. The nav structure changes; URLs do not.

---

## Mobile behavior

- Below `md:`, the two-tier sidebar collapses to a single hamburger that opens a full-screen drawer.
- The drawer shows the 10 domains in a single column. Tapping a domain expands its children inline.
- Each leaf entry is ≥ 48 px tall (mobile touch target standard).
- iPad lands in `md:` — sidebar visible with both tiers expanded.

---

## Out-of-scope for this iteration

- Backend route changes (URLs do not move on the backend either).
- Permission model changes.
- New pages (this is reorganization only).
- Visual restyling beyond the canonical header pattern.

---

## Verdict

🟡 **PLAN COMPLETE.** The 10-domain target structure is locked. Implementation proceeds one domain at a time, lowest-impact first, with full regression after each step. The path is reversible at every step because no URL is ever deleted.
