# TRACK 20.6 · Operational Intelligence Integration Audit — Fire Protection

**Question:** Should overdue fire extinguishers affect readiness on any
existing OI product? If yes — where?

**Answer:** **Yes — via `shop_intelligence` and `fleet_intelligence`, as
an ADDITIONAL SIGNAL only.** Zero new OI product.

## Existing OI products (frozen inventory per Track 20.5)

`safety_morning_digest` · `executive_operations_brief` ·
`po_weekly_digest` · `transportation_intelligence` ·
`fleet_intelligence` · `hr_intelligence` · `training_intelligence` ·
`project_intelligence` · `shop_intelligence`.

## Where overdue extinguishers matter operationally

| Consumer | Current state | Proposed Phase A signal |
|---|---|---|
| **Safety Digest** | Already tracks `fire_extinguishers_overdue` (KPI on `pages/SafetyDigest.jsx`) | **KEEP unchanged.** Consumer-side counter already ships. |
| **Fleet Intelligence** (per-vehicle Asset Thread) | Does not currently surface overdue mounted extinguishers | **EXTEND (client-side adapter).** When rendering a truck's thread and its mounted extinguisher is overdue, add an Attention item: "Truck-mounted fire extinguisher overdue (unit_id: FE-217, next due YYYY-MM-DD)". No new OI product; no server-side computation. |
| **Shop Intelligence** (Shop Asset Care) | Does not currently surface overdue extinguishers on the shop queue | **EXTEND (client-side adapter, optional).** Same pattern — surface as a shop-side attention item. Deferred if Fleet lens suffices. |
| **Project Intelligence** | N/A (extinguishers aren't project-assigned yet) | Deferred. Phase B may add. |
| **Executive Operations Brief** | Already indirectly reflects via the Safety digest counter | **KEEP unchanged.** No new server calculation. |
| **Transportation Intelligence** | Some DOT extinguishers matter for over-the-road units | Deferred. Add in a future Track when DOT extinguisher rules are formalized. |

## Zero-new-product doctrine

- The Safety Portal already ships the `fire_extinguishers_overdue`
  KPI on the digest. That is the **single canonical count**.
- The Asset Thread will read the existing `next_due_date` on
  `db.fire_extinguishers` (Phase A) or the derived next-due from
  `asset_service_events` (Phase B), and render it via the shared
  `AttentionChip` primitive — **not via a new score model, not via a
  new OI product**.
- There is no fire-protection-specific score. No %. No compliance
  verdict. No legal-defensibility claim.

## What Phase A actually adds to the OI surface

**Client-side adapters only.** Concretely, when the Asset Thread
resolves an extinguisher (Phase A read-side), the page's
`attentionAdapter` computes:

```js
if (nextDue && nextDue < today) {
  attention.push({
    severity: "HIGH",
    label: `Fire extinguisher ${unit_id} overdue`,
    why: `Next inspection was due ${nextDue}.`,
    owner: "Safety",
    deep_link: `/safety-portal/fire-extinguishers`,
  });
}
```

That is the entire OI change. No backend computation added.

## What Phase A does NOT add

- No new OI product.
- No new OI recipient class.
- No new digest job.
- No new email flow.
- No new scheduler.
- No new score or % anywhere.
- No new PDF renderer.

## Zero-Drift OI accounting

- OI engine inventory: **FROZEN** (nine files, lock-tested).
- OI component inventory: **FROZEN** (seven JSX primitives + one JS
  helper).
- Track 19.62 will not add a `.py` file to `backend/operational_intelligence/`.
- Track 19.62 will not add a `.jsx` file to
  `frontend/src/components/operational_intelligence/`.

**Verdict:** Existing OI products fully cover the fire-protection
readiness question. Zero new OI product.
