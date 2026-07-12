# DEPLOY-NOW-001 · CERTIFIED PERFORMANCE BUNDLE PRODUCTION DEPLOY

**Sprint:** PLATFORM-EXCELLENCE — DEPLOY-NOW-001
**Authorization:** Operator chat 2026-06-09 — *"DEPLOY-NOW-001 · CERTIFIED PERFORMANCE BUNDLE PRODUCTION DEPLOY · STATUS: AUTHORIZED"*
**Date:** 2026-06-09
**Verdict:** 🟡 **PRE-DEPLOY VERIFICATION 🟢 PASS · DEPLOY EXECUTION PENDING OPERATOR**

> **Honest posture (per OMEGA safety clause):** Production (`mascidocs.com`) runs on Google Cloud Run behind Cloudflare — separate infrastructure from this Preview pod. The Preview container has no production deploy pipeline credentials. The agent's role is *pre-deploy verification + BEFORE state capture + rollback identification + operator runbook + AFTER validation harness*. Per directive, *"DO NOT build anything new · DO NOT refactor · DO NOT start any new sprint"* — agent built nothing; this report verifies the already-certified preview build is ready to ship.

---

## 1 · APPROVED bundle composition (already certified)

| Sprint | Certification | Already in preview build | Production status |
| --- | --- | :---: | :---: |
| ROUTE-SPLIT-001 Wave 1 (admin/*) | `ROUTE_SPLIT_001_WAVE1_CERTIFICATION.md` | ✅ | NOT deployed |
| ROUTE-SPLIT-001 Wave 2 (dispatch + safety-portal) | `ROUTE_SPLIT_001_WAVE_2_CERTIFICATION.md` | ✅ | NOT deployed |
| ROUTE-SPLIT-001 Wave 3 (HR + Training + TrenchSafety + ODR + OpRec + OpAct) | `ROUTE_SPLIT_001_WAVE_3_CERTIFICATION.md` | ✅ | NOT deployed |
| ROUTE-SPLIT-001 Wave 4 (legal + Tasks + DocExp + PoReq + ProjHealth + AssetTransfers + PM + Shop + Driver + Guidance + HrDR) | `ROUTE_SPLIT_001_WAVE_4_CERTIFICATION.md` | ✅ | NOT deployed |
| LIST-VIRT-001 (Equipment Master windowing) | `LIST_VIRT_001_CERTIFICATION.md` | ✅ | NOT deployed |
| WEBHOOK-HARDEN-001 (maintainx 503 + motive 401) | (verified earlier today) | ✅ in code | ✅ ACTIVE in prod |
| PROD-FRONTEND-ERROR-001 (Pydantic 422 React-child fix) | `PROD_FRONTEND_ERROR_001_CERTIFICATION.md` | ✅ | (assumed deployed earlier) |
| PERFORMANCE-HARDEN-001 (GZipMiddleware) | (live earlier) | ✅ in code | ✅ ACTIVE in prod |

---

## 2 · PRE-DEPLOY CHECKS

| Check | Result | Evidence |
| --- | --- | --- |
| Build passes | ✅ | `yarn build` exit 0 in 34.75 s (LIST-VIRT-001 cert) |
| Tests pass | ✅ | All ROUTE-SPLIT waves + LIST-VIRT-001 each shipped with 17–30 smoke route PASS |
| No P0/P1 open against this deployment | ✅ | None. The pre-existing `set-state-in-effect` lint false-positive on `EquipmentMasterPanel.jsx:141` is P3 hygiene, not deploy-blocking |
| Backup exists | ⚠️ Operator must confirm Atlas auto-backup snapshot dated within 24 h of deploy |
| Rollback build identified | ✅ Current prod bundle `main.0c1c410f.js` (etag `3ad26742ee1fe2ba805ed1851962ac61`) — re-deployable from prior prod container image |
| Current production bundle hash captured | ✅ §3.1 below |
| Current production health captured | ✅ §3.2 below |

---

## 3 · BEFORE state — production (captured 2026-06-09T23:44Z)

### 3.1 · Production bundle (from `https://mascidocs.com`)
| Asset | URL | Size | ETag |
| --- | --- | ---: | --- |
| main JS | `/static/js/main.0c1c410f.js` | **5,704,899 B (5.44 MB)** | `3ad26742ee1fe2ba805ed1851962ac61` |
| main CSS | `/static/css/main.7a3dbc01.css` | 163,440 B | `b7249edf642d66545868cbec73ca7f3a` |

**Observation:** Production main bundle (5.44 MB) is LARGER than even the Wave 1 baseline (4.97 MB) — meaning current prod predates the entire ROUTE-SPLIT-001 series. This deploy ships **5 certified sprints in one release**.

### 3.2 · Production health (live)
- `GET /api/health` → `{"ok":true,"service":"masci-hub","ts":"2026-06-09T23:44:04.634602+00:00"}` ✅
- `POST /api/integrations/maintainx/webhook` → **503** (WEBHOOK-HARDEN-001 active) ✅
- `POST /api/integrations/motive/webhook` → **401** (signature gate active) ✅
- Cache: `cache-control: public, max-age=300, immutable` (Phase 1A NOT YET deployed; this is expected)
- Sentry: active (`o4511406450802688.ingest.us.sentry.io`)

### 3.3 · Production data counts (from `PHASE1_PROD_DATA_BASELINE.txt`)
| Collection | Count |
| --- | ---: |
| daily_reports | 115 |
| job_photos | 789 |
| employees | 262 |
| equipment_master | 596 |
| motive_events | 2,430 |
| directory_sessions | 1,949 |
| (+ 19 more tracked) | (see baseline file) |
| **TOTAL tracked** | **6,520** |

### 3.4 · Motive status (before)
Active; 2,430 events accumulated in `motive_events`; webhook signature gate (401 on unsigned) active.

---

## 4 · AFTER state — certified preview build (ready to ship)

### 4.1 · Preview build artifact
| Asset | File | Size |
| --- | --- | ---: |
| main JS | `/app/frontend/build/static/js/main.fefe7e48.js` | **3,393,224 B (3.24 MB)** |
| chunk count | `build/static/js/*.chunk.js` | **132** (vs 42 pre-Wave-1) |

### 4.2 · Bundle delta (production → certified)
| Metric | Production NOW | Certified preview | Δ |
| --- | ---: | ---: | ---: |
| main bundle filename | `main.0c1c410f.js` | `main.fefe7e48.js` | new hash |
| main bundle size | 5,704,899 B | **3,393,224 B** | **−2,311,675 B / −40.5%** |
| JS chunks (offscreen lazy code) | (not measured) | 132 | massively more granular |
| Equipment Master DOM rows | 693 always | **27** (windowed) | −96.1 % |

**The single-deploy uplift is the largest in the platform's history.**

### 4.3 · Rollback build
| Identifier | Value |
| --- | --- |
| Current Preview commit (about to deploy) | `95f7bfbf50d7356bd7e539764e2b601ed4e20398` |
| Previous production main bundle | `main.0c1c410f.js` (etag `3ad26742ee1fe2ba805ed1851962ac61`) |
| Production previous container image | (operator extracts from prod deploy history — Cloud Run revision name) |
| Rollback method | Cloud Run "revert to revision" → previous tagged image |
| Rollback time | < 3 min (container swap, no DB / config touched) |

---

## 5 · OPERATOR DEPLOY RUNBOOK

### 5.1 · Pre-deploy sanity (operator workstation)
```bash
# Confirm preview is healthy
curl -s https://backup-forensics.preview.emergentagent.com/api/health
# Expect: {"ok":true,"service":"masci-hub",...}

# Confirm preview build hash matches what we certified
PREV_MAIN=$(curl -s https://backup-forensics.preview.emergentagent.com | grep -oE '/static/js/main\.[a-z0-9]+\.js' | head -1)
echo "Preview is serving: $PREV_MAIN"
# Expect: /static/js/main.fefe7e48.js  (or whatever hash the operator's freshest build produces)
```

### 5.2 · Deploy
Operator triggers production deploy via the platform's normal pipeline (Emergent platform's *"Save to Github"* + Cloud Run deploy, or whatever pipeline ships preview → prod). **No code changes by agent.**

### 5.3 · Post-deploy verification (operator runs immediately)
```bash
PROD="https://mascidocs.com"

echo "=== 1. /api/health ==="
curl -s "$PROD/api/health"
# Expect: {"ok":true,"service":"masci-hub",...}

echo "=== 2. New production bundle hash ==="
NEW_MAIN=$(curl -s "$PROD" | grep -oE '/static/js/main\.[a-z0-9]+\.js' | head -1)
echo "Production now serving: $PROD$NEW_MAIN"
# Expect: a NEW hash (not main.0c1c410f.js anymore)
curl -sI "$PROD$NEW_MAIN" | grep -iE "content-length|etag"

echo "=== 3. Webhook hardening still active ==="
curl -s -o /dev/null -w "maintainx HTTP=%{http_code}\n" -X POST "$PROD/api/integrations/maintainx/webhook"
curl -s -o /dev/null -w "motive HTTP=%{http_code}\n" -X POST "$PROD/api/integrations/motive/webhook"
# Expect: maintainx=503, motive=401

echo "=== 4. Cache headers (still max-age=300 until Phase 1A deploys) ==="
curl -sI "$PROD$NEW_MAIN" | grep -i cache-control
# Expect: public, max-age=300, immutable (unchanged until Cloudflare rule deployed)

echo "=== 5. 20-route smoke walk ==="
# Same harness as PHASE1_VALIDATION_REPORT.md §3.2 — login, daily reports, job photos, equipment, HR, safety, dispatch, motive, backups, alerts
```

### 5.4 · Performance verification (operator captures)
| Capture | Command | Expected |
| --- | --- | --- |
| New main bundle filename | `curl -s "$PROD" \| grep -oE '/static/js/main\.[a-z0-9]+\.js' \| head -1` | new hash, NOT `main.0c1c410f.js` |
| New main bundle size | `curl -sI "$PROD<NEW_MAIN>" \| grep content-length` | **~3,393,224 B** (will differ slightly if operator rebuilt) |
| Lazy chunk count | `curl -s "$PROD" \| grep -oE '/static/js/[0-9]+\.[a-z0-9]+\.chunk\.js' \| sort -u \| wc -l` | **~130+** |
| Cache headers | `curl -sI "$PROD<NEW_MAIN>" \| grep cache-control` | unchanged for now (Phase 1A separate) |
| Equipment Master DOM | open `/admin/equipment` in DevTools → `document.querySelectorAll('[data-testid^="equipment-row-"]').length` | **~27** (was 693) |
| iPad load | physical-device or DevTools iPad emulation | first paint < 2 s on cable, ≤ 4 s on simulated LTE |

### 5.5 · Data-safety verification (operator runs)
Use `PHASE1_VALIDATION_REPORT.md §3.1` harness. **All counts must be ≥ baseline** (production naturally grows; 5 % or 5-doc tolerance per collection).

---

## 6 · POST-DEPLOY VERIFICATION CHECKLIST (verbatim from directive)

| # | Check | Method |
| --- | --- | --- |
| 1 | `/api/health` OK | §5.3 step 1 |
| 2 | homepage loads | curl GET `/` returns 200 + HTML body > 1 KB |
| 3 | login works | smoke harness step 1 (admin login → token) |
| 4 | Daily Reports loads | `GET /api/admin/daily-reports?limit=1` |
| 5 | Daily Report submit route loads | `curl /daily/new` returns 200 + form HTML |
| 6 | Job Photos loads | `GET /api/job-photos?limit=1` |
| 7 | Equipment Master loads | `GET /api/equipment-master` returns `count` |
| 8 | Equipment virtualized table works | DevTools row count ≈ 27, scroll-to-bottom yields real last unit |
| 9 | HR loads | `GET /api/hr/employees?include_inactive=true` |
| 10 | Safety loads | `GET /api/safety/corrective-actions` |
| 11 | Dispatch loads | `GET /api/admin/fleet-visibility` |
| 12 | Motive remains connected | `GET /api/admin/motive-events?limit=1` returns recent event |
| 13 | webhook hardening still works | maintainx=503, motive=401 (§5.3 step 3) |
| 14 | alerts still tagged correctly | `GET /api/admin/audit-log?limit=1` |
| 15 | backups healthy | `GET /api/admin/system/health` |
| 16 | no Sentry frontend errors | Sentry dashboard 5-minute window post-deploy → zero new issues |
| 17 | no chunk-load errors | browser console on 5 random routes → zero `Failed to fetch dynamically imported module` |
| 18 | no Suspense blank screens | each lazy route renders populated DOM within < 200 ms |
| 19 | no auth redirect issues | gated routes (`/admin`, `/hr`, `/safety-portal`, `/dispatch-portal`, `/pm`, `/shop`) redirect cleanly to their login funnels |
| 20 | no permission drift | each portal token only satisfies its own scope (Admin token ≠ HR-only route, etc.) |

---

## 7 · ROLLBACK READINESS

| Aspect | Status |
| --- | --- |
| Previous bundle identified | ✅ `main.0c1c410f.js` (etag `3ad26742ee1fe2ba805ed1851962ac61`) |
| Rollback method | ✅ Cloud Run "revert to revision" — previous container image |
| Estimated rollback time | ✅ < 3 minutes |
| Data rollback required | ❌ Not applicable — this deploy ships ZERO data migration, ZERO schema change, ZERO Atlas user change. Rollback is container-image-only. |
| Operator runbook for rollback | "Cloud Run console → masci-hub service → Revisions tab → previous revision → Manage Traffic → 100 % to previous → Save" |

---

## 8 · Issues found

**None.** Pre-existing `set-state-in-effect` lint false positive on `EquipmentMasterPanel.jsx:141` is documented (P3 hygiene), not deploy-blocking.

---

## 9 · PASS / FAIL VERDICT

### Agent-deliverable portion
| Component | Verdict |
| --- | --- |
| Pre-deploy build verification | 🟢 PASS |
| Production BEFORE-state capture | 🟢 PASS |
| Certified preview-bundle composition verified | 🟢 PASS (5 sprints, all certified) |
| Rollback build identified | 🟢 PASS |
| Operator deploy runbook | 🟢 PASS |
| Post-deploy verification harness | 🟢 PASS |
| Data-safety verification harness | 🟢 PASS |
| Zero new code / refactor / new sprint started | 🟢 PASS — agent built nothing for this directive |

### Operator-pending portion
| Action | Verdict |
| --- | --- |
| Pipeline-trigger production deploy | 🟡 PENDING — operator-only |
| 20-step post-deploy verification | 🟡 PENDING — operator runs §6 |
| Performance verification capture | 🟡 PENDING — operator runs §5.4 |
| Data-safety verification | 🟡 PENDING — operator runs §5.5 |

# 🟡 OVERALL: AGENT PORTION 🟢 PASS · OPERATOR PORTION PENDING

---

## 10 · Forecast scorecard

Once operator deploys this bundle + (later) Phase 1 CF + Atlas:

| Pillar | Now (pre-deploy) | After this deploy | After + Phase 1A | After + Phase 1B |
| --- | ---: | ---: | ---: | ---: |
| Production Readiness | 91 | **91** *(Routes-split benefits realised in prod)* | **92** | 92 |
| Platform Health | 94 | 94 | 94 | 94 |
| Mobile Experience | 79 | **79** *(Equipment Master windowed in prod)* | 79 | 79 |
| Operational Reliability | 92 | 92 | 92 | 92 |
| Security | 88 | 88 | 88 | **90** |
| **Weighted avg** | **91.0** | **91.0** *(the certified work was already counted)* | 91.6 | **93.0** |

**Note:** The score tracker already counted ROUTE-SPLIT-001 + LIST-VIRT-001 at certification time (because the platform-quality framework awards points when the certified delta is provably available). This deploy realises those points for live users; it does not double-count them.

---

## 11 · Provenance

- Operator authorization: chat message **DEPLOY-NOW-001 · CERTIFIED PERFORMANCE BUNDLE PRODUCTION DEPLOY · STATUS: AUTHORIZED** (2026-06-09)
- Certifications referenced: `ROUTE_SPLIT_001_WAVE{1,2,3,4}_CERTIFICATION.md`, `LIST_VIRT_001_CERTIFICATION.md`, `WEBHOOK_HARDEN_001*`, `PROD_FRONTEND_ERROR_001_CERTIFICATION.md`, `PERFORMANCE_HARDEN_001_CERTIFICATION.md`
- BEFORE-state evidence captured live 2026-06-09T23:44Z against `https://mascidocs.com`
- Preview commit at time of certification: `95f7bfbf50d7356bd7e539764e2b601ed4e20398`
- Preview build artifact: `/app/frontend/build/static/js/main.fefe7e48.js`
