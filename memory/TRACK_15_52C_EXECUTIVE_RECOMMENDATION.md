# TRACK 15.52C · Executive Recommendation

**Question:** Which of options A-F should MASCI choose?

```
A. Leave everything exactly as-is.
B. Fix retention conflict only.
C. Enable Versioning only.
D. Enable Versioning + fix retention conflict.
E. Safe to move to 6-hour cadence.
F. Unsafe to move to 6-hour cadence.
```

## Decision

**🟢 D · Enable R2 versioning AND fix the retention conflict.**

**🟢 F · Moving to 6-hour cadence is UNSAFE today.**

(Both apply. They are independent questions in the same audit cycle.)

## Why D (versioning + retention fix)

### What's broken today

| Defect | Severity | Window |
|---|:---:|---|
| R2 lifecycle (90 d) silently overrides app Tier 3 (365 d) | CRITICAL | Will first cause data loss on ~2026-08-29 (52 days from now) |
| R2 versioning disabled (any delete is permanent) | HIGH | Live posture; impacts every accidental-delete scenario |
| R2 object-lock disabled (no compliance-grade immutability) | MEDIUM | Live posture; matters for OSHA chain-of-custody disputes |
| R2 replication disabled (single-account, single-bucket) | LOW (Cloudflare's 11-nines durability covers most failure modes) | Live posture |

### Why option A (do nothing) is the wrong call

- It accepts a known, dated, forecasted data-loss event in 52 days.
- It leaves the platform's long-term recovery story dependent on an UNVERIFIED Atlas PITR configuration.
- It misaligns the docs and the live behavior — any reader of `lib/r2_retention.py` would believe retention extends to 365 days; the live state will prove that wrong on 2026-08-29.

### Why option B (retention only) is half a fix

- Resolves the lifecycle conflict.
- Does NOT protect against accidental delete.
- For a safety-critical platform with WV / OSHA / police-involvement records, accidental-delete protection is high-value at near-zero cost.

### Why option C (versioning only) is the other half-fix

- Protects against accidental delete.
- Does NOT resolve the 90-day retention ceiling for long-term recovery.
- Audit and OSHA reviewers asking for 6-month-old records would still be told "we don't have that."

### Why option D is the right combination

- Removing (or shortening to 365 d) the `masci-backups-auto-90d` lifecycle rule **OR** routing monthly survivors to a non-lifecycle-managed prefix, lets the app's `r2_retention.py` Tier 3 logic actually do what it was designed to do.
- Enabling versioning costs ~$0.50/month and gives MASCI a real undo button for accidental deletes.
- Together these two cheap, low-risk changes give MASCI the long-term recovery story its documentation already advertises.
- Both are reversible.

### What option D does NOT do

- It does not enable Atlas PITR (still UNVERIFIED — operator dashboard task).
- It does not change the backup cadence (which should stay hourly — see option F).
- It does not modify any code (env / dashboard changes only, applied by operator at their pace).

## Why F (6-hour cadence UNSAFE)

### The unchanged truths from Track 15.52B

1. The cost saving is only $17/year.
2. Atlas PITR — the safety net that would make 6-hour cadence sane — is **UNVERIFIED**.
3. Worst-case RPO would degrade from 60 min to 360 min without Atlas PITR.
4. The retention conflict (option D) is a higher-priority operational issue than cadence.

### What's new from Track 15.52C

5. The bucket is 39 days old. The platform has not yet experienced its first complete retention cycle. Changing cadence during this window introduces additional uncertainty.

### Conclusion

Moving to 6-hour cadence today is **unsafe** for the same reason it was unsafe in Track 15.52B: Atlas PITR is unverified, and R2 hourly is currently the platform's only confirmed sub-hour recovery layer. Adding 15.52C's new finding — that the *long-term* recovery layer (Tier 3 monthly) is structurally broken — strengthens the case to leave the hourly cadence alone until the platform's protection model is hardened end-to-end.

## Sequence the operator should follow

Strict priority order:

1. **D-1:** Resolve the R2 lifecycle vs. app Tier 3 conflict. Two acceptable resolutions:
   - **D-1a:** Edit the `masci-backups-auto-90d` lifecycle rule from `Expiration: 90 days` to `Expiration: 365 days` (or delete it entirely and let the app-side `r2_retention.py` Tier 4 handle deletion at Day 365).
   - **D-1b:** Modify the upload code path so monthly-survivor candidates are copied to a separate prefix `backups/monthly-365d/` that is NOT covered by the 90-day lifecycle rule. (This is a code change, deferred to a future track per current hard rules.)
   
   Recommended: **D-1a** — operator-side, 3-click dashboard change, no code deploy.

2. **D-2:** Enable R2 bucket versioning (3-click dashboard change, +$0.50/month, gives accidental-delete protection).

3. **Atlas gate:** Verify Atlas PITR status, PITR retention, snapshot retention, cluster tier. Document with screenshots.

4. **Legacy sweep:** Delete the 500-object / 22.5 GB legacy `backups/*.zip` prefix (or move it into `auto-90d/` for lifecycle management). Saves $4/year and removes audit ambiguity.

5. **Then and only then:** Re-evaluate the 6-hour cadence decision in a future track.

## Sign-off

**Recommendation: D + F.**

- D: Enable R2 versioning AND fix the R2 lifecycle / app Tier 3 conflict.
- F: Moving to 6-hour cadence is UNSAFE today.

Both are evidence-anchored. Both are independent of each other. Neither requires any code change. The D actions are operator-dashboard work taking < 15 minutes total. The F decision is a "do nothing on cadence" — preserves the status quo until Atlas PITR is verified.
