# TRACK 19.44 · Training Intelligence Digest

**Status:** 🟢 IMPLEMENTED (from CONTRACT_REGISTERED).
**Product ID:** `training_intelligence`.
**Gate:** `admin_only`.

## 14 sections

1. Executive Summary — active employees · completions (7d) · total records · expired certs · expiring 30d · missing records.
2. Operational Intelligence Score.
3. Trend Direction — expired-cert headline metric.
4. Top Wins — completions activity · all quals current · meeting attendance.
5. Needs Immediate Attention — expired certs · expiring 30d · missing records · pending approvals.
6. Top 5 · Expired Certifications (employee · cert type · expired on).
7. Core Metrics — meetings held · pending approvals · expiring 60d.
8. Trend Table — not-applicable this run.
9. Recommendations — renew · schedule · chase · clear approvals.
10. Upcoming Risks — 30d / 60d expiring cert windows.
11. Recent Changes — completions + meetings volume.
12. Deep Links — `/hr/training-records`, `/hr/employees`, `/meetings`, `/hr/historical-records/queue`.
13. No-Auto-Decision Notice — HR + Safety own investigation.
14. Audit Footer.

## Insufficient-data guard

Returns CRITICAL + `insufficient_data` when zero training signals populated.

## Non-goals

- Does NOT determine discipline, employment eligibility, OSHA recordability, or legal compliance.
- Only surfaces gaps · owners decide.
