// Shared "← Back to Shop" link for all /shop/* subpages. Plain
// operator copy. Routes to /shop regardless of any subroute depth.
import React from "react";
import { Link } from "react-router-dom";
import { useT } from "@/lib/i18n";

export default function BackToShopLink({ style = {}, testId = "back-to-shop" }) {
  const { t } = useT();
  return (
    <Link
      to="/shop"
      data-testid={testId}
      style={{
        display: "inline-flex", alignItems: "center", gap: 6,
        padding: "6px 12px", fontSize: 12, fontWeight: 600,
        color: "var(--brand-primary, #1b4965)",
        background: "var(--paper-card)", border: "1px solid var(--border-bold)",
        borderRadius: "var(--radius-card)", textDecoration: "none",
        ...style,
      }}
    >
      ← {t("Back to Shop")}
    </Link>
  );
}
