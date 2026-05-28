# Append-Only Memory — Certification

**Phase V-Prelude · Wave 1.1B**
**Status:** 🟢 **DOCTRINE ENFORCED · preview env**
**Date:** 2026-05-28

---

## Doctrine statement

> Governance memory in this platform is append-only. Entries are NEVER
> overwritten. Corrections take the form of NEW entries that supersede
> earlier ones — never of in-place mutation. The probe enforces this
> contract.

## Why append-only

1. **Truth preservation.** A calmness score from Q1 2026 stays a
   Q1 2026 score even when better instruments arrive later. The
   trendline becomes the platform's honest history.
2. **Triage clarity.** When a regression is reported, the entire
   chronological context is intact — no entries silently vanished.
3. **Anti-revisionism.** No agent can "make the trendline look
   better" by editing past entries. The cost of bad scores is
   institutional accountability.
4. **Future doctrine evolution.** When the heuristics tune (the
   targets in `timeline_calmness_probe.py`), the OLD entries remain
   comparable — that's the only way longitudinal calmness analysis
   is meaningful.

## Enforcement mechanism

The `trendline_integrity_probe.py` enforces append-only through two
mechanisms:

### Mechanism 1 — Snapshot entry-count floor
A `<trendline>.snapshot.json` file stores the last known-good
`entry_count`. The probe REFUSES any run where the live trendline has
FEWER entries than the snapshot says it had.

### Mechanism 2 — Prefix checksum
The snapshot stores a SHA-256 checksum of the first `entry_count`
entries. On every probe run, the live trendline's prefix is
re-checksummed; divergence indicates an entry was MUTATED IN PLACE.

Together these mechanisms detect every form of historical revision
short of someone deleting BOTH the trendline AND its snapshot
simultaneously — at which point the absence of the snapshot is itself
suspicious (caught by the probe's "snapshot missing" warning).

## Permitted operations

| Operation | Permitted? | How |
|---|---|---|
| Append a new entry | ✓ | normal `timeline_calmness_probe.py` run |
| Read entries | ✓ | any tool, anywhere — files are world-readable |
| Add NEW columns to entries | ✓ | adds keys; checksum sees same prefix entries |
| Correct a stale entry | ✗ | append a NEW entry with the corrected value |
| Delete entries (no replay) | ✗ | snapshot count check rejects |
| Re-baseline after intentional prune | ✓ | `--refresh-snapshot` operator-explicit override |
| Replay an old run | ✗ | duplicate (iter, ts) check rejects |
| Edit a historical timestamp | ✗ | prefix-checksum check rejects |

## When can the snapshot be refreshed?

Three scenarios:
1. **Clean probe run** — snapshot is refreshed automatically (the
   anchor moves forward to capture the new known-good state).
2. **Operator-explicit `--refresh-snapshot`** — used after an
   intentional prune (e.g., the trendline grew to 10,000 entries and
   the oldest are no longer interesting). Operator takes
   responsibility; the snapshot's `refreshed_at` records when.
3. **NEVER on a violating run** — corruption preserves the anchor so
   triage can reconstruct what changed.

## Operator playbook

### "I want to drop the trendline back to last week"
```bash
# 1. Back up the current file.
cp /app/memory/TIMELINE_LOUDNESS_TRENDLINE.json /tmp/backup-$(date +%s).json

# 2. Edit the trendline (manual prune).
# (use a text editor)

# 3. Re-baseline the snapshot.
python3 /app/scripts/trendline_integrity_probe.py --refresh-snapshot

# 4. Verify clean.
python3 /app/scripts/trendline_integrity_probe.py --gate
```

### "The probe is failing on a deploy"
```bash
# 1. Read the violations.
python3 /app/scripts/trendline_integrity_probe.py

# 2. Diff the live file against last commit.
git diff HEAD -- /app/memory/TIMELINE_LOUDNESS_TRENDLINE.json

# 3. Revert or repair as appropriate.
# 4. Do NOT refresh the snapshot until the violation is understood.
```

## What this certification is NOT

- ❌ A claim that no trendline data can ever be lost (a disk failure
  obviously still loses data — append-only is a behavioural contract,
  not a durability guarantee).
- ❌ A replacement for git history (which records the file changes
  themselves — append-only enforces SEMANTIC append behaviour on top
  of git's syntactic file tracking).
- ❌ A reason to add operator-facing audit logs (Wave 1.1B is
  deliberately silent to operators).

---

— certified by E1 · V-Prelude Wave 1.1B · 2026-05-28
