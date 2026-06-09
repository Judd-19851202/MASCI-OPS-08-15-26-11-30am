# MOTIVE-PROD-INCIDENT-001 · RECOVERY REPORT

**Incident:** MOTIVE-PROD-INCIDENT-001
**Phase:** 3 · Recovery analysis
**Status:** ✅ ANALYSIS COMPLETE · 🟡 PARTIAL DATA UNRECOVERABLE BY DESIGN

---

## Q13 · Can Motive replay missed webhooks?

**NO — not for the deliveries that hit during the incident window.**

### Why not
Motive's webhook system (per [Motive Webhooks v2 documentation](https://developer.gomotive.com/docs/webhooks-v2)) interprets *any HTTP 2xx response from the receiver* as a successful delivery. It only retries on 5xx errors (with exponential backoff, ~4-5 attempts over ~24 hours).

The MASCI receiver in `routes/integrations/webhooks.py:48-58` returns:
```python
return {
    "ok": False, "status": "awaiting_credentials",
    "stored": False, "message": "...",
}
```
FastAPI serialises this as **HTTP 200 OK** with the dict body. From Motive's perspective every one of the 41,139 rejected payloads was *accepted*. **Motive will not replay them.**

### Caveat
The receiver's docstring on line 6 claims "503" but the code returns 200. This is a code-level defect noted for follow-up (NOT remediated in this incident scope per OMEGA — minimum-safe remediation only). Even if the receiver had returned 5xx, the retry window would have expired ~24 hours after the first batch on 2026-06-08T15:54, so by 2026-06-09T16:00 Motive's retry queue for those payloads is empty regardless.

---

## Q14 · Can a full reconciliation sync recover all missed operational state?

| Domain | Recoverable via API sync? | Method | Verified |
|---|---|---|---|
| **Vehicles** | ✅ YES — full | `MotiveService.sync_assets()` → `GET /v3/vehicle_locations` | ✅ 190 records created in prod 2026-06-09T17:03 |
| **Drivers** | ✅ YES — full | `MotiveService.sync_users()` → `GET /v1/users` | ✅ 65 records created in prod 2026-06-09T17:03 |
| **Assets (non-vehicle)** | ✅ YES — full | included in sync_assets | ✅ |
| **Geofences** | ✅ YES — full | `MotiveService.sync_geofences()` → `GET /v2/geofences` | ✅ 67 records created in prod 2026-06-09T17:03 |
| **Current GPS positions** | ✅ YES — current snapshot | sync_assets uses `vehicle_locations` which returns the *current* location per vehicle | ✅ persisted into `asset_mappings.motive.{lat,lon,located_at}` |
| **GPS position HISTORY** | ❌ **NOT RECOVERABLE** | Motive does not expose historical position trails older than the current cycle without a dedicated event subscription | — |
| **Harsh-event / hard-brake history** | ❌ Limited recovery | `GET /fleet_events` exposes ~7 days back-fill; events older than the API's retention are gone | — |
| **DVIR submissions** | ❌ Limited recovery | DVIR events flow only via webhook in Motive's public API surface | — |
| **HOS violations** | 🟡 Partial | Available via `/v2/hos_violations` endpoint, retention varies | — |
| **Geofence enter/exit events during incident** | ❌ NOT recoverable | event-only payload — once missed, gone | — |
| **AI Coach Recap** | ❌ Webhook-only | — |
| **Gateway disconnected / reconnected** | ❌ Webhook-only | — |

---

## Q15 · Exact operational data at risk

### Reconcilable (NOW RECOVERED via this incident's sync)
- ✅ Vehicle roster (190 vehicles)
- ✅ Driver roster (65 drivers)
- ✅ Geofence inventory (67 geofences)
- ✅ Current GPS position per vehicle

### Permanently lost (no recovery path)
| Data class | Estimated loss volume (incident window 2026-06-08T15:54 → 2026-06-09T16:59 ≈ 25 h) |
|---|---|
| Vehicle GPS position UPDATES (event stream) | If a meaningful fraction of the 41,139 hits were real Motive deliveries, this represents up to ~41k position points. **Likely ZERO** if the post-remediation pattern (100% unsigned, no Motive signature) holds for the prior window — but cannot be confirmed without Motive-side delivery logs. |
| Harsh-brake / acceleration events during window | Cannot reconstruct |
| Geofence enter/exit events during window | Cannot reconstruct |
| DVIR submissions during window | Cannot reconstruct (DVIR webhook-only) |
| AI Coach recaps during window | Cannot reconstruct |
| Gateway disconnect / reconnect events during window | Cannot reconstruct |
| Fault codes opened/closed during window | Cannot reconstruct |
| HOS violations during window | Possibly retrievable via `/v2/hos_violations` REST endpoint — NOT attempted in this incident scope |

### Impact on downstream MASCI surfaces during incident window
- Operations dashboard: GPS staleness ≥ 26 h (now refreshed)
- Dispatch live activity strip: empty during incident (no real-time updates from webhook stream)
- Safety harsh-event card: empty during incident
- Shop fault-code feed: empty during incident
- Driver scorecards / Andres-Masci-style profiles: stale during incident

### Recommendation
**File a Motive Support ticket** to:
1. Confirm whether any signed webhook deliveries were attempted to `https://mascidocs.com/api/integrations/motive/webhook` during the incident window.
2. Request a one-time replay of any deliveries that Motive's outbound log shows as 2xx-completed but for which MASCI returned `stored: false`.
3. Confirm the webhook subscription endpoint URL on Motive's side matches the production URL.

This is the only path to recover meaningful event-stream data that may have been lost.

— end of recovery report —
