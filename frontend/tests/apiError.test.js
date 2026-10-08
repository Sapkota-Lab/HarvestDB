import assert from "node:assert/strict";
import test from "node:test";

import { readApiError } from "../src/services/apiError.js";

test("shows the API's error message", async () => {
  const response = new Response(JSON.stringify({ detail: "Harvest event not found" }));
  assert.equal(await readApiError(response, "Submission failed"), "Harvest event not found");
});

test("formats FastAPI validation errors with their field paths", async () => {
  const response = new Response(JSON.stringify({ detail: [
    { loc: ["body", "plot_number"], msg: "Field required" },
    { loc: ["body", "dynamic_data", "weight"], msg: "Invalid value" }
  ] }));
  assert.equal(
    await readApiError(response, "Submission failed"),
    "plot_number: Field required; dynamic_data.weight: Invalid value"
  );
});

test("uses a readable fallback for empty, malformed, or unexpected responses", async () => {
  for (const body of ["", "<html>Server error</html>", "null", "{}", '{"detail": {}}', '{"detail": [{}]}', '{"detail": " "}']) {
    assert.equal(await readApiError(new Response(body), "Submission failed"), "Submission failed");
  }
});
