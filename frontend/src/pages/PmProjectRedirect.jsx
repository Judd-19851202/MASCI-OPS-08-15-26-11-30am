/**
 * PmProjectRedirect.jsx — sends /pm/projects/:projectNumber to the
 * PM Command Center with a project_number filter so a single project
 * surface is the Command Center filter, not a duplicate page.
 */
import React from "react";
import { Navigate, useParams } from "react-router-dom";

export default function PmProjectRedirect() {
  const { projectNumber } = useParams();
  const pn = (projectNumber || "").trim();
  const target = pn
    ? `/pm/command-center?project_number=${encodeURIComponent(pn)}`
    : "/pm/command-center";
  return <Navigate to={target} replace />;
}
