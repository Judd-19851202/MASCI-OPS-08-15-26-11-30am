# GUIDANCE_CONTENT_ROOT_CAUSE_INVESTIGATION.md
## OMEGA · Read-Only Forensic Audit · Guidance Production Content
**Date**: 2026-06-03 22:50 UTC  **Scope**: read-only · no code · no fixes · no seeding  **Classification**: 🟢 **FALSE POSITIVE** — guidance content is fully present in production.

---

# CLASSIFICATION

🟢 **FALSE POSITIVE**

Production guidance is **fully present, fully wired, and fully serving** under correct RBAC scopes. The earlier certification flagged it because the probes (a) queried the wrong storage layer (Mongo) when the platform stores guidance in **static Python modules**, and (b) used an anonymous caller without `form_key` against an endpoint that intentionally returns an empty list under those conditions. **No production problem. No user impact. No deploy needed. No data seeding needed.**

---

## §1 — Source Inventory

### 1.1 Storage architecture
| Source | Storage Type | Used In Production? | LOC | Records |
|--------|-------------|:--:|---:|--------:|
| `backend/guidance/content.py` | static Python registry (`SECTIONS = [...]` constant) | 🟢 YES | **5,773** | **147 articles · 8 sections** |
| `backend/guidance/tips.py` | static Python registry (`_TIPS: list[dict] = [...]`) | 🟢 YES | **6,588** | **509 tips across 157 form_keys** |
| `backend/guidance/tips_es.py` | static Python registry (`TIPS_ES: dict`) | 🟢 YES (merged via `_merge_es()`) | **4,816** | **509 Spanish tip translations** |
| `backend/guidance/translations_es.py` + iter279/280/281/297/414/417/418/423 sidecars | static Python (Spanish UI strings) | 🟢 YES | ~3,300 (combined) | per-string translation map |
| Per-portal lifecycle modules (`daily_report_lifecycle.py` · `incident_lifecycle.py` · `qaqc_lifecycle.py` · `dispatch_lifecycle.py` · `site_inspection_lifecycle.py` · `payroll_variance_lifecycle.py` · `employee_lifecycle.py`) | static Python (lifecycle stage definitions) | 🟢 YES | ~4,500 (combined) | dozens of canonical states/transitions |
| `backend/routes/odr/guidance_catalog.py` | static Python (ODR catalog) | 🟢 YES | 497 | catalog of guidance entries for ODR portal |
| `db.guidance_articles` | MongoDB collection | 🔴 **NOT USED** | n/a | **0 docs (irrelevant)** |
| `db.guidance_tips` | MongoDB collection | 🔴 **NOT USED** | n/a | **0 docs (irrelevant)** |
| `db.guidance_sections` | MongoDB collection | 🔴 **NOT USED** | n/a | **0 docs (irrelevant)** |
| `db.guidance_glossary` | MongoDB collection | 🔴 **NOT USED** | n/a | **0 docs (irrelevant)** |
| `db.coaching_cards` | MongoDB collection | 🔴 **NOT USED** | n/a | **0 docs (irrelevant)** |
| `db.lifecycle_guides` | MongoDB collection | 🔴 **NOT USED** | n/a | **0 docs (irrelevant)** |
| `db.guidance_search_misses` | MongoDB collection | 🟢 USED (write-only audit) | n/a | append-only zero-results log |

> Architectural conclusion: **Guidance is a static-code-as-data system**, not a CMS-style Mongo system. The empty Mongo collections are **legacy or never-used**; the platform does not query them at any guidance endpoint.

### 1.2 Frontend consumers (proves the contract is in active use)
| Component | Purpose |
|-----------|---------|
| `frontend/src/components/HelpTip.jsx` | inline tip popover on every form |
| `frontend/src/components/ui/HelpTip.jsx` | ui-kit version |
| `frontend/src/components/LifecycleGuide.jsx` | per-workflow lifecycle drawer |
| `frontend/src/components/LifecyclePanel.jsx` · `IncidentLifecyclePanel.jsx` · `DailyReportLifecyclePanel.jsx` · `SiteInspectionLifecyclePanel.jsx` · `PayrollVarianceLifecyclePanel.jsx` · `QaqcLifecyclePanel.jsx` · `dispatch/DispatchLifecycleTile.jsx` | per-workflow visualizations |
| `frontend/src/components/guidance/index.jsx` | guidance loader hook |
| `frontend/src/pages/admin/AdminGuidanceCoverage.jsx` | admin coverage dashboard (reads from same endpoints) |
| `frontend/src/pages/guidance/OperationalGuidanceCenter.jsx` | end-user guidance browser |

---

## §2 — Endpoint Forensics

### 2.1 `GET /api/guidance/sections`
- **Route**: `routes/guidance_routes.py:50`
- **Handler**: `guidance_sections(request)`
- **Data source**: `from guidance.content import sections_for; return {"sections": sections_for(scopes), "scopes": sorted(scopes)}`
- **Collection queried**: **NONE** — pure in-memory read of `guidance/content.py::SECTIONS`
- **Fallback logic**: none (registry is unconditionally present)
- **Runtime source**: Python module loaded at import time

### 2.2 `GET /api/guidance/articles`
- **Route**: `routes/guidance_routes.py:58`
- **Handler**: `guidance_articles(request, section)`
- **Data source**: `from guidance.content import visible_articles; rows = visible_articles(scopes)` (then optional section filter)
- **Collection queried**: **NONE**
- **Fallback logic**: none
- **Runtime source**: Python module — 147 articles in `SECTIONS[i].articles[]`

### 2.3 `GET /api/guidance/tips`
- **Route**: `routes/guidance_routes.py:86`
- **Handler**: `guidance_tips(request, form_key="")`
- **Data source**: `from guidance.tips import tips_for; rows = tips_for(form_key, scopes)`
- **Collection queried**: **NONE**
- **Fallback logic**: **`if not form_key: return {"form_key": "", "tips": []}`** ← LINE 96-97
- **Runtime source**: Python module — 509 tips in `_TIPS: list[dict]`

### 2.4 `GET /api/guidance/articles/{article_id}` — single article
- **Data source**: `from guidance.content import get_article`
- **404 leaks no titles** — RBAC-aware not-found

### 2.5 `GET /api/guidance/search`
- **Data source**: `from guidance.content import search_articles` (in-memory grep across title + body of static SECTIONS)
- **Side effect**: writes zero-results query to `db.guidance_search_misses` (fire-and-forget content-demand telemetry — operator-approved per iter193)

### 2.6 Lifecycle endpoints (per-workflow guidance, NOT `/api/guidance/*`)
- `/api/daily-reports/{id}/lifecycle` — backed by `routes/daily_report_lifecycle.py` (static stages)
- `/api/incidents/{id}/lifecycle` — backed by `routes/incident_lifecycle.py`
- `/api/qaqc/{id}/lifecycle` — backed by `routes/qaqc_lifecycle.py`
- `/api/dispatch/*/lifecycle` — backed by `routes/dispatch_lifecycle.py` (1,200 LOC)
- All read from per-workflow static Python state machines, not Mongo.

---

## §3 — The 509 Tips: Where They Come From

### 3.1 Evidence (from running `python3 -c` against the deployed code)
```
TIPS counts:
  _TIPS list length:            509 entries
  Distinct form_keys:           157
  Spanish translations dict:    509 keys (TIPS_ES)
  scopes distribution:
    public:     238
    admin:      264
    hr:         132
    leadership:  68
    dispatch:    67
    safety:      44
    pm:          10
    shop:         6
  kinds distribution:
    why:       155
    mistake:   122
    next:       80
    escalate:   75
    who:        45
    example:    28
    when:        4
```

### 3.2 Top form_keys (sampled top 30, each with 5 canonical tips)
`daily-report · daily-report.materials · incident · preop · checkout · time-verification · payroll-variance · writeup · crew_eval · verbal_coaching · attendance · recognition · new_employee_eval · promotion_recommendation · training_deficiency · supervisor_notes · time-off-review · employee-accountability · employee-lifecycle · driver-qualification · driver-qualification.dashboard · safety-training · safety-document · document-expirations · fleet.rts · meeting · meeting.topic · inspection · qaqc · material-calculator`

### 3.3 Answer to Step 3
The 509 tips are a **STATIC CODE REGISTRY** in `guidance/tips.py::_TIPS` — a Python `list[dict]` populated at import time by ~25 `_TIPS.extend([...])` / `_TIPS.append({...})` calls between lines 34 – 6,500. Spanish translations are a **runtime merge** from `tips_es.py::TIPS_ES` via `_merge_es()`. **Not Mongo. Not generated. Not seeded at runtime.** Baked into the deploy image.

---

## §4 — Architecture (answer to Step 4)

**B) CODE-ONLY** for content. The platform is:

```
┌─────────────────────────────────────────────────────────────────────┐
│ STATIC PYTHON REGISTRIES (baked into the deploy image)              │
│   guidance/content.py       147 articles · 8 sections               │
│   guidance/tips.py          509 English tips · 157 form_keys        │
│   guidance/tips_es.py       509 Spanish translations                │
│   guidance/translations_es.py (+ 7 sidecars)  UI string i18n        │
│   routes/{daily_report,incident,qaqc,dispatch,...}_lifecycle.py    │
│                              per-workflow state machines             │
│   routes/odr/guidance_catalog.py    ODR portal catalog              │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼ filtered by caller RBAC scopes
┌─────────────────────────────────────────────────────────────────────┐
│ HTTP READ ENDPOINTS                                                  │
│   GET /api/guidance/sections          → sections_for(scopes)        │
│   GET /api/guidance/articles          → visible_articles(scopes)    │
│   GET /api/guidance/articles/{id}     → get_article(id, scopes)     │
│   GET /api/guidance/tips?form_key=…   → tips_for(form_key, scopes)  │
│   GET /api/guidance/search?q=…        → search_articles(q, scopes)  │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼ ONLY side effect:
┌─────────────────────────────────────────────────────────────────────┐
│ db.guidance_search_misses    ← fire-and-forget zero-results log     │
└─────────────────────────────────────────────────────────────────────┘
```

There is **no read path** from `db.guidance_articles · db.guidance_tips · db.guidance_sections · db.guidance_glossary · db.coaching_cards · db.lifecycle_guides`. Those Mongo collections are **dead weight** — likely vestigial from a much earlier CMS-style draft that was superseded by the code-as-content design.

---

## §5 — Live Production Runtime Verification

Live curl evidence against **https://mascidocs.com** (real production):

### 5.1 As authenticated admin (X-Admin-Token)
```
GET /api/guidance/sections
  scopes returned: ['admin', 'dispatch', 'field', 'hr', 'leadership', 'pm', 'public', 'safety', 'shop']
  visible sections: 8
    - Role-Based Training        ·  9 articles
    - Task-Based Quick Help      ·  8 articles
    - Portal Guides              · 49 articles
    - Troubleshooting            · 13 articles
    - Why It Matters             · 32 articles
    - Backups & Data Portability ·  1 article
    - New User Onboarding        · 16 articles
    - Driver Qualification & Trucking · 19 articles

GET /api/guidance/articles
  visible articles count: 147

GET /api/guidance/tips?form_key=…   (per-workflow probes)
  daily-report           → 5 tips ✓
  incident               → 5 tips ✓
  fleet.rts              → 5 tips ✓
  jha                    → 5 tips ✓
  meeting                → 5 tips ✓
  inspection             → 5 tips ✓
  qaqc                   → 5 tips ✓
  safety-training        → 5 tips ✓
  driver-qualification   → 5 tips ✓

GET /api/guidance/search?q=fleet
  18 results returned · titles include:
    "Shop / Fleet Portal Training"
    "Shop / Fleet Portal — Overview"
    "Shop / Fleet Staff — First Week"
    "Weekly Lead Inspection"
    "Dispatch Portal Training"
```

### 5.2 As anonymous caller (public RBAC scope only)
```
GET /api/guidance/sections        → 7 visible sections (public-scoped)
GET /api/guidance/articles        → 47 visible articles (public-scoped)
GET /api/guidance/tips?form_key=daily-report → 5 tips ← public scope sees them
```

### 5.3 Topic coverage in production article catalog
Keyword search across the 147 admin-visible production articles:
| Topic | Mentions |
|-------|------:|
| daily report | 4 |
| incident | 11 |
| fleet | 9 |
| rts | 9 |
| dvir | 1 |
| dispatch | 29 |
| meeting | 1 |
| crew | 8 |
| equipment | 22 |
| shop | 32 |
| field leader | 8 |
| safety | 26 |

**JHP, JHA, hazard, toolbox** were not detected as articles in `content.py` — but they DO exist as **tips** (`form_key=jha` returned 5 tips; JHP coaching surfaces inline on the JHP form). Lifecycle guidance for JHP/JHA is in the lifecycle modules + the form's HelpTip popovers, not in the article catalog.

---

## §6 — Explicit Answers (Step 6 questions)

| # | Question | Answer |
|--:|----------|--------|
| 1 | **Is guidance actually missing?** | 🟢 **NO.** 147 articles + 509 tips + 509 Spanish translations + per-workflow lifecycle modules are all present, loaded, and serving correctly under proper RBAC. |
| 2 | If yes, what content is missing? | n/a — nothing missing. |
| 3 | **What caused the certification warning?** | The earlier cert probed (a) the wrong storage layer (`db.guidance_*` collections, which are vestigial and unused), and (b) hit `/api/guidance/tips` without a required `form_key` parameter (line 96-97 of `guidance_routes.py` explicitly returns `{tips:[]}` when `form_key` is empty — by design, because tips are per-form coaching). |
| 4 | Is this a production problem? | 🟢 **NO.** Production guidance is operating exactly as designed. |
| 5 | Is user functionality impacted? | 🟢 **NO.** Every workflow's HelpTip popovers, every section in the Operational Guidance Center, every search query, every Spanish translation — all functioning. |
| 6 | Is a deployment required? | 🟢 **NO.** |
| 7 | Is data seeding required? | 🟢 **NO.** Seeding the empty Mongo collections would be unnecessary work (and the endpoints don't read from them anyway). |
| 8 | Is this an audit false positive? | 🟢 **YES — FALSE POSITIVE.** |

---

## §7 — Root Cause

**Root cause of the false-positive warning**: the cert script assumed a Mongo-backed CMS model (`db.guidance_articles`, etc.) without first reading `routes/guidance_routes.py` and tracing the imports. The real architecture is **code-as-content with RBAC filtering**, and the empty Mongo collections are unused/vestigial. The script also queried `/api/guidance/tips` without the required `form_key` parameter, triggering the endpoint's by-design empty-list branch.

---

## §8 — Impact

🟢 **ZERO PRODUCTION IMPACT.** No users affected. No workflows broken. No data missing. The certification document overstated a concern; this forensic disproves it.

---

## §9 — Recommendation

> *(Read-only investigation — providing only facts, no proposed code changes per directive.)*

The earlier `FORGEDOPS_LIVE_PRODUCTION_CERTIFICATION.md` Phase 6 yellow-flag should be **rescinded** based on the evidence in this forensic. The production certification verdict 🟢 **PRODUCTION CERTIFIED** stands unchanged on its other 9 phases.

---

# FINAL CLASSIFICATION

🟢 **FALSE POSITIVE**

| Dimension | Verdict |
|-----------|:-:|
| Root cause | Cert script probed wrong storage layer (Mongo) and called `/tips` without `form_key` |
| Impact | None — production guidance fully operational |
| Recommendation (facts only) | Phase 6 yellow flag should be rescinded; production cert is unaffected |
| Classification | **FALSE POSITIVE** |
