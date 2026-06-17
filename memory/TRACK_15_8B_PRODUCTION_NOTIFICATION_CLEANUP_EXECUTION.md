# TRACK 15.8B — PRODUCTION NOTIFICATION CLEANUP EXECUTION WITH PROD-CONFIRM SAFETY

**Date:** 2026-06-17
**Target:** `https://mascidocs.com` · DB `masci_safety`
**Final verdict:** 🟢 **PHASES 1 + 2 COMPLETE (script hardened, 31/31 tests green)** · 🔴 **PHASES 3-5 STILL OPERATOR-OWNED** — the preview pod is correctly blocked at the MongoDB Atlas authorization layer from authenticating against `masci_safety`. Operator must run the now-hardened script from a production-authorized context. Full runbook in §6.

---

## 1. Executive summary

The Track 15.2 cleanup script has been **hardened** with the requested `--prod-confirm` belt-and-suspenders safety guard. The patch is shipped, exhaustively tested (20 new unit + CLI tests, 100% green; 11 pre-existing Track 15.1/15.2 tests still green; 0 regressions), and the live preview run confirms the guard rejects production-mutation attempts that lack the explicit confirmation.

**Phase 3 (production dry-run) and Phase 4 (production apply) still cannot be executed by the agent** for the same reason documented in Track 15.8A: the preview pod's MongoDB Atlas user has `readWrite` only on `masci_safety_preview` and is denied by the database server when it tries to query `masci_safety`. The hardened script's safety guard is *additive* on top of this Atlas-level barrier — even if the operator accidentally runs the script with the wrong env vars on a production pod, the guard now refuses unless every safety condition is satisfied.

The runbook for the operator (§6 below) is unchanged from Track 15.8A in structure but now invokes the explicit `--apply --prod-confirm` form per the new contract.

---

## 2. Phase 1 — Patch the script with --prod-confirm ✅

**File modified:** `/app/backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py`

### What was added

```python
def cli_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(...)
    p.add_argument("--apply", action="store_true", ...)
    p.add_argument("--dry-run", action="store_true", dest="dry_run_explicit",
                   help="explicit dry-run (default behavior; no-op alias).")
    p.add_argument("--prod-confirm", action="store_true", dest="prod_confirm",
                   help="required to --apply against APP_ENV=production / "
                        "DB_NAME=masci_safety. Belt-and-suspenders guard.")
    p.add_argument("--max-rows", type=int, default=200, ...)
    return p.parse_args(argv)


def validate_safety(args, app_env, db_name) -> Optional[str]:
    """Return None if safe, else an error string.

    Rules (TRACK 15.8B):
      • Dry-run always safe; --prod-confirm is no-op for dry-runs.
      • --apply against production target (APP_ENV=production OR
        DB_NAME=masci_safety) REQUIRES --prod-confirm.
      • --prod-confirm ASSERTS APP_ENV=production AND DB_NAME=masci_safety.
      • Non-production --apply works without --prod-confirm (preview).
    """
    if not args.apply:
        return None
    env = (app_env or "").strip().lower()
    db = (db_name or "").strip()
    targets_prod = (env == "production") or (db == "masci_safety")
    if args.prod_confirm:
        if env != "production":
            return f"--prod-confirm requires APP_ENV=production (got APP_ENV={app_env!r}). Refusing to apply."
        if db != "masci_safety":
            return f"--prod-confirm requires DB_NAME=masci_safety (got DB_NAME={db_name!r}). Refusing to apply."
        return None
    if targets_prod:
        return ("Refusing production mutation without --prod-confirm "
                f"(APP_ENV={app_env!r} DB_NAME={db_name!r}). "
                "Re-run with --apply --prod-confirm on a production-authorized pod.")
    return None
```

Plus an `__main__` guard wired to short-circuit on a safety failure with `sys.exit(2)`.

### Live behavior smoke (this pod)

```
$ MONGO_URL="dummy" DB_NAME="masci_safety" APP_ENV="production" \
    python3 scripts/track_15_2_backfill_leaked_pm_offboarding.py --apply
# SAFETY GUARD: Refusing production mutation without --prod-confirm
#   (APP_ENV='production' DB_NAME='masci_safety').
#   Re-run with --apply --prod-confirm on a production-authorized pod.
# (exit code 2)
```

```
$ MONGO_URL="$PREVIEW_URL" DB_NAME="masci_safety_preview" APP_ENV="preview" \
    python3 scripts/track_15_2_backfill_leaked_pm_offboarding.py
# TRACK 15.2 cleanup · db=masci_safety_preview · ts=20260617T023202Z
# scanned: 0 leaked PM-offboarding row(s)
# nothing to clean up. exit 0.
```

Both behaviors match the contract.

## 3. Phase 2 — Regression tests ✅ 20/20 green + 11/11 pre-existing

**File created:** `/app/backend/tests/test_track_15_8b_prod_confirm_safety.py` (240 lines, 20 tests).

### Test groups and what each one proves

**`TestProdConfirmSafetyGuard`** — pure unit tests of `validate_safety()`:
| # | Test | Proves |
|---|---|---|
| 1 | `test_dry_run_always_safe_no_env` | Dry-run with `APP_ENV` and `DB_NAME` unset → safe. |
| 2 | `test_dry_run_safe_even_against_production` | Read-only dry-run against prod target → safe. |
| 3 | `test_dry_run_with_prod_confirm_is_noop` | `--prod-confirm` without `--apply` doesn't change behavior. |
| 4 | `test_preview_apply_without_prod_confirm_allowed` | Pre-deploy gate flow (preview apply) still works without `--prod-confirm`. |
| 5 | `test_prod_apply_without_prod_confirm_refused_by_app_env` | `--apply` + `APP_ENV=production` (any DB) → refused. |
| 6 | `test_prod_apply_without_prod_confirm_refused_by_db_name` | `--apply` + `DB_NAME=masci_safety` (any env) → refused. |
| 7 | `test_prod_confirm_with_wrong_app_env_refused` | `--prod-confirm` + `APP_ENV=preview` → refused. |
| 8 | `test_prod_confirm_with_wrong_db_name_refused` | `--prod-confirm` + `DB_NAME=masci_safety_staging` → refused. |
| 9 | `test_prod_confirm_with_correct_env_allowed` | Happy path: all four conditions met → allowed. |
| 10 | `test_prod_confirm_app_env_case_insensitive` | `APP_ENV="PRODUCTION"` also works. |

**`TestCliBehavior`** — subprocess invocations of the actual script:
| # | Test | Proves |
|---|---|---|
| 11 | `test_help_lists_prod_confirm_flag` | `--help` documents `--prod-confirm`, `--apply`, `--dry-run`. |
| 12 | `test_prod_apply_without_prod_confirm_exits_2` | CLI exits 2, stderr says "Refusing production mutation". |
| 13 | `test_prod_confirm_wrong_db_exits_2` | CLI exits 2 on wrong DB. |
| 14 | `test_prod_confirm_wrong_env_exits_2` | CLI exits 2 on wrong env. |

**`TestPredicateAndVerbContracts`** — guarding the patch didn't accidentally weaken the original Track 15.2 safety contract:
| # | Test | Proves |
|---|---|---|
| 15 | `test_predicate_is_four_clause_and` | Predicate still requires `linked_source_module="hr.offboarding"` AND `recipient_role="pm"` AND `recipient_user_id=None` AND `linked_employee_id != None`. |
| 16 | `test_no_hard_delete_calls` | Script source contains no `notifications.delete_one` / `delete_many`. Verb is still `$set: expires_at = now`. |
| 17 | `test_audit_event_on_every_apply` | Audit row is still written with category `track_15_2.pm_offboarding_cleanup`. |
| 18 | `test_idempotency_flag_is_set` | `_track_15_2_cleaned_at` flag still present (idempotent re-runs). |
| 19 | `test_max_rows_cap_default_is_200` | 200-row cap unchanged. |
| 20 | `test_apply_default_is_false` | `--apply` and `--prod-confirm` default to False — dry-run still the default. |

### Run result

```
$ python3 -m pytest tests/test_track_15_8b_prod_confirm_safety.py -v
============================== 20 passed in 0.86s ==============================

$ MONGO_URL="$PREVIEW_URL" DB_NAME="masci_safety_preview" \
    python3 -m pytest tests/test_track_15_1_offboarding_pm_scoping.py \
                       tests/test_track_15_2_pm_add_member_runtime.py -v
======================== 11 passed, 1 warning in 5.27s =========================
```

**31 tests green · 0 regressions.**

## 4. Phase 3 — Production dry-run 🔴 BLOCKED (operator action required)

Same blocker as Track 15.8A — the preview pod's MongoDB Atlas user is not authorized to read `masci_safety`. Re-attempting the dry-run from preview returns:

```
pymongo.errors.OperationFailure:
  not authorized on masci_safety to execute command { find: "notifications", ... }
  Code: 13 (Unauthorized)
```

This is the **correct security boundary working as designed**, and is now reinforced by the in-script safety guard. The new guard would NOT have helped here — the Atlas server refused the connection before the safety code ran. Two complementary protections now stack:

1. **Atlas role-based access control** — preview pod literally cannot read or write `masci_safety`.
2. **Script-level safety guard (Track 15.8B)** — even from a production-authorized pod, `--apply` against production now requires explicit `--prod-confirm` AND explicit env-var match.

## 5. Phase 4 — Production apply 🔴 NOT REACHED (depends on Phase 3)

## 6. Phase 5 — Live PM bell verification 🔴 NOT REACHED (depends on Phase 4)

---

## 7. Operator runbook (the only safe path forward — UPDATED for 15.8B)

Run these on a pod with **production-scoped MongoDB credentials**.

### Step 1 — Confirm pod identity
```bash
echo "APP_ENV=$APP_ENV DB_NAME=$DB_NAME"
# Required:  APP_ENV=production DB_NAME=masci_safety
```
Abort if either does not match.

### Step 2 — Dry run (no --prod-confirm needed)
```bash
cd /app/backend
python3 scripts/track_15_2_backfill_leaked_pm_offboarding.py
```
Or with the explicit alias for clarity in the runbook:
```bash
python3 scripts/track_15_2_backfill_leaked_pm_offboarding.py --dry-run
```
Writes `scripts/track_15_2_dryrun_<UTC_TS>.json`.

### Step 3 — Review the dry-run ledger
```bash
ls -lt scripts/track_15_2_dryrun_*.json | head -1
jq '{row_count, sample_titles: [.plans[].title][:10]}' \
   scripts/track_15_2_dryrun_<UTC_TS>.json
```

Acceptance criteria (must all be satisfied):
- `row_count` is reasonable (single- to low-double-digit).
- Every title matches `"New task: Offboarding: <name> — ..."` pattern.
- Expected names per the user's screenshot: Ryan Heims, James Pudder, Mark Stalter, Timothy Carpenter, Shan Wilson (and any other historical offboarding).
- Every entry has `current_recipient_role: "pm"` and `current_recipient_user_id: null`.
- Every entry has non-null `linked_employee_id`.
- `proposed_action` is `expire_and_fanout` or `expire_only_no_targets`.

If any entry's title does not match the offboarding pattern, **stop** and surface the ledger entry.

### Step 4 — Apply (NOW requires --prod-confirm)
```bash
python3 scripts/track_15_2_backfill_leaked_pm_offboarding.py --apply --prod-confirm
```

The script will assert `APP_ENV=production` AND `DB_NAME=masci_safety`. If either is wrong, it exits 2 without touching the database.

If the operator omits `--prod-confirm`, the script also exits 2:
```
# SAFETY GUARD: Refusing production mutation without --prod-confirm
#   (APP_ENV='production' DB_NAME='masci_safety').
#   Re-run with --apply --prod-confirm on a production-authorized pod.
```

On success, the script writes `scripts/track_15_2_applied_<UTC_TS>.json` and prints per-row progress.

### Step 5 — Verify the PM bell
1. Sign into `/pm/portal` as one of the PMs whose bell previously showed the leaked rows.
2. Open the bell drawer.
3. **Expected:**
   - Leaked offboarding rows (Ryan Heims, James Pudder, Mark Stalter, Timothy Carpenter, Shan Wilson, George Shannis, etc.) gone.
   - Legitimate notifications (including post-15.1 person-targeted offboarding rows) still visible.
   - Unread count reflects cleanup.
   - Drawer renders cleanly on iPad — no overlap on close/mute/mark-read.
   - 0 new console errors.

### Step 6 — Archive ledgers
```bash
cp scripts/track_15_2_dryrun_<UTC_TS>.json /app/memory/
cp scripts/track_15_2_applied_<UTC_TS>.json /app/memory/
```

### Step 7 — Reversal procedure (only if anything looks wrong post-apply)
```javascript
// Re-open the original broadcast row:
db.notifications.update_one(
  { id: "<row id from applied ledger>" },
  { $set: { expires_at: "<original_expires_at from ledger>",
            _track_15_2_cleaned_at: null,
            _track_15_2_replaced_with: null } }
)
// Remove the per-PM copies created during apply:
db.notifications.delete_many(
  { _track_15_2_source_id: "<row id from applied ledger>" }
)
```

Both halves are necessary (re-open original + remove fanout copies).

---

## 8. Cleanup ledger (this track)

| Category | Created | Deleted | Net |
|---|---|---|---|
| Production users | 0 | 0 | **0** |
| Production records | 0 | 0 | **0** |
| Production notifications modified | 0 | 0 | **0** |
| Real emails | 0 | — | 0 |
| Real SMS | 0 | — | 0 |
| Preview DB writes | 0 | 0 | **0** (0-row dry-run only) |
| Source files modified | 1 | 0 | **1** (cleanup script) |
| Test files created | 1 | 0 | **1** |
| Memory reports | 1 | 0 | **1** |

**Production is in the exact state it was in pre-track.** No mutations were possible.

## 9. Final status

# 🟢 PHASES 1 + 2 COMPLETE · 🔴 PHASES 3-5 OPERATOR-OWNED

**Done in this track:**
- Cleanup script hardened with `--prod-confirm` + explicit `--dry-run` alias.
- New `validate_safety()` helper enforces APP_ENV/DB_NAME assertions when --prod-confirm is used.
- 20 new unit + CLI tests, 100% green.
- 11 pre-existing Track 15.1/15.2 tests still 100% green (0 regressions).
- Predicate (4-clause AND), verb (expire-not-delete), idempotency flag, audit, max-row cap, dry-run default — all preserved.

**Deferred to operator (carry-over from Track 15.8A — unchanged in scope, only the invocation form is now `--apply --prod-confirm`):**
- Run §7 from a production-authorized pod.
- Archive both ledger JSON files to `/app/memory/`.
- Sign into `/pm/portal` as a representative PM and confirm the bell is clean.

The production cleanup itself is still pending, but the path forward is now defense-in-depth-hardened. Atlas RBAC + script-level guard + dry-run-by-default + 200-row cap + per-row audit + ledger reversibility.

---

## 10. Files changed in Track 15.8B

- `/app/backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py` — MODIFIED (added `--prod-confirm`, `--dry-run` alias, `validate_safety()` helper, updated `__main__` guard, updated docstring).
- `/app/backend/tests/test_track_15_8b_prod_confirm_safety.py` — NEW (20 tests, 240 lines).
- `/app/memory/TRACK_15_8B_PRODUCTION_NOTIFICATION_CLEANUP_EXECUTION.md` — NEW (this report).
- `/app/memory/PRD.md` — UPDATED Latest Closed Track entry.
