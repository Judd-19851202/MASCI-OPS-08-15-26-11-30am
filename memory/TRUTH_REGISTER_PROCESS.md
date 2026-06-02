# TRUTH REGISTER · PROCESS

**Authority**: FOCP MASTER PROGRAM · Phase 1
**Companion to**: `TRUTH_REGISTER.md`, `TRUTH_REGISTER_GOVERNANCE.md`

---

## Process · Adding a finding

1. **Capture** — Discover a candidate finding (user report, audit pass, support ticket, code review).
2. **Reproduce** — Reproduce the finding in source (`view_file`, `grep`) OR in preview UI (screenshot tool). Record evidence.
3. **Classify** — Assign severity (CRITICAL / HIGH / MEDIUM / LOW) and source label (e.g., FOCP-P2, ITER500-#X).
4. **Verify** — Set `verified_source_date` = today. Set `verified_ui_date` if applicable.
5. **Allocate ID** — Use the next monotonic `TR-####`.
6. **Append** — Write the row to `TRUTH_REGISTER.md`. Default status = ACTIVE.
7. **Cross-reference** — If the finding supersedes an older register entry, set `superseded_by` (on the older) or note in evidence.

## Process · Working a finding (ACTIVE → IN_PROGRESS → RETIRED)

1. Pick an ACTIVE finding for the sprint. Verify `verified_source_date` is < 30 days old; if older, re-verify before committing.
2. Move to IN_PROGRESS at sprint start. Append date to the row.
3. Implement the change.
4. Verify the fix:
   * `verified_source_date` updated.
   * If UI-facing, `verified_ui_date` captured (screenshot of the fix).
   * If production-deployed, the operator captures `verified_production_date`.
5. Move to RETIRED. Cite resolving file + line numbers + iter/PR.

## Process · Deferring a finding

A finding moves to DEFERRED when verification or implementation requires resources outside AI / engineering control. The DEFERRED row must specify in its evidence field exactly what the operator (or an external party) must provide to unblock.

Examples of valid DEFERRED reasons:

* Requires production access AI cannot hold.
* Requires interview with a domain expert.
* Requires review of a training video / Skywork video / knowledge-base entry whose file path the agent does not have.
* Requires a product-level doctrine decision (e.g., "should Constraint have a multi-state lifecycle?").

## Process · Rejecting a finding

A finding moves to REJECTED when:

1. Re-verification shows the gap does not exist (and never did — distinguish from RETIRED, where the gap once existed and has since been fixed).
2. The finding explicitly conflicts with codified doctrine. Cite the doctrine.

## Process · Quarterly sweep

Every 90 days:

1. **ACTIVE sweep** — re-verify every ACTIVE finding against current source. If unchanged, refresh `verified_source_date`. If invalid, move to REJECTED or SUPERSEDED.
2. **RETIRED spot-check** — pick a random 10% of RETIRED findings and re-verify the fix is still in place. Any regression moves the finding back to ACTIVE.
3. **DEFERRED review** — for each DEFERRED finding, ask the operator: still blocked? blocker resolved? newly actionable?

## Process · Migration from legacy registers

For each legacy register (ITER500_*, ITER501_*, OMEGA_*, GAP_*, GREENFIELD_*, etc.):

1. Read the legacy row.
2. Re-verify against current `/app/` source.
3. Decide outcome.
4. Add a `TR-####` row to `TRUTH_REGISTER.md`. Cite the legacy register in the `source` field.
5. Do NOT delete the legacy register file. It remains an audit-trail artifact.
6. When all of a legacy register's findings are migrated, mark the legacy file with a footer note: `Migrated to TRUTH_REGISTER on YYYY-MM-DD.`

## Process · AI-agent participation rules

AI agents may:

* Add ACTIVE findings (with full evidence).
* Move findings to RETIRED (with cited resolving evidence).
* Propose moves to DEFERRED (with precise operator-action specifications).

AI agents may NOT:

* Set `verified_production_date`.
* Move a finding to REJECTED without operator concurrence on a doctrine conflict.
* Bypass verification ("trust me, this is shipped") — every status change must cite evidence.

## Process · Engineering integration

Every PR / commit that closes a finding shall reference the `TR-####` in its message footer:

```
Closes TR-0003 (Sub/Vendor archive workflow).
```

Engineering retrospectives shall report the ratio of `Closes TR-####` commits to total commits as a discipline metric. Target: > 70% of feature commits cite a TR-####. Hot-fixes and refactors are exempt.

---

End of process.
