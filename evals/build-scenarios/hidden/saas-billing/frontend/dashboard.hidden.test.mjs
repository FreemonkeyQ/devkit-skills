import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import {
  filterInvoices,
  renderInvoiceRow,
  summarize,
  viewState,
} from "../dashboard.js";

const execFileAsync = promisify(execFile);
const frontend = fileURLToPath(new URL("../", import.meta.url));

const invoices = [
  {
    id: 1,
    tenant_name: "Acme Robotics",
    period: "2026-10",
    status: "OPEN",
    usage_units: 6200,
    total_cents: 22076,
    created_at: "2026-11-01T02:00:00Z",
  },
  {
    id: 2,
    tenant_name: "Globex Labs",
    period: "2026-09",
    status: "PAID",
    usage_units: 900,
    total_cents: 5255,
    created_at: "2026-10-01T02:00:00Z",
  },
  {
    id: 3,
    tenant_name: "<img src=x onerror=alert(1)>",
    period: "2026-10",
    status: "VOID",
    usage_units: 0,
    total_cents: 0,
    created_at: "2026-11-01T02:00:00Z",
  },
];

test("empty state is distinct from ready", () => {
  assert.equal(viewState({ invoices: [] }), "empty");
});

test("error wins over empty and loading wins over error", () => {
  assert.equal(viewState({ error: "boom", invoices: [] }), "error");
  assert.equal(viewState({ loading: true, error: "boom", invoices: [] }), "loading");
});

test("filters period and status together", () => {
  assert.deepEqual(
    filterInvoices(invoices, { period: "2026-09", status: "ALL" }).map((item) => item.id),
    [2],
  );
  assert.deepEqual(
    filterInvoices(invoices, { period: "2026-10", status: "OPEN" }).map((item) => item.id),
    [1],
  );
});

test("summary uses integer cents", () => {
  assert.deepEqual(summarize(invoices.slice(0, 2)), {
    totalCents: 27331,
    usageUnits: 7100,
  });
});

test("row escapes tenant name and reuses shared formatting", () => {
  const html = renderInvoiceRow(invoices[2]);
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(html, /<img src=x/);
  assert.match(html, /2026-11-01/);
  assert.match(html, /¥0\.00/);
});

test("page exposes a polite live region", async () => {
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  assert.match(html, /aria-live=["']polite["']/);
});

test("existing frontend suite still passes", async () => {
  await execFileAsync(process.execPath, ["--test", "tests/dashboard.test.mjs"], {
    cwd: frontend,
  });
});
