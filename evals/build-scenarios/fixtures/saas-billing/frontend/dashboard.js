import { escapeHtml, formatDate, formatMoney } from "./ui.js";

export const DEFAULT_FILTERS = { period: "2026-10", status: "ALL" };

export const STATUS_LABELS = {
  PAID: "已支付",
  OPEN: "待支付",
  VOID: "已作废",
};

export function viewState({ loading = false, error = null, invoices = [] } = {}) {
  if (loading) return "loading";
  if (error) return "error";
  return "ready";
}

export function filterInvoices(invoices, filters = {}) {
  const { status = "ALL" } = filters;
  return invoices.filter((invoice) => status === "ALL" || invoice.status === status);
}

export function summarize(invoices) {
  return {
    totalCents: invoices.reduce((sum, invoice) => sum + invoice.total_cents / 100, 0),
    usageUnits: invoices.reduce((sum, invoice) => sum + invoice.usage_units, 0),
  };
}

export function renderInvoiceRow(invoice) {
  const status = STATUS_LABELS[invoice.status] ?? escapeHtml(invoice.status);
  return `<tr data-invoice-id="${invoice.id}"><td>${invoice.tenant_name}</td><td>${invoice.period}</td><td>${status}</td><td>${invoice.usage_units}</td><td>${formatMoney(invoice.total_cents)}</td><td>${formatDate(invoice.created_at)}</td></tr>`;
}
