# MASTER DEFECT REGISTER

Date: 2026-07-19  
Checkpoint: D5/D6

## Defects fixed in D5/D6

| ID | Severity | Title | Status | Owner | Evidence |
|---|---:|---|---|---|---|
| D5D6-001 | P0 | Deployment source authority undocumented for Emergent workspace deploys | FIXED | Main agent | `docs/governance/DEPLOYMENT_PIPELINE_REGISTER.md` |
| D5D6-002 | P0 | Canonical release gate manifest absent | FIXED | Main agent | `docs/governance/release_gate_manifest.json` |
| D5D6-003 | P0 | Frontend build identity could fail open on verifier errors | FIXED | Main agent | `frontend/scripts/stamp-build-version.js` |
| D5D6-004 | P0 | Release identity missing deterministic manifest hashes for artifact traceability | FIXED | Main agent | `backend/lib/release_identity.py`, tests |
| D5D6-005 | P1 | Legacy workflow governance still included `master` deploy branches | FIXED | Main agent | workflow diffs + tests |

## Owned / deferred

| ID | Severity | Title | Status | Owner | Target checkpoint |
|---|---:|---|---|---|---|
| D5D6-OWN-001 | P2 | Performance optimization beyond baseline capture deferred intentionally | OWNED | Main agent | D7 |
| D5D6-OWN-002 | P2 | Live deployed Preview/Production SHA remains unprovable from local workspace without owner deployment evidence | OWNED | Main agent + Owner | Post-owner deployment certification |
