# AI-ADMIN-001 · UI Spec

**Route:** `/admin/ai-configuration` (admin-only)
**Shell:** `AdminShell` (section = `"system"`)
**Nav home:** Admin sidebar → *System & Governance* group

---

## 1. Header

- Icon: `Sparkles` in a solid `bg-indigo-700` tile.
- Kicker (mono/caps): `AI-ADMIN-001 · Optional Intelligence Controls`.
- Title: `AI Configuration`.
- Subtitle: "Manage AI availability per tenant and per module. AI is
  optional — the platform runs 100% with every switch off. Field users
  see no AI chrome regardless of these settings."
- Amber safety chip: "API keys are managed in **Emergent Secrets**.
  Keys are never displayed here."
- Right side: `Refresh` button.

Every element carries a `data-testid`. Root: `admin-ai-configuration-page`.

## 2. Section 1 — System Status (`admin-ai-system-status`)

Five status cards in a responsive grid:

| Card                             | testid                                     |
| -------------------------------- | ------------------------------------------ |
| AI Gateway (Enabled / Disabled)  | `admin-ai-gateway-status`                  |
| Claude / Anthropic status        | `admin-ai-provider-anthropic`              |
| OpenAI status                    | `admin-ai-provider-openai`                 |
| Google Gemini status             | `admin-ai-provider-google`                 |
| Failover (Enabled / Disabled)    | `admin-ai-failover-status`                 |

Provider tone rules:
- `enabled=true & key_present=true` → **Configured** (emerald)
- `enabled=true & key_present=false` → **Missing key** (amber)
- `enabled=false & key_present=true` → **Globally disabled** (slate)
- otherwise → **Unavailable** (slate)

## 3. Section 2 — Provider Routing (`admin-ai-routing`)

Read-only fields (mono value, muted label):

- Default text provider
- Default text model
- Default vision provider
- Default vision model
- Timeout (ms)
- Max retries
- Resolved selected provider
- Resolved fallback provider

Values sourced from `/api/admin/ai/config/status`. No editing here — a
note in the header directs admins to Emergent Secrets for edits.

## 4. Section 3 — Tenant Selector (`admin-ai-tenants`)

Chip list. Each chip:

- Tenant name (bold), tenant id (mono, dimmed).
- "AI on" / "AI off" state.
- "(default)" suffix when the tenant has no override doc.
- testid: `admin-ai-tenant-btn-{tenant_id}` (e.g. `admin-ai-tenant-btn-masci`).

Active chip: indigo border + tint.

## 5. Section 4 — Tenant AI Enablement (`admin-ai-tenant-toggles`)

Layout:

```
[toggle] AI enabled for this tenant                     [Enabled/Disabled badge]
Master switch. Off → every module for this tenant is off.

┌──────────────────────────────────────┬──────────────────────────────────────┐
│ [t] Daily Report Summary [E/D badge] │ [t] Photo Intelligence [E/D badge]   │
│ [t] PM Intelligence      [E/D badge] │ [t] Admin Intelligence [E/D badge]   │
│ [t] Safety Intelligence  [E/D badge] │ [t] Translation (EN↔ES)[E/D badge]   │
└──────────────────────────────────────┴──────────────────────────────────────┘

Change note (optional):
[   textarea recorded in audit                                              ]

<Discard>              <Save changes>
```

Testids:
- Master switch: `admin-ai-toggle-master`
- Module switches: `admin-ai-toggle-{module}` (e.g. `admin-ai-toggle-photo_intelligence`)
- Note textarea: `admin-ai-change-note`
- Discard: `admin-ai-discard`
- Save: `admin-ai-save`

Behavior:
- Toggles reflect *effective* state = server overrides + unsaved patch.
- When the master switch is OFF, sub-module toggle rows are greyed
  (opacity 60%). They can still be flipped in the UI (so admins can
  pre-configure), but only the master switch materially matters until
  it's flipped on.
- When a toggle is ON in the UI but the resolver returns
  `enabled=false` for that module, a small amber chip surfaces the
  human-readable reason (e.g. "Deployment flag for this module is off.").
- Save calls `PUT /api/admin/ai/tenants/{id}/capabilities` with only
  the patched fields plus the note. Discard clears both.

## 6. Section 5 — Disabled-Mode Guarantees (`admin-ai-disabled-mode-proof`)

Static list of six always-true invariants with green check icons:

1. Daily Reports submit without AI.
2. ODS spine emits facts without AI.
3. PM & Admin dashboards render deterministic data.
4. PDFs, HR, Safety, Equipment, Photos untouched by AI state.
5. Field UI is byte-identical whether AI is on or off.
6. Provider API keys never appear in this UI.

## 7. Section 6 — Audit Log (`admin-ai-audit-log`)

Newest-first list. Each entry (`admin-ai-audit-entry-{i}`):

- Timestamp (mono, dimmed).
- Actor (bold).
- Changed-field chips (mono/caps).
- Optional italic note.

Empty state: "No recorded changes yet."

## 8. Loading / error states

- Global loading: `<Loader2 />` spinner + "Loading AI configuration…"
  while first fetches are outstanding.
- Failed fetch: toast via `sonner`, no partial state breakage.
- Save failure: toast, patch remains for retry.
- No secrets are ever rendered — even in error paths.

## 9. Accessibility

- All interactive controls have `data-testid` and semantic labels via
  `<Label>` where appropriate.
- Toggle rows use the shadcn `Switch` component for keyboard access.
- Status badges use both colour and an icon to satisfy WCAG colour+shape.

## 10. Design tokens

- Cards: `bg-white border border-slate-200 rounded-md p-5`.
- Section title: `font-display text-lg font-black tracking-tight`.
- Body: `text-sm text-slate-600 leading-relaxed`.
- Muted mono: `font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold`.
- No purple gradients, no emoji.
