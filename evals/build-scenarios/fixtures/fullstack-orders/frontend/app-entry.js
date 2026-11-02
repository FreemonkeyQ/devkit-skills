import { filterOrders, renderOrderRow, viewState } from "./orders.js";

const orders = [
  { id: 1, customer: "Acme", status: "PAID", created_at: "2026-01-01T09:00:00Z" },
  { id: 2, customer: "Beta", status: "SHIPPED", created_at: "2026-01-02T09:00:00Z" },
  { id: 3, customer: "Acme Labs", status: "SHIPPED", created_at: "2026-01-03T09:00:00Z" },
];

const state = viewState({ orders });
const stateNode = document.querySelector("#orders-state");
const body = document.querySelector("#orders-body");

stateNode.textContent = state;
body.innerHTML = filterOrders(orders).map(renderOrderRow).join("");
