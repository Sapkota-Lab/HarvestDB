import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { after, before, test } from "node:test";
import React from "react";
import { act, create } from "react-test-renderer";
import { createServer } from "vite";

let server;
let CropRecordForm;
let FieldEntryPage;
let CsvUploadForm;

before(async () => {
  server = await createServer({
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: { server: createHttpServer() } }
  });
  CropRecordForm = (await server.ssrLoadModule("/src/components/CropRecordForm.jsx")).default;
  FieldEntryPage = (await server.ssrLoadModule("/src/pages/FieldEntryPage.jsx")).default;
  CsvUploadForm = (await server.ssrLoadModule("/src/components/CsvUploadForm.jsx")).default;
});

after(async () => {
  await server?.close();
});

async function render(t, Component, props = {}) {
  let view;
  await act(async () => { view = create(React.createElement(Component, props)); });
  t.after(() => act(() => view.unmount()));
  return view;
}

function change(view, name, value) {
  act(() => {
    view.root.findByProps({ name }).props.onChange({ target: { name, value } });
  });
}

function submit(view, focus = () => {}) {
  return (view.root || view).findByType("form").props.onSubmit({
    preventDefault() {},
    currentTarget: { elements: { namedItem: (name) => ({ focus: () => focus(name) }) } }
  });
}

function mockSelectionFetch(t, handler) {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = async (url, options) => {
    if (url.includes("/fields/")) return new Response(JSON.stringify([{ id: 1, name: "Lexington" }]));
    if (url.includes("/harvests/")) return new Response(JSON.stringify([{ id: 1, field_id: 1, harvest_date: "2026-10-20" }]));
    if (url.includes("/images")) return new Response("[]");
    return handler(url, options);
  };
}

async function selectEvent(view) {
  await act(async () => { change(view, "field_id", "1"); });
  await act(async () => { change(view, "harvest_event_id", "1"); });
}

function mockFetch(t, handler) {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = handler;
}

function response(value, status = 200) {
  return new Response(JSON.stringify(value), { status });
}

function click(view, label) {
  view.root.findAllByType("button").find((button) => button.children[0] === label).props.onClick();
}

test("invalid entries focus the first error without calling the API", async (t) => {
  let calls = 0;
  let focused;
  const view = await render(t, CropRecordForm, { onSubmit: () => { calls++; } });
  change(view, "dynamic_data", "[]");
  await act(async () => { await submit(view, (name) => { focused = name; }); });
  assert.equal(calls, 0);
  assert.equal(focused, "plot_number");
  assert.equal(view.root.findByProps({ name: "plot_number" }).props["aria-invalid"], true);
  assert.equal(view.root.findByProps({ name: "dynamic_data" }).props["aria-invalid"], true);
});

test("failed submissions retain inputs and allow a successful retry", async (t) => {
  let fail = true;
  const view = await render(t, CropRecordForm, { onSubmit: async () => {
    if (fail) throw new Error("Harvest event not found");
  } });
  change(view, "plot_number", " P-1 ");
  change(view, "dynamic_data", '{"weight":12.5}');
  await act(async () => { await submit(view); });
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Harvest event not found");
  assert.equal(view.root.findByProps({ name: "plot_number" }).props.value, " P-1 ");
  assert.equal(view.root.findByProps({ name: "dynamic_data" }).props.value, '{"weight":12.5}');
  assert.equal(view.root.findByProps({ type: "submit" }).props.disabled, false);
  fail = false;
  await act(async () => { await submit(view); });
  assert.equal(view.root.findByProps({ name: "plot_number" }).props.value, "");
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Record saved.");
});

test("editing uses the same validation and blocks duplicate submissions", async (t) => {
  let resolve;
  let calls = 0;
  let payload;
  const pending = new Promise((done) => { resolve = done; });
  const view = await render(t, CropRecordForm, {
    record: { id: 7, plot_number: "P-7", dynamic_data: { count: 3 } },
    onCancelEdit() {},
    onSubmit: (value) => { calls++; payload = value; return pending; }
  });
  assert.equal(view.root.findByProps({ type: "submit" }).children[0], "Update Record");
  change(view, "dynamic_data", "null");
  await act(async () => { await submit(view); });
  assert.equal(calls, 0);
  change(view, "dynamic_data", '{"count":4}');
  let saving;
  act(() => { saving = submit(view); });
  await act(async () => { await submit(view); });
  assert.equal(calls, 1);
  assert.deepEqual(payload, { plot_number: "P-7", dynamic_data: { count: 4 } });
  assert.equal(view.root.findByProps({ type: "submit" }).props.disabled, true);
  assert.equal(view.root.findByProps({ type: "button" }).props.disabled, true);
  await act(async () => { resolve(); await saving; });
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Record updated.");
});

test("the entry page propagates save failures and distinguishes refresh failures", async (t) => {
  let failSave = true;
  let failRefresh = false;
  mockSelectionFetch(t, async (_url, options) => {
    if (options?.method === "POST") {
      return failSave
        ? new Response(JSON.stringify({ detail: "Harvest event not found" }), { status: 404 })
        : new Response(JSON.stringify({ id: 1 }));
    }
    if (failRefresh) throw new TypeError("Failed to fetch");
    return new Response(JSON.stringify({ records: [] }));
  });
  const view = await render(t, FieldEntryPage);
  await selectEvent(view);
  change(view, "plot_number", "P-1");
  const form = view.root.findByType(CropRecordForm);
  await act(async () => { await submit(form); });
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Harvest event not found");
  assert.equal(view.root.findByProps({ name: "plot_number" }).props.value, "P-1");
  assert.equal(view.root.findAllByType("fieldset")[0].props.disabled, false);
  failSave = false;
  failRefresh = true;
  await act(async () => { await submit(form); });
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Record saved.");
  assert.match(view.root.findByProps({ className: "form-error" }).children[0], /saved, but the list could not refresh/);
});

test("the entry page preserves edit mode after a rejected update", async (t) => {
  let failUpdate = true;
  let updateUrl;
  const record = { id: 7, plot_number: "P-7", dynamic_data: { count: 3 } };
  mockSelectionFetch(t, async (url, options) => {
    if (options?.method === "PATCH") {
      updateUrl = url;
      return failUpdate
        ? new Response(JSON.stringify({ detail: "Update rejected" }), { status: 400 })
        : new Response(JSON.stringify(record));
    }
    return new Response(JSON.stringify({ records: [record] }));
  });
  const view = await render(t, FieldEntryPage);
  await selectEvent(view);
  act(() => {
    view.root.findAllByType("button").find((button) => button.children[0] === "Edit").props.onClick();
  });
  change(view, "dynamic_data", '{"count":4}');
  const form = view.root.findByType(CropRecordForm);
  await act(async () => { await submit(form); });
  assert.match(updateUrl, /harvest-records\/7$/);
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Update rejected");
  assert.equal(view.root.findByProps({ name: "dynamic_data" }).props.value, '{"count":4}');
  assert.equal(form.findByProps({ type: "submit" }).children[0], "Update Record");
  failUpdate = false;
  await act(async () => { await submit(form); });
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Record updated.");
  assert.equal(view.root.findByProps({ name: "plot_number" }).props.value, "");
});

test("users can create a field and event, then save and upload to that event", async (t) => {
  const calls = [];
  const field = { id: 8, name: "Lexington" };
  const harvest = { id: 18, field_id: 8, harvest_date: "2026-10-20", harvest_number: 2 };
  mockFetch(t, async (url, options) => {
    calls.push({ url, options });
    if (url.includes("/fields/")) return response(options?.method === "POST" ? field : []);
    if (url.includes("/harvests/")) return response(options?.method === "POST" ? harvest : []);
    if (url.includes("/upload")) return response({ records: [{ id: 2 }], imported_sheets: [], skipped_sheets: [] });
    return response(options?.method === "POST" ? { id: 1 } : { records: [] });
  });
  const view = await render(t, FieldEntryPage);
  assert.equal(view.root.findAllByType("fieldset")[2].props.disabled, true);
  act(() => click(view, "Add field"));
  change(view, "field_name", " Lexington ");
  await act(async () => {
    await view.root.findByProps({ "aria-label": "Add field" }).props.onSubmit({ preventDefault() {} });
  });
  assert.equal(view.root.findByProps({ name: "field_id" }).props.value, "8");
  act(() => click(view, "New harvest event"));
  change(view, "harvest_date", "2026-10-20");
  change(view, "harvest_number", "2");
  change(view, "harvest_notes", " First test ");
  await act(async () => {
    await view.root.findByProps({ "aria-label": "New harvest event" }).props.onSubmit({ preventDefault() {} });
  });
  assert.equal(view.root.findByProps({ name: "harvest_event_id" }).props.value, "18");
  assert.equal(view.root.findAllByType("fieldset")[2].props.disabled, false);
  const eventRequest = calls.find((call) => call.url.includes("/harvests/") && call.options?.method === "POST");
  assert.match(eventRequest.url, /field_id=8$/);
  assert.deepEqual(JSON.parse(eventRequest.options.body), {
    harvest_date: "2026-10-20", harvest_number: 2, notes: "First test"
  });
  change(view, "plot_number", "P-1");
  await act(async () => { await submit(view.root.findByType(CropRecordForm)); });
  assert.ok(calls.some((call) => call.options?.method === "POST" && call.url.endsWith("/harvest-records/?harvest_event_id=18")));
  const upload = view.root.findByType(CsvUploadForm);
  act(() => upload.findByProps({ type: "file" }).props.onChange({ target: {
    files: [new File(["plot_number\nP-2\n"], "records.csv", { type: "text/csv" })]
  } }));
  await act(async () => {
    await upload.findByType("form").props.onSubmit({
      preventDefault() {},
      currentTarget: { reset() {} }
    });
  });
  const csvRequest = calls.find((call) => call.url.includes("/upload"));
  assert.match(csvRequest.url, /harvest_event_id=18$/);
  assert.equal(csvRequest.options.body.get("file").name, "records.csv");
  assert.equal(upload.findByProps({ className: "upload-status" }).children[0], "Imported 1 record.");
});

test("switching fields ignores late harvest and record responses", async (t) => {
  let resolveHarvests;
  let resolveRecords;
  const oldHarvests = new Promise((resolve) => { resolveHarvests = resolve; });
  const oldRecords = new Promise((resolve) => { resolveRecords = resolve; });
  mockFetch(t, async (url) => {
    if (url.includes("/fields/")) return response([{ id: 1, name: "First" }, { id: 2, name: "Second" }]);
    if (url.includes("/harvests/?field_id=1")) return oldHarvests;
    if (url.includes("/harvests/?field_id=2")) return response([{ id: 22, field_id: 2, harvest_date: "2026-10-20" }]);
    return oldRecords;
  });
  const view = await render(t, FieldEntryPage);
  await act(async () => { change(view, "field_id", "1"); });
  await act(async () => { change(view, "field_id", "2"); });
  await act(async () => {
    resolveHarvests(response([{ id: 11, field_id: 1, harvest_date: "2026-10-19" }]));
    await oldHarvests;
  });
  const options = view.root.findByProps({ name: "harvest_event_id" }).findAllByType("option");
  assert.deepEqual(options.map((option) => option.props.value), ["", 22]);
  await act(async () => { change(view, "harvest_event_id", "22"); });
  await act(async () => { change(view, "field_id", "1"); });
  await act(async () => {
    resolveRecords(response({ records: [{ id: 5, plot_number: "OLD" }] }));
    await oldRecords;
  });
  assert.equal(view.root.findByProps({ name: "harvest_event_id" }).props.value, "");
  assert.equal(view.root.findAllByType("fieldset")[2].props.disabled, true);
  assert.equal(view.root.findAllByType("td").some((cell) => cell.children.includes("OLD")), false);
});

test("field and harvest loading failures can be retried", async (t) => {
  let failFields = true;
  let failHarvests = true;
  mockFetch(t, async (url) => {
    if (url.includes("/fields/")) {
      return failFields ? response({ detail: "Fields unavailable" }, 503) : response([{ id: 1, name: "Lexington" }]);
    }
    return failHarvests ? response({ detail: "Harvests unavailable" }, 503) : response([]);
  });
  const view = await render(t, FieldEntryPage);
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Fields unavailable");
  failFields = false;
  await act(async () => click(view, "Retry fields"));
  await act(async () => { change(view, "field_id", "1"); });
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Harvests unavailable");
  failHarvests = false;
  await act(async () => click(view, "Retry harvest events"));
  assert.equal(view.root.findAllByProps({ role: "alert" }).length, 0);
  assert.equal(view.root.findByProps({ name: "harvest_event_id" }).props.disabled, false);
});

test("failed event creation keeps the form values for retry", async (t) => {
  let fail = true;
  mockFetch(t, async (url, options) => {
    if (url.includes("/fields/")) return response([{ id: 1, name: "Lexington" }]);
    if (options?.method === "POST") {
      return fail ? response({ detail: "Could not create event" }, 503) : response({ id: 3, field_id: 1, harvest_date: "2026-10-20" });
    }
    return response(url.includes("/harvests/") ? [] : { records: [] });
  });
  const view = await render(t, FieldEntryPage);
  await act(async () => { change(view, "field_id", "1"); });
  act(() => click(view, "New harvest event"));
  change(view, "harvest_date", "2026-10-20");
  const createEvent = () => view.root.findByProps({ "aria-label": "New harvest event" }).props.onSubmit({ preventDefault() {} });
  await act(async () => { await createEvent(); });
  assert.equal(view.root.findByProps({ name: "harvest_date" }).props.value, "2026-10-20");
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Could not create event");
  fail = false;
  await act(async () => { await createEvent(); });
  assert.equal(view.root.findByProps({ name: "harvest_event_id" }).props.value, "3");
});
