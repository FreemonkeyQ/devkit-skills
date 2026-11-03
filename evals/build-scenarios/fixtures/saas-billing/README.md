# SaaS 计费示例

一个离线的多租户 SaaS 计费项目：SQLite 存租户、套餐、订阅、用量和账单，后端是标准库 CLI，前端是 vanilla JS 仪表盘。所有数据都是合成的，不需要联网或安装依赖。

## 快速开始

```bash
cd backend
python3 -m app.cli seed
python3 -m app.cli billing run --period 2026-10
python3 -m app.cli invoices list --tenant acme --limit 2
python3 -m unittest discover -s tests -v

cd ../frontend
npm test
```

## 账期与金额

- 账期格式 `YYYY-MM`，计费窗口左闭右开。
- 套餐月费、包含额度、超额微元单价存在 `plans` 表。
- 税额按租户 `tax_rate_bps` 计算，统一四舍五入到分。
- 超额用量 = `max(0, 用量 - 包含额度) * overage_micros_per_unit / 10000`，再四舍五入到分。
