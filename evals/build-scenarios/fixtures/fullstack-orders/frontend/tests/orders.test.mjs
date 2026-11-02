import assert from "node:assert/strict";
import test from "node:test";

import { filterOrders, renderOrderRow, viewState } from "../orders.js";

const orders = [
  { id: 1, customer: "Acme", status: "PAID", created_at: "2026-01-01T09:00:00Z" },
  { id: 2, customer: "Beta", status: "SHIPPED", created_at: "2026-01-02T09:00:00Z" },
];

test("filters by status", () => {
  assert.deepEqual(filterOrders(orders, { status: "PAID" }).map((order) => order.id), [1]);
});

test("loading state is reported", () => {
  assert.equal(viewState({ loading: true, orders }), "loading");
});

test("renders a row with formatted date", () => {
  const html = renderOrderRow(orders[0]);
  assert.match(html, /Acme/);
  assert.match(html, /2026-01-01/);
});
