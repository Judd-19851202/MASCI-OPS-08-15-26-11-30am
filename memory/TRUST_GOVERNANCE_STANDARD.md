# Trust Governance Standard
## MASCI Operational Trust Doctrine · 2026-05-27

> The 12 binding principles every shared platform surface must
> honor. This is the doctrine new features inherit from. Violating
> a principle requires explicit written justification (in the
> feature's PRD entry) and a remediation date.

---

## 1 · The 12 principles

### 1 · Truthful system state
A pill / banner / chip / toast must NEVER announce a state it cannot prove. "Saved" means the bytes are confirmed on disk. "Sent" means the server returned 2xx. "Loaded" means the snapshot was applied.

**Violation example (iter440 H1, closed):** pill said "Saved" on every silent quota failure.

### 2 · Survivability first
Operator work — even mid-edit, mid-debounce, mid-suspend — must survive every realistic interruption (screen lock · home button · call · low-memory eviction · bfcache miss · partial offline · network gate).

**Test:** if a foreman taps the home button mid-typing and returns 10 minutes later, the most recent 10 seconds of typing must be on disk.

### 3 · Calmness under pressure
No badge spam · no red-fatigue · no surveillance language · no modal-soup · no auto-dismissing toasts that vanish before the eye registers them · no marketing voice ("Awesome! 🎉").

**Test:** show the page to someone who has never used construction software. They must not feel they are being "celebrated" or "tracked".

### 4 · Predictable workflows
Same action on same surface → same result every time. No silent inference. No "smart" auto-apply. Operator intent is always explicit.

**Violation example (would-have-been):** auto-applying yesterday's crew setup without confirmation. iter442 closed this via project-change confirm + the explicit Use Setup tap.

### 5 · Contextual orientation
Operator always knows where they are AND where "back" goes. No hardcoded labels on shared surfaces. No `navigate(-1)` reliance.

**Mechanism:** `useReturnContext()` (iter443).

### 6 · Operational continuity
Token rotation · cross-portal navigation · session refresh · multi-login · passkey re-auth — none of these may orphan in-progress work.

**Mechanism:** device-scoped IDB keys (iter440) + legacy migration.

### 7 · Visible assumptions
Anything the platform infers (operator identity, device memory, preload setup) is **shown** to the operator before acting. Confidence-tiered banners (iter442) are the pattern: low/medium confidence = soft offer, high confidence = affirmative ("Loaded from recent reports").

### 8 · Reversible behavior
Every destructive action is recoverable for ≥24h.

**Mechanism:** soft-delete archives (iter440 draft archive) · open: `recoverArchivedDraft` is exported but no UI surface yet (TF-016).

### 9 · Field-first ergonomics
iPhone Safari is the design substrate. Desktop is a fallback. iPad is the second surface (superintendents). Every flow must be testable on the iPhone-class viewport before it ships.

**Mechanism:** Playwright tests parametrize across mobile / desktop / ipad viewports. Open: ipad viewport not in draft-loss regression (TF-009).

### 10 · Lightweight operational memory
Device may *suggest* context. Device must never *hard-lock* identity. No accounts, no passwords, no keys for crew memory.

**Mechanism:** `crewMemory.js` doctrine + `DAILY_REPORT_DEVICE_MEMORY_MODEL.md`.

### 11 · Observable failures
Every silent failure mode has a telemetry event. Every shipped event has a backend collection + admin-side surface. Telemetry without a consumer is a smell.

**Mechanism:** `/api/draft-telemetry` collection + Draft Health tile (iter440/442). Open: device_memory.* events not yet in allowlist (TF-006).

### 12 · Low-friction interaction
Calm beats clever. One tap to act. No multi-step wizards for routine actions. No "are you sure?" modals for safe operations. Reserve confirms for genuinely destructive operations (Clear Saved Setup; Discard Draft is already soft-delete so no confirm needed).

---

## 2 · Authoring contract

Any new shared surface (an RFI detail page · a Constraint detail · a Schedule view) MUST:

| # | Requirement | Verification |
|---|---|---|
| 1 | Use `useFormDraft` for any editable form | code review |
| 2 | Use `useReturnContext` for any back link | code review |
| 3 | Use `BackLink` primitive (no bespoke back buttons) | regression test |
| 4 | Pass through quota check via `quotaProbe` for any photo-heavy form | code review |
| 5 | Use device-scoped IDB key (never token-derived) | code review |
| 6 | Persist any idempotency key in IDB before first submit attempt | code review |
| 7 | Emit telemetry for write OK / write fail / lifecycle transitions | code review |
| 8 | Use coaching copy from `DAILY_REPORT_COACHING_LANGUAGE.md` phrase book (or extend it) | code review |
| 9 | Test on mobile viewport at minimum | Playwright |
| 10 | Test on iPad viewport for superintendent surfaces | Playwright |

---

## 3 · Severity tier for trust violations

| Tier | When a finding gets this tier |
|---|---|
| T0 | Cosmetic only · no operator-perceived difference |
| T1 | Mild friction · operator notices but works around easily |
| T2 | Workflow confusion · operator has to think about what just happened |
| T3 | Operator trust degradation · operator starts to question the platform |
| T4 | Data survivability risk · operator's work is conditionally at risk |
| T5 | Operational integrity failure · submitted records can disappear or duplicate silently |

T4 and T5 findings MUST be closed before any Phase V (RFI / Schedule / Constraints) work begins.

---

## 4 · Telemetry contract

For every silent-failure mode:

| Mode | Event |
|---|---|
| Draft write attempted | `draft.write.ok` |
| Draft write failed | `draft.write.fail` (carries `errorName` + `trigger`) |
| Restore prompt offered | `draft.restore.offered` |
| Restore prompt actioned | `draft.restore.action` (carries `choice`) |
| Lifecycle transition | `draft.lifecycle` (carries `transition` + `pendingDirty`) |
| Actor id rotated (migration) | `draft.actorId.rotated` |
| Quota warning | `quota.warning` |
| (future) Device memory action | `device_memory.applied / declined / cleared` |

Adding a new event requires updating `ALLOWED_EVENTS` in `routes/draft_telemetry.py` AND `DRAFT_INSTRUMENTATION_PLAN.md`.

---

## 5 · Visual doctrine intersection

This doctrine intersects with the existing visual doctrine
(diff_doctrine_baseline.py).

| Layer | Owner |
|---|---|
| Visual loudness gate | `pre_deploy_check.sh` + `diff_doctrine_baseline.py` |
| Operational trust gate | this document + `TRUST_FINDINGS_MATRIX.json` |

Red is reserved for actionable urgency only. OSHA Recordable chips
do not need to be red (TF-014 backlog).

---

## 6 · Language doctrine (anchor)

The phrase book is at `/app/memory/DAILY_REPORT_COACHING_LANGUAGE.md`.
Banned phrasing (regression-tested):
- "we identified you"
- "we are learning"
- "personalized for you"
- "we know you"
- "tracking" / "behavior"
- "ai" / "profile" (as standalone words)

New shared surfaces must add their strings to the phrase book
before merging.

---

## 7 · Migration policy

Existing surfaces migrate one at a time, on a real trigger:
- a field report
- a proactive sweep when the surface is being touched anyway
- a Phase V dependency

No big-bang migrations. The doctrine is binding for new code;
existing code migrates surgically.

---

## 8 · Audit cadence

| Cadence | Surface |
|---|---|
| On every field report | Specific surface in the report |
| Before Phase V work begins | Re-run TRUST-1 audit (this document) on any P0 surface touched in the interval |
| Quarterly | Lightweight regression — verify telemetry events still flow; doctrine documents still match code reality |

The audit is not corporate process — it is engineering hygiene. It
exists because the next layer (Phase V) compounds the consequences
of any unresolved trust risk.

---

## 9 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Doctrine published · 12 principles binding
- **Cross-refs:** `OPERATIONAL_TRUST_AUDIT_MASTER.md`, `TRUST_FINDINGS_MATRIX.json`, `TRUST_CRITICAL_SURFACES.md`, `TRUST_SEVERITY_HEATMAP.md`
