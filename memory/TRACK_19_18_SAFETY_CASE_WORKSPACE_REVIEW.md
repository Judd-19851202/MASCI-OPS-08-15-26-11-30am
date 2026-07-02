# Track 19.18 · Safety Case Workspace Review

**Status:** 🟢 Elite · fits VP-of-Ops standard

## Header

**Before:** Type · state chip · location · job · reporter · days-open.  
**After:** Same, plus an always-visible one-paragraph **Case Story** ("On {date}, a {type} was reported at {location} ({job}). Reported by {reporter · role}. {short narrative}") and a Next-Action chip when a blocker exists — clickable, jumps to the resolving tab.

**Effect:** A new Safety Director opening a case for the first time can answer "what happened / where / when / who / what's next" without touching a tab.

## Timeline

**Before:** Flat list of cards. No visual chronology beyond the sort order.  
**After:** Ordered list with a vertical spine (before-pseudo-element bar) and colored dots keyed to event kind — Safety and Executives see the story flow at a glance.

Color legend:
- **Slate** — state change / closed / submitted
- **Blue** — evidence / photo
- **Purple** — witness / statement
- **Red** — medical / agency / police
- **Emerald** — CAPA / corrective / verified
- **Amber** — communications / notifications

## Blockers

**Before:** Static list under Case Health with an alert icon.  
**After:** Every blocker is a button. Clicking it advances the workspace to the tab that resolves it (`missing_root_cause` → RCA, `no_photos` → Evidence, `no_witnesses` → Witnesses, etc.).

## Executive Snapshot

**Before:** Key/value grid leading with "Incident: ...".  
**After:** Big one-liner headline first — "Ready for closeout · 82%" / "Under investigation · 55%" / "Early — evidence gathering · 22%" — with the KV grid below and empty values dropped.

## Empty-State Elimination

The Case Health count grid now filters to non-zero entries only. If a case has no medical entries, no agency contacts, and no linked records, those cells simply do not render — no "0" spam.

## Regression Guard

`/app/backend/tests/test_track_19_18_safety_case_workspace.py` locks:
- `composeCaseStory` helper exists
- `data-testid="case-header-story"` renders
- `data-testid="case-header-next-action"` renders when a blocker exists
- `BLOCKER_TAB` mapping covers the standard blocker keys
- `jumpToBlocker` wires `setTab`
- Timeline is an `<ol>` with a `before:absolute` spine + `_timelineDotColor` helper
- `data-testid="case-exec-snapshot-headline"` present
- Health-counts filter removes zeros

## Acceptance vs. 5-Minute Executive Review

| Question | Answer time |
|---|---|
| VP: "What happened?" | < 5 seconds (Case Story paragraph in header) |
| Safety Director: "What's my next step?" | < 5 seconds (Next Action chip, one tap) |
| Executive: "Is this ready for closeout?" | < 5 seconds (one-liner headline) |
| Attorney: "Reconstruct chronology" | < 60 seconds (timeline spine + narrative rows in PDF) |
| OSHA: "Show me evidence" | < 30 seconds (Evidence tab, or PDF Evidence Index) |
