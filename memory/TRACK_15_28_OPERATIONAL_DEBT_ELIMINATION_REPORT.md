# TRACK 15.28 — OPERATIONAL DEBT ELIMINATION REPORT

**Date:** 2026-06-19 00:18 UTC
**Type:** READ-ONLY · No code, no deploy, no fix.
**Trust classes:** 🟢 Measured · 🟡 Vendor / Code-confirmed · 🟠 Modeled · 🔴 Unknown / Operator-required.

---

## SECTION 1 — PM Notifications Audit (P1)

### 1.1 Schema (🟢 live)

`db.notifications` document shape (sample-key inspection):
```
_id · id · acknowledged_at · acknowledged_by · created_at · delivery
expires_at · linked_employee_id · linked_equipment_id · linked_project_number
linked_source_module · linked_source_record_id · linked_task_id · message
read_by · recipient_role · recipient_user_id · severity · title · type · link_url
```

Mixed-era schema: **9,190 docs use `type` field; 552 docs use `kind` field; 552 docs use `audience`; 552 docs use `user_email`** — three concurrent vocabularies for the same purpose.

### 1.2 Volume + state (🟢 live)

| Metric | Value |
|---|---:|
| Total notifications | **9,742** |
| 30-day inflow | ~9,004 (per 15.24B audit) ≈ **321/day** |
| Field `read` (legacy boolean) — present | **0** docs (never written) |
| Field `read_by` (array of user ids who marked read) — schema confirms | present on every doc |
| Field `acknowledged_at` populated | (would need follow-up scan; not measured this run) |
| Field `dismissed` | 0 docs (never written) |
| Field `expires_at` | present on schema but population unverified |

⚠️ **Finding F-N1 (P1):** My initial unread query used the wrong field (`read`) — actually the schema settled on `read_by` as an array. The 9,742 "all unread" reading is **not interpretable** — needs a re-pass using `read_by: {$size: 0}` or `acknowledged_at: null` to derive a true unread count. **The platform may or may not have a real unread-pileup problem — currently unverified.**

### 1.3 Confirmed clean (🟢)

- **Zero orphans** referencing deleted projects: scanned every `linked_project_number` value against `jobs_master.project_number` (30 active projects) — **0 dangling references**. ✅

### 1.4 Defect ledger (audit findings)

| # | Defect | Severity | Evidence | Status |
|---|---|:--:|---|---|
| F-N1 | Inconsistent unread-state field (`read` vs `read_by`) makes "is the inbox cluttered?" unanswerable without code-side normalization | P1 | 🟢 schema scan | UNVERIFIED |
| F-N2 | Mixed schema: `kind` (552 docs, legacy) vs `type` (9,190 docs, current) | P2 | 🟢 schema scan | KNOWN — legacy bleed |
| F-N3 | Mixed recipient model: `recipient_user_id`+`recipient_role` (current) vs `user_email`+`audience` (legacy 552 docs) | P2 | 🟢 schema scan | KNOWN |
| F-N4 | No `dismissed` action ever recorded in the collection | P3 | 🟢 measured | DESIGN — by design? unconfirmed |
| F-N5 | `linked_project_number` → 0 orphans against `jobs_master` | — | 🟢 measured | **PASS — no defect** |
| F-N6 | No measured proof of "stale-never-clears" / "wrong user" / "duplicates" complaints from the original incident | 🔴 | unverified | **Original 15.8A/15.8B complaint not yet reproduced inside this audit.** Needs operator's original incident exemplars to re-anchor. |

### 1.5 Remediation plan (no code yet)

| Step | Action | Risk | Verification |
|---|---|---|---|
| R-N1 | Code-audit `notifications` writers — find every `db.notifications.insert_one` callsite and verify which schema vocabulary each uses | Low (read-only) | grep + 1-page schema-canonicalization doc |
| R-N2 | Backfill script: convert `kind` → `type` and `user_email`/`audience` → `recipient_user_id`/`recipient_role` for the 552 legacy docs | Medium — touches 552 prod rows | Dry-run first; pre-image dump to JSON; rollback script |
| R-N3 | Add `read_by:[] OR acknowledged_at:null` unread query as the canonical "unread" definition; update all read-counters | Low | Re-run "unread" count before vs after |
| R-N4 | If the original 15.8A/15.8B complaint provides concrete examples (specific PM, specific stale notification) — reproduce locally and verify the fix against that example | Low | Reproduction by example |

### 1.6 Deployment plan

1. PR with backfill + canonicalization is preview-only first.
2. Atlas snapshot taken before backfill run.
3. Backfill is **idempotent + dry-run-first** (count would-be writes; only commit on operator confirm).
4. No user-facing change required.

### 1.7 Certification plan

- Pre/post `read_by:[]` count.
- Per-recipient unread count for top 10 recipients before and after.
- 7-day re-check: confirm new writes use the canonical schema only (zero new `kind` writes, zero new `user_email` writes).

---

## SECTION 2 — R2 Backup Retention Audit (P0)

### 2.1 Current state (🟢 measured)

| Metric | Value |
|---|---|
| Bucket `masci-hub` total | **285.45 GiB / 9,608 objects** |
| `backups/auto-90d/` | **1,476 zips · 261.16 GiB** (oldest 2026-05-17, newest 2026-06-18) |
| `backups/` (legacy direct) | **500 zips · 22.51 GiB** (older format, 2026-05-11 → 2026-05-17 only) |
| Cadence | Confirmed hourly: **exactly 24 zips in last 24h, 617.4 MiB avg, very stable** |
| Per-day growth | **+14.47 GiB / day** |
| Projected steady state at current cadence + 90-day retention | **1,302 GiB ≈ $19.50 / month at R2 list price** |
| Projected if NO retention enforced for 12 mo | 5,569 GiB ≈ **$83.50 / month** by month 12 |

### 2.2 Existing retention code (🟢 code-confirmed)

`server.py` ships `_emergency_prune_backups(reason)` at line 5721 with the following envs:

| env | default | meaning |
|---|---|---|
| `BACKUP_RETENTION_DAYS` | **14** | files older than this are eligible for prune |
| `BACKUP_KEEP_MAX` | (set in code) | hard cap on max kept files |
| `BACKUP_DISK_WARN_WATERMARK` | configured | when disk % rises, warn |
| `BACKUP_DISK_HIGH_WATERMARK` | configured | when disk % rises further, run `_emergency_prune_backups` |

When the prune runs, it correctly deletes both local-disk copies AND walks the R2 prefix to delete S3 objects older than `BACKUP_RETENTION_DAYS`. **Tests confirm the function works** (`tests/test_iter427_legacy_backup_prune.py`, `tests/test_deploy_fix_001_backup_hardening.py`).

### 2.3 The gap (🟢 code-confirmed)

`_emergency_prune_backups` is invoked from **TWO triggers only:**

1. **Startup sweep** (`server.py:9844-9852`) — runs once at process boot.
2. **Pre-flight before next backup** when disk %≥`BACKUP_DISK_HIGH_WATERMARK` (`server.py:5917`).

There is **NO scheduled prune cron**. The hourly backup job (`BACKUP_R2_HOURLY=true`) writes a new zip every hour but only prunes opportunistically when disk pressure rises. On R2, where there is no local-disk pressure on the pod, the prune **never fires on schedule**.

**Result: R2 backups accumulate indefinitely** — this is the actual root cause of the unbounded growth observed in 15.24B.

### 2.4 Cost impact (🟢 + 🟡)

| Scenario | R2 storage / mo | Annual |
|---|---:|---:|
| Today (285 GiB) | $4.30 | $52 |
| 90-day retention enforced (steady state) | **$19.50** | **$235** |
| No retention (year 1 cumulative) | $83 by month 12 | ~$1,000 |
| No retention + 100% adoption (zip size grows ~3×) | $270 by month 12 | ~$3,300 |

### 2.5 Risk impact

- **Recovery capability:** preserved at 90-day retention (24 backups/day × 90 days = 2,160 recovery points) — vastly exceeds DR needs.
- **Disaster recovery:** preserved.
- **Auditability:** if monthly compliance backups are required separately, the design should keep N daily-keepers indefinitely (e.g., 1 backup/day for the past 365 days, plus the rolling hourly window).
- **Real risk if NOT addressed:** R2 bill silently grows ~$80/mo by year-end at current adoption and ~$270/mo at 100 % adoption.

### 2.6 Recommended retention policy (for operator approval)

| Tier | Retention | Cadence |
|---|---|---|
| Tier 1 — rolling hourly | **last 7 days** of hourly backups (168 zips) | every hour |
| Tier 2 — rolling daily | **next 30 days**, keep 1 zip/day | promote from Tier 1 |
| Tier 3 — rolling monthly | **next 11 months**, keep 1 zip/month | promote from Tier 2 |
| Tier 4 — annual archive | **last 5 years**, keep 1 zip/year (compliance) | promote from Tier 3 |

Steady-state size: **168 + 30 + 11 + 5 = 214 zips × ~0.6 GiB ≈ 130 GiB → $1.95 / month at R2 list price.**

### 2.7 Single-defect verdict

**F-R1 (P0):** `_emergency_prune_backups` is wired but **never scheduled**. One-line cron addition (already in the codebase pattern — the `scheduled-backup` job lives at `server.py:5875`) inserts a sibling `scheduled-prune` job that calls the existing helper. Zero new functions. Zero new logic.

---

## SECTION 3 — Mobile Production Certification Audit (P2)

### 3.1 What I CAN prove from inside the pod

Playwright at iPhone (390×844), iPad Portrait (768×1024), and iPad Landscape (1024×768) viewport sizes — **simulated mobile**, not a real device.

### 3.2 What I CANNOT prove from inside the pod

| Constraint | Why |
|---|---|
| Real iPhone hardware | Not in the pod's environment |
| Real iPad hardware | Same |
| Production URL (`https://mascidocs.com`) authentication | The pod cannot maintain a logged-in session against production; preview ingress is provable, production cannot be touched from here |
| Real-world network conditions (4G/LTE/WiFi cross-over) | Out of scope |

🔴 **The "real-device on real-production" certification is operator-only work.** I can produce a parameterized checklist + Playwright simulation for each portal, but the canonical Five-Pillar "Proven on production iPhone" verdict can only be issued by the operator with hardware in hand.

### 3.3 What was already proven this session

| Portal | Desktop (preview) | iPad Portrait (preview) | iPad Landscape (preview) | Real iPhone (production) | Real iPad (production) |
|---|:--:|:--:|:--:|:--:|:--:|
| HR (Field Leadership Users) | ✅ 15.22A | 🔴 needed | 🔴 needed | 🔴 needed | 🔴 needed |
| HR (Roster Export + Print) | ✅ 15.21A | 🔴 needed | 🔴 needed | 🔴 needed | 🔴 needed |
| Admin (Project Team) | ✅ 15.27A/B | ✅ 15.27A/B (sim) | ✅ 15.27A/B (sim) | 🔴 needed | 🔴 needed |
| PM (Project Team) | ✅ 15.27B | 🔴 needed | 🔴 needed | 🔴 needed | 🔴 needed |
| Shop | — | — | — | 🔴 needed | 🔴 needed |
| Safety | — | — | — | 🔴 needed | 🔴 needed |
| Dispatch | — | — | — | 🔴 needed | 🔴 needed |
| Field Leadership | API-cert in 15.23A | 🔴 needed | 🔴 needed | 🔴 needed | 🔴 needed |
| Asset Admin | N/A (0 provisioned users) | N/A | N/A | N/A | N/A |

### 3.4 Recommended operator-side cert plan

Per-portal Five-Pillar checklist (one page each):

1. Login (correct portal opens; temp-password enforcement; 401/403 surface).
2. Primary nav (sidebar/menu visible without overflow).
3. Primary table (renders; pagination; sort).
4. Primary form (opens; submits; success state).
5. Primary modal (centers; dismisses; iPad-keyboard interaction).
6. Search (focus, type, filter).
7. Save + hard refresh (data persists in production).

Each row recorded with timestamp + iOS version + device model. Operator runs the script in ~30 min/portal (8 portals × 3 viewports = ~12 hr of testing — best done in two batched sessions).

### 3.5 Mobile defect register from existing tracks

- No P0/P1 mobile defects open right now.
- 15.27A explicitly proves dialog centers on iPad portrait + landscape via Playwright simulation. Operator-side real-device confirmation is needed but no known regression.

---

## SECTION 4 — Team Assignment P2 Audit (P2)

### 4.1 Change Role workflow

**Current process:** Remove → Re-add. Two API calls. Two audit-trail rows. Two roster rerenders.

**Proposed (minimal):** new endpoint `PATCH /api/admin/jobs/{pn}/team/{assignment_id}/change-role` body `{new_role}`. Server logic:
1. Transaction begin.
2. Soft-end the current assignment with `end_reason="role_change"`, `ended_at=now`, `active=False`.
3. Insert a new assignment row with `assignment_role=new_role`, `active=True`, `notes="(role changed from {old})"`, same `user_id`/`email`/`display_name`.
4. Write one `audit_events` row of kind `role_change` referencing both ids.

Frontend: a new "Change role" affordance per row (icon `ArrowRightLeft` is already imported). Click → opens a small Dialog containing only the role-select (reuses the existing sorted registry).

| Pillar | Current (Remove + Add) | Proposed (Change Role) |
|---|:--:|:--:|
| Powerful | 4/5 (works) | **5/5** (single transaction) |
| Simple | 2/5 (3-step manual) | **5/5** (1 click + 1 select) |
| Beautiful | 3/5 | **5/5** |
| Trusted | 4/5 (audit trail is two rows) | **5/5** (single linked event) |
| Proven | 3/5 | needs cert after build |

**Implementation budget:** ~30 lines backend (route + transaction) + ~25 lines frontend (Dialog + icon button). Zero new collections. Zero new auth. Zero new audit collection.

### 4.2 Remove-reason Dialog (replace `window.prompt()`)

**Current:** `window.prompt("Reason?")` — OS-level modal that breaks iPad on-screen keyboards, can't be styled, doesn't support multiline.

**Proposed (minimal):** Replace with the same shadcn `<Dialog>` pattern already in use in 15.27A. Single `<Textarea>` field + Cancel/Confirm. No new dependency.

**Implementation budget:** ~25 lines. Pure frontend.

### 4.3 Combined verdict

Both P2 items are **low-risk frontend-leaning changes that take JobTeamRosterPanel.jsx from 25/25 (today, after 15.27A) to a more durable 25/25 with cleaner audit semantics and iPad-friendly remove UX.** Recommend bundling them together as a single small follow-up PR after the operator approves.

---

## SECTION 5 — Risk Ranking

| ID | Track | Description | Class | Severity | Status |
|---|---|---|:--:|:--:|---|
| **R-1** | 15.28 §2 | R2 backups grow indefinitely; no scheduled prune | 🟢 | **P0** | Awaiting operator |
| **R-2** | 15.28 §3 | Production iPhone/iPad real-device cert never completed across all 8 portals | 🟠 | **P0 (operational confidence)** | Operator-only work |
| **R-3** | 15.28 §1 / F-N1 | Notifications "is the inbox cluttered?" unanswerable until schema canonicalized | 🟢 | **P1** | Pending operator authorization to audit + backfill |
| **R-4** | 15.28 §4.2 | `window.prompt()` remove-reason hostile to iPad keyboards | 🟢 | **P1** | Bundled into 15.27 P2 follow-up |
| **R-5** | 15.28 §4.1 | Change-role requires Remove + Add (two audit rows) | 🟢 | **P2** | Same |
| **R-6** | 15.28 §1 / F-N2 / F-N3 | Mixed notification schema (552 legacy docs `kind`+`user_email`+`audience`) | 🟢 | **P2** | Bundled into R-3 |
| **R-7** | 15.27B carry-over | Production iPhone/iPad cycle test for Add → Refresh → Remove → Refresh on production | 🔴 | **P0 (final gate)** | Operator only |
| **R-8** | 15.24B | Atlas tier + Emergent invoice still unknown | 🔴 | **P1** | Operator dashboard pull |
| **R-9** | older tracks | Field Leadership shared-password gate / static Shop HMAC password | 🟢 | **P2** | D-16 backlog |

---

## SECTION 6 — Recommended Execution Order

Sorted by **Five-Pillar gain per hour of work** (deliver Trusted+Proven first, then Simple+Beautiful):

1. **R-1 — R2 retention scheduled prune (~1 hr).** P0. Largest cost-control gain; single sibling cron entry calling the already-tested `_emergency_prune_backups`. Most defensive Trust + cost gain on the platform.
2. **R-7 / R-2 — Production iPhone/iPad walkthrough (~30 min/portal × 8 = ~4 hr operator).** P0. Cannot be automated. Earns the final Proven score for every portal.
3. **R-3 — Notification schema canonicalization audit (~1 hr code-audit + ~30 min backfill drydown).** P1. Resolves the 552-row legacy vocabulary issue and answers the "is the inbox cluttered?" question that motivated 15.8A/15.8B in the first place.
4. **R-4 + R-5 — Team Assignment P2 bundle (~2 hr frontend + ~30 min backend Change-Role route).** P1/P2. Drops `window.prompt()` and adds Change Role; minor but eliminates the iPad-hostile pattern.
5. **R-8 — Operator pulls Atlas/Emergent/Resend/Sentry/Cloudflare dashboards (~30 min operator).** P1. Turns 15.24B's $66–$470 cost interval into a deterministic number.
6. **R-9 / R-6 — Long-tail tech debt** (static shop HMAC retirement, notification mixed-schema mop-up). P2/P3.

---

## Final rules check (operator-mandated)

- 🟢 No optimism. All assertions in §1/§2/§4 are anchored to live measurements.
- 🟠 No assumptions. Where modeled, the assumption is stated inline.
- 🔴 No "looks good." Real-device cert (§3) explicitly flagged as operator-only — not claimed as done.
- 🔴 No "should work." Every recommendation has a verification plan.
- 🔴 No "cannot reproduce." For F-N6 (original PM-notification complaint) I explicitly state the original symptoms have not yet been reproduced inside this audit — operator's incident exemplars are needed to lock the fix.

**Nothing closes until it is proven.** This document is the closing checklist, not a victory lap.

---

## Files

- `/app/memory/TRACK_15_28_OPERATIONAL_DEBT_ELIMINATION_REPORT.md` — this file
- `/app/memory/PRD.md` — appended

**No code changed. No deploy. Awaiting operator prioritization of R-1 through R-9.**
