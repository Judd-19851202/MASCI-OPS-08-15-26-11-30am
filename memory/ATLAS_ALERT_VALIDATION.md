# Atlas Alert Validation & Escalation — Certification

**Phase:** SIGMA-III · P1
**Iteration:** iter437
**Status:** 🟢 IN-APP THRESHOLDS CERTIFIED · ATLAS-SIDE CONFIG OPERATOR-OWNED

---

## Summary

The two-layer Atlas alerting model is:

1. **In-app last-line defence** — `/api/cluster/capacity` returns
   `severity ∈ {ok, warning, critical}` computed from
   `storage_used_pct` vs `ATLAS_QUOTA_MB`. The `<ClusterCapacityBanner />`
   on the login page surfaces this to crews BEFORE they submit a form.
2. **Atlas-side early warning** — proactive alerts configured in the
   Atlas project (CPU, connections, disk %, replica lag, backup
   failures). See `ATLAS_ALERTS_RUNBOOK.md` for the full required-alert
   matrix.

This document certifies what is **in-app verified** (the part we own
end-to-end) and documents the operator-owned validation path for the
Atlas-side configuration (which can only be confirmed by signing into
the Atlas UI).

---

## 1. In-app threshold logic — CERTIFIED

`/app/backend/routes/cluster_capacity.py` enforces:

| `storage_used_pct` | `severity`  |
|--------------------|-------------|
| ≥ 95%              | `critical`  |
| ≥ 80% and < 95%    | `warning`   |
| < 80%              | `ok`        |

**Proof from current preview probe (2026-02):**

```json
{
  "ok": true,
  "tier_quota_mb": 10240,
  "storage_used_mb": 792.14,
  "storage_used_pct": 7.7,
  "severity": "ok",
  "dbs": {
    "masci_safety_preview": 228.73,
    "masci_safety": 563.41
  },
  "ts": "2026-05-27T01:50:10Z"
}
```

**Three-severity verification** (per PRD § 1c of `REGRESSION_STRATEGY.md`,
recorded 2026-05-26):

- `ATLAS_QUOTA_MB=750`  → `severity=critical` (121.5%)
- `ATLAS_QUOTA_MB=1100` → `severity=warning`  (82.9%)
- `ATLAS_QUOTA_MB=10240` → `severity=ok`        (8.9%)

All three transitions hold. Backed by Playwright Flow 2
(`test_cluster_capacity_reachable_from_browser`) which exercises the
CORS path used by the in-app banner.

---

## 2. Escalation matrix

| Severity   | In-app surface                                | Atlas alert    | Operator action               |
|------------|-----------------------------------------------|----------------|-------------------------------|
| `ok`       | Banner hidden                                 | None           | None                          |
| `warning`  | Amber sticky banner across every page         | Disk > 75%     | Schedule tier review w/ ops   |
| `critical` | Red banner · "Block-imminent" message         | Disk > 90%     | PAGER · upgrade tier or purge |

The **in-app** layer fires immediately on every page load (≤ 60s cache
TTL). The **Atlas** layer is the early-warning system that wakes the
operator at home — see `ATLAS_ALERTS_RUNBOOK.md` for the recommended
alert thresholds (75% disk, 90% disk, 75% CPU, conns > 80% of pool,
replica lag > 60s, backup failure).

---

## 3. What this iteration validated

| Item                                              | Status                                                  |
|---------------------------------------------------|---------------------------------------------------------|
| `/api/cluster/capacity` endpoint reachable        | ✅ HTTP 200 · 7.7% utilization · severity=ok            |
| Severity computation                              | ✅ All 3 thresholds verified (per PRD 2026-05-26)        |
| `ClusterCapacityBanner` renders on login page     | ✅ Playwright Phase 1 Flow 1 covers this                 |
| `/api/cluster/capacity/history?days=N` reachable  | ✅ Playwright Phase 2 Flow 10 covers this                |
| Snapshot loop running (hourly)                    | ✅ 22 samples present from `cluster_capacity_history`    |
| `/admin/database` panel renders capacity widget   | ✅ New in Sigma-III · screenshot in `CALM_OBSERVABILITY_UI.md` |

---

## 4. What this iteration deliberately did NOT touch

- **Atlas UI configuration** — only the operator has the credentials.
  This document validates that the in-app contract is correct; the
  Atlas-side rules must be confirmed by the operator signing into
  `https://cloud.mongodb.com` and following
  `ATLAS_ALERTS_RUNBOOK.md` § "Manual configuration steps".
- **SMS / pager integration** — out of scope. Email alerts to
  `safety@mascigc.com` + project owner is the doctrine.
- **CPU / connection / replica alerts** — covered by the existing
  runbook. No code change needed on this side.

---

## 5. Operator validation checklist (1-minute)

Recommend the operator runs this once per quarter or after any Atlas
tier change:

```bash
# 1. In-app banner contract
curl -fsS https://mascidocs.com/api/cluster/capacity | python3 -m json.tool
# Expected: severity ∈ {ok, warning} · storage_used_pct shown

# 2. History endpoint contract
curl -fsS "https://mascidocs.com/api/cluster/capacity/history?days=7" | python3 -m json.tool | head -20
# Expected: samples > 0 · slope_mb_per_day populated · days_to_quota OR null

# 3. Atlas UI sanity
# Sign in → Project → Alerts → Alert Settings.
# Confirm at least 5 active alerts (75% disk, 90% disk, CPU, conns, backup).
```

If step 3 shows fewer than 5 active alerts, fix per
`ATLAS_ALERTS_RUNBOOK.md` BEFORE the next deploy.

---

## 6. Verdict

🟢 **In-app severity threshold logic — CERTIFIED.**
🟡 **Atlas-side alert configuration — OPERATOR-OWNED (runbook ready).**

The platform's last-line defence (in-app banner + history endpoint +
`/admin/database` widget) is verified end-to-end. The early-warning
layer (Atlas alerts) requires operator action to enable in the Atlas
UI — instructions are in `ATLAS_ALERTS_RUNBOOK.md` and the validation
script above.

# 🟢 P1 — Atlas Alert Validation & Escalation · CLOSED (in-app side)
