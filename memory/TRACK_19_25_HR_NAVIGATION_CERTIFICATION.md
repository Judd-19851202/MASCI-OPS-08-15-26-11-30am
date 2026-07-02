# TRACK 19.25 · HR Navigation Certification

## HR sidebar V2 · Compliance & Records domain (post-19.25)
1. Document Expirations
2. Training Records
3. Driver Qualification
4. Safety Records
5. **Historical Records Intake**       ← Track 19.24
6. **Historical Records Queue**        ← Track 19.24
7. **Bulk Historical Intake**          ← Track 19.25 (NEW)

## HR Hub V2 · HR Destinations grid (already includes intake + queue tiles from Track 19.24)
- Employees
- Training Records
- Driver Qualification
- Payroll Variance
- Time Verification
- FL Users
- Employee Accountability
- **Historical Records Intake**  (Track 19.24 tile)
- **Historical Records Queue**   (Track 19.24 tile)

## HR authority verified
- Sees all 4 lanes (HR · Safety · Asset · Corporate Import)
- Can upload · classify · approve · reject · reassign · export every record type
- Backed by the vocabulary endpoint returning `allowed_lanes_for_actor: ["hr","safety","asset","corporate_import"]` for HR tokens
- Backed by `PACKAGE_LANE_GATE` allowing HR + admin on all 6 export packages

**Verdict:** GO. HR has one-click access to every workflow.
