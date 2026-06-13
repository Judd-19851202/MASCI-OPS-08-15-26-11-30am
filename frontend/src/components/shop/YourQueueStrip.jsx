// Track 13.30C — Role-aware Your-Queue strip for ShopHubV2.
// Hits /api/shop/me/summary and renders role-specific cards.
// Falls back to the generic strip if role is unknown.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { Card, StatusChip } from "../../design-system";

// Local SectionHeader (matches ShopHubV2 inline component) — keeps
// typography consistent without depending on an unexported barrel.
function SectionHeader({ kicker, title, caption }) {
  return (
    <header style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".08em",
                    textTransform: "uppercase", color: "var(--ink-soft)" }}>{kicker}</div>
      <h2 style={{ margin: "2px 0 4px", fontSize: 18, fontWeight: 800, color: "var(--ink-strong)" }}>{title}</h2>
      {caption && (
        <div style={{ fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.4 }}>{caption}</div>
      )}
    </header>
  );
}

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

// Per-key destinations + accents. Counts > 0 get warning accent.
const MANAGER_DEFS = [
  { key: "unassigned",         to: "/shop/manager/queue",                  accent: "red" },
  { key: "pending_review",     to: "/shop/manager/queue",                  accent: "amber" },
  { key: "waiting_parts",      to: "/shop/equipment",                       accent: "amber" },
  { key: "rts_pending",        to: "/shop/manager/queue",                  accent: "blue" },
  { key: "variance_review_7d", to: "/shop/service-truck-reconciliation",   accent: "amber" },
];
const MECHANIC_DEFS = [
  { key: "assigned_to_me", to: "/shop/me", accent: "red" },
  { key: "accepted",       to: "/shop/me", accent: "amber" },
  { key: "in_progress",    to: "/shop/me", accent: "blue" },
  { key: "rejected_back",  to: "/shop/me", accent: "red" },
  { key: "waiting_parts",  to: "/shop/me", accent: "amber" },
];

function MetricCard({ to, label, count, accent, testid }) {
  const tone = count > 0 ? accent : "calm";
  const styleMap = {
    red:   { bg: "#fef2f2", border: "#fecaca", text: "#991b1b", chip: "pending_verification" },
    amber: { bg: "#fffbeb", border: "#fde68a", text: "#92400e", chip: "pending_verification" },
    blue:  { bg: "#eff6ff", border: "#bfdbfe", text: "#1e40af", chip: "draft" },
    calm:  { bg: "var(--paper-card)", border: "var(--border-bold)", text: "var(--ink-strong)", chip: "verified" },
  };
  const s = styleMap[tone] || styleMap.calm;
  return (
    <Link to={to} data-testid={testid}
          style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <div style={{
        padding: "14px 16px", background: s.bg, border: `1px solid ${s.border}`,
        borderRadius: "var(--radius-card)", minHeight: 92,
        display: "flex", flexDirection: "column", justifyContent: "space-between",
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".04em",
                      textTransform: "uppercase", color: s.text, opacity: 0.85 }}>{label}</div>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginTop: 4 }}>
          <div data-testid={`${testid}-value`}
               style={{ fontSize: 32, fontWeight: 700, color: s.text, lineHeight: 1 }}>
            {count == null ? "—" : count}
          </div>
          <StatusChip statusKey={s.chip} compact
                      label={count == null ? "Loading" : (count > 0 ? "Action" : "Clear")} />
        </div>
      </div>
    </Link>
  );
}

export default function YourQueueStrip() {
  const [body, setBody] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch(`${API}/api/shop/me/summary`, { headers: authHeaders() });
        const data = await r.json().catch(() => null);
        if (!r.ok) throw new Error((data && data.detail) || `HTTP ${r.status}`);
        if (alive) { setBody(data); setError(""); }
      } catch (e) {
        if (alive) setError(e.message || "Queue summary unavailable.");
      }
      if (alive) setLoading(false);
    })();
    return () => { alive = false; };
  }, []);

  const role = body?.role || "generic";
  const counts = body?.counts || {};
  const labels = body?.labels || {};
  const defs =
    role === "shop_manager" || role === "admin" ? MANAGER_DEFS
    : role === "mechanic" ? MECHANIC_DEFS
    : null;

  // Generic fallback — link cards, not metrics.
  if (!defs) {
    return (
      <section data-testid="shop-hub-v2-your-queue-strip" style={{ marginBottom: 24 }}>
        <SectionHeader
          kicker="Your queue"
          title="Pick up where the shop left off"
          caption={loading ? "Loading role summary…" :
                   error ? "Queue summary unavailable. No data invented." :
                   "Manager Queue · My Assignments · Fuel / Lube Visit · Unit History."}
        />
        <div data-testid="shop-hub-v2-your-queue-grid"
             style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
          <Link to="/shop/manager/queue" data-testid="shop-hub-v2-yq-manager-queue" style={{ textDecoration: "none", color: "inherit" }}>
            <Card title="Manager Queue" description="Unassigned · Pending Review · RTS Pending." />
          </Link>
          <Link to="/shop/me" data-testid="shop-hub-v2-yq-my-assignments" style={{ textDecoration: "none", color: "inherit" }}>
            <Card title="My Assignments" description="Mechanic queue — accept · start · complete." />
          </Link>
          <Link to="/shop/fuel-lube/new" data-testid="shop-hub-v2-yq-fuel-lube" style={{ textDecoration: "none", color: "inherit" }}>
            <Card title="Fuel / Lube Visit" description="One job · many equipment lines." />
          </Link>
          <Link to="/shop/units/history" data-testid="shop-hub-v2-yq-unit-history" style={{ textDecoration: "none", color: "inherit" }}>
            <Card title="Unit History" description="One unit · one timeline." />
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section data-testid="shop-hub-v2-your-queue-strip" style={{ marginBottom: 24 }}>
      <SectionHeader
        kicker={role === "mechanic" ? "Your queue · mechanic view" : "Your queue · shop manager view"}
        title={role === "mechanic" ? "Your assigned work" : "Shop-wide queue"}
        caption={
          loading ? "Loading queue summary…" :
          role === "mechanic"
            ? "What's assigned to you · what's in progress · what's blocked · what was rejected back."
            : "Unassigned · pending review · waiting parts · RTS pending · variance needing review."
        }
      />
      <div data-testid="shop-hub-v2-your-queue-grid"
           style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
        {defs.map((d) => (
          <MetricCard key={d.key}
                      to={d.to}
                      label={labels[d.key] || d.key.replace(/_/g, " ")}
                      count={typeof counts[d.key] === "number" ? counts[d.key] : null}
                      accent={d.accent}
                      testid={`shop-hub-v2-yq-${d.key.replace(/_/g, "-")}`} />
        ))}
      </div>
    </section>
  );
}
