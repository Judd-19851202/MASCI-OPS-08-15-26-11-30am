# ODR Adoption Observation Plan

_Phase V.1 · M0.3 · 2026-05-29 · ADOPTION TELEMETRY · NEVER PERFORMANCE SCORING._

## Purpose

Track **operator adoption** of the ODR system — answer
"are people actually using this the way it was designed to be used?"
without ever drifting into individual performance surveillance.

> Adoption telemetry ≠ scoring. Aggregates only. Never per-foreman.

## What is observed

### Foreman entry (`surface: "foreman"`)

| Signal | Captured | Used for |
|---|---|---|
| Session start | `session_start` | Mobile vs desktop usage |
| Section visited | `section_visited` | Where foremen pause |
| Section completed | `section_completed` | Funnel completion |
| Language toggled | `language_toggled` | Bilingual demand |
| Photo added | `photo_added` | Photo-first adoption |
| Voice caption used | `voice_caption_used` | Voice tool engagement |
| Autosave triggered | `autosave_triggered` | Offline-tolerance |
| Submit success | `submit_success` (+ `duration_ms`) | Average completion duration |
| Submit blocked | `submit_blocked` (+ hard_stop counts) | Hard-stop friction |
| Abandoned | `abandoned` | Abandonment rate |
| Coaching expanded | `coaching_expanded` | Coaching engagement |
| Draft resumed | `draft_resumed` | Offline durability |

### FL ODR Center (`surface: "fl_center"`)

| Signal | Used for |
|---|---|
| `fl_inbox_opened` | Daily superintendent visits |
| `fl_record_opened` | Review frequency |
| `amendment_routed` | Amendment routing volume |
| `amendment_approved` | Amendment approval volume |
| `constraint_link_visited` | Cross-substrate utility |
| `chronology_opened` | Chronology consumption |
| `readiness_signal_clicked` | Readiness usefulness |

### PM Panel (`surface: "pm_panel"`)

| Signal | Used for |
|---|---|
| `pm_panel_opened` | PM consumption frequency |
| `pm_project_opened` | Per-project drill-down rate |
| `pm_blocker_opened` | Blocker visibility usefulness |
| `pm_trend_inspected` | Trend usefulness |
| `pm_pdf_downloaded` | PDF reliance for status / cost |

### Public viewer (`surface: "public_viewer"`)

| Signal | Used for |
|---|---|
| `public_viewer_opened` | External audience engagement (CEI / DOT / FAA) |
| `public_pdf_downloaded` | External PDF reliance |

### System-wide

| Signal | Used for |
|---|---|
| `pdf_rendered` | PDF generation frequency |
| `trust_banner_shown` / `_dismissed` | Banner non-intrusiveness validation |
| `device_kind_detected` | Mobile vs desktop split |

## What is NEVER observed

- ❌ Free-text body of any ODR field
- ❌ Coaching content actually read
- ❌ Foreman names (only sha256 hash for support · NEVER exposed in API)
- ❌ Per-foreman counts in aggregates
- ❌ Per-record evaluation
- ❌ "Top 5 slowest foremen" or any ranking
- ❌ Hours-worked correlation with submit time
- ❌ Coaching-prompt acceptance per foreman

## Doctrine commitments

| Commitment | How |
|---|---|
| **Aggregates only** | `/api/odr/observation/summary` returns counts, not lists |
| **No PII in surface** | Response omits `actor_uid_hash` |
| **Closed-set kinds** | `ALLOWED_KINDS` set guards every event write |
| **Closed-set surfaces** | `ALLOWED_SURFACES` set guards every event write |
| **Fire-and-forget client** | `logObservation()` swallows all errors; never blocks UI |
| **Append-only** | No DELETE / UPDATE route on `odr_observation_events` |
| **Index strategy** | `at_utc · surface · kind` — supports time-window aggregates only |
| **Admin-only summary** | Summary endpoint requires `require_admin` |

## Aggregates produced by `/api/odr/observation/summary?days=N`

```
{
  "window_days": N,
  "total_events": int,
  "unique_foreman_sessions": int,  ← cardinality of uid_hash
  "by_surface": { surface: count, ... },
  "by_kind": { kind: count, ... },
  "by_device": { phone | tablet | desktop : count },
  "by_language": { en | es : count },
  "average_submit_duration_s": float | null,
  "photos_added_count": int,
  "coaching_engagement_count": int,
  "amendment_volume": int,
  "public_pdf_downloads": int,
  "pdf_render_count": int,
}
```

## Adoption health questions answered

| Operator question | Signal |
|---|---|
| Is the field actually using mobile? | `by_device.phone / by_device.desktop` |
| Are we ready to ship Spanish curriculum? | `by_language.es / total_events` |
| Is the coaching helpful? | `coaching_engagement_count / submit_success` |
| Are we drowning in amendments? | `amendment_volume / submitted_count` |
| Are public viewers actually using the link? | `public_pdf_downloads / public_viewer_opened` |
| Did the trust banner help or get dismissed instantly? | `trust_banner_dismissed / trust_banner_shown` |

## Out of scope (intentional)

- ❌ Per-project leaderboards
- ❌ Per-foreman "submitted on time" badges
- ❌ Time-to-submit competitive surfacing
- ❌ Coaching acceptance correlated with later amendments

These would convert the platform into a surveillance tool and erode
the field-first trust the OGC catalog tone deliberately builds.

## Verdict

🟢 **ADOPTION OBSERVATION PLAN LOCKED.** Telemetry exists to answer
adoption questions, not to evaluate people. The platform learns
from aggregates. The field stays trusted.
