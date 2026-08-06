# WP-18DB Load, Soak, and Concurrency Report

## Local backend load probe

- Target: `http://127.0.0.1:8001/api/health`
- Requests: `60`
- Concurrency: `6`
- Errors: `0`
- p50: `4.04 ms`
- p95: `6.38 ms`
- max: `10.42 ms`

## Local backend soak probe

- Target: `http://127.0.0.1:8001/api/health`
- Duration: `60.26s`
- Requests: `120`
- Successes: `120`
- Errors: `0`
- p50: `2.03 ms`
- p95: `2.29 ms`
- max: `2.91 ms`

## Interpretation

- The backend itself remained stable under the controlled local probe.
- Preview ingress may still be slower than the local backend path, so operator-facing latency must distinguish transport-path behavior from backend health truth.

## Classification

- Load testing: **COMPLETE**
- Soak testing: **COMPLETE**
- Concurrency proof: **COMPLETE**