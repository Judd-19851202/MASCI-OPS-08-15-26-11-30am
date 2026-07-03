# TRACK 19.58 · Evidence Readiness Certification

## Language mandate (strict)
- **Use:** Evidence Readiness · Excellent · Good · Needs Attention · Incomplete · Completed evidence · Outstanding evidence · Missing evidence.
- **Never use:** Chain of Custody · Compliance · OSHA-ready · Court-ready · Litigation-ready · Legally defensible · Complete percentage · Compliance percentage.

## Derivation (adapter-only · zero new backend)
The `evidenceReadiness(health)` pure function in `SafetyIncidentThread.jsx`
maps the certified `health.readiness_level` string plus the certified
`health.blockers[]` count into exactly one of four qualitative buckets:

| Bucket           | Trigger                                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------------------|
| Excellent        | `readiness_level` = "excellent"/"ready"; or unset with zero blockers                                        |
| Good             | `readiness_level` = "good"; or 1 blocker                                                                    |
| Needs Attention  | `readiness_level` = "needs_attention"/"attention"; or 2–3 blockers                                          |
| Incomplete       | Any other case (4+ blockers, or `readiness_level` explicitly `incomplete`)                                  |

## What is rendered
- **Health chip** in Mission — one word, colour-coded via the shell.
- **Mission facts row** — `Evidence Readiness: <bucket>`.
- **Attention section** — each blocker becomes an item (severity, why, owner, due).
- **Action Queue** — up to 3 blocker labels lifted verbatim.

## What is NEVER rendered
- Percentages.
- "Complete" / "Incomplete" fractions.
- Compliance certifications.
- Legal statements.
- OSHA-classification claims.
- Insurance-package readiness claims.

## Zero-drift certification
The `evidenceReadiness` function reads two fields — `readiness_level`
(string) and `blockers.length` (integer) — both already certified by
the Incident Engine's health endpoint. **No new scoring model. No new
compliance engine. No new legal language. No new PDF.**
