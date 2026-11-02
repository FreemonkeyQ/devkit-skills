# fullstack-orders

用于前后端 A/B 评估的合成项目，无外部依赖。

- `backend/`：Python 标准库订单查询服务，含内存仓库、分页响应和 CLI。
- `frontend/`：vanilla JS 订单列表页，含现有组件与 Node 内置测试。

## 运行

```bash
cd backend && python3 -m unittest discover -s tests -v
python3 -m app.cli orders --status PAID --limit 2
cd ../frontend && npm test
```
