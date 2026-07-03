# TRACK 19.54 · Universal Language

## Attention Vocabulary
Every portal, every card, every strip, every Cockpit tile uses the
same 4-value attention vocabulary. No portal invents its own.

| Level     | Operational meaning        | Colour ramp                          |
|-----------|----------------------------|--------------------------------------|
| CRITICAL  | Immediate action required. | red-100 bg · red-300 border · red-900 text   |
| HIGH      | Address today.             | orange-100 bg · orange-300 border · orange-900 text |
| MEDIUM    | Plan this week.            | amber-100 bg · amber-300 border · amber-900 text |
| LOW       | Healthy.                   | emerald-100 bg · emerald-300 border · emerald-900 text |

Enforced by:
- `AttentionChip.jsx` — the single component every consumer uses.
- Lock test `test_attention_chip_uses_four_universal_levels` — verifies
  each level and its exact hint text are present in the component
  source.

## Trend Vocabulary
Direction leads the number. Humans understand movement before they
scan digits.

| Direction  | Glyph | Label      | Colour  |
|------------|-------|------------|---------|
| up / ▲     | ▲     | Improving  | emerald-700 |
| flat / →   | →     | Stable     | slate-500   |
| down / ▼   | ▼     | Declining  | red-700     |

`TrendChip.jsx` renders `[glyph] [label] [score] [delta%]`.

## Deprecated / retired vocabulary
The following patterns MUST NOT appear on any new operational surface:
- "Investigate" (without a specific object)
- "Monitor" (without a follow-up action)
- "Keep an eye on"
- "Review periodically"
- "Consider evaluating"
- Generic "attention required" without an operational item

Portal-specific attention wording (e.g. "watch list", "flags",
"warnings") should route through `AttentionChip` going forward. This
Track 19.54 introduces the vocabulary; deprecation of legacy wording
across every screen is a follow-up polish item.

## Decision Boundary
Every Guidance Card ends with the immutable statement:

> "This information supports operational decision-making. The platform
> never makes operational decisions."

Enforced by lock test `test_guidance_card_includes_decision_boundary_copy`.
