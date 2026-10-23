import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { after, before, test } from "node:test";
import React from "react";
import { act, create } from "react-test-renderer";
import { createServer } from "vite";

let server;
let CsvUploadForm;
let uploadHarvestRecordsCsv;

before(async () => {
  server = await createServer({
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: { server: createHttpServer() } }
  });
  CsvUploadForm = (await server.ssrLoadModule("/src/components/CsvUploadForm.jsx")).default;
  uploadHarvestRecordsCsv = (await server.ssrLoadModule("/src/services/api.js")).uploadHarvestRecordsCsv;
});

after(async () => { await server?.close(); });

async function render(t, onUpload) {
  let view;
  await act(async () => { view = create(React.createElement(CsvUploadForm, { onUpload })); });
  t.after(() => act(() => view.unmount()));
  return view;
}

function choose(view, file) {
  act(() => view.root.findByProps({ type: "file" }).props.onChange({ target: { files: [file] } }));
}

function submit(view, reset = () => {}) {
  return view.root.findByType("form").props.onSubmit({ preventDefault() {}, currentTarget: { reset } });
}

test("the file picker accepts CSV and XLSX", async (t) => {
  const view = await render(t, async () => []);
  const input = view.root.findByProps({ type: "file" });
  assert.ok(input.props.accept.includes(".csv"));
  assert.ok(input.props.accept.includes(".xlsx"));
  assert.equal(view.root.findByProps({ type: "submit" }).props.disabled, true);
});

test("both supported file types reach the upload callback and reset after success", async (t) => {
  for (const filename of ["records.csv", "records.XLSX"]) {
    const file = new File(["test content"], filename);
    let uploaded;
    let resets = 0;
    const view = await render(t, async (value) => { uploaded = value; return [{ id: 1 }]; });
    choose(view, file);
    await act(async () => { await submit(view, () => { resets++; }); });
    assert.equal(uploaded, file);
    assert.equal(resets, 1);
    assert.equal(view.root.findByProps({ role: "status" }).children[0], "Imported 1 record.");
    assert.equal(view.root.findByProps({ type: "submit" }).props.disabled, true);
  }
});

test("unsupported files are rejected before uploading", async (t) => {
  let calls = 0;
  const view = await render(t, async () => { calls++; return []; });
  choose(view, new File(["test"], "records.xls"));
  await act(async () => { await submit(view); });
  assert.equal(calls, 0);
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Choose a .csv or .xlsx file.");
});

test("uploads block duplicate submissions and retain failed files for retry", async (t) => {
  let reject;
  let calls = 0;
  let fail = true;
  const pending = new Promise((_resolve, failUpload) => { reject = failUpload; });
  const view = await render(t, async () => { calls++; return fail ? pending : [{ id: 1 }]; });
  choose(view, new File(["test"], "records.xlsx"));
  let uploading;
  act(() => { uploading = submit(view); });
  assert.equal(view.root.findByProps({ type: "file" }).props.disabled, true);
  assert.equal(view.root.findByProps({ type: "submit" }).props.disabled, true);
  await act(async () => { await submit(view); });
  assert.equal(calls, 1);
  await act(async () => { reject(new Error("Workbook could not be read")); await uploading; });
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Workbook could not be read");
  assert.equal(view.root.findByProps({ type: "submit" }).props.disabled, false);
  fail = false;
  await act(async () => { await submit(view); });
  assert.equal(calls, 2);
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Imported 1 record.");
});

test("the API sends both file types as multipart data to the selected harvest", async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  for (const filename of ["records.csv", "records.xlsx"]) {
    let request;
    globalThis.fetch = async (url, options) => {
      request = { url, options };
      return new Response(JSON.stringify([{ id: 1 }]));
    };
    const file = new File(["test content"], filename);
    assert.deepEqual(await uploadHarvestRecordsCsv(18, file), [{ id: 1 }]);
    assert.match(request.url, /\/harvest-records\/upload\?harvest_event_id=18$/);
    assert.equal(request.options.method, "POST");
    assert.equal(request.options.body.get("file").name, filename);
    assert.equal(await request.options.body.get("file").text(), "test content");
  }
});
