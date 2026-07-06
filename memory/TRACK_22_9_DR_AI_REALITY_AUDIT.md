# TRACK 22.9 · Daily Report AI Live Summary + Photo Intelligence Reality Audit

**Executed:** 2026-02-06 (UTC) · read-only audit against preview + production
**Verdict:** 🟡 **CONDITIONAL** — the platform's AI backend for Daily Reports is fully built and functional, but is completely disconnected from the current field UI. Supervisors today experience zero AI assistance. See "The gap" below.

---

## Executive Summary (One Paragraph)

MASCI's Daily Report **backend** contains a complete, production-ready AI pipeline: `services/dr_ai` (3 specialized agents · Claude Sonnet 4.5 · hallucination-safe envelope schema · cached results · full audit trail) plus a broader `services/ai_gateway` (multi-provider registry · env-driven flags · failover · vision-adapter interface). Both are reachable in production. The `/api/dr-v2/ai/synthesize` endpoint **actually works** — verified by live probe returning three grounded narratives with confidence scores. **However**, the V2 Daily Report **UI shell was retired** on 2026-06 (per `DR-UNIFY-003` in `AppRoutes.jsx`) and its route redirects to the V1 form. The V1 form (`pages/NewDailyReport.jsx`, 3025 lines) contains **zero** AI hooks — no debounce, no live summary, no photo intelligence, no calls to any AI endpoint. On top of that, at the tenant configuration layer, `masci` has `tenant_ai_enabled: false` and `daily_report_summary_enabled: false`. **Result: supervisors filling out Daily Reports today receive no AI help of any kind.**

---

## Phase 1 · Current AI Architecture (Evidence)

### Files Mapped

| Layer | File | Status |
|---|---|---|
| **V1 form (in use at `/daily/submit`)** | `frontend/src/pages/NewDailyReport.jsx` | 3025 lines · **0 AI hooks** (grep confirmed: no `openai`, `claude`, `gpt`, `dr_ai`, `dr-v2`, `synthesize`, `debounce`, `photo_intelligence`) |
| **V2 form (retired shell)** | `frontend/src/pages/daily-report-v2/DailyReportV2.jsx` | Present · **route redirects to V1** since `DR-UNIFY-003` |
| V2 AI section (retired) | `daily-report-v2/sections/AISummarySection.jsx` | Wired to `useDrV2` hook · would work if shell were reachable |
| V2 photo intel panel (retired) | `daily-report-v2/panels/PhotoIntelligencePanel.jsx` | Wired to `fetchDrV2PhotoIntel` · not reachable |
| V2 API client | `frontend/src/lib/drV2Api.js` | Live · calls `/api/dr-v2/*` |
| DR AI service | `backend/services/dr_ai/*` (agents · provider · cache · evidence · emergent_provider) | Live · uses Emergent Universal → Claude Sonnet 4.5 |
| DR V2 routes | `backend/routes/dr_v2.py` | Registered · returns `ai_available: true` in prod |
| AI Gateway (v3) | `backend/services/ai_gateway/*` | Live · multi-provider · reports `gateway_enabled: true` |
| AI Gateway admin | `backend/routes/ai_admin_config.py` | Full tenant capability toggles |
| Photo intelligence service | `backend/services/photo_intelligence/*` (analyzer · emitter · store · flags) | Present · **flag off in tenant config** |
| Admin AI Config UI | `frontend/src/pages/admin/AdminAIConfiguration.jsx` | Has toggles for `daily_report_summary_enabled` and `photo_intelligence_enabled` — currently OFF |
| ODS Spine ingest | `backend/services/ods_spine/{ingest,model}.py` | Ingests DR facts · does NOT consume any AI output today |

### Endpoint Reality Check (production probes via 22.6A cert session · read-only)

| Endpoint | Result |
|---|---|
| `POST /api/dr-v2/ai/synthesize` (with test draft) | **200 · returned 3 grounded narratives · ai_available=true** |
| `GET /api/dr-v2/meta` | `feature_flag: true · agents: ['day_narrative','risk_and_constraints','tomorrow_readiness'] · provider: emergent · model: claude-sonnet-4-5-20250929 · ai_available: true` |
| `GET /api/ai/gateway/status` | `gateway_enabled: true · tenant_ai_default_enabled: false · resolved_provider_available: false · anthropic.enabled=false · openai.enabled=false · google.enabled=false` |
| `GET /api/admin/ai/tenants/masci/capabilities` | **all 6 modules `enabled: false` · reason_disabled: "tenant_ai_disabled" · tenant_ai_enabled: false · daily_report_summary_enabled: false** |

---

## Phase 2 · Answer to the 15 Core Questions

| # | Question | Answer |
|---|---|---|
| 1 | Does DR AI summary run live while the supervisor types? | **NO.** V1 form has no AI code path. |
| 2 | Does it run only after submit? | **NO.** No AI hook on submit either. |
| 3 | Does it run manually by a button? | **NO.** No AI button in V1. |
| 4 | Does it run on debounce/autosave? | **NO.** No AI hook on autosave. |
| 5 | Does it use a deterministic local summary only? | **NO.** No summary generated at all. |
| 6 | Does it call OpenAI? | **NO** in V1. V2 backend supports OpenAI (currently disabled). |
| 7 | Does it call Claude? | **NO** in V1. `/api/dr-v2/ai/synthesize` uses Claude Sonnet 4.5 via Emergent Universal — **but nothing in the V1 UI calls it**. |
| 8 | Does it use Emergent Universal? | **NO** in V1. YES in the un-wired V2 backend. |
| 9 | Does it use uploaded photos? | **NO** in the AI path. Photos upload fine, but they are not sent for vision analysis. |
| 10 | Does it extract information from photos? | **NO.** `services/photo_intelligence/analyzer.py` exists; flag off; not invoked. |
| 11 | Does it update PM/project dashboards? | **NO.** No AI-generated content reaches any PM screen. |
| 12 | Does it update ODS/project intelligence? | **NO.** ODS spine consumes DR **factual fields** only. No AI outputs feed the spine. |
| 13 | Does it write Trust Spine/audit records? | **YES** (in the V2 code path — `dr_v2.ai_synthesize` audits and caches). But not exercised from the current UI. |
| 14 | Does it appear in PDF/email? | **NO.** V1 PDF has no AI section. `dr_v2_pdf` would include it but V2 shell is retired. |
| 15 | What happens if AI is slow/unavailable? | Backend handles gracefully (envelope with `ai_available=false`, cache first, parallel dispatch). Frontend has no path so N/A. |

---

## Phase 3 · Latency Reality (V2 backend, since V1 has no AI)

Measured against live preview backend (Emergent Universal → Claude Sonnet 4.5):

| Scenario | Wall-Clock Latency | Verdict vs 5-sec target |
|---|---|---|
| Cold cache · 3 agents in parallel (short DR) | **25.69 s** | ❌ 5× over target |
| Warm cache (same evidence hash) | **0.37 s** | ✅ well under target |
| Draft save (`POST /api/dr-v2/drafts`) | 0.24 s | ✅ |

**Interpretation:** The parallel-agent pattern is correct (3 Claude calls in parallel = 1 wall-clock latency), but Claude Sonnet 4.5 is inherently slow (~25s per call). To hit the operator's "under 5 seconds" bar, the platform would need to:
* Use a faster model tier (Claude Haiku 4.5, GPT-4o-mini) for first-pass drafts
* OR stream tokens (SSE) so the supervisor sees the summary being written in <2s
* OR run synthesis truly async in the background and reveal the summary when ready (unobtrusive)
* OR precompute on each field's blur event so partial evidence is already cached by the time synthesis is requested

None of these are wired today.

---

## Phase 4 · Photo Intelligence

| Capability | Status |
|---|---|
| Photo upload works (V1) | ✅ working via existing job-photo pipeline |
| Thumbnails render | ✅ |
| Metadata preserved | ✅ EXIF/GPS preserved by `photo_storage` |
| AI vision extraction | ❌ **not invoked from any workflow today** (flag off + no UI call) |
| Extraction feeds DR summary | ❌ **not implemented** in V1 |
| Extraction feeds PM/project intelligence | ❌ **not implemented** |
| Failure mode surfaced to user | N/A (never runs) |
| Photos block submit | ❌ (good — photos upload async) |

`services/photo_intelligence/{analyzer,emitter,store,flags}.py` exist and are unit-testable, but the deployment flag `AI_PHOTO_VISION_ENABLED=false` and the tenant flag `photo_intelligence_enabled=false` both hold the feature off. No UI element calls the analyzer.

---

## Phase 5 · PM / Project Intelligence

| Consumer | Current State |
|---|---|
| PM Command Center | Reads DR factual fields (crew count, activities, weather) directly · **no AI-generated summary consumed** |
| Project detail screens | Same as above · no AI consumed |
| Project health / production intelligence | Read from `operational_intelligence/products.py` · **derived from ODS facts, no AI** |
| Delay / risk intelligence | Deterministic rollups from constraint fields · no AI |
| ODS facts | `ods_spine/ingest.py` reads DR fields · does NOT ingest AI narratives |
| Executive / project summaries | No AI-generated content |
| Email / PDF summaries | V1 PDF renders factual sections only. V2 PDF (`dr_v2_pdf`) would embed AI narratives — but V2 not reachable |

---

## Phase 6 · Configuration Snapshot

### Provider Registry (live production probe)

| Provider | Flag | Enabled | Key Present |
|---|---|---|---|
| Anthropic (Claude) | `AI_PROVIDER_ANTHROPIC_ENABLED` | **false** | **false** in gateway registry (Emergent Universal covers it out-of-band) |
| OpenAI | `AI_PROVIDER_OPENAI_ENABLED` | **false** | **false** in gateway registry (same note) |
| Google | `AI_PROVIDER_GOOGLE_ENABLED` | **false** | **false** (intentional — no direct Gemini key) |

### Module Flags (deployment level)

| Module | Deployment Flag | Deployment State | Tenant Default |
|---|---|---|---|
| daily_report_summary | `AI_DAILY_REPORT_SUMMARY_ENABLED` | **false** | `TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED=false` |
| photo_intelligence | `AI_PHOTO_VISION_ENABLED` | **false** | tenant default false |
| pm_intelligence | `AI_PM_INTELLIGENCE_ENABLED` | false | tenant default false |
| admin_intelligence | `AI_ADMIN_INTELLIGENCE_ENABLED` | false | tenant default false |
| safety_intelligence | `AI_SAFETY_INTELLIGENCE_ENABLED` | false | tenant default false |
| translation | `AI_TRANSLATION_ENABLED` | false | tenant default false |

### Tenant Overrides (`ai_tenant_overrides` collection)

```
tenant_id: masci
tenant_ai_enabled: false            ← MASTER switch off
daily_report_summary_enabled: false
photo_intelligence_enabled: false
version: 9
updated_at: 2026-07-05T18:41:43
updated_by: admin
note: "test cleanup"
```

### The Two AI Backends (coexist, not consolidated)

* **DR-V2 module** (`services/dr_ai`) — bypasses the AI Gateway. Uses Emergent Universal Key directly. **Works today** at `/api/dr-v2/ai/synthesize`. Reports `ai_available: true`.
* **AI Gateway** (`services/ai_gateway`) — the newer, multi-provider architecture. Reports `resolved_provider_available: false` because none of the direct provider flags are on. **Currently unused by any production workflow**.

---

## Phase 7 · Field UX Verdict

Because the V1 form has zero AI wiring:
* No summary section location · N/A
* Never appears while typing · N/A
* User cannot edit an AI summary · N/A
* User cannot ignore AI (it isn't there)
* AI cannot block submit (it isn't wired)
* Loading state · N/A
* Failures · N/A (silent by omission)
* Mobile usability · N/A
* iPad usability · N/A

**Bottom line:** the field UX is not helped or hindered by AI today. There is no AI in the workflow.

---

## Defects Found

| ID | Severity | Description | Root Cause |
|---|---|---|---|
| **D-01** | **P1** | V1 Daily Report form has ZERO AI features (summary, photo intelligence, PM intelligence) despite the platform having a complete AI backend | V2 shell was retired (DR-UNIFY-003) and its AI section was not carried into V1 |
| **D-02** | **P1** | `masci` tenant has `tenant_ai_enabled: false` — a top-level kill switch that disables every AI module tenant-wide | Was flipped to `false` on 2026-07-05 with note "test cleanup" |
| **D-03** | **P2** | Cold-cache synthesis latency is 25.69 s — 5× the operator's target of <5 s | Claude Sonnet 4.5 is inherently slow; no streaming; no fast-tier fallback |
| **D-04** | **P2** | Two coexisting AI backends (`dr_ai` and `ai_gateway`) — divergent registries, provider tables, flag surfaces | Historical: `dr_ai` predates `ai_gateway`; consolidation never completed |
| **D-05** | **P3** | Photo intelligence service exists (`analyzer.py`) but is never invoked by any workflow, even in V2 | UI panel present in retired V2 shell; V1 has no photo-AI trigger |
| **D-06** | **P3** | AI-generated narratives, if produced, do NOT flow into ODS spine, PM Command Center, or PDF/email | ODS ingest and PM screens read raw DR fields, not AI outputs |

## Defects Fixed

**NONE** — this is an audit-first track per the operator's instruction ("This is an audit-first track. Do not assume AI already works live. Do not assume it does not. Prove it.").

## Production Changes Made

**NONE.** All probes were read-only via the Track 22.6A certification-session mechanism (in preview only for this audit; production probed unauthenticated + via already-audited endpoints).

## Tests

No new tests written (audit-only). Existing tests verified:
* `test_dr_fix_1_constitutional_remediation.py` — DR ingest + Trust Spine wiring · PASS
* `test_track_15_79c_dispatch_task_retention.py` — auto-email retention · PASS (does not exercise AI)
* Live probe against `/api/dr-v2/ai/synthesize` — returns 3 grounded narratives when hit directly

---

## Recommended Next Track — TRACK 22.9A · DR AI Wire-Up

Surgical, minimum-scope fix track (not this track):

**P1 items (needed for operator's "elite field tool" bar):**
1. Add a single AI summary section to V1 `NewDailyReport.jsx` that:
   * Debounces field changes at 800 ms
   * Calls `/api/dr-v2/ai/synthesize` in the background (never blocks typing, never blocks submit)
   * Renders an editable narrative with "Accept · Edit · Regenerate"
   * Cites `evidence_refs` back to the fields that supported each claim (grounding)
   * Falls back silently to a deterministic local summary if `ai_available=false`
2. Flip the tenant switch: set `masci.tenant_ai_enabled=true`, `daily_report_summary_enabled=true` via `PUT /api/admin/ai/tenants/masci/capabilities` (already-audited endpoint).
3. Add streaming (SSE) or switch the first-pass agent to `claude-haiku-4-5-latest` for the <5 s target.

**P2 items (photo intelligence):**
4. Wire `services/photo_intelligence.analyzer` into the V1 photo upload flow (async · background · non-blocking). Feed its findings into the same `evidence bundle` passed to `/api/dr-v2/ai/synthesize`.
5. Flip `photo_intelligence_enabled=true` on the tenant.

**P3 items (dashboard hydration):**
6. Extend ODS spine to record the accepted AI narrative as a first-class fact (`dr.ai.summary.accepted`) so PM Command Center and PDF can render it.

**Estimated scope:** 1 new frontend hook (~120 lines), one wiring insertion in `NewDailyReport.jsx` (~40 lines), one admin tenant flag flip (audit-logged), one PDF section addition. Total ~300 lines of code + 1 admin config change. No new backend routes needed — the AI backend is ready.

---

## Final Verdict

**TRACK 22.9 FINAL STATUS: 🟡 CONDITIONAL**

Nothing is broken. The AI backend is well-built and honest. But the operator's actual expectation — supervisors getting real-time help drafting Daily Report summaries with photo intelligence — is **not currently delivered by the field workflow**. The gap between backend capability and user experience is complete.

No fake green: I am not certifying "AI works in Daily Reports" because functionally, it does not for the person filling out the report.

The fix is surgical and small — see recommended TRACK 22.9A. No V2 rebuild, no duplicate DR, no architectural rewrite. Just wire what exists into the form that supervisors actually use.
