# TRACK 19.47 · History + Audit UI

## History drawer
- Trigger — "History" button on any product card.
- Backend — `GET /api/operational-intelligence/history?product_id={id}&limit=25`.
- Rendering — table with columns: Generated · Period · Score · Attention · Trend · Confidence · By.
- Empty state — "No history rows recorded yet for this product." (no fake data).
- Cost — the list endpoint strips `rendered_html`, so 25 rows fit inside a normal HTTP payload.

## History detail (deep-dive)
Not surfaced in the drawer yet — the summary + list is enough for the
"what happened last week" answer. If a future track needs the full
digest HTML, the frontend can call `GET /history/{id}?include_html=true`
directly.

## Audit drawer
- Trigger — "Audit" button on any product card.
- Backend — `GET /api/operational-intelligence/audit?product_id={id}&limit=25`.
- Rendering — table with columns: At · Event · Actor · Status · Recipients · Dedupe.
- Empty state — "No audit rows recorded yet for this product." (no fake data).
- Sensitive-field posture — the backend strips `token` / `secret` /
  `password` / `api_key` payload keys defensively; the frontend then
  only renders a small allow-list of columns (send_status,
  recipient_count, dedupe_key). Even a hostile payload cannot leak
  through the UI.

## Zero drift
- No new history collection.
- No new audit collection.
- No client-side history/audit state persistence.
- No pagination "load more" (25-row window is sufficient for the
  Cockpit's monday-morning use case). If needed, expand later.

## Six-Pillar audit
Every column earns its place:
- **Generated / At** — chronology, always required.
- **Score / Attention / Trend** — the "what mattered" columns.
- **By / Actor** — accountability.
- **Status / Recipients** — dispatch outcome + fan-out size.
- **Dedupe** — proves the shared dedupe engine fired (or didn't).
