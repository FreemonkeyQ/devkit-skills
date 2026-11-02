import { escapeHtml, formatDate } from "./ui.js";

export const STATUS_LABELS = {
  PAID: "已支付",
  SHIPPED: "已发货",
  CANCELLED: "已取消",
};

export function filterOrders(orders, filters = {}) {
  const { status = "" } = filters;
  return orders.filter((order) => !status || order.status === status);
}

export function viewState({ loading = false, error = null, orders = [] } = {}) {
  if (loading) return "loading";
  if (error) return "error";
  return "ready";
}

export function renderOrderRow(order) {
  const status = STATUS_LABELS[order.status] ?? escapeHtml(order.status);
  return `<tr data-status="${escapeHtml(order.status)}"><td>${order.id}</td><td>${escapeHtml(order.customer)}</td><td>${status}</td><td>${formatDate(order.created_at)}</td></tr>`;
}
