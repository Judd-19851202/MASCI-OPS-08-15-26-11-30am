# DEPLOY-STABILIZATION-1 · Operator Handoff & Go/No-Go

_Final cleanroom certification + operator-owned action list._
_Generated: 2026-05-28 · Phase DEPLOY-STABILIZATION-1._

> The governance layer is GREEN. The platform self-protection layer is
> active. This document is the operator's flight card for the final
> validation + cutover sequence before Phase V.1 RFI MVP unlocks.

---

## 0 · Cleanroom certification (agent-completed)

| Gate | Result |
|---|---|
| Authority Mismatch Probe (`--gate`) | 🟢 0 violations · 0 warnings · 58 baselined · 90 ms |
| Self-Protection page status | 🟢 **GREEN** across all 8 stanzas |
| `drift.open_gaps` | 🟢 **0** |
| `context_governance.tbd` | 🟢 **0** |
| `authority.new_violations` | 🟢 **0** |
| `trust_surfaces` | 🟢 10 registered · 8 live · 2 planned |
| `truthful_state.contracts` | 🟢 12 declared |
| `telemetry.status` | 🟢 green |
| `field_walks.status` | 🟢 all 5 checklists current |
| PII scan on `/api/admin/governance/self-protection` | 🟢 clean (no `@`, `password`, `phone`, `email`) |
| Chart-creep scan on `SelfProtection.jsx` | 🟢 clean |
| Stale-bypass / TODO / FIXME / HACK in governance code | 🟢 none |
| Preview-URL contamination in governance code | 🟢 none |
| Preview-vs-prod source_hash | ▸ **preview ahead** — deploy will move prod forward (EXPECTED) |
| **Total regression battery** | 🟢 **52 / 52 PASS** |

### Test suites in the green sweep
- `test_governance_self_protection_page.py` · 11/11
- `test_stabilization_final_capabilities.py` · 4/4
- `test_governance_authority_mismatch_probe.py` · 6/6
- `test_trust_po1_backend_enforcement.py` · 10/10
- `test_trust_po1_frontend_capability_scope.py` · 4/4
- `test_contextual_return_path_iter443.py` · 7/7
- `test_mongo_id_leak_contract.py` · 10/10

### Preview environment confirmed
```
app_env     : preview
db_name     : masci_safety_preview
source_hash : 9c08065382b13022e550cf6682c59156   (preview · ahead)
prod_hash   : 0f5d997dffba4e95fefa9a58c7f02780   (production · will move forward on deploy)
```

🟢 **The agent's W3 obligations are complete.** Everything below is
operator-owned by definition (real iPads / real people / real time /
real deploy click).

---

## 1 · Workstream 1 — Real Field Walks (OPERATOR-OWNED)

Execute the 5 checklists on the actual hardware your field crews
carry. Do NOT simulate. Do NOT skip the suspend/resume + airplane
mode steps — those are the ones that catch the worst regressions.

| # | Checklist | Hardware | Critical moves |
|---|---|---|---|
| 1 | `FIELD_WALK_CHECKLISTS/FL.md` | Foreman iPad | airplane mode mid-draft · suspend Safari · photo upload on 4G |
| 2 | `FIELD_WALK_CHECKLISTS/PM.md` | PM laptop + iPad | office → field handoff · project switch · cross-portal navigation |
| 3 | `FIELD_WALK_CHECKLISTS/Safety.md` | Safety officer iPad | end-to-end · deliberate `QuotaExceededError` simulation |
| 4 | `FIELD_WALK_CHECKLISTS/MobileSafari.md` | Real iOS Safari (current version) | full cycle on real ITP behavior |
| 5 | `FIELD_WALK_CHECKLISTS/HR.md` | HR laptop | cross-portal reads of safety + payroll records |

### Friction-capture template (paste back into `STABILIZATION_FINAL_REPORT.md §W5`)

```
### FL.md walk · <operator name> · <iPad serial> · <YYYY-MM-DD>
- Hesitation moments    :
- Unclear state         :
- Workflow confusion    :
- Authority confusion   :
- Recovery confusion    :
- Upload friction       :
- Misleading wording    :
- Verdict               : 🟢 / 🟡 / 🔴
```

Repeat one block per walk. 🟡 or 🔴 verdicts block the deploy until
remediated.

---

## 2 · Workstream 2 — Telemetry Observation Window (24-72h)

Quiet watch on the preview deployment. **Do NOT overreact to
single events.** Look for **patterns**.

### Daily quick-glance (1 minute, 2× / day)
1. Hit `https://safety-audit-mobile-1.preview.emergentagent.com/admin/governance/self-protection`
2. Confirm overall pill is still **OK** (green)
3. Check `Authority Protection · NEW VIOLATIONS = 0`
4. Check `Open Governance Gaps · TOTAL = 0`

### Pattern signals worth investigating
| Signal | Threshold | Where |
|---|---|---|
| Same Support ID surfaces 3+ times in 24h | yes — investigate device | Admin Governance · Draft Health · "Devices affected" expander |
| `recovery.absent` event fires 5+ times across distinct devices | likely soft regression in cross-token storage | `/api/draft-telemetry/recent` |
| `quota.warning` fires within 30 minutes of a `write.fail` | photo blob overflow regression | Draft Health Tile · quota chip |
| New authority warning lands in OPS-1 page | a PR drifted from the capability layer | `python3 scripts/authority_mismatch_probe.py` locally |
| OPS-1 page status flips from green → amber | one of the 8 stanzas degraded | drill into specific stanza on the page |

### One-event noise (DO NOT panic)
- One transient `recovery.absent` from a single device
- One `quota.warning` from a heavy-photo report
- One amber Cloudflare cache-edge response on the auth-gate test

---

## 3 · Workstream 3 — Pre-Deploy Cleanroom Pass

🟢 **DONE BY AGENT.** See §0 above. Re-run before the click:

```bash
# 5-second sanity bundle the operator can paste before deploy
python3 /app/scripts/authority_mismatch_probe.py --gate
cd /app/backend && python3 -m pytest tests/pw_suite/test_governance_self_protection_page.py tests/pw_suite/test_stabilization_final_capabilities.py -q
```

Both must exit 0. If either fails, **do not deploy.**

---

## 4 · Workstream 4 — Save + Deploy (OPERATOR-OWNED)

### Step 1 · Save to GitHub
- Use the **"Save to GitHub"** affordance in the Emergent chat input.
- Confirm the commit message references `DEPLOY-STABILIZATION-1`
  so it's discoverable later.

### Step 2 · Deploy from Emergent UI
- Trigger from the Emergent deploy panel.
- Watch the deploy logs for any non-zero exit on
  `stage_governance_authority_mismatch` (the pre-deploy gate).

### Step 2.5 · Record the deploy moment (NEW · CUTOVER-READY)
**Immediately after the deploy succeeds**, hit the new endpoint
so the OPS-1 Deployment stanza records the cutover:

```bash
PROD="https://mascidocs.com"
PROD_TOKEN=$(curl -s -X POST "$PROD/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password":"MASCI1982!"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s -X POST "$PROD/api/admin/governance/record-deploy" \
  -H "X-Admin-Token: $PROD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note":"CUTOVER-READY · forward from 0f5d997"}' | python3 -m json.tool
```
Expect: `appended: true · history_size: 1+`. Idempotent against
re-runs with the same hash — safe to repeat.

### Step 3 · Production verification (paste these curl checks)
```bash
PROD="https://mascidocs.com"
# 1. version identity
curl -s "$PROD/api/version" | python3 -m json.tool
#    → expect: app_env: production · db_name: masci_safety
#    → expect: source_hash matches the preview hash above

# 2. health
curl -s "$PROD/api/health" | python3 -m json.tool

# 3. self-protection (admin only — bring an admin token)
PROD_TOKEN=$(curl -s -X POST "$PROD/api/admin/login" -H "Content-Type: application/json" -d '{"password":"MASCI1982!"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s "$PROD/api/admin/governance/self-protection" -H "X-Admin-Token: $PROD_TOKEN" | python3 -m json.tool | head -40
#    → expect: page_status: green · drift.open_gaps: 0

# 4. authority-mismatch probe runs the same on production source tree
#    (already proven by deploy gate, but worth a manual check)
```

### Step 4 · Browser verification (5 minutes, 1 operator)
- Visit `https://mascidocs.com/admin/governance/self-protection` →
  page must read **OK** with all 8 stanzas green.
- Visit `https://mascidocs.com/admin/governance` → no chart creep,
  no preview banner, no preview env markers.
- Open `/po-requests` from PM hub → approve block visible.
- Open `/po-requests` from Field Leadership hub → approve block hidden.
- Open `/inspections/:id` from `/pm/inspections` → back link reads
  "Inspections" (not "Admin Console").

---

## 5 · Workstream 5 — Post-Deploy 72-Hour Observation

Same daily glance + pattern signals from §2, but on **production**.
Observation window starts when the deploy lands.

### Hard rollback triggers (mascidocs.com)
- OPS-1 page reports `page_status: red` for >15 minutes
- `authority.new_violations` becomes non-zero
- `drift.open_gaps` jumps to >0 without an explanation
- `/api/draft-telemetry/health` returns 5xx
- Any FL user reports seeing approval controls on a PO

### Soft rollback triggers (investigate first, don't rollback yet)
- OPS-1 amber for <15 minutes (one stanza dipped)
- One device shows repeated `recovery.absent` events
- `governance/health` chip flips to drift on one portal

Rollback path: use the **rollback** option in the Emergent UI (free of
cost · reverts to the prior production commit).

---

## V.1 Gate (binding)

Phase V.1 RFI MVP begins ONLY AFTER:

- [ ] All 5 field walks recorded with 🟢 verdicts
- [ ] 24-72h preview observation clean (no recurring patterns)
- [ ] Save to GitHub completed
- [ ] Production deploy succeeded
- [ ] 4 production curl checks PASS
- [ ] Browser verification 5-step PASS
- [ ] 72-hour production observation clean

Once these are checked, the operator issues an explicit **"start V.1"**
command in a fresh chat and the agent begins the RFI MVP build.

---

## Verdict

🟢 **Cleanroom locked. Foundation is operationally ready for cutover.**

The agent has done everything that doesn't require physical iPads or
human deploy clicks. The remaining work is the operator's — and the
operator has the green light to proceed.
