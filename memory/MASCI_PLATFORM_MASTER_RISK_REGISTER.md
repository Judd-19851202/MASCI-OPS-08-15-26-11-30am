# MASCI Platform — Master Risk Register (Track 13.4C · Deliverable #8)

**Mode:** documentation only — every major finding scored as a risk.

Schema per row:  
`Risk ID · Description · Category · Impact · Likelihood · Affected Users · Affected Portals · Affected Workflows · Operational Severity · Trust Severity · Safety Severity · White-Label Severity · Status`

Severity & impact scale: 1 low · 2 medium · 3 high · 4 critical.  
Likelihood: 1 unlikely · 2 possible · 3 likely · 4 certain (already happening).  
Status: `observed (Track 13.4B)` for all rows — none yet remediated.

---

## Risk rows (Tier 1 + Tier 2 only)

| Risk ID | Description | Category | Impact | Likelihood | Affected users | Affected portals | Affected workflows | Op | Trust | Safety | WL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RISK-001 | No tenant model in DB or routes | Architecture | 4 | 4 | Customer #2 (future) | all | all | 1 | 3 | 1 | 4 | observed |
| RISK-002 | Hardcoded MASCI legal text in EN+ES safety-form acknowledgements | Legal · White-label | 4 | 4 | Customer #2 employees | Safety Forms | Equipment Issuance | 1 | 3 | 2 | 4 | observed |
| RISK-003 | Production Motive webhook activity unverified | Operational truth | 4 | 3 | dispatchers · PMs · drivers | Dispatch · PM | dispatch assignment · ODR | 4 | 4 | 2 | 1 | observed |
| RISK-004 | 100 of 190 motive-mapped assets without GPS coords | Data integrity | 4 | 4 (current state) | dispatchers · field | Dispatch | dispatch assignment | 4 | 4 | 2 | 1 | observed |
| RISK-005 | 157 assets stale / no-recent position | Data integrity | 3 | 4 | dispatchers | Dispatch | dispatch assignment | 4 | 4 | 1 | 1 | observed |
| RISK-006 | Safety-Critical UI Spanish readiness 75.8 % (100 orphan strings) | Translation · Safety | 3 | 3 | Spanish-speaking crew | Safety · Trench · public forms · HR | JHA · CAPA · trench · safety meeting | 2 | 3 | 4 | 2 | observed |
| RISK-007 | Outbound emails 0 % Spanish | Translation | 3 | 4 | Spanish-speaking crew + supervisors | all | all email-emitting workflows | 2 | 3 | 3 | 2 | observed |
| RISK-008 | Server-rendered PDFs 0 % Spanish | Translation | 3 | 4 | Spanish-speaking crew | all PDF-emitting | training certs · FL records · PM welcome · Safety Forms | 2 | 3 | 3 | 2 | observed |
| RISK-009 | `tokens.css` PROPOSAL — not wired; no retheming layer | Theming · WL | 3 | 4 | engineering · Customer #2 | all | all visual surfaces | 1 | 2 | 1 | 4 | observed |
| RISK-010 | Per-workflow status engines hardcoded (12 engines) | Architecture · WL | 3 | 4 | tenants needing custom statuses | all | all workflows | 1 | 2 | 1 | 4 | observed |
| RISK-011 | No tenant onboarding surface | WL | 3 | 4 | sales · ops | Admin | n/a (none exists) | 1 | 2 | 1 | 4 | observed |
| RISK-012 | 497 source files reference "MASCI" | Branding · WL | 3 | 4 | Customer #2 | all | all | 1 | 2 | 1 | 4 | observed |
| RISK-013 | Hardcoded recipient emails (`safety@`, `jaymn.judd@`, `shopmanager@`) | Routing · WL | 3 | 4 | Customer #2 recipients | Safety · Shop · Leadership · FL | safety form auto-email · leadership digest · shop alerts | 2 | 3 | 2 | 4 | observed |
| RISK-014 | Status verb overload — `offline`, `active`, `open` each mean ≥3 things | Verbiage | 2 | 4 | all operators | all | all status surfaces | 2 | 3 | 2 | 2 | observed |
| RISK-015 | Closure verb drift — 7 closure verbs (`closed`, `done`, `signed_off`, `final`, `success`, `approved`, `receipted`) | Verbiage | 2 | 4 | all operators | all | all workflows | 2 | 3 | 1 | 2 | observed |
| RISK-016 | OperationsActionsTile still mounted on 6 of 7 portals after Track 13.4A | Role drift | 2 | 4 | role-portal operators | DispatchHub · PmHub · ShopHub · SafetyHub · FieldLeadershipHub · AdminHub | OA-1 | 2 | 2 | 1 | 2 | observed |
| RISK-017 | Daily Report / Site Inspection / Incident form overlap | Productivity | 3 | 3 | foremen · field | public forms | 3 workflows | 2 | 1 | 1 | 1 | observed |
| RISK-018 | 8 distinct `*CommandCenter` pages | Navigation drift | 2 | 4 | all operators | Admin · PM · Dispatch · Operations · ODR · Trench · Ops Training · Guidance | navigation | 2 | 2 | 1 | 2 | observed |
| RISK-019 | 8 auth-flow variations | Architecture | 2 | 4 | all users | 7 portals + master sign-in | login · forgot · reset · change-password | 2 | 2 | 1 | 3 | observed |
| RISK-020 | 15 status-chip components, 2 share filename | UI sprawl | 2 | 4 | engineering · UX | all | all status surfaces | 1 | 2 | 1 | 2 | observed |
| RISK-021 | Hub-file size variance 4.6× | Maintainability | 2 | 4 | engineering | all portals | UI shell | 1 | 1 | 1 | 3 | observed |
| RISK-022 | Mobile evidence gap (only desktop Phase-1 landings) | Proof gap | 2 | 4 | field users | all | all | 2 | 2 | 2 | 1 | observed |
| RISK-023 | Driver portal landing missing as static page | Role gap | 2 | 3 | drivers | Driver | dispatch driver lifecycle | 2 | 2 | 1 | 1 | observed |
| RISK-024 | Field-Critical UI Spanish gap 82.5 % (126 strings) | Translation | 2 | 3 | Spanish field | all field surfaces | all field workflows | 2 | 2 | 2 | 2 | observed |
| RISK-025 | Workflow-Critical UI Spanish gap 82.5 % | Translation | 2 | 3 | Spanish field + office | all | all | 2 | 2 | 2 | 2 | observed |
| RISK-026 | Public-Facing UI Spanish gap 73.6 % | Translation · Public | 2 | 3 | public Spanish visitors | public surfaces | public forms · QR | 2 | 2 | 2 | 2 | observed |
| RISK-027 | Status verbs not wrapped in `t()` at engine level | Translation | 2 | 4 | Spanish operators | all | all status surfaces | 2 | 2 | 1 | 2 | observed |
| RISK-028 | 67 circle geofences render as 0 (geofence conversion gap) | Data integrity | 2 | 4 | dispatchers · drivers | Dispatch | geofence-based alerts | 2 | 2 | 2 | 1 | observed |
| RISK-029 | PO digest can duplicate per-action PO email | Notification noise | 2 | 4 | PO recipients | HR · Admin | PO request | 1 | 1 | 1 | 1 | observed |
| RISK-030 | 4 overlapping admin health pages | Navigation drift | 1 | 4 | admin | Admin | platform health | 1 | 1 | 1 | 1 | observed |
| RISK-031 | `AdminCompliance` + `AdminComplianceFindings` duplicate | Navigation drift | 1 | 4 | admin | Admin | compliance | 1 | 1 | 1 | 1 | observed |
| RISK-032 | 1,146 dead Spanish keys | Maintenance debt | 1 | 4 | engineering | n/a | n/a | 1 | 1 | 1 | 1 | observed |
| RISK-033 | `guidance_search_misses` invisible | Coaching loop | 1 | 4 | admin | Admin Guidance Coverage | guidance | 1 | 1 | 1 | 1 | observed |

---

## Dispatch Reality Status (mandated section)

### What is known (Track 13.4A confirmed)
- The Dispatch map render bug is fixed; visual guardrail in place.
- The marker filter bug is fixed (empty-status fallback).
- `/api/operations-map/snapshot` returns 190 assets with structured `band` and `marker_kind`.
- `DispatchMapHero` and `/operations-map` share `useMapSnapshot` — same data source.

### What is verified
- Preview-env snapshot integrity: 33 attention · 157 stale · 90 GPS-mapped · 100 no-GPS · 67 circle geofences in DB but 0 rendered.
- Visual render: real CARTO dark tiles with Florida geography and marker clusters (desktop / iPad landscape / iPad portrait).
- Cross-portal consistency: same hook, same endpoint.

### What remains unknown
- **Production Motive webhook arrival rate.** Preview env does not receive live webhooks; the 22.83h staleness in preview is *expected*, not a defect signal — but it means production behaviour has not been verified in this audit cycle.
- **GPS coverage triage:** which of the 100 no-GPS assets are "expected dark" (shop equipment, trailers without telematics) vs "should-be-live".
- **Per-unit staleness root causes:** why specific units have not posted in days/weeks.
- **`operational_summary` count derivation** has not been independently rederived from raw collections in this track.
- **`marker_kind` heuristic accuracy** vs `equipment_master.type` ground truth.
- **Trust verdict:** can Dispatch be trusted as operational truth in its current state? *Today, the honest answer is "not in preview; production webhook health must be verified."*

### What requires production validation
- Live webhook arrival logs over a 24h window in production.
- Per-unit GPS-coverage report (real vs expected dark).
- Independent rederivation of the operational summary counts.
- Geofence rendering pipeline once circle→polygon conversion lands.

---

## Translation Reality Status (mandated section)

### Operational readiness (NOT "20.5 % overall")
- Safety-Critical UI: **75.8 %**
- Field-Critical UI: 82.5 %
- Workflow-Critical UI: 82.5 %
- Public-Facing UI: 73.6 %
- Administrative UI: 74.0 %
- Technical UI: 68.8 %
- Outbound emails / PDFs / Excel / `HTTPException` / status verbs: **0 %**

### Highest-priority Spanish coverage gaps
1. Safety-Critical (100 orphan strings) — includes trench-box safety guidance, CAPA verbs, OSHA training reminders, bilingual safety-card copy that *describes* bilingual support but is itself only in English in the UI shell.
2. Field-Critical (126 orphan strings) — labels, button text, error messages.
3. Workflow-Critical (77 orphan strings) — submit / approve / close labels.
4. Public-Facing (24 orphan strings) — public posters, QR pages, cheatsheet.
5. Outbound emails / PDFs (0 % coverage) — Spanish recipients receive English-only documents.

### Lower-priority Spanish coverage gaps
- Admin / Office (19 orphan strings).
- Technical / Internal (15 orphan strings, lowest Spanish readiness at 68.8 % but smallest absolute size).
- Diagnostics, debug surfaces.

---

## Risk register discipline

- Status is **`observed`** for every row. None remediated.
- Recurrence of any row in a future audit must trigger an escalation note in the RC Certification Ledger.
- A risk row is closed only after operator approval AND a remediation entry in the ledger.
