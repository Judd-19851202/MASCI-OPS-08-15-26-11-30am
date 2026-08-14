# WAVE 5 — KPI FORMULA / DENOMINATOR RECONCILIATION (canonical concept register)

Goal (owner): same concept + same scope => one canonical calculation. Different
legitimate scopes must be explicitly named and governed. Reconcile highest
blast-radius shared KPI concepts first across the 547 truth surfaces.

Durable artifacts:
- scripts/wave5_kpi_concept_scan.py — discovers + ranks KPI compute sites by blast radius.
- memory/truth_program/WAVE5_KPI_CONCEPTS.json — per-concept compute sites (backend + frontend).

## BLAST-RADIUS RANKING (reconcile top-down)
| Rank | Concept ID | Distinct files | Compute sites | BE | FE |
|---|---|---|---|---|---|
| 1 | KPI-PERCENT-COMPLETE | 27 | 84 | 64 | 20 |
| 2 | KPI-EXPIRING-RATE | 29 | 50 | 12 | 38 |
| 3 | KPI-UTILIZATION | 22 | 45 | 19 | 26 |
| 4 | KPI-VARIANCE-PERCENT | 7 | 22 | 19 | 3 |
| 5 | KPI-HEALTH-SCORE | 7 | 13 | 2 | 11 |
| 6 | KPI-EFFICIENCY-PERCENT | 5 | 16 | 15 | 1 |
| 7 | KPI-AVG-DAYS | 2 | 4 | 1 | 3 |
| 8 | KPI-COMPLIANCE-RATE | 1 | 3 | 0 | 3 |
| 9 | KPI-OWNERSHIP-SCORE | 1 | 2 | 2 | 0 | (already reconciled — SO-07/TD-0006) |
| 10 | KPI-ELIGIBILITY-RATE | 1 | 2 | 2 | 0 |

## RECONCILIATION METHOD (per concept)
1. Enumerate every compute site (from WAVE5_KPI_CONCEPTS.json.concepts[<id>].sites).
2. Extract the exact formula (numerator / denominator / rounding / clamp) at each site.
3. Determine the intended SCOPE per site (project / fleet / employee / portfolio / window).
4. Group by (concept, scope). Within a group, all formulas MUST match a single canonical form.
5. If they diverge: pick the truthful canonical form, route all consumers through one shared
   helper (backend) / one util (frontend), preserve legitimate distinct scopes under explicit names.
6. Add a guard test asserting the canonical formula + denominator (esp. divide-by-zero / empty-set).

## STATUS
- Register + ranking: DONE (this session).
- Reconciliation: NOT STARTED (next: KPI-PERCENT-COMPLETE — highest blast radius, backend-heavy 64 sites).
- Note: KPI-OWNERSHIP-SCORE already canonicalized in Wave 2 (SO-07/TD-0006 attributable denominator, GD-0007).
