# MASCI · MOTIVE 7-DAY LIVE EVENT VALIDATION

**Date:** 2026-06-08
**Scope:** OMEGA · Read-only · live production-traffic validation.
**Cutover reference:** M-1R Reliability supervisor armed at **2026-06-08T15:42:39 UTC** (the latest operator-driven hardening event in MASCI). All "real production" claims below are measured against this cutover.
**Verdict:** 🟡 **INITIAL LIVE VALIDATION — CONTINUE MONITORING** (less than 1 day of post-cutover traffic available)

---

## EXECUTIVE SUMMARY (one paragraph)

MASCI's Motive receiver is hardened, signature-verified, and ready. The reliability supervisor is alive and successfully completed one full sync cycle (events / assets / users / geofences) against live Motive API. **However, since the M-1R cutover at 15:42 UTC (≈1 hour ago at audit time), zero real Motive webhooks have arrived.** The last webhook receipt of any kind was a P1.6 replay event at 14:27 UTC — 90 minutes before the cutover. This audit cannot confirm or refute that the operator's webhook re-verification fixed the upstream Motive dashboard subscription, because **no event from Motive has fired in the audit window**. Either (a) the upstream subscriptions are now enabled but no event has occurred during the ~1-hour window, (b) subscriptions remain disabled in Motive Admin, or (c) the upstream is sending but those payloads are being filtered or rate-limited before reaching the receiver. Pull-side reliability is fully proven (poll sync wrote 90 GPS rows in the last hour with no errors). Push-side reality is unobservable until events occur.

---

## PHASE 1 — WEBHOOK STATUS CHECK

| Check | Result |
| --- | --- |
| Webhook endpoint active in MASCI | ✅ PASS (`POST /api/integrations/motive/webhook` mounted, route returns 200/401 correctly) |
| Webhook secret present | ✅ PASS (ends `c106`, stored in `integration_settings.motive.webhook_secret_value`) |
| Receiver accepts valid HMAC | ✅ PASS (16 successful signed-replay receipts since 2026-06-08 12:42) |
| Receiver rejects invalid HMAC | ✅ PASS (3 rejections logged with `status="Awaiting Credentials"` for pre-cred attempts on 12:38-12:41; the negative-signature-test path returns HTTP 401 — verified in P1.5) |
| Last webhook received | 2026-06-08 14:27:38 UTC (**90 min before cutover** — replay event, not real production) |
| Last webhook family received | `dvir` (P1.6 replay) |
| Total webhook receipts all-time | 19 (3 pre-cred rejected, 16 sprint-replay successes) |
| Webhook receipts since M-1R cutover | **0** |

**Phase 1 verdict: PASS for receiver health · FAIL for live-traffic evidence.**

---

## PHASE 2 — REAL EVENT FLOW CHECK (post-cutover only)

Webhook events (`source="webhook" AND received_at >= 2026-06-08T15:42`) grouped by family:

| Family | Count | First | Last | Decorated summary | Visible surface |
| --- | ---: | --- | --- | --- | --- |
| vehicle_gps | **0** | — | — | — | — |
| harsh_event | **0** | — | — | — | — |
| fault_code | **0** | — | — | — | — |
| dvir | **0** | — | — | — | — |
| geofence_enter | **0** | — | — | — | — |
| geofence_exit | **0** | — | — | — | — |
| hos_violation | **0** | — | — | — | — |
| gateway_disconnected | **0** | — | — | — | — |
| gateway_reconnected | **0** | — | — | — | — |
| asset_geofence_enter | **0** | — | — | — | — |
| asset_geofence_exit | **0** | — | — | — | — |
| ai_coach_recap | **0** | — | — | — | — |
| fault_code_closed | **0** | — | — | — | — |
| inspection_report_updated | **0** | — | — | — | — |
| speeding_event | **0** | — | — | — | — |
| engine_on | **0** | — | — | — | — |
| engine_off | **0** | — | — | — | — |
| dashcam_disconnected | **0** | — | — | — | — |
| vehicle_created_updated | **0** | — | — | — | — |
| user_created_updated | **0** | — | — | — | — |

**All real-production webhook counters are zero.** Either the upstream subscriptions are silent, or the post-cutover window is too short for any subscribed event to have fired yet.

### Poll-source events since cutover (reliability loop refreshes)

| Source | Kind | Count | First | Last |
| --- | --- | ---: | --- | --- |
| `poll` | `vehicle_gps` | **90** | 2026-06-08 15:47:58 | 2026-06-08 15:48:01 |

The 90 poll-source rows are the result of the M-1R reliability supervisor's first `sync_events` tick. They are production-real GPS readings pulled from Motive's `/v3/vehicle_locations` API, but they arrived via the **pull** path rather than the **push** webhook path. **This is real Motive data — just not from a real-time webhook.**

---

## PHASE 3 — END-TO-END TRACE

For families with zero post-cutover events, no trace is possible. For the **poll-source `vehicle_gps` rows** that did arrive after cutover:

```
Motive API (/v3/vehicle_locations · X-API-KEY auth)
  → MotiveService.sync_events()
  → motive_events.insert (90 docs · event_family="vehicle_gps" · source="poll")
  → integration_sync_logs.insert (status="Success" · records_created=90)
  → asset_mappings.motive.{lat,lon,located_at} HYDRATED (90 vehicles refreshed)
  → AssetProfile → Motive tab shows live coords for those 90 vehicles
  → Operations Center counters re-rolled-up (over_24h dropped 95→94)
  → Reliability state endpoint reports status=ok for the events tick
```

End-to-end PASS for the pull path. **Push path cannot be traced because no push events have arrived.**

---

## PHASE 4 — RELIABILITY LOOP CHECK

| Loop | Last tick | Status | Records (C/U/F) |
| --- | --- | --- | --- |
| `sync_events` | 2026-06-08 15:48:01 | ✅ Success | C=90 · U=0 · F=0 |
| `sync_assets` | 2026-06-08 15:48:10 | ✅ Success | C=0 · U=190 · F=0 |
| `sync_users` | 2026-06-08 15:48:13 | ✅ Success | C=0 · U=65 · F=0 |
| `sync_geofences` | 2026-06-08 15:48:17 | ✅ Success | C=0 · U=67 · F=0 |

Reliability supervisor: **alive · started_at 2026-06-08T15:42:39 · all 4 loops green · 0 failures · multi-worker singleton-lock honored**.

Staleness rollup (after first tick):
- `over_24h`: **94** of 158 GPS-enabled vehicles (down from 95 at audit baseline — proves at least 1 vehicle refreshed)
- `over_7d`: 79
- `over_30d`: 71

**Phase 4 verdict: PASS.**

---

## PHASE 5 — VISIBILITY CHECK

| Surface | Status | Evidence |
| --- | --- | --- |
| Asset Profile (Motive tab + Events tab) | ✅ PASS (renders live GPS for 90 refreshed vehicles + replay event timeline) |
| Integration Events Feed (Safety / HR / Admin) | ⚠️ PARTIAL — renders correctly but only replay rows exist; no real webhook events to display since cutover |
| Dispatch Hub Integrations tab — Live Activity strip | ⚠️ PARTIAL — strip renders, but no real geofence enter/exit events since cutover |
| Operations Center — Integration Readiness tile | ✅ PASS (counters use the freshly-hydrated asset_mappings · idle/moving/not_reporting reflect post-tick numbers) |
| Safety Hub event card | ⚠️ PARTIAL — same as Integration Events Feed (UI ready · zero real events) |
| Shop Hub | ⚠️ PARTIAL — fault_code / DVIR rendering is ready · no real events to display |

**Phase 5 verdict: PASS for pull-path visibility (Asset Profile, Operations Center) · PARTIAL for push-path surfaces (Safety Hub, Shop Hub, Dispatch Live Activity) — all waiting on upstream events.**

---

## PHASE 6 — NOISE CHECK

| Family | Classification | Why |
| --- | --- | --- |
| `vehicle_gps` (pull) | **Useful** | 90 rows / 15 min via the reliability poll · expected cadence · zero error rate |
| All push families | **Not enough data yet** | 0 post-cutover events across all 20 named families |
| `vehicle_gps` (push) | **Not enough data yet** | The original subscription that produced 3 rejected attempts on 12:38-12:41 has not retried |

**No family is producing noise. No family is misconfigured by MASCI side.** If subscriptions are enabled upstream and still nothing flows in a 24 h window, that would indicate misconfiguration — but the current 1-hour window is too short to draw that conclusion.

---

## PHASE 7 — TRUST VERDICT

| Role | Trust today | Reason |
| --- | --- | --- |
| **Operations** | **70 %** | Pull-side data is fresh (5 % of GPS fleet refreshed in the last hour · reliability loop will continue every 15 min). Push-side latency unknown until first real event. |
| **Dispatch** | **30 %** | Live Activity strip is wired and ready. No real arrivals/departures observable yet. |
| **Safety** | **15 %** | Event card is wired and ready. No real harsh / HOS / AI-Coach events received. |
| **Shop** | **15 %** | Equipment-down rendering is ready. No real fault_code / DVIR events received. |
| **Admin** | **95 %** | Reliability state endpoint surfaces full health; sync logs are fresh; mapping coverage unchanged from M-1R. |

The pull-side is **PROVEN** at the 1-hour mark (one complete reliability cycle observed with zero errors). The push-side is **NOT YET OBSERVABLE** — neither proven nor disproven.

---

## CONFIDENCE WINDOW

| Metric | Pre-M-1R (audit) | Post-M-1R (now) |
| --- | --- | --- |
| Last successful sync_events | 2026-06-08 12:58 (manual M-1) | **2026-06-08 15:48** (automatic supervisor tick) |
| over_24h stale | 95 | **94** |
| over_7d stale | 79 | 79 |
| over_30d stale | 71 | 71 |
| Real production webhooks | 0 (3 attempted, all rejected) | 0 (no new attempts since cutover) |
| Reliability scheduler alive | NO | **YES** |

---

## FINAL VERDICT

🟡 **INITIAL LIVE VALIDATION — CONTINUE MONITORING**

- **Pull-side: PROVEN.** Reliability supervisor running every 15 minutes (events) and 12 hours (assets/users/geofences). One complete cycle observed · zero errors · real Motive API data landing in MASCI collections · existing surfaces consuming it.
- **Push-side: NOT YET OBSERVABLE.** Zero real Motive webhooks have arrived in the post-cutover window (≈1 hour). Insufficient time has elapsed to confirm or refute that the operator's webhook re-verification has caused subscriptions to deliver to MASCI. The receiver is provably ready; the upstream is provably silent for this short window.

**Recommended re-audit checkpoint:** 24 hours post-cutover (2026-06-09 15:42 UTC). At that point, if `motive_events.find({source:"webhook", received_at >= cutover}).count() == 0`, the verdict shifts to 🔴 NOT PROVEN for the push path and operator-side investigation in Motive Admin Dashboard is required. If push events arrive in any volume, the verdict shifts toward 🟢 PROVEN family-by-family.

**Continue monitoring · no code changes required · no M-2 · no new features.**

---

## GUARDRAILS UPHELD

- ❌ No code changes · No DB changes · No deploys · No automation · No M-2 · No new features
- ✅ Read-only · evidence-based · cutover-anchored
- ✅ Honest about what is unobservable (push path) vs proven (pull path)

---

## EVIDENCE CITATIONS

- `db.integration_sync_logs` (`integration=motive AND sync_type=webhook`): 19 rows · last = 2026-06-08T14:27:38 · 0 since cutover.
- `db.integration_sync_logs` (`integration=motive AND started_at >= cutover`): 4 reliability ticks all `Success` between 15:48:01 and 15:48:17.
- `db.motive_events` (`source=webhook AND received_at >= cutover`): empty.
- `db.motive_events` (`source=poll AND received_at >= cutover`): 90 rows, all `event_kind=vehicle_gps`, between 15:47:58 and 15:48:01.
- `db.integration_settings.motive`: `enabled=true · status=Connected · last_sync_at=2026-06-08T15:48:17.236621 · webhook_secret_value ends c106`.
- M-1R Reliability `STATE` snapshot via `/api/admin/integrations/motive/reliability-state` confirmed `alive=true` with all 4 loops `last_status=ok`.
