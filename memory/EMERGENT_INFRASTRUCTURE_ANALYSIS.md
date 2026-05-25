# EMERGENT_INFRASTRUCTURE_ANALYSIS.md
## MASCI Operations Platform · Phase 27 · Emergent Hosting Reliance Audit
## iter428 · 2026-05-25

---

## What Emergent currently provides

| Service | Provided by Emergent | Notes |
|---|---|---|
| Preview pod (Kubernetes container) | ✅ | 9.8 GB disk · ~600 MB RAM headroom · automated supervisor |
| Hot-reload dev runtime | ✅ | FastAPI auto-reload · React craco dev server |
| Production deploy pipeline | ✅ | redeploys via dashboard · CI-less |
| Production runtime container | ✅ | live at `mascidocs.com` |
| Edge / proxy routing | ✅ | maps `/api/*` → backend:8001 · everything else → frontend:3000 |
| TLS termination | ✅ | wildcard preview cert + custom prod cert |
| `REACT_APP_BACKEND_URL` env injection | ✅ | preview vs prod URLs handled automatically |
| `MONGO_URL` + `DB_NAME` env management | ✅ | preview-side editable in `.env`; production-side via Emergent deploy dashboard |
| Universal LLM key (covers OpenAI / Anthropic / Gemini) | ✅ | meter-billed against your Emergent account |
| GitHub sync ("Save to GitHub") | ✅ | manual commit button |
| Image / file upload to agent context | ✅ | how you handed me your Atlas screenshots |
| Rollback to prior checkpoints | ✅ | free of charge per Emergent doctrine |
| Support agent escalation | ✅ | for platform-level questions |

## What Emergent does NOT provide

| Item | Where you go instead |
|---|---|
| MongoDB persistent cluster | MongoDB Atlas (just migrated) |
| Object storage | Cloudflare R2 (already wired) |
| Email transactional | Resend (already wired) |
| Error telemetry | Sentry (already wired) |
| DNS / domain ownership | external registrar + Cloudflare |
| SMS / push notifications | future (Twilio / FCM if needed) |
| Background workers / cron beyond what FastAPI runs in-process | currently in-process; cron-as-a-service NOT needed |
| Persistent disk volumes per pod | preview pod disk is ephemeral; production disk persistence is **only as durable as Mongo Atlas + R2** |

---

## What Emergent costs you

The Emergent dashboard is the single source of truth for this. As of this audit:

| Line | How to check | What governs cost |
|---|---|---|
| Account subscription tier | Emergent dashboard → Account → Plan | flat per-month or per-developer |
| Compute usage (preview + prod) | Emergent dashboard → Usage | pod-hours · build minutes |
| Universal LLM key meter | Emergent dashboard → Profile → Universal Key | per-token usage from each provider |
| Email + SMS bonus credits | Emergent dashboard → Account | typically bundled with tier |
| Build minutes | Emergent dashboard → Usage | per redeploy build time |

**This audit cannot read the Emergent dashboard directly** — that data lives behind your Emergent account auth, not in the preview pod's filesystem. The operator (you) is the only authority for what your Emergent line is.

**Action item:** open the Emergent dashboard once a month for 60 seconds and screenshot Usage + Universal Key meter. Drop the screenshots in `/app/memory/EMERGENT_USAGE_LOG.md` and we'll keep a running record.

---

## Reliance / lock-in profile

| Vector | Risk | Mitigation |
|---|---|---|
| Pod gets terminated | Mongo lives in Atlas now; R2 holds disk-tree archive | already mitigated by iter428 migration |
| Emergent platform price increase | could materially affect the only non-free line | mitigation: the codebase is portable FastAPI + React + Mongo + S3-compatible — runnable on Render / Railway / Fly / DigitalOcean App Platform / AWS in a weekend |
| Emergent runtime outage | platform unavailable until Emergent recovers | mitigation: same — portable architecture, fresh R2 archive lets you stand up an alternate runtime same day |
| Universal LLM key key rotation | features that use AI temporarily fail | mitigation: no critical operational feature uses AI today; OCR pipeline is a one-off historical import |
| Emergent removes Universal Key feature | LLM features stop working until you bring your own keys | mitigation: trivial — swap `EMERGENT_LLM_KEY` for `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` from the same providers |

**Worst case:** Emergent disappears tomorrow. Recovery posture:
1. Spin up a $5/mo Render or Fly.io app
2. Point at the same Atlas cluster
3. Point at the same R2 bucket
4. Update Cloudflare DNS to the new runtime IP
5. Operational continuity restored in ≤ 4 hours

This is not a fire drill — this is a known mitigation. The platform is **architected for portability**.

---

## Real measurements visible to the preview pod

| Item | Reading |
|---|---|
| Pod disk | 9.8 GB total / 6.0 GB used / 3.8 GB free (62 % use after iter427/428 cleanup) |
| Pod inode use | 21 % |
| Container Mongo (preview-side, soon to be retired) | 858 MB |
| Backend `__pycache__` | 1.7 MB |
| Frontend `node_modules` | 1.6 GB |
| `.git` repo | 1.3 GB |
| `/app/backend/storage` (project_docs, etc.) | 533 MB |
| `/app/backend/static` (training videos) | 300 MB |
| `/app/memory` | 3.9 MB |
| Preview pod backend uptime | ~17 min (post-iter428 restart) |
| Preview pod CPU pressure | nominal · supervisor reports healthy |

These are preview-pod numbers, not production-pod numbers. **Production runs in a separate Emergent-managed pod** that I cannot directly inspect from inside this preview workspace.

---

## Verdict

🟡 **Emergent runtime is the single non-free line in the budget — but only because every other line is on a hard-cap free tier.** Reliance on Emergent is high (it's the runtime), but **lock-in is low** because the entire codebase is portable to any FastAPI + Node-capable host within a single workday.

---

End of Emergent Infrastructure Analysis.
