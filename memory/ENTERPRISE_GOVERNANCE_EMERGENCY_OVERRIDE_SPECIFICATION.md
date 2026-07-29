# Enterprise Governance Emergency Override Specification

Emergency overrides are persisted in `enterprise_governance_emergency_overrides`.

## Required attributes

- requesting identity
- acting identity
- company and project scope
- module and record
- requested capability
- denied policy
- justification
- urgency
- evidence
- required reviewers
- acknowledgement requirements
- result / disposition
- Trust Spine correlation and causation
- communication records

Preview behavior uses the existing Operations Control Plane communication chain; no direct uncontrolled email path is introduced.
