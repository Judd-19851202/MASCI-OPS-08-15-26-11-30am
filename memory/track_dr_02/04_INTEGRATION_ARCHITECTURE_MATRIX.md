# Integration Architecture Matrix

Date: 2026-07-14
Track: DR-02

| Integration | Current repository-backed interaction | Impact | Risk | Root cause if drifted | Canonical solution | Migration strategy | Regression tests required |
|---|---|---|---|---|---|---|---|
| PM Command Center | Reads pending review Daily Reports from `db.daily_reports` | PM review flow | Medium | shell/lifecycle drift changes queue visibility | one lifecycle state contract | align all submissions to same lifecycle fields | pending-review queue tests |
| HR Time Verification | derives payroll/time rows from `masci_crews` in `daily_reports` | payroll reconciliation | High | crew shape drift across shells | one canonical crew row contract | normalize field payloads before submit | hourly row parity tests |
| Safety Portal | read-only flagged Daily Report stream | safety oversight | Medium | safety fields missing/inconsistent by shell | one safety field contract | keep submit contract identical | flagged DR list tests |
| Field Leadership Portal | read-only recent Daily Report visibility | crew continuity oversight | Medium | inconsistent summary field / read model | one read model | keep projections additive | FL list regression |
| Search / doc-id lookup | global search and doc-id lookup resolve Daily Reports | discoverability | Medium | competing identity/read families | one canonical identity | unify source identity | global search and doc-id tests |
| ODS ingest | V1 and V2 emit different source types to ODS | intelligence / briefs | High | duplicate source families | one Daily Report semantic fact contract | preserve lineage, unify semantics | ODS fact parity tests |
| PM brief / executive brief | consume ODS facts, not raw docs | leadership visibility | High | summary/ODS drift | Daily Report contributes only through ODS | unify accepted summary + ODS emission | brief content provenance tests |
| Admin daily roll-up | reads `daily_reports` directly via rollup module | exec/admin analytics | Medium | field contract drift changes totals | one canonical `daily_reports` shape | keep rollup aligned to final contract | roll-up invariants |
| PDF | one alias, multiple backing sources | legal/ops record | High | duplicate source models and summary fields | one PDF contract | redirect legacy routes to canonical source model | PDF parity tests |
| CSV export | reads canonical `daily_reports` | downstream review/export | Medium | competing record families | one export source | deprecate non-canonical export paths | CSV shape tests |
| Notifications | submit email + lifecycle bell fanout + kickback email | operator awareness | High | stage ownership split | event-driven lifecycle notifications | move all triggers to lifecycle authority | notification event tests |
| Trust Spine | lifecycle event chain for `daily-report` | trust/audit proof | High | multi-path workflows skip stages | one canonical lifecycle emitter | standardize stage emission across record journey | trust stage completeness tests |
| Attachments/evidence | upload → manifest/extraction → PDF/evidence use | proof/audit/AI | High | attachment paths not tied to one evidence chain | one evidence architecture | keep photos/docs distinct but one manifest | evidence manifest tests |
| Equipment suggestions | read-only detection API for equipment on project/date | productivity | Low-Med | suggestion path disconnected from canonical shell | keep as suggestion-only integration | wire to canonical shell or omit | equipment suggestion non-mutating tests |
| Scheduling | signal-only flags and notes | PM awareness | Medium | accidental mutation or inconsistent signal fields | keep DR signal-only | preserve no-direct-scheduling doctrine | no-direct-schedule mutation tests |
| Weekly reconciliation | **UNKNOWN dedicated module** | Unknown | Unknown | business term not mapped to one repo subsystem | mark UNKNOWN until evidence identifies a single owner | require explicit mapping | mapping/spec test once defined |
