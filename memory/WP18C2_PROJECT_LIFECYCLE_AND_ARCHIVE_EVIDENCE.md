# WP18C2 · Project Lifecycle and Archive Evidence

## Implemented Lifecycle Register

Collection:

- `project_controls_project_lifecycle`

Implemented states:

- Proposal
- Awarded
- Preconstruction
- Active
- Substantial Completion
- Final Completion
- Closed
- Archived

## Runtime Evidence

Current lifecycle record count: **1**

Certified sample project:

- Project: `ZZ-RUNTIME-CERT-2026`
- Derived source state from protected project identity: `Active`
- Archive status: verified **true then false** during QA archive/restore cycle

### Recorded lifecycle history

1. `wp18c2_backfill` derived initial `Active`
2. `cert.pm@example.com` runtime verification update
3. `cert.pm@example.com` archive action with reason `QA archive pass`
4. `cert.pm@example.com` restore action with reason `QA restore pass`

### Recorded archive history

- archive event retained with timestamp and actor
- restore event retained with timestamp and actor

## Archive Rule Implemented

Archive in WP18C2 means:

- set governed archive status
- preserve lifecycle and archive history
- preserve search/read access subject to permissions
- never delete historical operational evidence

This satisfies the constitutional rule:

> Archive never means delete.

## Connected Structure Evidence

When a matching project hierarchy node exists, archive/restore updates the connected hierarchy archive flag additively instead of introducing a new project identity system.
