# Index / Query Recommendation Register

## Governing Rule
- No Atlas index creation, hide, unhide, or drop was performed.
- Every item below ends in code repair, owner review, or not recommended.

## Register

### 1. `operational_facts` latest trench fact read
- **Outcome:** `CODE_REPAIR_COMPLETE`
- **Reason:** the project-scoped latest-fact readers were repaired in code to target the existing tenant-aware query pattern instead of asking Atlas for a new index first.
- **Index action:** none

### 2. `__pm_empty_scope__` impossible-query sentinel
- **Outcome:** `CODE_REPAIR_COMPLETE`
- **Reason:** the defect was not an indexing problem; the fix was to avoid issuing the query at all.
- **Index action:** none

### 3. Company-wide `operational_facts.distinct("project_id", ...)`
- **Outcome:** `OWNER_REVIEW`
- **Reason:** code targeting was tightened with `tenant_id`, but if Atlas still reports this path after the repair is live, the owner should review whether the company-wide fallback belongs on snapshots or needs a new read model instead of a direct index request.
- **Index action:** none in this checkpoint

### 4. Additional Atlas recommendations not supplied in this fork
- **Outcome:** `SOURCE_NOT_PROVEN`
- **Reason:** no raw alert payload was available to prove the exact query shape.
- **Index action:** none