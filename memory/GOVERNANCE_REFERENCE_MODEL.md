# Governance Reference Model — Phase IV-BETA.5A-P5A

*iter437 · 2026-02-27*
*Status: 🟢 TWO-CLASS MODEL OPERATIONAL*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Document the **two-class governance reference model** introduced in
P5A. The model defines how the platform's chip, deploy gate, and
trendline file collaborate to expose drift against the *right* anchor.

## II. The two classes

| Class | Source | Cadence | Persistence | Sanctity |
|---|---|---|---|---|
| **Operator** | Manual command | Low-frequency (milestones) | Append-only | 🔴 sacred |
| **Auto-deploy** | `pre_deploy_check.sh` | Every successful deploy | Append-only · rolling cap | 🟡 breadcrumb |

## III. Operator class semantics (🟢)

- Declared via `--checkpoint "<free text>"` (label MUST NOT start with `auto · deploy`).
- Sacred — used to anchor drift against an operator-blessed governance state.
- Lifetime: until the rolling cap (500 records) ages it out OR until another operator checkpoint supersedes it.
- Chip displays drift as `+N drift since checkpoint`.

## IV. Auto class semantics (🟢)

- Declared automatically at the tail of `pre_deploy_check.sh`.
- Label format: `auto · deploy {git-sha}` (e.g. `auto · deploy 7af3c12`).
- Breadcrumb — primarily for audit & post-mortem analysis.
- Lifetime: until the rolling cap ages it out.
- Chip displays drift as `+N drift since deploy`.

## V. Resolution algorithm (🟢)

The chip endpoint resolves drift reference as follows (per portal):

```
records = load_trendline(portal)

operator_cps = [r for r in records if checkpoint and not label.startswith("auto · deploy ")]
auto_cps     = [r for r in records if checkpoint and     label.startswith("auto · deploy ")]

if operator_cps:        anchor = operator_cps[-1]   # most-recent operator wins
elif auto_cps:           anchor = auto_cps[-1]       # fallback breadcrumb
else:                    anchor = None               # falls to rolling math
```

**Last-write-wins WITHIN each class · operator class ALWAYS preferred
over auto class.**

## VI. What this protects against (🟢)

| Risk | Mitigation |
|---|---|
| Auto-deploy spam dilutes operator anchor | Operator class always wins |
| Operator forgets to declare checkpoint | Auto-deploy class still gives a breadcrumb |
| Trendline grows forever | Rolling cap at 500 records (per P2A) |
| Deploy gate fails to checkpoint | `|| true` in shell script — gate continues, checkpoint quietly skipped |
| Stale checkpoint becomes misleading | Operator can declare a new one any time |
| Auto label collision (same git-sha twice) | Trendline is append-only — duplicates coexist with distinct timestamps |

## VII. Operator workflows (🟢)

### Declaring a new operator anchor

```bash
python3 scripts/diff_doctrine_baseline.py --append \
  --checkpoint "Post-feature-X release · operator-blessed"
```

The chip switches to this new anchor immediately. All future drift
reads relative to it until a newer operator checkpoint supersedes.

### Reading current anchor

```bash
curl -s "$URL/api/governance/health/pm" | jq '{kind: .checkpoint_kind, label: .checkpoint_label}'
```

### Audit deploy-by-deploy

```bash
jq '.records[] | select(.checkpoint and (.checkpoint_label | startswith("auto · deploy ")))' \
  /app/memory/DOCTRINE_TRENDLINE.json
```

## VIII. What is NOT in this model (🟢)

- ❌ NO email notification when drift is detected
- ❌ NO dashboard panel
- ❌ NO chart
- ❌ NO automatic rollback
- ❌ NO automatic checkpoint promotion (auto → operator)
- ❌ NO checkpoint deletion API (append-only)
- ❌ NO confirmation prompt before declaring (operator confidence assumed)

## IX. Doctrine reaffirmed

- ✅ Two-class model · operator > auto
- ✅ Last-write-wins within each class
- ✅ Filesystem-only · no DB · no notifications
- ✅ Chip footprint unchanged
- ✅ Preview only · NO production deploy
