# Smart Prefill Architecture Lock

Date: 2026-07-14
Track: DR-02

## Canonical source
- `GET /api/jobs/{project_number}/recent-context`

Evidence:
- `backend/server.py:4078-4237`

## Canonical semantics
Smart Prefill is **server-derived prior project context**. It is not:
- a live draft restore
- a local-device setup snapshot
- a hidden auto-fill

## Canonical contents proven in repo
- prior crew rows
- prior equipment rows
- start/stop/lunch time pattern fields
- actor-scoped preference when foreman/superintendent are supplied

## UI rules
- explicit offer only
- explicit apply only
- one apply transform
- one review notice explaining prefilled hours/time patterns need review

## What is not proven today
- dedicated backend recent-context support for weather/materials/haul tickets/work areas/cost codes as named prefill domains beyond what current endpoint returns

Those are **UNKNOWN / NOT VERIFIED** from repository evidence and must not be invented in implementation.

## Local setup memory boundary
- `crewMemory.js` remains local setup continuity only.
- It may help restore yesterday’s crew setup on the same device.
- It must not be presented as server-backed Smart Prefill.
