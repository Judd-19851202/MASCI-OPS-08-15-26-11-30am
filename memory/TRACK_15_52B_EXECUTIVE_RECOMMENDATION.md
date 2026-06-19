# TRACK 15.52B · Executive Recommendation

**One recommendation only. No hedging.**

## Decision

**A · REMAIN ON HOURLY CADENCE.**

## Why (evidence summary)

### 1. The cost saving is real but small.

- Current annual R2 cost: **$34.90.**
- 6-hourly annual R2 cost: **$17.83.**
- Annual saving: **$17/year** (Track 15.37's "−66%" projection was understated; actual −49%).

This is well below the threshold at which an operational risk would be worth taking — it's less than the cost of a single billable hour reviewing the change.

### 2. The recovery posture argument depends on a gate that is still open.

- **Atlas PITR status is UNVERIFIED** (`TRACK_15_52B_ATLAS_PROTECTION_AUDIT.md`).
- IF Atlas PITR is ON: switching to 6-hour cadence is safe (RPO stays at sub-minute).
- IF Atlas PITR is OFF: switching to 6-hour cadence degrades worst-case RPO from 60 min to 360 min (a 6× regression for a safety-critical platform that supports OSHA-recordable training, workplace-violence incident defensibility, and chain-of-custody requirements).

Until the gate is closed, **the conservative move is to keep the layer of protection that is actively working today.**

### 3. The platform's infrastructure posture has a separate, latent problem that should be addressed first.

The audit discovered (`TRACK_15_52B_CONTRADICTION_ANALYSIS.md` §New-contradictions-1):
- Cloudflare's bucket lifecycle rule `masci-backups-auto-90d` silently deletes the entire `backups/auto-90d/` prefix at 90 days.
- The app's `lib/r2_retention.py` says it preserves monthly survivors for 365 days.
- Reality: live cohort histogram shows **zero objects past 90 days**.

The operator should resolve this conflict FIRST (either remove the R2-side lifecycle rule and let the app handle 365-d monthlies, OR accept the 90-day effective retention and delete the misleading Tier 3 code path). Making any cadence decision while the two engines disagree silently is a poor sequence.

### 4. R2 is currently the platform's *only proven* sub-hour recovery mechanism.

- R2 versioning: NOT ENABLED.
- R2 Object Lock: NOT ENABLED.
- R2 Replication: NOT ENABLED.
- Atlas PITR: UNVERIFIED.

In this posture, **the most valuable property R2 provides is the rate at which it captures the latest state of the platform.** Reducing that rate by 6× without first proving Atlas PITR is operational removes a working safety net to save $17/year.

### 5. The platform has a single critical confidence interval window upon production deployment.

Per Track 15.51's certification, MASCI is preparing for first-time production operation tomorrow morning (2026-06-20). The first 30 days of production are the worst window in which to change foundational data-protection cadence. **Changing cadence during a fragile period is exactly the move a careful operator should not make.**

## What to do instead

In strict priority order:

1. **Operator: verify Atlas PITR status.** 5-minute Atlas-dashboard task. Result: ON or OFF. Capture screenshot.
2. **Operator: decide whether to enable R2 versioning** (3-click change, ~$0.50/month). Recommended for any platform with WV / police / OSHA chain-of-custody requirements.
3. **Operator: decide whether to keep the R2 lifecycle rule `masci-backups-auto-90d`** or rely on the app-side Tier 3. **Either choice is valid**; the current state where both exist and disagree is not.
4. **Operator: sweep the legacy `backups/*.zip` prefix** — 22.5 GB / 500 frozen objects / 30 of them corrupted stubs. Saves $4/year and reduces noise in restore drills.
5. **Defer the cadence change** until items 1-3 are complete. Once Atlas PITR is verified ON, R2 versioning is on, and the lifecycle conflict is resolved, the 6-hour cadence becomes a routine optimization with no downside.

## What the recommendation is NOT

- It is not "the proposal was wrong." Tracks 15.37 and 15.38 were *directionally correct*. The code is *production-ready*. The operator gate is the only thing standing between the proposal and execution.
- It is not "hourly is the right cadence forever." It is the right cadence **today, in the current verified posture**.
- It is not "don't trust the R2 backups." R2 backups are demonstrably healthy and arrive on cadence.

## Final answer to the FINAL QUESTION

> **"If Jaymn had to make the backup cadence decision today using evidence only, what should he do and why?"**

**Keep hourly. Do not flip to 6-hour cadence yet.**

Because:

1. The $17/year saving is too small to justify any risk.
2. Atlas PITR — the only thing that would make 6-hour cadence safe at a safety-critical platform — is **UNVERIFIED** and the verification was already listed as `❓ OPERATOR REQUIRED` two tracks ago (15.37, 15.38).
3. The platform launches production tomorrow morning; the first 30 days are the worst time to change foundational data-protection cadence.
4. A separate, higher-priority infrastructure conflict (R2 lifecycle silently overriding app-side Tier 3) should be resolved first.
5. R2 hourly is the platform's only *currently verified* sub-hour recovery layer. Until Atlas PITR is confirmed, removing that layer is a regression.

Once the operator verifies Atlas PITR is ON, enables R2 versioning, and resolves the lifecycle conflict, the 6-hour switch becomes a routine optimization. Until then: **keep hourly.**
