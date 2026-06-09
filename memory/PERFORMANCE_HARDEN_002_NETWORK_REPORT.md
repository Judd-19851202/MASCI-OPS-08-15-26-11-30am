# PERFORMANCE-HARDEN-002 · Phase 2C+2D+2E+2F · Network · Image · Payload · Trust

```
Environment    : preview (changes executed) · production (ships on next deploy)
Access Level   : preview-runtime + static-analysis
Evidence Source: file diff · index.html · live frontend probe
Confidence     : VERIFIED for every change · INFERRED for projected mobile-LCP impact
```

---

## §2C · Network Hardening

### Current state (after this sprint + carry-forward)

`/app/frontend/public/index.html` carries five resource hints:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="preconnect" href="https://assets.emergent.sh" crossorigin />
<link rel="preconnect" href="https://us.i.posthog.com" crossorigin />
<link rel="dns-prefetch" href="https://us-assets.i.posthog.com" />
```

### Audit result this refresh

No additional preconnect or dns-prefetch is justified by evidence:

| Origin | Considered? | Decision |
|---|---|---|
| `mascidocs.com` API | YES | Same-origin as the page → preconnect unnecessary (browser already has the connection from initial HTML fetch). |
| Cloudflare R2 (photo storage) | YES | All photo URLs are served through `/api/job-photos/.../thumb` on same-origin via signed token — no separate CDN origin to preconnect. |
| Motive API | NO | Server-side only; never called from the browser. |
| Sentry ingest | YES | Same-page Sentry SDK lazily inits. Adding preconnect would warm a socket the browser may not need for 5+ seconds. **NOT JUSTIFIED.** |
| Google Tag Manager / Analytics | n/a | Not in use. |

**Action this sprint:** none. The 5 existing hints stand.

---

## §2D · Image Hardening

### State after this sprint

`<img>` tags carrying `loading=` or `decoding=` attributes: **10** (up from 7 in prior sprint).

### Files touched this refresh

| File | Change |
|---|---|
| `src/components/ActivityFeed.jsx:94` | `+ loading="lazy" decoding="async"` (scrolling feed image — below the fold) |
| `src/components/DriverCommandProfile.jsx:93` | `+ decoding="async"` (profile photo — above fold, no lazy) |
| `src/pages/admin/AdminPromoAssets.jsx:811` | `+ decoding="async"` (modal lightbox — async decode is safe even though it's the main content) |

### Files intentionally left unchanged

| File | `<img>` purpose | Why no change |
|---|---|---|
| `AdminMfa.jsx:229` | MFA enrollment QR code | Tiny inline QR; above fold; user is actively enrolling — lazy would feel sluggish |
| `TrainingQrPoster.jsx:283` | QR poster | The QR IS the entire page content; lazy would block printing |
| `TrenchSafetyOpsCenter.jsx:419` | Asset QR label inside modal | Modal is gated by user click; loading="lazy" inside `display:none` parent has cross-browser quirks |
| 8 signature `<img>` tags across `FieldLeadershipView`, `ViewMeeting`, `ViewSafetyForm`, `ViewQaqcInspection`, `ViewEquipmentInspection` | Each is small (max-h-20 to max-h-32), single-use, and rendered after the report's photo grid (which IS lazy) — adding lazy here would force two phases of rendering |

### Layout-shift risk

None. Every changed `<img>` retains its prior `className` which fully constrains layout (`object-cover`, `max-h-28`, `h-full w-full`, etc.). `loading="lazy"` and `decoding="async"` are layout-neutral attributes.

### Quality / regression

None. Both attributes are passive hints to the browser; no quality reduction.

---

## §2E · Payload Hardening

### lucide-react import audit

```
Files importing from lucide-react:  408
Patterns used:
  import { IconA, IconB } from "lucide-react"  ← named imports, tree-shakeable
  import * from "lucide-react"                  ← NOT FOUND (0 instances)
```

All imports are already tree-shakeable by Webpack/craco. **No action required.**

### Dead-import audit

| Class | Count | Action |
|---|---|---|
| Unused imports flagged by ruff in `server.py` (F401) | 0 (none in our compiled list — see GOVERNANCE-HARDEN-001 baseline) | n/a |
| Unused vars (F841) in `server.py` | 1 (pre-existing) | **Leave alone** — OMEGA "no unrelated cleanup" |
| Re-defined functions (F811) | 2 (pre-existing) | **Leave alone** — same |
| Frontend duplicate imports | 0 (eslint clean on touched files) | n/a |

### Bundle-size audit

Not run as a deep webpack-bundle-analyzer this sprint (would be effort outside OMEGA's scope). The four explicitly prohibited remediations (route code-splitting, virtualization, framework changes, refactors) remove the only reasonable bundle-shrinking actions, so further work here is gated behind a future sprint.

---

## §2F · Trust Hardening

OMEGA constraint: "Only proven improvements. No feature additions."

### Audit method

Reviewed every user-facing status field in the live preview UI for ambiguity. Compared with the existing PROD-side messaging patterns documented in `RESILIENCY_HARDEN_001_CERTIFICATION.md`, `MOTIVE_PROD_INCIDENT_001_PLATFORM_INTEGRATION.md`, and `WEBHOOK_HARDEN_001_CERTIFICATION.md`.

### Verdict

Existing status surfaces are **already clear and operator-tested** as of:
- Resiliency queue: `DraftStatusPill`, `OfflineIndicator`, `DraftRecoveryNotice`, `DraftRestorePrompt` (4 components, all reviewed in RESILIENCY-HARDEN-001 and operator-approved).
- Integration health: `/api/integrations/health` returns explicit `status` + `awaiting_credentials` + timestamps per WEBHOOK-HARDEN-001.
- Upload status: photo upload flows show progress per file with per-chunk state (chunked upload contract).
- Sync timestamps: `integration_settings.<provider>.last_sync_at` rendered in admin panel.

No new ambiguity surfaced in this audit that meets the directive's "proven improvement" bar.

### Action

**None.** The directive explicitly forbids feature additions, and any change in this category would be feature-shaped.

If the operator surfaces a specific user-facing confusion in a future sprint, that becomes a justified one-line fix with its own evidence.

---

## §2G · Mobile Certification (deferred to companion `MOBILE_REPORT.md`)

See `/app/memory/PERFORMANCE_HARDEN_002_MOBILE_REPORT.md` for the dedicated mobile audit.

---

## Summary table (Phases 2C + 2D + 2E + 2F)

| Phase | Action | Files touched | Net change |
|---|---|---|---|
| 2C Network | Audit-only this refresh; 5 hints carried forward | 0 | 0 lines |
| 2D Image | +3 image attribute additions | 3 (ActivityFeed, DriverCommandProfile, AdminPromoAssets) | +3 attrs |
| 2E Payload | Audit-only | 0 | 0 lines |
| 2F Trust | Audit-only | 0 | 0 lines |

Total LOC delta in this category: **+3** (additive only).
