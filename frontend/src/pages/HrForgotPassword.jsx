import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

/**
 * HrForgotPassword — DEPRECATED. The forgot-password flow is now an
 * inline dialog on the HR Login page (iter80). This route exists only
 * as a backstop for any old bookmarks or email links pointing at
 * /hr/forgot — bounce them to /hr/login where the dialog lives.
 */
export default function HrForgotPassword() {
  const navigate = useNavigate();
  useEffect(() => {
    navigate("/hr/login", { replace: true });
  }, [navigate]);
  return null;
}
