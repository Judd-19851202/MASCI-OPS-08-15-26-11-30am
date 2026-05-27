# Trust Regression Gap Analysis
## Phase TRUST-1 · 2026-05-27

> What's NOT tested. Where invisible failure can hide. The
> regression suite covers the iter440/442/443 work well; this
> document catalogues the holes.

---

## 1 · Current coverage snapshot

| Suite | Files | Tests | Status |
|---|---|---|---|
| Draft telemetry endpoint | `test_draft_telemetry_endpoint.py` | 10 | ✅ green |
| Draft loss remediation | `test_draft_loss_remediation.py` | 5 | ✅ green |
| Draft loss regression iter440 | `test_draft_loss_regression_iter440.py` | 6 | ✅ green |
| Field trust iter442 | `test_field_trust_iter442.py` | 7 | ✅ green |
| Contextual return-path iter443 | `test_contextual_return_path_iter443.py` | 7 | ✅ green |
| Governance health chip | existing | n | ✅ |
| Portal token routing | existing | n | ✅ |
| Static helpers extraction | `test_static_helpers_extraction.py` | n | ✅ |

**Total new trust-related tests since iter440:** 35.

---

## 2 · Coverage gaps (ranked)

### 2.1 · ITP / Private Browsing simulation
**Why missing:** Hard to trigger in headless Chromium. WebKit-only path.
**Risk:** Genuine field scenario (foreman returns from vacation) goes untested.
**Mitigation:** Add a synthetic IDB-clear test that mimics the symptom (mount with no draft + no localStorage) and asserts the page handles it cleanly.

### 2.2 · iPad viewport for draft survivability
**Why missing:** Existing parametrize lists `mobile` only on draft tests.
**Risk:** Superintendent layout regressions invisible.
**Mitigation:** Add `'ipad'` to parametrize on existing draft tests. 1-line conftest expansion. (Tracked as TF-009.)

### 2.3 · Sibling form idempotency persistence
**Why missing:** Only Daily Report's idempotency persistence is tested.
**Risk:** NewIncident, NewInspection, HrPayrollVariance could regress without notice.
**Mitigation:** Add 1 parametrized test per sibling form covering submit-reload-resubmit.

### 2.4 · Cross-portal navigation preserves session
**Why missing:** Existing `test_portal_token_routing.py` covers routing; not session continuity across portals.
**Risk:** Multi-login user friction (TF-010 backlog).
**Mitigation:** Optional.

### 2.5 · MongoDB _id leak surface
**Why missing:** Only `/api/draft-telemetry/recent` asserted.
**Risk:** Any future endpoint could leak ObjectId silently (TF-015).
**Mitigation:** Add a contract test that calls a sampling of read-only `/api/admin/*` and `/api/pm/*` endpoints and grep-asserts no `"_id":` in responses.

### 2.6 · Pre-deploy gate touches draft-telemetry route
**Why missing:** Deploy gate verifies `/api/healthz` only.
**Risk:** Silent route drop (TF-018).
**Mitigation:** One-line curl in `pre_deploy_check.sh`.

### 2.7 · ViewCAPA / ViewInspection / ViewMeeting return-path
**Why missing:** iter443 only migrated Incident.
**Risk:** Same field-report pattern as the Incident issue, latent on three other shared surfaces.
**Mitigation:** Migrate one surface at a time (per `RETURN_PATH_GOVERNANCE_STANDARD §7`).

### 2.8 · Device memory adoption telemetry
**Why missing:** `device_memory.*` events not yet emitted.
**Risk:** Cannot measure whether the iter442 coaching is working (TF-006).
**Mitigation:** Add events + 1 telemetry test.

### 2.9 · Draft Health tile drill-down
**Why missing:** Drill-down UI doesn't exist yet (TF-005).
**Risk:** Per-device triage requires manual curl.
**Mitigation:** Build affordance + 1 test.

### 2.10 · Restore archive recovery affordance
**Why missing:** Surface not built (TF-016).
**Risk:** Mis-tap on Discard is recoverable in principle, not in practice.
**Mitigation:** Add a UI surface + 1 test.

### 2.11 · "Quiet" verdict for telemetry pipeline outage
**Why missing:** Tile maps 0 events → "Healthy" today (TF-012).
**Risk:** Pipeline outage looks identical to clean week.
**Mitigation:** Add minimum-volume floor + verdict differentiation.

### 2.12 · Spanish localization regression
**Why missing:** iter442 strings not in Spanish dictionary (TF-007).
**Risk:** Bilingual operator sees mixed-language coaching.
**Mitigation:** Dictionary update + 1 Spanish-viewport test.

---

## 3 · Invisible failure inventory

The most dangerous gaps are not test gaps — they're surfaces where
a failure literally cannot be observed today:

| Surface | What's silently failable |
|---|---|
| Telemetry pipeline | Could drop all events; tile shows "Healthy" (TF-012) |
| ITP eviction | Foreman returns from vacation; no banner (TF-001) |
| Submit-then-queue-fail | Draft already discarded; payload lost in transit (TF-011) |
| _id leak on a future endpoint | No contract test (TF-015) |
| Draft-telemetry route absent post-deploy | No deploy gate verification (TF-018) |

Every one of these is a "no telemetry to even tell us it happened"
class.

---

## 4 · Recommendation sequence

| Priority | Add to test surface |
|---|---|
| Wave 1 | TF-015 (_id leak contract test) + TF-018 (deploy gate route ping) + TF-012 (Quiet verdict) |
| Wave 2 | TF-009 (iPad parametrize) + TF-002 (sibling idempotency tests) + TF-016 (recovery affordance) |
| Wave 3 | TF-005 (drill-down) + TF-006 (device memory telemetry) + TF-001 (ITP empty-IDB banner) |
| Backlog | TF-007 (Spanish) + TF-014 (visual sweep) + remaining |

---

## 5 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 12 coverage gaps catalogued · sequencing in `TRUST_REMEDIATION_PRIORITY_PLAN.md`
- **Cross-refs:** `TRUST_FINDINGS_MATRIX.json`, `TRUST_REMEDIATION_PRIORITY_PLAN.md`
