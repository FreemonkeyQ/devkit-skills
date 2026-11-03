import assert from "node:assert/strict";
import test from "node:test";

import { filterInvoices, renderInvoiceRow, viewState } from "../dashboard.js";

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
];

test("filters invoices by status", () => {
  assert.deepEqual(
    filterInvoices(invoices, { status: "PAID" }).map((invoice) => invoice.id),
    [2],
  );
});

test("loading and error states", () => {
  assert.equal(viewState({ loading: true, invoices }), "loading");
  assert.equal(viewState({ error: "boom", invoices }), "error");
});

test("renders amount, date and localized status", () => {
  const html = renderInvoiceRow(invoices[0]);
  assert.match(html, /¥220\.76/);
  assert.match(html, /2026-11-01/);
  assert.match(html, /待支付/);
});
