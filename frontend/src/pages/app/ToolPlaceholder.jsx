import React from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Hammer } from "lucide-react";

/**
 * Placeholder route for Message Board / To-dos / Schedule / Docs / Hill
 * Charts. Replaced by real implementations in Phase 2/3.
 */
export default function ToolPlaceholder({ title, description }) {
  const { projectId } = useParams();
  return (
    <div className="p-8 sm:p-10 max-w-4xl">
      <Link
        to={`/app/projects/${projectId}`}
        className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6"
        data-testid="tool-placeholder-back"
      >
        <ArrowLeft className="w-3 h-3" /> Back to project
      </Link>

      <div className="bg-white border-2 border-slate-200 rounded-md p-10 text-center">
        <div className="w-14 h-14 mx-auto rounded-md bg-amber-100 text-amber-700 flex items-center justify-center">
          <Hammer className="w-7 h-7" />
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-amber-700 font-bold mt-5">
          Phase 2 · Coming soon
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-2">
          {title}
        </h1>
        <p className="text-slate-600 text-sm mt-3 max-w-xl mx-auto">{description}</p>
      </div>
    </div>
  );
}
