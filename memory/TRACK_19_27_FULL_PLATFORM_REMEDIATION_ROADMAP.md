# TRACK 19.27 · Full Platform Remediation Roadmap

**Only actionable non-P0/P1 items. P0/P1 are either already fixed (Tracks 19.24-19.26) or would be fixed in this track — none remain open.**

## P0 · Immediate (blocks operations)
_None identified._

## P1 · Before broader rollout (serious usability)
_None identified in Track 19.27. Track 19.26 closed the only P1 (TrenchAssetPicker screen-blocking) immediately prior to this audit._

## P2 · Post-deploy polish (nice to close soon)
| # | Item | Domain | Proposed fix | Risk | Scope | Owner | Zero-drift constraint |
|---|---|---|---|---|---|---|---|
| P2-1 | Retire legacy `AdminHub.jsx` V1 | Admin portal | Behind flag until confirmed, then remove import | Low | 1 file · 1 route removal | Platform | Keep V2 mount unchanged |
| P2-2 | Consolidate `/cheat-sheet` and `/cheatsheet` routes | Guidance | Redirect one to the other | Low | 2 route lines | Platform | Preserve deep-link URLs (301) |
| P2-3 | Guidance Center content freshness pass | Guidance | Author-side content refresh (not code) | Low | Content-only | Docs owner | No route changes |
| P2-4 | Hide "Asset Records" Shop tiles for non-`is_asset_admin` users | Shop Hub | Conditional render based on token flag | Low | 1 tile group | Platform | Backend gate already enforces — this is cosmetic |
| P2-5 | Retire legacy unversioned `Hub.jsx` | Cross-portal | Remove import after portal V2 rollout confirmed | Low | 1 file | Platform | Ensure `/` landing still routes cleanly |

## P3 · Backlog (opportunistic polish)
| # | Item | Domain | Notes |
|---|---|---|---|
| P3-1 | Sidebar V2 for Shop portal | Shop | Currently uses tile-grid HubV2; formalize to match HR/Safety/Admin/PM/Dispatch |
| P3-2 | Sidebar V2 for Transportation / Fleet | Transportation | Same |
| P3-3 | Enter-key auto-select in TrenchAssetPicker | Trench Safety | Zero-drift enhancement suggested at close of Track 19.26 |
| P3-4 | Recently-used assets shortcut in TrenchAssetPicker | Trench Safety | Zero-drift enhancement suggested at close of Track 19.26 |
| P3-5 | "Continue previous session" one-click in bulk-batches | HR historical intake | Zero-drift enhancement suggested at close of Track 19.25 |
| P3-6 | Session-level batch analytics ("boxes digitized this quarter") | HR historical intake | Additive read-only |
| P3-7 | Pilot-signoff PDF stitcher | Deployment | Suggested at close of Track 19.23 |
| P3-8 | Compliance At Risk widget | HR portal home | Suggested at close of Track 19.22 |
| P3-9 | Recent intake activity feed | HR portal home | Suggested at close of Track 19.21b |
| P3-10 | Onboarding hint / "New here?" callout | HR portal | Would take discoverability score from 9→10 |

## Future / bigger tracks (not for surgical fixes)
- Mobile-native (iOS/Android) app shell
- Pre-canned OSHA 300 auto-fill (partial today · could be full)
- Wider integrations catalog (Samsara, Buildertrend, HCSS deeper)
- Content-refresh cadence for Guidance Center (quarterly)
- Sidebar V2 rollouts for Shop / Transportation / Fleet portals (P3-1 · P3-2)

## Test-infra debt (pre-existing, unchanged this track)
- Pytest asyncio cross-suite bleed on combined-suite runs. Isolated per-file execution GREEN. Owned by a future test-infra refactor track.

## Deployment blockers
**None.** The platform is ready for continued pilot expansion.
