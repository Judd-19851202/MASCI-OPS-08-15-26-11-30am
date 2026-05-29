# ODR Completion-Time Drift Report

_Window: last 7 day(s) · sample size 8 · generated 2026-05-29T13:00:38.663189+00:00._

**Doctrine source:** `ODR_SIMPLICITY_TEST_DOCTRINE.md`

## Summary

- Mean completion: **1.50 min** (90 sec)
- p50 completion: 1.50 min
- p95 completion: 1.50 min
- Drift state: **GREEN**

## Thresholds

| Bound | Value | This window |
|---|---|---|
| Stretch goal | < 3.0 min | PASS |
| Target | < 5.0 min | PASS |
| Hard ceiling (regression) | 7.0 min | PASS |

## ADVISORY

This probe **never fails the build**. It surfaces the rolling
completion trend so operators can intervene before regression
becomes structural.

_Probe exit code: 0 (advisory)._
