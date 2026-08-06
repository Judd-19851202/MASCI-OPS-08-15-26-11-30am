# WP-18DB Release Identity and Version Parity

## Preview workspace

- Frontend build stamp was regenerated against the current workspace source hash.
- Release-gate source authority is passing for preview.
- Latest preview complete archive manifest records:
  - source hash: `40e4b0ceecaec5834f2a503c139aa594`
  - git commit short identity: `40e4b0ceecae`
  - release identity: `40e4b0ceecaec5834f2a503c139aa594`

## Production read-only evidence

- Public `mascidocs.com/api/health` returns `200` with runtime identity verified.
- Public `mascidocs.com/api/version` returns `200` and exposes the current production release identity payload.
- Observed production commit from public version route: `7662415285c40bfca887ce44714c2759dfc4e527`
- Observed production built-at source: `2026-08-05T15:16:15+00:00`

## Parity interpretation

- Preview workspace and production are intentionally **not** assumed identical.
- Preview parity is proven against the active workspace and latest backup manifest.
- Production parity proof is limited to public read-only version/health evidence in this package.

## Conclusion

Release identity is now explicit across preview workspace evidence, latest certified archive manifest, and production public read-only version reporting, with environment separation preserved.