# PLATFORM-EXCELLENCE-005 · Execution Material Only

```
Environment    : both
Access Level   : preview-runtime · prod-DB-read · external-probe
Evidence Source: live measurement + carry-forward
Confidence     : VERIFIED for all measurements · ACTIONABLE for all execution items
```

---

## PHASE 1 · Operator-Blocked Closure Instructions

### 1A · Cloudflare Cache Rule

**Click path:** Cloudflare Dashboard → select `mascidocs.com` zone → Caching → Cache Rules → Create rule.

**Exact values:**
- Rule name: `MASCI static assets — 1y immutable`
- If incoming requests match: **URI Path → starts with → `/static/`**
- Then:
  - Cache eligibility: **Eligible for cache**
  - Edge TTL: **Override origin → 1 year (31,536,000 s)**
  - Browser TTL: **Override origin → 1 year (31,536,000 s)**

**Expected result:** `/static/js/main.*.js` and `/static/css/main.*.css` return `cache-control: public, max-age=31536000, immutable` + `cf-cache-status: HIT` on repeat fetches.

**Verification:** `curl -skI https://mascidocs.com/static/js/main.0c1c410f.js | grep -i cache-control` must show `max-age=31536000`.

### 1B · Atlas User Split

**Click path:** MongoDB Atlas → Project `MASCI-prod` → Security → Database Access → ADD NEW DATABASE USER (twice).

**Exact values — User 1:**
- Authentication: SCRAM password
- Username: `masci_preview_user`
- Password: (generate, save in vault)
- Built-in Role: ❌ none — use Specific Privileges:
  - Role: `readWrite` · Database: `masci_safety_preview` · Collection: (blank = all)
- Restrict to specific clusters: ✅ MASCI-prod only

**Exact values — User 2:**
- Username: `masci_prod_user`
- Password: (generate **different** from above, save in vault)
- Specific Privileges: Role `readWrite` · Database `masci_safety` · Collection blank
- Restrict to specific clusters: ✅ MASCI-prod only

**Then in Emergent secrets panels:**
- Production pod → set `MONGO_URL = mongodb+srv://masci_prod_user:<pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-prod` → redeploy.
- Preview pod → set `MONGO_URL = mongodb+srv://masci_preview_user:<pwd>@masci-prod.1nduwmg.mongodb.net/?retryWrites=true&w=majority&appName=MASCI-preview` → restart backend.

**Then in Atlas → Security → Database Access:**
- Edit `admin_db_user` → toggle **Disable user** (do NOT delete).
- Edit `Password` → toggle **Disable user** (do NOT delete).

**Expected result:** preview pod can no longer reach `masci_safety`; production pod cannot reach `masci_safety_preview`.

**Verification:** From preview pod shell:
```python
mc = AsyncIOMotorClient(os.environ["MONGO_URL"])
await mc["masci_safety"].daily_reports.estimated_document_count()
# Must raise OperationFailure: not authorized on masci_safety
```

### 1C · Real-Device Certification

**Click path:** BrowserStack Live → Devices: iPhone 13 (Safari iOS 17), iPad Air (Safari iPadOS 17), Pixel 7 (Chrome Android 14), Surface Pro (Edge), MacBook Pro (Safari macOS 14).

**Exact values per device:** run the 9 workflows (login, navigation, daily report create, photo upload, HR edit, equipment assign, safety inspection, dispatch board, governance acknowledge, logout) and mark each PASS/FAIL.

**Performance acceptance (run via WebPageTest from `webpagetest.org` on iPhone 13 LTE preset):**
- LCP ≤ 2.5 s
- INP ≤ 200 ms
- CLS ≤ 0.1

**Expected result:** All workflows PASS · LCP/INP/CLS thresholds met or explicit defect captured.

**Verification:** Paste WebPageTest run URL into `/app/memory/REAL_DEVICE_LCP_001_RESULTS.md` (operator creates).

---

## PHASE 2 · ROUTE-SPLIT-001 Execution Plan

**Measured BEFORE:** App.js 871 lines · 242 eager `import` · 294 routes · main bundle 5.5 MB raw / 1.4 MB gz.

**Forensic — shared dependencies (will stay in main):** React, React-DOM, react-router-dom, Tailwind runtime, Shadcn UI primitives, lucide-react, sonner, Sentry (already split).

### Wave 1 — Admin Portal (largest gain · safest first split)
- Targets: every `import` from `@/pages/admin/*` (~60 pages) → wrap in `React.lazy()` keyed off route.
- Add single `<Suspense fallback={<BrandSpinner />}>` around `<Routes>` in `App.js`.
- Expected raw-bundle reduction: ~30% (admin pages only render when an admin authenticates).
- Rollback: revert `App.js` to pre-wave commit; redeploy.
- Test gate: every `/admin/*` route loads + smoke screenshot.

### Wave 2 — Safety + QA/QC
- Targets: `@/pages/Safety*`, `@/pages/Qaqc*`, `@/pages/Field*`, ~40 pages.
- Expected raw reduction: ~10%.
- Rollback / Test gate: as above.

### Wave 3 — Photos + ODR + Daily-Reports + Driver + Dispatch
- Targets: `@/pages/JobPhotosLibrary`, `@/pages/odr/*`, `@/pages/driver/*`, `@/pages/dispatch/*`, ~55 pages.
- Expected raw reduction: ~10%.

### Wave 4 — Remaining (HR, Equipment, Trench Safety, Hub variants, Public, Meetings)
- ~85 pages.
- Expected raw reduction: ~5%.

### Acceptance per wave
- `yarn build` succeeds · per-portal chunk visible in `build/static/js/`.
- `testing_agent_v3_fork` walks at least 3 representative routes per wave with PASS.
- No console error on first navigation to each split route.
- Smoke screenshot at preview URL passes.

---

## PHASE 3 · LIST-VIRT-001 Execution Plan

| Target | Current row count (prod) | Render cost today | Virtualize? | Expected gain |
|---|---|---|---|---|
| **JobPhotosLibrary** | 789 photos · growing | Renders all in one grid | **YES** | Initial render 800 ms → ~80 ms; smooth 60 fps scroll on iPhone |
| AdminEmployeesList | 262 employees | Already paginated client-side per filter | NO | <50 ms gain · risk to filter |
| MotiveEventsTable | 1,800 · server-paginated | <100 ms render | NO | server pagination already efficient |
| IntegrationSyncLogsTable | 41,263 · server-paginated | <100 ms | NO | same |
| Notifications drawer | 142 · capped at 50 visible | <50 ms | NO | not warranted |

**Order:** JobPhotosLibrary only. Add `react-window` + `react-virtualized-auto-sizer`. Keep existing `loading="lazy" decoding="async"`. Verify thumb-token pagination integrates with virtualized cell renderer.

---

## PHASE 4 · Security Gap Closure Paths

| ID | Closure path | Owner | Action class |
|---|---|---|---|
| PE002-D05 (cluster-admin shared Atlas user) | Execute Phase 1B above end-to-end | Operator | INFRASTRUCTURE |
| PE003-D01 (3rd fork-side prod-DB write debt) | Closes automatically when PE002-D05 closes (no separate action) | Operator | INFRASTRUCTURE |
| Shared `test_credentials.md` accounts (5 PROD-CAPABLE) | Rotate prod-side passwords via `/admin/users/<id>/reset-password` UI · annotate `test_credentials.md` to mark preview-only | Operator | OPERATOR ACTION |
| Likely-shared `JWT_SECRET` / `ADMIN_HMAC_SECRET` / `MFA_ENCRYPTION_KEY` between envs | Rotate in production-pod Emergent secrets panel (operator); preview already rotated in GR-001 | Operator | OPERATOR ACTION |
| Optional: rotate `RESEND_API_KEY`, `RESEND_WEBHOOK_SECRET` independently per env | Two new env-specific Resend API keys + per-pod replacement | Operator | OPERATOR ACTION |

---

## PHASE 5 · 95+ Roadmap (only sub-95 pillars)

### Mobile Experience  78 → ≥95

| Blocker | Action | Owner | Effort | Risk | Score impact |
|---|---|---|---|---|---|
| No real-device LCP/INP/CLS data | Execute Phase 1C above on BrowserStack + WebPageTest | Operator | 1-2 h | LOW | +12 (verified PASS) |
| `JobPhotosLibrary` non-virtualized | Phase 3 execution | Engineering | 1 sprint (1-2 sessions) | LOW with proper test | +3 |
| Heavy main bundle on mobile cold load | Phase 2 Wave 1 + Wave 2 (admin + safety) | Engineering | 2 sprints | LOW per-wave | +2 |
| **Total path to ≥95** | | | | | **+17 → 95** |

### Operational Reliability  94 → ≥95

| Blocker | Action | Owner | Effort | Risk | Score impact |
|---|---|---|---|---|---|
| Stale ODR test fixture | Update `tests/odr/test_m1_option_c.py:133` seed or assertion | Engineering | 1 session | LOW | +1 |
| 21 orphan ephemeral test DBs | Drop via Atlas Console | Operator | 5 min | NIL | +0 (hygiene only) |
| `_headers` propagation (Phase 1A) | Operator Cloudflare rule | Operator | 10 min | NIL | +1 (TTL stability) |
| **Total path to ≥95** | | | | | **+2 → 96** |

### Security  88 → ≥95

| Blocker | Action | Owner | Effort | Risk | Score impact |
|---|---|---|---|---|---|
| Cluster-admin shared Atlas user (PE002-D05) | Phase 1B | Operator | 30 min | LOW (rollback-able) | +5 |
| Shared `test_credentials.md` prod-capable accounts | Phase 4 row 3 | Operator | 15 min | LOW | +2 |
| Cross-env shared JWT / HMAC / MFA secrets | Phase 4 row 4 (re-login required) | Operator | 10 min + ops window for re-enroll | MEDIUM (sessions invalidate) | +1 |
| **Total path to ≥95** | | | | | **+8 → 96** |

---

## PHASE 6 · Execution Authorization Matrix

| Item | Category |
|---|---|
| Phase 1A Cloudflare cache rule | OPERATOR REQUIRED |
| Phase 1B Atlas user split + MONGO_URL flip | OPERATOR + INFRASTRUCTURE REQUIRED |
| Phase 1C Real-device certification | OPERATOR REQUIRED (BrowserStack / WebPageTest) |
| Phase 2 Wave 1 (admin portal route-split) | SAFE TO EXECUTE NOW (dedicated session) |
| Phase 2 Wave 2 (safety + QA/QC route-split) | SAFE TO EXECUTE NOW (dedicated session) |
| Phase 2 Wave 3 (photos + odr + driver + dispatch route-split) | SAFE TO EXECUTE NOW (dedicated session) |
| Phase 2 Wave 4 (remaining route-split) | SAFE TO EXECUTE NOW (dedicated session) |
| Phase 3 JobPhotosLibrary virtualization | SAFE TO EXECUTE NOW (dedicated session) |
| Phase 4 row 3 (rotate 5 shared prod passwords) | OPERATOR REQUIRED |
| Phase 4 row 4 (rotate 3 cross-env secrets in prod) | OPERATOR REQUIRED |
| Stale ODR fixture fix | SAFE TO EXECUTE NOW (small backend test sprint) |
| Drop 21 orphan ephemeral DBs | OPERATOR REQUIRED (Atlas Console) |
| FleetWatcher | DO NOT TOUCH |
| Dispatch Automation | DO NOT TOUCH |
| Material Movement | DO NOT TOUCH |
| MaintainX expansion | DO NOT TOUCH |
| New portals / dashboards / workflows / integrations | DO NOT TOUCH |
| `react-hooks/exhaustive-deps` warnings cleanup | DEFER |
| `server.py` F541/F841/F811 ruff cleanup | DEFER |
| `_demo_tor_*.png` removal | DEFER (verify references first) |
| Real-device LCP run | OPERATOR REQUIRED |

---

## Single deliverable
`/app/memory/PLATFORM_EXCELLENCE_005_EXECUTION_MATERIAL.md` (this file) · PRD.md updated.
