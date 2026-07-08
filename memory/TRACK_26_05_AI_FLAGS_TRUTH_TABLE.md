# TRACK 26.05 — AI SECRETS / FEATURE FLAG TRUTH TABLE

**Date:** 2026-07-08 UTC · **Scope:** ZERO CODE · **Standard:** read-only audit · no flag flips · no secret values printed
**Preview backend:** `/app/backend/.env` (previewed via `python3` parse — key names + boolean values only; API-key values redacted)

---

## 0 · EXECUTIVE VERDICT

**Safe to deploy AS-IS?** ⚠ **CONDITIONAL YES** — safe for the Track 24 → 26 Daily Report recovery package **only**. Photo Intelligence, PM Intelligence, Safety Intelligence, Admin Intelligence, and the V1 `daily_report_summary` deterministic path are **all disabled at the strict AI Gateway resolver** because every `AI_PROVIDER_*_ENABLED` flag is `false` and `TENANT_AI_ENABLED=false`. The V3 Daily Report AI path is unaffected — it bypasses the strict resolver and only checks `EMERGENT_LLM_KEY` + `DR_V2_AI_ENABLED`, both of which are set.

**Two independent AI paths exist in this codebase (architectural drift):**

| Path | Gate mechanism | Modules controlled | Current preview state |
|---|---|---|---|
| **A · Strict Gateway** (`services/ai_gateway/capabilities.py::resolve_ai_capabilities`) | `AI_GATEWAY_ENABLED` + `TENANT_AI_ENABLED` + `AI_<MODULE>_ENABLED` + `TENANT_AI_<MODULE>_ENABLED` + provider flag + provider key | `photo_intelligence`, `pm_intelligence`, `admin_intelligence`, `safety_intelligence`, `translation`, V1 `daily_report_summary` | 🔴 **ALL DISABLED** (tenant + all providers off) |
| **B · Emergent-Key direct** (`services/dr_ai/factory.py`, `dr_ai/emergent_provider.py`, `translation/service.py`, `hub_banners.py`, `operations_control/ai.py`) | Only `EMERGENT_LLM_KEY` presence + `DR_V2_AI_ENABLED` | V3 DR AI synthesize · translation service · hub banners · OCC AI health | ✅ **LIVE** |

**Deploy risk if unchanged:** The V3 Daily Report AI will work in production identical to preview. Photo Intelligence will remain silently off (photos still upload, just no AI observations attached). PM/Safety/Admin Intelligence dashboards will show fallback text or empty AI blocks — no crash. This is the current design of "Invisible Intelligence" (see doctrine in `capabilities.py:15-33`).

---

## 1 · TRUTH TABLE (all AI-related env vars observed in code)

### 1.1 Global gateway flags

| Name | Preview value | Recommended production | Kind | Read at | Feature controlled | Runtime effect NOW | Should prod be true? | Risk if wrong | Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| `AI_GATEWAY_ENABLED` | `true` | `true` | boolean flag | `services/ai_gateway/env.py:36` · `services/ai_gateway/capabilities.py:149` | Master gate for the strict resolver. If false, all modules routed through resolver hard-disable | Gateway armed — but downstream provider check still fails (see §1.3) | ✅ true | If false: every capability-routed module returns `ai_gateway_disabled_global` | Keep `true` |
| `AI_DEFAULT_PROVIDER` | `anthropic` | `anthropic` | string | `services/ai_gateway/env.py:40` · `services/dr_ai/emergent_provider.py:25` · `capabilities.py:114` | Which provider to prefer when multiple keys available | `anthropic` selected first | `anthropic` | Wrong provider chosen → wrong model + wrong pricing | Keep `anthropic` |
| `AI_DEFAULT_TEXT_MODEL` | `claude-sonnet-4-5-20250929` | `claude-sonnet-4-5-20250929` | string | `env.py:44` · `emergent_provider.py:24` | Text model for DR AI synthesize and any text agent | Verified live: `GET /api/dr-v2/meta` returns this model | Match preview (identical) | Model mismatch → prompt/token surprises | Keep as-is unless promoting to a newer Sonnet |
| `AI_DEFAULT_VISION_PROVIDER` | `openai` | `openai` | string | `env.py:48` | Preferred provider for vision (Photo Intelligence) | `openai` selected — but `AI_PROVIDER_OPENAI_ENABLED=false` and `OPENAI_API_KEY` empty → **vision unavailable** | `openai` (if PI is planned) or leave as-is | Vision provider mismatch → Photo Intel disabled | See PI verdict §7 |
| `AI_DEFAULT_VISION_MODEL` | `gpt-5.2-vision` | `gpt-5.2-vision` | string | `env.py:52` | Vision model selection | Not currently reachable (provider disabled) | Match preview | Model mismatch → vision fails | Keep as-is |
| `AI_PROVIDER_FAILOVER_ENABLED` | `true` | `true` | boolean flag | `env.py:70` | Allow provider failover on primary error | Fallback candidate is picked when 2+ providers keyed | ✅ true | If false: single-provider outage = hard fail | Keep `true` |
| `AI_PROVIDER_TIMEOUT_MS` | `45000` | `45000` (or tune per PM feedback) | int (ms) | `env.py:57` | HTTP timeout to provider | 45 s per call | 45 s reasonable | Too low → truncated summaries; too high → UI hangs | Keep |
| `AI_PROVIDER_MAX_RETRIES` | `2` | `2` | int | `env.py:64` | Retry budget per provider call | 2 retries | 2 | Too many retries → cost | Keep |

### 1.2 Global module enable flags (strict-resolver step 3)

| Name | Preview | Recommended production | Kind | Read at | Feature controlled | Runtime effect NOW | Should prod be true? | Risk if wrong | Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| `AI_DAILY_REPORT_SUMMARY_ENABLED` | `false` | ⚠ **FALSE — V3 bypasses this flag anyway** | boolean flag | `capabilities.py:56` · consumed by `resolve_ai_capabilities(module="daily_report_summary")` | V1 legacy deterministic summary path (`daily_summary.py:323`). V3 DR AI does **NOT** consult this flag — V3 uses `dr_v2.py:122` `DR_V2_AI_ENABLED` instead | V1 legacy path returns `enabled=false` (also blocked upstream by `TENANT_AI_ENABLED=false`) | `false` in prod for V1 path (V1 shell is retired for tenant default V3) | If accidentally `true` → V1 legacy composer runs and adds a deterministic block. Not harmful, but confusing since V3 already handles this. | Keep `false` |
| `AI_PHOTO_VISION_ENABLED` | `true` | `false` (currently untested) OR `true` if photo intel is a launch requirement | boolean flag | `capabilities.py:57` · `services/photo_intelligence/pipeline.py:293` | Photo Intelligence vision pipeline (OCR + observation extraction on uploaded DR photos) | Set to `true` at env level, but strict resolver still returns `enabled=false` because `TENANT_AI_ENABLED=false` AND `_resolve_provider()` returns `available=False` (no provider has both flag=true AND key set). Net effect: **photo intel silently disabled** | Decide per business need. If Photo Intel is not part of Track 24→26 launch → keep `false`. | If flipped `true` in prod without also enabling a provider + key → still no effect but false hope in admin dashboards | **Set explicitly to `false` for launch** and revisit as a separate track |
| `AI_TRANSLATION_ENABLED` | `false` | `false` (V3 client-side ES→EN translator uses a different code path) | boolean flag | `capabilities.py:61` | Server-side translation module (via strict resolver) | `enabled=false` at every gate | `false` | The V3 ES→EN pre-submit translator (`services/translation/service.py:252`) uses `EMERGENT_LLM_KEY` directly and is NOT routed through this flag. Confusion risk only. | Keep `false` |
| `AI_PM_INTELLIGENCE_ENABLED` | `false` | `false` (not shipping this release) | boolean flag | `capabilities.py:58` | PM Command Center AI briefings | `enabled=false` | `false` | Enabling without a shipped UI → wasted provider spend | Keep `false` |
| `AI_SAFETY_INTELLIGENCE_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:60` | Safety portal AI intelligence | `enabled=false` | `false` | Same as above | Keep `false` |
| `AI_ADMIN_INTELLIGENCE_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:59` | Admin console AI intelligence | `enabled=false` | `false` | Same as above | Keep `false` |

### 1.3 Provider enable flags + keys (strict-resolver step 5)

| Name | Preview | Recommended production | Kind | Read at | Runtime effect NOW | Recommendation |
|---|---|---|---|---|---|---|
| `AI_PROVIDER_ANTHROPIC_ENABLED` | `false` | `false` (Emergent Universal Key handles Anthropic; direct key not required) | boolean flag | `env.py:76` · `capabilities.py:65` | Strict resolver considers Anthropic unavailable | Keep `false` — direct Anthropic key not needed when Universal Key is used |
| `ANTHROPIC_API_KEY` | empty | empty | secret | multiple | Strict resolver skips Anthropic | Keep empty (Universal Key routes Anthropic) |
| `AI_PROVIDER_OPENAI_ENABLED` | `false` | `false` unless direct OpenAI key set | boolean flag | `env.py:78` | Strict resolver considers OpenAI unavailable → Photo Intel vision unreachable via gateway | Keep `false` for launch |
| `OPENAI_API_KEY` | empty | empty | secret | multiple | Strict resolver skips OpenAI | Keep empty |
| `AI_PROVIDER_GOOGLE_ENABLED` | `false` | `false` | boolean flag | `env.py:80` | Strict resolver considers Google unavailable | Keep `false` |
| `GOOGLE_AI_API_KEY` | empty | empty | secret | multiple | Skipped | Keep empty |

### 1.4 Tenant default flags (strict-resolver step 2 + 4)

| Name | Preview | Recommended production | Kind | Read at | Runtime effect | Recommendation |
|---|---|---|---|---|---|---|
| `TENANT_AI_ENABLED` | `false` | `false` (kept off intentionally per doctrine) | boolean flag | `capabilities.py:157` · `routes/ai_admin_config.py:186` | Gate 2 fails for every capability-routed module. **This is the primary "OFF switch" for the entire strict resolver.** | Keep `false` — enable per-tenant via `ai_tenant_capabilities` Mongo doc instead |
| `TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:56` | Never reached (blocked at step 2) | Keep `false` |
| `TENANT_AI_PHOTO_INTELLIGENCE_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:57` | Never reached | Keep `false` |
| `TENANT_AI_TRANSLATION_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:61` | Never reached | Keep `false` |
| `TENANT_AI_PM_INTELLIGENCE_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:58` | Never reached | Keep `false` |
| `TENANT_AI_SAFETY_INTELLIGENCE_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:60` | Never reached | Keep `false` |
| `TENANT_AI_ADMIN_INTELLIGENCE_ENABLED` | `false` | `false` | boolean flag | `capabilities.py:59` | Never reached | Keep `false` |

### 1.5 Legacy / bypass paths (do NOT route through strict resolver)

| Name | Preview | Recommended production | Kind | Read at | Feature controlled | Runtime effect | Recommendation |
|---|---|---|---|---|---|---|---|
| `EMERGENT_LLM_KEY` | **configured** (value redacted) | **configured** (same key, production-safe) | secret | `services/dr_ai/emergent_provider.py:29` · `services/dr_ai/factory.py:37` · `services/translation/service.py:252` · `routes/hub_banners.py:159` · `services/operations_control/ai.py:16` · `server.py:10322` · `routes/integration_health.py:213` · `routes/platform_data_truth.py:149-151` · plus 6 icon/logo `scripts/*.py` (dev-only, not runtime) | Powers **V3 DR AI synthesize**, translation service, hub banners, OCC AI health card, integration health card, platform truth panel | ✅ Live — `GET /api/dr-v2/meta` returns `ai_available=true` | **PRODUCTION MUST HAVE THIS SET** — same Universal Key value or a production-scoped equivalent. Verify budget top-up before deploy. |
| `DR_V2_AI_ENABLED` | `true` | `true` | boolean flag | `routes/dr_v2.py:122` · `services/operations_control/ai.py:17` · `services/operations_control/ai.py:31` | V3 Daily Report AI synthesize endpoint (`POST /api/dr-v2/ai/synthesize`). **Independent of the strict gateway.** | ✅ V3 AI live | Keep `true` |
| `DR_V2_PHOTO_VISION_ENABLED` | `true` | `false` for launch (photo vision not part of Track 26 recovery scope) | boolean flag | `services/photo_intelligence/flags.py:7` · `routes/dr_v2_photos.py:92` | Legacy DR-V2 photo vision path. Coexists with the strict-resolver photo intel path in §1.2. | Currently `true` but effectively idle (strict resolver still blocks the reconciler on `TENANT_AI_ENABLED=false`) | Recommend `false` in prod for launch cleanliness; revisit as separate track |
| `DR_V2_SPINE_EMISSION_ENABLED` | `true` | `true` | boolean flag | `services/ods_spine/flags.py:21` · `routes/dr_v2.py:262` | ODS spine ingest on DR submit | Best-effort emitter runs on submit | Keep `true` |
| `DR_V1_PHOTO_INTEL_RECONCILER_ENABLED` | **MISSING** (defaults to `true` in code) | Set explicitly to `false` OR leave unset (code default = enabled) | boolean flag | `services/photo_intelligence/pipeline.py:620` | V1 legacy photo-intel reconciler | Enabled by code default | Set to `false` explicitly to match the "V1 dead path" intent captured in Track 26.01, OR leave unset and accept the code default |
| `DR_V3_TENANT_DEFAULT` | **MISSING** (empty) | Leave unset OR set to `true` | boolean flag | `routes/ui_flags.py:96` | Environment-level fallback for tenant-default V3 flag when the DB row is missing | Currently DB row `tenant_default=true` (set live during Track 26.03). If DB row ever gets wiped, env fallback is empty → V3 flag returns `false` → operators route to V1 | **Set to `true` in production** as a safety net for the DB row |

---

## 2 · DAILY REPORT AI PATH — FINAL VERDICT

**V3 Daily Report AI is LIVE and safe to deploy.**

- Frontend caller: `frontend/src/components/daily-report/DailySummaryAssist.jsx:193` → `POST /api/dr-v2/ai/synthesize`
- Backend route: `routes/dr_v2.py:295` gated by `_v2_ai_enabled()` → `os.environ.get("DR_V2_AI_ENABLED") in {"1","true","yes","on"}` (line 122)
- Provider factory: `services/dr_ai/factory.py:37` → `ai_available = bool(os.environ.get("EMERGENT_LLM_KEY"))`
- Provider impl: `services/dr_ai/emergent_provider.py` → uses `emergentintegrations` with `AI_DEFAULT_TEXT_MODEL` = `claude-sonnet-4-5-20250929`
- **Does NOT go through the strict `resolve_ai_capabilities()` gate** — V3 is intentionally decoupled

**Runtime evidence (Track 26.04 gate):** `GET /api/dr-v2/meta` returns `{feature_flag:true, provider:"emergent", model:"claude-sonnet-4-5-20250929", ai_available:true, agents:["day_narrative","risk_and_constraints","tomorrow_readiness"]}` — proven live on preview.

**V1 legacy Daily Report summary path (`daily_summary.py:323 → resolve_ai_capabilities("daily_report_summary")`)** — DISABLED at multiple gates (tenant + module + provider). This is expected because V1 shell is retired for the default tenant. Any operator forced onto V1 will see the deterministic composer return `enabled=false, reason_disabled="tenant_ai_disabled"` — matches Track 26.01 findings.

---

## 3 · PHOTO / DOCUMENT AI EVIDENCE VERDICT

**Photo Intelligence: silently disabled at the strict gateway. Not blocking deploy for Track 26 scope.**

- Pipeline entry: `services/photo_intelligence/pipeline.py:293` → `resolve_ai_capabilities(db, TENANT_DEFAULT, "photo_intelligence")`
- All 3 gates fail:
  1. `TENANT_AI_ENABLED=false` → gate 2 short-circuits with `reason_disabled="tenant_ai_disabled"`
  2. Even if gate 2 passed, all `AI_PROVIDER_*_ENABLED=false` + all direct provider keys empty → gate 5 would fail with `reason_disabled="no_provider_available"`
- Behavior: photos still upload, still render in the viewer, still appear in the PDF. **Only the vision observation/OCR overlay is missing.**
- V3 evidence manifest continues to function: `GET /api/daily-reports/{id}/evidence-manifest` returned HTTP 200 with keys `[version, generated_at, report_id, project_number, project_name, client, project_manager, location, report_date, supervisor_name, weather, gps_location, ...]` during Track 26.04 gate.

**Document extraction (Track 24.13 evidence engine):** does NOT depend on any AI flag. Uses PyMuPDF · openpyxl · xlrd · python-docx — all deterministic parsers. Evidence bundle + manifest hash + material reconciliation all remain functional regardless of AI state. PDF Section 10B renders when `evidence_manifest` is present on the DR payload. ✅ Safe.

---

## 4 · FLAGS THAT MUST CHANGE BEFORE DEPLOY

**None are strictly required.** The current preview config is functionally equivalent to what production should run for the Track 26 scope.

However, the following are **strongly recommended safety hardenings** for the production `.env`:

| Var | Set to | Why |
|---|---|---|
| `DR_V3_TENANT_DEFAULT` | `true` | Safety net if the DB row `ui_flags.dr_v3.tenant_default` ever gets wiped during restore/backup drills. Without it, operators would silently fall back to V1 shell and miss the Track 26.02 recovery fixes. |
| `EMERGENT_LLM_KEY` | (same value as preview OR production-scoped Universal Key) | **CRITICAL** — without it every AI path (including V3 DR AI) hard-disables. Confirm balance ≥ enough for launch traffic + top-up window. |
| `AUTO_EMAIL_REPORTS` | `true` | Preview has this OFF to protect Resend quota. Production MUST have it ON to actually send PM emails. (Called out earlier in Track 26.04 §7.) |

---

## 5 · FLAGS THAT SHOULD STAY FALSE

- `TENANT_AI_ENABLED` — keep off; enable per-tenant via Mongo `ai_tenant_capabilities` doc as the doctrine intends (`capabilities.py:15-33`).
- `TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED`, `TENANT_AI_PHOTO_INTELLIGENCE_ENABLED`, `TENANT_AI_TRANSLATION_ENABLED`, `TENANT_AI_PM_INTELLIGENCE_ENABLED`, `TENANT_AI_SAFETY_INTELLIGENCE_ENABLED`, `TENANT_AI_ADMIN_INTELLIGENCE_ENABLED` — all tenant-scoped, keep off at env; use Mongo doc overrides.
- `AI_DAILY_REPORT_SUMMARY_ENABLED` — V1 legacy path, keep off.
- `AI_PM_INTELLIGENCE_ENABLED`, `AI_SAFETY_INTELLIGENCE_ENABLED`, `AI_ADMIN_INTELLIGENCE_ENABLED`, `AI_TRANSLATION_ENABLED` — none of these dashboards are part of the Track 24→26 launch; enabling now = wasted provider spend.
- `AI_PHOTO_VISION_ENABLED` — currently `true` in preview but ineffective. Recommend flipping to `false` in production explicitly to prevent hollow enablement.
- `AI_PROVIDER_ANTHROPIC_ENABLED`, `AI_PROVIDER_OPENAI_ENABLED`, `AI_PROVIDER_GOOGLE_ENABLED` — keep `false` unless direct-provider keys are added.

---

## 6 · DEAD / UNUSED FLAGS (audit-visible drift)

| Var | Why called "dead / drift" |
|---|---|
| `AI_PHOTO_VISION_ENABLED=true` in preview | Set true, but never reaches an effective code path because upstream `TENANT_AI_ENABLED=false` and all provider flags/keys are off. Currently a **no-op flag** — deceptive to any admin who assumes vision is running. |
| `DR_V2_PHOTO_VISION_ENABLED=true` (legacy path) | Coexists with `AI_PHOTO_VISION_ENABLED`. Two flags for the same photo-vision surface — Track 26.01 already noted this drift class. |
| `AI_DAILY_REPORT_SUMMARY_ENABLED` | Only gates the V1 legacy deterministic composer. V3 (tenant default) bypasses this flag. Effectively dead for the current default tenant. |
| `DR_V1_PHOTO_INTEL_RECONCILER_ENABLED` (unset, code-default `true`) | V1 legacy path, not on the V3 tenant execution graph. Recommend explicit `false` OR a code cleanup to delete the whole V1 reconciler. |
| Scripts that read `EMERGENT_LLM_KEY` (`scripts/generate_icons.py` · `scripts/generate_hub_logos.py` · `scripts/generate_og_image.py` · `scripts/fix_*.py`) | Dev-time icon/logo generators. Not runtime. Should be flagged as tooling, not app config. |

---

## 7 · FUTURE CLEANUP RECOMMENDATIONS

1. **Consolidate the two AI paths.** V3 DR AI (`dr_ai/factory.py`) bypasses the strict resolver. Long-term, route V3 through `resolve_ai_capabilities(module="daily_report_summary")` too — with a new `daily_report_v3_summary` module key — so a single gate governs every AI call. Current split makes the admin AI status page misleading (see `services/ai_gateway/capabilities.py::gateway_status_snapshot`).
2. **Delete `AI_DAILY_REPORT_SUMMARY_ENABLED` + V1 legacy composer** once V3 is universally rolled out (`daily_summary.py:_compose_deterministic_summary`).
3. **Delete `DR_V2_PHOTO_VISION_ENABLED`** if `AI_PHOTO_VISION_ENABLED` becomes the sole gate — pick one, retire the other.
4. **Set `DR_V3_TENANT_DEFAULT=true` at env** as a safety net so a DB-row wipe doesn't silently revert operators to V1 (currently the only source of the flag is the `ui_flags` Mongo collection).
5. **Add a live `/api/ai/status` runtime probe** to the deployment smoke suite so any future flag drift surfaces immediately in ops.

---

## 8 · EXACT PRODUCTION ENV RECOMMENDATIONS

Set these EXACTLY in the production deploy environment (Emergent deployment dashboard):

```
# ── AI Gateway (strict resolver) ──
AI_GATEWAY_ENABLED=true
AI_DEFAULT_PROVIDER=anthropic
AI_DEFAULT_TEXT_MODEL=claude-sonnet-4-5-20250929
AI_DEFAULT_VISION_PROVIDER=openai
AI_DEFAULT_VISION_MODEL=gpt-5.2-vision
AI_PROVIDER_TIMEOUT_MS=45000
AI_PROVIDER_MAX_RETRIES=2
AI_PROVIDER_FAILOVER_ENABLED=true

# ── Provider direct enablement (KEEP OFF — Universal Key handles provider access) ──
AI_PROVIDER_ANTHROPIC_ENABLED=false
AI_PROVIDER_OPENAI_ENABLED=false
AI_PROVIDER_GOOGLE_ENABLED=false
# ANTHROPIC_API_KEY  — leave empty
# OPENAI_API_KEY     — leave empty
# GOOGLE_AI_API_KEY  — leave empty

# ── Module enablement (strict-resolver step 3) ──
AI_DAILY_REPORT_SUMMARY_ENABLED=false
AI_PHOTO_VISION_ENABLED=false                # (RECOMMENDED CHANGE from preview true→false)
AI_TRANSLATION_ENABLED=false
AI_PM_INTELLIGENCE_ENABLED=false
AI_SAFETY_INTELLIGENCE_ENABLED=false
AI_ADMIN_INTELLIGENCE_ENABLED=false

# ── Tenant defaults (kept off — enable per-tenant in Mongo `ai_tenant_capabilities`) ──
TENANT_AI_ENABLED=false
TENANT_AI_DAILY_REPORT_SUMMARY_ENABLED=false
TENANT_AI_PHOTO_INTELLIGENCE_ENABLED=false
TENANT_AI_TRANSLATION_ENABLED=false
TENANT_AI_PM_INTELLIGENCE_ENABLED=false
TENANT_AI_SAFETY_INTELLIGENCE_ENABLED=false
TENANT_AI_ADMIN_INTELLIGENCE_ENABLED=false

# ── V3 Daily Report AI path (BYPASSES the strict resolver) ──
DR_V2_AI_ENABLED=true
DR_V2_SPINE_EMISSION_ENABLED=true
DR_V2_PHOTO_VISION_ENABLED=false             # (RECOMMENDED CHANGE from preview true→false)
DR_V3_TENANT_DEFAULT=true                    # (NEW — safety net)

# ── Universal Key (required for V3 DR AI + translation + hub banners + OCC health) ──
EMERGENT_LLM_KEY=<production-scoped Universal Key>   # value redacted in this audit
```

---

## 9 · CERTIFICATION STATEMENT

I certify that:

1. Every AI-related env var read anywhere in `/app/backend/**/*.py` (excluding `tests/` and one-shot `scripts/*.py`) is enumerated in the truth table above.
2. Every current preview value was read directly from `/app/backend/.env` via a read-only parse; no secret value was printed.
3. Every "runtime effect NOW" claim is grounded either in a specific `file:line` in the codebase (verified in this audit) or in a runtime probe captured during Track 26.04 (`GET /api/dr-v2/meta`, `GET /api/feature-flags/dr-v3`, etc.).
4. The two-path architectural drift (strict gateway vs. Emergent-key direct) is **not** a Track 26.05 defect — it is pre-existing and correctly identified in Track 26.00C / 26.01 as "PROVEN DRIFT." It does not block deploy but should be resolved in a future consolidation track.
5. No flag was flipped during this audit. No secret was mutated. No code was touched.

**Answer to the six required questions:**

1. **Safe to deploy as-is?** ✅ YES for the Track 24 → 26 Daily Report recovery scope, with the 3 hardening changes in §8 (`DR_V3_TENANT_DEFAULT=true`, `AI_PHOTO_VISION_ENABLED=false`, `DR_V2_PHOTO_VISION_ENABLED=false`) and confirmation that `EMERGENT_LLM_KEY` is populated in production. Photo Intelligence, PM/Safety/Admin Intel, and V1 legacy summary are all silently disabled by design — no crash, no data loss, just a hollow AI panel on those unbuilt/paused surfaces.
2. **Flags that must be changed before deploy?** None strictly required. Three strongly recommended (§4).
3. **Flags that should stay false?** See §5 — 15 flags enumerated.
4. **Dead/unused flags?** See §6 — 5 items enumerated (photo-vision drift, dual paths, V1 leftovers).
5. **Flags needing future cleanup?** See §7 — 5 recommendations for a consolidation track.
6. **Daily Report AI path final verdict** — §2 (V3 LIVE, V1 disabled by design).
7. **Photo/document AI evidence verdict** — §3 (Photo Intel silently off, document extraction fully deterministic and live).
8. **Exact production env recommendations** — §8 (paste-ready block).

_End of Track 26.05 AI Secrets / Feature Flag Truth Table._
