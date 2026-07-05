# DR-ROI-001D · Photo Linking UI

## Panel: `Photo Evidence` (right-side sticky, DR-V2 shell)

Renders **without** any AI branding:

- **Photo strip** — small numbered chips at the top, one per photo in `draft.photos[]`; clicking selects the target photo.
- **Detected** — up to 6 observations (`{label, category, confidence}`) rendered as a compact list. Confidence is a % badge, never a model score.
- **Suggested links** — chips with `target_type + target_label`. Each row has **Accept** / **Dismiss** buttons while `status="suggested"`. After decision, chip shows `ACCEPTED` in emerald or `DISMISSED` in muted gray.
- **Items to verify** — capped at 3 top questions, amber card. Each row offers **Confirm** / **Not applicable**.

## What is NOT rendered

- No model name.
- No provider name.
- No token count.
- No dollar cost.
- No raw JSON.
- No "AI Agent" label.
- No mention of Claude / GPT / Gemini.

## Data flow

- Panel component: `frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx`.
- API client: `frontend/src/lib/drV2Api.js` (fetch/analyze/accept/dismiss/resolve).
- Panel reads `draft.photos[]` from the shell and fetches per-photo intel via `GET /api/dr-v2/photos/{id}/intelligence`.
- Accept/dismiss/resolve calls flow to the corresponding `/photos/*` endpoint; the response includes the fresh intel doc so the panel updates in-place.
