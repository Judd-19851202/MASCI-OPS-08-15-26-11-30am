# FINAL_DEPLOY_POST_DEPLOY_CERTIFICATION

## User-run post-save / post-deploy checklist

These checks are prepared for the user to run after Save and Deploy. They have **not** been claimed as already executed in live production.

1. Check `/api/version` and confirm `frontend_backend_release_match=true`.
2. Check `/api/platform/data-truth` and confirm populated runtime identity fields.
3. Check `/api/health/full` and confirm backup + scheduler remain healthy.
4. Submit one controlled Daily Report and confirm the manual approved-summary lane works.
5. Confirm deferred lanes remain hidden:
   - no Monday Briefing PDF open action
   - no PM CSV export action
   - no PM schedule email-review action
6. Confirm the deployment candidate archive remains selectable for rollback.

## Post-deploy rollback trigger

If any of the checks above fail, stop release validation and use `FINAL_DEPLOY_ROLLBACK_PACKAGE.md`.