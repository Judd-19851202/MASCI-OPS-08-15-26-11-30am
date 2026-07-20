# Performance Event Contract

## Canonical Authorities
- Runtime health and bounded resilience: `backend/lib/runtime_reliability.py`
- Admin diagnostics: `backend/routes/admin_runtime_reliability.py`
- Release gate enforcement: `scripts/release_gate.py`
- Machine-readable baseline: `docs/performance/performance_baseline.json`

## Event Classes
- `query_targeting_repair`
- `pm_scope_short_circuit`
- `resource_threshold_crossed`
- `bounded_workspace_cleanup`
- `intentional_fail_closed_probe`

## Required Event Properties
- `checkpoint`
- `source_file`
- `disposition`
- `evidence_path`
- `mutation_performed` (must remain `false` for D7/D8)

## Guardrails
- Events extend the existing runtime health and release gate spines; no parallel monitoring system is introduced.
- Resource distress can trigger bounded cleanup and incident evidence capture only.
- Atlas index actions remain owner-governed and out-of-scope for automatic remediation.