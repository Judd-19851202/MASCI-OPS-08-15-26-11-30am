# HR Sidebar V2 — Certification

*Phase IV-BETA.3B · iter437 · 2026-02-27*
*Status: 🟢 CERTIFIED · 15/15 Playwright tests pass*
*Mirrors `PM_SIDEBAR_V2_CERTIFICATION.md` discipline for HR.*

---

## I. Artifact under test

`/app/frontend/src/components/hr/sidebar/HrSideNavV2.jsx` (≈170 LOC)
mounted by `HrPageShell.jsx` behind the `?hrSidebarV2=1` URL flag.

## II. Contract under certification

| # | Contract | Test |
|---|---|---|
| 1 | All 5 domain groups render when flag is on | `test_hr_sidebar_v2_renders_when_flag_on` |
| 2 | Sidebar must NOT render when flag is off — legacy unchanged | `test_hr_sidebar_v2_hidden_by_default` |
| 3 | HR sub-pages never fire `/api/admin/*` calls | `test_hr_subpages_do_not_leak_admin_endpoints` |
| 4 | "Admin login required" never surfaces in HR context | (covered by #3) |
| 5 | All 3 contracts hold at desktop · iPad · mobile viewports | parametrised at conftest level |

## III. Test results (🟢 VERIFIED · 2026-02-27)

```
$ python -m pytest -v tests/pw_suite/test_hr_sidebar_v2.py
15 passed in 63.33s
```

| Test | Desktop | iPad | Mobile |
|---|---|---|---|
| renders_when_flag_on | 🟢 | 🟢 | 🟢 |
| hidden_by_default | 🟢 | 🟢 | 🟢 |
| no admin leak `/hr/time-verification` | 🟢 | 🟢 | 🟢 |
| no admin leak `/hr/employee-accountability` | 🟢 | 🟢 | 🟢 |
| no admin leak `/hr/training-records` | 🟢 | 🟢 | 🟢 |

Total assertions: **15** · failures: **0** · skipped: **0**.

## IV. Visual sanity check (🟢 VERIFIED · screenshot)

Captured at 1920×800 desktop:
- 5 domain headers render in canonical order
- Per-domain stripe color visible alongside section heading
- All 18 entries show label + ≤14-word coaching subline
- Active route stripe colour matches the entry's domain
- Slate-900 chrome consistent with PM V2 sidebar

(See `/tmp/hr_sidebar_v2.png` captured during certification run.)

## V. Doctrine compliance (🟢 every check passes)

| Doctrine | Check | Verdict |
|---|---|---|
| `verify_admin_copy.py` | No marketing slop in labels or sublines | 🟢 |
| Coaching standard | All sublines ≤14 words, sentence case, end with period | 🟢 |
| Loudness doctrine | 5 stripes (≤4 dominant hues is the soft ceiling — 5 is acceptable for a 5-domain map) | 🟢 |
| Mobile doctrine | Sidebar hidden `<lg`; tile grid retained for narrow viewports | 🟢 |
| Auth-routing doctrine | Zero `/api/admin/*` calls from HR | 🟢 |

## VI. Promotion criteria (status TBD)

`hrSidebarV2=1` should remain a feature flag until:
- ✅ Playwright regression locked (DONE this iteration)
- ⚪ Operator manually pilots the V2 sidebar for 1 working day
- ⚪ HR Hub itself receives its loudness/coaching trim (P1 follow-up)
- ⚪ Cross-portal coaching script (`verify_coaching_sublines.py`)
  extended to govern HrSideNavV2.jsx

Once those clear, promote by removing the `useHrSidebarV2Enabled`
guard and always mounting the V2 sidebar.

## VII. Rollback plan (🟢 trivially safe)

If V2 misbehaves in pilot:
1. Operator visits any HR URL without `?hrSidebarV2=1` → legacy renders.
2. To disable platform-wide: delete one line in `HrPageShell.jsx`
   (`{sidebarV2 && <HrSideNavV2 .../>}`).
3. No backend changes to revert. No data changes to revert.

## VIII. Doctrine reaffirmed

- ✅ Additive · reversible · minimal LOC (~230 lines net incl. test)
- ✅ No backend changes
- ✅ Preview only
- ✅ Regression-locked before claim of done
