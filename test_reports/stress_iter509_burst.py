"""STRESS-3 & STRESS-4: with session keep-alive + retries."""
import os, time, json, statistics, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

s = requests.Session()
adapter = HTTPAdapter(pool_connections=4, pool_maxsize=10,
                      max_retries=Retry(total=2, backoff_factor=0.3,
                                        status_forcelist=[502, 503, 504]))
s.mount("https://", adapter)
s.mount("http://", adapter)

# Login
r = s.post(f"{API}/auth/multi-login",
           json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
           timeout=30)
assert r.status_code == 200, f"login {r.status_code}"
admin_tok = r.json()["portal_tokens"]["admin"]

results = {}

# === STRESS-3 ===
print("=== STRESS-3: perf-snapshot ===")
r = s.get(f"{API}/admin/perf-snapshot", timeout=15)
results["s3_unauth_status"] = r.status_code
print(f"unauth status: {r.status_code}")

r = s.get(f"{API}/admin/perf-snapshot", headers={"X-Admin-Token": admin_tok}, timeout=15)
assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"
d = r.json()
results["s3_overall"] = d.get("overall")
results["s3_disk_percent"] = d.get("disk", {}).get("percent")
results["s3_memory_percent"] = d.get("memory", {}).get("percent")
results["s3_mongo_ok"] = d.get("mongo", {}).get("ok")
results["s3_self_probe_p50_ms"] = d.get("self_probe", {}).get("p50_ms")
results["s3_env"] = d.get("env", {}).get("env")
results["s3_uptime_hours"] = d.get("uptime", {}).get("hours")
print(f"overall={results['s3_overall']} disk%={results['s3_disk_percent']} mem%={results['s3_memory_percent']} "
      f"mongo.ok={results['s3_mongo_ok']} p50={results['s3_self_probe_p50_ms']}ms env={results['s3_env']}")

samples = []
for _ in range(5):
    t0 = time.perf_counter()
    s.get(f"{API}/admin/perf-snapshot", headers={"X-Admin-Token": admin_tok}, timeout=15)
    samples.append((time.perf_counter() - t0) * 1000)
results["s3_warm_p50_ms"] = round(statistics.median(samples), 1)
results["s3_warm_max_ms"] = round(max(samples), 1)
print(f"warm p50={results['s3_warm_p50_ms']}ms max={results['s3_warm_max_ms']}ms")

def burst(url, n, label, headers=None):
    codes, lats = [], []
    t_start = time.perf_counter()
    errors = 0
    for i in range(n):
        try:
            t0 = time.perf_counter()
            r = s.get(url, headers=headers, timeout=20)
            lats.append((time.perf_counter() - t0) * 1000)
            codes.append(r.status_code)
        except Exception as e:
            errors += 1
            codes.append(-1)
            lats.append(20000)
    elapsed = time.perf_counter() - t_start
    ok = sum(1 for c in codes if c == 200)
    p50 = round(statistics.median(lats), 1)
    p95 = round(sorted(lats)[max(0, int(n * 0.95) - 1)], 1)
    mx = round(max(lats), 1)
    non200 = [c for c in codes if c != 200][:8]
    print(f"{label}: 200s={ok}/{n} errors={errors} p50={p50}ms p95={p95}ms max={mx}ms elapsed={round(elapsed,1)}s non200={non200}")
    return {"ok": ok, "errors": errors, "p50": p50, "p95": p95, "max": mx, "elapsed_s": round(elapsed, 1), "non200_sample": non200}

print("\n=== STRESS-4: 100x /api/health ===")
results["s4_health"] = burst(f"{API}/health", 100, "health")

print("\n=== STRESS-4b: 100x /api/notifications ===")
results["s4_notif"] = burst(f"{API}/notifications", 100, "notif", headers={"X-Admin-Token": admin_tok})

with open("/app/test_reports/stress_iter509_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\n=== FINAL ===")
print(json.dumps(results, indent=2))
