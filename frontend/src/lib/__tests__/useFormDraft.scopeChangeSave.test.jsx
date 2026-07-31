/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("useFormDraft scope-change persistence guard", () => {
  test("preserves dirty state when a new scope has no stored draft", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/lib/resiliency/useFormDraft.js"),
      "utf8",
    );

    expect(source).toContain("const hasLoadedScopeOnceRef = useRef(false);");
    expect(source).toContain("} else if (hasLoadedScopeOnceRef.current) {");
    expect(source).toContain("lastSavedKeyRef.current = null;");
    expect(source).toContain("hasLoadedScopeOnceRef.current = true;");
  });
});