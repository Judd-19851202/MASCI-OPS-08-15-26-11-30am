# TRACK 15.68C · Asset Taxonomy Sweep
See `TRACK_15_68C_FINAL_CLOSEOUT.md` §4. **✅ Classified — no code change required.**
`backend/services/asset_taxonomy.py` `CANONICAL_COMPANIES` tuple includes `"MASCI"`, `"MASCI_GC"` — internal Mongo discriminator. Not surfaced to UI/PDF/exports/API responses consumed by Customer #2. Verified by grep: no `CANONICAL_COMPANIES` import reaches frontend JSX or PDF templates. Allowed per Phase 4 option (3).
