# SaaS 计费项目约定

## 后端
- 只使用 Python 标准库与 SQLite，不新增第三方依赖。
- 测试：`cd backend && python3 -m unittest discover -s tests -v`
- 建库：`python3 -m app.cli seed`
- 生成账单：`python3 -m app.cli billing run --period 2026-10`
- 查询账单：`python3 -m app.cli invoices list --tenant acme --status OPEN --period 2026-10 --limit 20`
- `--db` 是全局参数，需要改库路径时放在子命令前：`python3 -m app.cli --db /tmp/saas.db billing run --period 2026-10`
- 服务层接口固定：
  - `app.db.connect(path)` 返回 `sqlite3.Connection`，`row_factory=sqlite3.Row`
  - `app.db.init_schema(conn)` 建表
  - `app.seed.seed(conn)` 写入固定租户、套餐、订阅和用量
  - `app.billing.run_billing(conn, period)` 返回 `{"created": int, "existing": int, "invoice_ids": [int]}`
  - `app.invoices.list_invoices(conn, tenant_id, status=None, period=None, limit=20, cursor=None)` 返回 `{"items": [...], "next_cursor": str | None}`
  - `app.invoices.get_invoice(conn, tenant_id, invoice_id)` 返回字典或 `None`
- 金额只存整数分。微元换算与税额舍入复用 `app/money.py` 的 `micros_to_cents`、`tax_cents`，不要在业务代码里另写浮点公式。
- 账单唯一键是 `(tenant_id, period)`；重复执行同一账期必须返回已有账单，不能重复计费。
- 账单列表按 `period DESC, id DESC` 排序；游标必须由实现自行编码，客户端只回传。

## 前端
- 测试：`cd frontend && npm test`（只用 Node 内置 test，不安装依赖）。
- 日期、HTML 转义、金额格式复用 `ui.js` 的 `formatDate`、`escapeHtml`、`formatMoney`。
- 仪表盘状态由 `dashboard.js` 的 `viewState` 返回 `loading`、`error`、`empty`、`ready`。
- `summarize(invoices)` 返回整数分：`{totalCents, usageUnits}`。
- 账单行渲染复用 `renderInvoiceRow`，租户名必须转义。
- 页面状态容器使用 `aria-live="polite"`，不新增运行时依赖。
