# Daily Report · Device Memory Model
## iter442 · Field-Trust Doctrine · 2026-05-27

> What the iPad remembers. What it does not remember. How confidence
> is accrued. How the operator stays in control.
>
> **This is NOT login.** Not passwords. Not keys. Not accounts.
> Not authentication. The device may **suggest** context. The
> device must **never** silently hard-lock identity.

---

## 1 · Doctrine

| Principle | What it means |
|---|---|
| **No accounts** | Device memory is anonymous. It never proves who someone is. |
| **No passwords** | The memory is unlocked by being on the device. That is all. |
| **No distributed keys** | Nothing is synced. Nothing is shared. Nothing leaves the iPad. |
| **No portal login requirement** | Foremen on the public `/daily/submit` link have full access to device memory. |
| **device_id may SUGGEST context** | Yes — preload crew, equipment, foreman name, project. |
| **device_id MUST NOT silently hard-lock identity** | Every reuse is operator-confirmed. The operator can always Start Blank. |
| **If confidence is low, ask minimal setup questions** | First-time on this device → no preload banner · normal blank form. |
| **If project changes, confirm before reusing crew/equipment** | The "Use Setup" button surfaces a confirmation when the current project differs from the snapshot's project. |

---

## 2 · What is remembered

Stored in `localStorage` at key `masci.crew-memory.daily-report.v1`:

```js
{
  schemaVersion: 1,
  nickname: "Paving Crew A",           // optional operator-set label
  prepared_by: "J. Doe",               // foreman name
  superintendent: "S. Smith",
  project_name: "Test Yard",
  project_number: "P-999",             // confidence key (see §4)
  masci_crews:    [{name, trade, ...}],
  subcontractors: [{name, ...}],
  equipment:      [{description, ...}],
  savedAt:        1748381234123,
  lastUsedAt:     1748381234123,
  firstSeenAt:    1748000000000,       // first-save timestamp (confidence)
  usageCount:     5                     // confidence proxy (see §4)
}
```

### What is NEVER remembered

| Field | Why not |
|---|---|
| Narrative text · weather notes · incident descriptions | Per-day content, not setup |
| Photos (any form) | iOS quota constraint AND privacy |
| GPS coordinates | Privacy |
| Signatures | Legal-evidentiary; per-event only |
| Operator login state | Device memory is anonymous by construction |
| Server credentials, tokens, keys | None — device memory is purely client-side |
| Any field outside the schema in §2 above | The store re-strips on every write (`extractSetupSnapshot`) |

---

## 3 · Visibility surface

The operator always knows what is remembered:

1. **Preload banner** on `/daily/submit`:
   - Low/no confidence → no banner (just blank form)
   - Medium confidence (`usageCount ≥ 2`) → "Recent crew and equipment may preload to speed up daily reporting."
   - High confidence (`usageCount ≥ 5`) → "Loaded from recent reports on this iPad."

2. **Operator buttons** on the banner:
   - **Use Setup** — apply the snapshot (with project-change confirm if applicable)
   - **Change project / foreman** — clear project + foreman fields; keep crew memory available
   - **Start Blank** — dismiss banner; do not apply
   - **Clear Saved Setup** — delete the memory entirely

3. **Load-trace line** below the banner after Use Setup:
   *"Loaded from recent reports on this iPad."* — a quiet
   acknowledgement, never a celebration.

4. **No surveillance language.** Banned phrasing: "we identified
   you", "we are learning your patterns", "personalized for you",
   "AI", "tracking", "profile", "behavior". (Tested by
   `test_crew_setup_prompt_uses_calm_coaching_copy`.)

---

## 4 · Confidence accrual

Confidence is a **proxy for trust**, not a security token. It only
controls **the banner text** and whether preload is offered.

| usageCount | Level | Banner | What happens |
|---|---|---|---|
| 0 | **none** | (no banner) | First time on device. Blank form. No suggestion. |
| 1 | **low** | "Recent crew and equipment may preload…" | Soft offer · operator must tap Use Setup |
| 2–4 | **medium** | "Recent crew and equipment may preload…" | Same offer · same explicit consent |
| ≥ 5 | **high** | "Loaded from recent reports on this iPad." | Same offer · slightly more affirmative copy |

Accrual rule (in `saveCrewSetup`):

```
On saveCrewSetup({project_number: P, ...}):
  if existing snapshot.project_number === P:
    usageCount += 1
    firstSeenAt = existing.firstSeenAt (preserved)
  else:
    usageCount = 1 (reset)
    firstSeenAt = now()
```

**Project change resets accrual.** This is intentional — the iPad
should not carry "5 successful submissions" trust from a closed-out
job into a new job. Each new project starts fresh.

---

## 5 · Project-change guard

Defined in `lib/crewMemory.js::isProjectChange(snapshot, current)`:

```
if !snapshot.project_number → false (nothing to compare)
if !current → false (operator hasn't picked yet)
return snapshot.project_number !== current
```

Used in `NewDailyReport.jsx::onUseCrewSetup`:

```
const current = data.project_number?.trim()
if (current && isProjectChange(crewSetup, current)):
  if !window.confirm("This setup is from a different project. Reuse crew and equipment anyway?"):
    return
apply snapshot
```

This is the one place where the device memory **explicitly asks
permission** to apply across a project boundary. Doctrine compliant.

---

## 6 · Shared-device safety

What happens when two crews share one iPad:

| Scenario | Behavior |
|---|---|
| Crew A submits Monday under P-100 | Memory saved · usageCount=1 · projectNumber=P-100 |
| Crew B starts Tuesday under P-200 | Banner offers Crew A's setup |
| Crew B taps Use Setup | Project-change confirm fires; Crew B can decline |
| Crew B taps Change project / foreman | Project + foreman fields cleared; crew memory preserved (Crew A can come back tomorrow) |
| Crew B taps Start Blank | Banner dismissed for this session; memory preserved |
| Crew B taps Clear Saved Setup | Memory wiped; both crews lose preload |

**No accounts. No passwords. No way for Crew A to "stay logged in"
because there is no login.** The device merely remembers a
suggestion.

---

## 7 · Lifecycle

| Trigger | Effect |
|---|---|
| Successful daily-report submit | `saveCrewSetup` called with the submitted form's setup fields |
| Mount `/daily/submit` | `loadCrewSetup` runs · banner shown only if record exists & not stale |
| TTL 30 days | Stale records auto-purged on next load (see `lib/crewMemory.js::TTL_MS`) |
| Operator taps Clear | `clearCrewSetup` wipes the slot |
| Operator submits new project | usageCount resets to 1 |
| Schema version mismatch | Record is discarded (forward-compat: never crash on v2 reading v1) |

---

## 8 · Telemetry interaction

Device memory events are **NOT** logged to `/api/draft-telemetry`.

Rationale: the draft-telemetry collection is for **draft I/O
failures** (the P0 incident). Device memory is operator-facing UX
and never fails in a way that matters at scale. The lifecycle is
entirely local.

If a future scale-out is needed (e.g., admin Draft Health tile
shows "% of devices using memory preload"), the contract for
adding it is:
- emit `device_memory.applied`, `device_memory.declined`,
  `device_memory.cleared` events via `emitDraftEvent`
- meta carries `usageCount`, `confidenceLevel`, `isProjectChange`
- **never** carries snapshot content

---

## 9 · Acceptance Criteria

| # | Criterion | Verified |
|---|---|---|
| 1 | localStorage key is `masci.crew-memory.daily-report.v1` | manual code-grep |
| 2 | Snapshot never persists banned fields | `extractSetupSnapshot` unit-tested in iter437 |
| 3 | usageCount increments on same-project resave | `test_crew_memory_confidence_accrual` |
| 4 | usageCount resets on project change | same |
| 5 | "Change project / foreman" button present at medium+ confidence | `test_change_project_button_present` |
| 6 | Banner copy is calm + non-surveillance | `test_crew_setup_prompt_uses_calm_coaching_copy` |
| 7 | TTL 30d auto-purge | iter437 spec — unchanged |

---

## 10 · Sign-off

- **Author:** E1 · iter442 P0/P1 field-trust pass
- **Status:** 🟢 Doctrine locked · code in preview · operator-confirmed flow
- **Cross-refs:** `DAILY_REPORT_COACHING_LANGUAGE.md`,
  `DAILY_REPORT_FIELD_TRUST_REVIEW.md`,
  `DRAFT_HEALTH_TILE_CERTIFICATION.md`
