# TRACK 19.25 · Safety Navigation Certification

## Safety sidebar V2 · Compliance & Records domain (post-19.25)
1. Document Expirations
2. Fire Extinguishers
3. Weekly Digest
4. Reports & Exports
5. **Safety Records Intake**       ← NEW · same route as HR intake, backend gate confines Safety to Safety lane
6. **Safety Records Queue**        ← NEW · same route, `allowed_lanes_for_actor: ["safety"]` on server
7. **Bulk Historical Intake**      ← NEW · same route, Safety lane batches only

## Safety authority verified (live curl)
- `GET /api/employee-records/vocabulary` with `X-Safety-Token` → `allowed_lanes_for_actor: ["safety"]`
- `GET /api/employee-records/queues/hr` with `X-Safety-Token` → **403** ✅
- `GET /api/employee-records/queues/safety` with `X-Safety-Token` → **200** ✅
- Can upload / approve / reject Safety-lane records
- Can link employee + incident/case + training via existing intake fields
- Cannot mutate HR-lane or Asset-lane records

The Safety-lane intake page automatically reveals the **Incident Case ID** field when `lane === "safety"` (existing Track 19.21b behavior — retained).

**Verdict:** GO. Safety has one-click access to their lane workflow; hard-gated at the server on cross-lane attempts.
