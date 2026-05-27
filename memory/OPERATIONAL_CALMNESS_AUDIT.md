# Operational Calmness Audit
## Phase TRUST-1 · 2026-05-27

> Calm beats clever. The platform must sound industrial, not
> marketing. It must use color and signal sparingly. It must avoid
> surveillance voice. This audit verifies and lists residual risk.

---

## 1 · Language voice

Status by surface:

| Surface | Voice | Status |
|---|---|---|
| Autosave pill (`DraftStatusPill`) | Industrial · relative time | ✅ iter440/442 phrasebook locked |
| Draft restore prompt | Calm · operator-language | ✅ |
| Crew-memory restore prompt | Confidence-tiered · soft offer | ✅ iter442 |
| Coaching language overall | Phrase book + banned list + regex test | ✅ regression-tested |
| Spanish localization of new strings | Not yet translated | 🟧 TF-007 |

Banned phrases (regression-tested):
- "we identified you" · "we are learning" · "personalized for you"
- "we know you" · "tracking" · "behavior"
- "ai" / "profile" (as standalone words)

---

## 2 · Visual signal discipline

| Pattern | Status |
|---|---|
| Red reserved for actionable urgency | ⚠ Drift observed on IncidentsDashboard (TF-014) |
| OSHA Recordable chip in red | ⚠ visually competes with severity badge |
| Animation: only on user action (refresh spin, toast slide) | ✅ |
| Sound: never | ✅ |
| Modals: only for genuinely destructive actions | ✅ (Discard is soft-delete · no confirm) |
| Toasts auto-dismiss > 3s for important messages | ✅ |
| Visual loudness gate | ✅ `diff_doctrine_baseline.py` + `pre_deploy_check.sh` |

---

## 3 · Information density

The Daily Report header now carries:
- MASCI logo (left)
- Back link (`← <context>`)
- Edit Project button
- Delete button
- Email Report dialog launcher
- Print Report dialog launcher
- Submit Language badge
- Autosave pill (when editing)

This is within calm density. Not overloaded.

Governance page header:
- Convergence banner
- Draft Health tile (new iter442)
- Severity strip
- Doctrine cards

Acceptable.

---

## 4 · Coaching tone (per iter442)

Confidence-tiered banner copy:

| Confidence | Title |
|---|---|
| low/medium | "Recent crew and equipment may preload to speed up daily reporting." |
| high (≥5 uses) | "Loaded from recent reports on this iPad." |

Subtitle: "Saved setups stay only on this device."

Footer: "You can edit crew and equipment after loading. Starting blank will not erase previously submitted reports."

Voice: industrial, factual, no celebration, no surveillance.

---

## 5 · Destructive-action ergonomics

| Action | UX |
|---|---|
| Discard draft | Soft-delete to 24h archive · no confirm needed |
| Clear saved setup | One-tap clears the device memory · no confirm |
| Delete incident record | Confirm dialog (existing) |
| Delete daily report | Confirm dialog (existing) |
| Change project / foreman (iter442) | One-tap, clears project + foreman fields · keeps crew memory |
| Submit | One-tap, goes through autosave + queue path |

Confirm dialogs are reserved for genuinely irreversible operations.

---

## 6 · Toast inflation risk

Today's toast catalog (rough):
- "Saved · will upload when reconnected" (offline)
- "Submitted" (online)
- "Loaded from recent reports on this iPad." (use setup)
- "Pick a project · crew and equipment can preload after." (change project)
- Error toasts: localized + truthful

No toast spam observed. Each event produces one toast, max.

---

## 7 · Open calmness findings

| ID | Sev | What |
|---|---|---|
| TF-007 | T1 | Spanish localization gap for new coaching copy |
| TF-014 | T1 | Severity badge / OSHA chip red-fatigue risk on busy IncidentsDashboard |

---

## 8 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Calmness doctrine holds · 2 open backlog finds
- **Cross-refs:** `DAILY_REPORT_COACHING_LANGUAGE.md`, `DAILY_REPORT_DEVICE_MEMORY_MODEL.md`, visual doctrine baseline in `/app/scripts/diff_doctrine_baseline.py`
