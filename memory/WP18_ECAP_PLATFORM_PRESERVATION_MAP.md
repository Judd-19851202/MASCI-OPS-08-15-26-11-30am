# WP18 ECAP Platform Preservation Map

Date: 2026-08-03

## Preservation method

**Proof label:** `DOCUMENTED_ONLY`

Authoritative source: `WP18_ECAP_CAPABILITY_DISPOSITION_MATRIX.csv`

### Calculation method

- denominator = every row in `WP18_ECAP_CAPABILITY_DISPOSITION_MATRIX.csv`
- each row = one major subsystem / architecture surface
- percentages below are count-based, not effort-weighted
- row count denominator = `36`

## Preservation percentages

| Disposition | Count | Percentage |
|---|---:|---:|
| `PRESERVE_EXACTLY` | 7 | 19.4% |
| `PRESERVE_AND_GOVERN` | 16 | 44.4% |
| `EXTEND` | 8 | 22.2% |
| `CONSOLIDATE` | 1 | 2.8% |
| `REFACTOR_IN_PLACE` | 1 | 2.8% |
| `RETIRE` | 1 | 2.8% |
| `BUILD_NEW` | 2 | 5.6% |

### Executive interpretation

- preserved exactly or governed without structural replacement = `63.9%`
- preserved as the foundation including extension/consolidation/refactor = `91.7%`
- net-new architecture = `5.6%`

## Coverage map

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

### Preserve exactly

- project identity / `jobs_master`
- authentication / MFA / passkeys / session minting
- role / permission / approval enforcement
- project team assignments
- cost-code registry
- payroll variance
- backup / recovery systems

### Preserve and govern

- portal shells
- design system
- forms / schema-driven capture
- public workflows
- Daily Reports architecture
- safety workflows
- QA/QC workflows
- transportation / dispatch workflows
- shop workflows
- HR workflows
- notifications / approvals / escalations
- AI assistive layer
- Project P&L snapshot
- PO workflow
- PDF / email / report framework
- integration adapters / import-export

### Extend

- enterprise hierarchy propagation
- project cost-code planning
- schedule engine
- lookahead / Monday review
- forecast / commitments / overrides
- operational constraints
- Asset Spine equipment identity
- KPI rollups

### Consolidate

- resource federation

### Refactor in place

- executive reporting hierarchy

### Retire

- legacy operational intelligence digest

### Build new

- Budget Hierarchy
- Earned Value engine

## No hidden rebuild law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

No subsystem classified outside `BUILD_NEW` may be rebuilt during WP-18C unless the reopening trigger in `WP18_ECAP_NO_REBUILD_REGISTER.md` is met.