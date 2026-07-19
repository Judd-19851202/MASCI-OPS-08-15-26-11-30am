# DEPLOYMENT ROLLBACK RUNBOOK

Date: 2026-07-19  

Application rollback is source/image only by default. It does not imply configuration rollback, migration rollback, data restore, or domain rollback. Required steps: identify current and prior known-good SHA/source hash, confirm migration compatibility, keep DB/R2 untouched, redeploy prior app artifact only, verify runtime/database identity, run post-rollback probes, capture evidence, and define rollback failure response. Rollback-back requires reapplying the corrected candidate, verifying exact source identity/no config drift/DB untouched, rerunning full post-deploy certificate, and comparing error/performance metrics. Automatic Production rollback is not implemented.
