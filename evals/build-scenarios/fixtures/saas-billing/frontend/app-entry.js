import {
  DEFAULT_FILTERS,
  filterInvoices,
  renderInvoiceRow,
  summarize,
  viewState,
} from "./dashboard.js";
import { formatMoney } from "./ui.js";

const stateNode = document.querySelector("#state");
const rowsNode = document.querySelector("#invoice-rows");
const totalNode = document.querySelector("#total");
const usageNode = document.querySelector("#usage");
const form = document.querySelector("#filters");

let invoices = [];
let loading = false;
let error = null;

function render() {
  const state = viewState({ loading, error, invoices });
  stateNode.textContent = state === "ready" ? "" : state;
  const visible = filterInvoices(invoices, {
    period: form.period.value,
    status: form.status.value,
  });
  rowsNode.innerHTML = visible.map(renderInvoiceRow).join("");
  const summary = summarize(visible);
  totalNode.textContent = formatMoney(summary.totalCents);
  usageNode.textContent = String(summary.usageUnits);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  render();
});

render();
