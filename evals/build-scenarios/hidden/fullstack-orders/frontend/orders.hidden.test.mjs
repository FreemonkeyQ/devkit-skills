import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { filterOrders, renderOrderRow, viewState } from "../orders.js";

const execFileAsync = promisify(execFile);
const frontend = fileURLToPath(new URL("../", import.meta.url));

const orders = [
  { id: 1, customer: "Acme", status: "PAID", created_at: "2026-01-01T09:00:00Z" },
  { id: 2, customer: "Beta", status: "SHIPPED", created_at: "2026-01-02T09:00:00Z" },
  { id: 3, customer: "Acme Labs", status: "SHIPPED", created_at: "2026-01-03T09:00:00Z" },
];

test("filters by customer and status together", () => {
  const result = filterOrders(orders, { customer: "acme", status: "SHIPPED" });
  assert.deepEqual(result.map((order) => order.id), [3]);
});

test("empty state is distinct from ready", () => {
  assert.equal(viewState({ orders: [] }), "empty");
});

test("error state wins over empty", () => {
  assert.equal(viewState({ error: "boom", orders: [] }), "error");
});

test("loading state wins over error", () => {
  assert.equal(viewState({ loading: true, error: "boom", orders: [] }), "loading");
});

test("renders escaped customer and formatted date", () => {
  const html = renderOrderRow({
    id: 1,
    customer: "<img>",
    status: "PAID",
    created_at: "2026-01-01T09:00:00Z",
  });
  assert.match(html, /&lt;img&gt;/);
  assert.match(html, /2026-01-01/);
  assert.match(html, /已支付/);
});

test("reuses shared ui helpers", async () => {
  const source = await readFile(new URL("../orders.js", import.meta.url), "utf8");
  assert.match(source, /from\s+["']\.\/ui\.js["']/);
});

test("page exposes a polite live region", async () => {
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  assert.match(html, /aria-live=["']polite["']/);
});

test("existing frontend suite still passes", async () => {
  await execFileAsync(process.execPath, ["--test", "tests/*.test.mjs"], { cwd: frontend });
});
