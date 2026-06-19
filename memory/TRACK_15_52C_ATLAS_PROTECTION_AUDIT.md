# TRACK 15.52C · Atlas Protection Audit

**Status:** Read-only · captured 2026-06-19 21:30 UTC. UNVERIFIED items remain UNVERIFIED — re-running the audit did not change the gates documented in Track 15.52A/B.

## What is verifiable

| # | Item | Status | Evidence |
|---|---|:---:|---|
| 1 | Cluster reachable | ✅ VERIFIED | `mongodb+srv://masci-prod.1nduwmg.mongodb.net` accepts auth and serves traffic; `mascidocs.com/api/health/full` reports `mongo: true` and `ok: true`. |
| 2 | Atlas-managed (vs self-hosted) | ✅ VERIFIED | SRV cluster naming under `.mongodb.net` is exclusive to Atlas. |
| 3 | DB names in use | ✅ VERIFIED | Production = `masci_safety` (referenced throughout); preview = `masci_safety_preview` (in `/app/backend/.env`). |

## What is **UNVERIFIED** (and remains so)

| # | Item | Status | Reason |
|---|---|:---:|---|
| 1 | PITR (Continuous Backup) enabled? | **UNVERIFIED** | Requires Atlas dashboard or Atlas Admin API key. Neither is available in this container. The Atlas Admin API key (`ATLAS_API_KEY`) is **not** in `/app/backend/.env`. |
| 2 | PITR retention window | **UNVERIFIED** | Same. Defaults: M10/M20 = 24-72h, M30+ = up to 7 days. |
| 3 | Snapshot schedule | **UNVERIFIED** | Same. Defaults depend on tier (typically hourly+daily+weekly+monthly). |
| 4 | Snapshot retention | **UNVERIFIED** | Same. |
| 5 | Cluster tier (M0/M2/M5/M10/M20/M30/M40+) | **UNVERIFIED** | The cluster name `masci-prod` alone does not encode tier. Could be inferred from query latency profile, but that is circumstantial. |
| 6 | Restore capabilities | **UNVERIFIED** | Tier-gated. |
| 7 | Restore limitations | **UNVERIFIED** | Tier-gated. |
| 8 | Encryption at rest with customer keys | **UNVERIFIED** | Tier-gated (M10+). |

## What can be inferred (but should not be trusted as evidence)

- The cluster path `masci-prod.1nduwmg.mongodb.net` follows the M10+ shared-tenant naming convention; free-tier (M0) clusters typically use names like `Cluster0` and inherit a generic mongodb.net subdomain.
- Aggregate query performance against the cluster (Track 15.51 Phase 7 measurements: median 0.22s, max 0.86s) is consistent with M10+ dedicated-CPU, but is not exclusionary.
- Pre-launch CHANGELOG references (Tracks 15.10 – 15.30) talk about Atlas as a managed service without ever mentioning Atlas's free-tier limitations, **implying** (not proving) that MASCI is on a paid tier.

These are inferences. None of them is evidence.

## What the operator must verify (5-minute dashboard task)

1. Log into `https://cloud.mongodb.com`.
2. Navigate to the `masci-prod` cluster.
3. Open **Backup** → confirm:
   - "Continuous Backup (PITR)" toggle status.
   - PITR retention window (hours).
   - Scheduled snapshot policy (daily/weekly/monthly retention).
4. Open **Cluster Configuration** → confirm tier (M10 / M20 / M30 / etc.).
5. Screenshot all four confirmations and attach to `/app/memory/TRACK_15_52C_ATLAS_PROTECTION_AUDIT.md` as evidence.

Until this is done, the platform's long-term recovery posture beyond the 90-day R2 ceiling is **NOT ESTABLISHED**.

## Implication

Without Atlas PITR verified ON and with sufficient retention:
- R2 alone cannot satisfy any restore older than 90 days (forecast from `TRACK_15_52C_R2_LIFECYCLE_FORENSICS.md`).
- The platform has no proven means of answering questions like "what did the incidents collection look like 4 months ago when this WV claim was filed?".
- The 6-hour cadence change still remains UNSAFE without this verification (Track 15.52B Section I).

## Question 6 — direct answer

| Sub-question | Answer |
|---|---|
| PITR enabled? | **UNVERIFIED** |
| PITR retention window? | **UNVERIFIED** |
| Snapshot schedule? | **UNVERIFIED** |
| Snapshot retention? | **UNVERIFIED** |
| Backup tier? | **UNVERIFIED** |

This is the **same status as Tracks 15.37, 15.38, 15.52, 15.52A, 15.52B**. The Atlas-side operator gate has not been closed since it was first opened in Track 15.37.
