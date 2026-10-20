import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { after, before, test } from "node:test";
import React from "react";
import { act, create } from "react-test-renderer";
import { createServer } from "vite";

let server;
let CropRecordForm;
let FieldEntryPage;

before(async () => {
  server = await createServer({ server: { middlewareMode: true, hmr: { server: createHttpServer() } } });
  CropRecordForm = (await server.ssrLoadModule("/src/components/CropRecordForm.jsx")).default;
  FieldEntryPage = (await server.ssrLoadModule("/src/pages/FieldEntryPage.jsx")).default;
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
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let failSave = true;
  let failRefresh = false;
  globalThis.fetch = async (_url, options) => {
    if (options?.method === "POST") {
      return failSave
        ? new Response(JSON.stringify({ detail: "Harvest event not found" }), { status: 404 })
        : new Response(JSON.stringify({ id: 1 }));
    }
    if (failRefresh) throw new TypeError("Failed to fetch");
    return new Response(JSON.stringify({ records: [] }));
  };
  const view = await render(t, FieldEntryPage);
  await act(async () => {
    view.root.findByProps({ type: "number" }).props.onChange({ target: { value: "1" } });
  });
  change(view, "plot_number", "P-1");
  const form = view.root.findByType(CropRecordForm);
  await act(async () => { await submit(form); });
  assert.equal(view.root.findByProps({ role: "alert" }).children[0], "Harvest event not found");
  assert.equal(view.root.findByProps({ name: "plot_number" }).props.value, "P-1");
  assert.equal(view.root.findByType("fieldset").props.disabled, false);
  failSave = false;
  failRefresh = true;
  await act(async () => { await submit(form); });
  assert.equal(view.root.findByProps({ role: "status" }).children[0], "Record saved.");
  assert.match(view.root.findByProps({ className: "form-error" }).children[0], /saved, but the list could not refresh/);
});

test("the entry page preserves edit mode after a rejected update", async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  let failUpdate = true;
  let updateUrl;
  const record = { id: 7, plot_number: "P-7", dynamic_data: { count: 3 } };
  globalThis.fetch = async (url, options) => {
    if (options?.method === "PATCH") {
      updateUrl = url;
      return failUpdate
        ? new Response(JSON.stringify({ detail: "Update rejected" }), { status: 400 })
        : new Response(JSON.stringify(record));
    }
    return new Response(JSON.stringify({ records: [record] }));
  };
  const view = await render(t, FieldEntryPage);
  await act(async () => {
    view.root.findByProps({ type: "number" }).props.onChange({ target: { value: "1" } });
  });
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
