# DR-ROI-001D · Backward Compatibility

| Surface | Proof |
| --- | --- |
| V1 daily report POST / GET | still 200 · route unchanged |
| V1 photo upload | untouched · Job Photos mirror routes unchanged |
| V1 minimum 6-photo requirement | unchanged (validator untouched) |
| V1 PDF generation | untouched · no read/write to daily_reports fields |
| V1 email routing | untouched · no import of email sender |
| Job Photos mirror | grepped clean of any `db.job_photos` write from DR-ROI-001D code |
| DR-V2 shell | still renders `dr-v2-shell`; PhotoIntelligencePanel replaces the placeholder without changing test IDs on other panels |
| DR-V2 AI synthesis | still returns 3 outputs; provider metadata still audit-only |
| ODS spine emission | unchanged for non-photo fact types; adds `photo_evidence_fact` emission on link accept |
| Route count | 1455 → 1460 (+5 additive `/api/dr-v2/photos/*`) |
| OpenAPI paths | 1277 → 1282 (+5) |
| Method count | 1459 → 1464 (+5) |
| No live emails | `EMAIL_SAFETY_MODE=strict` preserved · no imports of `email_router` |
| Feature flags default OFF | `DR_V2_PHOTO_VISION_ENABLED` default OFF |
| Field UI · Invisible Intelligence | no model names / providers / cost meters visible; verified below |

## Field UI verification checklist

- `PhotoIntelligencePanel.jsx` — contains no `Claude`, `GPT`, `Gemini`, `Anthropic`, `OpenAI`, `Google`, `token`, or `cost` strings.
- Provider/model metadata lives inside the intel doc's audit fields; the panel never renders them.
- Only user-facing labels: "Photo Evidence", "Detected", "Suggested links", "Items to verify", "Accept", "Dismiss", "Confirm", "Not applicable".
