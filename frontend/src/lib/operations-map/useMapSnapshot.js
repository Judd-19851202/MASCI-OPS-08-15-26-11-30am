import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

/* Pulls the /api/operations-map/snapshot payload on a 15-s tick.
 * Returns { data, loading, error, lastFetchMs }. Doesn't block render
 * while refreshing — keeps the previous payload available. */
export function useMapSnapshot({ refreshMs = 15000 } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetchMs, setLastFetchMs] = useState(null);
  const timer = useRef(null);

  useEffect(() => {
    let cancelled = false;
    const fetchOnce = async () => {
      const t0 = performance.now();
      try {
        const { data } = await api.get("/operations-map/snapshot");
        if (!cancelled) {
          setData(data);
          setError(null);
          setLastFetchMs(Math.round(performance.now() - t0));
        }
      } catch (e) {
        if (!cancelled) setError(e?.response?.data?.detail || e?.message || "snapshot failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchOnce();
    timer.current = setInterval(fetchOnce, refreshMs);
    return () => { cancelled = true; if (timer.current) clearInterval(timer.current); };
  }, [refreshMs]);

  return { data, loading, error, lastFetchMs };
}

export function useTimeline({ refreshMs = 15000 } = {}) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    const fetchOnce = async () => {
      try {
        const { data } = await api.get("/operations-map/timeline?limit=50");
        if (!cancelled) setRows(data?.rows || []);
      } catch { /* ignore */ } finally { if (!cancelled) setLoading(false); }
    };
    fetchOnce();
    const t = setInterval(fetchOnce, refreshMs);
    return () => { cancelled = true; clearInterval(t); };
  }, [refreshMs]);
  return { rows, loading };
}

export async function fetchAsset(key) {
  const { data } = await api.get(`/operations-map/asset/${encodeURIComponent(key)}`);
  return data;
}
export async function searchAssets(q) {
  if (!q) return { hits: [], count: 0 };
  const { data } = await api.get(`/operations-map/search?q=${encodeURIComponent(q)}`);
  return data || { hits: [], count: 0 };
}
