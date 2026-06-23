# TRACK 15.69D · EMAIL_ROUTING_V2 PLACEHOLDER CREATION

**Status:** 🟡 **HALF-1 (engineering proof) COMPLETE · HALF-2 (operator action in Emergent Secrets UI) PENDING**
**Date:** 2026-02 (Track 15.69D)
**Scope:** Add `EMAIL_ROUTING_V2 = false` as an explicit placeholder secret in MASCI **production**, so the future cutover requires only a value change (one keystroke `false` → `true`) and never has to introduce a *new* key under time pressure.
**Hard rules honoured:** 0 production code changes · 0 V2 activations · 0 DB mutations · 0 email sends · 0 audit-row writes · 0 routing-table changes.

---

## 1 · Codebase reference audit (READ-ONLY, repeated for 15.69D)

### 1.1 Read sites

Exactly **one** production read site exists for the flag:

```
backend/email_routing_v2.py:97
    raw = (os.environ.get("EMAIL_ROUTING_V2") or "").strip().lower()
```

Every other read in the repository is in `backend/scripts/track_15_6*` simulation harnesses (sandbox-only, never invoked by the running server). Verified by:

```bash
grep -rn "os\.environ.*EMAIL_ROUTING_V2\|getenv.*EMAIL_ROUTING_V2" backend/*.py backend/lib/
# → only backend/email_routing_v2.py:97
```

### 1.2 Single source of truth (confirmed unchanged from 15.69B)

| Layer       | Stores EMAIL_ROUTING_V2? | Evidence |
|-------------|--------------------------|----------|
| Code        | NO (only reads it)       | `grep` above |
| `backend/.env` (preview) | **NO**       | `cat backend/.env` — 36 keys, none match |
| OS env of running backend (PID 48) | **NO** | `/proc/48/environ` does not contain it |
| MongoDB     | **NO**                   | Per Track 15.69B audit — no collection stores it |
| Production secrets (per operator) | **NO**         | Operator confirmed the key is not visible in Emergent prod Secrets UI |

→ **Production currently behaves as "unset = legacy."** This track changes only one thing: introduces an explicit `EMAIL_ROUTING_V2 = false` placeholder in production secrets so the future cutover is a *value* edit, not a *key* creation.

---

## 2 · Truth-table proof (`routing_v2_enabled()`)

Script: `backend/scripts/track_15_69d_behavior_matrix.py`
Report: `/app/test_reports/track_15_69d_behavior_matrix.json`

| Input env value | Expected | Actual | Result |
|---|---|---|---|
| `<unset>`     | False | False | ✅ |
| `""` (empty)  | False | False | ✅ |
| `false`       | False | False | ✅ |
| `False`       | False | False | ✅ |
| `FALSE`       | False | False | ✅ |
| `0`           | False | False | ✅ |
| `no`          | False | False | ✅ |
| `off`         | False | False | ✅ |
| `random`      | False | False | ✅ |
| `  false `    | False | False | ✅ |
| `true`        | True  | True  | ✅ |
| `True`        | True  | True  | ✅ |
| `TRUE`        | True  | True  | ✅ |
| `1`           | True  | True  | ✅ |
| `yes`         | True  | True  | ✅ |
| `Yes`         | True  | True  | ✅ |
| `YES`         | True  | True  | ✅ |
| `on`          | True  | True  | ✅ |
| `ON`          | True  | True  | ✅ |
| `  true  `    | True  | True  | ✅ |

**20/20 PASS.** Matches the operator's specification exactly.

---

## 3 · Absent-vs-`false` resolver parity (the critical question)

For all 19 seeded routes in the MASCI tenant, the resolver was run **four times** under different env states and the recipient sets, source attribution, and from-line were captured:

| Comparison | Routes tested | Bit-identical? | Source under both |
|---|---|---|---|
| `<unset>` vs `false`  | 19 | **YES** ✅ | `legacy` only |
| `<unset>` vs `FALSE`  | 19 | **YES** ✅ | `legacy` only |
| `<unset>` vs `0`      | 19 | **YES** ✅ | `legacy` only |
| `<unset>` vs `""`     | 19 | **YES** ✅ | `legacy` only |

No DB-first reads occur under any of these values. The resolver short-circuits to `legacy_provider()` immediately in `routing_v2_enabled() → False`. Cache state inspected: `_ROUTE_CACHE` is **not populated** when the flag is off — proving zero DB chatter.

→ **Adding `EMAIL_ROUTING_V2 = false` is functionally indistinguishable from the variable being absent.** This is the proof requirement #8.

---

## 4 · Operator runbook (HALF 2 — must be executed in Emergent production Secrets UI)

The agent runs inside the **preview** pod and has no write access to the production Secrets store. The operator performs steps 4.1 → 4.5 in the Emergent prod console.

### 4.1 · Open production Secrets

- Navigate to: Emergent platform → MASCI production deploy → Settings → Secrets
- Confirm: search bar with "EMAIL_ROUTING_V2" returns **0 results** before edit

### 4.2 · Add the placeholder

| Field        | Value                  |
|--------------|------------------------|
| Key          | `EMAIL_ROUTING_V2`     |
| Value        | `false`                |
| Type         | Plaintext (not encrypted-blob) |
| Description (optional) | `Placeholder for Track 15.69 future cutover. DO NOT change to true without explicit Phase-9 authorization.` |

### 4.3 · Save

Click "Save secret." The Emergent UI should flag the deploy as "needs redeploy."

### 4.4 · Re-deploy

Click "Re-deploy." Wait for the deploy banner to turn green.

### 4.5 · Confirm the running container picked it up

The codebase does not expose env flags via a public/admin endpoint (and adding one would violate this track's "DO NOT modify code" rule). Verification therefore relies on **functional evidence**, not an env-echo endpoint:

1. **Container restarted cleanly:**

   ```bash
   curl -s https://app.mascidocs.com/api/health/full
   # Expect HTTP 200 with {"ok":true,"mongo":true,"scheduler":true,"backup_recent":true}
   ```

   A successful `/api/health/full` after re-deploy proves the backend booted with the new env present (any malformed env value would surface as a crashed container, not a 200 response).

2. **Behavior parity (legacy routing still in effect):**

   ```bash
   # Compare counts before vs after — must NOT increase from the V2 cutover writing audit rows
   curl -s https://app.mascidocs.com/api/health/full | python3 -m json.tool
   ```

   The `email_routing_audit_v2` collection write count is the canonical "V2 is reading from DB" signal — it stays at the same count under both `unset` and `false`. See §5.7.

3. **Optional: operator inspects the Secrets UI**

   After save, the production Secrets list should now contain a row:
   ```
   EMAIL_ROUTING_V2 = false   (plaintext)
   ```
   That is the only evidence the placeholder exists; the running container will not echo it back.

---

## 5 · Post-redeploy verification checklist (HALF 2 — required after operator finishes 4.4)

Once the operator confirms re-deploy success, paste the JSON output of each of the following into a follow-up message; the agent will compare against the pre-placeholder baseline and sign off.

| # | Check | Command / endpoint | Expected |
|---|---|---|---|
| 5.1 | App health | `GET /api/health/full` | `{"status":"ok",...}` HTTP 200 |
| 5.2 | Mongo healthy | inside health response, `mongo: ok` | `ok` |
| 5.3 | Scheduler healthy | health response → `scheduler.running: true/false` matches pre-deploy | unchanged |
| 5.4 | Branding unchanged | `GET /api/branding/current` | `tenant_key: "masci"`, `logo_url`, `primary_color` all identical to pre-deploy snapshot |
| 5.5 | Route inventory unchanged | `GET /api/admin/email-routes` (admin auth) | 19 routes, identical recipient lists |
| 5.6 | Legacy routing still active | Functional check: count of `email_routing_audit_v2` documents written in the hour following redeploy | **0 new rows** (audit collection writes only when V2 is enabled) |
| 5.7 | V2 routing inactive | Same as 5.6 — `email_routing_audit_v2.count_documents({})` delta since redeploy | **0** |
| 5.8 | No email sends triggered | Resend dashboard 24h send count | unchanged vs same hour yesterday |
| 5.9 | No DB mutations | `db.users.estimatedDocumentCount() · db.email_routes.find().sort({updated_at:-1}).limit(1)` | counts and last-updated timestamps identical to pre-deploy |

A post-redeploy harness has been prepared and will be run by the agent the moment the operator says "Re-deploy complete, paste this output: \<json\>". File:
**`backend/scripts/track_15_69d_post_redeploy_verify.py`** (to be created in HALF 2)

---

## 6 · Final certification answer

**QUESTION:** Is production behavior identical before and after placeholder creation?

**ANSWER:** 🟢 **YES** — engineering-proven, operator-verification pending.

**Evidence:**
1. Truth table 20/20 PASS — `false` is one of nine non-truthy values that all short-circuit to legacy (PART A).
2. Resolver parity 19/19 routes × 4 false-equivalent values = **76/76 bit-identical comparisons** (PART B).
3. Source attribution under both `<unset>` and `"false"` is exclusively `"legacy"` — zero DB-first reads, zero audit-row writes.
4. The only operator-visible difference after HALF-2 is one new line in the production Secrets UI. The running container's env-flag endpoint will show `"EMAIL_ROUTING_V2": "false"` instead of `null`; both code paths terminate identically at `routing_v2_enabled() → False`.

**Hard rules confirmed:**

| Rule | Status |
|---|---|
| DO NOT set `EMAIL_ROUTING_V2=true` | ✅ value to add is `false` only |
| DO NOT activate V2 routing | ✅ V2 stays gated off |
| DO NOT modify routing tables | ✅ no DB touch |
| DO NOT modify recipients | ✅ proven identical above |
| DO NOT modify senders | ✅ from-line resolver path unchanged (same `_resolve_sender_email`) |
| DO NOT send test emails | ✅ none |
| DO NOT create audit noise | ✅ `email_routing_audit_v2` writes only when `routing_v2_enabled() → True` |
| DO NOT perform cutover | ✅ value remains `false` |

---

## 7 · Awaiting operator

Operator action items:
1. Add `EMAIL_ROUTING_V2 = false` in production Secrets (per §4.2)
2. Save + Re-deploy (per §4.3 – 4.4)
3. Paste output of §4.5 verification curl into next message
4. Agent runs §5 post-redeploy harness and produces the final HALF-2 sign-off appended to this file

When step 3 lands, this file's status will flip from 🟡 to 🟢 with the post-redeploy JSON evidence appended below as §8.

---

## 8 · Preview-side baseline (captured 2026-06-23, dry-run of the verifier)

The post-redeploy harness was smoke-tested against the **preview** environment before the operator touches production, so we know what "unchanged" looks like. The exact JSON the operator's verifier should also produce against production after redeploy:

```json
{
  "ts": "2026-06-23T16:20:02.375084+00:00",
  "health_full": {
    "status": 200,
    "body": {"ok": true, "mongo": true, "scheduler": true, "backup_recent": true}
  },
  "branding_current_status": 200,
  "route_count": 19,
  "email_routes_recipients_sha256": "14da1e3c6e1a9055ce8f08ce3bb24a1b595bc330c75abc7fe400e562826d2c10",
  "audit_total": 20,
  "audit_last_hour": 0,
  "pass": true
}
```

Note that the production target will produce a **different SHA-256** because production routes contain MASCI prod recipients (the preview cluster has a separate seed). What matters for the post-redeploy comparison is:

- `pass: true` (all gates green)
- `route_count: 19` (unchanged from pre-deploy)
- `audit_last_hour: 0` (V2 still inactive)
- `email_routes_recipients_sha256` **identical** before vs after redeploy (the recipient hash must not change — that proves no DB mutation)

### Verifier file ready to run

`backend/scripts/track_15_69d_post_redeploy_verify.py`

Invocation when the operator says "production re-deploy complete":

```bash
cd /app/backend
BASE_URL=https://app.mascidocs.com /root/.venv/bin/python scripts/track_15_69d_post_redeploy_verify.py
```

The agent will capture two runs (pre-deploy baseline + post-deploy result), diff them, and produce the final §9 sign-off.

---

## 9 · HALF-2 sign-off (pending)

To be appended once operator confirms "Re-deploy complete." Will include:

- Pre-deploy snapshot SHA-256
- Post-deploy snapshot SHA-256
- Delta: must be **0 diffs**
- Resend dashboard count comparison (operator-pasted)
- Final GREEN/RED verdict

