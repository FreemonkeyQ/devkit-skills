# 全栈订单示例约定

## 后端
- 测试：`cd backend && python3 -m unittest discover -s tests -v`
- 查询入口：`python3 -m app.cli orders --customer Acme --status PAID --offset 0 --limit 20`
- CLI 输出 JSON，键固定为 `items`、`total`、`next_offset`；`items[]` 含 `id/customer/status/item_count/created_at`。
- 分页响应优先复用 `app.models.PageResponse`。
- 订单列表需要订单项数量时，复用 `OrderRepository.get_items_many()` 批量取，不要在循环里逐单调用 `get_items()`。

## 前端
- 测试：`cd frontend && npm test`（只用 Node 内置 test，不安装依赖）。
- 日期与转义复用 `ui.js` 的 `formatDate`、`escapeHtml`。
- 列表状态由 `orders.js` 的 `viewState` 统一返回 `loading`、`error`、`empty`、`ready`。
- 页面状态容器使用 `aria-live="polite"`。
- 不新增运行时依赖。
