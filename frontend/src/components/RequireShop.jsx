import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isShop } from "@/lib/shopAuth";
import { isAdmin } from "@/lib/adminAuth";

/**
 * Allows the route through if the user holds EITHER a shop token or an
 * admin token (admin can see everything the shop sees).
 */
export function RequireShop({ children }) {
  const location = useLocation();
  if (!isShop() && !isAdmin()) {
    return (
      <Navigate
        to="/shop/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }
  return children;
}

export default RequireShop;
