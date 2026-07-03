# TRACK 19.39 · MORNING SAFETY INTELLIGENCE DIGEST

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillar: 58/60 · Production Strong · Zero-Drift**
**Anchor:** `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md` · `TRACK_19_37_PASSIVE_INCIDENT_PRESENCE_SCORING.md` · `TRACK_19_38_CROSS_PORTAL_READ_FANOUT.md`

## Charter
Turn the certified incident intelligence (Track 19.36 model + Track 19.37 scorer + Track 19.38 portfolio aggregator) into a controlled, opt-in Monday-morning email digest. Zero new decisions. Zero new email provider. Zero new scoring logic.

## What shipped
- `backend/incident_engine/morning_digest.py` — digest generator (composes from the aggregator) + recipient CRUD helpers + `send_digest(dry_run=…)` + `render_html`.
- `backend/incident_engine/morning_digest_routes.py` — 5 additive Safety+Admin endpoints.
- **Two new Mongo collections** (additive only):
  - `morning_digest_recipients` — `id · email · display_name · role_label · active · digest_type · created_at · updated_at · added_by · notes`.
  - `morning_digest_audit` — `id · dry_run · generated_at · generated_by · digest_window_days · subject · top_case_count · recipient_count · recipients · send_status · delivery`.
- **Seed defaults on first read**: Jaymn (`jaymn.judd@mascigc.com`) + Safety placeholder (`safety@mascigc.com` · admin should replace via API). Configurable via `MORNING_DIGEST_DEFAULT_RECIPIENTS` env variable (`email|display_name|role_label` · comma-separated).

## Endpoints
| Method | Route | Gate | Purpose |
|---|---|---|---|
| GET | `/api/incident-intelligence/morning-digest/preview` | Safety+Admin | HTML preview (no send) |
| GET | `/api/incident-intelligence/morning-digest/preview.json` | Safety+Admin | JSON preview |
| POST | `/api/incident-intelligence/morning-digest/send?dry_run=true\|false` | Safety+Admin | Compose + (optional) send |
| GET | `/api/incident-intelligence/morning-digest/recipients?active_only=true\|false` | Safety+Admin | List |
| POST | `/api/incident-intelligence/morning-digest/recipients` | Safety+Admin | Add |
| PATCH | `/api/incident-intelligence/morning-digest/recipients/{id}` | Safety+Admin | Update (`active` toggle · notes · display_name) |

## Digest sections
1. **Executive Summary** — total open · high-attention · opened last 7 days · closed last 7 days · overdue CAPAs · avg readiness · oldest open case.
2. **Top Attention Cases** — top 5 by `attention_score` DESC. Each row: case number · project · type · attention level+score · days open · readiness band · open CAPAs · top firing signal + rationale · deep-link.
3. **Needs Attention Today** — counts for evidence gaps · overdue CAPAs · delayed closeout · executive review needed.
4. **Portfolio Trends** — count of open cases per incident type.
5. **No-Auto-Decision Notice** (verbatim).

## Zero-drift protection
- No new email provider — uses existing `fsi_send_email` from `backend/lib/fsi_email_sender.py`.
- Additive collections only · never mutates existing case/CAPA/evidence/task/audit collections.
- No changes to existing routes.
- Same Safety+Admin gate as write-side Safety-Admin surfaces — no permission widened.

## Rollback
1. Delete `backend/incident_engine/morning_digest.py` and `morning_digest_routes.py`.
2. Remove `_register_ie_morning_digest_routes(…)` block in `server.py`.
3. (Optional) `db.morning_digest_recipients.drop()` and `db.morning_digest_audit.drop()`. These are additive collections; leaving them in place breaks nothing.

**Rollback confidence:** HIGH.
