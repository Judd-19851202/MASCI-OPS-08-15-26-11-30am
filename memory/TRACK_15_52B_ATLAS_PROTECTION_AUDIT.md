# TRACK 15.52B · Atlas Protection Audit

**Status:** Read-only · evidence captured 2026-06-19 21:05 UTC.

## What is verifiable from inside this container

| # | Item | Status | Evidence |
|---|---|:---:|---|
| 1 | Cluster reachable | ✅ VERIFIED | `mongodb+srv://masci-prod.1nduwmg.mongodb.net` resolves and accepts writes (live `db.tasks.find_one()` returns within 0.05 s; `mascidocs.com/api/health/full` reports `mongo: true`). |
| 2 | Cluster identity | ✅ VERIFIED | SRV cluster `masci-prod`, sub-domain `1nduwmg.mongodb.net` — confirms an Atlas-managed cluster (vs self-hosted). |
| 3 | DB name in use | ✅ VERIFIED | Production: `masci_safety` (inferred from prior tracks · cannot read from preview env). Preview: `masci_safety_preview`. |

## What is **UNVERIFIABLE** from inside this container

| # | Item | Status | Why |
|---|---|:---:|---|
| 1 | Atlas PITR (Continuous Backup) enabled? | **UNVERIFIED** | Requires Atlas dashboard access OR Atlas Admin API key. Neither is available in this container. Track 15.37/15.38 explicitly listed this as `❓ OPERATOR REQUIRED · dashboard click-path documented`. |
| 2 | PITR retention length | **UNVERIFIED** | Same — requires dashboard. Atlas default is 24 h for shared clusters, 72 h for M10+, configurable up to 7 d. Without dashboard access cannot confirm. |
| 3 | Scheduled-snapshot retention length | **UNVERIFIED** | Same — Atlas defaults: daily-7, weekly-4, monthly-12, but customer-configurable. |
| 4 | Cluster tier (M0/M2/M5/M10/M20/M30/...) | **UNVERIFIED** | Tier governs whether PITR is even AVAILABLE: it requires M10 or higher. Cannot determine cluster tier without dashboard. |
| 5 | Restore capabilities (PITR target window) | **UNVERIFIED** | Tier-dependent. |
| 6 | Restore limitations (cross-region, cross-cluster) | **UNVERIFIED** | Tier-dependent. |
| 7 | Encryption-at-rest with customer keys | **UNVERIFIED** | Tier-dependent (M10+). |

## "What data protection exists even if R2 disappears?"

**Cannot answer with certainty.** The honest evidence-based answer is:

- IF Atlas PITR is enabled on a paid tier (M10+): RPO ≤ 60 seconds and recovery is independent of R2.
- IF Atlas is on a shared free tier (M0/M2): NO PITR · NO scheduled snapshots · last-good-state recovery requires R2.
- IF Atlas snapshots are configured but PITR is off: RPO = snapshot interval (typically 24 h) · also independent of R2.

The cluster name `masci-prod.1nduwmg.mongodb.net` *implies* a paid tier (free-tier clusters typically carry `mongodb.net` paths without environment-specific naming), but this is **inference, not evidence.**

## Recommendation for this section

Before any cadence change is approved, the operator must perform a one-time verification (5 minutes in Atlas dashboard):
1. Log in to https://cloud.mongodb.com → MASCI org → `masci-prod` cluster.
2. Click **Backup**. Confirm:
   - "Continuous Backup (PITR)" toggle is **on**
   - PITR retention window is at least 24 hours (recommend 72 h)
   - Snapshot retention is at least daily-7
3. Click **Cluster Configuration**. Confirm:
   - Tier is M10 or higher
4. Screenshot all three confirmations and attach to this audit file.

Without this verification, **R2 is the only proven data-protection layer**, and removing R2 hourly cadence weakens the platform's only confirmed RPO guarantee.

## SECTION C summary

**Atlas protection status: UNVERIFIED.** Inferred (not proven) to be paid-tier M10+ with PITR likely enabled, but operator must confirm via dashboard before any backup-cadence change is approved. This is a **HARD GATE** carried forward from Track 15.37 + 15.38 (both explicitly flagged this as `❓ OPERATOR REQUIRED`).
