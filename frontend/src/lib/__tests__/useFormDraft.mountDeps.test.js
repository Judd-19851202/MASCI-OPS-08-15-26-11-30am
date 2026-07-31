/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

describe("useFormDraft mount load dependencies", () => {
  test("does not re-run the initial draft-load effect on every data change", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "src/lib/resiliency/useFormDraft.js"),
      "utf8",
    );

    expect(source).toContain('}, [actorId, formKey, publicAnonymous]);');
    expect(source).not.toContain('}, [actorId, data, formKey, publicAnonymous]);');
  });
});