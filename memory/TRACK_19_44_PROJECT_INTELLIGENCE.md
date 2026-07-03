# TRACK 19.44 · Project Intelligence Digest

**Status:** 🟢 IMPLEMENTED (from CONTRACT_REGISTERED).
**Product ID:** `project_intelligence`.
**Gate:** `admin_only`.

## 14 sections

1. Executive Summary — active projects · daily reports (7d) · missing/overdue DRs · project incidents (7d) · HIGH-attention cases · open constraints.
2. Operational Intelligence Score.
3. Trend Direction — HIGH-attention headline metric.
4. Top Wins — daily-report cadence · photo activity · zero incidents.
5. Needs Immediate Attention — HIGH cases · missing reports · aging constraints · project incidents.
6. Top 5 · Projects by Incident Volume (7d) with `/pm/projects/{job_number}` deep link.
7. Core Metrics — job photos · aging constraints · portfolio open POs.
8. Trend Table — not-applicable this run.
9. Recommendations — executive review · chase reports · resolve constraints · address incidents.
10. Upcoming Risks — reserved.
11. Recent Changes — DR + photo + incident cadence.
12. Deep Links — `/pm/projects`, `/pm/daily`, `/pm/photos`, `/safety/cases`, `/pm/constraints`.
13. No-Auto-Decision Notice — PMs + Ops + Safety own investigation.
14. Audit Footer.

## Insufficient-data guard

Returns CRITICAL + `insufficient_data` when zero project signals populated.

## Non-goals

- Does NOT declare projects on-time / off-track (only schedule system can).
- Does NOT assign blame.
- Does NOT determine fault.
- Does NOT infer financial overrun beyond what underlying systems record.
