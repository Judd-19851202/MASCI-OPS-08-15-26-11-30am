# DEPLOY.md

> **One-line philosophy:**
> The pre-deploy gate is operational guidance — not bureaucracy theater.
> **HOLD is a conversation. BLOCK is a fix-first signal. APPROVE is a fast-path for proven-safe iter classes.**

This document institutionalizes deployment discipline for the MASCI Operations
Platform stabilization phase. It is intentionally short. If you find yourself
adding sections to it, ask whether the platform really needs the additional
process — usually the answer is no.

> **Vocabulary note (iter231):** In this codebase, **"walkthrough"** refers
> to an internal Playwright-driven QA/simulation tool used by developers and
> agents — *never* a user-facing tutorial. End-user contextual guidance is
> delivered exclusively via **HelpTip blocks** ("N coaching tips available
> · tap to expand"). The walkthrough framework PRODUCES coaching content;
> users never interact with it. See `walkthroughs/walkthrough_pass.md` for
> the full terminology table.

---

## 1 · Before every production push

Run the gate:

```bash
python3 /app/scripts/pre_deploy_verify.py
```

Read the verdict. Decide.

That's the discipline.

---

## 2 · Which mode for which situation

| Mode | When to use | Time |
|---|---|---|
| `pre_deploy_verify.py` (default · full) | **Every production push.** Mandatory. | ~100–180s |
| `pre_deploy_verify.py --fast` | Rapid iteration during dev. Skips Phase 3 walkthroughs. **Must justify in deploy summary.** | ~30s |
| `pre_deploy_verify.py --auth-only` | Targeted verification when only auth/RBAC changed. | ~30s |
| `pre_deploy_verify.py --classify-only` | Quick risk read on a pending batch. Doesn't run any tests. | <1s |

When in doubt, run full. The full gate is ~2 minutes. That is not slow.

---

## 3 · How to read the verdict

The gate returns one of three verdicts:

### ✅ APPROVE (exit code 0)
- All phases passed.
- Risk is LOW or MEDIUM with no sensitivity flags.
- Deploy is safe to proceed.
- **You still own the Deploy click.** The gate doesn't deploy for you.

### ⏸ HOLD (exit code 1)
- All phases passed, BUT:
  - risk is HIGH, OR
  - any sensitivity flag is set (auth · data · rollback), OR
  - any phase returned WARN
- **This is not a block.** It is a request for explicit operator acknowledgement.
- Read the deploy summary. Decide intentionally. Deploy if intended.
- HOLD is the gate saying *"this batch touches sensitive surfaces — confirm you mean to."*

### ❌ BLOCK (exit code 2)
- A phase FAILED.
- **DO NOT DEPLOY.** Fix the failing phase first.
- Each failed phase has an `Action` field telling you what to fix.

---

## 4 · Risk classification interpretation

Phase 5 classifies every batch into one of three risk levels:

| Level | What triggers it | Typical deploy cadence |
|---|---|---|
| **LOW** | Coaching-only iter · doc-only iter · no code surfaces touched | Same-day deploy fine |
| **MEDIUM** | UI changes · new routes · walkthrough changes · ≥20 file diff | Same-day deploy fine if APPROVE |
| **HIGH** | Auth/RBAC · backend models · migrations · scheduler · session handling · export pipeline | **Always HOLD.** Operator review required before deploy. |

Plus three sensitivity flags (auth-sensitive · data-sensitive · rollback-sensitive)
that each independently trigger HOLD even if risk is otherwise MEDIUM.

---

## 5 · Rollback expectations

Each deploy summary auto-generates rollback guidance based on classification.
Read it. Internalize it before deploying.

Default rollback expectations by class:

| Class | Rollback path |
|---|---|
| **Coaching-only** | Revert `tips.py` / `tips_es.py` + the frontend wiring change. Idempotent. |
| **UI / route changes** | Revert the commit, redeploy. No data implications. |
| **Auth-touched** | Confirm a tested auth rollback path exists. Re-run `--auth-only` on the rollback commit before reverting. |
| **Data-sensitive** | Verify backups are current. Run `backend/backup_verification.py`. Recent restore-drill required. |
| **Migrations present** | One-way unless explicitly reversible. Reverse-migration path MUST be documented in deploy summary. |

If the deploy summary's rollback section feels thin for your batch, you have
the wrong classification — re-read Phase 5 detail.

---

## 6 · Stabilization-phase deploy cadence philosophy

The platform has crossed the proof threshold for coaching, walkthroughs, and
operational continuity. The next maturity phase is **stabilization** —
characterized by:

- **Smaller operational deltas per deploy.** A 5-tip coaching iter is better than a 30-tip one.
- **Observation between deploys.** Not every approved batch should ship same-hour.
- **Real-user validation cadence.** New surfaces benefit from real usage before the next iter ships on top.
- **Friction reduction over feature expansion.** Removing complexity counts as progress.
- **Strategic-hold respect.** Held architectures (mid-day-defect · Supervisor first-14-days) remain held until operator releases them.

The gate enforces this naturally:
- LOW-risk batches → fast-path APPROVE → small deltas ship easily
- HIGH-risk batches → HOLD → operator reviews before deploying

**You should NOT see frequent HIGH-risk deploys in the stabilization phase.**
If you do, the deploys are too large or the iter is touching the wrong surfaces.

---

## 7 · What this gate is NOT

Reinforced because it matters:

- ❌ NOT a compliance artifact factory. The deploy summary is an operator decision aid, not paperwork.
- ❌ NOT a branch-protection mechanism. It's a discipline tool that runs in the preview pod.
- ❌ NOT a replacement for operator judgment. The verdict is advisory; you still click Deploy.
- ❌ NOT a production smoke test. Use `scripts/post_deploy_check.py` after deploy.
- ❌ NOT a slow ceremony. Full gate runs in ~2 minutes. If it feels slow, you're deploying too rarely.
- ❌ NOT a KPI dashboard. There is no "deploys-per-week" target. There is no leaderboard. There never will be.

---

## 8 · What to do when the gate is wrong

The gate is a tool, not a god. Sometimes it will:
- Classify a batch as HIGH-risk that you know is safe
- WARN on a walkthrough that you've intentionally adjusted
- Fail Phase 1 on a test that you've intentionally rewritten

In those cases:
1. Read the deploy summary's per-phase detail.
2. Confirm the gate's reasoning matches reality.
3. If the gate is reading the situation wrong: **update the gate, not the verdict**. The classification rules live in `pre_deploy_verify.py`; the walkthrough baselines live in `WALKTHROUGH_BASELINES` at the top of that file.
4. Never bypass the gate by editing the summary. If a HOLD is justified, document the justification in your commit message.

---

## 9 · Deeper docs

- Policy: [`walkthroughs/pre_deploy_verification.md`](walkthroughs/pre_deploy_verification.md)
- Walkthrough editorial protocol: [`walkthroughs/walkthrough_pass.md`](walkthroughs/walkthrough_pass.md)
- Foreman architecture brief: [`walkthroughs/foreman_architecture_brief.md`](walkthroughs/foreman_architecture_brief.md)
- Project memory: [`memory/PRD.md`](memory/PRD.md)
- Legacy baseline gate (preserved): [`scripts/pre_deploy_check.sh`](scripts/pre_deploy_check.sh)
- Post-deploy drift check: [`scripts/post_deploy_check.py`](scripts/post_deploy_check.py)

---

*Authored iter229. This document is part of the stabilization-phase maturity
protocol. The discipline is preserved through use, not through length.*
