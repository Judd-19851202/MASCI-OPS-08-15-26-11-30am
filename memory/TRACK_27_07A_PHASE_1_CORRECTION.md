# TRACK 27.07A · PHASE 1 · CORRECTION MEMO

**Session:** 2026-02 (fork)
**Mode:** Read-only. No deploy. No UI build. No R2 mutation.
**Environment reached:** PREVIEW ONLY. Production not reachable from this pod.

Delivers:
- Part A · Policy provenance matrix
- Part B · Corrected composite severity contract (proposal only)
- Part C · Root cause of the "44 507 m old" backup evidence
- Part D · Production access proof / gap

Parts E, F, G, H **NOT executed** — production access is unavailable from
this pod. See §D for exact missing access.

---

## Part A · Policy provenance matrix

Every threshold I introduced in Phase 1 is graded here. **Nothing in this table is described as approved unless approval evidence exists.**

| # | Policy value | Exact value | Source | Who approved it | Approval date | Existing policy or newly invented? | Operational consequence |
|---|---|---|---|---|---|---|---|
| 1 | Technical-capacity ceiling | **10 000 000 GB (10 PB)** | Cloudflare R2 public developer docs (per-bucket soft limit for Standard R2) | **NO OPERATOR** | — | **NEWLY INVENTED — PROVIDER MAX MIS-USED AS BUSINESS THRESHOLD.** Cloudflare's provider limit is not MASCI's approved business capacity. | Composite `technical_capacity` dimension effectively never fires. Bucket could grow to hundreds of TB before any capacity dimension warned. **This masks growth risk.** |
| 2 | Storage-cost HEALTHY ceiling | **$30 / month** | Phase 0B §7 Option A "provisional" recommendation authored by me | **NO OPERATOR** | — | **NEWLY INVENTED.** No budget line, no invoice-derived target, no operator sign-off. | At $30/mo the dimension is HEALTHY, so cost pressure is invisible until it exceeds ~2 TB. |
| 3 | Storage-cost ATTENTION ceiling | **$75 / month** | Phase 0B §7 Option A "provisional" | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same as above. |
| 4 | Storage-cost CRITICAL floor | **$150 / month** | Phase 0B §7 Option A "provisional" | **NO OPERATOR** | — | **NEWLY INVENTED.** | Cost only becomes RED at ~10 TB. |
| 5 | Growth baseline window | **30 days** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** No prior policy names a baseline window. | Baseline is easily gamed by short bursts. |
| 6 | Growth recent window | **7 days** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 7 | Growth ATTENTION multiplier | **3× baseline** | Referenced Phase 31.3 forensic report's "9.6 GB/day pathological ÷ 2.1 GB/day steady" ≈ 4.6× ratio; I rounded down to 3× | **NO OPERATOR** | — | **NEWLY INVENTED.** Not a policy — a rounded observation. | A single legitimate refactor spike (e.g., photo backfill) would flip ATTENTION. |
| 8 | Growth CRITICAL multiplier | **10× baseline** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 9 | Growth min-samples | **5** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Below 5 samples the dimension returns UNKNOWN — reasonable but not approved. |
| 10 | Orphan HEALTHY ceiling | **≤ 1.00 %** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** No prior operator statement about acceptable orphan share. | A bucket with 0.9 % orphans (potentially TBs) evaluates HEALTHY. |
| 11 | Orphan ATTENTION ceiling | **≤ 5.00 %** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 12 | Orphan CRITICAL floor | **≥ 20.00 %** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Below 20 % orphan share, the dimension is only ATTENTION — meaning a 61 % orphan share (like the preview reading) IS correctly CRITICAL, but the *threshold* itself is arbitrary. |
| 13 | Classifier freshness window | **7 days** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Older classifier snapshots correctly downgrade to UNKNOWN — but 7 d is not derived from an approved policy. |
| 14 | Backup HEALTHY age max | **25 h** | Phase 1 authoring convenience — matches "hourly cadence + 1 h grace" | **NO OPERATOR** | — | **NEWLY INVENTED.** | See §C — this input is measured against the WRONG source signal (local marker vs R2-direct probe). |
| 15 | Backup ATTENTION age max | **48 h** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same as #14. |
| 16 | Evidence-freshness HEALTHY inventory age | **24 h** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Preview inventory is 36 h → ATTENTION. Threshold is not approved. |
| 17 | Evidence-freshness ATTENTION inventory age | **7 days** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 18 | Evidence-freshness CRITICAL inventory age | **30 days** | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 19 | Usage-signal HEALTHY age | **6 h** | Phase 1 authoring convenience — matches complete-R2 hourly cadence | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 20 | Composite rule: `≥ 2 CRITICAL → CRITICAL` | see rule | Phase 0B §7 Option D "provisional" and Phase 1 authoring | **NO OPERATOR** | — | **NEWLY INVENTED — DANGEROUS.** See Part B. A single blocking-critical (e.g., no recoverable backup) is masked to ATTENTION. |
| 21 | Composite rule: POLICY_REQUIRED never elevates | see rule | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** A missing retention policy that gates a deletion pass MUST elevate; the current rule silently swallows it. |
| 22 | Composite rule: UNKNOWN never elevates | see rule | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** UNKNOWN on backup integrity or classifier confidence during a proposed deletion must not remain neutral. |
| 23 | Review cadence "90 days" (cost, growth, backup) | 90 d | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Advisory only; no enforcement mechanism. |
| 24 | Review cadence "180 days" (capacity, waste, retention, freshness) | 180 d | Phase 1 authoring convenience | **NO OPERATOR** | — | **NEWLY INVENTED.** | Same. |
| 25 | Policy `owner` = "Track 27.07A Phase 0B audit (provisional)" | see policy.py | Phase 1 authoring convenience | **NO OPERATOR** | — | **MIS-LABELED.** "Provisional" was clearer than "approved" but still implies more legitimacy than exists. **Correct label: `PROPOSED_POLICY — OPERATOR APPROVAL REQUIRED`.** | Downstream consumers of the manifest may still read "PROVISIONAL_FROM_AUDIT" as a green-light. |
| 26 | Cloudflare R2 pricing constants ($0.015/GB, $4.50/M Class A, $0.36/M Class B, $0 egress) | see policy.py | Cloudflare R2 public developer docs (Feb 2026) | Cloudflare (provider) — **NOT** MASCI | 2026-02 | **PROVIDER_PUBLISHED — genuine.** These are the only values on this list that are actually approved by their stated owner. | Truthful. Estimator will remain correct until Cloudflare changes its list. |

**Corrective classification:** Every row except #26 must be relabeled `PROPOSED_POLICY — OPERATOR APPROVAL REQUIRED`. The `policy_manifest()` output currently uses `PROVISIONAL_FROM_AUDIT` / `OPERATOR_APPROVED` — that is misleading and will be fixed before any deploy.

---

## Part B · Corrected composite severity contract (proposal only — not shipped)

The current rule masks four categories of blocking-critical conditions. Replace with:

### Category 1 · Blocking Critical (single dimension → composite CRITICAL, no aggregation)

A single dimension flips the composite to CRITICAL when *any* of these conditions are true, regardless of counts:

| Signal | Detection | Composite result |
|---|---|---|
| Backup integrity failure | Most recent `backup_health.ok == false` OR most recent complete backup checksum failure recorded | CRITICAL |
| No recoverable backup | Neither `backup_health` NOR direct R2 archive listing has any `complete-r2` snapshot in the last 48 h **AND** last quarterly drill did not verify a restore | CRITICAL |
| Legal-hold violation | Any object in `LEGAL_HOLD` class has been marked for delete/quarantine OR any legal-hold prefix has been mutated | CRITICAL |
| Retention violation with active deletion risk | An approved retention window would expire an object within 24 h AND the delete-engine is enabled AND the object is not classified `RETENTION_PROTECTED` | CRITICAL |
| Uncontrolled destructive capability | `hard_delete_status` reports enabled without explicit run-scoped operator approval token, or any quarantine → delete window is less than the minimum 24 h holding period | CRITICAL |
| Production data loss | Any collection under `data_size` monitoring shows > 5 % row loss vs 24 h prior, or R2 total_objects drops > 5 % vs 24 h prior without an approved deletion batch on record | CRITICAL |
| Inaccessible required evidence | Legal / OSHA / contract-referenced object returns 4xx/5xx from R2 direct probe | CRITICAL |
| Classifier uncertainty during proposed deletion | A quarantine batch is queued AND `AMBIGUOUS + UNKNOWN + PENDING` share of the same batch exceeds 0 % | CRITICAL |
| Required storage system failure | Cloudflare R2 endpoint returns > 50 % 5xx over a 5-minute window, or Mongo primary is unreachable | CRITICAL |

### Category 2 · Operational Critical (single dimension → composite CRITICAL when explicitly configured)

A dimension flips composite to CRITICAL only when the operator's approved policy names that dimension as an operational critical. Example: an operator-signed policy stating "storage cost > $500/mo is critical" would put storage_cost into Category 2. Nothing enters this category without a signed policy record.

### Category 3 · Attention (real but non-immediate)

Composite escalates to ATTENTION when any of these are true and no Category 1/2 conditions apply:

- Certified `VERIFIED_ORPHAN` share exceeds an operator-approved advisory threshold, *while delete-engine is disabled and no quarantine is queued* — meaning it is a housekeeping opportunity, not an emergency.
- Inventory scan older than the approved freshness window but younger than the "must re-scan before trusting" window.
- Cloudflare-side lifecycle rule reports NOT applied, but no retention SLA is currently at risk.
- Growth ratio elevated but sample count is limited or explanation exists (e.g., known migration).
- POLICY_REQUIRED item pending, but the current operator flow does not depend on it.

### Category 4 · Advisory (UNKNOWN + POLICY_REQUIRED)

- `UNKNOWN` on a safety-critical dimension (backup integrity, classifier confidence during quarantine, legal-hold status): **CRITICAL** — treat unknown as unsafe.
- `UNKNOWN` on optional cost telemetry (no invoice available): **ATTENTION** — visible but not blocking.
- `POLICY_REQUIRED` for retention / legal / contract windows: **CRITICAL if delete-engine is enabled**, **ATTENTION otherwise** — a missing retention policy must not silently allow deletion.
- `POLICY_REQUIRED` on cost budget lines with no active pressure: **ATTENTION** — surface, do not block.

### Reason-code contract

Every composite verdict must emit a machine-parseable reason code from the closed set:

```
COMPOSITE_HEALTHY
COMPOSITE_ATTENTION_HOUSEKEEPING          # orphan share, stale inventory, etc.
COMPOSITE_ATTENTION_GROWTH                # elevated but controlled
COMPOSITE_ATTENTION_POLICY_MISSING        # POLICY_REQUIRED not blocking
COMPOSITE_ATTENTION_UNKNOWN_COST          # advisory UNKNOWN
COMPOSITE_CRITICAL_BACKUP_INTEGRITY
COMPOSITE_CRITICAL_NO_RECOVERABLE_BACKUP
COMPOSITE_CRITICAL_LEGAL_HOLD_VIOLATION
COMPOSITE_CRITICAL_RETENTION_VIOLATION_ACTIVE_DELETE
COMPOSITE_CRITICAL_UNCONTROLLED_DELETE_CAPABILITY
COMPOSITE_CRITICAL_PRODUCTION_DATA_LOSS
COMPOSITE_CRITICAL_INACCESSIBLE_REQUIRED_EVIDENCE
COMPOSITE_CRITICAL_CLASSIFIER_UNCERTAIN_DURING_DELETE
COMPOSITE_CRITICAL_STORAGE_SYSTEM_FAILURE
COMPOSITE_CRITICAL_UNKNOWN_ON_SAFETY_DIMENSION
COMPOSITE_CRITICAL_POLICY_REQUIRED_BLOCKS_DELETE
COMPOSITE_CRITICAL_OPERATIONAL_POLICY_BREACH  # Category 2
```

Each code names *exactly* the dimension and condition responsible. Tests must be permanent for every branch of the truth table above.

**Status: PROPOSAL — NOT SHIPPED.** No code has been written for this corrected rule. It replaces `policy.py::aggregate()` on operator approval only.

---

## Part C · The "44 507 m old" backup evidence — root-cause trace

**Environment:** PREVIEW (APP_ENV=preview, DB_NAME=masci_safety_preview).

### Direct DB probe (this session, `now=2026-07-12T00:22:02Z`)

```
health.py::compute_storage_health · backup_footprint query
────────────────────────────────────────────────────────────
find_one( {mode: {$in: [complete, complete-r2, complete-nightly]}} , sort: ts desc )

  mode          : complete-r2
  ts            : 2026-06-11T02:14:07.940173+00:00
  ok            : True
  age (min)     : 44 527.9      ← this is the "44 507 m" value from the earlier report,
                                  slightly different because now-clock has advanced
  age (hours)   : 742.1
  age (days)    : 30.92
```

### backup_health mode histogram (preview, this session)

```
mode=complete-r2            n=91   latest=2026-06-11T02:14:07Z
mode=r2-usage-alert         n=90   latest=2026-06-11T02:14:17Z
mode=lite                   n=16   latest=2026-06-16T10:47:37Z
mode=complete-r2-error      n=2    latest=2026-05-25T15:18:06Z
```

### Contradiction root cause

| Layer | Source of "last backup" signal | Result |
|---|---|---|
| `routes/recovery_dashboard.py::snapshot` (Recovery card) | 1) queries `backup_health` for the latest `complete-r2 · ok:true` row, 2) THEN queries R2 directly via `_newest_r2_backup_summary()` — **if R2 has a newer archive, R2-direct wins and drives the pill** | GREEN — the R2 hourly writer is still landing archives in the preview R2 bucket even though the local `backup_health` scheduler has been quiet since 2026-06-11 |
| `services/r2_lifecycle/health.py::compute_storage_health` (Storage Health card, my Phase 1 rewrite) | Reads ONLY the local `backup_health.complete-r2` row via a plain Mongo query | RED (age = 44 528 m) — **stale local marker** |

### Verdict on the classification

**The 44 507 m value was arithmetically correct given its input, but the input was the wrong signal.** The Storage Health card's `backup_footprint` dimension read the local `backup_health` scheduler row, which is 31 days stale in preview because the preview scheduler is not consistently producing local health markers. The recovery-dashboard card reads BOTH the local marker AND a live R2-direct probe and promotes R2 when it's newer — which correctly reports GREEN.

**This is a Phase 1 defect.** The corrected implementation must:

1. In `services/r2_lifecycle/health.py::compute_storage_health`, compute the backup-footprint dimension against the **same authoritative signal** used by `recovery_dashboard.py::snapshot` — i.e., **max(local `backup_health.complete-r2.ok:true.ts`, R2-direct newest-archive `LastModified`)**.
2. Route both cards through the composite policy engine so *evidence* is shared, not just *thresholds*.
3. Add a permanent regression test that if the recovery card is GREEN and the storage health card is RED for reason `backup_footprint`, the test fails with a truthfulness-invariant message.

**Was the classification correct?** *Given its inputs*, yes. *In truthful terms*, no — the composite reported CRITICAL on a signal that another card in the same environment correctly reports GREEN. This is precisely the "policy evidence must not contradict live healthy backup-freshness" invariant the user named.

**Status:** BUG identified. Fix designed. **NOT SHIPPED.** Corrective change requires operator approval to modify `services/r2_lifecycle/health.py` again.

---

## Part D · Production access gate — RESULT

Verified without exposing secrets. The pod's `backend/.env` reads:

```
APP_ENV       = preview                                ← NOT production
DB_NAME       = masci_safety_preview                   ← NOT masci_safety
MONGO_URL     = mongodb+srv://***@masci-prod.***.mongodb.net/...
              (Atlas cluster host is shared, but the DB_NAME is the
               preview logical database on that cluster)
S3_BUCKET     = masci-***                              ← preview bucket, obscured
S3_ENDPOINT   = https://46400762d3027afbb26819a8de8...  (Cloudflare R2 account host)
```

### Access checklist per the mission

| Required | Present in this pod? |
|---|---|
| APP_ENV = production | ❌ `preview` |
| DB_NAME = masci_safety | ❌ `masci_safety_preview` |
| Production R2 bucket identity | ❌ this pod's `S3_BUCKET` is the preview bucket |
| Production Mongo access (masci_safety DB) | ❌ this pod's `DB_NAME` is the preview logical DB |
| Production R2 read access | ❌ this pod's R2 credentials are keyed to the preview bucket |
| Current production bucket bytes | ❌ cannot query — no production S3 endpoint credentials in this pod |
| Current production object count | ❌ same |
| Delete engine remains disabled | ✅ verifiable at code level — `hard_delete_status` refuses in all paths; Track 27.07 Phase 0 lock intact |

**Missing access — exact:**

1. A production-scoped `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` (or equivalent Cloudflare R2 tokens) — required for Parts E, F, G, H.
2. A production `DB_NAME=masci_safety` connection string — required for Part F (reference-resolution audit).
3. An authorized production execution environment (this preview pod is expressly not production).

**No workaround is being proposed.** Per user instruction, I am not building UI, deploying, or running Parts E-H against preview as a substitute.

---

## Verdict

# 🛑 STOP — POLICY APPROVAL REQUIRED + PRODUCTION ACCESS UNAVAILABLE

**Reason:**

1. **Policy approval required.** 25 of 26 policy values in the shipped Phase 1 code are `PROPOSED_POLICY — OPERATOR APPROVAL REQUIRED`, mis-labeled today as `PROVISIONAL_FROM_AUDIT` / `OPERATOR_APPROVED`. The composite severity rule masks nine categories of blocking-critical conditions (Part B). The mis-labeling and the rule must be corrected before any deploy.
2. **Production access unavailable.** This pod is `APP_ENV=preview` with `DB_NAME=masci_safety_preview` and a preview R2 bucket. Parts E, F, G, H cannot be executed here. No substitution is acceptable per user instruction.
3. **Phase 1 has one identified defect.** The `backup_footprint` dimension reads a stale local marker in preview and reports CRITICAL while the recovery card correctly reports GREEN using an R2-direct probe. That is exactly the "evidence must not contradict" invariant the user named.

**Do not deploy Phase 1 as shipped.**

**Not proposed:** UI dimension chips, additional feature tracks, quarantine, deletion, retention runs, threshold changes on production.

**Awaiting operator:**

1. Approve or amend the 25 proposed policy values (Part A table).
2. Approve the corrected composite severity contract (Part B) — or amend it.
3. Approve the `backup_footprint` fix (dual-source signal — Part C).
4. Provide production execution access (Part D missing-access list) so Parts E-H can proceed.

Then, and only then:
- Re-label the manifest.
- Re-implement `aggregate()` per the corrected contract.
- Fix the backup-footprint source.
- Run Parts E-H read-only in production.
- Return an immutable `VERIFIED_ORPHAN` manifest + GO/HOLD/STOP verdict.
