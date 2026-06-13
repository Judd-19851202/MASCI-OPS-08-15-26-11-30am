// Track 13.27 — Unit History selector landing page.
//
// MOUNTED AT: /shop/units/history (behind RequireShop).
// Lets the operator type a unit number and open its timeline.
// Also surfaces a "recent OOS units" list from the existing
// `/api/dispatch/command/summary.shop` channel so it never invents
// or queries an unbounded asset list.
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card, EmptyState } from "../../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

async function safeJson(path) {
  try {
    const r = await fetch(`${API}${path}`, { headers: authHeaders() });
    return r.ok ? await r.json().catch(() => null) : null;
  } catch { return null; }
}

export default function UnitHistoryLanding() {
  const navigate = useNavigate();
  const [unit, setUnit] = useState("");
  const [recentUnits, setRecentUnits] = useState([]);

  useEffect(() => {
    // Pull a short list of units already on the Shop radar (units with
    // open defects in the dispatch command summary). Falls back gracefully.
    safeJson("/api/shop/manager/queue").then((body) => {
      if (!body || !body.buckets) return;
      const seen = new Set();
      const out = [];
      Object.values(body.buckets).forEach((rows) => {
        (rows || []).forEach((d) => {
          const u = d.trailer_unit_number || d.truck_unit_number;
          if (u && !seen.has(u)) {
            seen.add(u);
            out.push(u);
          }
        });
      });
      setRecentUnits(out.slice(0, 20));
    });
  }, []);

  const go = (u) => {
    const clean = (u || "").trim();
    if (!clean) return;
    navigate(`/shop/units/${encodeURIComponent(clean)}/history`);
  };

  const onSubmit = (e) => {
    e.preventDefault();
    go(unit);
  };

  return (
    <div data-testid="unit-history-landing-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Portal · Unit History"
        pageTitle="Open a unit's timeline"
        subtitle="Type a unit number to see its complete operational history. Single source · Asset Service Event Backbone (Track 13.26). No new history system."
      >
        <Card data-testid="unit-history-landing-search-card">
          <form onSubmit={onSubmit} style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label style={{ fontSize: 12, fontWeight: 700 }}>Unit number</label>
            <input
              data-testid="unit-history-landing-input"
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              placeholder="e.g. 152"
              style={{ padding: 8, fontSize: 14, flex: 1, minWidth: 220 }}
              autoFocus
            />
            <button
              data-testid="unit-history-landing-submit"
              type="submit"
              disabled={!(unit || "").trim()}
              style={{
                padding: "8px 16px", fontSize: 13, fontWeight: 700,
                background: (unit || "").trim() ? "var(--brand-primary, #1b4965)" : "#aaa",
                color: "#fff", border: "none", borderRadius: 4,
                cursor: (unit || "").trim() ? "pointer" : "not-allowed",
              }}
            >Open history →</button>
          </form>
        </Card>

        <h3 style={{ marginTop: 24, fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: "#666" }}>
          Recent units in the Shop queue
        </h3>
        {recentUnits.length === 0 ? (
          <EmptyState
            data-testid="unit-history-landing-recent-empty"
            kicker="Nothing in queue"
            title="No units currently in the Shop Manager queue."
            body="Type a unit number above to open its history directly."
          />
        ) : (
          <div data-testid="unit-history-landing-recent-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 8 }}>
            {recentUnits.map((u) => (
              <button
                key={u}
                data-testid={`unit-history-landing-recent-${u}`}
                type="button"
                onClick={() => go(u)}
                style={{
                  padding: 12, fontSize: 13, fontWeight: 700,
                  background: "var(--paper-card)", border: "1px solid var(--border-bold)",
                  borderRadius: 4, cursor: "pointer", textAlign: "left",
                }}
              >Unit {u} →</button>
            ))}
          </div>
        )}

        <div data-testid="unit-history-landing-footer" style={{
          marginTop: 28, padding: 12, fontSize: 11, color: "#666",
          background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4,
        }}>
          Recent units derived from <code>/api/shop/manager/queue</code>. The timeline endpoint itself is <code>/api/assets/{`{unit}`}/timeline</code>.
          No master asset list query — operators with the unit number can always open its history.
        </div>
      </PortalShell>
    </div>
  );
}
