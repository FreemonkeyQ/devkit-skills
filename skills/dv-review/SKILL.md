---
name: dv-review
description: 分别从正确性、项目规范、原始需求三条轴独立评审改动，各轴分开报告不合并。用于审 diff、提交前检查、开合并请求前复查、看这次改动有没有实现原意。Triggers: 评审, review, 审diff, 提交前检查, 看看这次改动, code review.
metadata:
  stage: verify
  reads: [.devkit/issues, .devkit/specs, CONTEXT.md, AGENTS.md]
  writes: [docs/reviews]
  edits-code: false
  next: [dv-done]
---

# 三轴评审

三条轴**并行、独立、不合并、不重排**。这个技能只报告，不改代码——要改用 `/dv-build`。

## 适用 / 不适用

适用：有 diff 要审；提交前；开 MR 前；怀疑实现偏离了需求。

不适用：要看整体代码健康 / 测试有效性 → `/dv-audit`；要改 → `/dv-build`；要看架构合理性 → `/dv-arch shape`。

## 流程

### 1. 固定比较点

用户给了就用；没给就问一次。命令固定：

```bash
git diff <fixed>...HEAD          # 三点，对比 merge-base
git log <fixed>..HEAD --oneline
```

先 `git rev-parse` 确认 ref 存在、diff 非空。坏 ref 或空 diff 在这里失败，不要带病进入子任务。

### 2. 找三样输入

| 轴 | 输入 |
|---|---|
| Correctness | diff，仓库规范，工具已覆盖项（跳过） |
| Standards | `AGENTS.md` / `CONTRIBUTING.md` / 语言规范文档 |
| Spec | 提交信息里的 issue 号 → 对应 `.devkit/issues|specs`；找不到就问 |

### 3. 并行三个子任务

用 `general-purpose` 子代理，一次发出三份：

- **Correctness** — 找 bug：边界、空值、并发、错误路径、资源泄漏。可引用 smell 基线（命名不清、重复代码、Feature Envy、数据泥团、基本类型偏执、重复 switch、散弹式修改、发散式变化、臆测的通用性、消息链、中间人、被拒绝的遗赠）。**仓库规范压过基线**；基线一律是「疑似」，标为判断项。工具已强制的跳过。≤400 字。
- **Standards** — 逐条对照仓库文档化规范，引用规范出处（文件 + 规则）。硬违规与判断项分开。≤400 字。
- **Spec** — 对照 spec 原文：(a) 要求了但缺失/不完整；(b) 做了但没要求（范围蔓延）；(c) 看着做了但实现错。每条引 spec 原句。无 spec 则跳过并注明。≤400 字。

### 4. 汇总

```
## Correctness
<原文>

## Standards
<原文>

## Spec
<原文>

---
合计：Correctness N 项 / Standards N 项 / Spec N 项
各轴最严重：<按轴各写一句，不跨轴排名>
```

### 5. 落盘

写 `docs/reviews/<YYYY-MM-DD>-<sha>.md`，含比较点、命令、三轴结论。

## 硬约束

- 不合并、不跨轴排名——这是三轴分离的全部意义
- 不修改代码（发现要改的，输出「建议 → `/dv-build`」）
- 不评价格式问题，除非工具未覆盖且规范明确要求

## 自检

- [ ] 比较点已确认，diff 非空
- [ ] 三轴各自独立成段
- [ ] 每条发现都指向具体文件/片段或 spec 原句
- [ ] 没有「整体感觉还行」这类无证据结论

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「三个轴合并成一张优先级列表更清楚」 | 合并会让一个轴掩盖另一个；分开才能同时看到「合规但做错」和「做对但不合规」 |
| 「这个规范没写清楚，我按最佳实践算」 | 基线是判断项，不是硬违规 |
| 「顺手把这几个问题改了」 | 评审不改代码 |
| 「没有 spec，那就只审代码质量吧」 | 明确标注 Spec 轴跳过，别假装审过 |
