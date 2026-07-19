# RELEASE GATE REGISTER

Date: 2026-07-19  
Checkpoint: D5/D6

Machine-readable authority: `docs/governance/release_gate_manifest.json`

Every blocking gate now has a stable ID, owner, evidence output, severity, failure message, and remediation reference. Production acceptance is strictly stronger than Preview acceptance. The gate fails if One Body authorities diverge.

## PRD-governance-lint

`python3 scripts/lint-iteration-summary.py` remains mandatory and may not be skipped or weakened.
