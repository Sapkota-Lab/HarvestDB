import assert from "node:assert/strict";
import test from "node:test";

import { validateRecord } from "../src/services/recordValidation.js";

test("requires a plot number, including when only whitespace is entered", () => {
  for (const plot_number of ["", "  ", "\t\n"]) {
    const result = validateRecord({ plot_number, dynamic_data: "{}" });
    assert.ok(result.errors.plot_number);
    assert.equal(result.payload, null);
  }
});

test("trims plot numbers and respects the backend's 64-character limit", () => {
  for (const character of ["A", "🌱"]) {
    const plot_number = character.repeat(64);
    const valid = validateRecord({ plot_number: ` ${plot_number} `, dynamic_data: "{}" });
    assert.deepEqual(valid.errors, {});
    assert.equal(valid.payload.plot_number, plot_number);
    const invalid = validateRecord({ plot_number: plot_number + character, dynamic_data: "{}" });
    assert.ok(invalid.errors.plot_number);
    assert.equal(invalid.payload, null);
  }
});

test("rejects malformed JSON and JSON values that are not objects", () => {
  for (const dynamic_data of ["", "{weight: 2}", '{"weight": 2,}', "null", "[]", "2", '"text"', "true"]) {
    const result = validateRecord({ plot_number: "P-1", dynamic_data });
    assert.ok(result.errors.dynamic_data, dynamic_data);
    assert.equal(result.payload, null);
  }
});

test("preserves flexible measurements and accepts an empty object", () => {
  for (const dynamic_data of [{}, { weight: 12.5, count: 0, notes: "ripe", optional: null, sizes: [1, 2] }]) {
    const result = validateRecord({ plot_number: " P-1 ", dynamic_data: JSON.stringify(dynamic_data) });
    assert.deepEqual(result.errors, {});
    assert.deepEqual(result.payload, { plot_number: "P-1", dynamic_data });
  }
});

test("reports both field errors together", () => {
  const result = validateRecord({ plot_number: " ", dynamic_data: "[]" });
  assert.deepEqual(Object.keys(result.errors), ["plot_number", "dynamic_data"]);
  assert.equal(result.payload, null);
});
